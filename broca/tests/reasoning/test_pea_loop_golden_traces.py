"""
Golden trace replay tests for PEA loop scenarios.
"""

import pytest
import json
from pathlib import Path
from broca.reasoning.plan_exec_assess_loop import (
    PlanExecuteAssessLoop,
    Plan,
    ActionExecution,
    LoopPhase,
)


@pytest.fixture
def golden_traces_dir(tmp_path):
    """Create a temporary directory for golden traces."""
    traces_dir = tmp_path / "golden_traces" / "pea_loop"
    traces_dir.mkdir(parents=True)
    return traces_dir


def load_golden_trace(trace_name: str, golden_traces_dir: Path) -> dict:
    """Load a golden trace from file."""
    trace_path = golden_traces_dir / f"{trace_name}.json"
    if not trace_path.exists():
        pytest.skip(f"Golden trace {trace_name} not found at {trace_path}")
    
    with open(trace_path, 'r') as f:
        return json.load(f)


def create_successful_execution_trace(golden_traces_dir: Path):
    """Create golden trace for successful execution."""
    trace = {
        "scenario": "successful_execution",
        "description": "Plan succeeds on first try",
        "inputs": {
            "user_message": "Fix the bug",
            "plan": {
                "goal": "Fix the bug",
                "steps": [
                    {"description": "Check error logs"},
                    {"description": "Apply fix"},
                ]
            },
            "executions": [
                {"tool_name": "terminal", "success": True},
                {"tool_name": "terminal", "success": True},
            ]
        },
        "expected_outputs": {
            "goal_achieved": True,
            "success_rate": 1.0,
            "should_replan": False,
            "final_phase": "complete",
        }
    }
    
    trace_file = golden_traces_dir / "successful_execution.json"
    with open(trace_file, 'w') as f:
        json.dump(trace, f, indent=2)
    
    return trace


def create_replan_success_trace(golden_traces_dir: Path):
    """Create golden trace for replan success."""
    trace = {
        "scenario": "replan_success",
        "description": "First plan fails, second succeeds",
        "inputs": {
            "user_message": "Fix the bug",
            "plan1": {
                "goal": "Fix the bug",
                "steps": [{"description": "Try approach A"}]
            },
            "executions1": [
                {"tool_name": "terminal", "success": False}
            ],
            "plan2": {
                "goal": "Fix the bug",
                "steps": [{"description": "Try approach B"}]
            },
            "executions2": [
                {"tool_name": "terminal", "success": True}
            ]
        },
        "expected_outputs": {
            "assessment1": {
                "goal_achieved": False,
                "should_replan": True,
            },
            "assessment2": {
                "goal_achieved": True,
                "should_replan": False,
            },
            "final_replan_count": 1,
        }
    }
    
    trace_file = golden_traces_dir / "replan_success.json"
    with open(trace_file, 'w') as f:
        json.dump(trace, f, indent=2)
    
    return trace


def create_max_replans_reached_trace(golden_traces_dir: Path):
    """Create golden trace for max replans reached."""
    trace = {
        "scenario": "max_replans_reached",
        "description": "All replan attempts exhausted",
        "inputs": {
            "user_message": "Fix the bug",
            "max_replan_attempts": 3,
            "plans": [
                {"goal": "Fix the bug", "steps": [{"description": "Try A"}]},
                {"goal": "Fix the bug", "steps": [{"description": "Try B"}]},
                {"goal": "Fix the bug", "steps": [{"description": "Try C"}]},
            ],
            "executions": [
                [{"tool_name": "terminal", "success": False}],
                [{"tool_name": "terminal", "success": False}],
                [{"tool_name": "terminal", "success": False}],
            ]
        },
        "expected_outputs": {
            "final_replan_count": 3,
            "final_should_replan": False,
            "final_phase": "complete",
        }
    }
    
    trace_file = golden_traces_dir / "max_replans_reached.json"
    with open(trace_file, 'w') as f:
        json.dump(trace, f, indent=2)
    
    return trace


