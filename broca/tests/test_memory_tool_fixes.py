"""
Tests for memory tool fixes.

Validates that all syntax errors are fixed and both tools work correctly.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

from broca.memory import MemoryRecord


class TestSyntaxErrors:
    """Test that file can be imported without syntax errors."""
    
    def test_file_can_be_imported(self):
        """
        Test that memory_tool.py can be imported without syntax errors.
        
        Rationale: Ensures all syntax errors are fixed.
        """
        # This will raise SyntaxError if there are syntax issues
        try:
            from broca.tools.memory_tool import StoreMemoryTool, RetrieveMemoriesTool
            assert True
        except SyntaxError as e:
            pytest.fail(f"Syntax error in memory_tool.py: {e}")
        except ImportError as e:
            pytest.fail(f"Import error in memory_tool.py: {e}")
    
    def test_both_classes_exist(self):
        """
        Test that both StoreMemoryTool and RetrieveMemoriesTool classes exist.
        
        Rationale: Ensures both classes are properly defined.
        """
        from broca.tools.memory_tool import StoreMemoryTool, RetrieveMemoriesTool
        
        assert StoreMemoryTool is not None
        assert RetrieveMemoriesTool is not None


class TestStoreMemoryToolStructure:
    """Test StoreMemoryTool structure and deduplicate parameter."""
    
    def test_store_tool_has_deduplicate_parameter(self):
        """
        Test that StoreMemoryTool has deduplicate parameter.
        
        Rationale: Ensures deduplicate parameter is included in schema.
        """
        from broca.tools.memory_tool import StoreMemoryTool
        
        mock_manager = Mock()
        tool = StoreMemoryTool(mock_manager)
        
        assert "deduplicate" in tool.parameters["properties"]
        assert tool.parameters["properties"]["deduplicate"]["type"] == "boolean"
    
    def test_store_tool_execute_handles_deduplicate(self):
        """
        Test that StoreMemoryTool.execute handles deduplicate parameter.
        
        Rationale: Ensures deduplicate is passed to memory_manager.
        """
        from broca.tools.memory_tool import StoreMemoryTool
        
        mock_manager = Mock()
        mock_manager.store_memory.return_value = (123, False, [])
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="test",
            text="Test memory",
            importance=0.5,
            deduplicate=True
        )
        
        assert result["success"] is True
        mock_manager.store_memory.assert_called_once_with(
            namespace="test",
            text="Test memory",
            importance=0.5,
            tags=[],
            deduplicate=True,
            conflict_check=False,  # Default value
            auto_resolve=False,  # Default value
            auto_link=True  # Default value
        )
    
    def test_store_tool_execute_returns_was_duplicate(self):
        """
        Test that StoreMemoryTool.execute returns was_duplicate field.
        
        Rationale: Ensures format_result can handle was_duplicate.
        """
        from broca.tools.memory_tool import StoreMemoryTool
        
        mock_manager = Mock()
        mock_manager.store_memory.return_value = (123, True, [])  # was_duplicate=True
        
        tool = StoreMemoryTool(mock_manager)
        result = tool.execute(
            namespace="test",
            text="Test memory",
            importance=0.5
        )
        
        assert result["success"] is True
        assert result["was_duplicate"] is True
        assert result["memory_id"] == 123


class TestRetrieveMemoriesToolStructure:
    """Test RetrieveMemoriesTool structure and recency_weight parameter."""
    
    def test_retrieve_tool_has_recency_weight_parameter(self):
        """
        Test that RetrieveMemoriesTool has recency_weight parameter.
        
        Rationale: Ensures recency_weight parameter is included in schema.
        """
        from broca.tools.memory_tool import RetrieveMemoriesTool
        
        mock_manager = Mock()
        tool = RetrieveMemoriesTool(mock_manager)
        
        assert "recency_weight" in tool.parameters["properties"]
        assert tool.parameters["properties"]["recency_weight"]["type"] == "number"
        assert tool.parameters["properties"]["recency_weight"]["minimum"] == 0.0
        assert tool.parameters["properties"]["recency_weight"]["maximum"] == 1.0
    
    def test_retrieve_tool_execute_handles_recency_weight(self):
        """
        Test that RetrieveMemoriesTool.execute handles recency_weight parameter.
        
        Rationale: Ensures recency_weight is passed to memory_manager.
        """
        from broca.tools.memory_tool import RetrieveMemoriesTool
        
        mock_manager = Mock()
        mock_manager.retrieve_memories.return_value = []
        
        tool = RetrieveMemoriesTool(mock_manager)
        result = tool.execute(
            query="test query",
            recency_weight=0.5
        )
        
        assert result["success"] is True
        mock_manager.retrieve_memories.assert_called_once_with(
            query="test query",
            namespace=None,
            namespaces=None,
            tags=None,
            limit=5,
            recency_weight=0.5,
            namespace_exact=False,
            tag_mode="any",
            query_phrases=None,
            created_after=None,
            created_before=None,
            last_used_after=None,
            last_used_before=None,
            min_importance=None,
            max_importance=None
        )


class TestTemporalFeatures:
    """Test temporal features in RetrieveMemoriesTool."""
    
    def test_retrieve_tool_includes_temporal_info(self):
        """
        Test that RetrieveMemoriesTool includes temporal information in results.
        
        Rationale: Ensures age calculation, formatting, and recency checks work.
        """
        from broca.tools.memory_tool import RetrieveMemoriesTool
        
        # Create a mock memory
        mock_memory = MemoryRecord(
            id=123,
            namespace="test",
            text="Test memory",
            importance=0.7,
            tags=["tag1"],
            created_at=datetime.now(timezone.utc) - timedelta(hours=12)  # 12 hours ago
        )
        
        mock_manager = Mock()
        mock_manager.retrieve_memories.return_value = [mock_memory]
        mock_manager.calculate_memory_age.return_value = timedelta(hours=12)
        mock_manager.format_memory_age.return_value = "12 hours ago"
        mock_manager.is_memory_recent.return_value = True
        
        tool = RetrieveMemoriesTool(mock_manager)
        result = tool.execute(query="test")
        
        assert result["success"] is True
        assert len(result["memories"]) == 1
        
        memory = result["memories"][0]
        assert "age_days" in memory
        assert "age_human" in memory
        assert "is_recent" in memory
        assert memory["age_human"] == "12 hours ago"
        assert memory["is_recent"] is True
        
        # Verify temporal methods were called
        mock_manager.calculate_memory_age.assert_called_once_with(mock_memory)
        mock_manager.format_memory_age.assert_called_once_with(mock_memory)
        mock_manager.is_memory_recent.assert_called_once_with(mock_memory, hours=24)
    
    def test_retrieve_tool_format_result_includes_temporal_info(self):
        """
        Test that format_result displays temporal information.
        
        Rationale: Ensures temporal context is visible to LLM.
        """
        from broca.tools.memory_tool import RetrieveMemoriesTool
        
        mock_manager = Mock()
        tool = RetrieveMemoriesTool(mock_manager)
        
        result = {
            "success": True,
            "count": 1,
            "memories": [{
                "id": 123,
                "text": "Test memory",
                "namespace": "test",
                "tags": ["tag1"],
                "importance": 0.7,
                "created_at": "2024-01-01T00:00:00",
                "age_human": "12 hours ago",
                "is_recent": True
            }],
            "query": "test",
            "recency_weight_used": 0.3
        }
        
        formatted = tool.format_result(result)
        
        assert "12 hours ago" in formatted
        assert "Recent" in formatted or "recent" in formatted.lower()
        assert "recency weight" in formatted.lower()

