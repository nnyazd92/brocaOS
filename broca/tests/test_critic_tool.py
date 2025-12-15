"""
Unit tests for CriticTool.

Tests the critic tool that validates LLM responses against constraints.
"""

from __future__ import annotations

from unittest.mock import Mock, MagicMock, patch
import pytest
import json

from broca.tools.critic import CriticTool
from broca.llm.deepseek_client import DeepSeekClient
from broca.tests.utils import build_llm_response


class TestCriticToolInitialization:
    """Test CriticTool initialization."""
    
    def test_init_with_default_llm(self):
        """
        Test initialization with default LLM client.
        
        Rationale: Ensures tool can be created without explicit LLM client.
        """
        tool = CriticTool()
        assert tool._llm is not None
        assert isinstance(tool._llm, DeepSeekClient)
    
    def test_init_with_custom_llm(self):
        """
        Test initialization with custom LLM client.
        
        Rationale: Ensures dependency injection works for testing.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        tool = CriticTool(llm_client=mock_llm)
        assert tool._llm == mock_llm
    
    def test_init_with_custom_system_prompt(self):
        """
        Test initialization with custom system prompt template.
        
        Rationale: Ensures custom prompts can be provided.
        """
        custom_template = "Custom critical prompt: {constraints}"
        tool = CriticTool(system_prompt_template=custom_template)
        assert tool._system_prompt_template == custom_template
    
    def test_init_with_default_system_prompt(self):
        """
        Test initialization uses default system prompt if none provided.
        
        Rationale: Ensures sensible defaults are used.
        """
        tool = CriticTool()
        assert tool._system_prompt_template is not None
        assert len(tool._system_prompt_template) > 0


class TestCriticToolProperties:
    """Test Tool protocol compliance."""
    
    def test_name_property(self):
        """
        Test that name property returns 'critic'.
        
        Rationale: Ensures tool identifier is correct.
        """
        tool = CriticTool()
        assert tool.name == "critic"
    
    def test_description_property(self):
        """
        Test that description property is non-empty.
        
        Rationale: Ensures LLM can understand when to use the tool.
        """
        tool = CriticTool()
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert "critic" in tool.description.lower() or "validate" in tool.description.lower()
    
    def test_parameters_property(self):
        """
        Test that parameters property returns valid JSON schema.
        
        Rationale: Ensures tool parameters are properly defined.
        """
        tool = CriticTool()
        params = tool.parameters
        
        assert isinstance(params, dict)
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        
        # Check required fields
        assert "world_state" in params["required"]
        assert "content" in params["required"]
        
        # Check world_state structure
        world_state_props = params["properties"]["world_state"]
        assert world_state_props["type"] == "object"
        assert "properties" in world_state_props
        assert "constraints" in world_state_props["properties"]
        assert "metadata" in world_state_props["properties"]


class TestCriticToolExecute:
    """Test CriticTool execution."""
    
    def test_execute_with_accepted_response(self):
        """
        Test execution when response is accepted.
        
        Rationale: Ensures successful validation works correctly.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.return_value = build_llm_response(
            content=json.dumps({
                "accepted": True,
                "feedback": "The response meets all constraints.",
                "violations": []
            })
        )
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {
            "metadata": {"context": "test"},
            "constraints": {"rigor": "Be rigorous"}
        }
        content = "This is a valid response."
        
        result = tool.execute(world_state=world_state, content=content)
        
        assert result["accepted"] is True
        assert "feedback" in result
        assert "violations" in result
        assert len(result["violations"]) == 0
        
        # Verify LLM was called with correct messages
        mock_llm.chat.assert_called_once()
        call_args = mock_llm.chat.call_args[0][0]
        assert len(call_args) == 2  # system + user
        assert call_args[0]["role"] == "system"
        assert call_args[1]["role"] == "user"
        assert content in call_args[1]["content"]
    
    def test_execute_with_rejected_response(self):
        """
        Test execution when response is rejected.
        
        Rationale: Ensures validation failures are properly detected.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.return_value = build_llm_response(
            content=json.dumps({
                "accepted": False,
                "feedback": "The response violates the rigor constraint.",
                "violations": [
                    {
                        "constraint": "rigor",
                        "description": "Step 3 lacks justification"
                    }
                ]
            })
        )
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {
            "metadata": {"context": "mathematical proof"},
            "constraints": {
                "rigor": "All steps must be mathematically rigorous"
            }
        }
        content = "This response lacks rigor."
        
        result = tool.execute(world_state=world_state, content=content)
        
        assert result["accepted"] is False
        assert "feedback" in result
        assert "violations" in result
        assert len(result["violations"]) == 1
        assert result["violations"][0]["constraint"] == "rigor"
    
    def test_execute_system_prompt_generation(self):
        """
        Test that system prompt is generated correctly from world_state.
        
        Rationale: Ensures constraints and metadata are properly formatted.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.return_value = build_llm_response(
            content=json.dumps({"accepted": True, "feedback": "OK", "violations": []})
        )
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {
            "metadata": {
                "context": "mathematical proof",
                "domain": "physics"
            },
            "constraints": {
                "no_assumptions": "Do not make unstated assumptions",
                "rigor": "All steps must be mathematically rigorous"
            }
        }
        content = "Test content"
        
        tool.execute(world_state=world_state, content=content)
        
        # Verify system prompt contains constraints
        call_args = mock_llm.chat.call_args[0][0]
        system_prompt = call_args[0]["content"]
        
        assert "critical" in system_prompt.lower() or "validator" in system_prompt.lower()
        assert "no_assumptions" in system_prompt or "unstated assumptions" in system_prompt
        assert "rigor" in system_prompt or "mathematically rigorous" in system_prompt
    
    def test_execute_with_metadata(self):
        """
        Test that metadata is included in system prompt when provided.
        
        Rationale: Ensures context information is passed to critic.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.return_value = build_llm_response(
            content=json.dumps({"accepted": True, "feedback": "OK", "violations": []})
        )
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {
            "metadata": {
                "context": "mathematical proof",
                "domain": "physics"
            },
            "constraints": {"rigor": "Be rigorous"}
        }
        content = "Test"
        
        tool.execute(world_state=world_state, content=content)
        
        call_args = mock_llm.chat.call_args[0][0]
        system_prompt = call_args[0]["content"]
        
        # Metadata should be mentioned in prompt
        assert "mathematical proof" in system_prompt or "physics" in system_prompt
    
    def test_execute_without_metadata(self):
        """
        Test execution works without metadata.
        
        Rationale: Ensures metadata is optional.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.return_value = build_llm_response(
            content=json.dumps({"accepted": True, "feedback": "OK", "violations": []})
        )
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {
            "constraints": {"rigor": "Be rigorous"}
        }
        content = "Test"
        
        result = tool.execute(world_state=world_state, content=content)
        
        assert result["accepted"] is True
    
    def test_execute_malformed_json_response(self):
        """
        Test handling of malformed JSON response from LLM.
        
        Rationale: Ensures tool handles invalid responses gracefully.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.return_value = build_llm_response(
            content="This is not valid JSON"
        )
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {"constraints": {"rigor": "Be rigorous"}}
        content = "Test"
        
        result = tool.execute(world_state=world_state, content=content)
        
        # Should handle gracefully - either return error or default values
        assert "accepted" in result or "error" in result
    
    def test_execute_missing_required_fields(self):
        """
        Test handling of JSON response missing required fields.
        
        Rationale: Ensures tool handles incomplete responses.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.return_value = build_llm_response(
            content=json.dumps({"feedback": "Some feedback"})  # Missing accepted
        )
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {"constraints": {"rigor": "Be rigorous"}}
        content = "Test"
        
        result = tool.execute(world_state=world_state, content=content)
        
        # Should handle gracefully
        assert "accepted" in result or "error" in result


