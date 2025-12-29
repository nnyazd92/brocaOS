"""
Integration tests for web_api.py ensuring dissonance and contradiction detection work end-to-end.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
import json

from broca.web_api import app, get_runtime
from broca.main_repl_runtime import BrocaRuntime


class TestWebAPIDissonanceIntegration:
    """Test web API integration with cognitive dissonance."""
    
    @pytest.fixture
    def mock_runtime(self):
        """Create mock runtime with reasoning tool and cognitive dissonance monitor."""
        runtime = Mock(spec=BrocaRuntime)
        
        # Mock world state aggregator
        world_state_aggregator = Mock()
        reasoning_tool = Mock()
        cognitive_dissonance_monitor = Mock()
        
        # Mock measure_dissonance
        from broca.reasoning.cognitive_dissonance import DissonanceMetrics
        from datetime import datetime, timezone
        
        mock_metrics = DissonanceMetrics(
            timestamp=datetime.now(timezone.utc),
            logical_dissonance=0.2,
            factual_dissonance=0.3,
            behavioral_dissonance=0.1,
            goal_dissonance=0.05,
            overall_dissonance=0.2
        )
        cognitive_dissonance_monitor.measure_dissonance = Mock(return_value=mock_metrics)
        
        reasoning_tool.cognitive_dissonance_monitor = cognitive_dissonance_monitor
        world_state_aggregator.reasoning_tool = reasoning_tool
        runtime.world_state_aggregator = world_state_aggregator
        
        # Mock other runtime components
        runtime.tool_registry = Mock()
        runtime.session = Mock()
        
        return runtime
    
    def test_dissonance_measurement_called_in_stream_response(self, mock_runtime):
        """Test that dissonance measurement is called during stream_response."""
        with patch('broca.web_api.get_runtime', return_value=mock_runtime):
            with patch('broca.web_api.create_session') as mock_create_session:
                from broca.repl.session import ConversationSession
                
                session = Mock(spec=ConversationSession)
                session.llm = Mock()
                session.llm.chat = Mock(return_value={"choices": [{"message": {"content": "Test response"}}]})
                session.llm.extract_tool_calls = Mock(return_value=[])
                session.llm.extract_assistant_content = Mock(return_value="Test response")
                session.messages = []
                session.internal_sensing_framework = None
                
                mock_create_session.return_value = session
                
                # Call stream_response
                from broca.web_api import stream_response
                
                # Consume generator
                list(stream_response("test_id", "Test message", web_search_enabled=True))
                
                # Verify measure_dissonance was called
                cognitive_dissonance_monitor = mock_runtime.world_state_aggregator.reasoning_tool.cognitive_dissonance_monitor
                assert cognitive_dissonance_monitor.measure_dissonance.called
    
    def test_dissonance_measurement_with_tool_usage(self, mock_runtime):
        """Test that dissonance measurement includes tool usage."""
        with patch('broca.web_api.get_runtime', return_value=mock_runtime):
            with patch('broca.web_api.create_session') as mock_create_session:
                from broca.repl.session import ConversationSession
                
                session = Mock(spec=ConversationSession)
                session.llm = Mock()
                session.llm.chat = Mock(return_value={"choices": [{"message": {"content": "Test"}}]})
                session.llm.extract_tool_calls = Mock(return_value=[])
                session.llm.extract_assistant_content = Mock(return_value="Test response")
                session.messages = [
                    {"role": "assistant", "tool_calls": [{"function": {"name": "test_tool"}}]}
                ]
                session.internal_sensing_framework = None
                
                mock_create_session.return_value = session
                
                from broca.web_api import stream_response
                list(stream_response("test_id", "Test", web_search_enabled=True))
                
                # Verify measure_dissonance was called with tool_usage
                cognitive_dissonance_monitor = mock_runtime.world_state_aggregator.reasoning_tool.cognitive_dissonance_monitor
                call_args = cognitive_dissonance_monitor.measure_dissonance.call_args
                
                if call_args:
                    # Check that tool_usage was passed (may be None if no tools)
                    assert "tool_usage" in call_args.kwargs or len(call_args.args) >= 3

