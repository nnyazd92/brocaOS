"""
Access control enforcement for environment access system.

Defines access level requirements for operations and enforces them.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .access_types import AccessLevel


@dataclass
class AccessCheckResult:
    """Result of access level check."""
    
    allowed: bool
    error: Optional[str] = None
    required_level: Optional[AccessLevel] = None


class AccessControl:
    """
    Enforces access level requirements for operations.
    
    Defines which operations require which access levels and checks
    if the current access level is sufficient.
    """
    
    # Define access level requirements for operations
    OPERATION_REQUIREMENTS: Dict[str, AccessLevel] = {
        # Sensor operations
        "read_sensor": AccessLevel.SANDBOXED,  # Basic sensor reads allowed in sandbox
        "list_sensors": AccessLevel.SANDBOXED,
        "get_access_level": AccessLevel.SANDBOXED,
        "get_audit_log": AccessLevel.SANDBOXED,
        
        # Escalation operations
        "request_escalation": AccessLevel.SANDBOXED,
        "approve_escalation": AccessLevel.SANDBOXED,  # User can approve from any level
        "check_escalation_status": AccessLevel.SANDBOXED,
        "downgrade_access": AccessLevel.SANDBOXED,
        
        # Actuator operations
        "list_actuators": AccessLevel.SUPERVISED,
        "control_actuator": AccessLevel.AUTONOMOUS,  # Actuators require highest level
        
        # Approval token operations
        "request_actuator_approval": AccessLevel.SANDBOXED,  # Can request from any level
        "approve_actuator_request": AccessLevel.SANDBOXED,  # User can approve from any level
        "generate_approval_token": AccessLevel.AUTONOMOUS,  # Token generation requires AUTONOMOUS
        "verify_approval_token": AccessLevel.SANDBOXED,
        
        # Emergency access operations
        "request_emergency_access": AccessLevel.SANDBOXED,  # Can request from any level
        "exit_emergency_access": AccessLevel.SANDBOXED,  # Can exit from any level
    }
    
    # Define sensor type requirements
    SENSOR_TYPE_REQUIREMENTS: Dict[str, AccessLevel] = {
        "system": AccessLevel.SANDBOXED,
        "filesystem": AccessLevel.SUPERVISED,
        "process": AccessLevel.SUPERVISED,
        "network": AccessLevel.SUPERVISED,
        "user_activity": AccessLevel.SUPERVISED,
    }
    
    @classmethod
    def check_operation_access(
        cls,
        operation: str,
        current_level: AccessLevel,
        sensor_type: Optional[str] = None,
        is_emergency: bool = False
    ) -> AccessCheckResult:
        """
        Check if operation is allowed at current access level.
        
        Args:
            operation: Operation name
            current_level: Current access level
            sensor_type: Optional sensor type (for sensor operations)
            is_emergency: Whether emergency access is active (bypasses restrictions)
            
        Returns:
            AccessCheckResult indicating if operation is allowed
        """
        # Emergency access bypasses all restrictions
        if is_emergency or current_level == AccessLevel.EMERGENCY:
            return AccessCheckResult(allowed=True)
        
        # Check sensor type requirements if applicable
        if sensor_type and sensor_type in cls.SENSOR_TYPE_REQUIREMENTS:
            required_level = cls.SENSOR_TYPE_REQUIREMENTS[sensor_type]
            if current_level.value < required_level.value:
                return AccessCheckResult(
                    allowed=False,
                    error=f"Sensor type '{sensor_type}' requires {required_level.name} access level",
                    required_level=required_level
                )
        
        # Check operation requirements
        if operation in cls.OPERATION_REQUIREMENTS:
            required_level = cls.OPERATION_REQUIREMENTS[operation]
            if current_level.value < required_level.value:
                return AccessCheckResult(
                    allowed=False,
                    error=f"Operation '{operation}' requires {required_level.name} access level",
                    required_level=required_level
                )
        
        return AccessCheckResult(allowed=True)

