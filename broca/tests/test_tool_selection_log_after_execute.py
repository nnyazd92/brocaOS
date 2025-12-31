import importlib
import json
import logging

from broca.tools.registry import ToolRegistry


class MockTool:
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


def test_tool_selection_log_appends_per_tool_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Ensure logger initialization is bound to this tmp cwd.
    import broca.rl.tool_selection_logging as tsl

    tsl = importlib.reload(tsl)

    logger = logging.getLogger("broca.rl.tool_selection")
    for handler in list(logger.handlers):
        try:
            handler.close()
        except Exception:
            pass
    logger.handlers[:] = []
    tsl = importlib.reload(tsl)
    tsl.get_tool_selection_logger()

    registry = ToolRegistry()
    registry.register_tool(MockTool("test_tool"))

    tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {"name": "test_tool", "arguments": json.dumps({"param": "x"})},
    }

    registry.execute_tool_call(tool_call)

    logger = logging.getLogger("broca.rl.tool_selection")
    for handler in logger.handlers:
        try:
            handler.flush()
        except Exception:
            pass

    log_path = tmp_path / "data" / "rl" / "tool_selection.log"
    text = log_path.read_text(encoding="utf-8")
    assert "TOOL_CALL_START" in text
    assert "TOOL_CALL_DONE" in text
    assert "tool_call_id=call_123" in text
