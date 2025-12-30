"""
Regression: rl_rewards.csv must never be truncated/reset on schema change.

We allow in-place migration that preserves all rows and expands columns.
"""

from __future__ import annotations

import csv
from pathlib import Path

from broca.reasoning.rl_reward_logger import RLRewardLogger


class DummyMetrics:
    # minimal v1-ish metrics
    schema_version = 3
    dissonance_reward = 0.1
    surprise_reward = 0.2
    curiosity_reward = 0.3
    information_gain_reward = 0.4
    coherence_reward = 0.5
    composite_reward = 0.6
    weight_dissonance = 0.3
    weight_surprise = 0.2
    weight_curiosity = 0.2
    weight_info_gain = 0.15
    weight_coherence = 0.15

    def get_exploration_exploitation_balance(self):
        return 0.5


def test_rl_rewards_inplace_migration_preserves_rows(tmp_path):
    p = Path(tmp_path) / "rl_rewards.csv"

    # Create an old schema file (subset of columns) with one row
    old_header = ["timestamp", "dissonance_reward", "surprise_reward", "curiosity_reward", "composite_reward", "context"]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=old_header)
        w.writeheader()
        w.writerow(
            {
                "timestamp": "2025-01-01T00:00:00Z",
                "dissonance_reward": "0.9",
                "surprise_reward": "0.8",
                "curiosity_reward": "0.7",
                "composite_reward": "0.85",
                "context": "old",
            }
        )

    logger = RLRewardLogger(log_file=str(p), enabled=True, append=True)
    logger.log_reward_signals(DummyMetrics(), context="new")

    # File should still contain old row + new row
    with p.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["context"] == "old"
    assert rows[1]["context"] == "new"


def test_rl_rewards_repairs_headerless_v3_file(tmp_path):
    p = Path(tmp_path) / "rl_rewards.csv"

    # Create a headerless file that matches the current v3 schema positionally.
    # (This mirrors what the user observed in data/rl_rewards.csv.)
    logger = RLRewardLogger(log_file=str(p), enabled=True, append=True)
    # Write two rows without header, in v3 positional order
    rows = [
        [
            "2025-12-30T00:16:41.892143+00:00",
            "0.1",
            "0.2",
            "0.3",
            "0.4",
            "0.5",
            "0.6",
            "0.7",
            "0.3",
            "0.2",
            "0.2",
            "0.15",
            "0.15",
            "ctx",
            "3",
            "0.0",
            "False",
            "",
            "",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "",
            "True",
            "high",
            "",
            "0.0",
            "0.0",
            "True",
            "high",
            "",
            "0.0",
            "0.0",
            "True",
            "high",
            "",
            "0.0",
            "0.0",
            "",
            "True",
            "",
            "0.0",
        ],
        [
            "2025-12-30T00:28:39.108258+00:00",
            "0.11",
            "0.21",
            "0.31",
            "0.41",
            "0.51",
            "0.61",
            "0.71",
            "0.3",
            "0.2",
            "0.2",
            "0.15",
            "0.15",
            "ctx2",
            "3",
            "0.0",
            "False",
            "",
            "",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "",
            "True",
            "high",
            "",
            "0.0",
            "0.0",
            "True",
            "high",
            "",
            "0.0",
            "0.0",
            "True",
            "high",
            "",
            "0.0",
            "0.0",
            "",
            "True",
            "",
            "0.0",
        ],
    ]

    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)

    # Re-initialize; should repair headerless file without losing rows
    _ = RLRewardLogger(log_file=str(p), enabled=True, append=True)

    with p.open("r", newline="", encoding="utf-8") as f:
        dr = csv.DictReader(f)
        out = list(dr)

    assert dr.fieldnames is not None
    assert "timestamp" in dr.fieldnames
    assert len(out) == 2
    assert out[0]["context"] == "ctx"
    assert out[1]["context"] == "ctx2"


