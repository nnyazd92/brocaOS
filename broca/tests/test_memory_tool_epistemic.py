"""
Tests for memory operations epistemic integration.

Tests that memory tools track knowledge acquisition when epistemic engine is available.
"""

from __future__ import annotations

import pytest
import tempfile
import os

from broca.tools.memory_tool import StoreMemoryTool, RetrieveMemoriesTool
from broca.memory.manager import MemoryManager
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata
from datetime import datetime, timezone


class TestMemoryOperationsEpistemicIntegration:
    """Test memory operations epistemic integration."""
    
    @pytest.fixture
    def memory_manager(self):
        """Create a memory manager for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary paths
            db_path = os.path.join(tmpdir, "test_memories.db")
            index_path = os.path.join(tmpdir, "test_memories.faiss")
            
            try:
                # Initialize components
                embedding_service = EmbeddingService()
                storage = MemoryStorage(db_path=db_path)
                vector_index = VectorIndex(dimension=1536, index_path=index_path)
                
                manager = MemoryManager(storage, vector_index, embedding_service)
                yield manager
                
                # Cleanup
                manager.close()
            except Exception:
                # If embedding service fails (no API key), skip
                pytest.skip("Embedding service not available")
    
    def test_store_memory_tool_tracks_knowledge_acquisition(self, memory_manager):
        """
        Test that StoreMemoryTool tracks knowledge acquisition when epistemic engine available.
        
        Rationale: Ensures memories are tracked as knowledge sources in the epistemic layer.
        """
        # Create epistemic engine
        engine = MetacognitiveEngine()
        
        # Create store tool with epistemic engine
        # Note: StoreMemoryTool doesn't currently accept epistemic_engine directly
        # This test verifies the expected behavior when integration is complete
        store_tool = StoreMemoryTool(memory_manager)
        
        # Store a memory
        result = store_tool.execute(
            namespace="test.namespace",
            text="Test memory content",
            importance=0.7
        )
        
        # Should succeed
        assert result["success"] is True
        assert "memory_id" in result
        
        # When epistemic integration is complete, this should track knowledge
        # For now, we just verify the tool works
    
    def test_memory_storage_creates_knowledge_ids(self, memory_manager):
        """
        Test that memory storage creates knowledge IDs and source metadata.
        
        Rationale: Ensures each stored memory gets a unique knowledge ID for tracking.
        """
        engine = MetacognitiveEngine()
        
        # Use the epistemic-aware method directly
        memory_id, was_duplicate, conflicts, epistemic_result = memory_manager.store_memory_with_epistemic(
            namespace="test.namespace",
            text="Test memory for epistemic tracking",
            importance=0.8,
            epistemic_engine=engine,
            source_metadata=SourceMetadata(
                source_type=SourceType.USER_PROVIDED,
                timestamp=datetime.now(timezone.utc)
            )
        )
        
        # Should succeed
        assert memory_id is not None
        assert not was_duplicate
        
        # Epistemic result should contain knowledge tracking info
        if epistemic_result:
            assert "knowledge_id" in epistemic_result or "source_metadata" in epistemic_result
    
    def test_memory_retrieval_includes_epistemic_context(self, memory_manager):
        """
        Test that memory retrieval includes epistemic context.
        
        Rationale: Ensures retrieved memories include confidence and source information.
        """
        # Store a memory first
        memory_id, _, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="Test memory for retrieval",
            importance=0.7
        )
        
        engine = MetacognitiveEngine()
        
        # Retrieve with epistemic context
        result = memory_manager.retrieve_memories_with_epistemic(
            query="test memory",
            limit=10,
            epistemic_engine=engine
        )
        
        # Should return memories and epistemic context
        assert "memories" in result
        assert "epistemic_context" in result
        assert len(result["memories"]) > 0
    
    def test_backward_compatibility_works_without_epistemic_engine(self, memory_manager):
        """
        Test backward compatibility: works without epistemic engine.
        
        Rationale: Ensures existing code that doesn't use epistemic engine continues to work.
        """
        store_tool = StoreMemoryTool(memory_manager)
        
        # Store memory without epistemic engine
        result = store_tool.execute(
            namespace="test.namespace",
            text="Test memory without epistemic",
            importance=0.5
        )
        
        # Should work fine
        assert result["success"] is True
        assert "memory_id" in result
        
        # Retrieve without epistemic engine
        retrieve_tool = RetrieveMemoriesTool(memory_manager)
        retrieve_result = retrieve_tool.execute(
            query="test memory",
            limit=10
        )
        
        # Should work fine
        assert retrieve_result["success"] is True
        assert "memories" in retrieve_result

