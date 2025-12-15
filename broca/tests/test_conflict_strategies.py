"""
Tests for conflict resolution strategies.

Tests all resolution strategy implementations.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from broca.memory import MemoryRecord
from broca.memory.conflict.models import Conflict


class TestRecencyResolutionStrategy:
    """Test recency-based resolution strategy."""
    
    def test_keeps_newer_memory(self):
        """
        Test that newer memory is kept when timestamps differ.
        
        Rationale: Ensures recency strategy prioritizes recent information.
        """
        from broca.memory.conflict.strategies import RecencyResolutionStrategy
        
        older_time = datetime.now(timezone.utc) - timedelta(days=5)
        newer_time = datetime.now(timezone.utc)
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Older memory",
            importance=0.5,
            created_at=older_time
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Newer memory",
            importance=0.5,
            created_at=newer_time
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="recency"
        )
        
        strategy = RecencyResolutionStrategy()
        resolution = strategy.resolve(conflict, {})
        
        assert resolution.action == "keep_new"
        assert resolution.kept_memory == memory2
        assert resolution.archived_memory == memory1
        assert "newer" in resolution.rationale.lower()
    
    def test_handles_equal_timestamps(self):
        """
        Test fallback behavior when timestamps are equal.
        
        Rationale: Ensures strategy has fallback for edge cases.
        """
        from broca.memory.conflict.strategies import RecencyResolutionStrategy
        
        same_time = datetime.now(timezone.utc)
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Memory 1",
            importance=0.7,  # Higher importance
            created_at=same_time
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Memory 2",
            importance=0.5,
            created_at=same_time
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="recency"
        )
        
        strategy = RecencyResolutionStrategy()
        resolution = strategy.resolve(conflict, {})
        
        # Should fallback to importance when timestamps are equal
        assert resolution.action in ["keep_new", "keep_important"]
        assert resolution.kept_memory is not None


class TestImportanceResolutionStrategy:
    """Test importance-based resolution strategy."""
    
    def test_keeps_higher_importance(self):
        """
        Test that higher importance memory is kept.
        
        Rationale: Ensures importance strategy prioritizes important information.
        """
        from broca.memory.conflict.strategies import ImportanceResolutionStrategy
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Lower importance",
            importance=0.3
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Higher importance",
            importance=0.8
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="importance"
        )
        
        strategy = ImportanceResolutionStrategy()
        resolution = strategy.resolve(conflict, {})
        
        assert resolution.action == "keep_important"
        assert resolution.kept_memory == memory2
        assert resolution.archived_memory == memory1
        assert "importance" in resolution.rationale.lower()
    
    def test_handles_equal_importance(self):
        """
        Test fallback behavior when importance is equal.
        
        Rationale: Ensures strategy has fallback for edge cases.
        """
        from broca.memory.conflict.strategies import ImportanceResolutionStrategy
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Memory 1",
            importance=0.5,
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Memory 2",
            importance=0.5,
            created_at=datetime.now(timezone.utc)
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="importance"
        )
        
        strategy = ImportanceResolutionStrategy()
        resolution = strategy.resolve(conflict, {})
        
        # Should fallback to recency when importance is equal
        assert resolution.action in ["keep_important", "keep_new"]
        assert resolution.kept_memory is not None


class TestNamespacePriorityStrategy:
    """Test namespace priority-based resolution strategy."""
    
    def test_namespace_priority_hierarchy(self):
        """
        Test namespace priority hierarchy (user.preferences > system.architecture).
        
        Rationale: Ensures namespace priority system works correctly.
        """
        from broca.memory.conflict.strategies import NamespacePriorityStrategy
        
        memory1 = MemoryRecord(
            namespace="system.architecture",
            text="System memory",
            importance=0.8
        )
        memory2 = MemoryRecord(
            namespace="user.preferences",
            text="User preference",
            importance=0.5
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="namespace_priority"
        )
        
        strategy = NamespacePriorityStrategy()
        resolution = strategy.resolve(conflict, {})
        
        # user.preferences should have higher priority than system.architecture
        assert resolution.action == "keep_important"  # or similar action
        assert resolution.kept_memory == memory2
        assert "namespace" in resolution.rationale.lower() or "priority" in resolution.rationale.lower()
    
    def test_default_priority_unknown_namespace(self):
        """
        Test default priority for unknown namespaces.
        
        Rationale: Ensures unknown namespaces get reasonable default priority.
        """
        from broca.memory.conflict.strategies import NamespacePriorityStrategy
        
        memory1 = MemoryRecord(
            namespace="unknown.namespace.1",
            text="Unknown 1",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="unknown.namespace.2",
            text="Unknown 2",
            importance=0.5
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="namespace_priority"
        )
        
        strategy = NamespacePriorityStrategy()
        resolution = strategy.resolve(conflict, {})
        
        # Should still resolve (fallback to other criteria)
        assert resolution.action is not None
        assert resolution.kept_memory is not None


class TestConsensusResolutionStrategy:
    """Test consensus-based resolution strategy."""
    
    def test_finds_similar_memories(self):
        """
        Test that similar memories are found and grouped.
        
        Rationale: Ensures consensus strategy can find related memories.
        """
        from broca.memory.conflict.strategies import ConsensusResolutionStrategy
        from unittest.mock import Mock
        
        memory1 = MemoryRecord(
            namespace="test",
            text="User likes Python",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="User prefers Java",
            importance=0.5
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="consensus"
        )
        
        # Mock memory manager for finding similar memories
        mock_manager = Mock()
        mock_manager.retrieve_memories.return_value = [memory1, memory2]
        
        strategy = ConsensusResolutionStrategy(memory_manager=mock_manager)
        resolution = strategy.resolve(conflict, {})
        
        # Should create a consensus resolution
        assert resolution.action == "consensus"
        assert resolution.merged_memory is not None or resolution.kept_memory is not None
    
    def test_selects_largest_group(self):
        """
        Test that largest group is selected as consensus.
        
        Rationale: Ensures consensus strategy uses majority rule.
        """
        from broca.memory.conflict.strategies import ConsensusResolutionStrategy
        from unittest.mock import Mock
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Group A memory 1",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Group A memory 2",
            importance=0.5
        )
        memory3 = MemoryRecord(
            namespace="test",
            text="Group B memory",
            importance=0.5
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory3,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="consensus"
        )
        
        # Mock to return Group A as larger
        mock_manager = Mock()
        mock_manager.retrieve_memories.return_value = [memory1, memory2, memory3]
        
        strategy = ConsensusResolutionStrategy(memory_manager=mock_manager)
        resolution = strategy.resolve(conflict, {})
        
        assert resolution.action == "consensus"
        assert "consensus" in resolution.rationale.lower() or resolution.merged_memory is not None


class TestSmartMergeStrategy:
    """Test smart merge resolution strategy."""
    
    def test_merges_conflicting_texts(self):
        """
        Test that conflicting texts are merged into coherent memory.
        
        Rationale: Ensures merge strategy creates coherent combined memory.
        """
        from broca.memory.conflict.strategies import SmartMergeStrategy
        
        older_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        memory1 = MemoryRecord(
            namespace="test",
            text="User prefers Python",
            importance=0.5,
            tags=["python", "programming"],
            created_at=older_time
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="User also likes Java",
            importance=0.7,
            tags=["java", "programming"],
            created_at=datetime.now(timezone.utc)
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="merge"
        )
        
        strategy = SmartMergeStrategy()
        resolution = strategy.resolve(conflict, {})
        
        assert resolution.action == "merge"
        assert resolution.merged_memory is not None
        assert resolution.merged_memory.namespace == "test"
        assert "python" in resolution.merged_memory.text.lower() or "java" in resolution.merged_memory.text.lower()
    
    def test_combines_tags_and_importance(self):
        """
        Test that tags are combined and max importance is used.
        
        Rationale: Ensures merge strategy properly combines metadata.
        """
        from broca.memory.conflict.strategies import SmartMergeStrategy
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Memory 1",
            importance=0.5,
            tags=["tag1", "tag2"]
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Memory 2",
            importance=0.8,
            tags=["tag2", "tag3"]
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="merge"
        )
        
        strategy = SmartMergeStrategy()
        resolution = strategy.resolve(conflict, {})
        
        assert resolution.merged_memory is not None
        # Should use max importance
        assert resolution.merged_memory.importance == 0.8
        # Should combine tags (unique union)
        merged_tags = set(resolution.merged_memory.tags)
        assert "tag1" in merged_tags
        assert "tag2" in merged_tags
        assert "tag3" in merged_tags
        assert len(merged_tags) == 3

