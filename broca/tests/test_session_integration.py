"""
Integration tests for ConversationSession and DeepSeekClient interaction.

Tests the full conversation flow, context preservation, error handling,
and realistic interaction patterns between session and LLM client.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import httpx

from broca.repl.session import ConversationSession
from broca.llm.deepseek_client import DeepSeekClient
from broca.tests.utils import build_llm_response, create_message_list


class TestFullConversationFlow:
    """Test complete conversation flows with mocked LLM client."""
    
    def test_multi_turn_conversation_context(self):
        """
        Test that conversation context is maintained across multiple turns.
        
        Rationale: Ensures the session correctly builds conversation history
        and passes it to the LLM on each turn, maintaining context.
        """
        # Create a mock HTTP client that captures requests
        request_history = []
        
        def proper_response(*args, **kwargs):
            messages = kwargs["json"]["messages"]
            request_history.append(messages)
            response_obj = Mock()
            response_obj.raise_for_status = Mock()
            response_obj.json.return_value = build_llm_response(
                content=f"Response to turn {len(request_history)}"
            )
            return response_obj
        
        mock_httpx = Mock()
        mock_httpx.post = Mock(side_effect=proper_response)
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        session = ConversationSession(
            system_prompt="You are a helpful assistant.",
            llm=client
        )
        
        # First turn
        session.send("Hello")
        assert len(request_history) == 1
        assert len(request_history[0]) == 2  # system, user (assistant message is in response, not request)
        assert request_history[0][0]["role"] == "system"
        assert request_history[0][1]["role"] == "user"
        assert request_history[0][1]["content"] == "Hello"
        
        # Second turn - should include full history
        session.send("What did I just say?")
        assert len(request_history) == 2
        assert len(request_history[1]) == 4  # system, user (turn 1), assistant (turn 1), user (turn 2)
        assert request_history[1][0]["role"] == "system"
        assert request_history[1][3]["content"] == "What did I just say?"
    
    def test_system_prompt_persistence(self):
        """
        Test that system prompt persists throughout the conversation.
        
        Rationale: Ensures system instructions remain in context for all turns.
        """
        system_prompt = "You are a code review assistant. Always be constructive."
        request_messages = []
        
        def capture_messages(*args, **kwargs):
            msgs = kwargs["json"]["messages"]
            request_messages.append(msgs)
            response_obj = Mock()
            response_obj.raise_for_status = Mock()
            response_obj.json.return_value = build_llm_response(content="Response")
            return response_obj
        
        mock_httpx = Mock()
        mock_httpx.post = Mock(side_effect=capture_messages)
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        session = ConversationSession(system_prompt=system_prompt, llm=client)
        
        session.send("First message")
        session.send("Second message")
        session.send("Third message")
        
        # Verify system prompt is in every request
        for messages in request_messages:
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == system_prompt
    
    def test_conversation_statistics_accuracy(self):
        """
        Test that conversation statistics remain accurate during conversation.
        
        Rationale: Ensures context tracking works correctly for monitoring purposes.
        """
        mock_httpx = Mock()
        response_obj = Mock()
        response_obj.raise_for_status = Mock()
        response_obj.json.return_value = build_llm_response(content="Response")
        mock_httpx.post.return_value = response_obj
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        session = ConversationSession(
            system_prompt="System",
            llm=client
        )
        
        # Verify initial stats
        stats = session._current_context_stats()
        assert stats["messages_total"] == 1
        assert stats["messages_system"] == 1
        
        # After first turn
        session.send("First")
        stats = session._current_context_stats()
        assert stats["messages_total"] == 3
        assert stats["messages_user"] == 1
        assert stats["messages_assistant"] == 1
        
        # After second turn
        session.send("Second")
        stats = session._current_context_stats()
        assert stats["messages_total"] == 5
        assert stats["messages_user"] == 2
        assert stats["messages_assistant"] == 2


class TestErrorPropagation:
    """Test error handling and propagation from LLM to session."""
    
    def test_http_error_propagation(self):
        """
        Test that HTTP errors from LLM client are handled gracefully.
        
        Rationale: Ensures errors are handled gracefully and return user-friendly messages.
        """
        mock_httpx = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request",
            request=Mock(),
            response=Mock(status_code=400)
        )
        mock_httpx.post.return_value = mock_response
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        session = ConversationSession(llm=client)
        
        # Should not raise, should return error message
        response = session.send("Test message")
        
        # Should return user-friendly error message
        assert "error" in response.lower() or "apologize" in response.lower()
        # Session should have user message and error assistant response
        assert len(session.messages) == 2  # user message + error assistant message
        assert session.messages[0]["role"] == "user"
        assert session.messages[1]["role"] == "assistant"
    
    def test_network_error_propagation(self):
        """
        Test that network errors from LLM client are handled gracefully.
        
        Rationale: Ensures network failures are handled gracefully and return user-friendly messages.
        """
        mock_httpx = Mock()
        mock_httpx.post.side_effect = httpx.NetworkError("Connection failed")
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        session = ConversationSession(llm=client)
        
        # Should not raise, should return error message
        response = session.send("Test message")
        
        # Should return user-friendly error message
        assert "network" in response.lower() or "connection" in response.lower() or "error" in response.lower()
        # Session should have user message and error assistant response
        assert len(session.messages) == 2  # user message + error assistant message
        assert session.messages[0]["role"] == "user"
        assert session.messages[1]["role"] == "assistant"
        assert session.messages[0]["role"] == "user"
    
    def test_malformed_response_handling(self):
        """
        Test that malformed LLM responses are handled gracefully.
        
        Rationale: Ensures the session continues working even with unexpected response formats.
        """
        mock_httpx = Mock()
        response_obj = Mock()
        response_obj.raise_for_status = Mock()
        response_obj.json.return_value = {"invalid": "structure"}  # Missing choices
        mock_httpx.post.return_value = response_obj
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        session = ConversationSession(llm=client)
        
        # Should not raise, but return empty string
        response = session.send("Test message")
        
        assert response == ""
        assert len(session.messages) == 2  # user + empty assistant
        assert session.messages[1]["content"] == ""


class TestRealisticScenarios:
    """Test realistic usage scenarios."""
    
    def test_code_review_session(self):
        """
        Test a realistic code review conversation session.
        
        Rationale: Ensures the session works correctly in real-world usage patterns.
        """
        responses = [
            "I'll review your code.",
            "Consider adding error handling here.",
            "The logic looks good, but add type hints."
        ]
        response_index = [0]
        
        def get_response(*args, **kwargs):
            idx = response_index[0]
            response_index[0] += 1
            response_obj = Mock()
            response_obj.raise_for_status = Mock()
            response_obj.json.return_value = build_llm_response(content=responses[idx])
            return response_obj
        
        mock_httpx = Mock()
        mock_httpx.post = Mock(side_effect=get_response)
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        session = ConversationSession(
            system_prompt="You are a code review assistant. Be constructive and specific.",
            llm=client
        )
        
        # Simulate code review conversation
        session.send("Can you review this code?")
        session.send("What about error handling?")
        session.send("Any other suggestions?")
        
        # Verify conversation built up correctly
        assert len(session.messages) == 7  # system + 3 turns
        stats = session._current_context_stats()
        assert stats["messages_user"] == 3
        assert stats["messages_assistant"] == 3
    
    def test_long_conversation_context_growth(self):
        """
        Test that context grows correctly in a long conversation.
        
        Rationale: Ensures the session handles extended conversations without issues.
        """
        mock_httpx = Mock()
        response_obj = Mock()
        response_obj.raise_for_status = Mock()
        response_obj.json.return_value = build_llm_response(content="Ok")
        mock_httpx.post.return_value = response_obj
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        session = ConversationSession(llm=client)
        
        # Simulate 10-turn conversation
        for i in range(10):
            session.send(f"Message {i}")
        
        stats = session._current_context_stats()
        assert stats["messages_total"] == 20  # 10 user + 10 assistant
        assert stats["messages_user"] == 10
        assert stats["messages_assistant"] == 10
        
        # Verify all messages are in history
        assert len(session.messages) == 20

