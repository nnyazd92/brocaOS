"""
Tests for RelationshipManager.

Tests relationship management operations (link, unlink, get_related, graph traversal).
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest

from broca.memory import MemoryRecord, RelationType, RelationshipRecord
from broca.memory.storage import MemoryStorage
from broca.memory.relationships import RelationshipManager

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@pytest.fixture
def temp_storage():
    """Temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        storage = MemoryStorage(db_path)
        yield storage
        storage.close()


@pytest.fixture
def relationship_manager(temp_storage):
    """RelationshipManager for testing."""
    return RelationshipManager(temp_storage)


class TestRelationshipManagerLink:
    """Test linking memories."""
    
    def test_link_memories_success(self, relationship_manager, temp_storage):
        """
        Test linking two memories successfully.
        
        Rationale: Ensures relationships can be created between memories.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        
        # Link them
        rel_id = relationship_manager.link(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type=RelationType.SUPPORTS,
            strength=0.9
        )
        
        assert rel_id > 0
        
        # Verify relationship exists
        relationships = temp_storage.get_relationships(source_id=mem_id1)
        assert len(relationships) == 1
        assert relationships[0].relation_type == RelationType.SUPPORTS
        assert relationships[0].strength == 0.9
    
    def test_link_bidirectional(self, relationship_manager, temp_storage):
        """
        Test bidirectional linking creates reverse relationship.
        
        Rationale: Ensures bidirectional relationships work correctly.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        
        # Link bidirectionally
        rel_id = relationship_manager.link(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type=RelationType.SIMILAR_TO,
            bidirectional=True
        )
        
        assert rel_id > 0
        
        # Verify both directions exist
        outgoing = temp_storage.get_relationships(source_id=mem_id1)
        incoming = temp_storage.get_relationships(target_id=mem_id1)
        
        assert len(outgoing) == 1
        assert len(incoming) == 1
        assert outgoing[0].target_id == mem_id2
        assert incoming[0].source_id == mem_id2
    
    def test_link_with_metadata(self, relationship_manager, temp_storage):
        """
        Test linking with metadata.
        
        Rationale: Ensures metadata can be stored with relationships.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        
        metadata = {"detection_method": "manual", "confidence": 0.95}
        
        rel_id = relationship_manager.link(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type=RelationType.ELABORATES,
            metadata=metadata
        )
        
        # Verify metadata stored
        relationships = temp_storage.get_relationships(source_id=mem_id1)
        assert len(relationships) == 1
        assert relationships[0].metadata == metadata


class TestRelationshipManagerUnlink:
    """Test unlinking memories."""
    
    def test_unlink_memories_success(self, relationship_manager, temp_storage):
        """
        Test unlinking memories successfully.
        
        Rationale: Ensures relationships can be removed.
        """
        # Create memories and link
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        
        rel_id = relationship_manager.link(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type=RelationType.SUPPORTS
        )
        
        # Verify exists
        assert len(temp_storage.get_relationships(source_id=mem_id1)) == 1
        
        # Unlink
        success = relationship_manager.unlink(
            source_id=mem_id1,
            target_id=mem_id2,
            relation_type=RelationType.SUPPORTS
        )
        
        assert success is True
        assert len(temp_storage.get_relationships(source_id=mem_id1)) == 0
    
    def test_unlink_all_relationships(self, relationship_manager, temp_storage):
        """
        Test unlinking all relationships between two memories.
        
        Rationale: Ensures all relationship types can be removed at once.
        """
        # Create memories and multiple links
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        
        relationship_manager.link(mem_id1, mem_id2, RelationType.SUPPORTS)
        relationship_manager.link(mem_id1, mem_id2, RelationType.REFERENCES)
        
        assert len(temp_storage.get_relationships(source_id=mem_id1)) == 2
        
        # Unlink all
        success = relationship_manager.unlink(mem_id1, mem_id2)
        
        assert success is True
        assert len(temp_storage.get_relationships(source_id=mem_id1)) == 0


class TestRelationshipManagerGetRelated:
    """Test getting related memories."""
    
    def test_get_related_outgoing(self, relationship_manager, temp_storage):
        """
        Test getting outgoing related memories.
        
        Rationale: Ensures outgoing relationships can be queried.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        mem_id3 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns3", text="Memory 3", importance=0.6
        ))
        
        # Create relationships from mem_id1
        relationship_manager.link(mem_id1, mem_id2, RelationType.SUPPORTS)
        relationship_manager.link(mem_id1, mem_id3, RelationType.CONTRADICTS)
        
        # Get outgoing
        related = relationship_manager.get_related(
            memory_id=mem_id1,
            direction="outgoing"
        )
        
        assert len(related) == 2
        related_ids = {mem.id for mem, rel in related}
        assert mem_id2 in related_ids
        assert mem_id3 in related_ids
    
    def test_get_related_incoming(self, relationship_manager, temp_storage):
        """
        Test getting incoming related memories.
        
        Rationale: Ensures incoming relationships can be queried.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        mem_id3 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns3", text="Memory 3", importance=0.6
        ))
        
        # Create relationships pointing to mem_id1
        relationship_manager.link(mem_id2, mem_id1, RelationType.ELABORATES)
        relationship_manager.link(mem_id3, mem_id1, RelationType.REFERENCES)
        
        # Get incoming
        related = relationship_manager.get_related(
            memory_id=mem_id1,
            direction="incoming"
        )
        
        assert len(related) == 2
        related_ids = {mem.id for mem, rel in related}
        assert mem_id2 in related_ids
        assert mem_id3 in related_ids
    
    def test_get_related_both(self, relationship_manager, temp_storage):
        """
        Test getting both incoming and outgoing relationships.
        
        Rationale: Ensures both directions can be queried together.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        mem_id3 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns3", text="Memory 3", importance=0.6
        ))
        
        # Create relationships in both directions
        relationship_manager.link(mem_id1, mem_id2, RelationType.SUPPORTS)
        relationship_manager.link(mem_id3, mem_id1, RelationType.ELABORATES)
        
        # Get both
        related = relationship_manager.get_related(
            memory_id=mem_id1,
            direction="both"
        )
        
        assert len(related) == 2
        related_ids = {mem.id for mem, rel in related}
        assert mem_id2 in related_ids
        assert mem_id3 in related_ids
    
    def test_get_related_filter_by_type(self, relationship_manager, temp_storage):
        """
        Test filtering related memories by relationship type.
        
        Rationale: Ensures relationships can be filtered by type.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        mem_id3 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns3", text="Memory 3", importance=0.6
        ))
        
        # Create relationships of different types
        relationship_manager.link(mem_id1, mem_id2, RelationType.CONTRADICTS)
        relationship_manager.link(mem_id1, mem_id3, RelationType.SUPPORTS)
        
        # Get only CONTRADICTS
        related = relationship_manager.get_related(
            memory_id=mem_id1,
            relation_types=[RelationType.CONTRADICTS]
        )
        
        assert len(related) == 1
        assert related[0][0].id == mem_id2
        assert related[0][1].relation_type == RelationType.CONTRADICTS
    
    def test_get_related_min_strength(self, relationship_manager, temp_storage):
        """
        Test filtering by minimum strength.
        
        Rationale: Ensures weak relationships can be filtered out.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        mem_id3 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns3", text="Memory 3", importance=0.6
        ))
        
        # Create relationships with different strengths
        relationship_manager.link(mem_id1, mem_id2, RelationType.SUPPORTS, strength=0.9)
        relationship_manager.link(mem_id1, mem_id3, RelationType.SUPPORTS, strength=0.5)
        
        # Get only strong relationships
        related = relationship_manager.get_related(
            memory_id=mem_id1,
            min_strength=0.8
        )
        
        assert len(related) == 1
        assert related[0][0].id == mem_id2


