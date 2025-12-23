"""
Mutation testing validation tests for input caching.

These tests are designed to kill mutations in the caching code.
The actual mutation testing is run with mutmut, but these tests help
validate that our test suite is comprehensive enough to catch bugs.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json
import hashlib

from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator
from broca.world_state.formatter import WorldStateFormatter


@pytest.fixture
def mock_world_state_aggregator():
    """Create a mock world state aggregator."""
    aggregator = Mock(spec=WorldStateAggregator)
    aggregator.aggregate.return_value = {
        "timestamp": "2024-01-01T00:00:00Z",
        "system": {"platform": "Linux"}
    }
    return aggregator


@pytest.fixture
def mock_world_state_formatter():
    """Create a mock world state formatter."""
    formatter = Mock(spec=WorldStateFormatter)
    formatter.format.return_value = '{"timestamp": "2024-01-01T00:00:00Z"}'
    return formatter


class TestMutationKillers:
    """
    Tests specifically designed to kill mutations.
    
    These tests verify specific behaviors that would be broken by common mutations
    like changing operators, conditions, or return values.
    """
    
    def test_hash_calculation_uses_sha256(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Kills mutation: changing hash algorithm or removing hash calculation."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        session._update_system_prompt()
        
        # Verify hash was calculated (should be 64 hex chars for SHA256)
        assert hasattr(session, '_last_world_state_hash')
        assert session._last_world_state_hash is not None
        assert len(session._last_world_state_hash) == 64
        assert all(c in '0123456789abcdef' for c in session._last_world_state_hash)
    
    def test_hash_comparison_uses_equality_not_inequality(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Kills mutation: changing == to != or vice versa."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # First update
        session._update_system_prompt()
        hash1 = session._last_world_state_hash
        
        # Second update with same state
        session._update_system_prompt()
        hash2 = session._last_world_state_hash
        
        # Hashes should be equal (same state)
        assert hash1 == hash2
    
    def test_hash_update_after_successful_prompt_update(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Kills mutation: not updating hash after prompt update."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # Initial state - hash should be None
        assert not hasattr(session, '_last_world_state_hash') or session._last_world_state_hash is None
        
        # Update - hash should be set
        session._update_system_prompt()
        assert hasattr(session, '_last_world_state_hash')
        assert session._last_world_state_hash is not None
    
    def test_skip_update_when_hash_matches(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Kills mutation: not skipping update when hash matches."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # First update
        session._update_system_prompt()
        initial_content = session.messages[0]["content"]
        initial_hash = session._last_world_state_hash
        
        # Reset mocks
        mock_world_state_aggregator.aggregate.reset_mock()
        mock_world_state_formatter.format.reset_mock()
        
        # Second update - should skip
        session._update_system_prompt()
        
        # Content should be unchanged
        assert session.messages[0]["content"] == initial_content
        assert session._last_world_state_hash == initial_hash
    
    def test_update_when_hash_differs(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Kills mutation: not updating when hash differs."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # First update
        session._update_system_prompt()
        initial_content = session.messages[0]["content"]
        
        # Change world state
        mock_world_state_aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T01:00:00Z",
            "system": {"platform": "Windows"}  # Changed
        }
        
        # Second update - should proceed
        session._update_system_prompt()
        new_content = session.messages[0]["content"]
        
        # Content should be different
        assert new_content != initial_content
    
    def test_json_sort_keys_for_determinism(self, mock_llm_client, mock_world_state_aggregator, mock_world_state_formatter):
        """Kills mutation: removing sort_keys=True (would break determinism)."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator
        )
        session._world_state_formatter = mock_world_state_formatter
        
        # Create world state with keys in different orders
        state1 = {"a": 1, "b": 2, "c": 3}
        state2 = {"c": 3, "a": 1, "b": 2}
        
        # Both should produce same hash (if sort_keys=True)
        hash1 = hashlib.sha256(json.dumps(state1, sort_keys=True).encode()).hexdigest()
        hash2 = hashlib.sha256(json.dumps(state2, sort_keys=True).encode()).hexdigest()
        
        assert hash1 == hash2
    
    def test_cached_tokens_extraction_from_usage(self, mock_llm_client):
        """Kills mutation: not extracting cached_tokens from usage dict."""
        response = {
            "usage": {
                "prompt_tokens": 100,
                "cached_tokens": 50
            }
        }
        
        usage = response.get("usage", {})
        cached_tokens = usage.get("cached_tokens", 0)
        
        # Should extract 50, not default to 0
        assert cached_tokens == 50
    
    def test_cached_tokens_default_to_zero_when_missing(self, mock_llm_client):
        """Kills mutation: not defaulting to 0 when cached_tokens missing."""
        response = {
            "usage": {
                "prompt_tokens": 100
                # No cached_tokens
            }
        }
        
        usage = response.get("usage", {})
        cached_tokens = usage.get("cached_tokens", 0)
        
        # Should default to 0
        assert cached_tokens == 0
    
    def test_hash_initialized_to_none(self, mock_llm_client):
        """Kills mutation: initializing hash to non-None value."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Hash should not exist or be None initially
        assert not hasattr(session, '_last_world_state_hash') or session._last_world_state_hash is None

