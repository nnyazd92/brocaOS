"""
Emotional appraisal system for cognitive dissonance and learning outcomes.

Implements cognitive appraisal theory to map cognitive dissonance and learning
outcomes to emotional responses (valence, arousal, etc.).
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime, timezone

if TYPE_CHECKING:
    from ..reasoning.cognitive_dissonance import DissonanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class EmotionalAppraisal:
    """Appraisal of an event along cognitive appraisal dimensions."""
    goal_relevance: float = 0.0  # 0.0-1.0: How relevant to current goals?
    goal_congruence: float = 0.0  # -1.0-1.0: Positive = goal-aligned, negative = goal-conflicting
    coping_potential: float = 0.5  # 0.0-1.0: Ability to cope with/address the event
    agency: float = 0.5  # 0.0-1.0: System responsibility/control over event
    certainty: float = 0.5  # 0.0-1.0: Certainty about event characteristics
    novelty: float = 0.0  # 0.0-1.0: Novelty/surprise factor


@dataclass
class EmotionalMapping:
    """Mapping from appraisal to emotional state changes."""
    valence_delta: float = 0.0  # Change in valence (-1.0 to 1.0)
    arousal_delta: float = 0.0  # Change in arousal (0.0 to 1.0)
    curiosity_delta: float = 0.0  # Change in curiosity (0.0 to 1.0)
    surprise_delta: float = 0.0  # Change in surprise (0.0 to 1.0)


class CognitiveAppraisalEngine:
    """
    Appraises events using cognitive appraisal theory dimensions.
    
    Based on cognitive appraisal theory (Lazarus, Scherer), appraises events
    along dimensions: goal relevance, goal congruence, coping potential, agency.
    """
    
    def __init__(self):
        """Initialize cognitive appraisal engine."""
        logger.info("Initialized CognitiveAppraisalEngine")
    
    def appraise_dissonance(
        self,
        dissonance_metrics: "DissonanceMetrics",
        current_goals: List[Dict[str, Any]],
        coping_resources: Optional[Dict[str, float]] = None
    ) -> EmotionalAppraisal:
        """
        Appraise cognitive dissonance along appraisal dimensions.
        
        Args:
            dissonance_metrics: Dissonance metrics from CognitiveDissonanceMonitor
            current_goals: List of current active goals
            coping_resources: Optional resources available for coping (e.g., {"learning_capacity": 0.7})
            
        Returns:
            EmotionalAppraisal with appraisal dimensions
        """
        overall_dissonance = dissonance_metrics.overall_dissonance
        
        # Goal relevance: High if dissonance relates to active goals
        # Assume high relevance if dissonance is significant
        goal_relevance = min(1.0, overall_dissonance * 1.2)  # Scale up slightly
        
        # Goal congruence: Negative if high dissonance (conflicts with goal of consistency)
        # Positive if dissonance is being reduced
        goal_congruence = -overall_dissonance  # High dissonance = goal-incongruent
        
        # Check if dissonance is trending down (improvement)
        if hasattr(dissonance_metrics, 'trend') and dissonance_metrics.trend == "decreasing":
            goal_congruence = 0.2  # Slight positive for improvement
        
        # Coping potential: Based on available resources and system capabilities
        coping_potential = 0.5  # Default moderate
        if coping_resources:
            # Average available resources
            resource_values = [v for v in coping_resources.values() if isinstance(v, (int, float))]
            if resource_values:
                coping_potential = sum(resource_values) / len(resource_values)
        else:
            # Assume moderate coping potential if dissonance is moderate
            # High dissonance = lower coping potential (harder to address)
            coping_potential = max(0.2, 0.8 - overall_dissonance * 0.6)
        
        # Agency: System is responsible for its own consistency
        # Higher if dissonance is behavioral/goal-based (system control)
        # Lower if dissonance is logical/factual (less direct control)
        agency = 0.5  # Default moderate
        behavioral_weight = dissonance_metrics.behavioral_dissonance
        goal_weight = dissonance_metrics.goal_dissonance
        logical_weight = dissonance_metrics.logical_dissonance + dissonance_metrics.factual_dissonance
        
        if behavioral_weight + goal_weight > logical_weight:
            agency = 0.7  # Higher agency for behavioral/goal issues
        else:
            agency = 0.4  # Lower agency for logical/factual issues
        
        # Certainty: Higher certainty for clear dissonance signals
        certainty = min(1.0, overall_dissonance * 1.5)
        
        # Novelty: High if unexpected dissonance (if trend is increasing unexpectedly)
        novelty = 0.0
        if hasattr(dissonance_metrics, 'trend'):
            if dissonance_metrics.trend == "increasing" and overall_dissonance > 0.5:
                novelty = 0.6  # Unexpected increase
        
        return EmotionalAppraisal(
            goal_relevance=goal_relevance,
            goal_congruence=goal_congruence,
            coping_potential=coping_potential,
            agency=agency,
            certainty=certainty,
            novelty=novelty
        )
    
    def appraise_learning_outcome(
        self,
        outcome: Dict[str, Any],
        expected_outcome: Optional[Dict[str, Any]] = None
    ) -> EmotionalAppraisal:
        """
        Appraise a learning outcome along appraisal dimensions.
        
        Args:
            outcome: Learning outcome dictionary with success, effectiveness, etc.
            expected_outcome: Optional expected outcome for comparison
            
        Returns:
            EmotionalAppraisal for the learning outcome
        """
        success = outcome.get("success", False)
        effectiveness = outcome.get("effectiveness", 0.0)
        dissonance_reduction = outcome.get("dissonance_reduction", 0.0)
        improvement = outcome.get("improvement", 0.0)
        
        # Goal relevance: High if learning outcome affects important goals
        goal_relevance = 0.7  # Learning outcomes are generally relevant
        
        # Goal congruence: Positive for success, negative for failure
        if success:
            goal_congruence = 0.6  # Positive alignment with learning goals
            if dissonance_reduction > 0.0:
                goal_congruence = 0.8  # Strong positive if reducing dissonance
        else:
            goal_congruence = -0.4  # Negative if learning failed
        
        # Coping potential: High if learning was successful (system can improve)
        coping_potential = 0.7 if success else 0.3
        
        # Agency: High for learning outcomes (system controls its learning)
        agency = 0.8
        
        # Certainty: Based on outcome clarity
        certainty = 0.8 if success else 0.6
        
        # Novelty: Higher for unexpected outcomes
        novelty = 0.0
        if expected_outcome:
            expected_success = expected_outcome.get("success", True)
            if success != expected_success:
                novelty = 0.5  # Unexpected outcome
        
        return EmotionalAppraisal(
            goal_relevance=goal_relevance,
            goal_congruence=goal_congruence,
            coping_potential=coping_potential,
            agency=agency,
            certainty=certainty,
            novelty=novelty
        )


class DissonanceEmotionalMapper:
    """
    Maps cognitive dissonance to emotional responses.
    
    Translates appraisal dimensions into emotional state changes (valence, arousal).
    """
    
    def __init__(
        self,
        valence_sensitivity: float = 1.0,
        arousal_sensitivity: float = 1.0,
        curiosity_sensitivity: float = 0.5
    ):
        """
        Initialize emotional mapper.
        
        Args:
            valence_sensitivity: Sensitivity multiplier for valence changes
            arousal_sensitivity: Sensitivity multiplier for arousal changes
            curiosity_sensitivity: Sensitivity multiplier for curiosity changes
        """
        self.valence_sensitivity = valence_sensitivity
        self.arousal_sensitivity = arousal_sensitivity
        self.curiosity_sensitivity = curiosity_sensitivity
        
        logger.info("Initialized DissonanceEmotionalMapper")
    
    def map_to_emotion(
        self,
        dissonance_metrics: "DissonanceMetrics",
        appraisal: EmotionalAppraisal
    ) -> EmotionalMapping:
        """
        Map cognitive dissonance and appraisal to emotional state changes.
        
        Args:
            dissonance_metrics: Dissonance metrics
            appraisal: Emotional appraisal of the dissonance
            
        Returns:
            EmotionalMapping with valence/arousal/curiosity deltas
        """
        overall_dissonance = dissonance_metrics.overall_dissonance
        
        # Valence: Negative for high dissonance (goal-incongruent)
        # Positive for dissonance reduction or low dissonance
        valence_delta = appraisal.goal_congruence * self.valence_sensitivity
        
        # Adjust based on coping potential: Higher coping = less negative impact
        coping_adjustment = (appraisal.coping_potential - 0.5) * 0.3
        valence_delta += coping_adjustment
        
        # Clamp to reasonable range
        valence_delta = max(-1.0, min(1.0, valence_delta))
        
        # Arousal: High for high dissonance + high goal relevance
        # Low arousal for low coping potential (helplessness)
        arousal_delta = (overall_dissonance * appraisal.goal_relevance * self.arousal_sensitivity)
        
        # Reduce arousal if low coping potential (helplessness reduces activation)
        if appraisal.coping_potential < 0.3:
            arousal_delta *= 0.5
        
        # Increase arousal if high agency (system can act)
        if appraisal.agency > 0.6:
            arousal_delta *= 1.2
        
        arousal_delta = max(-1.0, min(1.0, arousal_delta))
        
        # Curiosity: Higher for moderate dissonance with high coping potential
        # (suggests interesting problem to solve)
        if overall_dissonance > 0.2 and overall_dissonance < 0.6 and appraisal.coping_potential > 0.5:
            curiosity_delta = overall_dissonance * appraisal.coping_potential * self.curiosity_sensitivity
        else:
            curiosity_delta = 0.0
        
        curiosity_delta = max(-1.0, min(1.0, curiosity_delta))
        
        # Surprise: Based on novelty and unexpectedness
        surprise_delta = appraisal.novelty * 0.5
        surprise_delta = max(0.0, min(1.0, surprise_delta))
        
        logger.debug(
            f"Mapped dissonance to emotion: valence={valence_delta:.3f}, "
            f"arousal={arousal_delta:.3f}, curiosity={curiosity_delta:.3f}, surprise={surprise_delta:.3f}"
        )
        
        return EmotionalMapping(
            valence_delta=valence_delta,
            arousal_delta=arousal_delta,
            curiosity_delta=curiosity_delta,
            surprise_delta=surprise_delta
        )


class LearningOutcomeAppraiser:
    """
    Appraises learning outcomes emotionally.
    
    Maps learning successes/failures to emotional responses.
    """
    
    def __init__(self):
        """Initialize learning outcome appraiser."""
        logger.info("Initialized LearningOutcomeAppraiser")
    
    def appraise_and_map(
        self,
        outcome: Dict[str, Any],
        expected_outcome: Optional[Dict[str, Any]] = None
    ) -> EmotionalMapping:
        """
        Appraise learning outcome and map to emotional changes.
        
        Args:
            outcome: Learning outcome dictionary
            expected_outcome: Optional expected outcome
            
        Returns:
            EmotionalMapping with emotional state changes
        """
        appraisal_engine = CognitiveAppraisalEngine()
        appraisal = appraisal_engine.appraise_learning_outcome(outcome, expected_outcome)
        
        success = outcome.get("success", False)
        effectiveness = outcome.get("effectiveness", 0.0)
        dissonance_reduction = outcome.get("dissonance_reduction", 0.0)
        
        # Valence: Positive for success, negative for failure
        if success:
            valence_delta = 0.3 + (effectiveness * 0.4)  # 0.3-0.7 for success
            if dissonance_reduction > 0.0:
                valence_delta += dissonance_reduction * 0.3  # Bonus for dissonance reduction
        else:
            valence_delta = -0.2 - (abs(effectiveness) * 0.3)  # -0.2 to -0.5 for failure
        
        valence_delta = max(-1.0, min(1.0, valence_delta))
        
        # Arousal: Moderate increase for success (satisfaction), decrease for failure
        if success:
            arousal_delta = 0.2  # Moderate positive arousal
        else:
            arousal_delta = -0.1  # Slight decrease
        
        arousal_delta = max(-1.0, min(1.0, arousal_delta))
        
        # Curiosity: Higher for successful learning (encourages more exploration)
        if success:
            curiosity_delta = 0.1 + (effectiveness * 0.1)  # 0.1-0.2
        else:
            curiosity_delta = 0.0  # No change
        
        curiosity_delta = max(-1.0, min(1.0, curiosity_delta))
        
        # Surprise: Based on novelty (unexpected outcomes)
        surprise_delta = appraisal.novelty * 0.3
        surprise_delta = max(0.0, min(1.0, surprise_delta))
        
        return EmotionalMapping(
            valence_delta=valence_delta,
            arousal_delta=arousal_delta,
            curiosity_delta=curiosity_delta,
            surprise_delta=surprise_delta
        )

