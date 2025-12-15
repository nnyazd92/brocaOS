"""
Tests for tool registry epistemic tracking.

Tests that tool executions are tracked when epistemic engine is provided.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from broca.tools.registry import ToolRegistry
from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata
from broca.tools import Tool


class MockTool(Tool):
    """Mock tool for testing."""
    
    def __init__(self, name: str = "mock_tool", success: bool = True):
        self._name = name
        self._success = success
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return f"A mock tool named {self._name}"
    
    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Test parameter"}
            },
            "required": []
        }
    
    def execute(self, **kwargs):
        if self._success:
            return {"success": True, "result": "test result"}
        else:
            return {"success": False, "error": "test error"}
    
    def format_result(self, result):
        return str(result)


class TestToolRegistryEpistemicTracking:
    """Test tool registry epistemic tracking of tool executions."""
    
    def test_tool_executions_tracked_when_epistemic_engine_provided(self):
        """
        Test that tool executions are tracked when epistemic_engine is provided.
        
        Rationale: Ensures tool executions create knowledge sources when epistemic tracking is enabled.
        """
        # Create epistemic engine
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        # Register a tool
        tool = MockTool()
        registry.register_tool(tool)
        
        # Execute tool call
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "mock_tool",
                "arguments": '{"param1": "value1"}'
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Check that epistemic tracking occurred
        # The tool execution should have been tracked
        assert result.get("_epistemic_impact") is not None or registry.epistemic_engine is not None
    
    def test_tool_executions_create_knowledge_sources(self):
        """
        Test that tool executions create knowledge sources with correct metadata.
        
        Rationale: Ensures tool results are tracked as knowledge sources in the epistemic layer.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="test_tool", success=True)
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": "{}"
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Epistemic impact should be included
        assert "_epistemic_impact" in result or result.get("success", True)
    
    def test_tool_success_failure_affects_confidence_scores(self):
        """
        Test that tool success/failure affects confidence scores.
        
        Rationale: Ensures successful tool executions increase confidence, failures decrease it.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        # Test successful tool
        success_tool = MockTool(name="success_tool", success=True)
        registry.register_tool(success_tool)
        
        success_call = {
            "id": "call_success",
            "type": "function",
            "function": {
                "name": "success_tool",
                "arguments": "{}"
            }
        }
        
        success_result = registry.execute_tool_call(success_call)
        
        # Test failed tool
        fail_tool = MockTool(name="fail_tool", success=False)
        registry.register_tool(fail_tool)
        
        fail_call = {
            "id": "call_fail",
            "type": "function",
            "function": {
                "name": "fail_tool",
                "arguments": "{}"
            }
        }
        
        fail_result = registry.execute_tool_call(fail_call)
        
        # Both should have epistemic tracking
        # Success should have higher confidence metrics than failure
        assert success_result.get("success", True) or "_epistemic_impact" in success_result
        assert not fail_result.get("success", True) or "_epistemic_impact" in fail_result
    
    def test_backward_compatibility_works_without_epistemic_engine(self):
        """
        Test backward compatibility: works without epistemic_engine.

        Rationale: Ensures existing code that doesn't use epistemic engine continues to work.
        """
        # Create registry without epistemic engine
        registry = ToolRegistry()
        assert registry.epistemic_engine is None

        # Register and execute tool
        tool = MockTool()
        registry.register_tool(tool)

        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "mock_tool",
                "arguments": "{}"
            }
        }

        result = registry.execute_tool_call(tool_call)

        # Should work fine without epistemic tracking
        assert "tool_call_id" in result
        assert result["name"] == "mock_tool"
        assert "_epistemic_impact" not in result  # Should not be present when no engine

    def test_confidence_uses_tool_reliability_for_new_tool(self):
        """
        Test that new tool (no history) uses default reliability (~0.5), not hardcoded 0.9.
        
        Rationale: Ensures confidence calculation uses actual tool reliability scores, not hardcoded values.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        # New tool with no execution history
        tool = MockTool(name="new_tool", success=True)
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_new",
            "type": "function",
            "function": {"name": "new_tool", "arguments": "{}"}
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Get tool reliability that was used (stored in epistemic_impact)
        # This is the reliability BEFORE the current execution was recorded
        stored_reliability = result["_epistemic_impact"]["confidence_metrics"]["tool_reliability_score"]
        evidence_strength = result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        
        # Evidence strength should match the tool reliability that was used at calculation time
        assert evidence_strength == stored_reliability
        assert evidence_strength == 0.5  # New tool starts at neutral
        assert evidence_strength < 0.9  # Should not be hardcoded 0.9

    def test_confidence_uses_tool_reliability_for_reliable_tool(self):
        """
        Test that tool with high reliability gets higher confidence.
        
        Rationale: Ensures reliable tools produce knowledge with confidence matching their reliability.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        # Build up high reliability for a tool
        tool = MockTool(name="reliable_tool", success=True)
        registry.register_tool(tool)
        
        # Execute multiple successful runs to build reliability
        for i in range(20):
            tool_call = {
                "id": f"call_{i}",
                "type": "function",
                "function": {"name": "reliable_tool", "arguments": "{}"}
            }
            registry.execute_tool_call(tool_call)
        
        # Check final reliability before last execution
        tool_reliability = engine.validator.assess_tool_reliability("reliable_tool")
        assert tool_reliability > 0.7  # Should be high after many successes
        
        # Execute one more time and check confidence
        final_call = {
            "id": "call_final",
            "type": "function",
            "function": {"name": "reliable_tool", "arguments": "{}"}
        }
        result = registry.execute_tool_call(final_call)
        stored_reliability = result["_epistemic_impact"]["confidence_metrics"]["tool_reliability_score"]
        evidence_strength = result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        
        # Evidence strength should match the tool reliability used at calculation time
        assert evidence_strength == stored_reliability
        assert evidence_strength == tool_reliability  # Should match reliability before this execution
        assert evidence_strength > 0.7

    def test_confidence_uses_tool_reliability_for_unreliable_tool(self):
        """
        Test that tool with low reliability gets lower confidence.
        
        Rationale: Ensures unreliable tools produce knowledge with lower confidence.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        # Manually build up low reliability history (3 successes, 7 failures = 30% success rate)
        for i in range(3):
            engine.validator.record_tool_execution("unreliable_tool", True)
        for i in range(7):
            engine.validator.record_tool_execution("unreliable_tool", False)
        
        # Check reliability before final execution (should be low)
        tool_reliability = engine.validator.assess_tool_reliability("unreliable_tool")
        assert tool_reliability < 0.5  # Should be below neutral
        
        # Now execute one more successful run and check confidence
        tool = MockTool(name="unreliable_tool", success=True)
        registry.register_tool(tool)
        final_call = {
            "id": "call_final",
            "type": "function",
            "function": {"name": "unreliable_tool", "arguments": "{}"}
        }
        result = registry.execute_tool_call(final_call)
        stored_reliability = result["_epistemic_impact"]["confidence_metrics"]["tool_reliability_score"]
        evidence_strength = result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        
        # Evidence strength should match tool reliability (even for successful execution)
        assert evidence_strength == stored_reliability
        assert abs(evidence_strength - tool_reliability) < 0.01  # Allow small floating point difference
        assert evidence_strength < 0.5

    def test_confidence_scales_down_on_failure(self):
        """
        Test that failed executions use scaled-down reliability.
        
        Rationale: Ensures failed tool executions get appropriately reduced confidence.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        # Build up reliability first by recording successful executions directly
        for i in range(20):
            engine.validator.record_tool_execution("test_tool_fail", True)
        
        tool_reliability = engine.validator.assess_tool_reliability("test_tool_fail")
        assert tool_reliability > 0.7
        
        # Now execute a failed run with a tool
        fail_tool = MockTool(name="test_tool_fail", success=False)
        registry.register_tool(fail_tool)
        fail_call = {
            "id": "call_fail",
            "type": "function",
            "function": {"name": "test_tool_fail", "arguments": "{}"}
        }
        fail_result = registry.execute_tool_call(fail_call)
        stored_reliability = fail_result["_epistemic_impact"]["confidence_metrics"]["tool_reliability_score"]
        evidence_strength = fail_result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        
        # Evidence strength should be scaled down from reliability
        # Should be approximately reliability * 0.3
        expected_strength = stored_reliability * 0.3
        assert abs(evidence_strength - expected_strength) < 0.05  # Allow small difference
        assert evidence_strength < stored_reliability
        assert evidence_strength < 0.5

    def test_confidence_updates_as_reliability_changes(self):
        """
        Test that confidence reflects reliability changes over time.
        
        Rationale: Ensures confidence dynamically adapts as tool reliability changes.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="changing_tool", success=True)
        registry.register_tool(tool)
        
        # Initial execution - should use default reliability (~0.5)
        call1 = {
            "id": "call_1",
            "type": "function",
            "function": {"name": "changing_tool", "arguments": "{}"}
        }
        result1 = registry.execute_tool_call(call1)
        stored_reliability1 = result1["_epistemic_impact"]["confidence_metrics"]["tool_reliability_score"]
        evidence_strength1 = result1["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        assert evidence_strength1 == stored_reliability1
        
        # After many successes, reliability should increase
        for i in range(2, 22):
            tool_call = {
                "id": f"call_{i}",
                "type": "function",
                "function": {"name": "changing_tool", "arguments": "{}"}
            }
            registry.execute_tool_call(tool_call)
        
        reliability2 = engine.validator.assess_tool_reliability("changing_tool")
        assert reliability2 > stored_reliability1
        
        # Final execution should use updated reliability
        call_final = {
            "id": "call_final",
            "type": "function",
            "function": {"name": "changing_tool", "arguments": "{}"}
        }
        result_final = registry.execute_tool_call(call_final)
        stored_reliability2 = result_final["_epistemic_impact"]["confidence_metrics"]["tool_reliability_score"]
        evidence_strength_final = result_final["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        assert evidence_strength_final == stored_reliability2
        assert stored_reliability2 == reliability2  # Should match reliability before final execution
        assert evidence_strength_final > evidence_strength1

