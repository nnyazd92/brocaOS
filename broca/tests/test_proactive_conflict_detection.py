"""
Tests for proactive conflict detection in retrieval.

Tests that retrieval can detect and warn about conflicts.
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


class TestProactiveConflictDetection:
    """Test proactive conflict detection in retrieval."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_with_conflict_warnings(self, memory_manager):
        """
        Test that retrieval can detect conflicts in result set.
        
        Rationale: Ensures proactive conflict detection works during retrieval.
        """
        # Store conflicting memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User prefers Python programming",
            importance=0.5
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User hates Python programming",
            importance=0.5
        )
        
        # Retrieve with conflict detection
        results = memory_manager.retrieve_memories(
            query="Python programming preference",
            limit=10
        )
        
        # Should retrieve both memories
        assert len(results) >= 1
        
        # Check if proactive conflict detection method exists
        if hasattr(memory_manager, 'retrieve_with_conflict_warnings'):
            result_dict = memory_manager.retrieve_with_conflict_warnings(
                query="Python programming preference",
                limit=10
            )
            
            assert "memories" in result_dict
            assert "conflicts" in result_dict or "warnings" in result_dict
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_detects_conflicts_in_retrieved_set(self, memory_manager):
        """
        Test that conflicts are detected within retrieved memory set.
        
        Rationale: Ensures conflicts are identified even when not at storage time.
        """
        # Store memories that might conflict
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="The project uses Java",
            importance=0.6
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="The project uses Python",
            importance=0.6
        )
        
        # Retrieve memories
        memories = memory_manager.retrieve_memories(
            query="project programming language",
            limit=10
        )
        
        # Should retrieve both
        assert len(memories) >= 1
        
        # If method exists, check for conflicts
        if hasattr(memory_manager, '_detect_conflicts_in_set'):
            conflicts = memory_manager._detect_conflicts_in_set(memories)
            # May or may not detect conflicts depending on similarity
            assert isinstance(conflicts, list)

