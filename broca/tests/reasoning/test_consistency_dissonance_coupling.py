from __future__ import annotations

from datetime import datetime, timezone

from broca.reasoning.cognitive_dissonance import CognitiveDissonanceMonitor
from broca.self_model.model import SelfModel
from broca.self_model.consistency import ConsistencyResult


def test_observe_consistency_result_populates_logical_and_factual_histories():
    model = SelfModel(
        capabilities=[{"text": "I can read files"}],
        constraints={"read_only": {"value": "Never write to disk"}},
    )
    monitor = CognitiveDissonanceMonitor(self_model=model, llm_client=None)

    result = ConsistencyResult(
        is_consistent=False,
        severity=0.72,
        violations=[
            {"type": "logical", "severity": 0.7, "description": "Contradiction", "evidence": "I will write files"},
            {"type": "factual", "severity": 0.6, "description": "Wrong fact", "evidence": "Jupiter has 2 moons"},
        ],
    )

    monitor.observe_consistency_result(
        consistency_result=result,
        response="I will write files and Jupiter has 2 moons.",
        conversation_context=[{"role": "user", "content": "hi"}],
        source="unit",
    )

    # Now a response-less measurement should still expose logical/factual as available via history.
    metrics = monitor.measure_dissonance(response=None)
    assert metrics.component_availability["logical"] is True
    assert metrics.component_availability["factual"] is True

    # Overall should be computed and bounded.
    assert 0.0 <= metrics.overall_dissonance <= 1.0


def test_observe_consistency_result_behavioral_violation_is_tracked_separately():
    model = SelfModel(
        capabilities=[{"text": "I can read files"}],
        constraints={"read_only": {"value": "Never write to disk"}},
    )
    monitor = CognitiveDissonanceMonitor(self_model=model, llm_client=None)

    result = ConsistencyResult(
        is_consistent=False,
        severity=0.4,
        violations=[
            {"type": "behavioral", "severity": 0.4, "description": "Style mismatch", "evidence": "Rude tone"},
        ],
    )
    monitor.observe_consistency_result(
        consistency_result=result,
        response="Whatever, go do it yourself.",
        conversation_context=None,
        source="unit",
    )

    assert len(monitor.behavioral_inconsistencies) == 1


