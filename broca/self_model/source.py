"""
Source tracking for self-model items.

Tracks where items in the self-model came from (memory, system_default, user_input, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timezone


@dataclass
class Source:
    """
    Source information for self-model items.
    
    Tracks where an item in the self-model originated from, allowing
    linking back to memories or other sources.
    """
    type: str  # "memory", "system_default", "user_input", "llm_inference", etc.
    memory_id: Optional[int] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Source to dictionary representation.
        
        Returns:
            Dictionary containing source data
        """
        result = {
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
        if self.memory_id is not None:
            result["memory_id"] = self.memory_id
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Source:
        """
        Create Source from dictionary representation.
        
        Args:
            data: Dictionary containing source data
            
        Returns:
            Source instance
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        return cls(
            type=data.get("type", "unknown"),
            memory_id=data.get("memory_id"),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def system_default(cls, metadata: Optional[Dict[str, Any]] = None) -> Source:
        """Create a system_default source."""
        return cls(
            type="system_default",
            metadata=metadata or {},
        )
    
    @classmethod
    def from_memory(cls, memory_id: int, metadata: Optional[Dict[str, Any]] = None) -> Source:
        """Create a source from memory."""
        return cls(
            type="memory",
            memory_id=memory_id,
            metadata=metadata or {},
        )
    
    @classmethod
    def user_input(cls, metadata: Optional[Dict[str, Any]] = None) -> Source:
        """Create a user_input source."""
        return cls(
            type="user_input",
            metadata=metadata or {},
        )
    
    @classmethod
    def llm_inference(cls, metadata: Optional[Dict[str, Any]] = None) -> Source:
        """Create an llm_inference source."""
        return cls(
            type="llm_inference",
            metadata=metadata or {},
        )

