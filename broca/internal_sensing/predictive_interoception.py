"""
Predictive interoception for forecasting future internal states.

Implements predictive coding to anticipate future computational, cognitive,
and affective states.
"""

from __future__ import annotations

import time
import logging
import math
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
        """
        Initialize predictive interoception system.
        
        Implements predictive coding theory (Friston, Seth) with hierarchical
        prediction errors and Bayesian updating.
        """
        self.internal_models: Dict[str, Any] = {
            "resource_prediction": {},
            "cognitive_load_prediction": {},
            "affective_forecasting": {},
            "error_prediction": {},
        }
        
        self._prediction_history: deque = deque(maxlen=100)
        self._prediction_errors: deque = deque(maxlen=100)
        
        # Hierarchical prediction error tracking (multi-scale)
        self._short_term_errors: deque = deque(maxlen=10)  # Immediate prediction errors
        self._long_term_errors: deque = deque(maxlen=50)   # Long-term prediction errors
        
        # Bayesian confidence tracking
        self._prediction_confidence: Dict[str, float] = {}  # Confidence per model type
        self._prediction_uncertainty: Dict[str, float] = {}  # Uncertainty per model type

        # Calibrated surprise tracking (science-inspired):
        # Maintain an online distribution over prediction errors and compute a normalized
        # negative log-likelihood (Shannon surprise proxy) for the most recent error.
        self._error_stats: Dict[str, float] = {
            "count": 0.0,
            "mean": 0.0,
            "var": 0.05,  # non-zero prior variance to avoid division by zero
        }
        self._calibrated_surprise_history: deque = deque(maxlen=100)
        
        logger.info("Initialized PredictiveInteroception (predictive coding theory)")

    def _update_error_distribution(self, error: float, alpha: float = 0.05) -> None:
        """
        Update running mean/variance of prediction error using EWMA.

        Args:
            error: Prediction error (0.0-1.0)
            alpha: EWMA update rate
        """
        e = max(0.0, min(1.0, float(error)))
        # EWMA mean/var update
        mean = self._error_stats["mean"]
        var = self._error_stats["var"]
        mean_new = (1.0 - alpha) * mean + alpha * e
        # variance of residuals around updated mean
        resid = e - mean_new
        var_new = (1.0 - alpha) * var + alpha * (resid * resid)

        # clamp variance to a sane minimum/maximum
        var_new = max(1e-6, min(0.25, var_new))
        self._error_stats["mean"] = mean_new
        self._error_stats["var"] = var_new
        self._error_stats["count"] = self._error_stats["count"] + 1.0

    def _negative_log_likelihood(self, error: float) -> float:
        """
        Negative log-likelihood of observing `error` under a Gaussian model of errors.

        Note: This is a pragmatic proxy for Shannon surprise (-log p(o)).
        """
        e = max(0.0, min(1.0, float(error)))
        mu = float(self._error_stats["mean"])
        var = float(self._error_stats["var"])
        # Gaussian NLL
        return 0.5 * math.log(2.0 * math.pi * var) + ((e - mu) ** 2) / (2.0 * var)

    def _deviation_surprisal(self, error: float) -> float:
        """
        A strictly-nonnegative, distribution-aware surprisal proxy.

        We intentionally drop the constant term of Gaussian NLL and keep only the
        deviation component:

            s = (e - mu)^2 / (2 * var)

        This avoids negative "NLL" values (which would be clamped to 0 and collapse
        the calibrated signal in low-variance regimes).
        """
        e = max(0.0, min(1.0, float(error)))
        mu = float(self._error_stats["mean"])
        var = float(self._error_stats["var"])
        var = max(1e-6, var)
        return ((e - mu) ** 2) / (2.0 * var)

    def _normalize_surprise(self, nll: float, tau: float = 2.0) -> float:
        """
        Map NLL (unbounded) -> [0,1] using a saturating nonlinearity.
        """
        if not isinstance(nll, (int, float)) or math.isnan(nll) or math.isinf(nll):
            return 0.0
        # Ensure non-negative
        nll = max(0.0, float(nll))
        # 1 - exp(-nll/tau) gives smooth saturation; tau controls sensitivity.
        return max(0.0, min(1.0, 1.0 - math.exp(-nll / max(1e-6, tau))))
    
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
                load_uncertainty_quality = "high"
            else:
                predicted_load = current_load
                # High uncertainty when insufficient data for trend
                load_uncertainty = 0.8  # High uncertainty instead of neutral 0.5
                load_uncertainty_quality = "insufficient"
            
            # Calculate trend for memory_pressure
            memories = [s.get("memory_pressure", 0.5) for s in recent if s.get("memory_pressure") is not None]
            if len(memories) >= 2:
                trend = (memories[-1] - memories[0]) / len(memories)
                predicted_memory = min(1.0, max(0.0, memories[-1] + trend * horizon))
                variance = sum((m - sum(memories)/len(memories))**2 for m in memories) / len(memories)
                memory_uncertainty = min(1.0, variance ** 0.5)
                memory_uncertainty_quality = "high"
            else:
                predicted_memory = current_memory
                # High uncertainty when insufficient data for trend
                memory_uncertainty = 0.8  # High uncertainty instead of neutral 0.5
                memory_uncertainty_quality = "insufficient"
        else:
            # Use current values if no history
            predicted_load = current_load
            predicted_memory = current_memory
            # High uncertainty when no history available
            load_uncertainty = 0.8  # High uncertainty instead of neutral 0.5
            memory_uncertainty = 0.8  # High uncertainty instead of neutral 0.5
            load_uncertainty_quality = "missing"
            memory_uncertainty_quality = "missing"
        
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
        
        # Add data quality indicators
        prediction["data_quality"] = {
            "computational_load_uncertainty": load_uncertainty_quality,
            "memory_pressure_uncertainty": memory_uncertainty_quality
        }
        
        # Add Bayesian confidence based on prediction error history
        model_type = "resource_prediction"
        if model_type in self._prediction_confidence:
            prediction["prediction_confidence"] = self._prediction_confidence[model_type]
            prediction["prediction_uncertainty"] = self._prediction_uncertainty.get(model_type, load_uncertainty)
        else:
            # Initialize with high uncertainty if no history
            prediction["prediction_confidence"] = 0.5
            prediction["prediction_uncertainty"] = max(load_uncertainty, memory_uncertainty)
        
        # Store prediction for later error computation (predictive coding)
        prediction["_prediction_id"] = f"resource_{time.time()}_{horizon}"
        
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
        Compute hierarchical prediction error between predicted and actual values.
        
        Implements predictive coding theory: prediction errors drive model updates.
        Uses weighted errors based on importance of different metrics.
        
        Args:
            predicted: Predicted values dictionary
            actual: Actual values dictionary
            
        Returns:
            Weighted average prediction error (0.0-1.0)
        """
        errors = []
        weights = []
        
        # Weight different metrics by importance
        metric_weights = {
            "computational_load": 0.3,
            "memory_pressure": 0.3,
            "confidence_level": 0.2,
            "valence": 0.1,
            "arousal": 0.1,
        }
        
        for key in predicted:
            if key in actual and key not in ("timestamp", "_prediction_id", "data_quality", 
                                             "prediction_confidence", "prediction_uncertainty"):
                pred_val = predicted[key]
                actual_val = actual[key]
                
                if isinstance(pred_val, (int, float)) and isinstance(actual_val, (int, float)):
                    error = abs(pred_val - actual_val)
                    errors.append(error)
                    # Use specific weight if available, otherwise default
                    weight = metric_weights.get(key, 0.1)
                    weights.append(weight)
        
        if len(errors) == 0:
            return 0.0
        
        # Weighted average prediction error
        if weights and sum(weights) > 0:
            weighted_error = sum(e * w for e, w in zip(errors, weights)) / sum(weights)
        else:
            weighted_error = sum(errors) / len(errors)
        
        return min(1.0, weighted_error)
    
    def update_models(
        self,
        model_type: str,
        error: float,
        predicted: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> None:
        """
        Update internal models based on prediction errors (predictive coding theory).
        
        Implements hierarchical prediction error tracking and Bayesian updating
        for model confidence. Based on Friston's predictive coding framework.
        
        Args:
            model_type: Type of model to update
            error: Prediction error (hierarchical prediction error)
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
        try:
            # Compute calibrated surprise under the *prior* error distribution (before update),
            # then update the distribution with the new observation.
            s = self._deviation_surprisal(error)
            calibrated = self._normalize_surprise(s)
            self._calibrated_surprise_history.append(calibrated)
            self._update_error_distribution(error)
        except Exception as e:
            logger.debug(f"Failed to update calibrated surprise: {e}")
        
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
        
        # Hierarchical error tracking (short-term vs long-term)
        self._short_term_errors.append(error)
        self._long_term_errors.append(error)
        
        # Bayesian updating of prediction confidence
        # Confidence increases with low errors, decreases with high errors
        if model_type not in self._prediction_confidence:
            self._prediction_confidence[model_type] = 0.5  # Prior: uniform
            self._prediction_uncertainty[model_type] = 0.5
        
        # Update confidence using Bayesian approach (simplified)
        # Lower error = higher confidence
        error_normalized = min(1.0, error)  # Normalize to [0, 1]
        confidence_update = (1.0 - error_normalized) * 0.1  # Learning rate
        old_confidence = self._prediction_confidence[model_type]
        
        # Bayesian update: blend old confidence with new evidence
        # Weight recent errors more heavily
        if len(self._short_term_errors) >= 3:
            recent_avg_error = sum(list(self._short_term_errors)[-3:]) / 3
            recent_confidence = 1.0 - min(1.0, recent_avg_error)
            # Exponential moving average
            self._prediction_confidence[model_type] = (
                0.7 * old_confidence + 0.3 * recent_confidence
            )
        else:
            # Simple update if insufficient short-term data
            self._prediction_confidence[model_type] = old_confidence + confidence_update
        
        # Clamp confidence to [0, 1]
        self._prediction_confidence[model_type] = max(0.0, min(1.0, self._prediction_confidence[model_type]))
        
        # Update uncertainty based on error variance (predictive coding)
        error_history = list(self.internal_models[model_type]["error_history"])
        if len(error_history) >= 5:
            # Calculate variance in prediction errors
            mean_error = sum(error_history) / len(error_history)
            variance = sum((e - mean_error) ** 2 for e in error_history) / len(error_history)
            # Uncertainty is proportional to error variance
            self._prediction_uncertainty[model_type] = min(1.0, variance ** 0.5)
        
        # Model adaptation: adjust prediction strategy based on recent errors
        # If errors are consistently high, increase uncertainty in future predictions
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

    def get_rl_surprise_signal(self) -> float:
        """
        Get a calibrated surprise signal for RL (0.0-1.0).

        This is NOT the same as prediction error. It is a normalized, information-theoretic
        proxy (-log p(error)) under an online error distribution, which makes large
        outliers much more salient and reduces sensitivity to tiny fluctuations.
        """
        if len(self._calibrated_surprise_history) == 0:
            return 0.0

        # Use mean of the last few for stability
        if len(self._calibrated_surprise_history) >= 3:
            recent = list(self._calibrated_surprise_history)[-3:]
            val = sum(recent) / len(recent)
        else:
            val = self._calibrated_surprise_history[-1]

        return max(0.0, min(1.0, float(val)))

    def serialize_state(self) -> Dict[str, Any]:
        """
        Serialize predictive interoception state for persistence across restarts.

        We persist only bounded, learning-relevant state so RL signals (especially calibrated surprise)
        don't reset on web/API restart.
        """
        try:
            return {
                "error_stats": {
                    "count": float(self._error_stats.get("count", 0.0)),
                    "mean": float(self._error_stats.get("mean", 0.0)),
                    "var": float(self._error_stats.get("var", 0.05)),
                },
                "calibrated_surprise_history": [float(x) for x in list(self._calibrated_surprise_history)],
                "prediction_errors": [float(x) for x in list(self._prediction_errors)],
                "prediction_confidence": {str(k): float(v) for k, v in (self._prediction_confidence or {}).items()},
                "prediction_uncertainty": {str(k): float(v) for k, v in (self._prediction_uncertainty or {}).items()},
            }
        except Exception:
            # Best-effort: never let persistence crash the system.
            return {}

    def deserialize_state(self, data: Dict[str, Any]) -> None:
        """
        Restore predictive interoception state from a persisted snapshot.

        Backward compatible: missing keys are ignored.
        """
        if not isinstance(data, dict):
            return

        # Restore error distribution stats
        stats = data.get("error_stats")
        if isinstance(stats, dict):
            try:
                count = float(stats.get("count", self._error_stats.get("count", 0.0)))
                mean = float(stats.get("mean", self._error_stats.get("mean", 0.0)))
                var = float(stats.get("var", self._error_stats.get("var", 0.05)))
                self._error_stats["count"] = max(0.0, count)
                self._error_stats["mean"] = max(0.0, min(1.0, mean))
                self._error_stats["var"] = max(1e-6, min(0.25, var))
            except Exception:
                pass

        # Restore histories (bounded by deque maxlen)
        try:
            self._calibrated_surprise_history.clear()
            for x in (data.get("calibrated_surprise_history") or []):
                try:
                    self._calibrated_surprise_history.append(max(0.0, min(1.0, float(x))))
                except Exception:
                    continue
        except Exception:
            pass

        try:
            self._prediction_errors.clear()
            for x in (data.get("prediction_errors") or []):
                try:
                    self._prediction_errors.append(max(0.0, min(1.0, float(x))))
                except Exception:
                    continue
        except Exception:
            pass

        # Rebuild hierarchical error windows from restored prediction error history
        try:
            self._short_term_errors.clear()
            self._long_term_errors.clear()
            errs = list(self._prediction_errors)
            for e in errs[-self._short_term_errors.maxlen:]:
                self._short_term_errors.append(e)
            for e in errs[-self._long_term_errors.maxlen:]:
                self._long_term_errors.append(e)
        except Exception:
            pass

        # Restore confidence/uncertainty maps
        conf = data.get("prediction_confidence")
        if isinstance(conf, dict):
            try:
                self._prediction_confidence = {str(k): max(0.0, min(1.0, float(v))) for k, v in conf.items()}
            except Exception:
                pass
        unc = data.get("prediction_uncertainty")
        if isinstance(unc, dict):
            try:
                self._prediction_uncertainty = {str(k): max(0.0, min(1.0, float(v))) for k, v in unc.items()}
            except Exception:
                pass