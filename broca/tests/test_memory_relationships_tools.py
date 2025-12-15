"""
Tests for memory relationship tools.

Tests LinkMemoriesTool and GetRelatedMemoriesTool.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest

from broca.memory import RelationType
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.memory.manager import MemoryManager
from broca.tools.memory_tool import LinkMemoriesTool, GetRelatedMemoriesTool

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
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        embedding = [0.1 + (hash_val % 100) / 10000.0] * 1536
        return embedding
    
    service.generate_embedding.side_effect = generate_embedding
    return service


@pytest.fixture
def memory_manager(mock_embedding_service):
    """MemoryManager for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        index_path = os.path.join(tmpdir, "test.faiss")
        
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")
        
        storage = MemoryStorage(db_path)
        vector_index = VectorIndex(dimension=1536, index_path=index_path)
        manager = MemoryManager(storage, vector_index, mock_embedding_service)
        yield manager
        manager.close()


class TestLinkMemoriesTool:
    """Test LinkMemoriesTool."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_link_memories_tool_execution(self, memory_manager):
        """
        Test LinkMemoriesTool execution.
        
        Rationale: Ensures tool can create relationships between memories.
        """
        tool = LinkMemoriesTool(memory_manager)
        
        # Store memories
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        mem_id2, _, _ = memory_manager.store_memory(
            namespace="test.ns2",
            text="Memory 2",
            importance=0.8
        )
        
        # Link them using tool
        result = tool.execute(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type="supports",
            strength=0.9
        )
        
        assert result["success"] is True
        assert "relationship_id" in result
        assert result["relationship_id"] > 0
        
        # Verify relationship exists
        related = memory_manager.get_related_memories(mem_id1)
        assert len(related) == 1
        assert related[0][0].id == mem_id2
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_link_memories_tool_bidirectional(self, memory_manager):
        """
        Test LinkMemoriesTool with bidirectional relationship.
        
        Rationale: Ensures bidirectional relationships work through tool.
        """
        tool = LinkMemoriesTool(memory_manager)
        
        # Store memories
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        mem_id2, _, _ = memory_manager.store_memory(
            namespace="test.ns2",
            text="Memory 2",
            importance=0.8
        )
        
        # Link bidirectionally
        result = tool.execute(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type="similar_to",
            bidirectional=True
        )
        
        assert result["success"] is True
        
        # Verify both directions exist
        outgoing = memory_manager.get_related_memories(mem_id1, direction="outgoing")
        incoming = memory_manager.get_related_memories(mem_id1, direction="incoming")
        
        assert len(outgoing) == 1
        assert len(incoming) == 1
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_link_memories_tool_validation(self, memory_manager):
        """
        Test LinkMemoriesTool parameter validation.
        
        Rationale: Ensures tool validates parameters correctly.
        """
        tool = LinkMemoriesTool(memory_manager)
        
        # Store memories
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        mem_id2, _, _ = memory_manager.store_memory(
            namespace="test.ns2",
            text="Memory 2",
            importance=0.8
        )
        
        # Test invalid relation_type
        result = tool.execute(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type="invalid_type"
        )
        
        assert result["success"] is False
        assert "error" in result
        
        # Test invalid strength
        result = tool.execute(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type="supports",
            strength=1.5  # Invalid: > 1.0
        )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_link_memories_tool_nonexistent_memory(self, memory_manager):
        """
        Test LinkMemoriesTool with nonexistent memory IDs.
        
        Rationale: Ensures tool handles invalid memory IDs gracefully.
        """
        tool = LinkMemoriesTool(memory_manager)
        
        # Store one memory
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        
        # Try to link to nonexistent memory
        result = tool.execute(
            source_id=mem_id1,
            target_id=99999,
            relation_type="supports"
        )
        
        assert result["success"] is False
        assert "error" in result


class TestGetRelatedMemoriesTool:
    """Test GetRelatedMemoriesTool."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_related_memories_tool_execution(self, memory_manager):
        """
        Test GetRelatedMemoriesTool execution.
        
        Rationale: Ensures tool can retrieve related memories.
        """
        tool = GetRelatedMemoriesTool(memory_manager)
        
        # Store memories
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        mem_id2, _, _ = memory_manager.store_memory(
            namespace="test.ns2",
            text="Memory 2",
            importance=0.8
        )
        mem_id3, _, _ = memory_manager.store_memory(
            namespace="test.ns3",
            text="Memory 3",
            importance=0.6
        )
        
        # Create relationships
        memory_manager.link_memories(mem_id1, mem_id2, RelationType.SUPPORTS)
        memory_manager.link_memories(mem_id1, mem_id3, RelationType.CONTRADICTS)
        
        # Get related using tool
        result = tool.execute(memory_id=mem_id1)
        
        assert result["success"] is True
        assert "related_memories" in result
        assert len(result["related_memories"]) == 2
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_related_memories_tool_filter_by_type(self, memory_manager):
        """
        Test GetRelatedMemoriesTool filtering by relation type.
        
        Rationale: Ensures tool can filter relationships by type.
        """
        tool = GetRelatedMemoriesTool(memory_manager)
        
        # Store memories
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        mem_id2, _, _ = memory_manager.store_memory(
            namespace="test.ns2",
            text="Memory 2",
            importance=0.8
        )
        mem_id3, _, _ = memory_manager.store_memory(
            namespace="test.ns3",
            text="Memory 3",
            importance=0.6
        )
        
        # Create relationships
        memory_manager.link_memories(mem_id1, mem_id2, RelationType.SUPPORTS)
        memory_manager.link_memories(mem_id1, mem_id3, RelationType.CONTRADICTS)
        
        # Get only SUPPORTS relationships
        result = tool.execute(
            memory_id=mem_id1,
            relation_types=["supports"]
        )
        
        assert result["success"] is True
        assert len(result["related_memories"]) == 1
        assert result["related_memories"][0]["relationship_type"] == "supports"
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_related_memories_tool_limit(self, memory_manager):
        """
        Test GetRelatedMemoriesTool limit parameter.
        
        Rationale: Ensures tool respects limit parameter.
        """
        tool = GetRelatedMemoriesTool(memory_manager)
        
        # Store memories
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7
        )
        
        # Create multiple relationships
        for i in range(5):
            mem_id, _, _ = memory_manager.store_memory(
                namespace=f"test.ns{i+2}",
                text=f"Memory {i+2}",
                importance=0.7
            )
            memory_manager.link_memories(mem_id1, mem_id, RelationType.REFERENCES)
        
        # Get with limit
        result = tool.execute(
            memory_id=mem_id1,
            limit=3
        )
        
        assert result["success"] is True
        assert len(result["related_memories"]) <= 3
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_related_memories_tool_nonexistent_memory(self, memory_manager):
        """
        Test GetRelatedMemoriesTool with nonexistent memory ID.
        
        Rationale: Ensures tool handles invalid memory IDs gracefully.
        """
        tool = GetRelatedMemoriesTool(memory_manager)
        
        result = tool.execute(memory_id=99999)
        
        assert result["success"] is False
        assert "error" in result


