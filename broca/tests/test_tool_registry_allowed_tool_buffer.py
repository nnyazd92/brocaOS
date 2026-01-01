from broca.config import config
from broca.tools.registry import ToolRegistry


class _Tool:
    def __init__(self, name: str):
        self.name = name
        self.description = name
        self.parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs):
        return {"success": True, "result": self.name}


class _Sel:
    def __init__(self, mode: str, tool_name: str, alternatives=None):
        self.mode = mode
        self.tool_name = tool_name
        self.alternatives = alternatives or []
        self.confidence = 0.5
        self.score = 0.5
        self.reason = "test"
        self.all_scores = {}


def _tool_call(name: str, call_id: str = "call_1") -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": "{}"}}


def test_registry_blocks_tool_not_in_allowed_buffer_suggested_mode(monkeypatch):
    # This test uses synthetic tool names; ensure the registry is in legacy toolset mode.
    monkeypatch.setattr(config.tools, "toolset", "legacy", raising=False)
    reg = ToolRegistry()
    reg.register_tool(_Tool("a"))
    reg.register_tool(_Tool("b"))
    reg.register_tool(_Tool("c"))

    # Suggested mode filters the advertised tools to a small buffer.
    sel = _Sel("suggested", "a", alternatives=[("b", 0.4)])
    reg.to_openai_format(context={}, rl_selection=sel)

    blocked = reg.execute_tool_call(_tool_call("c"))
    assert blocked["_success"] is False
    assert "allowed tools" in blocked["content"].lower()


def test_registry_allows_tool_in_allowed_buffer_suggested_mode(monkeypatch):
    # This test uses synthetic tool names; ensure the registry is in legacy toolset mode.
    monkeypatch.setattr(config.tools, "toolset", "legacy", raising=False)
    reg = ToolRegistry()
    reg.register_tool(_Tool("a"))
    reg.register_tool(_Tool("b"))
    reg.register_tool(_Tool("c"))

    sel = _Sel("suggested", "a", alternatives=[("b", 0.4)])
    reg.to_openai_format(context={}, rl_selection=sel)

    ok = reg.execute_tool_call(_tool_call("b"))
    assert ok.get("_success", True) is True
    assert ok["name"] == "b"
