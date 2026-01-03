from __future__ import annotations

import json
from pathlib import Path

from broca.config import config
from broca.config import parse_execute_whitelist_env
from broca.tools.primitive_io import ExecuteTool
from broca.tools.registry import ToolRegistry


def _execute_call(cmd: str, cwd: Path, call_id: str) -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": "EXECUTE",
            "arguments": json.dumps(
                {
                    "cmd": cmd,
                    "cwd": str(cwd),
                    "timeout": 10,
                    "env_allowlist": ["PATH"],
                }
            ),
        },
    }


def test_parse_execute_whitelist_env_precedence(monkeypatch):
    monkeypatch.setenv("BROCA_EXECUTE_COMMAND_WHITELIST", "echo")
    monkeypatch.setenv("BROCA_EXECUTE_WHITELIST", "python, sage,find,,")
    assert parse_execute_whitelist_env() == ["python", "sage", "find"]


def test_parse_execute_whitelist_env_falls_back(monkeypatch):
    monkeypatch.delenv("BROCA_EXECUTE_WHITELIST", raising=False)
    monkeypatch.setenv("BROCA_EXECUTE_COMMAND_WHITELIST", "python3,  pytest")
    assert parse_execute_whitelist_env() == ["python3", "pytest"]


def test_registry_enforces_execute_whitelist_with_three_try_budget(monkeypatch, tmp_path: Path):
    reg = ToolRegistry()
    reg.register_tool(ExecuteTool())

    monkeypatch.setattr(config.tools, "toolset", "primitive", raising=False)
    monkeypatch.setattr(config.tools, "execute_command_whitelist", ["echo"], raising=False)

    reg.start_turn(1)

    allowed_cwd = Path.cwd()

    res1 = reg.execute_tool_call(_execute_call("ls", allowed_cwd, "c1"))
    assert res1.get("_success") is False
    assert "attempt: 1/3" in res1["content"]
    assert "allowed_base_commands" in res1["content"]

    res2 = reg.execute_tool_call(_execute_call("pwd", allowed_cwd, "c2"))
    assert res2.get("_success") is False
    assert "attempt: 2/3" in res2["content"]

    res3 = reg.execute_tool_call(_execute_call("cat /etc/hosts", allowed_cwd, "c3"))
    assert res3.get("_success") is False
    assert "attempt: 3/3" in res3["content"]
    assert "retry budget exhausted" in res3["content"].lower()

    res4 = reg.execute_tool_call(_execute_call("whoami", allowed_cwd, "c4"))
    assert res4.get("_success") is False
    assert "attempt: 3/3" in res4["content"]
    assert "retry budget exhausted" in res4["content"].lower()

    ok = reg.execute_tool_call(_execute_call("echo hi", allowed_cwd, "c5"))
    assert ok.get("_success") is True


def test_registry_execute_whitelist_budget_resets_each_turn(monkeypatch, tmp_path: Path):
    reg = ToolRegistry()
    reg.register_tool(ExecuteTool())

    monkeypatch.setattr(config.tools, "toolset", "primitive", raising=False)
    monkeypatch.setattr(config.tools, "execute_command_whitelist", ["echo"], raising=False)

    allowed_cwd = Path.cwd()

    reg.start_turn(1)
    reg.execute_tool_call(_execute_call("ls", allowed_cwd, "c1"))
    reg.execute_tool_call(_execute_call("pwd", allowed_cwd, "c2"))
    reg.execute_tool_call(_execute_call("whoami", allowed_cwd, "c3"))

    reg.start_turn(2)
    res = reg.execute_tool_call(_execute_call("ls", allowed_cwd, "c4"))
    assert res.get("_success") is False
    assert "attempt: 1/3" in res["content"]


def test_execute_whitelist_blocks_pipelines_and_chained_segments(monkeypatch, tmp_path: Path):
    """
    Ensure whitelist is enforced for *every* command segment, not just the first token.
    This prevents bypasses like: python -c '...' | terraform
    """
    reg = ToolRegistry()
    reg.register_tool(ExecuteTool())

    monkeypatch.setattr(config.tools, "toolset", "primitive", raising=False)
    monkeypatch.setattr(config.tools, "execute_command_whitelist", ["python3"], raising=False)

    reg.start_turn(1)
    allowed_cwd = Path.cwd()

    # Pipe to disallowed command
    res1 = reg.execute_tool_call(_execute_call("python3 -c 'print(1)' | ls", allowed_cwd, "p1"))
    assert res1.get("_success") is False
    assert "command_not_allowed" in (res1.get("content") or "")

    # Chaining to disallowed command
    res2 = reg.execute_tool_call(_execute_call("python3 -c 'print(1)' && pwd", allowed_cwd, "p2"))
    assert res2.get("_success") is False
    assert "command_not_allowed" in (res2.get("content") or "")
