"""
Lightweight online learning for memory priming.

This module keeps a compact per-(mode, namespace) preference that can be used to
slightly boost/penalize candidates during priming selection, based on whether the
primed memory appears to have been used in the assistant response.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict, Optional


def _clamp(x: float, lo: float, hi: float) -> float:
    try:
        xf = float(x)
    except Exception:
        xf = 0.0
    return max(lo, min(hi, xf))


@dataclass
class NamespacePolicy:
    boost: float = 1.0
    n: int = 0


class PrimingPolicyStore:
    """
    Persisted, compact policy store for priming.

    - mode: "chat" or "thought"
    - namespace: memory namespace string (fallback "*")
    - boost: multiplicative factor applied to candidate relevance
    """

    def __init__(
        self,
        *,
        path: str | os.PathLike[str] = "data/priming_policy.json",
        lr: float = 0.10,
        min_boost: float = 0.50,
        max_boost: float = 1.50,
    ) -> None:
        self.path = Path(path)
        self.lr = float(lr)
        self.min_boost = float(min_boost)
        self.max_boost = float(max_boost)
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {"version": 1, "modes": {}}
        self.load()

    def load(self) -> None:
        with self._lock:
            try:
                if not self.path.exists():
                    return
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and raw.get("version") == 1:
                    self._data = raw
            except Exception:
                # Fail open: keep defaults.
                return

    def save(self) -> None:
        with self._lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.path.with_suffix(self.path.suffix + ".tmp")
                tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                os.replace(tmp, self.path)
            except Exception:
                return

    def _get_ns_entry(self, *, mode: str, namespace: str) -> Dict[str, Any]:
        m = str(mode or "chat")
        ns = str(namespace or "*") or "*"
        modes = self._data.setdefault("modes", {})
        mode_obj = modes.setdefault(m, {})
        ns_map = mode_obj.setdefault("namespaces", {})
        entry = ns_map.setdefault(ns, {"boost": 1.0, "n": 0})
        if not isinstance(entry, dict):
            entry = {"boost": 1.0, "n": 0}
            ns_map[ns] = entry
        return entry

    def get_boost(self, *, mode: str, namespace: Optional[str]) -> float:
        with self._lock:
            entry = self._get_ns_entry(mode=mode, namespace=str(namespace or "*"))
            try:
                return _clamp(float(entry.get("boost", 1.0) or 1.0), self.min_boost, self.max_boost)
            except Exception:
                return 1.0

    def update(self, *, mode: str, namespace: Optional[str], used_score: float) -> float:
        """
        Update and return the new boost.

        used_score is expected in [0, 1], where >0.5 indicates "helpful/used".
        """
        with self._lock:
            entry = self._get_ns_entry(mode=mode, namespace=str(namespace or "*"))
            cur = _clamp(float(entry.get("boost", 1.0) or 1.0), self.min_boost, self.max_boost)
            n = int(entry.get("n", 0) or 0)

            # Simple online update: push boost up if used_score>0.5, down if <0.5.
            delta = _clamp(float(used_score) - 0.5, -0.5, 0.5)
            lr = max(0.0, float(self.lr))
            new_boost = _clamp(cur + lr * delta, self.min_boost, self.max_boost)

            entry["boost"] = float(new_boost)
            entry["n"] = int(n + 1)
            return float(new_boost)


