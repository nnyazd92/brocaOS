"""
Tests for memory deduplication feature.

Tests the exact duplicate detection and update functionality.
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


@pytest.fixture
def memory_manager(temp_storage, temp_vector_index, mock_embedding_service):
    """Memory manager for testing."""
    return MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)


class TestMemoryStorageDeduplication:
    """Test deduplication functionality in MemoryStorage."""
    
    def test_check_exact_duplicate_found(self, temp_storage):
        """
        Test that exact duplicates are detected.
        
        Rationale: Ensures duplicate detection works for same namespace and text.
        """
        # Store first memory
        record1 = MemoryRecord(
            namespace="test.namespace",
            text="Test memory content",
            importance=0.5
        )
        memory_id1 = temp_storage.store_memory(record1)
        
        # Check for duplicate
        duplicate_id = temp_storage.check_exact_duplicate("test.namespace", "Test memory content")
        assert duplicate_id == memory_id1
    
    def test_check_exact_duplicate_not_found(self, temp_storage):
        """
        Test that non-duplicates return None.
        
        Rationale: Ensures only exact matches are detected as duplicates.
        """
        # Store a memory
        record = MemoryRecord(
            namespace="test.namespace",
            text="Test memory content",
            importance=0.5
        )
        temp_storage.store_memory(record)
        
        # Check for non-duplicate (different namespace)
        result = temp_storage.check_exact_duplicate("different.namespace", "Test memory content")
        assert result is None
        
        # Check for non-duplicate (different text)
        result = temp_storage.check_exact_duplicate("test.namespace", "Different content")
        assert result is None
    
    def test_update_memory_success(self, temp_storage):
        """
        Test updating existing memory.
        
        Rationale: Ensures memory updates work correctly.
        """
        # Store initial memory
        record = MemoryRecord(
            namespace="test",
            text="Initial content",
            importance=0.3,
            tags=["tag1"]
        )
        memory_id = temp_storage.store_memory(record)
        
        # Update memory
        success = temp_storage.update_memory(memory_id, 0.8, ["tag1", "tag2"])
        assert success is True
        
        # Verify update
        updated = temp_storage.get_memory(memory_id)
        assert updated is not None
        assert updated.importance == 0.8
        assert set(updated.tags) == {"tag1", "tag2"}
    
    def test_update_memory_not_found(self, temp_storage):
        """
        Test updating non-existent memory returns False.
        
        Rationale: Ensures graceful handling of non-existent memory IDs.
        """
        success = temp_storage.update_memory(999, 0.5, ["tag"])
        assert success is False


class TestMemoryManagerDeduplication:
    """Test deduplication functionality in MemoryManager."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_with_deduplication_enabled(self, memory_manager):
        """
        Test storing with deduplication enabled.
        
        Rationale: Ensures duplicates are detected and updated.
        """
        # First store
        memory_id1, was_dup1, _ = memory_manager.store_memory(
            namespace="user.info",
            text="I like coffee",
            importance=0.6,
            deduplicate=True
        )
        assert was_dup1 is False
        
        # Second store (duplicate)
        memory_id2, was_dup2, _ = memory_manager.store_memory(
            namespace="user.info",
            text="I like coffee",
            importance=0.8,  # Higher importance
            deduplicate=True
        )
        assert was_dup2 is True
        assert memory_id2 == memory_id1  # Same memory ID
        
        # Verify importance was updated to max
        memory = memory_manager.get_memory(memory_id1)
        assert memory.importance == 0.8
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_with_deduplication_disabled(self, memory_manager):
        """
        Test storing with deduplication disabled.
        
        Rationale: Ensures duplicates can be created when deduplication is off.
        """
        # First store
        memory_id1, was_dup1, _ = memory_manager.store_memory(
            namespace="user.info",
            text="Duplicate text",
            importance=0.5,
            deduplicate=False
        )
        
        # Second store with deduplication disabled
        memory_id2, was_dup2, _ = memory_manager.store_memory(
            namespace="user.info",
            text="Duplicate text",
            importance=0.5,
            deduplicate=False
        )
        
        assert was_dup1 is False
        assert was_dup2 is False
        assert memory_id1 != memory_id2  # Different memory IDs
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_tags_merged_on_duplicate(self, memory_manager):
        """
        Test that tags are merged when duplicate is found.
        
        Rationale: Ensures tag merging works correctly.
        """
        # First store with tags
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Same text",
            importance=0.5,
            tags=["tag1", "tag2"],
            deduplicate=True
        )
        
        # Second store with different tags
        memory_id2, was_dup, _ = memory_manager.store_memory(
            namespace="test",
            text="Same text",
            importance=0.6,
            tags=["tag2", "tag3"],  # tag2 is common
            deduplicate=True
        )
        
        assert was_dup is True
        assert memory_id2 == memory_id1
        
        # Verify tags were merged (unique union)
        memory = memory_manager.get_memory(memory_id1)
        assert set(memory.tags) == {"tag1", "tag2", "tag3"}
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_store_memory_importance_max_on_duplicate(self, memory_manager):
        """
        Test that max importance is kept when duplicate is found.
        
        Rationale: Ensures the more important memory is preserved.
        """
        # First store with lower importance
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Important fact",
            importance=0.3,
            deduplicate=True
        )
        
        # Second store with higher importance
        memory_id2, was_dup, _ = memory_manager.store_memory(
            namespace="test",
            text="Important fact",
            importance=0.9,
            deduplicate=True
        )
        
        assert was_dup is True
        assert memory_id2 == memory_id1
        
        # Verify max importance was kept
        memory = memory_manager.get_memory(memory_id1)
        assert memory.importance == 0.9
        
        # Third store with lower importance (should not reduce it)
        memory_id3, was_dup3, _ = memory_manager.store_memory(
            namespace="test",
            text="Important fact",
            importance=0.5,
            deduplicate=True
        )
        
        assert was_dup3 is True
        assert memory_id3 == memory_id1
        
        # Importance should still be 0.9 (max)
        memory = memory_manager.get_memory(memory_id1)
        assert memory.importance == 0.9
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_different_namespace_not_duplicate(self, memory_manager):
        """
        Test that same text in different namespace is not a duplicate.
        
        Rationale: Ensures namespace is part of duplicate detection.
        """
        # Store in namespace A
        memory_id1, was_dup1, _ = memory_manager.store_memory(
            namespace="namespace.a",
            text="Common text",
            importance=0.5,
            deduplicate=True
        )
        
        # Store same text in namespace B
        memory_id2, was_dup2, _ = memory_manager.store_memory(
            namespace="namespace.b",
            text="Common text",
            importance=0.5,
            deduplicate=True
        )
        
        assert was_dup1 is False
        assert was_dup2 is False
        assert memory_id1 != memory_id2  # Different memories


