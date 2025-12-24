"""
Tests for message filtering in sessions when summarization is enabled.

Tests that only last K turns are sent to LLM when summaries exist.
"""

from __future__ import annotations

import tempfile
from unittest.mock import Mock
import pytest

from broca.repl.session import ConversationSession
from broca.llm.deepseek_client import DeepSeekClient
from broca.tests.utils import build_llm_response
from broca.summarization.models import SessionSummary, SummaryHeader, SummaryBlocks


@pytest.fixture
def temp_dirs():
    """Temporary directories for event logs and summaries."""
    with tempfile.TemporaryDirectory() as event_dir, tempfile.TemporaryDirectory() as summary_dir:
        yield {"event": event_dir, "summary": summary_dir}


@pytest.fixture
def mock_llm_client():
    """Mock LLM client that captures messages."""
    client = Mock(spec=DeepSeekClient)
    client.extract_assistant_content = Mock(return_value="Response")
    client.extract_tool_calls = Mock(return_value=[])
    client.chat.return_value = build_llm_response(content="Response")
    client.chat_stream = Mock(return_value=iter([]))
    return client


class TestMessageFiltering:
    """Test that messages are filtered when summarization is enabled."""
    
    def test_messages_filtered_when_summary_exists(self, temp_dirs, mock_llm_client):
        """Test that only last K turns are sent when summary exists."""
        captured_messages = []
        
        def capture_messages(*args, **kwargs):
            if "messages" in kwargs:
                captured_messages.append(kwargs["messages"].copy())
            elif len(args) > 0:
                captured_messages.append(args[0].copy())
            return build_llm_response(content="Response")
        
        mock_llm_client.chat.side_effect = capture_messages
        
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            m.setattr(config.summarization, "last_turns_count", 2)  # Last 2 turns
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Create a summary so filtering is enabled
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
            
            # Send multiple messages to build up history
            for i in range(5):
                session.send(f"Message {i}")
            
            # Check that captured messages were filtered
            # Should have system message + only last 2 turns (4 messages: user, assistant, user, assistant)
            if captured_messages:
                # Get the last call (most recent)
                last_messages = captured_messages[-1]
                # Should have system + last 2 turns = 1 + 4 = 5 messages max
                assert len(last_messages) <= 5, f"Expected <= 5 messages, got {len(last_messages)}"
                
                # Verify it's not the full history (which would be much longer)
                # Full history would be: system + 5 turns * 2 = 11 messages
                assert len(last_messages) < 11, "Messages were not filtered, full history was sent"
    
    def test_full_history_kept_in_session(self, temp_dirs, mock_llm_client):
        """Test that full history is still kept in session.messages."""
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Create a summary
            summary_storage = session._summarization_manager.summary_storage
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session.session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0
                ),
                summary_blocks=SummaryBlocks()
            )
            summary_storage.save_session_summary(session.session_id, summary)
            
            # Send multiple messages
            for i in range(5):
                session.send(f"Message {i}")
            
            # Full history should still be in session.messages
            # Should have: system + 5 turns * 2 = 11 messages
            assert len(session.messages) >= 10  # At least system + user/assistant pairs
    
    def test_no_filtering_when_no_summary(self, temp_dirs, mock_llm_client):
        """Test that full history is sent when no summary exists."""
        captured_messages = []
        
        def capture_messages(*args, **kwargs):
            if "messages" in kwargs:
                captured_messages.append(kwargs["messages"].copy())
            elif len(args) > 0:
                captured_messages.append(args[0].copy())
            return build_llm_response(content="Response")
        
        mock_llm_client.chat.side_effect = capture_messages
        
        with pytest.MonkeyPatch().context() as m:
            from broca.config import config
            m.setattr(config.summarization, "enabled", True)
            m.setattr(config.summarization, "event_log_path", temp_dirs["event"])
            m.setattr(config.summarization, "summary_path", temp_dirs["summary"])
            
            session = ConversationSession(
                system_prompt="Test",
                llm=mock_llm_client
            )
            
            # Don't create a summary - should send full history
            # Send a few messages
            for i in range(3):
                session.send(f"Message {i}")
            
            # Should send full history (no summary to filter against)
            if captured_messages:
                last_messages = captured_messages[-1]
                # Should have system + 3 turns = 7 messages
                assert len(last_messages) >= 6  # At least system + user/assistant pairs





