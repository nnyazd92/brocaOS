"""
Tests for temporal metadata in MemoryRecord.

Tests valid_from, valid_until, and temporal_scope fields.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from broca.memory import MemoryRecord


class TestTemporalMetadataFields:
    """Test temporal metadata fields in MemoryRecord."""
    
    def test_temporal_fields_optional(self):
        """
        Test that temporal metadata fields are optional.
        
        Rationale: Ensures backward compatibility with existing records.
        """
        record = MemoryRecord(
            namespace="test",
            text="Test memory",
            importance=0.5
        )
        
        assert record.valid_from is None
        assert record.valid_until is None
        assert record.temporal_scope is None
    
    def test_valid_from_can_be_set(self):
        """
        Test that valid_from can be set.
        
        Rationale: Ensures temporal validity tracking works.
        """
        valid_from = datetime.now(timezone.utc) - timedelta(days=30)
        record = MemoryRecord(
            namespace="test",
            text="Test memory",
            importance=0.5,
            valid_from=valid_from
        )
        
        assert record.valid_from == valid_from
        assert record.valid_from.tzinfo is not None
    
    def test_valid_until_can_be_set(self):
        """
        Test that valid_until can be set.
        
        Rationale: Ensures temporal validity expiration tracking works.
        """
        valid_until = datetime.now(timezone.utc) + timedelta(days=30)
        record = MemoryRecord(
            namespace="test",
            text="Test memory",
            importance=0.5,
            valid_until=valid_until
        )
        
        assert record.valid_until == valid_until
        assert record.valid_until.tzinfo is not None
    
    def test_temporal_scope_can_be_set(self):
        """
        Test that temporal_scope can be set.
        
        Rationale: Ensures temporal scope classification works.
        """
        for scope in ["past", "present", "future", "timeless"]:
            record = MemoryRecord(
                namespace="test",
                text="Test memory",
                importance=0.5,
                temporal_scope=scope
            )
            assert record.temporal_scope == scope
    
    def test_temporal_scope_validation(self):
        """
        Test that temporal_scope only accepts valid values.
        
        Rationale: Ensures temporal scope is constrained to valid options.
        """
        # This will depend on implementation - if using Literal, Pydantic will validate
        # For now, we'll test that invalid values raise errors
        with pytest.raises(ValidationError):
            MemoryRecord(
                namespace="test",
                text="Test memory",
                importance=0.5,
                temporal_scope="invalid_scope"
            )
    
    def test_valid_from_before_valid_until(self):
        """
        Test that valid_from can be before valid_until.
        
        Rationale: Ensures temporal validity range is logical.
        """
        valid_from = datetime.now(timezone.utc) - timedelta(days=10)
        valid_until = datetime.now(timezone.utc) + timedelta(days=10)
        
        record = MemoryRecord(
            namespace="test",
            text="Test memory",
            importance=0.5,
            valid_from=valid_from,
            valid_until=valid_until
        )
        
        assert record.valid_from < record.valid_until
    
    def test_temporal_metadata_with_full_record(self):
        """
        Test temporal metadata with all other fields.
        
        Rationale: Ensures temporal fields work with complete records.
        """
        valid_from = datetime.now(timezone.utc) - timedelta(days=5)
        valid_until = datetime.now(timezone.utc) + timedelta(days=5)
        
        record = MemoryRecord(
            id=1,
            namespace="test.namespace",
            tags=["tag1", "tag2"],
            text="Test memory with temporal metadata",
            importance=0.8,
            valid_from=valid_from,
            valid_until=valid_until,
            temporal_scope="present"
        )
        
        assert record.id == 1
        assert record.valid_from == valid_from
        assert record.valid_until == valid_until
        assert record.temporal_scope == "present"

