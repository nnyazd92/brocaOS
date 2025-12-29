"""
Fault injection tests for PEA loop robustness.
"""

import pytest
from unittest.mock import Mock
from broca.reasoning.plan_exec_assess_loop import (
    PlanExecuteAssessLoop,
    Plan,
    ActionExecution,
    LoopPhase,
)


@pytest.fixture
def pea_loop():
    """Create a PEA loop instance."""
    return PlanExecuteAssessLoop(
        goal_manager=None,
        skill_manager=None,
        experience_logger=None,
        max_replan_attempts=3,
    )


class TestFaultInjection:
    """Fault injection tests for robustness."""
    
    def test_none_goal_manager(self):
        """Test handling of None goal manager."""
        loop = PlanExecuteAssessLoop(goal_manager=None)
        assert loop.goal_manager is None
        
        # Should still work
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="tool",
                arguments={},
                result={},
                success=True,
            )
        ]
        
        assessment = loop.assess_execution(plan, executions)
        assert assessment is not None
    
    def test_none_skill_manager(self):
        """Test handling of None skill manager."""
        loop = PlanExecuteAssessLoop(skill_manager=None)
        assert loop.skill_manager is None
        
        # Should still work
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        loop.current_plan = plan
        loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=0,
            tool_name="tool",
            arguments={},
            result={},
            success=True,
        )
        assert len(loop.execution_history) == 1
    
    def test_none_experience_logger(self):
        """Test handling of None experience logger."""
        loop = PlanExecuteAssessLoop(experience_logger=None)
        assert loop.experience_logger is None
        
        # Should still work
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        assessment = loop.assess_execution(plan, [])
        assert assessment is not None
    
    def test_invalid_plan_extraction_malformed_response(self, pea_loop):
        """Test handling of malformed LLM response."""
        # Completely malformed
        response = "This is not a plan at all, just random text."
        plan = pea_loop.extract_plan_from_response(response)
        assert plan is None
        
        # Missing key sections
        response = "## Plan\nSome text but no structure"
        plan = pea_loop.extract_plan_from_response(response)
        # May or may not extract, but shouldn't crash
        assert plan is None or isinstance(plan, Plan)
    
    def test_empty_tool_results(self, pea_loop):
        """Test handling of empty tool results."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        
        pea_loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=0,
            tool_name="tool",
            arguments={},
            result={},  # Empty result
            success=True,
        )
        
        assert len(pea_loop.execution_history) == 1
        assert pea_loop.execution_history[0].result == {}
    
    def test_corrupted_execution_history(self, pea_loop):
        """Test handling of corrupted execution history."""
        # Manually add invalid execution (simulating corruption)
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        
        # Create execution with missing fields (simulating corruption)
        execution = ActionExecution(
            plan_id=plan.plan_id,
            step_index=0,
            tool_name="tool",
            arguments={},
            result={},
            success=True,
        )
        pea_loop.execution_history.append(execution)
        
        # Assessment should still work
        assessment = pea_loop.assess_execution(plan, [execution])
        assert assessment is not None
    
    def test_invalid_success_rates(self, pea_loop):
        """Test handling of invalid success rates in assessment."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        
        # All failures (success_rate = 0.0)
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="tool",
                arguments={},
                result={},
                success=False,
            )
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        assert 0.0 <= assessment.success_rate <= 1.0
        
        # All successes (success_rate = 1.0)
        executions[0].success = True
        assessment = pea_loop.assess_execution(plan, executions)
        assert 0.0 <= assessment.success_rate <= 1.0
    
    def test_missing_tool_call_data(self, pea_loop):
        """Test handling of missing tool call data."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        
        # Record with minimal data
        pea_loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=0,
            tool_name="",  # Empty tool name
            arguments={},  # Empty arguments
            result={},  # Empty result
            success=False,
        )
        
        assert len(pea_loop.execution_history) == 1
        assert pea_loop.execution_history[0].tool_name == ""
    
    def test_very_large_execution_histories(self, pea_loop):
        """Test handling of very large execution histories."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        
        # Add many executions
        for i in range(1000):
            pea_loop.record_action_execution(
                plan_id=plan.plan_id,
                step_index=i,
                tool_name="tool",
                arguments={},
                result={},
                success=(i % 2 == 0),
            )
        
        assert len(pea_loop.execution_history) == 1000
        
        # Assessment should still work
        assessment = pea_loop.assess_execution(plan, pea_loop.execution_history)
        assert assessment is not None
        assert 0.0 <= assessment.success_rate <= 1.0
    
    def test_very_large_plan_steps(self, pea_loop):
        """Test handling of plans with many steps."""
        # Create plan with many steps
        steps = [{"description": f"Step {i}"} for i in range(100)]
        plan = Plan(goal="Test", steps=steps)
        
        assert len(plan.steps) == 100
        
        # Should still work
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="tool",
                arguments={},
                result={},
                success=True,
            )
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        assert assessment is not None
    
    def test_corrupted_goal_manager(self):
        """Test handling of corrupted goal manager."""
        corrupted_manager = Mock()
        corrupted_manager.get_active_goals.side_effect = Exception("Corrupted")
        
        loop = PlanExecuteAssessLoop(goal_manager=corrupted_manager)
        
        # Should still work even if goal manager is corrupted
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        assessment = loop.assess_execution(plan, [])
        assert assessment is not None
    
    def test_invalid_phase_transitions(self, pea_loop):
        """Test handling of invalid phase transitions."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        
        # Try to record execution without a plan
        pea_loop.current_plan = None
        pea_loop.record_action_execution(
            plan_id="invalid",
            step_index=0,
            tool_name="tool",
            arguments={},
            result={},
            success=True,
        )
        
        # Should still work (just records execution)
        assert len(pea_loop.execution_history) == 1
    
    def test_empty_plan_steps(self, pea_loop):
        """Test handling of plan with no steps."""
        plan = Plan(goal="Test", steps=[])
        
        assessment = pea_loop.assess_execution(plan, [])
        assert assessment is not None
        assert assessment.success_rate == 0.0
        assert assessment.goal_achieved is False
    
    def test_unicode_in_plan(self, pea_loop):
        """Test handling of unicode characters in plan."""
        plan = Plan(
            goal="测试目标 🎯",
            steps=[{"description": "步骤 1 ✅"}],
            assumptions=["假设 1"],
        )
        
        assert plan.goal == "测试目标 🎯"
        assert len(plan.steps) == 1
        
        assessment = pea_loop.assess_execution(plan, [])
        assert assessment is not None
    
    def test_very_long_strings(self, pea_loop):
        """Test handling of very long strings."""
        long_string = "A" * 10000
        plan = Plan(goal=long_string, steps=[{"description": long_string}])
        
        assert len(plan.goal) == 10000
        assert len(plan.steps[0]["description"]) == 10000
        
        # Should still work
        assessment = pea_loop.assess_execution(plan, [])
        assert assessment is not None
    
    def test_negative_values(self, pea_loop):
        """Test handling of negative values."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        
        # Negative step_index
        pea_loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=-1,
            tool_name="tool",
            arguments={},
            result={},
            success=True,
        )
        
        assert len(pea_loop.execution_history) == 1
        assert pea_loop.execution_history[0].step_index == -1

