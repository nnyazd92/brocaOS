"""
Tests for event logger.

Tests JSONL append-only logging of conversation events.
"""

from __future__ import annotations

import tempfile
import os
import json
import hashlib
from pathlib import Path
from unittest.mock import Mock
import pytest
from datetime import datetime, timezone

from broca.summarization.event_logger import EventLogger


@pytest.fixture
def temp_event_log_dir():
    """Temporary directory for event logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def event_logger(temp_event_log_dir):
    """EventLogger instance for testing."""
    return EventLogger(log_dir=temp_event_log_dir)


class TestEventLogger:
    """Test EventLogger functionality."""
    
    def test_log_user_message(self, event_logger, temp_event_log_dir):
        """Test logging user messages."""
        session_id = "test_session_123"
        content = "Hello, how are you?"
        
        event_id = event_logger.log_user_message(session_id, content)
        
        # Check event file exists
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        assert log_file.exists()
        
        # Read and parse event
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            event = json.loads(lines[0])
            
            assert event["event_id"] == event_id
            assert event["type"] == "user_message"
            assert event["role"] == "user"
            assert event["content"] == content
            assert "ts" in event
            assert "sha256" in event
            assert event["sha256"] == hashlib.sha256(content.encode()).hexdigest()
    
    def test_log_assistant_message(self, event_logger, temp_event_log_dir):
        """Test logging assistant messages."""
        session_id = "test_session_123"
        content = "I'm doing well, thank you!"
        
        event_id = event_logger.log_assistant_message(session_id, content)
        
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'r') as f:
            event = json.loads(f.readlines()[0])
            
            assert event["type"] == "assistant_message"
            assert event["role"] == "assistant"
            assert event["content"] == content
            assert event["sha256"] == hashlib.sha256(content.encode()).hexdigest()
    
    def test_log_tool_call(self, event_logger, temp_event_log_dir):
        """Test logging tool calls."""
        session_id = "test_session_123"
        tool_name = "web_search"
        tool_args = {"query": "python programming"}
        
        event_id = event_logger.log_tool_call(session_id, tool_name, tool_args)
        
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'r') as f:
            event = json.loads(f.readlines()[0])
            
            assert event["type"] == "tool_call"
            assert event["tool_name"] == tool_name
            assert event["tool_args"] == tool_args
            assert "sha256" in event
    
    def test_log_tool_result(self, event_logger, temp_event_log_dir):
        """Test logging tool results."""
        session_id = "test_session_123"
        tool_name = "web_search"
        tool_result = {"results": [{"title": "Python", "url": "https://python.org"}]}
        
        event_id = event_logger.log_tool_result(session_id, tool_name, tool_result)
        
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'r') as f:
            event = json.loads(f.readlines()[0])
            
            assert event["type"] == "tool_result"
            assert event["tool_name"] == tool_name
            assert event["tool_result"] == tool_result
            assert "sha256" in event
    
    def test_append_only_behavior(self, event_logger, temp_event_log_dir):
        """Test that events are appended, not overwritten."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "First message")
        event_id2 = event_logger.log_user_message(session_id, "Second message")
        event_id3 = event_logger.log_assistant_message(session_id, "Response")
        
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3
            
            events = [json.loads(line) for line in lines]
            assert events[0]["event_id"] == event_id1
            assert events[1]["event_id"] == event_id2
            assert events[2]["event_id"] == event_id3
            assert events[0]["content"] == "First message"
            assert events[1]["content"] == "Second message"
            assert events[2]["content"] == "Response"
    
    def test_event_id_uniqueness(self, event_logger):
        """Test that event IDs are unique."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "Message 1")
        event_id2 = event_logger.log_user_message(session_id, "Message 2")
        
        assert event_id1 != event_id2
    
    def test_event_id_format(self, event_logger):
        """Test that event IDs have expected format."""
        session_id = "test_session_123"
        event_id = event_logger.log_user_message(session_id, "Test")
        
        # Event ID should be a string
        assert isinstance(event_id, str)
        assert len(event_id) > 0
        # Should start with session_id or be a UUID/hash
        assert event_id is not None
    
    def test_timestamp_format(self, event_logger, temp_event_log_dir):
        """Test that timestamps are in ISO format."""
        session_id = "test_session_123"
        event_logger.log_user_message(session_id, "Test")
        
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'r') as f:
            event = json.loads(f.readlines()[0])
            
            # Timestamp should be parseable as ISO format
            ts = datetime.fromisoformat(event["ts"].replace('Z', '+00:00'))
            assert isinstance(ts, datetime)
    
    def test_sha256_hash(self, event_logger, temp_event_log_dir):
        """Test that SHA256 hashes are computed correctly."""
        session_id = "test_session_123"
        content = "Test content for hashing"
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        
        event_logger.log_user_message(session_id, content)
        
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'r') as f:
            event = json.loads(f.readlines()[0])
            assert event["sha256"] == expected_hash

    def test_log_priming_selected_and_outcome(self, event_logger, temp_event_log_dir):
        session_id = "test_session_priming"
        sel_id = event_logger.log_priming_selected(session_id, {"mode": "chat", "selected_ids": [1]})
        out_id = event_logger.log_priming_outcome(session_id, {"mode": "chat", "used_score": 0.5})

        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            lines = [json.loads(ln) for ln in f.read().splitlines() if ln.strip()]

        assert len(lines) == 2
        assert lines[0]["event_id"] == sel_id
        assert lines[0]["type"] == "priming_selected"
        assert isinstance(lines[0]["payload"], dict)

        assert lines[1]["event_id"] == out_id
        assert lines[1]["type"] == "priming_outcome"
        assert isinstance(lines[1]["payload"], dict)
    
    def test_tool_result_sha256(self, event_logger, temp_event_log_dir):
        """Test SHA256 for tool results (JSON serialized)."""
        session_id = "test_session_123"
        tool_result = {"key": "value", "number": 42}
        result_json = json.dumps(tool_result, sort_keys=True)
        expected_hash = hashlib.sha256(result_json.encode()).hexdigest()
        
        event_logger.log_tool_result(session_id, "test_tool", tool_result)
        
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'r') as f:
            event = json.loads(f.readlines()[0])
            assert event["sha256"] == expected_hash
    
    def test_get_events(self, event_logger):
        """Test retrieving events from log."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        events = event_logger.get_events(session_id)
        assert len(events) == 2
        assert events[0]["event_id"] == event_id1
        assert events[1]["event_id"] == event_id2
    
    def test_get_events_empty(self, event_logger):
        """Test getting events from non-existent session."""
        events = event_logger.get_events("nonexistent_session")
        assert events == []
    
    def test_get_events_after_event_id(self, event_logger):
        """Test getting events after a specific event ID."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        event_id3 = event_logger.log_user_message(session_id, "Third")
        
        events = event_logger.get_events_after(session_id, event_id1)
        assert len(events) == 2
        assert events[0]["event_id"] == event_id2
        assert events[1]["event_id"] == event_id3
    
    def test_get_events_after_nonexistent(self, event_logger):
        """Test getting events after non-existent event ID."""
        session_id = "test_session_123"
        event_logger.log_user_message(session_id, "First")
        
        events = event_logger.get_events_after(session_id, "nonexistent_id")
        # Should return all events if event_id not found
        assert len(events) >= 1
    
    def test_get_event_ids_set(self, event_logger):
        """Test getting event IDs as a set for efficient membership testing."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        event_id3 = event_logger.log_assistant_message(session_id, "Response")
        
        event_ids_set = event_logger.get_event_ids_set(session_id)
        
        assert isinstance(event_ids_set, set)
        assert len(event_ids_set) == 3
        assert event_id1 in event_ids_set
        assert event_id2 in event_ids_set
        assert event_id3 in event_ids_set
    
    def test_get_event_ids_set_empty(self, event_logger):
        """Test getting event IDs set for empty session."""
        session_id = "empty_session"
        event_ids_set = event_logger.get_event_ids_set(session_id)
        
        assert isinstance(event_ids_set, set)
        assert len(event_ids_set) == 0
    
    def test_get_event_ids_set_nonexistent_session(self, event_logger):
        """Test getting event IDs set for non-existent session."""
        event_ids_set = event_logger.get_event_ids_set("nonexistent_session")
        
        assert isinstance(event_ids_set, set)
        assert len(event_ids_set) == 0
    
    def test_get_event_ids_set_excludes_none(self, event_logger, temp_event_log_dir):
        """Test that get_event_ids_set excludes events without event_id."""
        session_id = "test_session_123"
        
        # Create events normally
        event_id1 = event_logger.log_user_message(session_id, "First")
        
        # Manually write an event without event_id (corrupted entry)
        log_file = Path(temp_event_log_dir) / f"{session_id}_raw.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps({"type": "corrupted", "content": "no event_id"}) + '\n')
        
        event_ids_set = event_logger.get_event_ids_set(session_id)
        
        # Should only include event_id1, not the corrupted entry
        assert event_id1 in event_ids_set
        assert len(event_ids_set) == 1
    
    def test_get_event_ids_after(self, event_logger):
        """Test getting event IDs added after a specific event ID."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        event_id3 = event_logger.log_user_message(session_id, "Third")
        
        event_ids_set = event_logger.get_event_ids_after(session_id, event_id1)
        
        assert isinstance(event_ids_set, set)
        assert event_id1 not in event_ids_set  # Should not include the reference event
        assert event_id2 in event_ids_set
        assert event_id3 in event_ids_set
        assert len(event_ids_set) == 2
    
    def test_get_event_ids_after_none(self, event_logger):
        """Test getting event IDs after None (should return all event IDs)."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        event_ids_set = event_logger.get_event_ids_after(session_id, None)
        
        assert isinstance(event_ids_set, set)
        assert event_id1 in event_ids_set
        assert event_id2 in event_ids_set
        assert len(event_ids_set) == 2
    
    def test_get_event_ids_after_empty(self, event_logger):
        """Test getting event IDs after event ID when no events exist."""
        session_id = "empty_session"
        event_ids_set = event_logger.get_event_ids_after(session_id, "some_id")
        
        assert isinstance(event_ids_set, set)
        assert len(event_ids_set) == 0
    
    def test_get_event_ids_after_nonexistent_event_id(self, event_logger):
        """Test getting event IDs after non-existent event ID."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        # Should return all events if after_event_id not found
        event_ids_set = event_logger.get_event_ids_after(session_id, "nonexistent_id")
        
        assert isinstance(event_ids_set, set)
        assert event_id1 in event_ids_set
        assert event_id2 in event_ids_set
        assert len(event_ids_set) == 2
    
    def test_get_event_ids_after_last_event(self, event_logger):
        """Test getting event IDs after the last event (should return empty set)."""
        session_id = "test_session_123"
        
        event_id1 = event_logger.log_user_message(session_id, "First")
        event_id2 = event_logger.log_user_message(session_id, "Second")
        
        # Get the last event ID
        events = event_logger.get_events(session_id)
        last_event_id = events[-1]["event_id"]
        
        event_ids_set = event_logger.get_event_ids_after(session_id, last_event_id)
        
        assert isinstance(event_ids_set, set)
        assert len(event_ids_set) == 0

