"""
Fault injection tests for Summarizer.

Tests edge cases, error conditions, and malformed inputs to ensure graceful handling.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import json
import os
from typing import Dict, Any

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


class TestFaultInjection:
    """Fault injection tests for edge cases and error conditions."""
    
    def test_parse_json_response_malformed_missing_braces(self, summarizer):
        """Test handling of JSON with missing closing braces."""
        malformed = '{"summary_patch": {"current_goal": "test"}'
        
        result = summarizer._parse_json_response(malformed)
        # Should return None or handle gracefully
        assert result is None or isinstance(result, dict)
    
    def test_parse_json_response_trailing_comma(self, summarizer):
        """Test handling of JSON with trailing comma (invalid but common error)."""
        with_trailing_comma = '{"summary_patch": {"current_goal": "test"},}'
        
        result = summarizer._parse_json_response(with_trailing_comma)
        # Should handle gracefully
        assert result is None or isinstance(result, dict)
    
    def test_parse_json_response_invalid_escape(self, summarizer):
        """Test handling of invalid escape sequences."""
        invalid_escape = '{"summary_patch": {"current_goal": "test\\x"}}'
        
        result = summarizer._parse_json_response(invalid_escape)
        # Should handle gracefully
        assert result is None or isinstance(result, dict)
    
    def test_parse_json_response_null_bytes(self, summarizer):
        """Test handling of null bytes in input."""
        with_null = '{"summary_patch": {"current_goal": "test\\u0000"}}'
        
        result = summarizer._parse_json_response(with_null)
        # Should handle gracefully
        assert result is None or isinstance(result, dict)
    
    def test_parse_json_response_control_characters(self, summarizer):
        """Test handling of control characters."""
        with_control = '{"summary_patch": {"current_goal": "test\\n\\r\\t"}}'
        
        result = summarizer._parse_json_response(with_control)
        # Should parse successfully (control chars are valid in JSON strings)
        assert result is not None or isinstance(result, dict)
    
    def test_parse_json_response_very_deep_nesting(self, summarizer):
        """Test handling of very deeply nested structures."""
        # Create deeply nested JSON (100 levels)
        nested = {"level": 0}
        current = nested
        for i in range(100):
            current["nested"] = {"level": i + 1}
            current = current["nested"]
        
        json_str = json.dumps(nested)
        result = summarizer._parse_json_response(json_str)
        
        # Should handle deep nesting
        assert result is not None or isinstance(result, dict)
    
    def test_validate_summarization_result_missing_event_ids_various_combinations(self, summarizer):
        """Test validation with various combinations of missing event_ids."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"},
            {"event_id": "evt_2", "type": "assistant_message", "content": "Hi"}
        ]
        
        test_cases = [
            # Empty event_ids
            {
                "extracted": {
                    "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": []}]
                }
            },
            # Missing event_ids key
            {
                "extracted": {
                    "facts_added": [{"text": "Fact", "confidence": "high"}]
                }
            },
            # None as event_ids
            {
                "extracted": {
                    "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": None}]
                }
            },
            # Invalid type for event_ids
            {
                "extracted": {
                    "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": "not_a_list"}]
                }
            }
        ]
        
        for case in test_cases:
            result = {
                "summary_patch": {"current_goal": "Test"},
                "extracted": case["extracted"],
                "bookkeeping": {"new_last_summarized_event_id": "evt_2"}
            }
            
            validation = summarizer._validate_summarization_result(result, events)
            # Should all fail validation
            assert validation["valid"] is False
            assert len(validation.get("errors", [])) > 0
    
    def test_validate_summarization_result_invalid_event_ids_combinations(self, summarizer):
        """Test validation with various invalid event_id combinations."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        result = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [
                    {"text": "Fact 1", "confidence": "high", "event_ids": ["nonexistent"]},
                    {"text": "Fact 2", "confidence": "medium", "event_ids": ["evt_1", "nonexistent"]},
                    {"text": "Fact 3", "confidence": "low", "event_ids": ["evt_999"]}
                ]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation = summarizer._validate_summarization_result(result, events)
        assert validation["valid"] is False
        # Should have errors for all invalid event_ids
        errors = validation.get("errors", [])
        assert len(errors) > 0
    
    def test_enforce_size_limits_extremely_large_input(self, summarizer):
        """Test handling of extremely large inputs (10x token limits)."""
        huge_text = "x" * (summarizer.max_summary_tokens * 40)  # 10x in chars
        
        result = {
            "summary_patch": {
                "current_goal": huge_text,
                "what_we_built": [huge_text[:10000]] * 100,
            },
            "extracted": {
                "facts_added": [
                    {"text": huge_text[:10000], "confidence": "high", "event_ids": ["evt_1"]}
                ] * 100
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        final_tokens = estimate_tokens(compressed)
        
        # Should still be under limit
        assert final_tokens <= summarizer.max_summary_tokens
        assert isinstance(compressed, dict)
    
    def test_enforce_size_limits_unicode_special_chars(self, summarizer):
        """Test handling of unicode and special characters."""
        unicode_text = "测试" * 1000 + "🚀" * 500 + "ñáéíóú" * 500 + "αβγδε" * 200
        
        result = {
            "summary_patch": {
                "current_goal": unicode_text,
                "what_we_built": [unicode_text[:500]] * 10,
            },
            "extracted": {
                "facts_added": [
                    {"text": unicode_text[:500], "confidence": "high", "event_ids": ["evt_1"]}
                ] * 10
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        final_tokens = estimate_tokens(compressed)
        
        assert final_tokens <= summarizer.max_summary_tokens
        # Unicode should be preserved
        if compressed.get("summary_patch", {}).get("current_goal"):
            assert any(ord(c) > 127 for c in compressed["summary_patch"]["current_goal"][:100])
    
    def test_enforce_size_limits_deeply_nested_structures(self, summarizer):
        """Test handling of deeply nested extracted items."""
        nested_item = {
            "text": "fact",
            "confidence": "high",
            "event_ids": ["evt_1"],
            "metadata": {
                "nested": {
                    "deep": {
                        "very_deep": {
                            "value": "x" * 1000
                        }
                    }
                }
            }
        }
        
        result = {
            "summary_patch": {"current_goal": "x" * 2000},
            "extracted": {
                "facts_added": [nested_item] * 20
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        final_tokens = estimate_tokens(compressed)
        
        assert final_tokens <= summarizer.max_summary_tokens
        assert isinstance(compressed, dict)
    
    def test_enforce_size_limits_empty_null_values(self, summarizer):
        """Test handling of empty and null values in required fields."""
        test_cases = [
            {"summary_patch": None},
            {"summary_patch": ""},
            {"summary_patch": {"current_goal": None}},
            {"extracted": None},
            {"extracted": ""},
            {"bookkeeping": None},
            {"bookkeeping": {}},
        ]
        
        for case in test_cases:
            result = {
                "summary_patch": {"current_goal": "test"},
                "extracted": {},
                "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
            }
            result.update(case)
            
            # Should not crash
            compressed = summarizer._enforce_size_limits(result)
            assert isinstance(compressed, dict)
    
    def test_enforce_size_limits_type_mismatches(self, summarizer):
        """Test handling of type mismatches (wrong types in fields)."""
        result = {
            "summary_patch": "not a dict",  # Wrong type
            "extracted": ["not a dict"],  # Wrong type
            "bookkeeping": None
        }
        
        # Should handle gracefully
        compressed = summarizer._enforce_size_limits(result)
        assert isinstance(compressed, dict)
    
    def test_enforce_size_limits_list_items_wrong_type(self, summarizer):
        """Test handling of wrong types in list items."""
        result = {
            "summary_patch": {
                "current_goal": "test",
                "what_we_built": [123, {"not": "a string"}, None]  # Wrong types
            },
            "extracted": {},
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        assert isinstance(compressed, dict)
    
    def test_enforce_size_limits_summary_tokens_zero_edge_case(self, summarizer):
        """Test edge case where summary_tokens calculation might be 0."""
        # Empty or minimal result
        result = {
            "summary_patch": {
                "current_goal": "",
                "what_we_built": [],
                "open_questions": [],
                "constraints": [],
                "next_steps": []
            },
            "extracted": {},
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        tokens = estimate_tokens(compressed)
        
        # Should handle empty case gracefully
        assert tokens >= 0
        assert isinstance(compressed, dict)
    
    def test_retry_with_feedback_handles_llm_exception(self, summarizer, mock_llm_client):
        """Test that retry handles LLM exceptions gracefully."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        first_result = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": []}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation_result = {"valid": False, "errors": ["Missing event_ids"]}
        messages = [{"role": "system", "content": "test"}, {"role": "user", "content": "prompt"}]
        
        # Simulate LLM exception
        mock_llm_client.chat.side_effect = Exception("LLM API error")
        
        result = summarizer._retry_with_feedback(
            first_result, validation_result, "prompt", messages, events
        )
        
        # Should return None on error, not crash
        assert result is None
    
    def test_retry_with_feedback_empty_llm_response(self, summarizer, mock_llm_client):
        """Test that retry handles empty LLM response."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        first_result = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": []}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        validation_result = {"valid": False, "errors": ["Missing event_ids"]}
        messages = [{"role": "system", "content": "test"}, {"role": "user", "content": "prompt"}]
        
        # Empty response
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_llm_client.extract_assistant_content.return_value = ""
        
        result = summarizer._retry_with_feedback(
            first_result, validation_result, "prompt", messages, events
        )
        
        # Should return None for empty response
        assert result is None
    
    def test_summarize_delta_empty_events(self, summarizer):
        """Test summarize_delta with empty events list."""
        result = summarizer.summarize_delta("session_1", [])
        
        # Should return None for empty events
        assert result is None
    
    def test_summarize_delta_llm_returns_none(self, summarizer, mock_llm_client):
        """Test summarize_delta when LLM returns None."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        mock_llm_client.extract_assistant_content.return_value = None
        
        result = summarizer.summarize_delta("session_1", events)
        
        # Should handle None response gracefully
        assert result is None
    
    def test_summarize_delta_parse_fails(self, summarizer, mock_llm_client):
        """Test summarize_delta when JSON parsing fails."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Hello"}
        ]
        
        # Invalid JSON
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": "not json"}}]}
        mock_llm_client.extract_assistant_content.return_value = "not json"
        
        result = summarizer.summarize_delta("session_1", events)
        
        # Should return None when parsing fails
        assert result is None

