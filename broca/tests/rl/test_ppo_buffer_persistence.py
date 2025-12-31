import logging


class _Tool:
    def __init__(self, name: str) -> None:
        self.name = name


def test_ppo_buffer_persists_across_ranker_restart(tmp_path, monkeypatch, caplog):
    from broca.rl import ppo_online_policy
    from broca.rl.ppo_online_policy import PPOOnlinePolicyRanker

    caplog.set_level(logging.INFO)
    ppo_online_policy.tool_selection_logger = logging.getLogger("test.ppo.buffer.persist")
    ppo_online_policy.tool_selection_logger.setLevel(logging.INFO)
    ppo_online_policy.tool_selection_logger.propagate = True

    buffer_path = tmp_path / "ppo_buffer.json"

    tools = [_Tool("a"), _Tool("b")]

    r1 = PPOOnlinePolicyRanker(
        model_path=str(tmp_path / "policy.pt"),
        force_threshold=0.0,  # always forced so record_outcome is allowed
        suggest_threshold=0.0,
        top_k_suggest=0,
        batch_size=64,
        buffer_size=2048,
    )
    r1._buffer_path = buffer_path

    sel = r1.select_tool(tools, context={"rl_signals": {"composite_reward": 0.1}})
    assert sel.mode == "forced"
    r1.record_outcome(
        tool_name=sel.tool_name,
        context={"rl_signals": {"composite_reward": 0.1}},
        next_context={"rl_signals": {"composite_reward": 0.2}},
        success=True,
        execution_time_ms=1.0,
        result_quality=0.5,
    )
    assert buffer_path.exists()

    r2 = PPOOnlinePolicyRanker(
        model_path=str(tmp_path / "policy.pt"),
        force_threshold=0.0,
        suggest_threshold=0.0,
        top_k_suggest=0,
        batch_size=64,
        buffer_size=2048,
    )
    r2._buffer_path = buffer_path
    _ = r2.select_tool(tools, context={"rl_signals": {"composite_reward": 0.1}})
    assert r2._policy is not None
    with r2._policy.buffer_lock:
        assert len(r2._policy.buffer) >= 1

