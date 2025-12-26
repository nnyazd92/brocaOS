"""
Mutation testing for tool status display system.

Tests that ensure mutations (code changes) are caught by the test suite.
"""

from __future__ import annotations

import pytest
import sys
import io
import threading
import time
from unittest.mock import Mock, patch

try:
    from broca.repl.tool_status import (
        Spinner,
        ToolDescriptionFormatter,
        ToolStatusDisplay,
    )
except ImportError:
    Spinner = None
    ToolDescriptionFormatter = None
    ToolStatusDisplay = None


class TestMutationResistance:
    """Tests that catch common mutations."""
    
    def test_spinner_must_return_checkmark_on_success(self):
        """Mutation: If spinner.stop() doesn't return checkmark, test fails."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner(enabled=True)
        spinner.start()
        result = spinner.stop(success=True)
        
        # Mutation: Changed to return "✗" instead of "✓"
        assert result == "✓", "Spinner must return checkmark on success"
    
    def test_spinner_must_return_cross_on_failure(self):
        """Mutation: If spinner.stop() doesn't return cross, test fails."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner(enabled=True)
        spinner.start()
        result = spinner.stop(success=False)
        
        # Mutation: Changed to return "✓" instead of "✗"
        assert result == "✗", "Spinner must return cross on failure"
    
    def test_final_output_must_include_newline(self):
        """Mutation: If _print_final() doesn't add newline, test fails."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        # Use a mock that captures writes properly
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True)
            display.start_tool_call("test_mutation", {}, tool_call_id="mutation_test")
            time.sleep(0.05)
            display.complete_tool_call(tool_call_id="mutation_test", success=True)
            time.sleep(0.15)  # Wait for final write and thread cleanup
        
        # Check the last write call - it should be from _print_final and end with \n
        # Find writes that contain the completion indicator
        final_writes = [w for w in written_data if '✓' in w or '✗' in w or 'test_mutation' in w]
        if final_writes:
            final_write = final_writes[-1]
            # Mutation: Removed \n from _print_final
            assert final_write.endswith('\n'), f"Final write must end with newline. Write: {repr(final_write[:100])}"
        else:
            # If we can't find the final write, check if any write ends with \n
            has_newline = any(w.endswith('\n') for w in written_data)
            assert has_newline, f"At least one write should end with newline. Writes: {[repr(w[:50]) for w in written_data[-3:]]}"
    
    def test_status_output_must_not_include_newline(self):
        """Mutation: If _print_status() adds newline, test fails."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True)
                display.start_tool_call("test", {})
                time.sleep(0.05)  # Let spinner animate
        
        output_str = output.getvalue()
        # Check that status updates don't have trailing newlines (except final)
        # Split by \r to get individual status updates
        updates = output_str.split('\r')
        for update in updates[:-1]:  # All but the last (which may have \n)
            # Mutation: Added \n to _print_status
            assert not update.endswith('\n'), "Status updates must not have newlines"
    
    def test_spinner_thread_must_be_daemon(self):
        """Mutation: If spinner thread is not daemon, test fails."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            display = ToolStatusDisplay(enabled=True)
            display.start_tool_call("test", {}, tool_call_id="test1")
            
            with display._lock:
                thread = display._spinner_threads.get("test1")
            
            # Mutation: Changed daemon=False
            assert thread is None or thread.daemon, "Spinner thread must be daemon"
            
            display.complete_tool_call(tool_call_id="test1", success=True)
    
    def test_color_manager_must_be_used_for_indicators(self):
        """Mutation: If color manager is not used for indicators, test fails."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        try:
            from broca.repl.color_profile import ColorManager
            color_manager = ColorManager(enabled=True)
        except ImportError:
            pytest.skip("ColorManager not available")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True, color_manager=color_manager)
                display.start_tool_call("test", {})
                display.complete_tool_call(success=True)
        
        output_str = output.getvalue()
        # Mutation: Removed color application for success indicator
        # Should have ANSI codes if colors are enabled
        has_ansi = '\033[' in output_str or '\x1b[' in output_str
        assert has_ansi or not color_manager.is_enabled(), "Color manager should be used when enabled"
    
    def test_spinner_must_update_continuously(self):
        """Mutation: If spinner doesn't update continuously, test fails."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        # Create a mock stdout that properly supports isatty() for the spinner thread
        class MockStdout:
            def __init__(self, output):
                self.output = output
                self._isatty = True
            
            def isatty(self):
                return self._isatty
            
            def write(self, text):
                return self.output.write(text)
            
            def flush(self):
                return self.output.flush()
        
        mock_stdout = MockStdout(output)
        with patch('sys.stdout', mock_stdout):
            # Also patch isatty at module level for the thread
            with patch('broca.repl.tool_status.sys.stdout', mock_stdout):
                display = ToolStatusDisplay(enabled=True)
                # Force the display to treat output as NOT captured so spinner animates
                display._output_captured = False
                display.start_tool_call("test", {}, tool_call_id="test1")
                
                # Wait for multiple updates
                time.sleep(0.25)
                
                display.complete_tool_call(tool_call_id="test1", success=True)
        
        output_str = output.getvalue()
        # Count \r characters (each represents an update)
        update_count = output_str.count('\r')
        
        # Mutation: Removed background thread, only one update
        assert update_count > 1, f"Spinner must update multiple times (continuous animation), got {update_count} updates. Output: {repr(output_str[:200])}"
    
    def test_no_blank_lines_between_calls(self):
        """Mutation: If blank lines appear between calls, test fails."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True)
                
                # First call
                display.start_tool_call("test1", {}, tool_call_id="call1")
                time.sleep(0.05)
                display.complete_tool_call(tool_call_id="call1", success=True)
                
                # Second call immediately after
                display.start_tool_call("test2", {}, tool_call_id="call2")
                time.sleep(0.05)
                display.complete_tool_call(tool_call_id="call2", success=True)
        
        output_str = output.getvalue()
        lines = output_str.split('\n')
        
        # Check for consecutive empty lines (blank lines between calls)
        consecutive_empty = False
        for i in range(len(lines) - 1):
            if not lines[i].strip() and not lines[i+1].strip() and i > 0:
                consecutive_empty = True
                break
        
        # Mutation: Added extra newlines between calls
        assert not consecutive_empty, "Must not have blank lines between tool calls"
    
    def test_success_indicator_color_type_exists(self):
        """Mutation: If success_indicator color type doesn't exist, test fails."""
        try:
            from broca.repl.color_profile import ColorManager, DefaultColorProfile
        except ImportError:
            pytest.skip("ColorManager not available")
        
        profile = DefaultColorProfile()
        # Mutation: Removed success_indicator from ColorProfile
        assert hasattr(profile, 'success_indicator'), "ColorProfile must have success_indicator"
        
        color_manager = ColorManager(enabled=True)
        result = color_manager.colorize("✓", "success_indicator")
        # Should either have color codes or return original text
        assert isinstance(result, str)
    
    def test_error_indicator_color_type_exists(self):
        """Mutation: If error_indicator color type doesn't exist, test fails."""
        try:
            from broca.repl.color_profile import ColorManager, DefaultColorProfile
        except ImportError:
            pytest.skip("ColorManager not available")
        
        profile = DefaultColorProfile()
        # Mutation: Removed error_indicator from ColorProfile
        assert hasattr(profile, 'error_indicator'), "ColorProfile must have error_indicator"
        
        color_manager = ColorManager(enabled=True)
        result = color_manager.colorize("✗", "error_indicator")
        # Should either have color codes or return original text
        assert isinstance(result, str)

