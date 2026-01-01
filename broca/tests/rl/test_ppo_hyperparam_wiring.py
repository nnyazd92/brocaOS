"""
Wiring tests for PPO hyperparameters from ranker -> PPOConfig.

Requirements from AGENTS.md:
- Property-based testing (via Hypothesis)
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

try:
    import torch  # noqa: F401

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

pytestmark = pytest.mark.skipif(not HAS_TORCH, reason="PyTorch not available")


@dataclass
class _Tool:
    name: str


@settings(
    max_examples=25,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(
    ppo_epochs=st.integers(min_value=1, max_value=8),
    clip_epsilon=st.floats(min_value=0.05, max_value=0.35, allow_nan=False, allow_infinity=False),
    entropy_coef=st.floats(min_value=0.0, max_value=0.1, allow_nan=False, allow_infinity=False),
    value_coef=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    max_grad_norm=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_ranker_hyperparams_flow_into_ppo_config(
    tmp_path,
    monkeypatch,
    ppo_epochs: int,
    clip_epsilon: float,
    entropy_coef: float,
    value_coef: float,
    max_grad_norm: float,
):
    # Ensure PPO buffer/model paths don't touch workspace data.
    monkeypatch.setenv("BROCA_RL_PPO_BUFFER_PATH", str(tmp_path / "ppo_buffer.json"))
    monkeypatch.setenv("BROCA_RL_PPO_MODEL_PATH", str(tmp_path / "policy_ppo.pt"))

    from broca.rl.ppo_online_policy import PPOOnlinePolicyRanker

    ranker = PPOOnlinePolicyRanker(
        model_path=str(tmp_path / "policy_ppo.pt"),
        force_threshold=0.0,
        suggest_threshold=0.0,
        top_k_suggest=3,
        hidden_dim=32,
        learning_rate=1e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_epsilon=clip_epsilon,
        value_coef=value_coef,
        entropy_coef=entropy_coef,
        ppo_epochs=ppo_epochs,
        max_grad_norm=max_grad_norm,
        batch_size=8,
        buffer_size=8,
    )

    ranker._ensure_policy([_Tool("A"), _Tool("B"), _Tool("C")])
    assert ranker._policy is not None

    cfg = ranker._policy.config
    assert int(cfg.ppo_epochs) == int(ppo_epochs)
    assert float(cfg.clip_epsilon) == float(clip_epsilon)
    assert float(cfg.entropy_coef) == float(entropy_coef)
    assert float(cfg.value_coef) == float(value_coef)
    assert float(cfg.max_grad_norm) == float(max_grad_norm)
