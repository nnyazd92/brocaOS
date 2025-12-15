"""
Core access framework for direct environment access.

Provides the main EnvironmentAccessSystem class that coordinates
access levels, policy management, and sensor registry.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List

from .access_types import AccessLevel
from .policy.manager import PolicyManager


class SensorRegistry:
    """
    Registry for available sensors and their capabilities.
    
    Manages sensor discovery, registration, and retrieval.
    """
    
    def __init__(self) -> None:
        """Initialize sensor registry."""
        self.sensors: Dict[str, Any] = {}  # sensor_id -> Sensor object
    
    def discover_sensors(self) -> List[Any]:
        """
        Auto-discover available sensors in environment.
        
        Returns:
            List of discovered sensor objects
        """
        # Initially empty - will be populated by sensor implementations
        return list(self.sensors.values())
    
    def register_sensor(self, sensor: Any) -> str:
        """
        Register a new sensor with capability validation.
        
        Args:
            sensor: Sensor object to register (must have sensor_id attribute)
            
        Returns:
            Sensor ID
        """
        sensor_id = getattr(sensor, 'sensor_id', None)
        if not sensor_id:
            raise ValueError("Sensor must have a sensor_id attribute")
        
        self.sensors[sensor_id] = sensor
        return sensor_id
    
    def get_sensor(self, sensor_id: str) -> Optional[Any]:
        """
        Get a registered sensor by ID.
        
        Args:
            sensor_id: Sensor identifier
            
        Returns:
            Sensor object if found, None otherwise
        """
        return self.sensors.get(sensor_id)


class EnvironmentAccessSystem:
    """
    Core framework for direct environment access with safety controls.
    
    Coordinates access levels, policy management, sensor registry,
    and provides the main interface for environment interaction.
    """
    
    def __init__(self, policy_manager: Optional[PolicyManager] = None) -> None:
        """
        Initialize environment access system.
        
        Args:
            policy_manager: Optional PolicyManager instance (creates default if None)
        """
        self.policy_manager = policy_manager or PolicyManager()
        self.sensor_registry = SensorRegistry()
        from .actuators.registry import ActuatorRegistry
        self.actuator_registry = ActuatorRegistry()
        self.actuator_registry.initialize_default_actuators()
        from .actuators.approval import ApprovalSystem
        self.approval_system = ApprovalSystem()
    
    def get_access_level(self) -> AccessLevel:
        """
        Get current access level.
        
        Returns:
            Current AccessLevel
        """
        return self.policy_manager.current_level
    
    def request_escalation(
        self,
        target_level: AccessLevel,
        rationale: str
    ) -> bool:
        """
        Request policy escalation with user approval.
        
        Args:
            target_level: Target access level
            rationale: Reason for escalation
            
        Returns:
            True if escalation approved, False otherwise
        """
        request = self.policy_manager.request_escalation(target_level, rationale)
        
        # In a real implementation, this would prompt the user for approval
        # For now, return False (requires explicit approval via approve_escalation)
        return False
    
    def approve_escalation(self, request_id: str) -> bool:
        """
        Approve an escalation request.
        
        Args:
            request_id: ID of the escalation request
            
        Returns:
            True if approval successful, False otherwise
        """
        return self.policy_manager.approve_escalation(request_id)
    
    def discover_and_register_sensors(self) -> None:
        """
        Auto-discover and register available sensors.
        
        Discovers system, filesystem, process, network, and user activity sensors
        and registers them in the sensor registry.
        """
        from .sensors.network import SensorNetworkManager
        
        network_manager = SensorNetworkManager()
        network = network_manager.discover_network()
        
        # Register discovered sensors
        for sensor in network.sensors:
            try:
                self.sensor_registry.register_sensor(sensor)
            except Exception:
                pass  # Skip sensors that fail to register

