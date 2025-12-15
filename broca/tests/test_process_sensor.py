"""
Tests for ProcessSensor implementation.

Tests process monitoring.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from broca.environment.sensors.process_sensor import ProcessSensor


class TestProcessSensorInitialization:
    """Test ProcessSensor initialization."""
    
    def test_init_creates_sensor(self):
        """Test that process sensor initializes."""
        sensor = ProcessSensor()
        
        assert sensor is not None
        assert sensor.sensor_id is not None
        assert sensor.sensor_type == "process"
    
    @pytest.mark.skipif(not hasattr(__import__('sys'), 'psutil'), reason="psutil not available")
    def test_init_with_psutil(self):
        """Test initialization when psutil is available."""
        sensor = ProcessSensor()
        assert sensor.sensor_type == "process"


class TestProcessSensorRead:
    """Test sensor reading functionality."""
    
    @patch('broca.environment.sensors.process_sensor.psutil')
    def test_read_process_creation(self, mock_psutil):
        """Test reading process creation events."""
        mock_psutil.pids.return_value = [1, 2, 3]
        mock_psutil.Process.return_value = Mock(
            name="test_process",
            pid=1,
            status="running"
        )
        
        sensor = ProcessSensor()
        reading = sensor.read()
        
        assert reading is not None
        assert reading.sensor_type == "process"
        assert 'process_count' in reading.value or 'processes' in reading.value
    
    @patch('broca.environment.sensors.process_sensor.psutil')
    def test_read_resource_consumption(self, mock_psutil):
        """Test reading resource consumption."""
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 10.0
        mock_process.memory_info.return_value = Mock(rss=1024*1024)  # 1MB
        
        mock_psutil.pids.return_value = [1]
        mock_psutil.Process.return_value = mock_process
        
        sensor = ProcessSensor()
        reading = sensor.read()
        
        assert reading is not None
        # Should include resource consumption data
        assert 'resource_consumption' in reading.value or 'processes' in reading.value


class TestProcessSensorCapabilities:
    """Test sensor capabilities."""
    
    def test_get_capabilities(self):
        """Test getting sensor capabilities."""
        sensor = ProcessSensor()
        capabilities = sensor.get_capabilities()
        
        assert capabilities.sensor_type == "process"
        assert len(capabilities.metrics) > 0

