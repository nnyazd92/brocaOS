"""
Tests for advanced memory search features.

Tests cross-namespace search, date range filtering, importance filters, and combined filters.
"""

from __future__ import annotations

import tempfile
import os
from pathlib import Path
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from broca.memory import MemoryRecord
from broca.memory.storage import MemoryStorage
from broca.memory.manager import MemoryManager
from broca.memory.embeddings import EmbeddingService
from broca.memory.vector_index import VectorIndex
from broca.tools.memory_tool import RetrieveMemoriesTool


class TestCrossNamespaceSearch:
    """Test cross-namespace search functionality."""
    
    def test_retrieve_memories_with_multiple_namespaces(self):
        """
        Test that retrieve_memories can search across multiple namespaces.
        
        Rationale: Ensures cross-namespace search returns memories from any of the specified namespaces.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Create mock embedding service and vector index
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store memories in different namespaces
            manager.store_memory(
                namespace="math.sage",
                text="SageMath is a Python library",
                importance=0.7,
                tags=["math"]
            )
            manager.store_memory(
                namespace="python.api",
                text="Python has many APIs",
                importance=0.6,
                tags=["python"]
            )
            manager.store_memory(
                namespace="other",
                text="This should not be included",
                importance=0.5,
                tags=["other"]
            )
            
            # Search across multiple namespaces
            results = manager.retrieve_memories(
                query="library API",
                namespaces=["math.sage", "python.api"],
                limit=10
            )
            
            # Should find memories from both namespaces
            result_namespaces = {mem.namespace for mem in results}
            assert "math.sage" in result_namespaces
            assert "python.api" in result_namespaces
            assert "other" not in result_namespaces
            
            storage.close()
    
    def test_retrieve_memories_namespace_backward_compatibility(self):
        """
        Test that single namespace parameter still works (backward compatibility).
        
        Rationale: Ensures existing code using single namespace doesn't break.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            manager.store_memory(
                namespace="math.sage",
                text="SageMath library",
                importance=0.7
            )
            manager.store_memory(
                namespace="python.api",
                text="Python API",
                importance=0.6
            )
            
            # Single namespace should still work
            results = manager.retrieve_memories(
                query="library",
                namespace="math.sage",
                limit=10
            )
            
            assert len(results) > 0
            assert all(mem.namespace == "math.sage" for mem in results)
            
            storage.close()
    
    def test_retrieve_memories_prefers_namespaces_over_namespace(self):
        """
        Test that namespaces parameter takes precedence over namespace parameter.
        
        Rationale: If both are provided, namespaces (plural) should be used.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            manager.store_memory(
                namespace="math.sage",
                text="SageMath",
                importance=0.7
            )
            manager.store_memory(
                namespace="python.api",
                text="Python API",
                importance=0.6
            )
            manager.store_memory(
                namespace="other",
                text="Other",
                importance=0.5
            )
            
            # If both provided, namespaces should take precedence
            results = manager.retrieve_memories(
                query="test",
                namespace="other",  # Should be ignored
                namespaces=["math.sage", "python.api"],  # Should be used
                limit=10
            )
            
            result_namespaces = {mem.namespace for mem in results}
            assert "other" not in result_namespaces
            assert "math.sage" in result_namespaces or "python.api" in result_namespaces
            
            storage.close()


class TestDateRangeFilters:
    """Test date range filtering functionality."""
    
    def test_retrieve_memories_with_created_after(self):
        """
        Test filtering memories by created_after date.
        
        Rationale: Ensures only memories created after the specified date are returned.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store a memory
            memory_id = manager.store_memory(
                namespace="test",
                text="Test memory",
                importance=0.7
            )[0]
            
            # Get the memory to check its created_at
            memory = manager.get_memory(memory_id)
            assert memory is not None
            
            # Create a date before the memory was created
            before_date = memory.created_at - timedelta(hours=1)
            
            # Search with created_after filter
            results = manager.retrieve_memories(
                query="test",
                created_after=before_date,
                limit=10
            )
            
            # Should include the memory
            assert len(results) > 0
            assert any(mem.id == memory_id for mem in results)
            
            # Search with created_after after the memory was created
            after_date = memory.created_at + timedelta(hours=1)
            results = manager.retrieve_memories(
                query="test",
                created_after=after_date,
                limit=10
            )
            
            # Should not include the memory
            assert not any(mem.id == memory_id for mem in results)
            
            storage.close()
    
    def test_retrieve_memories_timezone_aware_naive_comparison(self):
        """
        Test that datetime comparisons work correctly with both timezone-aware and naive datetimes.
        
        Rationale: Ensures the fix for TypeError when comparing offset-naive and offset-aware datetimes works.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store a memory
            memory_id = manager.store_memory(
                namespace="test",
                text="Test memory for timezone",
                importance=0.7
            )[0]
            
            # Get the memory to check its created_at
            memory = manager.get_memory(memory_id)
            assert memory is not None
            
            # Test 1: Timezone-naive filter parameter vs timezone-aware memory
            naive_date = datetime(2024, 1, 1, 12, 0, 0)  # Naive datetime
            results = manager.retrieve_memories(
                query="test",
                created_after=naive_date,
                limit=10
            )
            # Should not raise TypeError, should work correctly
            assert isinstance(results, list)
            
            # Test 2: Timezone-aware filter parameter vs timezone-aware memory
            aware_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)  # Aware datetime
            results = manager.retrieve_memories(
                query="test",
                created_after=aware_date,
                limit=10
            )
            # Should not raise TypeError, should work correctly
            assert isinstance(results, list)
            
            # Test 3: Verify that memory.created_at is timezone-aware after storage
            # (storage layer normalizes it, so comparisons should always work)
            assert memory.created_at.tzinfo is not None, "Memory created_at should be timezone-aware"
            
            # Test 4: Mix naive and aware in last_used filters
            naive_last_used = datetime(2024, 1, 1, 12, 0, 0)  # Naive
            aware_last_used = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)  # Aware
            results = manager.retrieve_memories(
                query="test",
                last_used_after=naive_last_used,
                limit=10
            )
            assert isinstance(results, list)
            
            results = manager.retrieve_memories(
                query="test",
                last_used_before=aware_last_used,
                limit=10
            )
            assert isinstance(results, list)
            
            storage.close()
    
    def test_retrieve_memories_with_created_before(self):
        """
        Test filtering memories by created_before date.
        
        Rationale: Ensures only memories created before the specified date are returned.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store a memory
            memory_id = manager.store_memory(
                namespace="test",
                text="Test memory",
                importance=0.7
            )[0]
            
            # Get the memory to check its created_at
            memory = manager.get_memory(memory_id)
            assert memory is not None
            
            # Create a date after the memory was created
            after_date = memory.created_at + timedelta(hours=1)
            
            # Search with created_before filter
            results = manager.retrieve_memories(
                query="test",
                created_before=after_date,
                limit=10
            )
            
            # Should include the memory
            assert len(results) > 0
            assert any(mem.id == memory_id for mem in results)
            
            # Search with created_before before the memory was created
            before_date = memory.created_at - timedelta(hours=1)
            results = manager.retrieve_memories(
                query="test",
                created_before=before_date,
                limit=10
            )
            
            # Should not include the memory
            assert not any(mem.id == memory_id for mem in results)
            
            storage.close()
    
    def test_retrieve_memories_with_last_used_after(self):
        """
        Test filtering memories by last_used_after date.
        
        Rationale: Ensures only memories last used after the specified date are returned.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store a memory and retrieve it (updates last_used_at)
            memory_id = manager.store_memory(
                namespace="test",
                text="Test memory",
                importance=0.7
            )[0]
            
            # Retrieve to update last_used_at
            manager.retrieve_memories(query="test", limit=10)
            
            # Get the memory to check its last_used_at
            memory = manager.get_memory(memory_id)
            assert memory is not None
            
            # Create a date before last_used
            before_date = memory.last_used_at - timedelta(hours=1)
            
            # Search with last_used_after filter
            results = manager.retrieve_memories(
                query="test",
                last_used_after=before_date,
                limit=10
            )
            
            # Should include the memory
            assert len(results) > 0
            assert any(mem.id == memory_id for mem in results)
            
            storage.close()
    
    def test_retrieve_memories_with_last_used_before(self):
        """
        Test filtering memories by last_used_before date.
        
        Rationale: Ensures only memories last used before the specified date are returned.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store a memory
            memory_id = manager.store_memory(
                namespace="test",
                text="Test memory",
                importance=0.7
            )[0]
            
            # Get the memory to check its last_used_at
            memory = manager.get_memory(memory_id)
            assert memory is not None
            
            # Create a date after last_used
            after_date = memory.last_used_at + timedelta(hours=1)
            
            # Search with last_used_before filter
            results = manager.retrieve_memories(
                query="test",
                last_used_before=after_date,
                limit=10
            )
            
            # Should include the memory
            assert len(results) > 0
            assert any(mem.id == memory_id for mem in results)
            
            storage.close()
    
    def test_retrieve_memories_with_date_range(self):
        """
        Test filtering memories with both created_after and created_before.
        
        Rationale: Ensures date range filtering works with both bounds.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store a memory
            memory_id = manager.store_memory(
                namespace="test",
                text="Test memory",
                importance=0.7
            )[0]
            
            # Get the memory
            memory = manager.get_memory(memory_id)
            assert memory is not None
            
            # Create date range around the memory's created_at
            start_date = memory.created_at - timedelta(hours=1)
            end_date = memory.created_at + timedelta(hours=1)
            
            # Search with date range
            results = manager.retrieve_memories(
                query="test",
                created_after=start_date,
                created_before=end_date,
                limit=10
            )
            
            # Should include the memory
            assert len(results) > 0
            assert any(mem.id == memory_id for mem in results)
            
            # Search with date range that excludes the memory
            far_future = memory.created_at + timedelta(days=100)
            results = manager.retrieve_memories(
                query="test",
                created_after=far_future,
                created_before=far_future + timedelta(hours=1),
                limit=10
            )
            
            # Should not include the memory
            assert not any(mem.id == memory_id for mem in results)
            
            storage.close()


class TestImportanceFilters:
    """Test importance filtering functionality."""
    
    def test_retrieve_memories_with_min_importance(self):
        """
        Test filtering memories by minimum importance.
        
        Rationale: Ensures only memories with importance >= min_importance are returned.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store memories with different importance levels
            high_imp_id = manager.store_memory(
                namespace="test",
                text="High importance memory",
                importance=0.8
            )[0]
            
            low_imp_id = manager.store_memory(
                namespace="test",
                text="Low importance memory",
                importance=0.3
            )[0]
            
            # Search with min_importance
            results = manager.retrieve_memories(
                query="memory",
                min_importance=0.5,
                limit=10
            )
            
            result_ids = {mem.id for mem in results}
            assert high_imp_id in result_ids
            assert low_imp_id not in result_ids
            
            storage.close()
    
    def test_retrieve_memories_with_max_importance(self):
        """
        Test filtering memories by maximum importance.
        
        Rationale: Ensures only memories with importance <= max_importance are returned.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store memories with different importance levels
            high_imp_id = manager.store_memory(
                namespace="test",
                text="High importance memory",
                importance=0.8
            )[0]
            
            low_imp_id = manager.store_memory(
                namespace="test",
                text="Low importance memory",
                importance=0.3
            )[0]
            
            # Search with max_importance
            results = manager.retrieve_memories(
                query="memory",
                max_importance=0.5,
                limit=10
            )
            
            result_ids = {mem.id for mem in results}
            assert high_imp_id not in result_ids
            assert low_imp_id in result_ids
            
            storage.close()
    
    def test_retrieve_memories_with_importance_range(self):
        """
        Test filtering memories with both min and max importance.
        
        Rationale: Ensures importance range filtering works with both bounds.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store memories with different importance levels
            high_imp_id = manager.store_memory(
                namespace="test",
                text="High importance memory",
                importance=0.8
            )[0]
            
            mid_imp_id = manager.store_memory(
                namespace="test",
                text="Medium importance memory",
                importance=0.5
            )[0]
            
            low_imp_id = manager.store_memory(
                namespace="test",
                text="Low importance memory",
                importance=0.3
            )[0]
            
            # Search with importance range
            results = manager.retrieve_memories(
                query="memory",
                min_importance=0.4,
                max_importance=0.6,
                limit=10
            )
            
            result_ids = {mem.id for mem in results}
            assert high_imp_id not in result_ids
            assert mid_imp_id in result_ids
            assert low_imp_id not in result_ids
            
            storage.close()


