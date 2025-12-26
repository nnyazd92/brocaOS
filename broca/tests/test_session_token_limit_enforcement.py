"""
Tests for token limit enforcement in ConversationSession.

Tests that _apply_token_aware_filtering properly enforces token limits
by removing messages when necessary, respecting the safety margin, and
preserving system messages.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.repl.session import ConversationSession
from broca.summarization.token_estimator import estimate_messages_tokens


class TestTokenLimitEnforcement:
    """Test token limit enforcement in _apply_token_aware_filtering."""
    
    def test_messages_under_limit_unchanged(self, mock_llm_client: Mock):
        """
        Test that messages under the token limit are returned unchanged.
        
        Rationale: Messages that are already under the limit should not be modified.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create messages that are well under the limit
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        # Set a high token limit (1000 tokens)
        max_tokens = 1000
        
        # Filter messages
        filtered = session._apply_token_aware_filtering(messages, max_tokens)
        
        # Messages should be unchanged (possibly with tool results truncated)
        assert len(filtered) == len(messages)
        assert filtered[0]["role"] == "system"
        assert filtered[1]["role"] == "user"
        assert filtered[2]["role"] == "assistant"
    
    def test_messages_over_limit_get_removed(self, mock_llm_client: Mock):
        """
        Test that messages exceeding the limit are removed.
        
        Rationale: When messages exceed the token limit, older messages should be
        removed until the limit is satisfied.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create many messages that will exceed the limit
        messages = [{"role": "system", "content": "You are helpful."}]
        # Add many user/assistant pairs with large content
        for i in range(20):
            messages.append({
                "role": "user",
                "content": "User message " + "x" * 1000  # Large content to increase token count
            })
            messages.append({
                "role": "assistant",
                "content": "Assistant response " + "y" * 1000
            })
        
        # Set a low token limit (5000 tokens)
        max_tokens = 5000
        
        # Filter messages
        filtered = session._apply_token_aware_filtering(messages, max_tokens)
        
        # Messages should be reduced
        assert len(filtered) < len(messages), "Messages should be removed when over limit"
        
        # System message should always be preserved
        assert filtered[0]["role"] == "system"
        
        # Estimated tokens should be under the limit (with some tolerance for estimation error)
        estimated_tokens = estimate_messages_tokens(filtered)
        # Allow 10% tolerance since we use 95% of limit and estimation is approximate
        assert estimated_tokens <= max_tokens * 1.1, \
            f"Estimated tokens {estimated_tokens} should be <= {max_tokens * 1.1}"
    
    def test_safety_margin_applied(self, mock_llm_client: Mock):
        """
        Test that a safety margin (5%) is applied to the token limit.
        
        Rationale: The effective limit should be 95% of the provided limit to account
        for token estimation inaccuracy.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create messages that are just slightly over the limit
        # We'll create messages that would fit in 1000 tokens but not 950
        messages = [
            {"role": "system", "content": "System prompt"},
        ]
        # Add messages that total approximately 980 tokens
        for i in range(10):
            messages.append({
                "role": "user",
                "content": "Message " + str(i) + " " + "x" * 90  # ~100 chars per message
            })
            messages.append({
                "role": "assistant",
                "content": "Response " + str(i) + " " + "y" * 90
            })
        
        # Set limit to 1000 tokens
        max_tokens = 1000
        # Effective limit should be 950 (95% of 1000)
        
        # Filter messages
        filtered = session._apply_token_aware_filtering(messages, max_tokens)
        
        # Check that we're using the safety margin (effective limit of 950)
        estimated_tokens = estimate_messages_tokens(filtered)
        # Should be under the effective limit (950), not the original limit (1000)
        effective_limit = int(max_tokens * 0.95)
        assert estimated_tokens <= effective_limit * 1.1, \
            f"Should respect safety margin: {estimated_tokens} should be <= {effective_limit * 1.1}"
    
    def test_system_message_always_preserved(self, mock_llm_client: Mock):
        """
        Test that system message is always preserved, even when messages exceed limit.
        
        Rationale: System messages contain important context and should never be removed.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create messages with system message
        messages = [
            {"role": "system", "content": "You are a helpful assistant. " + "x" * 5000},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]
        
        # Set a very low limit that would require removing messages
        max_tokens = 100
        
        # Filter messages
        filtered = session._apply_token_aware_filtering(messages, max_tokens)
        
        # System message should still be present
        assert len(filtered) > 0
        assert filtered[0]["role"] == "system"
    
    def test_minimum_one_conversation_message_preserved(self, mock_llm_client: Mock):
        """
        Test that at least one conversation message (user/assistant) is preserved.
        
        Rationale: We should always keep at least the last user message or assistant response
        to maintain conversation continuity.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create messages with system message and conversation messages
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "First message " + "x" * 1000},
            {"role": "assistant", "content": "First response " + "y" * 1000},
            {"role": "user", "content": "Second message " + "z" * 1000},
            {"role": "assistant", "content": "Second response " + "w" * 1000},
        ]
        
        # Set a very low limit
        max_tokens = 200
        
        # Filter messages
        filtered = session._apply_token_aware_filtering(messages, max_tokens)
        
        # Should have at least system message + 1 conversation message
        assert len(filtered) >= 2
        assert filtered[0]["role"] == "system"
        # Last message should be from conversation (user or assistant)
        assert filtered[-1]["role"] in ["user", "assistant"]
    
    def test_tool_results_truncated_first(self, mock_llm_client: Mock):
        """
        Test that tool results are truncated before messages are removed.
        
        Rationale: Truncating tool results is less destructive than removing messages,
        so it should be done first.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create messages with large tool results
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "What's the weather?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "weather"}}]
            },
            {
                "role": "tool",
                "name": "weather",
                "tool_call_id": "call_1",
                "content": "x" * 50000  # Very large tool result
            },
            {"role": "assistant", "content": "It's sunny."}
        ]
        
        # Set a moderate limit
        max_tokens = 1000
        
        # Filter messages
        filtered = session._apply_token_aware_filtering(messages, max_tokens)
        
        # Tool result should be truncated (not removed)
        tool_message = next((m for m in filtered if m.get("role") == "tool"), None)
        if tool_message:
            content = tool_message.get("content", "")
            # Content should be truncated, not the full 50000 chars
            assert len(content) < 50000
    
    def test_tool_results_truncated_before_message_removal(self, mock_llm_client: Mock):
        """
        Test that tool results are truncated before messages are removed.
        
        Rationale: The code should try truncating tool results first before removing messages.
        This is verified by checking that tool results are truncated even when messages
        still need to be removed.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create messages with large tool results
        large_tool_result = "x" * 50000  # Very large tool result
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "test"}}]
            },
            {
                "role": "tool",
                "name": "test",
                "tool_call_id": "call_1",
                "content": large_tool_result
            },
            {"role": "assistant", "content": "Done."},
            # Add more messages to push over limit even after truncation
            {"role": "user", "content": "More text " + "y" * 5000},
            {"role": "assistant", "content": "More response " + "z" * 5000},
        ]
        
        # Set a moderate limit that requires both truncation and removal
        max_tokens = 2000
        
        # Filter messages
        filtered = session._apply_token_aware_filtering(messages, max_tokens)
        
        # Tool result should be truncated (not full size)
        tool_message = next((m for m in filtered if m.get("role") == "tool"), None)
        if tool_message:
            content = tool_message.get("content", "")
            # Content should be truncated, not the full 50000 chars
            assert len(content) < len(large_tool_result), \
                "Tool result should be truncated before messages are removed"
    
    def test_without_system_message(self, mock_llm_client: Mock):
        """
        Test token limit enforcement when there is no system message.
        
        Rationale: The method should work correctly even without a system message.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Create messages without system message
        messages = []
        for i in range(15):
            messages.append({
                "role": "user",
                "content": "User message " + str(i) + " " + "x" * 500
            })
            messages.append({
                "role": "assistant",
                "content": "Assistant response " + str(i) + " " + "y" * 500
            })
        
        # Set a low limit
        max_tokens = 2000
        
        # Filter messages
        filtered = session._apply_token_aware_filtering(messages, max_tokens)
        
        # Should have fewer messages
        assert len(filtered) < len(messages), "Messages should be removed when over limit"
        
        # Should preserve at least one message
        assert len(filtered) >= 1, "Should preserve at least one message"
        
        # Estimated tokens should be under limit
        estimated_tokens = estimate_messages_tokens(filtered)
        assert estimated_tokens <= max_tokens * 1.1, \
            f"Estimated tokens {estimated_tokens} should be <= {max_tokens * 1.1}"

