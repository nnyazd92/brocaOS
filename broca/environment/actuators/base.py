"""
Base actuator abstraction for environment access system.

Defines the abstract Actuator interface that all actuator implementations must follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

from .safety import SafetyInterlock


@dataclass
class ActivationResult:
    """Result of actuator activation."""
    
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class DeactivationResult:
    """Result of actuator deactivation."""
    
    success: bool
    error: Optional[str] = None


@dataclass
class EmergencyStopResult:
    """Result of emergency stop."""
    
    success: bool
    error: Optional[str] = None


class Actuator(ABC):
    """
    Abstract base class for all actuators.
    
    All actuator implementations must inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, actuator_id: str, max_power: float) -> None:
        """
        Initialize actuator.
        
        Args:
            actuator_id: Unique identifier for the actuator
            max_power: Maximum power/impact level (0.0 to 1.0)
        """
        self.id = actuator_id
        self.max_power = max_power
        self.current_state = 'idle'
        self.safety_interlock = SafetyInterlock()
    
    @abstractmethod
    def activate(self, parameters: Dict[str, Any]) -> ActivationResult:
        """
        Activate actuator with parameters.
        
        Args:
            parameters: Activation parameters
            
        Returns:
            ActivationResult indicating success or failure
        """
        ...
    
    @abstractmethod
    def deactivate(self) -> DeactivationResult:
        """
        Deactivate actuator.
        
        Returns:
            DeactivationResult indicating success or failure
        """
        ...
    
    @abstractmethod
    def emergency_stop(self) -> EmergencyStopResult:
        """
        Immediate emergency stop.
        
        Returns:
            EmergencyStopResult indicating success or failure
        """
        ...

