"""
Mutation-killer tests for Gemini retry/backoff logic.
"""

from __future__ import annotations

import random

from broca.llm.gemini_client import GeminiClient


class TestGeminiRetryMutationKillers:
    def test_respect_retry_after_takes_max(self):
        client = GeminiClient(
            api_key="test-key",
            base_url="https://example.com",
            model="gemini-3.0-flash-001",
            use_sdk=False,
            max_retries=0,
            backoff_base_seconds=1.0,
            backoff_max_seconds=60.0,
            backoff_jitter=0.0,
            respect_retry_after=True,
            _rng=random.Random(0),
        )
        # attempt=0 would yield 1s, header says 10s -> should wait 10s
        assert client._compute_backoff_seconds(0, retry_after_seconds=10.0) == 10.0

    def test_ignore_retry_after_when_disabled(self):
        client = GeminiClient(
            api_key="test-key",
            base_url="https://example.com",
            model="gemini-3.0-flash-001",
            use_sdk=False,
            max_retries=0,
            backoff_base_seconds=1.0,
            backoff_max_seconds=60.0,
            backoff_jitter=0.0,
            respect_retry_after=False,
            _rng=random.Random(0),
        )
        assert client._compute_backoff_seconds(0, retry_after_seconds=10.0) == 1.0

    def test_backoff_is_capped(self):
        client = GeminiClient(
            api_key="test-key",
            base_url="https://example.com",
            model="gemini-3.0-flash-001",
            use_sdk=False,
            max_retries=0,
            backoff_base_seconds=2.0,
            backoff_max_seconds=3.0,
            backoff_jitter=0.0,
            respect_retry_after=True,
            _rng=random.Random(0),
        )
        # attempt=2 would be 8s, but max is 3s
        assert client._compute_backoff_seconds(2, retry_after_seconds=None) == 3.0

    def test_backoff_base_zero_yields_zero(self):
        client = GeminiClient(
            api_key="test-key",
            base_url="https://example.com",
            model="gemini-3.0-flash-001",
            use_sdk=False,
            max_retries=0,
            backoff_base_seconds=0.0,
            backoff_max_seconds=60.0,
            backoff_jitter=0.0,
            respect_retry_after=True,
            _rng=random.Random(0),
        )
        assert client._compute_backoff_seconds(5, retry_after_seconds=None) == 0.0

