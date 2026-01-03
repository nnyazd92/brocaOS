"""
Thread-safe CSV logger for kappa_proxy(t).

Univariate time series:
  timestamp,kappa
"""

from __future__ import annotations

import csv
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DEFAULT_KAPPA_LOG_FILE = "data/rl/kappa_series.csv"


class KappaSeriesLogger:
    def __init__(self, *, enabled: bool = True, log_file: str = DEFAULT_KAPPA_LOG_FILE, append: bool = True) -> None:
        self.enabled = bool(enabled)
        self.log_file = Path(str(log_file))
        self.append = bool(append)
        self._lock = threading.Lock()
        self._header_written = False

    def _ensure_header(self, writer: csv.DictWriter) -> None:
        if self._header_written:
            return
        if self.log_file.exists() and self.log_file.stat().st_size > 0 and self.append:
            self._header_written = True
            return
        writer.writeheader()
        self._header_written = True

    def log_kappa(self, kappa_value: float, *, timestamp: Optional[str] = None) -> None:
        if not self.enabled:
            return
        try:
            kv = float(kappa_value)
        except Exception:
            return
        if kv != kv:
            return
        if kv == float("inf") or kv == float("-inf"):
            return
        kv = max(0.0, min(1.0, kv))

        ts = timestamp or datetime.now(timezone.utc).isoformat()
        payload = {"timestamp": ts, "kappa": f"{kv:.8f}"}

        with self._lock:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if self.append else "w"
            with self.log_file.open(mode, encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "kappa"], extrasaction="ignore")
                self._ensure_header(writer)
                writer.writerow(payload)


_global_logger: Optional[KappaSeriesLogger] = None
_global_sig: Optional[tuple[bool, str, bool]] = None


def get_kappa_series_logger() -> KappaSeriesLogger:
    global _global_logger
    global _global_sig

    enabled = os.getenv("BROCA_KAPPA_LOG_ENABLED", "true").lower() == "true"
    log_file = os.getenv("BROCA_KAPPA_LOG_FILE", DEFAULT_KAPPA_LOG_FILE)
    append = os.getenv("BROCA_KAPPA_LOG_APPEND", "true").lower() == "true"
    sig = (bool(enabled), str(log_file), bool(append))

    if _global_logger is None or _global_sig != sig:
        _global_logger = KappaSeriesLogger(enabled=bool(enabled), log_file=str(log_file), append=bool(append))
        _global_sig = sig
    return _global_logger


