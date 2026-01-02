from __future__ import annotations

import json
from pathlib import Path

from broca.rl.ppo_buffer_recovery import merge_ppo_buffers


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_merge_remaps_actions_by_tool_name_and_drops_unknown_tools(tmp_path):
    cur = tmp_path / "ppo_buffer.json"
    # Current mapping: A|B (so output_dim=2)
    _write(
        cur,
        {
            "version": 1,
            "mapping": "A|B",
            "input_dim": 3,
            "output_dim": 2,
            "buffer_size": 10,
            "batch_size": 2,
            "training_step": 0,
            "experiences": [],
        },
    )

    # Incompatible mapping: B|C. action=0->B (recover), action=1->C (drop unknown).
    inc = tmp_path / "ppo_buffer.incompatible.mapping_mismatch.t.json"
    _write(
        inc,
        {
            "version": 1,
            "mapping": "B|C",
            "input_dim": 3,
            "output_dim": 2,
            "buffer_size": 10,
            "batch_size": 2,
            "training_step": 0,
            "experiences": [
                {"state": [1, 2, 3], "action": 0, "reward": 1.0, "next_state": [1, 2, 3], "done": False},
                {"state": [1, 2, 3], "action": 1, "reward": 1.0, "next_state": [1, 2, 3], "done": False},
            ],
        },
    )

    merged, stats = merge_ppo_buffers(current_path=cur, extra_paths=[inc])
    exps = merged["experiences"]
    assert len(exps) == 1
    assert exps[0]["action"] == 1  # tool B -> index 1 in new mapping A|B
    assert exps[0]["tool"] == "B"
    assert stats.added == 1
    assert stats.dropped_unknown_tool == 1


def test_merge_dedups_and_caps_to_buffer_size(tmp_path):
    cur = tmp_path / "ppo_buffer.json"
    _write(
        cur,
        {
            "version": 1,
            "mapping": "A|B",
            "input_dim": 2,
            "output_dim": 2,
            "buffer_size": 1,
            "batch_size": 2,
            "training_step": 0,
            "experiences": [{"state": [0, 0], "action": 0, "reward": 0.0, "next_state": [0, 0], "done": False}],
        },
    )

    inc = tmp_path / "ppo_buffer.incompatible.mapping_mismatch.t.json"
    _write(
        inc,
        {
            "version": 1,
            "mapping": "A|B",
            "input_dim": 2,
            "output_dim": 2,
            "buffer_size": 10,
            "batch_size": 2,
            "training_step": 0,
            "experiences": [
                {"state": [0, 0], "action": 0, "reward": 0.0, "next_state": [0, 0], "done": False},  # duplicate
                {"state": [1, 1], "action": 1, "reward": 1.0, "next_state": [1, 1], "done": False},  # new
            ],
        },
    )

    merged, stats = merge_ppo_buffers(current_path=cur, extra_paths=[inc])
    assert stats.deduped == 1
    # Cap=1, so only the last one remains.
    assert len(merged["experiences"]) == 1
    assert merged["experiences"][0]["action"] == 1


