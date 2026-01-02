from __future__ import annotations

from broca.world_state.aggregator import WorldStateAggregator


def test_shared_state_persists_and_is_included_in_aggregate(tmp_path):
    path = tmp_path / "shared_state.json"

    agg1 = WorldStateAggregator(shared_state_path=path)
    agg1.set_shared_state("autonomous_loop.current", {"topic": "t1"}, source="test")
    ws1 = agg1.aggregate()
    assert "shared_state" in ws1
    assert "autonomous_loop.current" in ws1["shared_state"]
    assert ws1["shared_state"]["autonomous_loop.current"]["value"]["topic"] == "t1"

    # New aggregator instance loads persisted state
    agg2 = WorldStateAggregator(shared_state_path=path)
    ws2 = agg2.aggregate()
    assert ws2["shared_state"]["autonomous_loop.current"]["value"]["topic"] == "t1"

