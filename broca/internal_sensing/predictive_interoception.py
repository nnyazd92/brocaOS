"""
Predictive interoception for forecasting future internal states.

Implements predictive coding to anticipate future computational, cognitive,
and affective states.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from collections import deque

if TYPE_CHECKING:
    from .computational_physiology import ComputationalPhysiologyMonitor
    from .cognitive_state import CognitiveStateMonitor
    from .affective_state import ComputationalAffectMonitor

logger = logging.getLogger(__name__)


class PredictiveInteroception:
    """
    Predictive interoception system.
    
    Predicts future internal states including:
    - Resource needs
    - Cognitive load
    - Affective states
    - Error probability
    """
    
    def __init__(self) -> None:
        """Initialize predictive interoception system."""
        self.internal_models: Dict[str, Any] = {
            "resource_prediction": {},
            "cognitive_load_prediction": {},
            "affective_forecasting": {},
            "error_prediction": {},
        }
        
        self._prediction_history: deque = deque(maxlen=100)
        self._prediction_errors: deque = deque(maxlen=100)
        
        logger.info("Initialized PredictiveInteroception")
    
    def predict_resources(
        self,
        physiology: "ComputationalPhysiologyMonitor",
        horizon: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Predict future resource needs.
        
        Args:
            physiology: ComputationalPhysiologyMonitor instance
            horizon: Prediction horizon (number of steps ahead)
            
        Returns:
            Dictionary with predicted resource metrics, or None if insufficient history
        """
        history = physiology.get_history()
        
        if len(history) < 2:
            # Not enough history for prediction
            return None
        
        # Simple linear trend prediction
        recent = history[-min(5, len(history)):]
        
        # Calculate trend for computational_load (skip None values)
        loads = [s.get("computational_load") for s in recent if s.get("computational_load") is not None]
        if len(loads) >= 2:
            trend = (loads[-1] - loads[0]) / len(loads)
            predicted_load = min(1.0, max(0.0, loads[-1] + trend * horizon))
        elif len(loads) == 1:
            predicted_load = loads[0]
        else:
            predicted_load = None
        
        # Calculate trend for memory_pressure (skip None values)
        memories = [s.get("memory_pressure") for s in recent if s.get("memory_pressure") is not None]
        if len(memories) >= 2:
            trend = (memories[-1] - memories[0]) / len(memories)
            predicted_memory = min(1.0, max(0.0, memories[-1] + trend * horizon))
        elif len(memories) == 1:
            predicted_memory = memories[0]
        else:
            predicted_memory = None
        
        prediction = {
            "computational_load": predicted_load,
            "memory_pressure": predicted_memory,
            "processing_latency": physiology.metrics.get("processing_latency"),  # Preserve None
            "attention_fluctuation": physiology.metrics.get("attention_fluctuation"),  # Preserve None
            "energy_efficiency": physiology.metrics.get("energy_efficiency"),  # Preserve None
            "timestamp": time.time() + horizon,
        }
        
        return prediction
    
    def predict_cognitive_load(
        self,
        cognitive: "CognitiveStateMonitor",
        horizon: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Predict future cognitive load.
        
        Args:
            cognitive: CognitiveStateMonitor instance
            horizon: Prediction horizon
            
        Returns:
            Dictionary with predicted cognitive states, or None if insufficient history
        """
        history = cognitive.get_history()
        
        if len(history) < 2:
            # Not enough history for prediction
            return None
        
        # Simple trend prediction
        recent = history[-min(5, len(history)):]
        
        # Predict confidence (skip None values)
        confidences = [s.get("confidence_level") for s in recent if s.get("confidence_level") is not None]
        if len(confidences) >= 2:
            trend = (confidences[-1] - confidences[0]) / len(confidences)
            predicted_confidence = min(1.0, max(0.0, confidences[-1] + trend * horizon))
        elif len(confidences) == 1:
            predicted_confidence = confidences[0]
        else:
            predicted_confidence = None
        
        prediction = {
            "confidence_level": predicted_confidence,
            "conceptual_coherence": cognitive.states.get("conceptual_coherence"),  # Preserve None
            "processing_depth": cognitive.states.get("processing_depth"),  # Preserve None
            "uncertainty_tracking": cognitive.states.get("uncertainty_tracking"),  # Preserve None
            "attention_allocation": cognitive.states.get("attention_allocation", {}).copy(),
            "timestamp": time.time() + horizon,
        }
        
        return prediction
    
    def predict_affective_state(
        self,
        affective: "ComputationalAffectMonitor",
        horizon: int = 2
    ) -> Dict[str, Any]:
        """
        Predict future affective state.
        
        Args:
            affective: ComputationalAffectMonitor instance
            horizon: Prediction horizon
            
        Returns:
            Dictionary with predicted affective states
        """
        # For now, predict current state (affective states are more stable)
        # In future, could add trend analysis
        current = affective.affective_states.copy()
        current["timestamp"] = time.time() + horizon
        
        return current
    
    def predict_error_probability(
        self,
        cognitive: "CognitiveStateMonitor",
        physiology: "ComputationalPhysiologyMonitor"
    ) -> Optional[float]:
        """
        Predict probability of errors.
        
        Args:
            cognitive: CognitiveStateMonitor instance
            physiology: ComputationalPhysiologyMonitor instance
            
        Returns:
            Error probability (0.0-1.0), or None if required metrics unavailable
        """
        # Error probability increases with:
        # - Low confidence
        # - High computational load
        # - Low coherence
        
        confidence = cognitive.states.get("confidence_level")
        load = physiology.metrics.get("computational_load")
        coherence = cognitive.states.get("conceptual_coherence")
        
        # Need at least one metric to make a prediction
        if confidence is None and load is None and coherence is None:
            return None
        
        # Use available metrics, default missing ones to neutral (0.5)
        conf_value = confidence if confidence is not None else 0.5
        load_value = load if load is not None else 0.5
        coherence_value = coherence if coherence is not None else 0.5
        
        # Combine factors
        error_risk = (
            (1.0 - conf_value) * 0.4 +  # Low confidence increases risk
            load_value * 0.3 +  # High load increases risk
            (1.0 - coherence_value) * 0.3  # Low coherence increases risk
        )
        
        return min(1.0, max(0.0, error_risk))
    
    def compute_prediction_error(
        self,
        predicted: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> float:
        """
        Compute prediction error between predicted and actual values.
        
        Args:
            predicted: Predicted values dictionary
            actual: Actual values dictionary
            
        Returns:
            Average prediction error (0.0-1.0)
        """
        errors = []
        
        for key in predicted:
            if key in actual and key != "timestamp":
                pred_val = predicted[key]
                actual_val = actual[key]
                
                if isinstance(pred_val, (int, float)) and isinstance(actual_val, (int, float)):
                    error = abs(pred_val - actual_val)
                    errors.append(error)
        
        if len(errors) == 0:
            return 0.0
        
        return sum(errors) / len(errors)
    
    def update_models(
        self,
        model_type: str,
        error: float,
        predicted: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> None:
        """
        Update internal models based on prediction errors.
        
        Args:
            model_type: Type of model to update
            error: Prediction error
            predicted: Predicted values
            actual: Actual values
        """
        # Record prediction for learning
        self._prediction_history.append({
            "model_type": model_type,
            "predicted": predicted,
            "actual": actual,
            "error": error,
            "timestamp": time.time(),
        })
        
        self._prediction_errors.append(error)
        
        # Update model (simple: store recent patterns)
        if model_type not in self.internal_models:
            self.internal_models[model_type] = {}
        
        # Store recent prediction pattern
        if "recent_patterns" not in self.internal_models[model_type]:
            self.internal_models[model_type]["recent_patterns"] = deque(maxlen=20)
        
        self.internal_models[model_type]["recent_patterns"].append({
            "predicted": predicted,
            "actual": actual,
            "error": error,
        })
    
    def record_prediction(
        self,
        prediction_id: str,
        predicted: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> None:
        """
        Record a prediction and its outcome.
        
        Args:
            prediction_id: Unique identifier for the prediction
            predicted: Predicted values
            actual: Actual values
        """
        error = self.compute_prediction_error(predicted, actual)
        self.update_models("general", error, predicted, actual)
    
    def get_prediction_accuracy(self) -> Optional[float]:
        """
        Get overall prediction accuracy.
        
        Returns:
            Accuracy score (0.0-1.0), higher = more accurate, or None if no predictions recorded
        """
        if len(self._prediction_errors) == 0:
            return None  # No predictions recorded yet
        
        # Accuracy is inverse of average error
        avg_error = sum(self._prediction_errors) / len(self._prediction_errors)
        accuracy = 1.0 - min(avg_error, 1.0)
        
        return accuracy

