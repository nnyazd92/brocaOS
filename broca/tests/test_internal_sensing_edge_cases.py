"""
Tests for edge cases in internal sensing metrics.

Verifies system handles edge cases correctly.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.internal_sensing.framework import InternalSensingFramework
from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor
from broca.internal_sensing.integrated_interoception import IntegratedInteroception
from broca.world_state.aggregator import WorldStateAggregator


class TestEmptyHistories:
    """Test behavior with empty histories."""
    
    def test_behavior_when_no_data_recorded(self):
        """
        Test behavior when no data has been recorded.
        
        Rationale: Verifies system handles empty state correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # No data recorded - should use defaults
        assert monitor.states["confidence_level"] == 0.5
        assert monitor.states["uncertainty_tracking"] == 0.0
        assert monitor.states["processing_depth"] == 1.0
        
        # Sampling should still work
        sample = monitor.sample_cognitive_state()
        assert sample["confidence_level"] == 0.5
        assert sample["uncertainty_tracking"] == 0.0
    
    def test_behavior_when_recording_methods_never_called(self):
        """
        Test behavior when recording methods are never called.
        
        Rationale: Verifies system handles missing data gracefully.
        """
        framework = InternalSensingFramework()
        
        # No recording methods called
        state = framework.sample_internal_state()
        
        # Should still return valid state with defaults
        assert "cognitive" in state
        assert state["cognitive"]["confidence_level"] == 0.5
        assert state["cognitive"]["uncertainty_tracking"] == 0.0
    
    def test_behavior_with_empty_histories_moving_averages(self):
        """
        Test behavior with empty histories for moving averages.
        
        Rationale: Verifies moving averages handle empty data correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Empty history - should use default
        monitor._update_confidence_level()
        assert monitor.states["confidence_level"] == 0.5
        
        # Should not crash
        sample = monitor.sample_cognitive_state()
        assert "confidence_level" in sample


class TestMissingData:
    """Test behavior when data is missing."""
    
    def test_behavior_when_prediction_accuracy_is_none(self):
        """
        Test behavior when prediction accuracy is None.
        
        Rationale: Verifies system handles missing prediction data.
        """
        interoception = IntegratedInteroception()
        
        # No predictions recorded - accuracy should be None
        accuracy = interoception.prediction.get_prediction_accuracy()
        assert accuracy is None
        
        # track_interoceptive_accuracy should default to 0.5
        acc_dict = interoception.track_interoceptive_accuracy()
        assert acc_dict["prediction_accuracy"] == 0.5
    
    def test_behavior_when_coherence_is_none(self):
        """
        Test behavior when coherence is None.
        
        Rationale: Verifies system handles missing coherence data.
        """
        monitor = CognitiveStateMonitor()
        
        # No reasoning steps - coherence uses default
        assert monitor.states["conceptual_coherence"] == 0.5
        
        # measure_self_awareness_quality should still work
        interoception = IntegratedInteroception()
        quality = interoception.measure_self_awareness_quality()
        assert quality is not None
        assert 0.0 <= quality <= 1.0
    
    def test_system_doesnt_crash_on_missing_data(self):
        """
        Test that system doesn't crash on missing data.
        
        Rationale: Verifies robustness.
        """
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        # No data recorded - should not crash
        world_state = aggregator.aggregate()
        
        # Should return valid world state
        assert "internal_state" in world_state
        # Cognition may not be included if no cognitive data recorded, but internal_state should exist
        assert isinstance(world_state["internal_state"], dict)
    
    def test_defaults_used_appropriately_when_data_unavailable(self):
        """
        Test that defaults are used appropriately when data unavailable.
        
        Rationale: Verifies defaults are used correctly.
        """
        framework = InternalSensingFramework()
        
        # No data - should use defaults
        state = framework.sample_internal_state()
        
        # All metrics should have valid default values
        assert state["cognitive"]["confidence_level"] == 0.5
        assert state["cognitive"]["uncertainty_tracking"] == 0.0
        assert state["cognitive"]["processing_depth"] == 1.0
        
        # Quality metrics should use defaults
        quality = framework.interoception.measure_self_awareness_quality()
        assert quality == 0.5  # Default when no data


class TestBoundaryConditions:
    """Test boundary conditions and extreme values."""
    
    def test_extreme_confidence_values(self):
        """
        Test behavior with extreme confidence values.
        
        Rationale: Verifies system handles boundary values correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Record extreme values
        monitor.record_confidence("test1", 0.0)  # Minimum
        monitor.record_confidence("test2", 1.0)  # Maximum
        monitor.record_confidence("test3", -0.5)  # Below minimum (should clamp)
        monitor.record_confidence("test4", 1.5)  # Above maximum (should clamp)
        
        # Values should be clamped to [0.0, 1.0]
        assert 0.0 <= monitor.states["confidence_level"] <= 1.0
    
    def test_extreme_uncertainty_values(self):
        """
        Test behavior with extreme uncertainty values.
        
        Rationale: Verifies system handles boundary values correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Record extreme values
        monitor.record_uncertainty("test1", 0.0)  # Minimum
        monitor.record_uncertainty("test2", 1.0)  # Maximum
        monitor.record_uncertainty("test3", -0.5)  # Below minimum (should clamp)
        monitor.record_uncertainty("test4", 1.5)  # Above maximum (should clamp)
        
        # Values should be clamped to [0.0, 1.0]
        assert 0.0 <= monitor.states["uncertainty_tracking"] <= 1.0
    
    def test_empty_string_responses(self):
        """
        Test behavior with empty string responses.
        
        Rationale: Verifies system handles edge cases in response processing.
        """
        framework = InternalSensingFramework()
        
        # Record with empty response (should still work)
        framework.interoception.cognition.record_confidence("empty", 0.5)
        framework.interoception.cognition.record_uncertainty("empty", 0.0)
        
        # Should not crash
        state = framework.sample_internal_state()
        assert "cognitive" in state


class TestErrorHandling:
    """Test error handling in metrics system."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_handles_psutil_errors_gracefully(self, mock_psutil):
        """
        Test that system handles psutil errors gracefully.
        
        Rationale: Verifies robustness when system calls fail.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Simulate psutil error
        mock_psutil.cpu_percent.side_effect = Exception("psutil error")
        mock_psutil.virtual_memory.side_effect = Exception("psutil error")
        
        # Should not crash, should use defaults
        sample = monitor.sample_resources()
        assert sample["computational_load"] == 0.5  # Default
        assert sample["memory_pressure"] == 0.5  # Default
    
    def test_handles_none_values_gracefully(self):
        """
        Test that system handles None values gracefully.
        
        Rationale: Verifies robustness with unexpected data types.
        """
        framework = InternalSensingFramework()
        
        # Try to record None (should be handled)
        # This would normally be caught by type checking, but test robustness
        try:
            framework.interoception.cognition.record_confidence("test", None)  # type: ignore
        except (TypeError, ValueError):
            # Expected to fail - values should be validated
            pass
        
        # System should still work
        state = framework.sample_internal_state()
        assert "cognitive" in state

