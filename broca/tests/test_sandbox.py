"""
Tests for SandboxTool.

Tests sandbox command execution with path and command restrictions.
"""

from __future__ import annotations

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from broca.tools.sandbox import SandboxTool


class TestSandboxToolInitialization:
    """Test SandboxTool initialization."""
    
    def test_init_creates_sandbox_directory_if_missing(self):
        """
        Test that sandbox directory is created if it doesn't exist.
        
        Rationale: Ensures sandbox directory exists for safe operation.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            
            # Directory doesn't exist
            assert not os.path.exists(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Directory should be created
            assert os.path.exists(sandbox_path)
            assert os.path.isdir(sandbox_path)
    
    def test_init_uses_default_sandbox_path(self):
        """
        Test that default sandbox path is /home/wizard/broca.
        
        Rationale: Ensures default path is correct.
        """
        tool = SandboxTool()
        
        assert tool._sandbox_root == "/home/wizard/broca"
        assert tool._working_directory == "/home/wizard/broca"


class TestSandboxToolPathValidation:
    """Test path validation in SandboxTool."""
    
    def test_validate_path_allows_paths_within_sandbox(self):
        """
        Test that paths within sandbox are allowed.
        
        Rationale: Ensures valid paths are accepted.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Valid paths
            assert tool._validate_path("file.txt") is True
            assert tool._validate_path("subdir/file.txt") is True
            assert tool._validate_path(os.path.join(sandbox_path, "file.txt")) is True
            assert tool._validate_path(os.path.join(sandbox_path, "subdir", "file.txt")) is True
    
    def test_validate_path_blocks_path_traversal(self):
        """
        Test that path traversal (..) is blocked.
        
        Rationale: Prevents escaping sandbox directory.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Path traversal attempts
            assert tool._validate_path("../file.txt") is False
            assert tool._validate_path("subdir/../../file.txt") is False
            assert tool._validate_path("../../etc/passwd") is False
    
    def test_validate_path_blocks_paths_outside_sandbox(self):
        """
        Test that paths outside sandbox are blocked.
        
        Rationale: Prevents accessing files outside sandbox.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            # Create file outside sandbox
            outside_file = os.path.join(tmpdir, "outside.txt")
            Path(outside_file).touch()
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Absolute path outside sandbox
            assert tool._validate_path(outside_file) is False
            
            # Relative paths are always resolved relative to sandbox root
            # So "outside.txt" becomes "sandbox_root/outside.txt" which is valid
            # To test blocking paths outside, we need to use path traversal
            assert tool._validate_path("../outside.txt") is False
    
    def test_validate_path_handles_absolute_paths_correctly(self):
        """
        Test that absolute paths are validated correctly.
        
        Rationale: Ensures absolute paths within sandbox are allowed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Absolute path within sandbox
            valid_abs = os.path.join(sandbox_path, "file.txt")
            assert tool._validate_path(valid_abs) is True
            
            # Absolute path outside sandbox
            invalid_abs = os.path.join(tmpdir, "file.txt")
            assert tool._validate_path(invalid_abs) is False


class TestSandboxToolCommandWhitelist:
    """Test command whitelist enforcement."""
    
    def test_allowed_commands_pass_whitelist(self):
        """
        Test that whitelisted commands are allowed.
        
        Rationale: Ensures allowed commands can be executed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Allowed commands
            allowed = [
                "python script.py",
                "python3 script.py",
                "cat file.txt",
                "head file.txt",
                "tail file.txt",
                "grep pattern file.txt",
                "find . -name '*.py'",
                "ls -la",
                "pwd",
                "mkdir newdir",
                "touch file.txt",
                "echo hello",
                "printf 'test'",
                "cd subdir"
            ]
            
            for cmd in allowed:
                assert tool._is_command_allowed(cmd) is True, f"Command should be allowed: {cmd}"
    
    def test_blocked_commands_fail_whitelist(self):
        """
        Test that non-whitelisted commands are blocked.
        
        Rationale: Ensures dangerous commands are prevented.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Blocked commands
            blocked = [
                "rm file.txt",
                "rm -rf /",
                "mv file.txt /tmp",
                "cp file.txt /tmp",
                "chmod 777 file.txt",
                "chown user file.txt",
                "curl http://example.com",
                "wget http://example.com",
                "nc -l 1234",
                "bash -c 'rm -rf /'",
                "sh -c 'dangerous'",
                "/bin/rm file.txt"
            ]
            
            for cmd in blocked:
                assert tool._is_command_allowed(cmd) is False, f"Command should be blocked: {cmd}"


class TestSandboxToolExecution:
    """Test command execution in sandbox."""
    
    def test_execute_python_command(self):
        """
        Test that Python commands can be executed.
        
        Rationale: Core functionality for autonomous learning.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Execute Python command
            result = tool.execute(command="python3 -c 'print(\"Hello from sandbox\")'")
            
            assert result["success"] is True
            assert "Hello from sandbox" in result["stdout"]
    
    def test_execute_file_operations(self):
        """
        Test that file operations work within sandbox.
        
        Rationale: Allows creating and reading files for artifacts.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Create file
            result = tool.execute(command="touch test_file.txt")
            assert result["success"] is True
            
            # Verify file exists
            file_path = os.path.join(sandbox_path, "test_file.txt")
            assert os.path.exists(file_path)
            
            # Write to file
            result = tool.execute(command="echo 'test content' > test_file.txt")
            assert result["success"] is True
            
            # Read file
            result = tool.execute(command="cat test_file.txt")
            assert result["success"] is True
            assert "test content" in result["stdout"]
    
    def test_execute_rejects_blocked_commands(self):
        """
        Test that blocked commands are rejected.
        
        Rationale: Ensures security restrictions work.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Try to execute blocked command
            result = tool.execute(command="rm -rf /")
            
            assert result["success"] is False
            assert "not allowed" in result["error"].lower() or "blocked" in result["error"].lower()
    
    def test_execute_rejects_paths_outside_sandbox(self):
        """
        Test that commands with paths outside sandbox are rejected.
        
        Rationale: Prevents accessing files outside sandbox.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            # Create file outside sandbox
            outside_file = os.path.join(tmpdir, "outside.txt")
            Path(outside_file).touch()
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Try to access file outside sandbox
            result = tool.execute(command=f"cat {outside_file}")
            
            assert result["success"] is False
            assert "invalid path" in result["error"].lower() or "outside" in result["error"].lower()
    
    def test_execute_works_with_working_dir_parameter(self):
        """
        Test that working_dir parameter works correctly.
        
        Rationale: Allows executing commands in subdirectories.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            subdir = os.path.join(sandbox_path, "subdir")
            os.makedirs(subdir)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Execute in subdirectory
            result = tool.execute(command="pwd", working_dir=subdir)
            
            assert result["success"] is True
            assert "subdir" in result["stdout"]
    
    def test_execute_rejects_working_dir_outside_sandbox(self):
        """
        Test that working_dir outside sandbox is rejected.
        
        Rationale: Prevents escaping sandbox via working directory.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            outside_dir = os.path.join(tmpdir, "outside")
            os.makedirs(outside_dir)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            # Try to use working directory outside sandbox
            result = tool.execute(command="pwd", working_dir=outside_dir)
            
            assert result["success"] is False
            assert "invalid" in result["error"].lower() or "outside" in result["error"].lower()


class TestSandboxToolFormatResult:
    """Test result formatting."""
    
    def test_format_result_success(self):
        """
        Test that successful results are formatted correctly.
        
        Rationale: Ensures LLM can understand tool output.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            result = {
                "success": True,
                "stdout": "Hello",
                "stderr": "",
                "returncode": 0,
                "command": "echo Hello"
            }
            
            formatted = tool.format_result(result)
            
            assert "Hello" in formatted
            assert "success" in formatted.lower() or "completed" in formatted.lower()
    
    def test_format_result_error(self):
        """
        Test that error results are formatted correctly.
        
        Rationale: Ensures errors are clearly communicated.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox_path = os.path.join(tmpdir, "broca")
            os.makedirs(sandbox_path)
            
            tool = SandboxTool(sandbox_root=sandbox_path)
            
            result = {
                "success": False,
                "error": "Command not allowed",
                "command": "rm file.txt"
            }
            
            formatted = tool.format_result(result)
            
            assert "error" in formatted.lower() or "not allowed" in formatted.lower()
            assert "rm" in formatted


class TestSandboxToolProperties:
    """Test tool properties."""
    
    def test_name_property(self):
        """Test that name property returns 'sandbox'."""
        tool = SandboxTool()
        assert tool.name == "sandbox"
    
    def test_description_property(self):
        """Test that description is provided."""
        tool = SandboxTool()
        desc = tool.description
        assert isinstance(desc, str)
        assert len(desc) > 0
        assert "sandbox" in desc.lower()
    
    def test_parameters_property(self):
        """Test that parameters schema is provided."""
        tool = SandboxTool()
        params = tool.parameters
        assert isinstance(params, dict)
        assert "type" in params
        assert "properties" in params
        assert "command" in params["properties"]

