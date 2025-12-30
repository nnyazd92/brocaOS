"""
RL Reward Logger for CSV logging of reward signals.

Logs all RL reward signals to CSV for pandas/matplotlib analysis.
"""

from __future__ import annotations

import csv
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import shutil
import tempfile

logger = logging.getLogger(__name__)


class RLRewardLogger:
    """
    Thread-safe CSV logger for RL reward signals.
    
    Logs reward values, weights, and metadata to CSV file for analysis.
    """
    
    def __init__(
        self,
        log_file: str = "data/rl_rewards.csv",
        enabled: bool = True,
        append: bool = True
    ):
        """
        Initialize RL reward logger.
        
        Args:
            log_file: Path to CSV file for logging
            enabled: Whether logging is enabled
            append: Whether to append to existing file (True) or overwrite (False)
        """
        self.log_file = Path(log_file)
        self.enabled = enabled
        self.append = append
        self._lock = threading.Lock()
        self._header_written = False
        self._total_entries = 0
        self._last_summary_time = time.time()
        self._summary_interval = 300  # Log summary every 5 minutes

        # CSV schema (v4 adds epistemic uncertainty fields; v3 already includes per-signal missingness/estimator/uncertainty)
        self.schema_version = 4
        self._fieldnames_v4 = [
            # v1 fields
            "timestamp",
            "dissonance_reward",
            "surprise_reward",
            "curiosity_reward",
            "information_gain_reward",
            "coherence_reward",
            "composite_reward",
            "exploration_balance",
            "weight_dissonance",
            "weight_surprise",
            "weight_curiosity",
            "weight_info_gain",
            "weight_coherence",
            "context",
            # v2+ additions
            "schema_version",
            "dissonance_raw",
            "has_dissonance_data",
            "dissonance_estimator",
            "dissonance_uncertainty",
            "raw_surprise",
            "surprise_short_term",
            "surprise_long_term",
            "prediction_error_raw",
            "prediction_error_recent_avg",
            "calibrated_surprise",
            "surprise_source",
            "surprise_has_data",
            "surprise_data_quality",
            "surprise_estimator",
            "surprise_uncertainty",
            "curiosity_raw",
            "curiosity_has_data",
            "curiosity_data_quality",
            "curiosity_estimator",
            "curiosity_uncertainty",
            "coherence_raw",
            "coherence_has_data",
            "coherence_data_quality",
            "coherence_estimator",
            "coherence_uncertainty",
            "info_gain_raw",
            "info_gain_source",
            "info_gain_has_data",
            "info_gain_estimator",
            "info_gain_uncertainty",

            # v4: epistemic uncertainty (separate from measurement uncertainty)
            "epistemic_uncertainty_total",
            "epistemic_uncertainty_epistemic",
            "epistemic_uncertainty_aleatoric",
            "epistemic_uncertainty_model",
            "epistemic_uncertainty_data_quality",
            "epistemic_uncertainty_sample_size",
            "epistemic_uncertainty_has_data",
        ]
        
        # Statistics tracking
        self._stats = {
            "total_entries": 0,
            "composite_reward_sum": 0.0,
            "composite_reward_min": float('inf'),
            "composite_reward_max": float('-inf'),
            "dissonance_reward_sum": 0.0,
            "surprise_reward_sum": 0.0,
            "curiosity_reward_sum": 0.0,
        }
        
        # Ensure directory exists
        if self.enabled:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # If appending to an existing file, ensure schema compatibility WITHOUT truncation.
            # If the header is older/different, perform an in-place migration:
            # - backup the original once
            # - rewrite with the new superset header
            # - preserve all existing rows (missing columns => blank)
            if self.log_file.exists() and self.append:
                self._maybe_migrate_schema_in_place()

            # Check if file exists and has header, count existing entries
            if self.log_file.exists() and self.append:
                try:
                    with open(self.log_file, 'r') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if rows:
                            self._header_written = True
                            self._total_entries = len(rows)
                            # Initialize stats from existing file
                            self._stats["total_entries"] = len(rows)
                            for row in rows:
                                try:
                                    comp_reward = float(row.get("composite_reward", 0))
                                    self._stats["composite_reward_sum"] += comp_reward
                                    self._stats["composite_reward_min"] = min(self._stats["composite_reward_min"], comp_reward)
                                    self._stats["composite_reward_max"] = max(self._stats["composite_reward_max"], comp_reward)
                                except (ValueError, KeyError):
                                    pass
                except Exception:
                    # File exists but might be empty or corrupted
                    self._header_written = False
        
        # Log file path and initial status
        file_size = self.log_file.stat().st_size if self.log_file.exists() else 0
        logger.info(
            f"Initialized RLRewardLogger: enabled={enabled}, file={self.log_file.absolute()}, "
            f"append={append}, existing_entries={self._total_entries}, file_size={file_size} bytes",
            extra={
                "event": "rl_reward_logger_initialized",
                "enabled": enabled,
                "log_file": str(self.log_file.absolute()),
                "append": append,
                "existing_entries": self._total_entries,
                "file_size_bytes": file_size,
            }
        )
    
    def log_reward_signals(
        self,
        rl_metrics: Any,
        context: Optional[str] = None
    ) -> None:
        """
        Log RL reward signals to CSV.
        
        Args:
            rl_metrics: RLSignalMetrics object with reward values and weights
            context: Optional context string (e.g., endpoint name, conversation_id)
        """
        if not self.enabled:
            return
        
        # Guard: Reject test context patterns
        if context and (context.startswith("tool_call_test_") or "test_tool" in context):
            logger.debug(f"Skipping test data log entry: {context}")
            return
        
        try:
            ts = datetime.now(timezone.utc).isoformat()

            # Extract reward values (v2 schema)
            row = {
                "timestamp": ts,
                "dissonance_reward": round(float(getattr(rl_metrics, "dissonance_reward", 0.0)), 6),
                "surprise_reward": round(float(getattr(rl_metrics, "surprise_reward", 0.0)), 6),
                "curiosity_reward": round(float(getattr(rl_metrics, "curiosity_reward", 0.0)), 6),
                "information_gain_reward": round(float(getattr(rl_metrics, "information_gain_reward", 0.0)), 6),
                "coherence_reward": round(float(getattr(rl_metrics, "coherence_reward", 0.0)), 6),
                "composite_reward": round(float(getattr(rl_metrics, "composite_reward", 0.0)), 6),
                "exploration_balance": round(float(rl_metrics.get_exploration_exploitation_balance()), 6),
                "weight_dissonance": round(float(getattr(rl_metrics, "weight_dissonance", 0.0)), 6),
                "weight_surprise": round(float(getattr(rl_metrics, "weight_surprise", 0.0)), 6),
                "weight_curiosity": round(float(getattr(rl_metrics, "weight_curiosity", 0.0)), 6),
                "weight_info_gain": round(float(getattr(rl_metrics, "weight_info_gain", 0.0)), 6),
                "weight_coherence": round(float(getattr(rl_metrics, "weight_coherence", 0.0)), 6),
                "context": context or "",

                "schema_version": int(getattr(rl_metrics, "schema_version", self.schema_version)),
                "dissonance_raw": getattr(rl_metrics, "dissonance_raw", None),
                "has_dissonance_data": getattr(rl_metrics, "has_dissonance_data", None),
                "dissonance_estimator": getattr(rl_metrics, "dissonance_estimator", None),
                "dissonance_uncertainty": getattr(rl_metrics, "dissonance_uncertainty", None),
                "raw_surprise": getattr(rl_metrics, "raw_surprise", None),
                "surprise_short_term": getattr(rl_metrics, "surprise_short_term", None),
                "surprise_long_term": getattr(rl_metrics, "surprise_long_term", None),
                "prediction_error_raw": getattr(rl_metrics, "prediction_error_raw", None),
                "prediction_error_recent_avg": getattr(rl_metrics, "prediction_error_recent_avg", None),
                "calibrated_surprise": getattr(rl_metrics, "calibrated_surprise", None),
                "surprise_source": getattr(rl_metrics, "surprise_source", None),
                "surprise_has_data": getattr(rl_metrics, "surprise_has_data", None),
                "surprise_data_quality": getattr(rl_metrics, "surprise_data_quality", None),
                "surprise_estimator": getattr(rl_metrics, "surprise_estimator", None),
                "surprise_uncertainty": getattr(rl_metrics, "surprise_uncertainty", None),
                "curiosity_raw": getattr(rl_metrics, "curiosity_raw", None),
                "curiosity_has_data": getattr(rl_metrics, "curiosity_has_data", None),
                "curiosity_data_quality": getattr(rl_metrics, "curiosity_data_quality", None),
                "curiosity_estimator": getattr(rl_metrics, "curiosity_estimator", None),
                "curiosity_uncertainty": getattr(rl_metrics, "curiosity_uncertainty", None),
                "coherence_raw": getattr(rl_metrics, "coherence_raw", None),
                "coherence_has_data": getattr(rl_metrics, "coherence_has_data", None),
                "coherence_data_quality": getattr(rl_metrics, "coherence_data_quality", None),
                "coherence_estimator": getattr(rl_metrics, "coherence_estimator", None),
                "coherence_uncertainty": getattr(rl_metrics, "coherence_uncertainty", None),
                "info_gain_raw": getattr(rl_metrics, "info_gain_raw", None),
                "info_gain_source": getattr(rl_metrics, "info_gain_source", None),
                "info_gain_has_data": getattr(rl_metrics, "info_gain_has_data", None),
                "info_gain_estimator": getattr(rl_metrics, "info_gain_estimator", None),
                "info_gain_uncertainty": getattr(rl_metrics, "info_gain_uncertainty", None),

                "epistemic_uncertainty_total": getattr(rl_metrics, "epistemic_uncertainty_total", None),
                "epistemic_uncertainty_epistemic": getattr(rl_metrics, "epistemic_uncertainty_epistemic", None),
                "epistemic_uncertainty_aleatoric": getattr(rl_metrics, "epistemic_uncertainty_aleatoric", None),
                "epistemic_uncertainty_model": getattr(rl_metrics, "epistemic_uncertainty_model", None),
                "epistemic_uncertainty_data_quality": getattr(rl_metrics, "epistemic_uncertainty_data_quality", None),
                "epistemic_uncertainty_sample_size": getattr(rl_metrics, "epistemic_uncertainty_sample_size", None),
                "epistemic_uncertainty_has_data": getattr(rl_metrics, "epistemic_uncertainty_has_data", None),
            }
            
            # Write to CSV (thread-safe)
            with self._lock:
                file_exists = self.log_file.exists()
                write_header = not self._header_written and (not file_exists or not self.append)
                
                mode = "a" if (self.append and file_exists) else "w"
                with open(self.log_file, mode, newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=self._fieldnames_v4)
                    
                    if write_header:
                        writer.writeheader()
                        self._header_written = True
                    
                    writer.writerow(row)
                
                # Update statistics
                self._total_entries += 1
                self._stats["total_entries"] = self._total_entries
                composite = row["composite_reward"]
                self._stats["composite_reward_sum"] += composite
                self._stats["composite_reward_min"] = min(self._stats["composite_reward_min"], composite)
                self._stats["composite_reward_max"] = max(self._stats["composite_reward_max"], composite)
                self._stats["dissonance_reward_sum"] += row["dissonance_reward"]
                self._stats["surprise_reward_sum"] += row["surprise_reward"]
                self._stats["curiosity_reward_sum"] += row["curiosity_reward"]
                
                # Log at INFO level with full details
                file_size = self.log_file.stat().st_size if self.log_file.exists() else 0
                logger.info(
                    f"Logged RL reward signals: composite={composite:.4f}, "
                    f"dissonance={row['dissonance_reward']:.4f}, surprise={row['surprise_reward']:.4f}, "
                    f"curiosity={row['curiosity_reward']:.4f}, context={context}, "
                    f"file={self.log_file.name}, entries={self._total_entries}, size={file_size} bytes",
                    extra={
                        "event": "rl_reward_logged",
                        "composite_reward": composite,
                        "dissonance_reward": row["dissonance_reward"],
                        "surprise_reward": row["surprise_reward"],
                        "curiosity_reward": row["curiosity_reward"],
                        "information_gain_reward": row["information_gain_reward"],
                        "coherence_reward": row["coherence_reward"],
                        "exploration_balance": row["exploration_balance"],
                        "context": context,
                        "log_file": str(self.log_file.absolute()),
                        "total_entries": self._total_entries,
                        "file_size_bytes": file_size,
                    }
                )
                
                # Periodic summary logging
                current_time = time.time()
                if current_time - self._last_summary_time >= self._summary_interval:
                    self._log_summary()
                    self._last_summary_time = current_time
                
        except Exception as e:
            logger.warning(
                f"Failed to log RL reward signals: {e}",
                exc_info=True,
                extra={
                    "event": "rl_reward_log_error",
                    "log_file": str(self.log_file.absolute()),
                    "total_entries": self._total_entries,
                }
            )

    def _maybe_migrate_schema_in_place(self) -> None:
        """
        Ensure rl_rewards.csv always remains a single central append-only dataset.

        If the existing header differs from the current schema, we perform an in-place migration that:
        - preserves ALL existing rows
        - writes the new header (superset)
        - fills missing columns with blanks
        - keeps a backup copy of the pre-migration file
        """
        try:
            if not self.log_file.exists():
                return
            with open(self.log_file, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
            if not first_row:
                return

            # Detect a headerless file that is already in "v3 positional" format (data rows only).
            # This can happen if an earlier bug or manual edit wrote rows without a header.
            # Heuristic:
            # - first cell looks like an ISO timestamp
            # - number of columns matches current schema
            # - does not contain the literal "timestamp" header token
            def _looks_like_iso_ts(s: str) -> bool:
                if not isinstance(s, str):
                    return False
                # Lightweight, safe heuristic (no regex): "YYYY-" and "T" must exist.
                return len(s) >= 10 and s[4:5] == "-" and "T" in s

            is_headerless_current = (
                ("timestamp" not in [c.strip() for c in first_row if isinstance(c, str)])
                and len(first_row) == len(self._fieldnames_v4)
                and _looks_like_iso_ts(str(first_row[0]))
            )

            # Normal headered case
            if not is_headerless_current and list(first_row) == self._fieldnames_v4:
                return

            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = self.log_file.with_name(f"{self.log_file.stem}.schema_backup.{ts}{self.log_file.suffix}")
            shutil.copy2(self.log_file, backup_path)

            if is_headerless_current:
                # Read all rows positionally and re-emit with proper header
                with open(self.log_file, "r", encoding="utf-8", newline="") as f:
                    r = csv.reader(f)
                    positional_rows = list(r)

                with tempfile.NamedTemporaryFile(
                    mode="w",
                    newline="",
                    encoding="utf-8",
                    dir=str(self.log_file.parent),
                    delete=False,
                    prefix=f".{self.log_file.stem}.",
                    suffix=".tmp",
                ) as tf:
                    tmp_path = Path(tf.name)
                    writer = csv.DictWriter(tf, fieldnames=self._fieldnames_v4)
                    writer.writeheader()
                    for prow in positional_rows:
                        if len(prow) != len(self._fieldnames_v4):
                            # Skip malformed trailing blank lines
                            if len([c for c in prow if str(c).strip()]) == 0:
                                continue
                            raise ValueError(
                                f"Headerless rewards file has row with {len(prow)} cols; expected {len(self._fieldnames_v4)}"
                            )
                        out = {k: prow[i] for i, k in enumerate(self._fieldnames_v4)}
                        writer.writerow(out)

                tmp_path.replace(self.log_file)
                self._header_written = True
                logger.warning(
                    f"Repaired headerless RL rewards CSV (added header, preserved rows). "
                    f"Backup: {backup_path.absolute()} Current: {self.log_file.absolute()}"
                )
                return

            # Read all existing rows with the old header
            with open(self.log_file, "r", encoding="utf-8", newline="") as f:
                old_reader = csv.DictReader(f)
                old_rows = list(old_reader)
                old_fieldnames = list(old_reader.fieldnames or first_row)

            # Write migrated file to a temp path in same directory (atomic replace)
            with tempfile.NamedTemporaryFile(
                mode="w",
                newline="",
                encoding="utf-8",
                dir=str(self.log_file.parent),
                delete=False,
                prefix=f".{self.log_file.stem}.",
                suffix=".tmp",
            ) as tf:
                tmp_path = Path(tf.name)
                writer = csv.DictWriter(tf, fieldnames=self._fieldnames_v4)
                writer.writeheader()

                for r in old_rows:
                    out = {k: "" for k in self._fieldnames_v4}
                    for k in old_fieldnames:
                        if k in out:
                            out[k] = r.get(k, "")
                    writer.writerow(out)

            tmp_path.replace(self.log_file)
            self._header_written = True
            logger.warning(
                f"Migrated RL rewards CSV schema in place (preserved rows). "
                f"Backup: {backup_path.absolute()} Current: {self.log_file.absolute()}"
            )
        except Exception as e:
            logger.warning(f"Failed RL rewards CSV in-place schema migration: {e}", exc_info=True)
    
    def _log_summary(self) -> None:
        """Log periodic summary statistics."""
        if self._stats["total_entries"] == 0:
            return
        
        avg_composite = self._stats["composite_reward_sum"] / self._stats["total_entries"]
        avg_dissonance = self._stats["dissonance_reward_sum"] / self._stats["total_entries"]
        avg_surprise = self._stats["surprise_reward_sum"] / self._stats["total_entries"]
        avg_curiosity = self._stats["curiosity_reward_sum"] / self._stats["total_entries"]
        
        file_size = self.log_file.stat().st_size if self.log_file.exists() else 0
        
        logger.info(
            f"RL Reward Logger Summary: entries={self._stats['total_entries']}, "
            f"avg_composite={avg_composite:.4f} (min={self._stats['composite_reward_min']:.4f}, "
            f"max={self._stats['composite_reward_max']:.4f}), "
            f"avg_dissonance={avg_dissonance:.4f}, avg_surprise={avg_surprise:.4f}, "
            f"avg_curiosity={avg_curiosity:.4f}, file_size={file_size} bytes",
            extra={
                "event": "rl_reward_logger_summary",
                "total_entries": self._stats["total_entries"],
                "avg_composite_reward": avg_composite,
                "min_composite_reward": self._stats["composite_reward_min"],
                "max_composite_reward": self._stats["composite_reward_max"],
                "avg_dissonance_reward": avg_dissonance,
                "avg_surprise_reward": avg_surprise,
                "avg_curiosity_reward": avg_curiosity,
                "file_size_bytes": file_size,
                "log_file": str(self.log_file.absolute()),
            }
        )

