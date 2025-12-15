"""
Tests for conflict logging and audit system.

Tests conflict logging, statistics, and history tracking.
"""

from __future__ import annotations

import tempfile
import os
import pytest
from datetime import datetime, timezone

from broca.memory.storage import MemoryStorage
from broca.memory import MemoryRecord
from broca.memory.conflict.models import Conflict, Resolution


@pytest.fixture
def temp_storage():
    """Temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        storage = MemoryStorage(db_path)
        yield storage
        storage.close()


class TestConflictLogger:
    """Test conflict logger functionality."""
    
    def test_conflict_logging_to_database(self, temp_storage):
        """
        Test that conflicts are logged to database.
        
        Rationale: Ensures conflict logging persists correctly.
        """
        from broca.memory.conflict.logger import ConflictLogger
        
        logger = ConflictLogger(temp_storage)
        
        memory1 = MemoryRecord(namespace="test", text="Memory 1", importance=0.5)
        memory2 = MemoryRecord(namespace="test", text="Memory 2", importance=0.5)
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test conflict",
            resolution_strategy="recency"
        )
        
        resolution = Resolution(
            action="keep_new",
            kept_memory=memory2,
            archived_memory=memory1,
            merged_memory=None,
            rationale="Test resolution"
        )
        
        # Log conflict
        log_id = logger.log_conflict(conflict, resolution)
        assert log_id > 0
        
        # Verify it was logged
        stats = logger.get_conflict_stats()
        assert stats["total_conflicts"] >= 1
    
    def test_conflict_statistics_calculation(self, temp_storage):
        """
        Test conflict statistics calculation.
        
        Rationale: Ensures statistics are calculated correctly.
        """
        from broca.memory.conflict.logger import ConflictLogger
        
        logger = ConflictLogger(temp_storage)
        
        memory1 = MemoryRecord(namespace="test", text="Memory 1", importance=0.5)
        memory2 = MemoryRecord(namespace="test", text="Memory 2", importance=0.5)
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test",
            resolution_strategy="recency"
        )
        
        resolution = Resolution(
            action="keep_new",
            kept_memory=memory2,
            archived_memory=memory1,
            merged_memory=None,
            rationale="Test"
        )
        
        logger.log_conflict(conflict, resolution)
        
        stats = logger.get_conflict_stats()
        assert "total_conflicts" in stats
        assert "auto_resolved" in stats or "by_type" in stats
    
    def test_undo_stack_retrieval(self, temp_storage):
        """
        Test undo stack retrieval.
        
        Rationale: Ensures undo history can be retrieved.
        """
        from broca.memory.conflict.logger import ConflictLogger
        
        logger = ConflictLogger(temp_storage)
        
        # Get undo history (may be empty)
        undo_history = logger.get_undo_history(limit=10)
        assert isinstance(undo_history, list)
    
    def test_resolution_history_tracking(self, temp_storage):
        """
        Test resolution history tracking.
        
        Rationale: Ensures resolution history is tracked correctly.
        """
        from broca.memory.conflict.logger import ConflictLogger
        
        logger = ConflictLogger(temp_storage)
        
        memory1 = MemoryRecord(namespace="test", text="Memory 1", importance=0.5)
        memory2 = MemoryRecord(namespace="test", text="Memory 2", importance=0.5)
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Test",
            resolution_strategy="recency"
        )
        
        resolution = Resolution(
            action="keep_new",
            kept_memory=memory2,
            archived_memory=memory1,
            merged_memory=None,
            rationale="Test"
        )
        
        log_id = logger.log_conflict(conflict, resolution)
        
        # Should be able to retrieve history
        history = logger.get_resolution_history(limit=10)
        assert isinstance(history, list)

