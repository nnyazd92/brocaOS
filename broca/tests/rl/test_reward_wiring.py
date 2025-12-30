import tempfile
from pathlib import Path


class _DummyGuidanceAggregator:
    def __init__(self, dissonance_reward: float, surprise_reward: float, info_gain_reward: float, coherence_reward: float):
        self._signals = {
            "dissonance_reward": dissonance_reward,
            "surprise_reward": surprise_reward,
            "information_gain_reward": info_gain_reward,
            "coherence_reward": coherence_reward,
        }

    def gather_context(self):
        return {"rl_signals": dict(self._signals)}


class _DummyToolSelectionGuidance:
    def __init__(self, dissonance_reward: float, surprise_reward: float, info_gain_reward: float, coherence_reward: float):
        self.guidance_aggregator = _DummyGuidanceAggregator(dissonance_reward, surprise_reward, info_gain_reward, coherence_reward)


def test_registry_passes_rl_signals_as_reward_override():
    """
    ToolRegistry.record_rl_outcome should pass post-tool RL signals into the ranker,
    and the ranker should compute shaped reward (signals + success/failure - latency).
    """
    from broca.rl.online_policy import OnlinePolicyRanker
    from broca.tools.registry import ToolRegistry
    from broca.tools import Tool

    with tempfile.TemporaryDirectory() as tmpdir:
        ranker = OnlinePolicyRanker(
            model_path=str(Path(tmpdir) / "model.pt"),
            buffer_path=str(Path(tmpdir) / "buffer.json"),
        )

        guidance = _DummyToolSelectionGuidance(
            dissonance_reward=1.0,
            surprise_reward=1.0,
            info_gain_reward=1.0,
            coherence_reward=1.0,
        )
        registry = ToolRegistry(online_policy_ranker=ranker, tool_selection_guidance=guidance)

        # Register a tool and ensure mapping exists
        mock_tool = type("T", (), {})()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.parameters = {"type": "object", "properties": {}}
        registry._tools["test_tool"] = mock_tool  # type: ignore[attr-defined]

        # Ensure ranker knows about the tool
        ranker.select_tool([mock_tool], {"rl_signals": {"dissonance_reward": 0.1}})

        before = len(ranker.replay_buffer)
        registry.record_rl_outcome(tool_name="test_tool", success=True, execution_time_ms=10.0, result_quality=0.5)
        assert len(ranker.replay_buffer) == before + 1

        exp = list(ranker.replay_buffer.buffer)[-1]
        # Reward should be high (success + max intrinsic, with tiny latency penalty).
        assert exp.reward > 0.7

