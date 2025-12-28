"""
Unit tests for PEA loop functionality.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone

from broca.reasoning.plan_exec_assess_loop import (
    PlanExecuteAssessLoop,
    Plan,
    ActionExecution,
    Assessment,
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
        require_planning=True,
    )


class TestPlanCreation:
    """Test plan creation and extraction."""
    
    def test_extract_plan_from_response(self, pea_loop):
        """Test extracting plan from LLM response."""
        response = """
        ## Plan
        **Goal:** Fix the web app bug
        **Steps:**
        1. Check the error logs
        2. Review the code
        3. Apply fix
        **Assumptions:** Bug is in frontend
        **Expected Outcomes:** Bug fixed
        """
        
        plan = pea_loop.extract_plan_from_response(response)
        
        assert plan is not None
        assert plan.goal == "Fix the web app bug"
        assert len(plan.steps) == 3
        assert "Check the error logs" in plan.steps[0]["description"]
    
    def test_extract_plan_no_plan_section(self, pea_loop):
        """Test that None is returned when no plan section exists."""
        response = "Just some regular text without a plan."
        
        plan = pea_loop.extract_plan_from_response(response)
        
        assert plan is None
    
    def test_parse_plan_steps(self, pea_loop):
        """Test parsing plan steps from text."""
        plan_text = """
        1. First step
        2. Second step
        3. Third step
        """
        
        steps = pea_loop._parse_plan_steps(plan_text)
        
        assert len(steps) == 3
        assert "First step" in steps[0]["description"]
        assert "Second step" in steps[1]["description"]


class TestActionExecution:
    """Test action execution recording."""
    
    def test_record_action_execution(self, pea_loop):
        """Test recording an action execution."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}])
        pea_loop.current_plan = plan
        
        pea_loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=0,
            tool_name="test_tool",
            arguments={"param": "value"},
            result={"success": True},
            success=True,
        )
        
        assert len(pea_loop.execution_history) == 1
        assert pea_loop.execution_history[0].tool_name == "test_tool"
        assert pea_loop.execution_history[0].success is True
        assert pea_loop.current_phase == LoopPhase.EXECUTE
    
    def test_record_multiple_executions(self, pea_loop):
        """Test recording multiple action executions."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}, {"description": "Step 2"}])
        pea_loop.current_plan = plan
        
        pea_loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=0,
            tool_name="tool1",
            arguments={},
            result={},
            success=True,
        )
        
        pea_loop.record_action_execution(
            plan_id=plan.plan_id,
            step_index=1,
            tool_name="tool2",
            arguments={},
            result={},
            success=False,
        )
        
        assert len(pea_loop.execution_history) == 2
        assert pea_loop.execution_history[0].success is True
        assert pea_loop.execution_history[1].success is False


class TestAssessment:
    """Test assessment functionality."""
    
    def test_assess_execution_success(self, pea_loop):
        """Test assessing a successful execution."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}])
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="test_tool",
                arguments={},
                result={},
                success=True,
            )
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert assessment.goal_achieved is True
        assert assessment.success_rate == 1.0
        assert len(assessment.failures) == 0
        assert assessment.should_replan is False
    
    def test_assess_execution_failure(self, pea_loop):
        """Test assessing a failed execution."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}])
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="test_tool",
                arguments={},
                result={"error": "Failed"},
                success=False,
            )
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert assessment.goal_achieved is False
        assert assessment.success_rate == 0.0
        assert len(assessment.failures) == 1
        assert assessment.should_replan is True
    
    def test_assess_execution_partial_success(self, pea_loop):
        """Test assessing execution with partial success."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}, {"description": "Step 2"}])
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="tool1",
                arguments={},
                result={},
                success=True,
            ),
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=1,
                tool_name="tool2",
                arguments={},
                result={},
                success=False,
            ),
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert assessment.goal_achieved is False
        assert assessment.success_rate == 0.5
        assert len(assessment.failures) == 1
    
    def test_assess_execution_no_executions(self, pea_loop):
        """Test assessing execution with no executions."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}])
        
        assessment = pea_loop.assess_execution(plan, [])
        
        assert assessment.goal_achieved is False
        assert assessment.success_rate == 0.0
        assert assessment.should_replan is True
        assert "No actions were executed" in assessment.replan_reason


class TestFailedPatterns:
    """Test failed pattern tracking."""
    
    def test_track_failed_pattern(self, pea_loop):
        """Test tracking failed patterns."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}])
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="test_tool",
                arguments={},
                result={"error": "Failed"},
                success=False,
            )
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert len(pea_loop.failed_patterns) == 1
        assert pea_loop.failed_patterns[0]["plan_id"] == plan.plan_id
    
    def test_failed_pattern_limit(self, pea_loop):
        """Test that failed patterns are limited."""
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
        
        assert len(pea_loop.failed_patterns) == 3  # Should be limited to max


class TestReplanning:
    """Test replanning logic."""
    
    def test_should_replan_on_failure(self, pea_loop):
        """Test that replanning is triggered on failure."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}])
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="test_tool",
                arguments={},
                result={},
                success=False,
            )
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert assessment.should_replan is True
        assert assessment.replan_reason is not None
    
    def test_max_replan_attempts(self, pea_loop):
        """Test that replanning stops after max attempts."""
        pea_loop.max_replan_attempts = 2
        pea_loop.replan_count = 2
        
        plan = Plan(goal="Test goal", steps=[{"description": "Step 1"}])
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="test_tool",
                arguments={},
                result={},
                success=False,
            )
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert assessment.should_replan is False  # Max attempts reached


class TestStateManagement:
    """Test state management."""
    
    def test_reset_for_new_goal(self, pea_loop):
        """Test resetting state for new goal."""
        plan = Plan(goal="Old goal", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        pea_loop.current_phase = LoopPhase.EXECUTE
        pea_loop.replan_count = 2
        
        pea_loop.reset_for_new_goal("New goal")
        
        assert pea_loop.current_goal == "New goal"
        assert pea_loop.current_plan is None
        assert pea_loop.current_phase is None
        assert pea_loop.replan_count == 0
    
    def test_get_loop_state(self, pea_loop):
        """Test getting loop state."""
        plan = Plan(goal="Test goal", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        pea_loop.current_phase = LoopPhase.EXECUTE
        
        state = pea_loop.get_loop_state()
        
        assert state["current_phase"] == "action"
        assert state["current_plan_id"] == plan.plan_id
        assert state["current_goal"] is None  # Not set yet


class TestPlanningEnforcement:
    """Test planning enforcement."""
    
    def test_should_require_plan_no_plan(self, pea_loop):
        """Test that planning is required when no plan exists."""
        assert pea_loop.should_require_plan("User request", has_tool_calls=True) is True
    
    def test_should_require_plan_has_plan(self, pea_loop):
        """Test that planning is not required when plan exists."""
        plan = Plan(goal="Test", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        pea_loop.current_phase = LoopPhase.EXECUTE
        
        assert pea_loop.should_require_plan("User request", has_tool_calls=True) is False
    
    def test_should_require_plan_assess_phase(self, pea_loop):
        """Test that planning is required in ASSESS phase."""
        pea_loop.current_phase = LoopPhase.ASSESS
        
        assert pea_loop.should_require_plan("User request", has_tool_calls=False) is True
    
    def test_enforce_planning_phase(self, pea_loop):
        """Test enforcing planning phase."""
        user_message = "Fix the bug"
        
        result = pea_loop.enforce_planning_phase(user_message)
        
        assert "[SYSTEM DIRECTIVE - PLANNING REQUIRED]" in result
        assert "MUST create a plan" in result

