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
from .storage import InternalSensingStorage
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
        embedding_service: Optional[Any] = None,
    ) -> None:
        """
        Initialize internal sensing framework.
        
        Args:
            sampling_rate: Sampling rate in Hz (defaults to config)
            history_window: History window in seconds (defaults to config)
        """
        self.sampling_rate = sampling_rate or config.internal_sensing.sampling_rate
        self.history_window = history_window or config.internal_sensing.history_window
        
        # Initialize storage for persistence
        self.storage = InternalSensingStorage(config.internal_sensing.state_path)
        
        # Initialize integrated interoception
        self.interoception = IntegratedInteroception(history_window=self.history_window, embedding_service=embedding_service)
        
        # Internal state log
        self.internal_state_log: deque = deque(maxlen=int(self.history_window * self.sampling_rate))
        
        # Tool usage tracking
        self._tool_usage: List[Dict[str, Any]] = []
        
        # Last sample time for rate control
        self._last_sample_time: float = 0.0
        
        # Load persisted state if available
        self._load_state()
        
        # Seed initial baseline sample to ensure moving averages have data immediately
        # This ensures moving averages work from the first sample
        try:
            initial_state = self.interoception.sample_internal_state()
            self.internal_state_log.append(initial_state)
            logger.debug("Seeded initial baseline sample for moving averages")
        except Exception as e:
            logger.warning(f"Failed to seed initial baseline sample: {e}", exc_info=True)
        
        logger.info(
            f"Initialized InternalSensingFramework "
            f"(sampling_rate={self.sampling_rate}Hz, history_window={self.history_window}s)"
        )
    
    def sample_internal_state(self, force: bool = False) -> Dict[str, Any]:
        """
        Sample internal state at configured rate.
        
        Args:
            force: If True, force a fresh sample even if rate limit hasn't been reached
        
        Returns:
            Dictionary containing complete internal state
        """
        current_time = time.time()
        
        # Check if we should sample based on rate (unless forced)
        time_since_last = current_time - self._last_sample_time
        min_interval = 1.0 / self.sampling_rate if self.sampling_rate > 0 else 0.0
        
        if force or time_since_last >= min_interval:
            # Always get fresh state from interoception (which uses moving averages)
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
    


    def record_informational_surprise(self, expectation: str, reality: str) -> None:
        """
        Record informational surprise (novelty).
        
        Args:
            expectation: Predicted content
            reality: Actual content
        """
        self.interoception.record_informational_surprise(expectation, reality)

    def record_cognitive_impact(self, tool_name: str, impact_level: int = 1) -> None:
        """
        Record the cognitive impact of an operation.
        
        Args:
            tool_name: Name of the tool or operation
            impact_level: Depth/complexity of the operation
        """
        if self.interoception.cognition:
            # Record processing depth
            self.interoception.cognition.record_processing_depth(
                f'tool_{tool_name}_{time.time()}', 
                impact_level
            )
            
            # Record reasoning pattern
            self.interoception.cognition.record_reasoning_pattern(
                'tool_usage', 
                tool_name
            )

    def get_llm_description(self) -> str:
        """
        Generate LLM-readable description of internal state.
        
        Returns:
            Natural language description
        """
        return self.generate_interoceptive_report()
    
    def save_state(self) -> None:
        """
        Save moving average histories to disk.
        
        Called after significant updates and on shutdown.
        """
        try:
            # Collect histories from all monitors
            cognitive_histories = {}
            affective_histories = {}
            physiology_histories = {}
            
            if self.interoception.cognition:
                cognitive_histories = self.interoception.cognition.serialize_histories()
            
            if self.interoception.affect:
                affective_histories = self.interoception.affect.serialize_histories()
            
            if self.interoception.physiology:
                physiology_histories = self.interoception.physiology.serialize_histories()
            
            # Save to disk
            self.storage.save_state(
                cognitive_histories=cognitive_histories,
                affective_histories=affective_histories,
                physiology_histories=physiology_histories,
            )
            
            logger.debug("Saved internal sensing state to disk")
            
        except Exception as e:
            logger.warning(f"Failed to save internal sensing state: {e}", exc_info=True)
    
    def _load_state(self) -> None:
        """
        Load moving average histories from disk.
        
        Called during initialization.
        """
        try:
            state_data = self.storage.load_state()
            if state_data is None:
                logger.debug("No persisted state found, starting fresh")
                return
            
            # Restore cognitive histories
            if self.interoception.cognition and "cognitive" in state_data:
                self.interoception.cognition.deserialize_histories(state_data["cognitive"])
            
            # Restore affective histories
            if self.interoception.affect and "affective" in state_data:
                self.interoception.affect.deserialize_histories(state_data["affective"])
            
            # Restore physiology histories
            if self.interoception.physiology and "physiology" in state_data:
                self.interoception.physiology.deserialize_histories(state_data["physiology"])
            
            logger.info("Loaded persisted internal sensing state from disk")
            
        except Exception as e:
            logger.warning(f"Failed to load internal sensing state: {e}", exc_info=True)

