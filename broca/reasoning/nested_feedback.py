"""
Nested feedback loop system.

Implements nested feedback loops with different time scales (fast/slow loops)
and adaptive feedback strength based on system state.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

if TYPE_CHECKING:
    from .feedback_loop import FeedbackLoopManager, FeedbackMetrics
    from .cognitive_dissonance import CognitiveDissonanceMonitor

logger = logging.getLogger(__name__)


class FeedbackTimeScale(Enum):
    """Time scales for feedback loops."""
    FAST = "fast"        # Milliseconds to seconds (immediate reactions)
    MEDIUM = "medium"    # Seconds to minutes (short-term adjustments)
    SLOW = "slow"        # Minutes to hours (long-term adaptation)


@dataclass
class FeedbackLoop:
    """A single feedback loop."""
    loop_id: str
    name: str
    time_scale: FeedbackTimeScale
    update_interval: float  # Seconds between updates
    strength: float  # 0.0 to 1.0
    enabled: bool = True
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    update_count: int = 0
    handler: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None


@dataclass
class NestedFeedbackConfig:
    """Configuration for nested feedback system."""
    fast_interval: float = 0.1  # 100ms
    medium_interval: float = 5.0  # 5 seconds
    slow_interval: float = 60.0  # 1 minute
    adaptive_strength: bool = True
    max_nesting_depth: int = 3


class NestedFeedbackSystem:
    """
    Nested feedback loop system with multiple time scales.
    
    Supports:
    - Fast loops: Immediate reactions (milliseconds to seconds)
    - Medium loops: Short-term adjustments (seconds to minutes)
    - Slow loops: Long-term adaptation (minutes to hours)
    - Adaptive feedback strength based on system state
    - Loop composition and chaining
    """
    
    def __init__(
        self,
        config: Optional[NestedFeedbackConfig] = None,
        feedback_loop_manager: Optional["FeedbackLoopManager"] = None,
        cognitive_dissonance_monitor: Optional["CognitiveDissonanceMonitor"] = None
    ):
        """
        Initialize nested feedback system.
        
        Args:
            config: Optional configuration
            feedback_loop_manager: Optional FeedbackLoopManager for integration
            cognitive_dissonance_monitor: Optional CognitiveDissonanceMonitor for state-based adaptation
        """
        self.config = config or NestedFeedbackConfig()
        self.feedback_loop_manager = feedback_loop_manager
        self.cognitive_dissonance_monitor = cognitive_dissonance_monitor
        
        # Feedback loops by time scale
        self.fast_loops: List[FeedbackLoop] = []
        self.medium_loops: List[FeedbackLoop] = []
        self.slow_loops: List[FeedbackLoop] = []
        
        # Loop registry
        self.loops: Dict[str, FeedbackLoop] = {}
        self.next_loop_id: int = 1
        
        # Loop composition (chains of loops)
        self.loop_chains: List[List[str]] = []  # List of loop ID chains
        
        # State tracking
        self.system_state: Dict[str, Any] = {}
        self.feedback_history: deque = deque(maxlen=1000)
        
        logger.info("Initialized NestedFeedbackSystem")
    
    def register_loop(
        self,
        name: str,
        time_scale: FeedbackTimeScale,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        initial_strength: float = 1.0
    ) -> str:
        """
        Register a feedback loop.
        
        Args:
            name: Loop name
            time_scale: Time scale for the loop
            handler: Handler function that processes feedback
            initial_strength: Initial feedback strength
            
        Returns:
            Loop ID
        """
        loop_id = f"feedback_loop_{self.next_loop_id}"
        self.next_loop_id += 1
        
        # Determine update interval based on time scale
        if time_scale == FeedbackTimeScale.FAST:
            interval = self.config.fast_interval
            loop_list = self.fast_loops
        elif time_scale == FeedbackTimeScale.MEDIUM:
            interval = self.config.medium_interval
            loop_list = self.medium_loops
        else:  # SLOW
            interval = self.config.slow_interval
            loop_list = self.slow_loops
        
        loop = FeedbackLoop(
            loop_id=loop_id,
            name=name,
            time_scale=time_scale,
            update_interval=interval,
            strength=initial_strength,
            handler=handler
        )
        
        loop_list.append(loop)
        self.loops[loop_id] = loop
        
        logger.info(f"Registered feedback loop: {name} ({time_scale.value}, interval={interval}s)")
        
        return loop_id
    
    def create_loop_chain(self, loop_ids: List[str]) -> str:
        """
        Create a chain of feedback loops.
        
        Args:
            loop_ids: List of loop IDs in execution order
            
        Returns:
            Chain ID
        """
        # Validate all loops exist
        for loop_id in loop_ids:
            if loop_id not in self.loops:
                raise ValueError(f"Loop {loop_id} not found")
        
        self.loop_chains.append(loop_ids)
        chain_id = f"chain_{len(self.loop_chains)}"
        
        logger.info(f"Created feedback loop chain: {chain_id} with {len(loop_ids)} loops")
        
        return chain_id
    
    def update_all_loops(self, system_state: Optional[Dict[str, Any]] = None):
        """
        Update all feedback loops based on their time scales.
        
        Args:
            system_state: Optional current system state
        """
        if system_state:
            self.system_state = system_state
        
        current_time = datetime.now(timezone.utc)
        
        # Update fast loops
        self._update_loops(self.fast_loops, current_time)
        
        # Update medium loops
        self._update_loops(self.medium_loops, current_time)
        
        # Update slow loops
        self._update_loops(self.slow_loops, current_time)
        
        # Update adaptive strengths if enabled
        if self.config.adaptive_strength:
            self._update_adaptive_strengths()
    
    def _update_loops(
        self,
        loops: List[FeedbackLoop],
        current_time: datetime
    ):
        """Update a list of loops."""
        for loop in loops:
            if not loop.enabled:
                continue
            
            # Check if it's time to update
            time_since_update = (current_time - loop.last_update).total_seconds()
            if time_since_update >= loop.update_interval:
                try:
                    # Prepare feedback context
                    context = {
                        "system_state": self.system_state,
                        "loop_name": loop.name,
                        "time_scale": loop.time_scale.value,
                        "strength": loop.strength,
                        "update_count": loop.update_count
                    }
                    
                    # Call handler
                    if loop.handler:
                        result = loop.handler(context)
                        
                        # Record feedback
                        feedback_record = {
                            "loop_id": loop.loop_id,
                            "loop_name": loop.name,
                            "time_scale": loop.time_scale.value,
                            "timestamp": current_time.isoformat(),
                            "result": result
                        }
                        self.feedback_history.append(feedback_record)
                        
                        loop.update_count += 1
                        loop.last_update = current_time
                        
                        logger.debug(f"Updated feedback loop: {loop.name}")
                    
                except Exception as e:
                    logger.error(f"Error updating feedback loop {loop.name}: {e}", exc_info=True)
    
    def _update_adaptive_strengths(self):
        """Update feedback loop strengths adaptively based on system state."""
        # Get dissonance level if available
        dissonance = 0.5  # Default
        if self.cognitive_dissonance_monitor:
            dissonance_data = self.cognitive_dissonance_monitor.get_aggregated_dissonance()
            dissonance = dissonance_data.get("overall_dissonance", 0.5)
        
        # Adjust strengths based on dissonance
        # High dissonance -> stronger feedback (faster correction)
        # Low dissonance -> weaker feedback (maintain stability)
        
        for loop in self.loops.values():
            if loop.time_scale == FeedbackTimeScale.FAST:
                # Fast loops: strengthen when dissonance is high
                if dissonance > 0.6:
                    loop.strength = min(1.0, loop.strength + 0.1)
                elif dissonance < 0.3:
                    loop.strength = max(0.3, loop.strength - 0.05)
            
            elif loop.time_scale == FeedbackTimeScale.MEDIUM:
                # Medium loops: moderate adjustment
                if dissonance > 0.5:
                    loop.strength = min(1.0, loop.strength + 0.05)
                elif dissonance < 0.4:
                    loop.strength = max(0.5, loop.strength - 0.05)
            
            else:  # SLOW
                # Slow loops: gradual adjustment
                if dissonance > 0.7:
                    loop.strength = min(1.0, loop.strength + 0.02)
                elif dissonance < 0.2:
                    loop.strength = max(0.7, loop.strength - 0.02)
            
            # Clamp strength
            loop.strength = max(0.0, min(1.0, loop.strength))
    
    def execute_chain(
        self,
        chain_id: str,
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a chain of feedback loops.
        
        Args:
            chain_id: Chain ID (index in loop_chains)
            initial_context: Initial context for the chain
            
        Returns:
            Final result after chain execution
        """
        try:
            chain_index = int(chain_id.split("_")[1]) - 1
            if chain_index < 0 or chain_index >= len(self.loop_chains):
                raise ValueError(f"Invalid chain ID: {chain_id}")
            
            loop_ids = self.loop_chains[chain_index]
            context = initial_context.copy()
            
            # Execute loops in sequence
            for loop_id in loop_ids:
                loop = self.loops[loop_id]
                if loop.handler:
                    result = loop.handler({
                        **context,
                        "loop_name": loop.name,
                        "time_scale": loop.time_scale.value
                    })
                    context.update(result)
            
            return context
            
        except Exception as e:
            logger.error(f"Error executing feedback chain {chain_id}: {e}", exc_info=True)
            return {"error": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about feedback loops."""
        total_updates = sum(loop.update_count for loop in self.loops.values())
        
        updates_by_scale = {
            "fast": sum(loop.update_count for loop in self.fast_loops),
            "medium": sum(loop.update_count for loop in self.medium_loops),
            "slow": sum(loop.update_count for loop in self.slow_loops)
        }
        
        avg_strength_by_scale = {
            "fast": sum(loop.strength for loop in self.fast_loops) / len(self.fast_loops) if self.fast_loops else 0.0,
            "medium": sum(loop.strength for loop in self.medium_loops) / len(self.medium_loops) if self.medium_loops else 0.0,
            "slow": sum(loop.strength for loop in self.slow_loops) / len(self.slow_loops) if self.slow_loops else 0.0
        }
        
        return {
            "total_loops": len(self.loops),
            "fast_loops": len(self.fast_loops),
            "medium_loops": len(self.medium_loops),
            "slow_loops": len(self.slow_loops),
            "total_updates": total_updates,
            "updates_by_scale": updates_by_scale,
            "avg_strength_by_scale": avg_strength_by_scale,
            "loop_chains": len(self.loop_chains),
            "feedback_history_size": len(self.feedback_history)
        }

