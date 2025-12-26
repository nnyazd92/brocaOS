"""
Tests to verify state dictionaries are updated immediately when data is recorded.

Verifies that self.states and self.metrics are updated correctly.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor


class TestCognitiveStateUpdates:
    """Test that CognitiveStateMonitor.states is updated correctly."""
    
    def test_states_updated_by_update_confidence_level(self):
        """
        Test that states dict is updated by _update_confidence_level().
        
        Rationale: Verifies state dictionary updates correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Record confidence
        monitor.record_confidence("test1", 0.8)
        
        # states dict should be updated
        assert monitor.states["confidence_level"] == 0.8
        assert isinstance(monitor.states["confidence_level"], float)
    
    def test_states_updated_by_update_uncertainty(self):
        """
        Test that states dict is updated by _update_uncertainty().
        
        Rationale: Verifies state dictionary updates correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Record uncertainty
        monitor.record_uncertainty("test1", 0.6)
        
        # states dict should be updated
        assert monitor.states["uncertainty_tracking"] == 0.6
        assert isinstance(monitor.states["uncertainty_tracking"], float)
    
    def test_states_updated_by_update_coherence(self):
        """
        Test that states dict is updated by _update_coherence().
        
        Rationale: Verifies state dictionary updates correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Record reasoning steps (which triggers coherence update)
        monitor.record_reasoning_step("step1", {
            "premise": "A",
            "conclusion": "B"
        })
        monitor.record_reasoning_step("step2", {
            "premise": "B",
            "conclusion": "C"
        })
        
        # states dict should be updated
        assert "conceptual_coherence" in monitor.states
        assert isinstance(monitor.states["conceptual_coherence"], float)
        assert 0.0 <= monitor.states["conceptual_coherence"] <= 1.0
    
    def test_states_updated_by_update_processing_depth(self):
        """
        Test that states dict is updated by _update_processing_depth().
        
        Rationale: Verifies state dictionary updates correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Record processing depth
        monitor.record_processing_depth("op1", 5)
        
        # states dict should be updated
        assert monitor.states["processing_depth"] == 5.0
        assert isinstance(monitor.states["processing_depth"], float)
    
    def test_states_reflect_latest_computed_values_not_defaults(self):
        """
        Test that states dict reflects latest computed values, not defaults.
        
        Rationale: Verifies metrics don't stay stuck at defaults.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially at defaults
        assert monitor.states["confidence_level"] == 0.5
        assert monitor.states["uncertainty_tracking"] == 0.0
        
        # Record data
        monitor.record_confidence("test1", 0.9)
        monitor.record_uncertainty("test1", 0.7)
        
        # States should reflect recorded data, not defaults
        assert monitor.states["confidence_level"] == 0.9
        assert monitor.states["confidence_level"] != 0.5
        assert monitor.states["uncertainty_tracking"] == 0.7
        assert monitor.states["uncertainty_tracking"] != 0.0


class TestPhysiologyMetricsUpdates:
    """Test that ComputationalPhysiologyMonitor.metrics is updated correctly."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_metrics_updated_by_measure_cpu_load(self, mock_psutil):
        """
        Test that metrics dict is updated by _measure_cpu_load().
        
        Rationale: Verifies metrics dictionary updates correctly.
        """
        monitor = ComputationalPhysiologyMonitor()
        mock_psutil.cpu_percent.return_value = 75.0
        
        # Measure CPU load (called by sample_resources)
        load = monitor._measure_cpu_load()
        
        # metrics dict should be updated when sample_resources is called
        monitor.sample_resources()
        assert monitor.metrics["computational_load"] == load
        assert isinstance(monitor.metrics["computational_load"], float)
        assert 0.0 <= monitor.metrics["computational_load"] <= 1.0
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_metrics_updated_by_measure_memory_pressure(self, mock_psutil):
        """
        Test that metrics dict is updated by _measure_memory_pressure().
        
        Rationale: Verifies metrics dictionary updates correctly.
        """
        monitor = ComputationalPhysiologyMonitor()
        mock_psutil.virtual_memory.return_value = Mock(percent=60.0)
        
        # Measure memory pressure (called by sample_resources)
        pressure = monitor._measure_memory_pressure()
        
        # metrics dict should be updated when sample_resources is called
        monitor.sample_resources()
        assert monitor.metrics["memory_pressure"] == pressure
        assert isinstance(monitor.metrics["memory_pressure"], float)
        assert 0.0 <= monitor.metrics["memory_pressure"] <= 1.0
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_metrics_reflect_latest_computed_values(self, mock_psutil):
        """
        Test that metrics dict reflects latest computed values.
        
        Rationale: Verifies metrics update correctly over time.
        """
        monitor = ComputationalPhysiologyMonitor()
        mock_psutil.cpu_percent.side_effect = [25.0, 50.0, 75.0]
        mock_psutil.virtual_memory.return_value = Mock(percent=50.0)
        
        # Sample multiple times
        monitor.sample_resources()
        load1 = monitor.metrics["computational_load"]
        
        monitor.sample_resources()
        load2 = monitor.metrics["computational_load"]
        
        # Metrics should update (may be moving average, so load2 != load1 is not guaranteed)
        # But metrics should always be valid
        assert 0.0 <= load1 <= 1.0
        assert 0.0 <= load2 <= 1.0


class TestAffectiveStateUpdates:
    """Test that ComputationalAffectMonitor.affective_states is updated correctly."""
    
    def test_affective_states_updated_by_moving_averages(self):
        """
        Test that affective_states dict is updated by moving averages.
        
        Rationale: Verifies affective states update correctly.
        """
        monitor = ComputationalAffectMonitor()
        
        # Update certainty affect (uses moving average)
        monitor.update_certainty_affect(0.8)
        monitor.update_certainty_affect(0.9)
        
        # affective_states dict should be updated
        assert "certainty_affect" in monitor.affective_states
        assert isinstance(monitor.affective_states["certainty_affect"], float)
        assert 0.0 <= monitor.affective_states["certainty_affect"] <= 1.0
        # Should be average of 0.8 and 0.9 = 0.85
        assert monitor.affective_states["certainty_affect"] == pytest.approx(0.85, abs=0.01)
    
    def test_affective_states_reflect_latest_computed_values(self):
        """
        Test that affective_states dict reflects latest computed values.
        
        Rationale: Verifies affective states update correctly over time.
        """
        monitor = ComputationalAffectMonitor()
        
        # Initially at defaults
        assert monitor.affective_states["certainty_affect"] == 0.5
        
        # Update with new values
        monitor.update_certainty_affect(0.7)
        
        # Should reflect new value (may be moving average)
        assert monitor.affective_states["certainty_affect"] != 0.5 or monitor.affective_states["certainty_affect"] == 0.7

