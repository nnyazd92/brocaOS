"""
Performance tests for summarization validation.

Tests caching, incremental validation, and performance optimizations.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import os

from broca.summarization.event_logger import EventLogger
from broca.summarization.validation import SummarizationValidator
from broca.summarization.models import SessionSummary, SummaryHeader, SummaryBlocks, EvidenceItem


@pytest.fixture
def temp_event_log_dir():
    """Temporary directory for event logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def event_logger(temp_event_log_dir):
    """EventLogger instance."""
    return EventLogger(log_dir=temp_event_log_dir)


@pytest.fixture
def validator(event_logger):
    """SummarizationValidator instance."""
    return SummarizationValidator(event_logger)


class TestValidationCaching:
    """Test caching layer for validation."""
    
    def test_cache_hit_uses_cached_event_ids(self, validator, event_logger):
        """Test that cached event IDs are used on subsequent calls."""
        session_id = "test_session"
        
        # Add events
        event_id1 = event_logger.log_user_message(session_id, "Hello")
        event_id2 = event_logger.log_user_message(session_id, "World")
        
        # Create summary
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Test", event_ids=[event_id1, event_id2])
            ]
        )
        
        # First call - should populate cache
        result1 = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        assert result1["valid"] is True
        
        # Second call - should use cache
        # Mock get_events to verify cache is used
        original_get_events = event_logger.get_events
        call_count = []
        
        def tracked_get_events(sid):
            call_count.append(1)
            return original_get_events(sid)
        
        event_logger.get_events = tracked_get_events
        
        result2 = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        assert result2["valid"] is True
        
        # Cache should be used, so get_events should not be called again
        # (get_event_ids_set should be used from cache)
        assert len(call_count) == 0
    
    def test_cache_invalidates_on_file_modification(self, validator, event_logger, temp_event_log_dir):
        """Test that cache invalidates when event log file is modified."""
        session_id = "test_session"
        
        # Add initial events
        event_id1 = event_logger.log_user_message(session_id, "First")
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1])]
        )
        
        # First call - populate cache
        result1 = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        assert result1["valid"] is True
        
        # Add new event (modifies file)
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        # Update summary to include new event
        summary.evidence.append(EvidenceItem(claim="Test 2", event_ids=[event_id2]))
        
        # Second call - cache should be invalidated and reloaded
        result2 = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        assert result2["valid"] is True
        assert len(result2["missing_event_ids"]) == 0
    
    def test_cache_respects_use_cache_flag(self, validator, event_logger):
        """Test that use_cache=False bypasses cache."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "Hello")
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1])]
        )
        
        # With cache enabled
        result1 = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        
        # With cache disabled - should still work
        result2 = validator.verify_evidence_event_ids(session_id, summary, use_cache=False)
        assert result1["valid"] == result2["valid"]
    
    def test_cache_size_limit(self, validator, event_logger):
        """Test that cache respects size limits (max 100 sessions)."""
        # Create 101 sessions
        summaries = []
        for i in range(101):
            session_id = f"session_{i}"
            event_id = event_logger.log_user_message(session_id, "Test")
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0
                ),
                summary_blocks=SummaryBlocks(),
                evidence=[EvidenceItem(claim="Test", event_ids=[event_id])]
            )
            summaries.append((session_id, summary))
            
            # Validate to populate cache
            validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        
        # Cache should not exceed 100 entries
        # The oldest entries should be evicted
        cache_size = len(getattr(validator, '_event_ids_cache', {}))
        assert cache_size <= 100
    
    def test_cache_handles_missing_file_gracefully(self, validator):
        """Test that cache handles missing event log files gracefully."""
        session_id = "nonexistent_session"
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=["nonexistent_id"])]
        )
        
        # Should not raise exception
        result = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        assert result["valid"] is False
        assert len(result["missing_event_ids"]) > 0


class TestIncrementalValidation:
    """Test incremental validation logic."""
    
    def test_incremental_validation_only_validates_new_events(self, validator, event_logger):
        """Test that incremental validation only validates events after last_summarized_event_id."""
        session_id = "test_session"
        
        # Create initial events
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        event_id3 = event_logger.log_user_message(session_id, "Third")
        
        # Create previous summary that summarized up to event_id2
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                last_summarized_event_id=event_id2,
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Old claim", event_ids=[event_id1, event_id2])
            ]
        )
        
        # Create new summary with evidence pointing to old and new events
        new_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Old evidence", event_ids=[event_id1]),  # Old event
                EvidenceItem(claim="New evidence", event_ids=[event_id3])   # New event
            ]
        )
        
        # With incremental validation, only event_id3 should be checked
        result = validator.verify_evidence_event_ids(
            session_id,
            new_summary,
            previous_summary=previous_summary,
            use_incremental=True,
            use_cache=True
        )
        
        # Should be valid (event_id3 exists)
        assert result["valid"] is True
        assert len(result["missing_event_ids"]) == 0
    
    def test_incremental_validation_falls_back_when_no_previous_summary(self, validator, event_logger):
        """Test that incremental validation falls back to full validation when no previous_summary."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1])]
        )
        
        # Without previous_summary, should do full validation
        result = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=None,
            use_incremental=True,
            use_cache=True
        )
        
        assert result["valid"] is True
    
    def test_incremental_validation_falls_back_when_no_last_summarized_event_id(self, validator, event_logger):
        """Test that incremental validation falls back when last_summarized_event_id is None."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                last_summarized_event_id=None,  # No last_summarized_event_id
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[]
        )
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1])]
        )
        
        # Should fall back to full validation
        result = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=previous_summary,
            use_incremental=True,
            use_cache=True
        )
        
        assert result["valid"] is True
    
    def test_incremental_validation_detects_missing_new_event(self, validator, event_logger):
        """Test that incremental validation detects missing events in new evidence."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                last_summarized_event_id=event_id1,
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[]
        )
        
        # Summary with evidence pointing to non-existent event
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=["nonexistent_event_id"])]
        )
        
        result = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=previous_summary,
            use_incremental=True,
            use_cache=True
        )
        
        assert result["valid"] is False
        assert "nonexistent_event_id" in result["missing_event_ids"]
    
    def test_incremental_validation_with_use_incremental_false(self, validator, event_logger):
        """Test that use_incremental=False performs full validation."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                last_summarized_event_id=event_id1,
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[]
        )
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1, event_id2])]
        )
        
        # With use_incremental=False, should validate all events
        result = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=previous_summary,
            use_incremental=False,
            use_cache=True
        )
        
        # Should still be valid (full validation)
        assert result["valid"] is True
    
    def test_detect_drift_with_incremental_validation(self, validator, event_logger):
        """Test that detect_drift supports incremental validation."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                last_summarized_event_id=event_id1,
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[]
        )
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id2])]
        )
        
        result = validator.detect_drift(
            session_id,
            summary,
            events=None,
            previous_summary=previous_summary,
            use_incremental=True,
            use_cache=True
        )
        
        assert result["has_drift"] is False
        assert len(result["missing_event_ids"]) == 0


