import importlib
import json
from pathlib import Path

import numpy as np


class _Tool:
    def __init__(self, name: str):
        self.name = name


def _write_experiences_jsonl(path: Path, *, tool_name: str, n: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rl_signals = {
        "dissonance_reward": 0.2,
        "surprise_reward": 0.2,
        "curiosity_reward": 0.2,
        "information_gain_reward": 0.2,
        "coherence_reward": 0.2,
        "exploration_balance": 0.5,
        "composite_reward": 1.0,
    }
    pre_ctx = {"rl_signals": rl_signals}
    post_ctx = {"rl_signals": rl_signals}
    with path.open("w", encoding="utf-8") as f:
        for i in range(n):
            f.write(
                json.dumps(
                    {
                        "uid": f"u{i}",
                        "timestamp": "2025-01-01T00:00:00Z",
                        "tool_name": tool_name,
                        "success": True,
                        "execution_time_ms": 5.0,
                        "epistemic": {"evidence_strength": 0.8},
                        "pre_context": pre_ctx,
                        "post_context": post_ctx,
                    }
                )
                + "\n"
            )


def test_ppo_bc_warm_start_biases_policy_to_logged_tool(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Create a context-rich experiences file that overwhelmingly uses "terminal".
    _write_experiences_jsonl(tmp_path / "data" / "rl" / "experiences.jsonl", tool_name="terminal", n=128)

    # Patch runtime config values directly (config reads env at import).
    import broca.config as config_module

    old_text_dim = getattr(config_module.config.rl, "text_embedding_dim", 0)
    old_text_fields = getattr(config_module.config.rl, "text_embedding_fields", "")
    old_text_max_chars = getattr(config_module.config.rl, "text_embedding_max_chars", 2000)

    config_module.config.rl.ppo_bc_warm_start_enabled = True
    config_module.config.rl.ppo_bc_epochs = 3
    config_module.config.rl.ppo_bc_batch_size = 64
    config_module.config.rl.ppo_bc_max_samples = 256
    config_module.config.rl.ppo_bc_value_coef = 0.25
    config_module.config.rl.ppo_bc_entropy_coef = 0.0
    config_module.config.rl.ppo_forced_exploration_prob = 0.0
    config_module.config.rl.text_embedding_dim = 8
    config_module.config.rl.text_embedding_fields = "user_prompt,last_assistant"
    config_module.config.rl.text_embedding_max_chars = 500

    try:
        import broca.rl.ppo_online_policy as ppo_online_policy

        importlib.reload(ppo_online_policy)

        ranker = ppo_online_policy.PPOOnlinePolicyRanker(model_path=str(tmp_path / "policy_ppo.pt"))
        tools = [_Tool("terminal"), _Tool("web_search")]

        # Trigger initialization + warm-start.
        selection = ranker.select_tool(tools, context={})
        assert selection.tool_name in {"terminal", "web_search"}

        policy = ranker._policy
        assert policy is not None
        assert getattr(policy, "bc_step", 0) > 0
        assert ranker._bc_warm_started_for_mapping is not None

        state = ranker._extract_features({"text_features": {"user_prompt": "terminal pls", "last_assistant": ""}})
        probs = policy.predict_proba(state).astype(np.float32)
        terminal_idx = ranker._tool_to_idx["terminal"]
        web_idx = ranker._tool_to_idx["web_search"]
        assert float(probs[terminal_idx]) > float(probs[web_idx])
        # With 2 actions, uniform is ~0.5; warm-start should push above chance.
        assert float(probs[terminal_idx]) > 0.52
    finally:
        config_module.config.rl.text_embedding_dim = old_text_dim
        config_module.config.rl.text_embedding_fields = old_text_fields
        config_module.config.rl.text_embedding_max_chars = old_text_max_chars


def test_ppo_forced_exploration_returns_forced_mode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    import broca.config as config_module

    config_module.config.rl.ppo_bc_warm_start_enabled = False
    config_module.config.rl.ppo_forced_exploration_prob = 1.0

    import broca.rl.ppo_online_policy as ppo_online_policy

    importlib.reload(ppo_online_policy)

    ranker = ppo_online_policy.PPOOnlinePolicyRanker(model_path=str(tmp_path / "policy_ppo.pt"))
    tools = [_Tool("terminal"), _Tool("web_search")]

    sel = ranker.select_tool(tools, context={})
    assert sel.mode == "forced"
    assert "Forced exploration" in sel.reason
