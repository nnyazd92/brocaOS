"""
Property-based tests for system prompt management using Hypothesis.

Tests invariants that should hold for all inputs.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock
from hypothesis import given, strategies as st, settings, HealthCheck, assume

from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator
from broca.world_state.formatter import WorldStateFormatter
from broca.config import config


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.chat.return_value = {"choices": [{"message": {"content": "test"}}]}
    client.extract_assistant_content = Mock(return_value="test")
    client.extract_tool_calls = Mock(return_value=[])
    return client


class TestSizeLimitsAlwaysRespected:
    """Property: Size limits are always respected."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        base_prompt_size=st.integers(min_value=0, max_value=20000),
        world_state_size=st.integers(min_value=0, max_value=100000)
    )
    def test_system_prompt_size_never_exceeds_max(self, mock_llm_client, base_prompt_size, world_state_size):
        """Property: System prompt size never exceeds max_system_prompt_size."""
        original_max = config.storage.max_system_prompt_size
        config.storage.max_system_prompt_size = 50000
        
        try:
            base_prompt = "A" * base_prompt_size if base_prompt_size > 0 else None
            
            aggregator = Mock(spec=WorldStateAggregator)
            aggregator.aggregate.return_value = {
                "timestamp": "2024-01-01T00:00:00Z",
                "data": "x" * world_state_size
            }
            
            formatter = WorldStateFormatter(max_length=world_state_size + 1000)
            formatted_world_state = '{"data": "' + "x" * min(world_state_size, 45000) + '"}'
            formatter.format = Mock(return_value=formatted_world_state)
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=aggregator,
                base_system_prompt=base_prompt
            )
            session._world_state_formatter = formatter
            
            system_content = session.messages[0]["content"]
            assert len(system_content) <= config.storage.max_system_prompt_size
        finally:
            config.storage.max_system_prompt_size = original_max
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(world_state_size=st.integers(min_value=0, max_value=50000))
    def test_world_state_size_never_exceeds_max(self, world_state_size):
        """Property: World state size never exceeds max_world_state_size."""
        original_max = config.storage.max_world_state_size
        config.storage.max_world_state_size = 30000
        
        try:
            world_state = {"data": "x" * world_state_size}
            formatter = WorldStateFormatter(max_length=config.storage.max_world_state_size)
            formatted = formatter.format(world_state)
            
            assert len(formatted) <= config.storage.max_world_state_size
        finally:
            config.storage.max_world_state_size = original_max
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(base_prompt_size=st.integers(min_value=0, max_value=25000))
    def test_base_prompt_size_never_exceeds_max(self, mock_llm_client, mock_world_state_aggregator, base_prompt_size):
        """Property: Base prompt size never exceeds max_base_prompt_size."""
        original_base_max = config.storage.max_base_prompt_size
        original_system_max = config.storage.max_system_prompt_size
        config.storage.max_base_prompt_size = 20000
        config.storage.max_system_prompt_size = 50000  # Larger than base
        
        try:
            base_prompt = "A" * base_prompt_size if base_prompt_size > 0 else None
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt=base_prompt
            )
            
            system_content = session.messages[0]["content"]
            # Base prompt portion should respect base limit (with some overhead for truncation)
            if base_prompt_size > config.storage.max_base_prompt_size:
                # Should have truncation message
                assert "[Base system prompt truncated" in system_content or len(system_content) <= config.storage.max_base_prompt_size + 200
        finally:
            config.storage.max_base_prompt_size = original_base_max
            config.storage.max_system_prompt_size = original_system_max


class TestHashStability:
    """Property: Hash calculation is stable."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        platform=st.text(min_size=1, max_size=20),
        python_version=st.text(min_size=1, max_size=20),
        timestamp1=st.text(min_size=10, max_size=30),
        timestamp2=st.text(min_size=10, max_size=30)
    )
    def test_same_content_always_produces_same_hash(self, mock_llm_client, platform, python_version, timestamp1, timestamp2):
        """Property: Same world state content always produces same hash."""
        session = ConversationSession(llm=mock_llm_client)
        
        world_state1 = {
            "timestamp": timestamp1,
            "system": {"platform": platform, "python_version": python_version}
        }
        
        world_state2 = {
            "timestamp": timestamp2,  # Different timestamp
            "system": {"platform": platform, "python_version": python_version}  # Same content
        }
        
        hash1 = session._calculate_stable_world_state_hash(world_state1)
        hash2 = session._calculate_stable_world_state_hash(world_state2)
        
        # Hashes should be same (timestamp is normalized out)
        assert hash1 == hash2
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        content1=st.dictionaries(st.text(max_size=10), st.text(max_size=50), max_size=10),
        content2=st.dictionaries(st.text(max_size=10), st.text(max_size=50), max_size=10)
    )
    def test_normalized_world_state_produces_stable_hash(self, mock_llm_client, content1, content2):
        """Property: Normalized world state produces stable hash regardless of timestamp order."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Create world states with same content but different timestamps
        world_state1 = {
            "timestamp": "2024-01-01T00:00:00Z",
            "last_indexed": "2024-01-01T01:00:00Z",
            **content1
        }
        
        world_state2 = {
            "timestamp": "2024-01-01T02:00:00Z",
            "last_indexed": "2024-01-01T03:00:00Z",
            **content1  # Same content
        }
        
        hash1 = session._calculate_stable_world_state_hash(world_state1)
        hash2 = session._calculate_stable_world_state_hash(world_state2)
        
        # Hashes should be same (timestamps are normalized out)
        assert hash1 == hash2
        
        # But different content should produce different hash
        world_state3 = {
            "timestamp": "2024-01-01T00:00:00Z",
            **content2  # Different content
        }
        hash3 = session._calculate_stable_world_state_hash(world_state3)
        if content1 != content2:
            # Should be different (unless content1 and content2 happen to be same)
            assert hash1 != hash3 or content1 == content2


