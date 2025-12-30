"""
Tests to ensure RL signals do not treat missing/low-quality sources as real measurements.
"""

from datetime import datetime, timezone

from broca.reasoning.rl_signals import RLSignalAggregator


class StubEstimator:
    def estimate_dissonance(self, *, context) -> tuple[float, float]:
        # Return (overall_dissonance, uncertainty)
        return 0.4, 0.2


class TestRLMissingnessGating:
    def test_dissonance_has_data_but_insufficient_is_treated_as_missing(self):
        """
        If dissonance monitor reports has_data=True but has_sufficient_data=False,
        RL must NOT treat overall_dissonance=0.0 as a real measurement (which would yield reward=1.0).
        """
        class Monitor:
            def get_aggregated_dissonance(self):
                return {
                    "overall_dissonance": 0.0,
                    "has_data": True,
                    "has_sufficient_data": False,
                    "measurement_quality": "estimated",
                }

        agg = RLSignalAggregator(cognitive_dissonance_monitor=Monitor(), estimator=StubEstimator())
        metrics = agg.compute_signals()

        # Stub estimator returns overall dissonance=0.4 => reward=0.6
        assert 0.55 <= metrics.dissonance_reward <= 0.65
        assert metrics.dissonance_reward != 1.0


