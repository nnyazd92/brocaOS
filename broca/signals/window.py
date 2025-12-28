"""
Window aggregators for signal statistics.

Provides rolling window statistics (mean, std, min, max) for signals.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T', bound=float)


class RingBuffer(Generic[T]):
    """Generic ring buffer with fixed size."""
    
    def __init__(self, maxlen: int):
        """
        Initialize ring buffer.
        
        Args:
            maxlen: Maximum number of elements
        """
        self._buffer: deque = deque(maxlen=maxlen)
        self.maxlen = maxlen
    
    def append(self, value: T) -> None:
        """Append a value to the buffer."""
        self._buffer.append(value)
    
    def __len__(self) -> int:
        """Get current length."""
        return len(self._buffer)
    
    def __iter__(self):
        """Iterate over buffer."""
        return iter(self._buffer)
    
    def __getitem__(self, index: int) -> T:
        """Get element by index."""
        return self._buffer[index]
    
    def to_list(self) -> List[T]:
        """Convert to list."""
        return list(self._buffer)
    
    def clear(self) -> None:
        """Clear buffer."""
        self._buffer.clear()


class WindowAggregator:
    """
    Window aggregator for rolling statistics.
    
    Maintains a ring buffer and provides rolling statistics
    (mean, std, min, max) over a specified window size.
    """
    
    def __init__(self, max_buffer_size: int = 1000):
        """
        Initialize window aggregator.
        
        Args:
            max_buffer_size: Maximum buffer size
        """
        self._buffer: RingBuffer[float] = RingBuffer(max_buffer_size)
        self._event_count = 0
    
    def update(self, value: float) -> None:
        """
        Update aggregator with new value.
        
        Args:
            value: New value to add
        """
        self._buffer.append(value)
        self._event_count += 1
    
    def rolling_mean(self, window_size: int) -> float:
        """
        Compute rolling mean over window.
        
        Args:
            window_size: Size of rolling window
            
        Returns:
            Mean value (0.0 if insufficient data)
        """
        if len(self._buffer) == 0:
            return 0.0
        
        window = self._buffer.to_list()[-window_size:]
        if len(window) == 0:
            return 0.0
        
        return sum(window) / len(window)
    
    def rolling_std(self, window_size: int) -> float:
        """
        Compute rolling standard deviation over window.
        
        Args:
            window_size: Size of rolling window
            
        Returns:
            Standard deviation (0.0 if insufficient data)
        """
        if len(self._buffer) < 2:
            return 0.0
        
        window = self._buffer.to_list()[-window_size:]
        if len(window) < 2:
            return 0.0
        
        mean = sum(window) / len(window)
        variance = sum((x - mean) ** 2 for x in window) / len(window)
        return math.sqrt(variance)
    
    def rolling_min(self, window_size: int) -> float:
        """
        Compute rolling minimum over window.
        
        Args:
            window_size: Size of rolling window
            
        Returns:
            Minimum value (0.0 if insufficient data)
        """
        if len(self._buffer) == 0:
            return 0.0
        
        window = self._buffer.to_list()[-window_size:]
        if len(window) == 0:
            return 0.0
        
        return min(window)
    
    def rolling_max(self, window_size: int) -> float:
        """
        Compute rolling maximum over window.
        
        Args:
            window_size: Size of rolling window
            
        Returns:
            Maximum value (0.0 if insufficient data)
        """
        if len(self._buffer) == 0:
            return 0.0
        
        window = self._buffer.to_list()[-window_size:]
        if len(window) == 0:
            return 0.0
        
        return max(window)
    
    def event_count(self) -> int:
        """
        Get total event count.
        
        Returns:
            Total number of events processed
        """
        return self._event_count
    
    def get_buffer_size(self) -> int:
        """
        Get current buffer size.
        
        Returns:
            Current number of values in buffer
        """
        return len(self._buffer)
    
    def clear(self) -> None:
        """Clear buffer and reset event count."""
        self._buffer.clear()
        self._event_count = 0

