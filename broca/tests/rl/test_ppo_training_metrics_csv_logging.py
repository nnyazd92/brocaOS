import csv
import os

import numpy as np

from broca.rl.ppo_policy import PPOConfig, PPOPolicy


def test_ppo_training_metrics_are_logged_to_csv(tmp_path, monkeypatch):
    out = tmp_path / "ppo_training_metrics.csv"
    monkeypatch.setenv("BROCA_RL_PPO_TRAIN_LOG_ENABLED", "true")
    monkeypatch.setenv("BROCA_RL_PPO_TRAIN_LOG_FILE", str(out))
    monkeypatch.setenv("BROCA_RL_PPO_TRAIN_LOG_APPEND", "true")

    config = PPOConfig(
        input_dim=8,
        output_dim=3,
        hidden_dim=16,
        ppo_epochs=1,
        batch_size=16,
        buffer_size=8,
        learning_rate=1e-3,
    )
    policy = PPOPolicy(config)

    rng = np.random.default_rng(0)
    for i in range(8):
        s = rng.normal(size=(8,)).astype(np.float32)
        ns = rng.normal(size=(8,)).astype(np.float32)
        a = int(rng.integers(low=0, high=3))
        # Mark the last step as done so episode_returns has a clean terminal.
        policy.store_experience(s, a, float(rng.normal()), ns, info={"done": i == 7})

    assert out.exists()
    rows = list(csv.DictReader(out.read_text(encoding="utf-8").splitlines()))
    assert len(rows) >= 1
    last = rows[-1]
    assert int(last["training_step"]) >= 1
    assert int(last["n_experiences"]) == 8
    assert "approx_kl" in last and last["approx_kl"] != ""
    assert float(last["approx_kl"]) >= -1e-9
    assert "clip_fraction" in last and last["clip_fraction"] != ""
    assert float(last["configured_batch_size"]) == 16.0
    assert float(last["configured_buffer_size"]) == 8.0
