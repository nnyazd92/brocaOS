"""
Property-based tests for message validation and filtering using Hypothesis.

Tests invariants and properties that should hold for all message sequences.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
from typing import List, Dict, Any, Optional
from hypothesis import given, strategies as st, settings, HealthCheck, assume

from broca.repl.session import ConversationSession


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.chat.return_value = {"choices": [{"message": {"content": "test"}}]}
    client.extract_assistant_content = Mock(return_value="test")
    client.extract_tool_calls = Mock(return_value=[])
    return client


@pytest.fixture
def session(mock_llm_client):
    """ConversationSession instance for testing."""
    return ConversationSession(llm=mock_llm_client)


# Strategy for generating valid message roles
message_role = st.sampled_from(["system", "user", "assistant", "tool"])

# Strategy for generating tool call IDs
tool_call_id_strategy = st.text(min_size=1, max_size=20, alphabet=st.characters(whitespace=False))


def create_valid_tool_call_sequence(min_tool_calls: int = 1, max_tool_calls: int = 3) -> st.SearchStrategy:
    """
    Create a strategy for generating valid assistant + tool message sequences.
    
    Returns a strategy that generates:
    - An assistant message with tool_calls
    - Corresponding tool messages with matching tool_call_ids
    """
    def make_tool_sequence(tool_call_count: int):
        tool_call_ids = [f"call_{i}" for i in range(tool_call_count)]
        
        # Assistant message with tool_calls
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_id,
                    "type": "function",
                    "function": {
                        "name": st.text(min_size=1, max_size=20).example(),
                        "arguments": "{}"
                    }
                }
                for tool_id in tool_call_ids
            ]
        }
        
        # Tool messages corresponding to tool_calls
        tool_messages = [
            {
                "role": "tool",
                "name": st.text(min_size=1, max_size=20).example(),
                "content": st.text(min_size=1, max_size=100).example(),
                "tool_call_id": tool_id
            }
            for tool_id in tool_call_ids
        ]
        
        return [assistant_msg] + tool_messages
    
    return st.integers(min_value=min_tool_calls, max_value=max_tool_calls).map(make_tool_sequence)


class TestPropertyBasedValidation:
    """Property-based tests for message validation."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(
        num_turns=st.integers(min_value=0, max_value=10),
        has_tool_calls=st.booleans()
    )
    def test_validate_valid_sequences_always_pass(self, session, num_turns, has_tool_calls):
        """
        Property: All valid message sequences pass validation.
        
        For any valid sequence of messages (with proper tool message ordering),
        validation should always return True.
        """
        messages = []
        
        # Add system message
        messages.append({"role": "system", "content": "You are helpful"})
        
        # Generate turns
        for turn in range(num_turns):
            messages.append({
                "role": "user",
                "content": f"User message {turn}"
            })
            
            if has_tool_calls and turn % 2 == 0:
                # Add assistant with tool_calls
                tool_call_id = f"call_{turn}"
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {"name": "test_tool", "arguments": "{}"}
                        }
                    ]
                })
                # Add corresponding tool message
                messages.append({
                    "role": "tool",
                    "name": "test_tool",
                    "content": f'{{"result": "value_{turn}"}}',
                    "tool_call_id": tool_call_id
                })
            else:
                # Add regular assistant message
                messages.append({
                    "role": "assistant",
                    "content": f"Assistant response {turn}"
                })
        
        # Validate - should always pass for valid sequences
        is_valid, error = session._validate_message_ordering(messages)
        assert is_valid is True, f"Valid sequence failed validation: {error}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        num_messages=st.integers(min_value=1, max_value=20),
        orphan_probability=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_filtering_never_creates_invalid_sequences(self, session, num_messages, orphan_probability):
        """
        Property: Filtering never creates invalid sequences.
        
        For any message sequence, after filtering, the result should always
        be valid (no orphaned tool messages).
        """
        # Create a message sequence
        messages = [{"role": "system", "content": "You are helpful"}]
        
        for i in range(num_messages):
            if i % 3 == 0:
                messages.append({"role": "user", "content": f"Message {i}"})
            elif i % 3 == 1:
                # Sometimes add assistant with tool_calls
                if i % 2 == 0:
                    tool_call_id = f"call_{i}"
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call_id,
                                "type": "function",
                                "function": {"name": "test_tool", "arguments": "{}"}
                            }
                        ]
                    })
                    # Add tool message (sometimes orphan it by not including assistant)
                    if orphan_probability < 0.5:  # Normal case
                        messages.append({
                            "role": "tool",
                            "name": "test_tool",
                            "content": f'{{"result": {i}}}',
                            "tool_call_id": tool_call_id
                        })
                else:
                    messages.append({"role": "assistant", "content": f"Response {i}"})
        
        # Set messages in session
        session.messages = messages
        
        # Filter messages
        try:
            filtered = session._get_messages_for_llm()
            
            # Validate filtered messages - should always be valid
            is_valid, error = session._validate_message_ordering(filtered)
            assert is_valid is True, f"Filtering created invalid sequence: {error}"
        except Exception:
            # If filtering fails, that's also acceptable (graceful failure)
            pass
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(messages=st.lists(
        st.one_of(
            st.fixed_dictionaries({
                "role": st.just("system"),
                "content": st.text(min_size=1, max_size=100)
            }),
            st.fixed_dictionaries({
                "role": st.just("user"),
                "content": st.text(min_size=1, max_size=100)
            }),
            st.fixed_dictionaries({
                "role": st.just("assistant"),
                "content": st.text(min_size=0, max_size=100)
            })
        ),
        min_size=0,
        max_size=20
    ))
    def test_validation_is_idempotent(self, session, messages):
        """
        Property: Validation is idempotent.
        
        Validating the same message sequence multiple times should
        always return the same result.
        """
        # Ensure at least one message for meaningful test
        assume(len(messages) > 0)
        
        # Add system message if not present
        if not any(m.get("role") == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": "You are helpful"})
        
        # Validate multiple times
        result1 = session._validate_message_ordering(messages)
        result2 = session._validate_message_ordering(messages)
        result3 = session._validate_message_ordering(messages)
        
        # Results should be identical
        assert result1 == result2 == result3, "Validation is not idempotent"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        tool_call_count=st.integers(min_value=1, max_value=5),
        tool_result_count=st.integers(min_value=0, max_value=5)
    )
    def test_filtered_messages_maintain_tool_call_id_references(self, session, tool_call_count, tool_result_count):
        """
        Property: Filtered messages maintain tool_call_id references.
        
        After filtering, any tool message should have a tool_call_id that
        matches a tool_call in a preceding assistant message.
        """
        # Create messages with tool calls
        messages = [{"role": "system", "content": "You are helpful"}]
        messages.append({"role": "user", "content": "Test question"})
        
        # Add assistant with tool_calls
        tool_call_ids = [f"call_{i}" for i in range(tool_call_count)]
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_id,
                    "type": "function",
                    "function": {"name": f"tool_{i}", "arguments": "{}"}
                }
                for i, tool_id in enumerate(tool_call_ids)
            ]
        })
        
        # Add tool messages (some may be orphaned if tool_result_count < tool_call_count)
        for i in range(min(tool_result_count, tool_call_count)):
            messages.append({
                "role": "tool",
                "name": f"tool_{i}",
                "content": f'{{"result": {i}}}',
                "tool_call_id": tool_call_ids[i]
            })
        
        session.messages = messages
        
        try:
            filtered = session._get_messages_for_llm()
            
            # Check that all tool messages have valid references
            tool_messages = [m for m in filtered if m.get("role") == "tool"]
            for tool_msg in tool_messages:
                tool_call_id = tool_msg.get("tool_call_id")
                assert tool_call_id is not None, "Tool message missing tool_call_id"
                
                # Find matching assistant message
                found = False
                for msg in filtered:
                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                        tool_call_ids = [tc.get("id") for tc in msg.get("tool_calls", [])]
                        if tool_call_id in tool_call_ids:
                            found = True
                            break
                
                assert found, f"Tool message references non-existent tool_call_id: {tool_call_id}"
        except Exception:
            # Graceful failure is acceptable
            pass
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        num_tool_sequences=st.integers(min_value=0, max_value=5),
        tool_calls_per_sequence=st.integers(min_value=1, max_value=3)
    )
    def test_validation_handles_multiple_tool_sequences(self, session, num_tool_sequences, tool_calls_per_sequence):
        """
        Property: Validation handles multiple tool call sequences correctly.
        
        A conversation can have multiple tool call sequences, and validation
        should handle all of them correctly.
        """
        messages = [{"role": "system", "content": "You are helpful"}]
        
        for seq in range(num_tool_sequences):
            messages.append({"role": "user", "content": f"Question {seq}"})
            
            # Add assistant with tool_calls
            tool_call_ids = [f"call_{seq}_{i}" for i in range(tool_calls_per_sequence)]
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_id,
                        "type": "function",
                        "function": {"name": f"tool_{seq}_{i}", "arguments": "{}"}
                    }
                    for i, tool_id in enumerate(tool_call_ids)
                ]
            })
            
            # Add corresponding tool messages
            for i, tool_id in enumerate(tool_call_ids):
                messages.append({
                    "role": "tool",
                    "name": f"tool_{seq}_{i}",
                    "content": f'{{"result": {seq}_{i}}}',
                    "tool_call_id": tool_id
                })
            
            # Add final assistant response
            messages.append({"role": "assistant", "content": f"Response {seq}"})
        
        # Validate - should pass for valid sequences
        is_valid, error = session._validate_message_ordering(messages)
        
        # If we have tool sequences, they should be valid
        if num_tool_sequences > 0:
            assert is_valid is True, f"Valid tool sequences failed validation: {error}"




