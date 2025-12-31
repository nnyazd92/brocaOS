from collections import deque
from datetime import datetime, timezone

from broca.reasoning.cognitive_dissonance import DissonanceMetrics
from broca.reasoning.state_manager import ReasoningStateManager


class _DummyDissonanceMonitor:
    def __init__(self, history_window: int = 10):
        self.history_window = history_window
        self.dissonance_history = deque(maxlen=history_window)
        self.logical_violations = deque(maxlen=history_window)
        self.factual_errors = deque(maxlen=history_window)
        self.behavioral_deviations = deque(maxlen=history_window)
        self.behavioral_inconsistencies = deque(maxlen=history_window)
        self.goal_conflicts = deque(maxlen=history_window)
        self._commitment_strength = {}


def test_reasoning_state_manager_persists_dissonance_monitor(tmp_path):
    """
    Regression: dissonance histories should survive restarts, otherwise RL dissonance_reward
    can reset to misleading defaults right after restart.
    """
    state_path = tmp_path / "reasoning_state.json"
    sm = ReasoningStateManager(state_file_path=str(state_path), backup_enabled=False)

    mon1 = _DummyDissonanceMonitor(history_window=10)
    mon1.logical_violations.append({"type": "logical", "severity": 0.7})
    mon1.factual_errors.append({"type": "factual", "severity": 0.4})
    mon1._commitment_strength["capability_x"] = 0.9
    mon1.dissonance_history.append(
        DissonanceMetrics(
            timestamp=datetime.now(timezone.utc),
            logical_dissonance=0.6,
            factual_dissonance=0.2,
            behavioral_dissonance=0.0,
            goal_dissonance=0.0,
            overall_dissonance=0.4,
            measurement_quality="measured",
            has_sufficient_data=True,
            component_availability={"logical": True, "factual": True, "behavioral": False, "goal": False},
        )
    )

    assert sm.save_state(dissonance_monitor=mon1, force=True) is True

    mon2 = _DummyDissonanceMonitor(history_window=10)
    sm.load_state(dissonance_monitor=mon2)

    assert len(mon2.logical_violations) == 1
    assert len(mon2.factual_errors) == 1
    assert mon2._commitment_strength.get("capability_x") == 0.9
    assert len(mon2.dissonance_history) == 1
    assert isinstance(mon2.dissonance_history[-1], DissonanceMetrics)
    assert abs(mon2.dissonance_history[-1].overall_dissonance - 0.4) < 1e-9
