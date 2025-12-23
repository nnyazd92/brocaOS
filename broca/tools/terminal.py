"""
Terminal tool for executing commands.

Provides command execution, file operations, and proper error handling.
All commands are allowed - no whitelist restrictions.
"""

from __future__ import annotations

import os
import logging
import subprocess
import shlex
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from ..config import config

logger = logging.getLogger(__name__)


class TerminalTool:
    """
    Terminal tool for executing commands.
    
    Allows the LLM to execute any command, read/write files, and list directories.
    All commands are allowed - no whitelist restrictions.
    """
    
    def __init__(
        self,
        command_whitelist: Optional[List[str]] = None,
        working_directory: Optional[str] = None
    ) -> None:
        """
        Initialize the terminal tool.
        
        Args:
            command_whitelist: List of allowed command patterns (defaults to config)
            working_directory: Working directory for commands (defaults to config or current dir)
        """
        self._whitelist = command_whitelist or config.tools.terminal_command_whitelist
        self._working_directory = working_directory or config.tools.terminal_working_directory
        
        # Normalize whitelist - remove empty strings (kept for backward compatibility, but not used)
        self._whitelist = [cmd.strip() for cmd in self._whitelist if cmd.strip()]
        
        logger.info("Initialized TerminalTool (all commands allowed)")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "terminal"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Execute terminal commands and perform file operations. "
            "\n\n"
            "REQUIRED PARAMETER: 'command' (string) - The command to execute. "
            "You MUST ALWAYS provide the 'command' parameter as a non-empty string. "
            "\n\n"
            "Examples:\n"
            "  {\"command\": \"python script.py\"}\n"
            "  {\"command\": \"python3 my_script.py\"}\n"
            "  {\"command\": \"ls -la\"}\n"
            "  {\"command\": \"echo hello\", \"working_dir\": \"/path/to/dir\"}\n"
            "  {\"command\": \"python script.py\", \"timeout\": 60}\n"
            "\n"
            "All commands are allowed. Supports executing any command including Python, Sage, "
            "shell commands, and more. Can read/write files and list directories. "
            "Use this tool to create, compile, and run code files. "
            "\n\n"
            "IMPORTANT: The 'command' parameter is REQUIRED and must be a non-empty string. "
            "Never call this tool without providing the 'command' parameter."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to execute (any command is allowed)"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Optional working directory for command execution"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds (default: 30)",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300
                }
            },
            "required": ["command"]
        }
    
    def _normalize_command(self, command: str) -> Tuple[str, List[str]]:
        """
        Parse command string into command name and arguments.
        
        Args:
            command: Command string to parse
            
        Returns:
            Tuple of (command_name, arguments_list)
        """
        try:
            parts = shlex.split(command)
            if not parts:
                return "", []
            return parts[0], parts[1:]
        except ValueError:
            # If shlex fails, try simple split
            parts = command.split()
            if not parts:
                return "", []
            return parts[0], parts[1:]
    
    def _is_command_allowed(self, command: str) -> bool:
        """
        Check if command is allowed.
        
        All commands are now allowed - no restrictions.
        
        Args:
            command: Command string to check
            
        Returns:
            Always returns True (all commands allowed)
        """
        # All commands are allowed - no whitelist restrictions
        return True
    
    def _validate_path(self, path: str) -> bool:
        """
        Validate file path (prevent path traversal).
        
        Args:
            path: File path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        # Prevent path traversal
        if ".." in path:
            return False
        
        # Prevent absolute paths outside working directory if working directory is set
        if self._working_directory and os.path.isabs(path):
            try:
                abs_path = os.path.abspath(path)
                working_abs = os.path.abspath(self._working_directory)
                if not abs_path.startswith(working_abs):
                    return False
            except Exception:
                return False
        
        return True
    
    def _is_git_command(self, command: str) -> bool:
        """
        Check if command is a git command.
        
        Args:
            command: Command string to check
            
        Returns:
            True if command is a git command, False otherwise
        """
        cmd_name, _ = self._normalize_command(command)
        return cmd_name == "git"
    
    def _get_stderr_label(self, result: Dict[str, Any]) -> str:
        """
        Get appropriate label for stderr output based on command type and success status.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Appropriate label for stderr output
        """
        command = result.get("command", "")
        success = result.get("success", False)
        
        # For successful commands, don't use "Error output:"
        if success:
            if self._is_git_command(command):
                return "Git output:"
            else:
                return "Output:"
        else:
            # For failed commands, "Error output:" or "Stderr output:" is appropriate
            return "Stderr output:"
    
    def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a terminal command.
        
        Args:
            command: Command to execute
            working_dir: Optional working directory (overrides instance default)
            timeout: Command timeout in seconds
            
        Returns:
            Dictionary containing execution results
        """
        try:
            # All commands are allowed - no whitelist check needed
            
            # Determine working directory
            work_dir = working_dir or self._working_directory or os.getcwd()
            
            # Normalize command
            cmd_name, args = self._normalize_command(command)
            
            # Validate file paths in arguments
            # Skip validation for heredoc commands as shlex.split() doesn't handle them correctly
            if '<<' in command:
                # For heredoc commands, skip path validation of arguments
                # The shell will handle the heredoc correctly when executed
                logger.debug("Skipping path validation for heredoc command")
            else:
                # For normal commands, validate file paths in arguments
                for arg in args:
                    if os.path.sep in arg or "/" in arg or "\\" in arg:
                        if not self._validate_path(arg):
                            return {
                                "success": False,
                                "error": f"Invalid path in command arguments: {arg}",
                                "command": command
                            }
            
            logger.debug(f"Executing command: {command} in {work_dir}")
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {command}")
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """
        Read file contents.
        
        Args:
            path: File path to read
            
        Returns:
            Dictionary containing file contents or error
        """
        try:
            # Validate path
            if not self._validate_path(path):
                return {
                    "success": False,
                    "error": "Invalid file path (path traversal not allowed)",
                    "path": path
                }
            
            # Resolve path relative to working directory
            if self._working_directory and not os.path.isabs(path):
                full_path = os.path.join(self._working_directory, path)
            else:
                full_path = os.path.abspath(path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                return {
                    "success": False,
                    "error": "File not found",
                    "path": path
                }
            
            # Check if it's a file (not directory)
            if not os.path.isfile(full_path):
                return {
                    "success": False,
                    "error": "Path is not a file",
                    "path": path
                }
            
            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "path": path
            }
            
        except Exception as e:
            logger.error(f"Error reading file: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        Write file contents.
        
        Args:
            path: File path to write
            content: Content to write
            
        Returns:
            Dictionary containing success status or error
        """
        try:
            # Validate path
            if not self._validate_path(path):
                return {
                    "success": False,
                    "error": "Invalid file path (path traversal not allowed)",
                    "path": path
                }
            
            # Resolve path relative to working directory
            if self._working_directory and not os.path.isabs(path):
                full_path = os.path.join(self._working_directory, path)
            else:
                full_path = os.path.abspath(path)
            
            # Create parent directory if needed
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"Wrote file: {full_path}")
            
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            logger.error(f"Error writing file: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """
        List directory contents.
        
        Args:
            path: Directory path to list (default: current directory)
            
        Returns:
            Dictionary containing directory listing or error
        """
        try:
            # Validate path
            if not self._validate_path(path):
                return {
                    "success": False,
                    "error": "Invalid directory path (path traversal not allowed)",
                    "path": path
                }
            
            # Resolve path relative to working directory
            if self._working_directory and not os.path.isabs(path):
                full_path = os.path.join(self._working_directory, path)
            else:
                full_path = os.path.abspath(path)
            
            # Check if path exists
            if not os.path.exists(full_path):
                return {
                    "success": False,
                    "error": "Directory not found",
                    "path": path
                }
            
            # Check if it's a directory
            if not os.path.isdir(full_path):
                return {
                    "success": False,
                    "error": "Path is not a directory",
                    "path": path
                }
            
            # List directory
            entries = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                entries.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            
            return {
                "success": True,
                "path": path,
                "files": entries
            }
            
        except Exception as e:
            logger.error(f"Error listing directory: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format execution result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            command = result.get("command", result.get("path", "unknown"))
            error_msg = f"Error executing '{command}': {error}"
            
            # Always include stderr if available, even in error cases
            if "stderr" in result and result["stderr"]:
                error_msg += f"\n\nStderr output:\n{result['stderr']}"
            
            # Also include stdout if available (might contain useful context)
            if "stdout" in result and result["stdout"]:
                error_msg += f"\n\nStdout output:\n{result['stdout']}"
            
            # Include return code if available
            if "returncode" in result:
                error_msg += f"\n\nReturn code: {result['returncode']}"
            
            return error_msg
        
        # Format command execution result
        if "returncode" in result:
            lines = [f"Command: {result.get('command', 'unknown')}"]
            lines.append(f"Return code: {result.get('returncode', 0)}")
            
            if result.get("stdout"):
                lines.append(f"\nOutput:\n{result['stdout']}")
            
            if result.get("stderr"):
                stderr_label = self._get_stderr_label(result)
                lines.append(f"\n{stderr_label}\n{result['stderr']}")
            
            return "\n".join(lines)
        
        # Format file read result
        if "content" in result:
            path = result.get("path", "unknown")
            content = result.get("content", "")
            return f"File '{path}' contents:\n{content}"
        
        # Format file write result
        if "bytes_written" in result:
            path = result.get("path", "unknown")
            bytes_written = result.get("bytes_written", 0)
            return f"Successfully wrote {bytes_written} bytes to '{path}'"
        
        # Format directory listing result
        if "files" in result:
            path = result.get("path", "unknown")
            files = result.get("files", [])
            lines = [f"Directory '{path}' contents:"]
            for item in files:
                item_type = item.get("type", "unknown")
                item_name = item.get("name", "unknown")
                size = item.get("size")
                if size is not None:
                    lines.append(f"  {item_name} ({item_type}, {size} bytes)")
                else:
                    lines.append(f"  {item_name} ({item_type})")
            return "\n".join(lines)
        
        # Fallback
        return str(result)

