import json

from broca.tools.registry import ToolRegistry


class _Tool:
    def __init__(self, name: str):
        self._name = name
        self.executed = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "mock"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"param": {"type": "string"}}, "required": ["param"]}

    def execute(self, **kwargs):
        self.executed += 1
        return {"success": True, "echo": kwargs}

    def format_result(self, result: dict) -> str:
        return json.dumps(result)


class _Sel:
    def __init__(self, tool_name: str):
        self.mode = "forced"
        self.tool_name = tool_name
        self.confidence = 0.9
        self.reason = "forced"
        self.alternatives = []
        self.all_scores = {tool_name: 0.9}


def test_forced_mode_blocks_disallowed_tool_call():
    registry = ToolRegistry()
    terminal = _Tool("terminal")
    reasoning = _Tool("reasoning")
    registry.register_tool(terminal)
    registry.register_tool(reasoning)

    # Simulate tool schema formatting under a forced RL selection.
    registry.to_openai_format(context={}, rl_selection=_Sel("reasoning"))

    # LLM improperly calls terminal anyway.
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "terminal", "arguments": json.dumps({"param": "x"})},
    }
    res = registry.execute_tool_call(tool_call)

    assert res.get("_success") is False
    # Forced mode implies the allowed-tool buffer is a single tool; block is enforced at execution time.
    assert "blocked" in (res.get("content") or "").lower()
    assert terminal.executed == 0
    assert reasoning.executed == 0
