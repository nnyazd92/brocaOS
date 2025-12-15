"""
Tests for memory update functionality.

Tests updating memories with text changes (embedding regeneration) and metadata-only updates.
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
from broca.tools.memory_tool import UpdateMemoryTool

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
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        # Create a 1536-dim embedding with some variation
        embedding = [0.1 + (hash_val % 100) / 10000.0] * 1536
        return embedding
    
    service.generate_embedding.side_effect = generate_embedding
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


class TestMemoryManagerUpdate:
    """Test MemoryManager.update_memory()."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_memory_text_regenerates_embedding(self, temp_memory_system):
        """
        Test that updating text regenerates embedding and updates index.
        
        Rationale: Text changes require new embeddings for accurate search.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Original text",
            importance=0.7
        )
        
        # Get original embedding
        original_memory = storage.get_memory(memory_id)
        original_embedding = original_memory.embedding
        
        # Reset mock to track new calls
        manager.embedding_service.generate_embedding.reset_mock()
        
        # Update text
        success = manager.update_memory(
            memory_id=memory_id,
            text="Updated text"
        )
        
        assert success is True
        
        # Verify embedding was regenerated
        manager.embedding_service.generate_embedding.assert_called_once_with("Updated text")
        
        # Verify new embedding is different
        updated_memory = storage.get_memory(memory_id)
        assert updated_memory.embedding != original_embedding
        assert updated_memory.text == "Updated text"
        
        # Verify memory is still in index (with new embedding)
        assert memory_id in vector_index.get_memory_ids()
        assert vector_index.get_count() == 1
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_memory_metadata_only_no_embedding(self, temp_memory_system):
        """
        Test that metadata-only updates don't regenerate embeddings.
        
        Rationale: Metadata changes don't affect semantic search, so no embedding needed.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Test memory",
            importance=0.7,
            tags=["tag1"]
        )
        
        # Get original embedding
        original_memory = storage.get_memory(memory_id)
        original_embedding = original_memory.embedding
        
        # Reset mock
        manager.embedding_service.generate_embedding.reset_mock()
        
        # Update only metadata
        success = manager.update_memory(
            memory_id=memory_id,
            importance=0.9,
            tags=["tag1", "tag2"]
        )
        
        assert success is True
        
        # Verify embedding was NOT regenerated
        manager.embedding_service.generate_embedding.assert_not_called()
        
        # Verify embedding unchanged
        updated_memory = storage.get_memory(memory_id)
        assert updated_memory.embedding == original_embedding
        
        # Verify metadata updated
        assert updated_memory.importance == 0.9
        assert set(updated_memory.tags) == {"tag1", "tag2"}
        
        # Verify memory still in index
        assert memory_id in vector_index.get_memory_ids()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_memory_namespace(self, temp_memory_system):
        """
        Test updating namespace.
        
        Rationale: Namespace changes should update storage but not require embedding.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Test memory",
            importance=0.7
        )
        
        # Reset mock
        manager.embedding_service.generate_embedding.reset_mock()
        
        # Update namespace
        success = manager.update_memory(
            memory_id=memory_id,
            namespace="test.ns2"
        )
        
        assert success is True
        
        # Verify embedding was NOT regenerated (namespace doesn't affect embedding)
        manager.embedding_service.generate_embedding.assert_not_called()
        
        # Verify namespace updated
        updated_memory = storage.get_memory(memory_id)
        assert updated_memory.namespace == "test.ns2"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_memory_text_and_metadata(self, temp_memory_system):
        """
        Test updating both text and metadata together.
        
        Rationale: Ensures combined updates work correctly.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Original text",
            importance=0.7,
            tags=["tag1"]
        )
        
        # Update both text and metadata
        success = manager.update_memory(
            memory_id=memory_id,
            text="Updated text",
            importance=0.9,
            tags=["tag1", "tag2"]
        )
        
        assert success is True
        
        # Verify embedding was regenerated (because text changed)
        # May be called multiple times due to auto-detection
        assert manager.embedding_service.generate_embedding.call_count >= 1
        assert any("Updated text" in str(call) for call in manager.embedding_service.generate_embedding.call_args_list)
        
        # Verify all fields updated
        updated_memory = storage.get_memory(memory_id)
        assert updated_memory.text == "Updated text"
        assert updated_memory.importance == 0.9
        assert set(updated_memory.tags) == {"tag1", "tag2"}
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_memory_saves_index_immediately(self, temp_memory_system):
        """
        Test that text update saves index immediately.
        
        Rationale: Ensures index persistence after text updates.
        """
        manager, storage, vector_index, index_path = temp_memory_system
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Original text",
            importance=0.7
        )
        
        # Update text
        manager.update_memory(
            memory_id=memory_id,
            text="Updated text"
        )
        
        # Verify index was saved
        assert Path(index_path).exists()
        
        # Reload index and verify updated memory is searchable
        new_index = VectorIndex(dimension=1536, index_path=index_path)
        assert new_index.get_count() == 1
        assert memory_id in new_index.get_memory_ids()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_memory_nonexistent(self, temp_memory_system):
        """
        Test updating non-existent memory returns False.
        
        Rationale: Ensures graceful handling of non-existent memories.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Try to update non-existent memory
        success = manager.update_memory(
            memory_id=99999,
            text="Updated text"
        )
        
        assert success is False
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_memory_searchable_with_new_text(self, temp_memory_system):
        """
        Test that updated memory is searchable with new text.
        
        Rationale: Ensures embedding update makes new text searchable.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Original content",
            importance=0.7
        )
        
        # Update text
        manager.update_memory(
            memory_id=memory_id,
            text="Updated content with new information"
        )
        
        # Verify memory is searchable with new text
        results = manager.retrieve_memories(query="Updated content", limit=10)
        assert len(results) == 1
        assert results[0].id == memory_id
        assert results[0].text == "Updated content with new information"
        
        # Old text should be less relevant
        results_old = manager.retrieve_memories(query="Original content", limit=10)
        # May or may not find it depending on similarity, but if found, should have updated text
        if results_old:
            assert results_old[0].text == "Updated content with new information"


