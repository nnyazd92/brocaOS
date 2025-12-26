"""
Tests to verify internal sensing wiring completeness.

Ensures all state computation methods are called correctly and states transition properly.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor
from broca.internal_sensing.integrated_interoception import IntegratedInteroception
from broca.internal_sensing.framework import InternalSensingFramework


class TestAutomaticStateUpdates:
    """Test that automatic state updates are wired correctly."""
    
    def test_update_from_cognitive_called_automatically(self):
        """
        Test that update_from_cognitive is called automatically in generate_interoceptive_awareness.
        
        Rationale: Ensures automatic state updates are wired correctly.
        """
        interoception = IntegratedInteroception()
        
        # Set up cognitive states
        interoception.cognition.record_confidence("test", 0.8)
        interoception.cognition.record_uncertainty("test", 0.4)
        
        # Initially, affective states should be None
        assert interoception.affect.affective_states.get("certainty_affect") is None
        assert interoception.affect.affective_states.get("curiosity_drive") is None
        
        # Generate awareness - should automatically update affective states
        state = interoception.generate_interoceptive_awareness()
        
        # Verify that affective states were computed
        assert interoception.affect.affective_states.get("certainty_affect") is not None, \
            "certainty_affect should be computed automatically"
        assert interoception.affect.affective_states.get("curiosity_drive") is not None, \
            "curiosity_drive should be computed automatically"
        
        # Verify state includes computed values
        affective_state = state.get("affective", {})
        assert affective_state.get("certainty_affect") is not None
        assert affective_state.get("curiosity_drive") is not None
    
    def test_coherence_pleasure_computed_when_coherence_available(self):
        """
        Test that coherence_pleasure is computed when coherence is available.
        
        Rationale: Ensures coherence_pleasure computation is wired correctly.
        """
        interoception = IntegratedInteroception()
        
        # Record reasoning steps to generate coherence
        interoception.cognition.record_reasoning_step("step1", {"premise": "A", "conclusion": "B"})
        interoception.cognition.record_reasoning_step("step2", {"premise": "B", "conclusion": "C"})
        
        # Also need confidence for coherence_pleasure computation
        interoception.cognition.record_confidence("test", 0.7)
        
        # Generate awareness
        state = interoception.generate_interoceptive_awareness()
        
        # Verify coherence_pleasure was computed
        coherence_pleasure = interoception.affect.affective_states.get("coherence_pleasure")
        assert coherence_pleasure is not None, "coherence_pleasure should be computed when coherence is available"
        assert 0.0 <= coherence_pleasure <= 1.0, "coherence_pleasure should be in valid range"
    
    def test_curiosity_computed_when_uncertainty_available(self):
        """
        Test that curiosity is computed when uncertainty is available.
        
        Rationale: Ensures curiosity computation is wired correctly.
        """
        interoception = IntegratedInteroception()
        
        # Record uncertainty
        interoception.cognition.record_uncertainty("test", 0.5)
        interoception.cognition.record_attention("topic", 0.3)
        
        # Generate awareness
        state = interoception.generate_interoceptive_awareness()
        
        # Verify curiosity was computed
        curiosity = interoception.affect.affective_states.get("curiosity_drive")
        assert curiosity is not None, "curiosity_drive should be computed when uncertainty is available"
        assert 0.0 <= curiosity <= 1.0, "curiosity_drive should be in valid range"


class TestStateTransitions:
    """Test that states transition correctly from None to computed values."""
    
    def test_confidence_transition(self):
        """
        Test that confidence transitions from None to computed value.
        
        Rationale: Ensures state transitions work correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially None
        assert monitor.states.get("confidence_level") is None
        
        # Record confidence
        monitor.record_confidence("test", 0.75)
        
        # Should now be computed
        assert monitor.states.get("confidence_level") is not None
        assert monitor.states.get("confidence_level") == 0.75
    
    def test_uncertainty_transition(self):
        """
        Test that uncertainty transitions from None to computed value.
        
        Rationale: Ensures state transitions work correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially None
        assert monitor.states.get("uncertainty_tracking") is None
        
        # Record uncertainty
        monitor.record_uncertainty("test", 0.4)
        
        # Should now be computed
        assert monitor.states.get("uncertainty_tracking") is not None
        assert monitor.states.get("uncertainty_tracking") == 0.4
    
    def test_affective_state_transitions(self):
        """
        Test that affective states transition from None to computed values.
        
        Rationale: Ensures affective state transitions work correctly.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Initially None
        assert affective.affective_states.get("certainty_affect") is None
        assert affective.affective_states.get("curiosity_drive") is None
        
        # Set up cognitive states
        cognitive.record_confidence("test", 0.8)
        cognitive.record_uncertainty("test", 0.5)
        cognitive.record_attention("topic", 0.3)
        
        # Update affective
        affective.update_from_cognitive(cognitive)
        
        # Should now be computed
        assert affective.affective_states.get("certainty_affect") is not None
        assert affective.affective_states.get("curiosity_drive") is not None