class TestCombinedFilters:
    """Test combined filter functionality."""
    
    def test_retrieve_memories_with_all_filters(self):
        """
        Test combining all filters: namespaces, date ranges, importance, tags.
        
        Rationale: Ensures all filters work together correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            mock_embedding = Mock(spec=EmbeddingService)
            mock_embedding.generate_embedding.return_value = [0.1] * 1536
            
            index_path = os.path.join(tmpdir, "test.faiss")
            vector_index = VectorIndex(dimension=1536, index_path=index_path)
            
            manager = MemoryManager(storage, vector_index, mock_embedding)
            
            # Store memories with different properties
            target_id = manager.store_memory(
                namespace="math.sage",
                text="Target memory with important tag",
                importance=0.7,
                tags=["important"]
            )[0]
            
            # Memory in wrong namespace
            manager.store_memory(
                namespace="other",
                text="Wrong namespace",
                importance=0.7,
                tags=["important"]
            )
            
            # Memory with wrong importance
            manager.store_memory(
                namespace="math.sage",
                text="Wrong importance",
                importance=0.3,
                tags=["important"]
            )
            
            # Memory with wrong tags
            manager.store_memory(
                namespace="math.sage",
                text="Wrong tags",
                importance=0.7,
                tags=["unimportant"]
            )
            
            # Get target memory to set date range
            target_memory = manager.get_memory(target_id)
            assert target_memory is not None
            
            start_date = target_memory.created_at - timedelta(hours=1)
            end_date = target_memory.created_at + timedelta(hours=1)
            
            # Search with all filters
            results = manager.retrieve_memories(
                query="memory",
                namespaces=["math.sage"],
                tags=["important"],
                min_importance=0.5,
                max_importance=0.8,
                created_after=start_date,
                created_before=end_date,
                limit=10
            )
            
            result_ids = {mem.id for mem in results}
            assert target_id in result_ids
            
            # Verify other memories are excluded
            assert len(results) == 1
            
            storage.close()


class TestRetrieveMemoriesToolAdvanced:
    """Test RetrieveMemoriesTool with advanced search parameters."""
    
    def test_tool_execute_with_namespaces(self):
        """
        Test RetrieveMemoriesTool with namespaces parameter.
        
        Rationale: Ensures tool interface supports multiple namespaces.
        """
        mock_manager = Mock()
        mock_memory = MemoryRecord(
            id=123,
            namespace="math.sage",
            text="Test memory",
            importance=0.7
        )
        mock_manager.retrieve_memories.return_value = [mock_memory]
        mock_manager.calculate_memory_age.return_value = timedelta(days=1)
        mock_manager.format_memory_age.return_value = "1 day ago"
        mock_manager.is_memory_recent.return_value = False
        
        tool = RetrieveMemoriesTool(mock_manager)
        result = tool.execute(
            query="test",
            namespaces=["math.sage", "python.api"]
        )
        
        assert result["success"] is True
        mock_manager.retrieve_memories.assert_called_once()
        call_kwargs = mock_manager.retrieve_memories.call_args[1]
        assert call_kwargs.get("namespaces") == ["math.sage", "python.api"]
    
    def test_tool_execute_with_date_ranges(self):
        """
        Test RetrieveMemoriesTool with date range parameters.
        
        Rationale: Ensures tool interface supports date range filtering.
        """
        mock_manager = Mock()
        mock_manager.retrieve_memories.return_value = []
        
        tool = RetrieveMemoriesTool(mock_manager)
        
        now = datetime.now(timezone.utc)
        created_after = now - timedelta(days=7)
        created_before = now
        
        result = tool.execute(
            query="test",
            created_after=created_after.isoformat(),
            created_before=created_before.isoformat()
        )
        
        assert result["success"] is True
        mock_manager.retrieve_memories.assert_called_once()
        call_kwargs = mock_manager.retrieve_memories.call_args[1]
        assert "created_after" in call_kwargs
        assert "created_before" in call_kwargs
    
    def test_tool_execute_with_importance_filters(self):
        """
        Test RetrieveMemoriesTool with importance filter parameters.
        
        Rationale: Ensures tool interface supports importance filtering.
        """
        mock_manager = Mock()
        mock_manager.retrieve_memories.return_value = []
        
        tool = RetrieveMemoriesTool(mock_manager)
        result = tool.execute(
            query="test",
            min_importance=0.5,
            max_importance=0.9
        )
        
        assert result["success"] is True
        mock_manager.retrieve_memories.assert_called_once()
        call_kwargs = mock_manager.retrieve_memories.call_args[1]
        assert call_kwargs.get("min_importance") == 0.5
        assert call_kwargs.get("max_importance") == 0.9

