"""
Sensor network management for environment access system.

Manages sensor networks, discovery, and data aggregation.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .base import Sensor
from ..access_system import SensorRegistry
from .system_sensor import SystemSensor
from .filesystem_sensor import FileSystemSensor
from .process_sensor import ProcessSensor


@dataclass
class SensorNetwork:
    """Represents a network of sensors."""
    
    sensors: List[Sensor] = field(default_factory=list)
    
    def add_sensor(self, sensor: Sensor) -> None:
        """Add a sensor to the network."""
        self.sensors.append(sensor)
    
    def add_sensors(self, sensors: List[Sensor]) -> None:
        """Add multiple sensors to the network."""
        self.sensors.extend(sensors)


@dataclass
class SensorFusion:
    """Represents fused readings from multiple sensors."""
    
    sensor_ids: List[str]
    fused_data: Dict[str, Any]
    timestamp: Optional[str] = None


@dataclass
class DataQualityReport:
    """Report on sensor data quality."""
    
    sensors_checked: int = 0
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


class DataAggregator:
    """Aggregates data from multiple sensors."""
    
    def aggregate(self, readings: List[Any]) -> Dict[str, Any]:
        """
        Aggregate readings from multiple sensors.
        
        Args:
            readings: List of SensorReading objects
            
        Returns:
            Aggregated data dictionary
        """
        aggregated = {}
        for reading in readings:
            if hasattr(reading, 'value') and hasattr(reading, 'sensor_id'):
                aggregated[reading.sensor_id] = reading.value
        
        return aggregated


class DataQualityMonitor:
    """Monitors data quality from sensors."""
    
    def check_quality(self, readings: List[Any]) -> DataQualityReport:
        """
        Check quality of sensor readings.
        
        Args:
            readings: List of SensorReading objects
            
        Returns:
            DataQualityReport with quality metrics
        """
        issues = []
        metrics = {}
        
        for reading in readings:
            if hasattr(reading, 'value'):
                # Check for errors in readings
                if isinstance(reading.value, dict) and 'error' in reading.value:
                    issues.append(f"Sensor {getattr(reading, 'sensor_id', 'unknown')} has error: {reading.value['error']}")
        
        return DataQualityReport(
            sensors_checked=len(readings),
            quality_metrics=metrics,
            issues=issues
        )


class SensorNetworkManager:
    """
    Manages sensor networks, discovery, and data aggregation.
    
    Handles sensor discovery, network creation, data fusion, and quality monitoring.
    """
    
    def __init__(self) -> None:
        """Initialize sensor network manager."""
        self.sensor_registry = SensorRegistry()
        self.data_aggregator = DataAggregator()
        self.quality_monitor = DataQualityMonitor()
    
    def discover_network(self) -> SensorNetwork:
        """
        Discover all available sensors in the environment.
        
        Returns:
            SensorNetwork with discovered sensors
        """
        network = SensorNetwork()
        
        # System sensors (always try to add)
        try:
            system_sensor = SystemSensor()
            network.add_sensor(system_sensor)
            self.sensor_registry.register_sensor(system_sensor)
        except (ImportError, RuntimeError):
            pass  # psutil not available
        
        # File system sensors
        try:
            filesystem_sensor = FileSystemSensor()
            network.add_sensor(filesystem_sensor)
            self.sensor_registry.register_sensor(filesystem_sensor)
        except Exception:
            pass
        
        # Process sensors
        try:
            process_sensor = ProcessSensor()
            network.add_sensor(process_sensor)
            self.sensor_registry.register_sensor(process_sensor)
        except (ImportError, RuntimeError):
            pass  # psutil not available
        
        # Network sensor
        try:
            from .network_sensor import NetworkSensor
            network_sensor = NetworkSensor()
            network.add_sensor(network_sensor)
            self.sensor_registry.register_sensor(network_sensor)
        except (ImportError, RuntimeError):
            pass  # Network sensor requires psutil
        
        # User activity sensor
        try:
            from .user_activity_sensor import UserActivitySensor
            user_activity_sensor = UserActivitySensor()
            network.add_sensor(user_activity_sensor)
            self.sensor_registry.register_sensor(user_activity_sensor)
        except (ImportError, RuntimeError):
            pass  # User activity sensor requires psutil
        
        return network
    
    def create_sensor_fusion(self, sensor_types: List[str]) -> SensorFusion:
        """
        Create fused sensor readings from multiple sources.
        
        Args:
            sensor_types: List of sensor type names to fuse
            
        Returns:
            SensorFusion with combined data
        """
        readings = []
        sensor_ids = []
        
        for sensor_id, sensor in self.sensor_registry.sensors.items():
            if sensor.sensor_type in sensor_types:
                try:
                    reading = sensor.read()
                    readings.append(reading)
                    sensor_ids.append(sensor_id)
                except Exception:
                    pass
        
        fused_data = self.data_aggregator.aggregate(readings)
        
        return SensorFusion(
            sensor_ids=sensor_ids,
            fused_data=fused_data
        )
    
    def monitor_data_quality(self) -> DataQualityReport:
        """
        Monitor and report on sensor data quality.
        
        Returns:
            DataQualityReport with quality metrics
        """
        readings = []
        
        for sensor_id, sensor in self.sensor_registry.sensors.items():
            try:
                reading = sensor.read()
                readings.append(reading)
            except Exception:
                pass
        
        return self.quality_monitor.check_quality(readings)

