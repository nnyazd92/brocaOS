import uuid
import pytest
from unittest.mock import Mock, patch
from broca.repl.session import ConversationSession
from broca.repl.response_guard import FALLBACK_TEMPLATE

class DummyLLMClient:
    def __init__(self, result=None, raise_exc=False, raise_type=None, extract_result=None):
        self._result = result
        self._raise = raise_exc
        self._raise_type = raise_type
        self._extract_result = extract_result
    def chat(self, *args, **kwargs):
        if self._raise_type == TimeoutError:
            raise TimeoutError("dummy timeout")
        if self._raise_type == ConnectionError:
            raise ConnectionError("dummy connection error")
        if self._raise:
            raise RuntimeError("dummy llm failure")
        # Simulate a typical response structure
        return {"choices": [{"message": {"content": self._result}}]}
    def chat_stream(self, *args, **kwargs):
        # Simulate empty generator
        if self._raise:
            raise RuntimeError("dummy stream failure")
        if self._result is None:
            return iter(())
        return iter((self._result,))
    def extract_assistant_content(self, response):
        if self._extract_result is not None:
            return self._extract_result
        try:
            return response.get('choices', [])[0].get('message', {}).get('content')
        except Exception:
            return None
    def extract_tool_calls(self, response):
        return []


def test_empty_reply_gets_fallback(monkeypatch):
    """Test that empty string responses get fallback message instead of being preserved."""
    session = ConversationSession(storage=None, tool_registry=None)
    session.llm = DummyLLMClient(result="")
    reply = session.send("hello", stream=False)
    # Empty-string responses should get fallback, not be preserved
    assert reply is not None
    assert reply.strip() != ""
    assert "[automatic fallback]" in reply
    assert "TraceID" in reply


def test_llm_exception_fallback(monkeypatch):
    session = ConversationSession(storage=None, tool_registry=None)
    session.llm = DummyLLMClient(raise_exc=True)
    reply = session.send("trigger exception", stream=False)
    assert reply is not None and reply.strip() != ""
    assert "TraceID" in reply


def test_max_iterations_empty_content_gets_fallback():
    """Test that max iterations path with empty content returns fallback."""
    mock_llm = Mock()
    # Make extract_assistant_content return empty string to trigger max iterations path
    mock_llm.extract_assistant_content.return_value = ""
    mock_llm.extract_tool_calls.return_value = []
    mock_llm.chat.return_value = {"choices": [{"message": {"content": ""}}]}
    mock_llm.chat_stream.return_value = iter(())
    
    session = ConversationSession(llm=mock_llm, storage=None, tool_registry=None)
    # Set low max iterations to trigger the path quickly
    session._max_tool_iterations = 1
    
    # Create a simple tool registry that will cause tool calls
    from broca.tools.registry import ToolRegistry
    
    tool_registry = ToolRegistry()
    
    # Mock a simple tool
    mock_tool = Mock()
    mock_tool.name = "test_tool"
    mock_tool.description = "Test tool"
    mock_tool.parameters = {"type": "object", "properties": {}}
    mock_tool.execute.return_value = {"result": "test"}
    mock_tool.format_result = lambda r: str(r)
    
    tool_registry.register_tool(mock_tool)
    
    # Mock tool calls to always return this tool
    def mock_extract_tool_calls(response):
        return [{"function": {"name": "test_tool", "arguments": "{}"}}]
    
    mock_llm.extract_tool_calls = mock_extract_tool_calls
    session.tool_registry = tool_registry
    
    reply = session.send("test", stream=False)
    # Should get fallback, not empty string
    assert reply is not None
    assert reply.strip() != ""
    assert "[automatic fallback]" in reply or "I apologize" in reply


def test_timeout_error_returns_non_empty():
    """Test that TimeoutError path returns non-empty response."""
    mock_llm = Mock()
    mock_llm.chat.side_effect = TimeoutError("Request timed out")
    mock_llm.chat_stream.side_effect = TimeoutError("Request timed out")
    
    session = ConversationSession(llm=mock_llm, storage=None, tool_registry=None)
    reply = session.send("test", stream=False)
    
    assert reply is not None
    assert reply.strip() != ""
    assert "TraceID" in reply


def test_connection_error_returns_non_empty():
    """Test that ConnectionError path returns non-empty response."""
    mock_llm = Mock()
    mock_llm.chat.side_effect = ConnectionError("Network error")
    mock_llm.chat_stream.side_effect = ConnectionError("Network error")
    
    session = ConversationSession(llm=mock_llm, storage=None, tool_registry=None)
    reply = session.send("test", stream=False)
    
    assert reply is not None
    assert reply.strip() != ""
    assert "TraceID" in reply


def test_generic_exception_returns_non_empty():
    """Test that generic Exception path returns non-empty response."""
    mock_llm = Mock()
    mock_llm.chat.side_effect = ValueError("Unexpected error")
    mock_llm.chat_stream.side_effect = ValueError("Unexpected error")
    
    session = ConversationSession(llm=mock_llm, storage=None, tool_registry=None)
    reply = session.send("test", stream=False)
    
    assert reply is not None
    assert reply.strip() != ""
    assert "TraceID" in reply


def test_summarize_empty_returns_fallback():
    """Test that summarize path with empty string returns fallback."""
    session = ConversationSession(storage=None, tool_registry=None)
    
    # Mock _summarize_history to return empty string
    original_summarize = session._summarize_history
    session._summarize_history = lambda *args, **kwargs: ""
    
    reply = session.send("/summarize", stream=False)
    
    # Should get fallback, not empty string
    assert reply is not None
    assert reply.strip() != ""
    assert "[automatic fallback]" in reply
    
    # Restore original method
    session._summarize_history = original_summarize


def test_extract_assistant_content_empty_string_gets_fallback():
    """Test that extract_assistant_content returning empty string gets caught."""
    mock_llm = Mock()
    mock_llm.extract_assistant_content.return_value = ""  # Empty string, not None
    mock_llm.extract_tool_calls.return_value = []
    mock_llm.chat.return_value = {"choices": [{"message": {"content": ""}}]}
    mock_llm.chat_stream.return_value = iter(())
    
    session = ConversationSession(llm=mock_llm, storage=None, tool_registry=None)
    reply = session.send("test", stream=False)
    
    # Should get fallback, not empty string
    assert reply is not None
    assert reply.strip() != ""
    assert "[automatic fallback]" in reply
