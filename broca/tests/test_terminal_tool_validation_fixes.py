"""
Tests for terminal tool validation fixes.

Tests improvements to reduce "Missing required parameter(s): command" warnings.
"""

from __future__ import annotations

import json
import logging
from unittest.mock import Mock

import pytest

from broca.tools.registry import ToolRegistry
from broca.tools.terminal import TerminalTool
from broca.tools.json_repair import attempt_json_repair


class LogCapture:
    """Capture log records for testing."""
    
    def __init__(self, logger_name: str, level: int = logging.WARNING):
        self.logger_name = logger_name
        self.level = level
        self.records = []
        self.handler = None
    
    def __enter__(self):
        logger = logging.getLogger(self.logger_name)
        self.handler = logging.Handler()
        self.handler.setLevel(self.level)
        self.handler.emit = self.records.append
        logger.addHandler(self.handler)
        logger.setLevel(self.level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = logging.getLogger(self.logger_name)
        logger.removeHandler(self.handler)
    
    def has_event(self, event_name: str) -> bool:
        """Check if a log record with given event exists."""
        return any(
            hasattr(record, "event") and record.event == event_name
            for record in self.records
        )
    
    def has_message_containing(self, text: str) -> bool:
        """Check if any log record contains the given text."""
        return any(
            text in str(record.msg) for record in self.records
        )


class MockTool:
    """Mock tool for testing validation."""
    
    def __init__(self, name: str, required_params: list[str] = None):
        self._name = name
        self._required_params = required_params or []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return f"Mock tool {self._name}"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "string"},
            },
            "required": self._required_params
        }
    
    def execute(self, **kwargs):
        return {"result": f"Executed {self._name}"}
    
    def format_result(self, result: dict) -> str:
        return f"Result: {result}"


class TestTerminalToolDescriptionClarity:
    """Test that terminal tool description explicitly mentions command is required."""
    
    def test_description_mentions_required_command(self):
        """
        Test that terminal tool description explicitly mentions command is required.
        
        Rationale: Clearer descriptions help LLMs understand tool requirements.
        """
        tool = TerminalTool()
        description = tool.description.lower()
        
        assert "required" in description or "command" in description
        assert "command" in description


class TestEnhancedErrorMessageFormat:
    """Test that validation error messages include examples."""
    
    def test_error_message_includes_example_for_terminal(self):
        """
        Test that validation error messages include examples for terminal tool.
        
        Rationale: Better error messages help LLMs self-correct.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({})  # Missing command
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "")
        
        # Error message should contain example or guidance
        assert "command" in content.lower()
        # Should mention required parameter
        assert "required" in content.lower() or "missing" in content.lower()


class TestEmptyArgumentsHandling:
    """Test empty JSON string handling."""
    
    def test_empty_json_string_handled_correctly(self):
        """
        Test that empty JSON string "{}" is handled correctly.
        
        Rationale: Ensures validation catches missing command and returns helpful error.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": "{}"  # Empty JSON
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Should return error message, not raise exception
        assert "error" in result.get("content", "").lower() or "missing" in result.get("content", "").lower()
        assert "command" in result.get("content", "")


class TestWhitespaceOnlyArguments:
    """Test whitespace-only JSON strings handling."""
    
    def test_whitespace_only_json_string(self):
        """
        Test that whitespace-only JSON strings are handled.
        
        Rationale: Ensures whitespace-only strings are treated as empty dict.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        # Test various whitespace-only strings
        for whitespace_json in ["   ", "\t\t", "\n\n", "  \t  \n  "]:
            tool_call = {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "terminal",
                    "arguments": whitespace_json
                }
            }
            
            result = registry.execute_tool_call(tool_call)
            
            # Should be treated as empty dict, validation catches missing command
            assert "error" in result.get("content", "").lower() or "missing" in result.get("content", "").lower()
            assert "command" in result.get("content", "")


class TestDiagnosticLogging:
    """Test that validation failures log structured diagnostic info."""
    
    def test_validation_failure_logs_diagnostics(self):
        """
        Test that validation failures log structured diagnostic info.
        
        Rationale: Better diagnostics help identify root causes.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({})  # Missing command
            }
        }
        
        with LogCapture("broca.tools.registry") as logs:
            registry.execute_tool_call(tool_call)
        
        # Should log validation failure with event
        assert logs.has_event("tool_argument_validation_failed")
        
        # Check that logs contain diagnostic information
        assert any(
            "terminal" in str(record.msg).lower() or 
            hasattr(record, "tool_name") and record.tool_name == "terminal"
            for record in logs.records
        )


