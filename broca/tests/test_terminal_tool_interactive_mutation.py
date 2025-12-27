"""
Mutation testing validation tests for interactive terminal functionality.

These tests are designed to kill mutations in the interactive terminal code.
The actual mutation testing is run with mutmut, but these tests help
validate that our test suite is comprehensive enough to catch bugs.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
import subprocess

from broca.tools.terminal import TerminalTool


@pytest.fixture
def terminal_tool():
    """TerminalTool instance for testing."""
    return TerminalTool()


class TestMutationKillers:
    """
    Tests specifically designed to kill mutations.
    
    These tests verify specific behaviors that would be broken by common mutations
    like changing operators, conditions, or return values.
    """
    
    def test_is_interactive_pattern_returns_false_for_empty_string(self, terminal_tool):
        """Kills mutation: changing return to True for empty string."""
        result = terminal_tool._is_interactive_pattern("")
        assert result is False
    
    def test_is_interactive_pattern_detects_numbered_menu_with_dot(self, terminal_tool):
        """Kills mutation: removing numbered menu detection."""
        output = "1. Option"
        result = terminal_tool._is_interactive_pattern(output)
        assert result is True
    
    def test_is_interactive_pattern_detects_numbered_menu_with_parenthesis(self, terminal_tool):
        """Kills mutation: not detecting parenthesized menus."""
        output = "1) Option"
        result = terminal_tool._is_interactive_pattern(output)
        assert result is True
    
    def test_is_interactive_pattern_detects_lettered_menu(self, terminal_tool):
        """Kills mutation: not detecting lettered menus."""
        output = "a) Option"
        result = terminal_tool._is_interactive_pattern(output)
        assert result is True
    
    def test_is_interactive_pattern_detects_yes_no_brackets(self, terminal_tool):
        """Kills mutation: not detecting [y/N] pattern."""
        output = "Continue? [y/N]:"
        result = terminal_tool._is_interactive_pattern(output)
        assert result is True
    
    def test_is_interactive_pattern_detects_yes_no_parentheses(self, terminal_tool):
        """Kills mutation: not detecting (yes/no) pattern."""
        output = "Continue? (yes/no):"
        result = terminal_tool._is_interactive_pattern(output)
        assert result is True
    
    def test_is_interactive_pattern_detects_colon_prompt(self, terminal_tool):
        """Kills mutation: not detecting colon-ended prompts."""
        output = "Enter value:"
        result = terminal_tool._is_interactive_pattern(output)
        assert result is True
    
    def test_is_interactive_pattern_detects_question_mark_prompt(self, terminal_tool):
        """Kills mutation: not detecting question-mark-ended prompts."""
        output = "Choose option?"
        result = terminal_tool._is_interactive_pattern(output)
        assert result is True
    
    def test_is_interactive_pattern_detects_greater_than_prompt(self, terminal_tool):
        """Kills mutation: not detecting greater-than-ended prompts."""
        output = "Select >"
        result = terminal_tool._is_interactive_pattern(output)
        assert result is True
    
    def test_is_interactive_pattern_returns_false_for_plain_text(self, terminal_tool):
        """Kills mutation: returning True for non-interactive text."""
        output = "This is just plain text output."
        result = terminal_tool._is_interactive_pattern(output)
        assert result is False
    
    def test_extract_interactive_elements_returns_none_for_empty(self, terminal_tool):
        """Kills mutation: returning non-None for empty string."""
        result = terminal_tool._extract_interactive_elements("")
        assert result is None
    
    def test_extract_interactive_elements_returns_dict_for_menu(self, terminal_tool):
        """Kills mutation: returning None for valid menu."""
        output = "1. Option 1\n2. Option 2"
        result = terminal_tool._extract_interactive_elements(output)
        assert result is not None
        assert isinstance(result, dict)
        assert "type" in result
        assert result["type"] == "menu"
    
    def test_extract_interactive_elements_menu_has_options(self, terminal_tool):
        """Kills mutation: menu without options list."""
        output = "1. Option 1\n2. Option 2"
        result = terminal_tool._extract_interactive_elements(output)
        assert "options" in result
        assert len(result["options"]) > 0
    
    def test_extract_interactive_elements_yesno_has_type(self, terminal_tool):
        """Kills mutation: yesno without type field."""
        output = "Continue? [y/N]:"
        result = terminal_tool._extract_interactive_elements(output)
        assert result["type"] == "yesno"
    
    def test_extract_interactive_elements_prompt_has_type(self, terminal_tool):
        """Kills mutation: prompt without type field."""
        output = "Enter value:"
        result = terminal_tool._extract_interactive_elements(output)
        assert result["type"] == "prompt"
    
    def test_format_result_includes_interactive_header(self, terminal_tool):
        """Kills mutation: not including INTERACTIVE MENU DETECTED in formatted output."""
        result = {
            "success": True,
            "interactive": True,
            "interactive_elements": {
                "type": "menu",
                "options": ["1. Option"]
            },
            "command": "test"
        }
        formatted = terminal_tool.format_result(result)
        assert "INTERACTIVE" in formatted
    
    def test_format_result_includes_menu_options(self, terminal_tool):
        """Kills mutation: not including options in formatted output."""
        result = {
            "success": True,
            "interactive": True,
            "interactive_elements": {
                "type": "menu",
                "options": ["1. Test Option"]
            },
            "command": "test"
        }
        formatted = terminal_tool.format_result(result)
        assert "Test Option" in formatted or "Option" in formatted
    
    def test_execute_with_interactive_flag_uses_pexpect(self, terminal_tool):
        """Kills mutation: not using pexpect when interactive=True."""
        with patch('broca.tools.terminal.pexpect') as mock_pexpect:
            mock_process = MagicMock()
            mock_process.expect.side_effect = [(0, b"Output")]
            mock_process.before = b""
            mock_process.after = b"Output"
            mock_process.isalive.return_value = False
            mock_process.exitstatus = 0
            mock_pexpect.spawn.return_value = mock_process
            
            terminal_tool.execute(command="test", interactive=True)
            
            mock_pexpect.spawn.assert_called_once()
    
    def test_execute_without_interactive_flag_uses_subprocess(self, terminal_tool):
        """Kills mutation: using pexpect when interactive=False."""
        with patch('broca.tools.terminal.subprocess.run') as mock_subprocess:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Output"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result
            
            terminal_tool.execute(command="test", interactive=False)
            
            mock_subprocess.assert_called_once()

