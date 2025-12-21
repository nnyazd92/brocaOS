"""
Simple keyword-based retrieval index for memory cards.

Provides basic keyword search over summary notes. Embeddings can be added later.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RetrievalIndex:
    """
    Simple keyword-based retrieval index for memory cards.
    
    Stores and retrieves snippets based on keyword matching.
    Can be extended with embeddings later.
    """
    
    def __init__(self) -> None:
        """Initialize retrieval index."""
        self._memory_cards: List[Dict[str, Any]] = []
        logger.debug("Initialized RetrievalIndex")
    
    def add_memory_card(
        self,
        text: str,
        tags: List[str] = None,
        event_ids: List[str] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Add a memory card to the index.
        
        Args:
            text: Memory card text content
            tags: Optional list of tags
            event_ids: Optional list of associated event IDs
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Memory card ID
        """
        import uuid
        
        card_id = f"card_{uuid.uuid4().hex[:8]}"
        
        card = {
            "id": card_id,
            "text": text,
            "tags": tags or [],
            "event_ids": event_ids or [],
            "timestamp": timestamp or datetime.utcnow().isoformat()
        }
        
        self._memory_cards.append(card)
        logger.debug(f"Added memory card {card_id}")
        return card_id
    
    def search(
        self,
        query: str,
        limit: int = 5,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memory cards by keyword.
        
        Args:
            query: Search query (keywords)
            limit: Maximum number of results
            tags: Optional tags to filter by
            
        Returns:
            List of matching memory cards, sorted by relevance
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_cards = []
        
        for card in self._memory_cards:
            # Filter by tags if specified
            if tags:
                card_tags = [t.lower() for t in card.get("tags", [])]
                if not any(tag.lower() in card_tags for tag in tags):
                    continue
            
            # Score by keyword matches
            text_lower = card.get("text", "").lower()
            text_words = set(text_lower.split())
            
            # Count matching words
            matches = len(query_words & text_words)
            if matches == 0:
                continue
            
            # Score: number of matches / total query words
            score = matches / len(query_words) if query_words else 0
            
            # Boost score if query is a substring of text
            if query_lower in text_lower:
                score += 0.5
            
            scored_cards.append((score, card))
        
        # Sort by score (descending) and return top N
        scored_cards.sort(key=lambda x: x[0], reverse=True)
        results = [card for score, card in scored_cards[:limit]]
        
        logger.debug(f"Retrieved {len(results)} memory cards for query: {query[:50]}")
        return results
    
    def get_by_event_ids(self, event_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get memory cards associated with specific event IDs.
        
        Args:
            event_ids: List of event IDs
            
        Returns:
            List of matching memory cards
        """
        event_id_set = set(event_ids)
        results = [
            card for card in self._memory_cards
            if any(eid in event_id_set for eid in card.get("event_ids", []))
        ]
        return results
    
    def clear(self) -> None:
        """Clear all memory cards."""
        self._memory_cards.clear()
        logger.debug("Cleared retrieval index")

