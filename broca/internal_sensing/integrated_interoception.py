"""
Integrated interoceptive awareness.

Unifies all internal sensing components into a single interoceptive map.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional
from collections import deque

from .computational_physiology import ComputationalPhysiologyMonitor
from .cognitive_state import CognitiveStateMonitor
from .affective_state import ComputationalAffectMonitor
from .predictive_interoception import PredictiveInteroception
from .response_analyzer import ResponseAnalyzer

logger = logging.getLogger(__name__)


class IntegratedInteroception:
    """
    Integrated interoceptive awareness system.
    
    Combines all internal sensing components into unified awareness.
    """
    
    def __init__(self, history_window: int = 60, embedding_service: Optional[Any] = None, epistemic_engine: Optional[Any] = None) -> None:
        """
        Initialize integrated interoception.
        
        Args:
            history_window: Number of samples to keep in history
            embedding_service: Optional embedding service for semantic analysis
            epistemic_engine: Optional MetacognitiveEngine for second-order metacognition
        """
        self.physiology = ComputationalPhysiologyMonitor()
        self.cognition = CognitiveStateMonitor()
        self.affect = ComputationalAffectMonitor()
        self.prediction = PredictiveInteroception()
        self.embedding_service = embedding_service
        self.epistemic_engine = epistemic_engine
        
        # Create epistemic bridge if epistemic engine is available
        self.epistemic_bridge = None
        if epistemic_engine:
            from .epistemic_bridge import EpistemicBridge
            self.epistemic_bridge = EpistemicBridge(epistemic_engine)
            logger.info("Created epistemic bridge for IntegratedInteroception")
        
        # Pass embedding service to monitors that need it
        if embedding_service:
            self.affect.set_embedding_service(embedding_service)
            self.cognition.set_embedding_service(embedding_service)
        
        # Pass epistemic bridge to monitors
        if self.epistemic_bridge:
            self.affect.set_epistemic_bridge(self.epistemic_bridge)
            self.cognition.set_epistemic_bridge(self.epistemic_bridge)
            logger.info("Set epistemic bridge for cognitive and affective monitors")
        
        self.interoceptive_map: Dict[str, Any] = {}
        self.history_window = history_window
        self._history: deque = deque(maxlen=history_window)
        
        logger.info("Initialized IntegratedInteroception" + (" with epistemic engine" if epistemic_engine else ""))
    
    def generate_interoceptive_awareness(self) -> Dict[str, Any]:
        """
        Generate unified interoceptive awareness.
        
        This method automatically wires up state computations:
        - Cognitive states (confidence, coherence, uncertainty) are sampled from their monitors
        - Affective states are automatically updated from cognitive states via update_from_cognitive()
          * certainty_affect computed from confidence_level
          * coherence_pleasure computed from conceptual_coherence
          * curiosity_drive computed from uncertainty_tracking and attention_allocation
        - Valence and arousal are computed in session.py when conversation data is available
        - Surprise is computed from prediction error when previous prediction exists
        
        Returns:
            Dictionary containing unified internal state
        """
        # Tick κ-integrated (piecewise-constant hold) every interoception sample.
        try:
            self.prediction.tick_kappa(now=time.time())
        except Exception:
            pass

        # Sample all components
        computational = self.physiology.sample_resources()
        cognitive = self.cognition.sample_cognitive_state()
        
        # Update from epistemic engine if available
        if self.epistemic_bridge:
            self.cognition.update_from_epistemic()
            self.affect.update_from_epistemic()
        
        # Calculate Surprise (Prediction Error) from PREVIOUS turn's prediction vs CURRENT reality
        # Do this BEFORE update_from_cognitive so we can pass prediction_error to curiosity calculation
        prediction_error: Optional[float] = None
        if hasattr(self, '_last_prediction') and self._last_prediction:
            error = self.prediction.compute_prediction_error(self._last_prediction, computational)
            prediction_error = error  # Store for curiosity drive
            # Record prediction for accuracy tracking
            self.prediction.record_prediction(
                f"pred_{int(time.time())}",
                self._last_prediction,
                computational
            )
            calibrated = None
            if hasattr(self.prediction, "get_rl_surprise_signal"):
                try:
                    # After record_prediction(), the calibrated history has been updated for this error.
                    calibrated = float(self.prediction.get_rl_surprise_signal())
                except Exception:
                    calibrated = None
            self.affect.update_surprise(error, calibrated_surprise=calibrated)
            logger.debug(f"Recorded prediction for accuracy tracking (error: {error:.3f})")
        
        # Update affective states from cognitive states automatically
        # This ensures certainty_affect, coherence_pleasure, and curiosity_drive are computed
        # when cognitive data is available
        # Now includes prediction_error for curiosity calculation!
        self.affect.update_from_cognitive(self.cognition, prediction_error=prediction_error)
        
        # Log if states were computed (for debugging state transitions)
        if self.affect.affective_states.get("certainty_affect") is not None:
            logger.debug("Affective states updated from cognitive: certainty_affect computed")
        if self.affect.affective_states.get("curiosity_drive") is not None:
            logger.debug(
                f"Affective states updated from cognitive: curiosity_drive computed "
                f"(prediction_error={prediction_error})"
            )
        if self.affect.affective_states.get("coherence_pleasure") is not None:
            logger.debug("Affective states updated from cognitive: coherence_pleasure computed")

        affective = self.affect.sample_affective_state()
        
        # Generate predictions
        resource_prediction = self.prediction.predict_resources(self.physiology, horizon=3)
        cognitive_prediction = self.prediction.predict_cognitive_load(self.cognition, horizon=2)
        affective_prediction = self.prediction.predict_affective_state(self.affect, horizon=1)
        error_probability = self.prediction.predict_error_probability(self.cognition, self.physiology, self.affect)
        
        # Create unified state
        
        unified_state = {
            "computational": computational,
            "cognitive": cognitive,
            "affective": affective,
            "predictive": {
                "resources": resource_prediction,
                "cognitive": cognitive_prediction,
                "affective": affective_prediction,
                "error_probability": error_probability,
                "kappa_last": float(self.prediction.get_kappa_last()) if hasattr(self.prediction, "get_kappa_last") else None,
                "kappa_integrated": float(self.prediction.get_kappa_integrated()) if hasattr(self.prediction, "get_kappa_integrated") else None,
            },
            "timestamp": time.time(),
        }
        
        # Update interoceptive map
        self._last_prediction = resource_prediction
        self.interoceptive_map = unified_state.copy()
        
        return unified_state
    
    def sample_internal_state(self) -> Dict[str, Any]:
        """
        Sample complete internal state.
        
        Returns:
            Dictionary containing all internal states
        """
        state = self.generate_interoceptive_awareness()
        self._history.append(state)
        return state
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get history of internal state samples.
        
        Returns:
            List of state dictionaries
        """
        return list(self._history)
    
    def generate_interoceptive_report(self) -> str:
        """
        Generate natural language interoceptive report.
        
        Returns:
            Natural language description of internal state
        """
        # Use fresh state instead of stale interoceptive_map
        # Generate fresh awareness to ensure we have the latest computed values
        state = self.generate_interoceptive_awareness()
        
        if not state:
            return "No internal state data available."
        
        lines = ["Internal State Report:"]
        lines.append("")
        
        # Computational state
        comp = state.get("computational", {})
        lines.append("Computational State:")
        cpu_load = comp.get('computational_load')
        if cpu_load is not None:
            lines.append(f"  CPU Load: {cpu_load:.2%}")
        else:
            lines.append("  CPU Load: unknown")
        memory_pressure = comp.get('memory_pressure')
        if memory_pressure is not None:
            lines.append(f"  Memory Pressure: {memory_pressure:.2%}")
        else:
            lines.append("  Memory Pressure: unknown")
        energy_efficiency = comp.get('energy_efficiency')
        if energy_efficiency is not None:
            lines.append(f"  Energy Efficiency: {energy_efficiency:.2%}")
        else:
            lines.append("  Energy Efficiency: unknown")
        lines.append("")
        
        # Cognitive state
        cog = state.get("cognitive", {})
        lines.append("Cognitive State:")
        confidence = cog.get('confidence_level')
        if confidence is not None:
            lines.append(f"  Confidence: {confidence:.2%}")
        else:
            lines.append("  Confidence: unknown")
        coherence = cog.get('conceptual_coherence')
        if coherence is not None:
            lines.append(f"  Coherence: {coherence:.2%}")
        else:
            lines.append("  Coherence: unknown")
        uncertainty = cog.get('uncertainty_tracking')
        if uncertainty is not None:
            lines.append(f"  Uncertainty: {uncertainty:.2%}")
        else:
            lines.append("  Uncertainty: unknown")
        lines.append("")
        
        # Affective state
        aff = state.get("affective", {})
        lines.append("Affective State:")
        valence = aff.get('valence')
        if valence is not None:
            lines.append(f"  Valence: {valence:.2f}")
        else:
            lines.append("  Valence: unknown")
        arousal = aff.get('arousal')
        if arousal is not None:
            lines.append(f"  Arousal: {arousal:.2%}")
        else:
            lines.append("  Arousal: unknown")
        
        surprise = aff.get('surprise')
        if surprise is not None:
            lines.append(f'  Surprise: {surprise:.2%}')

        curiosity = aff.get('curiosity_drive')
        if curiosity is not None:
            lines.append(f"  Curiosity: {curiosity:.2%}")
        else:
            lines.append("  Curiosity: unknown")
        lines.append("")
        
        return "\n".join(lines)
    

    
    def record_informational_surprise(self, expectation: str, reality: str) -> None:
        """
        Record surprise at the informational level using embeddings if available.
        """
        semantic_surprise = 0.0
        
        if self.embedding_service:
            try:
                # Generate embeddings for both
                emb_exp = self.embedding_service.generate_embedding(expectation)
                emb_real = self.embedding_service.generate_embedding(reality)
                semantic_surprise = ResponseAnalyzer.calculate_semantic_distance(emb_exp, emb_real)
            except Exception as e:
                logger.debug(f'Embedding-based surprise failed: {e}')
                # Fallback to keyword surprise
                semantic_surprise = ResponseAnalyzer.calculate_informational_surprise(expectation, reality)
        else:
            # Fallback to keyword surprise
            semantic_surprise = ResponseAnalyzer.calculate_informational_surprise(expectation, reality)
        
        # Blend with existing surprise
        current_surprise = self.affect.affective_states.get("surprise", 0.0) or 0.0
        blended_surprise = (current_surprise * 0.3) + (semantic_surprise * 0.7)
        self.affect.update_surprise(blended_surprise)


    def detect_anomalies(self, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Detect significant state changes.
        
        Args:
            threshold: Threshold for anomaly detection
            
        Returns:
            List of anomaly dictionaries
        """
        anomalies = []
        
        # Check physiology anomalies
        phys_anomalies = self.physiology.detect_anomalies()
        anomalies.extend(phys_anomalies)
        
        # Check for significant changes in cognitive state
        history = self.get_history()
        if len(history) >= 2:
            recent = history[-1]
            previous = history[-2]
            
            # Check for large changes (only if both values are not None)
            recent_conf = recent.get("cognitive", {}).get("confidence_level")
            prev_conf = previous.get("cognitive", {}).get("confidence_level")
            
            if recent_conf is not None and prev_conf is not None:
                if abs(recent_conf - prev_conf) > threshold:
                    anomalies.append({
                        "type": "cognitive_state_change",
                        "metric": "confidence_level",
                        "change": recent_conf - prev_conf,
                        "timestamp": recent.get("timestamp", 0.0),
                    })
        
        return anomalies
    
    def track_interoceptive_accuracy(self) -> Dict[str, Any]:
        """
        Track interoceptive accuracy.
        
        Returns:
            Dictionary with accuracy metrics and data quality indicators
        """
        # Get prediction accuracy
        pred_accuracy = self.prediction.get_prediction_accuracy()
        has_data = pred_accuracy is not None
        
        if not has_data:
            # Return with missing data indicator
            return {
                "prediction_accuracy": None,
                "overall_accuracy": None,
                "has_data": False,
                "data_quality": "missing"
            }
        
        return {
            "prediction_accuracy": pred_accuracy,
            "overall_accuracy": pred_accuracy,  # Simplified for now
            "has_data": True,
            "data_quality": "high"  # If we have prediction accuracy, it's based on actual data
        }
    
    def measure_self_awareness_quality(self) -> Optional[float]:
        """
        Measure self-awareness quality.
        
        Returns:
            Quality score (0.0-1.0) if sufficient data, None if insufficient
        """
        # Quality based on:
        # - Prediction accuracy
        # - State coherence
        # - Historical consistency
        
        accuracy = self.prediction.get_prediction_accuracy()
        coherence = self.cognition.states.get("conceptual_coherence", 0.5)
        
        # Check if we have sufficient data
        has_accuracy = accuracy is not None
        # Check coherence data quality
        cog_data_quality = self.cognition.states.get("data_quality", {}).get("conceptual_coherence")
        has_coherence_data = cog_data_quality not in (None, "missing", "insufficient")
        
        # Need at least one metric with data
        if not has_accuracy and not has_coherence_data:
            logger.debug("Insufficient data for self_awareness_quality measurement")
            return None
        
        # Use available metrics, use None for missing ones
        acc_value = accuracy if has_accuracy else None
        coh_value = coherence if has_coherence_data else None
        
        # Combine factors (weight by availability)
        if acc_value is not None and coh_value is not None:
            quality = (acc_value * 0.5 + coh_value * 0.5)
        elif acc_value is not None:
            quality = acc_value  # Use accuracy alone
        elif coh_value is not None:
            quality = coh_value  # Use coherence alone
        else:
            return None
        
        logger.debug(f"Computed self_awareness_quality: {quality:.3f} (accuracy: {acc_value}, coherence: {coh_value})")
        
        return quality

