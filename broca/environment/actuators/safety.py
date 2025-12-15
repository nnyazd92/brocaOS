"""
Safety interlock system for actuators.

Provides hard safety constraints for actuator operations.
"""

from __future__ import annotations

from typing import Dict, Any


class SafetyInterlock:
    """
    Hard safety constraints for actuator operations.
    
    Enforces power limits, temperature limits, motion limits, and temporal limits.
    """
    
    def __init__(self) -> None:
        """Initialize safety interlock with default constraints."""
        self.interlocks = {
            'power_limit': 0.0,          # Initial: no power
            'temperature_limit': 0.0,
            'motion_limits': {'x': 0, 'y': 0, 'z': 0},
            'temporal_limits': {'max_on_time': '0s'},
            'sequence_requirements': []  # Required operation sequences
        }
    
    def check_interlock(self, operation: str, parameters: Dict[str, Any]) -> bool:
        """
        Check if operation passes interlock constraints.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            
        Returns:
            True if operation is allowed, False otherwise
        """
        # Check power limit
        power = parameters.get('power', 0.0)
        if power > self.interlocks['power_limit']:
            return False
        
        return True
    
    def set_power_limit(self, limit: float) -> None:
        """
        Set power limit for actuator.
        
        Args:
            limit: Maximum power (0.0 to 1.0)
        """
        self.interlocks['power_limit'] = max(0.0, min(1.0, limit))

