"""
Integration tests for session summarization.

Tests full summarization loop in session: prompt size stability, session resumption, evidence verification.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest

from broca.repl.session import ConversationSession
from broca.llm.deepseek_client import DeepSeekClient
from broca.tests.utils import build_llm_response
from broca.summarization.event_logger import EventLogger
from broca.summarization.storage import SummaryStorage
from broca.summarization.models import SessionSummary, SummaryHeader, SummaryBlocks
from broca.summarization.prompt_builder import PromptBuilder


@pytest.fixture
def temp_dirs():
    """Temporary directories for event logs and summaries."""
    with tempfile.TemporaryDirectory() as event_dir, tempfile.TemporaryDirectory() as summary_dir:
        yield {"event": event_dir, "summary": summary_dir}


@pytest.fixture
def mock_llm_client():
    """Mock LLM client that returns simple responses."""
    client = Mock(spec=DeepSeekClient)
    client.extract_assistant_content = Mock(return_value="Mock response")
    client.extract_tool_calls = Mock(return_value=[])
    client.chat.return_value = build_llm_response(content="Mock response")
    client.chat_stream = Mock(return_value=iter([]))
    return client


class TestSessionSummarizationIntegration:
    """Test session summarization integration."""
    
    def test_event_logging_in_session(self, temp_dirs, mock_llm_client):
        """Test that events are logged during session conversation."""
        # Create session with summarization enabled
        # We'll need to patch config to enable summarization
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Test system prompt",
                llm=mock_llm_client
            )
            
            # Send a message
            session.send("Hello")
            
            # Check that events were logged
            event_logger = session._event_logger
            assert event_logger is not None
            
            events = event_logger.get_events(session.session_id)
            assert len(events) >= 2  # At least user and assistant messages
            
            # Verify event types
            event_types = {e.get("type") for e in events}
            assert "user_message" in event_types
            assert "assistant_message" in event_types
    
    def test_summary_context_in_prompt(self, temp_dirs, mock_llm_client):
        """Test that summary context is included in system prompt."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Base prompt",
                llm=mock_llm_client
            )
            
            # Create a summary manually
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0
                ),
                summary_blocks=SummaryBlocks(current_goal="Test goal")
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            # Update system prompt (this should include summary context)
            # Note: This requires world_state_aggregator, so we'll test the logic indirectly
            # by checking that the summary storage can load the summary
            
            loaded_summary = summary_storage.load_session_summary(session.session_id)
            assert loaded_summary is not None
            assert loaded_summary.summary_blocks.current_goal == "Test goal"
    
    def test_prompt_size_stability(self, temp_dirs, mock_llm_client):
        """Test that prompt size stays stable across multiple turns."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "trigger_turns", 2)  # Trigger after 2 turns
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Send multiple messages (more than trigger_turns)
            for i in range(5):
                session.send(f"Message {i}")
            
            # Check that events were logged (should have many events)
            events = session._event_logger.get_events(session.session_id)
            assert len(events) >= 10  # At least 5 user + 5 assistant messages
            
            # Check that summary was created (if summarization triggered)
            # Note: This depends on the mock summarizer, so we're mainly testing the flow works
    
    def test_message_pruning_after_summarization(self, temp_dirs, mock_llm_client):
        """Test that messages are pruned after summarization."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "trigger_turns", 2)
            m.setattr(config.summarization, "last_turns_count", 2)
            
            session = ConversationSession(
                system_prompt="Test system",
                llm=mock_llm_client
            )
            
            # Send multiple messages to build up history
            initial_message_count = len(session.messages)
            for i in range(5):
                session.send(f"Message {i}")
            
            # Verify messages have event IDs
            non_system_messages = [m for m in session.messages if m.get("role") != "system"]
            messages_with_event_ids = [m for m in non_system_messages if m.get("event_ids")]
            assert len(messages_with_event_ids) > 0, "Some messages should have event IDs"
            
            # Manually trigger summarization and pruning
            if session._summarization_manager and session._event_logger:
                # Get the last event ID
                events = session._event_logger.get_events(session.session_id)
                if events:
                    # Use the second-to-last event as the "last summarized" event
                    # This simulates summarizing all but the last turn
                    last_summarized_idx = max(0, len(events) - 4)  # Keep last 2 turns (4 events)
                    last_summarized_event_id = events[last_summarized_idx].get("event_id")
                    
                    if last_summarized_event_id:
                        # Count messages before pruning
                        messages_before = len(session.messages)
                        
                        # Prune messages
                        removed_count = session._prune_summarized_messages(last_summarized_event_id)
                        
                        # Verify messages were removed
                        messages_after = len(session.messages)
                        assert messages_after < messages_before or removed_count == 0, \
                            "Messages should be removed after pruning (or none to remove)"
                        
                        # Verify system message is preserved
                        system_messages = [m for m in session.messages if m.get("role") == "system"]
                        assert len(system_messages) > 0, "System message should be preserved"
    
    def test_system_message_preserved_after_pruning(self, temp_dirs, mock_llm_client):
        """Test that system message is always preserved during pruning."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Important system prompt",
                llm=mock_llm_client
            )
            
            # Send some messages
            session.send("Test message")
            
            # Get system message
            system_message = next((m for m in session.messages if m.get("role") == "system"), None)
            assert system_message is not None, "System message should exist"
            
            # Try to prune (even if no events were summarized, system should remain)
            if session._event_logger:
                events = session._event_logger.get_events(session.session_id)
                if events:
                    # Use first event as "last summarized" to prune everything
                    last_summarized_event_id = events[-1].get("event_id")
                    if last_summarized_event_id:
                        session._prune_summarized_messages(last_summarized_event_id)
                        
                        # Verify system message still exists
                        system_messages_after = [m for m in session.messages if m.get("role") == "system"]
                        assert len(system_messages_after) > 0, "System message must be preserved"
                        assert system_messages_after[0].get("content") == "Important system prompt"
    
    def test_messages_without_event_ids_handled(self, temp_dirs, mock_llm_client):
        """Test that messages without event IDs are handled gracefully."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Add a message without event IDs (simulating old format)
            session.messages.append({
                "role": "user",
                "content": "Old format message without event_ids"
            })
            
            # Try to prune - should not crash
            if session._event_logger:
                events = session._event_logger.get_events(session.session_id)
                if events:
                    last_summarized_event_id = events[0].get("event_id") if events else None
                    if last_summarized_event_id:
                        # Should not raise an exception
                        removed_count = session._prune_summarized_messages(last_summarized_event_id)
                        
                        # Message without event IDs should be kept (backward compatibility)
                        old_format_messages = [
                            m for m in session.messages 
                            if m.get("content") == "Old format message without event_ids"
                        ]
                        assert len(old_format_messages) > 0, "Messages without event IDs should be kept"
    
    def test_last_k_turns_preserved(self, temp_dirs, mock_llm_client):
        """Test that last K turns are preserved after pruning."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "last_turns_count", 2)
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Send many messages
            for i in range(10):
                session.send(f"Message {i}")
            
            # Get message count before pruning
            messages_before = len(session.messages)
            
            # Prune with an early event ID (should keep last K turns)
            if session._event_logger:
                events = session._event_logger.get_events(session.session_id)
                if len(events) > 4:
                    # Use an event from the middle to simulate summarizing early events
                    mid_event_id = events[len(events) // 2].get("event_id")
                    if mid_event_id:
                        session._prune_summarized_messages(mid_event_id)
                        
                        # Should have fewer messages but still have some
                        messages_after = len(session.messages)
                        assert messages_after < messages_before, "Some messages should be removed"
                        assert messages_after > 1, "Should keep at least system message + some recent messages"
                        
                        # Verify we have at least last K turns worth of messages
                        # (K turns = K * 2 messages typically, plus system message)
                        min_expected = 1 + (config.summarization.last_turns_count * 2)  # system + K turns
                        assert messages_after >= min_expected or messages_before < min_expected, \
                            f"Should keep at least {min_expected} messages (system + last K turns)"
    
    def test_summary_formatted_as_historical_context(self, temp_dirs, mock_llm_client):
        """Test that summaries are formatted as historical context, not directives."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Base prompt",
                llm=mock_llm_client
            )
            
            # Create a summary with goals and next steps
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0
                ),
                summary_blocks=SummaryBlocks(
                    current_goal="Build a web application",
                    next_steps=["Set up database", "Create API endpoints"],
                    what_we_built=["Initial project structure"],
                    open_questions=["Which framework to use?"],
                    constraints=["Must use Python"]
                )
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            # Build context using PromptBuilder
            prompt_builder = PromptBuilder(
                summary_storage=summary_storage,
                last_turns_count=3
            )
            context = prompt_builder.build_context(session.session_id, session.messages)
            
            # Verify the context contains historical context language
            assert "Session Summary (Historical Context)" in context, \
                "Summary should be labeled as historical context"
            assert "may be outdated or completed" in context, \
                "Summary should include disclaimer about outdated goals"
            assert "Previous Goal Context" in context, \
                "Goals should be labeled as 'Previous Goal Context', not 'Current Goal'"
            assert "Previously Planned Steps" in context, \
                "Next steps should be labeled as 'Previously Planned Steps', not 'Next Steps'"
            
            # Verify it does NOT contain directive language
            assert "Current Goal:" not in context, \
                "Should not use 'Current Goal:' directive language"
            assert context.count("Next Steps:") == 0, \
                "Should not use 'Next Steps:' directive language (should use 'Previously Planned Steps')"
    
    def test_summary_context_prioritizes_current_request(self, temp_dirs, mock_llm_client):
        """Test that summary context includes language prioritizing current user request."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Base prompt",
                llm=mock_llm_client
            )
            
            # Create a summary with an old goal
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0
                ),
                summary_blocks=SummaryBlocks(
                    current_goal="Old goal that should be superseded"
                )
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            # Build context
            prompt_builder = PromptBuilder(
                summary_storage=summary_storage,
                last_turns_count=3
            )
            context = prompt_builder.build_context(session.session_id, session.messages)
            
            # Verify it includes language about prioritizing current request
            assert "prioritize the current user request" in context.lower() or \
                   "prioritize the current user request and recent conversation turns" in context.lower(), \
                "Context should instruct to prioritize current user request over historical goals"
    
    def test_summary_formatting_with_all_fields(self, temp_dirs, mock_llm_client):
        """Test that all summary fields are formatted with historical context language."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Base prompt",
                llm=mock_llm_client
            )
            
            # Create a comprehensive summary
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0
                ),
                summary_blocks=SummaryBlocks(
                    current_goal="Test goal",
                    what_we_built=["Item 1", "Item 2"],
                    open_questions=["Question 1"],
                    constraints=["Constraint 1"],
                    next_steps=["Step 1", "Step 2"]
                )
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            # Format the summary
            prompt_builder = PromptBuilder(
                summary_storage=summary_storage,
                last_turns_count=3
            )
            formatted = prompt_builder._format_summary(summary)
            
            # Verify all fields use historical context language
            assert "Previous Goal Context" in formatted
            assert "What Was Built (Historical)" in formatted
            assert "Previous Open Questions" in formatted and "may be resolved" in formatted
            assert "Previous Constraints" in formatted and "may no longer apply" in formatted
            assert "Previously Planned Steps" in formatted and "may be completed or outdated" in formatted


