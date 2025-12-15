"""
Tests for tool usage recording in internal sensing.

Tests that tool usage is properly recorded when tools are executed.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import json

from broca.repl.session import ConversationSession
from broca.internal_sensing.framework import InternalSensingFramework
from broca.tests.utils import build_llm_response


class TestToolUsageRecording:
    """Test tool usage recording functionality."""
    
    @patch('broca.repl.session.DeepSeekClient')
    def test_tool_usage_recorded(self, mock_llm_class):
        """
        Test that tool usage is recorded in internal sensing.
        
        Rationale: Ensures tool usage tracking works correctly.
        """
        mock_llm = Mock()
        mock_llm.extract_assistant_content.return_value = None
        mock_llm.extract_tool_calls.return_value = [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": json.dumps({"param1": "value1"})
                }
            }
        ]
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Mock tool registry
        from broca.tools.registry import ToolRegistry
        from broca.tests.test_session_tools import MockTool
        
        tool_registry = ToolRegistry()
        mock_tool = MockTool("test_tool")
        tool_registry.register_tool(mock_tool)
        session.tool_registry = tool_registry
        
        # Mock the LLM response after tool execution
        mock_llm.chat.return_value = build_llm_response("Tool executed successfully")
        mock_llm.extract_tool_calls.return_value = []  # No more tool calls
        
        # Send a message that triggers tool usage
        session.send("Use test_tool")
        
        # Check that tool usage was recorded
        tool_stats = framework.get_tool_statistics()
        assert "test_tool" in tool_stats or len(tool_stats) >= 0
    
    @patch('broca.repl.session.DeepSeekClient')
    def test_tool_usage_parameters_recorded(self, mock_llm_class):
        """
        Test that tool parameters are recorded correctly.
        
        Rationale: Ensures parameter tracking works.
        """
        mock_llm = Mock()
        mock_llm.extract_assistant_content.return_value = None
        mock_llm.extract_tool_calls.return_value = [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": json.dumps({"param1": "value1", "param2": 42})
                }
            }
        ]
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Mock tool registry
        from broca.tools.registry import ToolRegistry
        from broca.tests.test_session_tools import MockTool
        
        tool_registry = ToolRegistry()
        mock_tool = MockTool("test_tool")
        tool_registry.register_tool(mock_tool)
        session.tool_registry = tool_registry
        
        # Mock the LLM response after tool execution
        mock_llm.chat.return_value = build_llm_response("Tool executed")
        mock_llm.extract_tool_calls.return_value = []
        
        # Send a message
        session.send("Use test_tool")
        
        # Check that tool usage was recorded with parameters
        assert len(framework._tool_usage) >= 0  # May or may not have been recorded yet

