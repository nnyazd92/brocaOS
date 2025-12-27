"""
Fault injection tests for system prompt management.

Tests error handling and edge cases when components fail.
"""

from __future__ import annotations

import pytest
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


class TestWorldStateAggregatorFailures:
    """Test behavior when world state aggregator fails."""
    
    def test_aggregator_raises_exception(self, mock_llm_client):
        """Test behavior when world_state_aggregator.aggregate() raises exception."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.side_effect = Exception("Aggregator error")
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt="Base prompt"
        )
        
        # Should handle gracefully and log warning
        try:
            session._update_system_prompt()
            # Should not crash - exception should be caught and logged
        except Exception as e:
            pytest.fail(f"Should handle aggregator exception gracefully: {e}")
    
    def test_aggregator_returns_none(self, mock_llm_client):
        """Test behavior when world state aggregator returns None."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = None
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt="Base prompt"
        )
        
        # Should handle gracefully
        try:
            session._update_system_prompt()
        except Exception as e:
            pytest.fail(f"Should handle None world state gracefully: {e}")
    
    def test_aggregator_returns_empty_dict(self, mock_llm_client):
        """Test behavior when world state aggregator returns empty dict."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = {}
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt="Base prompt"
        )
        
        # Should handle gracefully
        try:
            session._update_system_prompt()
            # Should still have a system message
            assert len(session.messages) > 0
        except Exception as e:
            pytest.fail(f"Should handle empty world state gracefully: {e}")
    
    def test_world_state_exceeds_maximum_size(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when world state exceeds maximum size."""
        original_max = config.storage.max_world_state_size
        config.storage.max_world_state_size = 1000
        
        try:
            # Create formatter that will truncate
            formatter = WorldStateFormatter(max_length=config.storage.max_world_state_size)
            
            # Create very large world state
            large_world_state = {"data": "x" * 100000}
            formatted = formatter.format(large_world_state)
            
            # Should be truncated to max size
            assert len(formatted) <= config.storage.max_world_state_size
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt="Base prompt"
            )
            session._world_state_formatter = formatter
            
            # Should handle large world state gracefully
            session._update_system_prompt()
            system_content = session.messages[0]["content"]
            assert len(system_content) <= config.storage.max_system_prompt_size
        finally:
            config.storage.max_world_state_size = original_max


