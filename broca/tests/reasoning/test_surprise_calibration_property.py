"""
Property-based tests for calibrated surprise (science-inspired surprise-v2).

We test:
- Bounded output in [0,1]
- Monotonicity: larger outlier errors should yield >= surprise than typical errors
"""

import pytest
from hypothesis import given, strategies as st

from broca.internal_sensing.predictive_interoception import PredictiveInteroception


class TestSurpriseCalibrationProperties:
    @given(
        baseline_errors=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=10, max_size=30),
        outlier=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_calibrated_surprise_bounded_and_outlier_sensitive(self, baseline_errors, outlier):
        pi = PredictiveInteroception()

        # Warm up distribution with baseline
        for e in baseline_errors:
            pi._update_error_distribution(e)  # internal helper, deterministic update

        # Compute calibrated surprise for a typical point vs an outlier-ish point
        # Pick typical as the mean of baseline, and outlier as provided.
        typical = sum(baseline_errors) / len(baseline_errors)
        nll_typical = pi._negative_log_likelihood(typical)
        nll_outlier = pi._negative_log_likelihood(outlier)

        s_typical = pi._normalize_surprise(nll_typical)
        s_outlier = pi._normalize_surprise(nll_outlier)

        assert 0.0 <= s_typical <= 1.0
        assert 0.0 <= s_outlier <= 1.0

        # If outlier is farther from the current mean than typical, its surprise should be >= typical.
        mu = pi._error_stats["mean"]
        if abs(outlier - mu) >= abs(typical - mu):
            assert s_outlier >= s_typical


