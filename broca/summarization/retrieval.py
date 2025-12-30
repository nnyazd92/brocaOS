"""
Simple keyword-based retrieval index for memory cards.

Provides basic keyword search over summary notes. Can use LLM for semantic search.
"""

from __future__ import annotations

import logging
import json
import re
import time
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..llm import LLMClient

logger = logging.getLogger(__name__)

# Import logger utility
try:
    from ..reasoning.llm_pattern_logger import get_logger, initialize_logger
    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False


class RetrievalIndex:
    """
    Simple keyword-based retrieval index for memory cards.
    
    Stores and retrieves snippets based on keyword matching.
    Can be extended with embeddings later.
    """
    
    def __init__(self, llm_client: Optional["LLMClient"] = None) -> None:
        """
        Initialize retrieval index.
        
        Args:
            llm_client: Optional LLM client for semantic search
        """
        self._memory_cards: List[Dict[str, Any]] = []
        self.llm_client = llm_client
        self._llm_enabled = llm_client is not None
        logger.debug(f"Initialized RetrievalIndex (llm_semantic_search={self._llm_enabled})")
    
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
        Search memory cards using semantic search (LLM) or keyword matching.
        
        Args:
            query: Search query
            limit: Maximum number of results
            tags: Optional tags to filter by
            
        Returns:
            List of matching memory cards, sorted by relevance
        """
        # Filter by tags first
        candidate_cards = self._memory_cards
        if tags:
            candidate_cards = [
                card for card in candidate_cards
                if any(tag.lower() in [t.lower() for t in card.get("tags", [])] for tag in tags)
            ]
        
        if not candidate_cards:
            return []
        
        # Use LLM semantic search if available
        if self._llm_enabled and self.llm_client:
            try:
                return self._search_with_llm(query, candidate_cards, limit)
            except Exception as e:
                logger.warning(f"LLM semantic search failed, using keyword fallback: {e}")
                # Fall through to keyword matching
        
        # Fallback to keyword matching
        return self._search_with_keywords(query, candidate_cards, limit)
    
    def _search_with_llm(
        self,
        query: str,
        candidate_cards: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search using LLM semantic matching."""
        start_time = time.time()
        error_msg = None
        
        # Batch all cards into a single LLM call for efficiency
        cards_text = "\n\n".join([
            f"Card {i}: {card.get('text', '')}"
            for i, card in enumerate(candidate_cards)
        ])
        
        prompt = f"""Rank memory cards by semantic relevance to the query.

Query: {query}

Memory cards:
{cards_text}

For each card, determine:
- relevance_score: float 0.0-1.0 (how semantically relevant to the query)
- Consider semantic meaning, not just keyword matches

Return JSON array with one object per card:
[
  {{
    "card_index": 0,
    "relevance_score": 0.0-1.0
  }},
  ...
]

Sort by relevance_score descending. Return JSON only."""
        
        messages = [
            {
                "role": "system",
                "content": "You are a semantic search engine. Rank documents by relevance to queries. Return JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.llm_client.chat(messages, temperature=0.0)
            content = self.llm_client.extract_assistant_content(response)
            
            if not content:
                raise ValueError("Empty LLM response")
            
            # Extract JSON array
            content = content.strip()
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Find JSON array
            json_match = re.search(r'\[[^\]]*(?:\{[^{}]*\}[^\]]*)*\]', content, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
            else:
                results = json.loads(content)
            
            # Map results back to cards
            scored_cards = []
            relevance_scores = []
            for result in results:
                card_idx = result.get("card_index", -1)
                if 0 <= card_idx < len(candidate_cards):
                    score = float(result.get("relevance_score", 0.0))
                    scored_cards.append((score, candidate_cards[card_idx]))
                    relevance_scores.append(score)
            
            # Sort by score and return top N
            scored_cards.sort(key=lambda x: x[0], reverse=True)
            final_results = [card for score, card in scored_cards[:limit]]
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Log the search
            if HAS_LOGGER:
                logger_instance = get_logger()
                if logger_instance is None:
                    try:
                        from ..config import config
                        logger_instance = initialize_logger(
                            log_path=getattr(config.reasoning, 'llm_pattern_log_path', 'data/llm_pattern_matching_log.csv'),
                            enabled=getattr(config.reasoning, 'llm_pattern_logging_enabled', True)
                        )
                    except Exception:
                        logger_instance = None
                
                if logger_instance:
                    model = getattr(self.llm_client, 'model', 'unknown')
                    logger_instance.log(
                        component="RetrievalIndex",
                        operation="search_with_llm",
                        model=model,
                        input_text=query,
                        input_context={"card_count": len(candidate_cards), "limit": limit},
                        output_metrics={
                            "relevance_scores": relevance_scores[:limit],
                            "results_count": len(final_results)
                        },
                        latency_ms=latency_ms,
                        error=error_msg
                    )
            
            return final_results
            
        except Exception as e:
            error_msg = str(e)
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Error in LLM semantic search: {e}", exc_info=True)
            
            # Log error
            if HAS_LOGGER:
                logger_instance = get_logger()
                if logger_instance:
                    model = getattr(self.llm_client, 'model', 'unknown')
                    logger_instance.log(
                        component="RetrievalIndex",
                        operation="search_with_llm",
                        model=model,
                        input_text=query,
                        input_context={"card_count": len(candidate_cards), "limit": limit},
                        latency_ms=latency_ms,
                        error=error_msg
                    )
            
            raise
    
    def _search_with_keywords(
        self,
        query: str,
        candidate_cards: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback keyword-based search."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_cards = []
        
        for card in candidate_cards:
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

