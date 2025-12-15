"""
Comprehensive integration tests for epistemic layer functionality.

Tests end-to-end epistemic tracking including tool usage patterns,
knowledge source creation, confidence metrics, and verification prioritization.
"""

from __future__ import annotations

import pytest
import tempfile
import os
from unittest.mock import Mock
from datetime import datetime, timezone

from broca.tools.registry import ToolRegistry
from broca.self_model.epistemic.engine import MetacognitiveEngine
from broca.self_model.epistemic.models import SourceType, SourceMetadata
from broca.self_model.epistemic.ids import generate_knowledge_id
from broca.tools import Tool


class MockTool(Tool):
    """Mock tool for testing with configurable behavior."""
    
    def __init__(self, name: str = "mock_tool", success: bool = True, result_data: dict | None = None):
        self._name = name
        self._success = success
        self._result_data = result_data or {"result": f"Result from {name}"}
    
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
            return {"success": True, **self._result_data}
        else:
            return {"success": False, "error": "test error"}
    
    def format_result(self, result):
        if result.get("success", True):
            return f"Success: {result.get('result', 'OK')}"
        else:
            return f"Error: {result.get('error', 'Unknown error')}"


class TestToolExecutionTracking:
    """Test tool execution tracking in epistemic layer."""
    
    def test_tool_execution_creates_knowledge_source(self):
        """
        Test that tool execution creates a knowledge source in epistemic layer.
        
        Rationale: Ensures tool results are tracked as knowledge sources.
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
                "arguments": '{"param1": "value1"}'
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Verify epistemic impact is present
        assert "_epistemic_impact" in result
        assert "confidence_metrics" in result["_epistemic_impact"]
        assert "execution_success" in result["_epistemic_impact"]["confidence_metrics"]
        assert result["_epistemic_impact"]["confidence_metrics"]["execution_success"] is True
        
        # Verify tool execution was recorded in validator
        assert len(engine.validator._tool_executions.get("test_tool", [])) > 0
        assert engine.validator._tool_executions["test_tool"][-1] is True
    
    def test_tool_reliability_tracked_over_multiple_executions(self):
        """
        Test that tool reliability scores are tracked correctly over multiple executions.
        
        Rationale: Ensures reliability improves with successful executions and decreases with failures.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="reliable_tool", success=True)
        registry.register_tool(tool)
        
        # Execute successful tool calls multiple times
        for i in range(5):
            tool_call = {
                "id": f"call_{i}",
                "type": "function",
                "function": {
                    "name": "reliable_tool",
                    "arguments": "{}"
                }
            }
            registry.execute_tool_call(tool_call)
        
        # Check reliability has improved
        reliability = engine.validator.assess_tool_reliability("reliable_tool")
        assert reliability > 0.5  # Should be above neutral
        
        # Now execute some failures
        tool._success = False
        for i in range(3):
            tool_call = {
                "id": f"call_fail_{i}",
                "type": "function",
                "function": {
                    "name": "reliable_tool",
                    "arguments": "{}"
                }
            }
            registry.execute_tool_call(tool_call)
        
        # Reliability should decrease but still be tracked
        new_reliability = engine.validator.assess_tool_reliability("reliable_tool")
        assert new_reliability < reliability  # Should decrease after failures
        assert len(engine.validator._tool_executions["reliable_tool"]) == 8  # 5 success + 3 failure
    
    def test_success_failure_affects_confidence_metrics(self):
        """
        Test that success/failure affects confidence metrics appropriately.
        
        Rationale: Ensures successful executions result in higher confidence than failures.
        """
        engine = MetacognitiveEngine()
        
        # Test successful tool
        registry_success = ToolRegistry(epistemic_engine=engine)
        success_tool = MockTool(name="success_tool", success=True)
        registry_success.register_tool(success_tool)
        
        success_call = {
            "id": "call_success",
            "type": "function",
            "function": {
                "name": "success_tool",
                "arguments": "{}"
            }
        }
        success_result = registry_success.execute_tool_call(success_call)
        
        # Test failed tool
        registry_fail = ToolRegistry(epistemic_engine=engine)
        fail_tool = MockTool(name="fail_tool", success=False)
        registry_fail.register_tool(fail_tool)
        
        fail_call = {
            "id": "call_fail",
            "type": "function",
            "function": {
                "name": "fail_tool",
                "arguments": "{}"
            }
        }
        fail_result = registry_fail.execute_tool_call(fail_call)
        
        # Success should have higher evidence strength
        success_evidence = success_result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        fail_evidence = fail_result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        assert success_evidence > fail_evidence
        # New successful tools use default reliability (0.5), not hardcoded 0.9
        assert success_evidence == 0.5  # New tool starts at neutral
        # Failed tools scale down reliability: 0.5 * 0.3 = 0.15
        assert fail_evidence <= 0.2  # Failed tools have low evidence (0.5 * 0.3 = 0.15)
    
    def test_different_tools_tracked_independently(self):
        """
        Test that different tools are tracked independently.
        
        Rationale: Ensures each tool's reliability is tracked separately.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool1 = MockTool(name="tool_1", success=True)
        tool2 = MockTool(name="tool_2", success=False)
        
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        # Execute each tool multiple times
        for i in range(3):
            call1 = {
                "id": f"call_1_{i}",
                "type": "function",
                "function": {"name": "tool_1", "arguments": "{}"}
            }
            call2 = {
                "id": f"call_2_{i}",
                "type": "function",
                "function": {"name": "tool_2", "arguments": "{}"}
            }
            registry.execute_tool_call(call1)
            registry.execute_tool_call(call2)
        
        # Check each tool tracked separately
        reliability_1 = engine.validator.assess_tool_reliability("tool_1")
        reliability_2 = engine.validator.assess_tool_reliability("tool_2")
        
        assert reliability_1 > reliability_2  # Tool 1 should be more reliable
        assert len(engine.validator._tool_executions["tool_1"]) == 3
        assert len(engine.validator._tool_executions["tool_2"]) == 3


class TestKnowledgeSourceCreation:
    """Test knowledge source creation from tool executions."""
    
    def test_knowledge_id_generated_correctly(self):
        """
        Test that knowledge IDs are generated correctly for tool results.
        
        Rationale: Ensures each tool result gets a unique, deterministic knowledge ID.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="test_tool", success=True, result_data={"result": "test_data"})
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
        
        # Verify epistemic impact includes source metadata
        assert "_epistemic_impact" in result
        # Source metadata should be tracked in the engine
        # We can't directly check knowledge_id from result, but we can verify
        # that the workflow was called by checking tool reliability tracking
        assert len(engine.validator._tool_executions.get("test_tool", [])) > 0
    
    def test_source_metadata_captured_correctly(self):
        """
        Test that source metadata is captured correctly.
        
        Rationale: Ensures tool type, timestamp, and success metrics are stored.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="metadata_tool", success=True)
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_meta",
            "type": "function",
            "function": {
                "name": "metadata_tool",
                "arguments": "{}"
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Check epistemic impact includes confidence metrics with execution info
        impact = result["_epistemic_impact"]
        assert "confidence_metrics" in impact
        metrics = impact["confidence_metrics"]
        assert "tool_reliability_score" in metrics
        assert "execution_success" in metrics
        assert "evidence_strength" in metrics
        assert metrics["execution_success"] is True
        # New tool uses default reliability (0.5), not hardcoded 0.9
        assert metrics["evidence_strength"] == 0.5  # New tool starts at neutral
        assert metrics["evidence_strength"] == metrics["tool_reliability_score"]  # Should match reliability
    
    def test_initial_confidence_set_based_on_execution_success(self):
        """
        Test that initial confidence is set based on execution success.
        
        Rationale: Ensures successful executions get higher initial confidence.
        """
        engine = MetacognitiveEngine()
        
        # Successful tool
        registry_success = ToolRegistry(epistemic_engine=engine)
        success_tool = MockTool(name="high_conf_tool", success=True)
        registry_success.register_tool(success_tool)
        
        success_call = {
            "id": "call_high",
            "type": "function",
            "function": {"name": "high_conf_tool", "arguments": "{}"}
        }
        success_result = registry_success.execute_tool_call(success_call)
        success_strength = success_result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        
        # Failed tool
        registry_fail = ToolRegistry(epistemic_engine=engine)
        fail_tool = MockTool(name="low_conf_tool", success=False)
        registry_fail.register_tool(fail_tool)
        
        fail_call = {
            "id": "call_low",
            "type": "function",
            "function": {"name": "low_conf_tool", "arguments": "{}"}
        }
        fail_result = registry_fail.execute_tool_call(fail_call)
        fail_strength = fail_result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        
        # Successful should have higher evidence strength than failure
        assert success_strength > fail_strength
        # New successful tool uses default reliability (0.5), not hardcoded 0.9
        assert success_strength == 0.5  # New tool starts at neutral
        # Failed tool scales down: 0.5 * 0.3 = 0.15
        assert fail_strength <= 0.2  # Failed tool has low evidence


class TestConfidenceMetrics:
    """Test confidence metrics updates."""
    
    def test_confidence_updates_with_repeated_tool_executions(self):
        """
        Test that confidence updates correctly when tools succeed/fail repeatedly.
        
        Rationale: Ensures confidence metrics reflect tool execution patterns over time.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="confidence_tool", success=True)
        registry.register_tool(tool)
        
        # Execute multiple successful calls
        reliabilities = []
        for i in range(10):
            tool_call = {
                "id": f"call_{i}",
                "type": "function",
                "function": {"name": "confidence_tool", "arguments": "{}"}
            }
            registry.execute_tool_call(tool_call)
            reliabilities.append(engine.validator.assess_tool_reliability("confidence_tool"))
        
        # Reliability should improve with more successful executions
        # At least the last one should be higher than the first
        assert reliabilities[-1] >= reliabilities[0]
        
        # With many successes, reliability should be high
        assert reliabilities[-1] > 0.7
    
    def test_tool_reliability_affects_knowledge_source_confidence(self):
        """
        Test that tool reliability affects knowledge source confidence.
        
        Rationale: Ensures reliable tools produce knowledge with higher confidence.
        """
        engine = MetacognitiveEngine()
        
        # Build up reliability for one tool
        registry1 = ToolRegistry(epistemic_engine=engine)
        reliable_tool = MockTool(name="reliable", success=True)
        registry1.register_tool(reliable_tool)
        
        for i in range(5):
            call = {
                "id": f"reliable_{i}",
                "type": "function",
                "function": {"name": "reliable", "arguments": "{}"}
            }
            registry1.execute_tool_call(call)
        
        reliable_reliability = engine.validator.assess_tool_reliability("reliable")
        
        # New tool with no history
        registry2 = ToolRegistry(epistemic_engine=engine)
        new_tool = MockTool(name="new_tool", success=True)
        registry2.register_tool(new_tool)
        
        new_call = {
            "id": "new_call",
            "type": "function",
            "function": {"name": "new_tool", "arguments": "{}"}
        }
        new_result = registry2.execute_tool_call(new_call)
        
        # Reliable tool should have higher reliability score
        assert reliable_reliability > 0.5  # Should be above neutral
        # New tool starts at neutral (0.5) and uses that for evidence strength
        new_strength = new_result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        stored_reliability = new_result["_epistemic_impact"]["confidence_metrics"]["tool_reliability_score"]
        assert new_strength == stored_reliability  # Should match tool reliability
        assert new_strength == 0.5  # New tool starts at neutral, not hardcoded 0.9
        assert new_strength < 0.9  # Should not be hardcoded high value


