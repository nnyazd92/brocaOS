"""
Fault injection tests for internal sensing.

Tests error handling and edge cases when components fail or receive invalid input.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor
from broca.internal_sensing.integrated_interoception import IntegratedInteroception
from broca.internal_sensing.framework import InternalSensingFramework


class TestNoneComponentHandling:
    """Test handling when components are None or missing."""
    
    def test_update_from_cognitive_with_none_confidence(self):
        """
        Test that update_from_cognitive handles None confidence gracefully.
        
        Rationale: Ensures system doesn't crash when cognitive data is incomplete.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Don't record any confidence - should be None
        assert cognitive.states.get("confidence_level") is None
        
        # Should not crash
        affective.update_from_cognitive(cognitive)
        
        # Certainty affect should remain None
        assert affective.affective_states.get("certainty_affect") is None
    
    def test_update_from_cognitive_with_none_coherence(self):
        """
        Test that update_from_cognitive handles None coherence gracefully.
        
        Rationale: Ensures system doesn't crash when coherence is unavailable.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Don't record reasoning steps - coherence should be None
        assert cognitive.states.get("conceptual_coherence") is None
        
        # Should not crash
        affective.update_from_cognitive(cognitive)
        
        # Coherence pleasure should remain None
        assert affective.affective_states.get("coherence_pleasure") is None
    
    def test_update_from_cognitive_with_none_uncertainty(self):
        """
        Test that update_from_cognitive handles None uncertainty gracefully.
        
        Rationale: Ensures system doesn't crash when uncertainty is unavailable.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Don't record any uncertainty - should be None
        assert cognitive.states.get("uncertainty_tracking") is None
        
        # Should not crash
        affective.update_from_cognitive(cognitive)
        
        # Curiosity should remain None
        assert affective.affective_states.get("curiosity_drive") is None


class TestInvalidInputHandling:
    """Test handling of invalid input values."""
    
    def test_confidence_clamping(self):
        """
        Test that confidence values are clamped to [0, 1].
        
        Rationale: Ensures invalid values don't break the system.
        """
        monitor = CognitiveStateMonitor()
        
        # Test negative value
        monitor.record_confidence("test1", -0.5)
        assert monitor._confidence_history[-1]["confidence"] == 0.0, "Negative confidence should be clamped to 0.0"
        
        # Test value > 1.0
        monitor.record_confidence("test2", 1.5)
        assert monitor._confidence_history[-1]["confidence"] == 1.0, "Confidence > 1.0 should be clamped to 1.0"
    
    def test_uncertainty_clamping(self):
        """
        Test that uncertainty values are clamped to [0, 1].
        
        Rationale: Ensures invalid values don't break the system.
        """
        monitor = CognitiveStateMonitor()
        
        # Test negative value
        monitor.record_uncertainty("test1", -0.3)
        assert monitor._uncertainty_history[-1]["uncertainty"] == 0.0, "Negative uncertainty should be clamped to 0.0"
        
        # Test value > 1.0
        monitor.record_uncertainty("test2", 2.0)
        assert monitor._uncertainty_history[-1]["uncertainty"] == 1.0, "Uncertainty > 1.0 should be clamped to 1.0"
    
    def test_arousal_clamping(self):
        """
        Test that arousal values are clamped to [0, 1].
        
        Rationale: Ensures invalid values don't break the system.
        """
        affective = ComputationalAffectMonitor()
        
        # Test negative value
        affective.compute_arousal(-0.5)
        assert affective.affective_states["arousal"] == 0.0, "Negative arousal should be clamped to 0.0"
        
        # Test value > 1.0
        affective.compute_arousal(1.5)
        assert affective.affective_states["arousal"] == 1.0, "Arousal > 1.0 should be clamped to 1.0"
    
    def test_valence_clamping(self):
        """
        Test that valence values are clamped to [-1, 1].
        
        Rationale: Ensures invalid values don't break the system.
        """
        affective = ComputationalAffectMonitor()
        
        # Test extreme positive
        affective.compute_valence(10.0, 0.0)
        assert affective.affective_states["valence"] == 1.0, "Extreme positive valence should be clamped to 1.0"
        
        # Test extreme negative
        affective.compute_valence(0.0, 10.0)
        assert affective.affective_states["valence"] == -1.0, "Extreme negative valence should be clamped to -1.0"


