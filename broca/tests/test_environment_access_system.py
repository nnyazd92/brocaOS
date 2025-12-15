"""
Tests for EnvironmentAccessSystem implementation.

Tests access system initialization, access level management, and sensor registry.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from broca.environment.access_system import EnvironmentAccessSystem
from broca.environment.access_types import AccessLevel
from broca.environment.policy.manager import PolicyManager


class TestAccessLevel:
    """Test AccessLevel enum."""
    
    def test_access_level_values(self):
        """Test that access levels have correct integer values."""
        assert AccessLevel.SANDBOXED.value == 0
        assert AccessLevel.SUPERVISED.value == 1
        assert AccessLevel.AUTONOMOUS.value == 2
        assert AccessLevel.EMERGENCY.value == 3


class TestEnvironmentAccessSystemInitialization:
    """Test EnvironmentAccessSystem initialization."""
    
    def test_init_creates_system(self):
        """Test that system initializes with default SANDBOXED level."""
        system = EnvironmentAccessSystem()
        
        assert system is not None
        assert system.policy_manager is not None
        assert system.policy_manager.current_level == AccessLevel.SANDBOXED
    
    def test_init_with_custom_policy_manager(self):
        """Test initialization with custom policy manager."""
        policy_manager = PolicyManager()
        system = EnvironmentAccessSystem(policy_manager=policy_manager)
        
        assert system.policy_manager is policy_manager
    
    def test_sensor_registry_initialized(self):
        """Test that sensor registry is initialized."""
        system = EnvironmentAccessSystem()
        
        assert system.sensor_registry is not None
        assert hasattr(system.sensor_registry, 'sensors')
        assert isinstance(system.sensor_registry.sensors, dict)


class TestEnvironmentAccessSystemAccessLevels:
    """Test access level management."""
    
    def test_get_current_access_level(self):
        """Test getting current access level."""
        system = EnvironmentAccessSystem()
        
        level = system.get_access_level()
        assert level == AccessLevel.SANDBOXED
    
    def test_request_escalation_requires_approval(self):
        """Test that escalation requires user approval."""
        system = EnvironmentAccessSystem()
        
        # Escalation should return False without approval
        result = system.request_escalation(AccessLevel.SUPERVISED, "Test rationale")
        assert result is False
        assert system.get_access_level() == AccessLevel.SANDBOXED
    
    def test_request_escalation_with_approval(self):
        """Test escalation with user approval."""
        system = EnvironmentAccessSystem()
        
        # Request escalation and then approve it
        request = system.policy_manager.request_escalation(AccessLevel.SUPERVISED, "Test rationale")
        result = system.approve_escalation(request.request_id)
        
        assert result is True
        assert system.get_access_level() == AccessLevel.SUPERVISED


class TestSensorRegistry:
    """Test SensorRegistry functionality."""
    
    def test_register_sensor(self):
        """Test registering a sensor."""
        system = EnvironmentAccessSystem()
        
        mock_sensor = Mock()
        mock_sensor.sensor_id = "test_sensor"
        mock_sensor.sensor_type = "test"
        
        sensor_id = system.sensor_registry.register_sensor(mock_sensor)
        
        assert sensor_id == "test_sensor"
        assert "test_sensor" in system.sensor_registry.sensors
    
    def test_discover_sensors(self):
        """Test sensor discovery."""
        system = EnvironmentAccessSystem()
        
        sensors = system.sensor_registry.discover_sensors()
        
        assert isinstance(sensors, list)
        # Initially should be empty or contain only system sensors
    
    def test_get_sensor(self):
        """Test retrieving a registered sensor."""
        system = EnvironmentAccessSystem()
        
        mock_sensor = Mock()
        mock_sensor.sensor_id = "test_sensor"
        mock_sensor.sensor_type = "test"
        
        system.sensor_registry.register_sensor(mock_sensor)
        retrieved = system.sensor_registry.get_sensor("test_sensor")
        
        assert retrieved is mock_sensor
    
    def test_get_sensor_not_found(self):
        """Test retrieving non-existent sensor returns None."""
        system = EnvironmentAccessSystem()
        
        sensor = system.sensor_registry.get_sensor("nonexistent")
        assert sensor is None

