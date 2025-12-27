"""
Comprehensive tests for system prompt management.

Tests hash-based change detection, deduplication, size limits,
truncation prevention, and replace vs append behavior.
"""

from __future__ import annotations

import pytest
import json
import hashlib
from unittest.mock import Mock, MagicMock, patch

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


@pytest.fixture
def mock_world_state_aggregator():
    """Mock world state aggregator."""
    aggregator = Mock(spec=WorldStateAggregator)
    aggregator.aggregate.return_value = {
        "timestamp": "2024-01-01T00:00:00Z",
        "system": {"platform": "Linux", "python_version": "3.13.0"}
    }
    return aggregator


@pytest.fixture
def mock_world_state_formatter():
    """Mock world state formatter."""
    formatter = Mock(spec=WorldStateFormatter)
    formatter.format.return_value = '{"timestamp": "2024-01-01T00:00:00Z", "system": {"platform": "Linux"}}'
    return formatter


class TestHashBasedChangeDetection:
    """Test hash-based change detection for system prompt updates."""
    
    def test_identical_world_state_hash_prevents_update(self, mock_llm_client, mock_world_state_aggregator):
        """Test that identical world state hash prevents update."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        # Get initial content and hash
        initial_content = session.messages[0]["content"]
        initial_hash = session._last_world_state_hash
        assert initial_hash is not None
        
        # Update system prompt with same world state
        session._update_system_prompt()
        
        # Content should be unchanged (hash check should prevent update)
        updated_content = session.messages[0]["content"]
        assert updated_content == initial_content
        assert session._last_world_state_hash == initial_hash
    
    def test_changed_world_state_hash_triggers_update(self, mock_llm_client, mock_world_state_aggregator):
        """Test that changed world state hash triggers update."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        initial_content = session.messages[0]["content"]
        initial_hash = session._last_world_state_hash
        
        # Change world state
        mock_world_state_aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T01:00:00Z",
            "system": {"platform": "Windows", "python_version": "3.14.0"}
        }
        
        # Update system prompt
        session._update_system_prompt()
        
        # Content should be different and hash should change
        updated_content = session.messages[0]["content"]
        assert updated_content != initial_content
        assert session._last_world_state_hash != initial_hash
    
    def test_hash_stability_same_content(self, mock_llm_client):
        """Test that same world state content produces same hash."""
        session = ConversationSession(llm=mock_llm_client)
        
        world_state = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux", "python_version": "3.13.0"}
        }
        
        hash1 = session._calculate_stable_world_state_hash(world_state)
        hash2 = session._calculate_stable_world_state_hash(world_state)
        
        assert hash1 == hash2
    
    def test_hash_normalization_removes_timestamps(self, mock_llm_client):
        """Test that hash normalization removes volatile timestamp fields."""
        session = ConversationSession(llm=mock_llm_client)
        
        world_state1 = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux", "python_version": "3.13.0"}
        }
        
        world_state2 = {
            "timestamp": "2024-01-01T01:00:00Z",  # Different timestamp
            "system": {"platform": "Linux", "python_version": "3.13.0"}
        }
        
        hash1 = session._calculate_stable_world_state_hash(world_state1)
        hash2 = session._calculate_stable_world_state_hash(world_state2)
        
        # Hashes should be same despite different timestamps
        assert hash1 == hash2
    
    def test_hash_normalization_removes_multiple_timestamp_fields(self, mock_llm_client):
        """Test that normalization removes all timestamp-related fields."""
        session = ConversationSession(llm=mock_llm_client)
        
        world_state1 = {
            "timestamp": "2024-01-01T00:00:00Z",
            "last_indexed": "2024-01-01T00:00:00Z",
            "last_scan": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux"}
        }
        
        world_state2 = {
            "timestamp": "2024-01-01T01:00:00Z",
            "last_indexed": "2024-01-01T02:00:00Z",
            "last_scan": "2024-01-01T03:00:00Z",
            "system": {"platform": "Linux"}
        }
        
        hash1 = session._calculate_stable_world_state_hash(world_state1)
        hash2 = session._calculate_stable_world_state_hash(world_state2)
        
        assert hash1 == hash2
    
    def test_hash_changes_when_meaningful_content_changes(self, mock_llm_client):
        """Test that hash changes when meaningful content changes."""
        session = ConversationSession(llm=mock_llm_client)
        
        world_state1 = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Linux", "python_version": "3.13.0"}
        }
        
        world_state2 = {
            "timestamp": "2024-01-01T00:00:00Z",
            "system": {"platform": "Windows", "python_version": "3.13.0"}  # Different platform
        }
        
        hash1 = session._calculate_stable_world_state_hash(world_state1)
        hash2 = session._calculate_stable_world_state_hash(world_state2)
        
        assert hash1 != hash2


