"""
Unit tests for message validation in ConversationSession.

Tests the validation logic that ensures tool messages follow assistant messages
with tool_calls, as required by the OpenAI API.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
from typing import List, Dict, Any

from broca.repl.session import ConversationSession


class TestMessageValidation:
    """Test message ordering validation logic."""
    
    def test_validate_valid_sequence_with_tool_calls(self, mock_llm_client: Mock):
        """
        Test that valid message sequence passes validation.
        
        Valid sequence: assistant with tool_calls → tool messages
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
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
            }
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_tool_without_preceding_tool_calls(self, mock_llm_client: Mock):
        """
        Test that tool message without preceding tool_calls fails validation.
        
        Invalid: tool message appears without assistant with tool_calls before it.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            }
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is False
        assert error is not None
        assert "tool" in error.lower()
        assert "tool_calls" in error.lower()
    
    def test_validate_invalid_tool_after_user_message(self, mock_llm_client: Mock):
        """
        Test that tool message after user message fails validation.
        
        Invalid: tool message appears after user message without assistant with tool_calls.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "What's the weather?"},
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            }
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is False
        assert error is not None
    
    def test_validate_invalid_tool_after_assistant_without_tool_calls(self, mock_llm_client: Mock):
        """
        Test that tool message after assistant without tool_calls fails validation.
        
        Invalid: tool message appears after assistant message that doesn't have tool_calls.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            }
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is False
        assert error is not None
    
    def test_validate_multiple_tool_calls_with_results(self, mock_llm_client: Mock):
        """
        Test validation with multiple tool calls and their results.
        
        Valid: assistant with multiple tool_calls → multiple tool messages.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Get weather and time"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"}
                    },
                    {
                        "id": "call_124",
                        "type": "function",
                        "function": {"name": "get_time", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_weather",
                "content": '{"temperature": 72}',
                "tool_call_id": "call_123"
            },
            {
                "role": "tool",
                "name": "get_time",
                "content": '{"time": "12:00 PM"}',
                "tool_call_id": "call_124"
            }
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True
        assert error is None
    
    def test_validate_tool_message_missing_tool_call_id(self, mock_llm_client: Mock):
        """
        Test validation with tool message missing tool_call_id.
        
        Invalid: tool message without tool_call_id field.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
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
                "content": '{"temperature": 72}'
                # Missing tool_call_id
            }
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        # Should either fail validation or handle gracefully
        # The exact behavior depends on implementation
        assert is_valid is False or error is not None
    
    def test_validate_empty_message_list(self, mock_llm_client: Mock):
        """
        Test validation with empty message list.
        
        Valid: empty list should pass validation.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = []
        
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True
        assert error is None
    
    def test_validate_only_system_message(self, mock_llm_client: Mock):
        """
        Test validation with only system message.
        
        Valid: system message alone should pass validation.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"}
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True
        assert error is None
    
    def test_validate_tool_call_id_mismatch(self, mock_llm_client: Mock):
        """
        Test validation with tool_call_id that doesn't match any tool_calls.
        
        Invalid: tool message references non-existent tool_call_id.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
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
                "tool_call_id": "call_999"  # Doesn't match call_123
            }
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        # Should either fail or handle gracefully
        # The exact behavior depends on implementation
        assert is_valid is False or error is not None
    
    def test_validate_complex_valid_sequence(self, mock_llm_client: Mock):
        """
        Test validation with complex but valid sequence.
        
        Valid: multiple turns with tool calls, then final response.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
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
            {"role": "assistant", "content": "The weather is 72 degrees."},
            {"role": "user", "content": "What time is it?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_124",
                        "type": "function",
                        "function": {"name": "get_time", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "get_time",
                "content": '{"time": "12:00 PM"}',
                "tool_call_id": "call_124"
            },
            {"role": "assistant", "content": "It's 12:00 PM."}
        ]
        
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True
        assert error is None

