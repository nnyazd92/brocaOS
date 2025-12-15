"""
Safety constraints for environment access.

Defines and validates safety constraints for all environment operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class ValidationResult:
    """Result of operation validation."""
    
    is_valid: bool
    error: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        """Initialize warnings list if None."""
        if self.warnings is None:
            self.warnings = []


class SafetyConstraints:
    """
    Defines safety constraints for environment access.
    
    Validates operations against configurable safety constraints including
    actuator power limits, allowed sensor types, sampling rates, and temporal limits.
    """
    
    def __init__(self, constraints: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize safety constraints.
        
        Args:
            constraints: Optional custom constraints dictionary
        """
        if constraints is None:
            constraints = self._default_constraints()
        
        self.constraints = constraints
    
    def _default_constraints(self) -> Dict[str, Any]:
        """Get default safety constraints."""
        return {
            'max_actuator_power': 0.0,      # Initial: no actuator access
            'allowed_sensor_types': ['system', 'file', 'process'],
            'max_sampling_rate': 1.0,         # Hz
            'data_retention_limit': '24h',
            'geofencing': None,               # No location constraints initially
            'temporal_limits': {
                'max_continuous_operation': '1h',
                'cooling_period': '5m'
            }
        }
    
    def validate_operation(self, operation: Any) -> ValidationResult:
        """
        Validate operation against all safety constraints.
        
        Args:
            operation: Operation object to validate (must have attributes:
                      operation_type, sensor_type (if sensor op), actuator_power (if actuator op))
        
        Returns:
            ValidationResult indicating if operation is valid
        """
        errors = []
        warnings = []
        
        # Validate sensor operations
        if hasattr(operation, 'operation_type') and operation.operation_type == 'read_sensor':
            if hasattr(operation, 'sensor_type'):
                if operation.sensor_type not in self.constraints['allowed_sensor_types']:
                    errors.append(
                        f"Sensor type '{operation.sensor_type}' not allowed. "
                        f"Allowed types: {self.constraints['allowed_sensor_types']}"
                    )
            
            # Validate sampling rate
            if hasattr(operation, 'sampling_rate') and operation.sampling_rate is not None:
                try:
                    sampling_rate = float(operation.sampling_rate)
                    max_rate = self.constraints.get('max_sampling_rate', float('inf'))
                    if sampling_rate > max_rate:
                        errors.append(
                            f"Sampling rate {sampling_rate} Hz exceeds maximum "
                            f"of {max_rate} Hz"
                        )
                except (TypeError, ValueError):
                    pass  # Ignore invalid sampling rate values
        
        # Validate actuator operations
        if hasattr(operation, 'operation_type') and operation.operation_type == 'actuator':
            if hasattr(operation, 'actuator_power'):
                max_power = self.constraints.get('max_actuator_power', 0.0)
                if operation.actuator_power > max_power:
                    errors.append(
                        f"Actuator power {operation.actuator_power} exceeds maximum "
                        f"of {max_power}"
                    )
        
        if errors:
            return ValidationResult(
                is_valid=False,
                error="; ".join(errors),
                warnings=warnings
            )
        
        return ValidationResult(
            is_valid=True,
            warnings=warnings
        )

