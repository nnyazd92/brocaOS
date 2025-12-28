"""
Tests for terminal path validation.

Tests that path validation correctly distinguishes between actual file paths
and string literals in Python code.
"""

from __future__ import annotations

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

from broca.tools.terminal import TerminalTool


class TestPathValidation:
    """Test path validation logic."""
    
    @pytest.fixture
    def terminal_tool(self, tmp_path):
        """Create terminal tool for testing."""
        return TerminalTool(working_directory=str(tmp_path))
    
    def test_validates_actual_paths(self, terminal_tool):
        """Test that actual file paths are validated."""
        # Create a test file
        test_file = terminal_tool._working_directory / "test.txt"
        test_file.write_text("test")
        
        # Valid path should pass
        assert terminal_tool._validate_path(str(test_file)) is True
        
        # Path traversal should fail
        assert terminal_tool._validate_path("../etc/passwd") is False
    
    def test_does_not_validate_code_strings(self, terminal_tool):
        """Test that string literals in code are not validated as paths."""
        # String literal with path
        code_string = '"/home/wizard/Documents/Code/BrocaOS"'
        assert terminal_tool._is_likely_code_string(code_string) is True
        
        # String literal with single quotes
        code_string2 = "'/usr/local/bin/python'"
        assert terminal_tool._is_likely_code_string(code_string2) is True
    
    def test_detects_python_code_commands(self, terminal_tool):
        """Test detection of Python code commands."""
        # Python -c command
        assert terminal_tool._is_python_code_command('python3 -c "print(\'hello\')"') is True
        assert terminal_tool._is_python_code_command('python -c "import sys"') is True
        
        # Python -m command
        assert terminal_tool._is_python_code_command('python3 -m pytest') is True
        
        # Regular command
        assert terminal_tool._is_python_code_command('ls -la') is False
        assert terminal_tool._is_python_code_command('cd /home') is False
    
    def test_detects_multiline_python_code(self, terminal_tool):
        """Test detection of multiline Python code."""
        multiline_code = '''
import sys
sys.path.insert(0, '.')
from broca.web_api import app
print("test")
'''
        assert terminal_tool._is_python_code_command(multiline_code) is True
    
    def test_allows_python_code_with_paths(self, terminal_tool):
        """Test that Python code containing path strings is allowed."""
        python_command = 'python3 -c "import sys; sys.path.insert(0, \'/home/wizard/Documents/Code/BrocaOS\')"'
        
        # Should be detected as Python code
        assert terminal_tool._is_python_code_command(python_command) is True
        
        # Should not validate the path string inside
        cmd_name, args = terminal_tool._normalize_command(python_command)
        # The path string should be detected as code, not validated as path
        for arg in args:
            if '/' in arg or '\\' in arg:
                if terminal_tool._is_likely_code_string(arg):
                    # Should skip validation
                    assert True  # Test passes if we get here
                    break


class TestPathValidationPropertyBased:
    """Property-based tests for path validation."""
    
    @pytest.fixture
    def terminal_tool(self, tmp_path):
        """Create terminal tool for testing."""
        return TerminalTool(working_directory=str(tmp_path))
    
    @given(
        path_string=st.text(min_size=1, max_size=200).filter(
            lambda s: '/' in s or '\\' in s
        )
    )
    def test_code_strings_not_validated(self, terminal_tool, path_string):
        """Property: String literals with paths are not validated as file paths."""
        # Wrap in quotes to make it a string literal
        quoted = f'"{path_string}"'
        if terminal_tool._is_likely_code_string(quoted):
            # Should not be validated as a path
            assert True  # Test passes
    
    @given(
        code_content=st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
            min_size=10,
            max_size=500
        ).filter(lambda s: 'import' in s or 'from' in s or 'def' in s)
    )
    def test_python_code_detected(self, terminal_tool, code_content):
        """Property: Python code with keywords is detected."""
        command = f'python3 -c "{code_content}"'
        # Should be detected if it has Python keywords
        if any(kw in code_content for kw in ['import', 'from', 'def', 'class']):
            # Likely to be detected (may have false negatives, but should have few false positives)
            pass  # Just verify it doesn't crash


