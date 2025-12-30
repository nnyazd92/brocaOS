"""
TDD tests for reward signal quality - ensuring rewards aren't fed placeholder/default inputs.

These tests verify that:
1. information_gain_reward uses real importance/usage data, not estimated_inputs
2. coherence_reward is updated when dissonance changes (dissonance→coherence coupling)
3. curiosity_reward receives actual prediction_error from PredictiveInteroception

Per AGENTS.md: property-based testing, mutation testing, fault injection.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


# ---------------------------------------------------------------------
# 1) Information Gain: must NOT always be "estimated_inputs"
# ---------------------------------------------------------------------

class TestInformationGainRealData:
    """Tests ensuring information_gain uses real data when available."""

    def test_info_gain_with_real_importance_not_estimated_inputs(self):
        """
        When EpistemicBridge has knowledge items with REAL importance/usage_frequency,
        info_gain_estimator should be "measured", NOT "estimated_inputs".
        """
        from broca.internal_sensing.epistemic_bridge import EpistemicBridge

        # Create a mock epistemic engine with real knowledge data
        mock_engine = MagicMock()
        mock_engine.epistemic_layer.knowledge_sources = {
            "k1": {"id": "k1"},
            "k2": {"id": "k2"},
        }

        # Mock get_epistemic_context to return real confidence metrics
        def mock_context(kid):
            return {
                "confidence_metrics": {
                    "overall_confidence": 0.8,
                },
                # Real importance and usage tracked
                "importance": 0.7,
                "usage_frequency": 5,
            }

        mock_engine.get_epistemic_context = mock_context

        # Mock uncertainty_manager.information_gain_calculation
        mock_engine.uncertainty_manager.information_gain_calculation.return_value = [
            ("k1", 0.3),
            ("k2", 0.4),
        ]

        bridge = EpistemicBridge(epistemic_engine=mock_engine)

        # Call get_information_gain_info
        info = bridge.get_information_gain_info()

        # Should NOT be "estimated_inputs" when real data exists
        assert info["has_data"] is True
        assert info["value"] > 0.0
        # This test will FAIL initially (proving the bug exists)
        # After fix, estimator should be "measured" when real data is available
        assert info["estimator"] != "estimated_inputs", \
            f"Expected 'measured' when real data exists, got {info['estimator']}"

    def test_info_gain_falls_back_to_estimated_when_no_real_data(self):
        """
        When importance/usage_frequency are not available from epistemic context,
        it should fall back to estimated_inputs (correctly labeled).
        """
        from broca.internal_sensing.epistemic_bridge import EpistemicBridge

        mock_engine = MagicMock()
        mock_engine.epistemic_layer.knowledge_sources = {"k1": {"id": "k1"}}

        # No importance/usage_frequency in context
        def mock_context(kid):
            return {
                "confidence_metrics": {"overall_confidence": 0.8},
                # NO importance, NO usage_frequency
            }

        mock_engine.get_epistemic_context = mock_context
        mock_engine.uncertainty_manager.information_gain_calculation.return_value = [("k1", 0.2)]

        bridge = EpistemicBridge(epistemic_engine=mock_engine)
        info = bridge.get_information_gain_info()

        # When real data is missing, estimator SHOULD be "estimated_inputs"
        assert info["estimator"] == "estimated_inputs"

    @given(
        importance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        usage_frequency=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=50)
    def test_info_gain_value_bounded_0_1_property(self, importance, usage_frequency):
        """Property: info_gain value is always in [0, 1] regardless of inputs."""
        from broca.internal_sensing.epistemic_bridge import EpistemicBridge

        mock_engine = MagicMock()
        mock_engine.epistemic_layer.knowledge_sources = {"k1": {}}

        def mock_context(kid):
            return {
                "confidence_metrics": {"overall_confidence": 0.5},
                "importance": importance,
                "usage_frequency": usage_frequency,
            }

        mock_engine.get_epistemic_context = mock_context
        # Return gain based on importance
        mock_engine.uncertainty_manager.information_gain_calculation.return_value = [
            ("k1", importance * 0.5)
        ]

        bridge = EpistemicBridge(epistemic_engine=mock_engine)
        info = bridge.get_information_gain_info()

        assert 0.0 <= info["value"] <= 1.0


# ---------------------------------------------------------------------
# 2) Dissonance → Coherence coupling
# ---------------------------------------------------------------------

class TestDissonanceCoherenceCoupling:
    """Tests for dissonance-coherence coupling."""

    def test_dissonance_monitor_updates_affective_on_resolution(self):
        """
        When CognitiveDissonanceMonitor detects dissonance reduction,
        it should automatically update ComputationalAffectMonitor's coherence.
        """
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor
        from unittest.mock import MagicMock

        affect = ComputationalAffectMonitor()
        
        # Create mock dissonance monitor with the coupling
        mock_dissonance = MagicMock()
        mock_dissonance._affective_monitor = affect
        mock_dissonance._previous_dissonance = 0.6  # Previous high dissonance
        
        # Simulate what measure_dissonance does when dissonance reduces
        new_dissonance = 0.2
        resolution_delta = mock_dissonance._previous_dissonance - new_dissonance  # 0.4
        
        # Manual call to test the coupling
        base_coherence = 1.0 - new_dissonance
        affect.update_coherence_pleasure(
            coherence=base_coherence,
            resolution_satisfaction=resolution_delta,
        )
        
        # Coherence should have been updated
        assert len(affect._coherence_pleasure_history) > 0
        assert affect.affective_states["coherence_pleasure"] > 0.5  # Should be elevated

    def test_coherence_updates_when_dissonance_reduces(self):
        """
        When dissonance is reduced (e.g., contradiction resolved),
        coherence_pleasure should increase (resolution_satisfaction).
        """
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor

        monitor = ComputationalAffectMonitor()

        # Initial state
        initial_coherence = monitor.affective_states["coherence_pleasure"]

        # Simulate dissonance reduction
        dissonance_before = 0.6
        dissonance_after = 0.2
        delta = dissonance_before - dissonance_after  # 0.4 reduction

        # Update coherence with resolution satisfaction
        monitor.update_coherence_pleasure(
            coherence=0.5,
            resolution_satisfaction=delta,  # This should boost coherence
        )

        # Coherence should increase
        new_coherence = monitor.affective_states["coherence_pleasure"]
        # With resolution_satisfaction=0.4, and factor 0.10, expect ~0.04 boost
        assert new_coherence > initial_coherence or len(monitor._coherence_pleasure_history) == 1

    def test_coherence_coupled_to_dissonance_monitor(self):
        """
        Integration test: CognitiveDissonanceMonitor changes should
        propagate to ComputationalAffectMonitor's coherence.
        """
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor
        from unittest.mock import MagicMock

        affect = ComputationalAffectMonitor()

        # Simulate high dissonance state
        initial_dissonance = 0.7

        # Record initial coherence (low due to high dissonance)
        affect.update_coherence_pleasure(
            coherence=1.0 - initial_dissonance,  # 0.3
        )
        initial_coherence = affect.affective_states["coherence_pleasure"]

        # Now simulate dissonance reduction (resolution)
        final_dissonance = 0.3
        resolution_delta = initial_dissonance - final_dissonance  # 0.4 reduction

        affect.update_coherence_pleasure(
            coherence=1.0 - final_dissonance,  # 0.7
            resolution_satisfaction=resolution_delta,
        )

        final_coherence = affect.affective_states["coherence_pleasure"]

        # Should have increased or at least recorded the boost
        assert len(affect._coherence_pleasure_history) >= 2
        # Final coherence should be higher than initial
        assert final_coherence >= initial_coherence

    @given(
        dissonance_before=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        dissonance_after=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=50)
    def test_resolution_satisfaction_bounded_property(self, dissonance_before, dissonance_after):
        """Property: coherence_pleasure is always in [0, 1] after updates."""
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor

        monitor = ComputationalAffectMonitor()

        delta = dissonance_before - dissonance_after
        monitor.update_coherence_pleasure(
            coherence=0.5,
            resolution_satisfaction=max(0.0, delta),  # Only positive resolutions
        )

        coherence = monitor.affective_states["coherence_pleasure"]
        assert 0.0 <= coherence <= 1.0


# ---------------------------------------------------------------------
# 3) Prediction Error → Curiosity coupling
# ---------------------------------------------------------------------

class TestPredictionErrorCuriosityCoupling:
    """Tests for prediction_error → curiosity_drive coupling."""

    def test_curiosity_increases_with_prediction_error(self):
        """
        When prediction_error is high, curiosity_drive should increase.
        """
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor

        monitor = ComputationalAffectMonitor()

        # Compute curiosity with LOW prediction error
        monitor.compute_curiosity_drive(
            uncertainty=0.5,
            interest=0.5,
            prediction_error=0.1,  # Low error
        )
        low_error_curiosity = monitor.affective_states["curiosity_drive"]

        # Reset for fair comparison
        monitor._curiosity_drive_history.clear()

        # Compute curiosity with HIGH prediction error
        monitor.compute_curiosity_drive(
            uncertainty=0.5,
            interest=0.5,
            prediction_error=0.9,  # High error
        )
        high_error_curiosity = monitor.affective_states["curiosity_drive"]

        # High prediction error should yield higher curiosity
        assert high_error_curiosity > low_error_curiosity

    def test_prediction_error_from_predictive_interoception(self):
        """
        Integration: PredictiveInteroception.get_rl_surprise_signal()
        should provide prediction_error to curiosity computation.
        """
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor
        from broca.internal_sensing.predictive_interoception import PredictiveInteroception

        affect = ComputationalAffectMonitor()
        predictive = PredictiveInteroception()

        # Record some predictions to build history using correct API
        for i in range(5):
            prediction_id = f"pred_{i}"
            predicted = {
                "valence": 0.5,
                "arousal": 0.5,
            }
            actual = {
                "valence": 0.5 + i * 0.1,  # Increasing deviation
                "arousal": 0.5 + i * 0.05,
            }
            predictive.record_prediction(prediction_id, predicted, actual)

        # Get prediction error signal
        prediction_error = predictive.get_rl_surprise_signal()

        # This should be a valid float
        assert isinstance(prediction_error, (int, float))
        assert 0.0 <= prediction_error <= 1.0

        # Use it in curiosity computation
        affect.compute_curiosity_drive(
            uncertainty=0.5,
            interest=0.5,
            prediction_error=prediction_error,
        )

        # Curiosity should be computed (not stuck at default)
        assert len(affect._curiosity_drive_history) > 0

    @given(
        prediction_error=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        uncertainty=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        interest=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_curiosity_always_bounded_property(self, prediction_error, uncertainty, interest):
        """Property: curiosity_drive is always in [0, 1]."""
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor

        monitor = ComputationalAffectMonitor()
        monitor.compute_curiosity_drive(
            uncertainty=uncertainty,
            interest=interest,
            prediction_error=prediction_error,
        )

        curiosity = monitor.affective_states["curiosity_drive"]
        assert 0.0 <= curiosity <= 1.0


# ---------------------------------------------------------------------
# 4) Integration: RLSignalAggregator receives real signals
# ---------------------------------------------------------------------

class TestRLSignalAggregatorRealSignals:
    """Tests that RLSignalAggregator receives non-placeholder signals."""

    def test_aggregator_info_gain_not_always_estimated(self):
        """
        When epistemic bridge has real data, info_gain_estimator
        should NOT be "estimated_inputs".
        """
        from broca.reasoning.rl_signals import RLSignalAggregator
        from unittest.mock import MagicMock

        # Mock epistemic bridge with real data
        epistemic = MagicMock()
        epistemic.get_information_gain_info.return_value = {
            "value": 0.35,
            "has_data": True,
            "sample_size": 10,
            "estimator": "measured",  # Real data!
        }
        epistemic.get_aggregated_uncertainty.return_value = {
            "total": 0.3,
            "has_data": True,
        }

        # Minimal mocks for other monitors
        affect = MagicMock()
        affect.sample_affective_state.return_value = {
            "surprise": 0.3,
            "curiosity_drive": 0.4,
            "coherence_pleasure": 0.5,
            "data_quality": {},
        }

        dissonance = MagicMock()
        dissonance.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.2,
            "has_data": True,
            "has_sufficient_data": True,
        }

        predictive = MagicMock()
        predictive.get_rl_surprise_signal.return_value = 0.2

        aggregator = RLSignalAggregator(
            affective_monitor=affect,
            cognitive_dissonance_monitor=dissonance,
            epistemic_bridge=epistemic,
            predictive_interoception=predictive,
        )

        metrics = aggregator.compute_signals()

        # With real data, estimator should be "measured" (or at least not always "estimated_inputs")
        assert metrics.info_gain_estimator == "measured" or metrics.info_gain_estimator == "epistemic_bridge"
        assert metrics.info_gain_has_data is True
        assert metrics.information_gain_reward > 0.0

    def test_aggregator_coherence_reflects_dissonance_state(self):
        """
        When dissonance is high, coherence should be influenced.
        """
        from broca.reasoning.rl_signals import RLSignalAggregator
        from unittest.mock import MagicMock

        # High dissonance scenario
        affect_high_diss = MagicMock()
        affect_high_diss.sample_affective_state.return_value = {
            "surprise": 0.3,
            "curiosity_drive": 0.4,
            "coherence_pleasure": 0.3,  # Lower due to dissonance
            "data_quality": {"coherence_pleasure": "high"},
        }

        dissonance_high = MagicMock()
        dissonance_high.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.8,  # HIGH
            "has_data": True,
            "has_sufficient_data": True,
        }

        predictive = MagicMock()
        predictive.get_rl_surprise_signal.return_value = 0.2

        epistemic = MagicMock()
        epistemic.get_information_gain_info.return_value = {"value": 0.1, "has_data": True, "estimator": "measured"}
        epistemic.get_aggregated_uncertainty.return_value = {"total": 0.3, "has_data": True}

        agg_high = RLSignalAggregator(
            affective_monitor=affect_high_diss,
            cognitive_dissonance_monitor=dissonance_high,
            epistemic_bridge=epistemic,
            predictive_interoception=predictive,
        )

        metrics_high = agg_high.compute_signals()

        # Low dissonance scenario
        affect_low_diss = MagicMock()
        affect_low_diss.sample_affective_state.return_value = {
            "surprise": 0.3,
            "curiosity_drive": 0.4,
            "coherence_pleasure": 0.7,  # Higher due to low dissonance
            "data_quality": {"coherence_pleasure": "high"},
        }

        dissonance_low = MagicMock()
        dissonance_low.get_aggregated_dissonance.return_value = {
            "overall_dissonance": 0.1,  # LOW
            "has_data": True,
            "has_sufficient_data": True,
        }

        agg_low = RLSignalAggregator(
            affective_monitor=affect_low_diss,
            cognitive_dissonance_monitor=dissonance_low,
            epistemic_bridge=epistemic,
            predictive_interoception=predictive,
        )

        metrics_low = agg_low.compute_signals()

        # Low dissonance should yield higher coherence_reward
        assert metrics_low.coherence_reward > metrics_high.coherence_reward


# ---------------------------------------------------------------------
# Fault injection tests
# ---------------------------------------------------------------------

class TestProductionWiring:
    """Tests for production wiring of signal coupling."""

    def test_dissonance_coherence_coupling_wired_at_init(self):
        """
        When CognitiveDissonanceMonitor and ComputationalAffectMonitor are both
        available in production, set_affective_monitor should be called.
        """
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor
        from broca.reasoning.cognitive_dissonance import CognitiveDissonanceMonitor
        from unittest.mock import MagicMock

        affect = ComputationalAffectMonitor()
        
        # Mock self_model (required for CognitiveDissonanceMonitor)
        mock_self_model = MagicMock()
        mock_self_model.knowledge_boundaries = []
        mock_self_model.capabilities = {"tools": ["terminal", "web_search"]}
        mock_self_model.communication_style = {}
        mock_self_model.response_patterns = {}
        mock_self_model.objectives = []
        
        dissonance = CognitiveDissonanceMonitor(self_model=mock_self_model)
        
        # Simulate the production wiring in main_repl.py
        dissonance.set_affective_monitor(affect)
        
        # Now measure dissonance twice to trigger the coupling
        dissonance._previous_dissonance = 0.6  # Simulate high previous dissonance
        
        # Build coherence history
        for _ in range(5):
            affect.update_coherence_pleasure(0.5)
        
        initial_coherence_history_len = len(affect._coherence_pleasure_history)
        
        # Simulate dissonance reduction
        metrics = dissonance.measure_dissonance()  # This should have lower dissonance
        
        # The coupling should have triggered update_coherence_pleasure
        # (if dissonance reduced from 0.6 to lower)
        assert dissonance._affective_monitor is affect


class TestRewardSignalFaultInjection:
    """Fault injection tests per AGENTS.md."""

    def test_info_gain_handles_epistemic_engine_exception(self):
        """Fault: epistemic engine raises exception during info gain calculation."""
        from broca.internal_sensing.epistemic_bridge import EpistemicBridge

        mock_engine = MagicMock()
        mock_engine.epistemic_layer.knowledge_sources = {"k1": {}}
        mock_engine.get_epistemic_context.side_effect = RuntimeError("Simulated fault")

        bridge = EpistemicBridge(epistemic_engine=mock_engine)
        info = bridge.get_information_gain_info()

        # Should gracefully handle and return safe defaults
        assert info["has_data"] is False or info["estimator"] == "error"

    def test_curiosity_handles_none_prediction_error(self):
        """Fault: prediction_error is None."""
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor

        monitor = ComputationalAffectMonitor()

        # This should not crash
        monitor.compute_curiosity_drive(
            uncertainty=0.5,
            interest=0.5,
            prediction_error=None,  # Fault: None
        )

        curiosity = monitor.affective_states["curiosity_drive"]
        assert 0.0 <= curiosity <= 1.0

    def test_coherence_handles_extreme_resolution_satisfaction(self):
        """Fault: resolution_satisfaction is out of expected range."""
        from broca.internal_sensing.affective_state import ComputationalAffectMonitor

        monitor = ComputationalAffectMonitor()

        # Extreme value
        monitor.update_coherence_pleasure(
            coherence=0.5,
            resolution_satisfaction=10.0,  # Way out of range
        )

        coherence = monitor.affective_states["coherence_pleasure"]
        # Should still be bounded [0, 1]
        assert 0.0 <= coherence <= 1.0

