from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

import broca.tools.registry as registry_mod
from broca.config import config as app_config
from broca.tools.registry import ToolRegistry
from broca.veto.guard import VetoDecision


@dataclass
class _AlwaysVetoGuard:
    def build_time_slice(self, **kwargs: Any):
        return [0.0] * 12

    def check(self, *, x_t, reason: str, kappa_last: float, kappa_integrated: float) -> VetoDecision:
        return VetoDecision(
            veto=True,
            reason=reason,
            threshold=1.0,
            kappa_integrated=float(kappa_integrated),
            kappa_last=float(kappa_last),
            debug={"forced": True, "persist_n": 8, "persist_m": 5},
        )


class _CountTool:
    name = "READ_FILE"

    @property
    def description(self) -> str:
        return "Count tool executions"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def __init__(self) -> None:
        self.exec_count = 0

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        self.exec_count += 1
        return {"success": True, "count": self.exec_count}

    def format_result(self, result: Dict[str, Any]) -> str:
        return json.dumps(result, sort_keys=True)


def _tool_call(call_id: str) -> Dict[str, Any]:
    return {"id": call_id, "type": "function", "function": {"name": "READ_FILE", "arguments": "{}"}}


def test_max_consecutive_veto_failsafe_allows_execution(monkeypatch):
    # Force veto on every call.
    monkeypatch.setattr(registry_mod, "get_veto_guard", lambda: _AlwaysVetoGuard())

    # Enable failsafe: after 2 consecutive vetoes in a turn, fail-open on the 3rd.
    monkeypatch.setattr(app_config.veto, "max_consecutive_vetos", 2, raising=False)

    reg = ToolRegistry()
    reg._governance_engine = None  # type: ignore[attr-defined]
    reg.start_turn(1)

    tool = _CountTool()
    reg.register_tool(tool)

    # First two calls are vetoed.
    r1 = reg.execute_tool_call(_tool_call("c1"))
    r2 = reg.execute_tool_call(_tool_call("c2"))
    assert r1.get("_veto") is True and r1.get("_success") is False
    assert r2.get("_veto") is True and r2.get("_success") is False
    assert tool.exec_count == 0

    # Third call: failsafe triggers -> tool executes (no veto).
    r3 = reg.execute_tool_call(_tool_call("c3"))
    assert r3.get("_veto") is not True
    assert r3.get("name") == "READ_FILE"
    assert r3.get("_success") is True
    assert tool.exec_count == 1

    # Next call should be vetoed again (counter was reset by failsafe).
    r4 = reg.execute_tool_call(_tool_call("c4"))
    assert r4.get("_veto") is True and r4.get("_success") is False
    assert tool.exec_count == 1


def test_veto_failsafe_resets_each_turn(monkeypatch):
    monkeypatch.setattr(registry_mod, "get_veto_guard", lambda: _AlwaysVetoGuard())
    monkeypatch.setattr(app_config.veto, "max_consecutive_vetos", 1, raising=False)

    reg = ToolRegistry()
    reg._governance_engine = None  # type: ignore[attr-defined]
    tool = _CountTool()
    reg.register_tool(tool)

    reg.start_turn(1)
    _ = reg.execute_tool_call(_tool_call("t1_c1"))  # veto
    r2 = reg.execute_tool_call(_tool_call("t1_c2"))  # fail-open executes (max=1)
    assert r2.get("_success") is True
    assert tool.exec_count == 1

    # New turn should start veto streak fresh.
    reg.start_turn(2)
    r3 = reg.execute_tool_call(_tool_call("t2_c1"))
    assert r3.get("_veto") is True and r3.get("_success") is False


