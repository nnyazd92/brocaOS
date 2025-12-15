"""
Tests for memory tool with conflict resolution.

Tests enhanced StoreMemoryTool with conflict detection parameters.
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
from broca.tools.memory_tool import StoreMemoryTool

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = Mock(spec=EmbeddingService)
    def generate_embedding(text: str):
        hash_val = hash(text) % 1000
        base_embedding = [0.1] * 1536
        base_embedding[0] = hash_val / 1000.0
        return base_embedding
    service.generate_embedding.side_effect = generate_embedding
    return service


@pytest.fixture
def memory_manager(mock_embedding_service):
    """Memory manager for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        index_path = os.path.join(tmpdir, "test.faiss")
        
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")
        
        storage = MemoryStorage(db_path)
        vector_index = VectorIndex(dimension=1536, index_path=index_path)
        manager = MemoryManager(storage, vector_index, mock_embedding_service)
        yield manager
        storage.close()


class TestStoreMemoryToolConflicts:
    """Test StoreMemoryTool with conflict resolution."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tool_with_conflict_check(self, memory_manager):
        """
        Test StoreMemoryTool with conflict_check parameter.
        
        Rationale: Ensures tool supports conflict checking.
        """
        tool = StoreMemoryTool(memory_manager)
        
        # Store first memory
        result1 = tool.execute(
            namespace="test.namespace",
            text="User prefers Python",
            importance=0.5
        )
        assert result1["success"] is True
        
        # Store conflicting memory with conflict_check
        result2 = tool.execute(
            namespace="test.namespace",
            text="User hates Python",
            importance=0.5,
            conflict_check=True
        )
        assert result2["success"] is True
        assert "memory_id" in result2
        # Should have conflict information when conflict_check=True
        assert "conflicts" in result2 or "conflicts_detected" in result2
        assert "conflict_count" in result2
        # May have conflicts detected
        if result2.get("conflict_count", 0) > 0:
            conflicts = result2.get("conflicts") or result2.get("conflicts_detected", [])
            assert len(conflicts) > 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tool_with_auto_resolve(self, memory_manager):
        """
        Test StoreMemoryTool with auto_resolve parameter.
        
        Rationale: Ensures tool supports auto-resolution.
        """
        tool = StoreMemoryTool(memory_manager)
        
        # Store first memory
        tool.execute(
            namespace="test.namespace",
            text="User is 25 years old",
            importance=0.5
        )
        
        # Store conflicting memory with auto_resolve
        result = tool.execute(
            namespace="test.namespace",
            text="User is 30 years old",
            importance=0.5,
            conflict_check=True,
            auto_resolve=True
        )
        assert result["success"] is True

