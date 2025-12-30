"""
Regression: pattern matching logs must include input + output at minimum for training.
"""

from __future__ import annotations

import csv
from pathlib import Path

from broca.reasoning.pattern_match_logger import PatternMatchLogger, PatternMatchLogConfig


def test_pattern_match_logger_includes_prompt_response_and_pair_io(tmp_path):
    base = Path(tmp_path) / "llm_pattern_matching_log.csv"
    logger = PatternMatchLogger(
        PatternMatchLogConfig(enabled=True, base_path=base, rotation="none", max_content_chars=2000)
    )

    logger.log_batch(
        batch_id="b1",
        model="gpt-5-nano",
        num_pairs=1,
        prompt_text="PROMPT " * 1000,
        response_text="RESPONSE " * 1000,
        latency_ms=12.3,
        cache_hits=0,
        fallback_used=False,
        parse_ok=True,
        error_type=None,
    )
    logger.log_pair(
        batch_id="b1",
        pair_index=0,
        pattern={"type": "contradiction_check", "text": "A"},
        item={"text": "B"},
        match_label=False,
        confidence=0.12,
        cache_hit=False,
        fallback_used=False,
        llm_used=True,
        parse_ok=True,
        error_type=None,
        context="unit",
    )

    batches = base.with_name(f"{base.stem}_batches{base.suffix}")
    pairs = base.with_name(f"{base.stem}_pairs{base.suffix}")

    with batches.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
        assert "prompt_text_trunc" in r.fieldnames
        assert "response_text_trunc" in r.fieldnames
        assert len(rows) == 1

    with pairs.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
        assert "input_json" in r.fieldnames
        assert "output_json" in r.fieldnames
        assert len(rows) == 1


