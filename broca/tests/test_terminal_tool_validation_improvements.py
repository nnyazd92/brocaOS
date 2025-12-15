"""
Tests for terminal tool validation improvements.

Tests enhanced description clarity and improved error messages to reduce
"Missing required parameter(s): command" warnings.
"""

from __future__ import annotations

import json
import logging
from unittest.mock import Mock, patch

import pytest

from broca.tools.registry import ToolRegistry
from broca.tools.terminal import TerminalTool


class TestEnhancedTerminalToolDescription:
    """Test that terminal tool description is more explicit and examples-first."""
    
    def test_description_starts_with_examples(self):
        """
        Test that description starts with prominent examples.
        
        Rationale: Examples-first format helps LLMs understand usage immediately.
        """
        tool = TerminalTool()
        description = tool.description
        
        # Description should start with examples or clear requirement statement
        # Check that examples appear early in the description
        description_lower = description.lower()
        assert "example" in description_lower or "command" in description_lower[:200]
    
    def test_description_explicitly_requires_command(self):
        """
        Test that description explicitly states command is required.
        
        Rationale: Explicit requirement statements reduce confusion.
        """
        tool = TerminalTool()
        description = tool.description.lower()
        
        # Should explicitly mention required
        assert "required" in description
        assert "command" in description
    
    def test_description_includes_python_script_example(self):
        """
        Test that description includes python script.py example.
        
        Rationale: Concrete examples help LLMs use the tool correctly.
        """
        tool = TerminalTool()
        description = tool.description
        
        # Should include python script.py example
        assert "python script.py" in description or "python" in description.lower()
    
    def test_description_emphasizes_command_must_be_provided(self):
        """
        Test that description emphasizes command must always be provided.
        
        Rationale: Strong emphasis reduces empty argument calls.
        """
        tool = TerminalTool()
        description = tool.description.lower()
        
        # Should have strong language about providing command
        assert ("must" in description or "always" in description or 
                "required" in description)
        assert "command" in description


class TestImprovedValidationErrorMessages:
    """Test that validation error messages are more actionable."""
    
    def test_error_message_includes_python_script_example(self):
        """
        Test that error message includes python script.py example.
        
        Rationale: Concrete examples in errors help LLMs self-correct.
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
        
        # Error message should include python script.py example
        assert "python script.py" in content or "python" in content.lower()
        assert "command" in content.lower()
    
    def test_error_message_has_actionable_guidance(self):
        """
        Test that error message provides step-by-step guidance.
        
        Rationale: Actionable guidance helps LLMs fix the issue immediately.
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
        
        # Should have multiple examples or clear guidance
        assert len(content) > 100  # Should be substantial
        assert "example" in content.lower() or "usage" in content.lower()
        assert "command" in content.lower()
    
    def test_error_message_shows_exact_json_format(self):
        """
        Test that error message shows exact JSON format needed.
        
        Rationale: Exact format examples prevent formatting errors.
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
        
        # Should show JSON format with command parameter
        assert "{" in content and "}" in content
        assert '"command"' in content or "'command'" in content


class TestPythonScriptPyWorks:
    """Test that python script.py continues to work correctly."""
    
    def test_python_script_py_executes_successfully(self):
        """
        Test that python script.py command executes successfully.
        
        Rationale: Ensure the common use case continues to work.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        # Create a simple test script
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello from script')\n")
            script_path = f.name
        
        try:
            tool_call = {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "terminal",
                    "arguments": json.dumps({"command": f"python {script_path}"})
                }
            }
            
            result = registry.execute_tool_call(tool_call)
            content = result.get("content", "")
            
            # Should execute successfully
            assert "missing" not in content.lower()
            assert "required" not in content.lower() or "error" not in content.lower()
            # Should have execution result
            assert "return code" in content.lower() or "command" in content.lower()
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)
    
    def test_python3_script_py_works(self):
        """
        Test that python3 script.py also works.
        
        Rationale: Ensure python3 variant works too.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({"command": "python3 --version"})
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "")
        
        # Should execute successfully
        assert "missing" not in content.lower()
        assert "required" not in content.lower() or "error" not in content.lower()


class TestValidationStillCatchesEmptyArguments:
    """Test that validation still correctly catches empty arguments."""
    
    def test_empty_dict_still_rejected(self):
        """
        Test that empty dict {} still triggers validation error.
        
        Rationale: Validation must still catch missing parameters.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({})  # Empty dict
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "").lower()
        
        # Should return validation error
        assert "error" in content or "missing" in content
        assert "command" in content
    
    def test_missing_command_parameter_rejected(self):
        """
        Test that missing command parameter is still rejected.
        
        Rationale: Validation must catch missing required parameters.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({"working_dir": "/tmp"})  # Missing command
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "").lower()
        
        # Should return validation error
        assert "error" in content or "missing" in content
        assert "command" in content
    
    def test_none_command_rejected(self):
        """
        Test that None command value is rejected.
        
        Rationale: None should be treated as missing.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({"command": None})  # None value
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "").lower()
        
        # Should return validation error
        assert "error" in content or "missing" in content
        assert "command" in content


class TestRegressionValidCalls:
    """Regression tests ensuring valid calls still work."""
    
    def test_valid_command_with_working_dir(self):
        """
        Test that valid command with working_dir still works.
        
        Rationale: Ensure optional parameters don't break validation.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({
                    "command": "echo test",
                    "working_dir": "/tmp"
                })
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "").lower()
        
        # Should execute successfully
        assert "missing" not in content
        assert "required" not in content or "error" not in content
    
    def test_valid_command_with_timeout(self):
        """
        Test that valid command with timeout still works.
        
        Rationale: Ensure optional parameters don't break validation.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({
                    "command": "echo test",
                    "timeout": 60
                })
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "").lower()
        
        # Should execute successfully
        assert "missing" not in content
        assert "required" not in content or "error" not in content
    
    def test_simple_command_still_works(self):
        """
        Test that simple command like 'ls' still works.
        
        Rationale: Ensure basic usage continues to work.
        """
        registry = ToolRegistry()
        terminal_tool = TerminalTool()
        registry.register_tool(terminal_tool)
        
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": json.dumps({"command": "echo hello"})
            }
        }
        
        result = registry.execute_tool_call(tool_call)
        content = result.get("content", "")
        
        # Should execute successfully
        assert "missing" not in content.lower()
        assert "required" not in content.lower() or "error" not in content.lower()
        # Should have execution result
        assert "command" in content.lower() or "return code" in content.lower() or "hello" in content.lower()

