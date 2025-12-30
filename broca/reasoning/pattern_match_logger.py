"""
CSV logging for LLM-based PatternMatcher batching.

Purpose:
- Produce training-ready datasets to later replace LLM-based pattern matching
  (e.g., contradiction detection) with a local encoder-decoder.
- Log both per-batch metadata and per-pair labels/confidence.
"""

from __future__ import annotations

import csv
import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import tempfile

logger = logging.getLogger(__name__)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _json_dumps_stable(obj: Any) -> str:
    import json
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def _truncate(s: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + f"...(truncated,{len(s)}chars)"


@dataclass
class PatternMatchLogConfig:
    enabled: bool
    base_path: Path
    rotation: str = "daily"  # "daily" | "size" | "none"
    max_size_mb: int = 100
    max_content_chars: int = 20_000  # raw JSON text per cell


class PatternMatchLogger:
    """
    Thread-safe logger that writes:
    - `<base>_batches.csv` (one row per LLM call)
    - `<base>_pairs.csv` (one row per (pattern,item) pair)
    """

    def __init__(self, cfg: PatternMatchLogConfig):
        self.cfg = cfg
        self._lock = threading.Lock()
        self._header_written_batches = False
        self._header_written_pairs = False
        self._batch_fieldnames = [
            "timestamp",
            "batch_id",
            "model",
            "num_pairs",
            "latency_ms",
            "cache_hits",
            "fallback_used",
            "parse_ok",
            "error_type",
            "prompt_chars",
            "response_chars",
            "prompt_hash",
            "response_hash",
            # Training-relevant content (truncated)
            "prompt_text_trunc",
            "response_text_trunc",
        ]
        self._pair_fieldnames = [
            "timestamp",
            "batch_id",
            "pair_index",
            "pattern_type",
            "match_label",
            "confidence",
            "cache_hit",
            "fallback_used",
            "llm_used",
            "parse_ok",
            "error_type",
            "context",
            "pattern_json",
            "item_json",
            "pattern_hash",
            "item_hash",
            # Explicit training IO
            "input_json",
            "output_json",
        ]

        if not self.cfg.enabled:
            return

        self.cfg.base_path.parent.mkdir(parents=True, exist_ok=True)

    def _paths(self) -> tuple[Path, Path]:
        base = self.cfg.base_path
        stem = base.stem
        suffix = base.suffix or ".csv"

        # Daily rotation: incorporate YYYY-MM-DD into filenames.
        if self.cfg.rotation == "daily":
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            batches = base.with_name(f"{stem}_{day}_batches{suffix}")
            pairs = base.with_name(f"{stem}_{day}_pairs{suffix}")
        else:
            batches = base.with_name(f"{stem}_batches{suffix}")
            pairs = base.with_name(f"{stem}_pairs{suffix}")

        return batches, pairs

    def _maybe_rotate_size(self, path: Path) -> None:
        if self.cfg.rotation != "size":
            return
        try:
            if not path.exists():
                return
            max_bytes = int(self.cfg.max_size_mb) * 1024 * 1024
            if path.stat().st_size < max_bytes:
                return
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            rotated = path.with_name(f"{path.stem}.{ts}{path.suffix}")
            path.rename(rotated)
            logger.warning(f"Rotated PatternMatcher CSV by size: {rotated.absolute()}")
        except Exception as e:
            logger.warning(f"Failed size-rotation for {path}: {e}", exc_info=True)

    def log_batch(
        self,
        *,
        batch_id: str,
        model: str,
        num_pairs: int,
        prompt_text: str,
        response_text: str,
        latency_ms: float,
        cache_hits: int,
        fallback_used: bool,
        parse_ok: bool,
        error_type: Optional[str],
    ) -> None:
        if not self.cfg.enabled:
            return

        batches_path, _ = self._paths()
        self._maybe_rotate_size(batches_path)
        self._maybe_migrate_schema_in_place(batches_path, self._batch_fieldnames)

        prompt_text_t = _truncate(prompt_text, self.cfg.max_content_chars)
        response_text_t = _truncate(response_text, self.cfg.max_content_chars)
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "batch_id": batch_id,
            "model": model,
            "num_pairs": num_pairs,
            "latency_ms": round(float(latency_ms), 3),
            "cache_hits": int(cache_hits),
            "fallback_used": bool(fallback_used),
            "parse_ok": bool(parse_ok),
            "error_type": error_type or "",
            "prompt_chars": len(prompt_text),
            "response_chars": len(response_text),
            "prompt_hash": _sha256_text(prompt_text),
            "response_hash": _sha256_text(response_text) if response_text else "",
            "prompt_text_trunc": prompt_text_t,
            "response_text_trunc": response_text_t,
        }

        with self._lock:
            file_exists = batches_path.exists()
            mode = "a" if file_exists else "w"
            with open(batches_path, mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._batch_fieldnames)
                if not self._header_written_batches and not file_exists:
                    writer.writeheader()
                    self._header_written_batches = True
                writer.writerow(row)

    def log_pair(
        self,
        *,
        batch_id: str,
        pair_index: int,
        pattern: Dict[str, Any],
        item: Dict[str, Any],
        match_label: bool,
        confidence: float,
        cache_hit: bool,
        fallback_used: bool,
        llm_used: bool,
        parse_ok: bool,
        error_type: Optional[str],
        context: Optional[str],
    ) -> None:
        if not self.cfg.enabled:
            return

        _, pairs_path = self._paths()
        self._maybe_rotate_size(pairs_path)
        self._maybe_migrate_schema_in_place(pairs_path, self._pair_fieldnames)

        pattern_json = _json_dumps_stable(pattern)
        item_json = _json_dumps_stable(item)
        pattern_json_t = _truncate(pattern_json, self.cfg.max_content_chars)
        item_json_t = _truncate(item_json, self.cfg.max_content_chars)

        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "batch_id": batch_id,
            "pair_index": int(pair_index),
            "pattern_type": str(pattern.get("type", "")),
            "match_label": bool(match_label),
            "confidence": round(float(confidence), 6),
            "cache_hit": bool(cache_hit),
            "fallback_used": bool(fallback_used),
            "llm_used": bool(llm_used),
            "parse_ok": bool(parse_ok),
            "error_type": error_type or "",
            "context": context or "",
            "pattern_json": pattern_json_t,
            "item_json": item_json_t,
            "pattern_hash": _sha256_text(pattern_json),
            "item_hash": _sha256_text(item_json),
            "input_json": _truncate(_json_dumps_stable({"pattern": pattern, "item": item}), self.cfg.max_content_chars),
            "output_json": _truncate(_json_dumps_stable({"match": bool(match_label), "confidence": float(confidence)}), self.cfg.max_content_chars),
        }

        with self._lock:
            file_exists = pairs_path.exists()
            mode = "a" if file_exists else "w"
            with open(pairs_path, mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._pair_fieldnames)
                if not self._header_written_pairs and not file_exists:
                    writer.writeheader()
                    self._header_written_pairs = True
                writer.writerow(row)

    def _maybe_migrate_schema_in_place(self, path: Path, expected_fieldnames: list[str]) -> None:
        """
        Ensure we keep a single append-only CSV with stable columns.
        If header differs, rewrite once preserving all rows and filling new columns with blanks.
        """
        try:
            if not path.exists():
                return
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
            if not header:
                return
            if list(header) == expected_fieldnames:
                return

            # Backup then migrate in-place
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = path.with_name(f"{path.stem}.schema_backup.{ts}{path.suffix}")
            path.replace(backup)

            # Read old rows
            with open(backup, "r", encoding="utf-8", newline="") as f:
                old_reader = csv.DictReader(f)
                old_rows = list(old_reader)
                old_fields = list(old_reader.fieldnames or header)

            with tempfile.NamedTemporaryFile(
                mode="w",
                newline="",
                encoding="utf-8",
                dir=str(path.parent),
                delete=False,
                prefix=f".{path.stem}.",
                suffix=".tmp",
            ) as tf:
                tmp_path = Path(tf.name)
                writer = csv.DictWriter(tf, fieldnames=expected_fieldnames)
                writer.writeheader()
                for r in old_rows:
                    out = {k: "" for k in expected_fieldnames}
                    for k in old_fields:
                        if k in out:
                            out[k] = r.get(k, "")
                    writer.writerow(out)

            tmp_path.replace(path)
        except Exception as e:
            logger.warning(f"PatternMatchLogger schema migration failed for {path}: {e}", exc_info=True)


