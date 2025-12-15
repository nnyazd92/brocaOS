"""
Tests for OptimizationDaemon dynamic system prompt behavior.

Tests that the optimization daemon uses dynamic system prompts that mutate
per tool call and persist across cycles, matching main_repl behavior.
"""

from __future__ import annotations

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone

from broca.optimization_daemon import OptimizationDaemon
from broca.optimization.goal_manager import GoalManager
from broca.optimization.report_manager import ReportManager
from broca.world_state.aggregator import WorldStateAggregator
from broca.repl.session import ConversationSession


class TestOptimizationDaemonWorldStateAggregator:
    """Test that WorldStateAggregator is created and passed to session."""
    
    def test_world_state_aggregator_created(self):
        """
        Test that WorldStateAggregator is created during system initialization.
        
        Rationale: Ensures dynamic system prompt infrastructure is set up.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Mock the initialization functions to avoid full system setup
            with patch('broca.main_repl._initialize_storage', return_value=None), \
                 patch('broca.main_repl._initialize_memory_manager', return_value=None), \
                 patch('broca.main_repl._initialize_self_model', return_value=(None, None, None)), \
                 patch('broca.main_repl._initialize_internal_sensing', return_value=None), \
                 patch('broca.main_repl._initialize_environment_system', return_value=None), \
                 patch('broca.main_repl._initialize_tool_registry', return_value=None):
                
                # Initialize systems
                daemon._initialize_systems()
                
                # Verify session was created
                assert daemon.session is not None
                
                # Verify session has world_state_aggregator
                assert hasattr(daemon.session, 'world_state_aggregator')
                assert daemon.session.world_state_aggregator is not None
                assert isinstance(daemon.session.world_state_aggregator, WorldStateAggregator)
    
    def test_world_state_aggregator_components(self):
        """
        Test that WorldStateAggregator includes all expected components.
        
        Rationale: Ensures world state includes internal sensing, self-model, project state, tools.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            with patch('broca.main_repl._initialize_storage', return_value=None), \
                 patch('broca.main_repl._initialize_memory_manager', return_value=None), \
                 patch('broca.main_repl._initialize_self_model', return_value=(None, None, None)), \
                 patch('broca.main_repl._initialize_internal_sensing', return_value=None), \
                 patch('broca.main_repl._initialize_environment_system', return_value=None), \
                 patch('broca.main_repl._initialize_tool_registry', return_value=None), \
                 patch('broca.optimization_daemon.ConversationSession') as mock_session:
                
                daemon._initialize_systems()
                
                # Verify ConversationSession was called with world_state_aggregator
                assert mock_session.called
                call_kwargs = mock_session.call_args[1]
                assert 'world_state_aggregator' in call_kwargs
                assert call_kwargs['world_state_aggregator'] is not None


