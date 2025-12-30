import numpy as np


def test_ppo_select_action_has_entropy_and_logprob():
    from broca.rl.ppo_policy import PPOPolicy, PPOConfig

    policy = PPOPolicy(PPOConfig(input_dim=16, output_dim=5))
    state = np.zeros(16, dtype=np.float32)
    action, value, info = policy.select_action(state, explore=False)

    assert isinstance(action, int)
    assert isinstance(value, float)
    assert "log_prob" in info and isinstance(info["log_prob"], float)
    assert "entropy" in info and isinstance(info["entropy"], float)
    assert np.isfinite(info["log_prob"])
    assert np.isfinite(info["entropy"])


def test_ppo_store_experience_recomputes_log_prob_for_given_action():
    from broca.rl.ppo_policy import PPOPolicy, PPOConfig

    policy = PPOPolicy(PPOConfig(input_dim=16, output_dim=3))
    state = np.random.randn(16).astype(np.float32)
    action = 2

    policy.store_experience(
        state=state,
        action=action,
        reward=0.5,
        next_state=None,
        info={"log_prob": 999.0, "value": 999.0, "done": True},  # should be ignored
    )

    exp = policy.buffer[-1]
    lp_expected, _, _ = policy.evaluate_actions(np.array([state]), np.array([action]))
    assert abs(float(exp["log_prob"]) - float(lp_expected[0])) < 1e-6
