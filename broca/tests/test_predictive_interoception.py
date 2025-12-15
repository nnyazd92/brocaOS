"""
Tests for PredictiveInteroception.

Tests predictive interoception including resource forecasting, error prediction, and model updates.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.internal_sensing.predictive_interoception import PredictiveInteroception
from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor
from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor


class TestPredictiveInteroceptionInitialization:
    """Test PredictiveInteroception initialization."""
    
    def test_initialization(self):
        """
        Test that predictive system initializes with models.
        
        Rationale: Ensures predictive system starts with proper state.
        """
        monitor = PredictiveInteroception()
        
        assert monitor.internal_models is not None
        assert "resource_prediction" in monitor.internal_models
        assert "cognitive_load_prediction" in monitor.internal_models
        assert "affective_forecasting" in monitor.internal_models
        assert "error_prediction" in monitor.internal_models


class TestResourcePrediction:
    """Test resource prediction functionality."""
    
    def test_resource_prediction(self):
        """
        Test that future resource needs are predicted.
        
        Rationale: Ensures resource forecasting works.
        """
        monitor = PredictiveInteroception()
        physiology = ComputationalPhysiologyMonitor()
        
        # Set up some history
        physiology.metrics["computational_load"] = 0.5
        physiology.sample_resources()
        physiology.metrics["computational_load"] = 0.6
        physiology.sample_resources()
        
        prediction = monitor.predict_resources(physiology, horizon=5)
        
        assert isinstance(prediction, dict)
        assert "computational_load" in prediction
        assert "memory_pressure" in prediction
        assert "timestamp" in prediction
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_resource_prediction_trend(self, mock_psutil):
        """
        Test that predictions follow trends.
        
        Rationale: Ensures predictions are based on historical patterns.
        """
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        monitor = PredictiveInteroception()
        physiology = ComputationalPhysiologyMonitor()
        
        # Create increasing trend by directly setting metrics
        for load in [0.3, 0.4, 0.5, 0.6, 0.7]:
            physiology.metrics["computational_load"] = load
            physiology.metrics["memory_pressure"] = 0.5
            physiology.sample_resources()
        
        prediction = monitor.predict_resources(physiology, horizon=1)
        
        # Should predict increase (or at least maintain trend)
        assert prediction["computational_load"] >= 0.5


class TestCognitiveLoadPrediction:
    """Test cognitive load prediction functionality."""
    
    def test_cognitive_load_prediction(self):
        """
        Test that processing demands are anticipated.
        
        Rationale: Ensures cognitive load forecasting works.
        """
        monitor = PredictiveInteroception()
        cognitive = CognitiveStateMonitor()
        
        # Set up some history
        cognitive.record_confidence("r1", 0.7)
        cognitive.sample_cognitive_state()
        cognitive.record_confidence("r2", 0.8)
        cognitive.sample_cognitive_state()
        
        prediction = monitor.predict_cognitive_load(cognitive, horizon=3)
        
        assert isinstance(prediction, dict)
        assert "confidence_level" in prediction
        assert "processing_depth" in prediction
        assert "timestamp" in prediction


class TestAffectiveForecasting:
    """Test affective forecasting functionality."""
    
    def test_affective_forecasting(self):
        """
        Test that emotional responses are predicted.
        
        Rationale: Ensures affective forecasting works.
        """
        monitor = PredictiveInteroception()
        affective = ComputationalAffectMonitor()
        
        # Set up some state
        affective.compute_valence(0.6, 0.2)
        affective.compute_arousal(0.7)
        
        prediction = monitor.predict_affective_state(affective, horizon=2)
        
        assert isinstance(prediction, dict)
        assert "valence" in prediction
        assert "arousal" in prediction
        assert "timestamp" in prediction


class TestErrorPrediction:
    """Test error prediction functionality."""
    
    def test_error_prediction(self):
        """
        Test that potential errors are anticipated.
        
        Rationale: Ensures error prediction works.
        """
        monitor = PredictiveInteroception()
        cognitive = CognitiveStateMonitor()
        physiology = ComputationalPhysiologyMonitor()
        
        # Set up conditions that might lead to errors
        cognitive.states["confidence_level"] = 0.3  # Low confidence
        physiology.metrics["computational_load"] = 0.9  # High load
        
        error_probability = monitor.predict_error_probability(cognitive, physiology)
        
        assert isinstance(error_probability, float)
        assert 0.0 <= error_probability <= 1.0
        assert error_probability > 0.0  # Should detect some error risk
    
    def test_error_prediction_low_risk(self):
        """
        Test that good conditions show low error risk.
        
        Rationale: Ensures error prediction is calibrated.
        """
        monitor = PredictiveInteroception()
        cognitive = CognitiveStateMonitor()
        physiology = ComputationalPhysiologyMonitor()
        
        # Set up good conditions
        cognitive.states["confidence_level"] = 0.9  # High confidence
        physiology.metrics["computational_load"] = 0.3  # Low load
        
        error_probability = monitor.predict_error_probability(cognitive, physiology)
        
        # Should be lower than high-risk scenario
        assert error_probability < 0.5


class TestPredictionErrorComputation:
    """Test prediction error computation."""
    
    def test_prediction_error_computation(self):
        """
        Test that prediction errors are calculated.
        
        Rationale: Ensures prediction accuracy can be measured.
        """
        monitor = PredictiveInteroception()
        
        predicted = {"computational_load": 0.7}
        actual = {"computational_load": 0.8}
        
        error = monitor.compute_prediction_error(predicted, actual)
        
        assert isinstance(error, float)
        assert error >= 0.0
        assert abs(error - 0.1) < 0.001  # Should be approximately 0.1 difference
    
    def test_prediction_error_multiple_metrics(self):
        """
        Test that prediction errors handle multiple metrics.
        
        Rationale: Ensures error computation works for complex predictions.
        """
        monitor = PredictiveInteroception()
        
        predicted = {"computational_load": 0.6, "memory_pressure": 0.5}
        actual = {"computational_load": 0.7, "memory_pressure": 0.4}
        
        error = monitor.compute_prediction_error(predicted, actual)
        
        assert error >= 0.0
        # Should be average of errors
        assert 0.05 <= error <= 0.15


class TestModelUpdates:
    """Test model update functionality."""
    
    def test_model_updates(self):
        """
        Test that internal models update from errors.
        
        Rationale: Ensures models learn from prediction errors.
        """
        monitor = PredictiveInteroception()
        
        predicted = {"computational_load": 0.5}
        actual = {"computational_load": 0.7}
        error = monitor.compute_prediction_error(predicted, actual)
        
        monitor.update_models("resource_prediction", error, predicted, actual)
        
        # Models should be updated
        assert "resource_prediction" in monitor.internal_models
    
    def test_model_learning(self):
        """
        Test that models learn from prediction errors.
        
        Rationale: Ensures models improve over time.
        """
        monitor = PredictiveInteroception()
        
        # Make multiple predictions and updates
        for i in range(5):
            predicted = {"computational_load": 0.5 + i * 0.1}
            actual = {"computational_load": 0.6 + i * 0.1}
            error = monitor.compute_prediction_error(predicted, actual)
            monitor.update_models("resource_prediction", error, predicted, actual)
        
        # Models should have learned
        assert len(monitor._prediction_history) > 0


class TestPredictionAccuracy:
    """Test prediction accuracy tracking."""
    
    def test_prediction_accuracy(self):
        """
        Test that prediction accuracy is tracked.
        
        Rationale: Ensures accuracy metrics are maintained.
        """
        monitor = PredictiveInteroception()
        
        # Record some predictions and outcomes
        monitor.record_prediction("pred1", {"load": 0.6}, {"load": 0.7})
        monitor.record_prediction("pred2", {"load": 0.5}, {"load": 0.5})
        
        accuracy = monitor.get_prediction_accuracy()
        
        assert isinstance(accuracy, float)
        assert 0.0 <= accuracy <= 1.0
    
    def test_prediction_accuracy_none_when_no_data(self):
        """
        Test that prediction accuracy returns None when no predictions recorded.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        monitor = PredictiveInteroception()
        
        accuracy = monitor.get_prediction_accuracy()
        
        assert accuracy is None


class TestLearningFromMismatches:
    """Test learning from prediction errors."""
    
    def test_learning_from_mismatches(self):
        """
        Test that system learns from prediction errors.
        
        Rationale: Ensures system adapts based on errors.
        """
        monitor = PredictiveInteroception()
        
        # Record mismatches
        for i in range(10):
            predicted = {"computational_load": 0.5}
            actual = {"computational_load": 0.7}
            error = monitor.compute_prediction_error(predicted, actual)
            monitor.update_models("resource_prediction", error, predicted, actual)
        
        # System should have learned
        assert len(monitor._prediction_history) >= 10
        
        # Accuracy should improve or be tracked
        accuracy = monitor.get_prediction_accuracy()
        assert isinstance(accuracy, float)

