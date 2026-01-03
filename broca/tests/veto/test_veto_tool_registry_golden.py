from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pytest

import broca.tools.registry as registry_mod
from broca.tools.registry import ToolRegistry
from broca.veto.guard import VetoDecision


@dataclass
class _DummyTool:
    # Use a primitive-visible tool name to avoid toolset visibility blocks in default config.
    name: str = "READ_FILE"

    @property
    def description(self) -> str:
        return "Dummy tool for veto golden trace tests."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return {"success": True, "ok": True}

    def format_result(self, result: Dict[str, Any]) -> str:
        return json.dumps(result, sort_keys=True)


class _AlwaysVetoGuard:
    def build_time_slice(self, **kwargs: Any):
        # shape doesn't matter; ToolRegistry only passes it through to check()
        return [0.0] * 12

    def check(self, *, x_t, reason: str, kappa_last: float, kappa_integrated: float) -> VetoDecision:
        return VetoDecision(
            veto=True,
            reason=reason,
            threshold=1.0,
            kappa_integrated=0.0,
            kappa_last=1.0,
            debug={"persist_n": 8, "persist_m": 5, "forced": True},
        )


def test_tool_veto_golden_trace_payload_shape(monkeypatch):
    # Force the registry to veto deterministically.
    monkeypatch.setattr(registry_mod, "get_veto_guard", lambda: _AlwaysVetoGuard())

    reg = ToolRegistry()
    # Avoid governance preflight blocking (this test targets learned veto output shape).
    reg._governance_engine = None  # type: ignore[attr-defined]
    reg.register_tool(_DummyTool())

    tool_call = {
        "id": "call_veto_1",
        "type": "function",
        "function": {"name": "READ_FILE", "arguments": "{}"},
    }
    res = reg.execute_tool_call(tool_call)
    assert isinstance(res, dict)
    assert res.get("_veto") is True
    assert res.get("_success") is False
    payload = res.get("_veto_payload")
    assert isinstance(payload, dict)

    # Golden: payload has stable keys (values can change over time).
    stable = {k: payload.get(k) for k in sorted(payload.keys())}
    stable_keys = sorted(stable.keys())
    assert "tool_call_id" in stable_keys
    assert "tool_name" in stable_keys
    assert "kappa_integrated" in stable_keys
    assert "threshold" in stable_keys

    golden_file = Path(__file__).parent.parent / "fixtures" / "golden_traces" / "veto" / "vetoed_tool_call.json"
    golden_file.parent.mkdir(parents=True, exist_ok=True)

    # Store only keys and a minimal subset of fields to keep the golden stable.
    expected = {
        "tool_call_id": payload.get("tool_call_id"),
        "tool_name": payload.get("tool_name"),
        "source_of_conflict": payload.get("source_of_conflict"),
        "kappa": payload.get("kappa"),
        "kappa_integrated": payload.get("kappa_integrated"),
        "threshold": payload.get("threshold"),
        "has_debug": isinstance(payload.get("debug"), dict),
    }

    if golden_file.exists():
        golden = json.loads(golden_file.read_text(encoding="utf-8"))
        assert expected == golden
    else:
        golden_file.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        pytest.skip("Golden trace created - run again to verify")


def test_tool_registry_veto_guard_failure_is_fail_open(monkeypatch):
    # If veto guard is broken, tool execution must proceed (fail-open).
    def _boom():
        raise RuntimeError("veto_guard_failed")

    monkeypatch.setattr(registry_mod, "get_veto_guard", _boom)

    reg = ToolRegistry()
    reg._governance_engine = None  # type: ignore[attr-defined]
    reg.register_tool(_DummyTool())
    tool_call = {
        "id": "call_ok_1",
        "type": "function",
        "function": {"name": "READ_FILE", "arguments": "{}"},
    }
    res = reg.execute_tool_call(tool_call)
    assert res.get("name") == "READ_FILE"
    assert res.get("_veto") is not True
    # Dummy tool returns success=True, so formatted result should be JSON with ok.
    assert isinstance(res.get("content"), str)


