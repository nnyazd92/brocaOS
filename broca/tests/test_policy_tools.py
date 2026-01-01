from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from broca.config import config
from broca.rl.policy_versions import PolicyVersionStore
from broca.tools.rl_policy_tools import (
    EvaluatePolicyTool,
    PolicyDiffTool,
    PolicyGuardTool,
    PolicyListTool,
    PromotePolicyTool,
    RollbackPolicyTool,
    UpdatePolicyTool,
)
from broca.tools.registry import ToolRegistry


@dataclass
class _Exp:
    action: int
    reward: float
    tool_name: str = ""


class _Replay:
    def __init__(self):
        self.buffer: list[_Exp] = []

    def __len__(self) -> int:
        return len(self.buffer)


class _DummyRanker:
    def __init__(self):
        self.replay_buffer = _Replay()
        self._idx_to_tool = {0: "A", 1: "B"}
        # Put a low mean reward experience so guard can fail deterministically.
        self.replay_buffer.buffer.append(_Exp(action=0, reward=0.1, tool_name="A"))

    def _online_update(self):
        return None

    def _save_state(self):
        # Create/overwrite active model/buffer files.
        Path(config.rl.model_path).parent.mkdir(parents=True, exist_ok=True)
        Path(config.rl.buffer_path).parent.mkdir(parents=True, exist_ok=True)
        Path(config.rl.model_path).write_bytes(b"MODEL_ACTIVE")
        Path(config.rl.buffer_path).write_text(json.dumps({"ok": True}), encoding="utf-8")


class _Tool:
    def __init__(self, name: str):
        self.name = name
        self.description = name
        self.parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs):
        return {"success": True}

    def format_result(self, result):
        return ""


def _with_tmp_rl_paths(tmp_path: Path):
    original = {
        "model_path": config.rl.model_path,
        "buffer_path": config.rl.buffer_path,
        "policy_versions_path": config.rl.policy_versions_path,
        "policy_archive_dir": config.rl.policy_archive_dir,
        "policy_evaluations_path": config.rl.policy_evaluations_path,
        "tools_mode": getattr(config.tools, "tools_mode", "normal"),
    }
    config.rl.model_path = str(tmp_path / "model.pt")
    config.rl.buffer_path = str(tmp_path / "buffer.json")
    config.rl.policy_versions_path = str(tmp_path / "policy_versions.json")
    config.rl.policy_archive_dir = str(tmp_path / "policy_versions")
    config.rl.policy_evaluations_path = str(tmp_path / "policy_evals.json")
    return original


def _restore_cfg(original: dict):
    config.rl.model_path = original["model_path"]
    config.rl.buffer_path = original["buffer_path"]
    config.rl.policy_versions_path = original["policy_versions_path"]
    config.rl.policy_archive_dir = original["policy_archive_dir"]
    config.rl.policy_evaluations_path = original["policy_evaluations_path"]
    config.tools.tools_mode = original["tools_mode"]


def test_policy_version_store_create_and_restore(tmp_path: Path):
    store = PolicyVersionStore(store_path=str(tmp_path / "versions.json"), archive_dir=str(tmp_path / "archive"))
    active_model = tmp_path / "active_model.pt"
    active_buffer = tmp_path / "active_buffer.json"
    active_model.write_bytes(b"V1MODEL")
    active_buffer.write_text("{\"v\":1}", encoding="utf-8")

    v1 = store.create_version(
        algorithm="online_nn",
        active_model_path=str(active_model),
        active_buffer_path=str(active_buffer),
        status="candidate",
        label="v1",
    )
    assert v1["version_id"] == 1
    assert Path(v1["model_file"]).exists()
    assert Path(v1["buffer_file"]).exists()

    # Mutate active paths, then restore.
    active_model.write_bytes(b"CORRUPT")
    active_buffer.write_text("{\"v\":999}", encoding="utf-8")

    ok, err = store.restore_to_active_paths(version_id=1, active_model_path=str(active_model), active_buffer_path=str(active_buffer))
    assert ok is True
    assert err is None
    assert active_model.read_bytes() == b"V1MODEL"
    assert active_buffer.read_text(encoding="utf-8") == "{\"v\":1}"


