"""
Tests for MemoryRecord schema.

Tests schema validation, field constraints, and data integrity.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from broca.memory import MemoryRecord, SourceType, SourceMetadata


class TestMemoryRecordCreation:
    """Test MemoryRecord creation and validation."""
    
    def test_create_minimal_record(self):
        """
        Test creating a memory record with minimal required fields.
        
        Rationale: Ensures basic record creation works with required fields only.
        """
        record = MemoryRecord(
            namespace="test.namespace",
            text="Test memory text",
            importance=0.5
        )
        
        assert record.namespace == "test.namespace"
        assert record.text == "Test memory text"
        assert record.importance == 0.5
        assert record.tags == []
        assert record.id is None
        assert isinstance(record.created_at, datetime)
        assert isinstance(record.last_used_at, datetime)
    
    def test_create_full_record(self):
        """
        Test creating a memory record with all fields.
        
        Rationale: Ensures all fields can be set correctly.
        """
        tags = ["tag1", "tag2", "tag3"]
        record = MemoryRecord(
            id=1,
            namespace="math.sage.api",
            tags=tags,
            text="SageMath API change",
            importance=0.8,
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc)
        )
        
        assert record.id == 1
        assert record.namespace == "math.sage.api"
        assert record.tags == tags
        assert record.text == "SageMath API change"
        assert record.importance == 0.8
    
    def test_namespace_validation_empty(self):
        """
        Test that empty namespace raises validation error.
        
        Rationale: Ensures namespace is always provided and non-empty.
        """
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(namespace="", text="Test", importance=0.5)
        
        # Pydantic validates min_length before custom validators
        assert "namespace" in str(exc_info.value).lower() or "string_too_short" in str(exc_info.value)
    
    def test_namespace_validation_whitespace(self):
        """
        Test that whitespace-only namespace is stripped and validated.
        
        Rationale: Ensures namespace validation handles whitespace correctly.
        """
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(namespace="   ", text="Test", importance=0.5)
        
        assert "Namespace cannot be empty" in str(exc_info.value)
    
    def test_namespace_stripping(self):
        """
        Test that namespace whitespace is stripped.
        
        Rationale: Ensures namespace is cleaned of leading/trailing whitespace.
        """
        record = MemoryRecord(namespace="  test.namespace  ", text="Test", importance=0.5)
        assert record.namespace == "test.namespace"
    
    def test_text_validation_empty(self):
        """
        Test that empty text raises validation error.
        
        Rationale: Ensures text content is always provided.
        """
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(namespace="test", text="", importance=0.5)
        
        # Pydantic validates min_length before custom validators
        assert "text" in str(exc_info.value).lower() or "string_too_short" in str(exc_info.value)
    
    def test_text_validation_whitespace(self):
        """
        Test that whitespace-only text raises validation error.
        
        Rationale: Ensures text validation handles whitespace correctly.
        """
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(namespace="test", text="   ", importance=0.5)
        
        assert "Text cannot be empty" in str(exc_info.value)
    
    def test_text_stripping(self):
        """
        Test that text whitespace is stripped.
        
        Rationale: Ensures text is cleaned of leading/trailing whitespace.
        """
        record = MemoryRecord(namespace="test", text="  Test memory  ", importance=0.5)
        assert record.text == "Test memory"
    
    def test_importance_validation_min(self):
        """
        Test that importance below 0.0 raises validation error.
        
        Rationale: Ensures importance is within valid range [0.0, 1.0].
        """
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(namespace="test", text="Test", importance=-0.1)
        
        assert "importance" in str(exc_info.value).lower()
    
    def test_importance_validation_max(self):
        """
        Test that importance above 1.0 raises validation error.
        
        Rationale: Ensures importance is within valid range [0.0, 1.0].
        """
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(namespace="test", text="Test", importance=1.1)
        
        assert "importance" in str(exc_info.value).lower()
    
    def test_importance_boundary_values(self):
        """
        Test that importance boundary values (0.0 and 1.0) are valid.
        
        Rationale: Ensures boundary values are accepted.
        """
        record_min = MemoryRecord(namespace="test", text="Test", importance=0.0)
        record_max = MemoryRecord(namespace="test", text="Test", importance=1.0)
        
        assert record_min.importance == 0.0
        assert record_max.importance == 1.0
    
    def test_tags_validation_empty_list(self):
        """
        Test that empty tags list is valid.
        
        Rationale: Ensures tags are optional.
        """
        record = MemoryRecord(namespace="test", text="Test", importance=0.5, tags=[])
        assert record.tags == []
    
    def test_tags_cleaning(self):
        """
        Test that tags are cleaned (empty tags removed, whitespace stripped).
        
        Rationale: Ensures tag list is normalized.
        """
        record = MemoryRecord(
            namespace="test",
            text="Test",
            importance=0.5,
            tags=["  tag1  ", "", "tag2", "   ", "tag3"]
        )
        
        assert record.tags == ["tag1", "tag2", "tag3"]
    
    def test_tags_default_empty(self):
        """
        Test that tags default to empty list.
        
        Rationale: Ensures tags have sensible default.
        """
        record = MemoryRecord(namespace="test", text="Test", importance=0.5)
        assert record.tags == []


class TestMemoryRecordTimestamps:
    """Test timestamp handling in MemoryRecord."""
    
    def test_created_at_default(self):
        """
        Test that created_at is set to current time by default.
        
        Rationale: Ensures timestamps are automatically set.
        """
        record = MemoryRecord(namespace="test", text="Test", importance=0.5)
        
        assert isinstance(record.created_at, datetime)
        assert record.created_at.tzinfo is not None  # Should be timezone-aware
    
    def test_last_used_at_default(self):
        """
        Test that last_used_at is set to current time by default.
        
        Rationale: Ensures timestamps are automatically set.
        """
        record = MemoryRecord(namespace="test", text="Test", importance=0.5)
        
        assert isinstance(record.last_used_at, datetime)
        assert record.last_used_at.tzinfo is not None
    
    def test_update_last_used(self):
        """
        Test that update_last_used updates the timestamp.
        
        Rationale: Ensures last_used_at can be updated.
        """
        record = MemoryRecord(namespace="test", text="Test", importance=0.5)
        original_time = record.last_used_at
        
        # Wait a tiny bit to ensure time difference
        import time
        time.sleep(0.01)
        
        record.update_last_used()
        
        assert record.last_used_at > original_time
        assert isinstance(record.last_used_at, datetime)


class TestMemoryRecordEmbedding:
    """Test embedding field handling."""
    
    def test_embedding_optional(self):
        """
        Test that embedding is optional.
        
        Rationale: Ensures embedding can be None (stored separately in FAISS).
        """
        record = MemoryRecord(namespace="test", text="Test", importance=0.5)
        assert record.embedding is None
    
    def test_embedding_can_be_set(self):
        """
        Test that embedding can be set.
        
        Rationale: Ensures embedding field works when provided.
        """
        embedding = [0.1, 0.2, 0.3] * 512  # Mock 1536-dim embedding
        record = MemoryRecord(
            namespace="test",
            text="Test",
            importance=0.5,
            embedding=embedding
        )
        
        assert record.embedding == embedding
        assert len(record.embedding) == 1536


class TestMemoryRecordSource:
    """Test source tracking in MemoryRecord."""
    
    def test_memory_record_without_source(self):
        """
        Test that MemoryRecord can be created without source (backward compatibility).
        
        Rationale: Ensures backward compatibility for existing code.
        """
        record = MemoryRecord(
            namespace="test",
            text="Test memory",
            importance=0.5
        )
        
        assert record.source is None
    
    def test_memory_record_with_source(self):
        """
        Test that MemoryRecord can be created with source.
        
        Rationale: Ensures source tracking works correctly.
        """
        source = SourceMetadata(source_type=SourceType.USER)
        record = MemoryRecord(
            namespace="test",
            text="Test memory",
            importance=0.5,
            source=source
        )
        
        assert record.source is not None
        assert record.source.source_type == SourceType.USER
        assert record.source.metadata is None
    
    def test_memory_record_with_source_metadata(self):
        """
        Test that MemoryRecord can be created with source and metadata.
        
        Rationale: Ensures source metadata is preserved.
        """
        source = SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            metadata={"query": "test", "urls": ["http://example.com"]}
        )
        record = MemoryRecord(
            namespace="test",
            text="Test memory",
            importance=0.5,
            source=source
        )
        
        assert record.source.source_type == SourceType.WEB_SEARCH
        assert record.source.metadata is not None
        assert record.source.metadata["query"] == "test"
        assert len(record.source.metadata["urls"]) == 1
    
    def test_memory_record_all_source_types(self):
        """
        Test that MemoryRecord works with all source types.
        
        Rationale: Ensures all source types are supported.
        """
        for source_type in SourceType:
            source = SourceMetadata(source_type=source_type)
            record = MemoryRecord(
                namespace="test",
                text="Test memory",
                importance=0.5,
                source=source
            )
            
            assert record.source.source_type == source_type
    
    def test_memory_record_source_system_file(self):
        """
        Test MemoryRecord with system file source.
        
        Rationale: Ensures system file source tracking works.
        """
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_FILE,
            metadata={"file_path": "/etc/config.json"}
        )
        record = MemoryRecord(
            namespace="test",
            text="Config file content",
            importance=0.5,
            source=source
        )
        
        assert record.source.source_type == SourceType.SYSTEM_FILE
        assert record.source.metadata["file_path"] == "/etc/config.json"
    
    def test_memory_record_source_web_search(self):
        """
        Test MemoryRecord with web search source.
        
        Rationale: Ensures web search source tracking works.
        """
        source = SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            metadata={
                "query": "Python memory",
                "urls": ["https://example.com"],
                "result_count": 5
            }
        )
        record = MemoryRecord(
            namespace="test",
            text="Web search result",
            importance=0.5,
            source=source
        )
        
        assert record.source.source_type == SourceType.WEB_SEARCH
        assert record.source.metadata["query"] == "Python memory"
        assert len(record.source.metadata["urls"]) == 1

