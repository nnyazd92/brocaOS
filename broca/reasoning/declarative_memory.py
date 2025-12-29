"""
Declarative memory interface for reasoning system.

Provides interface layer between reasoning system and MemoryManager
for declarative memory access, retrieval, and storage.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..memory.manager import MemoryManager
from ..memory import MemoryRecord, SourceType, SourceMetadata

logger = logging.getLogger(__name__)


class DeclarativeMemoryInterface:
    """
    Interface for reasoning system to access declarative memory.
    
    Wraps MemoryManager to provide reasoning-specific memory operations:
    - Semantic search based on working memory content
    - Activation-based retrieval thresholds
    - Storage of reasoning results
    - Namespace organization for reasoning memories
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        reasoning_namespace: str = "reasoning/"
    ):
        """
        Initialize declarative memory interface.
        
        Args:
            memory_manager: MemoryManager instance for memory operations
            reasoning_namespace: Base namespace for reasoning-related memories
        """
        self.memory_manager = memory_manager
        self.reasoning_namespace = reasoning_namespace.rstrip("/")
        
        logger.info(f"Initialized DeclarativeMemoryInterface with namespace: {self.reasoning_namespace}")
    
    def retrieve_relevant(
        self,
        working_memory_items: List[Dict[str, Any]],
        limit: int = 5,
        min_activation: float = 0.7
    ) -> List[MemoryRecord]:
        """
        Retrieve memories relevant to high-activation working memory items.
        
        Args:
            working_memory_items: List of working memory items (dicts with 'content' and 'activation')
            limit: Maximum number of memories to retrieve
            min_activation: Minimum activation threshold for WM items to trigger retrieval
            
        Returns:
            List of MemoryRecord objects relevant to high-activation WM items
        """
        if not working_memory_items:
            return []
        
        # Filter for high-activation items
        high_activation_items = [
            item for item in working_memory_items
            if item.get("activation", 0.0) >= min_activation
        ]
        
        if not high_activation_items:
            logger.debug("No high-activation items to trigger memory retrieval")
            return []
        
        # Build query from high-activation item contents
        # Extract text from WM item content dicts
        query_texts = []
        for item in high_activation_items:
            content = item.get("content", {})
            # Try to extract meaningful text from content
            if isinstance(content, dict):
                # Look for common text fields
                for field in ["text", "content", "description", "value", "message"]:
                    if field in content and isinstance(content[field], str):
                        query_texts.append(content[field])
                        break
                else:
                    # If no text field, stringify the dict (limited)
                    query_texts.append(str(content)[:200])
            elif isinstance(content, str):
                query_texts.append(content)
        
        if not query_texts:
            return []
        
        # Combine queries (take most important/activation-weighted)
        # For now, use the first query text, or combine multiple
        combined_query = " ".join(query_texts[:3])  # Limit to top 3
        
        try:
            # Retrieve from reasoning namespace and general namespace
            memories = self.memory_manager.retrieve_memories(
                query=combined_query,
                namespaces=[self.reasoning_namespace],  # Search in reasoning namespace
                limit=limit,
                recency_weight=0.3,
                min_importance=0.3  # At least somewhat important
            )
            
            logger.debug(f"Retrieved {len(memories)} memories for WM items (activation >= {min_activation})")
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving relevant memories: {e}", exc_info=True)
            return []
    
    def store_reasoning_result(
        self,
        content: str,
        source: str = "reasoning",
        tags: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        importance: float = 0.6
    ) -> Optional[int]:
        """
        Store reasoning outcome to declarative memory.
        
        Args:
            content: Content to store
            source: Source identifier (e.g., "reasoning", "rule_inference", "goal_progress")
            tags: Optional tags for categorization
            namespace: Optional namespace (defaults to reasoning_namespace/{source}/)
            importance: Importance score (0.0-1.0)
            
        Returns:
            Memory ID if stored successfully, None otherwise
        """
        if not content or not content.strip():
            logger.warning("Cannot store empty reasoning result")
            return None
        
        if tags is None:
            tags = []
        
        # Add source tag
        if source and source not in tags:
            tags.append(source)
        tags.append("reasoning")
        
        # Determine namespace
        if namespace is None:
            namespace = f"{self.reasoning_namespace}/{source}"
        
        # Create source metadata
        source_metadata = SourceMetadata(
            source_type=SourceType.UNKNOWN,  # Could be a new type for reasoning
            metadata={"source": source, "stored_at": datetime.now(timezone.utc).isoformat()}
        )
        
        try:
            memory_id, was_duplicate, _ = self.memory_manager.store_memory(
                namespace=namespace,
                text=content,
                importance=importance,
                tags=tags,
                deduplicate=True,
                conflict_check=False,
                source=source_metadata
            )
            
            logger.debug(f"Stored reasoning result to memory {memory_id} (duplicate: {was_duplicate})")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing reasoning result: {e}", exc_info=True)
            return None
    
    def strengthen_memory(self, memory_id: int, boost: float = 0.1) -> bool:
        """
        Increase retrieval strength for frequently accessed memories.
        
        This increases the importance score of a memory to make it more
        likely to be retrieved in future searches.
        
        Args:
            memory_id: ID of memory to strengthen
            boost: Amount to boost importance (0.0-1.0, clamped to keep in range)
            
        Returns:
            True if memory was strengthened, False otherwise
        """
        try:
            memory = self.memory_manager.storage.get_memory(memory_id)
            if not memory:
                logger.warning(f"Memory {memory_id} not found for strengthening")
                return False
            
            # Boost importance, clamped to [0.0, 1.0]
            new_importance = min(1.0, memory.importance + boost)
            
            if new_importance == memory.importance:
                return False  # Already at max
            
            # Update memory importance
            success = self.memory_manager.storage.update_memory(
                memory_id,
                importance=new_importance,
                tags=memory.tags  # Keep existing tags
            )
            
            if success:
                logger.debug(f"Strengthened memory {memory_id}: {memory.importance:.2f} -> {new_importance:.2f}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error strengthening memory {memory_id}: {e}", exc_info=True)
            return False
    
    def get_context_for_goal(self, goal_name: str, limit: int = 5) -> List[MemoryRecord]:
        """
        Retrieve memories related to a specific goal.
        
        Args:
            goal_name: Name of the goal
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of MemoryRecord objects related to the goal
        """
        try:
            # Search in goal-related namespace and with goal tag
            memories = self.memory_manager.retrieve_memories(
                query=f"goal {goal_name}",
                namespaces=[f"{self.reasoning_namespace}/goals"],
                tags=[goal_name, "goal"],
                limit=limit,
                tag_mode="any"  # OR logic for tags
            )
            
            logger.debug(f"Retrieved {len(memories)} memories for goal: {goal_name}")
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving context for goal {goal_name}: {e}", exc_info=True)
            return []
    
    def store_goal_progress(
        self,
        goal_name: str,
        progress: float,
        description: Optional[str] = None
    ) -> Optional[int]:
        """
        Store goal progress update to declarative memory.
        
        Args:
            goal_name: Name of the goal
            progress: Progress value (0.0-1.0)
            description: Optional description of progress
            
        Returns:
            Memory ID if stored successfully, None otherwise
        """
        content = f"Goal '{goal_name}' progress: {progress:.2%}"
        if description:
            content += f" - {description}"
        
        return self.store_reasoning_result(
            content=content,
            source="goal_progress",
            tags=[goal_name, "goal", "progress"],
            namespace=f"{self.reasoning_namespace}/goals/{goal_name}",
            importance=0.7
        )
    
    def store_rule_execution(
        self,
        rule_name: str,
        results: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> Optional[int]:
        """
        Store rule execution result to declarative memory.
        
        Args:
            rule_name: Name of the rule that executed
            results: List of action results from rule execution
            context: Optional context about the execution
            
        Returns:
            Memory ID if stored successfully, None otherwise
        """
        content = f"Rule '{rule_name}' executed with {len(results)} action(s)"
        if context:
            content += f" - {context}"
        
        return self.store_reasoning_result(
            content=content,
            source="rule_execution",
            tags=[rule_name, "rule", "execution"],
            namespace=f"{self.reasoning_namespace}/rules",
            importance=0.5
        )
    
    def store_inference(
        self,
        inference: str,
        context: Optional[str] = None,
        importance: float = 0.7
    ) -> Optional[int]:
        """
        Store inference result to declarative memory.
        
        Args:
            inference: The inference made
            context: Optional context about how inference was made
            importance: Importance score (0.0-1.0)
            
        Returns:
            Memory ID if stored successfully, None otherwise
        """
        content = inference
        if context:
            content = f"{inference} (context: {context})"
        
        return self.store_reasoning_result(
            content=content,
            source="inference",
            tags=["inference", "reasoning"],
            namespace=f"{self.reasoning_namespace}/inferences",
            importance=importance
        )

