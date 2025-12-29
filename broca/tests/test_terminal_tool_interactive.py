"""
Tests for interactive terminal command handling.

Tests interactive command detection, menu extraction, and stdin input handling.
Following TDD approach - tests written before implementation.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import pytest
import subprocess

from broca.tools.terminal import TerminalTool


@pytest.fixture
def terminal_tool():
    """TerminalTool instance for testing."""
    return TerminalTool()


class TestInteractivePatternDetection:
    """Test detection of interactive patterns in command output."""
    
    def test_detect_numbered_menu_pattern(self, terminal_tool):
        """
        Test detection of numbered menu patterns like "1. Option 1".
        
        Rationale: Ensures numbered menus are detected as interactive.
        """
        output = "Please select an option:\n1. Option 1\n2. Option 2\n3. Option 3"
        is_interactive = terminal_tool._is_interactive_pattern(output)
        assert is_interactive is True
    
    def test_detect_parenthesized_numbered_menu(self, terminal_tool):
        """
        Test detection of parenthesized numbered menus like "1) Option".
        
        Rationale: Ensures parenthesized numbered menus are detected.
        """
        output = "1) Option A\n2) Option B"
        is_interactive = terminal_tool._is_interactive_pattern(output)
        assert is_interactive is True
    
    def test_detect_lettered_menu_pattern(self, terminal_tool):
        """
        Test detection of lettered menu patterns like "a) Option A".
        
        Rationale: Ensures lettered menus are detected as interactive.
        """
        output = "Choose:\na) Option A\nb) Option B\nc) Option C"
        is_interactive = terminal_tool._is_interactive_pattern(output)
        assert is_interactive is True
    
    def test_detect_yes_no_prompt(self, terminal_tool):
        """
        Test detection of yes/no prompts like "[y/N]" or "(yes/no)".
        
        Rationale: Ensures yes/no prompts are detected as interactive.
        """
        test_cases = [
            "Continue? [y/N]:",
            "Delete file? (yes/no):",
            "Proceed? Y/n:",
            "Confirm [Y/n]:"
        ]
        for output in test_cases:
            is_interactive = terminal_tool._is_interactive_pattern(output)
            assert is_interactive is True, f"Failed to detect yes/no in: {output}"
    
    def test_detect_prompt_ending_with_colon(self, terminal_tool):
        """
        Test detection of prompts ending with colon.
        
        Rationale: Ensures colon-ended prompts are detected.
        """
        output = "Enter your name:"
        is_interactive = terminal_tool._is_interactive_pattern(output)
        assert is_interactive is True
    
    def test_detect_prompt_ending_with_question_mark(self, terminal_tool):
        """
        Test detection of prompts ending with question mark.
        
        Rationale: Ensures question-mark-ended prompts are detected.
        """
        output = "What is your choice?"
        is_interactive = terminal_tool._is_interactive_pattern(output)
        assert is_interactive is True
    
    def test_detect_prompt_ending_with_greater_than(self, terminal_tool):
        """
        Test detection of prompts ending with greater-than symbol.
        
        Rationale: Ensures greater-than-ended prompts are detected.
        """
        output = "Select option >"
        is_interactive = terminal_tool._is_interactive_pattern(output)
        assert is_interactive is True
    
    def test_non_interactive_output_not_detected(self, terminal_tool):
        """
        Test that non-interactive output is not detected as interactive.
        
        Rationale: Ensures false positives are avoided.
        """
        non_interactive_outputs = [
            "Hello, World!",
            "File saved successfully.",
            "Processing 100 files...",
            "Error: File not found",
            "Results:\n  item1\n  item2",  # List output, not menu
            "1. Testing basic consistency...\n5. Analyzing holographic constraint...",  # Non-sequential numbered steps, not menu
            "Step 1: Initialize\nStep 5: Process"  # Step labels, not interactive menu
        ]
        for output in non_interactive_outputs:
            is_interactive = terminal_tool._is_interactive_pattern(output)
            assert is_interactive is False, f"False positive for: {output}"


class TestMenuExtraction:
    """Test extraction of interactive elements from output."""
    
    def test_extract_numbered_menu_options(self, terminal_tool):
        """
        Test extraction of numbered menu options.
        
        Rationale: Ensures numbered menus are correctly parsed.
        """
        output = "Please select:\n1. First option\n2. Second option\n3. Third option"
        elements = terminal_tool._extract_interactive_elements(output)
        
        assert elements is not None
        assert elements["type"] == "menu"
        assert len(elements["options"]) == 3
        assert "First option" in elements["options"][0]
        assert "Second option" in elements["options"][1]
        assert "Third option" in elements["options"][2]
    
    def test_extract_parenthesized_numbered_menu(self, terminal_tool):
        """
        Test extraction of parenthesized numbered menus.
        
        Rationale: Ensures parenthesized numbered menus are parsed correctly.
        """
        output = "Choose:\n1) Option A\n2) Option B"
        elements = terminal_tool._extract_interactive_elements(output)
        
        assert elements is not None
        assert elements["type"] == "menu"
        assert len(elements["options"]) == 2
    
    def test_extract_lettered_menu_options(self, terminal_tool):
        """
        Test extraction of lettered menu options.
        
        Rationale: Ensures lettered menus are correctly parsed.
        """
        output = "Select:\na) Alpha\nb) Beta\nc) Gamma"
        elements = terminal_tool._extract_interactive_elements(output)
        
        assert elements is not None
        assert elements["type"] == "menu"
        assert len(elements["options"]) == 3
    
    def test_extract_yes_no_prompt(self, terminal_tool):
        """
        Test extraction of yes/no prompts.
        
        Rationale: Ensures yes/no prompts are correctly identified.
        """
        output = "Continue? [y/N]:"
        elements = terminal_tool._extract_interactive_elements(output)
        
        assert elements is not None
        assert elements["type"] == "yesno"
        assert "prompt_text" in elements
    
    def test_extract_text_prompt(self, terminal_tool):
        """
        Test extraction of text input prompts.
        
        Rationale: Ensures text prompts are correctly identified.
        """
        output = "Enter your name:"
        elements = terminal_tool._extract_interactive_elements(output)
        
        assert elements is not None
        assert elements["type"] == "prompt"
        assert "prompt_text" in elements
    
    def test_extract_multi_line_menu(self, terminal_tool):
        """
        Test extraction of multi-line menus with descriptions.
        
        Rationale: Ensures complex menus are handled correctly.
        """
        output = """Select operation:
1. Create new file
   Creates a new file in the current directory
2. Delete file
   Removes an existing file
3. List files
   Shows all files in the directory"""
        elements = terminal_tool._extract_interactive_elements(output)
        
        assert elements is not None
        assert elements["type"] == "menu"
        assert len(elements["options"]) >= 3
    
    def test_extract_empty_output_returns_none(self, terminal_tool):
        """
        Test that empty output returns None.
        
        Rationale: Ensures empty output is handled gracefully.
        """
        elements = terminal_tool._extract_interactive_elements("")
        assert elements is None
    
    def test_extract_non_interactive_output_returns_none(self, terminal_tool):
        """
        Test that non-interactive output returns None.
        
        Rationale: Ensures non-interactive output doesn't return false positives.
        """
        output = "Hello, World!\nThis is just text output."
        elements = terminal_tool._extract_interactive_elements(output)
        assert elements is None


class TestInteractiveExecution:
    """Test interactive command execution."""
    
    @patch('broca.tools.terminal.pexpect')
    def test_execute_interactive_command_with_explicit_flag(self, mock_pexpect, terminal_tool):
        """
        Test executing interactive command with explicit interactive flag.
        
        Rationale: Ensures explicit flag triggers interactive execution.
        """
        # Mock pexpect spawn
        mock_process = MagicMock()
        mock_process.expect.side_effect = [
            (0, b"Output"),  # First expect succeeds
            (0, b"Please select:\n1. Option 1\n2. Option 2")  # Menu detected
        ]
        mock_process.before = b"Output"
        mock_process.after = b"Please select:\n1. Option 1\n2. Option 2"
        mock_process.isalive.return_value = False
        mock_process.exitstatus = 0
        mock_pexpect.spawn.return_value = mock_process
        
        result = terminal_tool.execute(command="interactive_command", interactive=True)
        
        assert result["success"] is True
        assert result.get("interactive") is True
        # interactive_elements is only set if explicitly extracted (no automatic detection)
        mock_pexpect.spawn.assert_called_once()
    
    @patch('broca.tools.terminal.subprocess.run')
    def test_execute_non_interactive_command_works_normally(self, mock_subprocess, terminal_tool):
        """
        Test that non-interactive commands work normally without pexpect.
        
        Rationale: Ensures backward compatibility is maintained.
        """
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Output"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = terminal_tool.execute(command="echo hello")
        
        assert result["success"] is True
        assert result.get("interactive") is not True
        mock_subprocess.assert_called_once()
    
    @patch('broca.tools.terminal.pexpect')
    def test_execute_interactive_with_stdin_input(self, mock_pexpect, terminal_tool):
        """
        Test executing interactive command with stdin_input parameter.
        
        Rationale: Ensures stdin_input is sent to interactive process.
        """
        mock_process = MagicMock()
        mock_process.expect.side_effect = [
            (0, b"Prompt: "),
            (0, b"Result")
        ]
        mock_process.before = b"Prompt: "
        mock_process.after = b"Result"
        mock_process.isalive.return_value = False
        mock_process.exitstatus = 0
        mock_pexpect.spawn.return_value = mock_process
        
        result = terminal_tool.execute(command="interactive_command", interactive=True, stdin_input="1")
        
        assert result["success"] is True
        mock_process.sendline.assert_called_with(b"1")
    
    @patch('broca.tools.terminal.pexpect')
    def test_interactive_command_timeout_handling(self, mock_pexpect, terminal_tool):
        """
        Test timeout handling for interactive commands.
        
        Rationale: Ensures interactive commands respect timeout.
        """
        import pexpect
        mock_process = MagicMock()
        mock_process.expect.side_effect = pexpect.TIMEOUT("Timeout")
        mock_process.before = b"Waiting for input..."
        mock_pexpect.spawn.return_value = mock_process
        
        result = terminal_tool.execute(command="interactive_command", interactive=True, timeout=5)
        
        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower() or "timed out" in result.get("error", "").lower()


class TestInteractiveResultFormatting:
    """Test formatting of interactive results for LLM consumption."""
    
    def test_format_result_with_interactive_menu(self, terminal_tool):
        """
        Test formatting of result with interactive menu.
        
        Rationale: Ensures interactive menus are prominently formatted for LLM.
        """
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "Please select:\n1. Option 1\n2. Option 2",
            "interactive": True,
            "interactive_elements": {
                "type": "menu",
                "options": ["1. Option 1", "2. Option 2"],
                "prompt_text": "Please select:"
            },
            "command": "test_command"
        }
        
        formatted = terminal_tool.format_result(result)
        
        assert "INTERACTIVE MENU DETECTED" in formatted
        assert "Option 1" in formatted
        assert "Option 2" in formatted
        assert "stdin_input" in formatted.lower() or "input" in formatted.lower()
    
    def test_format_result_with_yes_no_prompt(self, terminal_tool):
        """
        Test formatting of result with yes/no prompt.
        
        Rationale: Ensures yes/no prompts are clearly formatted.
        """
        result = {
            "success": True,
            "interactive": True,
            "interactive_elements": {
                "type": "yesno",
                "prompt_text": "Continue? [y/N]:"
            },
            "command": "test_command"
        }
        
        formatted = terminal_tool.format_result(result)
        
        assert "INTERACTIVE" in formatted
        assert "y/N" in formatted or "yes" in formatted.lower()


class TestToolParametersAndDescription:
    """Test tool schema and description updates."""
    
    def test_parameters_includes_interactive_flag(self, terminal_tool):
        """
        Test that parameters schema includes interactive flag.
        
        Rationale: Ensures LLM can use interactive flag.
        """
        params = terminal_tool.parameters
        assert "properties" in params
        assert "interactive" in params["properties"]
        assert params["properties"]["interactive"]["type"] == "boolean"
    
    def test_parameters_includes_stdin_input(self, terminal_tool):
        """
        Test that parameters schema includes stdin_input.
        
        Rationale: Ensures LLM can provide input for interactive commands.
        """
        params = terminal_tool.parameters
        assert "properties" in params
        assert "stdin_input" in params["properties"]
        assert params["properties"]["stdin_input"]["type"] == "string"
    
    def test_description_includes_interactive_documentation(self, terminal_tool):
        """
        Test that description includes interactive command documentation.
        
        Rationale: Ensures LLM understands how to use interactive features.
        """
        description = terminal_tool.description
        assert "INTERACTIVE" in description or "interactive" in description
        assert "menu" in description.lower() or "prompt" in description.lower()
        assert "stdin_input" in description.lower() or "input" in description.lower()