class TestStoreMemoryToolDeduplication:
    """Test deduplication in StoreMemoryTool."""
    
    @pytest.fixture
    def store_memory_tool(self, memory_manager):
        """StoreMemoryTool for testing."""
        from broca.tools.memory_tool import StoreMemoryTool
        return StoreMemoryTool(memory_manager)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tool_parameters_include_deduplicate(self, store_memory_tool):
        """
        Test that tool parameters include deduplicate option.
        
        Rationale: Ensures the tool exposes deduplication parameter.
        """
        params = store_memory_tool.parameters
        assert "deduplicate" in params["properties"]
        assert params["properties"]["deduplicate"]["type"] == "boolean"
        assert params["properties"]["deduplicate"]["default"] is True
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tool_execute_with_deduplication(self, store_memory_tool):
        """
        Test tool execution with deduplication.
        
        Rationale: Ensures tool correctly passes deduplicate parameter.
        """
        # First store
        result1 = store_memory_tool.execute(
            namespace="test.tool",
            text="Tool test memory",
            importance=0.5,
            deduplicate=True
        )
        
        assert result1["success"] is True
        assert result1["was_duplicate"] is False
        
        # Second store (duplicate)
        result2 = store_memory_tool.execute(
            namespace="test.tool",
            text="Tool test memory",
            importance=0.7,
            deduplicate=True
        )
        
        assert result2["success"] is True
        assert result2["was_duplicate"] is True
        assert result2["memory_id"] == result1["memory_id"]
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tool_format_result_shows_duplicate(self, store_memory_tool):
        """
        Test tool format result indicates duplicate.
        
        Rationale: Ensures LLM gets clear feedback about duplicates.
        """
        # Store a memory
        result = store_memory_tool.execute(
            namespace="test.format",
            text="Format test",
            importance=0.5,
            deduplicate=True
        )
        
        formatted = store_memory_tool.format_result(result)
        
        if result.get("was_duplicate"):
            assert "updated" in formatted.lower()
        else:
            assert "stored" in formatted.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
