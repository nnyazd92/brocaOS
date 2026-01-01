import json
import tempfile
from pathlib import Path

import numpy as np
from hypothesis import given, strategies as st


def test_dataset_builder_prefers_post_context_reward_over_csv():
    from broca.rl.dataset_builder import build_dataset

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "data/rl").mkdir(parents=True, exist_ok=True)

        # experiences.jsonl provides post_context composite_reward, which should override CSV.
        exp = {
            "uid": "u1",
            "timestamp": "2025-01-01T00:00:00Z",
            "tool_call_id": "call_abc",
            "tool_name": "terminal",
            "success": True,
            "execution_time_ms": 0.0,
            "pre_context": {"rl_signals": {"composite_reward": 0.1}},
            "post_context": {
                "rl_signals": {
                    "composite_reward": 0.4,
                    "dissonance_reward": 1.0,
                    "surprise_reward": 1.0,
                    "curiosity_reward": 1.0,
                    "information_gain_reward": 1.0,
                    "coherence_reward": 1.0,
                    "exploration_balance": 0.2,
                }
            },
        }
        (root / "data/rl/experiences.jsonl").write_text(json.dumps(exp) + "\n", encoding="utf-8")

        # rl_rewards.csv would say composite_reward=0.0, but should be ignored in favor of post_context
        (root / "data/rl_rewards.csv").write_text(
            "timestamp,composite_reward,context\n"
            "2025-01-01T00:00:01Z,0.0,tool_call_terminal_call_abc\n",
            encoding="utf-8",
        )

        ds = build_dataset(root)
        assert ds.rewards.shape == (1,)
        # Reward = composite_reward + (reward_success - 0.5) - latency (quality term is 0 for result_quality=0.5).
        from broca.config import config as _config

        expected = 0.4 + (_config.rl.reward_success - 0.5)
        assert abs(float(ds.rewards[0]) - float(expected)) < 1e-6


@given(
    composite=st.one_of(
        st.floats(min_value=-10, max_value=10),
        st.just(float("nan")),
        st.just(float("inf")),
        st.just(float("-inf")),
    ),
    n_missing=st.integers(min_value=0, max_value=10),
)
def test_extract_state_features_never_nan_inf(composite: float, n_missing: int):
    from broca.rl.features import extract_state_features, RL_SIGNAL_KEYS

    # Build rl_signals with some missing keys and potentially NaN/inf
    n_signals = len(RL_SIGNAL_KEYS)
    keys = RL_SIGNAL_KEYS[: max(0, n_signals - min(n_missing, n_signals))]
    rl = {k: composite for k in keys}
    ctx = {"rl_signals": rl}

    feats = extract_state_features(ctx, input_dim=16)
    assert feats.shape == (16,)
    assert np.all(np.isfinite(feats))
