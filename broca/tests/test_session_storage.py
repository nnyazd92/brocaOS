"""
Integration tests for ConversationSession with storage.

Tests the integration between ConversationSession and storage backends,
including auto-save, session ID generation, and loading from storage.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock
import pytest

from broca.repl.session import ConversationSession
from broca.storage.json_storage import JSONFileStorage
from broca.tests.utils import build_llm_response


class TestConversationSessionWithStorage:
    """Test ConversationSession with storage integration."""
    
    def test_session_without_storage_backward_compatible(self, mock_llm_client: Mock):
        """
        Test that session works without storage (backward compatibility).
        
        Rationale: Ensures existing code continues to work without changes.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(system_prompt="System", llm=mock_llm_client)
        
        response = session.send("Hello")
        
        assert response == "Response"
        assert session.storage is None
        assert session.session_id is not None  # Should still generate ID
    
    def test_session_id_generation(self, mock_llm_client: Mock):
        """
        Test that session ID is auto-generated when not provided.
        
        Rationale: Ensures each session gets a unique identifier.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(llm=mock_llm_client)
        
        assert session.session_id is not None
        assert len(session.session_id) > 0
    
    def test_session_id_custom(self, mock_llm_client: Mock):
        """
        Test that custom session ID can be provided.
        
        Rationale: Ensures sessions can be created with specific IDs.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(session_id="custom-id", llm=mock_llm_client)
        
        assert session.session_id == "custom-id"
    
    def test_auto_save_after_send(self, mock_llm_client: Mock):
        """
        Test that conversation is auto-saved after each send() call.
        
        Rationale: Ensures conversations are persisted automatically.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            session = ConversationSession(
                system_prompt="System",
                llm=mock_llm_client,
                storage=storage,
                session_id="test-session"
            )
            
            session.send("Hello")
            
            # Verify conversation was saved
            result = storage.load_conversation("test-session")
            assert result is not None
            assert len(result["messages"]) == 3  # system, user, assistant
            assert result["messages"][1]["content"] == "Hello"
            assert result["messages"][2]["content"] == "Response"
    
    def test_auto_save_multiple_turns(self, mock_llm_client: Mock):
        """
        Test that multiple turns are saved correctly.
        
        Rationale: Ensures conversation history accumulates in storage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            session = ConversationSession(
                system_prompt="System",
                llm=mock_llm_client,
                storage=storage,
                session_id="multi-turn"
            )
            
            session.send("First")
            session.send("Second")
            session.send("Third")
            
            # Verify all messages are saved
            result = storage.load_conversation("multi-turn")
            assert result is not None
            assert len(result["messages"]) == 7  # system + 3 turns
            
            # Check that messages are in order
            assert result["messages"][1]["content"] == "First"
            assert result["messages"][3]["content"] == "Second"
            assert result["messages"][5]["content"] == "Third"
    
    def test_save_includes_metadata(self, mock_llm_client: Mock):
        """
        Test that saved conversation includes metadata.
        
        Rationale: Ensures timestamps and system prompt are preserved.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            session = ConversationSession(
                system_prompt="Test system prompt",
                llm=mock_llm_client,
                storage=storage,
                session_id="metadata-test"
            )
            
            session.send("Hello")
            
            result = storage.load_conversation("metadata-test")
            assert result is not None
            metadata = result["metadata"]
            
            assert metadata["system_prompt"] == "Test system prompt"
            assert "created_at" in metadata
            assert "updated_at" in metadata
            assert metadata["created_at"] == session.created_at
            assert metadata["updated_at"] == session.updated_at
    
    def test_save_updates_timestamp(self, mock_llm_client: Mock):
        """
        Test that updated_at timestamp is updated on each send().
        
        Rationale: Ensures timestamps reflect conversation activity.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            session = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                session_id="timestamp-test"
            )
            
            initial_updated = session.updated_at
            session.send("First")
            first_updated = session.updated_at
            
            assert first_updated != initial_updated
            
            session.send("Second")
            second_updated = session.updated_at
            
            assert second_updated != first_updated
    
    def test_save_error_does_not_break_session(self, mock_llm_client: Mock):
        """
        Test that storage errors don't break the session.
        
        Rationale: Ensures REPL continues working even if storage fails.
        """
        mock_storage = Mock()
        mock_storage.save_conversation.side_effect = Exception("Storage error")
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        
        session = ConversationSession(
            llm=mock_llm_client,
            storage=mock_storage,
            session_id="error-test"
        )
        
        # Should not raise, should continue working
        response = session.send("Hello")
        
        assert response == "Response"
        assert len(session.messages) == 2  # user + assistant


