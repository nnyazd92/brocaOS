"""
Validation utilities for summarization.

Provides drift detection, compression ratio validation, and evidence verification.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from .event_logger import EventLogger
from .models import SessionSummary
from .token_estimator import estimate_tokens

logger = logging.getLogger(__name__)


class SummarizationValidator:
    """
    Validates summarization results for drift and quality.
    
    Provides methods to verify evidence pointers, check compression ratios,
    and detect inconsistencies.
    """
    
    def __init__(self, event_logger: EventLogger) -> None:
        """
        Initialize validator.
        
        Args:
            event_logger: EventLogger instance for accessing raw events
        """
        self.event_logger = event_logger
    
    def verify_evidence_event_ids(
        self,
        session_id: str,
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        all_events = self.event_logger.get_events(session_id)
        event_ids_in_log = {e.get("event_id") for e in all_events if e.get("event_id")}
        
        missing_event_ids = []
        total_items = len(summary.evidence)
        verified_items = 0
        
        for evidence_item in summary.evidence:
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
        events: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            events = self.event_logger.get_events(session_id)
        
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

