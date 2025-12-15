"""
Tests for MemoryManager orchestration.

Tests the integration of storage, vector index, and embeddings.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock, patch
import pytest

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
    # Return mock embeddings
    service.generate_embedding.return_value = [0.1] * 1536
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


class TestMemoryManagerStoreMemory:
    """Test storing memories through MemoryManager."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_success(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test storing a memory successfully.
        
        Rationale: Ensures MemoryManager orchestrates storage, embedding, and indexing.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        memory_id, was_duplicate, _ = manager.store_memory(
            namespace="test.namespace",
            tags=["tag1"],
            text="Test memory",
            importance=0.7
        )
        
        assert memory_id > 0
        assert was_duplicate is False
        # Verify stored in database
        stored = temp_storage.get_memory(memory_id)
        assert stored is not None
        assert stored.text == "Test memory"
        # Verify embedding was generated (may be called multiple times due to auto-detection)
        assert mock_embedding_service.generate_embedding.call_count >= 1
        # Verify it was called with "Test memory" at least once
        assert any("Test memory" in str(call) for call in mock_embedding_service.generate_embedding.call_args_list)
        # Verify added to index
        assert temp_vector_index.get_count() == 1
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_generates_embedding(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test that embedding is generated when storing memory.
        
        Rationale: Ensures embeddings are created for vector search.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        memory_id, was_duplicate, _ = manager.store_memory(
            namespace="test",
            text="Memory text",
            importance=0.5
        )
        
        assert was_duplicate is False
        # Verify embedding was generated (may be called multiple times due to auto-detection)
        assert mock_embedding_service.generate_embedding.call_count >= 1
        assert any("Memory text" in str(call) for call in mock_embedding_service.generate_embedding.call_args_list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_handles_errors(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test that errors during storage are propagated.
        
        Rationale: Ensures error handling works correctly.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Make embedding service raise an exception
        mock_embedding_service.generate_embedding.side_effect = RuntimeError("Embedding failed")
        
        with pytest.raises(RuntimeError, match="Embedding failed"):
            manager.store_memory(
                namespace="test",
                text="Error test",
                importance=0.5
            )


class TestMemoryManagerRetrieveMemories:
    """Test retrieving memories through MemoryManager."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_memories_vector_search(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test retrieving memories using vector similarity search.
        
        Rationale: Ensures vector search works correctly.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Store a memory
        memory_id, _, _ = manager.store_memory(
            namespace="test",
            text="Python programming language",
            importance=0.8
        )
        
        # Reset mock to track new calls
        mock_embedding_service.generate_embedding.reset_mock()
        
        # Retrieve memories
        results = manager.retrieve_memories("programming")
        
        assert len(results) == 1
        assert results[0].id == memory_id
        # Verify query embedding was generated
        mock_embedding_service.generate_embedding.assert_called_once_with("programming")
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_memories_with_namespace_filter(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test retrieving memories with namespace filter.
        
        Rationale: Ensures namespace filtering works correctly.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Store memories in different namespaces
        memory_id1, _, _ = manager.store_memory(
            namespace="lang.python",
            text="Python is great",
            importance=0.7
        )
        memory_id2, _, _ = manager.store_memory(
            namespace="lang.java",
            text="Java is also great",
            importance=0.7
        )
        
        # Reset mock
        mock_embedding_service.generate_embedding.reset_mock()
        
        # Retrieve with namespace filter
        results = manager.retrieve_memories("great", namespace="lang.python")
        
        assert len(results) == 1
        assert results[0].id == memory_id1
        assert results[0].namespace == "lang.python"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_memories_with_tags_filter(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test retrieving memories with tags filter.
        
        Rationale: Ensures tag filtering works correctly.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Store memories with different tags
        memory_id1, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with python tag",
            importance=0.7,
            tags=["python", "programming"]
        )
        memory_id2, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with java tag",
            importance=0.7,
            tags=["java", "programming"]
        )
        
        # Reset mock
        mock_embedding_service.generate_embedding.reset_mock()
        
        # Retrieve with tag filter
        results = manager.retrieve_memories("memory", tags=["python"])
        
        assert len(results) == 1
        assert results[0].id == memory_id1
        assert "python" in results[0].tags
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_memories_updates_last_used(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test that retrieved memories have last_used_at updated.
        
        Rationale: Ensures usage tracking works correctly.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        memory_id, _, _ = manager.store_memory(namespace="test", text="Test", importance=0.5)
        original = temp_storage.get_memory(memory_id)
        assert original is not None
        
        original_last_used = original.last_used_at
        
        # Retrieve the memory
        results = manager.retrieve_memories("Test")
        assert len(results) == 1
        
        # Check that last_used_at was updated
        updated = temp_storage.get_memory(memory_id)
        assert updated is not None
        assert updated.last_used_at > original_last_used
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_retrieve_memories_handles_errors(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test that errors during retrieval are handled gracefully.
        
        Rationale: Ensures retrieval doesn't crash on errors.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Make embedding service raise an exception
        mock_embedding_service.generate_embedding.side_effect = RuntimeError("Embedding failed")
        
        # Should return empty list, not crash
        results = manager.retrieve_memories("test")
        assert results == []


class TestMemoryManagerGetMemory:
    """Test getting individual memories by ID."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_memory_success(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test getting a memory by ID.
        
        Rationale: Ensures individual memory retrieval works.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        memory_id, _, _ = manager.store_memory(namespace="test", text="Test", importance=0.5)
        
        memory = manager.get_memory(memory_id)
        assert memory is not None
        assert memory.id == memory_id
        assert memory.text == "Test"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_memory_not_found(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test getting a non-existent memory returns None.
        
        Rationale: Ensures graceful handling of non-existent IDs.
        """
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        memory = manager.get_memory(999)
        assert memory is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