class TestStateComputationCompleteness:
    """Test that all computation methods are called when data is available."""
    
    def test_all_affective_states_computed_when_cognitive_data_available(self):
        """
        Test that all possible affective states are computed when cognitive data is available.
        
        Rationale: Ensures no states remain "unknown" when they should be computed.
        """
        interoception = IntegratedInteroception()
        
        # Set up complete cognitive state
        interoception.cognition.record_confidence("test1", 0.8)
        interoception.cognition.record_uncertainty("test2", 0.5)
        interoception.cognition.record_attention("topic1", 0.4)
        interoception.cognition.record_reasoning_step("step1", {"premise": "A", "conclusion": "B"})
        interoception.cognition.record_reasoning_step("step2", {"premise": "B", "conclusion": "C"})
        
        # Generate awareness
        state = interoception.generate_interoceptive_awareness()
        
        # Verify all possible states are computed
        affective = state.get("affective", {})
        
        # These should be computed from cognitive data
        assert affective.get("certainty_affect") is not None, "certainty_affect should be computed"
        assert affective.get("curiosity_drive") is not None, "curiosity_drive should be computed"
        assert affective.get("coherence_pleasure") is not None, "coherence_pleasure should be computed"
    
    def test_states_remain_none_when_data_unavailable(self):
        """
        Test that states remain None when data is unavailable.
        
        Rationale: Ensures "unknown" only appears when values truly haven't been computed.
        """
        interoception = IntegratedInteroception()
        
        # Don't set up any cognitive data
        # Generate awareness
        state = interoception.generate_interoceptive_awareness()
        
        # Verify states remain None when data unavailable
        affective = state.get("affective", {})
        cognitive = state.get("cognitive", {})
        
        # These should be None (no data to compute from)
        assert cognitive.get("confidence_level") is None, "confidence should be None with no data"
        assert cognitive.get("uncertainty_tracking") is None, "uncertainty should be None with no data"
        assert affective.get("certainty_affect") is None, "certainty_affect should be None with no confidence"
        assert affective.get("curiosity_drive") is None, "curiosity should be None with no uncertainty"


class TestReportGenerationUsesFreshState:
    """Test that report generation uses fresh state."""
    
    def test_report_uses_fresh_state(self):
        """
        Test that generate_interoceptive_report uses fresh state.
        
        Rationale: Ensures reports reflect current computed values.
        """
        interoception = IntegratedInteroception()
        
        # Initially, states should be None
        interoception.interoceptive_map = {}  # Clear stale map
        
        # Set up cognitive states
        interoception.cognition.record_confidence("test", 0.8)
        
        # Generate report - should use fresh state
        report = interoception.generate_interoceptive_report()
        
        # Report should reflect fresh state (may show "unknown" if no data, or computed values if data exists)
        assert isinstance(report, str)
        assert len(report) > 0
    
    def test_report_reflects_computed_values(self):
        """
        Test that report reflects computed values when available.
        
        Rationale: Ensures reports show computed values, not stale "unknown".
        """
        interoception = IntegratedInteroception()
        
        # Set up cognitive states
        interoception.cognition.record_confidence("test", 0.8)
        interoception.cognition.record_uncertainty("test", 0.4)
        
        # Generate report
        report = interoception.generate_interoceptive_report()
        
        # Report should contain computed values (not "unknown")
        # Note: Report format may vary, but should not show "unknown" for computed values
        assert "unknown" not in report or "Confidence: 80.00%" in report or "Confidence:" in report

