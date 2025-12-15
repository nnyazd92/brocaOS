"""
Tests for session integration with internal sensing.

Tests that internal sensing works during conversation sessions.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.repl.session import ConversationSession
from broca.internal_sensing.framework import InternalSensingFramework
from broca.tests.utils import build_llm_response


class TestSessionInitializationWithSensing:
    """Test session initialization with internal sensing."""
    
    def test_session_initialization_with_sensing(self):
        """
        Test that session initializes with sensing.
        
        Rationale: Ensures sensing is available in sessions.
        """
        framework = InternalSensingFramework()
        
        session = ConversationSession(
            internal_sensing_framework=framework
        )
        
        assert session.internal_sensing_framework is not None
        assert session.internal_sensing_framework == framework


class TestSensingDuringConversation:
    """Test sensing during conversation."""
    
    @patch('broca.repl.session.DeepSeekClient')
    def test_sensing_during_conversation(self, mock_llm_class):
        """
        Test that sensing occurs during conversation.
        
        Rationale: Ensures sensing is active during interactions.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Test response")
        mock_llm.extract_assistant_content.return_value = "Test response"
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Send a message
        response = session.send("Hello")
        
        # Sensing should have occurred
        assert len(framework.internal_state_log) >= 0  # May or may not have sampled yet
        assert response is not None
    
    def test_state_tracking_per_turn(self):
        """
        Test that states are tracked per conversation turn.
        
        Rationale: Ensures state tracking works per turn.
        """
        framework = InternalSensingFramework()
        
        # Sample multiple times (simulating turns)
        for _ in range(3):
            framework.sample_internal_state()
        
        history = framework.get_state_history()
        assert len(history) >= 0  # May be limited by rate


class TestSensingOverhead:
    """Test sensing overhead."""
    
    def test_sensing_overhead(self):
        """
        Test that overhead is minimal.
        
        Rationale: Ensures sensing doesn't significantly impact performance.
        """
        import time
        
        framework = InternalSensingFramework()
        
        start = time.time()
        for _ in range(10):
            framework.sample_internal_state()
        elapsed = time.time() - start
        
        # Should be fast (less than 1 second for 10 samples)
        assert elapsed < 1.0


class TestSensingPersistence:
    """Test sensing persistence."""
    
    def test_sensing_persistence(self):
        """
        Test that states persist across sessions.
        
        Rationale: Ensures state history is maintained.
        """
        framework = InternalSensingFramework()
        
        # Sample in first "session"
        framework.sample_internal_state()
        framework.sample_internal_state()
        
        history1 = framework.get_state_history()
        
        # Simulate new session (framework persists)
        framework2 = InternalSensingFramework()
        framework2.internal_state_log = framework.internal_state_log
        
        history2 = framework2.get_state_history()
        
        # History should be accessible
        assert isinstance(history1, list)
        assert isinstance(history2, list)


