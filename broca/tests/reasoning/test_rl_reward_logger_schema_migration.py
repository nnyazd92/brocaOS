"""
Regression: rl_rewards.csv must never be truncated/reset on schema change.

We allow in-place migration that preserves all rows and expands columns.
"""

from __future__ import annotations

import csv
from pathlib import Path

from broca.reasoning.rl_reward_logger import RLRewardLogger


class DummyMetrics:
    # minimal v5-ish metrics
    schema_version = 5
    dissonance_reward = 0.1
    surprise_reward = 0.2
    curiosity_reward = 0.3
    information_gain_reward = 0.4
    coherence_reward = 0.5
    valence_reward = 0.5
    composite_reward = 0.6
    weight_dissonance = 0.3
    weight_surprise = 0.2
    weight_curiosity = 0.2
    weight_info_gain = 0.15
    weight_coherence = 0.15
    weight_valence = 0.0

    # New epistemic uncertainty fields (v4)
    epistemic_uncertainty_total = 0.4
    epistemic_uncertainty_data_quality = "medium"
    epistemic_uncertainty_sample_size = 50

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


def test_rl_rewards_repairs_headerless_v4_file(tmp_path):
    p = Path(tmp_path) / "rl_rewards.csv"

    # Create a headerless file that matches the current schema positionally.
    # (This mirrors what the user observed in data/rl_rewards.csv.)
    _ = RLRewardLogger(log_file=str(p), enabled=True, append=True)

    # Get fieldnames from logger to ensure correct count
    from broca.reasoning.rl_reward_logger import RLRewardLogger as RRL
    fieldnames = list(RRL(log_file=str(p), enabled=False)._fieldnames_v5)
    expected_cols = len(fieldnames)
    idx = {k: i for i, k in enumerate(fieldnames)}

    # Build two rows positionally (all 52 columns)
    def make_row(ctx: str, diss: str, ts: str) -> list:
        # Fill with blanks, set specific positions
        row = [""] * expected_cols
        row[idx["timestamp"]] = ts
        row[idx["dissonance_reward"]] = diss
        row[idx["surprise_reward"]] = "0.2"
        row[idx["curiosity_reward"]] = "0.3"
        row[idx["information_gain_reward"]] = "0.4"
        row[idx["coherence_reward"]] = "0.5"
        row[idx["valence_reward"]] = "0.5"
        row[idx["composite_reward"]] = "0.6"
        row[idx["exploration_balance"]] = "0.7"
        row[idx["weight_dissonance"]] = "0.3"
        row[idx["weight_surprise"]] = "0.2"
        row[idx["weight_curiosity"]] = "0.2"
        row[idx["weight_info_gain"]] = "0.15"
        row[idx["weight_coherence"]] = "0.15"
        row[idx["weight_valence"]] = "0.0"
        row[idx["context"]] = ctx
        row[idx["schema_version"]] = "5"
        return row

    rows = [
        make_row("ctx", "0.1", "2025-12-30T00:16:41.892143+00:00"),
        make_row("ctx2", "0.11", "2025-12-30T00:28:39.108258+00:00"),
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

