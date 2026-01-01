from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from broca.tools.registry import ToolRegistry


class _MockTool:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "x"

    @property
    def parameters(self):
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs):
        return {"success": True}

    def format_result(self, result):
        return "ok"


def test_registry_hides_legacy_tools_in_primitive_toolset(monkeypatch):
    monkeypatch.setenv("BROCA_TOOLSET", "primitive")

    registry = ToolRegistry()
    registry.register_tool(_MockTool("READ_FILE"))
    registry.register_tool(_MockTool("environment_access"))
    registry.register_tool(_MockTool("terminal"))

    tools = registry.to_openai_format()
    names = [t["function"]["name"] for t in tools]

    assert "READ_FILE" in names
    assert "environment_access" not in names
    assert "terminal" not in names


def test_registry_blocks_execution_of_hidden_tool_in_primitive_toolset(monkeypatch):
    monkeypatch.setenv("BROCA_TOOLSET", "primitive")

    registry = ToolRegistry()
    registry.register_tool(_MockTool("READ_FILE"))
    registry.register_tool(_MockTool("environment_access"))

    # Simulate a provider emitting a hidden tool call anyway.
    result = registry.execute_tool_call(
        {"id": "x", "type": "function", "function": {"name": "environment_access", "arguments": "{}"}}
    )
    assert result.get("_success") is False
    assert "blocked by toolset policy" in (result.get("content") or "").lower()

