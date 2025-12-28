"""
Emotional regulation system using homeostatic control.

Implements PID-based controllers and homeostatic setpoints for maintaining
emotional equilibrium.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class RegulationSignal:
    """Regulation signal from emotional regulator."""
    valence_adjustment: float = 0.0  # Adjustment to valence
    arousal_adjustment: float = 0.0  # Adjustment to arousal
    curiosity_adjustment: float = 0.0  # Adjustment to curiosity
    strategy: str = "maintain"  # Regulation strategy name
    priority: float = 0.0  # Priority of regulation (0.0-1.0)


class HomeostaticEmotionalRegulator:
    """
    PID-based regulator for emotional homeostasis.
    
    Maintains emotional state near target setpoints using proportional-integral-derivative control.
    """
    
    def __init__(
        self,
        target_valence: float = 0.1,  # Slight positive bias
        target_arousal: float = 0.5,  # Moderate activation
        target_curiosity: float = 0.5,  # Balanced exploration
        kp_valence: float = 0.5,
        ki_valence: float = 0.1,
        kd_valence: float = 0.2,
        kp_arousal: float = 0.4,
        ki_arousal: float = 0.08,
        kd_arousal: float = 0.15,
        kp_curiosity: float = 0.3,
        ki_curiosity: float = 0.05,
        kd_curiosity: float = 0.1,
        history_window: int = 20
    ):
        """
        Initialize homeostatic emotional regulator.
        
        Args:
            target_valence: Target valence setpoint
            target_arousal: Target arousal setpoint
            target_curiosity: Target curiosity setpoint
            kp_valence: Proportional gain for valence
            ki_valence: Integral gain for valence
            kd_valence: Derivative gain for valence
            kp_arousal: Proportional gain for arousal
            ki_arousal: Integral gain for arousal
            kd_arousal: Derivative gain for arousal
            kp_curiosity: Proportional gain for curiosity
            ki_curiosity: Integral gain for curiosity
            kd_curiosity: Derivative gain for curiosity
            history_window: Number of recent values to track for derivative/integral
        """
        # Setpoints
        self.target_valence = target_valence
        self.target_arousal = target_arousal
        self.target_curiosity = target_curiosity
        
        # PID gains for each dimension
        self.kp_valence = kp_valence
        self.ki_valence = ki_valence
        self.kd_valence = kd_valence
        self.kp_arousal = kp_arousal
        self.ki_arousal = ki_arousal
        self.kd_arousal = kd_arousal
        self.kp_curiosity = kp_curiosity
        self.ki_curiosity = ki_curiosity
        self.kd_curiosity = kd_curiosity
        
        # History for integral and derivative terms
        self._valence_history: deque = deque(maxlen=history_window)
        self._arousal_history: deque = deque(maxlen=history_window)
        self._curiosity_history: deque = deque(maxlen=history_window)
        
        # Integral error accumulation
        self._valence_integral = 0.0
        self._arousal_integral = 0.0
        self._curiosity_integral = 0.0
        
        # Previous error for derivative
        self._last_valence_error = 0.0
        self._last_arousal_error = 0.0
        self._last_curiosity_error = 0.0
        
        logger.info(
            f"Initialized HomeostaticEmotionalRegulator "
            f"(targets: valence={target_valence:.2f}, arousal={target_arousal:.2f}, curiosity={target_curiosity:.2f})"
        )
    
    def compute_regulation_signal(
        self,
        current_emotion: Dict[str, float]
    ) -> RegulationSignal:
        """
        Compute regulation signal to bring emotion toward setpoints.
        
        Args:
            current_emotion: Current emotional state dictionary with valence, arousal, curiosity
            
        Returns:
            RegulationSignal with adjustments and strategy
        """
        current_valence = current_emotion.get("valence", 0.0)
        current_arousal = current_emotion.get("arousal", 0.5)
        current_curiosity = current_emotion.get("curiosity_drive", 0.5)
        
        # Compute errors (deviation from setpoint)
        valence_error = self.target_valence - current_valence
        arousal_error = self.target_arousal - current_arousal
        curiosity_error = self.target_curiosity - current_curiosity
        
        # Add to history
        self._valence_history.append(current_valence)
        self._arousal_history.append(current_arousal)
        self._curiosity_history.append(current_curiosity)
        
        # PID control for valence
        valence_p = self.kp_valence * valence_error
        
        # Integral term: accumulated error
        self._valence_integral += valence_error
        # Anti-windup: limit integral accumulation
        self._valence_integral = max(-2.0, min(2.0, self._valence_integral))
        valence_i = self.ki_valence * self._valence_integral
        
        # Derivative term: rate of change
        valence_d = self.kd_valence * (valence_error - self._last_valence_error)
        self._last_valence_error = valence_error
        
        valence_adjustment = valence_p + valence_i + valence_d
        
        # PID control for arousal
        arousal_p = self.kp_arousal * arousal_error
        self._arousal_integral += arousal_error
        self._arousal_integral = max(-2.0, min(2.0, self._arousal_integral))
        arousal_i = self.ki_arousal * self._arousal_integral
        arousal_d = self.kd_arousal * (arousal_error - self._last_arousal_error)
        self._last_arousal_error = arousal_error
        arousal_adjustment = arousal_p + arousal_i + arousal_d
        
        # PID control for curiosity
        curiosity_p = self.kp_curiosity * curiosity_error
        self._curiosity_integral += curiosity_error
        self._curiosity_integral = max(-2.0, min(2.0, self._curiosity_integral))
        curiosity_i = self.ki_curiosity * self._curiosity_integral
        curiosity_d = self.kd_curiosity * (curiosity_error - self._last_curiosity_error)
        self._last_curiosity_error = curiosity_error
        curiosity_adjustment = curiosity_p + curiosity_i + curiosity_d
        
        # Clamp adjustments to reasonable ranges
        valence_adjustment = max(-1.0, min(1.0, valence_adjustment))
        arousal_adjustment = max(-1.0, min(1.0, arousal_adjustment))
        curiosity_adjustment = max(-1.0, min(1.0, curiosity_adjustment))
        
        # Determine regulation strategy based on largest deviation
        max_error = max(abs(valence_error), abs(arousal_error), abs(curiosity_error))
        
        if max_error < 0.1:
            strategy = "maintain"
            priority = 0.1
        elif abs(valence_error) == max_error:
            if valence_error < -0.3:
                strategy = "boost_valence"
                priority = min(1.0, abs(valence_error))
            else:
                strategy = "reduce_valence"
                priority = min(1.0, abs(valence_error))
        elif abs(arousal_error) == max_error:
            if arousal_error < -0.3:
                strategy = "boost_arousal"
                priority = min(1.0, abs(arousal_error))
            else:
                strategy = "calm_arousal"
                priority = min(1.0, abs(arousal_error))
        else:
            if curiosity_error < -0.3:
                strategy = "boost_curiosity"
                priority = min(1.0, abs(curiosity_error))
            else:
                strategy = "reduce_curiosity"
                priority = min(1.0, abs(curiosity_error))
        
        logger.debug(
            f"Regulation signal: valence={valence_adjustment:.3f}, "
            f"arousal={arousal_adjustment:.3f}, curiosity={curiosity_adjustment:.3f}, "
            f"strategy={strategy}, priority={priority:.2f}"
        )
        
        return RegulationSignal(
            valence_adjustment=valence_adjustment,
            arousal_adjustment=arousal_adjustment,
            curiosity_adjustment=curiosity_adjustment,
            strategy=strategy,
            priority=priority
        )
    
    def update_setpoints(
        self,
        target_valence: Optional[float] = None,
        target_arousal: Optional[float] = None,
        target_curiosity: Optional[float] = None
    ):
        """Update target setpoints."""
        if target_valence is not None:
            self.target_valence = target_valence
        if target_arousal is not None:
            self.target_arousal = target_arousal
        if target_curiosity is not None:
            self.target_curiosity = target_curiosity


class EmotionalSetpointController:
    """
    Manages adaptive emotional setpoints based on context.
    
    Adjusts target setpoints based on current context (task type, time of day, etc.).
    """
    
    def __init__(
        self,
        base_valence: float = 0.1,
        base_arousal: float = 0.5,
        base_curiosity: float = 0.5
    ):
        """
        Initialize setpoint controller.
        
        Args:
            base_valence: Base valence setpoint
            base_arousal: Base arousal setpoint
            base_curiosity: Base curiosity setpoint
        """
        self.base_valence = base_valence
        self.base_arousal = base_arousal
        self.base_curiosity = base_curiosity
        
        logger.info("Initialized EmotionalSetpointController")
    
    def adjust_setpoints(
        self,
        context: Dict[str, Any],
        current_emotion: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Adjust setpoints based on context.
        
        Args:
            context: Context dictionary (task_type, urgency, etc.)
            current_emotion: Current emotional state
            
        Returns:
            Dictionary with adjusted setpoints (target_valence, target_arousal, target_curiosity)
        """
        # Start with base setpoints
        target_valence = self.base_valence
        target_arousal = self.base_arousal
        target_curiosity = self.base_curiosity
        
        # Adjust based on task type
        task_type = context.get("task_type", "")
        urgency = context.get("urgency", 0.5)
        
        if task_type == "exploration" or task_type == "learning":
            # Higher curiosity for exploration/learning tasks
            target_curiosity = min(0.8, self.base_curiosity + 0.2)
            target_arousal = min(0.7, self.base_arousal + 0.1)  # Slightly higher arousal
        
        elif task_type == "critical" or urgency > 0.8:
            # Lower curiosity, higher arousal for critical tasks
            target_curiosity = max(0.2, self.base_curiosity - 0.2)
            target_arousal = min(0.8, self.base_arousal + 0.2)
        
        elif task_type == "routine":
            # Lower arousal for routine tasks
            target_arousal = max(0.3, self.base_arousal - 0.2)
        
        # Adjust based on recent emotional state (if very far from setpoint, adjust target gradually)
        current_valence = current_emotion.get("valence", 0.0)
        if current_valence < -0.5:
            # Very negative valence: target slightly positive to pull up
            target_valence = 0.2
        elif current_valence > 0.7:
            # Very positive valence: target neutral to stabilize
            target_valence = 0.0
        
        return {
            "target_valence": target_valence,
            "target_arousal": target_arousal,
            "target_curiosity": target_curiosity
        }


