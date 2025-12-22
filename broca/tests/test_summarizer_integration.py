"""
Integration tests for Summarizer.

End-to-end tests for the summarize_delta workflow.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock
import pytest
import json

from broca.summarization.summarizer import Summarizer
from broca.summarization.storage import SummaryStorage
from broca.summarization.models import SessionSummary, SummaryHeader, SummaryBlocks
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
def temp_storage_dir():
    """Temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def storage(temp_storage_dir):
    """SummaryStorage instance."""
    return SummaryStorage(summary_path=temp_storage_dir)


class TestIntegration:
    """Integration tests for end-to-end scenarios."""
    
    def test_summarize_delta_synthetic_session(self, summarizer, mock_llm_client):
        """Test summarizing a synthetic session with multiple events."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "I want to build a web app"},
            {"event_id": "evt_2", "type": "assistant_message", "content": "Great! What kind of web app?"},
            {"event_id": "evt_3", "type": "user_message", "content": "A todo list application"},
            {"event_id": "evt_4", "type": "tool_call", "tool_name": "code_search", "tool_args": {"query": "todo"}},
            {"event_id": "evt_5", "type": "tool_result", "tool_name": "code_search", "tool_result": {"files": ["todo.py"]}},
            {"event_id": "evt_6", "type": "assistant_message", "content": "I found some todo-related code"}
        ]
        
        # Mock LLM response
        response_json = {
            "summary_patch": {
                "current_goal": "Build a todo list web application",
                "what_we_built": ["Found existing todo-related code"],
                "open_questions": ["What framework to use?"],
                "constraints": [],
                "next_steps": ["Review existing code", "Choose framework"]
            },
            "extracted": {
                "facts_added": [
                    {
                        "text": "User wants to build a todo list web app",
                        "confidence": "high",
                        "event_ids": ["evt_1", "evt_3"]
                    }
                ],
                "decisions_added": [],
                "tasks_added": [
                    {
                        "id": "task_1",
                        "description": "Review existing todo code",
                        "event_ids": ["evt_5"]
                    }
                ]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_6"}
        }
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": json.dumps(response_json)}}]}
        mock_llm_client.extract_assistant_content.return_value = json.dumps(response_json)
        
        result = summarizer.summarize_delta("session_1", events)
        
        assert result is not None
        assert result["summary_patch"]["current_goal"] == "Build a todo list web application"
        assert len(result["extracted"]["facts_added"]) > 0
        assert result["bookkeeping"]["new_last_summarized_event_id"] == "evt_6"
    
    def test_summarize_delta_with_previous_summary(self, summarizer, mock_llm_client):
        """Test delta summarization with previous summary context."""
        previous_summary = SessionSummary(
            header=SummaryHeader(
                session_id="session_1",
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0,
                last_summarized_event_id="evt_3"
            ),
            summary_blocks=SummaryBlocks(
                current_goal="Build a todo list web application",
                what_we_built=["Found existing todo-related code"],
                open_questions=["What framework to use?"]
            )
        )
        
        # New events
        events = [
            {"event_id": "evt_4", "type": "user_message", "content": "Let's use Flask"},
            {"event_id": "evt_5", "type": "assistant_message", "content": "Good choice! Flask is simple"}
        ]
        
        # Mock LLM response
        response_json = {
            "summary_patch": {
                "current_goal": "Build a todo list web application using Flask",
                "what_we_built": ["Found existing todo-related code", "Chose Flask framework"],
                "open_questions": ["What database to use?"],
                "constraints": [],
                "next_steps": ["Set up Flask project"]
            },
            "extracted": {
                "facts_added": [
                    {
                        "text": "User chose Flask framework",
                        "confidence": "high",
                        "event_ids": ["evt_4"]
                    }
                ],
                "decisions_added": [
                    {
                        "text": "Use Flask for the web framework",
                        "reasoning": "Flask is simple and suitable",
                        "event_ids": ["evt_4", "evt_5"]
                    }
                ],
                "tasks_added": []
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_5"}
        }
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": json.dumps(response_json)}}]}
        mock_llm_client.extract_assistant_content.return_value = json.dumps(response_json)
        
        result = summarizer.summarize_delta("session_1", events, previous_summary=previous_summary)
        
        assert result is not None
        assert "Flask" in result["summary_patch"]["current_goal"]
        assert len(result["extracted"]["decisions_added"]) > 0
    
    def test_save_load_cycle_with_storage(self, summarizer, storage, mock_llm_client):
        """Test complete save/load cycle with SummaryStorage."""
        session_id = "test_session"
        
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test message"},
            {"event_id": "evt_2", "type": "assistant_message", "content": "Test response"}
        ]
        
        # Mock LLM response
        response_json = {
            "summary_patch": {
                "current_goal": "Test goal",
                "what_we_built": [],
                "open_questions": [],
                "constraints": [],
                "next_steps": []
            },
            "extracted": {},
            "bookkeeping": {"new_last_summarized_event_id": "evt_2"}
        }
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": json.dumps(response_json)}}]}
        mock_llm_client.extract_assistant_content.return_value = json.dumps(response_json)
        
        # Summarize
        result = summarizer.summarize_delta(session_id, events)
        assert result is not None
        
        # Create SessionSummary and save
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0,
                last_summarized_event_id=result["bookkeeping"]["new_last_summarized_event_id"]
            ),
            summary_blocks=SummaryBlocks(
                current_goal=result["summary_patch"]["current_goal"],
                what_we_built=result["summary_patch"].get("what_we_built", []),
                open_questions=result["summary_patch"].get("open_questions", []),
                constraints=result["summary_patch"].get("constraints", []),
                next_steps=result["summary_patch"].get("next_steps", [])
            )
        )
        
        storage.save_session_summary(session_id, summary)
        
        # Load and verify
        loaded = storage.load_session_summary(session_id)
        assert loaded is not None
        assert loaded.summary_blocks.current_goal == "Test goal"
        assert loaded.header.last_summarized_event_id == "evt_2"
    
    def test_compression_ratio_edge_case_zero_tokens(self, summarizer):
        """Test compression ratio check with edge case where summary_tokens=0."""
        # Minimal result
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
        
        tokens = estimate_tokens(result)
        assert tokens >= 0
        
        # Enforce limits (should handle gracefully)
        compressed = summarizer._enforce_size_limits(result)
        compressed_tokens = estimate_tokens(compressed)
        
        assert compressed_tokens >= 0
        assert compressed_tokens <= summarizer.max_summary_tokens
    
    def test_summarize_delta_respects_token_budget_end_to_end(self, summarizer, mock_llm_client):
        """Test that summarize_delta respects token budget end-to-end."""
        events = [
            {"event_id": f"evt_{i}", "type": "user_message", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        # Mock LLM to return a large response
        large_response = {
            "summary_patch": {
                "current_goal": "x" * 2000,
                "what_we_built": ["x" * 500] * 20,
            },
            "extracted": {
                "facts_added": [
                    {"text": "x" * 500, "confidence": "high", "event_ids": [f"evt_{j}"]}
                    for j in range(20)
                ]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_9"}
        }
        
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": json.dumps(large_response)}}]}
        mock_llm_client.extract_assistant_content.return_value = json.dumps(large_response)
        
        result = summarizer.summarize_delta("session_1", events)
        
        if result:
            final_tokens = estimate_tokens(result)
            assert final_tokens <= summarizer.max_summary_tokens
    
    def test_summarize_delta_retry_flow(self, summarizer, mock_llm_client):
        """Test complete retry flow when first response fails validation."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        # First response (invalid - missing event_ids)
        first_response = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high"}]  # Missing event_ids
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        # Retry response (valid)
        retry_response = {
            "summary_patch": {"current_goal": "Test"},
            "extracted": {
                "facts_added": [{"text": "Fact", "confidence": "high", "event_ids": ["evt_1"]}]
            },
            "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
        }
        
        # First call returns invalid, second returns valid
        mock_llm_client.chat.side_effect = [
            {"choices": [{"message": {"content": json.dumps(first_response)}}]},
            {"choices": [{"message": {"content": json.dumps(retry_response)}}]}
        ]
        mock_llm_client.extract_assistant_content.side_effect = [
            json.dumps(first_response),
            json.dumps(retry_response)
        ]
        
        result = summarizer.summarize_delta("session_1", events)
        
        # Should succeed after retry
        assert result is not None
        assert len(result["extracted"]["facts_added"]) > 0
        assert len(result["extracted"]["facts_added"][0]["event_ids"]) > 0
        
        # Should have been called twice (initial + retry)
        assert mock_llm_client.chat.call_count == 2
    
    def test_summarize_delta_empty_events_returns_none(self, summarizer):
        """Test that summarize_delta returns None for empty events."""
        result = summarizer.summarize_delta("session_1", [])
        assert result is None
    
    def test_summarize_delta_llm_exception_handled(self, summarizer, mock_llm_client):
        """Test that LLM exceptions are handled gracefully."""
        events = [
            {"event_id": "evt_1", "type": "user_message", "content": "Test"}
        ]
        
        # Simulate LLM exception
        mock_llm_client.chat.side_effect = Exception("LLM API error")
        
        result = summarizer.summarize_delta("session_1", events)
        
        # Should return None, not crash
        assert result is None

