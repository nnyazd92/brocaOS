"""
Tests for user activity sensor.

Tests user session and activity monitoring capabilities.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock

from broca.environment.sensors.user_activity_sensor import UserActivitySensor
from broca.environment.sensors.base import SensorReading


class TestUserActivitySensorInitialization:
    """Test user activity sensor initialization."""
    
    def test_user_activity_sensor_initialization(self):
        """Test user activity sensor initializes correctly."""
        with patch('broca.environment.sensors.user_activity_sensor.psutil'):
            sensor = UserActivitySensor()
            assert sensor.sensor_type == "user_activity"
            assert "active_sessions" in sensor.metrics or "current_users" in sensor.metrics
    
    @patch('broca.environment.sensors.user_activity_sensor.psutil', None)
    def test_user_activity_sensor_handles_missing_psutil(self):
        """Test user activity sensor handles missing psutil gracefully."""
        # Should still initialize, but may have limited functionality
        try:
            sensor = UserActivitySensor()
            # If it initializes, it should handle missing psutil in read()
            reading = sensor.read()
            assert isinstance(reading, SensorReading)
        except ImportError:
            # It's okay if it raises ImportError when psutil is required
            pass


class TestUserActivitySensorRead:
    """Test reading from user activity sensor."""
    
    def test_read_active_sessions(self):
        """Test reading active user sessions."""
        with patch('broca.environment.sensors.user_activity_sensor.psutil') as mock_psutil:
            # Mock users
            mock_user1 = Mock()
            mock_user1.name = "testuser"
            mock_user1.terminal = "pts/0"
            mock_user1.host = "192.168.1.1"
            mock_user1.started = 1000.0
            
            mock_user2 = Mock()
            mock_user2.name = "testuser2"
            mock_user2.terminal = "tty1"
            mock_user2.host = "localhost"
            mock_user2.started = 2000.0
            
            mock_psutil.users.return_value = [mock_user1, mock_user2]
            
            sensor = UserActivitySensor()
            reading = sensor.read()
            
            assert isinstance(reading, SensorReading)
            assert reading.sensor_type == "user_activity"
            # Should have some user activity data
            assert len(reading.value) > 0
    
    def test_read_current_users(self):
        """Test reading current logged-in users."""
        with patch('broca.environment.sensors.user_activity_sensor.psutil') as mock_psutil:
            mock_psutil.users.return_value = [
                Mock(name="user1", terminal="pts/0", host="localhost", started=1000.0),
                Mock(name="user2", terminal="tty1", host="localhost", started=2000.0)
            ]
            
            sensor = UserActivitySensor()
            reading = sensor.read()
            
            # Should have user information
            assert "current_users" in reading.value or "active_sessions" in reading.value
    
    def test_read_user_process_counts(self):
        """Test reading user process counts."""
        with patch('broca.environment.sensors.user_activity_sensor.psutil') as mock_psutil:
            # Mock processes
            mock_proc1 = Mock()
            mock_proc1.username.return_value = "user1"
            mock_proc2 = Mock()
            mock_proc2.username.return_value = "user1"
            mock_proc3 = Mock()
            mock_proc3.username.return_value = "user2"
            
            mock_psutil.process_iter.return_value = [mock_proc1, mock_proc2, mock_proc3]
            mock_psutil.users.return_value = []
            
            sensor = UserActivitySensor()
            reading = sensor.read()
            
            # Should have process count information
            assert len(reading.value) > 0
    
    def test_read_handles_errors_gracefully(self):
        """Test that reading handles errors gracefully."""
        with patch('broca.environment.sensors.user_activity_sensor.psutil') as mock_psutil:
            mock_psutil.users.side_effect = Exception("Access denied")
            
            try:
                sensor = UserActivitySensor()
                reading = sensor.read()
                # Should still return a reading, but with None or empty values
                assert isinstance(reading, SensorReading)
            except ImportError:
                pass  # If psutil is required and missing, that's okay


class TestUserActivitySensorCapabilities:
    """Test user activity sensor capabilities."""
    
    def test_get_capabilities(self):
        """Test getting sensor capabilities."""
        with patch('broca.environment.sensors.user_activity_sensor.psutil'):
            try:
                sensor = UserActivitySensor()
                capabilities = sensor.get_capabilities()
                
                assert capabilities.sensor_type == "user_activity"
                assert len(capabilities.metrics) > 0
            except ImportError:
                pytest.skip("psutil not available")


class TestUserActivitySensorRegistration:
    """Test user activity sensor registration."""
    
    def test_sensor_registers_correctly(self):
        """Test sensor registers with correct ID."""
        with patch('broca.environment.sensors.user_activity_sensor.psutil'):
            try:
                from broca.environment.access_system import SensorRegistry
                
                registry = SensorRegistry()
                sensor = UserActivitySensor()
                sensor_id = registry.register_sensor(sensor)
                
                assert sensor_id == sensor.sensor_id
                assert registry.get_sensor(sensor_id) == sensor
            except ImportError:
                pytest.skip("psutil not available")

