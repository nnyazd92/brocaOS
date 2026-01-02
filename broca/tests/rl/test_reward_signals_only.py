from __future__ import annotations

from broca.rl.features import RL_SIGNAL_KEYS
from broca.rl.reward import compute_reward_from_outcome


def test_reward_is_extrinsic_anchored_and_applies_latency_penalty():
    # Post-signal only (pre missing) => shaping defaults to ~0; reward should be dominated by extrinsic/latency.
    rl_signals = {"composite_reward": 0.37}
    r, parts = compute_reward_from_outcome(
        rl_signals=rl_signals,
        intrinsic_keys=RL_SIGNAL_KEYS,
        success=True,
        execution_time_ms=1000.0,
        result_quality=1.0,
        reward_success=1.0,
        reward_failure=0.0,
        time_penalty_factor=0.001,
        max_latency_penalty=1.0,
        quality_bonus_factor=1.0,
    )

    assert parts["extrinsic"] == 1.0
    assert parts["latency_penalty"] > 0.0
    assert parts["total"] == float(r)
    assert 0.0 <= float(r) <= 1.0