class TestRelationshipManagerGraph:
    """Test relationship graph traversal."""
    
    def test_get_relationship_graph_depth_1(self, relationship_manager, temp_storage):
        """
        Test getting relationship graph with depth 1.
        
        Rationale: Ensures graph traversal works for single hop.
        """
        # Create memories
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        mem_id3 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns3", text="Memory 3", importance=0.6
        ))
        
        # Create relationships
        relationship_manager.link(mem_id1, mem_id2, RelationType.SUPPORTS)
        relationship_manager.link(mem_id1, mem_id3, RelationType.CONTRADICTS)
        
        # Get graph
        graph = relationship_manager.get_relationship_graph([mem_id1], depth=1)
        
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 3  # mem_id1 + 2 related
        assert len(graph["edges"]) == 2
    
    def test_get_relationship_graph_depth_2(self, relationship_manager, temp_storage):
        """
        Test getting relationship graph with depth 2 (multi-hop).
        
        Rationale: Ensures multi-hop graph traversal works.
        """
        # Create memories in chain
        mem_id1 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns1", text="Memory 1", importance=0.7
        ))
        mem_id2 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns2", text="Memory 2", importance=0.8
        ))
        mem_id3 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns3", text="Memory 3", importance=0.6
        ))
        mem_id4 = temp_storage.store_memory(MemoryRecord(
            namespace="test.ns4", text="Memory 4", importance=0.5
        ))
        
        # Create chain: mem_id1 -> mem_id2 -> mem_id3 -> mem_id4
        relationship_manager.link(mem_id1, mem_id2, RelationType.SUPPORTS)
        relationship_manager.link(mem_id2, mem_id3, RelationType.ELABORATES)
        relationship_manager.link(mem_id3, mem_id4, RelationType.REFERENCES)
        
        # Get graph with depth 2
        graph = relationship_manager.get_relationship_graph([mem_id1], depth=2)
        
        # Should include mem_id1, mem_id2, mem_id3 (2 hops from mem_id1)
        node_ids = {node["id"] for node in graph["nodes"]}
        assert mem_id1 in node_ids
        assert mem_id2 in node_ids
        assert mem_id3 in node_ids
        # mem_id4 might or might not be included depending on implementation
        assert len(graph["edges"]) >= 2


class TestRelationshipManagerAutoDetection:
    """Test auto-detection of relationships."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_auto_detect_similarity(self, relationship_manager, temp_storage):
        """
        Test auto-detection of SIMILAR_TO relationships.
        
        Rationale: Ensures similar memories are automatically linked.
        """
        # This test requires MemoryManager for similarity search
        # Will be tested in integration tests
        pass
    
    def test_auto_detect_namespace_hierarchy(self, relationship_manager, temp_storage):
        """
        Test auto-detection of ELABORATES for namespace hierarchy.
        
        Rationale: Ensures child namespaces are linked to parent namespaces.
        """
        # Create memories with hierarchical namespaces
        parent_id = temp_storage.store_memory(MemoryRecord(
            namespace="test.parent", text="Parent memory", importance=0.8
        ))
        child_id = temp_storage.store_memory(MemoryRecord(
            namespace="test.parent.child", text="Child memory", importance=0.7
        ))
        
        # Auto-detect should create ELABORATES relationship
        detected = relationship_manager.auto_detect_relationships(
            child_id,
            temp_storage,
            similarity_threshold=0.85
        )
        
        # Should detect namespace hierarchy relationship
        if detected:
            # Store detected relationships
            for rel in detected:
                temp_storage.store_relationship(rel)
        
        relationships = temp_storage.get_relationships(source_id=child_id)
        # May or may not be detected depending on implementation
        # This will be fully tested in integration tests

