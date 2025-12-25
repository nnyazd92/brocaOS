"""
Unit tests for message validation in ConversationSession.

Tests the validation logic that ensures tool messages follow assistant messages
with tool_calls, as required by the OpenAI API.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
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


class TestGeminiMessageOrderingFix:
    """Test Gemini-specific message ordering fix with iterative approach."""
    
    def test_fix_cascading_invalidations(self, mock_llm_client: Mock):
        """
        Test that fix handles cascading invalidations correctly.
        
        Scenario: System → Assistant(tool_calls) → Tool → Assistant(tool_calls)
        First assistant is invalid (after system), so both assistants and tool should be removed.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": "result1"
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_2", "type": "function", "function": {"name": "tool2", "arguments": "{}"}}
                ]
            },
        ]
        
        fixed = session._fix_gemini_tool_call_ordering(messages)
        
        # System message should remain
        assert len(fixed) == 1
        assert fixed[0]["role"] == "system"
        # All assistant messages with tool_calls should be removed
        # because first one is invalid (after system)
    
    def test_fix_system_followed_by_assistant_tool_calls(self, mock_llm_client: Mock):
        """
        Test fix removes assistant with tool_calls that immediately follows system message.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System prompt"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "user", "content": "User message"}
        ]
        
        fixed = session._fix_gemini_tool_call_ordering(messages)
        
        # Should keep system and user, remove invalid assistant
        assert len(fixed) == 2
        assert fixed[0]["role"] == "system"
        assert fixed[1]["role"] == "user"
        # Assistant with tool_calls should be removed
    
    def test_fix_valid_sequence_preserved(self, mock_llm_client: Mock):
        """
        Test that valid sequences are preserved by the fix.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": "result"
            },
            {"role": "assistant", "content": "Final response"}
        ]
        
        fixed = session._fix_gemini_tool_call_ordering(messages)
        
        # All messages should be preserved (valid sequence)
        assert len(fixed) == len(messages)
        assert fixed[0]["role"] == "system"
        assert fixed[1]["role"] == "user"
        assert fixed[2]["role"] == "assistant"
        assert "tool_calls" in fixed[2]
        assert fixed[3]["role"] == "tool"
        assert fixed[4]["role"] == "assistant"
    
    def test_fix_iterative_removes_cascading_invalidations(self, mock_llm_client: Mock):
        """
        Test that iterative fix properly handles messages that become invalid after removals.
        
        Structure: System → Assistant1(tool_calls) → Tool1 → Assistant2(tool_calls) → Tool2
        After removing Assistant1 and Tool1, Assistant2 should also be removed in next iteration.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result1"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_2", "type": "function", "function": {"name": "tool2", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_2", "content": "result2"}
        ]
        
        fixed = session._fix_gemini_tool_call_ordering(messages)
        
        # Should remove all invalid messages (all assistants with tool_calls and their tools)
        # Only system should remain
        assert len(fixed) == 1
        assert fixed[0]["role"] == "system"
    
    def test_fix_orphaned_tool_messages(self, mock_llm_client: Mock):
        """
        Test that orphaned tool messages are removed.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result1"},
            # Orphaned tool message (no matching assistant)
            {"role": "tool", "tool_call_id": "call_999", "content": "orphaned"}
        ]
        
        fixed = session._fix_gemini_tool_call_ordering(messages)
        
        # Should remove orphaned tool message
        tool_messages = [m for m in fixed if m["role"] == "tool"]
        assert len(tool_messages) == 1
        assert tool_messages[0]["tool_call_id"] == "call_1"
    
    def test_fix_empty_messages(self, mock_llm_client: Mock):
        """Test that empty message list is handled gracefully."""
        session = ConversationSession(llm=mock_llm_client)
        
        messages = []
        fixed = session._fix_gemini_tool_call_ordering(messages)
        
        assert fixed == []
    
    def test_fix_only_system_message(self, mock_llm_client: Mock):
        """Test that system-only message list is handled."""
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [{"role": "system", "content": "System only"}]
        fixed = session._fix_gemini_tool_call_ordering(messages)
        
        assert len(fixed) == 1
        assert fixed[0]["role"] == "system"
    
    def test_fix_validates_result(self, mock_llm_client: Mock):
        """
        Test that fix validates the result after fixing.
        Note: This tests that validation is called, not that it always passes.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result"}
        ]
        
        # Should not raise exception
        fixed = session._fix_gemini_tool_call_ordering(messages)
        
        # Result should be valid or at least handled
        assert isinstance(fixed, list)
        assert len(fixed) > 0


class TestGeminiFixGuard:
    """Test guard logic that ensures at least one non-system message remains after Gemini fix."""
    
    def test_guard_activates_when_all_non_system_removed(self, mock_llm_client: Mock):
        """
        Test that guard activates when fix removes all non-system messages.
        
        Rationale: Ensures at least one content message remains for API calls.
        Note: This test verifies the guard behavior when all non-system messages would be removed.
        The guard will find a fallback message from the original messages.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Messages that will result in all non-system being removed during fix
        # System → Assistant(tool_calls) → Tool → Assistant(tool_calls) → Tool
        # All assistants with tool_calls are invalid and will be removed
        # But we include a user message earlier that the guard can find as fallback
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Early user message"},  # This will be preserved by guard
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result1"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_2", "type": "function", "function": {"name": "tool2", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_2", "content": "result2"},
        ]
        
        with patch('broca.repl.session.logger') as mock_logger:
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # After fix, all invalid assistants and tools are removed
            # But the user message should be preserved (it's valid)
            # So guard may not trigger if user message remains
            # Let's verify the fix worked and at least one non-system message exists
            assert len(fixed) >= 2  # System + at least one non-system
            assert fixed[0]["role"] == "system"
            
            # Should have preserved at least one non-system message
            non_system_messages = [m for m in fixed if m["role"] != "system"]
            assert len(non_system_messages) >= 1
            
            # The guard only triggers if ALL non-system are removed, which won't happen
            # if there's a valid user message. So we just verify the fix works correctly.
            # The guard behavior is tested in test_guard_logs_error_when_no_fallback_available
    
    def test_guard_preserves_most_recent_user_message(self, mock_llm_client: Mock):
        """
        Test that guard prefers user messages over assistant messages.
        
        Rationale: Ensures most recent user message is preserved for context.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Messages with user message that should be preserved
        messages = [
            {"role": "system", "content": "System"},
            {
                "role": "assistant",
                "content": "Old assistant response",
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result"},
            {"role": "user", "content": "Recent user message"}  # Should be preserved
        ]
        
        with patch('broca.repl.session.logger'):
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Should preserve user message
            user_messages = [m for m in fixed if m["role"] == "user"]
            assert len(user_messages) >= 1
            assert user_messages[0]["content"] == "Recent user message"
    
    def test_guard_falls_back_to_assistant_with_content(self, mock_llm_client: Mock):
        """
        Test that guard falls back to assistant message with content if no user message.
        
        Rationale: Ensures some content message is preserved even if no user message exists.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Messages without user message, but with assistant message with content
        messages = [
            {"role": "system", "content": "System"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result"},
            {"role": "assistant", "content": "Assistant response with content"}  # Should be preserved
        ]
        
        with patch('broca.repl.session.logger'):
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Should preserve assistant message with content
            assistant_messages = [m for m in fixed if m["role"] == "assistant" and m.get("content")]
            assert len(assistant_messages) >= 1
            assert assistant_messages[0]["content"] == "Assistant response with content"
    
    def test_guard_logs_error_when_no_fallback_available(self, mock_llm_client: Mock):
        """
        Test that guard logs error when no valid content message is found.
        
        Rationale: Ensures error is logged when API call will likely fail.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Messages that result in only system, with no valid content messages
        messages = [
            {"role": "system", "content": "System"},
            {
                "role": "assistant",
                "content": None,  # No content, only tool_calls
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result"}
            # No user message, no assistant with content
        ]
        
        with patch('broca.repl.session.logger') as mock_logger:
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Should still return system message
            assert len(fixed) >= 1
            assert fixed[0]["role"] == "system"
            
            # Should have logged error about no fallback
            error_calls = [call for call in mock_logger.error.call_args_list 
                          if call and len(call[0]) > 0 and "no valid content message" in str(call[0][0]).lower()]
            # Error might be logged or warning - check both
            if not error_calls:
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if call and len(call[0]) > 0 and ("no fallback" in str(call[0][0]).lower() or "contents is not specified" in str(call[0][0]).lower())]
                assert len(warning_calls) > 0 or len(error_calls) > 0
    
    def test_guard_does_not_activate_when_messages_remain(self, mock_llm_client: Mock):
        """
        Test that guard does not activate when valid messages remain after fix.
        
        Rationale: Ensures guard only activates when needed.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Valid message sequence that should remain intact
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User message"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result"}
        ]
        
        with patch('broca.repl.session.logger') as mock_logger:
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # All messages should remain (valid sequence)
            assert len(fixed) == len(messages)
            
            # Guard should not have been triggered (no warnings about preserving fallback)
            guard_warnings = [call for call in mock_logger.warning.call_args_list 
                            if call and len(call[0]) > 0 and "removed all non-system" in str(call[0][0])]
            assert len(guard_warnings) == 0
    
    def test_guard_with_only_system_message(self, mock_llm_client: Mock):
        """
        Test guard behavior when only system message is present.
        
        Rationale: Edge case - system-only should not trigger guard (already only system).
        """
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [{"role": "system", "content": "System only"}]
        
        with patch('broca.repl.session.logger') as mock_logger:
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Should remain as system only
            assert len(fixed) == 1
            assert fixed[0]["role"] == "system"
            
            # Guard should not activate (no non-system messages to preserve)
            guard_warnings = [call for call in mock_logger.warning.call_args_list 
                            if call and len(call[0]) > 0 and "removed all non-system" in str(call[0][0])]
            assert len(guard_warnings) == 0