class TestConversationSessionLoadFromStorage:
    """Test loading conversations from storage."""
    
    def test_load_from_storage_success(self, mock_llm_client: Mock):
        """
        Test loading a conversation from storage.
        
        Rationale: Ensures conversations can be restored from storage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            # Create and save a conversation
            original_session = ConversationSession(
                system_prompt="System prompt",
                llm=mock_llm_client,
                storage=storage,
                session_id="load-test"
            )
            original_session.send("First message")
            original_session.send("Second message")
            
            # Load the conversation
            loaded_session = ConversationSession.load_from_storage(
                session_id="load-test",
                storage=storage,
                llm=mock_llm_client
            )
            
            assert loaded_session is not None
            assert loaded_session.session_id == "load-test"
            assert loaded_session.system_prompt == "System prompt"
            assert len(loaded_session.messages) == 5  # system + 2 turns
            assert loaded_session.messages[1]["content"] == "First message"
            assert loaded_session.messages[3]["content"] == "Second message"
    
    def test_load_from_storage_not_found(self, mock_llm_client: Mock):
        """
        Test loading a non-existent conversation returns None.
        
        Rationale: Ensures graceful handling of missing conversations.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            loaded_session = ConversationSession.load_from_storage(
                session_id="nonexistent",
                storage=storage,
                llm=mock_llm_client
            )
            
            assert loaded_session is None
    
    def test_load_from_storage_preserves_system_prompt(self, mock_llm_client: Mock):
        """
        Test that system prompt is preserved when loading.
        
        Rationale: Ensures system instructions are restored correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            system_prompt = "You are a helpful assistant."
            original_session = ConversationSession(
                system_prompt=system_prompt,
                llm=mock_llm_client,
                storage=storage,
                session_id="system-test"
            )
            original_session.send("Hello")
            
            loaded_session = ConversationSession.load_from_storage(
                session_id="system-test",
                storage=storage,
                llm=mock_llm_client
            )
            
            assert loaded_session is not None
            assert loaded_session.system_prompt == system_prompt
            assert loaded_session.messages[0]["role"] == "system"
            assert loaded_session.messages[0]["content"] == system_prompt
    
    def test_load_from_storage_preserves_timestamps(self, mock_llm_client: Mock):
        """
        Test that timestamps are preserved when loading.
        
        Rationale: Ensures metadata is correctly restored.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            original_session = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                session_id="timestamp-load-test"
            )
            original_session.send("Hello")
            
            original_created = original_session.created_at
            original_updated = original_session.updated_at
            
            loaded_session = ConversationSession.load_from_storage(
                session_id="timestamp-load-test",
                storage=storage,
                llm=mock_llm_client
            )
            
            assert loaded_session is not None
            assert loaded_session.created_at == original_created
            assert loaded_session.updated_at == original_updated
    
    def test_load_from_storage_continues_conversation(self, mock_llm_client: Mock):
        """
        Test that loaded session can continue the conversation.
        
        Rationale: Ensures loaded sessions are fully functional.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            # Create and save initial conversation
            session1 = ConversationSession(
                system_prompt="System",
                llm=mock_llm_client,
                storage=storage,
                session_id="continue-test"
            )
            session1.send("First")
            
            # Load and continue
            session2 = ConversationSession.load_from_storage(
                session_id="continue-test",
                storage=storage,
                llm=mock_llm_client
            )
            
            assert session2 is not None
            session2.send("Second")
            
            # Verify both messages are in storage
            result = storage.load_conversation("continue-test")
            assert result is not None
            assert len(result["messages"]) == 5  # system + 2 turns
            assert result["messages"][1]["content"] == "First"
            assert result["messages"][3]["content"] == "Second"
    
    def test_load_from_storage_without_system_prompt(self, mock_llm_client: Mock):
        """
        Test loading conversation that had no system prompt.
        
        Rationale: Ensures sessions without system prompts load correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            original_session = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                session_id="no-system-test"
            )
            original_session.send("Hello")
            
            loaded_session = ConversationSession.load_from_storage(
                session_id="no-system-test",
                storage=storage,
                llm=mock_llm_client
            )
            
            assert loaded_session is not None
            assert loaded_session.system_prompt is None
            assert len(loaded_session.messages) == 2  # user + assistant (no system)


class TestConversationSessionStorageIntegration:
    """Test complex storage integration scenarios."""
    
    def test_multiple_sessions_different_ids(self, mock_llm_client: Mock):
        """
        Test that multiple sessions with different IDs are stored separately.
        
        Rationale: Ensures session isolation in storage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            session1 = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                session_id="session-1"
            )
            session1.send("Message 1")
            
            session2 = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                session_id="session-2"
            )
            session2.send("Message 2")
            
            # Verify both are stored separately
            result1 = storage.load_conversation("session-1")
            result2 = storage.load_conversation("session-2")
            
            assert result1 is not None
            assert result2 is not None
            assert result1["messages"][0]["content"] == "Message 1"
            assert result2["messages"][0]["content"] == "Message 2"
    
    def test_storage_persistence_across_sessions(self, mock_llm_client: Mock):
        """
        Test that storage persists across different session instances.
        
        Rationale: Ensures storage is truly persistent.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            mock_llm_client.chat.return_value = build_llm_response(content="Response")
            
            # Create first session
            session1 = ConversationSession(
                llm=mock_llm_client,
                storage=storage,
                session_id="persist-test"
            )
            session1.send("First")
            session1.send("Second")
            
            # Create new session instance (simulating restart)
            session2 = ConversationSession.load_from_storage(
                session_id="persist-test",
                storage=storage,
                llm=mock_llm_client
            )
            
            assert session2 is not None
            assert len(session2.messages) == 4  # 2 turns (2 user + 2 assistant, no system)
            assert session2.messages[0]["content"] == "First"
            assert session2.messages[2]["content"] == "Second"

