"""
Validation utilities for summarization.

Provides drift detection, compression ratio validation, and evidence verification.
"""

from __future__ import annotations

import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from .event_logger import EventLogger
from .models import SessionSummary
from .token_estimator import estimate_tokens

logger = logging.getLogger(__name__)


class SummarizationValidator:
    """
    Validates summarization results for drift and quality.
    
    Provides methods to verify evidence pointers, check compression ratios,
    and detect inconsistencies.
    
    Includes caching for event ID sets to improve performance on large sessions.
    """
    
    # Maximum number of sessions to cache
    MAX_CACHE_SIZE = 100
    
    def __init__(self, event_logger: EventLogger) -> None:
        """
        Initialize validator.
        
        Args:
            event_logger: EventLogger instance for accessing raw events
        """
        self.event_logger = event_logger
        # Cache: session_id -> (event_ids_set, file_mtime)
        self._event_ids_cache: Dict[str, Tuple[set[str], float]] = {}
    
    def _get_log_file_mtime(self, session_id: str) -> Optional[float]:
        """Get modification time of event log file."""
        log_file = self.event_logger._get_log_file(session_id)
        if log_file.exists():
            return os.path.getmtime(log_file)
        return None
    
    def _get_cached_event_ids_set(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if not use_cache:
            return None
        
        if session_id not in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = self._event_ids_cache[session_id]
        current_mtime = self._get_log_file_mtime(session_id)
        
        # Cache is valid if file mtime matches
        if current_mtime == cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    def _set_cached_event_ids_set(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._event_ids_cache))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def _get_event_ids_set(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def verify_evidence_event_ids(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def check_compression_ratio(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def detect_drift(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }

