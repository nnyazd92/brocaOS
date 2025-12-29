"""
Integration tests for PEA loop with real session.
"""

import pytest
from unittest.mock import Mock, MagicMock
from broca.reasoning.plan_exec_assess_loop import (
    PlanExecuteAssessLoop,
    Plan,
    ActionExecution,
    LoopPhase,
)


@pytest.fixture
def mock_goal_manager():
    """Create a mock goal manager."""
    return Mock()


@pytest.fixture
def mock_skill_manager():
    """Create a mock skill manager."""
    return Mock()


@pytest.fixture
def mock_experience_logger():
    """Create a mock experience logger."""
    return Mock()


@pytest.fixture
def pea_loop_with_managers(mock_goal_manager, mock_skill_manager, mock_experience_logger):
    """Create PEA loop with managers."""
    return PlanExecuteAssessLoop(
        goal_manager=mock_goal_manager,
        skill_manager=mock_skill_manager,
        experience_logger=mock_experience_logger,
        max_replan_attempts=3,
    )


class TestIntegration:
    """Integration tests with real components."""
    
    def test_end_to_end_planning_flow(self, pea_loop_with_managers):
        """Test end-to-end planning flow."""
        pea_loop = pea_loop_with_managers
        
        # User message
        user_message = "Fix the web app bug"
        
        # Check if planning required
        assert pea_loop.should_require_plan(user_message, has_tool_calls=True) is True
        
        # Enforce planning
        modified_message = pea_loop.enforce_planning_phase(user_message)
        assert "[SYSTEM DIRECTIVE - PLANNING REQUIRED]" in modified_message
        
        # Simulate LLM response with plan
        llm_response = """
        ## Plan
        **Goal:** Fix the web app bug
        **Steps:**
        1. Check error logs
        2. Review code
        3. Apply fix
        **Assumptions:** Bug is in frontend
        **Expected Outcomes:** Bug fixed
        """
        
        # Extract plan
        plan = pea_loop.extract_plan_from_response(llm_response)
        assert plan is not None
        pea_loop.current_plan = plan
        pea_loop.current_phase = LoopPhase.PLAN
        
        # Record executions
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=0,
                tool_name="terminal",
                arguments={"command": "cat error.log"},
                result={"output": "Error found"},
                success=True,
            ),
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=1,
                tool_name="read_file",
                arguments={"path": "app.js"},
                result={"content": "code"},
                success=True,
            ),
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=2,
                tool_name="write_file",
                arguments={"path": "app.js", "content": "fixed"},
                result={"success": True},
                success=True,
            ),
        ]
        
        for execution in executions:
            pea_loop.record_action_execution(
                plan_id=execution.plan_id,
                step_index=execution.step_index,
                tool_name=execution.tool_name,
                arguments=execution.arguments,
                result=execution.result,
                success=execution.success,
            )
        
        # Assess
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert assessment.goal_achieved is True
        assert assessment.success_rate == 1.0
        assert assessment.should_replan is False
    
    def test_tool_execution_tracking(self, pea_loop_with_managers):
        """Test tool execution tracking."""
        pea_loop = pea_loop_with_managers
        
        plan = Plan(goal="Test", steps=[{"description": "Step 1"}, {"description": "Step 2"}])
        pea_loop.current_plan = plan
        
        # Record multiple tool executions
        tool_calls = [
            {"function": {"name": "tool1", "arguments": '{"param": "value"}'}},
            {"function": {"name": "tool2", "arguments": '{"param": "value2"}'}},
        ]
        
        for i, tool_call in enumerate(tool_calls):
            pea_loop.record_action_execution(
                plan_id=plan.plan_id,
                step_index=i,
                tool_name=tool_call["function"]["name"],
                arguments={"param": f"value{i+1}"},
                result={"output": f"result{i+1}"},
                success=True,
            )
        
        assert len(pea_loop.execution_history) == 2
        assert pea_loop.execution_history[0].tool_name == "tool1"
        assert pea_loop.execution_history[1].tool_name == "tool2"
    
    def test_assessment_and_replanning(self, pea_loop_with_managers):
        """Test assessment and replanning flow."""
        pea_loop = pea_loop_with_managers
        
        # First plan fails
        plan1 = Plan(goal="Fix bug", steps=[{"description": "Try approach A"}])
        executions1 = [
            ActionExecution(
                plan_id=plan1.plan_id,
                step_index=0,
                tool_name="terminal",
                arguments={},
                result={"error": "Failed"},
                success=False,
            )
        ]
        
        assessment1 = pea_loop.assess_execution(plan1, executions1)
        assert assessment1.should_replan is True
        
        # Enforce assessment phase
        assessment_msg = pea_loop.enforce_assessment_phase(assessment1)
        assert "ACTION REQUIRED" in assessment_msg
        assert pea_loop.replan_count == 1
        
        # Second plan succeeds
        plan2 = Plan(goal="Fix bug", steps=[{"description": "Try approach B"}])
        executions2 = [
            ActionExecution(
                plan_id=plan2.plan_id,
                step_index=0,
                tool_name="terminal",
                arguments={},
                result={"success": True},
                success=True,
            )
        ]
        
        assessment2 = pea_loop.assess_execution(plan2, executions2)
        assert assessment2.goal_achieved is True
        assert assessment2.should_replan is False
    
    def test_integration_with_goal_manager(self, mock_goal_manager, pea_loop_with_managers):
        """Test integration with goal manager."""
        pea_loop = pea_loop_with_managers
        
        # Goal manager should be available
        assert pea_loop.goal_manager is not None
        
        # Create a plan
        plan = Plan(goal="Test goal", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        
        # PEA loop should work independently of goal manager
        assessment = pea_loop.assess_execution(plan, [])
        assert assessment is not None
    
    def test_integration_with_skill_manager(self, mock_skill_manager, pea_loop_with_managers):
        """Test integration with skill manager."""
        pea_loop = pea_loop_with_managers
        
        # Skill manager should be available
        assert pea_loop.skill_manager is not None
        
        # Create a plan
        plan = Plan(goal="Test goal", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        
        # PEA loop should work independently of skill manager
        assessment = pea_loop.assess_execution(plan, [])
        assert assessment is not None
    
    def test_integration_with_experience_logger(self, mock_experience_logger, pea_loop_with_managers):
        """Test integration with experience logger."""
        pea_loop = pea_loop_with_managers
        
        # Experience logger should be available
        assert pea_loop.experience_logger is not None
        
        # Create a plan
        plan = Plan(goal="Test goal", steps=[{"description": "Step"}])
        pea_loop.current_plan = plan
        
        # PEA loop should work independently of experience logger
        assessment = pea_loop.assess_execution(plan, [])
        assert assessment is not None
    
    def test_complete_cycle_with_replan(self, pea_loop_with_managers):
        """Test complete cycle with replanning."""
        pea_loop = pea_loop_with_managers
        
        # Initial state
        assert pea_loop.current_phase is None
        assert pea_loop.current_plan is None
        
        # User request
        user_message = "Fix the issue"
        pea_loop.reset_for_new_goal(user_message)
        
        # Extract plan
        llm_response = """
        ## Plan
        **Goal:** Fix the issue
        **Steps:**
        1. Try method A
        """
        plan1 = pea_loop.extract_plan_from_response(llm_response)
        pea_loop.current_plan = plan1
        pea_loop.current_phase = LoopPhase.PLAN
        
        # Execute (fails)
        execution1 = ActionExecution(
            plan_id=plan1.plan_id,
            step_index=0,
            tool_name="tool",
            arguments={},
            result={},
            success=False,
        )
        pea_loop.record_action_execution(
            plan_id=execution1.plan_id,
            step_index=execution1.step_index,
            tool_name=execution1.tool_name,
            arguments=execution1.arguments,
            result=execution1.result,
            success=execution1.success,
        )
        
        # Assess (should replan)
        assessment1 = pea_loop.assess_execution(plan1, [execution1])
        assert assessment1.should_replan is True
        assert pea_loop.current_phase == LoopPhase.ASSESS
        
        # Replan
        pea_loop.enforce_assessment_phase(assessment1)
        
        # New plan
        llm_response2 = """
        ## Plan
        **Goal:** Fix the issue
        **Steps:**
        1. Try method B
        """
        plan2 = pea_loop.extract_plan_from_response(llm_response2)
        pea_loop.current_plan = plan2
        pea_loop.current_phase = LoopPhase.PLAN
        
        # Execute (succeeds)
        execution2 = ActionExecution(
            plan_id=plan2.plan_id,
            step_index=0,
            tool_name="tool",
            arguments={},
            result={},
            success=True,
        )
        pea_loop.record_action_execution(
            plan_id=execution2.plan_id,
            step_index=execution2.step_index,
            tool_name=execution2.tool_name,
            arguments=execution2.arguments,
            result=execution2.result,
            success=execution2.success,
        )
        
        # Assess (should complete)
        assessment2 = pea_loop.assess_execution(plan2, [execution2])
        assert assessment2.goal_achieved is True
        assert assessment2.should_replan is False
        
        # Complete
        pea_loop.enforce_assessment_phase(assessment2)
        assert pea_loop.current_phase == LoopPhase.COMPLETE

