"""
Tests for conversation storage implementations.

Tests the storage abstraction and JSONFileStorage implementation.
"""

from __future__ import annotations

import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from broca.storage.json_storage import JSONFileStorage
from broca.storage import ConversationStorage
from broca.tests.utils import create_message_list


class TestJSONFileStorageInitialization:
    """Test JSONFileStorage initialization."""
    
    def test_init_creates_directory(self):
        """
        Test that initialization creates storage directory if it doesn't exist.
        
        Rationale: Ensures storage directory is created automatically.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_conversations"
            storage = JSONFileStorage(storage_path=str(storage_path))
            
            assert storage_path.exists()
            assert storage_path.is_dir()
    
    def test_init_with_existing_directory(self):
        """
        Test that initialization works with existing directory.
        
        Rationale: Ensures storage works when directory already exists.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "existing"
            storage_path.mkdir()
            
            storage = JSONFileStorage(storage_path=str(storage_path))
            assert storage_path.exists()
    
    def test_init_stores_path(self):
        """
        Test that storage path is stored correctly.
        
        Rationale: Ensures storage path is accessible.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test"
            storage = JSONFileStorage(storage_path=str(storage_path))
            
            assert storage.storage_path == storage_path


class TestJSONFileStorageSaveConversation:
    """Test saving conversations to JSON files."""
    
    def test_save_conversation_creates_file(self):
        """
        Test that save_conversation creates a JSON file.
        
        Rationale: Ensures conversations are persisted to disk.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages = create_message_list(
                system="System prompt",
                user_messages=["Hello"],
                assistant_messages=["Hi there"]
            )
            metadata = {
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "system_prompt": "System prompt"
            }
            
            storage.save_conversation("test-session-1", messages, metadata)
            
            file_path = Path(tmpdir) / "test-session-1.json"
            assert file_path.exists()
    
    def test_save_conversation_file_format(self):
        """
        Test that saved file contains correct data structure.
        
        Rationale: Ensures file format matches expected structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages = create_message_list(
                system="System",
                user_messages=["User message"],
                assistant_messages=["Assistant reply"]
            )
            metadata = {
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "system_prompt": "System"
            }
            
            storage.save_conversation("test-session", messages, metadata)
            
            file_path = Path(tmpdir) / "test-session.json"
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert data["session_id"] == "test-session"
            assert data["messages"] == messages
            assert data["created_at"] == "2024-01-01T00:00:00"
            assert data["updated_at"] == "2024-01-01T00:00:00"
            assert data["system_prompt"] == "System"
    
    def test_save_conversation_atomic_write(self):
        """
        Test that save uses atomic writes (temp file then rename).
        
        Rationale: Ensures data integrity during writes.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages = create_message_list(user_messages=["Test"])
            metadata = {"created_at": "2024-01-01"}
            
            storage.save_conversation("atomic-test", messages, metadata)
            
            # Verify no temp files remain
            temp_files = list(Path(tmpdir).glob("*.tmp"))
            assert len(temp_files) == 0
            
            # Verify final file exists
            final_file = Path(tmpdir) / "atomic-test.json"
            assert final_file.exists()
    
    def test_save_conversation_overwrites_existing(self):
        """
        Test that saving to existing session_id overwrites the file.
        
        Rationale: Ensures updates work correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages1 = create_message_list(
                system="System",
                user_messages=["First"],
                assistant_messages=["Response 1"]
            )
            messages2 = create_message_list(
                system="System",
                user_messages=["First", "Second"],
                assistant_messages=["Response 1", "Response 2"]
            )
            metadata = {"created_at": "2024-01-01"}
            
            storage.save_conversation("overwrite-test", messages1, metadata)
            storage.save_conversation("overwrite-test", messages2, metadata)
            
            file_path = Path(tmpdir) / "overwrite-test.json"
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert len(data["messages"]) == 5  # system + 2 user + 2 assistant


class TestJSONFileStorageLoadConversation:
    """Test loading conversations from JSON files."""
    
    def test_load_conversation_success(self):
        """
        Test loading an existing conversation.
        
        Rationale: Ensures conversations can be retrieved from storage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages = create_message_list(
                system="System",
                user_messages=["Hello"],
                assistant_messages=["Hi"]
            )
            metadata = {
                "created_at": "2024-01-01T00:00:00",
                "system_prompt": "System"
            }
            
            storage.save_conversation("load-test", messages, metadata)
            result = storage.load_conversation("load-test")
            
            assert result is not None
            assert result["messages"] == messages
            assert result["metadata"]["created_at"] == "2024-01-01T00:00:00"
            assert result["metadata"]["system_prompt"] == "System"
    
    def test_load_conversation_not_found(self):
        """
        Test loading a non-existent conversation returns None.
        
        Rationale: Ensures graceful handling of missing conversations.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            result = storage.load_conversation("nonexistent")
            
            assert result is None
    
    def test_load_conversation_invalid_json(self):
        """
        Test that invalid JSON files are handled gracefully.
        
        Rationale: Ensures storage doesn't crash on corrupted files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            file_path = Path(tmpdir) / "invalid.json"
            
            # Write invalid JSON
            with open(file_path, 'w') as f:
                f.write("{ invalid json }")
            
            result = storage.load_conversation("invalid")
            
            assert result is None
    
    def test_load_conversation_missing_messages(self):
        """
        Test loading conversation with missing messages field.
        
        Rationale: Ensures graceful handling of malformed data.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            file_path = Path(tmpdir) / "no-messages.json"
            
            # Write JSON without messages
            with open(file_path, 'w') as f:
                json.dump({"session_id": "no-messages"}, f)
            
            result = storage.load_conversation("no-messages")
            
            # Should return empty messages list
            assert result is not None
            assert result["messages"] == []


class TestJSONFileStorageListConversations:
    """Test listing available conversations."""
    
    def test_list_conversations_empty(self):
        """
        Test listing when no conversations exist.
        
        Rationale: Ensures empty storage returns empty list.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            conversations = storage.list_conversations()
            
            assert conversations == []
    
    def test_list_conversations_multiple(self):
        """
        Test listing multiple conversations.
        
        Rationale: Ensures all conversations are listed correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages = create_message_list(user_messages=["Test"])
            metadata1 = {"created_at": "2024-01-01", "system_prompt": "System 1"}
            metadata2 = {"created_at": "2024-01-02", "system_prompt": "System 2"}
            
            storage.save_conversation("session-1", messages, metadata1)
            storage.save_conversation("session-2", messages, metadata2)
            
            conversations = storage.list_conversations()
            
            assert len(conversations) == 2
            session_ids = [c["session_id"] for c in conversations]
            assert "session-1" in session_ids
            assert "session-2" in session_ids
    
    def test_list_conversations_includes_metadata(self):
        """
        Test that listed conversations include metadata.
        
        Rationale: Ensures metadata is available without loading full conversation.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages = create_message_list(user_messages=["Test"])
            metadata = {
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T01:00:00",
                "system_prompt": "Test system"
            }
            
            storage.save_conversation("metadata-test", messages, metadata)
            
            conversations = storage.list_conversations()
            
            assert len(conversations) == 1
            conv = conversations[0]
            assert conv["session_id"] == "metadata-test"
            assert conv["created_at"] == "2024-01-01T00:00:00"
            assert conv["system_prompt"] == "Test system"
    
    def test_list_conversations_skips_invalid_files(self):
        """
        Test that invalid JSON files are skipped when listing.
        
        Rationale: Ensures listing doesn't fail due to corrupted files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages = create_message_list(user_messages=["Test"])
            metadata = {"created_at": "2024-01-01"}
            
            storage.save_conversation("valid", messages, metadata)
            
            # Create invalid JSON file
            invalid_file = Path(tmpdir) / "invalid.json"
            with open(invalid_file, 'w') as f:
                f.write("{ invalid }")
            
            conversations = storage.list_conversations()
            
            # Should only return the valid conversation
            assert len(conversations) == 1
            assert conversations[0]["session_id"] == "valid"


class TestJSONFileStorageDeleteConversation:
    """Test deleting conversations."""
    
    def test_delete_conversation_success(self):
        """
        Test deleting an existing conversation.
        
        Rationale: Ensures conversations can be removed from storage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            messages = create_message_list(user_messages=["Test"])
            metadata = {"created_at": "2024-01-01"}
            
            storage.save_conversation("delete-test", messages, metadata)
            assert (Path(tmpdir) / "delete-test.json").exists()
            
            storage.delete_conversation("delete-test")
            
            assert not (Path(tmpdir) / "delete-test.json").exists()
    
    def test_delete_conversation_not_found(self):
        """
        Test deleting a non-existent conversation doesn't raise error.
        
        Rationale: Ensures graceful handling of missing conversations.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONFileStorage(storage_path=tmpdir)
            
            # Should not raise
            storage.delete_conversation("nonexistent")


class TestConversationStorageProtocol:
    """Test that JSONFileStorage conforms to ConversationStorage protocol."""
    
    def test_json_storage_is_storage_protocol(self):
        """
        Test that JSONFileStorage implements ConversationStorage protocol.
        
        Rationale: Ensures type compatibility and interface compliance.
        """
        storage = JSONFileStorage()
        
        # Runtime check: has all required methods (Protocols can't be checked with isinstance at runtime)
        assert hasattr(storage, 'save_conversation')
        assert hasattr(storage, 'load_conversation')
        assert hasattr(storage, 'list_conversations')
        assert hasattr(storage, 'delete_conversation')
        
        # Verify methods are callable
        assert callable(storage.save_conversation)
        assert callable(storage.load_conversation)
        assert callable(storage.list_conversations)
        assert callable(storage.delete_conversation)

