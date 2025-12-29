"""
Mutation testing for terminal tool error handling.

Tests that ensure mutations (code changes) in error handling are caught by the test suite.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.tools.terminal import TerminalTool


class TestTerminalToolErrorHandlingMutations:
    """Mutation tests for error handling paths."""
    
    @patch('broca.tools.terminal.subprocess.run')
    def test_error_field_must_be_populated_when_stderr_exists(self, mock_subprocess):
        """
        Mutation: If error field is not populated from stderr, test fails.
        
        Rationale: Ensures error field is always populated when command fails with stderr.
        """
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error message"
        mock_subprocess.return_value = mock_result
        
        tool = TerminalTool()
        result = tool.execute(command="test_command")
        
        # Mutation: Removed error field population
        assert "error" in result, "error field must be populated when command fails"
        assert result["error"] == "Error message", "error field must contain stderr content"
    
    @patch('broca.tools.terminal.subprocess.run')
    def test_error_field_must_use_stderr_not_stdout(self, mock_subprocess):
        """
        Mutation: If error field uses stdout instead of stderr, test fails.
        
        Rationale: Ensures error field uses stderr content, not stdout.
        """
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "stdout content"
        mock_result.stderr = "stderr content"
        mock_subprocess.return_value = mock_result
        
        tool = TerminalTool()
        result = tool.execute(command="test_command")
        
        # Mutation: Changed to use stdout instead of stderr
        assert result["error"] == "stderr content", "error field must use stderr, not stdout"
        assert result["error"] != "stdout content", "error field must not use stdout"
    
    @patch('broca.tools.terminal.subprocess.run')
    def test_error_field_must_strip_whitespace_from_stderr(self, mock_subprocess):
        """
        Mutation: If error field doesn't strip whitespace, test fails.
        
        Rationale: Ensures error field contains clean content without leading/trailing whitespace.
        """
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "  \n  Error message  \n  "
        mock_subprocess.return_value = mock_result
        
        tool = TerminalTool()
        result = tool.execute(command="test_command")
        
        # Mutation: Removed .strip() call
        assert result["error"] == "Error message", "error field must strip whitespace from stderr"
        assert not result["error"].startswith(" "), "error field must not have leading whitespace"
        assert not result["error"].endswith(" "), "error field must not have trailing whitespace"
    
    @patch('broca.tools.terminal.subprocess.run')
    def test_error_field_must_use_returncode_when_stderr_empty(self, mock_subprocess):
        """
        Mutation: If error field doesn't use returncode when stderr is empty, test fails.
        
        Rationale: Ensures error field has meaningful content even when stderr is empty.
        """
        mock_result = Mock()
        mock_result.returncode = 127
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        tool = TerminalTool()
        result = tool.execute(command="test_command")
        
        # Mutation: Removed returncode-based error message
        assert "error" in result, "error field must be populated even when stderr is empty"
        assert "127" in result["error"], "error field must include returncode when stderr is empty"
        assert "return code" in result["error"].lower(), "error field must mention return code"
    
    @patch('broca.tools.terminal.subprocess.run')
    def test_error_field_must_not_be_populated_on_success(self, mock_subprocess):
        """
        Mutation: If error field is populated on success, test fails.
        
        Rationale: Ensures error field is only populated when command fails.
        """
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        tool = TerminalTool()
        result = tool.execute(command="test_command")
        
        # Mutation: Added error field population on success
        assert result["success"] is True, "command should succeed"
        assert "error" not in result, "error field must not be populated on success"
    
    def test_format_result_must_use_error_field_when_present(self):
        """
        Mutation: If format_result doesn't use error field when present, test fails.
        
        Rationale: Ensures format_result prioritizes explicit error field.
        """
        tool = TerminalTool()
        result = {
            "success": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "stderr message",
            "error": "error field message",
            "command": "test_command"
        }
        
        formatted = tool.format_result(result)
        
        # Mutation: Changed to use stderr instead of error field
        assert "error field message" in formatted, "format_result must use error field when present"
    
    def test_format_result_must_fallback_to_stderr_when_no_error_field(self):
        """
        Mutation: If format_result doesn't fallback to stderr, test fails.
        
        Rationale: Ensures format_result handles legacy results without error field.
        """
        tool = TerminalTool()
        result = {
            "success": False,
            "returncode": 2,
            "stdout": "",
            "stderr": "stderr fallback message",
            "command": "test_command"
        }
        
        formatted = tool.format_result(result)
        
        # Mutation: Removed stderr fallback logic
        assert "stderr fallback message" in formatted, "format_result must fallback to stderr when no error field"
    
    def test_format_result_must_fallback_to_returncode_when_no_error_or_stderr(self):
        """
        Mutation: If format_result doesn't fallback to returncode, test fails.
        
        Rationale: Ensures format_result handles edge case with only returncode.
        """
        tool = TerminalTool()
        result = {
            "success": False,
            "returncode": 3,
            "stdout": "",
            "stderr": "",
            "command": "test_command"
        }
        
        formatted = tool.format_result(result)
        
        # Mutation: Removed returncode fallback logic
        assert "return code 3" in formatted.lower(), "format_result must fallback to returncode when no error or stderr"
    
    def test_format_result_must_always_include_returncode_in_error_output(self):
        """
        Mutation: If format_result doesn't include returncode, test fails.
        
        Rationale: Ensures returncode is always shown for context.
        """
        tool = TerminalTool()
        result = {
            "success": False,
            "returncode": 42,
            "stdout": "",
            "stderr": "Error message",
            "error": "Error message",
            "command": "test_command"
        }
        
        formatted = tool.format_result(result)
        
        # Mutation: Removed returncode from formatted output
        assert "42" in formatted or "Return code: 42" in formatted, "format_result must always include returncode"
    
    def test_format_result_success_must_show_output_even_if_empty(self):
        """
        Mutation: If format_result doesn't show output indicator for empty stdout, test fails.
        
        Rationale: Ensures LLM knows command ran but produced no output.
        """
        tool = TerminalTool()
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "command": "find . -name 'nonexistent'"
        }
        
        formatted = tool.format_result(result)
        
        # Mutation: Removed empty output handling
        assert "Output:" in formatted, "format_result must show Output: for successful commands"
        assert "(empty)" in formatted, "format_result must indicate when output is empty"
    
    def test_format_result_success_must_not_show_empty_indicator_when_output_exists(self):
        """
        Mutation: If format_result shows empty indicator when output exists, test fails.
        
        Rationale: Ensures empty indicator only appears when output is actually empty.
        """
        tool = TerminalTool()
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "file1.txt\nfile2.txt",
            "stderr": "",
            "command": "find . -name '*.txt'"
        }
        
        formatted = tool.format_result(result)
        
        # Mutation: Always show (empty) even when output exists
        assert "file1.txt" in formatted, "format_result must show actual output when present"
        assert "(empty)" not in formatted, "format_result must not show (empty) when output exists"

