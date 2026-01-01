"""
Apply the currently active policy version on startup.

This makes policy promotion/rollback restart-safe and consistent across:
- main_repl.py
- main_repl_runtime.py (web_api.py)
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..config import config
from .policy_versions import PolicyVersionStore


def _sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    h = sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _active_paths_for_algorithm(algorithm: str) -> tuple[str, str]:
    if algorithm == "ppo":
        return str(config.rl.ppo_model_path), str(config.rl.ppo_buffer_path)
    return str(config.rl.model_path), str(config.rl.buffer_path)


def apply_active_policy_version(*, runtime_algorithm: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    If an active policy version exists, restore its artifacts into the active model/buffer paths.

    Returns:
        (applied, info)
    """
    algo = (runtime_algorithm or getattr(config.rl, "algorithm", "online_nn") or "online_nn").strip().lower()
    store = PolicyVersionStore(
        store_path=str(getattr(config.rl, "policy_versions_path", "data/rl/policy_versions.json")),
        archive_dir=str(getattr(config.rl, "policy_archive_dir", "models/rl/policy_versions")),
    )

    entry = store.get_active_entry()
    if entry is None:
        return False, {"reason": "no_active_version"}

    entry_algo = str(entry.get("algorithm", "") or "").strip().lower() or "unknown"
    # Only apply if it matches the currently configured algorithm (avoid surprising cross-algo restores).
    if entry_algo != algo:
        return False, {"reason": "algorithm_mismatch", "active_algorithm": entry_algo, "runtime_algorithm": algo}

    model_path, buffer_path = _active_paths_for_algorithm(algo)

    before: Dict[str, Any] = {}
    try:
        mp = Path(model_path)
        if mp.exists():
            before["model_sha256"] = _sha256_file(mp)
    except Exception:
        pass
    try:
        bp = Path(buffer_path)
        if bp.exists():
            before["buffer_sha256"] = _sha256_file(bp)
    except Exception:
        pass

    ok, err = store.restore_to_active_paths(version_id=int(entry.get("version_id", 0) or 0), active_model_path=model_path, active_buffer_path=buffer_path)
    if not ok:
        return False, {"reason": "restore_failed", "error": err, "version_id": entry.get("version_id"), "algorithm": algo}

    after: Dict[str, Any] = {}
    try:
        mp = Path(model_path)
        if mp.exists():
            after["model_sha256"] = _sha256_file(mp)
    except Exception:
        pass
    try:
        bp = Path(buffer_path)
        if bp.exists():
            after["buffer_sha256"] = _sha256_file(bp)
    except Exception:
        pass

    changed = {
        k: {"before": before.get(k), "after": after.get(k)}
        for k in set(before.keys()) | set(after.keys())
        if before.get(k) != after.get(k)
    }

    return True, {
        "version_id": int(entry.get("version_id", 0) or 0),
        "algorithm": algo,
        "model_path": model_path,
        "buffer_path": buffer_path,
        "changed": changed,
    }

