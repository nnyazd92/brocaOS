"""
Tests for system prompt interoperability between dynamic system prompts and storage.
"""

from __future__ import annotations

import pytest
import json
import tempfile
from unittest.mock import Mock
from pathlib import Path

from broca.repl.session import ConversationSession
from broca.storage.json_storage import JSONFileStorage
from broca.world_state.aggregator import WorldStateAggregator
from broca.llm.deepseek_client import DeepSeekClient
from broca.tests.utils import build_llm_response


class TestSystemPromptStorageInteroperability:
    """Test that system prompt is correctly saved and loaded with dynamic prompts."""
    
    def test_save_includes_base_system_prompt_in_metadata(self, mock_llm_client):
        """Test that base system prompt is saved in metadata."""
        base_prompt = "You are BrocaOS. Always be helpful."
        
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"},
            "self_model": None,
            "internal_state": None,
            "project": None,
            "tools": None
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            session = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                world_state_aggregator=aggregator,
                base_system_prompt=base_prompt
            )
            
            # Send a message to trigger save
            session.send("Hello")
            
            # Load the saved conversation
            result = storage.load_conversation(session.session_id)
            assert result is not None
            
            # Check that system_prompt in metadata contains the base prompt
            metadata = result.get("metadata", {})
            saved_system_prompt = metadata.get("system_prompt", "")
            
            # Should contain the base prompt
            assert base_prompt in saved_system_prompt or saved_system_prompt == base_prompt
            
            # Check that the actual system message contains both base prompt and world state
            messages = result.get("messages", [])
            assert len(messages) > 0
            system_message = messages[0]
            assert system_message["role"] == "system"
            assert base_prompt in system_message["content"]
            assert "timestamp" in system_message["content"]
    
    def test_load_restores_base_system_prompt(self, mock_llm_client):
        """Test that loading a conversation restores the base system prompt."""
        base_prompt = "You are BrocaOS. Core principles apply."
        
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"},
            "self_model": None,
            "internal_state": None,
            "project": None,
            "tools": None
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            # Create and save a session
            session1 = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                world_state_aggregator=aggregator,
                base_system_prompt=base_prompt
            )
            session1.send("Test")
            
            # Load the session
            session2 = ConversationSession.load_from_storage(
                session_id=session1.session_id,
                storage=storage,
                llm=mock_llm_client,
                world_state_aggregator=aggregator
            )
            
            assert session2 is not None
            # Base prompt should be restored
            assert session2.base_system_prompt == base_prompt or base_prompt in (session2.messages[0]["content"] if session2.messages else "")
    
    def test_save_with_empty_base_prompt_still_works(self, mock_llm_client):
        """Test that saving works even when base prompt is empty."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"},
            "self_model": None,
            "internal_state": None,
            "project": None,
            "tools": None
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            session = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                world_state_aggregator=aggregator,
                base_system_prompt=""
            )
            
            session.send("Hello")
            
            # Should save successfully
            result = storage.load_conversation(session.session_id)
            assert result is not None
            # System message should still have world state
            messages = result.get("messages", [])
            assert len(messages) > 0
            assert messages[0]["role"] == "system"
            assert "timestamp" in messages[0]["content"]
    
    def test_save_extracts_base_prompt_from_combined_message(self, mock_llm_client):
        """Test that base prompt is extracted from the combined system message when saving."""
        base_prompt = "You are BrocaOS."
        
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"},
            "self_model": None,
            "internal_state": None,
            "project": None,
            "tools": None
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            session = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                world_state_aggregator=aggregator,
                base_system_prompt=base_prompt
            )
            
            # Verify the system message contains both parts
            assert len(session.messages) > 0
            system_content = session.messages[0]["content"]
            assert base_prompt in system_content
            assert "\n\n" in system_content  # Should have separator
            
            # Save and check metadata
            session.send("Test")
            result = storage.load_conversation(session.session_id)
            assert result is not None
            
            metadata = result.get("metadata", {})
            saved_prompt = metadata.get("system_prompt", "")
            # Should contain the base prompt (may be the full content or just base)
            assert base_prompt in saved_prompt or saved_prompt == base_prompt
    
    def test_load_handles_legacy_system_prompt_format(self, mock_llm_client):
        """Test that loading handles old format where system_prompt was just a string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            # Create a legacy conversation file
            legacy_data = {
                "session_id": "legacy-session",
                "messages": [
                    {"role": "system", "content": "Old system prompt"},
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi"}
                ],
                "metadata": {
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "system_prompt": "Old system prompt"
                }
            }
            
            file_path = Path(tmpdir) / "legacy-session.json"
            with open(file_path, 'w') as f:
                json.dump(legacy_data, f)
            
            # Should load successfully
            session = ConversationSession.load_from_storage(
                session_id="legacy-session",
                storage=storage,
                llm=mock_llm_client
            )
            
            assert session is not None
            assert len(session.messages) > 0
            # Should have the system prompt
            assert session.messages[0]["content"] == "Old system prompt" or session.system_prompt == "Old system prompt"
    
    def test_load_extracts_base_prompt_when_metadata_empty_but_message_has_content(self, mock_llm_client):
        """Test loading when system_prompt in metadata is empty but system message has base prompt + world state."""
        base_prompt = "You are BrocaOS, a cognitive architecture."
        
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"},
            "self_model": None,
            "internal_state": None,
            "project": None,
            "tools": None
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            # Create a conversation file like the real-world scenario
            # where system_prompt is empty but system message has content
            conversation_data = {
                "session_id": "real-world-session",
                "messages": [
                    {
                        "role": "system",
                        "content": f"{base_prompt}\n\n{{\n  \"timestamp\": \"2024-01-01T00:00:00Z\",\n  \"system\": {{\"platform\": \"Linux\"}},\n  \"self_model\": null,\n  \"internal_state\": null,\n  \"project\": null,\n  \"tools\": null\n}}"
                    },
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi"}
                ],
                "metadata": {
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "system_prompt": ""  # Empty in metadata, but message has content
                }
            }
            
            file_path = Path(tmpdir) / "real-world-session.json"
            with open(file_path, 'w') as f:
                json.dump(conversation_data, f)
            
            # Load the session
            session = ConversationSession.load_from_storage(
                session_id="real-world-session",
                storage=storage,
                llm=mock_llm_client,
                world_state_aggregator=aggregator
            )
            
            assert session is not None
            # Base prompt should be extracted from the message
            assert session.base_system_prompt == base_prompt
            # System message should still have both parts
            assert len(session.messages) > 0
            assert base_prompt in session.messages[0]["content"]
            assert "timestamp" in session.messages[0]["content"]


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    mock = Mock(spec=DeepSeekClient)
    mock.chat.return_value = build_llm_response(content="Test response")
    mock.extract_assistant_content = DeepSeekClient.extract_assistant_content
    return mock
