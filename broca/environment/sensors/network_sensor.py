"""
Network monitoring sensor for environment access.

Provides detailed network monitoring including interfaces, connections, and statistics.
"""

from __future__ import annotations

import uuid
from typing import Dict, Any, List
from collections import Counter

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore

from .base import Sensor, SensorReading, SensorCapabilities, CalibrationResult


class NetworkSensor(Sensor):
    """
    Network monitoring sensor.
    
    Monitors network interfaces, active connections, and connection statistics.
    """
    
    def __init__(self) -> None:
        """Initialize network sensor."""
        if not PSUTIL_AVAILABLE:
            raise ImportError("psutil is required for NetworkSensor. Install with: pip install psutil")
        
        self.sensor_id = f"network_sensor_{uuid.uuid4().hex[:8]}"
        self.sensor_type = "network"
        self.metrics = [
            'network_interfaces',
            'active_connections',
            'connection_statistics',
            'interface_statistics'
        ]
    
    def read(self) -> SensorReading:
        """
        Read current network metrics.
        
        Returns:
            SensorReading with network metrics
        """
        if not PSUTIL_AVAILABLE:
            raise RuntimeError("psutil not available")
        
        value: Dict[str, Any] = {}
        
        # Network interfaces
        try:
            value['network_interfaces'] = self._get_network_interfaces()
        except Exception:
            value['network_interfaces'] = []
        
        # Active connections
        try:
            value['active_connections'] = self._get_active_connections()
        except Exception:
            value['active_connections'] = []
        
        # Connection statistics
        try:
            value['connection_statistics'] = self._get_connection_statistics()
        except Exception:
            value['connection_statistics'] = {}
        
        # Interface statistics
        try:
            value['interface_statistics'] = self._get_interface_statistics()
        except Exception:
            value['interface_statistics'] = {}
        
        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            value=value
        )
    
    def _get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interfaces with addresses."""
        interfaces = []
        try:
            if_addrs = psutil.net_if_addrs()
            if_stats = psutil.net_if_stats()
            
            for if_name, addrs in if_addrs.items():
                interface_info: Dict[str, Any] = {
                    'name': if_name,
                    'addresses': [],
                    'isup': False
                }
                
                # Get addresses
                for addr in addrs:
                    interface_info['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask if hasattr(addr, 'netmask') else None,
                        'broadcast': addr.broadcast if hasattr(addr, 'broadcast') else None
                    })
                
                # Get interface status
                if if_name in if_stats:
                    stat = if_stats[if_name]
                    interface_info['isup'] = stat.isup
                    interface_info['speed'] = stat.speed
                    interface_info['mtu'] = stat.mtu
                
                interfaces.append(interface_info)
        except Exception:
            pass
        
        return interfaces
    
    def _get_active_connections(self) -> List[Dict[str, Any]]:
        """Get active network connections."""
        connections = []
        try:
            conns = psutil.net_connections(kind='inet')
            for conn in conns:
                conn_info: Dict[str, Any] = {
                    'family': str(conn.family),
                    'type': str(conn.type),
                    'status': conn.status,
                    'local_address': None,
                    'remote_address': None
                }
                
                if conn.laddr:
                    conn_info['local_address'] = {
                        'host': conn.laddr[0],
                        'port': conn.laddr[1]
                    }
                
                if conn.raddr:
                    conn_info['remote_address'] = {
                        'host': conn.raddr[0],
                        'port': conn.raddr[1]
                    }
                
                connections.append(conn_info)
        except (psutil.AccessDenied, AttributeError):
            # On some systems, we might not have permission to see all connections
            pass
        except Exception:
            pass
        
        return connections
    
    def _get_connection_statistics(self) -> Dict[str, Any]:
        """Get connection statistics by state."""
        stats: Dict[str, Any] = {
            'total': 0,
            'by_status': {},
            'by_family': {},
            'by_type': {}
        }
        
        try:
            conns = psutil.net_connections(kind='inet')
            stats['total'] = len(conns)
            
            # Count by status
            statuses = [conn.status for conn in conns if conn.status]
            stats['by_status'] = dict(Counter(statuses))
            
            # Count by family
            families = [str(conn.family) for conn in conns]
            stats['by_family'] = dict(Counter(families))
            
            # Count by type
            types = [str(conn.type) for conn in conns]
            stats['by_type'] = dict(Counter(types))
        except (psutil.AccessDenied, AttributeError):
            pass
        except Exception:
            pass
        
        return stats
    
    def _get_interface_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get per-interface statistics."""
        stats = {}
        try:
            io_counters = psutil.net_io_counters(pernic=True)
            for if_name, counters in io_counters.items():
                stats[if_name] = {
                    'bytes_sent': counters.bytes_sent,
                    'bytes_recv': counters.bytes_recv,
                    'packets_sent': counters.packets_sent,
                    'packets_recv': counters.packets_recv,
                    'errin': counters.errin,
                    'errout': counters.errout,
                    'dropin': counters.dropin,
                    'dropout': counters.dropout
                }
        except Exception:
            pass
        
        return stats
    
    def get_capabilities(self) -> SensorCapabilities:
        """
        Return sensor capabilities.
        
        Returns:
            SensorCapabilities describing network sensor capabilities
        """
        return SensorCapabilities(
            sensor_type=self.sensor_type,
            metrics=self.metrics,
            sampling_rate_max=5.0,  # Can sample up to 5 Hz
            accuracy=0.90,  # Network monitoring is generally accurate
            description="Network monitoring sensor for interfaces, connections, and statistics"
        )
    
    def calibrate(self) -> CalibrationResult:
        """
        Calibrate network sensor.
        
        Verifies that psutil network functions are working.
        
        Returns:
            CalibrationResult indicating success
        """
        if not PSUTIL_AVAILABLE:
            return CalibrationResult(
                success=False,
                error="psutil not available"
            )
        
        try:
            # Test that we can read network information
            psutil.net_if_addrs()
            psutil.net_io_counters()
            # Note: net_connections() may require elevated permissions, so we don't test it here
            
            return CalibrationResult(
                success=True,
                calibration_data={
                    'psutil_version': psutil.__version__ if hasattr(psutil, '__version__') else 'unknown'
                }
            )
        except Exception as e:
            return CalibrationResult(
                success=False,
                error=str(e)
            )

