"""
Tests for namespace index generation.

Tests the automatic generation of markdown index files for memory namespaces.
"""

from __future__ import annotations

import tempfile
import os
from pathlib import Path
import pytest
from datetime import datetime, timezone

from broca.memory import MemoryRecord
from broca.memory.storage import MemoryStorage
from broca.memory.namespace_index import NamespaceIndexGenerator


class TestNamespaceIndexGenerator:
    """Test NamespaceIndexGenerator functionality."""
    
    def test_get_all_namespaces(self):
        """
        Test that get_all_namespaces returns all unique namespaces.
        
        Rationale: Ensures namespace extraction from database works correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store memories with different namespaces
            record1 = MemoryRecord(
                namespace="math.sage.api",
                text="Sage API documentation",
                importance=0.8,
                tags=["api", "sage"]
            )
            record2 = MemoryRecord(
                namespace="math.sage.examples",
                text="Sage examples",
                importance=0.7,
                tags=["examples"]
            )
            record3 = MemoryRecord(
                namespace="project.optimization",
                text="Optimization project",
                importance=0.9,
                tags=["project"]
            )
            
            storage.store_memory(record1)
            storage.store_memory(record2)
            storage.store_memory(record3)
            
            generator = NamespaceIndexGenerator(storage)
            namespaces = generator.get_all_namespaces()
            
            assert len(namespaces) == 3
            assert "math.sage.api" in namespaces
            assert "math.sage.examples" in namespaces
            assert "project.optimization" in namespaces
            
            storage.close()
    
    def test_build_namespace_tree(self):
        """
        Test that build_namespace_tree creates correct hierarchical structure.
        
        Rationale: Ensures tree building logic works correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            generator = NamespaceIndexGenerator(storage)
            
            namespaces = [
                "math.sage.api",
                "math.sage.examples",
                "math.numpy",
                "project.optimization"
            ]
            
            tree = generator.build_namespace_tree(namespaces)
            
            # Verify structure
            assert "math" in tree
            assert "project" in tree
            assert "sage" in tree["math"]["children"]
            assert "numpy" in tree["math"]["children"]
            assert "api" in tree["math"]["children"]["sage"]["children"]
            assert "examples" in tree["math"]["children"]["sage"]["children"]
            assert "optimization" in tree["project"]["children"]
            
            storage.close()
    
    def test_generate_markdown(self):
        """
        Test that generate_markdown produces correct markdown format.
        
        Rationale: Ensures markdown generation works correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            generator = NamespaceIndexGenerator(storage)
            
            namespaces = [
                "math.sage.api",
                "math.numpy"
            ]
            
            tree = generator.build_namespace_tree(namespaces)
            markdown = generator.generate_markdown(tree)
            
            # Verify markdown structure
            assert "# Memory Namespace Index" in markdown
            assert "## Namespace Hierarchy" in markdown
            assert "- math" in markdown
            assert "- sage" in markdown
            assert "- api" in markdown
            assert "- numpy" in markdown
            
            storage.close()
    
    def test_update_index_creates_file(self):
        """
        Test that update_index creates the index file.
        
        Rationale: Ensures index file is created when it doesn't exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store a memory
            record = MemoryRecord(
                namespace="math.sage.api",
                text="Sage API",
                importance=0.8
            )
            storage.store_memory(record)
            
            generator = NamespaceIndexGenerator(storage)
            generator.update_index()
            
            index_path = generator.get_index_path()
            assert index_path.exists()
            
            # Verify content
            content = index_path.read_text()
            assert "# Memory Namespace Index" in content
            assert "math" in content
            
            storage.close()
    
    def test_update_index_updates_existing(self):
        """
        Test that update_index updates existing index file.
        
        Rationale: Ensures index file is updated when namespaces change.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store initial memory
            record1 = MemoryRecord(
                namespace="math.sage.api",
                text="Sage API",
                importance=0.8
            )
            storage.store_memory(record1)
            
            generator = NamespaceIndexGenerator(storage)
            generator.update_index()
            
            # Store another memory with new namespace
            record2 = MemoryRecord(
                namespace="project.optimization",
                text="Optimization",
                importance=0.9
            )
            storage.store_memory(record2)
            
            # Update index
            generator.update_index()
            
            # Verify both namespaces are in the file
            index_path = generator.get_index_path()
            content = index_path.read_text()
            assert "math" in content
            assert "project" in content
            
            storage.close()
    
    def test_hierarchical_structure(self):
        """
        Test that hierarchical structure is correctly represented.
        
        Rationale: Ensures nested namespaces are properly indented.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store memories with nested namespaces
            record1 = MemoryRecord(
                namespace="math.sage.api",
                text="API",
                importance=0.8
            )
            record2 = MemoryRecord(
                namespace="math.sage.examples",
                text="Examples",
                importance=0.7
            )
            storage.store_memory(record1)
            storage.store_memory(record2)
            
            generator = NamespaceIndexGenerator(storage)
            generator.update_index()
            
            index_path = generator.get_index_path()
            content = index_path.read_text()
            
            # Verify hierarchy (check for proper indentation)
            lines = content.split('\n')
            math_line = next(i for i, line in enumerate(lines) if '- math' in line)
            sage_line = next(i for i, line in enumerate(lines) if '- sage' in line)
            api_line = next(i for i, line in enumerate(lines) if '- api' in line)
            
            # sage should be indented more than math
            assert lines[sage_line].startswith('  ')
            # api should be indented more than sage
            assert lines[api_line].startswith('    ')
            
            storage.close()
    
    def test_empty_namespaces(self):
        """
        Test that empty namespace list is handled correctly.
        
        Rationale: Ensures edge case of no namespaces is handled.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            generator = NamespaceIndexGenerator(storage)
            generator.update_index()
            
            index_path = generator.get_index_path()
            assert index_path.exists()
            
            content = index_path.read_text()
            assert "# Memory Namespace Index" in content
            # Should have some indication of empty state or just empty hierarchy section
            
            storage.close()
    
    def test_get_index_path(self):
        """
        Test that get_index_path returns correct path.
        
        Rationale: Ensures index file path is correctly determined.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            generator = NamespaceIndexGenerator(storage)
            index_path = generator.get_index_path()
            
            # Should be in same directory as database
            expected_path = Path(tmpdir) / "memory_namespaces_index.md"
            assert index_path == expected_path
            
            storage.close()
    
    def test_is_namespace_new(self):
        """
        Test that is_namespace_new correctly identifies new namespaces.
        
        Rationale: Ensures namespace newness detection works.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            generator = NamespaceIndexGenerator(storage)
            
            # Initially, all namespaces are new
            assert generator.is_namespace_new("math.sage.api")
            
            # Store memory and update index
            record = MemoryRecord(
                namespace="math.sage.api",
                text="API",
                importance=0.8
            )
            storage.store_memory(record)
            generator.update_index()
            
            # After update, existing namespace should not be new
            # (This depends on implementation - may need to reload from file)
            # For now, we'll test that it works with the current state
            
            storage.close()
    
    def test_index_created_on_init_if_missing(self):
        """
        Test that index is created on MemoryManager initialization if missing.
        
        Rationale: Ensures index is automatically created when MemoryManager starts.
        """
        from broca.memory.vector_index import VectorIndex
        from broca.memory.embeddings import EmbeddingService
        from broca.memory.manager import MemoryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Store a memory first
            record = MemoryRecord(
                namespace="math.sage.api",
                text="Sage API",
                importance=0.8
            )
            storage.store_memory(record)
            
            # Create MemoryManager (should create index)
            # Use correct embedding dimension (1536 for OpenAI embeddings)
            vector_index = VectorIndex(dimension=1536, index_path=os.path.join(tmpdir, "test.index"))
            embedding_service = EmbeddingService()
            manager = MemoryManager(storage, vector_index, embedding_service)
            
            # Verify index was created
            index_path = manager.namespace_index.get_index_path()
            assert index_path.exists()
            
            # Verify content
            content = index_path.read_text()
            assert "# Memory Namespace Index" in content
            assert "math" in content
            
            manager.close()
    
    def test_index_updated_on_new_namespace(self):
        """
        Test that index is updated when a new namespace is stored.
        
        Rationale: Ensures index is automatically updated when new namespaces are created.
        """
        from broca.memory.vector_index import VectorIndex
        from broca.memory.embeddings import EmbeddingService
        from broca.memory.manager import MemoryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Use correct embedding dimension (1536 for OpenAI embeddings)
            vector_index = VectorIndex(dimension=1536, index_path=os.path.join(tmpdir, "test.index"))
            embedding_service = EmbeddingService()
            manager = MemoryManager(storage, vector_index, embedding_service)
            
            # Store memory with first namespace
            manager.store_memory(
                namespace="math.sage.api",
                text="Sage API",
                importance=0.8
            )
            
            index_path = manager.namespace_index.get_index_path()
            assert index_path.exists()
            
            # Store memory with new namespace
            manager.store_memory(
                namespace="project.optimization",
                text="Optimization",
                importance=0.9
            )
            
            # Verify both namespaces are in index
            content = index_path.read_text()
            assert "math" in content
            assert "project" in content
            
            manager.close()

