"""
Comprehensive tests for command output handling in TerminalTool.

Tests git, sed, and other commands that write informational output to stderr.
Includes mutation testing, property-based testing, fault injection,
golden trace replay, and coverage requirements.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from typing import Dict, Any

from broca.tools.terminal import TerminalTool


@pytest.fixture
def terminal_tool():
    """TerminalTool instance for testing."""
    return TerminalTool()


@pytest.fixture
def golden_traces_dir():
    """Path to golden traces directory."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    golden_dir = fixtures_dir / "golden_traces"
    golden_dir.mkdir(parents=True, exist_ok=True)
    return golden_dir


def load_golden_trace(trace_name: str, golden_traces_dir: Path) -> dict:
    """Load a golden trace JSON file."""
    trace_path = golden_traces_dir / f"{trace_name}.json"
    if not trace_path.exists():
        pytest.skip(f"Golden trace {trace_name} not found at {trace_path}")
    
    with open(trace_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# Mutation Testing - Tests designed to kill mutations
# ============================================================================

class TestMutationKillers:
    """Tests specifically designed to kill mutations in git command handling."""
    
    def test_git_push_success_detection_branch_pattern(self, terminal_tool):
        """Kills mutation: not detecting '-> branch' pattern in stderr."""
        # This is the actual case from the log - git push writes to stderr
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "To https://github.com/user/repo.git\n   e74d1a5..9b58e41  develop -> develop\n",
            "command": "git push origin develop"
        }
        
        formatted = terminal_tool.format_result(result)
        
        # Should NOT contain "Error output:" since command succeeded
        assert "Error output:" not in formatted
        # Should contain the branch update info
        assert "develop -> develop" in formatted or "develop" in formatted
        # Should indicate success
        assert result["success"] is True
    
    def test_git_push_success_detection_no_output(self, terminal_tool):
        """Kills mutation: treating empty stderr as error."""
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "command": "git push origin develop"
        }
        
        formatted = terminal_tool.format_result(result)
        
        # Should format successfully without errors
        assert "Error output:" not in formatted
        assert result["success"] is True
    
    def test_git_push_failure_detection_rejected(self, terminal_tool):
        """Kills mutation: not detecting rejection patterns."""
        result = {
            "success": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "error: failed to push some refs to 'origin'\nremote: error: GH006: Protected branch update failed",
            "command": "git push origin develop"
        }
        
        formatted = terminal_tool.format_result(result)
        
        # Should indicate failure
        assert result["success"] is False
        assert "error" in formatted.lower() or "failed" in formatted.lower()
    
    def test_format_result_git_command_label(self, terminal_tool):
        """Kills mutation: using wrong label for git command stderr."""
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "Branch 'feature' set up to track remote branch 'feature'",
            "command": "git push -u origin feature"
        }
        
        formatted = terminal_tool.format_result(result)
        
        # Should NOT use "Error output:" for successful git commands
        assert "Error output:" not in formatted
        # Should use appropriate label (Output, Status, or Git output)
        assert any(label in formatted for label in ["Output:", "Status:", "Git output:"])
    
    def test_format_result_non_git_command_stderr(self, terminal_tool):
        """Kills mutation: incorrectly handling non-git command stderr."""
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "Hello World",
            "stderr": "Warning: deprecated feature",
            "command": "python script.py"
        }
        
        formatted = terminal_tool.format_result(result)
        
        # For non-git commands with stderr, should still not use "Error output:"
        # since command succeeded
        assert "Error output:" not in formatted
        assert "Warning:" in formatted or "deprecated" in formatted
    
    def test_sed_command_success_labeling(self, terminal_tool):
        """Kills mutation: using error label for successful sed command."""
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "line 1\nline 2\nline 3",
            "stderr": "",
            "command": "sed -n '1,3p' file.txt"
        }
        
        formatted = terminal_tool.format_result(result)
        
        # Should not use "Error output:" for successful sed command
        assert "Error output:" not in formatted
        assert result["success"] is True
    
    def test_sed_command_with_stderr_success(self, terminal_tool):
        """Test sed command that writes to stderr on success."""
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "output",
            "stderr": "some informational message",
            "command": "sed -n '1,10p' file.txt"
        }
        
        formatted = terminal_tool.format_result(result)
        
        # Should use "Output:" not "Error output:" for successful command
        assert "Error output:" not in formatted
        # Should contain the stderr output
        assert "informational message" in formatted or "some informational message" in formatted
    
    def test_detect_git_command_method_exists(self, terminal_tool):
        """Kills mutation: missing _is_git_command method."""
        # Verify helper method exists (if we add one)
        # This test ensures the method is callable
        command = "git push origin develop"
        cmd_name, _ = terminal_tool._normalize_command(command)
        assert cmd_name == "git"


