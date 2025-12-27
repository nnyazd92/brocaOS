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
        # Sample all components
        computational = self.physiology.sample_resources()
        cognitive = self.cognition.sample_cognitive_state()
        
        # Update from epistemic engine if available
        if self.epistemic_bridge:
            self.cognition.update_from_epistemic()
            self.affect.update_from_epistemic()
        
        # Update affective states from cognitive states automatically
        # This ensures certainty_affect, coherence_pleasure, and curiosity_drive are computed
        # when cognitive data is available
        # This is called before sampling affective state to ensure all derived states are computed
        self.affect.update_from_cognitive(self.cognition)
        
        # Log if states were computed (for debugging state transitions)
        if self.affect.affective_states.get("certainty_affect") is not None:
            logger.debug("Affective states updated from cognitive: certainty_affect computed")
        if self.affect.affective_states.get("curiosity_drive") is not None:
            logger.debug("Affective states updated from cognitive: curiosity_drive computed")
        if self.affect.affective_states.get("coherence_pleasure") is not None:
            logger.debug("Affective states updated from cognitive: coherence_pleasure computed")
        
        # Calculate Surprise (Prediction Error) from PREVIOUS turn's prediction vs CURRENT reality
        if hasattr(self, '_last_prediction') and self._last_prediction:
            error = self.prediction.compute_prediction_error(self._last_prediction, computational)
            self.affect.update_surprise(error)
            # Record prediction for accuracy tracking
            self.prediction.record_prediction(
                f"pred_{int(time.time())}",
                self._last_prediction,
                computational
            )
            logger.debug(f"Recorded prediction for accuracy tracking (error: {error:.3f})")

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
            Dictionary with accuracy metrics (always returns defaults instead of None)
        """
        # Get prediction accuracy (defaults to 0.5 if None)
        pred_accuracy = self.prediction.get_prediction_accuracy()
        if pred_accuracy is None:
            pred_accuracy = 0.5
        
        return {
            "prediction_accuracy": pred_accuracy,
            "overall_accuracy": pred_accuracy,  # Simplified for now
        }
    
    def measure_self_awareness_quality(self) -> float:
        """
        Measure self-awareness quality.
        
        Returns:
            Quality score (0.0-1.0), always returns a value (defaults to 0.5 if insufficient data)
        """
        # Quality based on:
        # - Prediction accuracy
        # - State coherence
        # - Historical consistency
        
        accuracy = self.prediction.get_prediction_accuracy()
        coherence = self.cognition.states.get("conceptual_coherence", 0.5)
        
        # Use available metrics, default missing ones to neutral (0.5)
        acc_value = accuracy if accuracy is not None else 0.5
        coh_value = coherence if coherence is not None else 0.5
        
        # Combine factors
        quality = (acc_value * 0.5 + coh_value * 0.5)
        
        logger.debug(f"Computed self_awareness_quality: {quality:.3f} (accuracy: {acc_value:.3f}, coherence: {coh_value:.3f})")
        
        return quality

