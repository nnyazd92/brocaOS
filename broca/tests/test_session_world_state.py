"""
Tests for session world state integration.
"""

from __future__ import annotations

import pytest
import json
from unittest.mock import Mock, MagicMock, patch

from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator
from broca.world_state.formatter import WorldStateFormatter
from broca.self_model.model import SelfModel


class TestSessionWorldState:
    """Test world state integration in ConversationSession."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        mock = Mock()
        mock.chat.return_value = {
            "choices": [{"message": {"content": "Test response", "role": "assistant"}}]
        }
        mock.extract_assistant_content.return_value = "Test response"
        mock.extract_tool_calls.return_value = []
        return mock
    
    @pytest.fixture
    def mock_world_state_aggregator(self):
        """Create a mock world state aggregator."""
        mock = Mock(spec=WorldStateAggregator)
        mock.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "datetime": "2024-01-01T12:00:00Z",
                "platform": "Linux",
            },
            "self_model": {
                "summary": "Test summary",
            },
        }
        return mock
    
    def test_init_with_world_state_aggregator(self, mock_llm_client, mock_world_state_aggregator):
        """Test initializing session with world state aggregator."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        assert session.world_state_aggregator is mock_world_state_aggregator
        assert session._world_state_formatter is not None
        
        # Verify aggregator was called during initialization
        mock_world_state_aggregator.aggregate.assert_called_once()
        
        # Verify system message contains only world state as JSON (no base prompt)
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        # Check that it's valid JSON with expected structure
        system_content = session.messages[0]["content"]
        parsed = json.loads(system_content)
        assert "timestamp" in parsed
        assert "system" in parsed or "self_model" in parsed
    
    def test_init_without_world_state_aggregator(self, mock_llm_client):
        """Test initializing session without world state aggregator."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
        )
        
        assert session.world_state_aggregator is None
        assert session._world_state_formatter is None
        # Without aggregator, no system message should be created
        assert len(session.messages) == 0
    
    def test_init_populates_world_state_before_first_message(self, mock_llm_client, mock_world_state_aggregator):
        """Test that world state is populated at initialization, before any user message."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Verify aggregator was called during initialization
        assert mock_world_state_aggregator.aggregate.call_count == 1
        
        # Verify system message exists and contains only world state as JSON
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Check that it's valid JSON
        parsed = json.loads(system_content)
        assert "timestamp" in parsed
        assert "system" in parsed or "self_model" in parsed
        
        # Verify no user messages yet
        user_messages = [m for m in session.messages if m.get("role") == "user"]
        assert len(user_messages) == 0
    
    def test_init_populates_world_state_without_initial_prompt(self, mock_llm_client, mock_world_state_aggregator):
        """Test that world state is populated even when no initial system prompt is provided."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Verify aggregator was called
        assert mock_world_state_aggregator.aggregate.call_count == 1
        
        # Verify system message was created with only world state as JSON
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Check that it's valid JSON
        parsed = json.loads(system_content)
        assert "timestamp" in parsed
    
    def test_update_system_prompt_with_aggregator(self, mock_llm_client, mock_world_state_aggregator):
        """Test updating system prompt with world state aggregator."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Reset call count (aggregator was called during init)
        initial_call_count = mock_world_state_aggregator.aggregate.call_count
        mock_world_state_aggregator.aggregate.reset_mock()
        
        # Call update method
        session._update_system_prompt()
        
        # Verify aggregator was called again
        mock_world_state_aggregator.aggregate.assert_called_once()
        
        # Verify system message contains only world state as JSON (no base prompt)
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Check that it's valid JSON
        parsed = json.loads(system_content)
        assert "timestamp" in parsed
    
    def test_update_system_prompt_without_aggregator(self, mock_llm_client):
        """Test updating system prompt without aggregator (should do nothing)."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
        )
        
        original_messages = session.messages.copy()
        
        # Call update method
        session._update_system_prompt()
        
        # Should not change messages (no aggregator, so no system message)
        assert session.messages == original_messages
    
    def test_update_system_prompt_creates_system_message(self, mock_llm_client, mock_world_state_aggregator):
        """Test that update creates system message if none exists."""
        # Create session without system prompt but with aggregator
        # This will create system message during init
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # System message should be created during initialization
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Check that it's valid JSON
        parsed = json.loads(system_content)
        assert "timestamp" in parsed
        
        # Reset and manually remove system message to test creation
        session.messages = []
        mock_world_state_aggregator.aggregate.reset_mock()
        
        # Call update method
        session._update_system_prompt()
        
        # Should create system message with only world state as JSON
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        system_content = session.messages[0]["content"]
        # Check that it's valid JSON
        parsed = json.loads(system_content)
        assert "timestamp" in parsed
    
    def test_update_system_prompt_handles_errors(self, mock_llm_client):
        """Test that update handles errors gracefully."""
        # Create aggregator that raises error
        mock_aggregator = Mock(spec=WorldStateAggregator)
        mock_aggregator.aggregate.side_effect = Exception("Test error")
        
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_aggregator,
        )
        
        # On init, aggregator is called and may fail, but session should still be created
        # If there's a system message from init, it should remain unchanged on error
        # If no system message exists, update should not create one on error
        original_messages_count = len(session.messages)
        
        # Call update method (should not raise)
        session._update_system_prompt()
        
        # Should not change messages on error (either keep existing or remain empty)
        assert len(session.messages) == original_messages_count
    
    def test_send_updates_system_prompt_before_llm_call(self, mock_llm_client, mock_world_state_aggregator):
        """Test that send() updates system prompt before LLM call."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Reset call count
        mock_world_state_aggregator.aggregate.reset_mock()
        
        # Send a message
        session.send("Test user message")
        
        # Verify aggregator was called (before LLM call)
        assert mock_world_state_aggregator.aggregate.called
        
        # Verify system message contains only world state as JSON
        system_content = session.messages[0]["content"]
        parsed = json.loads(system_content)
        assert "timestamp" in parsed
    
    def test_send_updates_system_prompt_each_iteration(self, mock_llm_client, mock_world_state_aggregator):
        """Test that system prompt is updated before each LLM call iteration."""
        # Simple test: verify aggregator is called during send
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Reset call count
        mock_world_state_aggregator.aggregate.reset_mock()
        
        # Send a message
        session.send("Test user message")
        
        # Verify aggregator was called (at least once before LLM call)
        assert mock_world_state_aggregator.aggregate.call_count >= 1
    
    def test_system_prompt_always_first_message(self, mock_llm_client, mock_world_state_aggregator):
        """Test that system prompt is always the first message."""
        session = ConversationSession(
            system_prompt=None,
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
        )
        
        # Add some messages
        session.messages.append({"role": "user", "content": "User message"})
        session.messages.append({"role": "assistant", "content": "Assistant message"})
        
        # Update system prompt
        session._update_system_prompt()
        
        # System message should be first
        assert session.messages[0]["role"] == "system"
        assert session.messages[1]["role"] == "user"
        assert session.messages[2]["role"] == "assistant"
        # System message should contain only world state as JSON
        system_content = session.messages[0]["content"]
        parsed = json.loads(system_content)
        assert "timestamp" in parsed

