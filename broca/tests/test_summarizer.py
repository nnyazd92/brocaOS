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
    
    # Issue 1: Retry Validation Bug Tests
    def test_retry_with_feedback_validates_with_original_events(self, summarizer, mock_llm_client):
        """Test that retry validation uses original events list, not empty list."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"},
            {"event_id": "evt_2", "type": "assistant_message", "content": "Hi"}
        ]
        
        # First response with invalid event_id
        first_result = {
            "summary_patch": {"current_goal": "Test goal"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["nonexistent"]}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_2"}
        }
        
        # Retry response with valid event_id
        retry_response = '{"summary_patch": {"current_goal": "Test goal"}, "extracted": {"facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["evt_1"]}]}, "bookkeeping": {"new_last_summarized_event_id": "evt_2"}}'
        
        validation_result = {"valid": False, "errors": ["facts_added item has invalid event_ids: ['nonexistent']"]}
        original_prompt = "Test prompt"
        messages = [{"role": "system", "content": "test"}, {"role": "user", "content": original_prompt}]
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": retry_response}}]}
        mock_llm_client.extract_assistant_content.return_value = retry_response
        
        # This should validate with events, not empty list
        result = summarizer._retry_with_feedback(first_result, validation_result, original_prompt, messages, events)
        
        # Should succeed because retry has valid event_id
        assert result is not None
        assert result["extracted"]["facts_added"][0]["event_ids"] == ["evt_1"]
    
    def test_retry_with_feedback_rejects_invalid_event_ids(self, summarizer, mock_llm_client):
        """Test that retry correctly rejects invalid event_ids when using original events."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        first_result = {
            "summary_patch": {"current_goal": "Test goal"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": []}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        # Retry still has invalid event_id
        retry_response = '{"summary_patch": {"current_goal": "Test goal"}, "extracted": {"facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["still_invalid"]}]}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}'
        
        validation_result = {"valid": False, "errors": ["facts_added item missing event_ids"]}
        original_prompt = "Test prompt"
        messages = [{"role": "system", "content": "test"}, {"role": "user", "content": original_prompt}]
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": retry_response}}]}
        mock_llm_client.extract_assistant_content.return_value = retry_response
        
        result = summarizer._retry_with_feedback(first_result, validation_result, original_prompt, messages, events)
        
        # Should fail because retry still has invalid event_id
        assert result is None
    
    # Issue 2: Fragile JSON Parsing Tests
    def test_parse_json_response_with_trailing_text(self, summarizer):
        """Test parsing JSON with trailing text after closing brace."""
        json_with_trailing = '{"summary_patch": {}, "extracted": {}, "bookkeeping": {}} This is trailing text that should be ignored'
        
        result = summarizer._parse_json_response(json_with_trailing)
        assert result is not None
        assert "summary_patch" in result
        assert "extracted" in result
        assert "bookkeeping" in result
    
    def test_parse_json_response_with_leading_text(self, summarizer):
        """Test parsing JSON with leading text before opening brace."""
        json_with_leading = 'Here is some leading text {"summary_patch": {}, "extracted": {}, "bookkeeping": {}}'
        
        result = summarizer._parse_json_response(json_with_leading)
        assert result is not None
        assert "summary_patch" in result
    
    def test_parse_json_response_with_imbalanced_braces_in_strings(self, summarizer):
        """Test parsing JSON with braces inside string values."""
        json_with_braces_in_string = '{"summary_patch": {"current_goal": "This has {braces} in it"}, "extracted": {}, "bookkeeping": {}}'
        
        result = summarizer._parse_json_response(json_with_braces_in_string)
        assert result is not None
        assert result["summary_patch"]["current_goal"] == "This has {braces} in it"
    
    def test_parse_json_response_multiple_objects_extracts_largest(self, summarizer):
        """Test parsing when multiple JSON objects exist, extracts largest balanced."""
        # Two JSON objects, second is larger
        multiple_json = '{"small": "object"} {"summary_patch": {"current_goal": "test"}, "extracted": {"facts_added": []}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}'
        
        result = summarizer._parse_json_response(multiple_json)
        assert result is not None
        # Should extract the larger object
        assert "summary_patch" in result
        assert "extracted" in result
        assert "bookkeeping" in result
    
    def test_parse_json_response_code_fence_with_trailing_text(self, summarizer):
        """Test parsing JSON in code fences with trailing text."""
        markdown_with_trailing = """```json
{"summary_patch": {}, "extracted": {}, "bookkeeping": {}}
```
This is trailing text after the code fence"""
        
        result = summarizer._parse_json_response(markdown_with_trailing)
        assert result is not None
        assert "summary_patch" in result
    
    def test_parse_json_response_malformed_returns_none(self, summarizer):
        """Test that malformed JSON returns None gracefully."""
        malformed = '{"summary_patch": {, "extracted": {}, "bookkeeping": {}}'  # Missing key after {
        
        result = summarizer._parse_json_response(malformed)
        assert result is None
    
    def test_parse_json_response_escaped_braces_in_strings(self, summarizer):
        """Test parsing JSON with escaped braces in string values."""
        json_with_escaped = '{"summary_patch": {"current_goal": "This has \\"quotes\\" and {braces}"}, "extracted": {}, "bookkeeping": {}}'
        
        result = summarizer._parse_json_response(json_with_escaped)
        assert result is not None
        assert result["summary_patch"]["current_goal"] == 'This has "quotes" and {braces}'
    
    def test_parse_json_response_nested_objects(self, summarizer):
        """Test parsing deeply nested JSON structures."""
        nested_json = '{"summary_patch": {"current_goal": "test", "nested": {"deep": {"value": 123}}}, "extracted": {}, "bookkeeping": {}}'
        
        result = summarizer._parse_json_response(nested_json)
        assert result is not None
        assert result["summary_patch"]["nested"]["deep"]["value"] == 123
    
    def test_parse_json_response_unicode_characters(self, summarizer):
        """Test parsing JSON with unicode characters."""
        unicode_json = '{"summary_patch": {"current_goal": "测试 🚀 ñáéíóú"}, "extracted": {}, "bookkeeping": {}}'
        
        result = summarizer._parse_json_response(unicode_json)
        assert result is not None
        assert "测试" in result["summary_patch"]["current_goal"]
    
    def test_extract_largest_json_object_handles_multiple_objects(self, summarizer):
        """Test that _extract_largest_json_object correctly identifies largest object."""
        # Three objects, middle one is largest
        large_value = "x" * 100
        content = f'{{"small": "1"}} {{"summary_patch": {{"current_goal": "test", "large": "{large_value}"}}, "extracted": {{}}, "bookkeeping": {{}}}} {{"tiny": "2"}}'
        
        result = summarizer._extract_largest_json_object(content)
        assert result is not None
        parsed = json.loads(result)
        assert "summary_patch" in parsed
    
    def test_extract_largest_json_object_empty_string(self, summarizer):
        """Test _extract_largest_json_object with empty string."""
        result = summarizer._extract_largest_json_object("")
        assert result is None
    
    def test_extract_largest_json_object_no_braces(self, summarizer):
        """Test _extract_largest_json_object with no JSON objects."""
        result = summarizer._extract_largest_json_object("This is just text with no JSON")
        assert result is None
    
    def test_extract_largest_json_object_imbalanced_braces(self, summarizer):
        """Test _extract_largest_json_object with imbalanced braces."""
        content = '{"valid": "object"} {"invalid": {unclosed'
        result = summarizer._extract_largest_json_object(content)
        # Should extract the valid object, ignore the invalid one
        assert result is not None
        parsed = json.loads(result)
        assert parsed["valid"] == "object"
    
    # Issue 3: Missing event_id Hard Validation Tests
    def test_validate_missing_event_ids_facts_added(self, summarizer):
        """Test that missing event_ids in facts_added triggers hard error."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test goal"},
            "extracted": {
                "facts_added": [{"text": "Fact without event_ids", "confidence": "high"}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
        errors = validation.get("errors", [])
        assert len(errors) > 0
        # Should have specific error about missing event_ids
        assert any("missing event_ids" in error.lower() for error in errors)
        assert any("facts_added" in error for error in errors)
    
    def test_validate_missing_event_ids_decisions_added(self, summarizer):
        """Test that missing event_ids in decisions_added triggers hard error."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test goal"},
            "extracted": {
                "decisions_added": [{"text": "Decision without event_ids", "reasoning": "test"}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
        errors = validation.get("errors", [])
        assert any("missing event_ids" in error.lower() for error in errors)
        assert any("decisions_added" in error for error in errors)
    
    def test_validate_missing_event_ids_tasks_added(self, summarizer):
        """Test that missing event_ids in tasks_added triggers hard error."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test goal"},
            "extracted": {
                "tasks_added": [{"id": "task_1", "description": "Task without event_ids"}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
        errors = validation.get("errors", [])
        assert any("missing event_ids" in error.lower() for error in errors)
        assert any("tasks_added" in error for error in errors)
    
    def test_validate_missing_event_ids_error_includes_example_format(self, summarizer):
        """Test that missing event_ids error includes example format."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test goal"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high"}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
        errors = validation.get("errors", [])
        # Error should include example format
        error_text = " ".join(errors)
        assert "event_ids" in error_text
        # Should mention the required format
        assert "format" in error_text.lower() or "required" in error_text.lower()
    
    # Issue 3: Bookkeeping Field Naming Tests
    def test_bookkeeping_uses_new_last_summarized_event_id(self, summarizer, mock_llm_client):
        """Test that bookkeeping consistently uses new_last_summarized_event_id."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"},
            {"event_id": "evt_2", "type": "assistant_message", "content": "Hi"}
        ]
        
        # Response with both fields (should standardize on new_last_summarized_event_id)
        response_json = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {},
            "bookkeeping": {
                "last_summarized_event_id": "evt_1",
                "new_last_summarized_event_id": "evt_2"
            }
        }
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": json.dumps(response_json)}}]}
        mock_llm_client.extract_assistant_content.return_value = json.dumps(response_json)
        
        result = summarizer.summarize_delta("session_1", events)
        
        # Should have new_last_summarized_event_id
        assert result is not None
        assert "bookkeeping" in result
        assert "new_last_summarized_event_id" in result["bookkeeping"]
        assert result["bookkeeping"]["new_last_summarized_event_id"] == "evt_2"
    
    def test_validate_bookkeeping_requires_new_last_summarized_event_id(self, summarizer):
        """Test that validation requires new_last_summarized_event_id in bookkeeping."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        # Missing new_last_summarized_event_id
        result = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {},
            "bookkeeping": {
                "last_summarized_event_id": "evt_1"  # Missing new_last_summarized_event_id
            }
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
        assert any("new_last_summarized_event_id" in error for error in validation.get("errors", []))
    
    # Task completion prompt validation tests
    def test_system_prompt_includes_task_completion_guidance(self, summarizer, mock_llm_client):
        """Test that system prompt contains task completion instructions."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        # Mock LLM to capture messages
        captured_messages = []
        def capture_messages(messages, **kwargs):
            captured_messages.extend(messages)
            return {"choices": [{"message": {"content": '{"summary_patch": {}, "extracted": {}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}"}}]}
        
        mock_llm_client.chat.side_effect = capture_messages
        mock_llm_client.extract_assistant_content.return_value = '{"summary_patch": {}, "extracted": {}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}'
        
        summarizer.summarize_delta("session_1", events)
        
        # Find system message
        system_message = next((m for m in captured_messages if m.get("role") == "system"), None)
        assert system_message is not None
        system_content = system_message.get("content", "")
        
        # Verify task completion keywords are present
        assert "task" in system_content.lower()
        assert "completed" in system_content.lower() or "complete" in system_content.lower()
        assert "next_steps" in system_content.lower() or "next steps" in system_content.lower()
        assert "tasks_updated" in system_content.lower() or "tasks updated" in system_content.lower()
    
    def test_user_prompt_includes_previous_next_steps(self, summarizer, mock_llm_client):
        """Test that previous summary context includes next_steps."""
        events = [
            {"event_id": "evt_2", "type": "user_message", "content": "Test"}
        ]
        
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id="session_1",
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                last_summarized_event_id="evt_1",
                revision=0
            ),
            summary_blocks=SummaryBlocks(
                current_goal="Test goal",
                next_steps=["Step 1", "Step 2", "Step 3"]
            )
        )
        
        # Mock LLM to capture messages
        captured_messages = []
        def capture_messages(messages, **kwargs):
            captured_messages.extend(messages)
            return {"choices": [{"message": {"content": '{"summary_patch": {}, "extracted": {}, "bookkeeping": {"new_last_summarized_event_id": "evt_2"}}"}}]}
        
        mock_llm_client.chat.side_effect = capture_messages
        mock_llm_client.extract_assistant_content.return_value = '{"summary_patch": {}, "extracted": {}, "bookkeeping": {"new_last_summarized_event_id": "evt_2"}}'
        
        summarizer.summarize_delta("session_1", events, previous_summary)
        
        # Find user message
        user_message = next((m for m in captured_messages if m.get("role") == "user"), None)
        assert user_message is not None
        user_content = user_message.get("content", "")
        
        # Verify next_steps from previous summary are included
        assert "Next steps" in user_content or "next_steps" in user_content
        assert "Step 1" in user_content or "Step 2" in user_content
    
    def test_user_prompt_contains_task_completion_rules(self, summarizer, mock_llm_client):
        """Test that user prompt has explicit task completion rules."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        # Mock LLM to capture messages
        captured_messages = []
        def capture_messages(messages, **kwargs):
            captured_messages.extend(messages)
            return {"choices": [{"message": {"content": '{"summary_patch": {}, "extracted": {}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}"}}]}
        
        mock_llm_client.chat.side_effect = capture_messages
        mock_llm_client.extract_assistant_content.return_value = '{"summary_patch": {}, "extracted": {}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}'
        
        summarizer.summarize_delta("session_1", events)
        
        # Find user message
        user_message = next((m for m in captured_messages if m.get("role") == "user"), None)
        assert user_message is not None
        user_content = user_message.get("content", "")
        
        # Verify task completion rules are present
        assert "TASK MANAGEMENT" in user_content or "task completion" in user_content.lower() or "task" in user_content.lower()
        assert "completed" in user_content.lower() or "complete" in user_content.lower()
        assert "tasks_updated" in user_content or "tasks updated" in user_content.lower()

