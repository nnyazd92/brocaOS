from __future__ import annotations

from broca.config import config as app_config
from broca.tools.registry import ToolRegistry


class _Tool:
    def __init__(self, name: str):
        self.name = name
        self.description = name
        self.parameters = {"type": "object", "properties": {}}
        self.calls = 0

    def execute(self, **kwargs):
        self.calls += 1
        return {"success": True, "result": self.name}

    def format_result(self, result):
        return str(result.get("result", ""))


class _Selection:
    def __init__(self):
        self.tool_name = "READ_FILE"
        self.mode = "forced"
        self.reason = "Forced exploration (p=1.0) - collect on-policy data"
        self.confidence = 1.0
        self.score = 1.0
        self.alternatives = []
        self.all_scores = {}


class _Ranker:
    def __init__(self):
        self.select_calls = 0

    def select_tool(self, tools, ctx):
        self.select_calls += 1
        return _Selection()

    def record_outcome(self, **kwargs):
        return None


def _tool_call(name: str, call_id: str) -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": "{}"}}


def test_done_disables_tools_until_next_turn(monkeypatch):
    monkeypatch.setattr(app_config.tools, "toolset", "primitive", raising=False)
    monkeypatch.setattr(app_config.rl, "enabled", True, raising=False)

    reg = ToolRegistry()
    read = _Tool("READ_FILE")
    done = _Tool("DONE")
    solve = _Tool("SOLVE")
    reg.register_tool(read)
    reg.register_tool(done)
    reg.register_tool(solve)

    ranker = _Ranker()
    reg.set_online_policy_ranker(ranker)

    # Tools are available initially.
    tools_before = reg.to_openai_format()
    assert {t["function"]["name"] for t in tools_before} == {"READ_FILE", "DONE", "SOLVE"}

    # Executing DONE latches the force-final state.
    done_res = reg.execute_tool_call(_tool_call("DONE", "call_done"))
    assert done_res.get("_success", True) is True
    assert reg.force_final_response is True

    # While latched, RL selection is disabled and the tool buffer is empty.
    sel = reg.get_rl_selection(context={"rl_signals": {"composite_reward": 0.1}})
    assert sel is None
    assert ranker.select_calls == 0

    tools_after = reg.to_openai_format()
    assert tools_after == []

    # While latched, tool execution is blocked (even if a model emits tool_calls anyway).
    blocked = reg.execute_tool_call(_tool_call("SOLVE", "call_solve"))
    assert blocked.get("_success") is False
    assert blocked.get("_error") == "force_final_response"
    assert solve.calls == 0

    # Next user turn clears DONE latch.
    reg.start_turn(2)
    assert reg.force_final_response is False
    tools_reset = reg.to_openai_format()
    assert {t["function"]["name"] for t in tools_reset} == {"READ_FILE", "DONE", "SOLVE"}
