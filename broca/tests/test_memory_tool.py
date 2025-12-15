"""
Tests for memory tools (StoreMemoryTool and RetrieveMemoriesTool).

Tests tool execution, schema validation, and result formatting.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import Mock
import pytest

from broca.tools.memory_tool import StoreMemoryTool, RetrieveMemoriesTool
from broca.memory import MemoryRecord, SourceType, SourceMetadata


class TestStoreMemoryTool:
    """Test StoreMemoryTool."""
    
    def test_tool_properties(self):
        """
        Test that tool has required properties.
        
        Rationale: Ensures tool conforms to Tool protocol.
        """
        mock_manager = Mock()
        tool = StoreMemoryTool(mock_manager)
        
        assert tool.name == "store_memory"
        assert isinstance(tool.description, str)
        assert isinstance(tool.parameters, dict)
        assert "properties" in tool.parameters
        # Check that deduplicate parameter is included
        assert "deduplicate" in tool.parameters["properties"]
    
    def test_execute_success(self):
        """
        Test successful memory storage.
        
        Rationale: Ensures tool can store memories correctly.
        """
        mock_manager = Mock()
        mock_manager.store_memory.return_value = (123, False, [])  # Returns (memory_id, was_duplicate, conflicts)
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="test.namespace",
            text="Test memory",
            tags=["tag1"],
            importance=0.7
        )
        
        assert result["success"] is True
        assert result["memory_id"] == 123
        assert result["was_duplicate"] is False
        # Check that store_memory was called with source (defaults to USER)
        call_args = mock_manager.store_memory.call_args
        assert call_args is not None
        assert call_args.kwargs.get("namespace") == "test.namespace"
        assert call_args.kwargs.get("text") == "Test memory"
        assert call_args.kwargs.get("importance") == 0.7
        assert call_args.kwargs.get("tags") == ["tag1"]
        assert call_args.kwargs.get("source") is not None
        assert call_args.kwargs.get("source").source_type == SourceType.USER
    
    def test_execute_with_deduplicate_false(self):
        """
        Test memory storage with deduplicate=False.
        
        Rationale: Ensures deduplicate parameter is passed correctly.
        """
        mock_manager = Mock()
        mock_manager.store_memory.return_value = (123, False, [])
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="test.namespace",
            text="Test memory",
            tags=["tag1"],
            importance=0.7,
            deduplicate=False
        )
        
        assert result["success"] is True
        # Check that store_memory was called with source
        call_args = mock_manager.store_memory.call_args
        assert call_args is not None
        assert call_args.kwargs.get("deduplicate") is False
        assert call_args.kwargs.get("source") is not None
        assert call_args.kwargs.get("source").source_type == SourceType.USER
    
    def test_execute_validates_namespace(self):
        """
        Test that empty namespace is rejected.
        
        Rationale: Ensures schema validation works.
        """
        mock_manager = Mock()
        tool = StoreMemoryTool(mock_manager)
        
        result = tool.execute(namespace="", text="Test", importance=0.5)
        
        assert result["success"] is False
        assert "error" in result
        mock_manager.store_memory.assert_not_called()
    
    def test_execute_validates_text(self):
        """
        Test that empty text is rejected.
        
        Rationale: Ensures schema validation works.
        """
        mock_manager = Mock()
        tool = StoreMemoryTool(mock_manager)
        
        result = tool.execute(namespace="test", text="", importance=0.5)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_execute_validates_importance(self):
        """
        Test that invalid importance is rejected.
        
        Rationale: Ensures importance is in valid range.
        """
        mock_manager = Mock()
        tool = StoreMemoryTool(mock_manager)
        
        result = tool.execute(namespace="test", text="Test", importance=1.5)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_execute_strips_whitespace(self):
        """
        Test that whitespace is stripped from inputs.
        
        Rationale: Ensures clean data storage.
        """
        mock_manager = Mock()
        mock_manager.store_memory.return_value = (123, False, [])
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="  test.namespace  ",
            text="  Test memory  ",
            importance=0.5
        )
        
        assert result["success"] is True
        # Check that store_memory was called with source (defaults to USER)
        call_args = mock_manager.store_memory.call_args
        assert call_args is not None
        assert call_args.kwargs.get("namespace") == "test.namespace"
        assert call_args.kwargs.get("text") == "Test memory"
        assert call_args.kwargs.get("importance") == 0.5
        assert call_args.kwargs.get("tags") == []
        assert call_args.kwargs.get("source") is not None
        assert call_args.kwargs.get("source").source_type == SourceType.USER
    
    def test_execute_handles_errors(self):
        """
        Test that storage errors are handled gracefully.
        
        Rationale: Ensures tool doesn't crash on errors.
        """
        mock_manager = Mock()
        mock_manager.store_memory.side_effect = RuntimeError("Storage failed")
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="test",
            text="Test",
            importance=0.5
        )
        
        assert result["success"] is False
        assert "error" in result
    
    def test_format_result_success(self):
        """
        Test formatting successful storage result.
        
        Rationale: Ensures LLM gets clear feedback.
        """
        mock_manager = Mock()
        tool = StoreMemoryTool(mock_manager)
        
        # Test new memory
        result = {"success": True, "memory_id": 123, "was_duplicate": False, "namespace": "test"}
        formatted = tool.format_result(result)
        assert "stored" in formatted.lower()
        assert "123" in formatted
        
        # Test duplicate memory
        result = {"success": True, "memory_id": 123, "was_duplicate": True, "namespace": "test"}
        formatted = tool.format_result(result)
        assert "updated" in formatted.lower()
        assert "123" in formatted
    
    def test_format_result_error(self):
        """
        Test formatting error result.
        
        Rationale: Ensures error messages are clear.
        """
        mock_manager = Mock()
        tool = StoreMemoryTool(mock_manager)
        
        result = {"success": False, "error": "Test error"}
        formatted = tool.format_result(result)
        assert "error" in formatted.lower()
        assert "test error" in formatted.lower()


class TestRetrieveMemoriesTool:
    """Test RetrieveMemoriesTool."""
    
    def test_tool_properties(self):
        """
        Test that tool has required properties.
        
        Rationale: Ensures tool conforms to Tool protocol.
        """
        mock_manager = Mock()
        tool = RetrieveMemoriesTool(mock_manager)
        
        assert tool.name == "retrieve_memories"
        assert isinstance(tool.description, str)
        assert isinstance(tool.parameters, dict)
        assert "properties" in tool.parameters
    
    def test_execute_success(self):
        """
        Test successful memory retrieval.
        
        Rationale: Ensures tool can retrieve memories correctly.
        """
        mock_manager = Mock()
        mock_memory = MemoryRecord(
            id=123,
            namespace="test",
            text="Test memory",
            importance=0.7,
            tags=["tag1"]
        )
        mock_manager.retrieve_memories.return_value = [mock_memory]
        mock_manager.calculate_memory_age.return_value = timedelta(days=1)
        mock_manager.format_memory_age.return_value = "1 day ago"
        mock_manager.is_memory_recent.return_value = False
        
        tool = RetrieveMemoriesTool(mock_manager)
        result = tool.execute(query="test query")
        
        assert result["success"] is True
        assert result["count"] == 1
        assert len(result["memories"]) == 1
        assert result["memories"][0]["id"] == 123
        assert "age_days" in result["memories"][0]
        assert "age_human" in result["memories"][0]
        assert "is_recent" in result["memories"][0]
        # Check that retrieve_memories was called (may include source_types=None)
        call_args = mock_manager.retrieve_memories.call_args
        assert call_args is not None
        assert call_args.kwargs.get("query") == "test query"
        assert call_args.kwargs.get("limit") == 5
    
    def test_execute_with_filters(self):
        """
        Test memory retrieval with filters.
        
        Rationale: Ensures namespace and tag filters work.
        """
        mock_manager = Mock()
        mock_manager.retrieve_memories.return_value = []
        
        tool = RetrieveMemoriesTool(mock_manager)
        result = tool.execute(
            query="test",
            namespace="user.info",
            tags=["important"],
            limit=10
        )
        
        assert result["success"] is True
        # Check that retrieve_memories was called with correct parameters
        call_args = mock_manager.retrieve_memories.call_args
        assert call_args is not None
        assert call_args.kwargs.get("query") == "test"
        assert call_args.kwargs.get("namespace") == "user.info"
        assert call_args.kwargs.get("tags") == ["important"]
        assert call_args.kwargs.get("limit") == 10
    
    def test_execute_validates_query(self):
        """
        Test that empty query is rejected.
        
        Rationale: Ensures schema validation works.
        """
        mock_manager = Mock()
        tool = RetrieveMemoriesTool(mock_manager)
        
        result = tool.execute(query="")
        
        assert result["success"] is False
        assert "error" in result
        mock_manager.retrieve_memories.assert_not_called()
    
    def test_execute_clamps_limit(self):
        """
        Test that limit is clamped to valid range.
        
        Rationale: Ensures limit stays within bounds.
        """
        mock_manager = Mock()
        mock_manager.retrieve_memories.return_value = []
        
        tool = RetrieveMemoriesTool(mock_manager)
        
        # Test too low
        result = tool.execute(query="test", limit=0)
        # Check that limit was clamped to 1
        call_args = mock_manager.retrieve_memories.call_args
        assert call_args is not None
        assert call_args.kwargs.get("limit") == 1
        
        # Test too high
        mock_manager.retrieve_memories.reset_mock()
        result = tool.execute(query="test", limit=100)
        call_args = mock_manager.retrieve_memories.call_args
        assert call_args is not None
        assert call_args.kwargs.get("limit") == 20
    
    def test_execute_handles_errors(self):
        """
        Test that retrieval errors are handled gracefully.
        
        Rationale: Ensures tool doesn't crash on errors.
        """
        mock_manager = Mock()
        mock_manager.retrieve_memories.side_effect = RuntimeError("Retrieval failed")
        
        tool = RetrieveMemoriesTool(mock_manager)
        result = tool.execute(query="test")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_format_result_with_memories(self):
        """
        Test formatting retrieval result with memories.
        
        Rationale: Ensures LLM gets clear memory information.
        """
        mock_manager = Mock()
        tool = RetrieveMemoriesTool(mock_manager)
        
        memories = [
            {
                "id": 123,
                "namespace": "test.namespace",
                "text": "First memory",
                "importance": 0.8,
                "tags": ["tag1", "tag2"],
                "created_at": "2024-01-01T00:00:00",
                "last_used_at": "2024-01-01T00:00:00"
            },
            {
                "id": 124,
                "namespace": "test.namespace",
                "text": "Second memory",
                "importance": 0.6,
                "tags": [],
                "created_at": "2024-01-01T00:00:00",
                "last_used_at": "2024-01-01T00:00:00"
            }
        ]
        
        result = {"success": True, "count": 2, "memories": memories, "query": "test"}
        formatted = tool.format_result(result)
        
        assert "found 2 memory" in formatted.lower()
        assert "first memory" in formatted.lower()
        assert "second memory" in formatted.lower()
        assert "tag1, tag2" in formatted.lower()
    
    def test_format_result_empty(self):
        """
        Test formatting empty retrieval result.
        
        Rationale: Ensures clear feedback when no memories found.
        """
        mock_manager = Mock()
        tool = RetrieveMemoriesTool(mock_manager)
        
        result = {"success": True, "count": 0, "memories": [], "query": "test"}
        formatted = tool.format_result(result)
        
        assert "no memories found" in formatted.lower()
        assert "test" in formatted
    
    def test_format_result_error(self):
        """
        Test formatting error result.
        
        Rationale: Ensures error messages are clear.
        """
        mock_manager = Mock()
        tool = RetrieveMemoriesTool(mock_manager)
        
        result = {"success": False, "error": "Retrieval failed"}
        formatted = tool.format_result(result)
        
        assert "error" in formatted.lower()
        assert "retrieval failed" in formatted.lower()


class TestStoreMemoryToolSource:
    """Test source tracking in StoreMemoryTool."""
    
    def test_execute_defaults_to_user_source(self):
        """
        Test that execute defaults to USER source for user-initiated storage.
        
        Rationale: Ensures user-initiated storage is tagged correctly.
        """
        mock_manager = Mock()
        mock_manager.store_memory.return_value = (123, False, [])
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="test",
            text="Test memory",
            importance=0.5
        )
        
        assert result["success"] is True
        call_args = mock_manager.store_memory.call_args
        assert call_args is not None
        source = call_args.kwargs.get("source")
        assert source is not None
        assert source.source_type == SourceType.USER
        assert source.metadata is None
    
    def test_execute_with_source_type(self):
        """
        Test that execute accepts source_type parameter.
        
        Rationale: Ensures source type can be specified.
        """
        mock_manager = Mock()
        mock_manager.store_memory.return_value = (123, False, [])
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="test",
            text="Test memory",
            importance=0.5,
            source_type="web_search"
        )
        
        assert result["success"] is True
        call_args = mock_manager.store_memory.call_args
        assert call_args is not None
        source = call_args.kwargs.get("source")
        assert source is not None
        assert source.source_type == SourceType.WEB_SEARCH
    
    def test_execute_with_source_metadata(self):
        """
        Test that execute accepts source_metadata parameter.
        
        Rationale: Ensures source metadata can be provided.
        """
        mock_manager = Mock()
        mock_manager.store_memory.return_value = (123, False, [])
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="test",
            text="Test memory",
            importance=0.5,
            source_type="web_search",
            source_metadata={"query": "test", "urls": ["http://example.com"]}
        )
        
        assert result["success"] is True
        call_args = mock_manager.store_memory.call_args
        assert call_args is not None
        source = call_args.kwargs.get("source")
        assert source is not None
        assert source.source_type == SourceType.WEB_SEARCH
        assert source.metadata is not None
        assert source.metadata["query"] == "test"
        assert len(source.metadata["urls"]) == 1
    
    def test_execute_invalid_source_type(self):
        """
        Test that execute rejects invalid source_type.
        
        Rationale: Ensures validation of source type.
        """
        mock_manager = Mock()
        tool = StoreMemoryTool(mock_manager)
        
        result = tool.execute(
            namespace="test",
            text="Test memory",
            importance=0.5,
            source_type="invalid_source"
        )
        
        assert result["success"] is False
        assert "Invalid source_type" in result.get("error", "")
        mock_manager.store_memory.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
