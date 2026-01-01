from __future__ import annotations

from unittest.mock import Mock


def test_world_state_prefers_reasoning_state_summary_and_caches(monkeypatch):
    monkeypatch.setenv("BROCA_WORLD_STATE_REASONING_STATE_CACHE_MS", "10000")

    reasoning_tool = Mock()
    reasoning_tool.daemon = None
    reasoning_tool.rule_engine = None
    reasoning_tool.affect_monitor = None

    # First call: summary succeeds.
    summary_state = {
        "success": True,
        "state": {
            "active_goals": [{"name": "g", "description": "d", "priority": 1.0}],
            "ready_goals_count": 0,
            "total_rules": 3,
            "working_memory_size": 1,
            "last_cycle_time": "2025-01-01T00:00:00+00:00",
        },
    }

    reasoning_tool.execute = Mock(
        side_effect=[
            summary_state,  # get_state_summary
        ]
    )

    from broca.world_state.aggregator import WorldStateAggregator

    agg = WorldStateAggregator(reasoning_tool=reasoning_tool)

    r1 = agg.get_reasoning_state()
    r2 = agg.get_reasoning_state()

    assert r1.get("available") is True
    assert r1 == r2  # cached

    # Only one execute call should occur due to caching.
    assert reasoning_tool.execute.call_count == 1
    (action,), _kwargs = reasoning_tool.execute.call_args
    assert action == "get_state_summary"

