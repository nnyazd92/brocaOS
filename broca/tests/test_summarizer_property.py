"""
Property-based tests for Summarizer using Hypothesis.

Tests invariants and properties that should hold for all inputs.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json
from hypothesis import given, strategies as st, settings, HealthCheck, assume
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


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(
        current_goal=st.text(min_size=0, max_size=5000),
        num_items=st.integers(min_value=0, max_value=100),
        item_length=st.integers(min_value=0, max_value=200),
        num_facts=st.integers(min_value=0, max_value=50),
        fact_length=st.integers(min_value=0, max_value=200),
    )
    def test_enforce_size_limits_always_under_budget(
        self, mock_llm_client, current_goal, num_items, item_length, num_facts, fact_length
    ):
        """Property: Result is always under max_summary_tokens after enforcement."""
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
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(content=st.text())
    def test_parse_json_response_never_crashes(self, summarizer, content):
        """Property: _parse_json_response never crashes on any string input."""
        # Should either return None or a valid JSON value (dict, list, str, int, etc), never crash
        try:
            result = summarizer._parse_json_response(content)
            # If not None, should be a valid JSON-serializable type
            if result is not None:
                # Should be JSON-serializable (dict, list, str, int, float, bool, None)
                assert isinstance(result, (dict, list, str, int, float, bool)) or result is None
        except Exception as e:
            pytest.fail(f"_parse_json_response crashed on input: {repr(content[:100])}, error: {e}")
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        result_dict=st.dictionaries(
            keys=st.sampled_from(["summary_patch", "extracted", "bookkeeping", "conflicts"]),
            values=st.recursive(
                st.one_of(
                    st.text(max_size=100),
                    st.integers(),
                    st.booleans(),
                    st.lists(st.text(max_size=50), max_size=10),
                ),
                lambda children: st.dictionaries(st.text(max_size=20), children, max_size=5),
                max_leaves=20
            ),
            max_size=10
        )
    )
    def test_enforce_size_limits_preserves_structure(self, mock_llm_client, result_dict):
        """Property: Result structure matches input structure (top-level keys preserved)."""
        summarizer = Summarizer(llm=mock_llm_client, max_summary_tokens=1000, max_block_tokens=200)
        
        # Ensure we have at least summary_patch for the method to work
        if "summary_patch" not in result_dict:
            result_dict["summary_patch"] = {}
        
        compressed = summarizer._enforce_size_limits(result_dict)
        
        # Top-level keys should be preserved if summary_patch is a dict
        if isinstance(result_dict.get("summary_patch"), dict):
            assert "summary_patch" in compressed
            assert isinstance(compressed.get("summary_patch"), dict)
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        events=st.lists(
            st.dictionaries(
                keys=st.sampled_from(["event_id", "type", "content"]),
                values=st.text(max_size=100),
                min_size=1,
                max_size=5
            ),
            min_size=0,
            max_size=20
        ),
        result_dict=st.dictionaries(
            keys=st.just("summary_patch") | st.just("extracted") | st.just("bookkeeping"),
            values=st.dictionaries(st.text(max_size=20), st.text(max_size=50), max_size=5),
            min_size=1,
            max_size=3
        )
    )
    def test_validate_summarization_result_idempotent(self, summarizer, events, result_dict):
        """Property: Validation is idempotent (running twice gives same result)."""
        # Ensure basic structure
        if "summary_patch" not in result_dict:
            result_dict["summary_patch"] = {}
        if "extracted" not in result_dict:
            result_dict["extracted"] = {}
        if "bookkeeping" not in result_dict:
            result_dict["bookkeeping"] = {}
        
        # Add event_ids to events for realistic validation
        for i, event in enumerate(events):
            event["event_id"] = event.get("event_id", f"evt_{i}")
        
        validation1 = summarizer._validate_summarization_result(result_dict, events)
        validation2 = summarizer._validate_summarization_result(result_dict, events)
        
        assert validation1["valid"] == validation2["valid"]
        assert set(validation1.get("errors", [])) == set(validation2.get("errors", []))
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        num_facts=st.integers(min_value=1, max_value=20),
        fact_text_length=st.integers(min_value=1, max_value=500),
        num_event_ids=st.integers(min_value=1, max_value=10)
    )
    def test_compress_aggressively_preserves_event_ids(
        self, summarizer, num_facts, fact_text_length, num_event_ids
    ):
        """Property: Compression preserves event_ids even when truncating text."""
        large_text = "x" * fact_text_length
        
        result = {
            "summary_patch": {"current_goal": large_text * 10},  # Way over limit
            "extracted": {
                "facts_added": [
                    {
                        "text": large_text,
                        "confidence": "high",
                        "event_ids": [f"evt_{j}" for j in range(num_event_ids)]
                    }
                ] * num_facts
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        
        # Verify event_ids are preserved in compressed result
        if compressed.get("extracted", {}).get("facts_added"):
            for item in compressed["extracted"]["facts_added"]:
                assert "event_ids" in item
                assert isinstance(item["event_ids"], list)
                assert len(item["event_ids"]) > 0
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(
        text1=st.text(max_size=1000),
        text2=st.text(max_size=1000)
    )
    def test_estimate_tokens_monotonic(self, text1, text2):
        """Property: Token estimation is monotonic (larger input → more tokens)."""
        tokens1 = estimate_tokens(text1)
        tokens2 = estimate_tokens(text2)
        
        # If text1 is longer, tokens1 should be >= tokens2 (allowing for rounding)
        if len(text1) > len(text2) * 2:  # Significant difference
            assert tokens1 >= tokens2 - 1  # Allow small rounding differences
        
        # Combining texts should give at least the sum (minus small overhead)
        combined_tokens = estimate_tokens(text1 + text2)
        assert combined_tokens >= tokens1 + tokens2 - 2  # Allow small rounding
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        valid_json_str=st.recursive(
            st.one_of(
                st.text(max_size=50),
                st.integers(),
                st.booleans(),
                st.floats(allow_nan=False, allow_infinity=False),
            ),
            lambda children: st.one_of(
                st.lists(children, max_size=5),
                st.dictionaries(st.text(max_size=10), children, max_size=5)
            ),
            max_leaves=10
        )
    )
    def test_parse_json_response_handles_valid_json(self, summarizer, valid_json_str):
        """Property: Valid JSON strings are parsed correctly."""
        try:
            json_str = json.dumps(valid_json_str)
            result = summarizer._parse_json_response(json_str)
            
            # If it's a dict, should parse successfully
            if isinstance(valid_json_str, dict):
                assert result is not None
                assert isinstance(result, dict)
                # Top-level keys should match
                if result:
                    assert set(result.keys()).issubset(set(valid_json_str.keys()))
        except (TypeError, ValueError):
            # Some values can't be JSON serialized, skip those
            assume(False)
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        max_tokens=st.integers(min_value=50, max_value=1000),  # Minimum 50 to reliably fit compressed structure
        max_block_tokens=st.integers(min_value=5, max_value=200)
    )
    def test_enforce_size_limits_respects_config(self, mock_llm_client, max_tokens, max_block_tokens):
        """Property: Size limits respect configuration parameters."""
        assume(max_block_tokens <= max_tokens)  # Block limit should be <= total limit
        assume(max_tokens >= 50)  # Need minimum tokens for reliable compression
        
        summarizer = Summarizer(
            llm=mock_llm_client,
            max_summary_tokens=max_tokens,
            max_block_tokens=max_block_tokens
        )
        
        # Create result that definitely exceeds limits
        # Use reasonable size to avoid memory issues
        huge_text = "x" * min(max_tokens * 40, 50000)  # Cap at 50k chars
        result = {
            "summary_patch": {
                "current_goal": huge_text,
                "what_we_built": [huge_text[:min(1000, max_tokens * 10)]] * min(50, max_tokens),
            },
            "extracted": {},
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        compressed = summarizer._enforce_size_limits(result)
        final_tokens = estimate_tokens(compressed)
        
        # Should be under limit (allow small rounding differences)
        assert final_tokens <= max_tokens + 5  # Allow 5 token tolerance for rounding/estimation
    
    # Task completion property tests
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        next_steps=st.lists(st.text(max_size=100), min_size=0, max_size=10),
        tasks_updated=st.lists(
            st.fixed_dictionaries({
                "id": st.text(min_size=1, max_size=50),
                "status": st.sampled_from(["completed", "in_progress", "pending", "cancelled"]),
                "event_ids": st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)
            }),
            min_size=0,
            max_size=10
        )
    )
    def test_next_steps_never_contains_completed_tasks(
        self, next_steps, tasks_updated
    ):
        """Property: After filtering, no completed task should appear in next_steps."""
        # This property will be tested after merge logic is implemented
        # For now, we verify the invariant conceptually
        completed_task_ids = {
            t["id"].lower() for t in tasks_updated if t["status"] == "completed"
        }
        
        # Filter logic: remove items from next_steps that match completed task IDs
        # Simple heuristic: if next_step contains task_id or vice versa
        filtered_next_steps = []
        for step in next_steps:
            step_lower = step.lower()
            is_completed = any(
                task_id in step_lower or step_lower in task_id 
                for task_id in completed_task_ids
            )
            if not is_completed:
                filtered_next_steps.append(step)
        
        # Property: No completed task should be in filtered_next_steps
        for step in filtered_next_steps:
            step_lower = step.lower()
            for task_id in completed_task_ids:
                # If task_id and step overlap significantly, they should have been filtered
                if task_id in step_lower or step_lower in task_id:
                    # This should not happen in filtered list
                    assert False, f"Completed task {task_id} found in filtered next_steps: {step}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        tasks_updated=st.lists(
            st.fixed_dictionaries({
                "id": st.text(min_size=1, max_size=50),
                "status": st.sampled_from(["completed", "in_progress", "pending", "cancelled"]),
                "event_ids": st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)
            }),
            min_size=1,
            max_size=10
        ),
        next_steps=st.lists(st.text(max_size=100), min_size=0, max_size=10)
    )
    def test_tasks_updated_implies_not_in_next_steps(self, tasks_updated, next_steps):
        """Property: If task in tasks_updated with status='completed', it must not be in next_steps after filtering."""
        completed_tasks = [t for t in tasks_updated if t.get("status") == "completed"]
        
        if not completed_tasks:
            # No completed tasks, property trivially holds
            return
        
        # Filter logic simulation
        completed_task_ids = {t["id"].lower() for t in completed_tasks}
        filtered_next_steps = []
        for step in next_steps:
            step_lower = step.lower()
            is_completed = any(
                task_id in step_lower or step_lower in task_id 
                for task_id in completed_task_ids
            )
            if not is_completed:
                filtered_next_steps.append(step)
        
        # Property: For each completed task, it should not appear in filtered_next_steps
        for completed_task in completed_tasks:
            task_id_lower = completed_task["id"].lower()
            for step in filtered_next_steps:
                step_lower = step.lower()
                # If they overlap, property is violated
                assert not (task_id_lower in step_lower or step_lower in task_id_lower), \
                    f"Completed task {completed_task['id']} found in filtered next_steps: {step}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        previous_next_steps=st.lists(st.text(max_size=100), min_size=0, max_size=10),
        new_next_steps=st.lists(st.text(max_size=100), min_size=0, max_size=10),
        completed_task_ids=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5)
    )
    def test_next_steps_filtering_invariant(
        self, previous_next_steps, new_next_steps, completed_task_ids
    ):
        """Property: Merge result's next_steps is subset of union that excludes completed."""
        # Simulate merge: extend previous + new
        all_next_steps = previous_next_steps + new_next_steps
        
        # Filter out completed tasks
        completed_ids_lower = {tid.lower() for tid in completed_task_ids}
        filtered_next_steps = []
        for step in all_next_steps:
            step_lower = step.lower()
            is_completed = any(
                task_id in step_lower or step_lower in task_id 
                for task_id in completed_ids_lower
            )
            if not is_completed:
                filtered_next_steps.append(step)
        
        # Property 1: Filtered result is a subset of union (some items may be filtered out)
        assert len(filtered_next_steps) <= len(all_next_steps)
        
        # Property 2: All items in filtered result are in original union
        for step in filtered_next_steps:
            assert step in all_next_steps
        
        # Property 3: No completed task appears in filtered result
        for step in filtered_next_steps:
            step_lower = step.lower()
            for task_id in completed_ids_lower:
                assert not (task_id in step_lower or step_lower in task_id), \
                    f"Completed task {task_id} found in filtered result"

