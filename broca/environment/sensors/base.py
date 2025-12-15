"""
Base sensor abstraction for environment access system.

Defines the abstract Sensor interface that all sensor implementations must follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


@dataclass
class SensorReading:
    """Represents a reading from a sensor."""
    
    sensor_id: str
    sensor_type: str
    value: Dict[str, Any]
    timestamp: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SensorCapabilities:
    """Represents sensor capabilities and metadata."""
    
    sensor_type: str
    metrics: List[str]
    sampling_rate_max: float = 1.0  # Hz
    accuracy: Optional[float] = None
    description: Optional[str] = None


@dataclass
class CalibrationResult:
    """Result of sensor calibration."""
    
    success: bool
    error: Optional[str] = None
    calibration_data: Optional[Dict[str, Any]] = None


class Sensor(ABC):
    """
    Abstract base class for all sensors.
    
    All sensor implementations must inherit from this class and implement
    the required abstract methods.
    """
    
    @abstractmethod
    def read(self) -> SensorReading:
        """
        Read current sensor value.
        
        Returns:
            SensorReading with current sensor data
        """
        ...
    
    @abstractmethod
    def get_capabilities(self) -> SensorCapabilities:
        """
        Return sensor capabilities and metadata.
        
        Returns:
            SensorCapabilities object describing sensor capabilities
        """
        ...
    
    @abstractmethod
    def calibrate(self) -> CalibrationResult:
        """
        Calibrate sensor if applicable.
        
        Returns:
            CalibrationResult indicating success or failure
        """
        ...

