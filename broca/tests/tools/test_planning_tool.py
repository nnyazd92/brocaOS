"""
Tests for PlanningTool.

Uses TDD approach - tests define the expected behavior of the planning tool.
"""

import pytest
from typing import Dict, Any, List
from broca.tools.planning_tool import PlanningTool


class TestPlanningToolProtocol:
    """Test that PlanningTool implements the Tool protocol."""
    
    def test_tool_has_name_property(self):
        """Tool must have a name property."""
        tool = PlanningTool()
        assert hasattr(tool, 'name')
        assert isinstance(tool.name, str)
        assert tool.name == "planning"
    
    def test_tool_has_description_property(self):
        """Tool must have a description property."""
        tool = PlanningTool()
        assert hasattr(tool, 'description')
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        # Description should mention z3_validate integration
        assert "z3_validate" in tool.description.lower() or "z3" in tool.description.lower()
    
    def test_tool_has_parameters_property(self):
        """Tool must have a parameters property with JSON schema."""
        tool = PlanningTool()
        assert hasattr(tool, 'parameters')
        assert isinstance(tool.parameters, dict)
        assert tool.parameters.get("type") == "object"
        assert "properties" in tool.parameters
        assert "required" in tool.parameters
    
    def test_tool_has_execute_method(self):
        """Tool must have an execute method."""
        tool = PlanningTool()
        assert hasattr(tool, 'execute')
        assert callable(tool.execute)
    
    def test_tool_has_format_result_method(self):
        """Tool must have a format_result method."""
        tool = PlanningTool()
        assert hasattr(tool, 'format_result')
        assert callable(tool.format_result)


class TestPlanningToolParameters:
    """Test parameter schema validation."""
    
    def test_parameters_include_required_fields(self):
        """Parameters schema must include goal and steps as required."""
        tool = PlanningTool()
        required = tool.parameters.get("required", [])
        assert "goal" in required
        assert "steps" in required
    
    def test_parameters_include_optional_fields(self):
        """Parameters schema should include optional fields."""
        tool = PlanningTool()
        properties = tool.parameters.get("properties", {})
        assert "goal" in properties
        assert "steps" in properties
        assert "context" in properties
        assert "assumptions" in properties
        assert "expected_outcomes" in properties
    
    def test_steps_is_array_type(self):
        """Steps parameter must be an array."""
        tool = PlanningTool()
        properties = tool.parameters.get("properties", {})
        steps_schema = properties.get("steps", {})
        assert steps_schema.get("type") == "array"
        assert "items" in steps_schema


class TestPlanningToolExecution:
    """Test plan generation and execution."""
    
    def test_execute_with_minimal_required_params(self):
        """Tool should execute with only goal and steps."""
        tool = PlanningTool()
        result = tool.execute(
            goal="Test goal",
            steps=["Step 1", "Step 2"]
        )
        
        assert isinstance(result, dict)
        assert result.get("goal") == "Test goal"
        assert result.get("steps") == ["Step 1", "Step 2"]
        assert "plan_id" in result
        assert "created_at" in result
    
    def test_execute_with_all_params(self):
        """Tool should execute with all parameters."""
        tool = PlanningTool()
        result = tool.execute(
            goal="Complete task",
            steps=["Step 1", "Step 2", "Step 3"],
            context="Some context",
            assumptions=["Assumption 1", "Assumption 2"],
            expected_outcomes=["Outcome 1", "Outcome 2"]
        )
        
        assert result.get("goal") == "Complete task"
        assert result.get("steps") == ["Step 1", "Step 2", "Step 3"]
        assert result.get("context") == "Some context"
        assert result.get("assumptions") == ["Assumption 1", "Assumption 2"]
        assert result.get("expected_outcomes") == ["Outcome 1", "Outcome 2"]
    
    def test_execute_generates_unique_plan_ids(self):
        """Each plan should have a unique plan_id."""
        tool = PlanningTool()
        result1 = tool.execute(goal="Goal 1", steps=["Step 1"])
        result2 = tool.execute(goal="Goal 2", steps=["Step 2"])
        
        assert result1.get("plan_id") != result2.get("plan_id")
    
    def test_execute_handles_empty_steps(self):
        """Tool should handle empty steps list gracefully."""
        tool = PlanningTool()
        result = tool.execute(goal="Goal", steps=[])
        
        assert result.get("goal") == "Goal"
        assert result.get("steps") == []
    
    def test_execute_handles_none_optional_params(self):
        """Tool should handle None for optional parameters."""
        tool = PlanningTool()
        result = tool.execute(
            goal="Goal",
            steps=["Step 1"],
            context=None,
            assumptions=None,
            expected_outcomes=None
        )
        
        assert result.get("goal") == "Goal"
        assert result.get("steps") == ["Step 1"]
        # Optional fields should be None or not present
        assert result.get("context") is None or "context" not in result
        assert result.get("assumptions") is None or "assumptions" not in result
        assert result.get("expected_outcomes") is None or "expected_outcomes" not in result


