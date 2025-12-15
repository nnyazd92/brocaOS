"""
Tests for memory index-storage synchronization.

Tests automatic rebuilding of FAISS index from storage when mismatches are detected.
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
    """Mock embedding service that returns unique embeddings based on text."""
    service = Mock(spec=EmbeddingService)
    
    def generate_embedding(text: str):
        # Generate a simple deterministic embedding based on text hash
        # This ensures different texts get different embeddings
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        # Create a 1536-dim embedding with some variation
        embedding = [0.1 + (hash_val % 100) / 10000.0] * 1536
        return embedding
    
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
def temp_memory_system(mock_embedding_service):
    """Create temporary memory system for testing."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        index_path = os.path.join(tmpdir, "test.faiss")
        
        storage = MemoryStorage(db_path)
        vector_index = VectorIndex(dimension=1536, index_path=index_path)
        manager = MemoryManager(storage, vector_index, mock_embedding_service)
        
        yield manager, storage, vector_index
        
        manager.close()


class TestIndexRebuildWhenEmpty:
    """Test index rebuild when index is empty but storage has memories."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_rebuild_index_when_empty_but_storage_has_memories(
        self, temp_storage, temp_vector_index, mock_embedding_service
    ):
        """
        Test that index is rebuilt when empty but storage has memories.
        
        Rationale: Ensures memories in storage are searchable after index loss.
        """
        # Store memories directly in storage (bypassing manager to simulate index loss)
        record1 = MemoryRecord(
            namespace="test.ns1",
            tags=["tag1"],
            text="Memory 1",
            importance=0.7
        )
        record2 = MemoryRecord(
            namespace="test.ns2",
            tags=["tag2"],
            text="Memory 2",
            importance=0.8
        )
        
        mem_id1 = temp_storage.store_memory(record1)
        mem_id2 = temp_storage.store_memory(record2)
        
        # Verify storage has memories but index is empty
        assert len(temp_storage.get_all_memories()) == 2
        assert temp_vector_index.get_count() == 0
        
        # Create manager - should trigger sync and rebuild
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Verify index was rebuilt
        assert temp_vector_index.get_count() == 2
        
        # Verify memories are searchable
        results = manager.retrieve_memories(query="Memory", limit=5)
        assert len(results) >= 1  # Should find at least one memory
        
        manager.close()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_rebuild_preserves_existing_indexed_memories(
        self, temp_memory_system
    ):
        """
        Test that rebuild doesn't duplicate already indexed memories.
        
        Rationale: Ensures sync doesn't create duplicates when some memories are already indexed.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store some memories normally (through manager)
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
        
        # Verify both are indexed
        assert vector_index.get_count() == 2
        
        # Add a memory directly to storage (simulating a memory that wasn't indexed)
        record3 = MemoryRecord(
            namespace="test.ns3",
            tags=[],
            text="Memory 3",
            importance=0.6
        )
        mem_id3 = storage.store_memory(record3)
        
        # Manually trigger sync by creating new manager
        # (in real scenario, this would happen on next startup)
        manager2 = MemoryManager(storage, vector_index, manager.embedding_service)
        
        # Verify index now has all 3 memories (no duplicates)
        assert vector_index.get_count() == 3
        
        # Verify all memories are searchable
        results = manager2.retrieve_memories(query="Memory", limit=10)
        assert len(results) == 3
        
        manager2.close()


