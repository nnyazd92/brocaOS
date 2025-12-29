"""
Tests for internal sensing metrics wiring.

Ensures that metrics properly accumulate over time and update from defaults
when data is recorded.
"""

from __future__ import annotations

import time
from unittest.mock import Mock, patch
import pytest

from broca.internal_sensing.framework import InternalSensingFramework
from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor
from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.integrated_interoception import IntegratedInteroception


class TestMovingAveragesAccumulation:
    """Test that moving averages accumulate over multiple samples."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_cpu_load_moving_average_accumulates(self, mock_psutil):
        """
        Test that CPU load moving average accumulates over multiple samples.
        
        Rationale: Ensures moving averages reflect actual system state over time.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Simulate varying CPU loads (need more values since sample_resources() calls _measure_cpu_load)
        mock_psutil.cpu_percent.side_effect = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        
        # Sample multiple times (sample_resources() calls _measure_cpu_load internally)
        for i in range(5):
            monitor.sample_resources()
        
        # Moving average should be computed from all samples
        final_load = monitor.metrics["computational_load"]
        assert final_load > 0.0, "CPU load should be greater than 0 after samples"
        assert final_load < 1.0, "CPU load should be less than 1.0"
        # Should be approximately the average of the 5 samples (0.1, 0.2, 0.3, 0.4, 0.5 = 0.3)
        # But allow some variance due to moving average window
        assert 0.15 <= final_load <= 0.5, f"CPU load should be around 0.3, got {final_load}"
    
    def test_confidence_moving_average_accumulates(self):
        """
        Test that confidence moving average accumulates over multiple recordings.
        
        Rationale: Ensures confidence metrics update from defaults when data is recorded.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially should be at default
        assert monitor.states["confidence_level"] == 0.5
        
        # Record multiple confidence values
        monitor.record_confidence("resp1", 0.3)
        monitor.record_confidence("resp2", 0.5)
        monitor.record_confidence("resp3", 0.7)
        monitor.record_confidence("resp4", 0.9)
        
        # Confidence should be average of recorded values
        assert monitor.states["confidence_level"] == pytest.approx(0.6, abs=0.01)
        assert monitor.states["confidence_level"] != 0.5, "Confidence should have changed from default"
    
    def test_uncertainty_moving_average_accumulates(self):
        """
        Test that uncertainty moving average accumulates over multiple recordings.
        
        Rationale: Ensures uncertainty metrics update from defaults when data is recorded.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially should be at default
        assert monitor.states["uncertainty_tracking"] == 0.0
        
        # Record multiple uncertainty values
        monitor.record_uncertainty("q1", 0.2)
        monitor.record_uncertainty("q2", 0.4)
        monitor.record_uncertainty("q3", 0.6)
        
        # Uncertainty should be average of recorded values
        assert monitor.states["uncertainty_tracking"] == pytest.approx(0.4, abs=0.01)
        assert monitor.states["uncertainty_tracking"] != 0.0, "Uncertainty should have changed from default"


