"""
Tests for Summarizer.

Tests JSON schema validation, conflict detection, evidence pointers, and size limits.
"""

from __future__ import annotations

from unittest.mock import Mock, MagicMock
import pytest
import json

from broca.summarization.summarizer import Summarizer
from broca.summarization.models import SessionSummary, SummaryHeader, SummaryBlocks


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = Mock()
    client.extract_assistant_content = Mock(return_value="")
    return client


@pytest.fixture
def summarizer(mock_llm_client):
    """Summarizer instance with mocked LLM."""
    return Summarizer(llm=mock_llm_client, max_summary_tokens=1200, max_block_tokens=200)


class TestSummarizer:
    """Test Summarizer functionality."""
    
    def test_parse_json_response_simple(self, summarizer, mock_llm_client):
        """Test parsing simple JSON response."""
        json_response = '{"summary_patch": {}, "extracted": {}, "bookkeeping": {}}'
        mock_llm_client.extract_assistant_content.return_value = json_response
        
        result = summarizer._parse_json_response(json_response)
        assert result is not None
        assert "summary_patch" in result
        assert "extracted" in result
        assert "bookkeeping" in result
    
    def test_parse_json_response_markdown(self, summarizer):
        """Test parsing JSON wrapped in markdown code blocks."""
        markdown_response = """```json
{"summary_patch": {}, "extracted": {}, "bookkeeping": {}}
```"""
        
        result = summarizer._parse_json_response(markdown_response)
        assert result is not None
        assert "summary_patch" in result
    
    def test_validate_summarization_result_valid(self, summarizer):
        """Test validation of valid summarization result."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"},
            {"event_id": "evt_2", "type": "assistant_message", "content": "Hi"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test goal"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["evt_1"]}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_2"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is True
        assert len(validation.get("errors", [])) == 0
    
    def test_validate_summarization_result_invalid_event_ids(self, summarizer):
        """Test validation fails for invalid event IDs."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test goal"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["nonexistent"]}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_2"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
        assert len(validation.get("errors", [])) > 0
    
    def test_enforce_size_limits(self, summarizer):
        """Test that size limits are enforced."""
        # Create a result with very long current_goal
        long_goal = "x" * 1000  # Much longer than max_block_tokens (200 tokens = ~800 chars)
        
        result = {
            "summary_patch": {
                "current_goal": long_goal,
                "what_we_built": ["Item 1", "Item 2"] * 20  # Many items
            },
            "extracted": {},
            "bookkeeping": {}
        }
        
        result = summarizer._enforce_size_limits(result)
        
        # Goal should be truncated
        assert len(result["summary_patch"]["current_goal"]) < len(long_goal)
        assert result["summary_patch"]["current_goal"].endswith("...")
        
        # Items should be limited
        assert len(result["summary_patch"]["what_we_built"]) <= 10

