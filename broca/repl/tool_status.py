"""
Tool status display system for visual feedback during tool invocations.

Provides spinners, description formatting, and thread-safe display updates
for tool execution status in the REPL.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import shutil
import re
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .color_profile import ColorManager

# ANSI escape code pattern
_ANSI_ESCAPE_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def _strip_ansi_codes(text: str) -> str:
    """
    Strip ANSI escape codes from text.
    
    Args:
        text: Text that may contain ANSI codes
        
    Returns:
        Text with ANSI codes removed
    """
    return _ANSI_ESCAPE_PATTERN.sub('', text)


def _get_visible_width(text: str) -> int:
    """
    Get the visible width of text, excluding ANSI escape codes.
    
    Args:
        text: Text that may contain ANSI codes
        
    Returns:
        Visible width in characters
    """
    return len(_strip_ansi_codes(text))


def _get_terminal_width() -> int:
    """
    Get terminal width, with fallback to default.
    
    Returns:
        Terminal width in characters
    """
    try:
        return shutil.get_terminal_size().columns
    except (OSError, AttributeError):
        return 80  # Default fallback


class Spinner:
    """
    Terminal spinner for loading indicators.
    
    Provides animated spinner characters similar to npm's loading indicator.
    """
    
    # Spinner characters (braille patterns)
    SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    
    def __init__(self, enabled: bool = None):
        """
        Initialize spinner.
        
        Args:
            enabled: Whether spinner is enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        self._index = 0
        self._lock = threading.Lock()
        self._running = False
    
    def _get_next_char(self) -> str:
        """Get next spinner character, cycling through all characters."""
        with self._lock:
            char = self.SPINNER_CHARS[self._index]
            self._index = (self._index + 1) % len(self.SPINNER_CHARS)
            return char
    
    def start(self) -> None:
        """Start the spinner (no-op if disabled)."""
        if not self._enabled:
            return
        with self._lock:
            self._running = True
    
    def stop(self, success: bool = True) -> str:
        """
        Stop the spinner and return final indicator.
        
        Args:
            success: Whether operation succeeded
            
        Returns:
            Final indicator character (checkmark or cross)
        """
        with self._lock:
            self._running = False
        return "✓" if success else "✗"
    
    def update(self) -> str:
        """
        Get current spinner character for display.
        
        Returns:
            Current spinner character or empty string if disabled
        """
        if not self._enabled or not self._running:
            return ""
        return self._get_next_char()


