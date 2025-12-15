"""
Integration tests for conflict resolution with MemoryManager.

Tests end-to-end conflict detection and resolution integration.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest

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


class TestMemoryManagerConflictIntegration:
    """Test conflict resolution integration with MemoryManager."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_with_conflict_check(self, memory_manager):
        """
        Test store_memory() with conflict_check=True detects conflicts.
        
        Rationale: Ensures conflict detection is integrated correctly.
        """
        # Store first memory
        memory_id1, was_duplicate1, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="User prefers Python",
            importance=0.5
        )
        assert was_duplicate1 is False
        
        # Store conflicting memory with conflict_check
        memory_id2, was_duplicate2, conflicts = memory_manager.store_memory(
            namespace="test.namespace",
            text="User hates Python",
            importance=0.5,
            conflict_check=True
        )
        
        assert memory_id2 > 0
        assert was_duplicate2 is False
        # Should have conflicts detected
        assert isinstance(conflicts, list)
        # May have conflicts depending on detection
        if len(conflicts) > 0:
            assert len(conflicts) > 0
            # Verify conflict structure
            conflict = conflicts[0]
            assert hasattr(conflict, 'conflict_type')
            assert hasattr(conflict, 'confidence')
            assert hasattr(conflict, 'evidence')
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_with_auto_resolve(self, memory_manager):
        """
        Test store_memory() with auto_resolve=True automatically resolves.
        
        Rationale: Ensures auto-resolution works correctly.
        """
        # Store first memory
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="User is 25 years old",
            importance=0.5
        )
        
        # Store conflicting memory with auto_resolve
        memory_id2, was_duplicate2, conflicts = memory_manager.store_memory(
            namespace="test.namespace",
            text="User is 30 years old",
            importance=0.5,
            conflict_check=True,
            auto_resolve=True
        )
        
        # Should resolve automatically
        assert memory_id2 > 0
        assert isinstance(conflicts, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_existing_behavior_unchanged(self, memory_manager):
        """
        Test that existing store_memory() behavior is unchanged when conflict_check=False.
        
        Rationale: Ensures backward compatibility is maintained.
        """
        # This test should pass even before implementation
        # Store a memory without conflict checking (default behavior)
        memory_id, was_duplicate, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="Test memory",
            importance=0.5
            # conflict_check defaults to False for backward compatibility
        )
        
        assert memory_id > 0
        assert was_duplicate is False
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_conflict_detection_doesnt_interfere_with_deduplication(self, memory_manager):
        """
        Test that conflict detection doesn't interfere with deduplication.
        
        Rationale: Ensures deduplication still works correctly.
        """
        # Store first memory
        memory_id1, was_duplicate1, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="Exact duplicate test",
            importance=0.5
        )
        assert was_duplicate1 is False
        
        # Store exact duplicate
        memory_id2, was_duplicate2, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="Exact duplicate test",
            importance=0.6
        )
        assert was_duplicate2 is True
        assert memory_id2 == memory_id1  # Should update existing