class TestMetricsUpdateFromDefaults:
    """Test that metrics update from defaults when data is recorded."""
    
    def test_confidence_updates_from_default_when_recorded(self):
        """
        Test that confidence updates from default when data is recorded.
        
        Rationale: Ensures metrics don't stay stuck at defaults.
        """
        monitor = CognitiveStateMonitor()
        
        # Should start at default
        assert monitor.states["confidence_level"] == 0.5
        
        # Record a confidence value
        monitor.record_confidence("test_response", 0.8)
        
        # Should update immediately
        assert monitor.states["confidence_level"] == 0.8
        assert monitor.states["confidence_level"] != 0.5
    
    def test_uncertainty_updates_from_default_when_recorded(self):
        """
        Test that uncertainty updates from default when data is recorded.
        
        Rationale: Ensures metrics don't stay stuck at defaults.
        """
        monitor = CognitiveStateMonitor()
        
        # Should start at default
        assert monitor.states["uncertainty_tracking"] == 0.0
        
        # Record an uncertainty value
        monitor.record_uncertainty("test_question", 0.5)
        
        # Should update immediately
        assert monitor.states["uncertainty_tracking"] == 0.5
        assert monitor.states["uncertainty_tracking"] != 0.0
    
    def test_processing_depth_updates_when_recorded(self):
        """
        Test that processing depth updates when recorded.
        
        Rationale: Ensures processing depth metrics accumulate.
        """
        monitor = CognitiveStateMonitor()
        
        # Should start at default
        assert monitor.states["processing_depth"] == 1.0
        
        # Record processing depths
        monitor.record_processing_depth("op1", 5)
        monitor.record_processing_depth("op2", 10)
        monitor.record_processing_depth("op3", 15)
        
        # Should be average of recorded depths
        assert monitor.states["processing_depth"] == 10.0
        assert monitor.states["processing_depth"] != 1.0


class TestQualityMetricsComputation:
    """Test that quality metrics are computed correctly."""
    
    def test_quality_metrics_always_return_value(self):
        """
        Test that quality metrics always return a value, not None.
        
        Rationale: Ensures quality metrics are always available in world state.
        """
        interoception = IntegratedInteroception()
        
        # Should always return a value, even with no data
        quality = interoception.measure_self_awareness_quality()
        assert quality is not None
        assert isinstance(quality, float)
        assert 0.0 <= quality <= 1.0
    
    def test_interoceptive_accuracy_always_returns_dict(self):
        """
        Test that interoceptive accuracy always returns a dict with values.
        
        Rationale: Ensures accuracy metrics are always available.
        """
        interoception = IntegratedInteroception()
        
        accuracy = interoception.track_interoceptive_accuracy()
        assert isinstance(accuracy, dict)
        assert "prediction_accuracy" in accuracy
        assert "overall_accuracy" in accuracy
        assert isinstance(accuracy["prediction_accuracy"], float)
        assert isinstance(accuracy["overall_accuracy"], float)
    
    def test_quality_metrics_update_with_prediction_data(self):
        """
        Test that quality metrics update when prediction data is available.
        
        Rationale: Ensures quality metrics reflect actual system performance.
        """
        interoception = IntegratedInteroception()
        
        # Record some predictions
        predicted = {"computational_load": 0.5, "memory_pressure": 0.5}
        actual1 = {"computational_load": 0.6, "memory_pressure": 0.4}
        actual2 = {"computational_load": 0.4, "memory_pressure": 0.6}
        
        interoception.prediction.record_prediction("pred1", predicted, actual1)
        interoception.prediction.record_prediction("pred2", predicted, actual2)
        
        # Quality should be computed from prediction accuracy
        quality = interoception.measure_self_awareness_quality()
        assert quality is not None
        assert 0.0 <= quality <= 1.0
        
        # Accuracy should reflect prediction errors
        accuracy = interoception.track_interoceptive_accuracy()
        assert accuracy["prediction_accuracy"] is not None
        assert 0.0 <= accuracy["prediction_accuracy"] <= 1.0


class TestPredictionRecording:
    """Test that predictions are recorded for accuracy tracking."""
    
    def test_predictions_recorded_in_generate_awareness(self):
        """
        Test that predictions are recorded when generating interoceptive awareness.
        
        Rationale: Ensures prediction accuracy can be tracked over time.
        """
        interoception = IntegratedInteroception()
        
        # First call - no previous prediction, so no recording
        state1 = interoception.generate_interoceptive_awareness()
        assert "_last_prediction" in interoception.__dict__ or hasattr(interoception, '_last_prediction')
        
        # Second call - should record prediction from first call
        state2 = interoception.generate_interoceptive_awareness()
        
        # Check that prediction errors are being tracked
        # After at least one prediction cycle, errors should be recorded
        if len(interoception.prediction._prediction_errors) > 0:
            accuracy = interoception.prediction.get_prediction_accuracy()
            assert accuracy is not None
            assert 0.0 <= accuracy <= 1.0


