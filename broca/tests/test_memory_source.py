"""
Tests for memory source tracking models.

Tests SourceType enum and SourceMetadata model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from broca.memory import SourceType, SourceMetadata


class TestSourceType:
    """Test SourceType enum."""
    
    def test_source_type_values(self):
        """Test that all expected source types exist."""
        assert SourceType.WEB_SEARCH == "web_search"
        assert SourceType.USER == "user"
        assert SourceType.SYSTEM_FILE == "system_file"
        assert SourceType.TERMINAL_OUTPUT == "terminal_output"
        assert SourceType.MEMORY_RETRIEVAL == "memory_retrieval"
        assert SourceType.UNKNOWN == "unknown"
    
    def test_source_type_enum_membership(self):
        """Test that SourceType values are enum members."""
        assert isinstance(SourceType.WEB_SEARCH, SourceType)
        assert isinstance(SourceType.USER, SourceType)
        assert isinstance(SourceType.UNKNOWN, SourceType)
    
    def test_source_type_string_value(self):
        """Test that SourceType can be used as string."""
        assert SourceType.WEB_SEARCH.value == "web_search"
        assert SourceType.USER.value == "user"
        # Test that enum members can be compared to strings
        assert SourceType.USER == "user"


class TestSourceMetadata:
    """Test SourceMetadata model."""
    
    def test_create_minimal_source_metadata(self):
        """Test creating SourceMetadata with only source_type."""
        metadata = SourceMetadata(source_type=SourceType.USER)
        
        assert metadata.source_type == SourceType.USER
        assert metadata.metadata is None
    
    def test_create_source_metadata_with_metadata(self):
        """Test creating SourceMetadata with additional metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            metadata={"query": "test query", "urls": ["http://example.com"]}
        )
        
        assert metadata.source_type == SourceType.WEB_SEARCH
        assert metadata.metadata == {"query": "test query", "urls": ["http://example.com"]}
    
    def test_source_metadata_all_source_types(self):
        """Test creating SourceMetadata with all source types."""
        for source_type in SourceType:
            metadata = SourceMetadata(source_type=source_type)
            assert metadata.source_type == source_type
    
    def test_source_metadata_web_search_example(self):
        """Test SourceMetadata for web search with typical metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            metadata={
                "query": "Python memory management",
                "urls": ["https://example.com/1", "https://example.com/2"],
                "result_count": 5
            }
        )
        
        assert metadata.source_type == SourceType.WEB_SEARCH
        assert metadata.metadata["query"] == "Python memory management"
        assert len(metadata.metadata["urls"]) == 2
        assert metadata.metadata["result_count"] == 5
    
    def test_source_metadata_system_file_example(self):
        """Test SourceMetadata for system file with typical metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.SYSTEM_FILE,
            metadata={"file_path": "/etc/config.json", "file_size": 1024}
        )
        
        assert metadata.source_type == SourceType.SYSTEM_FILE
        assert metadata.metadata["file_path"] == "/etc/config.json"
        assert metadata.metadata["file_size"] == 1024
    
    def test_source_metadata_user_example(self):
        """Test SourceMetadata for user input."""
        metadata = SourceMetadata(source_type=SourceType.USER)
        
        assert metadata.source_type == SourceType.USER
        assert metadata.metadata is None
    
    def test_source_metadata_unknown_example(self):
        """Test SourceMetadata for unknown source."""
        metadata = SourceMetadata(source_type=SourceType.UNKNOWN)
        
        assert metadata.source_type == SourceType.UNKNOWN
        assert metadata.metadata is None
    
    def test_source_metadata_optional_metadata(self):
        """Test that metadata field is optional."""
        metadata1 = SourceMetadata(source_type=SourceType.USER, metadata=None)
        metadata2 = SourceMetadata(source_type=SourceType.USER)
        
        assert metadata1.metadata is None
        assert metadata2.metadata is None
    
    def test_source_metadata_complex_metadata(self):
        """Test SourceMetadata with complex nested metadata."""
        metadata = SourceMetadata(
            source_type=SourceType.TERMINAL_OUTPUT,
            metadata={
                "command": "ls -la",
                "exit_code": 0,
                "output_lines": ["file1.txt", "file2.txt"],
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
        
        assert metadata.source_type == SourceType.TERMINAL_OUTPUT
        assert metadata.metadata["command"] == "ls -la"
        assert metadata.metadata["exit_code"] == 0
        assert len(metadata.metadata["output_lines"]) == 2

