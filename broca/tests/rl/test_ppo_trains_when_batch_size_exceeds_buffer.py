import numpy as np

from broca.rl.ppo_policy import PPOConfig, PPOPolicy


def test_ppo_trains_when_configured_batch_size_exceeds_buffer_size():
    """
    Regression: training should not be blocked when batch_size > buffer_size.

    `batch_size` is a mini-batch size; the training trigger is `buffer_size`.
    If buffer_size=32 and batch_size=64, we still want training to run when 32
    experiences are collected (with an effective mini-batch of 32).
    """
    config = PPOConfig(
        input_dim=8,
        output_dim=3,
        hidden_dim=16,
        ppo_epochs=1,
        batch_size=64,
        buffer_size=32,
        learning_rate=1e-3,
    )
    policy = PPOPolicy(config)

    rng = np.random.default_rng(0)
    for _ in range(32):
        s = rng.normal(size=(8,)).astype(np.float32)
        ns = rng.normal(size=(8,)).astype(np.float32)
        a = int(rng.integers(low=0, high=3))
        policy.store_experience(s, a, float(rng.normal()), ns, info={"done": False})

    assert policy.training_step >= 1

