"""
Tests for system prompt generation with base prompt and world state structure.
"""

from __future__ import annotations

import pytest
import json
from unittest.mock import Mock, MagicMock

from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator
from broca.world_state.formatter import WorldStateFormatter
from broca.llm.deepseek_client import DeepSeekClient


class TestSystemPromptWithBasePrompt:
    """Test system prompt generation with base prompt section."""
    
    def test_base_system_prompt_prepended(self, mock_llm_client):
        """Test that base system prompt is prepended when configured."""
        base_prompt = "You are BrocaOS. Always be helpful and accurate."
        
        # Create aggregator that returns minimal world state
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "platform": "Linux",
                "python_version": "3.13.0"
            }
        }
        
        # Create session with base prompt
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt=base_prompt
        )
        
        # Check that system message contains base prompt
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        content = session.messages[0]["content"]
        
        # Base prompt should be at the start
        assert content.startswith(base_prompt)
        # World state JSON should be present
        assert "timestamp" in content
        assert "system" in content
    
    def test_empty_base_prompt_still_works(self, mock_llm_client):
        """Test that empty base prompt still works (just world state)."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"}
        }
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt=""
        )
        
        # Should still have system message with world state
        assert len(session.messages) == 1
        content = session.messages[0]["content"]
        parsed = json.loads(content)
        assert "timestamp" in parsed
    
    def test_no_base_prompt_uses_world_state_only(self, mock_llm_client):
        """Test that when no base prompt is provided, only world state is used."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"}
        }
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator
        )
        
        # Should have system message with only world state
        assert len(session.messages) == 1
        content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in content:
            json_part = content.split("\n\n", 1)[1]
        else:
            json_part = content
        parsed = json.loads(json_part)
        assert "timestamp" in parsed
        assert "system" in parsed


class TestSystemPromptWithEmptyWorldState:
    """Test system prompt generation when world state sections are empty."""
    
    def test_world_state_always_has_structure(self, mock_llm_client):
        """Test that world state always has structure even when sections are empty."""
        aggregator = Mock(spec=WorldStateAggregator)
        # Return world state with null/empty sections
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "platform": "Linux",
                "python_version": "3.13.0"
            },
            "self_model": None,
            "internal_state": None,
            "project": None,
            "tools": None
        }
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator
        )
        
        # System message should contain structured JSON
        assert len(session.messages) == 1
        content = session.messages[0]["content"]
        # Extract JSON part (may have base prompt separated by \n\n)
        if "\n\n" in content:
            json_part = content.split("\n\n", 1)[1]
        else:
            json_part = content
        parsed = json.loads(json_part)
        
        # All sections should be present (this test uses a mock that returns None values)
        assert "timestamp" in parsed
        assert "system" in parsed
        assert "self_model" in parsed
        assert parsed["self_model"] is None
        assert "internal_state" in parsed
        assert parsed["internal_state"] is None
        assert "project" in parsed
        assert parsed["project"] is None
        assert "tools" in parsed
        assert parsed["tools"] is None
    
    def test_system_prompt_with_no_self_model_or_memories(self, mock_llm_client):
        """Test system prompt when there's no self model or memories."""
        aggregator = Mock(spec=WorldStateAggregator)
        # Minimal world state - just system info
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "platform": "Linux",
                "python_version": "3.13.0",
                "working_directory": "/test"
            },
            "self_model": None,
            "internal_state": None,
            "project": None,
            "tools": None
        }
        
        base_prompt = "You are BrocaOS. Core principles: accuracy, helpfulness."
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt=base_prompt
        )
        
        # Should have both base prompt and structured world state
        assert len(session.messages) == 1
        content = session.messages[0]["content"]
        
        # Base prompt should be present
        assert base_prompt in content
        # World state structure should be present
        assert "timestamp" in content
        assert "self_model" in content
        # Should be valid JSON
        json_part = content.split("\n\n", 1)[1] if "\n\n" in content else content
        parsed = json.loads(json_part)
        assert parsed["self_model"] is None


class TestSystemPromptUpdates:
    """Test that system prompt updates correctly."""
    
    def test_system_prompt_updates_with_world_state_changes(self, mock_llm_client):
        """Test that system prompt updates when world state changes."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"}
        }
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt="Base prompt"
        )
        
        initial_content = session.messages[0]["content"]
        
        # Change world state
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T01:00:00Z",
            "system": {"platform": "Linux", "python_version": "3.13.0"}
        }
        
        # Update system prompt
        session._update_system_prompt()
        
        # Content should be updated
        updated_content = session.messages[0]["content"]
        assert updated_content != initial_content
        assert "3.13.0" in updated_content
        # Base prompt should still be present
        assert "Base prompt" in updated_content


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    mock = Mock(spec=DeepSeekClient)
    mock.chat.return_value = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Test response"
            }
        }]
    }
    return mock

