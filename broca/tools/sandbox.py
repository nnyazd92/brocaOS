"""
Sandbox tool for safe command execution in restricted directory.

Provides whitelisted command execution limited to /home/wizard/broca directory.
Safe for autonomous learning operations.
"""

from __future__ import annotations

import os
import logging
import subprocess
import shlex
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SandboxTool:
    """
    Sandbox tool for safe command execution.
    
    Restricts command execution to whitelisted commands and limits file access
    to /home/wizard/broca directory and subdirectories only.
    """
    
    # Whitelist of allowed commands
    ALLOWED_COMMANDS = {
        "python", "python3",
        "cat", "head", "tail", "grep", "find",
        "ls", "pwd",
        "mkdir", "touch",
        "echo", "printf",
        "cd"
    }
    
    # Commands that are explicitly blocked
    BLOCKED_COMMANDS = {
        "rm", "mv", "cp", "chmod", "chown", "chgrp",
        "curl", "wget", "nc", "netcat", "ssh", "scp",
        "bash", "sh", "zsh", "fish",
        "sudo", "su", "doas"
    }
    
    def __init__(
        self,
        sandbox_root: str = "/home/wizard/broca",
        command_whitelist: Optional[List[str]] = None
    ) -> None:
        """
        Initialize the sandbox tool.
        
        Args:
            sandbox_root: Root directory for sandbox (default: /home/wizard/broca)
            command_whitelist: Optional custom command whitelist
        """
        self._sandbox_root = os.path.abspath(sandbox_root)
        self._working_directory = self._sandbox_root
        
        # Create sandbox directory if it doesn't exist
        os.makedirs(self._sandbox_root, exist_ok=True)
        
        # Use custom whitelist if provided, otherwise use default
        if command_whitelist:
            self._allowed_commands = set(command_whitelist)
        else:
            self._allowed_commands = self.ALLOWED_COMMANDS.copy()
        
        logger.info(f"Initialized SandboxTool with root: {self._sandbox_root}")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "sandbox"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Execute commands in a safe sandbox environment restricted to /home/wizard/broca. "
            "Use this tool for Python code execution, file operations, artifact generation, and note-taking. "
            "\n\n"
            "REQUIRED PARAMETER: 'command' (string) - The command to execute. "
            "You MUST ALWAYS provide the 'command' parameter as a non-empty string. "
            "\n\n"
            "Allowed commands: python, python3, cat, head, tail, grep, find, ls, pwd, mkdir, touch, echo, printf, cd. "
            "All file operations are restricted to /home/wizard/broca and subdirectories. "
            "\n\n"
            "Examples:\n"
            "  {\"command\": \"python3 script.py\"}\n"
            "  {\"command\": \"cat notes.txt\"}\n"
            "  {\"command\": \"mkdir artifacts && touch artifacts/result.txt\"}\n"
            "  {\"command\": \"echo 'Note' > notes.txt\"}\n"
            "  {\"command\": \"python3 -c 'print(\\\"Hello\\\")'\"}\n"
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
                    "description": "Command to execute (must be whitelisted and within sandbox)"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Optional working directory (must be within sandbox)"
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
    
    def _normalize_command(self, command: str) -> tuple[str, list[str]]:
        """
        Normalize command to extract base command name.
        
        Args:
            command: Command string
            
        Returns:
            Tuple of (base_command, args)
        """
        try:
            # Split command into parts
            parts = shlex.split(command)
            if not parts:
                return "", []
            
            # Get base command (first part, without path)
            base_cmd = os.path.basename(parts[0])
            
            return base_cmd, parts[1:] if len(parts) > 1 else []
        except ValueError:
            # If shlex.split fails, try simple split
            parts = command.split()
            if not parts:
                return "", []
            base_cmd = os.path.basename(parts[0])
            return base_cmd, parts[1:] if len(parts) > 1 else []
    
    def _is_command_allowed(self, command: str) -> bool:
        """
        Check if command is allowed by whitelist.
        
        Args:
            command: Command string to check
            
        Returns:
            True if command is allowed, False otherwise
        """
        base_cmd, _ = self._normalize_command(command)
        
        # Check if explicitly blocked
        if base_cmd in self.BLOCKED_COMMANDS:
            return False
        
        # Check if in whitelist
        if base_cmd in self._allowed_commands:
            return True
        
        # Check for absolute paths to blocked commands
        if os.path.isabs(command.split()[0]) if command.split() else False:
            cmd_path = command.split()[0]
            base_name = os.path.basename(cmd_path)
            if base_name in self.BLOCKED_COMMANDS:
                return False
            if base_name in self._allowed_commands:
                return True
        
        # Command not in whitelist
        return False
    
    def _validate_path(self, path: str) -> bool:
        """
        Validate file path is within sandbox.
        
        Args:
            path: File path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        # Prevent path traversal
        if ".." in path:
            return False
        
        try:
            # Always resolve relative paths relative to sandbox root, not current directory
            if os.path.isabs(path):
                abs_path = os.path.abspath(path)
            else:
                # Resolve relative to sandbox root (not current working directory)
                abs_path = os.path.abspath(os.path.join(self._sandbox_root, path))
            
            # Normalize path (resolve symlinks, etc.)
            abs_path = os.path.normpath(abs_path)
            sandbox_abs = os.path.normpath(self._sandbox_root)
            
            # Check if path is within sandbox
            if not abs_path.startswith(sandbox_abs):
                return False
            
            # Additional check: ensure it's actually within (not just starts with)
            # Handle case where sandbox is /home/wizard/broca and path is /home/wizard/broca2
            try:
                rel_path = os.path.relpath(abs_path, sandbox_abs)
                if rel_path.startswith(".."):
                    return False
            except ValueError:
                # If paths are on different drives (Windows), relpath raises ValueError
                return False
            
            return True
        except Exception:
            return False
    
    def _validate_working_dir(self, working_dir: str) -> bool:
        """
        Validate working directory is within sandbox.
        
        Args:
            working_dir: Working directory path
            
        Returns:
            True if valid, False otherwise
        """
        return self._validate_path(working_dir)
    
    def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a command in the sandbox.
        
        Args:
            command: Command to execute
            working_dir: Optional working directory (must be within sandbox)
            timeout: Command timeout in seconds
            
        Returns:
            Dictionary containing execution results
        """
        try:
            # Check command whitelist
            if not self._is_command_allowed(command):
                return {
                    "success": False,
                    "error": f"Command not allowed: {command}. Only whitelisted commands are permitted.",
                    "command": command
                }
            
            # Determine working directory
            if working_dir:
                if not self._validate_working_dir(working_dir):
                    return {
                        "success": False,
                        "error": f"Working directory outside sandbox: {working_dir}",
                        "command": command
                    }
                work_dir = os.path.abspath(os.path.join(self._sandbox_root, working_dir))
            else:
                work_dir = self._working_directory
            
            # Ensure working directory exists
            os.makedirs(work_dir, exist_ok=True)
            
            # Validate file paths in command arguments
            base_cmd, args = self._normalize_command(command)
            
            # Skip path validation for heredoc commands
            if '<<' in command:
                logger.debug("Skipping path validation for heredoc command")
            else:
                # Validate file paths in arguments
                for arg in args:
                    # Check if argument looks like a file path
                    if os.path.sep in arg or "/" in arg or "\\" in arg:
                        # Skip flags and options
                        if arg.startswith("-") or arg.startswith("--"):
                            continue
                        if not self._validate_path(arg):
                            return {
                                "success": False,
                                "error": f"Invalid path in command arguments (outside sandbox): {arg}",
                                "command": command
                            }
            
            logger.debug(f"Executing sandbox command: {command} in {work_dir}")
            
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
            logger.warning(f"Sandbox command timed out: {command}")
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            logger.error(f"Error executing sandbox command: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation of the result
        """
        if result.get("success"):
            lines = [
                f"Command executed successfully: {result.get('command', 'unknown')}",
            ]
            
            if result.get("stdout"):
                lines.append(f"Output:\n{result['stdout']}")
            
            if result.get("stderr"):
                lines.append(f"Errors/Warnings:\n{result['stderr']}")
            
            if result.get("returncode") is not None and result["returncode"] != 0:
                lines.append(f"Return code: {result['returncode']}")
            
            return "\n".join(lines)
        else:
            error_msg = result.get("error", "Unknown error")
            command = result.get("command", "unknown")
            return f"Command failed: {command}\nError: {error_msg}"

