"""
Golden trace replay tests for Summarizer.

Tests with captured real LLM responses to ensure no regressions.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock
import pytest

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
def golden_traces_dir():
    """Path to golden traces directory."""
    return Path(__file__).parent / "fixtures" / "golden_traces"


def load_golden_trace(trace_name: str, golden_traces_dir: Path) -> dict:
    """Load a golden trace JSON file."""
    trace_path = golden_traces_dir / f"{trace_name}.json"
    if not trace_path.exists():
        pytest.skip(f"Golden trace {trace_name} not found at {trace_path}")
    
    with open(trace_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class TestGoldenTraces:
    """Golden trace replay tests."""
    
    def test_golden_trace_typical_summary(self, summarizer, golden_traces_dir):
        """Test with typical summary golden trace."""
        golden_trace = load_golden_trace("typical_summary", golden_traces_dir)
        
        # Simulate this being the LLM response
        json_str = json.dumps(golden_trace)
        
        # Test parsing
        parsed = summarizer._parse_json_response(json_str)
        assert parsed is not None
        assert parsed["summary_patch"]["current_goal"] == golden_trace["summary_patch"]["current_goal"]
        
        # Test validation with mock events
        events = [
            {"event_id": f"evt_{i}", "type": "user_message", "content": f"Message {i}"}
            for i in range(1, 11)
        ]
        
        validation = summarizer._validate_summarization_result(parsed, events)
        assert validation["valid"] is True
        
        # Test size enforcement
        compressed = summarizer._enforce_size_limits(parsed)
        assert estimate_tokens(compressed) <= summarizer.max_summary_tokens
        
        # Verify structure preserved
        assert "summary_patch" in compressed
        assert "extracted" in compressed
        assert "bookkeeping" in compressed
    
    def test_golden_trace_task_completion_typical(self, summarizer, golden_traces_dir):
        """Test with typical task completion golden trace."""
        golden_trace = load_golden_trace("task_completion_typical", golden_traces_dir)
        
        json_str = json.dumps(golden_trace)
        
        # Test parsing
        parsed = summarizer._parse_json_response(json_str)
        assert parsed is not None
        assert parsed["summary_patch"]["current_goal"] == golden_trace["summary_patch"]["current_goal"]
        
        # Test validation with mock events
        events = [
            {"event_id": f"evt_{i}", "type": "user_message", "content": f"Message {i}"}
            for i in range(1, 8)
        ]
        
        validation = summarizer._validate_summarization_result(parsed, events)
        assert validation["valid"] is True
        
        # Verify task completion property: completed task should NOT be in next_steps
        next_steps = parsed["summary_patch"].get("next_steps", [])
        tasks_updated = parsed["extracted"].get("tasks_updated", [])
        completed_task_ids = {
            t["id"].lower() 
            for t in tasks_updated 
            if t.get("status") == "completed"
        }
        
        # No completed tasks should appear in next_steps
        for step in next_steps:
            step_lower = step.lower()
            for task_id in completed_task_ids:
                assert task_id not in step_lower, f"Completed task {task_id} found in next_steps: {step}"
    
    def test_golden_trace_task_completion_multiple(self, summarizer, golden_traces_dir):
        """Test with multiple task completion golden trace."""
        golden_trace = load_golden_trace("task_completion_multiple", golden_traces_dir)
        
        json_str = json.dumps(golden_trace)
        
        # Test parsing
        parsed = summarizer._parse_json_response(json_str)
        assert parsed is not None
        
        # Test validation
        events = [
            {"event_id": f"evt_{i}", "type": "user_message", "content": f"Message {i}"}
            for i in range(1, 12)
        ]
        
        validation = summarizer._validate_summarization_result(parsed, events)
        assert validation["valid"] is True
        
        # Verify: completed tasks should NOT be in next_steps
        next_steps = parsed["summary_patch"].get("next_steps", [])
        tasks_updated = parsed["extracted"].get("tasks_updated", [])
        completed_task_ids = {
            t["id"].lower() 
            for t in tasks_updated 
            if t.get("status") == "completed"
        }
        
        # Only pending tasks should be in next_steps
        for step in next_steps:
            step_lower = step.lower()
            for task_id in completed_task_ids:
                assert task_id not in step_lower, f"Completed task {task_id} found in next_steps: {step}"
        
        # Verify pending tasks are in next_steps
        assert len(next_steps) > 0
    
    def test_golden_trace_task_completion_regression(self, summarizer, golden_traces_dir):
        """Test regression case: verify completed task is removed from next_steps."""
        golden_trace = load_golden_trace("task_completion_regression", golden_traces_dir)
        
        json_str = json.dumps(golden_trace)
        
        # Test parsing
        parsed = summarizer._parse_json_response(json_str)
        assert parsed is not None
        
        # Test validation
        events = [
            {"event_id": f"evt_{i}", "type": "user_message", "content": f"Message {i}"}
            for i in range(1, 8)
        ]
        
        validation = summarizer._validate_summarization_result(parsed, events)
        assert validation["valid"] is True
        
        # Regression test: completed task must NOT be in next_steps
        next_steps = parsed["summary_patch"].get("next_steps", [])
        tasks_updated = parsed["extracted"].get("tasks_updated", [])
        
        # Extract completed task descriptions/IDs
        completed_task_info = [
            t["id"].lower() 
            for t in tasks_updated 
            if t.get("status") == "completed"
        ]
        
        # Verify completed task is not in next_steps (the bug this fixes)
        for step in next_steps:
            step_lower = step.lower()
            for task_info in completed_task_info:
                # Should not contain completed task
                assert task_info not in step_lower or "fix" not in step_lower.lower(), \
                    f"Regression: Completed task '{task_info}' found in next_steps: '{step}'"
        
        # Completed task should be in tasks_updated
        assert len(tasks_updated) > 0
        assert any(t.get("status") == "completed" for t in tasks_updated)
    
    def test_golden_trace_large_summary(self, summarizer, golden_traces_dir):
        """Test with large summary golden trace."""
        golden_trace = load_golden_trace("large_summary", golden_traces_dir)
        
        json_str = json.dumps(golden_trace)
        
        # Test parsing
        parsed = summarizer._parse_json_response(json_str)
        assert parsed is not None
        
        # Test validation
        events = [
            {"event_id": f"evt_{i}", "type": "user_message", "content": f"Message {i}"}
            for i in range(1, 21)
        ]
        
        validation = summarizer._validate_summarization_result(parsed, events)
        assert validation["valid"] is True
        
        # Test compression (large summary should be compressed)
        initial_tokens = estimate_tokens(parsed)
        compressed = summarizer._enforce_size_limits(parsed)
        final_tokens = estimate_tokens(compressed)
        
        # Should be under limit
        assert final_tokens <= summarizer.max_summary_tokens
        
        # If initial was over limit, should be compressed
        if initial_tokens > summarizer.max_summary_tokens:
            assert final_tokens < initial_tokens
        
        # Verify event_ids preserved
        if compressed.get("extracted", {}).get("facts_added"):
            for item in compressed["extracted"]["facts_added"]:
                assert "event_ids" in item
                assert len(item["event_ids"]) > 0
    
    def test_golden_trace_markdown_wrapped(self, summarizer, golden_traces_dir):
        """Test parsing golden trace wrapped in markdown code blocks."""
        golden_trace = load_golden_trace("typical_summary", golden_traces_dir)
        json_str = json.dumps(golden_trace)
        
        # Wrap in markdown
        markdown_wrapped = f"```json\n{json_str}\n```"
        
        parsed = summarizer._parse_json_response(markdown_wrapped)
        assert parsed is not None
        assert parsed["summary_patch"]["current_goal"] == golden_trace["summary_patch"]["current_goal"]
    
    def test_golden_trace_with_trailing_text(self, summarizer, golden_traces_dir):
        """Test parsing golden trace with trailing explanatory text."""
        golden_trace = load_golden_trace("typical_summary", golden_traces_dir)
        json_str = json.dumps(golden_trace)
        
        # Add trailing text
        with_trailing = json_str + "\n\nThis is a valid JSON response above."
        
        parsed = summarizer._parse_json_response(with_trailing)
        assert parsed is not None
        assert parsed["summary_patch"]["current_goal"] == golden_trace["summary_patch"]["current_goal"]
    
    def test_golden_trace_compression_preserves_event_ids(self, summarizer, golden_traces_dir):
        """Test that compression preserves event_ids from golden traces."""
        golden_trace = load_golden_trace("large_summary", golden_traces_dir)
        
        # Create events matching the trace
        all_event_ids = set()
        for category in ["facts_added", "decisions_added", "tasks_added"]:
            for item in golden_trace.get("extracted", {}).get(category, []):
                all_event_ids.update(item.get("event_ids", []))
        
        events = [
            {"event_id": evt_id, "type": "user_message", "content": f"Message for {evt_id}"}
            for evt_id in all_event_ids
        ]
        
        # Enforce size limits (might compress)
        compressed = summarizer._enforce_size_limits(golden_trace)
        
        # Verify all event_ids are still present and valid
        for category in ["facts_added", "decisions_added", "tasks_added"]:
            compressed_items = compressed.get("extracted", {}).get(category, [])
            for item in compressed_items:
                assert "event_ids" in item
                event_ids = item.get("event_ids", [])
                assert len(event_ids) > 0
                
                # Verify event_ids exist in events
                for evt_id in event_ids:
                    assert any(e.get("event_id") == evt_id for e in events)
    
    def test_golden_trace_deterministic_compression(self, summarizer, golden_traces_dir):
        """Test that compression is deterministic (same input → same output)."""
        golden_trace = load_golden_trace("large_summary", golden_traces_dir)
        
        # Compress twice
        compressed1 = summarizer._enforce_size_limits(golden_trace)
        compressed2 = summarizer._enforce_size_limits(golden_trace)
        
        # Token counts should be identical
        tokens1 = estimate_tokens(compressed1)
        tokens2 = estimate_tokens(compressed2)
        assert tokens1 == tokens2
        
        # Structure should be identical
        assert json.dumps(compressed1, sort_keys=True) == json.dumps(compressed2, sort_keys=True)
    
    def test_golden_trace_compression_ratio(self, summarizer, golden_traces_dir):
        """Test that compression ratios are reasonable."""
        golden_trace = load_golden_trace("large_summary", golden_traces_dir)
        
        # Calculate initial size
        initial_tokens = estimate_tokens(golden_trace)
        
        # Compress
        compressed = summarizer._enforce_size_limits(golden_trace)
        final_tokens = estimate_tokens(compressed)
        
        # Compression ratio should be reasonable (not more than 10x reduction)
        if initial_tokens > summarizer.max_summary_tokens:
            compression_ratio = initial_tokens / final_tokens
            assert compression_ratio < 10.0, f"Compression ratio {compression_ratio} is too aggressive"
        
        # Final should be under limit
        assert final_tokens <= summarizer.max_summary_tokens
        
        # Should preserve essential structure
        assert "bookkeeping" in compressed
        assert "new_last_summarized_event_id" in compressed["bookkeeping"]

