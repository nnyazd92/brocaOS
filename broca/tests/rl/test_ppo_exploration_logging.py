import logging


class _Tool:
    def __init__(self, name: str) -> None:
        self.name = name


def test_ppo_logs_exploration_check_when_not_triggered(tmp_path, caplog, monkeypatch):
    from broca.rl import ppo_online_policy
    from broca.rl.ppo_online_policy import PPOOnlinePolicyRanker
    from broca.config import config as _config

    caplog.set_level(logging.INFO)
    ppo_online_policy.tool_selection_logger = logging.getLogger("test.ppo.explore")
    ppo_online_policy.tool_selection_logger.setLevel(logging.INFO)
    ppo_online_policy.tool_selection_logger.propagate = True

    # Ensure exploration doesn't trigger (roll > p).
    monkeypatch.setattr(ppo_online_policy.random, "random", lambda: 0.999)
    monkeypatch.setattr(_config.rl, "ppo_forced_exploration_prob", 0.05)
    monkeypatch.setattr(_config.rl, "ppo_forced_exploration_min_prob", 0.0)
    monkeypatch.setattr(_config.rl, "ppo_forced_exploration_decay", 1.0)

    tools = [_Tool("a"), _Tool("b")]
    ranker = PPOOnlinePolicyRanker(
        model_path=str(tmp_path / "policy.pt"),
        force_threshold=1.0,
        suggest_threshold=1.0,
        top_k_suggest=1,
        batch_size=2,
        buffer_size=2,
    )

    ranker.select_tool(tools, context={"rl_signals": {"composite_reward": 0.1}})

    logged = "\n".join(r.message for r in caplog.records)
    assert "PPO_EXPLORE_CHECK" in logged
    assert "triggered=False" in logged

