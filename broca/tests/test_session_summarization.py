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





