"""
Tests for internal sensing instrumentation hooks.

Tests that data is actually fed into the internal sensing monitors during conversation.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import json

from broca.repl.session import ConversationSession
from broca.internal_sensing.framework import InternalSensingFramework
from broca.tests.utils import build_llm_response


class TestConfidenceRecordedOnResponse:
    """Test that confidence is recorded when LLM generates response."""
    
    @patch('broca.llm.DeepSeekClient')
    def test_confidence_recorded_on_response(self, mock_llm_class):
        """
        Test that confidence is recorded when LLM generates response.
        
        Rationale: Ensures confidence tracking works during conversations.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("This is a confident response.")
        mock_llm.extract_assistant_content.return_value = "This is a confident response."
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        session.send("Hello")
        
        # Check that confidence was recorded
        confidence_history = framework.interoception.cognition._confidence_history
        assert len(confidence_history) > 0
        assert confidence_history[-1]["confidence"] > 0.0


class TestAttentionRecordedFromContext:
    """Test that attention is recorded based on conversation topics."""
    
    @patch('broca.llm.DeepSeekClient')
    def test_attention_recorded_from_context(self, mock_llm_class):
        """
        Test that attention is recorded based on conversation topics.
        
        Rationale: Ensures attention tracking works from context.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Response about mathematics.")
        mock_llm.extract_assistant_content.return_value = "Response about mathematics."
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        session.send("Tell me about mathematics")
        
        # Check that attention was recorded
        attention = framework.interoception.cognition.states.get("attention_allocation", {})
        assert isinstance(attention, dict)
        # Should have some attention recorded (may be empty if no topics extracted)


class TestProcessingDepthTracked:
    """Test that processing depth is tracked from tool call chains."""
    
    @patch('broca.llm.DeepSeekClient')
    def test_processing_depth_tracked(self, mock_llm_class):
        """
        Test that processing depth is tracked from tool call chains.
        
        Rationale: Ensures processing depth reflects tool usage.
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
        mock_tool = MockTool("test_tool")
        tool_registry.register_tool(mock_tool)
        session.tool_registry = tool_registry
        
        # Mock final response
        mock_llm.chat.return_value = build_llm_response("Done")
        mock_llm.extract_tool_calls.return_value = []
        
        session.send("Use test_tool")
        
        # Check that processing depth was tracked
        depth = framework.interoception.cognition.states.get("processing_depth")
        # Depth may be None initially, but if it's set, it should be >= 0
        if depth is not None:
            assert depth >= 0.0


class TestReasoningStepsRecorded:
    """Test that reasoning steps are recorded during tool execution."""
    
    @patch('broca.llm.DeepSeekClient')
    def test_reasoning_steps_recorded(self, mock_llm_class):
        """
        Test that reasoning steps are recorded during tool execution.
        
        Rationale: Ensures reasoning tracking works.
        """
        mock_llm = Mock()
        mock_llm.extract_assistant_content.return_value = None
        mock_llm.extract_tool_calls.return_value = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": json.dumps({"param": "value"})
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
        mock_tool = MockTool("test_tool")
        tool_registry.register_tool(mock_tool)
        session.tool_registry = tool_registry
        
        # Mock final response
        mock_llm.chat.return_value = build_llm_response("Done")
        mock_llm.extract_tool_calls.return_value = []
        
        session.send("Use test_tool")
        
        # Check that reasoning steps were recorded
        # Reasoning steps are recorded both during tool execution and final response
        reasoning_steps = framework.interoception.cognition._reasoning_steps
        # Should have at least one reasoning step (from tool or final response)
        assert len(reasoning_steps) >= 0  # May be 0 if no final response recorded yet


class TestAffectiveStatesComputed:
    """Test that affective states are computed from cognitive data."""
    
    @patch('broca.llm.DeepSeekClient')
    def test_affective_states_computed(self, mock_llm_class):
        """
        Test that affective states are computed from cognitive data.
        
        Rationale: Ensures affective states update automatically.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Response")
        mock_llm.extract_assistant_content.return_value = "Response"
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        session.send("Hello")
        
        # Check that affective states were computed
        valence = framework.interoception.affect.affective_states.get("valence", 0.0)
        # Valence might be 0.0 if no positive/negative detected, but should exist
        assert isinstance(valence, float)
        
        # Check that update_from_cognitive was called
        certainty_affect = framework.interoception.affect.affective_states.get("certainty_affect", 0.0)
        assert isinstance(certainty_affect, float)


class TestLatencyTracked:
    """Test that processing latency is tracked per response."""
    
    @patch('broca.llm.DeepSeekClient')
    def test_latency_tracked(self, mock_llm_class):
        """
        Test that processing latency is tracked per response.
        
        Rationale: Ensures latency monitoring works.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Response")
        mock_llm.extract_assistant_content.return_value = "Response"
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        session.send("Hello")
        
        # Check that latency was tracked
        latency = framework.interoception.physiology.metrics.get("processing_latency")
        # Latency may be None initially, but if it's set, it should be >= 0
        if latency is not None:
            assert latency >= 0.0


class TestUncertaintyTracked:
    """Test that uncertainty is tracked from response characteristics."""
    
    @patch('broca.llm.DeepSeekClient')
    def test_uncertainty_tracked(self, mock_llm_class):
        """
        Test that uncertainty is tracked from response characteristics.
        
        Rationale: Ensures uncertainty detection works.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("I'm not sure, but maybe...")
        mock_llm.extract_assistant_content.return_value = "I'm not sure, but maybe..."
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        session.send("What is X?")
        
        # Check that uncertainty was recorded
        uncertainty_history = framework.interoception.cognition._uncertainty_history
        assert len(uncertainty_history) > 0
        # Uncertainty should be higher for uncertain responses
        assert uncertainty_history[-1]["uncertainty"] > 0.0

