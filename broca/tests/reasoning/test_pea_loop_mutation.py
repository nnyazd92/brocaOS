"""
Mutation tests for PEA loop.

Tests specifically designed to kill mutations.
These tests verify specific behaviors that would be broken by common mutations
like changing operators, conditions, or return values.
"""

import pytest
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
        max_replan_attempts=3,
        success_threshold=0.8,
        max_failed_patterns=10,
    )


class TestMutationKillers:
    """Tests designed to kill mutations."""
    
    def test_success_threshold_enforced(self, pea_loop):
        """Kills mutation: changing success threshold comparison."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        # Success rate 0.85 should achieve goal (>= 0.8)
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
        
        assert assessment.goal_achieved is True  # 1.0 >= 0.8
    
    def test_success_threshold_not_achieved(self, pea_loop):
        """Kills mutation: success threshold not properly checked."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        # Success rate 0.5 should NOT achieve goal (< 0.8)
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="tool",
                arguments={},
                result={},
                success=True,
            ),
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=1,
                tool_name="tool",
                arguments={},
                result={},
                success=False,
            ),
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert assessment.goal_achieved is False  # 0.5 < 0.8
    
    def test_max_replan_attempts_enforced(self, pea_loop):
        """Kills mutation: max replan attempts not enforced."""
        pea_loop.max_replan_attempts = 2
        pea_loop.replan_count = 2
        
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
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
        
        assert assessment.should_replan is False  # Max attempts reached
    
    def test_replan_count_increments(self, pea_loop):
        """Kills mutation: replan count not incrementing."""
        initial_count = pea_loop.replan_count
        
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
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
        pea_loop.enforce_assessment_phase(assessment)
        
        assert pea_loop.replan_count == initial_count + 1
    
    def test_failed_patterns_limit_enforced(self, pea_loop):
        """Kills mutation: failed patterns limit not enforced."""
        pea_loop.max_failed_patterns = 3
        
        for i in range(5):
            plan = Plan(goal=f"Goal {i}", steps=[{"description": "Step"}])
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
            pea_loop.assess_execution(plan, executions)
        
        assert len(pea_loop.failed_patterns) == 3  # Must not exceed max
    
    def test_success_rate_bounds(self, pea_loop):
        """Kills mutation: success rate outside [0, 1] bounds."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        
        # All failures
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
        
        # All successes
        executions[0].success = True
        assessment = pea_loop.assess_execution(plan, executions)
        assert 0.0 <= assessment.success_rate <= 1.0
    
    def test_phase_transition_plan_to_action(self, pea_loop):
        """Kills mutation: phase not transitioning from PLAN to ACTION."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        pea_loop.current_phase = LoopPhase.PLAN
        
        pea_loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=0,
            tool_name="tool",
            arguments={},
            result={},
            success=True,
        )
        
        assert pea_loop.current_phase == LoopPhase.EXECUTE
    
    def test_phase_transition_action_to_assess(self, pea_loop):
        """Kills mutation: phase not transitioning from ACTION to ASSESS."""
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
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert pea_loop.current_phase == LoopPhase.ASSESS
    
    def test_phase_transition_assess_to_complete(self, pea_loop):
        """Kills mutation: phase not transitioning from ASSESS to COMPLETE."""
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
        
        assessment = pea_loop.assess_execution(plan, executions)
        pea_loop.enforce_assessment_phase(assessment)
        
        assert pea_loop.current_phase == LoopPhase.COMPLETE
    
    def test_execution_history_increments(self, pea_loop):
        """Kills mutation: execution history not incrementing."""
        initial_count = len(pea_loop.execution_history)
        
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        
        pea_loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=0,
            tool_name="tool",
            arguments={},
            result={},
            success=True,
        )
        
        assert len(pea_loop.execution_history) == initial_count + 1
    
    def test_assessment_history_increments(self, pea_loop):
        """Kills mutation: assessment history not incrementing."""
        initial_count = len(pea_loop.assessment_history)
        
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
        
        pea_loop.assess_execution(plan, executions)
        
        assert len(pea_loop.assessment_history) == initial_count + 1
    
    def test_goal_achieved_requires_no_failures(self, pea_loop):
        """Kills mutation: goal achieved even with failures."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="tool",
                arguments={},
                result={},
                success=True,
            ),
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=1,
                tool_name="tool",
                arguments={},
                result={},
                success=False,  # One failure
            ),
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        # Even with 0.5 success rate, should not achieve goal due to failures
        assert assessment.goal_achieved is False