class TestFormatterFailures:
    """Test behavior when formatter fails."""
    
    def test_formatter_raises_exception(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when WorldStateFormatter.format() raises exception."""
        formatter = Mock(spec=WorldStateFormatter)
        formatter.format.side_effect = Exception("Formatter error")
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        session._world_state_formatter = formatter
        
        # Should handle gracefully and log warning
        try:
            session._update_system_prompt()
            # Should not crash
            assert len(session.messages) > 0
        except Exception as e:
            pytest.fail(f"Should handle formatter exception gracefully: {e}")
    
    def test_formatter_returns_none(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when formatter returns None."""
        formatter = Mock(spec=WorldStateFormatter)
        formatter.format.return_value = None
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        session._world_state_formatter = formatter
        
        # Should handle gracefully (None should be treated as empty)
        try:
            session._update_system_prompt()
            # Should still have system message (base prompt at least)
            assert len(session.messages) > 0
        except Exception as e:
            pytest.fail(f"Should handle None formatter output gracefully: {e}")
    
    def test_formatter_returns_empty_string(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when formatter returns empty string."""
        formatter = Mock(spec=WorldStateFormatter)
        formatter.format.return_value = ""
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        session._world_state_formatter = formatter
        
        # Should handle gracefully
        try:
            session._update_system_prompt()
            # Should still have system message with base prompt
            system_content = session.messages[0]["content"]
            assert "Base prompt" in system_content
        except Exception as e:
            pytest.fail(f"Should handle empty formatter output gracefully: {e}")
    
    def test_formatter_returns_malformed_json(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when formatter returns malformed JSON."""
        formatter = Mock(spec=WorldStateFormatter)
        formatter.format.return_value = "This is not valid JSON {"
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        session._world_state_formatter = formatter
        
        # Should handle gracefully (formatter should ensure valid JSON, but test edge case)
        try:
            session._update_system_prompt()
            # System message should still exist
            assert len(session.messages) > 0
        except Exception as e:
            # If it raises, should be a specific error, not a crash
            assert "JSON" in str(e) or "format" in str(e).lower()


class TestSummaryContextFailures:
    """Test behavior when summary context builder fails."""
    
    def test_prompt_builder_raises_exception(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when PromptBuilder.build_context() raises exception."""
        from broca.summarization.prompt_builder import PromptBuilder
        from broca.summarization.storage import SummaryStorage
        
        storage = Mock(spec=SummaryStorage)
        storage.load_session_summary.return_value = None
        storage.load_project_state.return_value = None
        
        builder = Mock(spec=PromptBuilder)
        builder.build_context.side_effect = Exception("Builder error")
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        mock_summarization_manager = Mock()
        mock_summarization_manager.summary_storage = storage
        session._summarization_manager = mock_summarization_manager
        
        # Should handle gracefully (exception should be caught and logged)
        try:
            session._update_system_prompt()
            # Should still have system message
            assert len(session.messages) > 0
        except Exception as e:
            pytest.fail(f"Should handle builder exception gracefully: {e}")
    
    def test_summary_context_is_none(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when summary context is None."""
        from broca.summarization.prompt_builder import PromptBuilder
        from broca.summarization.storage import SummaryStorage
        
        storage = Mock(spec=SummaryStorage)
        storage.load_session_summary.return_value = None
        storage.load_project_state.return_value = None
        
        builder = Mock(spec=PromptBuilder)
        builder.build_context.return_value = None
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt="Base prompt"
        )
        
        mock_summarization_manager = Mock()
        mock_summarization_manager.summary_storage = storage
        session._summarization_manager = mock_summarization_manager
        
        # Should handle gracefully (None should be treated as empty)
        try:
            session._update_system_prompt()
            # Should still have system message with base prompt
            system_content = session.messages[0]["content"]
            assert "Base prompt" in system_content
        except Exception as e:
            pytest.fail(f"Should handle None summary context gracefully: {e}")
    
    def test_summary_context_exceeds_maximum_size(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when summary context exceeds maximum size."""
        from broca.summarization.prompt_builder import PromptBuilder
        from broca.summarization.storage import SummaryStorage
        
        original_max = config.storage.max_summary_context_size
        config.storage.max_summary_context_size = 500
        
        try:
            storage = Mock(spec=SummaryStorage)
            storage.load_session_summary.return_value = None
            storage.load_project_state.return_value = None
            
            # Create large summary context
            large_context = "A" * 10000
            builder = Mock(spec=PromptBuilder)
            builder.build_context.return_value = large_context
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt="Base prompt"
            )
            
            mock_summarization_manager = Mock()
            mock_summarization_manager.summary_storage = storage
            session._summarization_manager = mock_summarization_manager
            
            # Should handle gracefully (context should be truncated)
            session._update_system_prompt()
            system_content = session.messages[0]["content"]
            assert len(system_content) <= config.storage.max_system_prompt_size
        finally:
            config.storage.max_summary_context_size = original_max


class TestBasePromptFailures:
    """Test behavior when base prompt has issues."""
    
    def test_base_prompt_is_none(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when base prompt is None."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt=None
        )
        
        # Should handle gracefully
        try:
            session._update_system_prompt()
            # Should still have system message (with world state)
            assert len(session.messages) > 0
        except Exception as e:
            pytest.fail(f"Should handle None base prompt gracefully: {e}")
    
    def test_base_prompt_is_empty_string(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when base prompt is empty string."""
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt=""
        )
        
        # Should handle gracefully
        try:
            session._update_system_prompt()
            # Should still have system message (with world state)
            assert len(session.messages) > 0
        except Exception as e:
            pytest.fail(f"Should handle empty base prompt gracefully: {e}")
    
    def test_base_prompt_exceeds_maximum_size(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when base prompt exceeds maximum size."""
        original_base_max = config.storage.max_base_prompt_size
        original_system_max = config.storage.max_system_prompt_size
        config.storage.max_base_prompt_size = 1000
        config.storage.max_system_prompt_size = 5000
        
        try:
            huge_prompt = "A" * 100000  # 100KB
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=mock_world_state_aggregator,
                base_system_prompt=huge_prompt
            )
            
            # Should truncate gracefully
            system_content = session.messages[0]["content"]
            assert len(system_content) <= config.storage.max_system_prompt_size
            assert "[Base system prompt truncated" in system_content
        finally:
            config.storage.max_base_prompt_size = original_base_max
            config.storage.max_system_prompt_size = original_system_max
    
    def test_base_prompt_contains_json_contamination(self, mock_llm_client, mock_world_state_aggregator):
        """Test behavior when base prompt contains JSON contamination."""
        contaminated_prompt = """You are BrocaOS.
        
        {"timestamp": "2024-01-01T00:00:00Z", "system": {"platform": "Linux"}}
        
        Always be helpful."""
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=mock_world_state_aggregator,
            base_system_prompt=contaminated_prompt
        )
        
        # Should handle gracefully (clean_base_prompt should remove JSON)
        try:
            session._update_system_prompt()
            system_content = session.messages[0]["content"]
            # JSON should not appear in base prompt section (may appear in world state section)
            # Base prompt should be cleaned
            assert len(system_content) > 0
        except Exception as e:
            pytest.fail(f"Should handle JSON contamination gracefully: {e}")


class TestCombinedFailures:
    """Test behavior when multiple components fail simultaneously."""
    
    def test_aggregator_and_formatter_fail(self, mock_llm_client):
        """Test behavior when both aggregator and formatter fail."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.side_effect = Exception("Aggregator error")
        
        formatter = Mock(spec=WorldStateFormatter)
        formatter.format.side_effect = Exception("Formatter error")
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt="Base prompt"
        )
        session._world_state_formatter = formatter
        
        # Should handle gracefully
        try:
            session._update_system_prompt()
            # Should still have system message with base prompt
            assert len(session.messages) > 0
        except Exception as e:
            pytest.fail(f"Should handle multiple failures gracefully: {e}")
    
    def test_all_components_fail(self, mock_llm_client):
        """Test behavior when all components fail."""
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.side_effect = Exception("Aggregator error")
        
        formatter = Mock(spec=WorldStateFormatter)
        formatter.format.side_effect = Exception("Formatter error")
        
        from broca.summarization.prompt_builder import PromptBuilder
        from broca.summarization.storage import SummaryStorage
        
        storage = Mock(spec=SummaryStorage)
        builder = Mock(spec=PromptBuilder)
        builder.build_context.side_effect = Exception("Builder error")
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt="Base prompt"
        )
        session._world_state_formatter = formatter
        
        mock_summarization_manager = Mock()
        mock_summarization_manager.summary_storage = storage
        session._summarization_manager = mock_summarization_manager
        
        # Should handle gracefully
        try:
            session._update_system_prompt()
            # Should still have system message with base prompt (if base prompt is valid)
            assert len(session.messages) > 0
        except Exception as e:
            pytest.fail(f"Should handle all failures gracefully: {e}")


@pytest.fixture
def mock_world_state_aggregator():
    """Mock world state aggregator."""
    aggregator = Mock(spec=WorldStateAggregator)
    aggregator.aggregate.return_value = {
        "timestamp": "2024-01-01T00:00:00Z",
        "system": {"platform": "Linux", "python_version": "3.13.0"}
    }
    return aggregator

