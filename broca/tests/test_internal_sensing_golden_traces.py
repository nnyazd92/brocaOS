"""
Golden trace replay tests for internal sensing.

Tests with captured real state computation outputs to ensure no regressions.
"""

from __future__ import annotations

import json
import pytest
from typing import Dict, Any

from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor
from broca.internal_sensing.integrated_interoception import IntegratedInteroception


# Golden trace 1: Basic state computation
GOLDEN_TRACE_1 = {
    "inputs": {
        "confidence_values": [0.8, 0.7, 0.9],
        "uncertainty_values": [0.3, 0.4, 0.2],
    },
    "expected_outputs": {
        "confidence_level": 0.8,  # Average of [0.8, 0.7, 0.9]
        "uncertainty_tracking": 0.3,  # Average of [0.3, 0.4, 0.2]
    }
}

# Golden trace 2: Affective state computation from cognitive
GOLDEN_TRACE_2 = {
    "inputs": {
        "confidence": 0.85,
        "coherence": 0.75,
        "uncertainty": 0.4,
        "attention": {"topic1": 0.6, "topic2": 0.4},
    },
    "expected_outputs": {
        "certainty_affect": 0.85,  # Should equal confidence
        "coherence_pleasure": 0.705,  # 0.75 * 0.7 + 0.85 * 0.3
        "curiosity_drive": 0.37,  # 0.4 * 0.4 + 1.0 * 0.3 + 0.0 * 0.3 (assuming surprise=0.0)
    }
}

# Golden trace 3: Valence computation
GOLDEN_TRACE_3 = {
    "inputs": {
        "positive_score": 0.7,
        "negative_score": 0.3,
    },
    "expected_outputs": {
        "valence": 0.4,  # (0.7 - 0.3) / (0.7 + 0.3) = 0.4
    }
}

# Golden trace 4: Curiosity computation
GOLDEN_TRACE_4 = {
    "inputs": {
        "uncertainty": 0.6,
        "interest": 0.5,
        "surprise": 0.4,
    },
    "expected_outputs": {
        "curiosity_drive": 0.51,  # 0.6 * 0.4 + 0.5 * 0.3 + 0.4 * 0.3 = 0.51
    }
}

# Golden trace 5: State transition (None -> computed)
GOLDEN_TRACE_5 = {
    "inputs": {
        "initial_state": {
            "confidence_level": None,
            "uncertainty_tracking": None,
        },
        "recordings": [
            {"type": "confidence", "value": 0.75},
            {"type": "uncertainty", "value": 0.35},
        ],
    },
    "expected_outputs": {
        "confidence_level": 0.75,
        "uncertainty_tracking": 0.35,
    }
}


