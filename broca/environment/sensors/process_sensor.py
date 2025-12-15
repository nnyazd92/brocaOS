"""
Process monitoring sensors for environment access.

Provides process creation, termination, and resource consumption monitoring.
"""

from __future__ import annotations

import uuid
from typing import Dict, Any, List

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore

from .base import Sensor, SensorReading, SensorCapabilities, CalibrationResult


class ProcessSensor(Sensor):
    """
    Process monitoring sensors.
    
    Monitors process creation, termination, resource consumption, and network connections.
    """
    
    def __init__(self) -> None:
        """Initialize process sensor."""
        if not PSUTIL_AVAILABLE:
            raise ImportError("psutil is required for ProcessSensor. Install with: pip install psutil")
        
        self.sensor_id = f"process_sensor_{uuid.uuid4().hex[:8]}"
        self.sensor_type = "process"
        self.metrics = ['process_creation', 'process_termination', 'resource_consumption', 'network_connections']
    
    def read(self) -> SensorReading:
        """
        Read current process state.
        
        Returns:
            SensorReading with process metrics
        """
        if not PSUTIL_AVAILABLE:
            raise RuntimeError("psutil not available")
        
        value: Dict[str, Any] = {}
        
        try:
            # Process count
            pids = psutil.pids()
            value['process_count'] = len(pids)
            
            # Process list with basic info
            processes = []
            for pid in pids[:50]:  # Limit to first 50 for performance
                try:
                    proc = psutil.Process(pid)
                    processes.append({
                        'pid': pid,
                        'name': proc.name(),
                        'status': proc.status(),
                        'cpu_percent': proc.cpu_percent(),
                        'memory_percent': proc.memory_percent()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            value['processes'] = processes
            
            # Resource consumption summary
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                
                value['resource_consumption'] = {
                    'total_cpu_percent': cpu_percent,
                    'total_memory_percent': mem.percent,
                    'total_memory_used': mem.used,
                    'total_memory_available': mem.available
                }
            except Exception:
                value['resource_consumption'] = None
            
            # Network connections count
            try:
                connections = psutil.net_connections()
                value['network_connections'] = len(connections)
            except Exception:
                value['network_connections'] = None
            
        except Exception as e:
            value['error'] = str(e)
        
        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            value=value
        )
    
    def get_capabilities(self) -> SensorCapabilities:
        """
        Return sensor capabilities.
        
        Returns:
            SensorCapabilities describing process sensor capabilities
        """
        return SensorCapabilities(
            sensor_type=self.sensor_type,
            metrics=self.metrics,
            sampling_rate_max=2.0,  # Process monitoring can be more frequent
            accuracy=0.95,
            description="Process monitoring sensors for process creation, termination, and resource consumption"
        )
    
    def calibrate(self) -> CalibrationResult:
        """
        Calibrate process sensor.
        
        Verifies that psutil can access process information.
        
        Returns:
            CalibrationResult indicating success
        """
        if not PSUTIL_AVAILABLE:
            return CalibrationResult(
                success=False,
                error="psutil not available"
            )
        
        try:
            # Test that we can read process information
            pids = psutil.pids()
            if len(pids) > 0:
                test_pid = pids[0]
                proc = psutil.Process(test_pid)
                proc.name()  # Test access
            
            return CalibrationResult(
                success=True,
                calibration_data={
                    'psutil_version': psutil.__version__ if hasattr(psutil, '__version__') else 'unknown',
                    'process_count': len(pids)
                }
            )
        except Exception as e:
            return CalibrationResult(
                success=False,
                error=str(e)
            )

