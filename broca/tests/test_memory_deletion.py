"""
Tests for memory deletion functionality.

Tests deletion at storage, manager, and tool levels.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest
from pathlib import Path

from broca.memory import MemoryRecord
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.memory.manager import MemoryManager
from broca.tools.memory_tool import DeleteMemoryTool

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    service = Mock(spec=EmbeddingService)
    service.generate_embedding.return_value = [0.1] * 1536
    return service


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
        
        yield manager, storage, vector_index, index_path
        
        manager.close()


class TestMemoryManagerDelete:
    """Test MemoryManager.delete_memory()."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_delete_memory_success(self, temp_memory_system):
        """
        Test deleting a memory successfully.
        
        Rationale: Ensures deletion removes memory from both storage and index.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store a memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Memory to delete",
            importance=0.7
        )
        
        # Verify it exists in both storage and index
        assert storage.get_memory(memory_id) is not None
        assert memory_id in vector_index.get_memory_ids()
        assert vector_index.get_count() == 1
        
        # Delete it
        success = manager.delete_memory(memory_id)
        
        assert success is True
        assert storage.get_memory(memory_id) is None
        assert memory_id not in vector_index.get_memory_ids()
        assert vector_index.get_count() == 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_delete_memory_nonexistent(self, temp_memory_system):
        """
        Test deleting non-existent memory returns False.
        
        Rationale: Ensures graceful handling of deletion of non-existent memories.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Try to delete non-existent memory
        success = manager.delete_memory(99999)
        
        assert success is False
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_delete_memory_removes_from_index(self, temp_memory_system):
        """
        Test that deletion removes memory from vector index.
        
        Rationale: Ensures deleted memories are not searchable.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store multiple memories
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
        
        assert vector_index.get_count() == 2
        assert mem_id1 in vector_index.get_memory_ids()
        assert mem_id2 in vector_index.get_memory_ids()
        
        # Delete one
        manager.delete_memory(mem_id1)
        
        # Verify it's removed from index
        assert vector_index.get_count() == 1
        assert mem_id1 not in vector_index.get_memory_ids()
        assert mem_id2 in vector_index.get_memory_ids()
        
        # Verify deleted memory is not searchable
        results = manager.retrieve_memories(query="Memory 1", limit=10)
        # Check that deleted memory (mem_id1) is not in results
        result_ids = [mem.id for mem in results]
        assert mem_id1 not in result_ids
        
        # Verify remaining memory is still searchable
        results = manager.retrieve_memories(query="Memory 2", limit=10)
        assert len(results) == 1
        assert results[0].id == mem_id2
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_delete_memory_saves_index_immediately(self, temp_memory_system):
        """
        Test that deletion saves index immediately.
        
        Rationale: Ensures index persistence after deletion.
        """
        manager, storage, vector_index, index_path = temp_memory_system
        
        # Store a memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Memory to delete",
            importance=0.7
        )
        
        # Delete it
        manager.delete_memory(memory_id)
        
        # Verify index was saved
        from pathlib import Path
        index_path_obj = Path(index_path)
        assert index_path_obj.exists()
        
        # Reload index and verify deletion persisted
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 0
        assert memory_id not in new_index.get_memory_ids()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_delete_multiple_memories(self, temp_memory_system):
        """
        Test deleting multiple memories.
        
        Rationale: Ensures multiple deletions work correctly.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store multiple memories
        memory_ids = []
        for i in range(5):
            mem_id, _, _ = manager.store_memory(
                namespace=f"test.ns{i}",
                text=f"Memory {i}",
                importance=0.5
            )
            memory_ids.append(mem_id)
        
        assert vector_index.get_count() == 5
        
        # Delete some
        deleted_ids = memory_ids[:2]
        remaining_ids = memory_ids[2:]
        
        for mem_id in deleted_ids:
            manager.delete_memory(mem_id)
        
        # Verify correct state
        assert vector_index.get_count() == 3
        indexed_ids = set(vector_index.get_memory_ids())
        assert set(remaining_ids) == indexed_ids
        assert not any(mid in indexed_ids for mid in deleted_ids)
        
        # Verify deleted memories are not in storage
        for mem_id in deleted_ids:
            assert storage.get_memory(mem_id) is None
        
        # Verify remaining memories are in storage
        for mem_id in remaining_ids:
            assert storage.get_memory(mem_id) is not None


class TestDeleteMemoryTool:
    """Test DeleteMemoryTool."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_delete_tool_execute_success(self, temp_memory_system):
        """
        Test DeleteMemoryTool execution success.
        
        Rationale: Ensures tool correctly executes deletion.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store a memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Memory to delete",
            importance=0.7
        )
        
        # Create tool
        tool = DeleteMemoryTool(manager)
        
        # Execute deletion
        result = tool.execute(memory_id=memory_id)
        
        assert result["success"] is True
        assert result["memory_id"] == memory_id
        assert storage.get_memory(memory_id) is None
        assert memory_id not in vector_index.get_memory_ids()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_delete_tool_execute_nonexistent(self, temp_memory_system):
        """
        Test DeleteMemoryTool with non-existent memory.
        
        Rationale: Ensures tool handles non-existent memories gracefully.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        tool = DeleteMemoryTool(manager)
        
        result = tool.execute(memory_id=99999)
        
        assert result["success"] is False
        assert "error" in result or "not found" in result.get("message", "").lower()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_delete_tool_format_result(self, temp_memory_system):
        """
        Test DeleteMemoryTool result formatting.
        
        Rationale: Ensures tool formats results correctly for LLM consumption.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store and delete memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Memory to delete",
            importance=0.7
        )
        
        tool = DeleteMemoryTool(manager)
        result = tool.execute(memory_id=memory_id)
        
        formatted = tool.format_result(result)
        
        assert "deleted" in formatted.lower() or "removed" in formatted.lower()
        assert str(memory_id) in formatted

