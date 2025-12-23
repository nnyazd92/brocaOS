"""
Tool status display system for visual feedback during tool invocations.

Provides spinners, description formatting, and thread-safe display updates
for tool execution status in the REPL.
"""

from __future__ import annotations

import sys
import threading
import time
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .color_profile import ColorManager


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
                # Truncate long commands
                cmd_str = str(command)
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
        
        elif tool_name == "version_control":
            action = arguments.get("action", "")
            if action:
                return f"Version control: {action}"
            return "Version control operation"
        
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
            
            # Print initial status line
            self._print_status(key, description, spinner.update())
        
        except Exception:
            # Graceful degradation - don't crash if display fails
            pass
    
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
            
            with self._lock:
                spinner = self._active_spinners.pop(key, None)
                description = self._active_descriptions.pop(key, "")
            
            if spinner and description:
                # Get final indicator
                indicator = spinner.stop(success=success)
                # Clear the line and print final status
                self._print_final(key, description, indicator, success)
        
        except Exception:
            # Graceful degradation
            pass
    
    def _print_status(self, key: str, description: str, spinner_char: str) -> None:
        """
        Print status line with spinner.
        
        Args:
            key: Unique key for this tool call
            description: Description text
            spinner_char: Current spinner character
        """
        try:
            # Clear line and print status
            # Use carriage return to overwrite line
            prompt = "BrocaOS> "
            if self._color_manager:
                prompt = self._color_manager.colorize(prompt, "brocaos_prompt")
            line = f"\r{prompt}{spinner_char} {description}"
            sys.stdout.write(line)
            sys.stdout.flush()
        except (IOError, OSError):
            # Handle write errors gracefully
            pass
    
    def _print_final(self, key: str, description: str, indicator: str, success: bool) -> None:
        """
        Print final status line with completion indicator.
        
        Args:
            key: Unique key for this tool call
            description: Description text
            indicator: Final indicator (checkmark or cross)
            success: Whether operation succeeded
        """
        try:
            # Clear line and print final status
            prompt = "BrocaOS> "
            if self._color_manager:
                prompt = self._color_manager.colorize(prompt, "brocaos_prompt")
            line = f"\r{prompt}{indicator} {description}\n"
            sys.stdout.write(line)
            sys.stdout.flush()
        except (IOError, OSError):
            # Handle write errors gracefully
            pass

