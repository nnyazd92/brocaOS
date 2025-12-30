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
        # Use deviation-only surprisal (always nonnegative) to avoid degeneracy for low-variance regimes.
        dev_typical = pi._deviation_surprisal(typical)
        dev_outlier = pi._deviation_surprisal(outlier)

        s_typical = pi._normalize_surprise(dev_typical)
        s_outlier = pi._normalize_surprise(dev_outlier)

        assert 0.0 <= s_typical <= 1.0
        assert 0.0 <= s_outlier <= 1.0

        # Ensure the signal is not degenerate: a moderate deviation from mu should yield > 0.
        mu = float(pi._error_stats["mean"])
        moderate = mu + 0.1 if mu <= 0.9 else mu - 0.1
        moderate = max(0.0, min(1.0, float(moderate)))
        s_moderate = pi._normalize_surprise(pi._deviation_surprisal(moderate))
        assert s_moderate > 1e-9

        # If outlier is farther from the current mean than typical, its surprise should be >= typical.
        if abs(outlier - mu) >= abs(typical - mu):
            assert s_outlier >= s_typical


