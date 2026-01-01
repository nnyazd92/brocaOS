from __future__ import annotations

import json
from pathlib import Path

import pytest

from broca.tools.cognition_tools import InterpretTool, SolveTool, VerifyTool


class _StubWebSearch:
    def __init__(self, results):
        self._results = results

    def execute(self, **kwargs):
        return {"results": list(self._results)}


def test_solve_persists_reasoning_state(tmp_path: Path):
    state_path = tmp_path / "reasoning_state.json"
    tool = SolveTool(state_file_path=str(state_path))

    res = tool.execute(problem="Solve test problem", cycles=0, persist=True)
    assert res["success"] is True
    assert state_path.exists()

    # Verify state contains working memory with our problem item.
    raw = json.loads(state_path.read_text(encoding="utf-8"))
    wm = raw.get("working_memory") or {}
    items = wm.get("items") or []
    assert any(isinstance(i, dict) and (i.get("content") or {}).get("type") == "problem" for i in items)


def test_interpret_adds_observation_and_persists(tmp_path: Path):
    state_path = tmp_path / "reasoning_state.json"
    tool = InterpretTool(state_file_path=str(state_path))

    res = tool.execute(observation="Observation text", cycles=0, persist=True)
    assert res["success"] is True
    assert state_path.exists()

    raw = json.loads(state_path.read_text(encoding="utf-8"))
    wm = raw.get("working_memory") or {}
    items = wm.get("items") or []
    assert any(isinstance(i, dict) and (i.get("content") or {}).get("type") == "observation" for i in items)


def test_verify_facts_uses_fact_checker_and_persists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Stub web search so test is deterministic and offline.
    stub_results = [
        {
            "title": "Python history",
            "content": "Confirmed fact: Python created 1991 by Guido van Rossum.",
        }
    ]
    monkeypatch.setattr(
        "broca.reasoning.fact_checker.FactChecker._get_web_search_tool",
        lambda self: _StubWebSearch(stub_results),
    )

    state_path = tmp_path / "reasoning_state.json"
    tool = VerifyTool(state_file_path=str(state_path))

    res = tool.execute(text="Python was created in 1991.", max_claims=5, persist=True)
    assert res["success"] is True
    assert res["mode"] == "facts"
    assert res["count"] >= 1
    assert state_path.exists()

    assert any(r.get("verified") in (True, False) for r in res["results"])


def test_verify_logic_calls_z3_validate_and_persists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def _stub_z3_execute(self, z3_code: str, timeout=None):
        return {"result": "sat", "model": {"x": "1"}, "unsat_core": None, "note": None, "output": "", "z3_available": True}

    monkeypatch.setattr("broca.tools.z3_validator_tool.Z3ValidatorTool.execute", _stub_z3_execute)

    state_path = tmp_path / "reasoning_state.json"
    tool = VerifyTool(state_file_path=str(state_path))

    res = tool.execute(
        text="Validate constraints for my plan.",
        mode="logic",
        z3_code="from z3 import *\nsolver = Solver()\nx = Int('x')\nsolver.add(x == 1)\n",
        persist=True,
    )
    assert res["success"] is True
    assert res["mode"] == "logic"
    assert res["z3"]["result"] == "sat"
    assert state_path.exists()

    raw = json.loads(state_path.read_text(encoding="utf-8"))
    wm = raw.get("working_memory") or {}
    items = wm.get("items") or []
    assert any(
        isinstance(i, dict)
        and (i.get("content") or {}).get("type") == "verification"
        and (i.get("content") or {}).get("mode") == "logic"
        for i in items
    )


def test_verify_logic_fault_injection_z3_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def _raise(self, z3_code: str, timeout=None):
        raise RuntimeError("boom")

    monkeypatch.setattr("broca.tools.z3_validator_tool.Z3ValidatorTool.execute", _raise)

    tool = VerifyTool(state_file_path=str(tmp_path / "reasoning_state.json"))
    res = tool.execute(text="x", mode="logic", z3_code="from z3 import *\n", persist=False)
    assert res["success"] is False
    assert str(res.get("error", "")).startswith("z3_execute_failed:")


def test_corrupt_state_file_fault_injection(tmp_path: Path):
    state_path = tmp_path / "reasoning_state.json"
    state_path.write_text("{not json", encoding="utf-8")

    tool = SolveTool(state_file_path=str(state_path))
    res = tool.execute(problem="still works", cycles=0, persist=True)
    assert res["success"] is True
    # tool should be able to recover and write a valid state file
    _ = json.loads(state_path.read_text(encoding="utf-8"))
