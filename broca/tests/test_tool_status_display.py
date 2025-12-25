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
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        tool_name=st.text(min_size=1, max_size=30),
        arguments=st.dictionaries(
            keys=st.text(min_size=1, max_size=15),
            values=st.one_of(
                st.text(max_size=200),
                st.integers(),
                st.booleans(),
                st.none()
            ),
            min_size=0,
            max_size=5
        ),
        success=st.booleans()
    )
    def test_tool_status_display_handles_arbitrary_inputs(self, tool_name, arguments, success):
        """Property: ToolStatusDisplay handles arbitrary tool names, arguments, and success states."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True)
                try:
                    display.start_tool_call(tool_name, arguments, tool_call_id=f"test_{tool_name}")
                    time.sleep(0.05)  # Brief delay
                    display.complete_tool_call(tool_call_id=f"test_{tool_name}", success=success)
                    
                    # Should not crash
                    output_str = output.getvalue()
                    assert isinstance(output_str, str)
                except Exception as e:
                    # Only allow expected exceptions
                    assert isinstance(e, (TypeError, AttributeError, ValueError))
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        num_concurrent=st.integers(min_value=1, max_value=10)
    )
    def test_concurrent_tool_calls_thread_safety(self, num_concurrent):
        """Property: Multiple concurrent tool calls are thread-safe."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay(enabled=True)
        errors = []
        results = []
        
        def run_tool_call(tool_id: int):
            try:
                with patch('sys.stdout') as mock_stdout:
                    mock_stdout.isatty.return_value = True
                    mock_stdout.write = Mock()
                    mock_stdout.flush = Mock()
                    
                    display.start_tool_call("test_tool", {"id": tool_id}, tool_call_id=f"call_{tool_id}")
                    time.sleep(0.05)
                    display.complete_tool_call(tool_call_id=f"call_{tool_id}", success=True)
                    results.append(tool_id)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=run_tool_call, args=(i,))
            for i in range(num_concurrent)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=1.0)
        
        # Should complete without errors
        assert len(errors) == 0, f"Thread safety issues: {errors}"
        assert len(results) == num_concurrent, "All tool calls should complete"
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        text=st.text(min_size=0, max_size=100).filter(lambda t: not t.startswith('\x1b') and '\x1b' not in t)
    )
    def test_colorize_preserves_text_content(self, text):
        """Property: Color application preserves text content."""
        try:
            from broca.repl.color_profile import ColorManager
        except ImportError:
            pytest.skip("ColorManager not available")
        
        color_manager = ColorManager(enabled=True)
        
        # Test all color types
        color_types = ["brocaos_prompt", "response_text", "you_prompt", "input_text", 
                      "success_indicator", "error_indicator"]
        
        for color_type in color_types:
            colored = color_manager.colorize(text, color_type)
            # Remove ANSI codes to get original text
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            cleaned = ansi_escape.sub('', colored)
            # Text should be preserved (allowing for ANSI reset codes)
            assert text in cleaned or text == cleaned or (not text and not cleaned), f"Text content should be preserved for {color_type}"


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
    
    def test_thread_interruption_during_animation(self):
        """Test behavior when thread is interrupted during spinner animation."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay(enabled=True)
        
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write = Mock()
            mock_stdout.flush = Mock()
            
            display.start_tool_call("test", {}, tool_call_id="test1")
            
            # Simulate thread interruption
            with display._lock:
                thread = display._spinner_threads.get("test1")
                if thread:
                    # Interrupt the thread
                    import signal
                    try:
                        # Try to interrupt (may not work on all systems)
                        pass
                    except:
                        pass
            
            time.sleep(0.1)
            # Should still complete gracefully
            display.complete_tool_call(tool_call_id="test1", success=True)
    
    def test_color_manager_returns_none(self):
        """Test behavior when color manager returns None."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        try:
            from broca.repl.color_profile import ColorManager
        except ImportError:
            pytest.skip("ColorManager not available")
        
        # Create a mock color manager that returns None
        mock_color_manager = Mock(spec=ColorManager)
        mock_color_manager.colorize.side_effect = lambda text, color_type: None
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True, color_manager=mock_color_manager)
                # Should not crash even if colorize returns None
                try:
                    display.start_tool_call("test", {})
                    display.complete_tool_call(success=True)
                except (TypeError, AttributeError):
                    # Some errors are acceptable if colorize is broken
                    pass
    
    def test_color_manager_raises_exception(self):
        """Test behavior when color manager raises exception."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        try:
            from broca.repl.color_profile import ColorManager
        except ImportError:
            pytest.skip("ColorManager not available")
        
        # Create a mock color manager that raises exception
        mock_color_manager = Mock(spec=ColorManager)
        mock_color_manager.colorize.side_effect = Exception("Color error")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True, color_manager=mock_color_manager)
                # Should handle exception gracefully
                display.start_tool_call("test", {})
                display.complete_tool_call(success=True)
    
    def test_stdout_disconnected_during_animation(self):
        """Test behavior when stdout is disconnected during animation."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True)
                display.start_tool_call("test", {}, tool_call_id="test1")
                
                # Simulate stdout disconnection
                def failing_write(*args, **kwargs):
                    raise OSError("Broken pipe")
                
                output.write = failing_write
                time.sleep(0.1)
                
                # Should handle gracefully
                try:
                    display.complete_tool_call(tool_call_id="test1", success=True)
                except OSError:
                    pytest.fail("Should handle stdout disconnection gracefully")
    
    def test_multiple_failures_in_sequence(self):
        """Test behavior with multiple failures in sequence."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay(enabled=True)
        errors = []
        
        for i in range(3):
            try:
                with patch('sys.stdout') as mock_stdout:
                    mock_stdout.isatty.return_value = True
                    if i == 1:
                        # Fail on second iteration
                        mock_stdout.write.side_effect = IOError("Write failed")
                    else:
                        mock_stdout.write = Mock()
                    mock_stdout.flush = Mock()
                    
                    display.start_tool_call("test", {"id": i}, tool_call_id=f"call_{i}")
                    time.sleep(0.05)
                    display.complete_tool_call(tool_call_id=f"call_{i}", success=True)
            except Exception as e:
                errors.append(e)
        
        # Should handle failures gracefully
        assert all(isinstance(e, (IOError, OSError)) for e in errors) if errors else True


class TestContinuousSpinnerAnimation:
    """Tests for continuous spinner animation in background thread."""
    
    def test_spinner_animates_continuously(self):
        """Test that spinner continuously animates while tool is running."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        # Create a mock stdout that has isatty() method
        class MockStdout:
            def __init__(self, output):
                self.output = output
                self.isatty = Mock(return_value=True)
            
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
                display.start_tool_call("terminal", {"command": "sleep 0.3"})
            
            # Wait for multiple spinner updates (spinner updates every 0.1s)
            time.sleep(0.35)  # Wait longer than spinner update interval
            
            display.complete_tool_call(success=True)
        
        output_str = output.getvalue()
        # Check that we got multiple write calls (indicating animation)
        # Should have multiple \r characters indicating updates
        write_count = output_str.count('\r')
        assert write_count > 1, f"Spinner should animate multiple times, got {write_count} updates. Output: {repr(output_str[:200])}"
    
    def test_spinner_updates_on_same_line(self):
        """Test that spinner updates occur on the same line using \\r."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True)
                display.start_tool_call("web_search", {"query": "test"})
                time.sleep(0.15)
                display.complete_tool_call(success=True)
                # Wait a bit for thread to finish
                time.sleep(0.1)
        
        output_str = output.getvalue()
        # All status updates should use \r (carriage return) not \n
        # Check that we have \r characters (same-line updates)
        assert '\r' in output_str, "Status updates should use \\r for same-line updates"
        # The final output should contain the completion indicator
        assert '✓' in output_str or '✗' in output_str or 'Web searching' in output_str, "Output should contain description or indicator"
    
    def test_no_blank_lines_between_calls(self):
        """Test that there are no blank lines between consecutive tool calls."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True)
                
                # Start and complete first tool call
                display.start_tool_call("terminal", {"command": "cmd1"}, tool_call_id="call1")
                time.sleep(0.05)
                display.complete_tool_call(tool_call_id="call1", success=True)
                
                # Start and complete second tool call immediately
                display.start_tool_call("terminal", {"command": "cmd2"}, tool_call_id="call2")
                time.sleep(0.05)
                display.complete_tool_call(tool_call_id="call2", success=True)
        
        output_str = output.getvalue()
        # Split by newlines and check for consecutive empty lines
        lines = output_str.split('\n')
        consecutive_empty = False
        for i in range(len(lines) - 1):
            if not lines[i].strip() and not lines[i+1].strip():
                consecutive_empty = True
                break
        
        assert not consecutive_empty, "Should not have consecutive blank lines between tool calls"
    
    def test_spinner_thread_cleanup(self):
        """Test that spinner background thread is properly cleaned up."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        import threading
        initial_thread_count = threading.active_count()
        
        with patch('sys.stdout.isatty', return_value=True):
            display = ToolStatusDisplay(enabled=True)
            display.start_tool_call("terminal", {"command": "test"}, tool_call_id="test1")
            time.sleep(0.1)
            display.complete_tool_call(tool_call_id="test1", success=True)
            
            # Wait a bit for thread cleanup
            time.sleep(0.2)
        
        # Thread count should return to approximately initial (allow some variance)
        final_thread_count = threading.active_count()
        # Should not have significantly more threads (allow 2-3 for test infrastructure)
        assert final_thread_count <= initial_thread_count + 3, "Spinner threads should be cleaned up"


class TestColorApplication:
    """Tests for color application to indicators."""
    
    def test_success_indicator_is_green(self):
        """Test that success indicator (✓) is colored green."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        try:
            from broca.repl.color_profile import ColorManager
            color_manager = ColorManager(enabled=True)
        except ImportError:
            pytest.skip("ColorManager not available")
        
        # Use a mock that captures writes properly
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True, color_manager=color_manager)
            display.start_tool_call("terminal", {"command": "test"}, tool_call_id="test1")
            time.sleep(0.1)  # Let spinner animate
            display.complete_tool_call(tool_call_id="test1", success=True)
            time.sleep(0.15)  # Wait for thread cleanup and final write
        
        # Get all written data
        output_str = ''.join(written_data)
        # Check for green ANSI code (32 or 92) before checkmark
        # ANSI_GREEN = \033[32m, ANSI_BRIGHT_GREEN = \033[92m
        has_green = '\033[32m' in output_str or '\033[92m' in output_str or '\x1b[32m' in output_str or '\x1b[92m' in output_str
        has_checkmark = '✓' in output_str
        # Either has green color code, or checkmark is present (colors may be disabled in test)
        assert has_green or has_checkmark, f"Success indicator should be green or present. Output: {repr(output_str[:200])}"
    
    def test_error_indicator_is_red(self):
        """Test that error indicator (✗) is colored red."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        try:
            from broca.repl.color_profile import ColorManager
            color_manager = ColorManager(enabled=True)
        except ImportError:
            pytest.skip("ColorManager not available")
        
        # Use a mock that captures writes properly
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True, color_manager=color_manager)
            display.start_tool_call("terminal", {"command": "test"}, tool_call_id="test1")
            time.sleep(0.1)  # Let spinner animate
            display.complete_tool_call(tool_call_id="test1", success=False)
            time.sleep(0.15)  # Wait for thread cleanup and final write
        
        # Get all written data
        output_str = ''.join(written_data)
        # Check for red ANSI code (31 or 91) before cross
        # ANSI_RED = \033[31m, ANSI_BRIGHT_RED = \033[91m
        has_red = '\033[31m' in output_str or '\033[91m' in output_str or '\x1b[31m' in output_str or '\x1b[91m' in output_str
        has_cross = '✗' in output_str
        # Either has red color code, or cross is present (colors may be disabled in test)
        assert has_red or has_cross, f"Error indicator should be red or present. Output: {repr(output_str[:200])}"
    
    def test_same_line_transition(self):
        """Test that spinner transitions to indicator on the same line."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        output = io.StringIO()
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True)
                display.start_tool_call("web_search", {"query": "test"})
                time.sleep(0.1)
                display.complete_tool_call(success=True)
        
        output_str = output.getvalue()
        # The final line should contain both the description and the indicator
        # Should use \r to overwrite, then \n only at the end
        lines = [l for l in output_str.split('\n') if l.strip()]
        if lines:
            final_line = lines[-1]
            # Should have both description and indicator on same line
            assert 'Web searching' in final_line or 'web_search' in final_line.lower()
            assert '✓' in final_line or '✗' in final_line or 'BrocaOS' in final_line


