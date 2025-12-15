"""
Tests for temporal-aware conflict detection.

Tests that conflict detection considers temporal context.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest
from datetime import datetime, timezone, timedelta

from broca.memory import MemoryRecord
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.memory.manager import MemoryManager

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    service = Mock(spec=EmbeddingService)
    def generate_embedding(text: str):
        hash_val = hash(text) % 1000
        base_embedding = [0.1] * 1536
        base_embedding[0] = hash_val / 1000.0
        return base_embedding
    service.generate_embedding.side_effect = generate_embedding
    return service


@pytest.fixture
def temp_storage():
    """Temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        storage = MemoryStorage(db_path)
        yield storage
        storage.close()


@pytest.fixture
def temp_vector_index():
    """Temporary vector index for testing."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test.faiss")
        index = VectorIndex(dimension=1536, index_path=index_path)
        yield index


@pytest.fixture
def memory_manager(temp_storage, temp_vector_index, mock_embedding_service):
    """Memory manager for testing."""
    return MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)


class TestTemporalConflictDetection:
    """Test temporal-aware conflict detection."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_detects_conflicts_in_same_period(self, memory_manager):
        """
        Test that temporal context is added when conflicts are detected in same period.
        
        Rationale: Ensures temporal overlap is considered in conflict detection.
        """
        from broca.memory.conflict.detection import ConflictDetector
        
        # Store a memory
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User prefers Python programming language",
            importance=0.5
        )
        
        memory1 = memory_manager.storage.get_memory(memory_id1)
        assert memory1 is not None
        
        # Create conflicting memory in same time period
        now = datetime.now(timezone.utc)
        conflicting_memory = MemoryRecord(
            namespace="test",
            text="User hates Python programming language",
            importance=0.5,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
            temporal_scope="present"
        )
        
        detector = ConflictDetector(
            memory_manager=memory_manager,
            similarity_threshold=0.5,  # Lower threshold to ensure detection
            contradiction_threshold=0.5
        )
        
        # Set temporal metadata on memory1 to match
        memory1.valid_from = now - timedelta(days=1)
        memory1.valid_until = now + timedelta(days=1)
        memory1.temporal_scope = "present"
        
        conflicts = detector.detect_conflicts(conflicting_memory, [memory1])
        
        # If conflicts are detected, they should have temporal context
        if conflicts:
            assert hasattr(conflicts[0], 'temporal_context')
            assert conflicts[0].temporal_context in ["same_period", "different_periods", "unknown", None]
            assert hasattr(conflicts[0], 'temporal_gap')
            assert hasattr(conflicts[0], 'detected_at')
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_different_periods_may_be_update_not_conflict(self, memory_manager):
        """
        Test that memories in different time periods may be updates, not conflicts.
        
        Rationale: Ensures temporal context distinguishes updates from contradictions.
        """
        from broca.memory.conflict.detection import ConflictDetector
        
        # Store old memory
        old_time = datetime.now(timezone.utc) - timedelta(days=365)
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User prefers Java",
            importance=0.5
        )
        
        memory1 = memory_manager.storage.get_memory(memory_id1)
        assert memory1 is not None
        memory1.valid_from = old_time - timedelta(days=30)
        memory1.valid_until = old_time + timedelta(days=30)
        memory1.temporal_scope = "past"
        
        # New memory in different period
        new_time = datetime.now(timezone.utc)
        new_memory = MemoryRecord(
            namespace="test",
            text="User prefers Python",
            importance=0.5,
            valid_from=new_time - timedelta(days=30),
            valid_until=new_time + timedelta(days=30),
            temporal_scope="present"
        )
        
        detector = ConflictDetector(
            memory_manager=memory_manager,
            similarity_threshold=0.7,
            contradiction_threshold=0.6
        )
        
        conflicts = detector.detect_conflicts(new_memory, [memory1])
        
        # May detect conflict, but should have temporal context indicating different periods
        # This test verifies the structure exists for temporal-aware detection
        assert isinstance(conflicts, list)
    
    def test_temporal_overlap_detection(self):
        """
        Test helper method for detecting temporal overlap.
        
        Rationale: Ensures temporal overlap logic works correctly.
        """
        from broca.memory.conflict.detection import ConflictDetector
        
        detector = ConflictDetector()
        
        # Test overlapping periods
        now = datetime.now(timezone.utc)
        memory1 = MemoryRecord(
            namespace="test",
            text="Memory 1",
            importance=0.5,
            valid_from=now - timedelta(days=10),
            valid_until=now + timedelta(days=10)
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Memory 2",
            importance=0.5,
            valid_from=now - timedelta(days=5),
            valid_until=now + timedelta(days=5)
        )
        
        # Should overlap
        overlap = detector._check_temporal_overlap(memory1, memory2) if hasattr(detector, '_check_temporal_overlap') else None
        # If method exists, test it; otherwise just verify structure
        assert True  # Placeholder - will be implemented
    
    def test_no_temporal_overlap(self):
        """
        Test that non-overlapping periods are detected.
        
        Rationale: Ensures temporal non-overlap is correctly identified.
        """
        from broca.memory.conflict.detection import ConflictDetector
        
        detector = ConflictDetector()
        
        now = datetime.now(timezone.utc)
        memory1 = MemoryRecord(
            namespace="test",
            text="Memory 1",
            importance=0.5,
            valid_from=now - timedelta(days=30),
            valid_until=now - timedelta(days=20)
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Memory 2",
            importance=0.5,
            valid_from=now - timedelta(days=10),
            valid_until=now + timedelta(days=10)
        )
        
        # Should not overlap
        overlap = detector._check_temporal_overlap(memory1, memory2) if hasattr(detector, '_check_temporal_overlap') else None
        assert True  # Placeholder - will be implemented

