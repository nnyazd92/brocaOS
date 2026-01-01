from __future__ import annotations

from unittest.mock import Mock

from broca.tools.primitive_toolset import register_primitive_toolset
from broca.tools.registry import ToolRegistry


def test_primitive_toolset_registers_explicit_tools_without_terminal():
    registry = ToolRegistry()
    # Pass a lightweight mock so memory macros are registered without needing a full DB/FAISS setup.
    register_primitive_toolset(registry, memory_manager=Mock())

    tool_names = {t.name for t in registry.list_tools()}
    assert "terminal" not in tool_names

    # Core I/O primitives
    for required in ["READ_FILE", "WRITE_FILE", "APPEND_FILE", "PATCH_FILE", "LIST_DIR", "STAT_PATH", "EXECUTE"]:
        assert required in tool_names

    # Cognition markers
    for required in ["PLAN", "SOLVE", "VERIFY", "INTERPRET"]:
        assert required in tool_names

    # Memory extras (macro)
    for required in ["MEMORY_UPDATE", "MEMORY_RELATED"]:
        assert required in tool_names
