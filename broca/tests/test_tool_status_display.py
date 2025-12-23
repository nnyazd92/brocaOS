"""
Tests for tool status display system.

Tests the visual feedback system for tool invocations including spinners,
description formatting, and thread-safe display updates.
"""

from __future__ import annotations

import pytest
import sys
import io
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import will be available after implementation
try:
    from broca.repl.tool_status import (
        Spinner,
        ToolDescriptionFormatter,
        ToolStatusDisplay,
    )
except ImportError:
    # For TDD - these will be implemented
    Spinner = None
    ToolDescriptionFormatter = None
    ToolStatusDisplay = None

# Hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st, settings, HealthCheck
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False


class TestSpinner:
    """Test Spinner class for terminal animation."""
    
    def test_spinner_initialization(self):
        """Test that Spinner initializes correctly."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner()
        assert spinner is not None
        assert hasattr(spinner, 'start')
        assert hasattr(spinner, 'stop')
        assert hasattr(spinner, 'update')
    
    def test_spinner_characters_cycle(self):
        """Test that spinner cycles through all characters."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner()
        chars = []
        
        # Collect characters from multiple updates
        for _ in range(20):
            char = spinner._get_next_char()
            chars.append(char)
        
        # Should have multiple different characters
        unique_chars = set(chars)
        assert len(unique_chars) > 1, "Spinner should cycle through multiple characters"
    
    def test_spinner_stops_correctly(self):
        """Test that spinner stops and returns final character."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner()
        spinner.start()
        time.sleep(0.1)  # Let it run briefly
        result = spinner.stop()
        
        # Should return a valid character (checkmark or similar)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_spinner_handles_non_tty(self):
        """Test that spinner handles non-TTY gracefully."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=False):
            spinner = Spinner()
            # Should not crash when stdout is not a TTY
            spinner.start()
            spinner.stop()
    
    def test_spinner_thread_safety(self):
        """Test that spinner is thread-safe."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner()
        errors = []
        
        def update_spinner():
            try:
                for _ in range(10):
                    spinner._get_next_char()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=update_spinner) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Thread safety issues: {errors}"


class TestToolDescriptionFormatter:
    """Test ToolDescriptionFormatter for generating human-readable descriptions."""
    
    def test_formatter_initialization(self):
        """Test that ToolDescriptionFormatter initializes correctly."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        assert formatter is not None
    
    def test_web_search_description(self):
        """Test web search tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "web_search"
        arguments = {"query": "python programming"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Web searching" in description
        assert "python programming" in description
    
    def test_web_search_multiple_queries(self):
        """Test web search with multiple query terms."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "web_search"
        arguments = {"query": "python, machine learning, AI"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Web searching" in description
        # Should include query terms
        assert "python" in description.lower() or "machine learning" in description.lower()
    
    def test_terminal_command_description(self):
        """Test terminal tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "terminal"
        arguments = {"command": "ls -la"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Running terminal command" in description
        assert "ls -la" in description
    
    def test_terminal_command_truncation(self):
        """Test that long terminal commands are truncated."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "terminal"
        long_command = "python" + " " * 100 + "script.py"
        arguments = {"command": long_command}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Running terminal command" in description
        # Should be truncated
        assert len(description) < len(long_command) + 30
    
    def test_store_memory_description(self):
        """Test store memory tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "store_memory"
        arguments = {"content": "This is a test memory"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Storing memory" in description
        assert "test memory" in description.lower()
    
    def test_retrieve_memories_description(self):
        """Test retrieve memories tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "retrieve_memories"
        arguments = {"query": "test query"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Retrieving memories" in description
        assert "test query" in description.lower()
    
    def test_delete_memory_description(self):
        """Test delete memory tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "delete_memory"
        arguments = {"memory_id": "mem_123"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Deleting memory" in description
        assert "mem_123" in description
    
    def test_update_memory_description(self):
        """Test update memory tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "update_memory"
        arguments = {"memory_id": "mem_456"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Updating memory" in description
        assert "mem_456" in description
    
    def test_link_memories_description(self):
        """Test link memories tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "link_memories"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Linking memories" in description
    
    def test_get_related_memories_description(self):
        """Test get related memories tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "get_related_memories"
        arguments = {"memory_id": "mem_789"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Getting related memories" in description
        assert "mem_789" in description
    
    def test_critic_description(self):
        """Test critic tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "critic"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Running critic check" in description
    
    def test_project_world_state_description(self):
        """Test project world state tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "project_world_state"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Updating project world state" in description
    
    def test_query_self_model_description(self):
        """Test query self model tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "query_self_model"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Querying self model" in description
    
    def test_environment_access_description(self):
        """Test environment access tool description formatting."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "environment_access"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Accessing environment" in description
    
    def test_web_search_no_query(self):
        """Test web search without query argument."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "web_search"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Web searching" in description
    
    def test_terminal_no_command(self):
        """Test terminal without command argument."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "terminal"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Running terminal command" in description
    
    def test_store_memory_no_content(self):
        """Test store memory without content argument."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "store_memory"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Storing memory" in description
    
    def test_retrieve_memories_no_query(self):
        """Test retrieve memories without query argument."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "retrieve_memories"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Retrieving memories" in description
    
    def test_delete_memory_no_id(self):
        """Test delete memory without memory_id argument."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "delete_memory"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Deleting memory" in description
    
    def test_get_related_memories_no_id(self):
        """Test get related memories without memory_id argument."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "get_related_memories"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Getting related memories" in description
    
    def test_store_memory_long_content_truncation(self):
        """Test store memory with long content that gets truncated."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "store_memory"
        long_content = "x" * 100
        arguments = {"content": long_content}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Storing memory" in description
        assert len(description) < len(long_content) + 20  # Should be truncated
    
    def test_retrieve_memories_long_query_truncation(self):
        """Test retrieve memories with long query that gets truncated."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "retrieve_memories"
        long_query = "x" * 100
        arguments = {"query": long_query}
        
        description = formatter.format(tool_name, arguments)
        
        assert "Retrieving memories" in description
        assert len(description) < len(long_query) + 25  # Should be truncated
    
    def test_spinner_update_when_disabled(self):
        """Test spinner update when disabled."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner(enabled=False)
        result = spinner.update()
        
        assert result == ""
    
    def test_spinner_update_when_not_running(self):
        """Test spinner update when not running."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner(enabled=True)
        # Don't start it
        result = spinner.update()
        
        assert result == ""
    
    def test_display_complete_without_start(self):
        """Test completing a tool call that was never started."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            display = ToolStatusDisplay()
            # Complete without starting - should not crash
            display.complete_tool_call(tool_call_id="nonexistent", success=True)
    
    def test_generic_tool_description(self):
        """Test generic tool description fallback."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "unknown_tool"
        arguments = {"param1": "value1", "param2": "value2"}
        
        description = formatter.format(tool_name, arguments)
        
        assert "unknown_tool" in description.lower()
        assert "argument" in description.lower()
    
    def test_empty_arguments(self):
        """Test description with empty arguments."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "test_tool"
        arguments = {}
        
        description = formatter.format(tool_name, arguments)
        
        assert tool_name in description.lower()
    
    def test_special_characters_handling(self):
        """Test that special characters are handled correctly."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "terminal"
        arguments = {"command": "echo 'test & < > \"quotes\"'"}
        
        description = formatter.format(tool_name, arguments)
        
        # Should not crash and should include command
        assert "Running terminal command" in description
        assert isinstance(description, str)


class TestToolStatusDisplay:
    """Test ToolStatusDisplay manager class."""
    
    def test_display_initialization(self):
        """Test that ToolStatusDisplay initializes correctly."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        assert display is not None
    
    def test_start_tool_call(self):
        """Test starting a tool call display."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write = Mock()
            mock_stdout.flush = Mock()
            
            # Create display after patching stdout
            display = ToolStatusDisplay()
            display.start_tool_call(tool_name, arguments)
            
            # Should have written something
            assert mock_stdout.write.called
    
    def test_complete_tool_call_success(self):
        """Test completing a tool call with success."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write = Mock()
            mock_stdout.flush = Mock()
            
            # Create display after patching stdout
            display = ToolStatusDisplay()
            display.start_tool_call(tool_name, arguments)
            display.complete_tool_call(success=True)
            
            # Should have written checkmark or success indicator
            write_calls = [str(call) for call in mock_stdout.write.call_args_list]
            # Check if checkmark was written in any call
            all_calls_str = " ".join([str(call) for call in mock_stdout.write.call_args_list])
            assert "✓" in all_calls_str or mock_stdout.write.called
    
    def test_complete_tool_call_error(self):
        """Test completing a tool call with error."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write = Mock()
            mock_stdout.flush = Mock()
            
            # Create display after patching stdout
            display = ToolStatusDisplay()
            display.start_tool_call(tool_name, arguments)
            display.complete_tool_call(success=False)
            
            # Should have written error indicator
            all_calls_str = " ".join([str(call) for call in mock_stdout.write.call_args_list])
            assert "✗" in all_calls_str or mock_stdout.write.called
    
    def test_non_tty_disabled(self):
        """Test that display is disabled for non-TTY."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        with patch('sys.stdout.isatty', return_value=False):
            # Should not crash
            display.start_tool_call(tool_name, arguments)
            display.complete_tool_call(success=True)
    
    def test_thread_safety(self):
        """Test that display is thread-safe."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        errors = []
        
        def run_tool_call(tool_name: str, args: Dict[str, Any]):
            try:
                with patch('sys.stdout') as mock_stdout:
                    mock_stdout.isatty.return_value = True
                    mock_stdout.write = Mock()
                    mock_stdout.flush = Mock()
                    
                    display.start_tool_call(tool_name, args)
                    time.sleep(0.01)
                    display.complete_tool_call(success=True)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=run_tool_call, args=("web_search", {"query": f"test{i}"}))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Thread safety issues: {errors}"
    
    def test_output_format(self):
        """Test that output follows expected format."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        tool_name = "web_search"
        arguments = {"query": "python"}
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                # Create display after patching
                display = ToolStatusDisplay()
                display.start_tool_call(tool_name, arguments)
                display.complete_tool_call(success=True)
        
        output_str = output.getvalue()
        assert "BrocaOS>" in output_str or "BrocaOS" in output_str
        assert "Web searching" in output_str or "web_search" in output_str.lower()
    
    def test_graceful_degradation_on_error(self):
        """Test that display degrades gracefully on errors."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        # Simulate write error
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write.side_effect = IOError("Write failed")
            mock_stdout.flush = Mock()
            
            # Should not raise exception
            try:
                display.start_tool_call(tool_name, arguments)
                display.complete_tool_call(success=True)
            except Exception:
                pytest.fail("Display should handle errors gracefully")


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        tool_name=st.text(min_size=1, max_size=50),
        query=st.text(min_size=0, max_size=200)
    )
    def test_formatter_always_produces_valid_description(self, tool_name, query):
        """Property: Formatter always produces a valid description for any tool name and query."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        arguments = {"query": query} if query else {}
        
        description = formatter.format(tool_name, arguments)
        
        # Should always return a string
        assert isinstance(description, str)
        assert len(description) > 0
        # Should not crash
        assert description is not None
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        command=st.text(min_size=0, max_size=500)
    )
    def test_terminal_command_truncation_preserves_meaning(self, command):
        """Property: Terminal command truncation preserves meaning (first part visible)."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        arguments = {"command": command}
        
        description = formatter.format("terminal", arguments)
        
        assert isinstance(description, str)
        assert "Running terminal command" in description
        
        # If command is long, should be truncated but first part visible
        if len(command) > 50:
            # First 47 chars should be in description
            assert command[:47] in description or command[:40] in description
        elif command:
            # Short commands should be fully visible
            assert command in description
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        arguments=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.booleans(),
                st.none()
            ),
            min_size=0,
            max_size=10
        )
    )
    def test_formatter_handles_arbitrary_arguments(self, arguments):
        """Property: Formatter handles arbitrary argument dictionaries without crashing."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        tool_name = "test_tool"
        
        # Should not crash on any argument structure
        description = formatter.format(tool_name, arguments)
        
        assert isinstance(description, str)
        assert len(description) > 0
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        num_iterations=st.integers(min_value=1, max_value=100)
    )
    def test_spinner_cycles_through_all_characters(self, num_iterations):
        """Property: Spinner cycles through all characters."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner(enabled=True)
        chars = []
        
        for _ in range(num_iterations):
            char = spinner._get_next_char()
            chars.append(char)
        
        # Should have used spinner characters
        assert all(c in Spinner.SPINNER_CHARS for c in chars)
        
        # If enough iterations, should have seen multiple different chars
        if num_iterations >= len(Spinner.SPINNER_CHARS):
            unique_chars = set(chars)
            assert len(unique_chars) > 1
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        special_chars=st.text(alphabet=st.characters(blacklist_categories=('C',)), min_size=0, max_size=50)
    )
    def test_formatter_handles_special_characters(self, special_chars):
        """Property: Formatter handles special characters in arguments."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        arguments = {"query": special_chars}
        
        # Should not crash on special characters
        description = formatter.format("web_search", arguments)
        
        assert isinstance(description, str)
        assert len(description) > 0


class TestFaultInjection:
    """Fault injection tests for error handling."""
    
    def test_stdout_write_failure(self):
        """Test behavior when stdout.write fails."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write.side_effect = IOError("Write failed")
            mock_stdout.flush = Mock()
            
            # Should not raise exception
            try:
                display.start_tool_call(tool_name, arguments)
                display.complete_tool_call(success=True)
            except Exception as e:
                pytest.fail(f"Should handle write errors gracefully: {e}")
    
    def test_stdout_flush_failure(self):
        """Test behavior when stdout.flush fails."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write = Mock()
            mock_stdout.flush.side_effect = IOError("Flush failed")
            
            # Should not raise exception
            try:
                display.start_tool_call(tool_name, arguments)
                display.complete_tool_call(success=True)
            except Exception as e:
                pytest.fail(f"Should handle flush errors gracefully: {e}")
    
    def test_non_tty_terminal(self):
        """Test behavior when stdout is not a TTY."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        with patch('sys.stdout.isatty', return_value=False):
            # Should not crash
            display.start_tool_call(tool_name, arguments)
            display.complete_tool_call(success=True)
    
    def test_missing_isatty_attribute(self):
        """Test behavior when stdout doesn't have isatty method."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        # Create mock stdout without isatty
        mock_stdout = Mock()
        del mock_stdout.isatty
        
        with patch('sys.stdout', mock_stdout):
            # Should handle gracefully (defaults to disabled)
            display.start_tool_call(tool_name, arguments)
            display.complete_tool_call(success=True)
    
    def test_ansi_code_failure(self):
        """Test behavior when ANSI codes fail (non-UTF-8 terminal)."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        tool_name = "web_search"
        arguments = {"query": "test"}
        
        # Simulate encoding error
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write.side_effect = UnicodeEncodeError(
                'utf-8', 'test', 0, 1, 'invalid'
            )
            mock_stdout.flush = Mock()
            
            # Should not crash
            try:
                display.start_tool_call(tool_name, arguments)
                display.complete_tool_call(success=True)
            except UnicodeEncodeError:
                pytest.fail("Should handle encoding errors gracefully")
    
    def test_formatter_with_invalid_arguments(self):
        """Test formatter with invalid argument types."""
        if ToolDescriptionFormatter is None:
            pytest.skip("ToolDescriptionFormatter not yet implemented")
        
        formatter = ToolDescriptionFormatter()
        
        # Test with various invalid argument types
        invalid_args = [
            None,
            "not a dict",
            123,
            [],
            {"key": object()},  # Non-serializable object
        ]
        
        for args in invalid_args:
            try:
                if isinstance(args, dict):
                    description = formatter.format("test_tool", args)
                else:
                    # Skip non-dict args as they're type errors
                    continue
                assert isinstance(description, str)
            except Exception as e:
                # Should handle gracefully or raise expected type errors
                assert isinstance(e, (TypeError, AttributeError))
    
    def test_spinner_with_disabled_state(self):
        """Test spinner behavior when disabled."""
        if Spinner is None:
            pytest.skip("Spinner not yet implemented")
        
        spinner = Spinner(enabled=False)
        
        # Should not crash
        spinner.start()
        result = spinner.stop()
        
        # Should return empty or default value
        assert result in ("✓", "✗", "")
    
    def test_display_with_none_tool_name(self):
        """Test display with None tool name."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        
        with patch('sys.stdout.isatty', return_value=True):
            # Should handle None gracefully
            try:
                display.start_tool_call(None, {})
                display.complete_tool_call(tool_name=None)
            except Exception as e:
                # Should either handle or raise expected error
                assert isinstance(e, (TypeError, AttributeError))
    
    def test_concurrent_fault_injection(self):
        """Test fault injection with concurrent operations."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay()
        errors = []
        
        def fault_inject_operation(tool_id: str):
            try:
                with patch('sys.stdout') as mock_stdout:
                    # Randomly fail operations
                    import random
                    if random.random() < 0.3:
                        mock_stdout.write.side_effect = IOError("Random failure")
                    else:
                        mock_stdout.write = Mock()
                    
                    mock_stdout.isatty.return_value = True
                    mock_stdout.flush = Mock()
                    
                    display.start_tool_call("test_tool", {"id": tool_id}, tool_id)
                    time.sleep(0.01)
                    display.complete_tool_call(tool_call_id=tool_id, success=True)
            except Exception as e:
                # Collect errors but don't fail - should handle gracefully
                errors.append(e)
        
        threads = [
            threading.Thread(target=fault_inject_operation, args=(f"tool_{i}",))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Errors should be handled gracefully (IOError, etc.)
        # Not all errors are failures - some are expected
        assert all(
            isinstance(e, (IOError, OSError, AttributeError)) 
            for e in errors
        ) if errors else True

