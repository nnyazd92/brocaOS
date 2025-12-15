"""
Conflict resolution strategies.

Implements various strategies for resolving conflicts between memories.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .. import MemoryRecord
from .models import Conflict, Resolution

logger = logging.getLogger(__name__)


class ResolutionStrategy(ABC):
    """Base class for conflict resolution strategies."""
    
    @abstractmethod
    def resolve(
        self,
        conflict: Conflict,
        context: Dict[str, Any]
    ) -> Resolution:
        """
        Apply resolution strategy to conflict.
        
        Args:
            conflict: Conflict to resolve
            context: Additional context for resolution
            
        Returns:
            Resolution object with action taken
        """
        pass


class RecencyResolutionStrategy(ResolutionStrategy):
    """Keep the most recent memory."""
    
    def resolve(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )


class ImportanceResolutionStrategy(ResolutionStrategy):
    """Keep the memory with higher importance."""
    
    def resolve(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )


class NamespacePriorityStrategy(ResolutionStrategy):
    """Resolve based on namespace hierarchy priority."""
    
    NAMESPACE_PRIORITY = {
        "user.preferences": 100,
        "user.personal_info": 90,
        "user.health": 85,
        "system.critical": 80,
        "user.interests": 70,
        "system.architecture": 60,
        "test": 10,
    }
    
    def get_namespace_priority(self, namespace: str) -> int:
        """Get priority score for namespace."""
        for ns_prefix, priority in self.NAMESPACE_PRIORITY.items():
            if namespace.startswith(ns_prefix):
                return priority
        return 50  # Default priority
    
    def resolve(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )


class ConsensusResolutionStrategy(ResolutionStrategy):
    """Use multiple similar memories to determine consensus."""
    
    def __init__(self, memory_manager: Optional[Any] = None) -> None:
        """
        Initialize consensus strategy.
        
        Args:
            memory_manager: Optional MemoryManager for finding similar memories
        """
        self.memory_manager = memory_manager
    
    def resolve(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def _cluster_by_content(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def _texts_similar(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def _create_consensus_memory(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )


class SmartMergeStrategy(ResolutionStrategy):
    """Merge conflicting memories into a coherent whole."""
    
    def resolve(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def _merge_texts(self, text1: str, text2: str) -> str:
        """Merge two texts into coherent memory."""
        # Simple merge: combine with separator
        # In a more sophisticated implementation, could use LLM to merge coherently
        return f"{text1} | {text2}"


class TemporalAwareResolutionStrategy(ResolutionStrategy):
    """Resolve conflicts considering temporal ordering and context."""
    
    def resolve(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)

