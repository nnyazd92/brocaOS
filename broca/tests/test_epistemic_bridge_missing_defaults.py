"""
Tests that EpistemicBridge does not emit placeholder zeros when epistemic engine is missing.
"""

from broca.internal_sensing.data_quality import DataQuality, uncertainty_for_missing_data
from broca.internal_sensing.epistemic_bridge import EpistemicBridge


def test_epistemic_bridge_missing_engine_returns_explicit_missing_uncertainty():
    bridge = EpistemicBridge(epistemic_engine=None)
    u = bridge.get_aggregated_uncertainty()

    assert u["has_data"] is False
    assert u["data_quality"] == DataQuality.MISSING.value
    assert u["total"] == uncertainty_for_missing_data()
    # Sanity: not zeros masquerading as certainty
    assert u["epistemic"] >= 0.8


