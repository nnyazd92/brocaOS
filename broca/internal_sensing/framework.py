"""
Internal sensing framework.

Main framework that orchestrates all internal sensing components and provides
the primary interface for internal state monitoring.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional
from collections import deque, defaultdict

from .integrated_interoception import IntegratedInteroception
from ..config import config

logger = logging.getLogger(__name__)


class InternalSensingFramework:
    """
    Main internal sensing framework.
    
    Orchestrates all internal sensing components and provides unified interface.
    """
    
    def __init__(
        self,
        sampling_rate: Optional[float] = None,
        history_window: Optional[int] = None,
    ) -> None:
        """
        Initialize internal sensing framework.
        
        Args:
            sampling_rate: Sampling rate in Hz (defaults to config)
            history_window: History window in seconds (defaults to config)
        """
        self.sampling_rate = sampling_rate or config.internal_sensing.sampling_rate
        self.history_window = history_window or config.internal_sensing.history_window
        
        # Initialize integrated interoception
        self.interoception = IntegratedInteroception(history_window=self.history_window)
        
        # Internal state log
        self.internal_state_log: deque = deque(maxlen=int(self.history_window * self.sampling_rate))
        
        # Tool usage tracking
        self._tool_usage: List[Dict[str, Any]] = []
        
        # Last sample time for rate control
        self._last_sample_time: float = 0.0
        
        logger.info(
            f"Initialized InternalSensingFramework "
            f"(sampling_rate={self.sampling_rate}Hz, history_window={self.history_window}s)"
        )
    
    def sample_internal_state(self) -> Dict[str, Any]:
        """
        Sample internal state at configured rate.
        
        Returns:
            Dictionary containing complete internal state
        """
        current_time = time.time()
        
        # Check if we should sample based on rate
        time_since_last = current_time - self._last_sample_time
        min_interval = 1.0 / self.sampling_rate if self.sampling_rate > 0 else 0.0
        
        if time_since_last >= min_interval:
            state = self.interoception.sample_internal_state()
            self.internal_state_log.append(state)
            self._last_sample_time = current_time
            return state
        else:
            # Return most recent state if not time to sample yet
            if len(self.internal_state_log) > 0:
                return self.internal_state_log[-1]
            else:
                return self.interoception.sample_internal_state()
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """
        Get history of internal states.
        
        Returns:
            List of state dictionaries
        """
        return list(self.internal_state_log)
    
    def generate_interoceptive_report(self) -> str:
        """
        Generate natural language interoceptive report.
        
        Returns:
            Natural language description of internal state
        """
        return self.interoception.generate_interoceptive_report()
    
    def record_tool_usage(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Record tool usage for pattern analysis.
        
        Args:
            tool_name: Name of the tool used
            parameters: Tool parameters
            result: Tool execution result
        """
        self._tool_usage.append({
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "timestamp": time.time(),
        })
        
        # Keep only recent usage
        if len(self._tool_usage) > 100:
            self._tool_usage = self._tool_usage[-100:]
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """
        Get tool usage statistics.
        
        Returns:
            Dictionary with tool usage statistics
        """
        if len(self._tool_usage) == 0:
            return {}
        
        stats = defaultdict(int)
        for usage in self._tool_usage:
            stats[usage["tool_name"]] += 1
        
        return dict(stats)
    
    def extract_behavioral_patterns(self) -> List[Dict[str, Any]]:
        """
        Extract behavioral patterns from internal sensing data.
        
        Returns:
            List of behavioral pattern dictionaries
        """
        patterns = []
        
        # Extract patterns from cognitive state
        cognitive_patterns = self.interoception.cognition._get_reasoning_patterns()
        for pattern in cognitive_patterns:
            patterns.append({
                "type": "reasoning",
                "pattern": pattern,
                "source": "cognitive",
            })
        
        # Extract patterns from tool usage
        tool_stats = self.get_tool_statistics()
        for tool_name, count in tool_stats.items():
            if count > 5:  # Frequently used tools
                patterns.append({
                    "type": "tool_usage",
                    "tool": tool_name,
                    "frequency": count,
                    "source": "tool_usage",
                })
        
        return patterns
    
    def get_llm_description(self) -> str:
        """
        Generate LLM-readable description of internal state.
        
        Returns:
            Natural language description
        """
        return self.generate_interoceptive_report()