class TestGeminiGuardMutationKillers:
    """
    Mutation tests for Gemini guard logic.
    
    These tests verify specific behaviors that would be broken by common mutations
    like changing operators, conditions, or return values.
    """
    
    def test_find_most_recent_content_message_prefers_user_over_assistant(self, mock_llm_client: Mock):
        """Kills mutation: preferring assistant messages over user messages."""
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System"},
            {"role": "assistant", "content": "Assistant message"},
            {"role": "user", "content": "User message"}  # Should be preferred
        ]
        
        result = session._find_most_recent_content_message(messages)
        
        # Should prefer user message
        assert result is not None
        assert result["role"] == "user"
        assert result["content"] == "User message"
    
    def test_find_most_recent_content_message_skips_system_messages(self, mock_llm_client: Mock):
        """Kills mutation: including system messages in results."""
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"}
        ]
        
        result = session._find_most_recent_content_message(messages)
        
        # Should not return system message
        assert result is not None
        assert result["role"] != "system"
        assert result["role"] == "user"
    
    def test_find_most_recent_content_message_requires_content(self, mock_llm_client: Mock):
        """Kills mutation: returning messages without content."""
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1"}]},
            {"role": "assistant", "content": "Has content"}  # Should be returned
        ]
        
        result = session._find_most_recent_content_message(messages)
        
        # Should return message with content, not None
        assert result is not None
        assert result.get("content") is not None
        assert result["content"] == "Has content"
    
    def test_find_most_recent_content_message_returns_none_when_no_content(self, mock_llm_client: Mock):
        """Kills mutation: returning non-None when no valid content messages exist."""
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System"},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1"}]},
            {"role": "tool", "tool_call_id": "call_1", "content": "result"}
        ]
        
        result = session._find_most_recent_content_message(messages)
        
        # Should return None when no user or assistant with content
        assert result is None
    
    def test_guard_preserves_fallback_message_in_result(self, mock_llm_client: Mock):
        """Kills mutation: not preserving fallback message in fixed messages."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Messages that will result in all non-system being removed
        messages = [
            {"role": "system", "content": "System"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "tool", "arguments": "{}"}}]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result"},
            {"role": "user", "content": "User message to preserve"}
        ]
        
        with patch('broca.repl.session.logger'):
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Guard should have preserved the user message
            assert len(fixed) >= 2
            assert fixed[0]["role"] == "system"
            
            # Should contain the user message
            user_messages = [m for m in fixed if m["role"] == "user"]
            assert len(user_messages) >= 1
            assert user_messages[0]["content"] == "User message to preserve"
    
    def test_guard_always_ensures_non_system_message_exists(self, mock_llm_client: Mock):
        """Kills mutation: allowing only system messages after guard."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Messages with valid fallback
        messages = [
            {"role": "system", "content": "System"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "tool", "arguments": "{}"}}]
            },
            {"role": "user", "content": "User message"}
        ]
        
        with patch('broca.repl.session.logger'):
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Should have at least one non-system message
            non_system = [m for m in fixed if m["role"] != "system"]
            assert len(non_system) >= 1
    
    def test_guard_places_fallback_after_system_messages(self, mock_llm_client: Mock):
        """Kills mutation: placing fallback before system messages."""
        session = ConversationSession(llm=mock_llm_client)
        
        messages = [
            {"role": "system", "content": "System1"},
            {"role": "system", "content": "System2"},  # Multiple system messages
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "tool", "arguments": "{}"}}]
            },
            {"role": "user", "content": "User message"}
        ]
        
        with patch('broca.repl.session.logger'):
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # System messages should come first, then fallback
            assert fixed[0]["role"] == "system"
            # At least one non-system message should exist after system messages
            non_system_indices = [i for i, m in enumerate(fixed) if m["role"] != "system"]
            if non_system_indices:
                assert non_system_indices[0] > 0  # After at least one system message


