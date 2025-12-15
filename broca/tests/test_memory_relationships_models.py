"""
Tests for memory relationship models.

Tests RelationshipRecord and RelationType data models.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from broca.memory import RelationshipRecord, RelationType, MemoryRecord


class TestRelationType:
    """Test RelationType enum."""
    
    def test_relation_type_values(self):
        """
        Test that all expected relation types exist.
        
        Rationale: Ensures all relationship types from spec are available.
        """
        # Logical relationships
        assert RelationType.SUPPORTS == "supports"
        assert RelationType.CONTRADICTS == "contradicts"
        assert RelationType.SUPERSEDES == "supersedes"
        
        # Structural relationships
        assert RelationType.ELABORATES == "elaborates"
        assert RelationType.SUMMARIZES == "summarizes"
        assert RelationType.REFERENCES == "references"
        
        # Causal relationships
        assert RelationType.CAUSES == "causes"
        assert RelationType.CAUSED_BY == "caused_by"
        
        # Temporal relationships
        assert RelationType.PRECEDES == "precedes"
        assert RelationType.FOLLOWS == "follows"
        
        # Semantic relationships
        assert RelationType.SIMILAR_TO == "similar_to"
        assert RelationType.RELATED_TO == "related_to"
    
    def test_relation_type_enum_membership(self):
        """
        Test that RelationType values are proper enum members.
        
        Rationale: Ensures enum works correctly.
        """
        assert isinstance(RelationType.SUPPORTS, RelationType)
        assert isinstance(RelationType.CONTRADICTS, RelationType)
        assert RelationType.SUPPORTS.value == "supports"


class TestRelationshipRecord:
    """Test RelationshipRecord model."""
    
    def test_create_relationship_record_minimal(self):
        """
        Test creating RelationshipRecord with minimal required fields.
        
        Rationale: Ensures basic relationship creation works.
        """
        record = RelationshipRecord(
            source_id=1,
            target_id=2,
            relation_type=RelationType.SUPPORTS
        )
        
        assert record.source_id == 1
        assert record.target_id == 2
        assert record.relation_type == RelationType.SUPPORTS
        assert record.strength == 1.0  # Default
        assert record.bidirectional is False  # Default
        assert record.metadata is None  # Default
        assert record.id is None  # Default
        assert record.created_at is None  # Default
    
    def test_create_relationship_record_full(self):
        """
        Test creating RelationshipRecord with all fields.
        
        Rationale: Ensures all fields can be set.
        """
        metadata = {"reason": "Auto-detected", "confidence": 0.95}
        created_at = datetime.now(timezone.utc)
        
        record = RelationshipRecord(
            source_id=1,
            target_id=2,
            relation_type=RelationType.CONTRADICTS,
            strength=0.9,
            bidirectional=True,
            metadata=metadata,
            id=10,
            created_at=created_at
        )
        
        assert record.source_id == 1
        assert record.target_id == 2
        assert record.relation_type == RelationType.CONTRADICTS
        assert record.strength == 0.9
        assert record.bidirectional is True
        assert record.metadata == metadata
        assert record.id == 10
        assert record.created_at == created_at
    
    def test_relationship_record_strength_validation(self):
        """
        Test that strength is validated to be in range [0.0, 1.0].
        
        Rationale: Ensures strength values are valid.
        """
        # Valid values
        record1 = RelationshipRecord(
            source_id=1,
            target_id=2,
            relation_type=RelationType.SUPPORTS,
            strength=0.0
        )
        assert record1.strength == 0.0
        
        record2 = RelationshipRecord(
            source_id=1,
            target_id=2,
            relation_type=RelationType.SUPPORTS,
            strength=1.0
        )
        assert record2.strength == 1.0
        
        record3 = RelationshipRecord(
            source_id=1,
            target_id=2,
            relation_type=RelationType.SUPPORTS,
            strength=0.5
        )
        assert record3.strength == 0.5
        
        # Invalid values should raise validation error
        with pytest.raises(ValueError, match="strength"):
            RelationshipRecord(
                source_id=1,
                target_id=2,
                relation_type=RelationType.SUPPORTS,
                strength=-0.1
            )
        
        with pytest.raises(ValueError, match="strength"):
            RelationshipRecord(
                source_id=1,
                target_id=2,
                relation_type=RelationType.SUPPORTS,
                strength=1.1
            )
    
    def test_relationship_record_bidirectional(self):
        """
        Test bidirectional flag.
        
        Rationale: Ensures bidirectional relationships work correctly.
        """
        record = RelationshipRecord(
            source_id=1,
            target_id=2,
            relation_type=RelationType.SIMILAR_TO,
            bidirectional=True
        )
        
        assert record.bidirectional is True
    
    def test_relationship_record_metadata(self):
        """
        Test metadata field accepts dict.
        
        Rationale: Ensures metadata can store additional context.
        """
        metadata = {
            "detection_method": "embedding_similarity",
            "similarity_score": 0.87,
            "auto_detected": True
        }
        
        record = RelationshipRecord(
            source_id=1,
            target_id=2,
            relation_type=RelationType.SIMILAR_TO,
            metadata=metadata
        )
        
        assert record.metadata == metadata
        assert record.metadata["detection_method"] == "embedding_similarity"
    
    def test_relationship_record_all_relation_types(self):
        """
        Test that all relation types can be used.
        
        Rationale: Ensures all relation types work with RelationshipRecord.
        """
        for rel_type in RelationType:
            record = RelationshipRecord(
                source_id=1,
                target_id=2,
                relation_type=rel_type
            )
            assert record.relation_type == rel_type
    
    def test_relationship_record_serialization(self):
        """
        Test that RelationshipRecord can be serialized to dict.
        
        Rationale: Ensures relationship records can be converted for JSON/API.
        """
        record = RelationshipRecord(
            source_id=1,
            target_id=2,
            relation_type=RelationType.ELABORATES,
            strength=0.8,
            bidirectional=False,
            metadata={"key": "value"},
            id=5,
            created_at=datetime.now(timezone.utc)
        )
        
        # Pydantic models can be converted to dict
        record_dict = record.model_dump()
        
        assert record_dict["source_id"] == 1
        assert record_dict["target_id"] == 2
        assert record_dict["relation_type"] == "elaborates"
        assert record_dict["strength"] == 0.8
        assert record_dict["bidirectional"] is False
        assert record_dict["metadata"] == {"key": "value"}
        assert record_dict["id"] == 5