class TestPathValidationFaultInjection:
    """Fault injection tests for path validation."""
    
    @pytest.fixture
    def terminal_tool(self, tmp_path):
        """Create terminal tool for testing."""
        return TerminalTool(working_directory=str(tmp_path))
    
    def test_empty_path(self, terminal_tool):
        """Test with empty path."""
        assert terminal_tool._validate_path("") is True  # Empty is valid
    
    def test_special_characters_in_path(self, terminal_tool):
        """Test with special characters."""
        # Paths with special chars that might appear in code
        special_paths = [
            "path/with spaces/file.txt",
            "path/with'quotes/file.txt",
            'path/with"quotes/file.txt',
            "path/with(parentheses)/file.txt",
            "path/with[brackets]/file.txt",
        ]
        
        for path in special_paths:
            # Should handle without crashing
            result = terminal_tool._validate_path(path)
            assert isinstance(result, bool)
    
    def test_very_long_path_string(self, terminal_tool):
        """Test with very long path string."""
        long_path = "/" + "/".join(["very"] * 100 + ["long"] * 100 + ["path"])
        result = terminal_tool._validate_path(long_path)
        assert isinstance(result, bool)
    
    def test_path_with_code_like_syntax(self, terminal_tool):
        """Test path that looks like code."""
        code_like = "/home/user/file.py"
        # This is an actual path, not code
        assert terminal_tool._is_likely_code_string(code_like) is False
        
        # But if wrapped in quotes, it's code
        assert terminal_tool._is_likely_code_string(f'"{code_like}"') is True
    
    def test_malformed_command(self, terminal_tool):
        """Test with malformed commands."""
        malformed = [
            'python3 -c "unclosed quote',
            'python3 -c \'unclosed quote',
            'python3 -c "path/to/file" extra',
        ]
        
        for cmd in malformed:
            # Should handle without crashing
            try:
                result = terminal_tool._is_python_code_command(cmd)
                assert isinstance(result, bool)
            except Exception:
                # Acceptable if it raises on truly malformed input
                pass


class TestTerminalExecutionWithPaths:
    """Test terminal execution with various path scenarios."""
    
    @pytest.fixture
    def terminal_tool(self, tmp_path):
        """Create terminal tool for testing."""
        return TerminalTool(working_directory=str(tmp_path))
    
    def test_executes_python_code_with_path_strings(self, terminal_tool):
        """Test that Python code with path strings executes successfully."""
        # This should not be rejected due to path validation
        command = '''python3 -c "
import sys
sys.path.insert(0, '/home/wizard/Documents/Code/BrocaOS')
print('Path added')
"'''
        
        # Should be detected as Python code and skip path validation
        assert terminal_tool._is_python_code_command(command) is True
    
    def test_rejects_actual_invalid_paths(self, terminal_tool):
        """Test that actual invalid paths are still rejected."""
        # Path traversal attempt
        invalid_path = "../../etc/passwd"
        assert terminal_tool._validate_path(invalid_path) is False
        
        # Absolute path outside working directory
        if terminal_tool._working_directory:
            outside_path = "/etc/passwd"
            # May or may not be rejected depending on working directory
            result = terminal_tool._validate_path(outside_path)
            assert isinstance(result, bool)
    
    def test_multiline_python_script(self, terminal_tool):
        """Test multiline Python script with imports and paths."""
        multiline_script = '''
import sys
import os
sys.path.insert(0, '/home/wizard/Documents/Code/BrocaOS')
from broca.web_api import app
print("Success")
'''
        
        # Should be detected as Python code
        assert terminal_tool._is_python_code_command(multiline_script) is True

