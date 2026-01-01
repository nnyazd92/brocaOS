"""
Unit tests for ReasoningDaemon performance no-op skips.
"""

from __future__ import annotations

import os
from unittest.mock import Mock

from broca.reasoning.daemon import ReasoningDaemon


def test_daemon_skips_postprocess_when_no_rules_fired(monkeypatch):
    monkeypatch.setenv("BROCA_REASONING_DAEMON_SKIP_POSTPROCESS_WHEN_NO_RULES", "true")

    goal_manager = Mock()
    goal_manager.get_ready_goals.return_value = [{"name": "g1"}]

    rule_engine = Mock()
    rule_engine.execute_cycle.return_value = []

    rule_system = Mock()
    rule_system.working_memory = Mock()

    reasoning_tool = Mock()
    reasoning_tool.goal_manager = goal_manager
    reasoning_tool.rule_engine = rule_engine
    reasoning_tool.rule_system = rule_system

    feedback_loop = Mock()
    self_model_loop = Mock()

    daemon = ReasoningDaemon(
        reasoning_tool=reasoning_tool,
        feedback_loop_manager=feedback_loop,
        self_model_feedback_loop=self_model_loop,
        cycle_delay_seconds=0.01,
        max_cycles_per_minute=100,
    )

    ok = daemon._execute_cycle()
    assert ok is True
    feedback_loop.evaluate_cycle_outcomes.assert_not_called()
    feedback_loop.apply_feedback.assert_not_called()
    self_model_loop.increment_cycle_count.assert_not_called()
    self_model_loop.should_update.assert_not_called()
    self_model_loop.trigger_update.assert_not_called()
    assert daemon.cycle_history and daemon.cycle_history[-1].get("skipped_postprocess") is True


def test_daemon_offloads_self_model_update(monkeypatch):
    monkeypatch.setenv("BROCA_REASONING_DAEMON_SKIP_POSTPROCESS_WHEN_NO_RULES", "false")
    monkeypatch.setenv("BROCA_REASONING_DAEMON_ASYNC_SELF_MODEL_UPDATES", "true")
    monkeypatch.setenv("BROCA_REASONING_DAEMON_ASYNC_DISSONANCE_MEASUREMENT", "true")

    goal_manager = Mock()
    goal_manager.get_ready_goals.return_value = [{"name": "g1"}]

    rule_engine = Mock()
    rule_engine.execute_cycle.return_value = [{"type": "noop"}]  # something fired

    rule_system = Mock()
    rule_system.working_memory = Mock()

    reasoning_tool = Mock()
    reasoning_tool.goal_manager = goal_manager
    reasoning_tool.rule_engine = rule_engine
    reasoning_tool.rule_system = rule_system

    feedback_loop = Mock()
    feedback_loop.cognitive_dissonance_monitor = Mock()
    feedback_loop.cognitive_dissonance_monitor.measure_dissonance = Mock()
    feedback_loop.evaluate_cycle_outcomes.return_value = Mock(overall_dissonance=0.0)

    self_model_loop = Mock()
    self_model_loop.should_update.return_value = True

    daemon = ReasoningDaemon(
        reasoning_tool=reasoning_tool,
        feedback_loop_manager=feedback_loop,
        self_model_feedback_loop=self_model_loop,
        cycle_delay_seconds=0.01,
        max_cycles_per_minute=100,
    )

    ok = daemon._execute_cycle()
    assert ok is True
    # In async mode, we should have scheduled the update rather than calling directly.
    assert daemon._self_model_update_future is not None
    assert daemon._dissonance_future is not None
    self_model_loop.trigger_update.assert_not_called()
