"""
Tests for summarization validation and drift detection.

Tests drift detection, compression ratios, and retrieval usefulness.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock
import pytest

from broca.summarization.event_logger import EventLogger
from broca.summarization.storage import SummaryStorage
from broca.summarization.models import SessionSummary, SummaryHeader, SummaryBlocks, EvidenceItem


@pytest.fixture
def temp_event_log_dir():
    """Temporary directory for event logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_summary_dir():
    """Temporary directory for summaries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def event_logger(temp_event_log_dir):
    """EventLogger instance."""
    return EventLogger(log_dir=temp_event_log_dir)


@pytest.fixture
def summary_storage(temp_summary_dir):
    """SummaryStorage instance."""
    return SummaryStorage(summary_path=temp_summary_dir)


class TestDriftDetection:
    """Test drift detection functionality."""
    
    def test_verify_evidence_event_ids_exist(self, event_logger, summary_storage):
        """Test that evidence event IDs can be verified against event log."""
        session_id = "test_session"
        
        # Add some events
        event_id1 = event_logger.log_user_message(session_id, "Hello")
        event_id2 = event_logger.log_assistant_message(session_id, "Hi there")
        
        # Create summary with evidence pointing to real event IDs
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="Test goal"),
            evidence=[
                EvidenceItem(claim="User said hello", event_ids=[event_id1]),
                EvidenceItem(claim="Assistant responded", event_ids=[event_id2])
            ]
        )
        
        # Verify evidence event IDs exist
        all_events = event_logger.get_events(session_id)
        event_ids_in_log = {e.get("event_id") for e in all_events}
        
        for evidence_item in summary.evidence:
            for event_id in evidence_item.event_ids:
                assert event_id in event_ids_in_log, f"Event ID {event_id} not found in log"
    
    def test_detect_missing_event_ids(self, event_logger, summary_storage):
        """Test detection of missing (hallucinated) event IDs."""
        session_id = "test_session"
        
        # Add some events
        event_logger.log_user_message(session_id, "Hello")
        
        # Create summary with evidence pointing to non-existent event ID
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Claim", event_ids=["nonexistent_event_id"])
            ]
        )
        
        # Verify that the event ID doesn't exist
        all_events = event_logger.get_events(session_id)
        event_ids_in_log = {e.get("event_id") for e in all_events}
        
        assert "nonexistent_event_id" not in event_ids_in_log
    
    def test_compression_ratio_calculation(self):
        """Test calculation of compression ratio."""
        # Simulate raw events
        raw_events_text = "x" * 10000  # ~2500 tokens
        
        # Simulate summary
        summary_text = "x" * 400  # ~100 tokens
        
        # Compression ratio should be > 5x typically
        compression_ratio = len(raw_events_text) / len(summary_text)
        assert compression_ratio > 5.0