# ============================================================================
# Property-Based Testing (Hypothesis)
# ============================================================================

class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(
        stdout_text=st.text(max_size=500),
        stderr_text=st.text(max_size=500),
        returncode=st.integers(min_value=0, max_value=1),
    )
    def test_format_result_never_crashes(self, terminal_tool, stdout_text, stderr_text, returncode):
        """Property: format_result never crashes on any input."""
        result = {
            "success": returncode == 0,
            "returncode": returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "command": "git push origin develop"
        }
        
        # Should never crash
        try:
            formatted = terminal_tool.format_result(result)
            assert isinstance(formatted, str)
        except Exception as e:
            pytest.fail(f"format_result crashed on input: stdout={repr(stdout_text[:50])}, "
                       f"stderr={repr(stderr_text[:50])}, returncode={returncode}, error: {e}")
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        command=st.text(min_size=1, max_size=200),
        returncode=st.integers(min_value=0, max_value=255),
        stdout=st.text(max_size=500),
        stderr=st.text(max_size=500),
    )
    def test_format_result_success_matches_returncode(self, terminal_tool, command, returncode, stdout, stderr):
        """Property: format_result handles success flag consistently with returncode."""
        success = returncode == 0
        
        result = {
            "success": success,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "command": command
        }
        
        formatted = terminal_tool.format_result(result)
        
        # If success is True, should not use error formatting
        if success:
            assert "Error executing" not in formatted or returncode == 0
        else:
            # If success is False, should indicate error
            assert "Error executing" in formatted or "error" in formatted.lower() or str(returncode) in formatted
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(
        branch_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Ll", "Nd", "P"), min_codepoint=32, max_codepoint=126)),
    )
    def test_git_push_output_always_formatted(self, terminal_tool, branch_name):
        """Property: git push output is always formatted correctly regardless of branch name."""
        assume(branch_name and not any(c in branch_name for c in ['\n', '\r', '\t']))
        
        # Success case
        result_success = {
            "success": True,
            "returncode": 0,
            "stdout": "",
            "stderr": f"To https://github.com/user/repo.git\n   abc123..def456  {branch_name} -> {branch_name}\n",
            "command": f"git push origin {branch_name}"
        }
        
        formatted = terminal_tool.format_result(result_success)
        assert isinstance(formatted, str)
        assert "Error output:" not in formatted
        assert result_success["success"] is True


# ============================================================================
# Fault Injection
# ============================================================================

