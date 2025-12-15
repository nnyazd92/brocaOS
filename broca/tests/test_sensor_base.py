"""
Tests for sensor base classes and protocol compliance.
"""

from __future__ import annotations

import pytest
from abc import ABC

from broca.environment.sensors.base import Sensor, SensorReading, SensorCapabilities


class TestSensorProtocol:
    """Test sensor protocol compliance."""
    
    def test_sensor_is_abstract(self):
        """Test that Sensor is an abstract base class."""
        assert issubclass(Sensor, ABC)
        
        # Cannot instantiate directly
        with pytest.raises(TypeError):
            Sensor()
    
    def test_sensor_has_required_methods(self):
        """Test that Sensor defines required abstract methods."""
        # Check that abstract methods exist
        assert hasattr(Sensor, 'read')
        assert hasattr(Sensor, 'get_capabilities')
        assert hasattr(Sensor, 'calibrate')


class TestSensorReading:
    """Test SensorReading dataclass."""
    
    def test_sensor_reading_creation(self):
        """Test creating a sensor reading."""
        reading = SensorReading(
            sensor_id="test_sensor",
            sensor_type="system",
            value={"cpu_usage": 0.5},
            timestamp=None
        )
        
        assert reading.sensor_id == "test_sensor"
        assert reading.sensor_type == "system"
        assert reading.value == {"cpu_usage": 0.5}
    
    def test_sensor_reading_has_timestamp(self):
        """Test that sensor reading can have timestamp."""
        from datetime import datetime, timezone
        
        reading = SensorReading(
            sensor_id="test",
            sensor_type="system",
            value={},
            timestamp=datetime.now(timezone.utc)
        )
        
        assert reading.timestamp is not None


class TestSensorCapabilities:
    """Test SensorCapabilities dataclass."""
    
    def test_sensor_capabilities_creation(self):
        """Test creating sensor capabilities."""
        capabilities = SensorCapabilities(
            sensor_type="system",
            metrics=["cpu_usage", "memory_usage"],
            sampling_rate_max=10.0,
            accuracy=0.95
        )
        
        assert capabilities.sensor_type == "system"
        assert "cpu_usage" in capabilities.metrics
        assert capabilities.sampling_rate_max == 10.0

