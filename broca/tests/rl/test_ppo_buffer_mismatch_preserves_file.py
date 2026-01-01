from __future__ import annotations

import json

from broca.rl.ppo_online_policy import PPOOnlinePolicyRanker


class _Tool:
    def __init__(self, name: str) -> None:
        self.name = name


def test_mapping_mismatch_preserves_existing_buffer_file(tmp_path):
    buf = tmp_path / "ppo_buffer.json"
    buf.write_text(
        json.dumps(
            {
                "version": 1,
                "mapping": "OLD_TOOL",
                "input_dim": 32,
                "output_dim": 1,
                "buffer_size": 128,
                "batch_size": 8,
                "training_step": 0,
                "experiences": [],
            }
        ),
        encoding="utf-8",
    )

    ranker = PPOOnlinePolicyRanker(buffer_size=8, batch_size=2)
    ranker._buffer_path = buf  # force test isolation
    ranker._ensure_policy([_Tool("NEW_TOOL")])

    assert not buf.exists(), "expected incompatible buffer to be moved aside"
    preserved = list(tmp_path.glob("ppo_buffer.incompatible.mapping_mismatch.*.json"))
    assert preserved, "expected a preserved incompatible buffer file"

