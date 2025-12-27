"""
Property-based tests for web_api.py using Hypothesis.

Tests invariants that should hold for all inputs.
"""

from __future__ import annotations

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

# Import web_api functions
from broca.web_api import stream_response, create_session, get_runtime, get_storage
from broca.repl.session import ConversationSession


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


@pytest.fixture
def mock_session(mock_llm_client):
    """Mock session for testing."""
    session = Mock(spec=ConversationSession)
    session.messages = []
    session.llm = mock_llm_client
    session.internal_sensing_framework = None
    session._update_system_prompt = Mock()
    session._get_messages_for_llm = Mock(return_value=[])
    session._current_response_id = "response_1"
    return session


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.chat.return_value = {"choices": [{"message": {"content": "test response"}}]}
    client.extract_assistant_content = Mock(return_value="test response")
    client.extract_tool_calls = Mock(return_value=[])
    return client


class TestStreamResponseProperties:
    """Property: Stream response always yields valid JSON."""
    
    @patch('broca.web_api.get_runtime')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.create_session')
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        user_message=st.text(min_size=1, max_size=500),
        conversation_id=st.text(min_size=1, max_size=50)
    )
    def test_stream_response_yields_valid_json(
        self, mock_create_session, mock_get_storage, mock_get_runtime,
        mock_runtime, mock_storage, mock_session, mock_llm_client,
        user_message, conversation_id
    ):
        """Property: Stream response always yields valid JSON."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_session.llm = mock_llm_client
        mock_session.llm.extract_assistant_content.return_value = "Test response"
        
        # Collect all chunks
        chunks = list(stream_response(conversation_id, user_message))
        
        # Each chunk should be valid JSON
        for chunk in chunks:
            if chunk.strip():  # Skip empty chunks
                try:
                    data = json.loads(chunk.strip())
                    assert isinstance(data, dict)
                    assert "type" in data
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in chunk: {chunk}")
    
    @patch('broca.web_api.get_runtime')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.create_session')
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        user_message=st.text(min_size=1, max_size=500),
        conversation_id=st.text(min_size=1, max_size=50)
    )
    def test_stream_response_ends_with_done(
        self, mock_create_session, mock_get_storage, mock_get_runtime,
        mock_runtime, mock_storage, mock_session, mock_llm_client,
        user_message, conversation_id
    ):
        """Property: Stream response always ends with 'done' message."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_session.llm = mock_llm_client
        mock_session.llm.extract_assistant_content.return_value = "Test response"
        
        # Collect all chunks
        chunks = list(stream_response(conversation_id, user_message))
        
        # Last chunk should be 'done'
        assert len(chunks) > 0
        last_chunk = chunks[-1].strip()
        if last_chunk:
            data = json.loads(last_chunk)
            assert data["type"] == "done"
            assert data["conversation_id"] == conversation_id
    
    @patch('broca.web_api.get_runtime')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.create_session')
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        user_message=st.text(min_size=1, max_size=500),
        conversation_id=st.text(min_size=1, max_size=50)
    )
    def test_conversation_id_consistent_throughout_stream(
        self, mock_create_session, mock_get_storage, mock_get_runtime,
        mock_runtime, mock_storage, mock_session, mock_llm_client,
        user_message, conversation_id
    ):
        """Property: Conversation ID is consistent throughout stream."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_session.llm = mock_llm_client
        mock_session.llm.extract_assistant_content.return_value = "Test response"
        
        # Collect all chunks
        chunks = list(stream_response(conversation_id, user_message))
        
        # All chunks should have same conversation_id
        for chunk in chunks:
            if chunk.strip():
                try:
                    data = json.loads(chunk.strip())
                    if "conversation_id" in data:
                        assert data["conversation_id"] == conversation_id
                except json.JSONDecodeError:
                    pass  # Skip invalid JSON (shouldn't happen, but be defensive)
    
    @patch('broca.web_api.get_runtime')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.create_session')
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        user_message=st.text(min_size=1, max_size=500),
        conversation_id=st.text(min_size=1, max_size=50)
    )
    def test_internal_sensing_integration_doesnt_break(
        self, mock_create_session, mock_get_storage, mock_get_runtime,
        mock_runtime, mock_storage, mock_session, mock_llm_client,
        user_message, conversation_id
    ):
        """Property: Internal sensing integration doesn't break on various inputs."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_session.llm = mock_llm_client
        mock_session.llm.extract_assistant_content.return_value = "Test response"
        
        # Mock internal sensing framework (can be None or present)
        mock_session.internal_sensing_framework = None
        
        # Should not raise exception
        try:
            chunks = list(stream_response(conversation_id, user_message))
            assert len(chunks) > 0  # Should yield at least done message
        except Exception as e:
            pytest.fail(f"Internal sensing integration should not break: {e}")
    
    @patch('broca.web_api.get_runtime')
    @patch('broca.web_api.get_storage')
    @patch('broca.web_api.create_session')
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        response_content=st.text(min_size=0, max_size=1000),
        user_message=st.text(min_size=1, max_size=200)
    )
    def test_stream_response_handles_various_response_lengths(
        self, mock_create_session, mock_get_storage, mock_get_runtime,
        mock_runtime, mock_storage, mock_session, mock_llm_client,
        response_content, user_message
    ):
        """Property: Stream response handles various response content lengths."""
        mock_get_runtime.return_value = mock_runtime
        mock_get_storage.return_value = mock_storage
        mock_create_session.return_value = mock_session
        
        mock_session.llm = mock_llm_client
        mock_session.llm.extract_assistant_content.return_value = response_content
        
        conversation_id = "test_conv"
        
        # Should not raise exception
        try:
            chunks = list(stream_response(conversation_id, user_message))
            # Should have text chunks if response_content is non-empty
            if response_content:
                text_chunks = [c for c in chunks if c.strip() and json.loads(c.strip()).get("type") == "text"]
                assert len(text_chunks) > 0 or len(response_content) == 0
        except Exception as e:
            pytest.fail(f"Should handle various response lengths: {e}")