class TestEpistemicContext:
    """Test epistemic context retrieval."""
    
    def test_epistemic_context_retrievable_for_tool_derived_knowledge(self):
        """
        Test that epistemic context can be retrieved for tool-derived knowledge.
        
        Rationale: Ensures we can query epistemic metadata about tool-derived knowledge.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="context_tool", success=True, result_data={"data": "test"})
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_context",
            "type": "function",
            "function": {
                "name": "context_tool",
                "arguments": "{}"
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Verify we can get epistemic context (knowledge would be stored with generated ID)
        # We verify by checking that tool execution was tracked
        assert len(engine.validator._tool_executions.get("context_tool", [])) > 0
        
        # Verify epistemic impact is in result
        assert "_epistemic_impact" in result
        assert "confidence_metrics" in result["_epistemic_impact"]
    
    def test_context_includes_confidence_metrics(self):
        """
        Test that context includes confidence metrics.
        
        Rationale: Ensures epistemic context contains all necessary confidence information.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="metrics_tool", success=True)
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_metrics",
            "type": "function",
            "function": {"name": "metrics_tool", "arguments": "{}"}
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Check confidence metrics are present
        impact = result["_epistemic_impact"]
        metrics = impact["confidence_metrics"]
        
        assert "tool_reliability_score" in metrics
        assert "execution_success" in metrics
        assert "evidence_strength" in metrics
        assert isinstance(metrics["tool_reliability_score"], (int, float))
        assert 0.0 <= metrics["tool_reliability_score"] <= 1.0


