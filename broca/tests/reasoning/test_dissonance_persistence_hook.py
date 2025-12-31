from __future__ import annotations

from broca.reasoning.cognitive_dissonance import CognitiveDissonanceMonitor
from broca.self_model.model import SelfModel
from broca.self_model.consistency import ConsistencyResult


def test_dissonance_monitor_calls_persistence_hook_on_updates():
    model = SelfModel(
        capabilities=[{"text": "I can read files"}],
        constraints={"read_only": {"value": "Never write to disk"}},
    )
    monitor = CognitiveDissonanceMonitor(self_model=model, llm_client=None)

    calls = {"n": 0}

    def hook():
        calls["n"] += 1

    monitor.set_persistence_hook(hook, min_interval_seconds=0.0)

    # observe_consistency_result should trigger hook
    result = ConsistencyResult(
        is_consistent=False,
        severity=0.72,
        violations=[
            {"type": "logical", "severity": 0.7, "description": "Contradiction", "evidence": "I will write files"},
        ],
    )
    monitor.observe_consistency_result(consistency_result=result, response="I will write files.", conversation_context=None, source="unit")

    # measure_dissonance should trigger hook
    monitor.measure_dissonance(response=None)

    assert calls["n"] >= 2

