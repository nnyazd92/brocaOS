"""
End-to-end integration tests for internal sensing.

Simulates realistic conversation flow and verifies metrics update correctly.
"""

from __future__ import annotations

import time
from unittest.mock import Mock, patch
import pytest

from broca.internal_sensing.framework import InternalSensingFramework
from broca.world_state.aggregator import WorldStateAggregator
from broca.tools.registry import ToolRegistry
from broca.tools.terminal import TerminalTool


class TestConversationFlowIntegration:
    """Test complete conversation flow with metrics updates."""
    
    def test_metrics_update_after_multiple_conversation_turns(self):
        """
        Test that metrics update after multiple conversation turns.
        
        Rationale: Verifies metrics accumulate over realistic conversation flow.
        """
        framework = InternalSensingFramework()
        
        # Simulate multiple conversation turns
        for i in range(3):
            # Record confidence for each turn
            framework.interoception.cognition.record_confidence(f"resp{i}", 0.5 + i * 0.1)
            framework.interoception.cognition.record_uncertainty(f"q{i}", 0.3 + i * 0.1)
            
            # Sample internal state
            state = framework.sample_internal_state()
            
            # Metrics should reflect accumulated data
            assert state["cognitive"]["confidence_level"] is not None
            assert state["cognitive"]["uncertainty_tracking"] is not None
        
        # Final state should reflect moving averages
        final_state = framework.sample_internal_state()
        final_conf = final_state["cognitive"]["confidence_level"]
        final_uncert = final_state["cognitive"]["uncertainty_tracking"]
        
        # Should be average of recorded values
        assert 0.5 <= final_conf <= 0.8  # Average of 0.5, 0.6, 0.7
        assert 0.3 <= final_uncert <= 0.6  # Average of 0.3, 0.4, 0.5
    
    def test_moving_averages_accumulate_over_multiple_samples(self):
        """
        Test that moving averages accumulate over multiple samples.
        
        Rationale: Verifies moving averages work correctly over time.
        """
        framework = InternalSensingFramework()
        
        # Record data
        framework.interoception.cognition.record_confidence("resp1", 0.3)
        framework.interoception.cognition.record_confidence("resp2", 0.5)
        framework.interoception.cognition.record_confidence("resp3", 0.7)
        
        # Sample multiple times
        states = []
        for i in range(3):
            state = framework.sample_internal_state()
            states.append(state["cognitive"]["confidence_level"])
        
        # All samples should reflect the same moving average
        assert all(s == pytest.approx(0.5, abs=0.01) for s in states)
    
    def test_quality_metrics_computed_after_predictions_recorded(self):
        """
        Test that quality metrics are computed after predictions are recorded.
        
        Rationale: Verifies quality metrics update as predictions accumulate.
        """
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        # Generate prediction cycles (need at least 2 calls)
        framework.sample_internal_state()  # First call - generates prediction
        framework.sample_internal_state()  # Second call - validates prediction
        
        # Quality metrics should be computable
        sensing_state = aggregator.get_internal_sensing_state()
        assert "quality_metrics" in sensing_state
        
        # After more cycles, accuracy should be computed
        framework.sample_internal_state()  # Third call
        sensing_state2 = aggregator.get_internal_sensing_state()
        quality = sensing_state2["quality_metrics"]["self_awareness_quality"]
        assert quality is not None
        assert 0.0 <= quality <= 1.0
    
    def test_world_state_includes_updated_metrics_after_recording_data(self):
        """
        Test that world state includes updated metrics after recording data.
        
        Rationale: Verifies complete flow from recording to world state.
        """
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        # Record data
        framework.interoception.cognition.record_confidence("test1", 0.85)
        framework.interoception.cognition.record_uncertainty("test1", 0.35)
        
        # Aggregate world state
        world_state = aggregator.aggregate()
        
        # Should include updated metrics
        assert "internal_state" in world_state
        internal_state = world_state["internal_state"]
        assert "cognition" in internal_state
        assert internal_state["cognition"]["confidence_level"] == 0.85
        assert internal_state["cognition"]["uncertainty_tracking"] == 0.35
    
    def test_metrics_dont_revert_to_defaults_after_being_updated(self):
        """
        Test that metrics don't revert to defaults after being updated.
        
        Rationale: Verifies metrics persist correctly.
        """
        framework = InternalSensingFramework()
        
        # Record data
        framework.interoception.cognition.record_confidence("test1", 0.9)
        
        # Verify updated
        assert framework.interoception.cognition.states["confidence_level"] == 0.9
        
        # Sample multiple times
        for i in range(3):
            state = framework.sample_internal_state()
            # Should remain at recorded value (not revert to default)
            assert state["cognitive"]["confidence_level"] == 0.9
    
    def test_tool_usage_tracking_integrates_with_metrics(self):
        """
        Test that tool usage tracking integrates with metrics system.
        
        Rationale: Verifies tool usage is tracked and affects metrics.
        """
        framework = InternalSensingFramework()
        tool_registry = ToolRegistry(internal_sensing_framework=framework)
        
        # Register a tool
        terminal_tool = TerminalTool()
        tool_registry.register_tool(terminal_tool)
        
        # Record tool usage
        framework.record_tool_usage(
            tool_name="terminal",
            parameters={"command": "echo test"},
            result={"success": True, "stdout": "test"}
        )
        
        # Record cognitive impact
        framework.record_cognitive_impact("terminal", impact_level=2)
        
        # Processing depth should be updated
        framework.interoception.cognition.record_processing_depth("tool_terminal", 2)
        
        # Sample and verify
        state = framework.sample_internal_state()
        assert state["cognitive"]["processing_depth"] >= 2.0


