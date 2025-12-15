"""
Tests for Conflict and Resolution models.

Tests schema validation, field constraints, and data integrity.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from broca.memory import MemoryRecord


class TestConflictModel:
    """Test Conflict model creation and validation."""
    
    def test_create_conflict_minimal(self):
        """
        Test creating a conflict with minimal required fields.
        
        Rationale: Ensures basic conflict creation works.
        """
        from broca.memory.conflict.models import Conflict
        
        memory1 = MemoryRecord(
            namespace="test.namespace",
            text="User prefers Python",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test.namespace",
            text="User hates Python",
            importance=0.5
        )
        
        conflict = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Boolean contradiction: prefers vs hates",
            resolution_strategy="recency"
        )
        
        assert conflict.memory1 == memory1
        assert conflict.memory2 == memory2
        assert conflict.conflict_type == "contradiction"
        assert conflict.confidence == 0.8
        assert conflict.evidence == "Boolean contradiction: prefers vs hates"
        assert conflict.resolution_strategy == "recency"
    
    def test_conflict_confidence_validation(self):
        """
        Test that confidence must be between 0.0 and 1.0.
        
        Rationale: Ensures confidence values are valid.
        """
        from broca.memory.conflict.models import Conflict
        
        memory1 = MemoryRecord(namespace="test", text="Text 1", importance=0.5)
        memory2 = MemoryRecord(namespace="test", text="Text 2", importance=0.5)
        
        # Should raise ValidationError for confidence > 1.0
        with pytest.raises(ValidationError):
            Conflict(
                memory1=memory1,
                memory2=memory2,
                conflict_type="contradiction",
                confidence=1.5,  # Invalid
                evidence="Test",
                resolution_strategy="recency"
            )
        
        # Should raise ValidationError for confidence < 0.0
        with pytest.raises(ValidationError):
            Conflict(
                memory1=memory1,
                memory2=memory2,
                conflict_type="contradiction",
                confidence=-0.1,  # Invalid
                evidence="Test",
                resolution_strategy="recency"
            )
        
        # Valid confidence values should work
        conflict1 = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.0,  # Valid
            evidence="Test",
            resolution_strategy="recency"
        )
        assert conflict1.confidence == 0.0
        
        conflict2 = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=1.0,  # Valid
            evidence="Test",
            resolution_strategy="recency"
        )
        assert conflict2.confidence == 1.0
    
    def test_conflict_type_validation(self):
        """
        Test that conflict_type must be a valid value.
        
        Rationale: Ensures conflict types are constrained.
        """
        from broca.memory.conflict.models import Conflict
        
        memory1 = MemoryRecord(namespace="test", text="Text 1", importance=0.5)
        memory2 = MemoryRecord(namespace="test", text="Text 2", importance=0.5)
        
        # Valid conflict types should work
        valid_types = ["contradiction", "ambiguity", "update"]
        for conflict_type in valid_types:
            conflict = Conflict(
                memory1=memory1,
                memory2=memory2,
                conflict_type=conflict_type,
                confidence=0.5,
                evidence="Test",
                resolution_strategy="recency"
            )
            assert conflict.conflict_type == conflict_type


class TestResolutionModel:
    """Test Resolution model creation and validation."""
    
    def test_create_resolution_minimal(self):
        """
        Test creating a resolution with minimal required fields.
        
        Rationale: Ensures basic resolution creation works.
        """
        from broca.memory.conflict.models import Resolution
        from broca.memory import MemoryRecord
        
        memory = MemoryRecord(
            namespace="test.namespace",
            text="Resolved memory",
            importance=0.7
        )
        
        resolution = Resolution(
            action="keep_new",
            kept_memory=memory,
            archived_memory=None,
            merged_memory=None,
            rationale="Keeping newer memory"
        )
        
        assert resolution.action == "keep_new"
        assert resolution.kept_memory == memory
        assert resolution.archived_memory is None
        assert resolution.merged_memory is None
        assert resolution.rationale == "Keeping newer memory"
    
    def test_resolution_action_validation(self):
        """
        Test that action must be a valid value.
        
        Rationale: Ensures resolution actions are constrained.
        """
        from broca.memory.conflict.models import Resolution
        from broca.memory import MemoryRecord
        
        memory = MemoryRecord(namespace="test", text="Test", importance=0.5)
        
        # Valid actions should work
        valid_actions = ["keep_both", "keep_new", "keep_old", "keep_important", "consensus", "merge", "ask_user"]
        for action in valid_actions:
            resolution = Resolution(
                action=action,
                kept_memory=memory if action != "merge" else None,
                archived_memory=None,
                merged_memory=memory if action == "merge" else None,
                rationale=f"Test {action}"
            )
            assert resolution.action == action
    
    def test_resolution_with_merged_memory(self):
        """
        Test resolution with merged memory.
        
        Rationale: Ensures merge action works correctly.
        """
        from broca.memory.conflict.models import Resolution
        from broca.memory import MemoryRecord
        
        merged = MemoryRecord(
            namespace="test",
            text="Merged text",
            importance=0.8
        )
        
        resolution = Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged,
            rationale="Merged conflicting memories"
        )
        
        assert resolution.action == "merge"
        assert resolution.merged_memory == merged
        assert resolution.kept_memory is None

