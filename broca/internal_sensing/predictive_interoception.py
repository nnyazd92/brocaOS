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
        horizon: int = 5,
        multi_horizon: bool = False
    ) -> Dict[str, Any]:
        """
        Predict future resource needs with optional multi-horizon and uncertainty quantification.
        
        Args:
            physiology: ComputationalPhysiologyMonitor instance
            horizon: Prediction horizon (number of steps ahead)
            multi_horizon: If True, return predictions for multiple horizons
            
        Returns:
            Dictionary with predicted resource metrics and uncertainty intervals
        """
        history = physiology.get_history()
        current_load = physiology.metrics.get("computational_load", 0.5)
        current_memory = physiology.metrics.get("memory_pressure", 0.5)
        
        # Simple linear trend prediction if we have history
        if len(history) >= 2:
            recent = history[-min(5, len(history)):]
            
            # Calculate trend for computational_load
            loads = [s.get("computational_load", 0.5) for s in recent if s.get("computational_load") is not None]
            if len(loads) >= 2:
                trend = (loads[-1] - loads[0]) / len(loads)
                predicted_load = min(1.0, max(0.0, loads[-1] + trend * horizon))
                # Calculate uncertainty (variance in recent values)
                variance = sum((l - sum(loads)/len(loads))**2 for l in loads) / len(loads)
                load_uncertainty = min(1.0, variance ** 0.5)
            else:
                predicted_load = current_load
                load_uncertainty = 0.5
            
            # Calculate trend for memory_pressure
            memories = [s.get("memory_pressure", 0.5) for s in recent if s.get("memory_pressure") is not None]
            if len(memories) >= 2:
                trend = (memories[-1] - memories[0]) / len(memories)
                predicted_memory = min(1.0, max(0.0, memories[-1] + trend * horizon))
                variance = sum((m - sum(memories)/len(memories))**2 for m in memories) / len(memories)
                memory_uncertainty = min(1.0, variance ** 0.5)
            else:
                predicted_memory = current_memory
                memory_uncertainty = 0.5
        else:
            # Use current values if no history
            predicted_load = current_load
            predicted_memory = current_memory
            load_uncertainty = 0.5
            memory_uncertainty = 0.5
        
        prediction = {
            "computational_load": predicted_load,
            "computational_load_uncertainty": load_uncertainty,
            "computational_load_interval": (max(0.0, predicted_load - load_uncertainty), 
                                          min(1.0, predicted_load + load_uncertainty)),
            "memory_pressure": predicted_memory,
            "memory_pressure_uncertainty": memory_uncertainty,
            "memory_pressure_interval": (max(0.0, predicted_memory - memory_uncertainty),
                                        min(1.0, predicted_memory + memory_uncertainty)),
            "processing_latency": physiology.metrics.get("processing_latency", 0.0),
            "attention_fluctuation": physiology.metrics.get("attention_fluctuation", 0.0),
            "energy_efficiency": physiology.metrics.get("energy_efficiency", 0.5),
            "timestamp": time.time() + horizon,
            "horizon": horizon,
        }
        
        # Multi-horizon predictions if requested
        if multi_horizon:
            horizons = [1, 3, 5, 10]
            multi_predictions = {}
            for h in horizons:
                if h != horizon:
                    h_pred = self.predict_resources(physiology, horizon=h, multi_horizon=False)
                    multi_predictions[f"horizon_{h}"] = h_pred
            prediction["multi_horizon"] = multi_predictions
        
        return prediction
    
    def predict_cognitive_load(
        self,
        cognitive: "CognitiveStateMonitor",
        horizon: int = 3
    ) -> Dict[str, Any]:
        """
        Predict future cognitive load.
        
        Args:
            cognitive: CognitiveStateMonitor instance
            horizon: Prediction horizon
            
        Returns:
            Dictionary with predicted cognitive states (always returns dict with defaults if needed)
        """
        history = cognitive.get_history()
        current_confidence = cognitive.states.get("confidence_level", 0.5)
        
        # Simple trend prediction if we have history
        if len(history) >= 2:
            recent = history[-min(5, len(history)):]
            
            # Predict confidence
            confidences = [s.get("confidence_level", 0.5) for s in recent]
            if len(confidences) >= 2:
                trend = (confidences[-1] - confidences[0]) / len(confidences)
                predicted_confidence = min(1.0, max(0.0, confidences[-1] + trend * horizon))
            else:
                predicted_confidence = current_confidence
        else:
            predicted_confidence = current_confidence
        
        prediction = {
            "confidence_level": predicted_confidence,
            "conceptual_coherence": cognitive.states.get("conceptual_coherence", 0.5),
            "processing_depth": cognitive.states.get("processing_depth", 1.0),
            "uncertainty_tracking": cognitive.states.get("uncertainty_tracking", 0.0),
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
        Predict future affective state using trend analysis.
        
        Args:
            affective: ComputationalAffectMonitor instance
            horizon: Prediction horizon
            
        Returns:
            Dictionary with predicted affective states
        """
        current = affective.affective_states.copy()
        
        predicted = {}
        for key, val in current.items():
            if isinstance(val, (int, float)):
                # Decay toward 0.5 (neutral) for most metrics, 0.0 for valence
                target = 0.0 if key == 'valence' else 0.5
                decay_factor = 0.1 * horizon
                predicted[key] = val + (target - val) * decay_factor
            else:
                # Use defaults for non-numeric values (shouldn't happen but ensure defaults)
                if key == 'valence':
                    predicted[key] = 0.0
                elif key in ('arousal', 'certainty_affect', 'curiosity_drive', 'coherence_pleasure'):
                    predicted[key] = 0.5
                elif key == 'surprise':
                    predicted[key] = 0.0
                else:
                    predicted[key] = val
                
        predicted["timestamp"] = time.time() + horizon
        return predicted
    
    def predict_error_probability(
        self,
        cognitive: "CognitiveStateMonitor",
        physiology: "ComputationalPhysiologyMonitor",
        affective: Optional["ComputationalAffectMonitor"] = None
    ) -> float:
        """
        Predict probability of errors based on cognitive, physiological, and affective load.
        
        Args:
            cognitive: CognitiveStateMonitor instance
            physiology: ComputationalPhysiologyMonitor instance
            affective: Optional ComputationalAffectMonitor instance
            
        Returns:
            Error probability (0.0-1.0), always returns a value using defaults if needed
        """
        confidence = cognitive.states.get("confidence_level", 0.5)
        load = physiology.metrics.get("computational_load", 0.5)
        coherence = cognitive.states.get("conceptual_coherence", 0.5)
        surprise = affective.affective_states.get("surprise", 0.0) if affective else 0.0
        
        # Error risk formula:
        # - Low confidence (30%)
        # - High computational load (20%)
        # - Low coherence (30%)
        # - High surprise/distraction (20%)
        risk = (
            (1.0 - confidence) * 0.3 + 
            load * 0.2 + 
            (1.0 - coherence) * 0.3 + 
            surprise * 0.2
        )
        
        return min(1.0, max(0.0, risk))
    
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
            self.internal_models[model_type] = {
                "recent_patterns": deque(maxlen=20),
                "error_history": deque(maxlen=50),
                "adaptation_factor": 0.1,  # Learning rate for model adaptation
            }
        
        # Store recent prediction pattern
        if "recent_patterns" not in self.internal_models[model_type]:
            self.internal_models[model_type]["recent_patterns"] = deque(maxlen=20)
        
        self.internal_models[model_type]["recent_patterns"].append({
            "predicted": predicted,
            "actual": actual,
            "error": error,
        })
        
        # Track error history for adaptation
        if "error_history" not in self.internal_models[model_type]:
            self.internal_models[model_type]["error_history"] = deque(maxlen=50)
        self.internal_models[model_type]["error_history"].append(error)
        
        # Model adaptation: adjust prediction strategy based on recent errors
        # If errors are consistently high, increase uncertainty in future predictions
        error_history = list(self.internal_models[model_type]["error_history"])
        if len(error_history) >= 5:
            recent_avg_error = sum(error_history[-5:]) / 5
            # If recent errors are high, increase adaptation (be more conservative)
            if recent_avg_error > 0.3:
                self.internal_models[model_type]["adaptation_factor"] = min(0.3, 
                    self.internal_models[model_type].get("adaptation_factor", 0.1) * 1.1)
            elif recent_avg_error < 0.1:
                # If errors are low, decrease adaptation (be more confident)
                self.internal_models[model_type]["adaptation_factor"] = max(0.05,
                    self.internal_models[model_type].get("adaptation_factor", 0.1) * 0.95)
    
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
        
        logger.debug(f"Computed prediction_accuracy: {accuracy:.3f} (from {len(self._prediction_errors)} predictions, avg_error: {avg_error:.3f})")
        
        return accuracy
    
    def get_rl_prediction_error_signal(self) -> float:
        """
        Get prediction error signal for reinforcement learning.
        
        Returns:
            Recent prediction error (0.0-1.0) for RL signal computation.
            Returns 0.0 if no predictions recorded yet.
        """
        if len(self._prediction_errors) == 0:
            return 0.0  # No predictions recorded yet
        
        # Use most recent prediction error, or average of last few if available
        if len(self._prediction_errors) >= 3:
            # Average of last 3 predictions for stability
            recent_errors = list(self._prediction_errors)[-3:]
            avg_error = sum(recent_errors) / len(recent_errors)
        else:
            # Use most recent
            avg_error = self._prediction_errors[-1]
        
        # Ensure bounded [0, 1]
        return max(0.0, min(1.0, avg_error))