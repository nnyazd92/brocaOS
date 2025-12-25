"""
Integration tests for message filtering in ConversationSession.

Tests that message filtering maintains proper tool message ordering
and removes orphaned tool messages.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
from typing import List, Dict, Any

from broca.repl.session import ConversationSession
from broca.tests.utils import build_llm_response


class TestMessageFiltering:
    """Test message filtering maintains tool message ordering."""
    
    def test_filtering_preserves_tool_message_ordering(self, mock_llm_client: Mock):
        """
        Test that filtering preserves valid tool message ordering.
        
        When messages are filtered, tool messages should still follow
        their corresponding assistant messages with tool_calls.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create a conversation with tool calls
        session.messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "What's the weather?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            },
            {"role": "assistant", "content": "The weather is 72 degrees."}
        ]
        
        # Get filtered messages
        filtered = session._get_messages_for_llm()
        
        # Validate ordering is maintained
        is_valid, error = session._validate_message_ordering(filtered)
        assert is_valid is True, f"Filtered messages invalid: {error}"
    
    def test_filtering_removes_orphaned_tool_messages(self, mock_llm_client: Mock):
        """
        Test that filtering removes orphaned tool messages.
        
        If filtering removes an assistant message with tool_calls,
        the corresponding tool messages should also be removed.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create a conversation where early messages will be filtered out
        session.messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "First question"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            },
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Response 2"}
        ]
        
        # Mock summarization to force filtering to last turn only
        with patch.object(session, '_summarization_manager') as mock_mgr:
            mock_mgr.summary_storage.load_session_summary.return_value = {"summary": "test"}
            from broca.config import config
            with patch.object(config, 'summarization') as mock_summarization:
                with patch.object(config, 'llm') as mock_llm:
                    type(mock_summarization).last_turns_count = 1
                    type(mock_llm).max_context_tokens = 100000
                    type(mock_summarization).max_tool_result_size = 1000
                
                    filtered = session._get_messages_for_llm()
        
        # The filtering may leave orphaned tool messages, but Gemini fix should remove them
        # Apply Gemini fix to remove orphaned tool messages (works for all clients)
        filtered = session._fix_gemini_tool_call_ordering(filtered)
        
        # Validate that orphaned tool messages are removed
        is_valid, error = session._validate_message_ordering(filtered)
        assert is_valid is True, f"Filtered messages invalid: {error}"
        
        # Verify no orphaned tool messages remain
        tool_messages = [m for m in filtered if m.get("role") == "tool"]
        if tool_messages:
            # If tool messages exist, they must have preceding assistant with tool_calls
            for i, msg in enumerate(filtered):
                if msg.get("role") == "tool":
                    # Check previous messages for assistant with matching tool_calls
                    found_assistant = False
                    for j in range(i - 1, -1, -1):
                        prev_msg = filtered[j]
                        if prev_msg.get("role") == "assistant":
                            tool_calls = prev_msg.get("tool_calls", [])
                            if tool_calls:
                                tool_call_ids = [tc.get("id") for tc in tool_calls]
                                if msg.get("tool_call_id") in tool_call_ids:
                                    found_assistant = True
                                    break
                    assert found_assistant, "Orphaned tool message found"
    
    def test_filtering_with_summarization_maintains_ordering(self, mock_llm_client: Mock):
        """
        Test that filtering with summarization enabled maintains ordering.
        
        When summarization is enabled and messages are filtered to last K turns,
        tool message ordering should be preserved.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create conversation with multiple turns and tool calls
        session.messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Turn 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Turn 2"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            },
            {"role": "assistant", "content": "Response 2"}
        ]
        
        # Mock summarization to filter to last 2 turns
        with patch.object(session, '_summarization_manager') as mock_mgr:
            mock_mgr.summary_storage.load_session_summary.return_value = {"summary": "test"}
            from broca.config import config
            with patch.object(config, 'summarization') as mock_summarization:
                with patch.object(config, 'llm') as mock_llm:
                    type(mock_summarization).last_turns_count = 2
                    type(mock_llm).max_context_tokens = 100000
                    type(mock_summarization).max_tool_result_size = 1000
                
                    filtered = session._get_messages_for_llm()
        
        # Validate ordering is maintained
        is_valid, error = session._validate_message_ordering(filtered)
        assert is_valid is True, f"Filtered messages invalid: {error}"
    
    def test_token_aware_filtering_maintains_ordering(self, mock_llm_client: Mock):
        """
        Test that token-aware filtering maintains tool message ordering.
        
        When messages are filtered based on token limits, tool message
        ordering should be preserved.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create conversation with tool calls
        session.messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "What's the weather?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72, "humidity": 50}',
                "tool_call_id": "call_123"
            },
            {"role": "assistant", "content": "The weather is 72 degrees."}
        ]
        
        # Get filtered messages (token-aware filtering)
        filtered = session._get_messages_for_llm()
        
        # Validate ordering is maintained
        is_valid, error = session._validate_message_ordering(filtered)
        assert is_valid is True, f"Filtered messages invalid: {error}"
    
    def test_filtering_at_boundary_of_tool_call_sequence(self, mock_llm_client: Mock):
        """
        Test filtering at the boundary of a tool call sequence.
        
        Edge case: filtering boundary falls in the middle of a tool call sequence.
        Should either keep the entire sequence or remove it entirely.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create conversation where filtering boundary is in tool call sequence
        session.messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Old question"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            },
            {"role": "assistant", "content": "Old response"},
            {"role": "user", "content": "New question"},
            {"role": "assistant", "content": "New response"}
        ]
        
        # Mock summarization to filter to last 1 turn (boundary in tool sequence)
        with patch.object(session, '_summarization_manager') as mock_mgr:
            mock_mgr.summary_storage.load_session_summary.return_value = {"summary": "test"}
            from broca.config import config
            with patch.object(config, 'summarization') as mock_summarization:
                with patch.object(config, 'llm') as mock_llm:
                    type(mock_summarization).last_turns_count = 1
                    type(mock_llm).max_context_tokens = 100000
                    type(mock_summarization).max_tool_result_size = 1000
                
                    filtered = session._get_messages_for_llm()
        
        # Apply Gemini fix to remove orphaned tool messages if any
        filtered = session._fix_gemini_tool_call_ordering(filtered)
        
        # Validate ordering - should either have complete tool sequence or none
        is_valid, error = session._validate_message_ordering(filtered)
        assert is_valid is True, f"Filtered messages invalid: {error}"
        
        # If tool messages exist, they must have complete sequence
        tool_messages = [m for m in filtered if m.get("role") == "tool"]
        if tool_messages:
            # Find corresponding assistant with tool_calls
            for i, msg in enumerate(filtered):
                if msg.get("role") == "tool":
                    # Must have assistant with matching tool_calls before it
                    found = False
                    for j in range(i - 1, -1, -1):
                        prev = filtered[j]
                        if prev.get("role") == "assistant" and prev.get("tool_calls"):
                            tool_call_ids = [tc.get("id") for tc in prev.get("tool_calls", [])]
                            if msg.get("tool_call_id") in tool_call_ids:
                                found = True
                                break
                    assert found, "Tool message without matching assistant"
    
    def test_filtering_preserves_tool_call_id_references(self, mock_llm_client: Mock):
        """
        Test that filtering preserves tool_call_id references.
        
        When messages are filtered, tool_call_id references in tool messages
        should still match tool_calls in assistant messages.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        session.messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Get weather"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            }
        ]
        
        filtered = session._get_messages_for_llm()
        
        # Find tool messages and verify their tool_call_id references exist
        tool_messages = [m for m in filtered if m.get("role") == "tool"]
        for tool_msg in tool_messages:
            tool_call_id = tool_msg.get("tool_call_id")
            assert tool_call_id is not None, "Tool message missing tool_call_id"
            
            # Find matching assistant message with tool_calls
            found = False
            for msg in filtered:
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    tool_call_ids = [tc.get("id") for tc in msg.get("tool_calls", [])]
                    if tool_call_id in tool_call_ids:
                        found = True
                        break
            assert found, f"Tool message references non-existent tool_call_id: {tool_call_id}"




