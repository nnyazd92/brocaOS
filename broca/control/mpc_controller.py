"""
Model Predictive Control (MPC) for goal pursuit.

Implements MPC controller for predictive goal pursuit with constraints.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
# numpy import removed - using simple math instead

if TYPE_CHECKING:
    from ..reasoning.goal_manager import GoalManager, Goal

logger = logging.getLogger(__name__)


@dataclass
class MPCConfig:
    """Configuration for MPC controller."""
    prediction_horizon: int = 5  # Steps ahead to predict
    control_horizon: int = 3  # Steps ahead to control
    state_dim: int = 2  # Dimension of state (e.g., [progress, velocity])
    control_dim: int = 1  # Dimension of control (e.g., effort)
    max_control: float = 1.0
    min_control: float = 0.0


@dataclass
class MPCState:
    """State for MPC."""
    progress: float  # Goal progress (0.0 to 1.0)
    velocity: float  # Rate of progress change
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MPCController:
    """
    Model Predictive Control for goal pursuit.
    
    Predicts future goal progress and optimizes control actions
    to achieve goals efficiently.
    """
    
    def __init__(
        self,
        goal_manager: Optional["GoalManager"] = None,
        config: Optional[MPCConfig] = None
    ):
        """
        Initialize MPC controller.
        
        Args:
            goal_manager: Optional GoalManager for goal tracking
            config: Optional MPC configuration
        """
        self.goal_manager = goal_manager
        self.config = config or MPCConfig()
        
        # State history
        self.state_history: List[MPCState] = []
        
        # Control history
        self.control_history: List[float] = []
        
        logger.info(
            f"Initialized MPCController "
            f"(horizon={self.config.prediction_horizon}, "
            f"control_horizon={self.config.control_horizon})"
        )
    
    def compute_control(
        self,
        goal: "Goal",
        current_state: Optional[MPCState] = None
    ) -> float:
        """
        Compute optimal control action for goal pursuit.
        
        Args:
            goal: Goal to pursue
            current_state: Optional current state
            
        Returns:
            Optimal control effort (0.0 to 1.0)
        """
        # Get or create current state
        if current_state is None:
            current_state = self._get_current_state(goal)
        
        # Predict future states
        predicted_states = self._predict_states(current_state, self.config.prediction_horizon)
        
        # Optimize control sequence
        optimal_control = self._optimize_control(current_state, predicted_states, goal)
        
        # Apply first control action
        control_action = optimal_control[0] if optimal_control else 0.5
        
        # Clamp control
        control_action = max(self.config.min_control, min(self.config.max_control, control_action))
        
        # Record
        self.control_history.append(control_action)
        if len(self.control_history) > 1000:
            self.control_history = self.control_history[-1000:]
        
        logger.debug(
            f"MPC control for goal '{goal.name}': "
            f"progress={current_state.progress:.2f}, "
            f"control={control_action:.2f}"
        )
        
        return control_action
    
    def _get_current_state(self, goal: "Goal") -> MPCState:
        """Get current state for goal."""
        progress = goal.progress
        
        # Compute velocity (rate of change)
        velocity = 0.0
        if len(self.state_history) > 0:
            last_state = self.state_history[-1]
            time_diff = (datetime.now(timezone.utc) - last_state.timestamp).total_seconds()
            if time_diff > 0:
                velocity = (progress - last_state.progress) / time_diff
        
        state = MPCState(progress=progress, velocity=velocity)
        self.state_history.append(state)
        
        if len(self.state_history) > 1000:
            self.state_history = self.state_history[-1000:]
        
        return state
    
    def _predict_states(
        self,
        current_state: MPCState,
        horizon: int
    ) -> List[MPCState]:
        """Predict future states."""
        predicted = []
        state = current_state
        
        for step in range(horizon):
            # Simple linear prediction model
            # progress(t+1) = progress(t) + velocity(t) * dt
            # velocity(t+1) = velocity(t) * damping
            
            dt = 1.0  # Assume 1 time unit per step
            damping = 0.9  # Velocity damping
            
            new_progress = state.progress + state.velocity * dt
            new_velocity = state.velocity * damping
            
            # Clamp progress
            new_progress = max(0.0, min(1.0, new_progress))
            
            predicted_state = MPCState(
                progress=new_progress,
                velocity=new_velocity
            )
            predicted.append(predicted_state)
            state = predicted_state
        
        return predicted
    
    def _optimize_control(
        self,
        current_state: MPCState,
        predicted_states: List[MPCState],
        goal: "Goal"
    ) -> List[float]:
        """
        Optimize control sequence.
        
        Uses simple optimization: maximize progress while minimizing effort.
        """
        # Simple greedy optimization
        # Control effort proportional to distance from goal
        
        target_progress = 1.0  # Goal is to reach 100%
        current_progress = current_state.progress
        
        # Distance to goal
        distance = target_progress - current_progress
        
        # Control effort: higher when far from goal, lower when close
        # Also consider velocity: if moving fast, can reduce effort
        
        base_control = distance * 0.8  # Base control from distance
        velocity_adjustment = -current_state.velocity * 0.3  # Reduce if moving fast
        
        control = base_control + velocity_adjustment
        
        # Generate control sequence
        control_sequence = []
        for i in range(self.config.control_horizon):
            # Gradually reduce control as we approach goal
            step_control = control * (1.0 - i * 0.1)
            control_sequence.append(max(0.0, min(1.0, step_control)))
        
        return control_sequence
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about MPC control."""
        if not self.control_history:
            return {"status": "no_data"}
        
        avg_control = sum(self.control_history) / len(self.control_history)
        
        return {
            "total_control_actions": len(self.control_history),
            "avg_control": avg_control,
            "state_history_size": len(self.state_history)
        }

