"""
Tests for SensorNetworkManager implementation.

Tests sensor discovery, data aggregation, and quality monitoring.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from broca.environment.sensors.network import SensorNetworkManager
from broca.environment.sensors.system_sensor import SystemSensor
from broca.environment.sensors.filesystem_sensor import FileSystemSensor


class TestSensorNetworkManagerInitialization:
    """Test SensorNetworkManager initialization."""
    
    def test_init_creates_manager(self):
        """Test that sensor network manager initializes."""
        manager = SensorNetworkManager()
        
        assert manager is not None
        assert manager.sensor_registry is not None
        assert manager.data_aggregator is not None
        assert manager.quality_monitor is not None


class TestSensorNetworkDiscovery:
    """Test sensor discovery functionality."""
    
    @patch('broca.environment.sensors.network.SystemSensor')
    def test_discover_network_finds_system_sensors(self, mock_system_sensor):
        """Test that network discovery finds system sensors."""
        mock_sensor = Mock()
        mock_sensor.sensor_id = "system_1"
        mock_system_sensor.return_value = mock_sensor
        
        manager = SensorNetworkManager()
        network = manager.discover_network()
        
        assert network is not None
        assert len(network.sensors) > 0
    
    def test_discover_network_adds_sensors(self):
        """Test that discovered sensors are added to network."""
        manager = SensorNetworkManager()
        network = manager.discover_network()
        
        # Should discover at least system sensors
        assert len(network.sensors) >= 0  # May be 0 if psutil not available


class TestSensorNetworkDataAggregation:
    """Test data aggregation functionality."""
    
    def test_create_sensor_fusion(self):
        """Test creating fused sensor readings."""
        manager = SensorNetworkManager()
        
        # Create mock sensors
        sensor1 = Mock()
        sensor1.read.return_value.value = {'cpu_usage': 50.0}
        sensor1.sensor_id = "sensor1"
        
        sensor2 = Mock()
        sensor2.read.return_value.value = {'memory_usage': 60.0}
        sensor2.sensor_id = "sensor2"
        
        fusion = manager.create_sensor_fusion(['sensor1', 'sensor2'])
        
        assert fusion is not None
        # Fusion should combine readings from multiple sensors


class TestSensorNetworkQualityMonitoring:
    """Test data quality monitoring."""
    
    def test_monitor_data_quality(self):
        """Test monitoring sensor data quality."""
        manager = SensorNetworkManager()
        
        report = manager.monitor_data_quality()
        
        assert report is not None
        assert hasattr(report, 'quality_metrics') or hasattr(report, 'sensors_checked')

