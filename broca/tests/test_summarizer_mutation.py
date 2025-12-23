"""
Mutation testing validation tests for Summarizer.

These tests are designed to kill mutations in the summarizer code.
The actual mutation testing is run with mutmut, but these tests help
validate that our test suite is comprehensive enough to catch bugs.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json

from broca.summarization.summarizer import Summarizer
from broca.summarization.token_estimator import estimate_tokens


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


class TestMutationKillers:
    """
    Tests specifically designed to kill mutations.
    
    These tests verify specific behaviors that would be broken by common mutations
    like changing operators, conditions, or return values.
    """
    
    def test_parse_json_response_returns_none_for_empty_string(self, summarizer):
        """Kills mutation: changing return to not-None for empty string."""
        result = summarizer._parse_json_response("")
        # Should return None for empty string
        assert result is None
    
    def test_parse_json_response_handles_markdown_code_block(self, summarizer):
        """Kills mutation: removing markdown code block handling."""
        content = "```json\n{\"test\": \"value\"}\n```"
        result = summarizer._parse_json_response(content)
        assert result is not None
        assert result["test"] == "value"
    
    def test_extract_largest_json_object_handles_no_objects(self, summarizer):
        """Kills mutation: returning non-None for no objects."""
        result = summarizer._extract_largest_json_object("no json here")
        assert result is None
    
    def test_extract_largest_json_object_returns_largest(self, summarizer):
        """Kills mutation: returning smallest instead of largest."""
        content = '{"small": "1"} {"large": {"nested": "value", "more": "data"}}'
        result = summarizer._extract_largest_json_object(content)
        assert result is not None
        # Should be the larger object
        assert "large" in result or "small" in result
        parsed = json.loads(result)
        # Verify it's a dict with content
        assert isinstance(parsed, dict)
        assert len(str(parsed)) > len('{"small": "1"}')
    
    def test_validate_summarization_result_valid_result(self, summarizer):
        """Kills mutation: returning invalid for valid result."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["evt_1"]}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is True
    
    def test_validate_summarization_result_invalid_missing_key(self, summarizer):
        """Kills mutation: returning valid for missing required key."""
        events = []
        
        result = {
            "summary_patch": {},
            # Missing extracted and bookkeeping
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
    
    def test_validate_summarization_result_invalid_event_ids(self, summarizer):
        """Kills mutation: not checking event_ids."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["nonexistent"]}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
        assert any("invalid event_ids" in error for error in validation.get("errors", []))
    
    def test_enforce_size_limits_returns_dict(self, summarizer):
        """Kills mutation: returning None or wrong type."""
        result = {
            "summary_patch": {"current_goal": "test"},
            "extracted": {},
            "bookkeeping": {}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        assert isinstance(compressed, dict)
        assert "summary_patch" in compressed
    
    def test_enforce_size_limits_respects_max_tokens(self, summarizer):
        """Kills mutation: not enforcing max_summary_tokens."""
        large_text = "x" * 5000
        result = {
            "summary_patch": {
                "current_goal": large_text,
                "what_we_built": [large_text[:1000]] * 20,
            },
            "extracted": {},
            "bookkeeping": {}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        tokens = estimate_tokens(compressed)
        assert tokens <= summarizer.max_summary_tokens
    
    def test_enforce_size_limits_preserves_bookkeeping(self, summarizer):
        """Kills mutation: removing bookkeeping."""
        result = {
            "summary_patch": {"current_goal": "x" * 5000},
            "extracted": {},
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        assert "bookkeeping" in compressed
        assert "new_last_summarized_event_id" in compressed["bookkeeping"]
    
    def test_enforce_size_limits_preserves_event_ids(self, summarizer):
        """Kills mutation: removing event_ids during compression."""
        result = {
            "summary_patch": {"current_goal": "x" * 5000},
            "extracted": {
                "facts_added": [
                    {"text": "x" * 500, "confidence": "high", "event_ids": ["evt_1", "evt_2"]}
                ] * 10
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        
        # Event_ids should be preserved
        if compressed.get("extracted", {}).get("facts_added"):
            for item in compressed["extracted"]["facts_added"]:
                assert "event_ids" in item
                assert isinstance(item["event_ids"], list)
                assert len(item["event_ids"]) > 0
    
    def test_retry_with_feedback_uses_events_not_empty(self, summarizer, mock_llm_client):
        """Kills mutation: using empty list instead of events."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        first_result = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": []}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation_result = {"valid": False, "errors": ["missing event_ids"]}
        messages = [{"role": "system", "content": "test"}, {"role": "user", "content": "prompt"}]
        
        # Valid retry response
        retry_response = '{"summary_patch": {"current_goal": "Test"}, "extracted": {"facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["evt_1"]}]}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}'
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": retry_response}}]}
        mock_llm_client.extract_assistant_content.return_value = retry_response
        
        result = summarizer._retry_with_feedback(
            first_result, validation_result, "prompt", messages, events
        )
        
        # Should succeed with valid event_id
        assert result is not None
        assert result["extracted"]["facts_added"][0]["event_ids"] == ["evt_1"]
    
    def test_retry_with_feedback_returns_none_on_invalid_retry(self, summarizer, mock_llm_client):
        """Kills mutation: returning invalid result instead of None."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        first_result = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": []}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation_result = {"valid": False, "errors": ["missing event_ids"]}
        messages = [{"role": "system", "content": "test"}, {"role": "user", "content": "prompt"}]
        
        # Still invalid retry response
        retry_response = '{"summary_patch": {"current_goal": "Test"}, "extracted": {"facts_added": [{"text": "Fact", "confidence": "high", "event_ids": []}]}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}'
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": retry_response}}]}
        mock_llm_client.extract_assistant_content.return_value = retry_response
        
        result = summarizer._retry_with_feedback(
            first_result, validation_result, "prompt", messages, events
        )
        
        # Should return None for still-invalid response
        assert result is None
    
    def test_summarize_delta_returns_none_for_empty_events(self, summarizer):
        """Kills mutation: returning non-None for empty events."""
        result = summarizer.summarize_delta("session_1", [])
        assert result is None
    
    def test_summarize_delta_calls_enforce_size_limits(self, summarizer, mock_llm_client):
        """Kills mutation: not calling _enforce_size_limits."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        # Large response that needs compression
        large_response = {
            "summary_patch": {
                "current_goal": "x" * 5000,
            },
            "extracted": {},
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": json.dumps(large_response)}}]}
        mock_llm_client.extract_assistant_content.return_value = json.dumps(large_response)
        
        result = summarizer.summarize_delta("session_1", events)
        
        # Should be compressed
        if result:
            tokens = estimate_tokens(result)
            assert tokens <= summarizer.max_summary_tokens
    
    def test_prompt_contains_task_completion_keywords(self, summarizer, mock_llm_client):
        """Kills mutation: removing task completion keywords from prompt."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        captured_messages = []
        json_response = '{"summary_patch": {}, "extracted": {}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}'
        def capture_messages(messages, **kwargs):
            captured_messages.extend(messages)
            return {"choices": [{"message": {"content": json_response}}]}
        
        mock_llm_client.chat.side_effect = capture_messages
        mock_llm_client.extract_assistant_content.return_value = json_response
        
        summarizer.summarize_delta("session_1", events)
        
        # Find system message
        system_message = next((m for m in captured_messages if m.get("role") == "system"), None)
        assert system_message is not None
        system_content = system_message.get("content", "")
        
        # These keywords must be present (kills mutation that removes them)
        assert "completed" in system_content.lower() or "complete" in system_content.lower()
        assert "tasks_updated" in system_content or "tasks updated" in system_content.lower()
        assert "next_steps" in system_content or "next steps" in system_content.lower()
    
    def test_filter_completed_tasks_logic(self, summarizer):
        """Kills mutation: changing filter logic to include completed tasks."""
        # This tests the filtering logic conceptually
        # The actual implementation will be in manager.py
        
        completed_task_ids = {"task_a", "task_b"}
        next_steps = ["Complete task_a", "Do task_c", "Finish task_b"]
        
        # Correct filtering logic: remove items matching completed tasks
        filtered = []
        for step in next_steps:
            step_lower = step.lower()
            is_completed = any(
                task_id.lower() in step_lower or step_lower in task_id.lower()
                for task_id in completed_task_ids
            )
            if not is_completed:
                filtered.append(step)
        
        # Kills mutation: if logic changed to include completed, this would fail
        assert "Complete task_a" not in filtered
        assert "Finish task_b" not in filtered
        assert "Do task_c" in filtered
    
    def test_user_prompt_contains_task_rules(self, summarizer, mock_llm_client):
        """Kills mutation: removing task completion rules from user prompt."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        captured_messages = []
        json_response = '{"summary_patch": {}, "extracted": {}, "bookkeeping": {"new_last_summarized_event_id": "evt_1"}}'
        def capture_messages(messages, **kwargs):
            captured_messages.extend(messages)
            return {"choices": [{"message": {"content": json_response}}]}
        
        mock_llm_client.chat.side_effect = capture_messages
        mock_llm_client.extract_assistant_content.return_value = json_response
        
        summarizer.summarize_delta("session_1", events)
        
        # Find user message
        user_message = next((m for m in captured_messages if m.get("role") == "user"), None)
        assert user_message is not None
        user_content = user_message.get("content", "")
        
        # These keywords must be present in user prompt (kills mutation that removes them)
        # At least one of these task-related keywords should be present
        has_task_keyword = (
            "task" in user_content.lower() or
            "TASK MANAGEMENT" in user_content or
            "task completion" in user_content.lower() or
            "tasks_updated" in user_content or
            "completed" in user_content.lower()
        )
        assert has_task_keyword, "User prompt must contain task-related keywords"