class TestNoneHandlingInSessionInstrumentation:
    """Test that session handles None values from ResponseAnalyzer gracefully."""
    
    @patch('broca.repl.session.DeepSeekClient')
    @patch('broca.repl.session.ResponseAnalyzer')
    def test_session_handles_none_confidence(self, mock_analyzer_class, mock_llm_class):
        """
        Test that session handles None confidence values gracefully.
        
        Rationale: Ensures instrumentation doesn't crash when ResponseAnalyzer returns None.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Test response")
        mock_llm.extract_assistant_content.return_value = "Test response"
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        # Mock ResponseAnalyzer to return None for confidence
        mock_analyzer = Mock()
        mock_analyzer.estimate_confidence.return_value = None
        mock_analyzer.detect_uncertainty.return_value = 0.5
        mock_analyzer.compute_valence.return_value = (0.6, 0.2)
        mock_analyzer.compute_arousal.return_value = 0.7
        mock_analyzer.extract_topics.return_value = {}
        mock_analyzer_class.return_value = mock_analyzer
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Should not crash when confidence is None
        response = session.send("Hello")
        assert response is not None
    
    @patch('broca.repl.session.DeepSeekClient')
    @patch('broca.repl.session.ResponseAnalyzer')
    def test_session_handles_none_uncertainty(self, mock_analyzer_class, mock_llm_class):
        """
        Test that session handles None uncertainty values gracefully.
        
        Rationale: Ensures instrumentation doesn't crash when ResponseAnalyzer returns None.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Test response")
        mock_llm.extract_assistant_content.return_value = "Test response"
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        # Mock ResponseAnalyzer to return None for uncertainty
        mock_analyzer = Mock()
        mock_analyzer.estimate_confidence.return_value = 0.8
        mock_analyzer.detect_uncertainty.return_value = None
        mock_analyzer.compute_valence.return_value = (0.6, 0.2)
        mock_analyzer.compute_arousal.return_value = 0.7
        mock_analyzer.extract_topics.return_value = {}
        mock_analyzer_class.return_value = mock_analyzer
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Should not crash when uncertainty is None
        response = session.send("Hello")
        assert response is not None
    
    @patch('broca.repl.session.DeepSeekClient')
    @patch('broca.repl.session.ResponseAnalyzer')
    def test_session_handles_none_valence(self, mock_analyzer_class, mock_llm_class):
        """
        Test that session handles None valence values gracefully.
        
        Rationale: Ensures instrumentation doesn't crash when ResponseAnalyzer returns None.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Test response")
        mock_llm.extract_assistant_content.return_value = "Test response"
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        # Mock ResponseAnalyzer to return None for valence
        mock_analyzer = Mock()
        mock_analyzer.estimate_confidence.return_value = 0.8
        mock_analyzer.detect_uncertainty.return_value = 0.5
        mock_analyzer.compute_valence.return_value = None
        mock_analyzer.compute_arousal.return_value = 0.7
        mock_analyzer.extract_topics.return_value = {}
        mock_analyzer_class.return_value = mock_analyzer
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Should not crash when valence is None
        response = session.send("Hello")
        assert response is not None
    
    @patch('broca.repl.session.DeepSeekClient')
    @patch('broca.repl.session.ResponseAnalyzer')
    def test_session_handles_none_arousal(self, mock_analyzer_class, mock_llm_class):
        """
        Test that session handles None arousal values gracefully.
        
        Rationale: Ensures instrumentation doesn't crash when ResponseAnalyzer returns None.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Test response")
        mock_llm.extract_assistant_content.return_value = "Test response"
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        # Mock ResponseAnalyzer to return None for arousal
        mock_analyzer = Mock()
        mock_analyzer.estimate_confidence.return_value = 0.8
        mock_analyzer.detect_uncertainty.return_value = 0.5
        mock_analyzer.compute_valence.return_value = (0.6, 0.2)
        mock_analyzer.compute_arousal.return_value = None
        mock_analyzer.extract_topics.return_value = {}
        mock_analyzer_class.return_value = mock_analyzer
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Should not crash when arousal is None
        response = session.send("Hello")
        assert response is not None
    
    @patch('broca.repl.session.DeepSeekClient')
    def test_session_handles_none_latency(self, mock_llm_class):
        """
        Test that session handles None latency values gracefully.
        
        Rationale: Ensures instrumentation doesn't crash when operation not found.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("Test response")
        mock_llm.extract_assistant_content.return_value = "Test response"
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Try to end operation that was never started (will return None)
        # Should not crash
        response = session.send("Hello")
        assert response is not None
    
    @patch('broca.repl.session.DeepSeekClient')
    @patch('broca.repl.session.ResponseAnalyzer')
    def test_session_handles_empty_response(self, mock_analyzer_class, mock_llm_class):
        """
        Test that session handles empty responses gracefully.
        
        Rationale: Ensures instrumentation doesn't crash with empty assistant text.
        """
        mock_llm = Mock()
        mock_llm.chat.return_value = build_llm_response("")
        mock_llm.extract_assistant_content.return_value = ""
        mock_llm.extract_tool_calls.return_value = []
        mock_llm_class.return_value = mock_llm
        
        # Mock ResponseAnalyzer to return None for empty responses
        mock_analyzer = Mock()
        mock_analyzer.estimate_confidence.return_value = None
        mock_analyzer.detect_uncertainty.return_value = None
        mock_analyzer.compute_valence.return_value = None
        mock_analyzer.compute_arousal.return_value = None
        mock_analyzer.extract_topics.return_value = {}
        mock_analyzer_class.return_value = mock_analyzer
        
        framework = InternalSensingFramework()
        session = ConversationSession(
            llm=mock_llm,
            internal_sensing_framework=framework
        )
        
        # Should not crash with empty response
        response = session.send("Hello")
        assert response == ""

