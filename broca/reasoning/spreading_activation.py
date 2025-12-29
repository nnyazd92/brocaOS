"""
Spreading activation mechanism for declarative memory retrieval.

Implements activation-based retrieval from working memory to declarative memory,
with damping to prevent activation cascade loops.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from collections import defaultdict

from .declarative_memory import DeclarativeMemoryInterface
from ..memory import MemoryRecord

logger = logging.getLogger(__name__)


class SpreadingActivation:
    """
    Manages spreading activation from working memory to declarative memory.
    
    Monitors working memory activation levels and triggers retrieval when
    activation exceeds threshold. Creates associative links between WM items
    and retrieved memories, with temporal decay and damping.
    """
    
    def __init__(
        self,
        declarative_memory: DeclarativeMemoryInterface,
        activation_threshold: float = 0.7,
        damping_factor: float = 0.5,
        max_activations_per_cycle: int = 3
    ):
        """
        Initialize spreading activation mechanism.
        
        Args:
            declarative_memory: DeclarativeMemoryInterface for memory retrieval
            activation_threshold: Minimum activation to trigger retrieval
            damping_factor: Damping factor to prevent cascade loops (0.0-1.0)
            max_activations_per_cycle: Maximum number of activations per cycle
        """
        self.declarative_memory = declarative_memory
        self.activation_threshold = activation_threshold
        self.damping_factor = damping_factor
        self.max_activations_per_cycle = max_activations_per_cycle
        
        # Track recent activations to prevent loops
        self.recent_activations: Dict[str, float] = {}  # item_key -> last_activation_time
        self.activation_timeout: float = 5.0  # seconds
        
        # Track associations between WM items and retrieved memories
        self.associations: Dict[str, Set[int]] = defaultdict(set)  # item_key -> set of memory_ids
        
        logger.info(f"Initialized SpreadingActivation (threshold={activation_threshold}, damping={damping_factor})")
    
    def _get_item_key(self, item: Dict[str, Any]) -> str:
        """Generate a unique key for a working memory item."""
        content = item.get("content", {})
        if isinstance(content, dict):
            # Try to use a unique identifier from content
            if "id" in content:
                return f"id:{content['id']}"
            elif "name" in content:
                return f"name:{content['name']}"
            elif "type" in content:
                return f"type:{content['type']}:{hash(str(content))}"
        # Fallback to hash of content
        return f"hash:{hash(str(content))}"
    
    def _should_trigger(self, item: Dict[str, Any], activation: float) -> bool:
        """
        Check if activation should trigger retrieval.
        
        Args:
            item: Working memory item
            activation: Current activation level
            
        Returns:
            True if activation should trigger retrieval
        """
        if activation < self.activation_threshold:
            return False
        
        # Check if recently activated (damping)
        item_key = self._get_item_key(item)
        current_time = time.time()
        
        if item_key in self.recent_activations:
            time_since_activation = current_time - self.recent_activations[item_key]
            if time_since_activation < self.activation_timeout:
                # Recently activated, apply damping
                logger.debug(f"Item {item_key} recently activated ({time_since_activation:.2f}s ago), damping")
                return False
        
        return True
    
    def propagate_activation(
        self,
        working_memory_items: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[MemoryRecord]:
        """
        Propagate activation from working memory to declarative memory.
        
        High-activation WM items trigger semantic search in declarative memory.
        Retrieved memories are returned for integration into working memory.
        
        Args:
            working_memory_items: List of WM items with activation levels
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of retrieved MemoryRecord objects
        """
        if not working_memory_items:
            return []
        
        # Filter for items that should trigger activation
        triggering_items = []
        for item in working_memory_items:
            activation = item.get("activation", 0.0)
            if self._should_trigger(item, activation):
                triggering_items.append(item)
        
        if not triggering_items:
            logger.debug("No items triggered spreading activation")
            return []
        
        # Limit number of activations per cycle
        if len(triggering_items) > self.max_activations_per_cycle:
            # Sort by activation (highest first) and take top N
            triggering_items.sort(key=lambda x: x.get("activation", 0.0), reverse=True)
            triggering_items = triggering_items[:self.max_activations_per_cycle]
        
        # Retrieve memories for triggering items
        try:
            retrieved = self.declarative_memory.retrieve_relevant(
                working_memory_items=triggering_items,
                limit=limit,
                min_activation=self.activation_threshold
            )
            
            # Record activations to prevent immediate re-activation
            current_time = time.time()
            for item in triggering_items:
                item_key = self._get_item_key(item)
                self.recent_activations[item_key] = current_time
                
                # Record associations between item and retrieved memories
                for memory in retrieved:
                    self.associations[item_key].add(memory.id)
            
            # Clean up old activation records
            self._cleanup_activations()
            
            logger.debug(f"Spreading activation retrieved {len(retrieved)} memories from {len(triggering_items)} triggering items")
            return retrieved
            
        except Exception as e:
            logger.error(f"Error in spreading activation: {e}", exc_info=True)
            return []
    
    def boost_activation_for_retrieved(
        self,
        item: Dict[str, Any],
        retrieved_memories: List[MemoryRecord],
        boost_amount: float = 0.1
    ) -> float:
        """
        Boost activation of a WM item when related memories are retrieved.
        
        This creates positive feedback: high activation triggers retrieval,
        and retrieved memories boost activation of related items.
        
        Args:
            item: Working memory item
            retrieved_memories: Memories retrieved for this item
            boost_amount: Amount to boost activation
            
        Returns:
            New activation level
        """
        if not retrieved_memories:
            return item.get("activation", 0.0)
        
        current_activation = item.get("activation", 0.0)
        # Boost activation, clamped to reasonable maximum (e.g., 2.0)
        new_activation = min(2.0, current_activation + boost_amount * len(retrieved_memories))
        
        item["activation"] = new_activation
        logger.debug(f"Boosted activation: {current_activation:.2f} -> {new_activation:.2f} (retrieved {len(retrieved_memories)} memories)")
        
        return new_activation
    
    def get_associations(self, item: Dict[str, Any]) -> Set[int]:
        """
        Get memory IDs associated with a working memory item.
        
        Args:
            item: Working memory item
            
        Returns:
            Set of memory IDs associated with this item
        """
        item_key = self._get_item_key(item)
        return self.associations.get(item_key, set())
    
    def strengthen_association(
        self,
        item: Dict[str, Any],
        memory_id: int
    ):
        """
        Strengthen association between WM item and memory.
        
        This can be called when an association is frequently used,
        to track which memories are most relevant to which WM items.
        
        Args:
            item: Working memory item
            memory_id: ID of associated memory
        """
        item_key = self._get_item_key(item)
        self.associations[item_key].add(memory_id)
        
        # Optionally boost memory importance in declarative memory
        self.declarative_memory.strengthen_memory(memory_id, boost=0.05)
    
    def _cleanup_activations(self):
        """Remove old activation records that have expired."""
        current_time = time.time()
        expired_keys = [
            key for key, activation_time in self.recent_activations.items()
            if current_time - activation_time > self.activation_timeout
        ]
        for key in expired_keys:
            del self.recent_activations[key]
    
    def reset(self):
        """Reset activation tracking (useful for testing or new reasoning cycles)."""
        self.recent_activations.clear()
        self.associations.clear()
        logger.debug("Reset spreading activation tracking")

