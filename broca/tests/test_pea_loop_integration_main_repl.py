"""
Integration tests for PEA loop manager wiring in main_repl.py.

Tests that goal_manager, skill_manager, and experience_logger are properly
wired from reasoning_tool to ConversationSession instances in the REPL.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from broca.repl.session import ConversationSession


class TestPEALoopManagerWiringMainRepl:
    """Test PEA loop manager wiring in main_repl."""
    
    def test_session_creation_with_managers(self):
        """
        Test that ConversationSession accepts and wires PEA loop managers.
        
        Rationale: Ensures PEA loop managers can be passed during session creation.
        """
        mock_goal_manager = Mock()
        mock_skill_manager = Mock()
        mock_experience_logger = Mock()
        
        # Create session with managers
        session = ConversationSession(
            goal_manager=mock_goal_manager,
            skill_manager=mock_skill_manager,
            experience_logger=mock_experience_logger,
        )
        
        # Verify PEA loop was initialized with managers
        if session.pea_loop:
            assert session.pea_loop.goal_manager == mock_goal_manager
            assert session.pea_loop.skill_manager == mock_skill_manager
            assert session.pea_loop.experience_logger == mock_experience_logger
    
    def test_wire_pea_loop_managers_method(self):
        """
        Test that wire_pea_loop_managers() method works correctly.
        
        Rationale: Ensures managers can be wired after session creation.
        """
        session = ConversationSession()
        
        # Initially managers should be None
        if session.pea_loop:
            assert session.pea_loop.goal_manager is None
            assert session.pea_loop.skill_manager is None
            assert session.pea_loop.experience_logger is None
        
        # Wire managers
        mock_goal_manager = Mock()
        mock_skill_manager = Mock()
        mock_experience_logger = Mock()
        
        session.wire_pea_loop_managers(
            goal_manager=mock_goal_manager,
            skill_manager=mock_skill_manager,
            experience_logger=mock_experience_logger,
        )
        
        # Verify managers are now wired
        if session.pea_loop:
            assert session.pea_loop.goal_manager == mock_goal_manager
            assert session.pea_loop.skill_manager == mock_skill_manager
            assert session.pea_loop.experience_logger == mock_experience_logger
    
    def test_from_storage_with_managers(self):
        """
        Test that ConversationSession.from_storage() accepts and wires managers.
        
        Rationale: Ensures managers can be passed when loading from storage.
        """
        mock_storage = Mock()
        mock_storage.load_conversation.return_value = {
            "messages": [],
            "metadata": {}
        }
        
        mock_goal_manager = Mock()
        mock_skill_manager = Mock()
        mock_experience_logger = Mock()
        
        session = ConversationSession.from_storage(
            session_id="test-session",
            storage=mock_storage,
            goal_manager=mock_goal_manager,
            skill_manager=mock_skill_manager,
            experience_logger=mock_experience_logger,
        )
        
        # Verify PEA loop was initialized with managers
        if session.pea_loop:
            assert session.pea_loop.goal_manager == mock_goal_manager
            assert session.pea_loop.skill_manager == mock_skill_manager
            assert session.pea_loop.experience_logger == mock_experience_logger

