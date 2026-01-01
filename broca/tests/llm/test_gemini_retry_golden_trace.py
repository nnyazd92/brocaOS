"""
Golden trace replay for Gemini backoff schedule.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from broca.llm.gemini_client import GeminiClient


class TestGeminiRetryGoldenTrace:
    def test_backoff_schedule_matches_golden_trace(self):
        trace_path = Path(__file__).parent.parent / "fixtures" / "golden_traces" / "gemini_backoff.json"
        if not trace_path.exists():
            pytest.skip(f"Golden trace missing: {trace_path}")

        trace = json.loads(trace_path.read_text())
        cfg = trace["config"]

        client = GeminiClient(
            api_key="test-key",
            base_url="https://example.com",
            model="gemini-3.0-flash-001",
            use_sdk=False,
            max_retries=0,
            backoff_base_seconds=cfg["backoff_base_seconds"],
            backoff_max_seconds=cfg["backoff_max_seconds"],
            backoff_jitter=cfg["backoff_jitter"],
            respect_retry_after=cfg["respect_retry_after"],
        )

        retry_after = trace.get("retry_after_seconds")
        waits = [
            client._compute_backoff_seconds(attempt, retry_after_seconds=retry_after) for attempt in trace["attempts"]
        ]
        assert waits == trace["expected_wait_seconds"]

