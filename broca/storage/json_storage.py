"""
JSON file-based storage implementation for conversations.

Stores each conversation as a separate JSON file in a configurable directory.
Uses atomic writes for safety.
"""

from __future__ import annotations

import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from . import ConversationStorage

logger = logging.getLogger(__name__)


class JSONFileStorage:
    """
    JSON file-based storage implementation for conversations.
    
    Each conversation is stored as a separate JSON file named {session_id}.json
    in the configured storage directory.
    """
    
    def __init__(self, storage_path: str = "conversations") -> None:
        """
        Initialize JSON file storage.
        
        Args:
            storage_path: Directory path where conversation files will be stored
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized JSONFileStorage at {self.storage_path.absolute()}")
    
    def save_conversation(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Save a conversation to a JSON file.
        
        Uses atomic writes (write to temp file, then rename) for safety.
        
        Args:
            session_id: Unique identifier for the conversation session
            messages: List of message dictionaries
            metadata: Additional metadata to store
        """
        file_path = self.storage_path / f"{session_id}.json"
        
        data = {
            "session_id": session_id,
            "messages": messages,
            **metadata
        }
        
        tmp_path = None
        try:
            # Use a deterministic temp file path in the same directory as the target file.
            storage_dir = self.storage_path.resolve()
            storage_dir.mkdir(parents=True, exist_ok=True)
            import time, secrets
            tmp_path = storage_dir / f'.{session_id}.{secrets.token_hex(8)}.{time.monotonic_ns()}.tmp'
            
            # Write JSON to temporary file
            with open(tmp_path, 'w', encoding='utf-8') as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            
            # Ensure temp file exists
            if not tmp_path.exists():
                raise OSError(f"Temporary file {tmp_path} was not created or does not exist")
            
            # Atomic replace
            os.replace(str(tmp_path), str(file_path))
            logger.debug(f"Saved conversation {session_id} to {file_path}")
        except (OSError, IOError, TypeError, ValueError) as e:
            logger.error(f"Failed to save conversation {session_id}: {e}")
            # Clean up temp file if present
            try:
                if tmp_path and Path(tmp_path).exists():
                    Path(tmp_path).unlink()
            except Exception:
                pass
            raise

    def load_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a conversation from a JSON file.
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            Dictionary with 'messages' and metadata, or None if not found
        """
        file_path = self.storage_path / f"{session_id}.json"
        
        if not file_path.exists():
            logger.debug(f"Conversation {session_id} not found at {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract messages and metadata
            messages = data.pop("messages", [])
            metadata = data
            
            logger.debug(f"Loaded conversation {session_id} from {file_path}")
            return {
                "messages": messages,
                "metadata": metadata
            }
            
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load conversation {session_id}: {e}")
            return None
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all available conversations.
        
        Returns:
            List of dictionaries containing session_id and metadata for each conversation
        """
        conversations = []
        
        if not self.storage_path.exists():
            return conversations
        
        try:
            for file_path in self.storage_path.glob("*.json"):
                session_id = file_path.stem  # filename without extension
                
                # Try to load metadata without full messages for efficiency
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract metadata (everything except messages)
                    metadata = {k: v for k, v in data.items() if k != "messages"}
                    conversations.append({
                        "session_id": session_id,
                        **metadata
                    })
                except (OSError, IOError, json.JSONDecodeError) as e:
                    logger.warning(f"Failed to read conversation file {file_path}: {e}")
                    continue
            
            logger.debug(f"Listed {len(conversations)} conversations")
            return conversations
            
        except OSError as e:
            logger.error(f"Failed to list conversations: {e}")
            return []
    
    def delete_conversation(self, session_id: str) -> None:
        """
        Delete a conversation file.
        
        Args:
            session_id: Unique identifier for the conversation session
        """
        file_path = self.storage_path / f"{session_id}.json"
        
        if not file_path.exists():
            logger.debug(f"Conversation {session_id} not found, nothing to delete")
            return
        
        try:
            file_path.unlink()
            logger.debug(f"Deleted conversation {session_id}")
        except OSError as e:
            logger.error(f"Failed to delete conversation {session_id}: {e}")
            raise

