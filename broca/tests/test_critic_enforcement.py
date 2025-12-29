"""
Tests for critic tool as a free tool (no enforcement).

The critic tool is now a freely callable devils advocate tool with no
enforcement or binding logic. These tests verify it works as a normal tool.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tests.utils import build_llm_response


class MockCriticTool:
    """Mock critic tool for testing."""
    
    def __init__(self, name: str = "critic"):
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return "Mock critic tool"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "world_state": {"type": "object"},
                "content": {"type": "string"}
            },
            "required": ["world_state", "content"]
        }
    
    def execute(self, **kwargs):
        # Return result based on test scenario
        # Tests will override this
        return {"accepted": True, "feedback": "Accepted", "violations": []}
    
    def format_result(self, result: dict) -> str:
        if result.get("accepted", False):
            return f"ACCEPTABLE: {result.get('feedback', '')}"
        else:
            return f"CONCERNS IDENTIFIED: {result.get('feedback', '')}"


class TestCriticToolAsFreeTool:
    """Test critic tool works as a free tool without enforcement."""
    
    def test_critic_tool_can_be_called_freely(self, mock_llm_client: Mock):
        """
        Test that critic tool can be called without enforcement.
        
        Rationale: Ensures tool is freely callable like any other tool.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": True,
            "feedback": "Content is acceptable",
            "violations": []
        })
        registry.register_tool(critic_tool)
        
        session = ConversationSession(
            tool_registry=registry,
            llm=mock_llm_client
        )
        
        # LLM calls critic tool
        tool_call_response = build_llm_response(
            content=None,
            tool_calls=[{
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "critic",
                    "arguments": json.dumps({
                        "world_state": {"constraints": {}},
                        "content": "Test content"
                    })
                }
            }]
        )
        
        # Then provides final response
        final_response = build_llm_response(content="Final response")
        
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [
            None,
            "Final response"
        ]
        
        response = session.send("Test message")
        
        # Should return final response without blocking
        assert response == "Final response"
        assert critic_tool.execute.called
    
    def test_critic_rejection_does_not_block_final_response(self, mock_llm_client: Mock):
        """
        Test that critic rejection does not block final response.
        
        Rationale: Ensures no enforcement logic prevents final responses.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Content has concerns",
            "violations": [{"constraint": "test", "description": "Issue found"}]
        })
        registry.register_tool(critic_tool)
        
        session = ConversationSession(
            tool_registry=registry,
            llm=mock_llm_client
        )
        
        # LLM calls critic tool (rejection)
        tool_call_response = build_llm_response(
            content=None,
            tool_calls=[{
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "critic",
                    "arguments": json.dumps({
                        "world_state": {"constraints": {}},
                        "content": "Test content"
                    })
                }
            }]
        )
        
        # Then provides final response anyway
        final_response = build_llm_response(content="Final response despite rejection")
        
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [
            None,
            "Final response despite rejection"
        ]
        
        response = session.send("Test message")
        
        # Should return final response even after rejection
        assert response == "Final response despite rejection"
        assert critic_tool.execute.called