class TestLinkMemoriesToolFormatResult:
    """Test LinkMemoriesTool format_result method."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_format_result_success(self, memory_manager):
        """
        Test format_result with successful linking.
        
        Rationale: Ensures format_result formats success results correctly.
        """
        tool = LinkMemoriesTool(memory_manager)
        
        result = {
            "success": True,
            "relationship_id": 1,
            "source_id": 10,
            "target_id": 20,
            "relation_type": "supports",
            "strength": 0.9,
            "bidirectional": False,
            "message": "Linked memory 10 -> 20 (supports)"
        }
        
        formatted = tool.format_result(result)
        
        assert "Linked memory" in formatted
        assert "10" in formatted
        assert "20" in formatted
        assert "supports" in formatted
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_format_result_error(self, memory_manager):
        """
        Test format_result with error.
        
        Rationale: Ensures format_result formats error results correctly.
        """
        tool = LinkMemoriesTool(memory_manager)
        
        result = {
            "success": False,
            "error": "Memory not found",
            "message": "Failed to link memories: Memory not found"
        }
        
        formatted = tool.format_result(result)
        
        assert "Error" in formatted or "error" in formatted.lower()
        assert "Memory not found" in formatted


class TestGetRelatedMemoriesToolFormatResult:
    """Test GetRelatedMemoriesTool format_result method."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_format_result_success(self, memory_manager):
        """
        Test format_result with successful retrieval.
        
        Rationale: Ensures format_result formats success results correctly.
        """
        tool = GetRelatedMemoriesTool(memory_manager)
        
        result = {
            "success": True,
            "memory_id": 10,
            "related_memories": [
                {
                    "memory_id": 20,
                    "namespace": "test.ns2",
                    "text": "Related memory 1",
                    "importance": 0.8,
                    "relationship_type": "supports",
                    "relationship_strength": 0.9,
                    "bidirectional": False
                },
                {
                    "memory_id": 30,
                    "namespace": "test.ns3",
                    "text": "Related memory 2",
                    "importance": 0.7,
                    "relationship_type": "contradicts",
                    "relationship_strength": 0.8,
                    "bidirectional": False
                }
            ],
            "count": 2,
            "message": "Found 2 related memories"
        }
        
        formatted = tool.format_result(result)
        
        assert "related memories" in formatted.lower() or "2" in formatted
        assert "supports" in formatted or "Related memory 1" in formatted
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_format_result_empty(self, memory_manager):
        """
        Test format_result with no related memories.
        
        Rationale: Ensures format_result handles empty results correctly.
        """
        tool = GetRelatedMemoriesTool(memory_manager)
        
        result = {
            "success": True,
            "memory_id": 10,
            "related_memories": [],
            "count": 0,
            "message": "Found 0 related memories"
        }
        
        formatted = tool.format_result(result)
        
        assert "No related memories" in formatted or "0" in formatted
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_format_result_error(self, memory_manager):
        """
        Test format_result with error.
        
        Rationale: Ensures format_result formats error results correctly.
        """
        tool = GetRelatedMemoriesTool(memory_manager)
        
        result = {
            "success": False,
            "error": "Memory not found",
            "message": "Memory 999 does not exist"
        }
        
        formatted = tool.format_result(result)
        
        assert "Error" in formatted or "error" in formatted.lower()
        assert "Memory not found" in formatted or "999" in formatted

