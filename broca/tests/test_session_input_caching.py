"""
Tests for input caching optimization in ConversationSession.

Tests system prompt hash tracking, cache effectiveness monitoring,
and message consistency for optimal API caching.
"""

from __future__ import annotations

import pytest
import json
import hashlib
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator
from broca.world_state.formatter import WorldStateFormatter
from broca.tests.utils import build_llm_response


class TestSystemPromptHashTracking:
    """Test system prompt hash-based change detection."""
    
    @pytest.fixture
    def mock_world_state_aggregator(self):
        """Create a mock world state aggregator."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "platform": "Linux",
                "python_version": "3.13.0"
            }
        }
        return aggregator
    
    @pytest.fixture
    def mock_world_state_formatter(self):
        """Create a mock world state formatter."""
        formatter = Mock(spec=WorldStateFormatter)
        formatter.format.return_value = '{"timestamp": "2024-01-01T00:00:00Z", "system": {"platform": "Linux"}}'
        return formatter
    
    def test_hash_calculation_for_world_state(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Test that hash is calculated correctly for world state."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        
        # Manually set formatter (normally set in __init__)
        session._world_state_formatter = mock_world_state_formatter
        
        # Calculate expected hash (matches implementation: str(sorted(world_state.items())))
        world_state = mock_world_state_aggregator.aggregate()
        world_state_str = str(sorted(world_state.items()))
        expected_hash = hashlib.sha256(world_state_str.encode()).hexdigest()
        
        # Update system prompt (should calculate hash)
        session._update_system_prompt()
        
        # Verify hash was stored
        assert hasattr(session, '_last_world_state_hash')
        assert session._last_world_state_hash == expected_hash
    
    def test_skip_update_when_hash_unchanged(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Test that system prompt update is skipped when hash is unchanged."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # First update - should proceed
        initial_content = session.messages[0]["content"] if session.messages else None
        session._update_system_prompt()
        
        # Get content after first update
        first_update_content = session.messages[0]["content"]
        assert first_update_content is not None
        
        # Reset aggregator call count
        mock_world_state_aggregator.aggregate.reset_mock()
        mock_world_state_formatter.format.reset_mock()
        
        # Second update with same world state - should skip
        session._update_system_prompt()
        
        # Aggregator should not be called again (or called but update skipped)
        # Content should remain the same
        second_update_content = session.messages[0]["content"]
        assert second_update_content == first_update_content
    
    def test_update_when_hash_changes(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Test that system prompt is updated when world state hash changes."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # First update
        session._update_system_prompt()
        first_content = session.messages[0]["content"]
        first_hash = session._last_world_state_hash
        
        # Change world state
        new_world_state = {
            "timestamp": "2024-01-01T01:00:00Z",  # Different timestamp
            "system": {
                "platform": "Linux",
                "python_version": "3.13.0",
                "new_field": "new_value"  # New field
            }
        }
        mock_world_state_aggregator.aggregate.return_value = new_world_state
        
        # Update formatter to return new world state JSON
        import json
        mock_world_state_formatter.format.return_value = json.dumps(new_world_state, indent=2)
        
        # Second update - should proceed
        session._update_system_prompt()
        second_content = session.messages[0]["content"]
        second_hash = session._last_world_state_hash
        
        # Hash should be different
        assert second_hash != first_hash
        # Content should be different
        assert second_content != first_content
        # New content should include new field
        assert "new_field" in second_content or "new_value" in second_content
    
    def test_hash_stability_same_state_same_hash(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Test that same world state always produces same hash."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # Calculate hash multiple times
        session._update_system_prompt()
        hash1 = session._last_world_state_hash
        
        session._update_system_prompt()
        hash2 = session._last_world_state_hash
        
        session._update_system_prompt()
        hash3 = session._last_world_state_hash
        
        # All hashes should be identical
        assert hash1 == hash2 == hash3
    
    def test_hash_with_different_structures(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Test hash calculation with different world state structures."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # Test with nested structures
        mock_world_state_aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "platform": "Linux",
                "nested": {
                    "level1": {
                        "level2": "value"
                    }
                }
            }
        }
        
        session._update_system_prompt()
        hash_nested = session._last_world_state_hash
        
        # Test with arrays
        mock_world_state_aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "platform": "Linux",
                "items": [1, 2, 3, 4, 5]
            }
        }
        
        session._update_system_prompt()
        hash_array = session._last_world_state_hash
        
        # Hashes should be different
        assert hash_nested != hash_array


class TestCacheEffectivenessTracking:
    """Test cache effectiveness tracking from API responses."""
    
    def test_extract_cached_tokens_from_response(self, mock_llm_client):
        """Test extraction of cached_tokens from API response."""
        # Create response with cached_tokens
        response_with_cache = build_llm_response(
            content="Test response",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "cached_tokens": 75  # Cached tokens
            }
        )
        
        # Verify cached_tokens can be extracted
        usage = response_with_cache.get("usage", {})
        cached_tokens = usage.get("cached_tokens", 0)
        assert cached_tokens == 75
    
    def test_handle_missing_cached_tokens_field(self, mock_llm_client):
        """Test graceful handling when cached_tokens field is missing."""
        # Response without cached_tokens
        response_no_cache = build_llm_response(
            content="Test response",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
                # No cached_tokens field
            }
        )
        
        # Should handle gracefully
        usage = response_no_cache.get("usage", {})
        cached_tokens = usage.get("cached_tokens", 0)
        assert cached_tokens == 0
    
    def test_cache_ratio_calculation(self, mock_llm_client):
        """Test cache ratio calculation."""
        response = build_llm_response(
            content="Test",
            usage={
                "prompt_tokens": 100,
                "cached_tokens": 50
            }
        )
        
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        cached_tokens = usage.get("cached_tokens", 0)
        
        if prompt_tokens > 0:
            cache_ratio = cached_tokens / prompt_tokens
            assert cache_ratio == 0.5
        else:
            pytest.skip("No prompt tokens to calculate ratio")
    
    def test_cache_metrics_with_zero_cached_tokens(self, mock_llm_client):
        """Test cache metrics when cached_tokens is zero."""
        response = build_llm_response(
            content="Test",
            usage={
                "prompt_tokens": 100,
                "cached_tokens": 0
            }
        )
        
        usage = response.get("usage", {})
        cached_tokens = usage.get("cached_tokens", 0)
        assert cached_tokens == 0


class TestMessageConsistency:
    """Test message consistency for optimal caching."""
    
    def test_deterministic_message_ordering(self, mock_llm_client):
        """Test that messages are returned in deterministic order."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Add messages
        session.messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"},
        ]
        
        # Get messages multiple times
        messages1 = session._get_messages_for_llm()
        messages2 = session._get_messages_for_llm()
        
        # Should be identical
        assert messages1 == messages2
        assert len(messages1) == len(messages2)
        for i, (m1, m2) in enumerate(zip(messages1, messages2)):
            assert m1 == m2, f"Message {i} differs"
    
    def test_message_structure_preservation(self, mock_llm_client):
        """Test that message structure is preserved across calls."""
        session = ConversationSession(llm=mock_llm_client)
        
        session.messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Test"},
        ]
        
        messages = session._get_messages_for_llm()
        
        # Verify structure
        assert all("role" in msg for msg in messages)
        assert all("content" in msg for msg in messages)
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_consistent_tool_result_formatting(self, mock_llm_client):
        """Test that tool results are consistently formatted."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Add messages with tool results
        session.messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Use tool"},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "test_tool", "arguments": "{}"}}]},
            {"role": "tool", "name": "test_tool", "content": "Tool result"},
        ]
        
        messages1 = session._get_messages_for_llm()
        messages2 = session._get_messages_for_llm()
        
        # Tool messages should be consistently formatted
        tool_msgs1 = [m for m in messages1 if m.get("role") == "tool"]
        tool_msgs2 = [m for m in messages2 if m.get("role") == "tool"]
        
        assert len(tool_msgs1) == len(tool_msgs2)
        if tool_msgs1:
            assert tool_msgs1[0] == tool_msgs2[0]


class TestCacheIntegration:
    """Integration tests for caching behavior."""
    
    @pytest.fixture
    def mock_world_state_aggregator(self):
        """Create a mock world state aggregator."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {
                "platform": "Linux",
                "python_version": "3.13.0"
            }
        }
        return aggregator
    
    @pytest.fixture
    def mock_world_state_formatter(self):
        """Create a mock world state formatter."""
        formatter = Mock(spec=WorldStateFormatter)
        formatter.format.return_value = '{"timestamp": "2024-01-01T00:00:00Z", "system": {"platform": "Linux"}}'
        return formatter
    
    def test_hash_tracking_with_real_update_flow(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Test hash tracking in a realistic update flow."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        # Note: _update_system_prompt() is called in __init__ if world_state_aggregator is available
        # So hash may already be set. Reset it for this test.
        session._last_world_state_hash = None
        session._world_state_formatter = mock_world_state_formatter
        
        # Initial state (after reset)
        assert session._last_world_state_hash is None
        
        # First update
        session._update_system_prompt()
        assert hasattr(session, '_last_world_state_hash')
        assert session._last_world_state_hash is not None
        
        # Second update (same state)
        initial_hash = session._last_world_state_hash
        session._update_system_prompt()
        assert session._last_world_state_hash == initial_hash
    
    def test_cache_tracking_with_llm_response(self, mock_llm_client):
        """Test cache tracking when processing LLM responses."""
        # This test will be expanded when we implement cache logging
        # For now, verify response structure supports it
        response = build_llm_response(
            content="Response",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "cached_tokens": 25
            }
        )
        
        # Verify structure
        assert "usage" in response
        assert "cached_tokens" in response["usage"]