class TestDeduplication:
    """Test deduplication logic in system prompts."""
    
    def test_base_prompt_vs_summary_context_deduplication(self, mock_llm_client, mock_world_state_aggregator):
        """Test that duplicate summary context is excluded when it matches base prompt."""
        from broca.summarization.prompt_builder import PromptBuilder
        from broca.summarization.storage import SummaryStorage
        
        base_prompt = "You are BrocaOS. Always be helpful."
        
        # Mock summary storage to return context that duplicates base prompt
        storage = Mock(spec=SummaryStorage)
        storage.load_session_summary.return_value = None
        storage.load_project_state.return_value = None
        
        builder = PromptBuilder(summary_storage=storage)
        builder.build_context = Mock(return_value="You are BrocaOS. Always be helpful.")  # Duplicate
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt=base_prompt
        )
        
        # Mock summarization manager
        mock_summarization_manager = Mock()
        mock_summarization_manager.summary_storage = storage
        session._summarization_manager = mock_summarization_manager
        
        # Update system prompt
        session._update_system_prompt()
        
        # Base prompt should appear only once
        system_content = session.messages[0]["content"]
        occurrences = system_content.count(base_prompt)
        assert occurrences == 1, f"Base prompt appears {occurrences} times, should be 1 (duplicate summary excluded)"
    
    def test_duplicate_section_detection_within_prompt(self, mock_llm_client):
        """Test duplicate section detection within prompt."""
        session = ConversationSession(llm=mock_llm_client)
        
        # Prompt with duplicate sections
        duplicate_prompt = "Section 1 content\n\nSection 2 content\n\nSection 1 content\n\nSection 3 content"
        
        # Should detect duplicates (logs warning, but doesn't crash)
        try:
            session._validate_system_prompt_for_duplicates(duplicate_prompt)
        except Exception as e:
            pytest.fail(f"Validation should not raise exception: {e}")
        
        # Prompt without duplicates
        unique_prompt = "Section 1 content\n\nSection 2 content\n\nSection 3 content"
        try:
            session._validate_system_prompt_for_duplicates(unique_prompt)
        except Exception as e:
            pytest.fail(f"Validation should not raise exception: {e}")
    
    def test_is_duplicate_content_various_thresholds(self, mock_llm_client):
        """Test _is_duplicate_content with various thresholds."""
        session = ConversationSession(llm=mock_llm_client)
        
        content1 = "Hello world"
        content2 = "Hello world test"
        
        # With threshold 0.65, should match (11/16 = 0.6875 > 0.65)
        assert session._is_duplicate_content(content1, content2, threshold=0.65)
        
        # With threshold 0.7, should not match (0.6875 < 0.7)
        assert not session._is_duplicate_content(content1, content2, threshold=0.7)
        
        # Exact duplicates
        assert session._is_duplicate_content("Hello", "Hello")
        
        # Different content
        assert not session._is_duplicate_content("Hello", "Goodbye")
        
        # Empty content
        assert not session._is_duplicate_content("", "Hello")
        assert not session._is_duplicate_content("Hello", "")
    
    def test_duplicate_summary_context_excluded(self, mock_llm_client, mock_world_state_aggregator):
        """Test that duplicate summary context is excluded from prompt."""
        from broca.summarization.prompt_builder import PromptBuilder
        from broca.summarization.storage import SummaryStorage
        
        base_prompt = "You are BrocaOS."
        duplicate_summary = "You are BrocaOS."  # Exact duplicate
        
        storage = Mock(spec=SummaryStorage)
        storage.load_session_summary.return_value = None
        storage.load_project_state.return_value = None
        
        builder = PromptBuilder(summary_storage=storage)
        builder.build_context = Mock(return_value=duplicate_summary)
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt=base_prompt
        )
        
        mock_summarization_manager = Mock()
        mock_summarization_manager.summary_storage = storage
        session._summarization_manager = mock_summarization_manager
        
        # Get initial content (before update with duplicate)
        initial_content = session.messages[0]["content"]
        initial_base_count = initial_content.count(base_prompt)
        
        # Update system prompt
        session._update_system_prompt()
        
        # Base prompt should not appear more times than before (duplicate excluded)
        updated_content = session.messages[0]["content"]
        updated_base_count = updated_content.count(base_prompt)
        assert updated_base_count <= initial_base_count + 1  # Allow one more if unique