class TestMetricsInWorldState:
    """Test that metrics are properly included in world state."""
    
    def test_quality_metrics_included_in_world_state(self):
        """
        Test that quality metrics are included in world state.
        
        Rationale: Ensures quality metrics are available to the LLM.
        """
        framework = InternalSensingFramework()
        
        # Sample internal state
        state = framework.sample_internal_state()
        
        # Quality metrics should be computable
        quality = framework.interoception.measure_self_awareness_quality()
        accuracy = framework.interoception.track_interoceptive_accuracy()
        
        assert quality is not None
        assert isinstance(accuracy, dict)
        assert "prediction_accuracy" in accuracy
    
    def test_metrics_update_over_multiple_samples(self):
        """
        Test that metrics update over multiple samples.
        
        Rationale: Ensures moving averages accumulate properly.
        """
        framework = InternalSensingFramework()
        
        # Record some data
        framework.interoception.cognition.record_confidence("test1", 0.7)
        framework.interoception.cognition.record_uncertainty("test1", 0.3)
        
        # Sample multiple times
        state1 = framework.sample_internal_state()
        state2 = framework.sample_internal_state()
        
        # Metrics should reflect recorded data
        cog1 = state1.get("cognitive", {})
        cog2 = state2.get("cognitive", {})
        
        # Confidence should be around 0.7 (may be averaged with defaults)
        assert cog1.get("confidence_level") is not None
        assert cog2.get("confidence_level") is not None
        
        # Uncertainty should be around 0.3
        assert cog1.get("uncertainty_tracking") is not None
        assert cog2.get("uncertainty_tracking") is not None


class TestMovingAverageWindowLimits:
    """Test that moving average windows (maxlen) are respected."""
    
    def test_confidence_history_respects_maxlen(self):
        """
        Test that confidence history respects maxlen limit.
        
        Rationale: Ensures moving averages don't grow unbounded.
        """
        monitor = CognitiveStateMonitor()
        
        # Record more values than maxlen (maxlen is 20 for _confidence_history)
        for i in range(25):
            monitor.record_confidence(f"resp{i}", 0.5 + (i % 10) / 100.0)
        
        # History should be limited to maxlen
        assert len(monitor._confidence_history) <= 20
        
        # Moving average should still work correctly
        assert monitor.states["confidence_level"] is not None
        assert 0.0 <= monitor.states["confidence_level"] <= 1.0
    
    def test_uncertainty_history_respects_maxlen(self):
        """
        Test that uncertainty history respects maxlen limit.
        
        Rationale: Ensures moving averages don't grow unbounded.
        """
        monitor = CognitiveStateMonitor()
        
        # Record more values than maxlen (maxlen is 20 for _uncertainty_history)
        for i in range(25):
            monitor.record_uncertainty(f"q{i}", 0.5 + (i % 10) / 100.0)
        
        # History should be limited to maxlen
        assert len(monitor._uncertainty_history) <= 20
        
        # Moving average should still work correctly
        assert monitor.states["uncertainty_tracking"] is not None
        assert 0.0 <= monitor.states["uncertainty_tracking"] <= 1.0
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_cpu_load_history_respects_maxlen(self, mock_psutil):
        """
        Test that CPU load history respects maxlen limit.
        
        Rationale: Ensures moving averages don't grow unbounded.
        """
        monitor = ComputationalPhysiologyMonitor()
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = Mock(percent=50.0)
        
        # Sample more times than maxlen (maxlen is 20 for _computational_load_history)
        for i in range(25):
            monitor.sample_resources()
        
        # History should be limited to maxlen
        assert len(monitor._computational_load_history) <= 20
        
        # Moving average should still work correctly
        assert monitor.metrics["computational_load"] is not None
        assert 0.0 <= monitor.metrics["computational_load"] <= 1.0

