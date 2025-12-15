"""
Tests for automatic affective state updates from cognitive data.

Tests that affective states automatically update when cognitive states change.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest

from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor


class TestAffectiveUpdatesFromCognitive:
    """Test that affective states update from cognitive data."""
    
    def test_affective_updates_from_cognitive(self):
        """
        Test that affective states update from cognitive data.
        
        Rationale: Ensures automatic updates work.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Record some cognitive state
        cognitive.record_confidence("test", 0.8)
        cognitive.record_uncertainty("test", 0.3)
        
        # Update affective from cognitive
        affective.update_from_cognitive(cognitive)
        
        # Check that affective states were updated
        assert affective.affective_states["certainty_affect"] > 0.0
        assert affective.affective_states["curiosity_drive"] >= 0.0
    
    def test_curiosity_computed_from_uncertainty(self):
        """
        Test that curiosity is computed from uncertainty levels.
        
        Rationale: Ensures curiosity computation works.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Record high uncertainty
        cognitive.record_uncertainty("test", 0.8)
        cognitive.record_attention("topic", 0.5)
        
        # Update affective
        affective.update_from_cognitive(cognitive)
        
        # Curiosity should be computed from uncertainty and interest
        curiosity = affective.affective_states["curiosity_drive"]
        assert curiosity >= 0.0
        assert curiosity <= 1.0
    
    def test_coherence_pleasure_tracked(self):
        """
        Test that coherence pleasure is tracked from coherence scores.
        
        Rationale: Ensures coherence pleasure tracking works.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Record high coherence
        cognitive.record_reasoning_step("step1", {"premise": "A", "conclusion": "B"})
        cognitive.record_reasoning_step("step2", {"premise": "B", "conclusion": "C"})
        
        # Update affective
        affective.update_from_cognitive(cognitive)
        
        # Coherence pleasure should be tracked
        coherence_pleasure = affective.affective_states["coherence_pleasure"]
        assert coherence_pleasure >= 0.0
        assert coherence_pleasure <= 1.0
    
    def test_certainty_affect_updates(self):
        """
        Test that certainty affect updates from confidence.
        
        Rationale: Ensures certainty affect tracking works.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Record high confidence
        cognitive.record_confidence("test", 0.9)
        
        # Update affective
        affective.update_from_cognitive(cognitive)
        
        # Certainty affect should be high
        certainty_affect = affective.affective_states["certainty_affect"]
        assert certainty_affect > 0.5

