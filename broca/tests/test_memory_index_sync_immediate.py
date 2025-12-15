"""
Tests for immediate FAISS index synchronization.

Tests that the index is saved immediately after memory operations (store/update/delete)
rather than only on exit.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock, patch
import pytest
from pathlib import Path

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
def temp_memory_system_with_index_path(mock_embedding_service):
    """Create temporary memory system with index path for testing persistence."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        index_path = os.path.join(tmpdir, "test.faiss")
        
        storage = MemoryStorage(db_path)
        vector_index = VectorIndex(dimension=1536, index_path=index_path)
        manager = MemoryManager(storage, vector_index, mock_embedding_service)
        
        yield manager, storage, vector_index, index_path
        
        manager.close()


class TestImmediateIndexSyncAfterStore:
    """Test that index is saved immediately after store_memory()."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_saved_immediately_after_store(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that save_index() is called immediately after store_memory().
        
        Rationale: Ensures index persists even if process crashes before close().
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Verify index file doesn't exist yet (or is empty)
        index_file = Path(index_path)
        mapping_file = index_file.with_suffix('.json')
        
        # Store a memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Test memory",
            importance=0.7
        )
        
        # Verify index file was created/saved immediately
        assert index_file.exists(), "Index file should exist after store_memory()"
        assert mapping_file.exists(), "Mapping file should exist after store_memory()"
        
        # Verify we can reload the index and find the memory
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 1
        assert memory_id in new_index.get_memory_ids()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_persists_after_multiple_stores(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that index persists correctly after multiple store operations.
        
        Rationale: Ensures each store operation saves the index incrementally.
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Store multiple memories
        memory_ids = []
        for i in range(3):
            mem_id, _, _ = manager.store_memory(
                namespace=f"test.ns{i}",
                text=f"Memory {i}",
                importance=0.5 + i * 0.1
            )
            memory_ids.append(mem_id)
        
        # Verify index file exists and contains all memories
        index_file = Path(index_path)
        assert index_file.exists()
        
        # Reload index and verify all memories are present
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 3
        indexed_ids = set(new_index.get_memory_ids())
        assert set(memory_ids) == indexed_ids
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_saved_after_duplicate_update(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that index is saved even when store_memory() updates a duplicate.
        
        Rationale: Ensures index is saved for all store operations, including updates.
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Store initial memory
        memory_id1, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Duplicate memory",
            importance=0.7
        )
        
        # Store duplicate (should update existing)
        memory_id2, was_duplicate, _ = manager.store_memory(
            namespace="test.ns1",
            text="Duplicate memory",
            importance=0.8,
            deduplicate=True
        )
        
        assert was_duplicate is True
        assert memory_id1 == memory_id2
        
        # Verify index was saved after duplicate update
        index_file = Path(index_path)
        assert index_file.exists()
        
        # Reload and verify memory is still indexed
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 1
        assert memory_id1 in new_index.get_memory_ids()


class TestImmediateIndexSyncAfterDelete:
    """Test that index is saved immediately after delete_memory()."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_saved_immediately_after_delete(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that save_index() is called immediately after delete_memory().
        
        Rationale: Ensures deleted memories are removed from persisted index.
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Store memories
        memory_id1, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        memory_id2, _, _ = manager.store_memory(
            namespace="test.ns2",
            text="Memory 2",
            importance=0.8
        )
        
        # Verify both are in index
        assert vector_index.get_count() == 2
        
        # Delete one memory
        success = manager.delete_memory(memory_id1)
        assert success is True
        
        # Verify index was saved immediately
        index_file = Path(index_path)
        assert index_file.exists()
        
        # Reload index and verify deleted memory is gone
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 1
        assert memory_id1 not in new_index.get_memory_ids()
        assert memory_id2 in new_index.get_memory_ids()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_persists_after_multiple_deletes(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that index persists correctly after multiple delete operations.
        
        Rationale: Ensures each delete operation saves the index.
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Store multiple memories
        memory_ids = []
        for i in range(5):
            mem_id, _, _ = manager.store_memory(
                namespace=f"test.ns{i}",
                text=f"Memory {i}",
                importance=0.5
            )
            memory_ids.append(mem_id)
        
        # Delete some memories
        deleted_ids = memory_ids[:2]
        remaining_ids = memory_ids[2:]
        
        for mem_id in deleted_ids:
            manager.delete_memory(mem_id)
        
        # Reload index and verify correct state
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 3
        indexed_ids = set(new_index.get_memory_ids())
        assert set(remaining_ids) == indexed_ids
        assert not any(mid in indexed_ids for mid in deleted_ids)


class TestImmediateIndexSyncAfterUpdate:
    """Test that index is saved immediately after update_memory()."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_saved_after_text_update(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that save_index() is called after update_memory() when text changes.
        
        Rationale: Text changes require embedding regeneration and index update.
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Original text",
            importance=0.7
        )
        
        # Update text (requires embedding regeneration)
        success = manager.update_memory(
            memory_id=memory_id,
            text="Updated text"
        )
        assert success is True
        
        # Verify index was saved
        index_file = Path(index_path)
        assert index_file.exists()
        
        # Reload index and verify updated memory is searchable with new text
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 1
        assert memory_id in new_index.get_memory_ids()
        
        # Verify updated text is in storage
        updated_memory = storage.get_memory(memory_id)
        assert updated_memory is not None
        assert updated_memory.text == "Updated text"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_not_saved_after_metadata_only_update(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that index save behavior for metadata-only updates.
        
        Rationale: Metadata-only updates don't require index changes, but should still work.
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Test memory",
            importance=0.7,
            tags=["tag1"]
        )
        
        # Update only metadata (importance and tags)
        success = manager.update_memory(
            memory_id=memory_id,
            importance=0.9,
            tags=["tag1", "tag2"]
        )
        assert success is True
        
        # Index should still exist and be valid
        index_file = Path(index_path)
        assert index_file.exists()
        
        # Verify memory is still indexed (metadata update doesn't remove it)
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 1
        assert memory_id in new_index.get_memory_ids()
        
        # Verify metadata was updated in storage
        updated_memory = storage.get_memory(memory_id)
        assert updated_memory.importance == 0.9
        assert set(updated_memory.tags) == {"tag1", "tag2"}


class TestIndexReloadAfterOperations:
    """Test that index can be reloaded correctly after various operations."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_reload_after_store_and_delete(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that index reloads correctly after store and delete operations.
        
        Rationale: Ensures index state is correctly persisted across operations.
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Store memories
        mem_id1, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="test.ns2",
            text="Memory 2",
            importance=0.8
        )
        
        # Delete one
        manager.delete_memory(mem_id1)
        
        # Create new manager with same index path (simulates restart)
        new_storage = MemoryStorage(storage.db_path)
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        new_manager = MemoryManager(new_storage, new_index, manager.embedding_service)
        
        # Verify correct state after reload
        assert new_index.get_count() == 1
        assert mem_id1 not in new_index.get_memory_ids()
        assert mem_id2 in new_index.get_memory_ids()
        
        # Verify memory is searchable
        results = new_manager.retrieve_memories(query="Memory 2", limit=5)
        assert len(results) == 1
        assert results[0].id == mem_id2
        
        new_manager.close()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_index_reload_after_text_update(
        self, temp_memory_system_with_index_path
    ):
        """
        Test that index reloads correctly after text update.
        
        Rationale: Ensures updated embeddings are correctly persisted.
        """
        manager, storage, vector_index, index_path = temp_memory_system_with_index_path
        
        # Store and update memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Original",
            importance=0.7
        )
        
        manager.update_memory(
            memory_id=memory_id,
            text="Updated"
        )
        
        # Reload index
        new_storage = MemoryStorage(storage.db_path)
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        new_manager = MemoryManager(new_storage, new_index, manager.embedding_service)
        
        # Verify memory is searchable with updated text
        results = new_manager.retrieve_memories(query="Updated", limit=5)
        assert len(results) == 1
        assert results[0].id == memory_id
        assert results[0].text == "Updated"
        
        new_manager.close()