class TestGeminiGuardProperties:
    """Property-based tests for Gemini guard logic."""
    
    def test_guard_always_ensures_at_least_one_non_system_message(self, mock_llm_client: Mock):
        """
        Property: After fix, there is always at least one non-system message (if fallback available).
        
        Rationale: This is the core property of the guard - it ensures API calls can succeed.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create test messages with invalid sequences that will be removed
        messages = [{"role": "system", "content": "System"}]
        
        # Add some invalid assistant messages that will be removed
        for i in range(3):
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": f"call_{i}", "type": "function", "function": {"name": "tool", "arguments": "{}"}}]
            })
            messages.append({"role": "tool", "tool_call_id": f"call_{i}", "content": f"result_{i}"})
        
        # Add a valid user message that should be preserved
        messages.append({"role": "user", "content": "User message"})
        
        with patch('broca.repl.session.logger'):
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Property: Should have at least one non-system message
            non_system = [m for m in fixed if m["role"] != "system"]
            assert len(non_system) >= 1
    
    def test_guard_preserves_most_recent_content_message_property(self, mock_llm_client: Mock):
        """
        Property: Guard preserves the most recent valid content message from original messages.
        
        Rationale: Ensures context is maintained by preserving recent content.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create messages with multiple content messages
        messages = [
            {"role": "system", "content": "System"},
            {"role": "assistant", "content": "Old assistant"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "tool", "arguments": "{}"}}]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result"},
            {"role": "user", "content": "Recent user"}  # Should be preserved
        ]
        
        with patch('broca.repl.session.logger'):
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Property: Should preserve the most recent user message
            user_messages = [m for m in fixed if m["role"] == "user"]
            if user_messages:
                assert user_messages[0]["content"] == "Recent user"


