from __future__ import annotations

import csv
from pathlib import Path

from broca.reasoning.rl_reward_logger import RLRewardLogger
from broca.web_api import _log_tool_call_rl_reward


def test_webapi_logs_rl_row_per_tool_call_with_minimal_metrics(tmp_path):
    """
    stream_response executes tools outside ConversationSession._handle_tool_calls(),
    so we must explicitly log per-tool-call RL rows in broca.web_api.
    """
    csv_path = Path(tmp_path) / "rl_rewards.csv"
    reward_logger = RLRewardLogger(log_file=str(csv_path), enabled=True, append=True)

    tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {"name": "terminal", "arguments": "{}"},
    }

    # No world_state_aggregator => should still log via minimal metrics fallback.
    _log_tool_call_rl_reward(
        reward_logger=reward_logger,
        tool_call=tool_call,
        session_messages=[{"role": "user", "content": "hi"}],
        world_state_aggregator=None,
    )

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["context"].startswith("tool_call_terminal_call_123")