class TestUpdateMemoryTool:
    """Test UpdateMemoryTool."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_tool_execute_text_update(self, temp_memory_system):
        """
        Test UpdateMemoryTool execution with text update.
        
        Rationale: Ensures tool correctly executes text updates.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Original text",
            importance=0.7
        )
        
        # Create tool
        tool = UpdateMemoryTool(manager)
        
        # Execute update
        result = tool.execute(
            memory_id=memory_id,
            text="Updated text"
        )
        
        assert result["success"] is True
        assert result["memory_id"] == memory_id
        
        # Verify update
        updated_memory = storage.get_memory(memory_id)
        assert updated_memory.text == "Updated text"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_tool_execute_metadata_update(self, temp_memory_system):
        """
        Test UpdateMemoryTool execution with metadata update.
        
        Rationale: Ensures tool correctly executes metadata-only updates.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store initial memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Test memory",
            importance=0.7,
            tags=["tag1"]
        )
        
        tool = UpdateMemoryTool(manager)
        
        result = tool.execute(
            memory_id=memory_id,
            importance=0.9,
            tags=["tag1", "tag2"]
        )
        
        assert result["success"] is True
        
        # Verify update
        updated_memory = storage.get_memory(memory_id)
        assert updated_memory.importance == 0.9
        assert set(updated_memory.tags) == {"tag1", "tag2"}
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_tool_execute_nonexistent(self, temp_memory_system):
        """
        Test UpdateMemoryTool with non-existent memory.
        
        Rationale: Ensures tool handles non-existent memories gracefully.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        tool = UpdateMemoryTool(manager)
        
        result = tool.execute(
            memory_id=99999,
            text="Updated text"
        )
        
        assert result["success"] is False
        assert "error" in result or "not found" in result.get("message", "").lower()
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_update_tool_format_result(self, temp_memory_system):
        """
        Test UpdateMemoryTool result formatting.
        
        Rationale: Ensures tool formats results correctly for LLM consumption.
        """
        manager, storage, vector_index, _ = temp_memory_system
        
        # Store and update memory
        memory_id, _, _ = manager.store_memory(
            namespace="test.ns1",
            text="Original text",
            importance=0.7
        )
        
        tool = UpdateMemoryTool(manager)
        result = tool.execute(
            memory_id=memory_id,
            text="Updated text"
        )
        
        formatted = tool.format_result(result)
        
        assert "updated" in formatted.lower()
        assert str(memory_id) in formatted