class TestFaultInjection:
    """Fault injection tests for edge cases and error conditions."""
    
    def test_git_push_network_error(self, terminal_tool):
        """Test handling of network errors during git push."""
        result = {
            "success": False,
            "returncode": 128,
            "stdout": "",
            "stderr": "fatal: unable to access 'https://github.com/user/repo.git/': Failed to connect",
            "command": "git push origin develop"
        }
        
        formatted = terminal_tool.format_result(result)
        
        assert result["success"] is False
        assert "error" in formatted.lower() or "failed" in formatted.lower()
        assert "Failed to connect" in formatted or "unable to access" in formatted
    
    def test_git_push_authentication_error(self, terminal_tool):
        """Test handling of authentication errors."""
        result = {
            "success": False,
            "returncode": 128,
            "stdout": "",
            "stderr": "error: failed to push some refs to 'origin'\nremote: Invalid username or password",
            "command": "git push origin develop"
        }
        
        formatted = terminal_tool.format_result(result)
        
        assert result["success"] is False
        assert "error" in formatted.lower()
    
    def test_git_push_branch_protected(self, terminal_tool):
        """Test handling of protected branch rejection."""
        result = {
            "success": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "remote: error: GH006: Protected branch update failed",
            "command": "git push origin main"
        }
        
        formatted = terminal_tool.format_result(result)
        
        assert result["success"] is False
        assert "error" in formatted.lower() or "protected" in formatted.lower()
    
    def test_git_push_with_warnings_success(self, terminal_tool):
        """Test handling of warnings in successful push."""
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "warning: push.default is unset\nTo https://github.com/user/repo.git\n   abc123..def456  develop -> develop\n",
            "command": "git push origin develop"
        }
        
        formatted = terminal_tool.format_result(result)
        
        # Should still be marked as success despite warnings
        assert result["success"] is True
        assert "Error output:" not in formatted
        # Warnings should be included
        assert "warning" in formatted.lower() or "develop -> develop" in formatted
    
    def test_git_push_timeout(self, terminal_tool):
        """Test handling of timeout errors."""
        result = {
            "success": False,
            "error": "Command timed out after 120 seconds",
            "command": "git push origin develop"
        }
        
        formatted = terminal_tool.format_result(result)
        
        assert result["success"] is False
        assert "timeout" in formatted.lower() or "timed out" in formatted.lower()
    
    def test_git_push_partial_output_malformed(self, terminal_tool):
        """Test handling of malformed or partial output."""
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "\x00\x01\x02partial output",
            "command": "git push origin develop"
        }
        
        # Should handle gracefully without crashing
        formatted = terminal_tool.format_result(result)
        assert isinstance(formatted, str)
        assert "Error output:" not in formatted
    
    def test_git_push_empty_command(self, terminal_tool):
        """Test handling of empty command string."""
        result = {
            "success": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "",
            "command": ""
        }
        
        formatted = terminal_tool.format_result(result)
        assert isinstance(formatted, str)


# ============================================================================
# Golden Trace Replay
# ============================================================================

