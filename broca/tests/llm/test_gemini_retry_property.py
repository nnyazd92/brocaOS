"""
Property-based tests for GeminiClient exponential backoff.
"""

from __future__ import annotations

import random

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from broca.llm.gemini_client import GeminiClient


class TestGeminiRetryProperties:
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
    @given(
        attempt=st.integers(min_value=0, max_value=12),
        base=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        max_sleep=st.floats(min_value=0.0, max_value=120.0, allow_nan=False, allow_infinity=False),
        retry_after=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=300.0, allow_nan=False, allow_infinity=False),
        ),
        respect_retry_after=st.booleans(),
    )
    def test_backoff_is_bounded_and_non_negative(
        self, attempt: int, base: float, max_sleep: float, retry_after: float | None, respect_retry_after: bool
    ):
        client = GeminiClient(
            api_key="test-key",
            base_url="https://example.com",
            model="gemini-3.0-flash-001",
            use_sdk=False,
            max_retries=0,
            backoff_base_seconds=base,
            backoff_max_seconds=max_sleep,
            backoff_jitter=0.0,
            respect_retry_after=respect_retry_after,
            _rng=random.Random(0),
        )

        wait = client._compute_backoff_seconds(attempt, retry_after_seconds=retry_after)
        assert 0.0 <= wait <= max_sleep + 1e-9

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
    @given(
        attempt=st.integers(min_value=0, max_value=12),
        base=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        max_sleep=st.floats(min_value=0.0, max_value=120.0, allow_nan=False, allow_infinity=False),
        retry_after=st.floats(min_value=0.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    )
    def test_respecting_retry_after_never_returns_less_than_header_when_possible(
        self, attempt: int, base: float, max_sleep: float, retry_after: float
    ):
        assume(max_sleep > 0.0)
        assume(retry_after <= max_sleep)
        client = GeminiClient(
            api_key="test-key",
            base_url="https://example.com",
            model="gemini-3.0-flash-001",
            use_sdk=False,
            max_retries=0,
            backoff_base_seconds=base,
            backoff_max_seconds=max_sleep,
            backoff_jitter=0.0,
            respect_retry_after=True,
            _rng=random.Random(0),
        )

        wait = client._compute_backoff_seconds(attempt, retry_after_seconds=retry_after)
        assert wait >= retry_after - 1e-9

