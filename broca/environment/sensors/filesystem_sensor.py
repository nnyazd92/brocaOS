"""
File system monitoring sensors for environment access.

Provides file system change detection and directory structure monitoring.
"""

from __future__ import annotations

import uuid
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .base import Sensor, SensorReading, SensorCapabilities, CalibrationResult


class FileSystemSensor(Sensor):
    """
    File system monitoring sensors.
    
    Monitors file changes, directory structure, disk usage, and permission changes.
    """
    
    def __init__(self, monitored_path: Optional[str] = None) -> None:
        """
        Initialize file system sensor.
        
        Args:
            monitored_path: Optional path to monitor (defaults to current directory)
        """
        self.sensor_id = f"filesystem_sensor_{uuid.uuid4().hex[:8]}"
        self.sensor_type = "filesystem"
        self.monitored_path = monitored_path or os.getcwd()
        self.metrics = ['file_changes', 'directory_structure', 'disk_usage', 'permission_changes']
        self._last_file_count = 0
    
    def read(self) -> SensorReading:
        """
        Read current file system state.
        
        Returns:
            SensorReading with file system metrics
        """
        value: Dict[str, Any] = {}
        
        try:
            path = Path(self.monitored_path)
            
            # Directory structure
            if path.exists() and path.is_dir():
                files = list(path.rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                dir_count = len([f for f in files if f.is_dir()])
                
                value['directory_structure'] = {
                    'file_count': file_count,
                    'directory_count': dir_count,
                    'total_entries': len(files)
                }
                
                # File changes (simple comparison)
                if self._last_file_count > 0:
                    value['file_changes'] = {
                        'files_added': max(0, file_count - self._last_file_count),
                        'files_removed': max(0, self._last_file_count - file_count)
                    }
                self._last_file_count = file_count
            
            # Disk usage
            try:
                stat = os.statvfs(self.monitored_path)
                total = stat.f_blocks * stat.f_frsize
                free = stat.f_bavail * stat.f_frsize
                used = total - free
                
                value['disk_usage'] = {
                    'total_bytes': total,
                    'free_bytes': free,
                    'used_bytes': used,
                    'usage_percent': (used / total * 100) if total > 0 else 0.0
                }
            except (OSError, AttributeError):
                value['disk_usage'] = None
            
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
            SensorCapabilities describing filesystem sensor capabilities
        """
        return SensorCapabilities(
            sensor_type=self.sensor_type,
            metrics=self.metrics,
            sampling_rate_max=1.0,  # File system monitoring is typically slower
            accuracy=0.9,
            description="File system monitoring sensors for file changes, directory structure, and disk usage"
        )
    
    def calibrate(self) -> CalibrationResult:
        """
        Calibrate file system sensor.
        
        Verifies that the monitored path is accessible.
        
        Returns:
            CalibrationResult indicating success
        """
        try:
            path = Path(self.monitored_path)
            if not path.exists():
                return CalibrationResult(
                    success=False,
                    error=f"Monitored path does not exist: {self.monitored_path}"
                )
            
            # Test read access
            if path.is_dir():
                list(path.iterdir())
            elif path.is_file():
                path.stat()
            
            return CalibrationResult(
                success=True,
                calibration_data={
                    'monitored_path': str(self.monitored_path),
                    'path_exists': True
                }
            )
        except Exception as e:
            return CalibrationResult(
                success=False,
                error=str(e)
            )

