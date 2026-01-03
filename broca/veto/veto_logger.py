from __future__ import annotations

import csv
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .guard import VetoDecision


DEFAULT_VETO_LOG_FILE = "data/rl/veto_guard.csv"


class VetoGuardCSVLogger:
    def __init__(self, *, enabled: bool = True, log_file: str = DEFAULT_VETO_LOG_FILE, append: bool = True) -> None:
        self.enabled = bool(enabled)
        self.log_file = Path(str(log_file))
        self.append = bool(append)
        self._lock = threading.Lock()
        self._header_written = False

        # Stable schema for analysis
        self._fields = [
            "timestamp",
            "event",
            "reason",
            "tool_name",
            "tool_call_id",
            "turn_no",
            "iteration",
            "kappa",
            "kappa_integrated",
            "threshold",
            "violation",
            "veto_active",
            "state_changed",
            "persist_n",
            "persist_m",
            "violations_count",
            "clear_k",
            "clear_count",
            "hysteresis_h",
            "mu",
            "sigma",
            "margin",
            "trained",
            "train_loss",
        ]

    def _ensure_header(self, writer: csv.DictWriter) -> None:
        if self._header_written:
            return
        if self.log_file.exists() and self.log_file.stat().st_size > 0 and self.append:
            self._header_written = True
            return
        writer.writeheader()
        self._header_written = True

    def log_decision(
        self,
        decision: VetoDecision,
        *,
        event: str,
        tool_name: str = "",
        tool_call_id: str = "",
        turn_no: Optional[int] = None,
        iteration: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return
        ts = timestamp or datetime.now(timezone.utc).isoformat()

        dbg = decision.debug if isinstance(decision.debug, dict) else {}
        pred = dbg.get("pred") if isinstance(dbg.get("pred"), dict) else {}
        train = dbg.get("train") if isinstance(dbg.get("train"), dict) else {}

        violations_window = dbg.get("violations_window")
        violations_count = None
        try:
            if isinstance(violations_window, list):
                violations_count = int(sum(1 for v in violations_window if bool(v)))
        except Exception:
            violations_count = None

        row: Dict[str, Any] = {
            "timestamp": ts,
            "event": str(event),
            "reason": str(decision.reason),
            "tool_name": str(tool_name or ""),
            "tool_call_id": str(tool_call_id or ""),
            "turn_no": "" if turn_no is None else int(turn_no),
            "iteration": "" if iteration is None else int(iteration),
            "kappa": f"{float(decision.kappa_last):.8f}",
            "kappa_integrated": f"{float(decision.kappa_integrated):.8f}",
            "threshold": f"{float(decision.threshold):.8f}",
            "violation": bool(dbg.get("violation", False)),
            "veto_active": bool(decision.veto),
            "state_changed": bool(dbg.get("state_changed", False)),
            "persist_n": dbg.get("persist_n", ""),
            "persist_m": dbg.get("persist_m", ""),
            "violations_count": "" if violations_count is None else int(violations_count),
            "clear_k": dbg.get("clear_k", ""),
            "clear_count": dbg.get("clear_count", ""),
            "hysteresis_h": dbg.get("hysteresis_h", ""),
            "mu": pred.get("mu", ""),
            "sigma": pred.get("sigma", ""),
            "margin": pred.get("margin", ""),
            "trained": bool(train.get("trained", False)),
            "train_loss": train.get("loss", ""),
        }

        with self._lock:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if self.append else "w"
            with self.log_file.open(mode, encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self._fields, extrasaction="ignore")
                self._ensure_header(writer)
                writer.writerow(row)


_global_logger: Optional[VetoGuardCSVLogger] = None
_global_sig: Optional[tuple[bool, str, bool]] = None


def get_veto_csv_logger() -> VetoGuardCSVLogger:
    global _global_logger
    global _global_sig

    enabled = os.getenv("BROCA_VETO_LOG_ENABLED", "true").lower() == "true"
    log_file = os.getenv("BROCA_VETO_LOG_FILE", DEFAULT_VETO_LOG_FILE)
    append = os.getenv("BROCA_VETO_LOG_APPEND", "true").lower() == "true"
    sig = (bool(enabled), str(log_file), bool(append))

    if _global_logger is None or _global_sig != sig:
        _global_logger = VetoGuardCSVLogger(enabled=bool(enabled), log_file=str(log_file), append=bool(append))
        _global_sig = sig
    return _global_logger