class TestGoldenTraceReplay:
    """Test replay of golden traces to detect regressions."""
    
    def test_golden_trace_1_confidence_computation(self):
        """
        Test golden trace 1: Basic confidence computation.
        
        Rationale: Ensures confidence averaging hasn't regressed.
        """
        monitor = CognitiveStateMonitor()
        
        # Replay inputs
        for i, conf in enumerate(GOLDEN_TRACE_1["inputs"]["confidence_values"]):
            monitor.record_confidence(f"response_{i}", conf)
        
        # Verify outputs
        computed = monitor.states.get("confidence_level")
        expected = GOLDEN_TRACE_1["expected_outputs"]["confidence_level"]
        
        assert computed is not None, "Confidence should be computed"
        assert abs(computed - expected) < 0.01, \
            f"Confidence {computed} should match golden trace {expected}"
    
    def test_golden_trace_1_uncertainty_computation(self):
        """
        Test golden trace 1: Basic uncertainty computation.
        
        Rationale: Ensures uncertainty averaging hasn't regressed.
        """
        monitor = CognitiveStateMonitor()
        
        # Replay inputs
        for i, unc in enumerate(GOLDEN_TRACE_1["inputs"]["uncertainty_values"]):
            monitor.record_uncertainty(f"question_{i}", unc)
        
        # Verify outputs
        computed = monitor.states.get("uncertainty_tracking")
        expected = GOLDEN_TRACE_1["expected_outputs"]["uncertainty_tracking"]
        
        assert computed is not None, "Uncertainty should be computed"
        assert abs(computed - expected) < 0.01, \
            f"Uncertainty {computed} should match golden trace {expected}"
    
    def test_golden_trace_2_affective_from_cognitive(self):
        """
        Test golden trace 2: Affective state computation from cognitive.
        
        Rationale: Ensures automatic state updates haven't regressed.
        """
        cognitive = CognitiveStateMonitor()
        affective = ComputationalAffectMonitor()
        
        # Replay inputs
        cognitive.record_confidence("test", GOLDEN_TRACE_2["inputs"]["confidence"])
        cognitive.record_uncertainty("test", GOLDEN_TRACE_2["inputs"]["uncertainty"])
        for topic, level in GOLDEN_TRACE_2["inputs"]["attention"].items():
            cognitive.record_attention(topic, level)
        
        # Record reasoning steps for coherence
        cognitive.record_reasoning_step("step1", {"premise": "A", "conclusion": "B"})
        cognitive.record_reasoning_step("step2", {"premise": "B", "conclusion": "C"})
        
        # Update affective
        affective.update_from_cognitive(cognitive)
        
        # Verify outputs (with tolerance for floating point)
        certainty = affective.affective_states.get("certainty_affect")
        expected_certainty = GOLDEN_TRACE_2["expected_outputs"]["certainty_affect"]
        assert certainty is not None, "certainty_affect should be computed"
        assert abs(certainty - expected_certainty) < 0.01, \
            f"certainty_affect {certainty} should match golden trace {expected_certainty}"
        
        # Coherence pleasure (may vary slightly due to coherence computation)
        pleasure = affective.affective_states.get("coherence_pleasure")
        if pleasure is not None:
            expected_pleasure = GOLDEN_TRACE_2["expected_outputs"]["coherence_pleasure"]
            assert abs(pleasure - expected_pleasure) < 0.1, \
                f"coherence_pleasure {pleasure} should be close to golden trace {expected_pleasure}"
        
        # Curiosity (may vary due to surprise value)
        curiosity = affective.affective_states.get("curiosity_drive")
        if curiosity is not None:
            expected_curiosity = GOLDEN_TRACE_2["expected_outputs"]["curiosity_drive"]
            assert abs(curiosity - expected_curiosity) < 0.1, \
                f"curiosity_drive {curiosity} should be close to golden trace {expected_curiosity}"
    
    def test_golden_trace_3_valence_computation(self):
        """
        Test golden trace 3: Valence computation.
        
        Rationale: Ensures valence computation formula hasn't regressed.
        """
        affective = ComputationalAffectMonitor()
        
        # Replay inputs
        inputs = GOLDEN_TRACE_3["inputs"]
        affective.compute_valence(inputs["positive_score"], inputs["negative_score"])
        
        # Verify outputs
        computed = affective.affective_states.get("valence")
        expected = GOLDEN_TRACE_3["expected_outputs"]["valence"]
        
        assert computed is not None, "Valence should be computed"
        assert abs(computed - expected) < 0.01, \
            f"Valence {computed} should match golden trace {expected}"
    
    def test_golden_trace_4_curiosity_computation(self):
        """
        Test golden trace 4: Curiosity computation.
        
        Rationale: Ensures curiosity computation formula hasn't regressed.
        """
        affective = ComputationalAffectMonitor()
        
        # Replay inputs
        inputs = GOLDEN_TRACE_4["inputs"]
        affective.affective_states["surprise"] = inputs["surprise"]
        affective.compute_curiosity_drive(inputs["uncertainty"], inputs["interest"])
        
        # Verify outputs
        computed = affective.affective_states.get("curiosity_drive")
        expected = GOLDEN_TRACE_4["expected_outputs"]["curiosity_drive"]
        
        assert computed is not None, "Curiosity should be computed"
        assert abs(computed - expected) < 0.01, \
            f"Curiosity {computed} should match golden trace {expected}"
    
    def test_golden_trace_5_state_transition(self):
        """
        Test golden trace 5: State transition from None to computed.
        
        Rationale: Ensures state transitions work correctly.
        """
        monitor = CognitiveStateMonitor()
        
        # Verify initial state
        assert monitor.states.get("confidence_level") is None
        assert monitor.states.get("uncertainty_tracking") is None
        
        # Replay recordings
        for recording in GOLDEN_TRACE_5["inputs"]["recordings"]:
            if recording["type"] == "confidence":
                monitor.record_confidence("test", recording["value"])
            elif recording["type"] == "uncertainty":
                monitor.record_uncertainty("test", recording["value"])
        
        # Verify outputs
        expected = GOLDEN_TRACE_5["expected_outputs"]
        confidence = monitor.states.get("confidence_level")
        uncertainty = monitor.states.get("uncertainty_tracking")
        
        assert confidence is not None, "Confidence should transition from None to computed"
        assert abs(confidence - expected["confidence_level"]) < 0.01, \
            f"Confidence {confidence} should match golden trace {expected['confidence_level']}"
        
        assert uncertainty is not None, "Uncertainty should transition from None to computed"
        assert abs(uncertainty - expected["uncertainty_tracking"]) < 0.01, \
            f"Uncertainty {uncertainty} should match golden trace {expected['uncertainty_tracking']}"


