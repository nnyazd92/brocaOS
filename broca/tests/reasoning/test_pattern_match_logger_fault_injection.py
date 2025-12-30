"""
Fault-injection tests for PatternMatcher CSV logging.

Goal: logging must never crash pattern matching, even if filesystem writes fail.
"""

from unittest.mock import Mock

import pytest

from broca.reasoning.pattern_matcher import PatternMatcher


class DummyLLM:
    def chat(self, messages, temperature=0.0):
        return {"choices": [{"message": {"content": '[{"match": true, "confidence": 0.9}]'}}]}

    def extract_assistant_content(self, response):
        return response["choices"][0]["message"]["content"]


def test_pattern_match_logging_write_failure_does_not_crash(monkeypatch):
    pm = PatternMatcher(llm_client=DummyLLM(), model="gpt-5-nano")

    # Force logger present but failing
    failing_logger = Mock()
    failing_logger.log_batch.side_effect = OSError("disk full")
    failing_logger.log_pair.side_effect = OSError("disk full")
    pm._pm_logger = failing_logger

    assert pm.match({"type": "contradiction_check", "text": "A"}, {"text": "not A"}) is True


