"""
Integrated interoceptive awareness.

Unifies all internal sensing components into a single interoceptive map.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List
from collections import deque

from .computational_physiology import ComputationalPhysiologyMonitor
from .cognitive_state import CognitiveStateMonitor
from .affective_state import ComputationalAffectMonitor
from .predictive_interoception import PredictiveInteroception

logger = logging.getLogger(__name__)


class IntegratedInteroception:
    """
    Integrated interoceptive awareness system.
    
    Combines all internal sensing components into unified awareness.
    """
    
    def __init__(self, history_window: int = 60) -> None:
        """
        Initialize integrated interoception.
        
        Args:
            history_window: Number of samples to keep in history
        """
        self.physiology = ComputationalPhysiologyMonitor()
        self.cognition = CognitiveStateMonitor()
        self.affect = ComputationalAffectMonitor()
        self.prediction = PredictiveInteroception()
        
        self.interoceptive_map: Dict[str, Any] = {}
        self.history_window = history_window
        self._history: deque = deque(maxlen=history_window)
        
        logger.info("Initialized IntegratedInteroception")
    
    def generate_interoceptive_awareness(self) -> Dict[str, Any]:
        """
        Generate unified interoceptive awareness.
        
        Returns:
            Dictionary containing unified internal state
        """
        # Sample all components
        computational = self.physiology.sample_resources()
        cognitive = self.cognition.sample_cognitive_state()
        affective = self.affect.sample_affective_state()
        
        # Generate predictions
        resource_prediction = self.prediction.predict_resources(self.physiology, horizon=3)
        cognitive_prediction = self.prediction.predict_cognitive_load(self.cognition, horizon=2)
        affective_prediction = self.prediction.predict_affective_state(self.affect, horizon=1)
        
        # Create unified state
        unified_state = {
            "computational": computational,
            "cognitive": cognitive,
            "affective": affective,
            "predictive": {
                "resources": resource_prediction,
                "cognitive": cognitive_prediction,
                "affective": affective_prediction,
            },
            "timestamp": time.time(),
        }
        
        # Update interoceptive map
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
        state = self.interoceptive_map
        
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
        curiosity = aff.get('curiosity_drive')
        if curiosity is not None:
            lines.append(f"  Curiosity: {curiosity:.2%}")
        else:
            lines.append("  Curiosity: unknown")
        lines.append("")
        
        return "\n".join(lines)
    
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
            Dictionary with accuracy metrics (may contain None values)
        """
        # Get prediction accuracy (may be None)
        pred_accuracy = self.prediction.get_prediction_accuracy()
        
        return {
            "prediction_accuracy": pred_accuracy,
            "overall_accuracy": pred_accuracy,  # Simplified for now
        }
    
    def measure_self_awareness_quality(self) -> Optional[float]:
        """
        Measure self-awareness quality.
        
        Returns:
            Quality score (0.0-1.0), or None if required metrics unavailable
        """
        # Quality based on:
        # - Prediction accuracy
        # - State coherence
        # - Historical consistency
        
        accuracy = self.prediction.get_prediction_accuracy()
        coherence = self.cognition.states.get("conceptual_coherence")
        
        # Need at least one metric to calculate quality
        if accuracy is None and coherence is None:
            return None
        
        # Use available metrics, default missing ones to neutral (0.5)
        acc_value = accuracy if accuracy is not None else 0.5
        coh_value = coherence if coherence is not None else 0.5
        
        # Combine factors
        quality = (acc_value * 0.5 + coh_value * 0.5)
        
        return quality

