"""
Signal manager implementation.

Centralized signal state management with damping pipelines.
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List

from .schema import SignalSpec, SIGNAL_REGISTRY
from .models import SignalState
from ..damping.profiles import PROFILE_REGISTRY, DampingProfile
from ..damping.pipeline import DampingPipeline

logger = logging.getLogger(__name__)


class SignalManager:
    """
    Manages signal state with damping.
    
    All signal updates must go through this manager to ensure
    consistent damping and prevent unstable feedback loops.
    """
    
    def __init__(
        self,
        history_size: int = 1000,
        default_profile: str = "MED"
    ):
        """
        Initialize signal manager.
        
        Args:
            history_size: Size of history buffer per signal
            default_profile: Default damping profile name if signal doesn't specify one
        """
        self._signals: Dict[str, SignalState] = {}
        self._history: Dict[str, deque] = {}
        self._pipelines: Dict[str, DampingPipeline] = {}
        self._raw_history: Dict[str, deque] = {}  # Store raw values for observability
        self._history_size = history_size
        self._default_profile = default_profile
        
        logger.info(f"Initialized SignalManager (history_size={history_size}, default_profile={default_profile})")
    
    def register_signal(
        self,
        signal_name: str,
        damping_profile: Optional[str] = None
    ) -> None:
        """
        Register a signal (creates state and pipeline).
        
        Args:
            signal_name: Signal name (must exist in SIGNAL_REGISTRY)
            damping_profile: Optional profile name override
        """
        if signal_name not in SIGNAL_REGISTRY:
            raise ValueError(f"Signal {signal_name} not found in registry")
        
        spec = SIGNAL_REGISTRY[signal_name]
        profile_name = damping_profile or spec.damping_profile_id or self._default_profile
        
        if profile_name not in PROFILE_REGISTRY:
            logger.warning(f"Profile {profile_name} not found, using default {self._default_profile}")
            profile_name = self._default_profile
        
        profile = PROFILE_REGISTRY[profile_name]
        pipeline = DampingPipeline(profile, spec)
        
        # Initialize signal state with default value
        initial_value = spec.default
        signal_state = SignalState(
            name=signal_name,
            value=initial_value,
            raw_value=initial_value,
            timestamp=datetime.now(timezone.utc)
        )
        
        self._signals[signal_name] = signal_state
        self._history[signal_name] = deque(maxlen=self._history_size)
        self._raw_history[signal_name] = deque(maxlen=self._history_size)
        self._pipelines[signal_name] = pipeline
        
        logger.debug(f"Registered signal {signal_name} with profile {profile_name}")
    
    def update(
        self,
        signal_name: str,
        raw_value: Any,
        timestamp: Optional[datetime] = None
    ) -> float | int | bool | str:
        """
        Update a signal with raw value, return damped value.
        
        Args:
            signal_name: Signal name
            raw_value: Raw input value
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Damped value
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Auto-register if not already registered
        if signal_name not in self._signals:
            self.register_signal(signal_name)
        
        signal_state = self._signals[signal_name]
        pipeline = self._pipelines[signal_name]
        
        # Store before value for observability
        before_value = signal_state.value
        
        # Apply damping pipeline
        damped_value = pipeline.apply(
            raw_value,
            signal_state.value,
            timestamp
        )
        
        # Update signal state
        signal_state.value = damped_value
        signal_state.raw_value = raw_value
        signal_state.timestamp = timestamp
        signal_state.last_update_time = timestamp
        
        # Append to history
        self._history[signal_name].append(damped_value)
        self._raw_history[signal_name].append(raw_value)
        
        # Emit event (for observability - can be extended with event system)
        logger.debug(
            f"Signal updated: {signal_name} raw={raw_value:.4f} damped={damped_value:.4f} "
            f"delta={float(damped_value) - float(before_value):.4f}"
        )
        
        return damped_value
    
    def get(self, signal_name: str) -> float | int | bool | str:
        """
        Get current damped value of a signal.
        
        Args:
            signal_name: Signal name
            
        Returns:
            Current damped value (or default if signal not registered)
        """
        if signal_name not in self._signals:
            # Return default if not registered
            if signal_name in SIGNAL_REGISTRY:
                return SIGNAL_REGISTRY[signal_name].default
            raise ValueError(f"Signal {signal_name} not found")
        
        return self._signals[signal_name].value
    
    def get_raw(self, signal_name: str) -> float | int | bool | str:
        """
        Get last raw value of a signal.
        
        Args:
            signal_name: Signal name
            
        Returns:
            Last raw value (or default if signal not registered)
        """
        if signal_name not in self._signals:
            if signal_name in SIGNAL_REGISTRY:
                return SIGNAL_REGISTRY[signal_name].default
            raise ValueError(f"Signal {signal_name} not found")
        
        return self._signals[signal_name].raw_value
    
    def get_history(
        self,
        signal_name: str,
        limit: Optional[int] = None
    ) -> List[float | int | bool | str]:
        """
        Get recent history of a signal.
        
        Args:
            signal_name: Signal name
            limit: Optional limit on number of values to return
            
        Returns:
            List of recent damped values (most recent last)
        """
        if signal_name not in self._history:
            return []
        
        history = list(self._history[signal_name])
        if limit is not None:
            history = history[-limit:]
        
        return history
    
    def get_raw_history(
        self,
        signal_name: str,
        limit: Optional[int] = None
    ) -> List[float | int | bool | str]:
        """
        Get recent raw history of a signal.
        
        Args:
            signal_name: Signal name
            limit: Optional limit on number of values to return
            
        Returns:
            List of recent raw values (most recent last)
        """
        if signal_name not in self._raw_history:
            return []
        
        history = list(self._raw_history[signal_name])
        if limit is not None:
            history = history[-limit:]
        
        return history
    
    def has_signal(self, signal_name: str) -> bool:
        """Check if a signal is registered."""
        return signal_name in self._signals
    
    def list_signals(self) -> List[str]:
        """List all registered signal names."""
        return list(self._signals.keys())

