from __future__ import annotations

from broca.config import config as app_config
from broca.tools.registry import ToolRegistry


class _Tool:
    def __init__(self, name: str):
        self.name = name
        self.description = name
        self.parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs):
        return {"success": True, "continue_prompt": "Now continue with the task at hand."}

    def format_result(self, result):
        return "ok"


def _tool_call(name: str, call_id: str, args: str = "{}") -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": args}}


def test_respond_and_continue_forces_response_and_returns_prompt(monkeypatch):
    monkeypatch.setattr(app_config.tools, "toolset", "primitive", raising=False)

    reg = ToolRegistry()
    reg.register_tool(_Tool("READ_FILE"))
    reg.register_tool(_Tool("RESPOND_AND_CONTINUE"))

    res = reg.execute_tool_call(_tool_call("RESPOND_AND_CONTINUE", "call_rac"))
    assert res.get("_success", True) is True
    assert reg.force_final_response is True
    assert res.get("_auto_continue_prompt") == "Now continue with the task at hand."

    # While latched, tool buffer is empty (forces LLM to answer).
    assert reg.to_openai_format() == []
