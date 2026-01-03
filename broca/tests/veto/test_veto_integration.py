from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

import broca.tools.registry as registry_mod
from broca.tools.registry import ToolRegistry
from broca.veto.guard import VetoDecision


@dataclass
class _DummyTool:
    name: str = "READ_FILE"

    @property
    def description(self) -> str:
        return "Dummy tool for veto integration tests."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return {"success": True, "ok": True}

    def format_result(self, result: Dict[str, Any]) -> str:
        return json.dumps(result, sort_keys=True)


class _MockVetoGuard:
    def __init__(self, should_veto: bool = True):
        self.should_veto = should_veto

    def build_time_slice(self, **kwargs: Any):
        return [0.0] * 12

    def check(self, *, x_t, reason: str, kappa_last: float, kappa_integrated: float) -> VetoDecision:
        return VetoDecision(
            veto=self.should_veto,
            reason=reason,
            threshold=0.5,
            kappa_integrated=0.1 if self.should_veto else 0.9,
            kappa_last=0.1 if self.should_veto else 0.9,
            debug={"forced": True},
        )


class _MockRegistry(ToolRegistry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rl_outcomes: List[Dict[str, Any]] = []

    def record_rl_outcome(self, **kwargs: Any) -> None:
        self.rl_outcomes.append(kwargs)


def test_veto_four_step_process(monkeypatch):
    # 1. Setup
    mock_guard = _MockVetoGuard(should_veto=True)
    monkeypatch.setattr(registry_mod, "get_veto_guard", lambda: mock_guard)

    reg = _MockRegistry()
    reg._governance_engine = None
    reg.register_tool(_DummyTool())

    tool_call = {
        "id": "call_veto_test",
        "type": "function",
        "function": {"name": "READ_FILE", "arguments": "{}"},
    }

    # 2. Execute
    res = reg.execute_tool_call(tool_call)

    # 3. Verify Step 1: Inhibition
    assert res.get("_veto") is True
    assert res.get("_success") is False

    # 4. Verify Step 2: Injection (Content check)
    content = res.get("content", "")
    assert "VETO: action suppressed (Immediate Inhibition)." in content
    assert "Dissonance Report (L3 Injection):" in content
    assert "kappa_integrated (I): 0.1" in content

    # 5. Verify Step 3: Recalibration (RL Outcome)
    assert len(reg.rl_outcomes) == 1
    outcome = reg.rl_outcomes[0]
    assert outcome["tool_name"] == "READ_FILE"
    assert outcome["success"] is False
    assert "VETOED" in outcome["tool_result_text"]

    # 6. Verify Step 4: Re-sampling (Instruction check)
    assert "Second Look required: re-sample context" in content
    assert "Do NOT retry the same tool call unchanged." in content


def test_no_veto_when_coherent(monkeypatch):
    # 1. Setup
    mock_guard = _MockVetoGuard(should_veto=False)
    monkeypatch.setattr(registry_mod, "get_veto_guard", lambda: mock_guard)

    reg = _MockRegistry()
    reg._governance_engine = None
    reg.register_tool(_DummyTool())

    tool_call = {
        "id": "call_ok_test",
        "type": "function",
        "function": {"name": "READ_FILE", "arguments": "{}"},
    }

    # 2. Execute
    res = reg.execute_tool_call(tool_call)

    # 3. Verify
    assert res.get("_veto") is not True
    assert res.get("name") == "READ_FILE"
    assert len(reg.rl_outcomes) == 0  # record_rl_outcome is called AFTER execution in normal flow, but we are testing the veto branch