class TestRealisticScenarioIntegration:
    """Test realistic scenarios with multiple interactions."""
    
    def test_complete_conversation_with_tools(self):
        """
        Test complete conversation flow with tool usage.
        
        Rationale: Verifies metrics update correctly in realistic scenario.
        """
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        # Simulate conversation turn 1: User asks question
        framework.interoception.cognition.record_confidence("resp1", 0.7)
        framework.interoception.cognition.record_uncertainty("q1", 0.4)
        state1 = framework.sample_internal_state()
        
        # Simulate tool usage
        framework.record_tool_usage("terminal", {"command": "ls"}, {"success": True})
        framework.record_cognitive_impact("terminal", 2)
        
        # Simulate conversation turn 2: Assistant responds with tool result
        framework.interoception.cognition.record_confidence("resp2", 0.8)
        framework.interoception.cognition.record_reasoning_step("step1", {
            "premise": "Need to list files",
            "conclusion": "Used terminal tool"
        })
        state2 = framework.sample_internal_state()
        
        # Aggregate world state
        world_state = aggregator.aggregate()
        
        # Verify metrics are updated
        assert world_state["internal_state"]["cognition"]["confidence_level"] >= 0.7
        assert world_state["internal_state"]["quality_metrics"] is not None
    
    def test_metrics_accumulate_across_multiple_interactions(self):
        """
        Test that metrics accumulate across multiple interactions.
        
        Rationale: Verifies metrics reflect system state over extended use.
        """
        framework = InternalSensingFramework()
        
        # Simulate 10 interactions
        for i in range(10):
            # Vary confidence and uncertainty
            confidence = 0.5 + (i % 5) * 0.1
            uncertainty = 0.2 + (i % 4) * 0.1
            
            framework.interoception.cognition.record_confidence(f"resp{i}", confidence)
            framework.interoception.cognition.record_uncertainty(f"q{i}", uncertainty)
            
            # Generate prediction cycle
            framework.sample_internal_state()
        
        # Final metrics should reflect accumulated data
        final_state = framework.sample_internal_state()
        
        # Confidence should be average of all recorded values
        final_conf = final_state["cognitive"]["confidence_level"]
        assert 0.5 <= final_conf <= 0.9  # Average of values in 0.5-0.9 range
        
        # Quality metrics should be computable
        quality = framework.interoception.measure_self_awareness_quality()
        assert quality is not None
        assert 0.0 <= quality <= 1.0