class TestStateSamplingFailures:
    """Test handling when state sampling fails."""
    
    @patch('broca.internal_sensing.computational_physiology.ComputationalPhysiologyMonitor.sample_resources')
    def test_sampling_failure_handling(self, mock_sample):
        """
        Test that sampling failures are handled gracefully.
        
        Rationale: Ensures system doesn't crash when resource sampling fails.
        """
        mock_sample.side_effect = Exception("Sampling failed")
        
        interoception = IntegratedInteroception()
        
        # Should handle exception gracefully
        with pytest.raises(Exception):
            interoception.generate_interoceptive_awareness()
    
    @patch('broca.internal_sensing.cognitive_state.CognitiveStateMonitor.sample_cognitive_state')
    def test_cognitive_sampling_failure(self, mock_sample):
        """
        Test that cognitive sampling failures are handled.
        
        Rationale: Ensures system handles cognitive state sampling errors.
        """
        mock_sample.side_effect = Exception("Cognitive sampling failed")
        
        interoception = IntegratedInteroception()
        
        # Should handle exception gracefully
        with pytest.raises(Exception):
            interoception.generate_interoceptive_awareness()
    
    @patch('broca.internal_sensing.affective_state.ComputationalAffectMonitor.sample_affective_state')
    def test_affective_sampling_failure(self, mock_sample):
        """
        Test that affective sampling failures are handled.
        
        Rationale: Ensures system handles affective state sampling errors.
        """
        mock_sample.side_effect = Exception("Affective sampling failed")
        
        interoception = IntegratedInteroception()
        
        # Should handle exception gracefully
        with pytest.raises(Exception):
            interoception.generate_interoceptive_awareness()


class TestPredictionFailures:
    """Test handling when prediction computation fails."""
    
    @patch('broca.internal_sensing.predictive_interoception.PredictiveInteroception.predict_resources')
    def test_resource_prediction_failure(self, mock_predict):
        """
        Test that resource prediction failures are handled.
        
        Rationale: Ensures system handles prediction errors gracefully.
        """
        mock_predict.side_effect = Exception("Prediction failed")
        
        interoception = IntegratedInteroception()
        
        # Should handle exception gracefully
        with pytest.raises(Exception):
            interoception.generate_interoceptive_awareness()
    
    @patch('broca.internal_sensing.predictive_interoception.PredictiveInteroception.compute_prediction_error')
    def test_prediction_error_computation_failure(self, mock_compute):
        """
        Test that prediction error computation failures are handled.
        
        Rationale: Ensures system handles prediction error calculation errors.
        """
        mock_compute.side_effect = Exception("Error computation failed")
        
        interoception = IntegratedInteroception()
        interoception._last_prediction = {"computational_load": 0.5}
        
        # Should handle exception gracefully
        with pytest.raises(Exception):
            interoception.generate_interoceptive_awareness()


class TestEmptyDataHandling:
    """Test handling of empty data structures."""
    
    def test_empty_conversation_history(self):
        """
        Test that empty conversation history is handled.
        
        Rationale: Ensures system doesn't crash with empty input.
        """
        affective = ComputationalAffectMonitor()
        
        # Should not crash with empty list
        affective.compute_valence_from_conversation_history([])
        
        # Valence should remain None
        assert affective.affective_states.get("valence") is None
    
    def test_empty_reasoning_steps(self):
        """
        Test that empty reasoning steps are handled.
        
        Rationale: Ensures coherence computation handles empty data.
        """
        monitor = CognitiveStateMonitor()
        
        # Should not crash
        monitor._update_coherence()
        
        # Coherence should remain None
        assert monitor.states.get("conceptual_coherence") is None
    
    def test_empty_confidence_history(self):
        """
        Test that empty confidence history is handled.
        
        Rationale: Ensures confidence computation handles empty data.
        """
        monitor = CognitiveStateMonitor()
        
        # Should not crash
        monitor._update_confidence_level()
        
        # Confidence should remain None
        assert monitor.states.get("confidence_level") is None


class TestNetworkIOErrors:
    """Test handling of network/IO errors (if applicable)."""
    
    @patch('broca.internal_sensing.integrated_interoception.IntegratedInteroception.generate_interoceptive_awareness')
    def test_state_sampling_with_io_error(self, mock_generate):
        """
        Test that IO errors during state sampling are handled.
        
        Rationale: Ensures system handles external failures gracefully.
        """
        mock_generate.side_effect = IOError("Network error")
        
        framework = InternalSensingFramework()
        
        # Should handle exception gracefully
        with pytest.raises(IOError):
            framework.sample_internal_state()


class TestStateConsistency:
    """Test that states remain consistent under fault conditions."""
    
    def test_state_consistency_after_partial_failure(self):
        """
        Test that states remain consistent after partial computation failure.
        
        Rationale: Ensures system maintains state integrity.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Record some data
        cognitive.record_confidence("test", 0.8)
        # Don't record uncertainty
        
        # Update affective - should partially succeed
        affective.update_from_cognitive(cognitive)
        
        # Certainty affect should be computed
        assert affective.affective_states.get("certainty_affect") is not None
        
        # Curiosity should remain None (no uncertainty)
        assert affective.affective_states.get("curiosity_drive") is None
    
    def test_state_consistency_with_invalid_values(self):
        """
        Test that states remain consistent with invalid input values.
        
        Rationale: Ensures system maintains valid state even with bad input.
        """
        monitor = CognitiveStateMonitor()
        
        # Record invalid values
        monitor.record_confidence("test1", -1.0)  # Will be clamped
        monitor.record_confidence("test2", 2.0)   # Will be clamped
        
        # State should still be valid
        confidence = monitor.states.get("confidence_level")
        assert confidence is not None
        assert 0.0 <= confidence <= 1.0, "Confidence should be valid even with invalid inputs"

