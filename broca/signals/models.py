"""
Signal state models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SignalState:
    """Current state of a signal."""
    name: str
    value: float | int | bool | str  # Damped value
    raw_value: float | int | bool | str  # Last raw value
    timestamp: datetime
    last_update_time: datetime
    
    def __init__(
        self,
        name: str,
        value: float | int | bool | str,
        raw_value: float | int | bool | str,
        timestamp: Optional[datetime] = None
    ):
        self.name = name
        self.value = value
        self.raw_value = raw_value
        now = timestamp or datetime.now()
        self.timestamp = now
        self.last_update_time = now

