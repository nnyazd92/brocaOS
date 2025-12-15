"""
Tests for SafetyConstraints implementation.

Tests constraint validation and operation validation.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from broca.environment.safety.constraints import SafetyConstraints, ValidationResult
from broca.environment.access_types import AccessLevel


class TestSafetyConstraintsInitialization:
    """Test SafetyConstraints initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default constraints."""
        constraints = SafetyConstraints()
        
        assert constraints.constraints is not None
        assert constraints.constraints['max_actuator_power'] == 0.0
        assert 'system' in constraints.constraints['allowed_sensor_types']
    
    def test_init_with_custom_constraints(self):
        """Test initialization with custom constraints."""
        custom = {
            'max_actuator_power': 0.5,
            'allowed_sensor_types': ['system', 'filesystem']
        }
        constraints = SafetyConstraints(constraints=custom)
        
        assert constraints.constraints['max_actuator_power'] == 0.5
        assert constraints.constraints['allowed_sensor_types'] == ['system', 'filesystem']


class TestSafetyConstraintsValidation:
    """Test operation validation."""
    
    def test_validate_operation_allowed(self):
        """Test validation of allowed operation."""
        constraints = SafetyConstraints()
        
        operation = Mock()
        operation.operation_type = 'read_sensor'
        operation.sensor_type = 'system'
        operation.actuator_power = 0.0
        
        result = constraints.validate_operation(operation)
        
        assert result.is_valid is True
        assert result.error is None
    
    def test_validate_operation_disallowed_sensor(self):
        """Test validation rejects disallowed sensor type."""
        constraints = SafetyConstraints()
        constraints.constraints['allowed_sensor_types'] = ['system']
        
        operation = Mock()
        operation.operation_type = 'read_sensor'
        operation.sensor_type = 'filesystem'
        
        result = constraints.validate_operation(operation)
        
        assert result.is_valid is False
        assert 'sensor_type' in result.error.lower() or 'not allowed' in result.error.lower()
    
    def test_validate_operation_exceeds_power_limit(self):
        """Test validation rejects operations exceeding power limit."""
        constraints = SafetyConstraints()
        constraints.constraints['max_actuator_power'] = 0.5
        
        operation = Mock()
        operation.operation_type = 'actuator'
        operation.actuator_power = 0.8
        
        result = constraints.validate_operation(operation)
        
        assert result.is_valid is False
        assert 'power' in result.error.lower() or 'exceed' in result.error.lower()
    
    def test_validate_operation_within_power_limit(self):
        """Test validation allows operations within power limit."""
        constraints = SafetyConstraints()
        constraints.constraints['max_actuator_power'] = 0.5
        
        operation = Mock()
        operation.operation_type = 'actuator'
        operation.actuator_power = 0.3
        
        result = constraints.validate_operation(operation)
        
        assert result.is_valid is True
    
    def test_validate_operation_sampling_rate(self):
        """Test validation enforces sampling rate limits."""
        constraints = SafetyConstraints()
        constraints.constraints['max_sampling_rate'] = 1.0  # 1 Hz
        
        operation = Mock()
        operation.operation_type = 'read_sensor'
        operation.sensor_type = 'system'
        operation.sampling_rate = 2.0  # 2 Hz - exceeds limit
        
        result = constraints.validate_operation(operation)
        
        assert result.is_valid is False
        assert 'sampling' in result.error.lower() or 'rate' in result.error.lower()

