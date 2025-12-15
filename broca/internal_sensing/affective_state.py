"""
Affective state monitoring for internal sensing.

Monitors affective states including valence, arousal, curiosity, and satisfaction.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .cognitive_state import CognitiveStateMonitor

logger = logging.getLogger(__name__)


class ComputationalAffectMonitor:
    """
    Monitor computational affective states.
    
    Tracks:
    - Valence: Positive/negative evaluation (-1 to 1)
    - Arousal: Activation level (0-1)
    - Certainty affect: Emotional aspect of confidence
    - Curiosity drive: Motivation to explore
    - Coherence pleasure: Satisfaction from understanding
    """
    
    def __init__(self) -> None:
        """Initialize computational affect monitor."""
        self.affective_states: Dict[str, Optional[float]] = {
            "valence": None,  # Unknown until computed
            "arousal": None,  # Unknown until computed
            "certainty_affect": None,  # Unknown until computed
            "curiosity_drive": None,  # Unknown until computed
            "coherence_pleasure": None,  # Unknown until computed
        }
        
        self._motivational_drives: Dict[str, float] = {}
        self._satisfaction_patterns: List[Dict[str, Any]] = []
        
        logger.info("Initialized ComputationalAffectMonitor")
    
    def compute_valence(self, positive_score: float, negative_score: float) -> None:
        """
        Compute valence from positive and negative scores.
        
        Args:
            positive_score: Positive evaluation score (0.0-1.0)
            negative_score: Negative evaluation score (0.0-1.0)
        """
        positive_score = max(0.0, min(1.0, positive_score))
        negative_score = max(0.0, min(1.0, negative_score))
        
        # Valence is difference: positive - negative, normalized to -1 to 1
        if positive_score + negative_score == 0:
            valence = 0.0
        else:
            valence = (positive_score - negative_score) / (positive_score + negative_score)
        
        self.affective_states["valence"] = max(-1.0, min(1.0, valence))
    
    def compute_arousal(self, activation_level: float) -> None:
        """
        Compute arousal from activation level.
        
        Args:
            activation_level: Activation level (0.0-1.0)
        """
        self.affective_states["arousal"] = max(0.0, min(1.0, activation_level))
    
    def update_certainty_affect(self, confidence: float) -> None:
        """
        Update certainty affect from confidence level.
        
        Args:
            confidence: Confidence level (0.0-1.0)
        """
        # Certainty affect is directly related to confidence
        self.affective_states["certainty_affect"] = max(0.0, min(1.0, confidence))
    
    def compute_curiosity_drive(self, uncertainty: float, interest: float) -> None:
        """
        Compute curiosity drive from uncertainty and interest.
        
        Args:
            uncertainty: Uncertainty level (0.0-1.0)
            interest: Interest level (0.0-1.0)
        """
        uncertainty = max(0.0, min(1.0, uncertainty))
        interest = max(0.0, min(1.0, interest))
        
        # Curiosity is combination of uncertainty and interest
        curiosity = (uncertainty * 0.5 + interest * 0.5)
        self.affective_states["curiosity_drive"] = curiosity
    
    def update_coherence_pleasure(self, coherence: float) -> None:
        """
        Update coherence pleasure from coherence level.
        
        Args:
            coherence: Coherence level (0.0-1.0)
        """
        # Pleasure increases with coherence
        self.affective_states["coherence_pleasure"] = max(0.0, min(1.0, coherence))
    
    def update_from_cognitive(self, cognitive_monitor: "CognitiveStateMonitor") -> None:
        """
        Update affective states from cognitive monitor.
        
        Args:
            cognitive_monitor: CognitiveStateMonitor instance
        """
        # Update certainty affect from confidence
        confidence = cognitive_monitor.states.get("confidence_level")
        if confidence is not None:
            self.update_certainty_affect(confidence)
        
        # Update coherence pleasure from coherence
        coherence = cognitive_monitor.states.get("conceptual_coherence")
        if coherence is not None:
            self.update_coherence_pleasure(coherence)
        
        # Update curiosity from uncertainty
        uncertainty = cognitive_monitor.states.get("uncertainty_tracking")
        # Use attention as proxy for interest
        attention_total = sum(cognitive_monitor.states.get("attention_allocation", {}).values())
        interest = min(attention_total, 1.0) if attention_total > 0 else 0.0
        
        if uncertainty is not None:
            self.compute_curiosity_drive(uncertainty, interest)
    
    def record_motivational_drive(self, drive_type: str, level: float) -> None:
        """
        Record a motivational drive.
        
        Args:
            drive_type: Type of drive (e.g., "exploration", "completion")
            level: Drive level (0.0-1.0)
        """
        self._motivational_drives[drive_type] = max(0.0, min(1.0, level))
    
    def get_motivational_drives(self) -> Dict[str, float]:
        """
        Get current motivational drives.
        
        Returns:
            Dictionary of drive types to levels
        """
        return self._motivational_drives.copy()
    
    def record_satisfaction(self, task_id: str, level: float) -> None:
        """
        Record satisfaction level for a task.
        
        Args:
            task_id: Unique identifier for the task
            level: Satisfaction level (0.0-1.0)
        """
        self._satisfaction_patterns.append({
            "task_id": task_id,
            "type": "satisfaction",
            "level": max(0.0, min(1.0, level)),
            "timestamp": time.time(),
        })
    
    def record_frustration(self, task_id: str, level: float) -> None:
        """
        Record frustration level for a task.
        
        Args:
            task_id: Unique identifier for the task
            level: Frustration level (0.0-1.0)
        """
        self._satisfaction_patterns.append({
            "task_id": task_id,
            "type": "frustration",
            "level": max(0.0, min(1.0, level)),
            "timestamp": time.time(),
        })
    
    def get_satisfaction_patterns(self) -> List[Dict[str, Any]]:
        """
        Get satisfaction/frustration patterns.
        
        Returns:
            List of pattern dictionaries
        """
        return self._satisfaction_patterns.copy()
    
    def sample_affective_state(self) -> Dict[str, Any]:
        """
        Sample complete affective state.
        
        Returns:
            Dictionary containing all affective states with timestamp
        """
        return {
            **self.affective_states,
            "motivational_drives": self._motivational_drives.copy(),
            "timestamp": time.time(),
        }

