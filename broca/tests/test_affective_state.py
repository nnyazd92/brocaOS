"""
Tests for ComputationalAffectMonitor.

Tests affective state tracking including valence, arousal, curiosity, and satisfaction.
"""

from __future__ import annotations

from unittest.mock import Mock
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

