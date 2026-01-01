from __future__ import annotations

import json
from pathlib import Path

import pytest

from broca.reasoning.goal_manager import GoalManager
from broca.reasoning.goal_snapshots import GoalSnapshotStore


def test_goal_snapshot_store_atomic_write_fault_injection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Fault injection: simulate os.replace failure during snapshot creation.

    Expectation: existing snapshot file content remains unchanged (no partial write).
    """
    snapshots_path = tmp_path / "goal_snapshots.json"
    initial = {"current_snapshot_id": 0, "history": []}
    snapshots_path.write_text(json.dumps(initial), encoding="utf-8")

    store = GoalSnapshotStore(str(snapshots_path))

    def _boom(*args, **kwargs):
        raise OSError("injected replace failure")

    monkeypatch.setattr("broca.reasoning.goal_snapshots.os.replace", _boom)

    with pytest.raises(OSError):
        store.create_snapshot(GoalManager(), label="v1", rationale="fault")

    assert json.loads(snapshots_path.read_text(encoding="utf-8")) == initial

