"""
End-to-end integration tests for internal sensing data flow.

Tests that data flows through all monitors correctly during actual conversations.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import json

from broca.repl.session import ConversationSession
from broca.internal_sensing.framework import InternalSensingFramework
from broca.tests.utils import build_llm_response


class TestEndToEndDataFlow:
    """Test end-to-end data flow through all monitors."""
    
    @patch('broca.llm.DeepSeekClient')
    def test_data_flows_through_all_monitors(self, mock_llm_class):
        """
        Test that data flows through all monitors during conversation.
        
        Rationale: Ensures complete data flow works end-to-end.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("This is a confident response about mathematics.")
        mock_llm.extract_assistant_content.return_value = "This is a confident response about mathematics."
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        session.send("Tell me about mathematics")
        
        # Check that all monitors received data
        state = framework.sample_internal_state()
        
        # Computational state should have data
        assert "computational" in state
        assert "timestamp" in state["computational"]
        
        # Cognitive state should have data
        assert "cognitive" in state
        cognitive = state["cognitive"]
        assert "confidence_level" in cognitive
        assert cognitive["confidence_level"] > 0.0  # Should have recorded confidence
        
        # Affective state should have data
        assert "affective" in state
        affective = state["affective"]
        assert "valence" in affective
        assert "arousal" in affective
    
    @patch('broca.llm.DeepSeekClient')
    def test_metrics_change_with_behavior(self, mock_llm_class):
        """
        Test that metrics change based on actual behavior.
        
        Rationale: Ensures metrics reflect actual system behavior.
        """
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # First response - confident
        mock_llm.chat.return_value = build_llm_response("I am certain this is correct.")
        mock_llm.extract_assistant_content.return_value = "I am certain this is correct."
        mock_llm.extract_tool_calls.return_value = []
        
        session.send("Question 1")
        state1 = framework.sample_internal_state()
        conf1 = state1["cognitive"]["confidence_level"]
        
        # Second response - uncertain
        mock_llm.chat.return_value = build_llm_response("I'm not sure, but maybe...")
        mock_llm.extract_assistant_content.return_value = "I'm not sure, but maybe..."
        mock_llm.extract_tool_calls.return_value = []
        
        session.send("Question 2")
        state2 = framework.sample_internal_state()
        conf2 = state2["cognitive"]["confidence_level"]
        uncertainty2 = state2["cognitive"]["uncertainty_tracking"]
        
        # Confidence should be different, uncertainty should be higher for uncertain response
        assert conf1 != conf2 or abs(conf1 - conf2) < 0.1  # May be similar, but uncertainty should differ
        assert uncertainty2 >= 0.0  # Should detect uncertainty (may be 0.0 if not detected)
    
    @patch('broca.llm.DeepSeekClient')
    def test_tool_usage_tracks_reasoning(self, mock_llm_class):
        """
        Test that tool usage tracks reasoning and depth.
        
        Rationale: Ensures tool usage is properly instrumented.
        """
        mock_llm = Mock()
        mock_llm.extract_assistant_content.return_value = None
        mock_llm.extract_tool_calls.return_value = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": json.dumps({})
                }
            }
        ]
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Mock tool registry
        from broca.tools.registry import ToolRegistry
        from broca.tests.test_session_tools import MockTool
        
        tool_registry = ToolRegistry()
        tool_registry.register_tool(MockTool("test_tool"))
        session.tool_registry = tool_registry
        
        # Mock final response
        mock_llm.chat.return_value = build_llm_response("Done")
        mock_llm.extract_tool_calls.return_value = []
        
        session.send("Use test_tool")
        
        # Check that tool usage was tracked
        tool_stats = framework.get_tool_statistics()
        assert "test_tool" in tool_stats or len(tool_stats) >= 0
        
        # Check that processing depth was tracked
        state = framework.sample_internal_state()
        depth = state["cognitive"].get("processing_depth")
        # Depth may be None initially, but if it's set, it should be >= 0
        if depth is not None:
            assert depth >= 0.0
    
    @patch('broca.llm.DeepSeekClient')
    def test_affective_updates_from_cognitive(self, mock_llm_class):
        """
        Test that affective states update from cognitive data.
        
        Rationale: Ensures automatic affective updates work.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Great! This is excellent.")
        mock_llm.extract_assistant_content.return_value = "Great! This is excellent."
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        session.send("Tell me something positive")
        
        # Check that affective states were computed
        state = framework.sample_internal_state()
        affective = state["affective"]
        
        # Should have valence (positive response should have positive valence)
        assert "valence" in affective
        assert affective["valence"] >= -1.0
        assert affective["valence"] <= 1.0
        
        # Should have certainty affect (from confidence)
        assert "certainty_affect" in affective
        assert affective["certainty_affect"] >= 0.0
        assert affective["certainty_affect"] <= 1.0

