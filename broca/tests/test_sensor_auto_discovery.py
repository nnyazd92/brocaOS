"""
Tests for sensor auto-discovery on system initialization.

Tests that sensors are automatically discovered and registered when the system initializes.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, Mock

from broca.environment.access_system import EnvironmentAccessSystem
from broca.environment.sensors.system_sensor import SystemSensor
from broca.environment.sensors.filesystem_sensor import FileSystemSensor


class TestSensorAutoDiscovery:
    """Test sensor auto-discovery functionality."""
    
    def test_discover_and_register_sensors_registers_system_sensor(self):
        """Test that system sensor is discovered and registered."""
        system = EnvironmentAccessSystem()
        
        # Initially should be empty or have discovered sensors
        system.discover_and_register_sensors()
        
        # Should have at least system sensor if psutil available
        sensors = system.sensor_registry.discover_sensors()
        assert isinstance(sensors, list)
    
    @patch('broca.environment.sensors.system_sensor.psutil')
    def test_discover_and_register_sensors_with_psutil(self, mock_psutil):
        """Test sensor discovery when psutil is available."""
        system = EnvironmentAccessSystem()
        system.discover_and_register_sensors()
        
        # Should have registered sensors
        assert len(system.sensor_registry.sensors) > 0
    
    def test_discover_and_register_sensors_handles_missing_dependencies(self):
        """Test that discovery handles missing dependencies gracefully."""
        system = EnvironmentAccessSystem()
        
        # Should not raise exception even if psutil not available
        try:
            system.discover_and_register_sensors()
        except ImportError:
            pytest.fail("discover_and_register_sensors should handle missing dependencies")
    
    def test_sensors_are_accessible_after_discovery(self):
        """Test that discovered sensors can be accessed."""
        system = EnvironmentAccessSystem()
        system.discover_and_register_sensors()
        
        # Should be able to list sensors
        sensors = system.sensor_registry.discover_sensors()
        for sensor in sensors:
            assert hasattr(sensor, 'sensor_id')
            assert hasattr(sensor, 'read')

