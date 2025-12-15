"""
Tests for temporal-aware conflict resolution strategy.

Tests that resolution considers temporal ordering and context.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from broca.memory import MemoryRecord
from broca.memory.conflict.models import Conflict


class TestTemporalAwareResolutionStrategy:
    """Test temporal-aware resolution strategy."""
    
    def test_resolves_based_on_temporal_ordering(self):
        """
        Test that resolution considers temporal relationships.
        
        Rationale: Ensures temporal ordering influences resolution.
        """
        from broca.memory.conflict.strategies import TemporalAwareResolutionStrategy
        
        older_time = datetime.now(timezone.utc) - timedelta(days=10)
        newer_time = datetime.now(timezone.utc)
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Older memory",
            importance=0.5,
            created_at=older_time,
            valid_from=older_time - timedelta(days=5),
            valid_until=older_time + timedelta(days=5)
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Newer memory",
            importance=0.5,
            created_at=newer_time,
            valid_from=newer_time - timedelta(days=5),
            valid_until=newer_time + timedelta(days=5)
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="temporal_aware",
            temporal_context="same_period"  # Same period - should use temporal ordering
        )
        
        strategy = TemporalAwareResolutionStrategy()
        resolution = strategy.resolve(conflict, {})
        
        # Should keep newer memory based on temporal ordering
        assert resolution.action == "keep_new"
        assert resolution.kept_memory == memory2
        assert "temporal" in resolution.rationale.lower() or "later" in resolution.rationale.lower()
    
    def test_keeps_both_for_different_periods(self):
        """
        Test that memories in different periods can both be kept.
        
        Rationale: Ensures temporal context allows keeping both valid memories.
        """
        from broca.memory.conflict.strategies import TemporalAwareResolutionStrategy
        
        past_time = datetime.now(timezone.utc) - timedelta(days=365)
        present_time = datetime.now(timezone.utc)
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Past preference",
            importance=0.5,
            created_at=past_time,
            valid_from=past_time - timedelta(days=30),
            valid_until=past_time + timedelta(days=30),
            temporal_scope="past"
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Present preference",
            importance=0.5,
            created_at=present_time,
            valid_from=present_time - timedelta(days=30),
            valid_until=present_time + timedelta(days=30),
            temporal_scope="present"
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="update",
            confidence=0.7,
            evidence="Different time periods",
            resolution_strategy="temporal_aware",
            temporal_context="different_periods"
        )
        
        strategy = TemporalAwareResolutionStrategy()
        resolution = strategy.resolve(conflict, {})
        
        # Should keep both since they're in different periods
        assert resolution.action == "keep_both"
        assert "different" in resolution.rationale.lower() or "period" in resolution.rationale.lower()
    
    def test_fallback_to_recency_when_no_temporal_metadata(self):
        """
        Test that strategy falls back to recency when no temporal metadata.
        
        Rationale: Ensures graceful degradation when temporal info unavailable.
        """
        from broca.memory.conflict.strategies import TemporalAwareResolutionStrategy
        
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
            resolution_strategy="temporal_aware"
        )
        
        strategy = TemporalAwareResolutionStrategy()
        resolution = strategy.resolve(conflict, {})
        
        # Should fallback to recency
        assert resolution.action == "keep_new"
        assert resolution.kept_memory == memory2