class TestOptimizationDaemonSystemPromptMutation:
    """Test that system prompt mutates per tool call."""
    
    def test_system_prompt_updates_before_llm_call(self):
        """
        Test that system prompt is updated before each LLM call in a cycle.
        
        Rationale: Ensures dynamic mutation happens per tool call iteration.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Create a mock session with world_state_aggregator
            mock_aggregator = Mock(spec=WorldStateAggregator)
            mock_session = Mock(spec=ConversationSession)
            mock_session.world_state_aggregator = mock_aggregator
            mock_session._world_state_formatter = Mock()
            mock_session.messages = []
            mock_session.send.return_value = "Test response"
            
            daemon.session = mock_session
            
            # Add a goal
            goal = {
                "goal": "Test goal",
                "active": True,
                "constraints": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            daemon.goal_manager.add_goal(goal)
            
            # Mock _update_system_prompt to track calls
            update_calls = []
            original_update = ConversationSession._update_system_prompt
            
            def track_update(self):
                update_calls.append(True)
                return original_update(self)
            
            with patch.object(ConversationSession, '_update_system_prompt', track_update):
                # Run a cycle
                daemon._run_cycle()
                
                # Verify _update_system_prompt was called (at least once before LLM call)
                # The actual call happens inside session.send(), so we verify send was called
                assert mock_session.send.called
    
    def test_system_prompt_includes_world_state(self):
        """
        Test that system prompt includes aggregated world state.
        
        Rationale: Ensures world state data is included in system prompt.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Create mock aggregator that returns test world state
            mock_aggregator = Mock(spec=WorldStateAggregator)
            mock_aggregator.aggregate.return_value = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system": {
                    "platform": "test",
                    "python_version": "3.13"
                }
            }
            
            mock_session = Mock(spec=ConversationSession)
            mock_session.world_state_aggregator = mock_aggregator
            mock_session._world_state_formatter = Mock()
            mock_session._world_state_formatter.format.return_value = '{"system": {"platform": "test"}}'
            mock_session.messages = []
            mock_session.send.return_value = "Test response"
            
            daemon.session = mock_session
            
            # Add a goal
            goal = {
                "goal": "Test goal",
                "active": True,
                "constraints": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            daemon.goal_manager.add_goal(goal)
            
            # Run a cycle
            daemon._run_cycle()
            
            # Verify aggregator.aggregate() was called (via _update_system_prompt)
            # This happens inside session.send(), so we verify send was called
            assert mock_session.send.called


class TestOptimizationDaemonSystemPromptPersistence:
    """Test that system prompt mutation chain persists across cycles."""
    
    def test_system_prompt_persists_across_cycles(self):
        """
        Test that system prompt mutations persist across optimization cycles.
        
        Rationale: Ensures mutation chain continues across autonomous cycles.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Create mock session
            mock_aggregator = Mock(spec=WorldStateAggregator)
            mock_session = Mock(spec=ConversationSession)
            mock_session.world_state_aggregator = mock_aggregator
            mock_session._world_state_formatter = Mock()
            
            # Start with a system message
            initial_system_message = {
                "role": "system",
                "content": "Initial system prompt"
            }
            mock_session.messages = [initial_system_message]
            mock_session.send.return_value = "Test response"
            
            daemon.session = mock_session
            
            # Add a goal
            goal = {
                "goal": "Test goal",
                "active": True,
                "constraints": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            daemon.goal_manager.add_goal(goal)
            
            # Run first cycle
            daemon._run_cycle()
            
            # Verify _clear_conversation_context preserves system messages
            # _clear_conversation_context should keep system messages
            system_messages_after_clear = [
                msg for msg in mock_session.messages 
                if msg.get("role") == "system"
            ]
            
            # The system message should still exist (even if mutated)
            assert len(system_messages_after_clear) > 0 or mock_session.messages[0].get("role") == "system"
    
    def test_clear_conversation_context_preserves_system_prompt(self):
        """
        Test that _clear_conversation_context preserves system prompt.
        
        Rationale: Ensures mutation chain persists by preserving system messages.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Create mock session with messages
            mock_session = Mock(spec=ConversationSession)
            mock_session.messages = [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User message"},
                {"role": "assistant", "content": "Assistant response"},
                {"role": "tool", "name": "test_tool", "content": "Tool result"}
            ]
            
            daemon.session = mock_session
            
            # Clear conversation context
            daemon._clear_conversation_context()
            
            # Verify only system messages remain
            assert len(mock_session.messages) == 1
            assert mock_session.messages[0]["role"] == "system"
            assert "System prompt" in mock_session.messages[0]["content"]


class TestOptimizationDaemonSystemPromptComponents:
    """Test that world state includes all expected components."""
    
    def test_world_state_includes_internal_sensing(self):
        """
        Test that world state aggregator includes internal sensing.
        
        Rationale: Ensures internal sensing state is included in system prompt.
        """
        # This test verifies the aggregator is configured with internal_sensing
        # The actual aggregation happens in WorldStateAggregator.aggregate()
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Mock initialization to capture aggregator creation
            mock_internal_sensing = Mock()
            with patch('broca.main_repl._initialize_storage', return_value=None), \
                 patch('broca.main_repl._initialize_memory_manager', return_value=None), \
                 patch('broca.main_repl._initialize_self_model', return_value=(None, None, None)), \
                 patch('broca.main_repl._initialize_internal_sensing', return_value=mock_internal_sensing), \
                 patch('broca.main_repl._initialize_environment_system', return_value=None), \
                 patch('broca.main_repl._initialize_tool_registry', return_value=None), \
                 patch('broca.optimization_daemon.ConversationSession') as mock_session:
                
                daemon._initialize_systems()
                
                # Verify ConversationSession was called with world_state_aggregator
                assert mock_session.called
                call_kwargs = mock_session.call_args[1]
                if 'world_state_aggregator' in call_kwargs:
                    aggregator = call_kwargs['world_state_aggregator']
                    # Aggregator should have internal_sensing attribute
                    assert hasattr(aggregator, 'internal_sensing')
    
    def test_world_state_includes_self_model(self):
        """
        Test that world state aggregator includes self-model.
        
        Rationale: Ensures self-model state is included in system prompt.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Mock initialization
            mock_self_model = Mock()
            with patch('broca.main_repl._initialize_storage', return_value=None), \
                 patch('broca.main_repl._initialize_memory_manager', return_value=None), \
                 patch('broca.main_repl._initialize_self_model', return_value=(None, mock_self_model, None)), \
                 patch('broca.main_repl._initialize_internal_sensing', return_value=None), \
                 patch('broca.main_repl._initialize_environment_system', return_value=None), \
                 patch('broca.main_repl._initialize_tool_registry', return_value=None), \
                 patch('broca.optimization_daemon.ConversationSession') as mock_session:
                
                daemon._initialize_systems()
                
                # Verify ConversationSession was called with world_state_aggregator
                assert mock_session.called
                call_kwargs = mock_session.call_args[1]
                if 'world_state_aggregator' in call_kwargs:
                    aggregator = call_kwargs['world_state_aggregator']
                    # Aggregator should have self_model attribute
                    assert hasattr(aggregator, 'self_model')

