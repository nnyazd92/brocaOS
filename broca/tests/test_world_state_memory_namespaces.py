"""
Tests for memory namespace hierarchy in world state.

Tests that memory namespace hierarchy is included in world state aggregation.
"""

from __future__ import annotations

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from broca.world_state.aggregator import WorldStateAggregator
from broca.memory import MemoryRecord
from broca.memory.storage import MemoryStorage
from broca.memory.namespace_index import NamespaceIndexGenerator
from broca.memory.manager import MemoryManager
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService


class TestNamespaceIndexGeneratorGetHierarchy:
    """Test get_namespace_hierarchy() method in NamespaceIndexGenerator."""
    
    def test_get_namespace_hierarchy_returns_tree_structure(self):
        """
        Test that get_namespace_hierarchy() returns the correct tree structure.
        
        Rationale: Ensures the method returns the namespace tree as a data structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store memories with different namespaces
            record1 = MemoryRecord(
                namespace="memory.system.analysis",
                text="Analysis memory",
                importance=0.8
            )
            record2 = MemoryRecord(
                namespace="memory.system.test",
                text="Test memory",
                importance=0.7
            )
            record3 = MemoryRecord(
                namespace="system.exploration",
                text="Exploration memory",
                importance=0.9
            )
            
            storage.store_memory(record1, [0.1] * 1536)
            storage.store_memory(record2, [0.2] * 1536)
            storage.store_memory(record3, [0.3] * 1536)
            
            generator = NamespaceIndexGenerator(storage)
            
            # Get hierarchy
            hierarchy = generator.get_namespace_hierarchy()
            
            # Verify structure
            assert isinstance(hierarchy, dict)
            assert "memory" in hierarchy
            assert "system" in hierarchy
            assert hierarchy["memory"]["children"]["system"]["children"]["analysis"]["is_leaf"] is True
            assert hierarchy["memory"]["children"]["system"]["children"]["test"]["is_leaf"] is True
            assert hierarchy["system"]["children"]["exploration"]["is_leaf"] is True
    
    def test_get_namespace_hierarchy_empty_when_no_namespaces(self):
        """
        Test that get_namespace_hierarchy() returns empty dict when no namespaces exist.
        
        Rationale: Ensures graceful handling of empty namespace list.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            generator = NamespaceIndexGenerator(storage)
            hierarchy = generator.get_namespace_hierarchy()
            
            assert isinstance(hierarchy, dict)
            assert len(hierarchy) == 0


