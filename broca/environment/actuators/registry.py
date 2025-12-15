"""
Actuator registry for environment access system.

Manages actuator discovery, registration, and retrieval.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from .base import Actuator
from .filesystem_actuator import FileSystemActuator


class ActuatorRegistry:
    """
    Registry for available actuators and their capabilities.
    
    Manages actuator discovery, registration, and retrieval.
    """
    
    def __init__(self) -> None:
        """Initialize actuator registry."""
        self.actuators: Dict[str, Actuator] = {}  # actuator_id -> Actuator object
    
    def discover_actuators(self) -> List[Actuator]:
        """
        Auto-discover available actuators in environment.
        
        Returns:
            List of discovered actuator objects
        """
        return list(self.actuators.values())
    
    def register_actuator(self, actuator: Actuator) -> str:
        """
        Register a new actuator.
        
        Args:
            actuator: Actuator object to register
            
        Returns:
            Actuator ID
        """
        self.actuators[actuator.id] = actuator
        return actuator.id
    
    def get_actuator(self, actuator_id: str) -> Optional[Actuator]:
        """
        Get a registered actuator by ID.
        
        Args:
            actuator_id: Actuator identifier
            
        Returns:
            Actuator object if found, None otherwise
        """
        return self.actuators.get(actuator_id)
    
    def initialize_default_actuators(self) -> None:
        """
        Initialize and register default actuators.
        
        Registers filesystem actuator and other available actuators.
        """
        try:
            filesystem_actuator = FileSystemActuator()
            self.register_actuator(filesystem_actuator)
        except Exception:
            pass  # Skip if actuator cannot be initialized

