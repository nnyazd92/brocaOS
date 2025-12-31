import logging


class _Tool:
    def __init__(self, name: str) -> None:
        self.name = name


def test_ppo_trains_when_rollout_buffer_fills(tmp_path, caplog):
    """
    Regression: PPOOnlinePolicyRanker collects on-policy (forced-mode) experiences,
    and PPOPolicy trains once buffer_size is reached.

    This also asserts the visibility logs exist (PPO_BUFFER / PPO_UPDATE).
    """
    from broca.rl import ppo_online_policy
    from broca.rl.ppo_online_policy import PPOOnlinePolicyRanker

    # Capture PPO_* visibility logs (tool_selection_logger uses propagate=False by default).
    caplog.set_level(logging.INFO)
    ppo_online_policy.tool_selection_logger = logging.getLogger("test.ppo.visibility")
    ppo_online_policy.tool_selection_logger.setLevel(logging.INFO)
    ppo_online_policy.tool_selection_logger.propagate = True

    tools = [_Tool("a"), _Tool("b")]
    ranker = PPOOnlinePolicyRanker(
        model_path=str(tmp_path / "policy.pt"),
        force_threshold=0.0,  # always force
        suggest_threshold=0.0,
        top_k_suggest=0,
        batch_size=2,
        buffer_size=2,
    )

    sel = ranker.select_tool(tools, context={"rl_signals": {"composite_reward": 0.1}})
    assert sel.mode == "forced"

    # Two matching outcomes should fill the rollout buffer and trigger a PPO training step.
    for _ in range(2):
        ranker.record_outcome(
            tool_name=sel.tool_name,
            context={"rl_signals": {"composite_reward": 0.1}},
            next_context={"rl_signals": {"composite_reward": 0.2}},
            success=True,
            execution_time_ms=1.0,
            result_quality=0.5,
        )

    assert ranker._policy is not None
    assert ranker._policy.training_step >= 1

    logged = "\n".join(r.message for r in caplog.records)
    assert "PPO_BUFFER" in logged
    assert "PPO_UPDATE" in logged
