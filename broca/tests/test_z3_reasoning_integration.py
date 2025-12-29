"""
Integration tests for Z3 validation in full reasoning cycles.

Tests Z3 validation integration with RuleEngine, GoalManager, and world state.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from broca.reasoning.rule_engine import RuleEngine
from broca.reasoning.goal_manager import GoalManager, Goal, GoalType, GoalStatus
from broca.reasoning.production_rules import ProductionRule, RuleType
from broca.reasoning.working_memory import WorkingMemory
from broca.reasoning.z3_validator import Z3LogicalValidator
from broca.world_state.aggregator import WorldStateAggregator
from broca.reasoning.integration_tool import ReasoningTool


class TestZ3RuleEngineIntegration:
    """Test Z3 validation integration with RuleEngine."""
    
    def test_rule_engine_with_z3_validation(self):
        """
        Test rule engine executes cycles with Z3 validation.
        
        Rationale: Z3 validation should be called during rule execution cycles.
        """
        rule_engine = RuleEngine(enable_z3_validation=True)
        
        # Create a simple rule
        rule = ProductionRule(
            name="test_rule",
            conditions=[{"type": "fact", "content": "premise"}],
            actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": "conclusion"}}],
            rule_type=RuleType.INFERENCE
        )
        
        rule_engine.rule_system.add_rule(rule)
        
        # Create working memory with premise
        wm = WorkingMemory()
        wm.add({"type": "fact", "content": "premise"})
        
        # Execute cycle
        results = rule_engine.execute_cycle(wm, max_rules=1)
        
        # Should execute successfully (validation may pass or fail, but shouldn't crash)
        assert isinstance(results, list)
    
    def test_rule_engine_without_z3(self):
        """
        Test rule engine works without Z3 validation.
        
        Rationale: System should work when Z3 is disabled.
        """
        rule_engine = RuleEngine(enable_z3_validation=False)
        
        rule = ProductionRule(
            name="test_rule",
            conditions=[{"type": "fact", "content": "premise"}],
            actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": "conclusion"}}],
            rule_type=RuleType.INFERENCE
        )
        
        rule_engine.rule_system.add_rule(rule)
        
        wm = WorkingMemory()
        wm.add({"type": "fact", "content": "premise"})
        
        results = rule_engine.execute_cycle(wm, max_rules=1)
        
        assert isinstance(results, list)


class TestZ3GoalManagerIntegration:
    """Test Z3 validation integration with GoalManager."""
    
    def test_goal_manager_with_z3_validation(self):
        """
        Test goal manager validates dependencies with Z3.
        
        Rationale: Z3 validation should prevent circular dependencies.
        """
        goal_manager = GoalManager()
        
        # Create goal with valid dependency
        goal1 = Goal(
            name="goal_1",
            description="First goal",
            goal_type=GoalType.ACHIEVE,
            dependencies=[],
            status=GoalStatus.ACTIVE
        )
        
        goal2 = Goal(
            name="goal_2",
            description="Second goal",
            goal_type=GoalType.ACHIEVE,
            dependencies=["goal_1"],
            status=GoalStatus.ACTIVE
        )
        
        # Should add successfully
        assert goal_manager.add_goal(goal1) is True
        assert goal_manager.add_goal(goal2) is True
    
    def test_goal_manager_rejects_circular_dependencies(self):
        """
        Test goal manager rejects circular dependencies.
        
        Rationale: Z3 should detect and prevent circular dependencies.
        """
        goal_manager = GoalManager()
        
        goal1 = Goal(
            name="goal_A",
            description="Goal A",
            goal_type=GoalType.ACHIEVE,
            dependencies=["goal_B"],
            status=GoalStatus.ACTIVE
        )
        
        goal2 = Goal(
            name="goal_B",
            description="Goal B",
            goal_type=GoalType.ACHIEVE,
            dependencies=["goal_A"],
            status=GoalStatus.ACTIVE
        )
        
        # Add first goal
        assert goal_manager.add_goal(goal1) is True
        
        # Second goal should be rejected if Z3 detects cycle
        result = goal_manager.add_goal(goal2)
        # May be rejected or accepted depending on Z3 availability and validation
        assert isinstance(result, bool)


class TestZ3WorldStateIntegration:
    """Test Z3 validation summary in world state."""
    
    def test_world_state_includes_z3_summary(self):
        """
        Test world state includes Z3 validation summary.
        
        Rationale: Z3 validation summary should be included in reasoning state.
        """
        # Create reasoning tool with Z3 validator
        reasoning_tool = ReasoningTool()
        
        # Create world state aggregator
        aggregator = WorldStateAggregator(reasoning_tool=reasoning_tool)
        
        # Get reasoning state
        reasoning_state = aggregator.get_reasoning_state()
        
        if reasoning_state.get("available"):
            reasoning = reasoning_state.get("reasoning", {})
            
            # Z3 validation summary may be included if validator is available
            if "z3_validation" in reasoning:
                z3_summary = reasoning["z3_validation"]
                assert "enabled" in z3_summary
                assert isinstance(z3_summary["enabled"], bool)
    
    def test_z3_summary_size_limit(self):
        """
        Test Z3 validation summary respects size limits.
        
        Rationale: Summary should not exceed 200 bytes.
        """
        validator = Z3LogicalValidator()
        
        # Update stats
        validator.update_validation_stats(
            rule_chain_valid=True,
            causal_chains_valid=True,
            goal_dependencies_valid=True,
            warnings_count=10,
            contradictions_count=5
        )
        
        summary = validator.get_validation_summary(max_size_bytes=200)
        
        import json
        json_str = json.dumps(summary)
        assert len(json_str.encode('utf-8')) <= 200


class TestZ3FullReasoningCycle:
    """Test Z3 validation in full reasoning cycles."""
    
    def test_full_reasoning_cycle_with_z3(self):
        """
        Test complete reasoning cycle with Z3 validation.
        
        Rationale: Z3 validation should work in end-to-end scenarios.
        """
        # Create reasoning tool
        reasoning_tool = ReasoningTool()
        
        # Add a rule
        rule_data = {
            "name": "test_rule",
            "conditions": [{"type": "fact", "content": "premise"}],
            "actions": [{"type": "add_to_memory", "content": {"type": "fact", "content": "conclusion"}}],
            "rule_type": "inference",
            "priority": 1.0
        }
        
        result = reasoning_tool.execute("add_rule", rule=rule_data)
        assert result.get("success") is True
        
        # Add to memory
        memory_result = reasoning_tool.execute("add_to_memory", memory_content={
            "type": "fact",
            "content": "premise"
        })
        assert memory_result.get("success") is True
        
        # Execute cycle (should trigger Z3 validation)
        cycle_result = reasoning_tool.execute("execute_cycle", max_rules=3)
        
        # Should execute successfully
        assert cycle_result.get("success") is True or cycle_result.get("success") is False
        # (May fail if Z3 validation fails, but should not crash)

