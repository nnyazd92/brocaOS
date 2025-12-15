"""
Tests for OptimizationDaemon.

Tests daemon initialization, single cycle execution, report generation, signal handling, and error recovery.
"""

from __future__ import annotations

import pytest
import tempfile
import os
import signal
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from broca.optimization_daemon import OptimizationDaemon
from broca.optimization.goal_manager import GoalManager
from broca.optimization.report_manager import ReportManager
from broca.tests.utils import build_llm_response


class TestOptimizationDaemonInitialization:
    """Test OptimizationDaemon initialization."""
    
    def test_init_with_custom_delay(self):
        """
        Test initialization with custom cycle delay.
        
        Rationale: Ensures daemon can be configured with custom delay.
        """
        daemon = OptimizationDaemon(cycle_delay_seconds=120.0)
        
        assert daemon.cycle_delay == 120.0
        assert daemon.running is False
        assert daemon.shutdown_requested is False
    
    def test_init_with_managers(self):
        """
        Test initialization with custom managers.
        
        Rationale: Ensures daemon can use custom goal/report managers.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            goal_manager = GoalManager(goals_file_path=goals_file)
            report_manager = ReportManager(reports_file_path=reports_file)
            
            daemon = OptimizationDaemon(
                goal_manager=goal_manager,
                report_manager=report_manager
            )
            
            assert daemon.goal_manager == goal_manager
            assert daemon.report_manager == report_manager


class TestOptimizationDaemonPromptBuilding:
    """Test prompt building for LLM queries."""
    
    def test_build_prompt_no_previous_report(self):
        """
        Test building prompt when no previous report exists.
        
        Rationale: Ensures prompt is correctly built for first cycle.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            prompt = daemon._build_optimization_prompt("Learn about X", None)
            
            assert "Learn about X" in prompt
            assert "first cycle" in prompt.lower()
            assert "What should I do next" in prompt
    
    def test_build_prompt_with_previous_report(self):
        """
        Test building prompt with previous report.
        
        Rationale: Ensures prompt includes context from previous cycle.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            previous_report = {
                "goal": "Learn about X",
                "cycle_number": 1,
                "timestamp": "2024-01-01T00:00:00Z",
                "actions_taken": ["web_search", "memory"],
                "findings": "Found some information",
                "next_steps": "Continue research"
            }
            
            prompt = daemon._build_optimization_prompt("Learn about X", previous_report)
            
            assert "Learn about X" in prompt
            assert "cycle 1" in prompt
            assert "Found some information" in prompt
            assert "web_search" in prompt or "memory" in prompt
    
    def test_build_prompt_with_constraints(self):
        """
        Test building prompt with constraints.
        
        Rationale: Ensures constraints are included in the prompt when present.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            constraints = ["No terminal access", "Use only memory tools"]
            prompt = daemon._build_optimization_prompt("Learn about X", None, constraints)
            
            assert "Learn about X" in prompt
            assert "constraints" in prompt.lower()
            assert "No terminal access" in prompt
            assert "Use only memory tools" in prompt
    
    def test_build_prompt_without_constraints(self):
        """
        Test building prompt without constraints (backward compatibility).
        
        Rationale: Ensures prompt works when constraints are None or empty.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Test with None constraints
            prompt = daemon._build_optimization_prompt("Learn about X", None, None)
            assert "Learn about X" in prompt
            assert "first cycle" in prompt.lower()
            
            # Test with empty constraints
            prompt = daemon._build_optimization_prompt("Learn about X", None, [])
            assert "Learn about X" in prompt
            assert "first cycle" in prompt.lower()


class TestOptimizationDaemonActionExtraction:
    """Test extraction of actions from messages."""
    
    def test_extract_actions_from_messages(self):
        """
        Test extracting tool names from conversation messages.
        
        Rationale: Ensures actions are correctly identified from message history.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            messages = [
                {"role": "user", "content": "Test"},
                {"role": "assistant", "content": "Response"},
                {"role": "tool", "name": "web_search", "content": "Results"},
                {"role": "tool", "name": "memory", "content": "Memory"},
                {"role": "assistant", "content": "Final response"}
            ]
            
            actions = daemon._extract_actions_from_messages(messages)
            
            assert "web_search" in actions
            assert "memory" in actions
            assert len(actions) == 2