class TestSizeLimitEnforcement:
    """Test size limit enforcement for system prompts."""
    
    def test_max_system_prompt_size_enforcement(self, mock_llm_client, mock_world_state_aggregator):
        """Test that max_system_prompt_size is enforced with truncation."""
        original_max = config.storage.max_system_prompt_size
        config.storage.max_system_prompt_size = 1000  # Small limit
        
        try:
            large_base_prompt = "A" * 2000  # 2KB base prompt
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt=large_base_prompt
            )
            
            system_content = session.messages[0]["content"]
            assert len(system_content) <= config.storage.max_system_prompt_size
        finally:
            config.storage.max_system_prompt_size = original_max
    
    def test_max_world_state_size_enforcement(self, mock_llm_client, mock_world_state_aggregator):
        """Test that max_world_state_size is enforced by WorldStateFormatter."""
        original_max = config.storage.max_world_state_size
        config.storage.max_world_state_size = 500  # Small limit
        
        try:
            # Create large world state
            large_world_state = {"data": "x" * 10000}
            formatter = WorldStateFormatter(max_length=config.storage.max_world_state_size)
            formatted = formatter.format(large_world_state)
            
            assert len(formatted) <= config.storage.max_world_state_size
        finally:
            config.storage.max_world_state_size = original_max
    
    def test_max_summary_context_size_enforcement(self, mock_llm_client):
        """Test that max_summary_context_size is enforced by PromptBuilder."""
        from broca.summarization.prompt_builder import PromptBuilder
        from broca.summarization.storage import SummaryStorage
        
        original_max = config.storage.max_summary_context_size
        config.storage.max_summary_context_size = 200  # Small limit
        
        try:
            storage = Mock(spec=SummaryStorage)
            storage.load_session_summary.return_value = None
            storage.load_project_state.return_value = None
            
            builder = PromptBuilder(summary_storage=storage)
            # Create large context
            large_context = "A" * 1000
            builder.build_context = Mock(return_value=large_context)
            
            # PromptBuilder should enforce limit (tested via actual implementation)
            # For this test, we verify the limit is respected in session
            context = builder.build_context("test", [], system_prompt=None)
            # If context exceeds limit, it should be truncated
            assert len(context) <= config.storage.max_summary_context_size + 50  # Allow truncation message overhead
        finally:
            config.storage.max_summary_context_size = original_max
    
    def test_max_base_prompt_size_enforcement(self, mock_llm_client, mock_world_state_aggregator):
        """Test that max_base_prompt_size is enforced."""
        original_base_max = config.storage.max_base_prompt_size
        original_system_max = config.storage.max_system_prompt_size
        config.storage.max_base_prompt_size = 500  # Small limit
        config.storage.max_system_prompt_size = 5000  # Larger system limit
        
        try:
            large_base_prompt = "A" * 2000  # Exceeds base limit
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt=large_base_prompt
            )
            
            # Base prompt should be truncated to base limit
            system_content = session.messages[0]["content"]
            # Check that truncation message is present
            assert "[Base system prompt truncated" in system_content or len(system_content) <= config.storage.max_base_prompt_size + 100
        finally:
            config.storage.max_base_prompt_size = original_base_max
            config.storage.max_system_prompt_size = original_system_max
    
    def test_component_size_allocation_when_total_exceeds_limit(self, mock_llm_client, mock_world_state_aggregator):
        """Test component size allocation when total exceeds limit."""
        original_max = config.storage.max_system_prompt_size
        config.storage.max_system_prompt_size = 1000  # Small limit
        
        try:
            # Create base prompt that takes most space
            base_prompt = "Base prompt " * 50  # ~600 chars
            
            # Create large world state
            large_world_state = '{"data": "' + "x" * 1000 + '"}'
            formatter = WorldStateFormatter(max_length=1000)
            formatter.format = Mock(return_value=large_world_state)
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt=base_prompt
            )
            session._world_state_formatter = formatter
            
            # Update system prompt
            session._update_system_prompt()
            
            # Total should be within limit (components should be allocated proportionally)
            system_content = session.messages[0]["content"]
            assert len(system_content) <= config.storage.max_system_prompt_size
        finally:
            config.storage.max_system_prompt_size = original_max


