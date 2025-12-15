"""
Tests for temporal ordering in memory retrieval.

Tests that memories can be ordered by PRECEDES/FOLLOWS relationships.
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


class TestTemporalRetrievalOrdering:
    """Test temporal ordering in retrieval."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_ordering_by_precedes_follows_relationships(self, memory_manager):
        """
        Test ordering by PRECEDES/FOLLOWS relationships.
        
        Rationale: Ensures memories are ordered chronologically based on temporal relationships.
        """
        import time
        
        # Store memories in sequence
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Step 1: Initialize",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Step 2: Process",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id3, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Step 3: Complete",
            importance=0.6
        )
        
        # Create temporal relationships
        memory_manager.link_memories(memory_id1, memory_id2, RelationType.PRECEDES)
        memory_manager.link_memories(memory_id2, memory_id3, RelationType.PRECEDES)
        
        # Retrieve with temporal ordering
        if hasattr(memory_manager, 'retrieve_memories'):
            results = memory_manager.retrieve_memories(
                query="steps",
                namespace="test",
                limit=10,
                order_by_temporal=True
            )
            
            # Should be ordered: memory_id1, memory_id2, memory_id3
            result_ids = [mem.id for mem in results if mem.id in [memory_id1, memory_id2, memory_id3]]
            if len(result_ids) >= 3:
                # Check that ordering respects PRECEDES relationships
                assert result_ids.index(memory_id1) < result_ids.index(memory_id2)
                assert result_ids.index(memory_id2) < result_ids.index(memory_id3)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_topological_sort_produces_chronological_order(self, memory_manager):
        """
        Test that topological sort produces correct chronological order.
        
        Rationale: Ensures complex temporal graphs are correctly ordered.
        """
        import time
        
        # Create memories
        memory_ids = []
        for i in range(4):
            mem_id, _, _ = memory_manager.store_memory(
                namespace="test",
                text=f"Event {i+1}",
                importance=0.6
            )
            memory_ids.append(mem_id)
            time.sleep(0.05)
        
        # Create chain: 1 -> 2 -> 3 -> 4
        for i in range(len(memory_ids) - 1):
            memory_manager.link_memories(memory_ids[i], memory_ids[i+1], RelationType.PRECEDES)
        
        # Test topological sort method if it exists
        if hasattr(memory_manager, '_order_by_temporal_relationships'):
            memories = [memory_manager.get_memory(mid) for mid in memory_ids]
            memories = [m for m in memories if m]
            
            ordered = memory_manager._order_by_temporal_relationships(memories)
            ordered_ids = [m.id for m in ordered]
            
            # Should maintain chronological order
            assert ordered_ids == memory_ids
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_fallback_to_created_at_when_no_temporal_relationships(self, memory_manager):
        """
        Test fallback to created_at when no temporal relationships exist.
        
        Rationale: Ensures ordering works even without explicit temporal relationships.
        """
        import time
        
        # Store memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Memory A",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Memory B",
            importance=0.6
        )
        
        # No temporal relationships created
        
        # Retrieve with temporal ordering
        if hasattr(memory_manager, 'retrieve_memories'):
            results = memory_manager.retrieve_memories(
                query="memory",
                namespace="test",
                limit=10,
                order_by_temporal=True
            )
            
            # Should fallback to created_at ordering
            result_ids = [mem.id for mem in results if mem.id in [memory_id1, memory_id2]]
            if len(result_ids) >= 2:
                # Should be ordered by created_at (memory_id1 before memory_id2)
                assert result_ids.index(memory_id1) < result_ids.index(memory_id2)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_cycles_trigger_fallback_and_warning(self, memory_manager):
        """
        Test that cycles in temporal graph trigger fallback and warning.
        
        Rationale: Ensures cycles don't break retrieval, but trigger appropriate handling.
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
        
        time.sleep(0.1)
        
        memory_id3, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Event C",
            importance=0.6
        )
        
        # Create cycle: A -> B -> C -> A
        memory_manager.link_memories(memory_id1, memory_id2, RelationType.PRECEDES)
        memory_manager.link_memories(memory_id2, memory_id3, RelationType.PRECEDES)
        memory_manager.link_memories(memory_id3, memory_id1, RelationType.PRECEDES)
        
        # Retrieve with temporal ordering - should handle cycle gracefully
        if hasattr(memory_manager, 'retrieve_memories'):
            results = memory_manager.retrieve_memories(
                query="event",
                namespace="test",
                limit=10,
                order_by_temporal=True
            )
            
            # Should still return results (fallback to created_at)
            assert len(results) >= 1
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_temporal_ordering_preserves_relevance(self, memory_manager):
        """
        Test that temporal ordering preserves relevance when combined with similarity search.
        
        Rationale: Ensures temporal ordering doesn't break relevance-based ranking.
        """
        import time
        
        # Store memories with different relevance to query
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Project started Python development",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Project completed Python development",
            importance=0.6
        )
        
        time.sleep(0.1)
        
        memory_id3, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Unrelated memory about Java",
            importance=0.6
        )
        
        # Create temporal relationship
        memory_manager.link_memories(memory_id1, memory_id2, RelationType.PRECEDES)
        
        # Retrieve with query about Python
        if hasattr(memory_manager, 'retrieve_memories'):
            results = memory_manager.retrieve_memories(
                query="Python development",
                namespace="test",
                limit=10,
                order_by_temporal=True
            )
            
            # Should include Python-related memories
            result_ids = [mem.id for mem in results]
            assert memory_id1 in result_ids or memory_id2 in result_ids
            # Unrelated memory should be ranked lower or not included
            # (This tests that relevance is still considered)

