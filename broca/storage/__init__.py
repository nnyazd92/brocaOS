"""
Storage abstraction for conversation persistence.

This module defines the ConversationStorage protocol that all storage backends
must implement. This allows easy extension to SQLite, Postgres, or other storage systems.
"""

from __future__ import annotations

from typing import Protocol, List, Dict, Any, Optional


class ConversationStorage(Protocol):
    """
    Protocol defining the interface for conversation storage backends.
    
    All storage implementations must conform to this interface to ensure
    compatibility and easy swapping between storage backends.
    """
    
    def save_conversation(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Save a conversation to storage.
        
        Args:
            session_id: Unique identifier for the conversation session
            messages: List of message dictionaries with 'role' and 'content' keys
            metadata: Additional metadata (e.g., created_at, updated_at, system_prompt)
        """
        ...
    
    def load_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a conversation from storage.
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            Dictionary containing 'messages' and 'metadata' keys, or None if not found
        """
        ...
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all available conversations.
        
        Returns:
            List of dictionaries containing session_id and metadata for each conversation
        """
        ...
    
    def delete_conversation(self, session_id: str) -> None:
        """
        Delete a conversation from storage.
        
        Args:
            session_id: Unique identifier for the conversation session
        """
        ...

