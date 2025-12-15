"""
Sensor abstraction layer for environment access system.

Provides unified interface for all sensor types with capability discovery.
"""

from .base import Sensor, SensorReading, SensorCapabilities
from .system_sensor import SystemSensor
from .filesystem_sensor import FileSystemSensor
from .process_sensor import ProcessSensor
from .network import SensorNetworkManager
from .network_sensor import NetworkSensor
from .user_activity_sensor import UserActivitySensor

__all__ = [
    "Sensor", "SensorReading", "SensorCapabilities",
    "SystemSensor", "FileSystemSensor", "ProcessSensor",
    "NetworkSensor", "UserActivitySensor",
    "SensorNetworkManager"
]

