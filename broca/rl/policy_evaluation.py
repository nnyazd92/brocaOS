"""
Policy evaluation persistence.

EVALUATE_POLICY computes simple, auditable metrics over the current policy's
experience buffer and optionally persists those reports for regression tracking.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


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


class PolicyEvaluationStore:
    def __init__(self, path: str, *, max_history: int = 200) -> None:
        self.path = Path(path)
        self.max_history = max(1, int(max_history))

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"history": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"history": []}
        if not isinstance(data, dict):
            return {"history": []}
        history = data.get("history")
        if not isinstance(history, list):
            history = []
        return {"history": history}

    def append(self, report: Dict[str, Any]) -> None:
        data = self._load()
        hist = [e for e in (data.get("history") or []) if isinstance(e, dict)]
        hist.append(report)
        hist = hist[-self.max_history :]
        out = {"history": hist, "last_updated": datetime.now(timezone.utc).isoformat()}
        _atomic_write_json(self.path, out)

    def list(self, *, limit: int = 20) -> List[Dict[str, Any]]:
        data = self._load()
        hist = [e for e in (data.get("history") or []) if isinstance(e, dict)]
        return hist[-max(1, int(limit)) :]