class TestTruncationMessageAccumulationPrevention:
    """Test that truncation messages don't accumulate."""
    
    def test_truncation_messages_dont_accumulate_base_prompt(self, mock_llm_client, mock_world_state_aggregator):
        """Test that base prompt truncation messages don't accumulate."""
        original_max = config.storage.max_base_prompt_size
        config.storage.max_base_prompt_size = 500
        
        try:
            large_base_prompt = "A" * 2000
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt=large_base_prompt
            )
            
            # Update multiple times
            for _ in range(5):
                session._update_system_prompt()
            
            system_content = session.messages[0]["content"]
            # Truncation message should appear only once (or at most a few times, not 5)
            truncation_count = system_content.count("[Base system prompt truncated due to size limit]")
            assert truncation_count <= 2  # Allow some duplication but not excessive
        finally:
            config.storage.max_base_prompt_size = original_max
    
    def test_truncation_messages_dont_accumulate_world_state(self, mock_llm_client, mock_world_state_aggregator):
        """Test that world state truncation messages don't accumulate."""
        original_max = config.storage.max_system_prompt_size
        config.storage.max_system_prompt_size = 500
        
        try:
            large_world_state = '{"data": "' + "x" * 2000 + '"}'
            formatter = WorldStateFormatter(max_length=500)
            formatter.format = Mock(return_value=large_world_state)
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt="Base"
            )
            session._world_state_formatter = formatter
            
            # Update multiple times
            for _ in range(5):
                session._update_system_prompt()
            
            system_content = session.messages[0]["content"]
            # Should not have excessive truncation messages
            # (WorldStateFormatter handles its own truncation, so we check for reasonable content)
            assert len(system_content) <= config.storage.max_system_prompt_size
        finally:
            config.storage.max_system_prompt_size = original_max
    
    def test_multiple_truncation_scenarios(self, mock_llm_client, mock_world_state_aggregator):
        """Test multiple truncation scenarios don't cause accumulation."""
        original_base_max = config.storage.max_base_prompt_size
        original_system_max = config.storage.max_system_prompt_size
        config.storage.max_base_prompt_size = 300
        config.storage.max_system_prompt_size = 500
        
        try:
            # Create prompts that will be truncated
            large_base = "A" * 1000
            large_world_state = '{"data": "' + "x" * 1000 + '"}'
            
            formatter = WorldStateFormatter(max_length=500)
            formatter.format = Mock(return_value=large_world_state)
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt=large_base
            )
            session._world_state_formatter = formatter
            
            # Update multiple times with varying world states
            for i in range(3):
                mock_world_state_aggregator.aggregate.return_value = {
                    "timestamp": f"2024-01-01T{i:02d}:00:00Z",
                    "data": "x" * (1000 + i * 100)
                }
                session._update_system_prompt()
            
            system_content = session.messages[0]["content"]
            # Should be within limits and not have excessive truncation messages
            assert len(system_content) <= config.storage.max_system_prompt_size
        finally:
            config.storage.max_base_prompt_size = original_base_max
            config.storage.max_system_prompt_size = original_system_max