class TestCriticToolFormatResult:
    """Test result formatting."""
    
    def test_format_result_accepted(self):
        """
        Test formatting of accepted result.
        
        Rationale: Ensures formatted output is readable for LLM.
        """
        tool = CriticTool()
        
        result = {
            "accepted": True,
            "feedback": "The response meets all constraints.",
            "violations": []
        }
        
        formatted = tool.format_result(result)
        
        assert isinstance(formatted, str)
        assert "accepted" in formatted.lower() or "pass" in formatted.lower()
        assert "feedback" in formatted.lower() or result["feedback"] in formatted
    
    def test_format_result_rejected(self):
        """
        Test formatting of rejected result with violations.
        
        Rationale: Ensures violations are clearly communicated.
        """
        tool = CriticTool()
        
        result = {
            "accepted": False,
            "feedback": "The response violates constraints.",
            "violations": [
                {
                    "constraint": "rigor",
                    "description": "Step 3 lacks justification"
                }
            ]
        }
        
        formatted = tool.format_result(result)
        
        assert isinstance(formatted, str)
        assert "rejected" in formatted.lower() or "violat" in formatted.lower()
        assert "rigor" in formatted or "justification" in formatted
    
    def test_format_result_with_multiple_violations(self):
        """
        Test formatting with multiple violations.
        
        Rationale: Ensures all violations are included in output.
        """
        tool = CriticTool()
        
        result = {
            "accepted": False,
            "feedback": "Multiple violations found.",
            "violations": [
                {"constraint": "rigor", "description": "Issue 1"},
                {"constraint": "completeness", "description": "Issue 2"}
            ]
        }
        
        formatted = tool.format_result(result)
        
        assert "rigor" in formatted or "Issue 1" in formatted
        assert "completeness" in formatted or "Issue 2" in formatted


class TestCriticToolErrorHandling:
    """Test error handling scenarios."""
    
    def test_execute_llm_error(self):
        """
        Test handling of LLM errors.
        
        Rationale: Ensures tool handles LLM failures gracefully.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.side_effect = Exception("LLM error")
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {"constraints": {"rigor": "Be rigorous"}}
        content = "Test"
        
        result = tool.execute(world_state=world_state, content=content)
        
        # Should return error information
        assert "error" in result or "accepted" not in result
    
    def test_execute_invalid_world_state(self):
        """
        Test handling of invalid world_state structure.
        
        Rationale: Ensures tool validates input structure.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        tool = CriticTool(llm_client=mock_llm)
        
        # Missing constraints
        world_state = {"metadata": {"context": "test"}}
        content = "Test"
        
        # Should handle gracefully - either raise error or use defaults
        try:
            result = tool.execute(world_state=world_state, content=content)
            # If it doesn't raise, should handle gracefully
            assert isinstance(result, dict)
        except (ValueError, KeyError):
            # Expected if validation is strict
            pass
    
    def test_execute_empty_content(self):
        """
        Test handling of empty content.
        
        Rationale: Ensures tool handles edge cases.
        """
        mock_llm = Mock(spec=DeepSeekClient)
        mock_llm.chat.return_value = build_llm_response(
            content=json.dumps({"accepted": False, "feedback": "Empty content", "violations": []})
        )
        
        tool = CriticTool(llm_client=mock_llm)
        
        world_state = {"constraints": {"rigor": "Be rigorous"}}
        content = ""
        
        result = tool.execute(world_state=world_state, content=content)
        
        assert isinstance(result, dict)

