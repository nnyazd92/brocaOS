"""
Tests that RL info-gain does not silently use placeholder zeros when epistemic data is missing.
"""

from broca.reasoning.rl_signals import RLSignalAggregator


class StubEstimator:
    def estimate_information_gain(self, *, context):
        # Return (info_gain, uncertainty)
        return 0.7, 0.1


class MissingEpistemicBridge:
    def get_information_gain_info(self):
        return {"value": 0.0, "has_data": False, "sample_size": 0, "estimator": "missing_engine"}


def test_info_gain_missing_epistemic_uses_estimator():
    agg = RLSignalAggregator(epistemic_bridge=MissingEpistemicBridge(), estimator=StubEstimator())
    metrics = agg.compute_signals()

    assert metrics.info_gain_estimator == "estimated_llm"
    assert metrics.info_gain_uncertainty is not None and 0.0 <= metrics.info_gain_uncertainty <= 1.0
    assert metrics.info_gain_raw is not None
    assert 0.65 <= metrics.information_gain_reward <= 0.75


