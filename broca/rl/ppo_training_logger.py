"""
PPO training CSV logger for monitoring training health over time.

This is intentionally separate from tool_selection.log (human readable) and rl_rewards.csv
(per-tool-call reward signals). This file captures per-update PPO optimization metrics.
"""

from __future__ import annotations

import csv
import logging
import os
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


DEFAULT_PPO_TRAIN_LOG_FILE = "data/rl/ppo_training_metrics.csv"


class PPOTrainingLogger:
    """
    Thread-safe append-only CSV logger for PPO update metrics.

    The schema is stable and versioned. Old files are not automatically migrated (yet);
    consumers should treat schema_version as authoritative.
    """

    def __init__(
        self,
        log_file: str = DEFAULT_PPO_TRAIN_LOG_FILE,
        *,
        enabled: bool = True,
        append: bool = True,
    ) -> None:
        self.log_file = Path(log_file)
        self.enabled = bool(enabled)
        self.append = bool(append)
        self._lock = threading.Lock()
        self._header_written = False

        self.schema_version = 1
        self._fieldnames: List[str] = [
            "timestamp",
            "schema_version",
            "training_step",
            "n_experiences",
            "n_episodes",
            "mean_episode_return",
            "approx_kl",
            "clip_fraction",
            "policy_entropy",
            "policy_loss",
            "value_loss",
            "total_loss",
            "learning_rate",
            "clip_epsilon",
            "entropy_coef",
            "value_coef",
            "ppo_epochs",
            "configured_batch_size",
            "configured_buffer_size",
            "minibatch_size",
        ]

    @staticmethod
    def from_env() -> "PPOTrainingLogger":
        enabled = os.getenv("BROCA_RL_PPO_TRAIN_LOG_ENABLED", "true").lower() == "true"
        log_file = os.getenv("BROCA_RL_PPO_TRAIN_LOG_FILE", DEFAULT_PPO_TRAIN_LOG_FILE)
        append = os.getenv("BROCA_RL_PPO_TRAIN_LOG_APPEND", "true").lower() == "true"
        return PPOTrainingLogger(log_file=log_file, enabled=enabled, append=append)

    def _ensure_header(self, writer: csv.DictWriter) -> None:
        if self._header_written:
            return
        if self.log_file.exists() and self.log_file.stat().st_size > 0 and self.append:
            self._header_written = True
            return
        writer.writeheader()
        self._header_written = True

    def log_update(self, row: Dict[str, Any]) -> None:
        if not self.enabled:
            return

        payload = {k: row.get(k) for k in self._fieldnames}
        payload["timestamp"] = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
        payload["schema_version"] = int(payload.get("schema_version") or self.schema_version)

        with self._lock:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if self.append else "w"
            with self.log_file.open(mode, encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self._fieldnames, extrasaction="ignore")
                self._ensure_header(writer)
                writer.writerow(payload)


_global_logger: Optional[PPOTrainingLogger] = None
_global_logger_sig: Optional[tuple[bool, str, bool]] = None


def get_ppo_training_logger() -> PPOTrainingLogger:
    global _global_logger
    global _global_logger_sig

    # Allow env-driven reconfiguration (important for tests and for runtime toggles).
    enabled = os.getenv("BROCA_RL_PPO_TRAIN_LOG_ENABLED", "true").lower() == "true"
    log_file = os.getenv("BROCA_RL_PPO_TRAIN_LOG_FILE", DEFAULT_PPO_TRAIN_LOG_FILE)
    append = os.getenv("BROCA_RL_PPO_TRAIN_LOG_APPEND", "true").lower() == "true"
    sig = (bool(enabled), str(log_file), bool(append))

    if _global_logger is None or _global_logger_sig != sig:
        _global_logger = PPOTrainingLogger(log_file=str(log_file), enabled=bool(enabled), append=bool(append))
        _global_logger_sig = sig
        logger.info(
            f"Initialized PPOTrainingLogger: enabled={_global_logger.enabled}, "
            f"file={_global_logger.log_file.absolute()}"
        )
    return _global_logger
