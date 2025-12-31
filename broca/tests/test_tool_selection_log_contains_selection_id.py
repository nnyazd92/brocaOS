import importlib
import json
import logging

from broca.tools.registry import ToolRegistry


class _MockTool:
    def __init__(self, name: str):
        self._name = name

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
        return {"success": True, "echo": kwargs}

    def format_result(self, result: dict) -> str:
        return json.dumps(result)


class _Sel:
    def __init__(self):
        self.mode = "suggested"
        self.tool_name = "terminal"
        self.confidence = 0.42
        self.reason = "test"
        self.alternatives = [("web_search", 0.2)]
        self.all_scores = {"terminal": 0.42, "web_search": 0.2}


def test_tool_selection_log_includes_selection_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Ensure the dedicated logger points at tmp_path/data/rl/tool_selection.log
    import broca.rl.tool_selection_logging as tsl

    tsl = importlib.reload(tsl)
    logger = tsl.get_tool_selection_logger()

    registry = ToolRegistry()
    registry.register_tool(_MockTool("terminal"))
    registry.register_tool(_MockTool("web_search"))

    # Simulate building tool schema list with an RL selection.
    registry.to_openai_format(context={}, rl_selection=_Sel())

    tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {"name": "terminal", "arguments": json.dumps({"param": "x"})},
    }
    registry.execute_tool_call(tool_call)

    for h in logger.handlers:
        try:
            h.flush()
        except Exception:
            pass

    text = (tmp_path / "data" / "rl" / "tool_selection.log").read_text(encoding="utf-8")
    assert "selection_id=" in text
    assert "TOOL_CALL_START" in text
    assert "TOOL_CALL_DONE" in text

