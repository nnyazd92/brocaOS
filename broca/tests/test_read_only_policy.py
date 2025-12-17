
import os
import types
from unittest.mock import patch, MagicMock

from broca.tools.registry import ToolRegistry
from broca.tools.web_search import WebSearchTool

class DummyTool:
    def __init__(self, name):
        self._name = name
    @property
    def name(self):
        return self._name
    @property
    def description(self):
        return ""
    @property
    def parameters(self):
        return {"type":"object","properties":{},"required":[]}
    def execute(self, **kwargs):
        return {"success": True, "echo": kwargs}
    def format_result(self, result):
        return str(result)


def make_tool_call(name, args):
    import json
    return {"id":"call1","type":"function","function":{"name":name,"arguments":json.dumps(args)}}


def test_read_only_blocks_memory_and_terminal(monkeypatch):
    with patch.dict(os.environ, {"BROCA_TOOLS_MODE":"read_only"}, clear=False):
        registry = ToolRegistry()
        # Register dummy tools
        for n in ["store_memory","update_memory","delete_memory","link_memories","terminal","web_search"]:
            try:
                registry.register_tool(DummyTool(n))
            except Exception:
                pass
        # Start turn 1
        registry.start_turn(1)
        for n in ["store_memory","update_memory","delete_memory","link_memories","terminal"]:
            res = registry.execute_tool_call(make_tool_call(n, {}))
            assert "Blocked by read-only policy" in res.get("content",""), f"Expected block for {n}"


def test_web_search_limits(monkeypatch):
    with patch.dict(os.environ, {"BROCA_TOOLS_MODE":"read_only","BROCA_WEB_SEARCH_MAX_QUERIES":"2","BROCA_WEB_SEARCH_COOLDOWN_TURNS":"2"}, clear=False):
        registry = ToolRegistry()
        try:
            registry.register_tool(DummyTool("web_search"))
        except Exception:
            pass
        registry.start_turn(1)
        # First two searches allowed (executed via DummyTool)
        for i in range(2):
            res = registry.execute_tool_call(make_tool_call("web_search", {"query":"x","max_results":5}))
            assert "limit" not in res.get("content",""), "Should not hit limit yet"
        # Third should be limited
        res = registry.execute_tool_call(make_tool_call("web_search", {"query":"x","max_results":5}))
        assert "limit" in res.get("content",""), "Expected per-turn limit message"
        # Next turn still within cooldown
        registry.start_turn(2)
        res = registry.execute_tool_call(make_tool_call("web_search", {"query":"x"}))
        assert "cooldown" in res.get("content",""), "Expected cooldown message"
        # After cooldown
        registry.start_turn(4)
        res = registry.execute_tool_call(make_tool_call("web_search", {"query":"x"}))
        assert "cooldown" not in res.get("content",""), "Cooldown should be over"