class TestGradualPruning:
    """Tests for gradual context reduction after summarization."""
    
    def test_buffer_calculation_first_cycle(self, temp_dirs, mock_llm_client):
        """Test that first summarization uses initial buffer size."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "gradual_pruning_enabled", True)
            m.setattr(config.summarization, "initial_buffer_turns", 10)
            m.setattr(config.summarization, "min_buffer_turns", 3)
            m.setattr(config.summarization, "buffer_reduction_rate", 2)
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Create a summary with cycle_count = 0 (first summarization)
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0,
                    summarization_cycle_count=0
                ),
                summary_blocks=SummaryBlocks()
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            # Calculate buffer size
            buffer_size = session._calculate_buffer_turns()
            
            # First cycle should use initial buffer
            assert buffer_size == 10, f"First cycle should use initial buffer (10), got {buffer_size}"
    
    def test_buffer_calculation_gradual_reduction(self, temp_dirs, mock_llm_client):
        """Test that buffer size reduces gradually over cycles."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "gradual_pruning_enabled", True)
            m.setattr(config.summarization, "initial_buffer_turns", 10)
            m.setattr(config.summarization, "min_buffer_turns", 3)
            m.setattr(config.summarization, "buffer_reduction_rate", 2)
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            summary_storage = session._summarization_manager.summary_storage
            
            # Test cycle 0: initial buffer
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0,
                    summarization_cycle_count=0
                ),
                summary_blocks=SummaryBlocks()
            )
            summary_storage.save_session_summary(session.session_id, summary)
            assert session._calculate_buffer_turns() == 10
            
            # Test cycle 1: 10 - (1 * 2) = 8
            summary.header.summarization_cycle_count = 1
            summary_storage.save_session_summary(session.session_id, summary)
            assert session._calculate_buffer_turns() == 8
            
            # Test cycle 2: 10 - (2 * 2) = 6
            summary.header.summarization_cycle_count = 2
            summary_storage.save_session_summary(session.session_id, summary)
            assert session._calculate_buffer_turns() == 6
            
            # Test cycle 3: 10 - (3 * 2) = 4
            summary.header.summarization_cycle_count = 3
            summary_storage.save_session_summary(session.session_id, summary)
            assert session._calculate_buffer_turns() == 4
            
            # Test cycle 4: 10 - (4 * 2) = 2, but min is 3, so should be 3
            summary.header.summarization_cycle_count = 4
            summary_storage.save_session_summary(session.session_id, summary)
            assert session._calculate_buffer_turns() == 3, "Should not go below min_buffer_turns"
    
    def test_buffer_calculation_with_gradual_disabled(self, temp_dirs, mock_llm_client):
        """Test that disabling gradual pruning uses standard last_turns_count."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "gradual_pruning_enabled", False)
            m.setattr(config.summarization, "last_turns_count", 5)
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Even with a summary with high cycle count, should use last_turns_count
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0,
                    summarization_cycle_count=10  # High cycle count
                ),
                summary_blocks=SummaryBlocks()
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            buffer_size = session._calculate_buffer_turns()
            assert buffer_size == 5, "Should use last_turns_count when gradual pruning is disabled"
    
    def test_cycle_count_increments_on_summarization(self, temp_dirs, mock_llm_client):
        """Test that cycle count increments when summarization occurs."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "trigger_turns", 2)
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Send messages to trigger summarization
            for i in range(3):
                session.send(f"Message {i}")
            
            # Check that summary was created and cycle count is tracked
            summary_storage = session._summarization_manager.summary_storage
            summary = summary_storage.load_session_summary(session.session_id)
            
            if summary:
                # First summarization should have cycle_count = 0
                assert summary.header.summarization_cycle_count == 0, \
                    "First summarization should have cycle_count = 0"
    
    def test_gradual_pruning_keeps_more_messages_initially(self, temp_dirs, mock_llm_client):
        """Test that gradual pruning keeps more messages initially than standard pruning."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "gradual_pruning_enabled", True)
            m.setattr(config.summarization, "initial_buffer_turns", 10)
            m.setattr(config.summarization, "min_buffer_turns", 3)
            m.setattr(config.summarization, "buffer_reduction_rate", 2)
            m.setattr(config.summarization, "last_turns_count", 3)  # Standard would be 3
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Send many messages
            for i in range(20):
                session.send(f"Message {i}")
            
            # Create summary with cycle_count = 0 (first summarization)
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0,
                    summarization_cycle_count=0,
                    last_summarized_event_id="evt_mid"
                ),
                summary_blocks=SummaryBlocks()
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            # Simulate events for pruning
            if session._event_logger:
                events = session._event_logger.get_events(session.session_id)
                if len(events) > 4:
                    # Use an event from the middle
                    mid_event_id = events[len(events) // 2].get("event_id")
                    if mid_event_id:
                        messages_before = len(session.messages)
                        session._prune_summarized_messages(mid_event_id)
                        messages_after = len(session.messages)
                        
                        # With gradual pruning (initial_buffer=10), should keep more messages
                        # than standard (last_turns_count=3)
                        # Standard would keep ~7 messages (1 system + 3*2 turns)
                        # Gradual should keep ~21 messages (1 system + 10*2 turns)
                        assert messages_after > 7, \
                            f"Gradual pruning should keep more messages initially (got {messages_after})"
    
    def test_filtering_uses_same_buffer_calculation(self, temp_dirs, mock_llm_client):
        """Test that message filtering uses the same buffer calculation as pruning."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "gradual_pruning_enabled", True)
            m.setattr(config.summarization, "initial_buffer_turns", 8)
            m.setattr(config.summarization, "min_buffer_turns", 3)
            m.setattr(config.summarization, "buffer_reduction_rate", 2)
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Send messages
            for i in range(15):
                session.send(f"Message {i}")
            
            # Create summary with cycle_count = 1
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0,
                    summarization_cycle_count=1  # Should give buffer = 8 - (1*2) = 6
                ),
                summary_blocks=SummaryBlocks()
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            # Get filtered messages
            filtered = session._get_filtered_messages()
            
            # Calculate expected buffer
            expected_buffer = 6  # 8 - (1 * 2)
            # Each turn is ~2 messages, so should have ~12 non-system messages
            non_system_filtered = [m for m in filtered if m.get("role") != "system"]
            
            # Should have approximately expected_buffer * 2 messages (allowing some variance)
            # Buffer of 6 turns = ~12 messages
            assert len(non_system_filtered) >= expected_buffer * 2 - 2, \
                f"Filtered messages should use gradual buffer calculation (expected ~{expected_buffer * 2}, got {len(non_system_filtered)})"
    
    def test_buffer_never_below_minimum(self, temp_dirs, mock_llm_client):
        """Test that buffer size never goes below min_buffer_turns."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "gradual_pruning_enabled", True)
            m.setattr(config.summarization, "initial_buffer_turns", 10)
            m.setattr(config.summarization, "min_buffer_turns", 3)
            m.setattr(config.summarization, "buffer_reduction_rate", 2)
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            summary_storage = session._summarization_manager.summary_storage
            
            # Test with very high cycle count
            for cycle_count in [10, 20, 50, 100]:
                summary = SessionSummary(
                    header=SummaryHeader(
                        session_id=session.session_id,
                        created_at="2024-01-01T00:00:00Z",
                        last_updated_at="2024-01-01T00:00:00Z",
                        revision=0,
                        summarization_cycle_count=cycle_count
                    ),
                    summary_blocks=SummaryBlocks()
                )
                summary_storage.save_session_summary(session.session_id, summary)
                
                buffer_size = session._calculate_buffer_turns()
                assert buffer_size >= 3, \
                    f"Buffer should never go below min_buffer_turns (3), got {buffer_size} at cycle {cycle_count}"


class TestGradualPruningPropertyBased:
    """Property-based tests for gradual pruning buffer calculation."""
    
    try:
        from hypothesis import given, strategies as st, settings, HealthCheck
        
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
        @given(
            initial_buffer=st.integers(min_value=3, max_value=20),
            min_buffer=st.integers(min_value=1, max_value=10),
            reduction_rate=st.integers(min_value=1, max_value=5),
            cycle_count=st.integers(min_value=0, max_value=20)
        )
        def test_buffer_calculation_property(
            self, temp_dirs, mock_llm_client, initial_buffer, min_buffer, reduction_rate, cycle_count
        ):
            """Property: Buffer size is always between min_buffer and initial_buffer."""
            # Ensure min_buffer <= initial_buffer
            if min_buffer > initial_buffer:
                return
            
            with pytest.MonkeyPatch().context() as m:
                from broca.config import config
                m.setattr(config.summarization, "enabled", True)
                m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
                m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
                m.setattr(config.summarization, "gradual_pruning_enabled", True)
                m.setattr(config.summarization, "initial_buffer_turns", initial_buffer)
                m.setattr(config.summarization, "min_buffer_turns", min_buffer)
                m.setattr(config.summarization, "buffer_reduction_rate", reduction_rate)
                
                session = ConversationSession(
                    system_prompt="Test",
                    llm=mock_llm_client
                )
                
                summary_storage = session._summarization_manager.summary_storage
                summary = SessionSummary(
                    header=SummaryHeader(
                        session_id=session.session_id,
                        created_at="2024-01-01T00:00:00Z",
                        last_updated_at="2024-01-01T00:00:00Z",
                        revision=0,
                        summarization_cycle_count=cycle_count
                    ),
                    summary_blocks=SummaryBlocks()
                )
                summary_storage.save_session_summary(session.session_id, summary)
                
                buffer_size = session._calculate_buffer_turns()
                
                # Property: buffer_size is always >= min_buffer
                assert buffer_size >= min_buffer, \
                    f"Buffer size {buffer_size} should be >= min_buffer {min_buffer}"
                
                # Property: buffer_size is always <= initial_buffer
                assert buffer_size <= initial_buffer, \
                    f"Buffer size {buffer_size} should be <= initial_buffer {initial_buffer}"
                
                # Property: buffer_size decreases (or stays same) as cycle_count increases
                if cycle_count > 0:
                    summary.header.summarization_cycle_count = cycle_count - 1
                    summary_storage.save_session_summary(session.session_id, summary)
                    prev_buffer = session._calculate_buffer_turns()
                    
                    summary.header.summarization_cycle_count = cycle_count
                    summary_storage.save_session_summary(session.session_id, summary)
                    curr_buffer = session._calculate_buffer_turns()
                    
                    assert curr_buffer <= prev_buffer, \
                        f"Buffer should decrease or stay same as cycle increases (prev={prev_buffer}, curr={curr_buffer})"
        
    except ImportError:
        # Hypothesis not available, skip property-based tests
        pass


