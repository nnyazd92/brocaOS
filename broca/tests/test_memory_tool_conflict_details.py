"""
Tests for conflict details in StoreMemoryTool results.

Tests that StoreMemoryTool returns actual conflict details instead of just
a boolean flag when conflict_check is enabled.
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
        manager.close()


class TestConflictDetailsInToolResult:
    """Test that StoreMemoryTool returns conflict details."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_conflict_details_returned_when_conflicts_detected(self, memory_manager):
        """
        Test that conflict details are returned when conflicts are detected.
        
        Rationale: Ensures tool returns actual conflict information, not just a flag.
        """
        tool = StoreMemoryTool(memory_manager)
        
        # Store first memory
        result1 = tool.execute(
            namespace="test.namespace",
            text="User prefers Python programming",
            importance=0.7
        )
        assert result1["success"] is True
        memory_id1 = result1["memory_id"]
        
        # Store conflicting memory with conflict_check
        result2 = tool.execute(
            namespace="test.namespace",
            text="User hates Python programming",
            importance=0.7,
            conflict_check=True
        )
        
        assert result2["success"] is True
        assert "conflicts" in result2 or "conflicts_detected" in result2
        assert "conflict_count" in result2
        
        # Verify conflict details structure
        if "conflicts" in result2:
            conflicts = result2["conflicts"]
            assert isinstance(conflicts, list)
            if len(conflicts) > 0:
                conflict = conflicts[0]
                assert "conflict_type" in conflict
                assert "confidence" in conflict
                assert "evidence" in conflict
                assert "memory1_id" in conflict or "memory2_id" in conflict
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_no_conflicts_when_none_detected(self, memory_manager):
        """
        Test that empty conflict list is returned when no conflicts detected.
        
        Rationale: Ensures tool returns empty list when conflict_check=True but no conflicts.
        """
        tool = StoreMemoryTool(memory_manager)
        
        # Store first memory
        tool.execute(
            namespace="test.namespace",
            text="User likes apples",
            importance=0.7
        )
        
        # Store non-conflicting memory with conflict_check
        result = tool.execute(
            namespace="test.namespace",
            text="User likes oranges",
            importance=0.7,
            conflict_check=True
        )
        
        assert result["success"] is True
        assert "conflict_count" in result
        assert result["conflict_count"] == 0
        assert "conflicts" in result or "conflicts_detected" in result
        
        # Conflicts list should be empty
        conflicts = result.get("conflicts") or result.get("conflicts_detected", [])
        assert isinstance(conflicts, list)
        assert len(conflicts) == 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_no_conflict_info_when_conflict_check_false(self, memory_manager):
        """
        Test that conflict info is not returned when conflict_check=False.
        
        Rationale: Ensures backward compatibility - no conflict info when not requested.
        """
        tool = StoreMemoryTool(memory_manager)
        
        # Store memory without conflict_check
        result = tool.execute(
            namespace="test.namespace",
            text="User likes Python",
            importance=0.7,
            conflict_check=False
        )
        
        assert result["success"] is True
        # Should not have conflict_check_performed or conflicts
        assert "conflict_check_performed" not in result
        assert "conflicts" not in result
        assert "conflict_count" not in result
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_conflict_details_structure(self, memory_manager):
        """
        Test that conflict details have correct structure.
        
        Rationale: Ensures conflict details include all necessary information.
        """
        tool = StoreMemoryTool(memory_manager)
        
        # Store first memory
        result1 = tool.execute(
            namespace="test.namespace",
            text="User is 25 years old",
            importance=0.8
        )
        memory_id1 = result1["memory_id"]
        
        # Store conflicting memory
        result2 = tool.execute(
            namespace="test.namespace",
            text="User is 30 years old",
            importance=0.8,
            conflict_check=True
        )
        memory_id2 = result2["memory_id"]
        
        # Check conflict details structure
        if result2.get("conflict_count", 0) > 0:
            conflicts = result2.get("conflicts") or result2.get("conflicts_detected", [])
            assert len(conflicts) > 0
            
            conflict = conflicts[0]
            # Should have conflict type
            assert "conflict_type" in conflict
            assert conflict["conflict_type"] in ["contradiction", "ambiguity", "update"]
            
            # Should have confidence
            assert "confidence" in conflict
            assert isinstance(conflict["confidence"], (int, float))
            assert 0.0 <= conflict["confidence"] <= 1.0
            
            # Should have evidence
            assert "evidence" in conflict
            assert isinstance(conflict["evidence"], str)
            assert len(conflict["evidence"]) > 0
            
            # Should have memory IDs (not full objects)
            assert "memory1_id" in conflict or "memory2_id" in conflict
            # At least one memory ID should match one of the stored memories
            if "memory1_id" in conflict:
                assert conflict["memory1_id"] in [memory_id1, memory_id2]
            if "memory2_id" in conflict:
                assert conflict["memory2_id"] in [memory_id1, memory_id2]
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_backward_compatibility_no_conflict_check(self, memory_manager):
        """
        Test that existing behavior is unchanged when conflict_check is not used.
        
        Rationale: Ensures backward compatibility for code not using conflict checking.
        """
        tool = StoreMemoryTool(memory_manager)
        
        # Store memory without conflict_check (default behavior)
        result = tool.execute(
            namespace="test.namespace",
            text="Test memory",
            importance=0.5
        )
        
        # Should have standard fields
        assert result["success"] is True
        assert "memory_id" in result
        assert "was_duplicate" in result
        assert "message" in result
        
        # Should not have conflict fields
        assert "conflict_check_performed" not in result
        assert "conflicts" not in result
        assert "conflict_count" not in result
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_multiple_conflicts_returned(self, memory_manager):
        """
        Test that multiple conflicts are returned when multiple conflicts detected.
        
        Rationale: Ensures tool handles multiple conflicts correctly.
        """
        tool = StoreMemoryTool(memory_manager)
        
        # Store multiple conflicting memories
        tool.execute(
            namespace="test.namespace",
            text="User prefers Python",
            importance=0.7
        )
        
        tool.execute(
            namespace="test.namespace",
            text="User prefers Java",
            importance=0.7
        )
        
        # Store memory that conflicts with both
        result = tool.execute(
            namespace="test.namespace",
            text="User hates programming",
            importance=0.7,
            conflict_check=True
        )
        
        assert result["success"] is True
        assert "conflict_count" in result
        conflicts = result.get("conflicts") or result.get("conflicts_detected", [])
        assert isinstance(conflicts, list)
        # May have multiple conflicts
        assert len(conflicts) == result["conflict_count"]

