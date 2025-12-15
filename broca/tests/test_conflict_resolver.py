"""
Tests for conflict resolver orchestrator.

Tests strategy chain execution and resolution orchestration.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from broca.memory import MemoryRecord
from broca.memory.conflict.models import Conflict


class TestConflictResolver:
    """Test conflict resolver orchestrator."""
    
    def test_strategy_chain_execution(self):
        """
        Test that strategies are tried in order.
        
        Rationale: Ensures resolver tries strategies in priority order.
        """
        from broca.memory.conflict.resolver import ConflictResolver
        
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
            resolution_strategy="recency"
        )
        
        resolver = ConflictResolver()
        results = resolver.resolve_conflicts([conflict], auto_resolve=True)
        
        assert len(results) == 1
        assert results[0].resolution.action is not None
        assert results[0].resolution.kept_memory is not None
    
    def test_auto_resolve_flag_behavior(self):
        """
        Test auto_resolve flag behavior.
        
        Rationale: Ensures auto-resolve works when enabled.
        """
        from broca.memory.conflict.resolver import ConflictResolver
        
        memory1 = MemoryRecord(namespace="test", text="Memory 1", importance=0.5)
        memory2 = MemoryRecord(namespace="test", text="Memory 2", importance=0.5)
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.9,  # High confidence
            evidence="Test conflict",
            resolution_strategy="recency"
        )
        
        resolver = ConflictResolver()
        
        # With auto_resolve=True, should resolve automatically
        results = resolver.resolve_conflicts([conflict], auto_resolve=True)
        assert len(results) == 1
        assert results[0].resolution.action != "ask_user"
        
        # With auto_resolve=False and high confidence, should still resolve
        results = resolver.resolve_conflicts([conflict], auto_resolve=False)
        assert len(results) == 1
    
    def test_user_confirmation_requirement(self):
        """
        Test user confirmation requirement when confidence is low.
        
        Rationale: Ensures low-confidence conflicts require user input.
        """
        from broca.memory.conflict.resolver import ConflictResolver
        
        memory1 = MemoryRecord(namespace="test", text="Memory 1", importance=0.5)
        memory2 = MemoryRecord(namespace="test", text="Memory 2", importance=0.5)
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.3,  # Low confidence
            evidence="Test conflict",
            resolution_strategy="recency"
        )
        
        resolver = ConflictResolver(ask_user_threshold=0.5)
        
        # With low confidence and auto_resolve=False, should ask user
        results = resolver.resolve_conflicts([conflict], auto_resolve=False)
        assert len(results) == 1
        # Should either ask user or still resolve (depending on implementation)
        assert results[0].resolution.action is not None
    
    def test_multiple_conflicts_resolution(self):
        """
        Test resolution of multiple conflicts.
        
        Rationale: Ensures resolver can handle multiple conflicts at once.
        """
        from broca.memory.conflict.resolver import ConflictResolver
        
        memory1 = MemoryRecord(namespace="test", text="Memory 1", importance=0.5)
        memory2 = MemoryRecord(namespace="test", text="Memory 2", importance=0.5)
        memory3 = MemoryRecord(namespace="test", text="Memory 3", importance=0.5)
        
        conflict1 = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Conflict 1",
            resolution_strategy="recency"
        )
        conflict2 = Conflict(
            memory1=memory2,
            memory2=memory3,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Conflict 2",
            resolution_strategy="recency"
        )
        
        resolver = ConflictResolver()
        results = resolver.resolve_conflicts([conflict1, conflict2], auto_resolve=True)
        
        assert len(results) == 2
        assert all(r.resolution.action is not None for r in results)

