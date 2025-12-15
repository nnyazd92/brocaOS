"""
Tests for SystemSensor implementation.

Tests CPU, memory, disk, network readings.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from broca.environment.sensors.system_sensor import SystemSensor


class TestSystemSensorInitialization:
    """Test SystemSensor initialization."""
    
    def test_init_creates_sensor(self):
        """Test that system sensor initializes."""
        sensor = SystemSensor()
        
        assert sensor is not None
        assert sensor.sensor_id is not None
        assert sensor.sensor_type == "system"
    
    def test_sensor_has_required_attributes(self):
        """Test that sensor has required attributes."""
        sensor = SystemSensor()
        
        assert hasattr(sensor, 'sensor_id')
        assert hasattr(sensor, 'sensor_type')
        assert hasattr(sensor, 'metrics')


class TestSystemSensorRead:
    """Test sensor reading functionality."""
    
    @patch('broca.environment.sensors.system_sensor.psutil')
    def test_read_cpu_usage(self, mock_psutil):
        """Test reading CPU usage."""
        # Mock psutil
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.virtual_memory.return_value = Mock(percent=60.0)
        mock_psutil.disk_usage.return_value = Mock(percent=30.0)
        mock_psutil.net_io_counters.return_value = Mock(bytes_sent=1000, bytes_recv=2000)
        mock_psutil.cpu_count.return_value = 4
        
        sensor = SystemSensor()
        reading = sensor.read()
        
        assert reading is not None
        assert reading.sensor_id == sensor.sensor_id
        assert reading.sensor_type == "system"
        assert 'cpu_usage' in reading.value
        assert reading.value['cpu_usage'] == 45.5
    
    @patch('broca.environment.sensors.system_sensor.psutil')
    def test_read_memory_usage(self, mock_psutil):
        """Test reading memory usage."""
        mock_psutil.cpu_percent.return_value = 0.0
        mock_psutil.virtual_memory.return_value = Mock(percent=75.0)
        mock_psutil.disk_usage.return_value = Mock(percent=0.0)
        mock_psutil.net_io_counters.return_value = Mock(bytes_sent=0, bytes_recv=0)
        mock_psutil.cpu_count.return_value = 1
        
        sensor = SystemSensor()
        reading = sensor.read()
        
        assert 'memory_usage' in reading.value
        assert reading.value['memory_usage'] == 75.0
    
    @patch('broca.environment.sensors.system_sensor.psutil')
    def test_read_disk_usage(self, mock_psutil):
        """Test reading disk usage."""
        mock_psutil.cpu_percent.return_value = 0.0
        mock_psutil.virtual_memory.return_value = Mock(percent=0.0)
        mock_psutil.disk_usage.return_value = Mock(percent=50.0)
        mock_psutil.net_io_counters.return_value = Mock(bytes_sent=0, bytes_recv=0)
        mock_psutil.cpu_count.return_value = 1
        
        sensor = SystemSensor()
        reading = sensor.read()
        
        assert 'disk_usage' in reading.value
        assert reading.value['disk_usage'] == 50.0
    
    @patch('broca.environment.sensors.system_sensor.psutil')
    def test_read_network_traffic(self, mock_psutil):
        """Test reading network traffic."""
        mock_psutil.cpu_percent.return_value = 0.0
        mock_psutil.virtual_memory.return_value = Mock(percent=0.0)
        mock_psutil.disk_usage.return_value = Mock(percent=0.0)
        mock_psutil.net_io_counters.return_value = Mock(bytes_sent=1000, bytes_recv=2000)
        mock_psutil.cpu_count.return_value = 1
        
        sensor = SystemSensor()
        reading = sensor.read()
        
        assert 'network_traffic' in reading.value
        assert reading.value['network_traffic']['bytes_sent'] == 1000
        assert reading.value['network_traffic']['bytes_recv'] == 2000


class TestSystemSensorCapabilities:
    """Test sensor capabilities."""
    
    def test_get_capabilities(self):
        """Test getting sensor capabilities."""
        sensor = SystemSensor()
        capabilities = sensor.get_capabilities()
        
        assert capabilities is not None
        assert capabilities.sensor_type == "system"
        assert len(capabilities.metrics) > 0
        assert 'cpu_usage' in capabilities.metrics or 'cpu_usage' in str(capabilities.metrics)
    
    def test_capabilities_include_sampling_rate(self):
        """Test that capabilities include sampling rate information."""
        sensor = SystemSensor()
        capabilities = sensor.get_capabilities()
        
        assert hasattr(capabilities, 'sampling_rate_max')
        assert capabilities.sampling_rate_max > 0

