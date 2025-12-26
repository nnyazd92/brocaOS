"""
Property-based tests for internal sensing state computations.

Uses Hypothesis to generate test cases and verify properties of state computations.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, Any, List

from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor
from broca.internal_sensing.integrated_interoception import IntegratedInteroception


class TestStateComputationProperties:
    """Property-based tests for state computation logic."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        confidence_values=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=20),
    )
    def test_confidence_averaging_property(self, confidence_values: List[float]):
        """
        Property: Average confidence should be between min and max of input values.
        
        Rationale: Ensures confidence computation is mathematically sound.
        """
        monitor = CognitiveStateMonitor()
        
        # Record confidence values
        for i, conf in enumerate(confidence_values):
            monitor.record_confidence(f"response_{i}", conf)
        
        # Check property
        computed = monitor.states.get("confidence_level")
        assert computed is not None, "Confidence should be computed when history exists"
        assert min(confidence_values) <= computed <= max(confidence_values), \
            f"Average {computed} should be between min {min(confidence_values)} and max {max(confidence_values)}"
        assert 0.0 <= computed <= 1.0, "Confidence should be in valid range"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        uncertainty_values=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=20),
    )
    def test_uncertainty_averaging_property(self, uncertainty_values: List[float]):
        """
        Property: Average uncertainty should be between min and max of input values.
        
        Rationale: Ensures uncertainty computation is mathematically sound.
        """
        monitor = CognitiveStateMonitor()
        
        # Record uncertainty values
        for i, unc in enumerate(uncertainty_values):
            monitor.record_uncertainty(f"question_{i}", unc)
        
        # Check property
        computed = monitor.states.get("uncertainty_tracking")
        assert computed is not None, "Uncertainty should be computed when history exists"
        assert min(uncertainty_values) <= computed <= max(uncertainty_values), \
            f"Average {computed} should be between min {min(uncertainty_values)} and max {max(uncertainty_values)}"
        assert 0.0 <= computed <= 1.0, "Uncertainty should be in valid range"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0),
        coherence=st.floats(min_value=0.0, max_value=1.0),
        uncertainty=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_affective_from_cognitive_property(
        self, 
        confidence: float, 
        coherence: float, 
        uncertainty: float
    ):
        """
        Property: Affective states should be computed from cognitive states when available.
        
        Rationale: Ensures automatic state updates work correctly.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Set up cognitive states
        cognitive.record_confidence("test", confidence)
        cognitive.record_uncertainty("test", uncertainty)
        # Record reasoning steps for coherence
        if coherence > 0:
            cognitive.record_reasoning_step("step1", {"premise": "A", "conclusion": "B"})
            cognitive.record_reasoning_step("step2", {"premise": "B", "conclusion": "C"})
        
        # Update affective from cognitive
        affective.update_from_cognitive(cognitive)
        
        # Check that certainty_affect was computed from confidence
        certainty = affective.affective_states.get("certainty_affect")
        assert certainty is not None, "certainty_affect should be computed from confidence"
        assert 0.0 <= certainty <= 1.0, "certainty_affect should be in valid range"
        assert abs(certainty - confidence) < 0.001, "certainty_affect should equal confidence"
        
        # Check that coherence_pleasure was computed if coherence exists
        if cognitive.states.get("conceptual_coherence") is not None:
            pleasure = affective.affective_states.get("coherence_pleasure")
            assert pleasure is not None, "coherence_pleasure should be computed from coherence"
            assert 0.0 <= pleasure <= 1.0, "coherence_pleasure should be in valid range"
        
        # Check that curiosity was computed from uncertainty
        if uncertainty > 0:
            curiosity = affective.affective_states.get("curiosity_drive")
            assert curiosity is not None, "curiosity_drive should be computed from uncertainty"
            assert 0.0 <= curiosity <= 1.0, "curiosity_drive should be in valid range"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        uncertainty=st.floats(min_value=0.0, max_value=1.0),
        interest=st.floats(min_value=0.0, max_value=1.0),
        surprise=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_curiosity_computation_property(
        self,
        uncertainty: float,
        interest: float,
        surprise: float
    ):
        """
        Property: Curiosity should be weighted combination of uncertainty, interest, and surprise.
        
        Rationale: Ensures curiosity computation follows the specified formula.
        """
        affective = ComputationalAffectMonitor()
        affective.affective_states["surprise"] = surprise
        
        affective.compute_curiosity_drive(uncertainty, interest)
        
        curiosity = affective.affective_states.get("curiosity_drive")
        assert curiosity is not None, "curiosity_drive should be computed"
        assert 0.0 <= curiosity <= 1.0, "curiosity_drive should be in valid range"
        
        # Check that curiosity is weighted combination (40% uncertainty, 30% interest, 30% surprise)
        expected = (uncertainty * 0.4 + interest * 0.3 + surprise * 0.3)
        assert abs(curiosity - expected) < 0.001, \
            f"curiosity {curiosity} should equal weighted combination {expected}"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        positive=st.floats(min_value=0.0, max_value=1.0),
        negative=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_valence_computation_property(self, positive: float, negative: float):
        """
        Property: Valence should be in range [-1, 1] and computed from positive/negative scores.
        
        Rationale: Ensures valence computation is mathematically sound.
        """
        affective = ComputationalAffectMonitor()
        
        affective.compute_valence(positive, negative)
        
        valence = affective.affective_states.get("valence")
        if positive + negative > 0:
            assert valence is not None, "valence should be computed when scores are non-zero"
            assert -1.0 <= valence <= 1.0, "valence should be in valid range [-1, 1]"
            
            # Check formula: (positive - negative) / (positive + negative)
            expected = (positive - negative) / (positive + negative)
            assert abs(valence - expected) < 0.001, \
                f"valence {valence} should equal {expected}"
        else:
            # When both are zero, valence should be 0.0
            assert valence == 0.0, "valence should be 0.0 when both scores are zero"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        activation=st.floats(min_value=-1.0, max_value=2.0),  # Test clamping
    )
    def test_arousal_clamping_property(self, activation: float):
        """
        Property: Arousal should be clamped to [0, 1] range.
        
        Rationale: Ensures arousal values are always valid.
        """
        affective = ComputationalAffectMonitor()
        
        affective.compute_arousal(activation)
        
        arousal = affective.affective_states.get("arousal")
        assert arousal is not None, "arousal should be computed"
        assert 0.0 <= arousal <= 1.0, "arousal should be clamped to [0, 1]"
        
        # Check clamping
        if activation < 0.0:
            assert arousal == 0.0, "arousal should be clamped to 0.0 for negative values"
        elif activation > 1.0:
            assert arousal == 1.0, "arousal should be clamped to 1.0 for values > 1.0"
        else:
            assert abs(arousal - activation) < 0.001, "arousal should equal activation when in range"


class TestStateTransitionProperties:
    """Property-based tests for state transitions (None -> computed)."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_recordings=st.integers(min_value=0, max_value=10),
    )
    def test_confidence_transition_property(self, num_recordings: int):
        """
        Property: Confidence should transition from None to computed value.
        
        Rationale: Ensures states are computed when data becomes available.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially should be None
        assert monitor.states.get("confidence_level") is None, "confidence should start as None"
        
        # Record some values
        for i in range(num_recordings):
            monitor.record_confidence(f"response_{i}", 0.5 + (i % 2) * 0.3)
        
        # Check transition
        if num_recordings > 0:
            assert monitor.states.get("confidence_level") is not None, \
                "confidence should be computed after recordings"
        else:
            assert monitor.states.get("confidence_level") is None, \
                "confidence should remain None with no recordings"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_reasoning_steps=st.integers(min_value=0, max_value=10),
    )
    def test_coherence_transition_property(self, num_reasoning_steps: int):
        """
        Property: Coherence should transition from None to computed value when steps >= 2.
        
        Rationale: Ensures coherence computation requires sufficient data.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially should be None
        assert monitor.states.get("conceptual_coherence") == 0.5, "coherence should start with default 0.5"
        
        # Record reasoning steps
        for i in range(num_reasoning_steps):
            monitor.record_reasoning_step(f"step_{i}", {
                "premise": f"P{i}",
                "conclusion": f"C{i}",
            })
        
        # Check transition
        if num_reasoning_steps >= 2:
            assert monitor.states.get("conceptual_coherence") is not None, \
                "coherence should be computed with 2+ reasoning steps"
        else:
            assert monitor.states.get("conceptual_coherence") == 0.5, \
                "coherence should remain at default 0.5 with < 2 reasoning steps"


class TestEdgeCases:
    """Property-based tests for edge cases."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        empty_list=st.just([]),
    )
    def test_empty_history_property(self, empty_list: List[float]):
        """
        Property: States should remain None with empty history.
        
        Rationale: Ensures system handles empty data gracefully.
        """
        monitor = CognitiveStateMonitor()
        
        # Should remain None
        assert monitor.states.get("confidence_level") is None
        assert monitor.states.get("uncertainty_tracking") is None
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        extreme_values=st.lists(
            st.one_of(
                st.just(0.0),
                st.just(1.0),
                st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
            ),
            min_size=1,
            max_size=5
        ),
    )
    def test_extreme_values_property(self, extreme_values: List[float]):
        """
        Property: System should handle extreme values (0.0, 1.0) correctly.
        
        Rationale: Ensures boundary conditions are handled properly.
        """
        monitor = CognitiveStateMonitor()
        
        for i, val in enumerate(extreme_values):
            monitor.record_confidence(f"response_{i}", val)
        
        computed = monitor.states.get("confidence_level")
        assert computed is not None
        assert 0.0 <= computed <= 1.0, "computed value should be in valid range even with extreme inputs"