class TestOptimizationDaemonContextManagement:
    """Test context clearing and management."""
    
    def test_format_conversation_summary_handles_none_content(self):
        """
        Test that _format_conversation_summary handles None content gracefully.
        
        Rationale: Ensures no TypeError when message content is None.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            messages = [
                {"role": "user", "content": "Test"},
                {"role": "assistant", "content": None},  # None content
                {"role": "tool", "name": "web_search", "content": "Results"}
            ]
            
            # Should not raise TypeError
            summary = daemon._format_conversation_summary(messages)
            assert isinstance(summary, str)
    
    def test_clear_context_after_cycle(self):
        """
        Test that context is cleared after cycle completion.
        
        Rationale: Ensures conversation context doesn't overflow between cycles.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            goal_manager = GoalManager(goals_file_path=goals_file)
            goal_manager.add_goal({
                "goal": "Test goal",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            
            daemon = OptimizationDaemon(
                goal_manager=goal_manager,
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Mock session with many messages
            mock_session = Mock()
            mock_session.send.return_value = (
                "I did research.\n\n"
                "## Report\n"
                "Actions Taken: web_search\n"
                "Findings: Found information\n"
                "Next Steps: Continue research"
            )
            # Simulate many messages (would cause overflow)
            mock_session.messages = [
                {"role": "user", "content": f"Message {i}"} for i in range(50)
            ]
            daemon.session = mock_session
            
            result = daemon._run_cycle()
            
            assert result is True
            # Verify context was cleared (messages should be reset or minimal)
            # After clearing, should have system prompt + new cycle messages
            assert len(mock_session.messages) < 50  # Context was cleared


class TestOptimizationDaemonReportGeneration:
    """Test combined report generation in main LLM response."""
    
    def test_parse_report_from_main_response(self):
        """
        Test parsing report from main LLM response (not separate call).
        
        Rationale: Ensures report is extracted from the same response that contains actions.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Response that includes both actions and report
            combined_response = (
                "I researched the topic using web_search and memory tools.\n\n"
                "## Report\n"
                "**Actions Taken:** web_search, memory\n\n"
                "**Findings:** I discovered that X is related to Y.\n\n"
                "**Next Steps:** Continue researching Y in the next cycle."
            )
            
            messages = [
                {"role": "user", "content": "What should I do?"},
                {"role": "tool", "name": "web_search", "content": "Results"},
                {"role": "tool", "name": "memory", "content": "Memory"},
                {"role": "assistant", "content": combined_response}
            ]
            
            report = daemon._parse_report_from_response(
                goal="Learn about X",
                cycle_number=1,
                llm_response=combined_response,
                messages=messages
            )
            
            assert report["goal"] == "Learn about X"
            assert report["cycle_number"] == 1
            assert "web_search" in report["actions_taken"]
            assert "memory" in report["actions_taken"]
            assert "X is related to Y" in report["findings"]
            assert "researching Y" in report["next_steps"]
    
    def test_parse_report_includes_constraints(self):
        """
        Test that parsed report includes constraints.
        
        Rationale: Ensures constraints are included in the report dictionary.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            combined_response = (
                "I researched the topic.\n\n"
                "## Report\n"
                "**Actions Taken:** web_search\n\n"
                "**Findings:** Found information\n\n"
                "**Next Steps:** Continue research"
            )
            
            messages = [
                {"role": "user", "content": "What should I do?"},
                {"role": "tool", "name": "web_search", "content": "Results"},
                {"role": "assistant", "content": combined_response}
            ]
            
            constraints = ["No terminal access", "Use only memory tools"]
            report = daemon._parse_report_from_response(
                goal="Learn about X",
                cycle_number=1,
                llm_response=combined_response,
                messages=messages,
                constraints=constraints
            )
            
            assert report["goal"] == "Learn about X"
            assert "constraints" in report
            assert report["constraints"] == constraints
    
    def test_parse_report_without_constraints(self):
        """
        Test that parsed report handles missing constraints gracefully.
        
        Rationale: Ensures backward compatibility when constraints are None.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            combined_response = (
                "I researched the topic.\n\n"
                "## Report\n"
                "**Actions Taken:** web_search\n\n"
                "**Findings:** Found information\n\n"
                "**Next Steps:** Continue research"
            )
            
            messages = [
                {"role": "user", "content": "What should I do?"},
                {"role": "tool", "name": "web_search", "content": "Results"},
                {"role": "assistant", "content": combined_response}
            ]
            
            # Test with None constraints
            report = daemon._parse_report_from_response(
                goal="Learn about X",
                cycle_number=1,
                llm_response=combined_response,
                messages=messages,
                constraints=None
            )
            
            assert report["goal"] == "Learn about X"
            # Should handle None gracefully - either missing or empty list
            assert report.get("constraints") is None or report.get("constraints") == []
    
    def test_cycle_uses_combined_response(self):
        """
        Test that cycle uses combined response (no separate report generation call).
        
        Rationale: Ensures feedback loop is tightened - one LLM call instead of two.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            goal_manager = GoalManager(goals_file_path=goals_file)
            report_manager = ReportManager(reports_file_path=reports_file)
            
            goal_manager.add_goal({
                "goal": "Learn about X",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            
            daemon = OptimizationDaemon(
                goal_manager=goal_manager,
                report_manager=report_manager
            )
            
            mock_session = Mock()
            # Single response with both actions and report
            mock_session.send.return_value = (
                "I used web_search to research.\n\n"
                "## Report\n"
                "Actions Taken: web_search\n"
                "Findings: Found information about X\n"
                "Next Steps: Continue research"
            )
            mock_session.messages = [
                {"role": "user", "content": "What should I do?"},
                {"role": "tool", "name": "web_search", "content": "Results"},
                {"role": "assistant", "content": mock_session.send.return_value}
            ]
            daemon.session = mock_session
            
            result = daemon._run_cycle()
            
            assert result is True
            # Should only call LLM once (not twice)
            assert mock_session.send.call_count == 1
            
            # Verify report was saved
            reports = report_manager.load_reports()
            assert len(reports) == 1
            assert reports[0]["goal"] == "Learn about X"
    


class TestOptimizationDaemonCycleExecution:
    """Test single cycle execution."""
    
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    @patch('broca.main_repl._initialize_tool_registry')
    def test_run_cycle_no_active_goal(self, mock_tool_registry, mock_env, mock_sensing, mock_self_model, mock_memory, mock_storage):
        """
        Test cycle execution when no active goal exists.
        
        Rationale: Ensures daemon handles missing goals gracefully.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Mock session initialization
            daemon.session = Mock()
            
            result = daemon._run_cycle()
            
            assert result is False
    
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    @patch('broca.main_repl._initialize_tool_registry')
    def test_run_cycle_success(self, mock_tool_registry, mock_env, mock_sensing, mock_self_model, mock_memory, mock_storage):
        """
        Test successful cycle execution.
        
        Rationale: Ensures cycle completes and generates report.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            goal_manager = GoalManager(goals_file_path=goals_file)
            report_manager = ReportManager(reports_file_path=reports_file)
            
            # Add active goal
            goal_manager.add_goal({
                "goal": "Learn about X",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            
            daemon = OptimizationDaemon(
                goal_manager=goal_manager,
                report_manager=report_manager
            )
            
            # Mock session - LLM called once with combined response
            mock_session = Mock()
            # Single response with both actions and report
            combined_response = (
                "I researched X using web_search.\n\n"
                "## Report\n"
                "Actions Taken: web_search\n"
                "Findings: I discovered X is related to Y\n"
                "Next Steps: Continue research"
            )
            mock_session.send.return_value = combined_response
            mock_session.messages = [
                {"role": "user", "content": "What should I do?"},
                {"role": "tool", "name": "web_search", "content": "Results"},
                {"role": "assistant", "content": combined_response}
            ]
            daemon.session = mock_session
            
            result = daemon._run_cycle()
            
            assert result is True
            # Verify LLM was called only once (combined response)
            assert mock_session.send.call_count == 1
            
            # Check that report was saved
            reports = report_manager.load_reports()
            assert len(reports) == 1
            assert reports[0]["goal"] == "Learn about X"
            assert reports[0]["cycle_number"] == 1
    
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    @patch('broca.main_repl._initialize_tool_registry')
    def test_run_cycle_with_constraints(self, mock_tool_registry, mock_env, mock_sensing, mock_self_model, mock_memory, mock_storage):
        """
        Test cycle execution with constraints in goal.
        
        Rationale: Ensures constraints are extracted and passed through the cycle.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            goal_manager = GoalManager(goals_file_path=goals_file)
            report_manager = ReportManager(reports_file_path=reports_file)
            
            # Add active goal with constraints
            goal_manager.add_goal({
                "goal": "Learn about X",
                "active": True,
                "constraints": ["No terminal access", "Use only memory tools"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            
            daemon = OptimizationDaemon(
                goal_manager=goal_manager,
                report_manager=report_manager
            )
            
            # Mock session - LLM called once with combined response
            mock_session = Mock()
            combined_response = (
                "I researched X using memory tools.\n\n"
                "## Report\n"
                "Actions Taken: memory\n"
                "Findings: I discovered X is related to Y\n"
                "Next Steps: Continue research"
            )
            mock_session.send.return_value = combined_response
            mock_session.messages = [
                {"role": "user", "content": "What should I do?"},
                {"role": "tool", "name": "memory", "content": "Memory"},
                {"role": "assistant", "content": combined_response}
            ]
            daemon.session = mock_session
            
            result = daemon._run_cycle()
            
            assert result is True
            # Verify LLM was called only once
            assert mock_session.send.call_count == 1
            
            # Check that report was saved with constraints
            reports = report_manager.load_reports()
            assert len(reports) == 1
            assert reports[0]["goal"] == "Learn about X"
            assert reports[0]["cycle_number"] == 1
            assert "constraints" in reports[0]
            assert reports[0]["constraints"] == ["No terminal access", "Use only memory tools"]
            
            # Verify constraints were included in prompt
            call_args = mock_session.send.call_args[0][0]
            assert "No terminal access" in call_args
            assert "Use only memory tools" in call_args
    
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    @patch('broca.main_repl._initialize_tool_registry')
    def test_run_cycle_without_constraints(self, mock_tool_registry, mock_env, mock_sensing, mock_self_model, mock_memory, mock_storage):
        """
        Test cycle execution without constraints (backward compatibility).
        
        Rationale: Ensures cycles work when goals don't have constraints field.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            goal_manager = GoalManager(goals_file_path=goals_file)
            report_manager = ReportManager(reports_file_path=reports_file)
            
            # Add active goal without constraints (old format)
            goal_manager.add_goal({
                "goal": "Learn about X",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            
            daemon = OptimizationDaemon(
                goal_manager=goal_manager,
                report_manager=report_manager
            )
            
            # Mock session - LLM called once with combined response
            mock_session = Mock()
            combined_response = (
                "I researched X using web_search.\n\n"
                "## Report\n"
                "Actions Taken: web_search\n"
                "Findings: I discovered X is related to Y\n"
                "Next Steps: Continue research"
            )
            mock_session.send.return_value = combined_response
            mock_session.messages = [
                {"role": "user", "content": "What should I do?"},
                {"role": "tool", "name": "web_search", "content": "Results"},
                {"role": "assistant", "content": combined_response}
            ]
            daemon.session = mock_session
            
            result = daemon._run_cycle()
            
            assert result is True
            # Verify LLM was called only once
            assert mock_session.send.call_count == 1
            
            # Check that report was saved (may or may not have constraints field)
            reports = report_manager.load_reports()
            assert len(reports) == 1
            assert reports[0]["goal"] == "Learn about X"
            assert reports[0]["cycle_number"] == 1


class TestOptimizationDaemonSignalHandling:
    """Test signal handling."""
    
    def test_signal_handler(self):
        """
        Test signal handler sets shutdown flag.
        
        Rationale: Ensures signals are handled correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            assert daemon.shutdown_requested is False
            
            # Simulate signal
            daemon._signal_handler(signal.SIGTERM, None)
            
            assert daemon.shutdown_requested is True


class TestOptimizationDaemonToolAccess:
    """Test tool access restrictions in daemon."""
    
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    @patch('broca.main_repl._initialize_tool_registry')
    def test_terminal_tool_not_available(self, mock_tool_registry, mock_env, mock_sensing, mock_self_model, mock_memory, mock_storage):
        """
        Test that terminal tool is not available in optimization daemon.
        
        Rationale: Ensures terminal tool is excluded from daemon for safety.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            # Setup mocks
            mock_storage.return_value = None
            mock_memory.return_value = None
            mock_self_model.return_value = (None, None, None)
            mock_sensing.return_value = None
            mock_env.return_value = None
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Create a mock registry with terminal tool
            from broca.tools.registry import ToolRegistry
            from broca.tools.terminal import TerminalTool
            
            mock_registry = ToolRegistry()
            terminal_tool = TerminalTool()
            # Create a mock tool for web_search
            mock_web_search = Mock()
            mock_web_search.name = "web_search"
            mock_web_search.description = "Web search tool"
            mock_web_search.parameters = {}
            
            mock_registry.register_tool(terminal_tool)
            mock_registry.register_tool(mock_web_search)
            
            mock_tool_registry.return_value = mock_registry
            
            # Initialize systems
            daemon._initialize_systems()
            
            # Verify terminal tool is removed
            assert daemon.session is not None
            tool_registry = daemon.session.tool_registry
            assert tool_registry is not None
            
            # Terminal tool should not be available
            terminal = tool_registry.get_tool("terminal")
            assert terminal is None, "Terminal tool should not be available in optimization daemon"
            
            # Other tools should still be available
            web_search = tool_registry.get_tool("web_search")
            assert web_search is not None, "Web search tool should still be available"
    
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    @patch('broca.main_repl._initialize_tool_registry')
    def test_system_prompt_excludes_terminal(self, mock_tool_registry, mock_env, mock_sensing, mock_self_model, mock_memory, mock_storage):
        """
        Test that system prompt does not mention terminal tool.
        
        Rationale: Ensures system prompt reflects tool availability.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            # Setup mocks
            mock_storage.return_value = None
            mock_memory.return_value = None
            mock_self_model.return_value = (None, None, None)
            mock_sensing.return_value = None
            mock_env.return_value = None
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Create a proper mock registry that can be iterated
            from broca.tools.registry import ToolRegistry
            mock_registry = ToolRegistry()
            mock_tool_registry.return_value = mock_registry
            
            # Initialize systems
            daemon._initialize_systems()
            
            # Check system prompt
            assert daemon.session is not None
            messages = daemon.session.messages
            system_message = next((msg for msg in messages if msg.get("role") == "system"), None)
            
            assert system_message is not None
            system_prompt = system_message.get("content", "")
            
            # Should not mention terminal tool
            assert "terminal" not in system_prompt.lower(), "System prompt should not mention terminal tool"
            
            # Should mention other tools or safety note
            assert "memory" in system_prompt.lower() or "web search" in system_prompt.lower() or "safety" in system_prompt.lower(), "System prompt should mention available tools or safety restrictions"
    
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    @patch('broca.main_repl._initialize_tool_registry')
    def test_environment_access_tool_not_available(self, mock_tool_registry, mock_env, mock_sensing, mock_self_model, mock_memory, mock_storage):
        """
        Test that environment access tool is not available in optimization daemon.
        
        Rationale: Ensures environment access tool is excluded from daemon for safety.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            # Setup mocks
            mock_storage.return_value = None
            mock_memory.return_value = None
            mock_self_model.return_value = (None, None, None)
            mock_sensing.return_value = None
            mock_env.return_value = None
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Create a mock registry with environment access tool
            from broca.tools.registry import ToolRegistry
            from broca.tools.terminal import TerminalTool
            
            mock_registry = ToolRegistry()
            terminal_tool = TerminalTool()
            # Create a mock tool for environment_access
            mock_env_tool = Mock()
            mock_env_tool.name = "environment_access"
            mock_env_tool.description = "Environment access tool"
            mock_env_tool.parameters = {}
            
            mock_registry.register_tool(terminal_tool)
            mock_registry.register_tool(mock_env_tool)
            
            mock_tool_registry.return_value = mock_registry
            
            # Initialize systems
            daemon._initialize_systems()
            
            # Verify environment access tool is removed
            assert daemon.session is not None
            tool_registry = daemon.session.tool_registry
            assert tool_registry is not None
            
            # Environment access tool should not be available
            env_tool = tool_registry.get_tool("environment_access")
            assert env_tool is None, "Environment access tool should not be available in optimization daemon"
            
            # Terminal tool should also not be available
            terminal = tool_registry.get_tool("terminal")
            assert terminal is None, "Terminal tool should not be available in optimization daemon"

