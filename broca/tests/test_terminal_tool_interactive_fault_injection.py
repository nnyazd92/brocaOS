"""
Fault injection tests for interactive terminal functionality.

Tests edge cases, error conditions, and malformed inputs to ensure graceful handling.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
import subprocess
import pexpect

from broca.tools.terminal import TerminalTool


@pytest.fixture
def terminal_tool():
    """TerminalTool instance for testing."""
    return TerminalTool()


class TestFaultInjection:
    """Fault injection tests for edge cases and error conditions."""
    
    def test_extract_interactive_elements_malformed_menu_missing_numbers(self, terminal_tool):
        """Test handling of malformed menu with missing numbers."""
        malformed = "Option 1\nOption 2"  # Missing numbers/letters
        result = terminal_tool._extract_interactive_elements(malformed)
        # Should handle gracefully (may return None or empty options)
        assert result is None or isinstance(result, dict)
    
    def test_extract_interactive_elements_binary_data(self, terminal_tool):
        """Test handling of binary data in output."""
        binary_data = b'\x00\x01\x02\x03'.decode('latin-1')
        result = terminal_tool._extract_interactive_elements(binary_data)
        # Should handle gracefully without crashing
        assert result is None or isinstance(result, dict)
    
    def test_extract_interactive_elements_very_long_menu(self, terminal_tool):
        """Test handling of very long menus (100+ options)."""
        long_menu = "Select:\n" + "\n".join([f"{i}. Option {i}" for i in range(200)])
        result = terminal_tool._extract_interactive_elements(long_menu)
        # Should handle long menus (may truncate or return all)
        if result is not None:
            assert isinstance(result, dict)
            assert "options" in result
    
    def test_extract_interactive_elements_control_characters(self, terminal_tool):
        """Test handling of control characters in menu."""
        with_control = "1. Option\n\x00\x01\x02\n2. Option 2"
        result = terminal_tool._extract_interactive_elements(with_control)
        # Should handle control characters gracefully
        assert result is None or isinstance(result, dict)
    
    def test_extract_interactive_elements_unicode_characters(self, terminal_tool):
        """Test handling of unicode characters in menu."""
        unicode_menu = "Select:\n1. 选项 1\n2. 选项 2\n3. 🎯 Option 3"
        result = terminal_tool._extract_interactive_elements(unicode_menu)
        # Should handle unicode gracefully
        assert result is None or isinstance(result, dict)
    
    def test_is_interactive_pattern_null_bytes(self, terminal_tool):
        """Test handling of null bytes in input."""
        with_null = "Enter value:\x00"
        result = terminal_tool._is_interactive_pattern(with_null)
        # Should handle null bytes (may detect or not, but shouldn't crash)
        assert isinstance(result, bool)
    
    @patch('broca.tools.terminal.pexpect')
    def test_interactive_execution_pexpect_import_error(self, mock_pexpect, terminal_tool):
        """Test graceful handling when pexpect import fails."""
        # Simulate import error
        with patch('broca.tools.terminal.pexpect', side_effect=ImportError("pexpect not available")):
            # Should fall back to subprocess or handle gracefully
            with patch('broca.tools.terminal.subprocess.run') as mock_subprocess:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "Output"
                mock_result.stderr = ""
                mock_subprocess.return_value = mock_result
                
                # Should not crash, but may fall back to subprocess
                result = terminal_tool.execute(command="test", interactive=True)
                # Result should be valid dict
                assert isinstance(result, dict)
    
    @patch('broca.tools.terminal.pexpect')
    def test_interactive_execution_process_exception(self, mock_pexpect, terminal_tool):
        """Test handling of pexpect process exceptions."""
        mock_process = MagicMock()
        mock_process.expect.side_effect = Exception("Process error")
        mock_pexpect.spawn.return_value = mock_process
        
        result = terminal_tool.execute(command="test", interactive=True)
        
        # Should handle exception gracefully
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
    
    @patch('broca.tools.terminal.pexpect')
    def test_interactive_execution_timeout_exception(self, mock_pexpect, terminal_tool):
        """Test handling of pexpect timeout exceptions."""
        mock_process = MagicMock()
        mock_process.expect.side_effect = pexpect.TIMEOUT("Timeout")
        mock_process.before = b"Waiting..."
        mock_pexpect.spawn.return_value = mock_process
        
        result = terminal_tool.execute(command="test", interactive=True, timeout=1)
        
        # Should handle timeout gracefully
        assert isinstance(result, dict)
        assert "timeout" in result.get("error", "").lower() or result["success"] is False
    
    @patch('broca.tools.terminal.pexpect')
    def test_interactive_execution_eof_exception(self, mock_pexpect, terminal_tool):
        """Test handling of pexpect EOF exceptions."""
        mock_process = MagicMock()
        mock_process.expect.side_effect = pexpect.EOF("EOF")
        mock_process.before = b"Output"
        mock_pexpect.spawn.return_value = mock_process
        
        result = terminal_tool.execute(command="test", interactive=True)
        
        # Should handle EOF gracefully
        assert isinstance(result, dict)
    
    @patch('broca.tools.terminal.pexpect')
    def test_interactive_execution_process_cleanup_on_error(self, mock_pexpect, terminal_tool):
        """Test that processes are cleaned up on error."""
        mock_process = MagicMock()
        mock_process.expect.side_effect = Exception("Error")
        mock_process.isalive.return_value = True
        mock_pexpect.spawn.return_value = mock_process
        
        terminal_tool.execute(command="test", interactive=True)
        
        # Process should be terminated/closed
        mock_process.terminate.assert_called() or mock_process.close.assert_called()
    
    def test_format_result_malformed_interactive_elements(self, terminal_tool):
        """Test formatting with malformed interactive_elements structure."""
        malformed_results = [
            {"success": True, "interactive": True, "interactive_elements": None},
            {"success": True, "interactive": True, "interactive_elements": {}},
            {"success": True, "interactive": True, "interactive_elements": {"type": "unknown"}},
            {"success": True, "interactive": True, "interactive_elements": {"type": "menu"}},  # Missing options
        ]
        
        for result in malformed_results:
            formatted = terminal_tool.format_result(result)
            # Should not crash, should return a string
            assert isinstance(formatted, str)
    
    def test_extract_interactive_elements_overlapping_patterns(self, terminal_tool):
        """Test handling of overlapping interactive patterns."""
        # Pattern that matches multiple patterns
        overlapping = "1. Option [y/N]: Enter value:"
        result = terminal_tool._extract_interactive_elements(overlapping)
        # Should handle gracefully (may detect one or all)
        assert result is None or isinstance(result, dict)
    
    def test_is_interactive_pattern_empty_lines_only(self, terminal_tool):
        """Test handling of output with only empty lines."""
        empty_lines = "\n\n\n"
        result = terminal_tool._is_interactive_pattern(empty_lines)
        # Should return False for empty lines
        assert result is False
    
    def test_extract_interactive_elements_mixed_line_endings(self, terminal_tool):
        """Test handling of mixed line endings (\\n, \\r\\n, \\r)."""
        mixed = "1. Option 1\r\n2. Option 2\n3. Option 3\r"
        result = terminal_tool._extract_interactive_elements(mixed)
        # Should handle mixed line endings
        assert result is None or isinstance(result, dict)
    
    @patch('broca.tools.terminal.pexpect')
    def test_interactive_execution_stdin_input_with_special_characters(self, mock_pexpect, terminal_tool):
        """Test handling of special characters in stdin_input."""
        mock_process = MagicMock()
        mock_process.expect.side_effect = [(0, b"Prompt: ")]
        mock_process.before = b"Prompt: "
        mock_process.isalive.return_value = False
        mock_process.exitstatus = 0
        mock_pexpect.spawn.return_value = mock_process
        
        # Test with various special characters
        special_inputs = ["hello\nworld", "test\x00", "test\r\n", "test\t"]
        for stdin_input in special_inputs:
            terminal_tool.execute(command="test", interactive=True, stdin_input=stdin_input)
            # Should handle without crashing
            assert mock_process.sendline.called or mock_process.send.called