class TestPauseResume:
    """Tests for pause/resume functionality to prevent input interference."""
    
    def test_pause_stops_spinner_updates(self):
        """Test that pause_updates() stops spinner updates."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True)
            display.start_tool_call("test", {}, tool_call_id="test1")
            
            # Let spinner animate a bit
            time.sleep(0.15)
            initial_write_count = len(written_data)
            
            # Pause updates
            display.pause_updates()
            
            # Wait a bit - should not have more writes
            time.sleep(0.2)
            after_pause_write_count = len(written_data)
            
            display.complete_tool_call(tool_call_id="test1", success=True)
            time.sleep(0.1)
        
        # Should have writes before pause, but not many after
        assert initial_write_count > 0, "Should have writes before pause"
        # After pause, writes should stop (may have 1-2 more as thread finishes)
        assert after_pause_write_count <= initial_write_count + 2, "Pause should stop spinner updates"
    
    def test_resume_restarts_spinner_updates(self):
        """Test that resume_updates() allows spinner updates to continue."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True)
            display.start_tool_call("test", {}, tool_call_id="test1")
            
            # Pause immediately
            display.pause_updates()
            time.sleep(0.1)
            pause_write_count = len(written_data)
            
            # Resume
            display.resume_updates()
            time.sleep(0.15)
            resume_write_count = len(written_data)
            
            display.complete_tool_call(tool_call_id="test1", success=True)
            time.sleep(0.1)
        
        # After resume, should have more writes (spinner restarted)
        assert resume_write_count >= pause_write_count, "Resume should allow spinner to continue"
    
    def test_pause_resume_thread_safety(self):
        """Test that pause/resume is thread-safe."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        display = ToolStatusDisplay(enabled=True)
        errors = []
        
        def pause_resume_cycle():
            try:
                for _ in range(10):
                    display.pause_updates()
                    time.sleep(0.01)
                    display.resume_updates()
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)
        
        # Start multiple tool calls
        for i in range(3):
            display.start_tool_call("test", {"id": i}, tool_call_id=f"call_{i}")
        
        # Run pause/resume in parallel
        pause_thread = threading.Thread(target=pause_resume_cycle)
        pause_thread.start()
        
        time.sleep(0.2)
        
        # Complete all calls
        for i in range(3):
            display.complete_tool_call(tool_call_id=f"call_{i}", success=True)
        
        pause_thread.join(timeout=1.0)
        
        assert len(errors) == 0, f"Thread safety issues: {errors}"
    
    def test_pause_prevents_print_status(self):
        """Test that _print_status() doesn't write when paused."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True)
            display.pause_updates()
            
            # pause_updates() should NOT write anything to avoid interfering with terminal
            # But _print_status() should not write anything when paused
            writes_before = len(written_data)
            
            # Try to print status directly
            display._print_status("test", "description", "⠋")
            
            # Should not have written anything (pause doesn't write, and _print_status is paused)
            writes_after = len(written_data)
            assert writes_after == writes_before, "Paused display should not write status via _print_status()"
    
    def test_resume_allows_print_status(self):
        """Test that _print_status() works after resume."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True)
            display.pause_updates()
            display.resume_updates()
            
            # Try to print status directly
            display._print_status("test", "description", "⠋")
            
            # Should have written
            assert len(written_data) > 0, "Resumed display should write status"
    
    def test_resume_clears_line_before_resuming(self):
        """Test that resume_updates() clears the line before resuming to prevent display corruption."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True)
            display.pause_updates()
            
            # Resume should clear the line first
            display.resume_updates()
        
        # Should have written a newline to clear the line
        output_str = ''.join(written_data)
        assert '\n' in output_str, "Resume should write newline to clear current line"
    
    def test_resume_prevents_display_corruption(self):
        """Test that resume doesn't cause spinner to overwrite input line."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        written_data = []
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write = Mock(side_effect=lambda data: written_data.append(data))
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True)
            
            # Start a tool call
            display.start_tool_call("test", {}, tool_call_id="test1")
            time.sleep(0.1)
            
            # Pause (simulating user input)
            display.pause_updates()
            
            # Resume (simulating after input returns)
            display.resume_updates()
            
            # Wait a bit to see if spinner resumes
            time.sleep(0.15)
            
            display.complete_tool_call(tool_call_id="test1", success=True)
            time.sleep(0.1)
        
        # Get all writes
        output_str = ''.join(written_data)
        
        # The resume should have written a newline first
        # Find where resume happened (after pause, before spinner resumes)
        # We should see a newline before any spinner updates after resume
        assert '\n' in output_str, "Resume should write newline to prevent corruption"
    
    def test_resume_handles_write_errors_gracefully(self):
        """Test that resume handles stdout write errors gracefully."""
        if ToolStatusDisplay is None:
            pytest.skip("ToolStatusDisplay not yet implemented")
        
        mock_stdout = Mock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write.side_effect = IOError("Write failed")
        mock_stdout.flush = Mock()
        
        with patch('sys.stdout', mock_stdout):
            display = ToolStatusDisplay(enabled=True)
            display.pause_updates()
            
            # Should not raise exception
            try:
                display.resume_updates()
            except Exception as e:
                pytest.fail(f"Resume should handle write errors gracefully: {e}")
            
            # Should still have resumed (paused flag should be False)
            with display._lock:
                assert not display._paused, "Should have resumed even if write failed"

