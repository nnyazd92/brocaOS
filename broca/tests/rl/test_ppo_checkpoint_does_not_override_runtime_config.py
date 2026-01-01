from pathlib import Path

from broca.rl.ppo_policy import PPOConfig, PPOPolicy


def test_ppo_load_does_not_override_runtime_config(tmp_path: Path):
    """
    Regression: PPOPolicy.load() must not overwrite runtime config values.

    Otherwise a saved checkpoint can silently force batch_size/buffer_size back to old defaults
    and prevent training under the current environment configuration.
    """
    ckpt_path = tmp_path / "ppo.pt"

    # "Old" checkpoint with different config.
    old = PPOPolicy(
        PPOConfig(
            input_dim=8,
            output_dim=3,
            hidden_dim=16,
            batch_size=64,
            buffer_size=2048,
        )
    )
    old.save(str(ckpt_path))

    # "Runtime" policy config should remain authoritative after load.
    runtime_cfg = PPOConfig(
        input_dim=8,
        output_dim=3,
        hidden_dim=16,
        batch_size=16,
        buffer_size=32,
    )
    runtime = PPOPolicy(runtime_cfg)
    runtime.load(str(ckpt_path))

    assert runtime.config.batch_size == 16
    assert runtime.config.buffer_size == 32

