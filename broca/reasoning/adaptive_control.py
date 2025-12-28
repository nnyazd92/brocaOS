"""
Adaptive control system for learning-reasoning integration.

Implements PID-like controllers for adaptive learning rate adjustment,
skill weight control, and exploration balance based on cognitive dissonance.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from collections import deque

if TYPE_CHECKING:
    from .cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics

logger = logging.getLogger(__name__)


class AdaptiveLearningRateController:
    """
    PID-based adaptive learning rate controller.
    
    Adjusts learning rates based on dissonance metrics:
    - Proportional (P): Current dissonance level
    - Integral (I): Cumulative dissonance over time
    - Derivative (D): Rate of change in dissonance
    """
    
    def __init__(
        self,
        base_learning_rate: float = 0.1,
        kp: float = 0.5,  # Proportional gain
        ki: float = 0.1,  # Integral gain
        kd: float = 0.2,  # Derivative gain
        min_learning_rate: float = 0.01,
        max_learning_rate: float = 1.0,
        history_window: int = 50
    ):
        """
        Initialize adaptive learning rate controller.
        
        Args:
            base_learning_rate: Base learning rate
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
            min_learning_rate: Minimum learning rate
            max_learning_rate: Maximum learning rate
            history_window: Number of recent values to track for integral/derivative
        """
        self.base_learning_rate = base_learning_rate
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_learning_rate = min_learning_rate
        self.max_learning_rate = max_learning_rate
        self.history_window = history_window
        
        # Tracking for integral and derivative terms
        self.dissonance_history: deque = deque(maxlen=history_window)
        self.integral_error = 0.0
        self.last_dissonance = None
        
        logger.info(f"Initialized AdaptiveLearningRateController (base LR: {base_learning_rate})")
    
    def compute_learning_rate(self, current_dissonance: float) -> float:
        """
        Compute adaptive learning rate using PID control.
        
        Args:
            current_dissonance: Current dissonance level (0.0-1.0)
            
        Returns:
            Adaptive learning rate
        """
        # Target is low dissonance (0.0)
        error = current_dissonance - 0.0  # Error from target (low dissonance)
        
        # Proportional term: current error
        p_term = self.kp * error
        
        # Integral term: accumulated error over time
        self.dissonance_history.append(current_dissonance)
        if len(self.dissonance_history) > 1:
            self.integral_error = sum(self.dissonance_history) / len(self.dissonance_history)
        else:
            self.integral_error = current_dissonance
        i_term = self.ki * self.integral_error
        
        # Derivative term: rate of change
        d_term = 0.0
        if self.last_dissonance is not None:
            d_error = current_dissonance - self.last_dissonance
            d_term = self.kd * d_error
        
        self.last_dissonance = current_dissonance
        
        # PID output: adjust learning rate based on error
        # High error (high dissonance) -> increase learning rate (learn faster)
        # Low error (low dissonance) -> decrease learning rate (stabilize)
        adjustment = p_term + i_term + d_term
        
        # Convert adjustment to learning rate (inverse relationship: high dissonance -> high LR)
        adaptive_lr = self.base_learning_rate * (1.0 + adjustment)
        
        # Clamp to bounds
        adaptive_lr = max(self.min_learning_rate, min(self.max_learning_rate, adaptive_lr))
        
        logger.debug(
            f"Adaptive LR: {adaptive_lr:.4f} "
            f"(dissonance: {current_dissonance:.3f}, P: {p_term:.3f}, I: {i_term:.3f}, D: {d_term:.3f})"
        )
        
        return adaptive_lr


class DissonanceFeedbackController:
    """
    Controls feedback loop strength based on dissonance.
    
    Adjusts how strongly feedback loops influence the system
    based on current dissonance levels and trends.
    """
    
    def __init__(
        self,
        base_strength: float = 1.0,
        high_dissonance_boost: float = 1.5,
        low_dissonance_damp: float = 0.7,
        threshold_high: float = 0.6,
        threshold_low: float = 0.2
    ):
        """
        Initialize feedback controller.
        
        Args:
            base_strength: Base feedback strength
            high_dissonance_boost: Multiplier when dissonance is high
            low_dissonance_damp: Multiplier when dissonance is low
            threshold_high: Dissonance threshold for high state
            threshold_low: Dissonance threshold for low state
        """
        self.base_strength = base_strength
        self.high_dissonance_boost = high_dissonance_boost
        self.low_dissonance_damp = low_dissonance_damp
        self.threshold_high = threshold_high
        self.threshold_low = threshold_low
        
        logger.info("Initialized DissonanceFeedbackController")
    
    def compute_feedback_strength(self, current_dissonance: float) -> float:
        """
        Compute feedback loop strength based on dissonance.
        
        Args:
            current_dissonance: Current dissonance level
            
        Returns:
            Feedback strength multiplier
        """
        if current_dissonance > self.threshold_high:
            # High dissonance: strengthen feedback to correct faster
            strength = self.base_strength * self.high_dissonance_boost
        elif current_dissonance < self.threshold_low:
            # Low dissonance: dampen feedback to maintain stability
            strength = self.base_strength * self.low_dissonance_damp
        else:
            # Medium dissonance: use base strength
            strength = self.base_strength
        
        return strength


class SkillWeightController:
    """
    Dynamically adjusts skill weights based on dissonance effectiveness.
    
    Increases weights for skills that reduce dissonance,
    decreases weights for skills that increase dissonance.
    """
    
    def __init__(
        self,
        base_weight: float = 1.0,
        max_weight: float = 3.0,
        min_weight: float = 0.1,
        effectiveness_threshold: float = 0.1
    ):
        """
        Initialize skill weight controller.
        
        Args:
            base_weight: Base weight for skills
            max_weight: Maximum weight (for highly effective skills)
            min_weight: Minimum weight (for ineffective skills)
            effectiveness_threshold: Threshold for considering skill effective
        """
        self.base_weight = base_weight
        self.max_weight = max_weight
        self.min_weight = min_weight
        self.effectiveness_threshold = effectiveness_threshold
        
        # Track skill effectiveness
        self.skill_weights: Dict[str, float] = {}
        
        logger.info("Initialized SkillWeightController")
    
    def get_skill_weight(self, skill_name: str, dissonance_impact: float) -> float:
        """
        Get weight for a skill based on its dissonance impact.
        
        Args:
            skill_name: Name of the skill
            dissonance_impact: Average dissonance impact (positive = reduction)
            
        Returns:
            Weight for the skill
        """
        if skill_name not in self.skill_weights:
            self.skill_weights[skill_name] = self.base_weight
        
        # Update weight based on effectiveness
        if dissonance_impact > self.effectiveness_threshold:
            # Effective skill: increase weight
            weight_change = min(0.1, dissonance_impact * 0.5)
            self.skill_weights[skill_name] = min(
                self.max_weight,
                self.skill_weights[skill_name] + weight_change
            )
        elif dissonance_impact < -self.effectiveness_threshold:
            # Ineffective skill: decrease weight
            weight_change = max(-0.1, dissonance_impact * 0.5)
            self.skill_weights[skill_name] = max(
                self.min_weight,
                self.skill_weights[skill_name] + weight_change
            )
        
        return self.skill_weights[skill_name]
    
    def reset_skill_weight(self, skill_name: str):
        """Reset a skill's weight to base value."""
        self.skill_weights[skill_name] = self.base_weight

