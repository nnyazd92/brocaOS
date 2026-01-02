from __future__ import annotations

from broca.rl.features import RL_SIGNAL_KEYS
from broca.rl.reward import compute_reward_from_outcome


def test_reward_uses_only_rl_signals_not_tool_outcome():
    rl_signals = {"composite_reward": 0.37}
    r, parts = compute_reward_from_outcome(
        rl_signals=rl_signals,
        intrinsic_keys=RL_SIGNAL_KEYS,
        success=True,
        execution_time_ms=999999.0,
        result_quality=1.0,
        reward_success=1.0,
        reward_failure=0.0,
        time_penalty_factor=1.0,
        max_latency_penalty=1.0,
        quality_bonus_factor=1.0,
    )

    assert abs(float(r) - 0.37) < 1e-9
    assert parts["tool_adjustment"] == 0.0
    assert parts["latency_penalty"] == 0.0

