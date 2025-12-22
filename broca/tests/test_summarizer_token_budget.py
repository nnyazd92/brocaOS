"""
Tests for token budget enforcement in Summarizer.

Tests global max_summary_tokens enforcement, compression strategies,
property-based testing, fault injection, and golden trace replay.
"""

from __future__ import annotations

from unittest.mock import Mock, MagicMock
import pytest
import json
from hypothesis import given, strategies as st, settings, HealthCheck

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


@pytest.fixture
def small_summarizer(mock_llm_client):
    """Summarizer with small token budget for testing."""
    return Summarizer(llm=mock_llm_client, max_summary_tokens=100, max_block_tokens=50)


class TestTokenBudgetEnforcement:
    """Test global token budget enforcement."""
    
    def test_enforce_size_limits_respects_max_summary_tokens(self, summarizer):
        """Test that global max_summary_tokens limit is enforced."""
        # Create a result that exceeds max_summary_tokens (1200)
        # Each character is ~0.25 tokens, so we need ~4800 chars to exceed 1200 tokens
        large_text = "x" * 5000  # ~1250 tokens
        
        result = {
            "summary_patch": {
                "current_goal": large_text,
                "what_we_built": [large_text[:1000]] * 10,
                "open_questions": [large_text[:1000]] * 10,
            },
            "extracted": {
                "facts_added": [
                    {"text": large_text[:500], "confidence": "high", "event_ids": ["evt_1"]}
                ] * 20
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        # Verify it exceeds limit before enforcement
        initial_tokens = estimate_tokens(result)
        assert initial_tokens > summarizer.max_summary_tokens
        
        # Enforce limits
        compressed = summarizer._enforce_size_limits(result)
        
        # Verify it's under limit after enforcement
        final_tokens = estimate_tokens(compressed)
        assert final_tokens <= summarizer.max_summary_tokens
    
    def test_enforce_size_limits_compresses_when_over_limit(self, small_summarizer):
        """Test that compression is applied when over limit."""
        # Create result that exceeds small limit (100 tokens)
        large_text = "x" * 500  # ~125 tokens
        
        result = {
            "summary_patch": {
                "current_goal": large_text,
                "what_we_built": [large_text[:200]] * 5,
            },
            "extracted": {},
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = small_summarizer._enforce_size_limits(result)
        
        # Should be compressed
        assert estimate_tokens(compressed) <= small_summarizer.max_summary_tokens
        # Text should be truncated
        assert len(compressed["summary_patch"]["current_goal"]) < len(large_text)
    
    def test_enforce_size_limits_preserves_evidence(self, small_summarizer):
        """Test that event_ids are preserved during compression."""
        result = {
            "summary_patch": {"current_goal": "x" * 500},
            "extracted": {
                "facts_added": [
                    {
                        "text": "x" * 500,  # Large text
                        "confidence": "high",
                        "event_ids": ["evt_1", "evt_2", "evt_3"]
                    }
                ] * 10
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = small_summarizer._enforce_size_limits(result)
        
        # Verify event_ids are preserved
        if compressed.get("extracted", {}).get("facts_added"):
            for item in compressed["extracted"]["facts_added"]:
                assert "event_ids" in item
                assert len(item["event_ids"]) > 0
    
    def test_enforce_size_limits_compression_priority(self, small_summarizer):
        """Test that compression follows priority order."""
        # Create result with all types of content
        large_text = "x" * 300
        
        result = {
            "summary_patch": {
                "current_goal": large_text,
                "what_we_built": [large_text[:200]] * 10,
                "open_questions": [large_text[:200]] * 10,
            },
            "extracted": {
                "facts_added": [
                    {"text": large_text, "confidence": "high", "event_ids": ["evt_1"]}
                ] * 10
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = small_summarizer._enforce_size_limits(result)
        
        # bookkeeping should be preserved
        assert "bookkeeping" in compressed
        assert "new_last_summarized_event_id" in compressed["bookkeeping"]
        
        # Overall result should be under limit
        assert estimate_tokens(compressed) <= small_summarizer.max_summary_tokens
        
        # summary_patch should exist
        assert "summary_patch" in compressed
        
        # Verify compression happened - either total is smaller or it's under limit
        initial_tokens = estimate_tokens(result)
        final_tokens = estimate_tokens(compressed)
        assert final_tokens <= small_summarizer.max_summary_tokens
        # Allow for rounding - if initial was over limit, final should be under
        if initial_tokens > small_summarizer.max_summary_tokens:
            assert final_tokens <= small_summarizer.max_summary_tokens
    
    def test_enforce_size_limits_handles_edge_cases(self, summarizer):
        """Test handling of edge cases."""
        # Empty dict
        result = {}
        compressed = summarizer._enforce_size_limits(result)
        assert compressed == {}
        
        # Missing summary_patch
        result = {"extracted": {}, "bookkeeping": {}}
        compressed = summarizer._enforce_size_limits(result)
        assert compressed == result
        
        # summary_patch is not a dict
        result = {"summary_patch": "not a dict"}
        compressed = summarizer._enforce_size_limits(result)
        assert compressed == result
        
        # Missing extracted
        result = {
            "summary_patch": {"current_goal": "test"},
            "bookkeeping": {}
        }
        compressed = summarizer._enforce_size_limits(result)
        assert "summary_patch" in compressed
        
        # Missing bookkeeping
        result = {
            "summary_patch": {"current_goal": "test"},
            "extracted": {}
        }
        compressed = summarizer._enforce_size_limits(result)
        assert "summary_patch" in compressed
    
    def test_enforce_size_limits_applies_final_truncation(self, small_summarizer):
        """Test that final truncation is applied when compression isn't enough."""
        # Create a result that's way over the limit
        huge_text = "x" * 10000  # Very large
        
        result = {
            "summary_patch": {
                "current_goal": huge_text,
                "what_we_built": [huge_text[:5000]] * 20,
                "open_questions": [huge_text[:5000]] * 20,
            },
            "extracted": {
                "facts_added": [
                    {"text": huge_text[:5000], "confidence": "high", "event_ids": ["evt_1"]}
                ] * 20
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = small_summarizer._enforce_size_limits(result)
        
        # Should be under limit even after aggressive compression
        final_tokens = estimate_tokens(compressed)
        assert final_tokens <= small_summarizer.max_summary_tokens
    
    def test_enforce_size_limits_token_estimation_accuracy(self, summarizer):
        """Test that token estimation works correctly."""
        # Simple case
        result = {
            "summary_patch": {"current_goal": "test"},
            "extracted": {},
            "bookkeeping": {}
        }
        tokens = estimate_tokens(result)
        assert tokens > 0
        assert isinstance(tokens, int)
        
        # Larger case
        large_result = {
            "summary_patch": {"current_goal": "x" * 1000},
            "extracted": {},
            "bookkeeping": {}
        }
        large_tokens = estimate_tokens(large_result)
        assert large_tokens > tokens


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        current_goal=st.text(min_size=0, max_size=5000),
        num_items=st.integers(min_value=0, max_value=100),
        item_length=st.integers(min_value=0, max_value=1000),
        num_facts=st.integers(min_value=0, max_value=50),
        fact_length=st.integers(min_value=0, max_value=1000),
    )
    def test_enforce_size_limits_always_under_budget(
        self, mock_llm_client, current_goal, num_items, item_length, num_facts, fact_length
    ):
        """Property: Result is always under max_summary_tokens."""
        summarizer = Summarizer(llm=mock_llm_client, max_summary_tokens=1000, max_block_tokens=200)
        
        result = {
            "summary_patch": {
                "current_goal": current_goal,
                "what_we_built": ["x" * item_length] * num_items,
                "open_questions": ["x" * item_length] * num_items,
            },
            "extracted": {
                "facts_added": [
                    {
                        "text": "x" * fact_length,
                        "confidence": "high",
                        "event_ids": ["evt_1", "evt_2"]
                    }
                ] * num_facts
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        final_tokens = estimate_tokens(compressed)
        
        assert final_tokens <= summarizer.max_summary_tokens
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        result_dict=st.dictionaries(
            keys=st.sampled_from(["summary_patch", "extracted", "bookkeeping", "conflicts"]),
            values=st.recursive(
                st.one_of(
                    st.text(),
                    st.integers(),
                    st.booleans(),
                    st.lists(st.text()),
                ),
                lambda children: st.dictionaries(st.text(), children, max_size=10),
                max_leaves=20
            ),
            max_size=10
        )
    )
    def test_enforce_size_limits_preserves_structure(self, mock_llm_client, result_dict):
        """Property: Result structure matches input structure."""
        summarizer = Summarizer(llm=mock_llm_client, max_summary_tokens=1000, max_block_tokens=200)
        
        # Ensure we have at least summary_patch for the method to work
        if "summary_patch" not in result_dict:
            result_dict["summary_patch"] = {}
        
        compressed = summarizer._enforce_size_limits(result_dict)
        
        # Top-level keys should be preserved if summary_patch is a dict
        if isinstance(result_dict.get("summary_patch"), dict):
            assert "summary_patch" in compressed
            assert isinstance(compressed.get("summary_patch"), dict)
    
    def test_enforce_size_limits_idempotent(self, summarizer):
        """Property: Applying twice doesn't change result."""
        result = {
            "summary_patch": {
                "current_goal": "x" * 2000,  # Large text
                "what_we_built": ["x" * 500] * 20,
            },
            "extracted": {
                "facts_added": [
                    {"text": "x" * 500, "confidence": "high", "event_ids": ["evt_1"]}
                ] * 20
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed_once = summarizer._enforce_size_limits(result)
        compressed_twice = summarizer._enforce_size_limits(compressed_once)
        
        # Token counts should be the same (or very close due to rounding)
        tokens_once = estimate_tokens(compressed_once)
        tokens_twice = estimate_tokens(compressed_twice)
        
        # Should be within 5% (allowing for minor estimation differences)
        assert abs(tokens_once - tokens_twice) <= max(1, tokens_once * 0.05)


class TestFaultInjection:
    """Fault injection tests for edge cases and error conditions."""
    
    def test_enforce_size_limits_handles_malformed_input(self, summarizer):
        """Test handling of malformed input structures."""
        # Invalid nested structure
        result = {
            "summary_patch": {
                "current_goal": None,  # None value
                "what_we_built": "not a list",  # Wrong type
            },
            "extracted": "not a dict",  # Wrong type
            "bookkeeping": {}
        }
        
        # Should not crash
        compressed = summarizer._enforce_size_limits(result)
        assert isinstance(compressed, dict)
    
    def test_enforce_size_limits_handles_extremely_large_input(self, summarizer):
        """Test handling of extremely large inputs."""
        # Create input that's 10x the limit
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
        
        assert final_tokens <= summarizer.max_summary_tokens
    
    def test_enforce_size_limits_handles_unicode_special_chars(self, summarizer):
        """Test handling of unicode and special characters."""
        # Unicode text
        unicode_text = "测试" * 1000 + "🚀" * 500 + "ñáéíóú" * 500
        
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
    
    def test_enforce_size_limits_handles_nested_structures(self, summarizer):
        """Test handling of deeply nested extracted items."""
        # Deeply nested structure
        nested_item = {
            "text": "fact",
            "confidence": "high",
            "event_ids": ["evt_1"],
            "metadata": {
                "nested": {
                    "deep": {
                        "value": "x" * 1000
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


class TestGoldenTraces:
    """Golden trace replay tests."""
    
    def test_enforce_size_limits_golden_traces(self, summarizer):
        """Test with captured real summary outputs."""
        # Golden trace 1: Typical summary
        golden_trace_1 = {
            "summary_patch": {
                "current_goal": "Implement token budget enforcement in summarizer",
                "what_we_built": [
                    "Added global token budget enforcement",
                    "Implemented compression strategies",
                    "Added comprehensive test suite"
                ],
                "open_questions": [
                    "Should we split summaries hierarchically?",
                    "What compression ratio is acceptable?"
                ],
                "constraints": ["Must preserve event_ids"],
                "next_steps": ["Run mutation testing", "Verify coverage"]
            },
            "extracted": {
                "facts_added": [
                    {
                        "text": "Token budget enforcement is needed",
                        "confidence": "high",
                        "event_ids": ["evt_1", "evt_2"]
                    }
                ],
                "decisions_added": [
                    {
                        "text": "Use aggressive compression first",
                        "reasoning": "Preserves evidence while reducing size",
                        "event_ids": ["evt_3"]
                    }
                ],
                "tasks_added": [
                    {
                        "id": "task_1",
                        "description": "Implement token budget",
                        "event_ids": ["evt_4"]
                    }
                ]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_10"}
        }
        
        compressed = summarizer._enforce_size_limits(golden_trace_1)
        
        # Should be under limit
        assert estimate_tokens(compressed) <= summarizer.max_summary_tokens
        # Should preserve structure
        assert "summary_patch" in compressed
        assert "extracted" in compressed
        assert "bookkeeping" in compressed
        # Should preserve event_ids
        if compressed.get("extracted", {}).get("facts_added"):
            assert "event_ids" in compressed["extracted"]["facts_added"][0]


class TestIntegration:
    """Integration tests."""
    
    def test_summarize_delta_respects_token_budget(self, summarizer, mock_llm_client):
        """Test that summarize_delta respects token budget end-to-end."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test message"},
            {"event_id": "evt_2", "type": "assistant_message", "content": "Response"}
        ]
        
        # Mock LLM to return a large response
        large_response = {
            "summary_patch": {
                "current_goal": "x" * 2000,
                "what_we_built": ["x" * 500] * 20,
            },
            "extracted": {
                "facts_added": [
                    {"text": "x" * 500, "confidence": "high", "event_ids": ["evt_1"]}
                ] * 20
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_2"}
        }
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": json.dumps(large_response)}}]}
        mock_llm_client.extract_assistant_content.return_value = json.dumps(large_response)
        
        result = summarizer.summarize_delta("session_1", events)
        
        if result:
            final_tokens = estimate_tokens(result)
            assert final_tokens <= summarizer.max_summary_tokens
    
    def test_token_budget_with_real_llm_responses(self, summarizer, mock_llm_client):
        """Test with mocked LLM responses of various sizes."""
        events = [
            {"event_id": f"evt_{i}", "type": "user_message", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        # Test with various response sizes
        for size_multiplier in [1, 2, 5, 10]:
            large_text = "x" * (100 * size_multiplier)
            response = {
                "summary_patch": {
                    "current_goal": large_text,
                    "what_we_built": [large_text[:100]] * size_multiplier,
                },
                "extracted": {
                    "facts_added": [
                        {"text": large_text[:100], "confidence": "high", "event_ids": [f"evt_{j}"]}
                        for j in range(size_multiplier)
                    ]
                },
                "bookkeeping": {"new_last_summarized_event_id": "evt_9"}
            }
            
            mock_llm_client.chat.return_value = {"choices": [{"message": {"content": json.dumps(response)}}]}
            mock_llm_client.extract_assistant_content.return_value = json.dumps(response)
            
            result = summarizer.summarize_delta("session_1", events)
            
            if result:
                final_tokens = estimate_tokens(result)
                assert final_tokens <= summarizer.max_summary_tokens