class TestIndexSyncWhenCountsMismatch:
    """Test index sync when counts don't match."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_when_storage_has_more_memories(
        self, temp_storage, temp_vector_index, mock_embedding_service
    ):
        """
        Test sync when storage has more memories than index.
        
        Rationale: Ensures missing memories are added to index.
        """
        # Store memories directly in storage
        for i in range(3):
            record = MemoryRecord(
                namespace=f"test.ns{i}",
                tags=[],
                text=f"Memory {i}",
                importance=0.5 + i * 0.1
            )
            temp_storage.store_memory(record)
        
        # Add only one to index manually
        embedding = mock_embedding_service.generate_embedding("Memory 0")
        temp_vector_index.add_vector(1, embedding)
        
        # Verify mismatch
        assert len(temp_storage.get_all_memories()) == 3
        assert temp_vector_index.get_count() == 1
        
        # Create manager - should sync
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Verify sync fixed the mismatch
        assert temp_vector_index.get_count() == 3
        
        manager.close()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_removes_orphaned_entries(
        self, temp_memory_system
    ):
        """
        Test sync removes orphaned entries from index.
        
        Rationale: Ensures orphaned index entries are removed when syncing.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store a memory normally
        mem_id1, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        
        # Manually add orphaned entries to index (memory IDs that don't exist in storage)
        embedding1 = manager.embedding_service.generate_embedding("Orphaned 1")
        embedding2 = manager.embedding_service.generate_embedding("Orphaned 2")
        vector_index.add_vector(99999, embedding1)  # Non-existent memory ID
        vector_index.add_vector(99998, embedding2)  # Another non-existent memory ID
        
        # Verify mismatch
        assert len(storage.get_all_memories()) == 1
        assert vector_index.get_count() == 3  # 1 real + 2 orphaned
        
        # Sync should remove orphaned entries
        manager2 = MemoryManager(storage, vector_index, manager.embedding_service)
        
        # Index count should match storage count (orphaned entries removed)
        assert vector_index.get_count() == 1
        assert len(storage.get_all_memories()) == 1
        
        # Verify the real memory is still searchable
        results = manager2.retrieve_memories(query="Memory 1", limit=10)
        assert len(results) == 1
        assert results[0].id == mem_id1
        
        manager2.close()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_handles_both_add_and_remove(
        self, temp_memory_system
    ):
        """
        Test sync handles both orphaned entries and missing memories.
        
        Rationale: Ensures sync correctly handles both scenarios simultaneously.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store a memory normally
        mem_id1, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        
        # Add orphaned entry to index
        embedding_orphan = manager.embedding_service.generate_embedding("Orphaned")
        vector_index.add_vector(99999, embedding_orphan)
        
        # Add a memory directly to storage (not in index)
        record2 = MemoryRecord(
            namespace="test.ns2",
            tags=[],
            text="Memory 2",
            importance=0.8
        )
        mem_id2 = storage.store_memory(record2)
        
        # Verify mismatch: 2 in storage, 2 in index (1 real + 1 orphaned)
        assert len(storage.get_all_memories()) == 2
        assert vector_index.get_count() == 2
        
        # Sync should remove orphaned and add missing
        manager2 = MemoryManager(storage, vector_index, manager.embedding_service)
        
        # Index should have exactly 2 entries (both real memories)
        assert vector_index.get_count() == 2
        assert len(storage.get_all_memories()) == 2
        
        # Verify both memories are searchable
        results = manager2.retrieve_memories(query="Memory", limit=10)
        assert len(results) == 2
        memory_ids = {r.id for r in results}
        assert mem_id1 in memory_ids
        assert mem_id2 in memory_ids
        
        manager2.close()


class TestIndexSyncWhenCountsMatch:
    """Test that sync preserves index when counts match."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_preserves_index_when_counts_match(
        self, temp_memory_system
    ):
        """
        Test that sync doesn't modify index when counts match.
        
        Rationale: Ensures sync doesn't unnecessarily rebuild when everything is in sync.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories normally
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
        
        # Get initial count
        initial_count = vector_index.get_count()
        assert initial_count == 2
        
        # Create new manager - should detect sync and not rebuild
        manager2 = MemoryManager(storage, vector_index, manager.embedding_service)
        
        # Count should remain the same
        assert vector_index.get_count() == initial_count
        
        # Memories should still be searchable
        results = manager2.retrieve_memories(query="Memory", limit=10)
        assert len(results) == 2
        
        manager2.close()


class TestIndexSyncEdgeCases:
    """Test edge cases for index sync."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_with_empty_storage_and_index(
        self, temp_storage, temp_vector_index, mock_embedding_service
    ):
        """
        Test sync with both storage and index empty.
        
        Rationale: Ensures sync handles empty state gracefully.
        """
        # Verify both are empty
        assert len(temp_storage.get_all_memories()) == 0
        assert temp_vector_index.get_count() == 0
        
        # Create manager - should not error
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Both should still be empty
        assert len(temp_storage.get_all_memories()) == 0
        assert temp_vector_index.get_count() == 0
        
        manager.close()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_handles_embedding_errors_gracefully(
        self, temp_storage, temp_vector_index, mock_embedding_service
    ):
        """
        Test that sync continues even if some embeddings fail.
        
        Rationale: Ensures partial failures don't stop entire sync.
        """
        # Store memories directly in storage
        record1 = MemoryRecord(
            namespace="test.ns1",
            tags=[],
            text="Memory 1",
            importance=0.7
        )
        record2 = MemoryRecord(
            namespace="test.ns2",
            tags=[],
            text="Memory 2",
            importance=0.8
        )
        
        temp_storage.store_memory(record1)
        temp_storage.store_memory(record2)
        
        # Make embedding service fail for one memory
        call_count = [0]
        def failing_embedding(text: str):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Embedding generation failed")
            return [0.1] * 1536
        
        mock_embedding_service.generate_embedding.side_effect = failing_embedding
        
        # Sync should handle the error and continue
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # At least one memory should be indexed (the one that didn't fail)
        assert temp_vector_index.get_count() >= 1
        
        manager.close()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_incremental_add_missing_memories(
        self, temp_memory_system
    ):
        """
        Test that sync incrementally adds only missing memories.
        
        Rationale: Ensures efficient sync that doesn't rebuild entire index.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store some memories normally
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
        
        initial_count = vector_index.get_count()
        assert initial_count == 2
        
        # Add a new memory directly to storage
        record3 = MemoryRecord(
            namespace="test.ns3",
            tags=[],
            text="Memory 3",
            importance=0.6
        )
        mem_id3 = storage.store_memory(record3)
        
        # Sync should add only the missing memory
        manager2 = MemoryManager(storage, vector_index, manager.embedding_service)
        
        # Should have one more memory
        assert vector_index.get_count() == initial_count + 1
        
        # All memories should be searchable
        results = manager2.retrieve_memories(query="Memory", limit=10)
        assert len(results) == 3
        
        manager2.close()


class TestEmbeddingLoadingFromDB:
    """Test that embeddings are loaded from DB instead of regenerated."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_loads_embeddings_from_db(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test that sync loads embeddings from DB instead of regenerating.
        
        Rationale: Ensures startup doesn't require API calls for existing memories.
        """
        # Store a memory with embedding directly in storage
        record = MemoryRecord(
            namespace="test.ns1",
            tags=[],
            text="Memory 1",
            importance=0.7
        )
        embedding = [0.1, 0.2, 0.3] * 512  # 1536-dim embedding
        mem_id = temp_storage.store_memory(record, embedding=embedding)
        
        # Verify embedding service is NOT called during sync
        mock_embedding_service.generate_embedding.reset_mock()
        
        # Create manager - should sync and load embedding from DB
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Verify embedding service was NOT called (embedding loaded from DB)
        mock_embedding_service.generate_embedding.assert_not_called()
        
        # Verify memory is indexed
        assert temp_vector_index.get_count() == 1
        
        manager.close()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_generates_embedding_if_missing(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test that sync generates embedding if not stored in DB.
        
        Rationale: Ensures backward compatibility with memories without embeddings.
        """
        # Store a memory WITHOUT embedding (backward compatibility)
        record = MemoryRecord(
            namespace="test.ns1",
            tags=[],
            text="Memory 1",
            importance=0.7
        )
        mem_id = temp_storage.store_memory(record)  # No embedding
        
        # Verify embedding service IS called for missing embedding
        mock_embedding_service.generate_embedding.reset_mock()
        
        # Create manager - should sync and generate embedding
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Verify embedding service WAS called (embedding generated)
        mock_embedding_service.generate_embedding.assert_called_once_with("Memory 1")
        
        # Verify memory is indexed
        assert temp_vector_index.get_count() == 1
        
        # Verify embedding was saved to DB
        retrieved = temp_storage.get_memory(mem_id)
        assert retrieved.embedding is not None
        
        manager.close()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_sync_mixed_embeddings(self, temp_storage, temp_vector_index, mock_embedding_service):
        """
        Test sync with some memories having embeddings and some not.
        
        Rationale: Ensures mixed scenarios work correctly.
        """
        # Store memory with embedding
        record1 = MemoryRecord(
            namespace="test.ns1",
            tags=[],
            text="Memory 1",
            importance=0.7
        )
        embedding1 = [0.1] * 1536
        mem_id1 = temp_storage.store_memory(record1, embedding=embedding1)
        
        # Store memory without embedding
        record2 = MemoryRecord(
            namespace="test.ns2",
            tags=[],
            text="Memory 2",
            importance=0.8
        )
        mem_id2 = temp_storage.store_memory(record2)  # No embedding
        
        # Reset mock
        mock_embedding_service.generate_embedding.reset_mock()
        
        # Create manager - should load embedding1 from DB and generate for record2
        manager = MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)
        
        # Verify embedding service was called only once (for record2)
        assert mock_embedding_service.generate_embedding.call_count == 1
        mock_embedding_service.generate_embedding.assert_called_with("Memory 2")
        
        # Verify both memories are indexed
        assert temp_vector_index.get_count() == 2
        
        manager.close()

