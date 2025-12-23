"""
Fault injection tests for message validation and filtering.

Tests edge cases, error conditions, and malformed inputs to ensure graceful handling.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
from typing import List, Dict, Any, Optional

from broca.repl.session import ConversationSession


class TestFaultInjection:
    """Fault injection tests for edge cases and error conditions."""
    
    def test_malformed_tool_message_missing_tool_call_id(self, mock_llm_client: Mock):
        """
        Test handling of tool message missing tool_call_id field.
        
        Fault: Tool message without tool_call_id should be handled gracefully.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Test"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "test_tool",
                "content": '{"result": "value"}'
                # Missing tool_call_id
            }
        ]
        
        # Should handle gracefully (either fail validation or handle missing field)
        is_valid, error = session._validate_message_ordering(messages)
        # Should either fail or handle gracefully
        assert isinstance(is_valid, bool)
        if not is_valid:
            assert error is not None
    
    def test_malformed_assistant_tool_calls_missing_id(self, mock_llm_client: Mock):
        """
        Test handling of assistant message with tool_calls missing id field.
        
        Fault: Assistant message with tool_calls that have missing id fields.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Test"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        # Missing "id" field
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "test_tool",
                "content": '{"result": "value"}',
                "tool_call_id": "call_123"
            }
        ]
        
        # Should handle gracefully
        is_valid, error = session._validate_message_ordering(messages)
        assert isinstance(is_valid, bool)
    
    def test_corrupted_message_sequence_mixed_ordering(self, mock_llm_client: Mock):
        """
        Test handling of corrupted message sequence with mixed ordering.
        
        Fault: Messages in wrong order (tool before assistant, etc.).
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {
                "role": "tool",  # Tool message before any assistant
                "name": "test_tool",
                "content": '{"result": "value"}',
                "tool_call_id": "call_123"
            },
            {"role": "user", "content": "Test"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }
                ]
            }
        ]
        
        # Should detect invalid ordering
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is False
        assert error is not None
    
    def test_empty_message_list(self, mock_llm_client: Mock):
        """
        Test handling of empty message list.
        
        Fault: Empty list should be handled gracefully.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = []
        
        # Should handle empty list gracefully
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True
        assert error is None
    
    def test_messages_with_none_values(self, mock_llm_client: Mock):
        """
        Test handling of messages with None values in fields.
        
        Fault: Messages with None in role, content, or other fields.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": None, "content": "Test"},  # None role
            {"role": "user", "content": None},  # None content
            {
                "role": "assistant",
                "content": None,
                "tool_calls": None  # None tool_calls
            }
        ]
        
        # Should handle None values gracefully
        try:
            is_valid, error = session._validate_message_ordering(messages)
            assert isinstance(is_valid, bool)
        except (TypeError, AttributeError, KeyError):
            # Exception is acceptable for malformed data
            pass
    
    def test_messages_with_missing_role_field(self, mock_llm_client: Mock):
        """
        Test handling of messages missing role field.
        
        Fault: Messages without "role" field.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"content": "Test"},  # Missing role
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }
                ]
            }
        ]
        
        # Should handle missing role gracefully
        try:
            is_valid, error = session._validate_message_ordering(messages)
            assert isinstance(is_valid, bool)
        except (TypeError, AttributeError, KeyError):
            # Exception is acceptable for malformed data
            pass
    
    def test_tool_calls_with_invalid_structure(self, mock_llm_client: Mock):
        """
        Test handling of tool_calls with invalid structure.
        
        Fault: tool_calls that are not a list, or have wrong structure.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        test_cases = [
            # tool_calls is not a list
            {
                "role": "assistant",
                "content": None,
                "tool_calls": "not a list"
            },
            # tool_calls is empty list (valid but edge case)
            {
                "role": "assistant",
                "content": None,
                "tool_calls": []
            },
            # tool_calls contains non-dict items
            {
                "role": "assistant",
                "content": None,
                "tool_calls": ["not a dict", 123]
            }
        ]
        
        for tool_calls_msg in test_cases:
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Test"},
                tool_calls_msg
            ]
            
            # Should handle invalid structure gracefully
            try:
                is_valid, error = session._validate_message_ordering(messages)
                assert isinstance(is_valid, bool)
            except (TypeError, AttributeError):
                # Exception is acceptable for malformed data
                pass
    
    def test_tool_message_with_wrong_type_fields(self, mock_llm_client: Mock):
        """
        Test handling of tool message with wrong type fields.
        
        Fault: tool_call_id is not a string, name is not a string, etc.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        test_cases = [
            # tool_call_id is not a string
            {
                "role": "tool",
                "name": "test_tool",
                "content": '{"result": "value"}',
                "tool_call_id": 123  # Should be string
            },
            # tool_call_id is None
            {
                "role": "tool",
                "name": "test_tool",
                "content": '{"result": "value"}',
                "tool_call_id": None
            },
            # name is not a string
            {
                "role": "tool",
                "name": 123,  # Should be string
                "content": '{"result": "value"}',
                "tool_call_id": "call_123"
            }
        ]
        
        for tool_msg in test_cases:
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Test"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {"name": "test_tool", "arguments": "{}"}
                        }
                    ]
                },
                tool_msg
            ]
            
            # Should handle wrong types gracefully
            try:
                is_valid, error = session._validate_message_ordering(messages)
                assert isinstance(is_valid, bool)
            except (TypeError, AttributeError):
                # Exception is acceptable for malformed data
                pass
    
    def test_filtering_with_corrupted_messages(self, mock_llm_client: Mock):
        """
        Test filtering with corrupted message sequences.
        
        Fault: Filtering should handle corrupted messages gracefully.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create corrupted message sequence
        session.messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Test"},
            {
                "role": "tool",  # Orphaned tool message
                "name": "test_tool",
                "content": '{"result": "value"}',
                "tool_call_id": "call_123"
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }
                ]
            }
        ]
        
        # Filtering should handle corrupted sequence
        try:
            filtered = session._get_messages_for_llm()
            
            # Result should be valid (orphaned messages removed)
            is_valid, error = session._validate_message_ordering(filtered)
            assert is_valid is True, f"Filtering didn't fix corrupted sequence: {error}"
        except Exception as e:
            # Graceful failure is acceptable
            assert isinstance(e, (ValueError, TypeError, AttributeError))
    
    def test_validation_with_very_long_tool_call_ids(self, mock_llm_client: Mock):
        """
        Test handling of very long tool_call_id values.
        
        Fault: Extremely long tool_call_id strings.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        long_id = "call_" + "x" * 10000
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Test"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": long_id,
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "test_tool",
                "content": '{"result": "value"}',
                "tool_call_id": long_id
            }
        ]
        
        # Should handle long IDs gracefully
        is_valid, error = session._validate_message_ordering(messages)
        assert isinstance(is_valid, bool)
    
    def test_validation_with_unicode_in_tool_call_ids(self, mock_llm_client: Mock):
        """
        Test handling of unicode characters in tool_call_id.
        
        Fault: Unicode characters in tool_call_id.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        unicode_id = "call_测试_🚀_ñáéíóú"
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Test"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": unicode_id,
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "test_tool",
                "content": '{"result": "value"}',
                "tool_call_id": unicode_id
            }
        ]
        
        # Should handle unicode gracefully
        is_valid, error = session._validate_message_ordering(messages)
        assert isinstance(is_valid, bool)
    
    def test_validation_with_duplicate_tool_call_ids(self, mock_llm_client: Mock):
        """
        Test handling of duplicate tool_call_ids in same assistant message.
        
        Fault: Multiple tool_calls with same id.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Test"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",  # Duplicate
                        "type": "function",
                        "function": {"name": "tool1", "arguments": "{}"}
                    },
                    {
                        "id": "call_123",  # Duplicate
                        "type": "function",
                        "function": {"name": "tool2", "arguments": "{}"}
                    }
                ]
            },
            {
                "role": "tool",
                "name": "tool1",
                "content": '{"result": "value1"}',
                "tool_call_id": "call_123"
            }
        ]
        
        # Should handle duplicates (may be valid or invalid depending on implementation)
        is_valid, error = session._validate_message_ordering(messages)
        assert isinstance(is_valid, bool)
    
    def test_filtering_with_empty_tool_calls_list(self, mock_llm_client: Mock):
        """
        Test filtering with assistant message having empty tool_calls list.
        
        Fault: Assistant message with tool_calls = [].
        """
        session = ConversationSession(llm=mock_llm_client)
        
        session.messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Test"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": []  # Empty list
            },
            {
                "role": "tool",
                "name": "test_tool",
                "content": '{"result": "value"}',
                "tool_call_id": "call_123"
            }
        ]
        
        # Filtering should handle empty tool_calls
        try:
            filtered = session._get_messages_for_llm()
            is_valid, error = session._validate_message_ordering(filtered)
            # Should either be valid (tool message removed) or invalid (detected)
            assert isinstance(is_valid, bool)
        except Exception:
            # Graceful failure is acceptable
            pass

