"""
Action gating for discrete actions.

Provides debounce, cooldown, evidence windows, and sustained trigger logic
to prevent unstable feedback loops in discrete actions like:
- self-model updates
- RL policy updates
- LLM suggestion injection
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ActionGateConfig:
    """Configuration for action gating."""
    debounce_seconds: float = 0.0  # Ignore rapid repeated triggers within this window
    cooldown_seconds: float = 0.0  # Minimum time between actions
    min_evidence_window_seconds: float = 0.0  # Require evidence sustained for this duration
    min_evidence_count: int = 0  # Require minimum number of evidence events
    sustained_trigger_threshold: float = 0.5  # Trigger only if condition holds above this threshold
    sustained_trigger_window_seconds: float = 0.0  # Window for sustained trigger check
    
    def __post_init__(self):
        """Validate configuration."""
        if self.debounce_seconds < 0:
            raise ValueError("debounce_seconds must be >= 0")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")
        if self.min_evidence_window_seconds < 0:
            raise ValueError("min_evidence_window_seconds must be >= 0")
        if self.min_evidence_count < 0:
            raise ValueError("min_evidence_count must be >= 0")
        if not (0.0 <= self.sustained_trigger_threshold <= 1.0):
            raise ValueError("sustained_trigger_threshold must be between 0 and 1")


class ActionGate:
    """
    Gate for discrete actions with debounce, cooldown, and evidence windows.
    
    Prevents unstable feedback loops by ensuring actions only trigger when:
    - Enough evidence has accumulated (evidence window)
    - Trigger has been sustained (sustained trigger logic)
    - Enough time has passed since last action (cooldown)
    - No rapid repeated triggers (debounce)
    """
    
    def __init__(
        self,
        config: ActionGateConfig,
        action_name: str = "action",
    ):
        """
        Initialize action gate.
        
        Args:
            config: Action gate configuration
            action_name: Name of the action (for logging)
        """
        self.config = config
        self.action_name = action_name
        
        # State tracking
        self._last_action_time: Optional[datetime] = None
        self._last_trigger_time: Optional[datetime] = None
        self._evidence_buffer: list[tuple[datetime, float]] = []  # (timestamp, value) pairs
        self._trigger_buffer: list[tuple[datetime, bool]] = []  # (timestamp, triggered) pairs
        
        logger.debug(f"Initialized ActionGate '{action_name}' with config: {config}")
    
    def should_allow_action(
        self,
        trigger_value: float,
        timestamp: Optional[datetime] = None,
        evidence_value: Optional[float] = None,
    ) -> tuple[bool, str]:
        """
        Check if an action should be allowed.
        
        Args:
            trigger_value: Current trigger signal value (0.0-1.0)
            timestamp: Current timestamp (defaults to now)
            evidence_value: Optional evidence value to record (same as trigger_value if None)
            
        Returns:
            Tuple of (should_allow, reason_string)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        if evidence_value is None:
            evidence_value = trigger_value
        
        # Record evidence
        self._evidence_buffer.append((timestamp, evidence_value))
        self._prune_evidence_buffer(timestamp)
        
        # Record trigger
        is_triggered = trigger_value >= self.config.sustained_trigger_threshold
        self._trigger_buffer.append((timestamp, is_triggered))
        self._prune_trigger_buffer(timestamp)
        
        # 1. Debounce check: ignore if too soon after last trigger
        if self._last_trigger_time is not None and self.config.debounce_seconds > 0:
            time_since_trigger = (timestamp - self._last_trigger_time).total_seconds()
            if time_since_trigger < self.config.debounce_seconds:
                return (False, f"debounced (last trigger {time_since_trigger:.2f}s ago)")
        
        # 2. Cooldown check: ignore if too soon after last action
        if self._last_action_time is not None and self.config.cooldown_seconds > 0:
            time_since_action = (timestamp - self._last_action_time).total_seconds()
            if time_since_action < self.config.cooldown_seconds:
                return (False, f"cooldown (last action {time_since_action:.2f}s ago)")
        
        # 3. Minimum evidence window check: require evidence for minimum duration
        if self.config.min_evidence_window_seconds > 0:
            if len(self._evidence_buffer) < 2:
                return (False, "insufficient evidence history")
            
            oldest_evidence_time = self._evidence_buffer[0][0]
            evidence_window_duration = (timestamp - oldest_evidence_time).total_seconds()
            if evidence_window_duration < self.config.min_evidence_window_seconds:
                return (False, f"evidence window too short ({evidence_window_duration:.2f}s < {self.config.min_evidence_window_seconds:.2f}s)")
        
        # 4. Minimum evidence count check
        if self.config.min_evidence_count > 0:
            if len(self._evidence_buffer) < self.config.min_evidence_count:
                return (False, f"insufficient evidence count ({len(self._evidence_buffer)} < {self.config.min_evidence_count})")
        
        # 5. Sustained trigger check: require trigger to be sustained over window
        if self.config.sustained_trigger_window_seconds > 0:
            if not self._check_sustained_trigger(timestamp):
                return (False, "trigger not sustained over window")
        
        # All checks passed - update last trigger time
        self._last_trigger_time = timestamp
        
        # All checks passed
        return (True, "allowed")
    
    def record_action(self, timestamp: Optional[datetime] = None) -> None:
        """
        Record that an action was performed.
        
        This should be called after the action is executed to update
        the gate's internal state.
        
        Args:
            timestamp: Timestamp of action (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        self._last_action_time = timestamp
        logger.debug(f"ActionGate '{self.action_name}': recorded action at {timestamp.isoformat()}")
    
    def _prune_evidence_buffer(self, current_time: datetime) -> None:
        """Remove evidence older than the maximum window."""
        max_age = max(
            self.config.min_evidence_window_seconds,
            self.config.sustained_trigger_window_seconds,
            60.0  # Keep at least 60 seconds for safety
        )
        cutoff_time = current_time - timedelta(seconds=max_age)
        self._evidence_buffer = [
            (ts, val) for ts, val in self._evidence_buffer
            if ts >= cutoff_time
        ]
    
    def _prune_trigger_buffer(self, current_time: datetime) -> None:
        """Remove triggers older than the sustained trigger window."""
        if self.config.sustained_trigger_window_seconds > 0:
            cutoff_time = current_time - timedelta(seconds=self.config.sustained_trigger_window_seconds)
            self._trigger_buffer = [
                (ts, triggered) for ts, triggered in self._trigger_buffer
                if ts >= cutoff_time
            ]
    
    def _check_sustained_trigger(self, timestamp: datetime) -> bool:
        """
        Check if trigger has been sustained over the window.
        
        Returns True if the trigger condition has been met for at least
        the sustained trigger window duration.
        """
        if len(self._trigger_buffer) < 2:
            return False
        
        # Check triggers within the sustained window
        window_start = timestamp - timedelta(seconds=self.config.sustained_trigger_window_seconds)
        triggers_in_window = [
            triggered for ts, triggered in self._trigger_buffer
            if ts >= window_start
        ]
        
        if not triggers_in_window:
            return False
        
        # Calculate sustained rate (fraction of time trigger was active)
        sustained_rate = sum(triggers_in_window) / len(triggers_in_window)
        
        # Trigger is sustained if rate exceeds threshold
        return sustained_rate >= self.config.sustained_trigger_threshold
    
    def reset(self) -> None:
        """Reset the gate's state."""
        self._last_action_time = None
        self._last_trigger_time = None
        self._evidence_buffer.clear()
        self._trigger_buffer.clear()
        logger.debug(f"ActionGate '{self.action_name}': reset")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current gate state for debugging/observability."""
        now = datetime.now(timezone.utc)
        time_since_last_action = None
        if self._last_action_time:
            time_since_last_action = (now - self._last_action_time).total_seconds()
        
        return {
            "action_name": self.action_name,
            "last_action_time": self._last_action_time.isoformat() if self._last_action_time else None,
            "time_since_last_action": time_since_last_action,
            "evidence_buffer_size": len(self._evidence_buffer),
            "trigger_buffer_size": len(self._trigger_buffer),
            "config": {
                "debounce_seconds": self.config.debounce_seconds,
                "cooldown_seconds": self.config.cooldown_seconds,
                "min_evidence_window_seconds": self.config.min_evidence_window_seconds,
                "min_evidence_count": self.config.min_evidence_count,
                "sustained_trigger_threshold": self.config.sustained_trigger_threshold,
                "sustained_trigger_window_seconds": self.config.sustained_trigger_window_seconds,
            },
        }

