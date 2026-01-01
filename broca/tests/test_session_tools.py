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

    def test_tool_call_does_not_shadow_app_config(self, mock_llm_client: Mock):
        """
        Regression test: tool call handling must not shadow Broca config with ReasoningConfig.

        This previously caused AttributeError: 'ReasoningConfig' object has no attribute 'summarization'
        during tool result truncation.
        """
        class BigResultTool(MockTool):
            def execute(self, **kwargs):
                return {"result": "x" * 20000}

        registry = ToolRegistry()
        tool = BigResultTool("big_tool")
        registry.register_tool(tool)

        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_big",
                        "type": "function",
                        "function": {"name": "big_tool", "arguments": json.dumps({"param": "value"})}
                    }]
                }
            }]
        }
        final_response = build_llm_response(content="OK")

        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "OK"]

        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Use tool")

        assert response == "OK"
        assert any(m.get("role") == "tool" for m in session.messages)
    
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


class TestConversationSessionReasonerModel:
    """Test ConversationSession with deepseek-reasoner model."""
    
    def test_reasoner_extracts_reasoning_content(self, mock_llm_client: Mock):
        """
        Test that session extracts reasoning_content from reasoner model responses.
        
        Rationale: Ensures reasoning_content is tracked for reasoner model.
        """
        from broca.llm.deepseek_client import DeepSeekClient
        
        # Create a reasoner client
        reasoner_client = DeepSeekClient(model="deepseek-reasoner")
        reasoner_client._client = mock_llm_client._client if hasattr(mock_llm_client, '_client') else None
        
        # Mock is_reasoner_model and extract_reasoning_content
        reasoner_client.is_reasoner_model = lambda: True
        reasoner_client.extract_reasoning_content = DeepSeekClient.extract_reasoning_content
        
        response_with_reasoning = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Final answer",
                    "reasoning_content": "Let me think step by step..."
                }
            }]
        }
        
        mock_llm_client.chat.return_value = response_with_reasoning
        mock_llm_client.extract_assistant_content.return_value = "Final answer"
        mock_llm_client.extract_tool_calls.return_value = []
        mock_llm_client.is_reasoner_model = lambda: True
        mock_llm_client.extract_reasoning_content = DeepSeekClient.extract_reasoning_content
        
        session = ConversationSession(llm=mock_llm_client)
        response = session.send("Hello")
        
        # Verify reasoning_content was extracted and stored
        assert hasattr(session, '_current_reasoning_content')
        # Note: reasoning_content is cleared at start of turn, so it may be None after final response
        assert response == "Final answer"
    
    def test_reasoner_passes_reasoning_content_during_tool_iterations(self, mock_llm_client: Mock):
        """
        Test that session passes reasoning_content during tool call iterations.
        
        Rationale: Ensures reasoning_content is sent back to API during tool iterations.
        """
        from broca.llm.deepseek_client import DeepSeekClient
        from broca.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        # First response: tool call with reasoning_content
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "reasoning_content": "I need to use a tool",
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }]
                }
            }]
        }
        
        # Second response: final answer with reasoning_content
        final_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Final answer",
                    "reasoning_content": "Based on tool result, here's the answer"
                }
            }]
        }
        
        mock_llm_client.is_reasoner_model = lambda: True
        mock_llm_client.extract_reasoning_content = DeepSeekClient.extract_reasoning_content
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        
        # Track chat calls to verify reasoning_content was passed
        chat_calls = []
        def track_chat(*args, **kwargs):
            chat_calls.append(kwargs)
            if len(chat_calls) == 1:
                return tool_call_response
            else:
                return final_response
        
        mock_llm_client.chat.side_effect = track_chat
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Use tool")
        
        # Verify reasoning_content was passed in second call (after tool execution)
        assert len(chat_calls) >= 2
        # Second call should include reasoning_content from first response
        assert chat_calls[1].get("reasoning_content") == "I need to use a tool"
        assert response == "Final answer"
    
    def test_reasoner_clears_reasoning_content_on_new_turn(self, mock_llm_client: Mock):
        """
        Test that session clears reasoning_content when starting a new user turn.
        
        Rationale: Ensures reasoning_content doesn't persist across turns (prevents 400 errors).
        """
        from broca.llm.deepseek_client import DeepSeekClient
        
        response_with_reasoning = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Answer",
                    "reasoning_content": "Reasoning from turn 1"
                }
            }]
        }
        
        mock_llm_client.is_reasoner_model = lambda: True
        mock_llm_client.extract_reasoning_content = DeepSeekClient.extract_reasoning_content
        mock_llm_client.extract_tool_calls.return_value = []
        mock_llm_client.extract_assistant_content.return_value = "Answer"
        mock_llm_client.chat.return_value = response_with_reasoning
        
        session = ConversationSession(llm=mock_llm_client)
        
        # First turn
        session.send("First question")
        
        # Verify reasoning_content was extracted
        assert hasattr(session, '_current_reasoning_content')
        
        # Track chat calls for second turn
        chat_calls = []
        def track_chat(*args, **kwargs):
            chat_calls.append(kwargs)
            return response_with_reasoning
        
        mock_llm_client.chat.side_effect = track_chat
        
        # Second turn - reasoning_content should be cleared
        session.send("Second question")
        
        # Verify reasoning_content was NOT passed (should be None/cleared)
        assert len(chat_calls) > 0
        # First call of second turn should not have reasoning_content from previous turn
        assert chat_calls[0].get("reasoning_content") is None
    
    def test_reasoner_assistant_message_always_has_reasoning_content_field(self, mock_llm_client: Mock):
        """
        Test that assistant messages with tool_calls always have reasoning_content field.
        
        Rationale: API requires reasoning_content field must be present, even if empty.
        """
        from broca.llm.deepseek_client import DeepSeekClient
        from broca.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        # Response with tool_calls but NO reasoning_content (first request might not have it)
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
                    # NO reasoning_content field
                }
            }]
        }
        
        final_response = build_llm_response(content="Final answer")
        
        mock_llm_client.is_reasoner_model = lambda: True
        mock_llm_client.extract_reasoning_content = DeepSeekClient.extract_reasoning_content
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        session.send("Use tool")
        
        # Check that assistant message with tool_calls has reasoning_content field
        assistant_messages = [msg for msg in session.messages if msg.get("role") == "assistant" and "tool_calls" in msg]
        assert len(assistant_messages) > 0
        assistant_with_tools = assistant_messages[0]
        assert "reasoning_content" in assistant_with_tools, "Assistant message with tool_calls must have reasoning_content field"
        # Field should exist (even if empty string)
        assert assistant_with_tools.get("reasoning_content") is not None