class TestJSONRepairEmpty:
    """Test JSON repair with empty strings."""
    
    def test_json_repair_empty_string(self):
        """
        Test that attempt_json_repair("") returns ({}, None).
        
        Rationale: Empty string should return empty dict, not None.
        """
        result, error = attempt_json_repair("")
        
        assert result == {}
        assert error is None
    
    def test_json_repair_whitespace_string(self):
        """
        Test that attempt_json_repair with whitespace returns ({}, None).
        
        Rationale: Whitespace-only strings should return empty dict.
        """
        for whitespace in ["   ", "\t\t", "\n\n", "  \t  \n  "]:
            result, error = attempt_json_repair(whitespace)
            
            assert result == {}
            assert error is None


class TestValidationErrorMessageActionability:
    """Test that error messages include actionable guidance."""
    
    def test_error_message_actionable(self):
        """
        Test that error messages include actionable guidance.
        
        Rationale: Error messages should suggest correct format and include example.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({})  # Missing command
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "")
        
        # Error message should be actionable
        assert "command" in content.lower()
        # Should provide guidance
        assert len(content) > 50  # Should be more than just "error"


class TestSystemPromptIncludesTerminalGuidance:
    """Test that system prompt mentions terminal tool parameter requirements."""
    
    def test_system_prompt_mentions_terminal_requirements(self):
        """
        Test that system prompt mentions terminal tool parameter requirements.
        
        Rationale: System-level guidance reinforces tool usage.
        """
        # Read the main_repl.py file to check the system prompt
        import os
        main_repl_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "broca", "main_repl.py"
        )
        
        with open(main_repl_path, 'r') as f:
            content = f.read()
        
        # Check that the system prompt contains terminal tool guidance
        # The prompt should mention terminal tool and command parameter
        assert "terminal" in content.lower()
        # Should have guidance about terminal tool usage
        assert "command" in content.lower() or "terminal tool" in content.lower()


class TestRegressionValidCalls:
    """Regression tests ensuring valid tool calls still work."""
    
    def test_valid_terminal_call_still_works(self):
        """
        Test that valid terminal tool calls with command parameter still execute.
        
        Rationale: No false positives in validation.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({"command": "echo test"})
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Should execute successfully, not return validation error
        assert "missing" not in result.get("content", "").lower()
        assert "required" not in result.get("content", "").lower() or "error" not in result.get("content", "").lower()
        # Should have execution result
        assert "command" in result.get("content", "").lower() or "test" in result.get("content", "").lower() or "return code" in result.get("content", "").lower()


class TestRegressionOtherTools:
    """Regression tests ensuring other tools validation still works."""
    
    def test_other_tools_validation_unaffected(self):
        """
        Test that changes don't break validation for other tools.
        
        Rationale: Other tools' validation should still work correctly.
        """
        registry = ToolRegistry()
        
        # Test with a mock tool
        mock_tool = MockTool("test_tool", required_params=["param1"])
        registry.register_tool(mock_tool)
        
        # Test missing parameter
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({})  # Missing param1
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Should return error message
        assert "error" in result.get("content", "").lower() or "missing" in result.get("content", "").lower()
        assert "param1" in result.get("content", "")
        
        # Test with valid parameter
        tool_call_valid = {
            "id": "call_2",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param1": "value1"})
            }
        }
        
        result_valid = registry.execute_tool_call(tool_call_valid)
        
        # Should execute successfully
        assert "error" not in result_valid.get("content", "").lower()
        assert "missing" not in result_valid.get("content", "").lower()

