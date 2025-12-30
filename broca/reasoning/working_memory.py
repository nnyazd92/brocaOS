"""
Working memory for cognitive reasoning.

Implements an active memory buffer with activation levels, decay,
and attention mechanisms similar to ACT-R working memory.
"""

from __future__ import annotations

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field
from contextlib import contextmanager

if TYPE_CHECKING:
    from .declarative_memory import DeclarativeMemoryInterface
    from .spreading_activation import SpreadingActivation
    from .llm_pattern_matcher import LLMPatternMatcher

logger = logging.getLogger(__name__)


@dataclass
class WorkingMemoryItem:
    """An item in working memory with activation level."""
    
    content: Dict[str, Any]
    activation: float = 1.0  # Current activation level
    base_level: float = 1.0  # Base activation (before decay)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 1
    decay_rate: float = 0.1  # How quickly activation decays
    
    def update_activation(self, time_passed: float = 1.0):
        """Update activation based on decay and time passed."""
        # Decay: activation = base_level * exp(-decay_rate * time_passed)
        time_since_access = (datetime.now(timezone.utc) - self.last_accessed).total_seconds()
        self.activation = self.base_level * (0.5 ** (self.decay_rate * time_since_access))
        
        # Also apply time-based decay since creation
        time_since_creation = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        creation_decay = 0.5 ** (0.01 * time_since_creation)  # Slow decay over hours
        self.activation *= creation_decay
        
        # Ensure activation stays in reasonable bounds
        self.activation = max(0.01, min(10.0, self.activation))
    
    def strengthen(self, amount: float = 0.2):
        """Strengthen the item (increase base level)."""
        self.base_level += amount
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)
        self.update_activation(0)  # Update with no time passed to apply new base level
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content": self.content,
            "activation": self.activation,
            "base_level": self.base_level,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "decay_rate": self.decay_rate,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkingMemoryItem:
        """Create from dictionary representation."""
        return cls(
            content=data["content"],
            activation=data.get("activation", 1.0),
            base_level=data.get("base_level", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if "last_accessed" in data else datetime.now(timezone.utc),
            access_count=data.get("access_count", 1),
            decay_rate=data.get("decay_rate", 0.1),
        )


class WorkingMemory:
    """
    Working memory buffer with activation-based retrieval.
    
    Models human working memory with limited capacity,
    activation-based retrieval, and decay over time.
    """
    
    def __init__(
        self,
        capacity: int = 7,
        update_interval: float = 1.0,
        declarative_memory: Optional["DeclarativeMemoryInterface"] = None,
        spreading_activation: Optional["SpreadingActivation"] = None,
        pattern_matcher: Optional["LLMPatternMatcher"] = None
    ):
        """
        Initialize working memory.
        
        Args:
            capacity: Maximum number of items (Miller's law: 7 ± 2)
            update_interval: How often to update activations (seconds)
            declarative_memory: Optional DeclarativeMemoryInterface for LTM integration
            spreading_activation: Optional SpreadingActivation for activation propagation
            pattern_matcher: Optional LLMPatternMatcher for semantic pattern matching
        """
        self.capacity = capacity
        self.update_interval = update_interval
        self.items: List[WorkingMemoryItem] = []
        self.goals: List[Dict[str, Any]] = []
        self.tool_queue: List[Dict[str, Any]] = []  # Queued tool calls
        self.last_update = time.time()
        
        # Declarative memory integration
        self.declarative_memory = declarative_memory
        self.spreading_activation = spreading_activation
        self.pattern_matcher = pattern_matcher
        
        # Attention focus (what's currently being attended to)
        self.focus: Optional[Dict[str, Any]] = None
        self.focus_strength: float = 0.0
        
        # State variables
        self.state: Dict[str, Any] = {
            "cognitive_load": 0.0,
            "attention_span": 1.0,
            "processing_depth": 1.0,
            "mode": "normal",  # normal, focused, distracted
        }
        
        # Threshold for storing items to declarative memory before eviction
        self.store_threshold: float = 0.6  # Store items with importance >= this
        
        # Thread safety for state synchronization
        self._state_lock = threading.RLock()
    
    @contextmanager
    def acquire_state_lock(self, timeout: Optional[float] = None):
        """
        Context manager for acquiring state lock.
        
        Args:
            timeout: Optional timeout in seconds (None = no timeout)
        """
        acquired = self._state_lock.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError(f"Failed to acquire state lock within {timeout}s")
        try:
            yield
        finally:
            self._state_lock.release()
    
    def add(self, content: Dict[str, Any], activation: float = 1.0) -> bool:
        """
        Add an item to working memory.
        
        Returns True if added, False if capacity reached.
        """
        with self._state_lock:
            if len(self.items) >= self.capacity:
                # Remove lowest activation item if at capacity
                self._remove_lowest_activation()
            
            item = WorkingMemoryItem(content=content, activation=activation)
            self.items.append(item)
            
            # Update cognitive load
            self.state["cognitive_load"] = len(self.items) / self.capacity
            
            logger.info(
                f"Added item to working memory: type={content.get('type', 'unknown')}, "
                f"activation={activation:.3f}, items_count={len(self.items)}/{self.capacity}, "
                f"cognitive_load={self.state['cognitive_load']:.3f}",
                extra={
                    "event": "working_memory_item_added",
                    "item_type": content.get('type', 'unknown'),
                    "activation": activation,
                    "items_count": len(self.items),
                    "capacity": self.capacity,
                    "cognitive_load": self.state["cognitive_load"],
                    "utilization": len(self.items) / self.capacity,
                }
            )
            return True
    
    def _remove_lowest_activation(self) -> Optional[WorkingMemoryItem]:
        """Remove the item with lowest activation."""
        if not self.items:
            return None
        
        # Find item with lowest activation
        lowest_idx = min(range(len(self.items)), key=lambda i: self.items[i].activation)
        removed = self.items.pop(lowest_idx)
        removed_activation = removed.activation
        
        # Store to declarative memory before eviction if it meets threshold
        stored_count = 0
        if self.declarative_memory:
            stored_count = self.to_declarative_memory([removed])
        
        logger.info(
            f"Removed low-activation item from working memory: type={removed.content.get('type', 'unknown')}, "
            f"activation={removed_activation:.3f}, stored_to_declarative={stored_count}, "
            f"remaining_items={len(self.items)}/{self.capacity}",
            extra={
                "event": "working_memory_item_removed",
                "item_type": removed.content.get('type', 'unknown'),
                "activation": removed_activation,
                "stored_to_declarative": stored_count,
                "remaining_items": len(self.items),
                "capacity": self.capacity,
            }
        )
        return removed
    
    def retrieve(self, pattern: Dict[str, Any] = None, 
                 min_activation: float = 0.5) -> List[Dict[str, Any]]:
        """
        Retrieve items matching pattern with sufficient activation.
        
        Returns list of content dictionaries.
        """
        self._update_activations()
        
        matching_items = []
        evaluated_count = 0
        for item in self.items:
            evaluated_count += 1
            if item.activation < min_activation:
                continue
            
            if pattern is None or self._pattern_matches(pattern, item.content):
                matching_items.append((item.activation, item.content))
                item.strengthen(0.1)  # Strengthen on retrieval
        
        # Sort by activation (highest first)
        matching_items.sort(key=lambda x: x[0], reverse=True)
        
        retrieved_content = [content for _, content in matching_items]
        
        logger.info(
            f"Retrieved items from working memory: pattern={pattern is not None}, "
            f"min_activation={min_activation:.3f}, evaluated={evaluated_count}, "
            f"matched={len(retrieved_content)}, "
            f"top_activation={matching_items[0][0]:.3f if matching_items else 0.0}",
            extra={
                "event": "working_memory_retrieve",
                "has_pattern": pattern is not None,
                "min_activation": min_activation,
                "evaluated_count": evaluated_count,
                "matched_count": len(retrieved_content),
                "total_items": len(self.items),
                "top_activation": matching_items[0][0] if matching_items else 0.0,
            }
        )
        
        # Return just the content
        return retrieved_content
    
    def _pattern_matches(self, pattern: Dict[str, Any], content: Dict[str, Any]) -> bool:
        """Check if pattern matches content."""
        # Use LLM pattern matcher if available
        if self.pattern_matcher is not None:
            return self.pattern_matcher.match(pattern, content)
        
        # Fallback to legacy dict subset/equality matching
        for key, value in pattern.items():
            if key not in content:
                return False
            if isinstance(value, dict) and isinstance(content[key], dict):
                if not self._pattern_matches(value, content[key]):
                    return False
            elif value != content[key]:
                return False
        return True
    
    def remove_matching(self, pattern: Dict[str, Any]) -> int:
        """Remove items matching pattern, return count removed."""
        with self._state_lock:
            removed_count = 0
            remaining_items = []
            
            for item in self.items:
                if self._pattern_matches(pattern, item.content):
                    removed_count += 1
                    logger.debug(f"Removed matching item: {item.content.get('type', 'unknown')}")
                else:
                    remaining_items.append(item)
            
            self.items = remaining_items
            
            # Update cognitive load after removal
            self.state["cognitive_load"] = len(self.items) / self.capacity
            
            logger.info(
                f"Removed matching items from working memory: pattern={pattern}, "
                f"removed_count={removed_count}, remaining_items={len(self.items)}/{self.capacity}, "
                f"cognitive_load={self.state['cognitive_load']:.3f}",
                extra={
                    "event": "working_memory_items_removed",
                    "pattern": pattern,
                    "removed_count": removed_count,
                    "remaining_items": len(self.items),
                    "capacity": self.capacity,
                    "cognitive_load": self.state["cognitive_load"],
                }
            )
            return removed_count
    
    def modify_matching(self, pattern: Dict[str, Any], 
                       modification: Dict[str, Any]) -> int:
        """Modify items matching pattern, return count modified."""
        with self._state_lock:
            modified_count = 0
            
            for item in self.items:
                if self._pattern_matches(pattern, item.content):
                    # Apply modification
                    old_activation = item.activation
                    self._apply_modification(item.content, modification)
                    item.strengthen(0.05)  # Slight strengthening on modification
                    modified_count += 1
            
            if modified_count > 0:
                logger.info(
                    f"Modified items in working memory: pattern={pattern}, "
                    f"modified_count={modified_count}, total_items={len(self.items)}",
                    extra={
                        "event": "working_memory_items_modified",
                        "pattern": pattern,
                        "modified_count": modified_count,
                        "total_items": len(self.items),
                    }
                )
            
            return modified_count
    
    def _apply_modification(self, content: Dict[str, Any], 
                           modification: Dict[str, Any]):
        """Apply modification to content dictionary."""
        for key, value in modification.items():
            if key in content and isinstance(content[key], dict) and isinstance(value, dict):
                # Recursive merge for nested dicts
                self._apply_modification(content[key], value)
            else:
                content[key] = value
    
    def add_goal(self, goal: Dict[str, Any]):
        """Add a goal to working memory."""
        self.goals.append(goal)
        logger.info(
            f"Added goal to working memory: name={goal.get('name', 'unnamed')}, "
            f"total_goals={len(self.goals)}",
            extra={
                "event": "working_memory_goal_added",
                "goal_name": goal.get('name', 'unnamed'),
                "goal_status": goal.get('status', 'unknown'),
                "total_goals": len(self.goals),
            }
        )
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """Get active goals."""
        return [g for g in self.goals if g.get("status") == "active"]
    
    def queue_tool_call(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        loop_detector: Optional[Any] = None
    ):
        """
        Queue a tool call for execution.
        
        Args:
            tool_name: Name of tool to call
            parameters: Tool parameters
            loop_detector: Optional LoopDetector to check for loops
        """
        # Check loop detector if provided
        if loop_detector is not None:
            # Check tool queue size
            queue_allowed, queue_reason = loop_detector.check_tool_queue(self.tool_queue)
            if not queue_allowed:
                logger.error(f"Cannot queue tool call '{tool_name}': {queue_reason}")
                raise ValueError(f"Tool queue blocked: {queue_reason}")
            
            # Check individual tool call retry limit
            call_allowed, call_reason = loop_detector.check_tool_call(tool_name, parameters)
            if not call_allowed:
                logger.error(f"Cannot queue tool call '{tool_name}': {call_reason}")
                raise ValueError(f"Tool call blocked: {call_reason}")
        
        self.tool_queue.append({
            "tool_name": tool_name,
            "parameters": parameters,
            "queued_at": datetime.now(timezone.utc).isoformat()
        })
        logger.debug(f"Queued tool call: {tool_name}")
    
    def get_queued_tools(self) -> List[Dict[str, Any]]:
        """Get queued tool calls."""
        return self.tool_queue
    
    def clear_tool_queue(self):
        """Clear the tool queue."""
        self.tool_queue = []
    
    def set_focus(self, content: Dict[str, Any], strength: float = 1.0):
        """Set attention focus."""
        old_focus = self.focus
        old_strength = self.focus_strength
        self.focus = content
        self.focus_strength = strength
        logger.info(
            f"Set attention focus: type={content.get('type', 'unknown')}, "
            f"strength={strength:.3f} (was {old_strength:.3f})",
            extra={
                "event": "working_memory_focus_set",
                "focus_type": content.get('type', 'unknown'),
                "focus_strength": strength,
                "previous_strength": old_strength,
                "had_focus": old_focus is not None,
            }
        )
    
    def clear_focus(self):
        """Clear attention focus."""
        had_focus = self.focus is not None
        old_strength = self.focus_strength
        self.focus = None
        self.focus_strength = 0.0
        if had_focus:
            logger.info(
                f"Cleared attention focus (was {old_strength:.3f})",
                extra={
                    "event": "working_memory_focus_cleared",
                    "previous_strength": old_strength,
                }
            )
    
    def _update_activations(self):
        """Update activation levels of all items."""
        current_time = time.time()
        time_passed = current_time - self.last_update
        
        if time_passed < self.update_interval:
            return
        
        # Track activation changes
        activation_changes = []
        for item in self.items:
            old_activation = item.activation
            item.update_activation(time_passed)
            if abs(item.activation - old_activation) > 0.01:  # Only log significant changes
                activation_changes.append((old_activation, item.activation))
        
        # Trigger spreading activation if enabled
        if self.spreading_activation:
            self._trigger_spreading_activation()
        
        # Log periodic status if there were significant changes or enough time passed
        if activation_changes or time_passed >= 60.0:  # Log every minute or on significant changes
            avg_activation = sum(item.activation for item in self.items) / len(self.items) if self.items else 0.0
            max_activation = max((item.activation for item in self.items), default=0.0)
            min_activation = min((item.activation for item in self.items), default=0.0)
            
            logger.info(
                f"Working memory activation update: items={len(self.items)}/{self.capacity}, "
                f"time_passed={time_passed:.2f}s, avg_activation={avg_activation:.3f}, "
                f"activation_range=[{min_activation:.3f}, {max_activation:.3f}], "
                f"cognitive_load={self.state['cognitive_load']:.3f}, "
                f"significant_changes={len(activation_changes)}",
                extra={
                    "event": "working_memory_activation_update",
                    "items_count": len(self.items),
                    "capacity": self.capacity,
                    "time_passed_seconds": time_passed,
                    "avg_activation": avg_activation,
                    "min_activation": min_activation,
                    "max_activation": max_activation,
                    "cognitive_load": self.state["cognitive_load"],
                    "significant_changes": len(activation_changes),
                    "utilization": len(self.items) / self.capacity if self.capacity > 0 else 0.0,
                }
            )
        
        self.last_update = current_time
    
    def _trigger_spreading_activation(self):
        """Trigger spreading activation based on current WM state."""
        if not self.spreading_activation:
            return
        
        try:
            # Convert items to dict format for spreading activation
            items_dict = [
                {
                    "content": item.content,
                    "activation": item.activation
                }
                for item in self.items
            ]
            
            # Propagate activation and retrieve memories
            retrieved = self.spreading_activation.propagate_activation(
                working_memory_items=items_dict,
                limit=5
            )
            
            # Merge retrieved memories into WM (respect capacity limits)
            if retrieved:
                self._merge_retrieved_memories(retrieved)
                
        except Exception as e:
            logger.error(f"Error in spreading activation: {e}", exc_info=True)
    
    def _merge_retrieved_memories(self, memories: List[Any]):
        """
        Merge retrieved declarative memories into working memory.
        
        Args:
            memories: List of MemoryRecord objects from declarative memory
        """
        from ..memory import MemoryRecord
        
        for memory in memories:
            if not isinstance(memory, MemoryRecord):
                continue
            
            # Convert memory record to WM item content
            content = {
                "type": "declarative_memory",
                "memory_id": memory.id,
                "text": memory.text,
                "namespace": memory.namespace,
                "tags": memory.tags,
                "source": "declarative_memory"
            }
            
            # Add to WM with moderate activation (higher than threshold to be usable)
            # Only add if not at capacity or if we can make room
            if len(self.items) < self.capacity:
                self.add(content, activation=0.8)  # High activation for retrieved memories
            else:
                # Check if we should replace a lower-activation item
                lowest_activation = min(item.activation for item in self.items)
                if 0.8 > lowest_activation:
                    # Replace lowest activation item
                    removed = self._remove_lowest_activation()
                    self.add(content, activation=0.8)
                    logger.debug(f"Replaced WM item (activation {lowest_activation:.2f}) with retrieved memory")
                else:
                    # Don't add - current items are more important
                    logger.debug(f"Skipped merging memory {memory.id} - WM items have higher activation")
    
    def refresh_from_declarative_memory(self, limit: int = 5):
        """
        Refresh working memory from declarative memory based on current state.
        
        This retrieves relevant memories and merges them into WM.
        Called manually or automatically during activation updates.
        
        Args:
            limit: Maximum number of memories to retrieve
        """
        if not self.declarative_memory or not self.spreading_activation:
            return
        
        # Trigger spreading activation which will retrieve and merge
        self._trigger_spreading_activation()
    
    def to_declarative_memory(self, items: Optional[List[WorkingMemoryItem]] = None, importance_threshold: Optional[float] = None) -> int:
        """
        Store high-value working memory items to declarative memory.
        
        Args:
            items: Optional list of items to store (defaults to all items above threshold)
            importance_threshold: Optional threshold (defaults to self.store_threshold)
            
        Returns:
            Number of items stored
        """
        if not self.declarative_memory:
            return 0
        
        if importance_threshold is None:
            importance_threshold = self.store_threshold
        
        stored_count = 0
        
        # Determine which items to store
        items_to_store = items if items is not None else [
            item for item in self.items
            if item.activation >= importance_threshold
        ]
        
        for item in items_to_store:
            try:
                content_dict = item.content
                
                # Extract text from content
                if isinstance(content_dict, dict):
                    # Try to find text field
                    text = content_dict.get("text") or content_dict.get("content") or content_dict.get("description")
                    if not text:
                        # Fallback: stringify dict
                        text = str(content_dict)[:500]  # Limit length
                    
                    # Extract tags if present
                    tags = content_dict.get("tags", [])
                    if not isinstance(tags, list):
                        tags = []
                    
                    # Extract namespace if present
                    namespace = content_dict.get("namespace")
                    if namespace and isinstance(namespace, str):
                        namespace = f"{self.declarative_memory.reasoning_namespace}/working_memory/{namespace}"
                    else:
                        namespace = f"{self.declarative_memory.reasoning_namespace}/working_memory"
                    
                    # Determine importance from activation
                    importance = min(0.9, item.activation / 2.0)  # Scale activation to importance
                    
                    # Store to declarative memory
                    memory_id = self.declarative_memory.store_reasoning_result(
                        content=text,
                        source="working_memory",
                        tags=tags + ["working_memory"],
                        namespace=namespace,
                        importance=importance
                    )
                    
                    if memory_id:
                        stored_count += 1
                        logger.debug(f"Stored WM item to declarative memory: {memory_id}")
                        
            except Exception as e:
                logger.error(f"Error storing WM item to declarative memory: {e}", exc_info=True)
                continue
        
        if stored_count > 0:
            logger.debug(f"Stored {stored_count} WM item(s) to declarative memory")
        
        return stored_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        self._update_activations()
        
        return {
            "capacity": self.capacity,
            "items": [item.to_dict() for item in self.items],
            "goals": self.goals,
            "tool_queue": self.tool_queue,
            "focus": self.focus,
            "focus_strength": self.focus_strength,
            "state": self.state,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkingMemory:
        """Create from dictionary representation."""
        wm = cls(
            capacity=data.get("capacity", 7),
            update_interval=data.get("update_interval", 1.0)
        )
        
        wm.items = [WorkingMemoryItem.from_dict(item_data) for item_data in data.get("items", [])]
        wm.goals = data.get("goals", [])
        wm.tool_queue = data.get("tool_queue", [])
        wm.focus = data.get("focus")
        wm.focus_strength = data.get("focus_strength", 0.0)
        wm.state = data.get("state", {})
        wm.last_update = time.time()
        
        return wm
