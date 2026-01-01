"""
Policy versioning + promotion/rollback.

This is the persistence layer for Learning/Policy macros:
- UPDATE_POLICY creates a "candidate" version snapshot
- PROMOTE_POLICY marks a version active and restores it into the active model/buffer paths
- ROLLBACK_POLICY restores a prior version into the active model/buffer paths

Design goals:
- restart-safe: everything needed for restore lives on disk
- auditable: stable metadata + sha256 digests for artifacts
- bounded growth: history capped (configurable)
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass


def _sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    h = sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _atomic_copy(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(str(src))
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dst.name}.", suffix=".tmp", dir=str(dst.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as out:
            with src.open("rb") as inp:
                shutil.copyfileobj(inp, out, length=1024 * 1024)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp_path, dst)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass


@dataclass(frozen=True)
class PolicyVersionMeta:
    version_id: int
    timestamp: str
    status: str  # "candidate" | "active" | "archived"
    algorithm: str  # "online_nn" | "ppo" | "unknown"
    label: str
    rationale: str
    model_file: Optional[str]
    buffer_file: Optional[str]
    model_sha256: Optional[str]
    buffer_sha256: Optional[str]


class PolicyVersionStore:
    """
    Append-only store of policy versions + artifact copies.
    """

    def __init__(self, store_path: str, archive_dir: str, *, max_history: int = 200) -> None:
        self.store_path = Path(store_path)
        self.archive_dir = Path(archive_dir)
        self.max_history = max(1, int(max_history))

    def _load(self) -> Dict[str, Any]:
        if not self.store_path.exists():
            return {"current_version_id": 0, "active_version_id": 0, "history": []}
        try:
            data = json.loads(self.store_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"current_version_id": 0, "active_version_id": 0, "history": []}
            history = data.get("history")
            if not isinstance(history, list):
                history = []
            return {
                "current_version_id": int(data.get("current_version_id", 0) or 0),
                "active_version_id": int(data.get("active_version_id", 0) or 0),
                "history": history,
            }
        except Exception:
            return {"current_version_id": 0, "active_version_id": 0, "history": []}

    def _save(self, data: Dict[str, Any]) -> None:
        _atomic_write_json(self.store_path, data)

    def list(self, *, limit: int = 20) -> List[PolicyVersionMeta]:
        data = self._load()
        items = [e for e in (data.get("history") or []) if isinstance(e, dict)]
        items = items[-max(1, int(limit)) :]
        metas: List[PolicyVersionMeta] = []
        for e in items:
            try:
                metas.append(
                    PolicyVersionMeta(
                        version_id=int(e.get("version_id")),
                        timestamp=str(e.get("timestamp", "")),
                        status=str(e.get("status", "")),
                        algorithm=str(e.get("algorithm", "")),
                        label=str(e.get("label", "")),
                        rationale=str(e.get("rationale", "")),
                        model_file=e.get("model_file") if isinstance(e.get("model_file"), str) else None,
                        buffer_file=e.get("buffer_file") if isinstance(e.get("buffer_file"), str) else None,
                        model_sha256=e.get("model_sha256") if isinstance(e.get("model_sha256"), str) else None,
                        buffer_sha256=e.get("buffer_sha256") if isinstance(e.get("buffer_sha256"), str) else None,
                    )
                )
            except Exception:
                continue
        return metas

    def get_active_version_id(self) -> int:
        data = self._load()
        try:
            return int(data.get("active_version_id", 0) or 0)
        except Exception:
            return 0

    def get_active_entry(self) -> Optional[Dict[str, Any]]:
        vid = self.get_active_version_id()
        if vid <= 0:
            return None
        return self.get(vid)

    def get(self, version_id: int) -> Optional[Dict[str, Any]]:
        data = self._load()
        for e in (data.get("history") or []):
            if not isinstance(e, dict):
                continue
            if int(e.get("version_id", -1)) == int(version_id):
                return e
        return None

    def _next_id(self) -> int:
        data = self._load()
        return int(data.get("current_version_id", 0) or 0) + 1

    def create_version(
        self,
        *,
        algorithm: str,
        active_model_path: Optional[str],
        active_buffer_path: Optional[str],
        status: str = "candidate",
        label: str = "",
        rationale: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data = self._load()
        version_id = int(data.get("current_version_id", 0) or 0) + 1
        timestamp = datetime.now(timezone.utc).isoformat()

        artifact_dir = self.archive_dir / f"v{version_id:06d}"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        model_file = None
        model_sha = None
        if isinstance(active_model_path, str) and active_model_path:
            src = Path(active_model_path)
            if src.exists():
                dst = artifact_dir / "model.pt"
                _atomic_copy(src, dst)
                model_file = str(dst)
                model_sha = _sha256_file(dst)

        buffer_file = None
        buffer_sha = None
        if isinstance(active_buffer_path, str) and active_buffer_path:
            src = Path(active_buffer_path)
            if src.exists():
                dst = artifact_dir / "buffer.json"
                _atomic_copy(src, dst)
                buffer_file = str(dst)
                buffer_sha = _sha256_file(dst)

        entry: Dict[str, Any] = {
            "version_id": version_id,
            "timestamp": timestamp,
            "status": status,
            "algorithm": algorithm,
            "label": label or "",
            "rationale": rationale or "",
            "artifact_dir": str(artifact_dir),
            "model_file": model_file,
            "buffer_file": buffer_file,
            "model_sha256": model_sha,
            "buffer_sha256": buffer_sha,
        }
        if isinstance(extra, dict) and extra:
            entry["extra"] = extra

        history = [e for e in (data.get("history") or []) if isinstance(e, dict)]
        history.append(entry)
        history = history[-self.max_history :]
        out = {
            "current_version_id": version_id,
            "active_version_id": int(data.get("active_version_id", 0) or 0),
            "history": history,
            "last_updated": timestamp,
        }
        self._save(out)
        return entry

    def set_active(self, version_id: int) -> Tuple[bool, Optional[str]]:
        data = self._load()
        vid = int(version_id)
        if self.get(vid) is None:
            return False, "version_not_found"
        prev = int(data.get("active_version_id", 0) or 0)
        history = [e for e in (data.get("history") or []) if isinstance(e, dict)]
        for e in history:
            try:
                if int(e.get("version_id", -1)) == vid:
                    e["status"] = "active"
                elif prev > 0 and int(e.get("version_id", -1)) == prev and e.get("status") == "active":
                    e["status"] = "archived"
            except Exception:
                continue
        data["active_version_id"] = vid
        data["history"] = history
        self._save(data)
        return True, None

    def restore_to_active_paths(
        self,
        *,
        version_id: int,
        active_model_path: Optional[str],
        active_buffer_path: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        entry = self.get(int(version_id))
        if entry is None:
            return False, "version_not_found"
        if isinstance(active_model_path, str) and active_model_path:
            src = entry.get("model_file")
            if isinstance(src, str) and src:
                _atomic_copy(Path(src), Path(active_model_path))
            elif Path(active_model_path).exists():
                # Version doesn't have model, but active has one; keep existing.
                pass
            else:
                return False, "model_missing"
        if isinstance(active_buffer_path, str) and active_buffer_path:
            src = entry.get("buffer_file")
            if isinstance(src, str) and src:
                _atomic_copy(Path(src), Path(active_buffer_path))
            elif Path(active_buffer_path).exists():
                pass
            else:
                return False, "buffer_missing"
        return True, None
