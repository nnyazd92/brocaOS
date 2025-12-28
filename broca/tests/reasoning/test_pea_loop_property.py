"""
Property-based tests for PEA loop using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
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


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_steps=st.integers(min_value=1, max_value=10),
        num_executions=st.integers(min_value=0, max_value=10),
        success_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_assessment_always_valid(self, pea_loop, num_steps, num_executions, success_rate):
        """Property: All assessments have valid structure and bounds."""
        plan = Plan(
            goal="Test goal",
            steps=[{"description": f"Step {i}"} for i in range(num_steps)]
        )
        
        # Create executions with given success rate
        executions = []
        for i in range(num_executions):
            # Approximate success rate by making executions succeed/fail accordingly
            should_succeed = (i / max(num_executions, 1)) < success_rate
            executions.append(
                ActionExecution(
                    plan_id=plan.plan_id,
                    step_index=i,
                    tool_name="tool",
                    arguments={},
                    result={},
                    success=should_succeed,
                )
            )
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        # Properties that must always hold
        assert assessment is not None
        assert 0.0 <= assessment.success_rate <= 1.0
        assert isinstance(assessment.goal_achieved, bool)
        assert isinstance(assessment.should_replan, bool)
        assert isinstance(assessment.failures, list)
        assert isinstance(assessment.learnings, list)
        assert len(assessment.failures) <= len(executions)
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        max_replans=st.integers(min_value=1, max_value=10),
        replan_count=st.integers(min_value=0, max_value=10),
    )
    def test_replan_count_bounds(self, max_replans, replan_count):
        """Property: Replan count never exceeds max_replan_attempts."""
        pea_loop = PlanExecuteAssessLoop(max_replan_attempts=max_replans)
        pea_loop.replan_count = min(replan_count, max_replans)  # Clamp to valid range
        
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
        
        # Should not replan if count exceeds max
        if pea_loop.replan_count >= max_replans:
            assert assessment.should_replan is False
        else:
            # May or may not replan depending on other conditions
            assert isinstance(assessment.should_replan, bool)
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        max_patterns=st.integers(min_value=1, max_value=20),
        num_failures=st.integers(min_value=0, max_value=30),
    )
    def test_failed_patterns_limit(self, max_patterns, num_failures):
        """Property: Failed patterns list never exceeds max."""
        pea_loop = PlanExecuteAssessLoop(max_failed_patterns=max_patterns)
        
        for i in range(num_failures):
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
        
        assert len(pea_loop.failed_patterns) <= max_patterns
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        success_threshold=st.floats(min_value=0.0, max_value=1.0),
        num_executions=st.integers(min_value=1, max_value=10),
        num_successes=st.integers(min_value=0, max_value=10),
    )
    def test_goal_achieved_property(self, success_threshold, num_executions, num_successes):
        """Property: Goal achieved respects success threshold and failure count."""
        num_successes = min(num_successes, num_executions)  # Clamp to valid range
        
        pea_loop = PlanExecuteAssessLoop(success_threshold=success_threshold)
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        
        executions = []
        for i in range(num_executions):
            executions.append(
                ActionExecution(
                    plan_id=plan.plan_id,
                    step_index=i,
                    tool_name="tool",
                    arguments={},
                    result={},
                    success=(i < num_successes),
                )
            )
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        actual_success_rate = num_successes / num_executions if num_executions > 0 else 0.0
        has_failures = num_successes < num_executions
        
        # Goal achieved only if success_rate >= threshold AND no failures
        expected_goal_achieved = (actual_success_rate >= success_threshold) and (not has_failures)
        assert assessment.goal_achieved == expected_goal_achieved
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_executions=st.integers(min_value=0, max_value=20),
    )
    def test_execution_history_consistency(self, pea_loop, num_executions):
        """Property: Execution history maintains consistency."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        
        initial_count = len(pea_loop.execution_history)
        
        for i in range(num_executions):
            pea_loop.record_action_execution(
                plan_id=plan.plan_id,
                step_index=i,
                tool_name="tool",
                arguments={},
                result={},
                success=(i % 2 == 0),
            )
        
        assert len(pea_loop.execution_history) == initial_count + num_executions
        
        # All executions should have correct plan_id
        for execution in pea_loop.execution_history[-num_executions:]:
            assert execution.plan_id == plan.plan_id
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        goal_text=st.text(min_size=1, max_size=100),
        num_steps=st.integers(min_value=1, max_value=10),
    )
    def test_plan_structure_valid(self, goal_text, num_steps):
        """Property: All plans have valid structure."""
        plan = Plan(
            goal=goal_text,
            steps=[{"description": f"Step {i}"} for i in range(num_steps)],
            assumptions=["Assumption 1"],
            expected_outcomes=["Outcome 1"],
        )
        
        # Properties that must always hold
        assert plan.goal == goal_text
        assert len(plan.steps) == num_steps
        assert isinstance(plan.plan_id, str)
        assert len(plan.plan_id) > 0
        from datetime import datetime
        assert isinstance(plan.created_at, datetime)
        
        # Test to_dict
        plan_dict = plan.to_dict()
        assert "goal" in plan_dict
        assert "steps" in plan_dict
        assert "plan_id" in plan_dict
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        phase_value=st.sampled_from(["plan", "action", "assess", "complete"]),
    )
    def test_phase_enum_valid(self, phase_value):
        """Property: Phase enum values are valid."""
        phase = LoopPhase(phase_value)
        assert phase.value == phase_value
        assert phase in [LoopPhase.PLAN, LoopPhase.ACTION, LoopPhase.ASSESS, LoopPhase.COMPLETE]

