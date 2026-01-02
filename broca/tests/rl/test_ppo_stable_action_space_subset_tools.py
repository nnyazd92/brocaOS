from __future__ import annotations

import logging


class _Tool:
    def __init__(self, name: str) -> None:
        self.name = name


def test_ppo_does_not_reinit_or_force_unavailable_tool_when_tools_are_subset(monkeypatch, tmp_path, caplog):
    """
    Regression: tool filtering (subset of tools) must not reset PPO policy/buffer and must
    never force-select an unavailable tool.
    """
    from broca.config import config as cfg
    from broca.rl import ppo_online_policy
    from broca.rl.ppo_online_policy import PPOOnlinePolicyRanker

    # Force exploration always triggers so we exercise the forced branch.
    monkeypatch.setattr(cfg.rl, "ppo_forced_exploration_prob", 1.0, raising=False)
    monkeypatch.setattr(cfg.rl, "ppo_forced_exploration_mode", "uniform", raising=False)

    caplog.set_level(logging.INFO)
    ppo_online_policy.tool_selection_logger = logging.getLogger("test.ppo.subset")
    ppo_online_policy.tool_selection_logger.setLevel(logging.INFO)
    ppo_online_policy.tool_selection_logger.propagate = True

    tools_full = [_Tool("a"), _Tool("b")]
    tools_subset = [_Tool("a")]

    ranker = PPOOnlinePolicyRanker(model_path=str(tmp_path / "policy.pt"), buffer_size=8, batch_size=2)

    sel1 = ranker.select_tool(tools_full, context={"rl_signals": {"composite_reward": 0.1}})
    assert sel1.mode == "forced"
    assert sel1.tool_name in {"a", "b"}
    policy_obj = ranker._policy
    mapping_keys = set(ranker._tool_to_idx.keys())
    assert mapping_keys == {"a", "b"}

    # Now provide a subset; this must not rebuild the policy/mapping.
    sel2 = ranker.select_tool(tools_subset, context={"rl_signals": {"composite_reward": 0.1}})
    assert sel2.mode == "forced"
    assert sel2.tool_name == "a"
    assert ranker._policy is policy_obj
    assert set(ranker._tool_to_idx.keys()) == {"a", "b"}


