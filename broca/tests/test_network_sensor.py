"""
Tests for network sensor.

Tests detailed network monitoring capabilities.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock

from broca.environment.sensors.network_sensor import NetworkSensor
from broca.environment.sensors.base import SensorReading


class TestNetworkSensorInitialization:
    """Test network sensor initialization."""
    
    def test_network_sensor_initialization(self):
        """Test network sensor initializes correctly."""
        with patch('broca.environment.sensors.network_sensor.psutil') as mock_psutil:
            sensor = NetworkSensor()
            assert sensor.sensor_type == "network"
            assert "network_interfaces" in sensor.metrics
            assert "active_connections" in sensor.metrics
    
    @patch('broca.environment.sensors.network_sensor.PSUTIL_AVAILABLE', False)
    def test_network_sensor_requires_psutil(self):
        """Test network sensor requires psutil."""
        with pytest.raises(ImportError, match="psutil is required"):
            NetworkSensor()


class TestNetworkSensorRead:
    """Test reading from network sensor."""
    
    def test_read_network_interfaces(self):
        """Test reading network interfaces."""
        with patch('broca.environment.sensors.network_sensor.psutil') as mock_psutil:
            # Mock network interfaces
            mock_if_addrs = {
                'eth0': [Mock(family=2, address='192.168.1.1'), Mock(family=10, address='::1')],
                'lo': [Mock(family=2, address='127.0.0.1')]
            }
            mock_psutil.net_if_addrs.return_value = mock_if_addrs
            
            # Mock interface stats
            mock_stats = {
                'eth0': Mock(bytes_sent=1000, bytes_recv=2000, packets_sent=10, packets_recv=20, errin=0, errout=0, dropin=0, dropout=0, isup=True),
                'lo': Mock(bytes_sent=100, bytes_recv=100, packets_sent=1, packets_recv=1, errin=0, errout=0, dropin=0, dropout=0, isup=True)
            }
            mock_psutil.net_if_stats.return_value = mock_stats
            
            sensor = NetworkSensor()
            reading = sensor.read()
            
            assert isinstance(reading, SensorReading)
            assert reading.sensor_type == "network"
            assert "network_interfaces" in reading.value
            assert len(reading.value["network_interfaces"]) > 0
    
    def test_read_active_connections(self):
        """Test reading active network connections."""
        with patch('broca.environment.sensors.network_sensor.psutil') as mock_psutil:
            # Mock connections
            mock_conn = Mock()
            mock_conn.fd = -1
            mock_conn.family = 2  # AF_INET
            mock_conn.type = 1  # SOCK_STREAM
            mock_conn.laddr = ('127.0.0.1', 8080)
            mock_conn.raddr = ('192.168.1.1', 12345)
            mock_conn.status = 'ESTABLISHED'
            mock_psutil.net_connections.return_value = [mock_conn]
            
            sensor = NetworkSensor()
            reading = sensor.read()
            
            assert "active_connections" in reading.value
            assert len(reading.value["active_connections"]) >= 0
    
    def test_read_connection_statistics(self):
        """Test reading connection statistics."""
        with patch('broca.environment.sensors.network_sensor.psutil') as mock_psutil:
            # Mock connections by state
            mock_psutil.net_connections.return_value = [
                Mock(status='ESTABLISHED', family=2, type=1),
                Mock(status='LISTENING', family=2, type=1),
                Mock(status='ESTABLISHED', family=2, type=1)
            ]
            
            sensor = NetworkSensor()
            reading = sensor.read()
            
            assert "connection_statistics" in reading.value
            stats = reading.value["connection_statistics"]
            assert "ESTABLISHED" in stats or "total" in stats
    
    def test_read_handles_errors_gracefully(self):
        """Test that reading handles errors gracefully."""
        with patch('broca.environment.sensors.network_sensor.psutil') as mock_psutil:
            mock_psutil.net_if_addrs.side_effect = Exception("Network error")
            
            sensor = NetworkSensor()
            reading = sensor.read()
            
            # Should still return a reading, but with None or empty values
            assert isinstance(reading, SensorReading)


class TestNetworkSensorCapabilities:
    """Test network sensor capabilities."""
    
    def test_get_capabilities(self):
        """Test getting sensor capabilities."""
        with patch('broca.environment.sensors.network_sensor.psutil'):
            sensor = NetworkSensor()
            capabilities = sensor.get_capabilities()
            
            assert capabilities.sensor_type == "network"
            assert len(capabilities.metrics) > 0
            assert capabilities.description is not None


class TestNetworkSensorRegistration:
    """Test network sensor registration."""
    
    def test_sensor_registers_correctly(self):
        """Test sensor registers with correct ID."""
        with patch('broca.environment.sensors.network_sensor.psutil'):
            from broca.environment.access_system import SensorRegistry
            
            registry = SensorRegistry()
            sensor = NetworkSensor()
            sensor_id = registry.register_sensor(sensor)
            
            assert sensor_id == sensor.sensor_id
            assert registry.get_sensor(sensor_id) == sensor