class RegulationStrategySelector:
    """
    Selects appropriate regulation strategies based on emotional state.
    
    Maps regulation signals to concrete strategies for influencing cognitive processes.
    """
    
    def __init__(self):
        """Initialize strategy selector."""
        logger.info("Initialized RegulationStrategySelector")
    
    def select_strategies(
        self,
        regulation_signal: RegulationSignal,
        current_emotion: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Select regulation strategies based on regulation signal.
        
        Args:
            regulation_signal: Regulation signal from regulator
            current_emotion: Current emotional state
            
        Returns:
            List of strategy dictionaries with actions to take
        """
        strategies = []
        
        strategy = regulation_signal.strategy
        priority = regulation_signal.priority
        
        if strategy == "boost_valence":
            strategies.append({
                "action": "cognitive_reappraisal",
                "description": "Reappraise negative events more positively",
                "priority": priority,
                "target": "reasoning"
            })
            strategies.append({
                "action": "goal_adjustment",
                "description": "Adjust goals to be more achievable",
                "priority": priority * 0.8,
                "target": "goal_manager"
            })
            strategies.append({
                "action": "focus_learning",
                "description": "Focus on successful learning patterns",
                "priority": priority * 0.7,
                "target": "learning"
            })
        
        elif strategy == "reduce_valence":
            strategies.append({
                "action": "temper_optimism",
                "description": "Increase realism in goal setting",
                "priority": priority,
                "target": "goal_manager"
            })
        
        elif strategy == "calm_arousal":
            strategies.append({
                "action": "reduce_exploration",
                "description": "Focus on known patterns, reduce novelty",
                "priority": priority,
                "target": "reasoning"
            })
            strategies.append({
                "action": "focus_known_patterns",
                "description": "Use proven procedures and skills",
                "priority": priority * 0.8,
                "target": "learning"
            })
        
        elif strategy == "boost_arousal":
            strategies.append({
                "action": "increase_exploration",
                "description": "Engage with novel tasks and patterns",
                "priority": priority,
                "target": "reasoning"
            })
            strategies.append({
                "action": "boost_curiosity_drive",
                "description": "Increase curiosity-driven exploration",
                "priority": priority * 0.9,
                "target": "affect"
            })
        
        elif strategy == "boost_curiosity":
            strategies.append({
                "action": "novel_task_engagement",
                "description": "Engage with novel or challenging tasks",
                "priority": priority,
                "target": "reasoning"
            })
            strategies.append({
                "action": "exploration_boost",
                "description": "Increase exploration-exploitation ratio",
                "priority": priority * 0.8,
                "target": "learning"
            })
        
        elif strategy == "reduce_curiosity":
            strategies.append({
                "action": "focus_exploitation",
                "description": "Focus on known successful strategies",
                "priority": priority,
                "target": "reasoning"
            })
        
        return strategies