class TestDeduplicationConsistency:
    """Property: Deduplication is consistent."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(
        content1=st.text(min_size=0, max_size=200),
        content2=st.text(min_size=0, max_size=200),
        threshold=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_duplicate_content_detection_is_consistent(self, mock_llm_client, content1, content2, threshold):
        """Property: Duplicate content detection is consistent (same inputs = same result)."""
        session = ConversationSession(llm=mock_llm_client)
        
        result1 = session._is_duplicate_content(content1, content2, threshold=threshold)
        result2 = session._is_duplicate_content(content1, content2, threshold=threshold)
        
        # Same inputs should produce same result
        assert result1 == result2
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        content1=st.text(min_size=0, max_size=200),
        content2=st.text(min_size=0, max_size=200),
        threshold=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_deduplication_is_idempotent(self, mock_llm_client, content1, content2, threshold):
        """Property: Deduplication is idempotent (running twice = same result)."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Check if duplicate
        is_duplicate1 = session._is_duplicate_content(content1, content2, threshold=threshold)
        is_duplicate2 = session._is_duplicate_content(content1, content2, threshold=threshold)
        
        # Should be idempotent
        assert is_duplicate1 == is_duplicate2
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        content=st.text(min_size=1, max_size=200),
        threshold=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_exact_duplicates_always_detected(self, mock_llm_client, content, threshold):
        """Property: Exact duplicates are always detected regardless of threshold."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Exact duplicates should always be detected
        assert session._is_duplicate_content(content, content, threshold=threshold)


class TestReplaceConsistency:
    """Property: System message replacement is consistent."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(num_updates=st.integers(min_value=1, max_value=10))
    def test_exactly_one_system_message_after_update(self, mock_llm_client, mock_world_state_aggregator, num_updates):
        """Property: After update, exactly one system message exists."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        for i in range(num_updates):
            # Change world state slightly
            mock_world_state_aggregator.aggregate.return_value = {
                "timestamp": f"2024-01-01T{i:02d}:00:00Z",
                "system": {"platform": "Linux", "iteration": i}
            }
            
            # Reset hash to force update
            session._last_world_state_hash = None
            
            session._update_system_prompt()
            
            # Should always have exactly one system message
            system_messages = [m for m in session.messages if m.get("role") == "system"]
            assert len(system_messages) == 1, f"Expected 1 system message after update {i}, found {len(system_messages)}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(num_user_messages=st.integers(min_value=0, max_value=5))
    def test_system_message_always_at_index_zero(self, mock_llm_client, mock_world_state_aggregator, num_user_messages):
        """Property: System message is always at index 0."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        # Add user messages
        for i in range(num_user_messages):
            session.messages.append({"role": "user", "content": f"Message {i}"})
        
        # Update system prompt
        session._last_world_state_hash = None
        session._update_system_prompt()
        
        # System message should be at index 0
        assert session.messages[0].get("role") == "system", "System message should always be at index 0"
        
        # No other system messages should exist
        for i, msg in enumerate(session.messages[1:], 1):
            assert msg.get("role") != "system", f"Found system message at index {i}, should only be at 0"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(num_extra_system_messages=st.integers(min_value=1, max_value=5))
    def test_multiple_system_messages_cleaned_up(self, mock_llm_client, mock_world_state_aggregator, num_extra_system_messages):
        """Property: Multiple system messages are cleaned up to exactly one."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        # Manually add extra system messages (simulating bug)
        for i in range(num_extra_system_messages):
            session.messages.append({"role": "system", "content": f"Extra system message {i}"})
        
        # Update system prompt (should clean up)
        session._last_world_state_hash = None
        session._update_system_prompt()
        
        # Should have exactly one system message
        system_messages = [m for m in session.messages if m.get("role") == "system"]
        assert len(system_messages) == 1, f"Expected 1 system message after cleanup, found {len(system_messages)}"
        
        # And it should be at index 0
        assert session.messages[0].get("role") == "system"


@pytest.fixture
def mock_world_state_aggregator():
    """Mock world state aggregator."""
    aggregator = Mock(spec=WorldStateAggregator)
    aggregator.aggregate.return_value = {
        "timestamp": "2024-01-01T00:00:00Z",
        "system": {"platform": "Linux", "python_version": "3.13.0"}
    }
    return aggregator