def test_update_policy_creates_candidate_version(tmp_path: Path):
    original = _with_tmp_rl_paths(tmp_path)
    try:
        reg = ToolRegistry()
        reg.register_tool(_Tool("A"))
        reg.register_tool(_Tool("B"))
        reg.set_online_policy_ranker(_DummyRanker())

        tool = UpdatePolicyTool(tool_registry=reg)
        res = tool.execute(train_steps=0, snapshot=True, label="cand", rationale="test")
        assert res["success"] is True
        cand = res["candidate_version"]
        assert cand["version_id"] == 1
        assert Path(cand["model_file"]).exists()
        assert Path(cand["buffer_file"]).exists()
        assert Path(config.rl.policy_versions_path).exists()
    finally:
        _restore_cfg(original)


def test_evaluate_policy_reads_buffer_and_persists(tmp_path: Path):
    original = _with_tmp_rl_paths(tmp_path)
    try:
        reg = ToolRegistry()
        reg.register_tool(_Tool("A"))
        reg.set_online_policy_ranker(_DummyRanker())

        # Add experiences to buffer.
        r = reg.online_policy_ranker
        r.replay_buffer.buffer.extend([_Exp(action=0, reward=0.2), _Exp(action=1, reward=0.8)])

        tool = EvaluatePolicyTool(tool_registry=reg)
        res = tool.execute(limit=100, persist=True, label="eval")
        assert res["success"] is True
        assert res["persisted"] is True
        report = res["report"]
        assert report["reward_stats"]["count"] >= 2
        assert Path(config.rl.policy_evaluations_path).exists()
    finally:
        _restore_cfg(original)


def test_read_only_blocks_mutation_but_allows_non_persist_eval(tmp_path: Path):
    original = _with_tmp_rl_paths(tmp_path)
    try:
        reg = ToolRegistry()
        reg.register_tool(_Tool("A"))
        reg.set_online_policy_ranker(_DummyRanker())

        config.tools.tools_mode = "read_only"

        upd = UpdatePolicyTool(tool_registry=reg)
        assert upd.execute(train_steps=0)["success"] is False

        promo = PromotePolicyTool(tool_registry=reg)
        assert promo.execute(version_id=1)["success"] is False

        rb = RollbackPolicyTool(tool_registry=reg)
        assert rb.execute(version_id=1)["success"] is False

        ev = EvaluatePolicyTool(tool_registry=reg)
        ok = ev.execute(limit=10, persist=False)
        assert ok["success"] is True

        bad = ev.execute(limit=10, persist=True)
        assert bad["success"] is False
        assert bad["error"] == "read_only_blocked"
    finally:
        _restore_cfg(original)


def test_policy_list_and_diff(tmp_path: Path):
    original = _with_tmp_rl_paths(tmp_path)
    try:
        reg = ToolRegistry()
        reg.register_tool(_Tool("A"))
        reg.register_tool(_Tool("B"))
        reg.set_online_policy_ranker(_DummyRanker())

        upd = UpdatePolicyTool(tool_registry=reg)
        _ = upd.execute(train_steps=0, snapshot=True, label="v1")
        _ = upd.execute(train_steps=0, snapshot=True, label="v2")

        lst = PolicyListTool().execute(limit=10)
        assert lst["success"] is True
        assert lst["count"] == 2

        diff = PolicyDiffTool().execute(from_version_id=1, to_version_id=2, include_buffer_summary=True)
        assert diff["success"] is True
        assert diff["from_version_id"] == 1
        assert diff["to_version_id"] == 2
        assert "meta_diff" in diff
    finally:
        _restore_cfg(original)


def test_policy_guard_blocks_promotion(tmp_path: Path):
    original = _with_tmp_rl_paths(tmp_path)
    try:
        reg = ToolRegistry()
        reg.register_tool(_Tool("A"))
        reg.register_tool(_Tool("B"))
        reg.set_online_policy_ranker(_DummyRanker())

        upd = UpdatePolicyTool(tool_registry=reg)
        res = upd.execute(train_steps=0, snapshot=True, label="low_reward")
        assert res["success"] is True
        vid = int(res["candidate_version"]["version_id"])

        guard = PolicyGuardTool().execute(version_id=vid, min_samples=1, min_mean_reward=0.99, eval_limit=5000)
        assert guard["success"] is True
        assert guard["allowed"] is False

        # Promotion should be blocked when guard=True and thresholds unmet.
        promo = PromotePolicyTool(tool_registry=reg)
        blocked = promo.execute(version_id=vid, guard=True, guard_min_samples=1, guard_min_mean_reward=0.99, guard_eval_limit=5000)
        assert blocked["success"] is False
        assert blocked["error"] == "guard_failed"
    finally:
        _restore_cfg(original)
