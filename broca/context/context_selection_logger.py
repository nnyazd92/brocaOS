"""
Context selection telemetry logger.

Writes a per-message row describing why each message was kept/dropped for an LLM call.
This is useful both for debugging \"agent weirdness\" and as future RL training data
for a learned pruning policy.
"""

from __future__ import annotations

import csv
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Iterable, Optional

logger = logging.getLogger(__name__)


class ContextSelectionLogger:
    def __init__(self, log_file: str = "data/context_selection.csv", enabled: bool = False, append: bool = True):
        self.log_file = Path(log_file)
        self.enabled = enabled
        self.append = append
        self._lock = threading.Lock()
        self._header_written = False
        self._fieldnames = [
            "timestamp",
            "run_id",
            "message_id",
            "role",
            "token_count",
            "kept",
            "kept_reason",
            "tool_chain_id",
            "is_summary",
            "is_compacted",
        ]

        if self.enabled:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, *, run_id: str, rows: Iterable[Dict[str, Any]]) -> None:
        if not self.enabled:
            return

        ts = datetime.now(timezone.utc).isoformat()
        with self._lock:
            file_exists = self.log_file.exists()
            mode = "a" if (self.append and file_exists) else "w"
            with self.log_file.open(mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._fieldnames)
                if not file_exists or mode == "w" or not self._header_written:
                    writer.writeheader()
                    self._header_written = True
                for row in rows:
                    out = {
                        "timestamp": ts,
                        "run_id": run_id,
                        "message_id": row.get("message_id", ""),
                        "role": row.get("role", ""),
                        "token_count": row.get("token_count", ""),
                        "kept": row.get("kept", ""),
                        "kept_reason": row.get("kept_reason", ""),
                        "tool_chain_id": row.get("tool_chain_id", ""),
                        "is_summary": row.get("is_summary", ""),
                        "is_compacted": row.get("is_compacted", ""),
                    }
                    writer.writerow(out)
        logger.debug(f"ContextSelectionLogger wrote rows for run_id={run_id}")


