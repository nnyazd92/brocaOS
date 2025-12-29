"""
System dynamics modeling for cognitive processes.

Implements system dynamics modeling with emergent property detection.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import deque

if TYPE_CHECKING:
    from ..reasoning.feedback_loop import FeedbackLoopManager
    from ..reasoning.cognitive_dissonance import CognitiveDissonanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class SystemVariable:
    """A variable in the system dynamics model."""
    name: str
    value: float
    rate_of_change: float = 0.0
    history: deque = field(default_factory=lambda: deque(maxlen=100))
    min_value: float = 0.0
    max_value: float = 1.0


@dataclass
class SystemState:
    """State of the cognitive system."""
    timestamp: datetime
    variables: Dict[str, float]
    stability: float = 0.5
    health: float = 0.5
    emergent_properties: List[str] = field(default_factory=list)


class SystemDynamicsModel:
    """
    System dynamics model for cognitive processes.
    
    Models cognitive system as interconnected variables with:
    - Feedback loops
    - Delays
    - Nonlinear relationships
    - Emergent properties
    """
    
    def __init__(
        self,
        feedback_loop_manager: Optional["FeedbackLoopManager"] = None,
        cognitive_dissonance_monitor: Optional["CognitiveDissonanceMonitor"] = None
    ):
        """
        Initialize system dynamics model.
        
        Args:
            feedback_loop_manager: Optional FeedbackLoopManager for feedback loops
            cognitive_dissonance_monitor: Optional CognitiveDissonanceMonitor for dissonance
        """
        self.feedback_loop_manager = feedback_loop_manager
        self.cognitive_dissonance_monitor = cognitive_dissonance_monitor
        
        # System variables
        self.variables: Dict[str, SystemVariable] = {}
        
        # State history
        self.state_history: deque = deque(maxlen=1000)
        
        # Initialize default variables
        self._initialize_default_variables()
        
        logger.info("Initialized SystemDynamicsModel")
    
    def _initialize_default_variables(self):
        """Initialize default system variables."""
        # Cognitive load
        self.variables["cognitive_load"] = SystemVariable(
            name="cognitive_load",
            value=0.5,
            min_value=0.0,
            max_value=1.0
        )
        
        # Confidence
        self.variables["confidence"] = SystemVariable(
            name="confidence",
            value=0.5,
            min_value=0.0,
            max_value=1.0
        )
        
        # Dissonance
        self.variables["dissonance"] = SystemVariable(
            name="dissonance",
            value=0.3,
            min_value=0.0,
            max_value=1.0
        )
        
        # Performance
        self.variables["performance"] = SystemVariable(
            name="performance",
            value=0.7,
            min_value=0.0,
            max_value=1.0
        )
    
    def update_variable(
        self,
        name: str,
        value: float,
        timestamp: Optional[datetime] = None
    ):
        """Update a system variable."""
        if name not in self.variables:
            self.variables[name] = SystemVariable(
                name=name,
                value=value,
                min_value=0.0,
                max_value=1.0
            )
        
        var = self.variables[name]
        old_value = var.value
        
        # Clamp value
        var.value = max(var.min_value, min(var.max_value, value))
        
        # Compute rate of change
        if var.history:
            last_value = var.history[-1]
            time_diff = 1.0  # Assume 1 time unit
            var.rate_of_change = (var.value - last_value) / time_diff
        else:
            var.rate_of_change = 0.0
        
        # Add to history
        var.history.append(var.value)
        
        logger.debug(f"Updated variable {name}: {old_value:.3f} -> {var.value:.3f}")
    
    def simulate_step(self, dt: float = 1.0) -> SystemState:
        """
        Simulate one step of system dynamics.
        
        Args:
            dt: Time step
            
        Returns:
            Current system state
        """
        # Update variables based on relationships
        
        # Cognitive load affects performance (negative feedback)
        if "cognitive_load" in self.variables and "performance" in self.variables:
            load = self.variables["cognitive_load"].value
            # High load -> lower performance
            performance_change = -0.1 * load * dt
            self.variables["performance"].value = max(
                0.0,
                min(1.0, self.variables["performance"].value + performance_change)
            )
        
        # Dissonance affects confidence (negative feedback)
        if "dissonance" in self.variables and "confidence" in self.variables:
            dissonance = self.variables["dissonance"].value
            # High dissonance -> lower confidence
            confidence_change = -0.2 * dissonance * dt
            self.variables["confidence"].value = max(
                0.0,
                min(1.0, self.variables["confidence"].value + confidence_change)
            )
        
        # Update from external sources
        if self.cognitive_dissonance_monitor:
            dissonance_data = self.cognitive_dissonance_monitor.get_aggregated_dissonance()
            self.update_variable("dissonance", dissonance_data.get("overall_dissonance", 0.3))
        
        # Compute stability
        stability = self._compute_stability()
        
        # Compute health
        health = self._compute_health()
        
        # Detect emergent properties
        emergent_properties = self._detect_emergent_properties()
        
        # Create state
        state = SystemState(
            timestamp=datetime.now(timezone.utc),
            variables={name: var.value for name, var in self.variables.items()},
            stability=stability,
            health=health,
            emergent_properties=emergent_properties
        )
        
        self.state_history.append(state)
        
        return state
    
    def _compute_stability(self) -> float:
        """Compute system stability."""
        if not self.variables:
            return 0.5
        
        # Stability is inverse of variance in rates of change
        rates = [abs(var.rate_of_change) for var in self.variables.values()]
        if not rates:
            return 0.5
        
        avg_rate = sum(rates) / len(rates)
        # Lower average rate of change = higher stability
        stability = max(0.0, min(1.0, 1.0 - avg_rate))
        
        return stability
    
    def _compute_health(self) -> float:
        """Compute system health."""
        if not self.variables:
            return 0.5
        
        # Health is combination of:
        # - Low dissonance
        # - High confidence
        # - Good performance
        # - Low cognitive load
        
        health_components = []
        
        if "dissonance" in self.variables:
            # Low dissonance is good
            health_components.append(1.0 - self.variables["dissonance"].value)
        
        if "confidence" in self.variables:
            health_components.append(self.variables["confidence"].value)
        
        if "performance" in self.variables:
            health_components.append(self.variables["performance"].value)
        
        if "cognitive_load" in self.variables:
            # Low load is good
            health_components.append(1.0 - self.variables["cognitive_load"].value)
        
        if health_components:
            health = sum(health_components) / len(health_components)
        else:
            health = 0.5
        
        return max(0.0, min(1.0, health))
    
    def _detect_emergent_properties(self) -> List[str]:
        """Detect emergent properties from system dynamics."""
        properties = []
        
        # Check for stability emergence
        if len(self.state_history) > 10:
            recent_stabilities = [s.stability for s in list(self.state_history)[-10:]]
            if all(s > 0.7 for s in recent_stabilities):
                properties.append("stable_operation")
        
        # Check for oscillation
        if len(self.state_history) > 5:
            recent_values = [s.variables.get("dissonance", 0.5) for s in list(self.state_history)[-5:]]
            # Check for alternating pattern
            if len(recent_values) >= 3:
                alternating = all(
                    (recent_values[i] > recent_values[i+1] and recent_values[i+1] < recent_values[i+2]) or
                    (recent_values[i] < recent_values[i+1] and recent_values[i+1] > recent_values[i+2])
                    for i in range(len(recent_values) - 2)
                )
                if alternating:
                    properties.append("oscillating_behavior")
        
        # Check for self-organization
        if "performance" in self.variables and "dissonance" in self.variables:
            perf = self.variables["performance"].value
            diss = self.variables["dissonance"].value
            # Self-organization: performance improves while dissonance decreases
            if perf > 0.7 and diss < 0.3:
                properties.append("self_organization")
        
        return properties
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about system dynamics."""
        if not self.state_history:
            return {"status": "no_data"}
        
        current_state = self.state_history[-1]
        
        return {
            "variables_count": len(self.variables),
            "current_stability": current_state.stability,
            "current_health": current_state.health,
            "emergent_properties": current_state.emergent_properties,
            "state_history_size": len(self.state_history),
            "variables": {
                name: {
                    "value": var.value,
                    "rate_of_change": var.rate_of_change,
                    "history_size": len(var.history)
                }
                for name, var in self.variables.items()
            }
        }