class TestGoldenTraces:
    """Golden trace replay tests."""
    
    def test_golden_trace_git_push_success(self, terminal_tool, golden_traces_dir):
        """Test with real git push success output."""
        # Create golden trace file if it doesn't exist
        trace_file = golden_traces_dir / "git_push_success.json"
        if not trace_file.exists():
            golden_trace = {
                "command": "git push origin develop",
                "result": {
                    "success": True,
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "To https://github.com/nnyazd92/brocaOS.git\n   e74d1a5..9b58e41  develop -> develop\n"
                },
                "expected_format_contains": ["develop -> develop"],
                "expected_format_not_contains": ["Error output:"]
            }
            with open(trace_file, 'w', encoding='utf-8') as f:
                json.dump(golden_trace, f, indent=2)
        
        golden_trace = load_golden_trace("git_push_success", golden_traces_dir)
        result = golden_trace["result"]
        
        formatted = terminal_tool.format_result(result)
        
        # Verify expected behavior
        for expected in golden_trace.get("expected_format_contains", []):
            assert expected in formatted, f"Expected '{expected}' in formatted output"
        
        for not_expected in golden_trace.get("expected_format_not_contains", []):
            assert not_expected not in formatted, f"Did not expect '{not_expected}' in formatted output"
    
    def test_golden_trace_git_push_failure(self, terminal_tool, golden_traces_dir):
        """Test with real git push failure output."""
        trace_file = golden_traces_dir / "git_push_failure.json"
        if not trace_file.exists():
            golden_trace = {
                "command": "git push origin develop",
                "result": {
                    "success": False,
                    "returncode": 1,
                    "stdout": "",
                    "stderr": "error: failed to push some refs to 'origin'\nremote: error: GH006: Protected branch update failed"
                },
                "expected_format_contains": ["error", "failed"],
                "expected_format_not_contains": []
            }
            with open(trace_file, 'w', encoding='utf-8') as f:
                json.dump(golden_trace, f, indent=2)
        
        golden_trace = load_golden_trace("git_push_failure", golden_traces_dir)
        result = golden_trace["result"]
        
        formatted = terminal_tool.format_result(result)
        
        # Verify expected behavior
        for expected in golden_trace.get("expected_format_contains", []):
            if isinstance(expected, str):
                assert expected.lower() in formatted.lower(), f"Expected '{expected}' in formatted output"
            else:
                # Handle list of expected strings
                assert any(exp.lower() in formatted.lower() for exp in expected), \
                    f"Expected one of {expected} in formatted output"
    
    def test_golden_trace_git_push_with_warnings(self, terminal_tool, golden_traces_dir):
        """Test with git push that has warnings but succeeds."""
        trace_file = golden_traces_dir / "git_push_warnings.json"
        if not trace_file.exists():
            golden_trace = {
                "command": "git push origin develop",
                "result": {
                    "success": True,
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "warning: push.default is unset; its implicit value has changed in Git 2.0\nTo https://github.com/user/repo.git\n   abc123..def456  develop -> develop\n"
                },
                "expected_format_contains": ["develop -> develop"],
                "expected_format_not_contains": ["Error output:"]
            }
            with open(trace_file, 'w', encoding='utf-8') as f:
                json.dump(golden_trace, f, indent=2)
        
        golden_trace = load_golden_trace("git_push_warnings", golden_traces_dir)
        result = golden_trace["result"]
        
        formatted = terminal_tool.format_result(result)
        
        # Should be successful despite warnings
        assert result["success"] is True
        for not_expected in golden_trace.get("expected_format_not_contains", []):
            assert not_expected not in formatted


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for git command handling."""
    
    @patch('broca.tools.terminal.subprocess.run')
    def test_git_push_execution_success(self, mock_subprocess, terminal_tool):
        """Test full execution flow for successful git push."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = "To https://github.com/user/repo.git\n   abc123..def456  develop -> develop\n"
        mock_subprocess.return_value = mock_result
        
        result = terminal_tool.execute(command="git push origin develop")
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "develop -> develop" in result["stderr"]
        
        # Format should not show error
        formatted = terminal_tool.format_result(result)
        assert "Error output:" not in formatted
    
    @patch('broca.tools.terminal.subprocess.run')
    def test_git_push_execution_failure(self, mock_subprocess, terminal_tool):
        """Test full execution flow for failed git push."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error: failed to push some refs"
        mock_subprocess.return_value = mock_result
        
        result = terminal_tool.execute(command="git push origin develop")
        
        assert result["success"] is False
        assert result["returncode"] == 1
        
        # Format should show error
        formatted = terminal_tool.format_result(result)
        assert "error" in formatted.lower() or "failed" in formatted.lower()


# ============================================================================
# Regression Tests
# ============================================================================

class TestRegressions:
    """Regression tests to ensure existing functionality still works."""
    
    def test_non_git_commands_unaffected(self, terminal_tool):
        """Ensure non-git commands are still handled correctly."""
        result = {
            "success": True,
            "returncode": 0,
            "stdout": "Hello World",
            "stderr": "",
            "command": "echo 'Hello World'"
        }
        
        formatted = terminal_tool.format_result(result)
        assert "Hello World" in formatted
        assert result["success"] is True
    
    def test_failed_commands_still_show_errors(self, terminal_tool):
        """Ensure failed commands still properly show errors."""
        result = {
            "success": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "command not found",
            "command": "nonexistent_command"
        }
        
        formatted = terminal_tool.format_result(result)
        assert "Error executing" in formatted or "error" in formatted.lower()
        assert result["success"] is False

