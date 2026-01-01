"""
Unit tests to ensure dissonance-to-emotion mapping avoids repeated mapper construction.
"""

from __future__ import annotations

from unittest.mock import Mock

from broca.internal_sensing.affective_state import ComputationalAffectMonitor


def test_dissonance_mapper_is_cached(monkeypatch):
    created = {"count": 0}

    class FakeMapper:
        def __init__(self, *args, **kwargs):
            created["count"] += 1

        def map_to_emotion(self, metrics, appraisal):
            return Mock(valence_delta=0.0, arousal_delta=0.0, curiosity_delta=0.0, surprise_delta=0.0)

    monkeypatch.setattr("broca.internal_sensing.emotional_appraisal.DissonanceEmotionalMapper", FakeMapper)

    monitor = ComputationalAffectMonitor()
    monitor._emotional_appraisal_engine = Mock()
    monitor._emotional_appraisal_engine.appraise_dissonance.return_value = Mock(
        goal_congruence=0.0, coping_potential=0.5, agency=0.5, goal_relevance=0.5, novelty=0.0
    )

    # Minimal metrics dict is accepted and converted.
    dm = {"logical_dissonance": 0.0, "factual_dissonance": 0.0, "behavioral_dissonance": 0.0, "goal_dissonance": 0.0, "overall_dissonance": 0.0}
    monitor.update_from_dissonance(dm, current_goals=[], coping_resources={})
    monitor.update_from_dissonance(dm, current_goals=[], coping_resources={})

    assert created["count"] == 1
