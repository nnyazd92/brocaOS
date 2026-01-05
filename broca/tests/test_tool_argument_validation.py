"""
Tests for tool argument validation.

Tests that required tool parameters are validated before execution,
preventing TypeError when LLM calls tools without required parameters.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json
import logging
import os

from broca.tools.registry import ToolRegistry
from broca.tools.terminal import TerminalTool
from broca.tools.primitive_io import WriteFileTool, PatchFileTool


class LogCapture:
    """Capture log records for testing."""
    
    def __init__(self, logger_name: str, level: int = logging.INFO):
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
                "optional_param": {"type": "string"}
            },
            "required": self._required_params
        }
    
    def execute(self, **kwargs):
        return {"result": f"Executed {self._name}"}
    
    def format_result(self, result: dict) -> str:
        return f"Result: {result}"


class TestToolArgumentValidation:
    """Test tool argument validation."""
    
    def test_missing_required_parameter(self):
        """
        Test that missing required parameter is detected.
        
        Rationale: Ensures validation catches missing required parameters.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1"])
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({})  # Missing param1
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Should return error message, not raise exception
        assert "error" in result.get("content", "").lower() or "missing" in result.get("content", "").lower()
        assert "param1" in result.get("content", "")
    
    def test_missing_required_parameter_error_message(self):
        """
        Test error message format for missing parameters.
        
        Rationale: Ensures error messages are clear and helpful.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1", "param2"])
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param1": "value1"})  # Missing param2
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "")
        
        # Error message should mention missing parameters
        assert "missing" in content.lower() or "required" in content.lower()
        assert "param2" in content
        assert "test_tool" in content
    
    def test_all_required_parameters_present(self):
        """
        Test that validation passes when all required params are present.
        
        Rationale: Ensures valid tool calls still work correctly.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1"])
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param1": "value1"})
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Should execute successfully, not return error
        assert "error" not in result.get("content", "").lower()
        assert "result" in result.get("content", "").lower() or "executed" in result.get("content", "").lower()
    
    def test_optional_parameters_missing(self):
        """
        Test that optional parameters can be missing.
        
        Rationale: Ensures only required parameters are validated.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1"])
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param1": "value1"})  # optional_param missing, that's OK
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Should execute successfully
        assert "error" not in result.get("content", "").lower()
    
    def test_multiple_required_parameters(self):
        """
        Test validation with multiple required parameters.
        
        Rationale: Ensures validation handles multiple required params correctly.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1", "param2"])
        registry.register_tool(tool)
        
        # Missing both
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({})
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "")
        
        assert "missing" in content.lower() or "required" in content.lower()
        assert "param1" in content or "param2" in content
    
    def test_validation_logging(self):
        """
        Test that validation failures are logged.
        
        Rationale: Ensures validation failures are tracked for debugging.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1"])
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({})  # Missing param1
            }
        }
        
        with LogCapture("broca.tools.registry") as logs:
            registry.execute_tool_call(tool_call)
        
        # Should log validation failure
        assert logs.has_event("tool_argument_validation_failed")
    
    def test_validation_in_tool_registry(self):
        """
        Test validation integrated in ToolRegistry.execute_tool_call().
        
        Rationale: Ensures validation works in the full execution flow.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1"])
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({})  # Missing param1
            }
        }
        
        # Should not raise exception
        result = registry.execute_tool_call(tool_call)
        
        # Should return error message
        assert result.get("role") == "tool"
        assert result.get("name") == "test_tool"
        assert "error" in result.get("content", "").lower() or "missing" in result.get("content", "").lower()
    
    def test_terminal_tool_missing_command(self, normal_tools_mode):
        """
        Test validation with actual TerminalTool missing command parameter.
        
        Rationale: Ensures validation works with real tools.
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
        
        # Should return error message, not raise TypeError
        assert "error" in result.get("content", "").lower() or "missing" in result.get("content", "").lower()
        assert "command" in result.get("content", "")
        # Should not contain TypeError traceback
        assert "TypeError" not in result.get("content", "")

    def test_write_file_missing_content_has_actionable_guidance(self, normal_tools_mode):
        """
        Test that WRITE_FILE missing required 'content' returns actionable guidance.

        Rationale: Prevents repeated tool-call loops by teaching the model to READ_FILE then WRITE_FILE with content.
        """
        registry = ToolRegistry()
        registry.register_tool(WriteFileTool())

        tool_call = {
            "id": "call_write_missing_content",
            "type": "function",
            "function": {
                "name": "WRITE_FILE",
                "arguments": json.dumps({"path": "/tmp/example.txt"}),  # Missing content
            },
        }

        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "")

        assert "missing" in content.lower() or "required" in content.lower()
        assert "content" in content
        assert "READ_FILE" in content  # plan: explicit READ_FILE → WRITE_FILE recovery
        assert "WRITE_FILE" in content

    def test_patch_file_no_edits_provided_includes_examples(self, normal_tools_mode, tmp_path):
        """
        Test that PATCH_FILE called without edits/unified_diff returns self-correcting guidance.

        Rationale: PATCH_FILE requires either edits or unified_diff; the error should include examples mentioning edits.
        """
        target = tmp_path / "a.txt"
        target.write_text("one\ntwo\nthree\n", encoding="utf-8")

        registry = ToolRegistry()
        registry.register_tool(PatchFileTool())

        tool_call = {
            "id": "call_patch_no_edits",
            "type": "function",
            "function": {
                "name": "PATCH_FILE",
                "arguments": json.dumps({"path": str(target)}),  # No edits/unified_diff
            },
        }

        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "")

        assert "no_edits_provided" in content
        assert "edits" in content  # plan: mention edits guidance
        assert "unified_diff" in content  # plan: mention unified diff alternative
    
    def test_none_value_treated_as_missing(self):
        """
        Test that None values for required parameters are treated as missing.
        
        Rationale: Ensures None is not considered a valid value for required params.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1"])
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param1": None})  # None value
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Should treat None as missing
        assert "missing" in result.get("content", "").lower() or "required" in result.get("content", "").lower()
    
    def test_empty_string_not_treated_as_missing(self):
        """
        Test that empty string is treated as a valid value (not missing).
        
        Rationale: Empty string might be a valid value for some tools.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool", required_params=["param1"])
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param1": ""})  # Empty string
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        
        # Empty string should be considered present (validation passes)
        # Tool execution might fail, but that's a different issue
        # The key is that validation doesn't reject it
        # Actually, let's check if it executes or returns validation error
        # If tool.execute handles empty string, it should execute
        # If validation rejects empty string, it should return validation error
        # For now, we'll just ensure it doesn't raise TypeError about missing parameter
        assert "missing" not in result.get("content", "").lower() or "executed" in result.get("content", "").lower()

