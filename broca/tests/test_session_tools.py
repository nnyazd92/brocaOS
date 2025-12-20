"""
Integration tests for ConversationSession with tools.

Tests tool call execution, tool result integration, and multi-turn tool conversations.
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


class TestConversationSessionWithTools:
    """Test ConversationSession with tool registry."""
    
    def test_session_without_tools_backward_compatible(self, mock_llm_client: Mock):
        """
        Test that session works without tools (backward compatibility).
        
        Rationale: Ensures existing code continues to work without changes.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(llm=mock_llm_client)
        
        response = session.send("Hello")
        
        assert response == "Response"
        assert session.tool_registry is None
    
    def test_session_with_tools_no_tool_calls(self, mock_llm_client: Mock):
        """
        Test session with tools when LLM doesn't call tools.
        
        Rationale: Ensures tools don't interfere with normal conversations.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        mock_llm_client.chat.return_value = build_llm_response(content="Regular response")
        mock_llm_client.extract_tool_calls.return_value = []  # No tool calls
        mock_llm_client.extract_assistant_content.return_value = "Regular response"
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        response = session.send("Hello")
        
        assert response == "Regular response"
        # Verify tools were passed to LLM
        call_args = mock_llm_client.chat.call_args
        assert "tools" in call_args[1] or len(call_args[0]) > 1


class TestConversationSessionToolCalls:
    """Test tool call execution in ConversationSession."""
    
    def test_single_tool_call_execution(self, mock_llm_client: Mock):
        """
        Test executing a single tool call.
        
        Rationale: Ensures tool calls are executed and results integrated.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        # First response: tool call
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
        
        # Second response: final answer
        final_response = build_llm_response(content="Final answer")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Use tool")
        
        assert response == "Final answer"
        # Verify tool was called
        assert mock_llm_client.chat.call_count == 2
    
    def test_multiple_tool_calls_execution(self, mock_llm_client: Mock):
        """
        Test executing multiple tool calls in one response.
        
        Rationale: Ensures multiple tools can be called simultaneously.
        """
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "tool1", "arguments": "{}"}
                        },
                        {
                            "id": "call_2",
                            "type": "function",
                            "function": {"name": "tool2", "arguments": "{}"}
                        }
                    ]
                }
            }]
        }
        
        final_response = build_llm_response(content="Done")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Done"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Use tools")
        
        assert response == "Done"
        # Verify both tools were called
        assert mock_llm_client.chat.call_count == 2
    
    def test_tool_call_loop_prevention(self, mock_llm_client: Mock):
        """
        Test that tool call loops are prevented.
        
        Rationale: Ensures infinite tool call loops don't occur.
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
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }]
                }
            }]
        }
        
        # Always return tool calls (simulating infinite loop)
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.return_value = tool_call_response
        mock_llm_client.extract_tool_calls.return_value = tool_calls_list
        mock_llm_client.extract_assistant_content.return_value = None
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Test")
        
        # Should stop after max iterations
        assert mock_llm_client.chat.call_count == session._max_tool_iterations
        assert "issue" in response.lower() or "apologize" in response.lower()
    
    def test_tool_messages_in_conversation(self, mock_llm_client: Mock):
        """
        Test that tool messages are added to conversation history.
        
        Rationale: Ensures tool calls and results are preserved in conversation.
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
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        session.send("Test")
        
        # Check for tool messages in conversation
        tool_messages = [msg for msg in session.messages if msg.get("role") == "tool"]
        assert len(tool_messages) > 0
        assert tool_messages[0]["name"] == "test_tool"
    
    def test_tool_error_handling(self, mock_llm_client: Mock):
        """
        Test that tool execution errors don't break the conversation.
        
        Rationale: Ensures graceful error handling for tool failures.
        """
        registry = ToolRegistry()
        
        class FailingTool:
            @property
            def name(self):
                return "failing_tool"
            
            @property
            def description(self):
                return "A tool that fails"
            
            @property
            def parameters(self):
                return {"type": "object"}
            
            def execute(self, **kwargs):
                raise ValueError("Tool failed")
            
            def format_result(self, result):
                return str(result)
        
        tool = FailingTool()
        registry.register_tool(tool)
        
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "failing_tool", "arguments": "{}"}
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Handled error")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Handled error"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Test")
        
        # Should continue despite tool error
        assert response == "Handled error"
        # Error should be in tool message
        tool_messages = [msg for msg in session.messages if msg.get("role") == "tool"]
        assert len(tool_messages) > 0
        assert "Error" in tool_messages[0]["content"]


class TestConversationSessionToolStorage:
    """Test tool messages with storage."""
    
    def test_tool_messages_saved_to_storage(self, mock_llm_client: Mock):
        """
        Test that tool messages are saved to storage.
        
        Rationale: Ensures tool calls and results are persisted.
        """
        import tempfile
        from broca.storage.json_storage import JSONFileStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
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
                            "function": {"name": "test_tool", "arguments": "{}"}
                        }]
                    }
                }]
            }
            
            final_response = build_llm_response(content="Final")
            
            tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
            mock_llm_client.chat.side_effect = [tool_call_response, final_response]
            mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
            mock_llm_client.extract_assistant_content.side_effect = [None, "Final"]
            
            session = ConversationSession(
                llm=mock_llm_client,
                tool_registry=registry,
                storage=storage,
                session_id="test-session"
            )
            session.send("Test")
            
            # Give background threads time to complete
            import time
            time.sleep(0.1)
            
            # Load from storage and verify tool messages
            result = storage.load_conversation("test-session")
            assert result is not None
            messages = result["messages"]
            tool_messages = [msg for msg in messages if msg.get("role") == "tool"]
            assert len(tool_messages) > 0

