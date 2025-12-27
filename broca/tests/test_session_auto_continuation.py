"""
Tests for automatic tool call continuation behavior.

Tests that the system automatically continues after tool calls complete,
supporting intermediary commentary like Cursor, without requiring manual "Proceed" prompts.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tests.utils import build_llm_response


class MockTool:
    """Mock tool for testing."""
    
    def __init__(self, name: str):
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return f"Mock tool {self._name}"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            }
        }
    
    def execute(self, **kwargs):
        return {"result": f"Executed {self._name} with {kwargs}"}
    
    def format_result(self, result: dict) -> str:
        return f"Result: {result}"


class TestAutomaticContinuation:
    """Test automatic continuation after tool calls."""
    
    def test_automatic_continuation_after_tool_calls(self, mock_llm_client: Mock):
        """
        Test that system automatically continues after tool calls complete.
        
        Rationale: Ensures tool results trigger automatic continuation without user input.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        # First response: tool call with commentary
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Let me check that file...",
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "arguments": json.dumps({"param": "value"})
                        }
                    }]
                }
            }]
        }
        
        # Second response: final answer (should happen automatically)
        final_response = build_llm_response(content="Based on the tool result, here's the answer.")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = ["Let me check that file...", "Based on the tool result, here's the answer."]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Check something")
        
        # Should automatically continue and get final response
        assert response == "Based on the tool result, here's the answer."
        # Verify two LLM calls: one for tool call, one for final response
        assert mock_llm_client.chat.call_count == 2
        
        # Verify tool result was added to messages
        tool_results = [msg for msg in session.messages if msg.get("role") == "tool"]
        assert len(tool_results) == 1
        assert tool_results[0]["name"] == "test_tool"
    
    def test_intermediary_commentary_preserved(self, mock_llm_client: Mock):
        """
        Test that intermediary commentary is preserved alongside tool calls.
        
        Rationale: Ensures commentary like "Let me check..." is kept in conversation history.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        # Response with commentary and tool call
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "I'll examine the code to find the issue.",
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "arguments": json.dumps({"param": "code"})
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Found the issue.")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = ["I'll examine the code to find the issue.", "Found the issue."]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        session.send("Find the bug")
        
        # Verify commentary is preserved in assistant message with tool calls
        assistant_messages_with_tools = [
            msg for msg in session.messages 
            if msg.get("role") == "assistant" and msg.get("tool_calls")
        ]
        assert len(assistant_messages_with_tools) == 1
        assert "I'll examine the code" in assistant_messages_with_tools[0]["content"]
    
    def test_multiple_tool_calls_automatic_continuation(self, mock_llm_client: Mock):
        """
        Test automatic continuation with multiple sequential tool calls.
        
        Rationale: Ensures system continues automatically through multiple tool call iterations.
        """
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        # First: tool1 call
        tool1_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Checking first thing...",
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "tool1",
                            "arguments": json.dumps({"param": "first"})
                        }
                    }]
                }
            }]
        }
        
        # Second: tool2 call (after tool1 result)
        tool2_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Now checking second thing...",
                    "tool_calls": [{
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "tool2",
                            "arguments": json.dumps({"param": "second"})
                        }
                    }]
                }
            }]
        }
        
        # Third: final response
        final_response = build_llm_response(content="All checks complete.")
        
        tool1_calls = tool1_response["choices"][0]["message"]["tool_calls"]
        tool2_calls = tool2_response["choices"][0]["message"]["tool_calls"]
        
        mock_llm_client.chat.side_effect = [tool1_response, tool2_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool1_calls, tool2_calls, []]
        mock_llm_client.extract_assistant_content.side_effect = [
            "Checking first thing...",
            "Now checking second thing...",
            "All checks complete."
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Check multiple things")
        
        # Should automatically continue through all tool calls
        assert response == "All checks complete."
        assert mock_llm_client.chat.call_count == 3
        
        # Verify both tool results are in messages
        tool_results = [msg for msg in session.messages if msg.get("role") == "tool"]
        assert len(tool_results) == 2
    
    def test_tool_result_added_before_continuation(self, mock_llm_client: Mock):
        """
        Test that tool results are added to messages before continuation.
        
        Rationale: Ensures next LLM call receives tool results in message history.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "arguments": json.dumps({"param": "value"})
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final answer")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        # Track messages before and after tool call
        initial_message_count = len(session.messages)
        
        session.send("Use tool")
        
        # Verify tool result was added
        tool_results = [msg for msg in session.messages if msg.get("role") == "tool"]
        assert len(tool_results) == 1
        
        # Verify the second LLM call received the tool result
        # Check that chat was called with messages containing tool result
        second_call_args = mock_llm_client.chat.call_args_list[1]
        messages_passed = second_call_args[0][0] if second_call_args[0] else second_call_args[1].get("messages", [])
        
        # Find tool result in messages passed to second call
        tool_results_in_call = [msg for msg in messages_passed if msg.get("role") == "tool"]
        assert len(tool_results_in_call) == 1


class TestSystemPromptInstructions:
    """Test that system prompt includes tool calling behavior instructions."""
    
    def test_tool_calling_instructions_in_system_prompt(self, mock_llm_client: Mock):
        """
        Test that system prompt includes automatic continuation instructions.
        
        Rationale: Ensures LLM receives guidance about automatic continuation behavior.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        mock_llm_client.extract_tool_calls.return_value = []
        mock_llm_client.extract_assistant_content.return_value = "Response"
        
        session = ConversationSession(llm=mock_llm_client)
        session.send("Test")
        
        # Check system message contains tool calling instructions
        system_messages = [msg for msg in session.messages if msg.get("role") == "system"]
        if system_messages:
            system_content = system_messages[0].get("content", "")
            # Instructions should mention automatic continuation
            assert "AUTOMATICALLY continue" in system_content or "automatically continue" in system_content
            assert "tool calls" in system_content.lower() or "tool results" in system_content.lower()

