"""
Golden trace replay tests for message validation and filtering.

Tests with real conversation traces to ensure message ordering is maintained
and to prevent regressions.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from broca.repl.session import ConversationSession


# Path to golden trace fixtures
GOLDEN_TRACES_DIR = Path(__file__).parent / "fixtures" / "golden_traces"


def load_golden_trace(trace_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a golden trace from JSON file.
    
    Args:
        trace_name: Name of trace file (without .json extension)
    
    Returns:
        Dictionary with trace data or None if not found
    """
    trace_path = GOLDEN_TRACES_DIR / f"{trace_name}.json"
    
    if not trace_path.exists():
        return None
    
    try:
        with open(trace_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def create_golden_trace_fixture(trace_name: str, messages: List[Dict[str, Any]], 
                                description: str = "", expected_valid: bool = True):
    """
    Create a golden trace fixture file.
    
    Args:
        trace_name: Name for the trace file
        messages: List of messages in the trace
        description: Description of the trace
        expected_valid: Whether the trace should be valid
    """
    # Ensure directory exists
    GOLDEN_TRACES_DIR.mkdir(parents=True, exist_ok=True)
    
    trace_data = {
        "description": description,
        "messages": messages,
        "expected_valid": expected_valid,
        "expected_filtered_count": len(messages)  # Default, may be adjusted
    }
    
    trace_path = GOLDEN_TRACES_DIR / f"{trace_name}.json"
    with open(trace_path, 'w') as f:
        json.dump(trace_data, f, indent=2)


class TestGoldenTraceReplay:
    """Golden trace replay tests."""
    
    def test_basic_tool_call_sequence(self, mock_llm_client: Mock):
        """
        Test replay of basic tool call sequence.
        
        Golden trace: Simple conversation with one tool call.
        """
        # Create a basic golden trace
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather in San Francisco?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "San Francisco"}'
                        }
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 65, "condition": "sunny"}',
                "tool_call_id": "call_abc123"
            },
            {"role": "assistant", "content": "The weather in San Francisco is 65°F and sunny."}
        ]
        
        session = ConversationSession(llm=mock_llm_client)
        session.messages = messages
        
        # Validate original messages
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True, f"Golden trace invalid: {error}"
        
        # Test filtering maintains validity
        filtered = session._get_messages_for_llm()
        is_valid_filtered, error_filtered = session._validate_message_ordering(filtered)
        assert is_valid_filtered is True, f"Filtered golden trace invalid: {error_filtered}"
    
    def test_multiple_tool_calls_sequence(self, mock_llm_client: Mock):
        """
        Test replay of multiple tool calls in sequence.
        
        Golden trace: Conversation with multiple tool calls.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Get the weather and current time."},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_weather_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "San Francisco"}'
                        }
                    },
                    {
                        "id": "call_time_456",
                        "type": "function",
                        "function": {
                            "name": "get_time",
                            "arguments": '{"timezone": "America/Los_Angeles"}'
                        }
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 65, "condition": "sunny"}',
                "tool_call_id": "call_weather_123"
            },
            {
                "role": "tool",
                "name": "get_time",
                "content": '{"time": "2024-01-15T14:30:00-08:00"}',
                "tool_call_id": "call_time_456"
            },
            {"role": "assistant", "content": "The weather is 65°F and sunny. The current time is 2:30 PM."}
        ]
        
        session = ConversationSession(llm=mock_llm_client)
        session.messages = messages
        
        # Validate
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True, f"Golden trace invalid: {error}"
        
        # Test filtering
        filtered = session._get_messages_for_llm()
        is_valid_filtered, error_filtered = session._validate_message_ordering(filtered)
        assert is_valid_filtered is True, f"Filtered golden trace invalid: {error_filtered}"
    
    def test_conversation_with_multiple_turns(self, mock_llm_client: Mock):
        """
        Test replay of conversation with multiple turns and tool calls.
        
        Golden trace: Multi-turn conversation with tool calls in different turns.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_1"
            },
            {"role": "assistant", "content": "The weather is 72°F."},
            {"role": "user", "content": "What time is it?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {"name": "get_time", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_time",
                "content": '{"time": "3:00 PM"}',
                "tool_call_id": "call_2"
            },
            {"role": "assistant", "content": "It's 3:00 PM."}
        ]
        
        session = ConversationSession(llm=mock_llm_client)
        session.messages = messages
        
        # Validate
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True, f"Golden trace invalid: {error}"
        
        # Test filtering with summarization
        with patch.object(session, '_summarization_manager') as mock_mgr:
            mock_mgr.summary_storage.load_session_summary.return_value = {"summary": "test"}
            from broca.config import config
            with patch.object(config, 'summarization') as mock_summarization:
                with patch.object(config, 'llm') as mock_llm:
                    type(mock_summarization).last_turns_count = 2
                    type(mock_llm).max_context_tokens = 100000
                    type(mock_summarization).max_tool_result_size = 1000
                
                filtered = session._get_messages_for_llm()
                is_valid_filtered, error_filtered = session._validate_message_ordering(filtered)
                assert is_valid_filtered is True, f"Filtered golden trace invalid: {error_filtered}"
    
    def test_regression_orphaned_tool_message(self, mock_llm_client: Mock):
        """
        Test regression: orphaned tool message scenario.
        
        Golden trace: This should trigger the original bug where tool messages
        appear without preceding tool_calls after filtering.
        """
        # This simulates the scenario from the error log
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Old question that will be filtered"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_old",
                        "type": "function",
                        "function": {"name": "old_tool", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "old_tool",
                "content": '{"result": "old"}',
                "tool_call_id": "call_old"
            },
            {"role": "assistant", "content": "Old response"},
            {"role": "user", "content": "New question"},
            {"role": "assistant", "content": "New response"}
        ]
        
        session = ConversationSession(llm=mock_llm_client)
        session.messages = messages
        
        # Mock summarization to filter to last turn only
        # This should remove the old tool call sequence
        with patch.object(session, '_summarization_manager') as mock_mgr:
            mock_mgr.summary_storage.load_session_summary.return_value = {"summary": "test"}
            from broca.config import config
            with patch.object(config, 'summarization') as mock_summarization:
                with patch.object(config, 'llm') as mock_llm:
                    type(mock_summarization).last_turns_count = 1
                    type(mock_llm).max_context_tokens = 100000
                    type(mock_summarization).max_tool_result_size = 1000
                
                filtered = session._get_messages_for_llm()
                
                # This should NOT have orphaned tool messages
                is_valid, error = session._validate_message_ordering(filtered)
                assert is_valid is True, f"Regression detected: orphaned tool message: {error}"
                
                # Verify no orphaned tool messages
                tool_messages = [m for m in filtered if m.get("role") == "tool"]
                for tool_msg in tool_messages:
                    tool_call_id = tool_msg.get("tool_call_id")
                    # Find matching assistant with tool_calls
                    found = False
                    for msg in filtered:
                        if msg.get("role") == "assistant" and msg.get("tool_calls"):
                            tool_call_ids = [tc.get("id") for tc in msg.get("tool_calls", [])]
                            if tool_call_id in tool_call_ids:
                                found = True
                                break
                    assert found, f"Orphaned tool message found: {tool_msg}"
    
    def test_load_and_replay_saved_trace(self, mock_llm_client: Mock):
        """
        Test loading and replaying a saved golden trace.
        
        If golden trace files exist, load and replay them.
        """
        # Check if golden traces directory exists and has files
        if not GOLDEN_TRACES_DIR.exists():
            pytest.skip("Golden traces directory does not exist")
        
        trace_files = list(GOLDEN_TRACES_DIR.glob("*.json"))
        if not trace_files:
            pytest.skip("No golden trace files found")
        
        # Load and test first available trace
        trace_file = trace_files[0]
        with open(trace_file, 'r') as f:
            trace_data = json.load(f)
        
        messages = trace_data.get("messages", [])
        expected_valid = trace_data.get("expected_valid", True)
        
        if not messages:
            pytest.skip(f"Trace {trace_file.name} has no messages")
        
        session = ConversationSession(llm=mock_llm_client)
        session.messages = messages
        
        # Validate
        is_valid, error = session._validate_message_ordering(messages)
        if expected_valid:
            assert is_valid is True, f"Golden trace {trace_file.name} invalid: {error}"
        else:
            # If trace is expected to be invalid, that's also a valid test case
            assert is_valid is False or error is not None
        
        # Test filtering if trace is valid
        if expected_valid and is_valid:
            filtered = session._get_messages_for_llm()
            is_valid_filtered, error_filtered = session._validate_message_ordering(filtered)
            assert is_valid_filtered is True, f"Filtered trace {trace_file.name} invalid: {error_filtered}"




