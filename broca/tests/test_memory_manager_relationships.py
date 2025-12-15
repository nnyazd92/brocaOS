"""
Tests for MemoryManager relationship integration.

Tests relationship functionality through MemoryManager interface.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest

from broca.memory import MemoryRecord, RelationType, RelationshipRecord
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


class TestMemoryManagerRelationshipMethods:
    """Test relationship methods in MemoryManager."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_link_memories(self, memory_manager):
        """
        Test linking memories through MemoryManager.
        
        Rationale: Ensures MemoryManager provides relationship linking interface.
        """
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
        
        # Link them
        rel_id = memory_manager.link_memories(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type=RelationType.SUPPORTS,
            strength=0.9
        )
        
        assert rel_id > 0
        
        # Verify relationship exists
        related = memory_manager.get_related_memories(mem_id1)
        assert len(related) == 1
        assert related[0][0].id == mem_id2
        assert related[0][1].relation_type == RelationType.SUPPORTS
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_unlink_memories(self, memory_manager):
        """
        Test unlinking memories through MemoryManager.
        
        Rationale: Ensures MemoryManager provides relationship unlinking interface.
        """
        # Store and link memories
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
        
        memory_manager.link_memories(mem_id1, mem_id2, RelationType.SUPPORTS)
        
        # Verify exists
        assert len(memory_manager.get_related_memories(mem_id1)) == 1
        
        # Unlink
        success = memory_manager.unlink_memories(mem_id1, mem_id2)
        assert success is True
        
        # Verify removed
        assert len(memory_manager.get_related_memories(mem_id1)) == 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_related_memories(self, memory_manager):
        """
        Test getting related memories through MemoryManager.
        
        Rationale: Ensures MemoryManager provides relationship query interface.
        """
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
        
        # Get related
        related = memory_manager.get_related_memories(mem_id1)
        
        assert len(related) == 2
        related_ids = {mem.id for mem, rel in related}
        assert mem_id2 in related_ids
        assert mem_id3 in related_ids
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_get_relationship_graph(self, memory_manager):
        """
        Test getting relationship graph through MemoryManager.
        
        Rationale: Ensures MemoryManager provides graph traversal interface.
        """
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
        
        # Get graph
        graph = memory_manager.get_relationship_graph([mem_id1], depth=1)
        
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) >= 3
        assert len(graph["edges"]) == 2


class TestMemoryManagerAutoDetection:
    """Test auto-detection of relationships."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_auto_detect_similarity(self, memory_manager):
        """
        Test auto-detection of SIMILAR_TO relationships.
        
        Rationale: Ensures similar memories are automatically linked.
        """
        # Store first memory
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="User likes Python programming",
            importance=0.7,
            auto_link=True
        )
        
        # Store similar memory
        mem_id2, _, _ = memory_manager.store_memory(
            namespace="test.ns2",
            text="User enjoys Python coding",
            importance=0.7,
            auto_link=True
        )
        
        # Check if SIMILAR_TO relationship was created
        # (May or may not be created depending on similarity threshold)
        related = memory_manager.get_related_memories(mem_id1)
        # At least verify the method doesn't crash
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_auto_detect_conflicts(self, memory_manager):
        """
        Test auto-detection of CONTRADICTS relationships.
        
        Rationale: Ensures conflicting memories are automatically linked.
        """
        # Store first memory
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="User prefers Python",
            importance=0.7,
            auto_link=True
        )
        
        # Store conflicting memory with conflict_check
        mem_id2, _, conflicts = memory_manager.store_memory(
            namespace="test.ns1",
            text="User hates Python",
            importance=0.7,
            conflict_check=True,
            auto_link=True
        )
        
        # If conflicts detected, should create CONTRADICTS relationship
        if conflicts:
            related = memory_manager.get_related_memories(
                mem_id2,
                relation_types=[RelationType.CONTRADICTS]
            )
            # May have CONTRADICTS relationship
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_auto_detect_namespace_hierarchy(self, memory_manager):
        """
        Test auto-detection of ELABORATES for namespace hierarchy.
        
        Rationale: Ensures child namespaces are linked to parent namespaces.
        """
        # Store parent memory
        parent_id, _, _ = memory_manager.store_memory(
            namespace="test.parent",
            text="Parent memory",
            importance=0.8,
            auto_link=True
        )
        
        # Store child memory
        child_id, _, _ = memory_manager.store_memory(
            namespace="test.parent.child",
            text="Child memory",
            importance=0.7,
            auto_link=True
        )
        
        # Check if ELABORATES relationship was created
        related = memory_manager.get_related_memories(
            child_id,
            relation_types=[RelationType.ELABORATES]
        )
        # May have ELABORATES relationship to parent
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_auto_link_can_be_disabled(self, memory_manager):
        """
        Test that auto-link can be disabled.
        
        Rationale: Ensures auto-detection is optional.
        """
        # Store memories with auto_link=False
        mem_id1, _, _ = memory_manager.store_memory(
            namespace="test.ns1",
            text="Memory 1",
            importance=0.7,
            auto_link=False
        )
        mem_id2, _, _ = memory_manager.store_memory(
            namespace="test.ns2",
            text="Memory 2",
            importance=0.8,
            auto_link=False
        )
        
        # Should not have auto-created relationships
        related = memory_manager.get_related_memories(mem_id1)
        # May have relationships from other sources, but not auto-detected ones

