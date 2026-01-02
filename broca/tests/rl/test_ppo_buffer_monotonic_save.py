from __future__ import annotations

import json
import logging
from pathlib import Path


class _Tool:
    def __init__(self, name: str) -> None:
        self.name = name


def test_ppo_save_buffer_does_not_shrink_existing_file(tmp_path, caplog):
    """
    Regression: if a process has a small in-memory buffer but the on-disk buffer is larger,
    _save_buffer must not overwrite the larger file (monotonic persistence).
    """
    from broca.rl import ppo_online_policy
    from broca.rl.ppo_online_policy import PPOOnlinePolicyRanker

    caplog.set_level(logging.INFO)
    ppo_online_policy.tool_selection_logger = logging.getLogger("test.ppo.monotonic")
    ppo_online_policy.tool_selection_logger.setLevel(logging.INFO)
    ppo_online_policy.tool_selection_logger.propagate = True

    buf = tmp_path / "ppo_buffer.json"
    # Seed a larger compatible buffer file.
    buf.write_text(
        json.dumps(
            {
                "version": 1,
                "mapping": "a|b",
                "input_dim": 32,
                "output_dim": 2,
                "buffer_size": 256,
                "batch_size": 2,
                "training_step": 0,
                "experiences": [
                    {"state": [0.0] * 32, "action": 0, "reward": 0.0, "next_state": [0.0] * 32, "done": False}
                    for _ in range(10)
                ],
            }
        ),
        encoding="utf-8",
    )

    ranker = PPOOnlinePolicyRanker(buffer_size=256, batch_size=2)
    ranker._buffer_path = buf
    ranker._ensure_policy([_Tool("a"), _Tool("b")])
    assert ranker._policy is not None

    # Shrink in-memory buffer to 1 and save; file should remain >= 10.
    with ranker._policy.buffer_lock:
        ranker._policy.buffer.clear()
        ranker._policy.buffer.append(
            {"state": [0.0] * 32, "action": 0, "reward": 0.0, "next_state": [0.0] * 32, "done": False}
        )

    ranker._save_buffer()

    payload = json.loads(buf.read_text(encoding="utf-8"))
    assert len(payload.get("experiences", [])) >= 10