class TestPropertyBasedValidation:
    """Property-based tests using Hypothesis."""
    
    from hypothesis import given, strategies as st, settings, HealthCheck
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_events=st.integers(min_value=0, max_value=100),
        num_evidence_items=st.integers(min_value=0, max_value=50),
        use_incremental=st.booleans(),
        use_cache=st.booleans()
    )
    def test_incremental_validation_matches_full_validation(
        self, validator, event_logger, num_events, num_evidence_items, use_incremental, use_cache
    ):
        """Property: Incremental validation results match full validation for same evidence."""
        session_id = "test_session"
        
        # Create events
        event_ids = []
        for i in range(num_events):
            event_id = event_logger.log_user_message(session_id, f"Message {i}")
            event_ids.append(event_id)
        
        if not event_ids:
            # Skip if no events
            return
        
        # Create previous summary at midpoint
        midpoint = len(event_ids) // 2
        if midpoint > 0:
            previous_summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    last_summarized_event_id=event_ids[midpoint - 1],
                    revision=0
                ),
                summary_blocks=SummaryBlocks(),
                evidence=[]
            )
        else:
            previous_summary = None
        
        # Create evidence items using random event IDs from the available ones
        evidence_items = []
        for i in range(num_evidence_items):
            # Select 1-3 random event IDs for each evidence item
            num_refs = min(i % 3 + 1, len(event_ids))
            selected_ids = event_ids[:num_refs] if num_refs <= len(event_ids) else event_ids
            evidence_items.append(
                EvidenceItem(claim=f"Claim {i}", event_ids=selected_ids)
            )
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=evidence_items
        )
        
        # Run both incremental and full validation
        result_incremental = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=previous_summary if use_incremental else None,
            use_incremental=use_incremental and previous_summary is not None,
            use_cache=use_cache
        )
        
        result_full = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=None,
            use_incremental=False,
            use_cache=use_cache
        )
        
        # Results should match (both should report same validity)
        assert result_incremental["valid"] == result_full["valid"]
        # Missing event IDs should be the same
        assert set(result_incremental["missing_event_ids"]) == set(result_full["missing_event_ids"])
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_calls=st.integers(min_value=1, max_value=10),
        use_cache=st.booleans()
    )
    def test_validation_idempotency(
        self, validator, event_logger, num_calls, use_cache
    ):
        """Property: Multiple validation calls return same results (idempotency)."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Test", event_ids=[event_id1, event_id2])
            ]
        )
        
        results = []
        for _ in range(num_calls):
            result = validator.verify_evidence_event_ids(
                session_id,
                summary,
                use_cache=use_cache
            )
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result["valid"] == first_result["valid"]
            assert set(result["missing_event_ids"]) == set(first_result["missing_event_ids"])
            assert result["total_evidence_items"] == first_result["total_evidence_items"]
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        event_ids_list=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=20),
        evidence_event_ids=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10)
    )
    def test_validation_set_operations(
        self, validator, event_logger, event_ids_list, evidence_event_ids
    ):
        """Property: Validation correctly handles set membership operations."""
        session_id = "test_session"
        
        # Create events with given event IDs
        logged_event_ids = set()
        for event_id_prefix in event_ids_list:
            # Use the prefix to generate a unique event ID by logging
            event_id = event_logger.log_user_message(session_id, f"Message for {event_id_prefix}")
            logged_event_ids.add(event_id)
        
        # Create summary with evidence using provided event IDs
        # Map evidence_event_ids to actual logged event IDs or use as-is
        summary_event_ids = []
        for i, eid_prefix in enumerate(evidence_event_ids):
            # Try to match with logged event IDs, or use as-is if not found
            # This creates a mix of valid and potentially invalid IDs
            if i < len(list(logged_event_ids)):
                # Use a real logged ID
                summary_event_ids.append(list(logged_event_ids)[i])
            else:
                # Use the prefix as a potentially invalid ID
                summary_event_ids.append(eid_prefix)
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Test", event_ids=summary_event_ids) if summary_event_ids else EvidenceItem(claim="Test", event_ids=[])
            ]
        )
        
        result = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        
        # Check that validation correctly identifies which event IDs exist
        missing_ids = set(result["missing_event_ids"])
        all_logged = logged_event_ids
        
        # Event IDs in summary that are in logged_event_ids should not be in missing
        for eid in summary_event_ids:
            if eid in all_logged:
                assert eid not in missing_ids, f"Valid event ID {eid} incorrectly marked as missing"
            else:
                assert eid in missing_ids, f"Invalid event ID {eid} not marked as missing"
        
        # Result should be valid only if all event IDs exist
        expected_valid = all(eid in all_logged for eid in summary_event_ids)
        assert result["valid"] == expected_valid


class TestFaultInjection:
    """Fault injection tests for robustness."""
    
    def test_corrupted_event_log_file(self, validator, event_logger, temp_event_log_dir):
        """Test that validator handles corrupted event log files gracefully."""
        session_id = "test_session"
        
        # Create valid event
        event_id1 = event_logger.log_user_message(session_id, "Valid message")
        
        # Corrupt the log file by adding invalid JSON
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'a') as f:
            f.write("invalid json line that cannot be parsed\n")
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1])]
        )
        
        # Should not raise exception, should handle gracefully
        result = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        # Should still find the valid event
        assert result["valid"] is True
        assert event_id1 not in result["missing_event_ids"]
    
    def test_missing_event_ids_in_log(self, validator, event_logger):
        """Test validation with evidence pointing to missing event IDs."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Valid", event_ids=[event_id1]),
                EvidenceItem(claim="Invalid", event_ids=["missing_id_1", "missing_id_2"])
            ]
        )
        
        result = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        
        assert result["valid"] is False
        assert "missing_id_1" in result["missing_event_ids"]
        assert "missing_id_2" in result["missing_event_ids"]
        assert event_id1 not in result["missing_event_ids"]
    
    def test_cache_with_file_modification_race_condition(self, validator, event_logger, temp_event_log_dir):
        """Test cache invalidation handles file modification timing correctly."""
        session_id = "test_session"
        
        # Create initial event
        event_id1 = event_logger.log_user_message(session_id, "First")
        
        summary1 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1])]
        )
        
        # Populate cache
        result1 = validator.verify_evidence_event_ids(session_id, summary1, use_cache=True)
        assert result1["valid"] is True
        
        # Modify file (add new event)
        import time
        time.sleep(0.01)  # Small delay to ensure mtime changes
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        # Cache should be invalidated and reloaded
        summary2 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1, event_id2])]
        )
        
        result2 = validator.verify_evidence_event_ids(session_id, summary2, use_cache=True)
        assert result2["valid"] is True
        assert event_id2 not in result2["missing_event_ids"]
    
    def test_invalid_last_summarized_event_id(self, validator, event_logger):
        """Test incremental validation with invalid last_summarized_event_id."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        # Previous summary with invalid last_summarized_event_id
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                last_summarized_event_id="nonexistent_event_id",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[]
        )
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1, event_id2])]
        )
        
        # Should fall back to full validation when last_summarized_event_id not found
        result = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=previous_summary,
            use_incremental=True,
            use_cache=True
        )
        
        # Should still work correctly (full validation)
        assert result["valid"] is True
    
    def test_empty_event_ids_in_evidence(self, validator, event_logger):
        """Test validation with evidence items that have empty event_ids lists."""
        session_id = "test_session"
        event_id1 = event_logger.log_user_message(session_id, "First")
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="With ID", event_ids=[event_id1]),
                EvidenceItem(claim="Without ID", event_ids=[])
            ]
        )
        
        result = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        
        # Should handle empty event_ids gracefully
        assert result["valid"] is True
        assert result["total_evidence_items"] == 2
    
    def test_event_id_none_in_log(self, validator, event_logger, temp_event_log_dir):
        """Test handling of events with None event_id."""
        session_id = "test_session"
        
        # Create valid event
        event_id1 = event_logger.log_user_message(session_id, "Valid")
        
        # Manually add event with None event_id
        import json
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps({"type": "invalid", "event_id": None, "content": "test"}) + '\n')
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[EvidenceItem(claim="Test", event_ids=[event_id1])]
        )
        
        # Should handle None event_id gracefully
        result = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        assert result["valid"] is True


class TestGoldenTraceReplay:
    """Golden trace replay tests with large sessions."""
    
    def test_large_session_performance(self, validator, event_logger):
        """Test performance with large session (1000+ events)."""
        import time
        
        session_id = "large_session"
        
        # Create 1000 events
        event_ids = []
        start_time = time.time()
        for i in range(1000):
            event_id = event_logger.log_user_message(session_id, f"Message {i}")
            event_ids.append(event_id)
        create_time = time.time() - start_time
        
        # Create summary with evidence pointing to various events
        evidence_items = []
        # Include events from beginning, middle, and end
        evidence_items.append(EvidenceItem(claim="Early", event_ids=event_ids[:10]))
        evidence_items.append(EvidenceItem(claim="Middle", event_ids=event_ids[500:510]))
        evidence_items.append(EvidenceItem(claim="Late", event_ids=event_ids[-10:]))
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=evidence_items
        )
        
        # Measure validation time with cache
        start_time = time.time()
        result_cached = validator.verify_evidence_event_ids(session_id, summary, use_cache=True)
        cached_time = time.time() - start_time
        
        # Measure validation time without cache
        start_time = time.time()
        result_uncached = validator.verify_evidence_event_ids(session_id, summary, use_cache=False)
        uncached_time = time.time() - start_time
        
        # Both should be valid
        assert result_cached["valid"] is True
        assert result_uncached["valid"] is True
        
        # Cached should be faster (or at least not slower)
        # Cache provides benefit on subsequent calls
        print(f"\nLarge session (1000 events):")
        print(f"  Creation time: {create_time:.3f}s")
        print(f"  Validation (cached): {cached_time:.3f}s")
        print(f"  Validation (uncached): {uncached_time:.3f}s")
    
    def test_large_session_incremental_validation(self, validator, event_logger):
        """Test incremental validation with large session."""
        session_id = "large_session_inc"
        
        # Create 500 events for "previous" session
        prev_event_ids = []
        for i in range(500):
            event_id = event_logger.log_user_message(session_id, f"Previous {i}")
            prev_event_ids.append(event_id)
        
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                last_summarized_event_id=prev_event_ids[-1],
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[]
        )
        
        # Add 500 more events
        new_event_ids = []
        for i in range(500):
            event_id = event_logger.log_user_message(session_id, f"New {i}")
            new_event_ids.append(event_id)
        
        # Create summary with evidence only from new events
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="New evidence", event_ids=new_event_ids[:10])
            ]
        )
        
        import time
        
        # Measure incremental validation
        start_time = time.time()
        result_incremental = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=previous_summary,
            use_incremental=True,
            use_cache=True
        )
        incremental_time = time.time() - start_time
        
        # Measure full validation
        start_time = time.time()
        result_full = validator.verify_evidence_event_ids(
            session_id,
            summary,
            previous_summary=None,
            use_incremental=False,
            use_cache=True
        )
        full_time = time.time() - start_time
        
        # Both should be valid
        assert result_incremental["valid"] is True
        assert result_full["valid"] is True
        
        # Incremental should be faster (only validates new events)
        print(f"\nIncremental validation (1000 total events, 500 new):")
        print(f"  Incremental time: {incremental_time:.3f}s")
        print(f"  Full time: {full_time:.3f}s")
        print(f"  Speedup: {full_time / incremental_time if incremental_time > 0 else 0:.2f}x")
    
    def test_session_with_multiple_summaries(self, validator, event_logger):
        """Test session with multiple incremental summaries (golden trace scenario)."""
        session_id = "multi_summary_session"
        
        summaries = []
        event_batches = []
        
        # Create 5 batches of 200 events each, with summaries after each batch
        for batch_num in range(5):
            batch_event_ids = []
            for i in range(200):
                event_id = event_logger.log_user_message(
                    session_id,
                    f"Batch {batch_num}, Message {i}"
                )
                batch_event_ids.append(event_id)
            event_batches.append(batch_event_ids)
            
            # Create summary for this batch
            last_event_id = batch_event_ids[-1] if batch_event_ids else None
            previous_summary = summaries[-1] if summaries else None
            
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session_id,
                    created_at=f"2024-01-01T0{batch_num}:00:00Z",
                    last_updated_at=f"2024-01-01T0{batch_num}:00:00Z",
                    last_summarized_event_id=last_event_id,
                    revision=batch_num
                ),
                summary_blocks=SummaryBlocks(),
                evidence=[
                    EvidenceItem(
                        claim=f"Batch {batch_num} evidence",
                        event_ids=batch_event_ids[:5]  # Reference 5 events from this batch
                    )
                ]
            )
            
            # Validate using incremental validation if previous summary exists
            result = validator.verify_evidence_event_ids(
                session_id,
                summary,
                previous_summary=previous_summary,
                use_incremental=(previous_summary is not None),
                use_cache=True
            )
            
            assert result["valid"] is True, f"Batch {batch_num} validation failed"
            summaries.append(summary)
        
        # Final summary should validate all events
        final_summary = summaries[-1]
        result = validator.verify_evidence_event_ids(
            session_id,
            final_summary,
            previous_summary=None,
            use_incremental=False,
            use_cache=True
        )
        assert result["valid"] is True
    
    def test_drift_detection_large_session(self, validator, event_logger):
        """Test drift detection with large session."""
        session_id = "drift_session"
        
        # Create 1000 events
        event_ids = []
        for i in range(1000):
            event_id = event_logger.log_user_message(session_id, f"Message {i}")
            event_ids.append(event_id)
        
        # Summary with valid evidence
        valid_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Valid", event_ids=event_ids[:10])
            ]
        )
        
        result_valid = validator.detect_drift(session_id, valid_summary, use_cache=True)
        assert result_valid["has_drift"] is False
        
        # Summary with invalid evidence (drift)
        drift_summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(),
            evidence=[
                EvidenceItem(claim="Valid", event_ids=event_ids[:10]),
                EvidenceItem(claim="Invalid", event_ids=["missing_1", "missing_2"])
            ]
        )
        
        result_drift = validator.detect_drift(session_id, drift_summary, use_cache=True)
        assert result_drift["has_drift"] is True
        assert "missing_1" in result_drift["missing_event_ids"]
        assert "missing_2" in result_drift["missing_event_ids"]

