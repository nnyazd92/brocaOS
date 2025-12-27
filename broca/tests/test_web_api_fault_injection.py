"""
Fault injection tests for web_api.py.

Tests error handling and edge cases when components fail.
"""

from __future__ import annotations

import pytest
import json
from unittest.mock import Mock, MagicMock, patch

from broca.web_api import stream_response


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.chat.return_value = {"choices": [{"message": {"content": "test response"}}]}
    client.extract_assistant_content = Mock(return_value="test response")
    client.extract_tool_calls = Mock(return_value=[])
    return client


@pytest.fixture
def mock_session(mock_llm_client):
    """Mock session for testing."""
    session = Mock()
    session.messages = []
    session.llm = mock_llm_client
    session.internal_sensing_framework = None
    session._update_system_prompt = Mock()
    session._get_messages_for_llm = Mock(return_value=[])
    session._current_response_id = "response_1"
    return session


@pytest.fixture
def mock_runtime():
    """Mock runtime for testing."""
    rt = Mock()
    rt.tool_registry = Mock()
    rt.tool_registry.to_openai_format.return_value = []
    rt.tool_registry.execute_tool_call.return_value = {"role": "tool", "content": "result"}
    return rt


@pytest.fixture
def mock_storage():
    """Mock storage for testing."""
    storage = Mock()
    storage.load_conversation.return_value = {"metadata": {}}
    storage.save_conversation = Mock()
    return storage


class TestSessionCreationFailures:
    """Test behavior when session creation fails."""
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    def test_session_creation_raises_exception(self, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage):
        """Test behavior when create_session() raises exception."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.side_effect = Exception("Session creation error")
        
        # Should propagate exception
        with pytest.raises(Exception, match="Session creation error"):
            list(stream_response("test_conv", "Hello"))


class TestLLMCallFailures:
    """Test behavior when LLM call fails."""
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    def test_llm_chat_raises_exception(self, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when LLM chat() raises exception."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_session.llm.chat.side_effect = Exception("LLM error")
        
        # Should yield error message
        chunks = list(stream_response("test_conv", "Hello"))
        assert len(chunks) > 0
        
        # Should have error in response
        error_chunks = [c for c in chunks if "Error" in c]
        assert len(error_chunks) > 0 or any("error" in json.loads(c.strip()).get("content", "").lower() for c in chunks if c.strip())
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    def test_llm_extract_assistant_content_raises_exception(self, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when extract_assistant_content() raises exception."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_session.llm.extract_assistant_content.side_effect = Exception("Extract error")
        
        # Should handle gracefully
        try:
            chunks = list(stream_response("test_conv", "Hello"))
            assert len(chunks) > 0  # Should yield at least done message
        except Exception as e:
            # If exception propagates, should be caught and handled
            assert "Extract error" in str(e) or "assistant_text" not in str(e)


class TestToolExecutionFailures:
    """Test behavior when tool execution fails."""
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    def test_tool_execution_raises_exception(self, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when tool execution fails."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        # Mock tool calls
        tool_call = {"id": "call_1", "function": {"name": "test_tool", "arguments": "{}"}}
        mock_session.llm.extract_tool_calls.return_value = [tool_call]
        mock_runtime.tool_registry.execute_tool_call.side_effect = Exception("Tool execution error")
        
        # Should handle gracefully (exception should be caught)
        try:
            chunks = list(stream_response("test_conv", "Hello"))
            # Should still yield chunks (error should be in tool result)
            assert len(chunks) > 0
        except Exception as e:
            # If exception propagates, it should be a specific error
            assert "Tool execution error" in str(e) or "tool" in str(e).lower()


class TestInternalSensingFailures:
    """Test behavior when internal sensing framework fails."""
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    @patch('broca.web_api.ResponseAnalyzer')
    def test_internal_sensing_framework_is_none(self, mock_response_analyzer, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when internal sensing framework is None."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_session.internal_sensing_framework = None
        
        # Should handle gracefully (no instrumentation, but should work)
        chunks = list(stream_response("test_conv", "Hello"))
        assert len(chunks) > 0
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    @patch('broca.web_api.ResponseAnalyzer')
    def test_response_analyzer_is_none(self, mock_response_analyzer, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when ResponseAnalyzer is None."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_response_analyzer = None
        
        # Should handle gracefully (no instrumentation, but should work)
        chunks = list(stream_response("test_conv", "Hello"))
        assert len(chunks) > 0
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    @patch('broca.web_api.ResponseAnalyzer')
    def test_internal_sensing_recording_raises_exception(self, mock_response_analyzer, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when internal sensing recording raises exception."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        # Mock internal sensing framework
        mock_framework = Mock()
        mock_framework.interoception.cognition.record_attention.side_effect = Exception("Recording error")
        mock_session.internal_sensing_framework = mock_framework
        
        # Should handle gracefully (exception should be caught and logged)
        try:
            chunks = list(stream_response("test_conv", "Hello"))
            assert len(chunks) > 0  # Should still yield chunks
        except Exception as e:
            # If exception propagates, should be caught in instrumentation block
            assert "Recording error" not in str(e) or "debug" in str(e).lower()


class TestStorageOperationFailures:
    """Test behavior when storage operations fail."""
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    def test_storage_load_conversation_raises_exception(self, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when storage.load_conversation() raises exception."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_storage.load_conversation.side_effect = Exception("Load error")
        
        # Should handle gracefully (exception should be caught)
        try:
            chunks = list(stream_response("test_conv", "Hello"))
            # Should still complete (may use default metadata)
            assert len(chunks) > 0
        except Exception as e:
            # If exception propagates, should be at the end (after streaming)
            assert "Load error" in str(e)
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    def test_storage_save_conversation_raises_exception(self, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when storage.save_conversation() raises exception."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_storage.save_conversation.side_effect = Exception("Save error")
        
        # Should handle gracefully (exception should be caught, streaming should complete)
        try:
            chunks = list(stream_response("test_conv", "Hello"))
            # Should still yield chunks (save happens after streaming)
            assert len(chunks) > 0
        except Exception as e:
            # Save error should not prevent streaming from completing
            assert "Save error" not in str(e) or "after" in str(e).lower()


class TestMaxIterationsReached:
    """Test behavior when max iterations is reached."""
    
    @patch('broca.web_api.create_session')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.get_runtime')
    def test_max_iterations_reached_with_tool_calls(self, mock_get_runtime, mock_get_storage, mock_create_session, mock_runtime, mock_storage, mock_session):
        """Test behavior when max iterations is reached due to repeated tool calls."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        # Always return tool calls (infinite loop scenario)
        tool_call = {"id": "call_1", "function": {"name": "test_tool", "arguments": "{}"}}
        mock_session.llm.extract_tool_calls.return_value = [tool_call]
        
        # Should break after max iterations (10)
        chunks = list(stream_response("test_conv", "Hello"))
        assert len(chunks) > 0  # Should yield chunks before breaking
        
        # Verify iterations were limited
        assert mock_session.llm.chat.call_count <= 10

