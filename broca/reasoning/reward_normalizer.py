"""
Running-variance normalization for RL reward components.

This module provides a small, stateful normalizer that:
- Tracks running mean/variance per key (Welford)
- Produces a variance-normalized z-score and a squashed [0,1] representation
- Persists statistics to disk so normalization survives restarts
"""

from __future__ import annotations

import json
import math
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass
class RunningMeanVar:
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, x: float) -> None:
        x = float(x)
        self.n += 1
        delta = x - self.mean
        self.mean += delta / float(self.n)
        delta2 = x - self.mean
        self.m2 += delta * delta2

    def variance(self) -> float:
        if self.n <= 1:
            return 0.0
        return max(0.0, self.m2 / float(self.n - 1))


class RewardVarianceNormalizer:
    """
    Running-variance normalizer for scalar reward components.

    Normalization:
    - z = (x - mean) / sqrt(var + eps)
    - z is clipped to [-z_clip, z_clip]
    - varnorm01 = 0.5 + 0.5 * tanh(z / squash)
    """

    def __init__(
        self,
        storage_path: str = "data/rl/reward_variance.json",
        *,
        enabled: bool = True,
        min_samples: int = 10,
        eps: float = 1e-6,
        z_clip: float = 5.0,
        squash: float = 2.0,
        persist_interval_s: float = 5.0,
    ) -> None:
        self.enabled = bool(enabled)
        self.storage_path = Path(storage_path)
        self.min_samples = max(1, int(min_samples))
        self.eps = float(eps)
        self.z_clip = float(z_clip)
        self.squash = float(squash)
        self.persist_interval_s = float(persist_interval_s)

        self._lock = threading.Lock()
        self._stats: Dict[str, RunningMeanVar] = {}
        self._last_persist_ts = 0.0

        if self.enabled:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_best_effort()

    def _load_best_effort(self) -> None:
        try:
            if not self.storage_path.exists():
                return
            data = json.loads(self.storage_path.read_text())
            if not isinstance(data, dict):
                return
            stats = data.get("stats")
            if not isinstance(stats, dict):
                return
            for k, v in stats.items():
                if not isinstance(k, str) or not isinstance(v, dict):
                    continue
                try:
                    rmv = RunningMeanVar(
                        n=int(v.get("n", 0) or 0),
                        mean=float(v.get("mean", 0.0) or 0.0),
                        m2=float(v.get("m2", 0.0) or 0.0),
                    )
                    if rmv.n >= 0:
                        self._stats[k] = rmv
                except Exception:
                    continue
        except Exception:
            return

    def _persist_best_effort(self) -> None:
        if not self.enabled:
            return
        now = time.time()
        if self.persist_interval_s > 0 and (now - self._last_persist_ts) < self.persist_interval_s:
            return
        self._last_persist_ts = now
        try:
            payload = {
                "schema_version": 1,
                "saved_at": now,
                "stats": {
                    k: {"n": v.n, "mean": v.mean, "m2": v.m2}
                    for k, v in self._stats.items()
                    if isinstance(k, str)
                },
            }
            tmp = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
            tmp.write_text(json.dumps(payload, sort_keys=True))
            tmp.replace(self.storage_path)
        except Exception:
            return

    def normalize(self, key: str, x: float) -> Tuple[float, float]:
        """
        Update running stats for `key` and return (z, varnorm01).

        varnorm01 is always in [0, 1]. When there are fewer than `min_samples`
        prior samples, returns a neutral 0.0 / 0.5 signal.
        """
        if not self.enabled:
            return 0.0, float(x)

        k = str(key)
        xv = float(x)

        with self._lock:
            rmv = self._stats.get(k) or RunningMeanVar()
            # Use pre-update stats to normalize this sample.
            n_prev = rmv.n
            mean_prev = rmv.mean
            var_prev = rmv.variance()
            std = math.sqrt(var_prev + self.eps)
            if n_prev < self.min_samples or std <= 0.0:
                z = 0.0
                varnorm01 = 0.5
            else:
                z = (xv - mean_prev) / std
                if self.z_clip > 0:
                    z = max(-self.z_clip, min(self.z_clip, z))
                denom = self.squash if self.squash != 0.0 else 1.0
                varnorm01 = 0.5 + 0.5 * math.tanh(z / denom)
                varnorm01 = max(0.0, min(1.0, float(varnorm01)))

            rmv.update(xv)
            self._stats[k] = rmv
            self._persist_best_effort()
            return float(z), float(varnorm01)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "enabled": self.enabled,
                "min_samples": self.min_samples,
                "eps": self.eps,
                "z_clip": self.z_clip,
                "squash": self.squash,
                "storage_path": str(self.storage_path),
                "stats": {k: {"n": v.n, "mean": v.mean, "m2": v.m2} for k, v in self._stats.items()},
            }