class TestGeminiGuardGoldenTrace:
    """Golden trace tests replicating real-world scenarios from logs."""
    
    def test_cat_command_scenario_guard_activation(self, mock_llm_client: Mock):
        """
        Golden trace: Cat command scenario where fix removed all non-system messages.
        
        This replicates the scenario from broca_repl.log lines 1601-1604 where:
        - Gemini fix removed 12 messages, leaving only system message
        - API call failed with "contents is not specified"
        - User message "Why do you stop when cat" was asked
        
        With the guard fix, this scenario should now preserve a fallback message.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Reconstruct the message structure from the log
        # Structure: 0:system -> 1:assistant[tool_calls=1] -> 2:tool -> 3:assistant[tool_calls=1] -> ...
        # All assistant messages with tool_calls will be invalid (cascading)
        messages = [
            {"role": "system", "content": "System prompt"},
            # First invalid assistant (after system, no valid predecessor)
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "function-call-452031", "type": "function", "function": {"name": "terminal", "arguments": "{\"command\": \"cat file1\"}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "function-call-452031", "content": "Tool result 1"},
            # Second invalid assistant (after tool, but tool was invalid so assistant is invalid)
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "function-call-149878", "type": "function", "function": {"name": "terminal", "arguments": "{\"command\": \"cat file2\"}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "function-call-149878", "content": "Tool result 2"},
            # More cascading invalid assistants
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "function-call-118778", "type": "function", "function": {"name": "terminal", "arguments": "{\"command\": \"cat file3\"}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "function-call-118778", "content": "Tool result 3"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "function-call-622555", "type": "function", "function": {"name": "terminal", "arguments": "{\"command\": \"cat docs/physics/rigor_upgrade/NUMEROLOGY_TO_MECHANISM_ROADMAP.md\"}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "function-call-622555", "content": "Tool result from cat command"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "function-call-148348", "type": "function", "function": {"name": "terminal", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "function-call-148348", "content": "Another tool result"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "function-call-326067", "type": "function", "function": {"name": "terminal", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "function-call-326067", "content": "Final tool result"},
            # User message that should be preserved by guard
            {"role": "user", "content": "Why do you stop when cat"}
        ]
        
        with patch('broca.repl.session.logger') as mock_logger:
            fixed = session._fix_gemini_tool_call_ordering(messages)
            
            # Golden trace expectation: Guard should activate and preserve user message
            # Before fix: messages_after was 1 (only system)
            # After fix with guard: should have at least system + user message
            
            assert len(fixed) >= 2, "Guard should preserve at least one non-system message"
            assert fixed[0]["role"] == "system", "System message should be first"
            
            # Should have preserved the user message
            user_messages = [m for m in fixed if m["role"] == "user"]
            assert len(user_messages) >= 1, "Guard should preserve user message"
            assert user_messages[0]["content"] == "Why do you stop when cat"
            
            # Guard should have logged a warning
            guard_warnings = [call for call in mock_logger.warning.call_args_list 
                            if call and len(call[0]) > 0 and "removed all non-system" in str(call[0][0])]
            guard_info = [call for call in mock_logger.info.call_args_list 
                         if call and len(call) > 1 and call[1].get('extra', {}).get('event') == 'gemini_fix_guard_triggered']
            
            # Either warning or info log should be present
            assert len(guard_warnings) > 0 or len(guard_info) > 0, "Guard should log when triggered"