class ToolDescriptionFormatter:
    """
    Formats tool names and arguments into human-readable descriptions.
    """
    
    def __init__(self):
        """Initialize formatter."""
        pass
    
    def format(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Format tool invocation into human-readable description.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments dictionary
            
        Returns:
            Human-readable description string
        """
        # Tool-specific formatting
        if tool_name == "web_search":
            query = arguments.get("query", "")
            if query:
                # Handle multiple queries (comma-separated)
                queries = [q.strip() for q in str(query).split(",") if q.strip()]
                if len(queries) > 1:
                    return f"Web searching {', '.join(queries[:3])}" + ("..." if len(queries) > 3 else "")
                else:
                    return f"Web searching {query}"
            return "Web searching"
        
        elif tool_name == "terminal":
            command = arguments.get("command", "")
            if command:
                # Handle heredoc commands specially - they can be very long
                cmd_str = str(command)
                # Check if it's a heredoc (contains <<)
                if '<<' in cmd_str:
                    # For heredocs, just show the command type, not the full content
                    # Extract the command before the heredoc marker
                    heredoc_match = re.search(r'^([^<]*?)\s*<<', cmd_str)
                    if heredoc_match:
                        base_cmd = heredoc_match.group(1).strip()
                        if base_cmd:
                            return f"Running terminal command: {base_cmd} << ..."
                    return "Running terminal command: heredoc"
                # For regular commands, truncate if too long
                if len(cmd_str) > 50:
                    return f"Running terminal command: {cmd_str[:47]}..."
                return f"Running terminal command: {cmd_str}"
            return "Running terminal command"
        
        elif tool_name == "store_memory":
            content = arguments.get("content", "")
            if content:
                content_str = str(content)
                if len(content_str) > 50:
                    return f"Storing memory: {content_str[:47]}..."
                return f"Storing memory: {content_str}"
            return "Storing memory"
        
        elif tool_name == "retrieve_memories":
            query = arguments.get("query", "")
            if query:
                query_str = str(query)
                if len(query_str) > 50:
                    return f"Retrieving memories: {query_str[:47]}..."
                return f"Retrieving memories: {query_str}"
            return "Retrieving memories"
        
        elif tool_name == "delete_memory":
            memory_id = arguments.get("memory_id", "")
            if memory_id:
                return f"Deleting memory: {memory_id}"
            return "Deleting memory"
        
        elif tool_name == "update_memory":
            memory_id = arguments.get("memory_id", "")
            if memory_id:
                return f"Updating memory: {memory_id}"
            return "Updating memory"
        
        elif tool_name == "link_memories":
            return "Linking memories"
        
        elif tool_name == "get_related_memories":
            memory_id = arguments.get("memory_id", "")
            if memory_id:
                return f"Getting related memories: {memory_id}"
            return "Getting related memories"
        
        elif tool_name == "critic":
            return "Running critic check"
        
        elif tool_name == "project_world_state":
            return "Updating project world state"
        
        elif tool_name == "query_self_model":
            return "Querying self model"
        
        elif tool_name == "environment_access":
            return "Accessing environment"
        
        # Generic fallback
        arg_count = len(arguments) if arguments else 0
        if arg_count > 0:
            return f"{tool_name} with {arg_count} argument(s)"
        return f"{tool_name}"


class ToolStatusDisplay:
    """
    Manages visual feedback for tool invocations.
    
    Provides thread-safe display of tool execution status with spinners
    and completion indicators.
    """
    
    def __init__(self, enabled: bool = None, color_manager: Optional[Any] = None):
        """
        Initialize tool status display.
        
        Args:
            enabled: Whether display is enabled (auto-detects TTY if None)
            color_manager: Optional ColorManager for colorizing output
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        self._color_manager = color_manager
        self._lock = threading.Lock()
        self._active_spinners: Dict[str, Spinner] = {}
        self._active_descriptions: Dict[str, str] = {}
        self._spinner_threads: Dict[str, threading.Thread] = {}
        self._spinner_running: Dict[str, bool] = {}
        self._paused: bool = False
        # Track which keys have had their initial status printed
        # This helps distinguish initial prints from intermediate animation updates
        self._initial_status_printed: Dict[str, bool] = {}
        # Cache the output capture detection result
        self._output_captured: Optional[bool] = None
    
    def start_tool_call(self, tool_name: str, arguments: Dict[str, Any], tool_call_id: str = "") -> None:
        """
        Start displaying status for a tool call.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
            tool_call_id: Optional unique ID for this tool call
        """
        if not self._enabled:
            return
        
        try:
            formatter = ToolDescriptionFormatter()
            description = formatter.format(tool_name, arguments)
            
            # Use tool_call_id if provided, otherwise use tool_name
            key = tool_call_id or tool_name
            
            with self._lock:
                spinner = Spinner(enabled=self._enabled)
                spinner.start()
                self._active_spinners[key] = spinner
                self._active_descriptions[key] = description
                self._spinner_running[key] = True
            
            # Print initial status line
            self._print_status(key, description, spinner.update(), is_initial=True)
            
            # Start background thread for continuous animation only if output is not captured
            # When output is captured, carriage returns don't work, so we skip animation
            # to avoid duplicate lines
            if not self._is_output_captured():
                self._start_spinner_thread(key, description)
        
        except Exception:
            # Graceful degradation - don't crash if display fails
            pass
    
    def _start_spinner_thread(self, key: str, description: str) -> None:
        """
        Start background thread to animate spinner.
        
        Args:
            key: Unique key for this tool call
            description: Description text
        """
        def animate():
            """Background thread function to continuously update spinner."""
            while True:
                with self._lock:
                    if not self._spinner_running.get(key, False) or self._paused:
                        break
                    spinner = self._active_spinners.get(key)
                    if not spinner:
                        break
                    spinner_char = spinner.update()
                    is_paused = self._paused
                
                # Check paused flag outside lock to avoid blocking
                if is_paused:
                    break
                
                if spinner_char:
                    try:
                        self._print_status(key, description, spinner_char)
                    except (IOError, OSError):
                        # Handle write errors gracefully
                        pass
                
                time.sleep(0.1)  # Update every 100ms
        
        thread = threading.Thread(target=animate, daemon=True)
        thread.start()
        with self._lock:
            self._spinner_threads[key] = thread
    
    def complete_tool_call(self, tool_call_id: str = "", tool_name: str = "", success: bool = True) -> None:
        """
        Complete displaying status for a tool call.
        
        Args:
            tool_call_id: Optional unique ID for this tool call
            tool_name: Name of the tool (used as fallback key)
            success: Whether the tool call succeeded
        """
        if not self._enabled:
            return
        
        try:
            # Use tool_call_id if provided, otherwise use tool_name
            key = tool_call_id or tool_name
            
            # Stop spinner animation
            with self._lock:
                self._spinner_running[key] = False
                spinner = self._active_spinners.pop(key, None)
                description = self._active_descriptions.pop(key, "")
                thread = self._spinner_threads.pop(key, None)
                # Clean up initial status tracking
                self._initial_status_printed.pop(key, None)
            
            # Wait briefly for thread to finish current iteration
            if thread and thread.is_alive():
                thread.join(timeout=0.15)
            
            if spinner and description:
                # Get final indicator
                indicator = spinner.stop(success=success)
                # Clear the line and print final status on same line
                # Always print final status, even if output is captured
                self._print_final(key, description, indicator, success)
        
        except Exception:
            # Graceful degradation
            pass
    
    def pause_updates(self) -> None:
        """
        Pause all spinner updates to prevent interference with user input.
        
        This should be called before user input to prevent spinner updates
        from overwriting what the user is typing. Waits for active threads
        to stop to ensure no updates occur while user is typing.
        
        Note: Does NOT write to stdout to avoid interfering with terminal
        line wrapping behavior during input().
        """
        threads_to_wait = []
        
        with self._lock:
            self._paused = True
            # Stop all active spinners
            for key in list(self._spinner_running.keys()):
                self._spinner_running[key] = False
                # Collect threads to wait for
                thread = self._spinner_threads.get(key)
                if thread:
                    threads_to_wait.append(thread)
        
        # Wait for threads to finish their current iteration (with timeout)
        # This ensures no spinner updates can occur while user is typing
        for thread in threads_to_wait:
            if thread and thread.is_alive():
                thread.join(timeout=0.15)  # Wait up to 150ms for thread to stop
        
        # Do NOT write anything to stdout here - it interferes with
        # terminal line wrapping when input() is called. The threads are
        # stopped, which is sufficient to prevent interference.
    
    def _clear_current_line(self) -> None:
        """
        Clear the current line and ensure cursor is positioned correctly.
        
        This helper method ensures we're on a fresh line before resuming
        spinner updates to prevent display corruption.
        """
        try:
            # Write a newline to ensure we're on a fresh line
            # This prevents spinner updates from overwriting the input line
            sys.stdout.write('\n')
            sys.stdout.flush()
        except (IOError, OSError):
            # Handle write errors gracefully
            pass
    
    def resume_updates(self) -> None:
        """
        Resume spinner updates after user input.
        
        This should be called after user input is received to allow
        spinner updates to continue. Clears the current line first to
        prevent display corruption.
        """
        # Clear any partial spinner output and ensure we're on a new line
        # This prevents spinner updates from overwriting the user's input line
        self._clear_current_line()
        
        with self._lock:
            self._paused = False
    
    def _is_output_captured(self) -> bool:
        """
        Detect if stdout is being captured/redirected where carriage returns won't work.
        
        When output is captured (e.g., by IDE terminal capture), carriage return
        sequences don't work properly, causing each update to appear as a new line.
        
        Returns:
            True if output appears to be captured, False otherwise
        """
        # Cache the result to avoid repeated checks
        if self._output_captured is not None:
            return self._output_captured
        
        # If not a TTY, output is definitely captured/redirected
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            self._output_captured = True
            return True
        
        # Check for common indicators of output capture
        # Some IDEs set specific environment variables when capturing output
        env_vars_to_check = [
            'CURSOR_TERMINAL_CAPTURE',
            'VSCODE_TERMINAL_CAPTURE',
            'PYCHARM_TERMINAL_CAPTURE',
        ]
        for var in env_vars_to_check:
            if os.environ.get(var, '').lower() in ('1', 'true', 'yes'):
                self._output_captured = True
                return True
        
        # Check if TERM indicates a non-interactive terminal
        term = os.environ.get('TERM', '')
        if term in ('dumb', 'unknown'):
            self._output_captured = True
            return True
        
        # If we can't detect capture, assume it's not captured
        # This allows normal spinner behavior in interactive terminals
        self._output_captured = False
        return False
    
    def _print_status(self, key: str, description: str, spinner_char: str, is_initial: bool = False) -> None:
        """
        Print status line with spinner.
        
        Args:
            key: Unique key for this tool call
            description: Description text
            spinner_char: Current spinner character
            is_initial: Whether this is the initial status print (not an animation update)
        """
        # Check if paused before writing
        with self._lock:
            if self._paused:
                return
        
        try:
            # Only print if spinner is enabled and we have a valid character
            if not spinner_char:
                return
            
            # Verify terminal is a TTY before using carriage return
            # Check hasattr first to handle cases where stdout might not have isatty
            # Use try/except to handle cases where isatty might raise or return unexpected values
            try:
                is_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
            except (AttributeError, TypeError):
                is_tty = False
            if not is_tty:
                return
            
            # If output is captured and this is an intermediate animation update,
            # skip it to avoid duplicate lines. Always allow initial and final status.
            if self._is_output_captured() and not is_initial:
                # Check if this is the initial status for this key
                with self._lock:
                    if not self._initial_status_printed.get(key, False):
                        # This is actually the initial status, mark it and allow it
                        self._initial_status_printed[key] = True
                    else:
                        # This is an intermediate animation update, skip it
                        return
            else:
                # Output not captured, or this is initial status - mark as printed
                with self._lock:
                    self._initial_status_printed[key] = True
            
            # Handle multi-line descriptions - take only first line
            # This prevents wrapping issues with long descriptions (especially heredocs)
            description_lines = description.split('\n')
            description = description_lines[0]
            
            # Get terminal width and truncate description if needed
            terminal_width = _get_terminal_width()
            prompt = "BrocaOS> "
            if self._color_manager:
                prompt = self._color_manager.colorize(prompt, "brocaos_prompt")
            
            # Calculate available width for description
            # Account for prompt width, spinner char, and space
            prompt_width = _get_visible_width(prompt)
            spinner_width = len(spinner_char)
            space_width = 1  # Space between spinner and description
            reserved_width = prompt_width + spinner_width + space_width
            
            # Reserve some margin (at least 10 chars) to prevent edge cases
            available_width = max(10, terminal_width - reserved_width - 10)
            
            # Truncate description if it's too long
            visible_desc = _strip_ansi_codes(description)
            if len(visible_desc) > available_width:
                description = description[:available_width - 3] + "..."
            
            # Use ANSI escape code to clear the line, then carriage return
            # \033[K clears from cursor to end of line
            # \r moves cursor to beginning of line
            # This ensures we overwrite any previous content, even if it was longer
            line = f"\r\033[K{prompt}{spinner_char} {description}"
            sys.stdout.write(line)
            sys.stdout.flush()  # Ensure output is immediately visible
        except (IOError, OSError, AttributeError):
            # Handle write errors gracefully (including when stdout doesn't have isatty)
            pass
    
    def _print_final(self, key: str, description: str, indicator: str, success: bool) -> None:
        """
        Print final status line with completion indicator.
        
        Always prints final status, even if output is captured, so users
        can see completion status.
        
        Args:
            key: Unique key for this tool call
            description: Description text
            indicator: Final indicator (checkmark or cross)
            success: Whether operation succeeded
        """
        try:
            # Only print if enabled
            if not self._enabled:
                return
            
            # If output is captured, print without carriage return (just newline)
            # This ensures it appears as a single line even when captured
            output_captured = self._is_output_captured()
            
            # If not a TTY and we haven't detected it as captured (truly redirected),
            # don't print final status
            if not sys.stdout.isatty() and not output_captured:
                return
            
            # Handle multi-line descriptions - take only first line
            description_lines = description.split('\n')
            description = description_lines[0]
            
            # Colorize the indicator
            if self._color_manager:
                if success:
                    indicator = self._color_manager.colorize(indicator, "success_indicator")
                else:
                    indicator = self._color_manager.colorize(indicator, "error_indicator")
            
            # Get terminal width and truncate description if needed
            terminal_width = _get_terminal_width()
            prompt = "BrocaOS> "
            if self._color_manager:
                prompt = self._color_manager.colorize(prompt, "brocaos_prompt")
            
            # Calculate available width for description
            prompt_width = _get_visible_width(prompt)
            indicator_width = _get_visible_width(indicator)
            space_width = 1  # Space between indicator and description
            reserved_width = prompt_width + indicator_width + space_width
            
            # Reserve some margin (at least 10 chars) to prevent edge cases
            available_width = max(10, terminal_width - reserved_width - 10)
            
            # Truncate description if it's too long
            visible_desc = _strip_ansi_codes(description)
            if len(visible_desc) > available_width:
                description = description[:available_width - 3] + "..."
            
            # If output is captured, don't use carriage return - just print with newline
            # This prevents duplicate lines when output is captured
            if output_captured:
                # Just print the final status on a new line
                line = f"{prompt}{indicator} {description}\n"
            else:
                # Use ANSI escape code to clear the line, then carriage return, then newline
                # \033[K clears from cursor to end of line
                # \r moves cursor to beginning of line
                # This ensures we overwrite any previous content, even if it was longer
                line = f"\r\033[K{prompt}{indicator} {description}\n"
            sys.stdout.write(line)
            sys.stdout.flush()  # Ensure output is immediately visible
        except (IOError, OSError, AttributeError):
            # Handle write errors gracefully (including when stdout doesn't have isatty)
            pass

