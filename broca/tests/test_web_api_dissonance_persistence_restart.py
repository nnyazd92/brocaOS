from __future__ import annotations

import importlib
from unittest.mock import Mock

import pytest


def test_dissonance_history_persists_across_web_runtime_restart(tmp_path, monkeypatch):
    """
    Regression: state was only loaded by ReasoningDaemon.start(), so when web_api runs with
    autonomous daemon disabled, restarts reset dissonance histories and RL shaping breaks.
    """
    state_path = tmp_path / "data" / "reasoning_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("BROCA_REASONING_STATE_FILE", str(state_path))
    monkeypatch.setenv("BROCA_REASONING_STATE_PERSISTENCE_ENABLED", "true")
    monkeypatch.setenv("BROCA_REASONING_AUTONOMOUS_ENABLED", "false")

    # ReasoningConfig reads env at import time via class defaults; reload to pick up tmp paths.
    import broca.reasoning.config as reasoning_config_module

    importlib.reload(reasoning_config_module)

    # Avoid creating real LLM clients in tests.
    import broca.llm as llm_module

    monkeypatch.setattr(llm_module, "create_llm_client", lambda *a, **k: Mock(), raising=True)

    from broca.main_repl import _initialize_reasoning_system
    from broca.reasoning.state_manager import ReasoningStateManager
    from broca.reasoning.cognitive_dissonance import DissonanceMetrics
    from datetime import datetime, timezone

    # First boot: create reasoning tool and persist a non-zero dissonance measurement.
    reasoning_tool_1 = _initialize_reasoning_system(
        memory_manager=None,
        self_model=Mock(),
        self_model_storage=None,
        internal_sensing=None,
    )
    assert reasoning_tool_1 is not None

    monitor_1 = getattr(reasoning_tool_1, "cognitive_dissonance_monitor", None)
    assert monitor_1 is not None

    monitor_1.dissonance_history.append(
        DissonanceMetrics(
            timestamp=datetime.now(timezone.utc),
            logical_dissonance=0.1,
            factual_dissonance=0.2,
            behavioral_dissonance=0.3,
            goal_dissonance=0.4,
            overall_dissonance=0.42,
            measurement_quality="measured",
            has_sufficient_data=True,
            component_availability={"logical": True, "factual": True, "behavioral": True, "goal": True},
        )
    )

    sm = ReasoningStateManager(state_file_path=str(state_path))
    sm.save_state(
        rule_system=reasoning_tool_1.rule_system,
        goal_manager=reasoning_tool_1.goal_manager,
        working_memory=reasoning_tool_1.rule_system.working_memory,
        dissonance_monitor=monitor_1,
        force=True,
    )

    # Second boot: should eagerly load state even without the daemon.
    reasoning_tool_2 = _initialize_reasoning_system(
        memory_manager=None,
        self_model=Mock(),
        self_model_storage=None,
        internal_sensing=None,
    )
    assert reasoning_tool_2 is not None

    monitor_2 = getattr(reasoning_tool_2, "cognitive_dissonance_monitor", None)
    assert monitor_2 is not None

    assert len(monitor_2.dissonance_history) >= 1
    assert monitor_2.dissonance_history[-1].overall_dissonance == pytest.approx(0.42)

