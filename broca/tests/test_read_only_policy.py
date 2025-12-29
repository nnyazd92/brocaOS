
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


def test_web_search_no_restrictions(monkeypatch):
    """
    Test that web_search has no rate limiting restrictions.
    
    Rationale: Web search now uses browser-based search (no API costs),
    so restrictions are no longer needed. This test verifies unlimited searches work.
    """
    with patch.dict(os.environ, {"BROCA_TOOLS_MODE":"read_only"}, clear=False):
        registry = ToolRegistry()
        try:
            registry.register_tool(DummyTool("web_search"))
        except Exception:
            pass
        registry.start_turn(1)
        # Should be able to make unlimited searches without restrictions
        for i in range(10):
            res = registry.execute_tool_call(make_tool_call("web_search", {"query":"x","max_results":20}))
            # Should not hit any limits or cooldowns
            assert "limit" not in res.get("content","").lower(), f"Search {i+1} should not be limited"
            assert "cooldown" not in res.get("content","").lower(), f"Search {i+1} should not be in cooldown"
            # max_results should not be artificially capped
            assert "20" in str(res.get("content","")) or "success" in str(res.get("content","")).lower(), "max_results should not be capped"
        
        # Should work immediately in next turn (no cooldown)
        registry.start_turn(2)
        res = registry.execute_tool_call(make_tool_call("web_search", {"query":"x","max_results":50}))
        assert "cooldown" not in res.get("content","").lower(), "Should work immediately in next turn"
        assert "limit" not in res.get("content","").lower(), "Should not be limited"
