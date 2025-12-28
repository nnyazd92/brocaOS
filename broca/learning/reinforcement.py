"""
Reinforcement learning for skill improvement.

Implements basic reinforcement learning algorithms for
improving skill selection and procedure application.
"""

from __future__ import annotations

import logging
import random
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class ReinforcementLearner:
    """
    Basic reinforcement learning for skill improvement.
    
    Uses Q-learning for skill selection and procedure improvement.
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        dissonance_reward_weight: float = 1.0
    ):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.dissonance_reward_weight = dissonance_reward_weight
        self.q_table: Dict[str, Dict[str, float]] = {}  # state -> action -> Q-value
        self.exploration_rate = 0.1
        
        logger.info(f"Initialized ReinforcementLearner (LR: {learning_rate}, DF: {discount_factor}, Dissonance Weight: {dissonance_reward_weight})")
    
    def select_action(
        self,
        state: str,
        available_actions: List[str],
        current_dissonance: Optional[float] = None
    ) -> str:
        """
        Select an action using ε-greedy policy with adaptive exploration based on dissonance.
        
        Args:
            state: Current state identifier
            available_actions: List of available actions
            current_dissonance: Optional current dissonance level (for adaptive exploration)
            
        Returns:
            Selected action
        """
        if not available_actions:
            return ""
        
        # Adaptive exploration: explore more when dissonance is high
        effective_exploration_rate = self.exploration_rate
        if current_dissonance is not None and current_dissonance > 0.5:
            # Increase exploration when dissonance is high (try new approaches)
            effective_exploration_rate = min(0.5, self.exploration_rate * (1.0 + current_dissonance))
        
        # Initialize Q-values for state if not present
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in available_actions}
        
        # Ensure all actions have Q-values
        for action in available_actions:
            if action not in self.q_table[state]:
                self.q_table[state][action] = 0.0
        
        # ε-greedy action selection with adaptive exploration
        if random.random() < effective_exploration_rate:
            # Explore: random action
            return random.choice(available_actions)
        else:
            # Exploit: best known action
            best_actions = []
            best_q = float('-inf')
            
            for action in available_actions:
                q_value = self.q_table[state].get(action, 0.0)
                if q_value > best_q:
                    best_q = q_value
                    best_actions = [action]
                elif q_value == best_q:
                    best_actions.append(action)
            
            return random.choice(best_actions) if best_actions else random.choice(available_actions)
    
    def update_q_value(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str,
        next_available_actions: List[str],
        dissonance_reward: Optional[float] = None
    ) -> None:
        """
        Update Q-value using Q-learning update rule with optional dissonance reward.
        
        Q(s, a) = Q(s, a) + α * [r + γ * max_a' Q(s', a') - Q(s, a)]
        
        If dissonance_reward is provided, it's incorporated into the reward signal.
        """
        # Combine base reward with dissonance reward
        total_reward = reward
        if dissonance_reward is not None:
            total_reward += self.dissonance_reward_weight * dissonance_reward
        
        # Initialize states if not present
        if state not in self.q_table:
            self.q_table[state] = {}
        if next_state not in self.q_table:
            self.q_table[next_state] = {action: 0.0 for action in next_available_actions}
        
        # Get current Q-value
        current_q = self.q_table[state].get(action, 0.0)
        
        # Get max Q-value for next state
        max_next_q = 0.0
        if next_available_actions:
            next_q_values = [self.q_table[next_state].get(a, 0.0) for a in next_available_actions]
            max_next_q = max(next_q_values) if next_q_values else 0.0
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (total_reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state][action] = new_q
        
        logger.debug(
            f"Updated Q({state}, {action}): {current_q:.3f} -> {new_q:.3f} "
            f"(reward: {reward:.2f}, dissonance: {dissonance_reward or 0.0:.2f}, total: {total_reward:.2f})"
        )
    
    def get_dissonance_reward(self, dissonance_before: float, dissonance_after: float) -> float:
        """
        Generate reward signal from dissonance change.
        
        Args:
            dissonance_before: Dissonance before action
            dissonance_after: Dissonance after action
            
        Returns:
            Reward signal: positive for reduction, negative for increase
        """
        dissonance_change = dissonance_before - dissonance_after  # Positive = reduction (good)
        # Normalize to [-1, 1] range
        reward = dissonance_change  # Already in reasonable range
        return reward
    
    def get_best_action(self, state: str) -> Optional[str]:
        """Get best action for a state."""
        if state not in self.q_table or not self.q_table[state]:
            return None
        
        best_actions = []
        best_q = float('-inf')
        
        for action, q_value in self.q_table[state].items():
            if q_value > best_q:
                best_q = q_value
                best_actions = [action]
            elif q_value == best_q:
                best_actions.append(action)
        
        return random.choice(best_actions) if best_actions else None
    
    def decay_exploration(self, decay_rate: float = 0.99):
        """Decay exploration rate over time."""
        self.exploration_rate = max(0.01, self.exploration_rate * decay_rate)
    
    def get_state_statistics(self, state: str) -> Dict[str, Any]:
        """Get statistics for a state."""
        if state not in self.q_table:
            return {}
        
        actions = self.q_table[state]
        if not actions:
            return {}
        
        q_values = list(actions.values())
        
        return {
            "action_count": len(actions),
            "max_q_value": max(q_values),
            "min_q_value": min(q_values),
            "avg_q_value": sum(q_values) / len(q_values),
            "best_action": self.get_best_action(state),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert learner to dictionary representation."""
        return {
            "q_table": self.q_table,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "exploration_rate": self.exploration_rate,
            "dissonance_reward_weight": self.dissonance_reward_weight,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReinforcementLearner:
        """Create learner from dictionary representation."""
        learner = cls(
            learning_rate=data.get("learning_rate", 0.1),
            discount_factor=data.get("discount_factor", 0.9),
            dissonance_reward_weight=data.get("dissonance_reward_weight", 1.0)
        )
        learner.q_table = data.get("q_table", {})
        learner.exploration_rate = data.get("exploration_rate", 0.1)
        return learner
