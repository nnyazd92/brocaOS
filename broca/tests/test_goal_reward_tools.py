from __future__ import annotations

import json
from pathlib import Path

import pytest

from broca.config import config
from broca.learning.experience_logger import ExperienceLogger
from broca.reasoning.goal_manager import GoalManager
from broca.rl.reward_design import apply_persisted_reward_design
from broca.tools.goal_reward_tools import DesignRewardTool, SetGoalsTool


def test_set_goals_upserts_and_persists(tmp_path: Path):
    gm = GoalManager()
    exp = ExperienceLogger(storage_path=str(tmp_path / "experiences.json"), auto_save=True)
    state_path = tmp_path / "reasoning_state.json"
    snapshots_path = tmp_path / "goal_snapshots.json"
    tool = SetGoalsTool(
        goal_manager=gm,
        experience_logger=exp,
        state_file_path=str(state_path),
        snapshots_file_path=str(snapshots_path),
    )

    res = tool.execute(
        mode="set_active",
        goals=[
            {
                "name": "user_goal_1",
                "description": "Do the thing",
                "goal_type": "achieve",
                "priority": 0.9,
                "tags": ["user"],
            }
        ],
        suspend_others=True,
        persist=True,
        rationale="test",
    )
    assert res["success"] is True
    assert any(g["name"] == "user_goal_1" for g in res["active_goals"])
    assert state_path.exists()
    assert snapshots_path.exists()
    assert res.get("snapshot", {}).get("snapshot_id") == 1

    # Experience should be logged
    saved = json.loads((tmp_path / "experiences.json").read_text(encoding="utf-8"))
    assert any(e.get("experience_type") == "set_goals" for e in saved.get("experiences", []))


def test_design_reward_updates_config_and_persists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    original = {
        "reward_success": config.rl.reward_success,
        "reward_failure": config.rl.reward_failure,
        "time_penalty_factor": config.rl.time_penalty_factor,
        "max_latency_penalty": config.rl.max_latency_penalty,
        "quality_bonus_factor": config.rl.quality_bonus_factor,
    }
    exp = ExperienceLogger(storage_path=str(tmp_path / "experiences.json"), auto_save=True)
    tool = DesignRewardTool(experience_logger=exp, design_file_path=str(tmp_path / "reward_design.json"))

    res = tool.execute(reward_success=0.9, reward_failure=0.1, time_penalty_factor=0.0, persist=True, rationale="test")
    assert res["success"] is True
    assert config.rl.reward_success == 0.9
    assert config.rl.reward_failure == 0.1
    assert config.rl.time_penalty_factor == 0.0
    assert (tmp_path / "reward_design.json").exists()

    # restore globals to avoid cross-test leakage
    config.rl.reward_success = original["reward_success"]
    config.rl.reward_failure = original["reward_failure"]
    config.rl.time_penalty_factor = original["time_penalty_factor"]
    config.rl.max_latency_penalty = original["max_latency_penalty"]
    config.rl.quality_bonus_factor = original["quality_bonus_factor"]


def test_set_goals_list_diff_and_rollback(tmp_path: Path):
    gm = GoalManager()
    state_path = tmp_path / "reasoning_state.json"
    snapshots_path = tmp_path / "goal_snapshots.json"
    tool = SetGoalsTool(goal_manager=gm, state_file_path=str(state_path), snapshots_file_path=str(snapshots_path))

    res1 = tool.execute(
        mode="set_active",
        goals=[{"name": "g1", "description": "one", "priority": 0.6, "tags": ["a"]}],
        persist=True,
        snapshot=True,
        snapshot_label="v1",
        rationale="initial",
    )
    assert res1["success"] is True
    assert res1["snapshot"]["snapshot_id"] == 1

    res2 = tool.execute(
        mode="upsert",
        goals=[
            {"name": "g1", "description": "one updated", "priority": 0.7, "tags": ["a", "b"]},
            {"name": "g2", "description": "two", "priority": 0.2},
        ],
        persist=True,
        snapshot=True,
        snapshot_label="v2",
        rationale="change",
    )
    assert res2["success"] is True
    assert res2["snapshot"]["snapshot_id"] == 2

    listed = tool.execute(mode="list_versions", limit=10)
    assert listed["success"] is True
    assert listed["count"] == 2
    assert [s["snapshot_id"] for s in listed["snapshots"]] == [1, 2]

    diff = tool.execute(mode="diff", from_snapshot_id=1, to_snapshot_id=2)
    assert diff["success"] is True
    assert "g2" in diff["diff"]["added"]
    assert "g1" in diff["diff"]["changed"]

    rb = tool.execute(mode="rollback", snapshot_id=1, persist=True, rationale="rollback")
    assert rb["success"] is True
    assert any(g["name"] == "g1" and g["description"] == "one" for g in rb["active_goals"])
    assert not any(g["name"] == "g2" for g in rb["active_goals"])
    assert state_path.exists()


def test_read_only_allows_audit_but_blocks_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    gm = GoalManager()
    state_path = tmp_path / "reasoning_state.json"
    snapshots_path = tmp_path / "goal_snapshots.json"
    goals_tool = SetGoalsTool(goal_manager=gm, state_file_path=str(state_path), snapshots_file_path=str(snapshots_path))
    reward_tool = DesignRewardTool(design_file_path=str(tmp_path / "reward_design.json"))

    # Create at least one snapshot in normal mode.
    goals_tool.execute(
        mode="set_active",
        goals=[{"name": "g1", "description": "one"}],
        persist=True,
        snapshot=True,
    )

    original_tools_mode = getattr(config.tools, "tools_mode", "normal")
    try:
        config.tools.tools_mode = "read_only"

        # Audit modes should still work.
        res_list = goals_tool.execute(mode="list_versions", limit=10)
        assert res_list["success"] is True
        assert res_list["count"] >= 1

        res_get = reward_tool.execute(action="get")
        assert res_get["success"] is True

        # Mutation should be blocked by tool-level gating.
        res_set = reward_tool.execute(action="set", reward_success=0.99)
        assert res_set["success"] is False
        assert res_set["error"] == "read_only_blocked"

        res_mut = goals_tool.execute(mode="upsert", goals=[{"name": "g2", "description": "two"}])
        assert res_mut["success"] is False
        assert res_mut["error"] == "read_only_blocked"
    finally:
        config.tools.tools_mode = original_tools_mode


def test_apply_persisted_reward_design_updates_runtime_config(tmp_path: Path):
    design_path = tmp_path / "reward_design.json"
    design_path.write_text(
        json.dumps({"current": {"reward_success": 0.95, "reward_failure": 0.05, "time_penalty_factor": 0.0}}),
        encoding="utf-8",
    )

    original = {
        "reward_success": config.rl.reward_success,
        "reward_failure": config.rl.reward_failure,
        "time_penalty_factor": config.rl.time_penalty_factor,
    }
    try:
        applied, changes = apply_persisted_reward_design(path=str(design_path))
        assert applied is True
        assert config.rl.reward_success == 0.95
        assert config.rl.reward_failure == 0.05
        assert config.rl.time_penalty_factor == 0.0
        assert "reward_success" in changes
    finally:
        config.rl.reward_success = original["reward_success"]
        config.rl.reward_failure = original["reward_failure"]
        config.rl.time_penalty_factor = original["time_penalty_factor"]