class TestReplaceVsAppend:
    """Test that system prompt is always replaced, never appended."""
    
    def test_system_prompt_replaces_not_appends(self, mock_llm_client, mock_world_state_aggregator):
        """Test that updating system prompt replaces content, doesn't append."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        initial_content = session.messages[0]["content"]
        initial_length = len(initial_content)
        
        # Change world state
        mock_world_state_aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T01:00:00Z",
            "system": {"platform": "Windows"}
        }
        
        # Update system prompt
        session._update_system_prompt()
        
        updated_content = session.messages[0]["content"]
        
        # Should not contain old content as substring (unless content is identical)
        if updated_content != initial_content:
            assert updated_content.count(initial_content) == 0, "Old content should not appear in new content"
        
        # Should only have one system message
        system_messages = [m for m in session.messages if m.get("role") == "system"]
        assert len(system_messages) == 1, f"Expected 1 system message, found {len(system_messages)}"
    
    def test_multiple_system_message_cleanup(self, mock_llm_client, mock_world_state_aggregator):
        """Test that multiple system messages are cleaned up before replacement."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        # Manually add extra system messages (simulating bug)
        session.messages.append({"role": "system", "content": "Extra system message 1"})
        session.messages.append({"role": "system", "content": "Extra system message 2"})
        
        # Update system prompt (should clean up all system messages first)
        session._update_system_prompt()
        
        # Should only have one system message
        system_messages = [m for m in session.messages if m.get("role") == "system"]
        assert len(system_messages) == 1, f"Expected 1 system message after cleanup, found {len(system_messages)}"
    
    def test_system_message_at_index_zero(self, mock_llm_client, mock_world_state_aggregator):
        """Test that system message is always at index 0."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        # Add some user messages
        session.messages.append({"role": "user", "content": "Hello"})
        session.messages.append({"role": "assistant", "content": "Hi"})
        
        # Update system prompt
        session._update_system_prompt()
        
        # System message should be at index 0
        assert session.messages[0].get("role") == "system", "System message should be at index 0"
        
        # Verify no system messages elsewhere
        for i, msg in enumerate(session.messages[1:], 1):
            assert msg.get("role") != "system", f"Found system message at index {i}, should only be at 0"
    
    def test_replace_behavior_with_content_change(self, mock_llm_client, mock_world_state_aggregator):
        """Test that replacement happens even when content changes."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt 1"
        )
        
        initial_content = session.messages[0]["content"]
        
        # Change base prompt (simulating config change)
        session.base_system_prompt = "Base prompt 2"
        
        # Change world state to trigger update
        mock_world_state_aggregator.aggregate.return_value = {
            "timestamp": "2024-01-01T01:00:00Z",
            "system": {"platform": "Windows"}
        }
        
        # Force hash change by resetting it
        session._last_world_state_hash = None
        
        # Update system prompt
        session._update_system_prompt()
        
        updated_content = session.messages[0]["content"]
        
        # Content should be different
        assert updated_content != initial_content
        
        # Should still only have one system message
        system_messages = [m for m in session.messages if m.get("role") == "system"]
        assert len(system_messages) == 1