def create_complex_multi_step_trace(golden_traces_dir: Path):
    """Create golden trace for complex multi-step plan."""
    trace = {
        "scenario": "complex_multi_step",
        "description": "Complex plan with many steps",
        "inputs": {
            "user_message": "Deploy the application",
            "plan": {
                "goal": "Deploy the application",
                "steps": [
                    {"description": "Build application"},
                    {"description": "Run tests"},
                    {"description": "Create deployment package"},
                    {"description": "Deploy to staging"},
                    {"description": "Verify deployment"},
                ]
            },
            "executions": [
                {"tool_name": "terminal", "success": True},
                {"tool_name": "terminal", "success": True},
                {"tool_name": "terminal", "success": True},
                {"tool_name": "terminal", "success": True},
                {"tool_name": "terminal", "success": True},
            ]
        },
        "expected_outputs": {
            "goal_achieved": True,
            "success_rate": 1.0,
            "num_executions": 5,
        }
    }
    
    trace_file = golden_traces_dir / "complex_multi_step.json"
    with open(trace_file, 'w') as f:
        json.dump(trace, f, indent=2)
    
    return trace


def create_failed_pattern_accumulation_trace(golden_traces_dir: Path):
    """Create golden trace for failed pattern accumulation."""
    trace = {
        "scenario": "failed_pattern_accumulation",
        "description": "Multiple failed patterns tracked",
        "inputs": {
            "user_message": "Fix multiple bugs",
            "max_failed_patterns": 5,
            "plans": [
                {"goal": "Fix bug 1", "steps": [{"description": "Try A"}]},
                {"goal": "Fix bug 2", "steps": [{"description": "Try B"}]},
                {"goal": "Fix bug 3", "steps": [{"description": "Try C"}]},
                {"goal": "Fix bug 4", "steps": [{"description": "Try D"}]},
                {"goal": "Fix bug 5", "steps": [{"description": "Try E"}]},
                {"goal": "Fix bug 6", "steps": [{"description": "Try F"}]},
            ],
            "executions": [
                [{"tool_name": "terminal", "success": False}],
                [{"tool_name": "terminal", "success": False}],
                [{"tool_name": "terminal", "success": False}],
                [{"tool_name": "terminal", "success": False}],
                [{"tool_name": "terminal", "success": False}],
                [{"tool_name": "terminal", "success": False}],
            ]
        },
        "expected_outputs": {
            "failed_patterns_count": 5,  # Limited to max
            "all_should_replan": True,
        }
    }
    
    trace_file = golden_traces_dir / "failed_pattern_accumulation.json"
    with open(trace_file, 'w') as f:
        json.dump(trace, f, indent=2)
    
    return trace


