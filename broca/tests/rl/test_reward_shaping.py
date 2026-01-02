from __future__ import annotations

from broca.rl.features import RL_SIGNAL_KEYS
from broca.rl.reward import compute_reward_from_outcome


def test_potential_shaping_uses_gamma_phi_post_minus_phi_pre():
    # Choose signals so phi is easy: composite_reward present.
    pre = {"composite_reward": 0.2}
    post = {"composite_reward": 0.6}
    r, parts = compute_reward_from_outcome(
        pre_rl_signals=pre,
        post_rl_signals=post,
        intrinsic_keys=RL_SIGNAL_KEYS,
        success=False,
        execution_time_ms=0.0,
        result_quality=0.0,
        reward_success=1.0,
        reward_failure=0.0,  # failure => extrinsic=0
        time_penalty_factor=0.0,
        max_latency_penalty=1.0,
        quality_bonus_factor=0.0,
        shaping_beta=1.0,
        shaping_gamma=0.5,
        use_varnorm_phi=False,
    )

    # extrinsic=0, latency=0 => total = clamp01(shaping)
    # shaping = 1.0 * (0.5*0.6 - 0.2) = 0.1
    assert abs(parts["shaping"] - 0.1) < 1e-9
    assert abs(float(r) - 0.1) < 1e-9


def test_extrinsic_anchor_dominates_when_beta_small():
    pre = {"composite_reward": 0.0}
    post = {"composite_reward": 1.0}
    r, parts = compute_reward_from_outcome(
        pre_rl_signals=pre,
        post_rl_signals=post,
        intrinsic_keys=RL_SIGNAL_KEYS,
        success=True,
        execution_time_ms=0.0,
        result_quality=0.0,
        reward_success=0.8,
        reward_failure=0.2,
        time_penalty_factor=0.0,
        max_latency_penalty=1.0,
        quality_bonus_factor=0.0,
        shaping_beta=0.01,
        shaping_gamma=0.99,
        use_varnorm_phi=False,
    )

    assert abs(parts["extrinsic"] - 0.8) < 1e-9
    assert parts["shaping"] <= 0.01
    assert float(r) >= 0.8