class TestPlanningToolFormatResult:
    """Test result formatting for LLM consumption."""
    
    def test_format_result_returns_string(self):
        """format_result should return a string."""
        tool = PlanningTool()
        result = tool.execute(goal="Test", steps=["Step 1"])
        formatted = tool.format_result(result)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
    
    def test_format_result_includes_goal(self):
        """Formatted result should include the goal."""
        tool = PlanningTool()
        result = tool.execute(goal="Test goal", steps=["Step 1"])
        formatted = tool.format_result(result)
        
        assert "Test goal" in formatted or "goal" in formatted.lower()
    
    def test_format_result_includes_steps(self):
        """Formatted result should include steps."""
        tool = PlanningTool()
        result = tool.execute(goal="Test", steps=["Step 1", "Step 2"])
        formatted = tool.format_result(result)
        
        assert "Step 1" in formatted
        assert "Step 2" in formatted
    
    def test_format_result_includes_optional_fields_when_present(self):
        """Formatted result should include optional fields when provided."""
        tool = PlanningTool()
        result = tool.execute(
            goal="Test",
            steps=["Step 1"],
            assumptions=["Assumption 1"],
            expected_outcomes=["Outcome 1"]
        )
        formatted = tool.format_result(result)
        
        # Should mention assumptions and outcomes if present
        assert "Assumption 1" in formatted or "assumption" in formatted.lower()
        assert "Outcome 1" in formatted or "outcome" in formatted.lower()


class TestPlanningToolZ3Integration:
    """Test that tool description mentions Z3 integration."""
    
    def test_description_mentions_z3_validate(self):
        """Tool description should mention z3_validate tool."""
        tool = PlanningTool()
        description = tool.description.lower()
        
        # Should mention z3_validate or z3 validation
        assert ("z3_validate" in description or 
                "z3" in description or 
                "logical" in description or
                "validate" in description)
    
    def test_description_guides_llm_to_use_z3(self):
        """Description should guide LLM on how to use z3_validate."""
        tool = PlanningTool()
        description = tool.description
        
        # Should provide guidance on Z3 usage
        assert len(description) > 100  # Should be descriptive


class TestPlanningToolErrorHandling:
    """Test error handling for invalid inputs."""
    
    def test_execute_handles_empty_goal(self):
        """Tool should handle empty goal string."""
        tool = PlanningTool()
        result = tool.execute(goal="", steps=["Step 1"])
        
        # Should still return a result (validation can be lenient)
        assert isinstance(result, dict)
        assert "plan_id" in result
    
    def test_execute_handles_very_long_inputs(self):
        """Tool should handle very long strings."""
        tool = PlanningTool()
        long_goal = "A" * 10000
        long_steps = ["B" * 1000] * 10
        
        result = tool.execute(goal=long_goal, steps=long_steps)
        
        assert isinstance(result, dict)
        assert result.get("goal") == long_goal
        assert len(result.get("steps", [])) == 10