class TestGoldenTraceReplay:
    """Golden trace replay tests."""
    
    def test_golden_trace_successful_execution(self, golden_traces_dir):
        """Test with successful execution golden trace."""
        # Create trace if it doesn't exist
        try:
            trace = load_golden_trace("successful_execution", golden_traces_dir)
        except:
            trace = create_successful_execution_trace(golden_traces_dir)
        
        pea_loop = PlanExecuteAssessLoop()
        inputs = trace["inputs"]
        expected = trace["expected_outputs"]
        
        # Create plan
        plan = Plan(
            goal=inputs["plan"]["goal"],
            steps=inputs["plan"]["steps"]
        )
        pea_loop.current_plan = plan
        
        # Create executions
        executions = []
        for i, exec_data in enumerate(inputs["executions"]):
            executions.append(
                ActionExecution(
                    plan_id=plan.plan_id,
                    step_index=i,
                    tool_name=exec_data["tool_name"],
                    arguments={},
                    result={},
                    success=exec_data["success"],
                )
            )
        
        # Assess
        assessment = pea_loop.assess_execution(plan, executions)
        
        # Verify outputs match expected
        assert assessment.goal_achieved == expected["goal_achieved"]
        assert abs(assessment.success_rate - expected["success_rate"]) < 0.01
        assert assessment.should_replan == expected["should_replan"]
        assert pea_loop.current_phase.value == expected["final_phase"]
    
    def test_golden_trace_replan_success(self, golden_traces_dir):
        """Test with replan success golden trace."""
        try:
            trace = load_golden_trace("replan_success", golden_traces_dir)
        except:
            trace = create_replan_success_trace(golden_traces_dir)
        
        pea_loop = PlanExecuteAssessLoop(max_replan_attempts=3)
        inputs = trace["inputs"]
        expected = trace["expected_outputs"]
        
        # First plan
        plan1 = Plan(
            goal=inputs["plan1"]["goal"],
            steps=inputs["plan1"]["steps"]
        )
        executions1 = [
            ActionExecution(
                plan_id=plan1.plan_id,
                step_index=0,
                tool_name=exec_data["tool_name"],
                arguments={},
                result={},
                success=exec_data["success"],
            )
            for exec_data in inputs["executions1"]
        ]
        
        assessment1 = pea_loop.assess_execution(plan1, executions1)
        assert assessment1.goal_achieved == expected["assessment1"]["goal_achieved"]
        assert assessment1.should_replan == expected["assessment1"]["should_replan"]
        
        # Replan
        if assessment1.should_replan:
            pea_loop.enforce_assessment_phase(assessment1)
        
        # Second plan
        plan2 = Plan(
            goal=inputs["plan2"]["goal"],
            steps=inputs["plan2"]["steps"]
        )
        executions2 = [
            ActionExecution(
                plan_id=plan2.plan_id,
                step_index=0,
                tool_name=exec_data["tool_name"],
                arguments={},
                result={},
                success=exec_data["success"],
            )
            for exec_data in inputs["executions2"]
        ]
        
        assessment2 = pea_loop.assess_execution(plan2, executions2)
        assert assessment2.goal_achieved == expected["assessment2"]["goal_achieved"]
        assert assessment2.should_replan == expected["assessment2"]["should_replan"]
        assert pea_loop.replan_count == expected["final_replan_count"]
    
    def test_golden_trace_max_replans_reached(self, golden_traces_dir):
        """Test with max replans reached golden trace."""
        try:
            trace = load_golden_trace("max_replans_reached", golden_traces_dir)
        except:
            trace = create_max_replans_reached_trace(golden_traces_dir)
        
        inputs = trace["inputs"]
        expected = trace["expected_outputs"]
        
        pea_loop = PlanExecuteAssessLoop(max_replan_attempts=inputs["max_replan_attempts"])
        
        # Execute all plans
        for plan_data, execs_data in zip(inputs["plans"], inputs["executions"]):
            plan = Plan(
                goal=plan_data["goal"],
                steps=plan_data["steps"]
            )
            executions = [
                ActionExecution(
                    plan_id=plan.plan_id,
                    step_index=i,
                    tool_name=exec_data["tool_name"],
                    arguments={},
                    result={},
                    success=exec_data["success"],
                )
                for i, exec_data in enumerate(execs_data)
            ]
            
            assessment = pea_loop.assess_execution(plan, executions)
            if assessment.should_replan:
                pea_loop.enforce_assessment_phase(assessment)
        
        assert pea_loop.replan_count == expected["final_replan_count"]
        # Last assessment should not require replan (max reached)
        assert pea_loop.assessment_history[-1].should_replan == expected["final_should_replan"]
    
    def test_golden_trace_complex_multi_step(self, golden_traces_dir):
        """Test with complex multi-step golden trace."""
        try:
            trace = load_golden_trace("complex_multi_step", golden_traces_dir)
        except:
            trace = create_complex_multi_step_trace(golden_traces_dir)
        
        pea_loop = PlanExecuteAssessLoop()
        inputs = trace["inputs"]
        expected = trace["expected_outputs"]
        
        plan = Plan(
            goal=inputs["plan"]["goal"],
            steps=inputs["plan"]["steps"]
        )
        
        executions = [
            ActionExecution(
                plan_id=plan.plan_id,
                step_index=i,
                tool_name=exec_data["tool_name"],
                arguments={},
                result={},
                success=exec_data["success"],
            )
            for i, exec_data in enumerate(inputs["executions"])
        ]
        
        assessment = pea_loop.assess_execution(plan, executions)
        
        assert assessment.goal_achieved == expected["goal_achieved"]
        assert abs(assessment.success_rate - expected["success_rate"]) < 0.01
        assert len(executions) == expected["num_executions"]
    
    def test_golden_trace_failed_pattern_accumulation(self, golden_traces_dir):
        """Test with failed pattern accumulation golden trace."""
        try:
            trace = load_golden_trace("failed_pattern_accumulation", golden_traces_dir)
        except:
            trace = create_failed_pattern_accumulation_trace(golden_traces_dir)
        
        inputs = trace["inputs"]
        expected = trace["expected_outputs"]
        
        pea_loop = PlanExecuteAssessLoop(max_failed_patterns=inputs["max_failed_patterns"])
        
        # Execute all plans
        for plan_data, execs_data in zip(inputs["plans"], inputs["executions"]):
            plan = Plan(
                goal=plan_data["goal"],
                steps=plan_data["steps"]
            )
            executions = [
                ActionExecution(
                    plan_id=plan.plan_id,
                    step_index=0,
                    tool_name=exec_data["tool_name"],
                    arguments={},
                    result={},
                    success=exec_data["success"],
                )
                for exec_data in execs_data
            ]
            
            assessment = pea_loop.assess_execution(plan, executions)
            assert assessment.should_replan == expected["all_should_replan"]
        
        assert len(pea_loop.failed_patterns) == expected["failed_patterns_count"]

