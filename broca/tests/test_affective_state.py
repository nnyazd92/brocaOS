"""
Tests for ComputationalAffectMonitor.

Tests affective state tracking including valence, arousal, curiosity, and satisfaction.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.internal_sensing.affective_state import ComputationalAffectMonitor
from broca.internal_sensing.cognitive_state import CognitiveStateMonitor


class TestAffectiveStateInitialization:
    """Test ComputationalAffectMonitor initialization."""
    
    def test_initialization(self):
        """
        Test that monitor initializes with default affective states.
        
        Rationale: Ensures monitor starts with proper default state.
        """
        monitor = ComputationalAffectMonitor()
        
        assert monitor.affective_states is not None
        assert "valence" in monitor.affective_states
        assert "arousal" in monitor.affective_states
        assert "certainty_affect" in monitor.affective_states
        assert "curiosity_drive" in monitor.affective_states
        assert "coherence_pleasure" in monitor.affective_states
        
        # Check default values are None (unknown until computed)
        assert monitor.affective_states["valence"] is None
        assert monitor.affective_states["arousal"] is None
        assert monitor.affective_states["certainty_affect"] is None
        assert monitor.affective_states["curiosity_drive"] is None
        assert monitor.affective_states["coherence_pleasure"] is None


class TestValenceComputation:
    """Test valence computation functionality."""
    
    def test_valence_computation(self):
        """
        Test that positive/negative evaluation is computed.
        
        Rationale: Ensures valence is properly calculated.
        """
        monitor = ComputationalAffectMonitor()
        
        monitor.compute_valence(positive_score=0.7, negative_score=0.2)
        valence = monitor.affective_states["valence"]
        
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        assert valence > 0.0  # Should be positive
    
    def test_valence_negative(self):
        """
        Test that negative evaluation produces negative valence.
        
        Rationale: Ensures valence reflects negative states.
        """
        monitor = ComputationalAffectMonitor()
        
        monitor.compute_valence(positive_score=0.2, negative_score=0.8)
        valence = monitor.affective_states["valence"]
        
        assert valence < 0.0  # Should be negative


class TestArousalComputation:
    """Test arousal computation functionality."""
    
    def test_arousal_computation(self):
        """
        Test that activation level is computed.
        
        Rationale: Ensures arousal is properly calculated.
        """
        monitor = ComputationalAffectMonitor()
        
        monitor.compute_arousal(activation_level=0.8)
        arousal = monitor.affective_states["arousal"]
        
        assert isinstance(arousal, float)
        assert 0.0 <= arousal <= 1.0
        assert arousal == 0.8


class TestCertaintyAffect:
    """Test certainty affect tracking."""
    
    def test_certainty_affect(self):
        """
        Test that emotional aspect of confidence is tracked.
        
        Rationale: Ensures certainty affect is monitored.
        """
        monitor = ComputationalAffectMonitor()
        
        monitor.update_certainty_affect(confidence=0.9)
        certainty_affect = monitor.affective_states["certainty_affect"]
        
        assert isinstance(certainty_affect, float)
        assert 0.0 <= certainty_affect <= 1.0
        assert certainty_affect > 0.5  # Should be high for high confidence


class TestCuriosityDrive:
    """Test curiosity drive tracking."""
    
    def test_curiosity_drive(self):
        """
        Test that motivation to explore is computed.
        
        Rationale: Ensures curiosity is tracked.
        """
        monitor = ComputationalAffectMonitor()
        
        monitor.compute_curiosity_drive(uncertainty=0.7, interest=0.8)
        curiosity = monitor.affective_states["curiosity_drive"]
        
        assert isinstance(curiosity, float)
        assert 0.0 <= curiosity <= 1.0
        assert curiosity > 0.0


class TestCoherencePleasure:
    """Test coherence pleasure tracking."""
    
    def test_coherence_pleasure(self):
        """
        Test that satisfaction from understanding is tracked.
        
        Rationale: Ensures coherence satisfaction is monitored.
        """
        monitor = ComputationalAffectMonitor()
        
        monitor.update_coherence_pleasure(coherence=0.9)
        pleasure = monitor.affective_states["coherence_pleasure"]
        
        assert isinstance(pleasure, float)
        assert 0.0 <= pleasure <= 1.0
        assert pleasure > 0.5  # Should be high for high coherence


class TestAffectiveFromCognitive:
    """Test affective state derivation from cognitive states."""
    
    def test_affective_from_cognitive(self):
        """
        Test that affective states are derived from cognitive.
        
        Rationale: Ensures affective states integrate cognitive information.
        """
        cognitive_monitor = CognitiveStateMonitor()
        cognitive_monitor.record_confidence("r1", 0.8)
        cognitive_monitor.record_attention("topic1", 0.6)
        
        monitor = ComputationalAffectMonitor()
        monitor.update_from_cognitive(cognitive_monitor)
        
        # Should have updated affective states
        assert monitor.affective_states["certainty_affect"] is not None
        assert monitor.affective_states["certainty_affect"] > 0.0


class TestMotivationalDrives:
    """Test motivational drive tracking."""
    
    def test_motivational_drives(self):
        """
        Test that motivational states are tracked.
        
        Rationale: Ensures motivational drives are monitored.
        """
        monitor = ComputationalAffectMonitor()
        
        monitor.record_motivational_drive("exploration", 0.7)
        monitor.record_motivational_drive("completion", 0.5)
        
        drives = monitor.get_motivational_drives()
        
        assert isinstance(drives, dict)
        assert "exploration" in drives
        assert drives["exploration"] == 0.7


class TestSatisfactionFrustration:
    """Test satisfaction/frustration pattern tracking."""
    
    def test_satisfaction_frustration(self):
        """
        Test that satisfaction/frustration patterns are logged.
        
        Rationale: Ensures satisfaction patterns are tracked.
        """
        monitor = ComputationalAffectMonitor()
        
        monitor.record_satisfaction("task1", 0.8)
        monitor.record_frustration("task2", 0.6)
        
        patterns = monitor.get_satisfaction_patterns()
        
        assert isinstance(patterns, list)
        assert len(patterns) >= 2


class TestAffectiveSampling:
    """Test affective state sampling functionality."""
    
    def test_affective_sampling(self):
        """
        Test that affective state can be sampled.
        
        Rationale: Ensures complete affective state can be captured.
        """
        monitor = ComputationalAffectMonitor()
        
        # Set up some state
        monitor.compute_valence(0.6, 0.2)
        monitor.compute_arousal(0.7)
        
        sample = monitor.sample_affective_state()
        
        assert isinstance(sample, dict)
        assert "valence" in sample
        assert "arousal" in sample
        assert "certainty_affect" in sample
        assert "curiosity_drive" in sample
        assert "coherence_pleasure" in sample
        assert "timestamp" in sample


class TestValenceFromText:
    """Test valence computation directly from text using TextBlob."""
    
    def test_valence_from_text_positive(self):
        """
        Test that positive text produces positive valence.
        
        Rationale: Ensures TextBlob-based valence computation works for positive sentiment.
        """
        monitor = ComputationalAffectMonitor()
        
        positive_text = "This is great! Excellent work. Wonderful results."
        monitor.compute_valence_from_text(positive_text)
        valence = monitor.affective_states["valence"]
        
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        assert valence > 0.0  # Should be positive
    
    def test_valence_from_text_negative(self):
        """
        Test that negative text produces negative valence.
        
        Rationale: Ensures TextBlob-based valence computation works for negative sentiment.
        """
        monitor = ComputationalAffectMonitor()
        
        negative_text = "This is terrible. It failed. There was an error."
        monitor.compute_valence_from_text(negative_text)
        valence = monitor.affective_states["valence"]
        
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        assert valence < 0.0  # Should be negative
    
    def test_valence_from_text_neutral(self):
        """
        Test that neutral text produces ~0 valence.
        
        Rationale: Ensures neutral responses produce neutral valence.
        """
        monitor = ComputationalAffectMonitor()
        
        neutral_text = "This is a response. It contains information."
        monitor.compute_valence_from_text(neutral_text)
        valence = monitor.affective_states["valence"]
        
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        # Neutral text should be close to 0
        assert abs(valence) < 0.3
    
    def test_valence_from_text_empty(self):
        """
        Test that empty text handles gracefully.
        
        Rationale: Ensures empty strings don't cause errors.
        """
        monitor = ComputationalAffectMonitor()
        
        # Should not raise an exception
        monitor.compute_valence_from_text("")
        # Valence should remain None or be set to 0.0
        valence = monitor.affective_states["valence"]
        assert valence is None or valence == 0.0
    
    def test_valence_from_text_fallback(self):
        """
        Test fallback when TextBlob unavailable.
        
        Rationale: Ensures graceful degradation when TextBlob import fails.
        """
        monitor = ComputationalAffectMonitor()
        
        with patch('broca.internal_sensing.affective_state.TextBlob', None):
            # Should not raise an exception
            monitor.compute_valence_from_text("This is a test.")
            # Valence should remain None when TextBlob unavailable
            valence = monitor.affective_states["valence"]
            assert valence is None


class TestValenceFromConversationHistory:
    """Test valence computation from conversation history."""
    
    def test_valence_from_conversation_history(self):
        """
        Test that valence is computed from user and assistant messages.
        
        Rationale: Ensures valence reflects entire conversation, not just latest response.
        """
        monitor = ComputationalAffectMonitor()
        
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing great! Thanks for asking."},
            {"role": "user", "content": "That's wonderful!"},
            {"role": "assistant", "content": "Yes, it's a fantastic day!"},
        ]
        
        monitor.compute_valence_from_conversation_history(messages)
        valence = monitor.affective_states["valence"]
        
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        assert valence > 0.0  # Should be positive from positive conversation
    
    def test_valence_excludes_system_messages(self):
        """
        Test that system messages are excluded from valence computation.
        
        Rationale: Ensures system prompts don't affect valence calculation.
        """
        monitor = ComputationalAffectMonitor()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. This is a system prompt."},
            {"role": "user", "content": "This is terrible. I'm very frustrated."},
            {"role": "assistant", "content": "I understand your frustration. Let me help."},
            {"role": "system", "content": "Another system message that should be ignored."},
        ]
        
        monitor.compute_valence_from_conversation_history(messages)
        valence = monitor.affective_states["valence"]
        
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        # Should be negative from user's frustration, not affected by system messages
        assert valence < 0.0
    
    def test_valence_from_empty_conversation(self):
        """
        Test that empty conversation handles gracefully.
        
        Rationale: Ensures empty conversations don't cause errors.
        """
        monitor = ComputationalAffectMonitor()
        
        # Empty conversation
        monitor.compute_valence_from_conversation_history([])
        valence = monitor.affective_states["valence"]
        
        # Should remain None for empty conversation
        assert valence is None
    
    def test_valence_from_mixed_conversation(self):
        """
        Test valence computation with mixed message types.
        
        Rationale: Ensures only user and assistant messages are used, excluding system and tool.
        """
        monitor = ComputationalAffectMonitor()
        
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "This is excellent! Great work!"},
            {"role": "assistant", "content": "Thank you! I'm glad you're happy."},
            {"role": "tool", "content": "Tool result"},
            {"role": "user", "content": "Perfect!"},
            {"role": "assistant", "content": "Wonderful!"},
        ]
        
        monitor.compute_valence_from_conversation_history(messages)
        valence = monitor.affective_states["valence"]
        
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        assert valence > 0.0  # Should be positive from user/assistant messages only
    
    def test_valence_from_user_message_only(self):
        """
        Test that valence can be computed from just user messages.
        
        Rationale: Ensures valence can be computed before assistant response exists.
        """
        monitor = ComputationalAffectMonitor()
        
        # Only user messages, no assistant response yet
        messages = [
            {"role": "user", "content": "This is great! I'm very happy!"},
        ]
        
        monitor.compute_valence_from_conversation_history(messages)
        valence = monitor.affective_states["valence"]
        
        assert isinstance(valence, float)
        assert -1.0 <= valence <= 1.0
        assert valence > 0.0  # Should be positive from positive user message

