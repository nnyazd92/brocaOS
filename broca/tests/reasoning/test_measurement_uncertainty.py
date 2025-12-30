"""
Regression: measurement uncertainty fields in rl_rewards must not be hardcoded 0.0
when signals are actually measured. They should reflect sensor/data-quality uncertainty.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from broca.internal_sensing.data_quality import (
    measurement_uncertainty_from_quality,
    DataQuality,
)


# ---------------------------------------------------------------------
# 1) Unit tests for measurement_uncertainty_from_quality
# ---------------------------------------------------------------------

@pytest.mark.parametrize("quality,expected_range", [
    ("high", (0.0, 0.10)),
    ("medium", (0.10, 0.25)),
    ("low", (0.25, 0.45)),
    ("insufficient", (0.45, 0.75)),
    (None, (0.85, 1.0)),
])
def test_measurement_uncertainty_mapping_boundaries(quality, expected_range):
    unc = measurement_uncertainty_from_quality(quality)
    lo, hi = expected_range
    assert lo <= unc <= hi, f"quality={quality} -> uncertainty={unc}, expected in [{lo}, {hi}]"


@pytest.mark.parametrize("quality", [q.value for q in DataQuality])
def test_sample_size_lowers_uncertainty(quality):
    """Larger sample size should decrease uncertainty (better measurement confidence)."""
    unc_small = measurement_uncertainty_from_quality(quality, sample_size=5)
    unc_large = measurement_uncertainty_from_quality(quality, sample_size=200)
    # unc_large <= unc_small (i.e., larger sample → lower uncertainty)
    assert unc_large <= unc_small, f"{quality}: sample=200 → {unc_large} should be ≤ sample=5 → {unc_small}"


# ---------------------------------------------------------------------
# 2) Property-based: output always in [0, 1]
# ---------------------------------------------------------------------

@given(
    quality=st.sampled_from([q.value for q in DataQuality] + [None]),
    sample_size=st.integers(min_value=0, max_value=10000) | st.none(),
)
@settings(max_examples=200)
def test_measurement_uncertainty_bounded_0_1(quality, sample_size):
    unc = measurement_uncertainty_from_quality(quality, sample_size)
    assert 0.0 <= unc <= 1.0


# ---------------------------------------------------------------------
# 3) Integration: RLSignalMetrics gets non-zero measurement uncertainty
# ---------------------------------------------------------------------

def test_rl_signal_metrics_has_nonzero_measurement_uncertainty_when_measured():
    """
    When affective data_quality is available, RLSignalAggregator should populate
    *_uncertainty with values > 0 (not hardcoded 0.0) for at least surprise/curiosity/coherence.
    """
    # Arrange: minimal mocks that expose data_quality="high"
    from unittest.mock import MagicMock

    from broca.reasoning.rl_signals import RLSignalAggregator

    # Affective monitor returns data_quality per signal
    affect = MagicMock()
    affect.sample_affective_state.return_value = {
        "surprise": 0.3,
        "curiosity_drive": 0.4,
        "coherence_pleasure": 0.5,
        "data_quality": {
            "surprise": "high",
            "curiosity_drive": "medium",
            "coherence_pleasure": "low",
        },
    }
    # Dissonance monitor
    dissonance = MagicMock()
    dissonance.measure_dissonance.return_value = MagicMock(
        overall_dissonance=0.2,
        has_sufficient_data=True,
        component_availability={"logical": True, "factual": True, "behavioral": True, "goal": True},
    )
    dissonance.get_aggregated_dissonance.return_value = {
        "overall_dissonance": 0.2,
        "has_data": True,
        "has_sufficient_data": True,
        "component_availability": {"logical": True, "factual": True, "behavioral": True, "goal": True},
        "history_size": 25,
    }
    # Epistemic
    epistemic = MagicMock()
    epistemic.get_information_gain_info.return_value = {
        "value": 0.3,
        "has_data": True,
        "sample_size": 100,
        "estimator": "measured",
    }
    epistemic.get_information_gain.return_value = 0.3  # fallback (float)
    epistemic.get_aggregated_uncertainty.return_value = {
        "total": 0.4,
        "data_quality": "medium",
        "sample_size": 80,
        "has_data": True,
    }
    # Predictive interoception (for surprise calibration)
    predictive = MagicMock()
    predictive.get_rl_surprise_signal.return_value = 0.3

    aggregator = RLSignalAggregator(
        affective_monitor=affect,
        cognitive_dissonance_monitor=dissonance,
        epistemic_bridge=epistemic,
        predictive_interoception=predictive,
    )

    # Act
    metrics = aggregator.compute_signals()

    # Assert: measured signals should NOT have uncertainty == 0.0
    # High quality → ~0.05, medium → ~0.15, low → ~0.30
    assert metrics.surprise_uncertainty > 0.0, "surprise_uncertainty should not be 0.0 when measured"
    assert metrics.curiosity_uncertainty > 0.0, "curiosity_uncertainty should not be 0.0 when measured"
    assert metrics.coherence_uncertainty > 0.0, "coherence_uncertainty should not be 0.0 when measured"
    # info_gain_uncertainty based on estimator + sample_size
    assert metrics.info_gain_uncertainty > 0.0, "info_gain_uncertainty should reflect epistemic data"


def test_rl_signal_metrics_epistemic_uncertainty_columns_populated():
    """New epistemic uncertainty fields should be populated from EpistemicBridge."""
    from unittest.mock import MagicMock

    from broca.reasoning.rl_signals import RLSignalAggregator

    affect = MagicMock()
    affect.sample_affective_state.return_value = {}
    dissonance = MagicMock()
    dissonance.measure_dissonance.return_value = MagicMock(
        overall_dissonance=0.5,
        has_sufficient_data=False,
        component_availability={},
    )
    dissonance.get_aggregated_dissonance.return_value = {
        "overall_dissonance": 0.5,
        "has_data": False,
        "has_sufficient_data": False,
        "component_availability": {},
        "history_size": 0,
    }
    epistemic = MagicMock()
    epistemic.get_information_gain_info.return_value = {"value": 0.0, "has_data": False}
    epistemic.get_information_gain.return_value = 0.0  # fallback
    epistemic.get_aggregated_uncertainty.return_value = {
        "total": 0.55,
        "data_quality": "low",
        "sample_size": 10,
        "has_data": True,
    }
    predictive = MagicMock()
    predictive.get_rl_surprise_signal.return_value = 0.0

    aggregator = RLSignalAggregator(
        affective_monitor=affect,
        cognitive_dissonance_monitor=dissonance,
        epistemic_bridge=epistemic,
        predictive_interoception=predictive,
    )

    metrics = aggregator.compute_signals()

    assert metrics.epistemic_uncertainty_total == 0.55
    assert metrics.epistemic_uncertainty_data_quality == "low"
    assert metrics.epistemic_uncertainty_sample_size == 10