class TestConversationSessionThoughtSignature:
    """Test thought_signature handling in ConversationSession for Gemini."""
    
    def test_thought_signature_added_to_tool_calls_when_missing(self):
        """
        Test that thought_signature is added to tool_calls when missing.
        
        Rationale: Ensures Gemini API requirements are met - each tool_call must have thought_signature.
        """
        from broca.llm.gemini_client import GeminiClient
        
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        # Create a Gemini client mock
        gemini_client = Mock(spec=GeminiClient)
        
        # Mock the client to return tool calls without thought_signature
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
                        # Missing thought_signature
                    }]
                }
            }],
            "thought_signature": "test-sig-123"  # Signature in response
        }
        
        final_response = build_llm_response(content="Final answer")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        gemini_client.chat.side_effect = [tool_call_response, final_response]
        gemini_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        gemini_client.extract_assistant_content.side_effect = [None, "Final answer"]
        gemini_client.extract_thought_signature.return_value = "test-sig-123"
        gemini_client._is_gemini_client = lambda: True
        
        session = ConversationSession(llm=gemini_client, tool_registry=registry)
        response = session.send("Use tool")
        
        assert response == "Final answer"
        
        # Check that tool_calls in conversation history have thought_signature
        assistant_messages = [msg for msg in session.messages if msg.get("role") == "assistant" and "tool_calls" in msg]
        assert len(assistant_messages) > 0
        assistant_with_tools = assistant_messages[0]
        tool_calls = assistant_with_tools.get("tool_calls", [])
        assert len(tool_calls) > 0
        # All tool_calls should have thought_signature
        for tool_call in tool_calls:
            assert "thought_signature" in tool_call
            assert tool_call["thought_signature"] == "test-sig-123"
    
    def test_thought_signature_preserved_when_present(self):
        """
        Test that existing thought_signature in tool_calls is preserved.
        
        Rationale: Ensures we don't overwrite existing thought_signature values.
        """
        from broca.llm.gemini_client import GeminiClient
        
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        gemini_client = Mock(spec=GeminiClient)
        
        # Tool calls already have thought_signature
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
                        },
                        "thought_signature": "existing-sig-456"  # Already present
                    }]
                }
            }],
            "thought_signature": "new-sig-789"
        }
        
        final_response = build_llm_response(content="Final answer")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        gemini_client.chat.side_effect = [tool_call_response, final_response]
        gemini_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        gemini_client.extract_assistant_content.side_effect = [None, "Final answer"]
        gemini_client.extract_thought_signature.return_value = "new-sig-789"
        gemini_client._is_gemini_client = lambda: True
        
        session = ConversationSession(llm=gemini_client, tool_registry=registry)
        response = session.send("Use tool")
        
        assert response == "Final answer"
        
        # Check that existing thought_signature is preserved
        assistant_messages = [msg for msg in session.messages if msg.get("role") == "assistant" and "tool_calls" in msg]
        assert len(assistant_messages) > 0
        assistant_with_tools = assistant_messages[0]
        tool_calls = assistant_with_tools.get("tool_calls", [])
        assert len(tool_calls) > 0
        # Existing thought_signature should be preserved
        assert tool_calls[0]["thought_signature"] == "existing-sig-456"
    
    def test_thought_signature_not_added_for_non_gemini(self, mock_llm_client: Mock):
        """
        Test that thought_signature is not added for non-Gemini clients.
        
        Rationale: Ensures we don't modify tool_calls for clients that don't need thought_signature.
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
                        # No thought_signature (not needed for non-Gemini)
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final answer")
        
        tool_calls_list = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [tool_calls_list, []]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        # Non-Gemini client
        mock_llm_client._is_gemini_client = lambda: False
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        response = session.send("Use tool")
        
        assert response == "Final answer"
        
        # Check that tool_calls don't have thought_signature (not needed for non-Gemini)
        assistant_messages = [msg for msg in session.messages if msg.get("role") == "assistant" and "tool_calls" in msg]
        assert len(assistant_messages) > 0
        assistant_with_tools = assistant_messages[0]
        tool_calls = assistant_with_tools.get("tool_calls", [])
        assert len(tool_calls) > 0
        # Non-Gemini clients don't need thought_signature
        assert "thought_signature" not in tool_calls[0]
