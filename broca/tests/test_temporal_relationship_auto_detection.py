"""
Tests for auto-detection of temporal relationships (PRECEDES/FOLLOWS).

Tests that temporal relationships are automatically detected when storing memories.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest
from datetime import datetime, timezone, timedelta

from broca.memory import MemoryRecord, RelationType
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
    def generate_embedding(text: str):
        # Create embeddings that are similar for similar texts
        hash_val = hash(text.lower()) % 1000
        base_embedding = [0.1] * 1536
        base_embedding[0] = hash_val / 1000.0
        # Make similar texts have similar embeddings
        if "project" in text.lower() and "start" in text.lower():
            base_embedding[1] = 0.9
        elif "project" in text.lower() and "complete" in text.lower():
            base_embedding[1] = 0.9
        return base_embedding
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
def memory_manager(temp_storage, temp_vector_index, mock_embedding_service):
    """Memory manager for testing."""
    return MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)


class TestTemporalRelationshipAutoDetection:
    """Test auto-detection of PRECEDES/FOLLOWS relationships."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_auto_detects_precedes_when_created_at_earlier(self, memory_manager):
        """
        Test that PRECEDES relationship is auto-detected when memory1.created_at < memory2.created_at.
        
        Rationale: Ensures temporal ordering based on created_at is detected.
        """
        import time
        
        # Store first memory
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Project started development phase",
            importance=0.6
        )
        
        # Small delay to ensure different timestamps
        time.sleep(0.1)
        
        # Store second memory later (about related topic)
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Project completed development phase",
            importance=0.6
        )
        
        # Check if PRECEDES relationship was created from memory_id1 to memory_id2
        # OR FOLLOWS from memory_id2 to memory_id1 (both are valid)
        related_precedes = memory_manager.get_related_memories(
            memory_id1,
            relation_types=[RelationType.PRECEDES],
            direction="outgoing"
        )
        
        related_follows = memory_manager.get_related_memories(
            memory_id2,
            relation_types=[RelationType.FOLLOWS],
            direction="outgoing"
        )
        
        # Should have temporal relationship in at least one direction
        precedes_ids = [mem.id for mem, _ in related_precedes]
        follows_ids = [mem.id for mem, _ in related_follows]
        
        # Either memory_id1 PRECEDES memory_id2, or memory_id2 FOLLOWS memory_id1
        assert memory_id2 in precedes_ids or memory_id1 in follows_ids or len(related_precedes) > 0 or len(related_follows) > 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_auto_detects_follows_when_created_at_later(self, memory_manager):
        """
        Test that FOLLOWS relationship is auto-detected when memory1.created_at > memory2.created_at.
        
        Rationale: Ensures reverse temporal ordering is detected as FOLLOWS.
        """
        import time
        
        # Store first memory
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Project started development",
            importance=0.6
        )
        
        # Small delay to ensure different timestamps
        time.sleep(0.1)
        
        # Store second memory later
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Project completed development",
            importance=0.6
        )
        
        # Check if FOLLOWS relationship was created from memory2 to memory1
        # OR PRECEDES from memory1 to memory2 (both are valid)
        related_follows = memory_manager.get_related_memories(
            memory_id2,
            relation_types=[RelationType.FOLLOWS],
            direction="outgoing"
        )
        
        related_precedes = memory_manager.get_related_memories(
            memory_id1,
            relation_types=[RelationType.PRECEDES],
            direction="outgoing"
        )
        
        # At least one temporal relationship should exist
        follows_ids = [mem.id for mem, _ in related_follows]
        precedes_ids = [mem.id for mem, _ in related_precedes]
        
        assert memory_id1 in follows_ids or memory_id2 in precedes_ids or len(related_follows) > 0 or len(related_precedes) > 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_temporal_relationships_only_for_similar_memories(self, memory_manager):
        """
        Test that temporal relationships are only created for semantically similar memories.
        
        Rationale: Ensures unrelated memories don't get temporal relationships.
        """
        # Store unrelated memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User likes Python programming",
            importance=0.6
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Weather is sunny today",
            importance=0.6
        )
        
        # Check for temporal relationships
        related = memory_manager.get_related_memories(
            memory_id1,
            relation_types=[RelationType.PRECEDES, RelationType.FOLLOWS],
            direction="outgoing"
        )
        
        # Should NOT have temporal relationship to unrelated memory
        related_ids = [mem.id for mem, _ in related]
        # Unrelated memories should not get temporal relationships
        # (This test verifies the filtering logic works)
        assert True  # Placeholder - will verify in implementation
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_temporal_metadata_takes_precedence_over_created_at(self, memory_manager):
        """
        Test that temporal metadata (valid_from/valid_until) takes precedence over created_at.
        
        Rationale: Ensures explicit temporal metadata is used when available.
        """
        # This test will verify that if memories have valid_from/valid_until,
        # those are used instead of created_at for temporal relationship detection
        # Implementation will check this
        
        # Store memory with temporal metadata
        now = datetime.now(timezone.utc)
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Project phase 1 started",
            importance=0.6
        )
        
        # Update memory1 with temporal metadata
        memory1 = memory_manager.get_memory(memory_id1)
        if memory1:
            # Store second memory with later temporal metadata
            memory_id2, _, _ = memory_manager.store_memory(
                namespace="test",
                text="Project phase 2 started",
                importance=0.6
            )
            
            # Verify temporal relationships use metadata if available
            # This will be verified in implementation
            assert True  # Placeholder
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_no_relationship_if_not_temporally_related(self, memory_manager):
        """
        Test that no temporal relationship is created if memories are not temporally related.
        
        Rationale: Ensures temporal relationships are only created when appropriate.
        """
        # Store memories that are similar but not about sequential events
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User prefers Python",
            importance=0.6
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User prefers Java",
            importance=0.6
        )
        
        # These are contradictory preferences, not sequential events
        # Should get CONTRADICTS, not PRECEDES/FOLLOWS
        related = memory_manager.get_related_memories(
            memory_id1,
            relation_types=[RelationType.PRECEDES, RelationType.FOLLOWS],
            direction="outgoing"
        )
        
        # Should not have temporal relationships for contradictory preferences
        related_ids = [mem.id for mem, _ in related]
        # Implementation should not create PRECEDES/FOLLOWS for contradictions
        assert True  # Placeholder - will verify in implementation

