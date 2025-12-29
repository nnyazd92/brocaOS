"""
Integration tests for PEA loop manager wiring in web_api.py.

Tests that goal_manager, skill_manager, and experience_logger are properly
wired from reasoning_tool to ConversationSession instances.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from broca.web_api import create_session, get_runtime
from broca.repl.session import ConversationSession


class TestPEALoopManagerWiring:
    """Test PEA loop manager wiring in web_api."""
    
    @patch('broca.web_api.get_runtime')
    def test_create_session_wires_pea_loop_managers(self, mock_get_runtime):
        """
        Test that create_session() wires PEA loop managers from reasoning_tool.
        
        Rationale: Ensures PEA loop managers are available in web API sessions.
        """
        # Setup mock runtime with reasoning_tool
        mock_goal_manager = Mock()
        mock_skill_manager = Mock()
        mock_experience_logger = Mock()
        
        mock_learning_tool = Mock()
        mock_learning_tool.skill_manager = mock_skill_manager
        mock_learning_tool.experience_logger = mock_experience_logger
        
        mock_reasoning_tool = Mock()
        mock_reasoning_tool.goal_manager = mock_goal_manager
        mock_reasoning_tool.learning_tool = mock_learning_tool
        
        mock_storage = Mock()
        mock_storage.load_conversation.return_value = {
            "messages": [],
            "metadata": {}
        }
        
        mock_runtime = Mock()
        mock_runtime.reasoning_tool = mock_reasoning_tool
        mock_runtime.conversation_storage = mock_storage
        mock_runtime.tool_registry = None
        mock_runtime.internal_sensing = None
        mock_runtime.world_state_aggregator = None
        
        mock_get_runtime.return_value = mock_runtime
        
        # Create session
        conversation_id = str(uuid4())
        session = create_session(conversation_id)
        
        # Verify PEA loop was initialized with managers
        assert session.pea_loop is not None
        assert session.pea_loop.goal_manager == mock_goal_manager
        assert session.pea_loop.skill_manager == mock_skill_manager
        assert session.pea_loop.experience_logger == mock_experience_logger
    
    @patch('broca.web_api.get_runtime')
    def test_create_session_handles_missing_managers(self, mock_get_runtime):
        """
        Test that create_session() handles missing managers gracefully.
        
        Rationale: Ensures system works even if reasoning_tool or managers are unavailable.
        """
        mock_storage = Mock()
        mock_storage.load_conversation.return_value = {
            "messages": [],
            "metadata": {}
        }
        
        mock_runtime = Mock()
        mock_runtime.reasoning_tool = None  # No reasoning tool
        mock_runtime.conversation_storage = mock_storage
        mock_runtime.tool_registry = None
        mock_runtime.internal_sensing = None
        mock_runtime.world_state_aggregator = None
        
        mock_get_runtime.return_value = mock_runtime
        
        # Create session - should not raise
        conversation_id = str(uuid4())
        session = create_session(conversation_id)
        
        # PEA loop may be None or initialized with None managers
        if session.pea_loop:
            # If PEA loop exists, managers should be None
            assert session.pea_loop.goal_manager is None
            assert session.pea_loop.skill_manager is None
            assert session.pea_loop.experience_logger is None
    
    @patch('broca.web_api.get_runtime')
    def test_create_session_handles_partial_managers(self, mock_get_runtime):
        """
        Test that create_session() handles partial manager availability.
        
        Rationale: Ensures system works if only some managers are available.
        """
        mock_goal_manager = Mock()
        
        mock_reasoning_tool = Mock()
        mock_reasoning_tool.goal_manager = mock_goal_manager
        mock_reasoning_tool.learning_tool = None  # No learning tool
        
        mock_storage = Mock()
        mock_storage.load_conversation.return_value = {
            "messages": [],
            "metadata": {}
        }
        
        mock_runtime = Mock()
        mock_runtime.reasoning_tool = mock_reasoning_tool
        mock_runtime.conversation_storage = mock_storage
        mock_runtime.tool_registry = None
        mock_runtime.internal_sensing = None
        mock_runtime.world_state_aggregator = None
        
        mock_get_runtime.return_value = mock_runtime
        
        # Create session
        conversation_id = str(uuid4())
        session = create_session(conversation_id)
        
        # Verify goal_manager is wired, but skill_manager and experience_logger are None
        if session.pea_loop:
            assert session.pea_loop.goal_manager == mock_goal_manager
            assert session.pea_loop.skill_manager is None
            assert session.pea_loop.experience_logger is None

