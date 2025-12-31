from broca.tools.registry import ToolRegistry


class _Tool:
    def __init__(self, name: str):
        self.name = name
        self.description = name
        self.parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs):
        return {"success": True, "result": self.name}

    def format_result(self, result):
        return str(result.get("result", ""))


class _Selection:
    def __init__(self, tool_name: str, *, mode: str, reason: str):
        self.tool_name = tool_name
        self.mode = mode
        self.reason = reason
        self.confidence = 0.1
        self.score = 0.1
        self.alternatives = []
        self.all_scores = {}


class _Ranker:
    def __init__(self):
        self.select_calls = 0
        self.outcomes = []

    def select_tool(self, tools, ctx):
        self.select_calls += 1
        # First call: forced exploration.
        if self.select_calls == 1:
            return _Selection("planning", mode="forced", reason="Forced exploration (p=1.0) - collect on-policy data")
        # Subsequent calls would be fallback, but sticky should override.
        return _Selection("terminal", mode="fallback", reason="low confidence")

    def record_outcome(self, **kwargs):
        self.outcomes.append(kwargs)


def _tool_call(name: str, call_id: str) -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": "{}"}}


def test_sticky_forced_exploration_persists_until_forced_tool_executes():
    reg = ToolRegistry()
    reg.register_tool(_Tool("planning"))
    reg.register_tool(_Tool("terminal"))
    reg.register_tool(_Tool("environment_access"))

    ranker = _Ranker()
    reg.set_online_policy_ranker(ranker)

    sel1 = reg.get_rl_selection(context={"rl_signals": {"composite_reward": 0.1}})
    assert sel1.mode == "forced"
    assert "Forced exploration" in sel1.reason
    assert ranker.select_calls == 1

    # Format tools for the forced selection (allowed buffer becomes ["planning"])
    reg.to_openai_format(context={}, rl_selection=sel1)

    # Noncompliant tool call: should be blocked and sticky should remain.
    blocked = reg.execute_tool_call(_tool_call("environment_access", "call_bad"))
    assert blocked.get("_success") is False

    sel2 = reg.get_rl_selection(context={"rl_signals": {"composite_reward": 0.1}})
    assert sel2.tool_name == "planning"
    assert sel2.mode == "forced"
    # Sticky should prevent a second ranker.select_tool call.
    assert ranker.select_calls == 1

    # Now execute the forced tool; this should clear sticky.
    reg.to_openai_format(context={}, rl_selection=sel2)
    ok = reg.execute_tool_call(_tool_call("planning", "call_ok"))
    assert ok.get("_success", True) is True

    # Next selection should consult the ranker again.
    _ = reg.get_rl_selection(context={"rl_signals": {"composite_reward": 0.1}})
    assert ranker.select_calls == 2
