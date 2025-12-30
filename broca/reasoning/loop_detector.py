"""
Loop detection for production rule system.

Detects and prevents infinite loops in rule execution using:
- History-based tracking: Rule firing history with time windows
- Graph-based detection: Rule dependency graph cycle detection
- Tool queue monitoring: Prevents queue growth and repeated tool calls
"""

from __future__ import annotations

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple, Set, TYPE_CHECKING
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from collections import deque, defaultdict

if TYPE_CHECKING:
    from .production_rules import ProductionRule
    from .working_memory import WorkingMemory

logger = logging.getLogger(__name__)


@dataclass
class RuleFiringRecord:
    """Record of a rule firing for loop detection."""
    rule_name: str
    wm_state_hash: str
    timestamp: datetime
    fired_count: int = 1


class LoopDetector:
    """
    Detects and prevents infinite loops in rule execution.
    
    Uses both history-based and graph-based detection methods.
    """
    
    def __init__(
        self,
        history_window: int = 10,
        time_window_seconds: float = 60.0,
        max_tool_queue_size: int = 50,
        max_tool_retries: int = 3
    ):
        """
        Initialize loop detector.
        
        Args:
            history_window: Number of recent rule firings to track
            time_window_seconds: Time window for detecting repeated firings
            max_tool_queue_size: Maximum size of tool queue before blocking
            max_tool_retries: Maximum retries per tool call before blocking
        """
        self.history_window = history_window
        self.time_window_seconds = time_window_seconds
        self.max_tool_queue_size = max_tool_queue_size
        self.max_tool_retries = max_tool_retries
        
        # History-based tracking: (rule_name, wm_state_hash) -> list of timestamps
        self._firing_history: deque = deque(maxlen=history_window)
        self._firing_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        
        # Graph-based tracking: rule_name -> set of rules it enables
        self._rule_graph: Dict[str, Set[str]] = {}
        
        # Tool queue tracking: tool_name -> retry count
        self._tool_retry_counts: Dict[str, int] = defaultdict(int)
        self._tool_last_call: Dict[str, datetime] = {}
        
    def check_rule_firing(
        self,
        rule: "ProductionRule",
        working_memory: "WorkingMemory"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a rule firing should be allowed.
        
        Args:
            rule: Rule that wants to fire
            working_memory: Current working memory state
            
        Returns:
            Tuple of (allowed, reason) - False if loop detected
        """
        # Compute working memory state hash
        wm_hash = self._hash_wm_state(working_memory)
        rule_key = (rule.name, wm_hash)
        
        # Check history-based detection
        now = datetime.now(timezone.utc)
        recent_firings = [
            record for record in self._firing_history
            if record.rule_name == rule.name
            and record.wm_state_hash == wm_hash
            and (now - record.timestamp).total_seconds() < self.time_window_seconds
        ]
        
        if recent_firings:
            # Same rule fired with same WM state recently
            firing_count = len(recent_firings)
            if firing_count >= 3:  # Allow up to 2 retries, block on 3rd
                reason = (
                    f"Rule '{rule.name}' fired {firing_count} times with same WM state "
                    f"within {self.time_window_seconds}s (possible loop)"
                )
                logger.warning(reason)
                return False, reason
        
        # Check graph-based cycle detection
        if self._would_create_cycle(rule, working_memory):
            reason = f"Rule '{rule.name}' would create a cycle in rule dependency graph"
            logger.warning(reason)
            return False, reason
        
        # Allowed
        return True, None
    
    def record_rule_firing(
        self,
        rule: "ProductionRule",
        working_memory: "WorkingMemory",
        enabled_rules: List["ProductionRule"]
    ) -> None:
        """
        Record a rule firing and update dependency graph.
        
        Args:
            rule: Rule that fired
            working_memory: Working memory state after firing
            enabled_rules: List of rules that are now enabled (matched) after this firing
        """
        wm_hash = self._hash_wm_state(working_memory)
        
        # Record in history
        record = RuleFiringRecord(
            rule_name=rule.name,
            wm_state_hash=wm_hash,
            timestamp=datetime.now(timezone.utc)
        )
        self._firing_history.append(record)
        self._firing_counts[(rule.name, wm_hash)] += 1
        
        # Update dependency graph
        if rule.name not in self._rule_graph:
            self._rule_graph[rule.name] = set()
        
        for enabled_rule in enabled_rules:
            self._rule_graph[rule.name].add(enabled_rule.name)
    
    def check_tool_queue(
        self,
        queue: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if tool queue is within limits.
        
        Args:
            queue: Current tool queue
            
        Returns:
            Tuple of (allowed, reason) - False if queue too large
        """
        if len(queue) >= self.max_tool_queue_size:
            reason = (
                f"Tool queue size ({len(queue)}) exceeds maximum "
                f"({self.max_tool_queue_size}). Possible infinite loop."
            )
            logger.warning(reason)
            return False, reason
        
        # Check for repeated tool calls (possible loop)
        tool_calls_by_name: Dict[str, int] = defaultdict(int)
        for tool_call in queue:
            tool_name = tool_call.get("tool_name", "unknown")
            tool_calls_by_name[tool_name] += 1
            
            if tool_calls_by_name[tool_name] > self.max_tool_retries:
                reason = (
                    f"Tool '{tool_name}' appears {tool_calls_by_name[tool_name]} times "
                    f"in queue (max: {self.max_tool_retries}). Possible loop."
                )
                logger.warning(reason)
                return False, reason
        
        return True, None
    
    def check_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a tool call should be allowed (retry limit).
        
        Args:
            tool_name: Name of tool to call
            parameters: Tool parameters
            
        Returns:
            Tuple of (allowed, reason) - False if retry limit exceeded
        """
        now = datetime.now(timezone.utc)
        tool_key = f"{tool_name}:{json.dumps(parameters, sort_keys=True)}"
        
        # Check if same tool call was made recently
        if tool_key in self._tool_last_call:
            last_call_time = self._tool_last_call[tool_key]
            time_since_last = (now - last_call_time).total_seconds()
            
            if time_since_last < 1.0:  # Same call within 1 second
                self._tool_retry_counts[tool_key] += 1
            else:
                # Reset counter if enough time passed
                self._tool_retry_counts[tool_key] = 1
        else:
            self._tool_retry_counts[tool_key] = 1
        
        self._tool_last_call[tool_key] = now
        
        # Check retry limit
        if self._tool_retry_counts[tool_key] > self.max_tool_retries:
            reason = (
                f"Tool '{tool_name}' called {self._tool_retry_counts[tool_key]} times "
                f"with same parameters (max: {self.max_tool_retries}). Possible loop."
            )
            logger.warning(reason)
            return False, reason
        
        return True, None
    
    def _would_create_cycle(
        self,
        rule: "ProductionRule",
        working_memory: "WorkingMemory"
    ) -> bool:
        """
        Check if firing this rule would create a cycle in the dependency graph.
        
        Uses DFS to detect cycles.
        
        Args:
            rule: Rule to check
            working_memory: Current working memory
            
        Returns:
            True if cycle would be created
        """
        # Build temporary graph including this rule
        temp_graph = self._rule_graph.copy()
        if rule.name not in temp_graph:
            temp_graph[rule.name] = set()
        
        # Find which rules would be enabled by this rule
        # (simplified: we'd need to actually match rules to know)
        # For now, we check if there's already a path from enabled rules back to this rule
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in temp_graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found back edge - cycle detected
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check if adding this rule creates a cycle
        # We check if any rule that would be enabled by this rule can reach back to this rule
        for enabled_rule_name in temp_graph.get(rule.name, set()):
            if enabled_rule_name == rule.name:
                # Self-loop
                return True
            
            # Check if enabled rule can reach back to this rule
            visited.clear()
            rec_stack.clear()
            if has_cycle(enabled_rule_name):
                return True
        
        return False
    
    def _hash_wm_state(self, working_memory: "WorkingMemory") -> str:
        """
        Create a hash of working memory state for loop detection.
        
        Args:
            working_memory: Working memory to hash
            
        Returns:
            Hash string
        """
        # Create a simplified representation of WM state
        # Include item types and key fields, but not full content
        wm_state = {
            "item_count": len(working_memory.items),
            "item_types": [item.content.get("type", "unknown") for item in working_memory.items],
            "goals": [g.get("name", "unknown") for g in working_memory.goals],
            "queue_size": len(working_memory.tool_queue)
        }
        
        state_str = json.dumps(wm_state, sort_keys=True)
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def clear_history(self) -> None:
        """Clear firing history (useful for testing or reset)."""
        self._firing_history.clear()
        self._firing_counts.clear()
        self._tool_retry_counts.clear()
        self._tool_last_call.clear()
        logger.debug("Cleared loop detector history")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get loop detection statistics."""
        return {
            "history_size": len(self._firing_history),
            "rule_graph_size": len(self._rule_graph),
            "firing_counts": dict(self._firing_counts),
            "tool_retry_counts": dict(self._tool_retry_counts),
            "max_tool_queue_size": self.max_tool_queue_size,
            "max_tool_retries": self.max_tool_retries
        }

