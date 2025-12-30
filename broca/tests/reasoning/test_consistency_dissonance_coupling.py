from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

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


def test_violations_persist_across_reboot_and_restore_component_availability():
    """
    Test that consistency violations persist across reboots and correctly restore
    component_availability when measured without a response.
    
    This is the key test for the issue where component_availability was False
    after reboot because violation histories were not being populated.
    """
    from broca.reasoning.state_manager import ReasoningStateManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "reasoning_state.json"
        
        # === Phase 1: Create monitor, observe violations, save state ===
        model = SelfModel(
            capabilities=[{"text": "I can read files"}],
            constraints={"read_only": {"value": "Never write to disk"}},
        )
        monitor1 = CognitiveDissonanceMonitor(self_model=model, llm_client=None)
        state_manager1 = ReasoningStateManager(state_file_path=state_file)
        
        # Observe a logical and factual violation
        result = ConsistencyResult(
            is_consistent=False,
            severity=0.7,
            violations=[
                {"type": "logical", "severity": 0.7, "description": "Contradiction", "evidence": "contradicts"},
                {"type": "factual", "severity": 0.6, "description": "Wrong fact", "evidence": "wrong"},
            ],
        )
        monitor1.observe_consistency_result(
            consistency_result=result,
            response="This response has violations.",
            conversation_context=[{"role": "user", "content": "test"}],
            source="test_persistence",
        )
        
        # Verify violations were recorded
        assert len(monitor1.logical_violations) == 1
        assert len(monitor1.factual_errors) == 1
        
        # Measure dissonance (with response=None to simulate daemon tick)
        metrics1 = monitor1.measure_dissonance(response=None)
        assert metrics1.component_availability["logical"] is True, "Logical should be available from history"
        assert metrics1.component_availability["factual"] is True, "Factual should be available from history"
        
        # Save state
        state_manager1.save_state(dissonance_monitor=monitor1, force=True)
        
        # === Phase 2: Simulate reboot - create new monitor, load state ===
        model2 = SelfModel(
            capabilities=[{"text": "I can read files"}],
            constraints={"read_only": {"value": "Never write to disk"}},
        )
        monitor2 = CognitiveDissonanceMonitor(self_model=model2, llm_client=None)
        state_manager2 = ReasoningStateManager(state_file_path=state_file)
        
        # Initially, new monitor should have empty histories
        assert len(monitor2.logical_violations) == 0
        assert len(monitor2.factual_errors) == 0
        
        # Load state from file
        state_manager2.load_state(dissonance_monitor=monitor2)
        
        # Verify violations were restored
        assert len(monitor2.logical_violations) == 1, "Logical violations should be restored"
        assert len(monitor2.factual_errors) == 1, "Factual errors should be restored"
        
        # Measure dissonance WITHOUT response (simulating daemon tick after reboot)
        metrics2 = monitor2.measure_dissonance(response=None)
        
        # KEY ASSERTION: component_availability should be True from restored history
        assert metrics2.component_availability["logical"] is True, (
            "Logical should be available from restored history after reboot"
        )
        assert metrics2.component_availability["factual"] is True, (
            "Factual should be available from restored history after reboot"
        )


def test_consistency_layer_wired_to_dissonance_monitor():
    """
    Test that ConsistencyLayer correctly calls observe_consistency_result()
    when check_response() is invoked.
    """
    from broca.self_model.layer import ConsistencyLayer
    from broca.self_model.storage import create_storage
    from broca.self_model.consistency import ConsistencyChecker
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "self_model.db"
        
        # Create self-model and storage
        model = SelfModel(
            capabilities=[{"text": "I can read files"}],
            constraints={"read_only": {"value": "Never write to disk"}},
        )
        storage = create_storage("sqlite", str(storage_path))
        storage.save(model)
        
        # Create dissonance monitor
        monitor = CognitiveDissonanceMonitor(self_model=model, llm_client=None)
        
        # Create a mock consistency checker that returns violations
        class MockConsistencyChecker(ConsistencyChecker):
            def validate(self, response, self_model, context=None):
                return ConsistencyResult(
                    is_consistent=False,
                    severity=0.5,
                    violations=[
                        {"type": "logical", "severity": 0.5, "description": "Test violation", "evidence": "test"},
                    ],
                )
        
        # Create consistency layer with dissonance monitor wired
        layer = ConsistencyLayer(
            self_model=model,
            storage=storage,
            checker=MockConsistencyChecker(),
            strict_mode=False,
            auto_update=False,
            max_iterations=1,
            dissonance_monitor=monitor,
        )
        
        # Initially, no violations
        assert len(monitor.logical_violations) == 0
        
        # Call check_response - this should call observe_consistency_result() internally
        layer.check_response(
            response="Test response that triggers violation.",
            conversation_context=[{"role": "user", "content": "test"}],
        )
        
        # Verify violation was recorded via observe_consistency_result()
        assert len(monitor.logical_violations) == 1, (
            "ConsistencyLayer should have called observe_consistency_result()"
        )
        
        # Verify component availability is set correctly
        metrics = monitor.measure_dissonance(response=None)
        assert metrics.component_availability["logical"] is True, (
            "Logical should be available after ConsistencyLayer check"
        )


