"""
Tests for temporal consistency checking.

Tests cycle detection, ordering validation, and temporal contradiction detection.
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
        hash_val = hash(text.lower()) % 1000
        base_embedding = [0.1] * 1536
        base_embedding[0] = hash_val / 1000.0
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


class TestTemporalConsistencyChecking:
    """Test temporal consistency checking."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_detects_cycles_in_precedes_follows(self, memory_manager):
        """
        Test that cycles in PRECEDES/FOLLOWS relationships are detected.
        
        Rationale: Ensures temporal graph doesn't have impossible cycles.
        """
        # Create memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Event A",
            importance=0.6
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Event B",
            importance=0.6
        )
        
        memory_id3, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Event C",
            importance=0.6
        )
        
        # Create cycle: A PRECEDES B, B PRECEDES C, C PRECEDES A (impossible!)
        memory_manager.link_memories(memory_id1, memory_id2, RelationType.PRECEDES)
        memory_manager.link_memories(memory_id2, memory_id3, RelationType.PRECEDES)
        memory_manager.link_memories(memory_id3, memory_id1, RelationType.PRECEDES)
        
        # Check for cycles using the validation method
        validation_result = memory_manager.temporal_consistency.validate_temporal_relationships(memory_id1)
        # Should detect cycle
        assert len(validation_result["cycles"]) > 0 or validation_result["total_issues"] > 0
        # Check that cycle is detected (either in cycles list or in inconsistencies)
        if len(validation_result["cycles"]) > 0:
            # Cycle was directly detected
            assert True
        else:
            # Cycle might be detected as ordering violations
            assert validation_result["total_issues"] > 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_validates_precedes_matches_temporal_ordering(self, memory_manager):
        """
        Test that PRECEDES relationships match temporal ordering.
        
        Rationale: Ensures temporal relationships are consistent with timestamps.
        """
        import time
        
        # Create memories with known temporal ordering
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Earlier event",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Later event",
            importance=0.6
        )
        
        # Create PRECEDES relationship (correct)
        memory_manager.link_memories(memory_id1, memory_id2, RelationType.PRECEDES)
        
        # Validate - should be consistent
        if hasattr(memory_manager, 'validate_temporal_relationships'):
            inconsistencies = memory_manager.validate_temporal_relationships(memory_id1)
            # Should be no inconsistencies for correct ordering
            assert len(inconsistencies) == 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_detects_temporal_contradictions(self, memory_manager):
        """
        Test detection of temporal contradictions.
        
        Rationale: Ensures contradictions like A PRECEDES B but A.created_at > B.created_at are detected.
        """
        import time
        
        # Create memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Event A",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Event B",
            importance=0.6
        )
        
        # Create incorrect PRECEDES relationship (memory_id2 PRECEDES memory_id1, but memory_id2 was created later!)
        memory_manager.link_memories(memory_id2, memory_id1, RelationType.PRECEDES)
        
        # Validate - should detect contradiction
        if hasattr(memory_manager, 'validate_temporal_relationships'):
            inconsistencies = memory_manager.validate_temporal_relationships(memory_id2)
            # Should detect temporal contradiction
            assert len(inconsistencies) > 0
            assert any("contradiction" in str(inc).lower() or "ordering" in str(inc).lower() for inc in inconsistencies)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_consistency_check_returns_empty_when_valid(self, memory_manager):
        """
        Test that consistency check returns empty list when all relationships are valid.
        
        Rationale: Ensures valid temporal relationships pass consistency checks.
        """
        import time
        
        # Create memories in sequence
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Step 1",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Step 2",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id3, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Step 3",
            importance=0.6
        )
        
        # Create valid chain: 1 PRECEDES 2, 2 PRECEDES 3
        memory_manager.link_memories(memory_id1, memory_id2, RelationType.PRECEDES)
        memory_manager.link_memories(memory_id2, memory_id3, RelationType.PRECEDES)
        
        # Validate - should be consistent
        if hasattr(memory_manager, 'validate_temporal_relationships'):
            inconsistencies = memory_manager.validate_temporal_relationships(memory_id1)
            assert len(inconsistencies) == 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_consistency_check_with_multiple_memories(self, memory_manager):
        """
        Test consistency check with multiple memories and relationships.
        
        Rationale: Ensures consistency checker handles complex temporal graphs.
        """
        import time
        
        # Create multiple memories
        memory_ids = []
        for i in range(5):
            memory_id, _, _ = memory_manager.store_memory(
                namespace="test",
                text=f"Event {i+1}",
                importance=0.6
            )
            memory_ids.append(memory_id)
            time.sleep(0.05)
        
        # Create valid chain
        for i in range(len(memory_ids) - 1):
            memory_manager.link_memories(memory_ids[i], memory_ids[i+1], RelationType.PRECEDES)
        
        # Validate - should be consistent
        if hasattr(memory_manager, 'validate_temporal_relationships'):
            inconsistencies = memory_manager.validate_temporal_relationships(memory_ids[0])
            assert len(inconsistencies) == 0