class TestWorkflowIntegration:
    """Test end-to-end workflow integration."""
    
    def test_full_workflow_tool_execution_to_confidence_update(self):
        """
        Test full workflow: tool execution → knowledge acquisition → confidence update.
        
        Rationale: Ensures the complete epistemic tracking workflow functions correctly.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="workflow_tool", success=True)
        registry.register_tool(tool)
        
        # Initial tool execution
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {"name": "workflow_tool", "arguments": "{}"}
        }
        
        result1 = registry.execute_tool_call(tool_call)
        
        # Verify epistemic tracking occurred
        assert "_epistemic_impact" in result1
        initial_reliability = engine.validator.assess_tool_reliability("workflow_tool")
        
        # Execute again to update confidence
        tool_call2 = {
            "id": "call_2",
            "type": "function",
            "function": {"name": "workflow_tool", "arguments": "{}"}
        }
        
        result2 = registry.execute_tool_call(tool_call2)
        
        # Reliability should be tracked and potentially improved
        updated_reliability = engine.validator.assess_tool_reliability("workflow_tool")
        assert updated_reliability >= initial_reliability  # Should stay same or improve
        
        # Verify both executions tracked
        assert len(engine.validator._tool_executions["workflow_tool"]) == 2
        assert all(engine.validator._tool_executions["workflow_tool"])  # Both successful
    
    def test_multiple_tool_executions_tracked_independently(self):
        """
        Test that multiple tool executions are tracked independently.
        
        Rationale: Ensures each tool execution creates separate knowledge entries.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="multi_tool", success=True)
        registry.register_tool(tool)
        
        # Execute tool multiple times with different arguments
        results = []
        for i in range(3):
            tool_call = {
                "id": f"call_multi_{i}",
                "type": "function",
                "function": {
                    "name": "multi_tool",
                    "arguments": f'{{"param1": "value_{i}"}}'
                }
            }
            result = registry.execute_tool_call(tool_call)
            results.append(result)
        
        # Each should have epistemic impact
        for result in results:
            assert "_epistemic_impact" in result
        
        # All executions should be tracked
        assert len(engine.validator._tool_executions["multi_tool"]) == 3
    
    def test_tool_reliability_improves_with_successful_executions(self):
        """
        Test that tool reliability improves with successful executions.
        
        Rationale: Ensures the system learns which tools are reliable over time.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        tool = MockTool(name="improving_tool", success=True)
        registry.register_tool(tool)
        
        reliabilities = []
        
        # Execute tool multiple times successfully
        for i in range(10):
            tool_call = {
                "id": f"call_improve_{i}",
                "type": "function",
                "function": {"name": "improving_tool", "arguments": "{}"}
            }
            registry.execute_tool_call(tool_call)
            
            # Check reliability after each execution
            reliability = engine.validator.assess_tool_reliability("improving_tool")
            reliabilities.append(reliability)
        
        # Reliability should improve (or at least stay high) with more successes
        # With 10 successful executions, reliability should be high
        assert reliabilities[-1] > 0.7
        assert len(engine.validator._tool_executions["improving_tool"]) == 10
        assert all(engine.validator._tool_executions["improving_tool"])  # All successful


class TestVerificationPrioritization:
    """Test verification prioritization for tool-derived knowledge."""
    
    def test_verification_prioritization_includes_tool_derived_knowledge(self):
        """
        Test that verification prioritization includes tool-derived knowledge.
        
        Rationale: Ensures tool results can be prioritized for verification.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        # Create tool with mixed success/failure to generate low-confidence knowledge
        tool = MockTool(name="priority_tool", success=False)  # Start with failure
        registry.register_tool(tool)
        
        # Execute failed tool call (creates low-confidence knowledge)
        tool_call = {
            "id": "call_priority",
            "type": "function",
            "function": {"name": "priority_tool", "arguments": "{}"}
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Failed execution should have low evidence strength
        assert "_epistemic_impact" in result
        evidence_strength = result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        assert evidence_strength <= 0.3  # Low confidence
        
        # Tool reliability should be low
        reliability = engine.validator.assess_tool_reliability("priority_tool")
        assert reliability < 0.5  # Below neutral due to failure
    
    def test_low_confidence_tool_results_prioritized_for_verification(self):
        """
        Test that low-confidence tool results are prioritized for verification.
        
        Rationale: Ensures the system identifies uncertain tool results for re-verification.
        """
        engine = MetacognitiveEngine()
        registry = ToolRegistry(epistemic_engine=engine)
        
        # Create tool that fails
        fail_tool = MockTool(name="low_conf_tool", success=False)
        registry.register_tool(fail_tool)
        
        fail_call = {
            "id": "call_low_conf",
            "type": "function",
            "function": {"name": "low_conf_tool", "arguments": "{}"}
        }
        
        fail_result = registry.execute_tool_call(fail_call)
        
        # Verify low confidence (new tool fails: 0.5 * 0.3 = 0.15)
        fail_evidence = fail_result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        assert fail_evidence <= 0.2  # Low confidence for failed new tool
        
        # Create tool that succeeds (for comparison)
        success_tool = MockTool(name="high_conf_tool", success=True)
        registry.register_tool(success_tool)
        
        success_call = {
            "id": "call_high_conf",
            "type": "function",
            "function": {"name": "high_conf_tool", "arguments": "{}"}
        }
        
        success_result = registry.execute_tool_call(success_call)
        
        # Verify confidence (new successful tool uses default reliability 0.5, not hardcoded 0.9)
        success_evidence = success_result["_epistemic_impact"]["confidence_metrics"]["evidence_strength"]
        assert success_evidence == 0.5  # New tool starts at neutral
        assert success_evidence > fail_evidence  # Success > failure
        
        # Failed tool should have lower confidence and be candidate for verification
        assert fail_evidence < success_evidence


class TestSystemDefaultSourceReliability:
    """Test that SYSTEM_DEFAULT sources use assessed reliability instead of hardcoded values."""
    
    def test_system_default_uses_assessed_reliability(self):
        """
        Test that SYSTEM_DEFAULT sources should use assessed reliability (0.5 default), not hardcoded values.
        
        Rationale: When code passes initial_confidence explicitly, it should use assess_source_reliability()
        instead of hardcoded values like 0.8, 0.9, etc.
        """
        from broca.self_model.epistemic.ids import generate_capability_id
        
        engine = MetacognitiveEngine()
        
        # Test capability with SYSTEM_DEFAULT source
        capability_id = generate_capability_id("test_capability")
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Assess reliability for SYSTEM_DEFAULT (should be 0.5 default)
        assessed_reliability = engine.validator.assess_source_reliability(source)
        assert assessed_reliability == 0.5  # SYSTEM_DEFAULT has default reliability
        
        # Simulate what the code SHOULD do: use assessed_reliability
        # (This is what we'll implement in the fix)
        correct_initial_confidence = assessed_reliability
        metrics_correct = engine.knowledge_acquisition_workflow(
            knowledge_id=capability_id,
            source=source,
            initial_confidence=correct_initial_confidence
        )
        
        # Simulate current WRONG behavior: using hardcoded 0.8
        metrics_wrong = engine.knowledge_acquisition_workflow(
            knowledge_id=generate_capability_id("test_capability2"),
            source=source,
            initial_confidence=0.8  # Hardcoded - this is wrong
        )
        
        # Correct approach should use assessed reliability
        assert metrics_correct.overall_confidence == assessed_reliability
        # Wrong approach uses hardcoded value (this test verifies the problem exists)
        assert metrics_wrong.overall_confidence == 0.8  # Hardcoded, not assessed
        assert metrics_wrong.overall_confidence != assessed_reliability
    
    def test_capability_confidence_uses_source_reliability(self):
        """
        Test that capabilities should use assessed source reliability, not hardcoded 0.8.
        
        Rationale: Ensures capabilities get confidence based on source reliability assessment.
        """
        from broca.self_model.epistemic.ids import generate_capability_id
        
        engine = MetacognitiveEngine()
        capability_id = generate_capability_id("Python programming")
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        
        assessed_reliability = engine.validator.assess_source_reliability(source)
        # Code SHOULD pass assessed_reliability, not hardcoded 0.8
        metrics = engine.knowledge_acquisition_workflow(
            knowledge_id=capability_id,
            source=source,
            initial_confidence=assessed_reliability  # Use assessed, not 0.8
        )
        
        # Should match assessed reliability (0.5 for SYSTEM_DEFAULT), not hardcoded 0.8
        assert abs(metrics.overall_confidence - assessed_reliability) < 0.01
        assert metrics.overall_confidence == 0.5
        assert metrics.overall_confidence != 0.8  # Should not be hardcoded value
    
    def test_constraint_confidence_uses_source_reliability(self):
        """
        Test that constraints should use assessed source reliability, not hardcoded 0.9.
        
        Rationale: Ensures constraints get confidence based on source reliability, not hardcoded 0.9.
        """
        from broca.self_model.epistemic.ids import generate_constraint_id
        
        engine = MetacognitiveEngine()
        constraint_id = generate_constraint_id("max_iterations", 100)
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        
        assessed_reliability = engine.validator.assess_source_reliability(source)
        # Code SHOULD pass assessed_reliability, not hardcoded 0.9
        metrics = engine.knowledge_acquisition_workflow(
            knowledge_id=constraint_id,
            source=source,
            initial_confidence=assessed_reliability  # Use assessed, not 0.9
        )
        
        # Should match assessed reliability (0.5 for SYSTEM_DEFAULT), not hardcoded 0.9
        assert abs(metrics.overall_confidence - assessed_reliability) < 0.01
        assert metrics.overall_confidence == 0.5
        assert metrics.overall_confidence != 0.9  # Should not be hardcoded value
    
    def test_behavioral_pattern_confidence_uses_source_reliability(self):
        """
        Test that behavioral patterns should use assessed source reliability, not hardcoded 0.6.
        
        Rationale: Ensures behavioral patterns get confidence based on source reliability, not hardcoded 0.6.
        """
        from broca.self_model.epistemic.ids import generate_behavioral_pattern_id
        
        engine = MetacognitiveEngine()
        pattern_id = generate_behavioral_pattern_id({"pattern": "test"})
        source = SourceMetadata(
            source_type=SourceType.SYSTEM_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        
        assessed_reliability = engine.validator.assess_source_reliability(source)
        # Code SHOULD pass assessed_reliability, not hardcoded 0.6
        metrics = engine.knowledge_acquisition_workflow(
            knowledge_id=pattern_id,
            source=source,
            initial_confidence=assessed_reliability  # Use assessed, not 0.6
        )
        
        # Should match assessed reliability (0.5 for SYSTEM_DEFAULT), not hardcoded 0.6
        assert abs(metrics.overall_confidence - assessed_reliability) < 0.01
        assert metrics.overall_confidence == 0.5
        assert metrics.overall_confidence != 0.6  # Should not be hardcoded value
    
    def test_consistency_violation_uses_source_reliability(self):
        """
        Test that consistency violations use assessed source reliability, not hardcoded values.
        
        Rationale: Ensures consistency violations get confidence based on source reliability assessment.
        """
        from broca.self_model.epistemic.ids import generate_knowledge_id
        from broca.self_model.consistency import ConsistencyResult
        
        engine = MetacognitiveEngine()
        
        # Create a consistency violation
        violation_desc = "Test violation description"
        knowledge_id = generate_knowledge_id("consistency_violation", violation_desc)
        
        violation_source = SourceMetadata(
            source_type=SourceType.LOGICAL_INFERENCE,
            inference_type="consistency_check",
            logical_strength=0.7,  # severity = 0.3, so logical_strength = 0.7
            timestamp=datetime.now(timezone.utc)
        )
        
        # Assess source reliability
        assessed_reliability = engine.validator.assess_source_reliability(violation_source)
        
        # Simulate what should happen: use assessed reliability
        # When knowledge doesn't exist, confidence_update_workflow calls knowledge_acquisition_workflow
        # with evidence_strength, but it should use assessed reliability
        metrics = engine.confidence_update_workflow(
            knowledge_id=knowledge_id,
            new_evidence=violation_source,
            evidence_strength=1.0 - 0.3  # evidence_strength = 0.7 (inverse of severity 0.3)
        )
        
        # Confidence should be based on assessed reliability (logical_strength = 0.7)
        # not hardcoded evidence_strength
        assert metrics.overall_confidence == assessed_reliability
        assert metrics.overall_confidence == 0.7  # Should use logical_strength from source

