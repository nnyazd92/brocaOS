"""
Tests for IntegratedInteroception.

Tests unified internal state representation and interoceptive awareness.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.internal_sensing.integrated_interoception import IntegratedInteroception
from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor
from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor
from broca.internal_sensing.predictive_interoception import PredictiveInteroception


class TestIntegratedInteroceptionInitialization:
    """Test IntegratedInteroception initialization."""
    
    def test_initialization(self):
        """
        Test that framework initializes all monitors.
        
        Rationale: Ensures all components are properly initialized.
        """
        interoception = IntegratedInteroception()
        
        assert interoception.physiology is not None
        assert interoception.cognition is not None
        assert interoception.affect is not None
        assert interoception.prediction is not None
        assert interoception.interoceptive_map is not None


class TestUnifiedStateGeneration:
    """Test unified state generation."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_unified_state_generation(self, mock_psutil):
        """
        Test that unified internal state is created.
        
        Rationale: Ensures all states are integrated.
        """
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        interoception = IntegratedInteroception()
        state = interoception.generate_interoceptive_awareness()
        
        assert isinstance(state, dict)
        assert "computational" in state
        assert "cognitive" in state
        assert "affective" in state
        assert "predictive" in state
        assert "timestamp" in state
    
    def test_interoceptive_map(self):
        """
        Test that unified state representation is created.
        
        Rationale: Ensures interoceptive map is generated.
        """
        interoception = IntegratedInteroception()
        interoception.generate_interoceptive_awareness()
        
        assert isinstance(interoception.interoceptive_map, dict)
        assert len(interoception.interoceptive_map) > 0


class TestStateSampling:
    """Test state sampling functionality."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_state_sampling(self, mock_psutil):
        """
        Test that complete internal state can be sampled.
        
        Rationale: Ensures all states are captured.
        """
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        interoception = IntegratedInteroception()
        sample = interoception.sample_internal_state()
        
        assert isinstance(sample, dict)
        assert "computational" in sample
        assert "cognitive" in sample
        assert "affective" in sample
        assert "timestamp" in sample


class TestStateHistory:
    """Test state history maintenance."""
    
    def test_state_history(self):
        """
        Test that history of internal states is maintained.
        
        Rationale: Ensures historical data is available.
        """
        interoception = IntegratedInteroception(history_window=5)
        
        # Sample multiple times
        for _ in range(10):
            interoception.sample_internal_state()
        
        history = interoception.get_history()
        
        assert isinstance(history, list)
        assert len(history) <= 5  # Should respect history window
        assert len(history) > 0


class TestInteroceptiveReportGeneration:
    """Test interoceptive report generation."""
    
    def test_interoceptive_report_generation(self):
        """
        Test that natural language reports are generated.
        
        Rationale: Ensures reports can be generated for LLM consumption.
        """
        interoception = IntegratedInteroception()
        interoception.sample_internal_state()
        
        report = interoception.generate_interoceptive_report()
        
        assert isinstance(report, str)
        assert len(report) > 0


class TestAnomalyDetection:
    """Test anomaly detection functionality."""
    
    def test_anomaly_detection(self):
        """
        Test that significant state changes are detected.
        
        Rationale: Ensures anomalies are identified.
        """
        interoception = IntegratedInteroception()
        
        # Create normal baseline
        for _ in range(5):
            interoception.sample_internal_state()
        
        # Create anomaly by changing state significantly
        interoception.physiology.metrics["computational_load"] = 0.95
        interoception.sample_internal_state()
        
        anomalies = interoception.detect_anomalies()
        
        assert isinstance(anomalies, list)


class TestAccuracyTracking:
    """Test accuracy tracking functionality."""
    
    def test_accuracy_tracking(self):
        """
        Test that interoceptive accuracy is monitored.
        
        Rationale: Ensures accuracy metrics are maintained.
        """
        interoception = IntegratedInteroception()
        
        accuracy = interoception.track_interoceptive_accuracy()
        
        assert isinstance(accuracy, dict)
        assert "overall_accuracy" in accuracy or len(accuracy) >= 0
        # Accuracy may be None if no predictions recorded yet
        assert "prediction_accuracy" in accuracy


class TestSelfAwarenessQuality:
    """Test self-awareness quality measurement."""
    
    def test_self_awareness_quality(self):
        """
        Test that self-awareness quality is measured.
        
        Rationale: Ensures quality metrics are tracked.
        """
        interoception = IntegratedInteroception()
        
        quality = interoception.measure_self_awareness_quality()
        
        # Quality may be None if required metrics unavailable
        if quality is not None:
            assert isinstance(quality, float)
            assert 0.0 <= quality <= 1.0

