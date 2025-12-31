import numpy as np

import pytest

# Check if PyTorch is available (PPO uses torch)
try:
    import torch  # noqa: F401

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

pytestmark = pytest.mark.skipif(not HAS_TORCH, reason="PyTorch not available")

from hypothesis import given, strategies as st


class _Tool:
    def __init__(self, name: str):
        self.name = name


def test_extract_state_features_golden_trace():
    from broca.rl.features import extract_state_features
    import hashlib

    ctx = {
        "rl_signals": {
            "dissonance_reward": 0.8,
            "surprise_reward": 0.7,
            "curiosity_reward": 0.6,
            "information_gain_reward": 0.5,
            "coherence_reward": 0.4,
            "exploration_balance": 0.3,
        },
        "active_goals": [{"priority": 0.7, "goal_type": "build"}, {"priority": 0.2, "goal_type": "test"}],
        "applicable_skills": [{"proficiency_level": 0.9, "usage_count": 10}],
        "working_memory_items": [1, 2, 3, 4],
        "recent_tools": ["terminal", "rg"],
        "production_rules": [{"active": True}, {"active": False}, {"active": True}],
    }

    feats = extract_state_features(ctx, input_dim=16).tolist()

    # 6 signal features (in fixed order) + 10 context features
    assert np.allclose(feats[:6], [0.8, 0.7, 0.6, 0.5, 0.4, 0.3])
    # Stable goal_type encoding (sha256 -> [0,1))
    h = hashlib.sha256("buildtest".encode("utf-8")).digest()
    stable_goal_hash = int.from_bytes(h[:4], "big", signed=False) / float(2**32)
    assert np.allclose(
        feats[6:],
        [
            2 / 5.0,  # active_goals count
            0.7,  # max priority
            stable_goal_hash,
        1 / 5.0,  # skills count
        0.9,  # max proficiency
        10 / 100.0,  # usage_count sum for top 3
        4 / 10.0,  # working memory count
        2 / 5.0,  # recent tools count
        3 / 10.0,  # rules count
        2 / 5.0,  # active rules count
        ],
    )


def test_extract_state_features_is_defensive_on_bad_inputs():
    from broca.rl.features import extract_state_features

    ctx = {
        "rl_signals": "not a dict",
        "active_goals": "nope",
        "applicable_skills": None,
        "working_memory_items": 123,
        "recent_tools": {"x": 1},
        "production_rules": [{"active": "yes"}, object()],
    }
    feats = extract_state_features(ctx, input_dim=16)
    assert feats.shape == (16,)
    assert np.all(np.isfinite(feats))

@given(
    rl_signals=st.dictionaries(
        keys=st.sampled_from(
            [
                "composite_reward",
                "dissonance_reward",
                "surprise_reward",
                "curiosity_reward",
                "information_gain_reward",
                "coherence_reward",
                "exploration_balance",
            ]
        ),
        values=st.one_of(
            st.floats(min_value=-10, max_value=10),
            st.just(float("nan")),
            st.just(float("inf")),
            st.just(float("-inf")),
        ),
        min_size=0,
        max_size=7,
    ),
)
def test_extract_state_features_clamps_rl_signals_to_unit_interval(rl_signals):
    from broca.rl.features import extract_state_features

    feats = extract_state_features({"rl_signals": rl_signals}, input_dim=16)
    assert feats.shape == (16,)

    # First 6 features correspond to rl_signals and must be clamped to [0, 1] with defaults.
    assert np.all(np.isfinite(feats[:6]))
    assert np.all(feats[:6] >= 0.0)
    assert np.all(feats[:6] <= 1.0)


def test_ppo_online_uses_post_rl_signals_for_reward_and_next_state_features():
    """
    Ensure the custom RL reward signals are used:
    - composite_reward drives the PPO reward
    - per-signal values appear in the feature vector (state + next_state)
    """
    from broca.rl.ppo_online_policy import PPOOnlinePolicyRanker, RL_SIGNAL_KEYS

    tools = [_Tool("terminal")]
    ranker = PPOOnlinePolicyRanker(force_threshold=0.0, suggest_threshold=0.0)  # always forced

    pre_ctx = {
        "rl_signals": {k: 0.1 for k in RL_SIGNAL_KEYS},
        "active_goals": [{"priority": 0.2, "goal_type": "x"}],
    }

    sel = ranker.select_tool(tools, pre_ctx)
    assert sel.mode == "forced"

    post_rl_signals = {k: 0.0 for k in RL_SIGNAL_KEYS}
    post_rl_signals["composite_reward"] = 0.77
    post_rl_signals["dissonance_reward"] = 0.11
    post_rl_signals["information_gain_reward"] = 0.99

    before = len(ranker._policy.buffer)  # type: ignore[union-attr]
    ranker.record_outcome(
        tool_name="terminal",
        context=pre_ctx,
        next_context={},  # simulate missing rl_signals in post context
        reward=None,  # must be derived from post rl_signals composite_reward
        rl_signals=post_rl_signals,
        success=True,
    )
    after = len(ranker._policy.buffer)  # type: ignore[union-attr]
    assert after == before + 1

    exp = ranker._policy.buffer[-1]  # type: ignore[union-attr]
    # Reward should be shaped and within [0,1].
    assert 0.0 <= float(exp["reward"]) <= 1.0

    # Verify signals are present as features (first 6 dims)
    state = exp["state"]
    next_state = exp["next_state"]
    # Feature dimension can expand when text embeddings are enabled.
    assert state.shape[0] == ranker._input_dim
    assert next_state.shape[0] == ranker._input_dim

    # Pre-state signals all 0.1 (in order)
    assert np.allclose(state[:6], np.array([0.1] * 6, dtype=np.float32))

    # Next-state signals match post_rl_signals ordering
    expected_next = np.array([float(post_rl_signals[k]) for k in RL_SIGNAL_KEYS], dtype=np.float32)
    assert np.allclose(next_state[:6], expected_next)
