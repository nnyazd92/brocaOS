"""
System-level sensors for environment access.

Provides CPU, memory, disk, and network monitoring using psutil.
"""

from __future__ import annotations

import uuid
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore

from .base import Sensor, SensorReading, SensorCapabilities, CalibrationResult


class SystemSensor(Sensor):
    """
    System-level sensors (CPU, memory, disk, network).
    
    Monitors system resources using psutil library.
    """
    
    def __init__(self) -> None:
        """Initialize system sensor."""
        if not PSUTIL_AVAILABLE:
            raise ImportError("psutil is required for SystemSensor. Install with: pip install psutil")
        
        self.sensor_id = f"system_sensor_{uuid.uuid4().hex[:8]}"
        self.sensor_type = "system"
        self.metrics = ['cpu_usage', 'memory_usage', 'disk_io', 'network_traffic', 'process_count']
    
    def read(self) -> SensorReading:
        """
        Read current system metrics.
        
        Returns:
            SensorReading with system metrics
        """
        if not PSUTIL_AVAILABLE:
            raise RuntimeError("psutil not available")
        
        value: Dict[str, Any] = {}
        
        # CPU usage
        try:
            value['cpu_usage'] = psutil.cpu_percent(interval=0.1)
        except Exception:
            value['cpu_usage'] = None
        
        # Memory usage
        try:
            mem = psutil.virtual_memory()
            value['memory_usage'] = mem.percent
            value['memory_total'] = mem.total
            value['memory_available'] = mem.available
        except Exception:
            value['memory_usage'] = None
        
        # Disk usage
        try:
            disk = psutil.disk_usage('/')
            value['disk_usage'] = disk.percent
            value['disk_total'] = disk.total
            value['disk_free'] = disk.free
        except Exception:
            value['disk_usage'] = None
        
        # Network traffic
        try:
            net = psutil.net_io_counters()
            value['network_traffic'] = {
                'bytes_sent': net.bytes_sent,
                'bytes_recv': net.bytes_recv,
                'packets_sent': net.packets_sent,
                'packets_recv': net.packets_recv
            }
        except Exception:
            value['network_traffic'] = None
        
        # Process count
        try:
            value['process_count'] = len(psutil.pids())
        except Exception:
            value['process_count'] = None
        
        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            value=value
        )
    
    def get_capabilities(self) -> SensorCapabilities:
        """
        Return sensor capabilities.
        
        Returns:
            SensorCapabilities describing system sensor capabilities
        """
        return SensorCapabilities(
            sensor_type=self.sensor_type,
            metrics=self.metrics,
            sampling_rate_max=10.0,  # Can sample up to 10 Hz
            accuracy=0.95,  # psutil is generally accurate
            description="System-level sensors for CPU, memory, disk, and network monitoring"
        )
    
    def calibrate(self) -> CalibrationResult:
        """
        Calibrate system sensor.
        
        System sensors don't require calibration, but we verify psutil is working.
        
        Returns:
            CalibrationResult indicating success
        """
        if not PSUTIL_AVAILABLE:
            return CalibrationResult(
                success=False,
                error="psutil not available"
            )
        
        try:
            # Test that we can read basic metrics
            psutil.cpu_percent(interval=0.1)
            psutil.virtual_memory()
            psutil.disk_usage('/')
            
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