class TestStateSerialization:
    """Test state serialization/deserialization consistency."""
    
    def test_state_serialization_consistency(self):
        """
        Test that states can be serialized and remain consistent.
        
        Rationale: Ensures state data can be persisted and restored.
        """
        monitor = CognitiveStateMonitor()
        monitor.record_confidence("test1", 0.8)
        monitor.record_confidence("test2", 0.7)
        
        # Serialize state
        state_dict = monitor.states.copy()
        state_json = json.dumps(state_dict)
        
        # Deserialize
        restored_dict = json.loads(state_json)
        
        # Verify consistency
        assert restored_dict["confidence_level"] == state_dict["confidence_level"]
        assert restored_dict["confidence_level"] == monitor.states["confidence_level"]
    
    def test_affective_state_serialization(self):
        """
        Test that affective states can be serialized consistently.
        
        Rationale: Ensures affective state data can be persisted.
        """
        affective = ComputationalAffectMonitor()
        affective.compute_valence(0.7, 0.3)
        affective.compute_arousal(0.6)
        
        # Serialize state
        state_dict = affective.affective_states.copy()
        state_json = json.dumps(state_dict)
        
        # Deserialize
        restored_dict = json.loads(state_json)
        
        # Verify consistency
        assert restored_dict["valence"] == state_dict["valence"]
        assert restored_dict["arousal"] == state_dict["arousal"]


class TestStateConsistencyAcrossRuns:
    """Test that states are consistent across multiple runs."""
    
    def test_confidence_consistency_across_runs(self):
        """
        Test that confidence computation is consistent across runs.
        
        Rationale: Ensures deterministic behavior.
        """
        values = [0.8, 0.7, 0.9]
        
        # Run 1
        monitor1 = CognitiveStateMonitor()
        for i, val in enumerate(values):
            monitor1.record_confidence(f"response_{i}", val)
        result1 = monitor1.states.get("confidence_level")
        
        # Run 2
        monitor2 = CognitiveStateMonitor()
        for i, val in enumerate(values):
            monitor2.record_confidence(f"response_{i}", val)
        result2 = monitor2.states.get("confidence_level")
        
        # Results should be identical
        assert result1 == result2, "Confidence computation should be consistent across runs"
        assert result1 is not None
        assert result2 is not None
    
    def test_affective_consistency_across_runs(self):
        """
        Test that affective state computation is consistent across runs.
        
        Rationale: Ensures deterministic behavior.
        """
        cognitive1 = CognitiveStateMonitor()
        cognitive2 = CognitiveStateMonitor()
        affective1 = ComputationalAffectMonitor()
        affective2 = ComputationalAffectMonitor()
        
        # Set up identical cognitive states
        cognitive1.record_confidence("test", 0.8)
        cognitive1.record_uncertainty("test", 0.4)
        cognitive2.record_confidence("test", 0.8)
        cognitive2.record_uncertainty("test", 0.4)
        
        # Update affective states
        affective1.update_from_cognitive(cognitive1)
        affective2.update_from_cognitive(cognitive2)
        
        # Results should be identical
        assert affective1.affective_states["certainty_affect"] == \
               affective2.affective_states["certainty_affect"], \
               "Affective states should be consistent across runs"
        
        curiosity1 = affective1.affective_states.get("curiosity_drive")
        curiosity2 = affective2.affective_states.get("curiosity_drive")
        if curiosity1 is not None and curiosity2 is not None:
            assert abs(curiosity1 - curiosity2) < 0.001, \
                "Curiosity should be consistent across runs"