class TestWorldStateAggregatorMemoryNamespaces:
    """Test that WorldStateAggregator includes memory namespace hierarchy."""
    
    def test_aggregator_includes_memory_hierarchy_when_manager_provided(self):
        """
        Test that WorldStateAggregator includes memory namespace hierarchy.
        
        Rationale: Ensures memory namespace hierarchy is included in world state.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store memories with namespaces
            record1 = MemoryRecord(
                namespace="memory.system.analysis",
                text="Analysis memory",
                importance=0.8
            )
            record2 = MemoryRecord(
                namespace="user.preferences",
                text="User preferences",
                importance=0.9
            )
            
            storage.store_memory(record1, [0.1] * 1536)
            storage.store_memory(record2, [0.2] * 1536)
            
            # Create memory manager
            vector_index = VectorIndex(dimension=1536, index_path=os.path.join(tmpdir, "test.index"))
            embedding_service = EmbeddingService()
            memory_manager = MemoryManager(storage, vector_index, embedding_service)
            
            # Create aggregator with memory manager
            aggregator = WorldStateAggregator(memory_manager=memory_manager)
            
            # Aggregate world state
            world_state = aggregator.aggregate()
            
            # Verify memory section exists
            assert "memory" in world_state
            assert "namespace_hierarchy" in world_state["memory"]
            
            # Verify hierarchy structure
            hierarchy = world_state["memory"]["namespace_hierarchy"]
            assert isinstance(hierarchy, dict)
            assert "memory" in hierarchy
            assert "user" in hierarchy
    
    def test_aggregator_works_without_memory_manager(self):
        """
        Test that WorldStateAggregator works when memory_manager is not provided.
        
        Rationale: Ensures backward compatibility when memory_manager is None.
        """
        aggregator = WorldStateAggregator(memory_manager=None)
        
        world_state = aggregator.aggregate()
        
        # Should not include memory section
        assert "memory" not in world_state
        
        # Should still include other sections
        assert "system" in world_state
        assert "timestamp" in world_state
    
    def test_get_memory_namespace_hierarchy_returns_correct_structure(self):
        """
        Test that get_memory_namespace_hierarchy() returns correct structure.
        
        Rationale: Ensures the method returns the namespace hierarchy correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store memories
            record = MemoryRecord(
                namespace="test.namespace.example",
                text="Example memory",
                importance=0.8
            )
            storage.store_memory(record, [0.1] * 1536)
            
            # Create memory manager
            vector_index = VectorIndex(dimension=1536, index_path=os.path.join(tmpdir, "test.index"))
            embedding_service = EmbeddingService()
            memory_manager = MemoryManager(storage, vector_index, embedding_service)
            
            aggregator = WorldStateAggregator(memory_manager=memory_manager)
            
            # Get hierarchy
            hierarchy = aggregator.get_memory_namespace_hierarchy()
            
            # Verify structure
            assert hierarchy.get("available") is True
            assert "namespace_hierarchy" in hierarchy
            assert "test" in hierarchy["namespace_hierarchy"]
            assert hierarchy["namespace_hierarchy"]["test"]["children"]["namespace"]["children"]["example"]["is_leaf"] is True
    
    def test_get_memory_namespace_hierarchy_handles_missing_manager(self):
        """
        Test that get_memory_namespace_hierarchy() handles missing memory_manager.
        
        Rationale: Ensures graceful handling when memory_manager is None.
        """
        aggregator = WorldStateAggregator(memory_manager=None)
        
        hierarchy = aggregator.get_memory_namespace_hierarchy()
        
        assert hierarchy.get("available") is False
    
    def test_get_memory_namespace_hierarchy_handles_errors(self):
        """
        Test that get_memory_namespace_hierarchy() handles errors gracefully.
        
        Rationale: Ensures errors don't break world state aggregation.
        """
        # Create a mock memory manager that raises an error
        mock_memory_manager = Mock()
        mock_memory_manager.namespace_index = Mock()
        mock_memory_manager.namespace_index.get_namespace_hierarchy.side_effect = Exception("Test error")
        
        aggregator = WorldStateAggregator(memory_manager=mock_memory_manager)
        
        hierarchy = aggregator.get_memory_namespace_hierarchy()
        
        assert hierarchy.get("available") is False
        assert "error" in hierarchy


class TestWorldStateMemorySection:
    """Test that world state includes memory section correctly."""
    
    def test_world_state_includes_memory_section_structure(self):
        """
        Test that world state includes memory section with correct structure.
        
        Rationale: Ensures memory section has the expected format.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store memories
            record = MemoryRecord(
                namespace="example.namespace",
                text="Example",
                importance=0.8
            )
            storage.store_memory(record, [0.1] * 1536)
            
            # Create memory manager
            vector_index = VectorIndex(dimension=1536, index_path=os.path.join(tmpdir, "test.index"))
            embedding_service = EmbeddingService()
            memory_manager = MemoryManager(storage, vector_index, embedding_service)
            
            aggregator = WorldStateAggregator(memory_manager=memory_manager)
            world_state = aggregator.aggregate()
            
            # Verify memory section structure
            assert "memory" in world_state
            memory_section = world_state["memory"]
            assert "namespace_hierarchy" in memory_section
            assert isinstance(memory_section["namespace_hierarchy"], dict)
    
    def test_world_state_memory_section_matches_namespace_tree(self):
        """
        Test that world state memory section matches the namespace tree structure.
        
        Rationale: Ensures the hierarchy in world state matches what NamespaceIndexGenerator produces.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store memories with specific namespaces
            namespaces = [
                "memory.system.analysis",
                "memory.system.test",
                "user.preferences"
            ]
            
            for i, namespace in enumerate(namespaces):
                record = MemoryRecord(
                    namespace=namespace,
                    text=f"Memory {i}",
                    importance=0.8
                )
                storage.store_memory(record, [float(i)] * 1536)
            
            # Create memory manager
            vector_index = VectorIndex(dimension=1536, index_path=os.path.join(tmpdir, "test.index"))
            embedding_service = EmbeddingService()
            memory_manager = MemoryManager(storage, vector_index, embedding_service)
            
            aggregator = WorldStateAggregator(memory_manager=memory_manager)
            world_state = aggregator.aggregate()
            
            # Verify hierarchy contains expected namespaces
            hierarchy = world_state["memory"]["namespace_hierarchy"]
            assert "memory" in hierarchy
            assert "user" in hierarchy
            assert "system" in hierarchy["memory"]["children"]
            assert "analysis" in hierarchy["memory"]["children"]["system"]["children"]
            assert "test" in hierarchy["memory"]["children"]["system"]["children"]

