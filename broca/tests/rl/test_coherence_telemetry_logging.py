from __future__ import annotations

import importlib
import json

import pytest

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry


class _MockTool:
    def __init__(self, name: str = "test_tool"):
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


def _reset_singletons():
    # Ensure env-driven loggers and telemetry singleton bind to the current test env/cwd.
    import broca.rl.coherence_telemetry as ct

    ct = importlib.reload(ct)
    import broca.rl.kappa_logger as kl
    import broca.rl.kappa_integrated_logger as kil

    importlib.reload(kl)
    importlib.reload(kil)
    return ct


def test_registry_writes_kappa_and_kappa_integrated_csv_without_internal_sensing(tmp_path, monkeypatch):
    # Keep all artifacts inside tmp_path (avoid polluting repo data/).
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BROCA_KAPPA_LOG_ENABLED", "true")
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_ENABLED", "true")
    monkeypatch.setenv("BROCA_KAPPA_LOG_FILE", str(tmp_path / "data" / "rl" / "kappa_series.csv"))
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_FILE", str(tmp_path / "data" / "rl" / "kappa_integrated_series.csv"))
    monkeypatch.setenv("BROCA_KAPPA_LOG_APPEND", "true")
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_APPEND", "true")

    _reset_singletons()

    registry = ToolRegistry()
    registry.register_tool(_MockTool("test_tool"))

    tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {"name": "test_tool", "arguments": json.dumps({"param": "x"})},
    }
    registry.execute_tool_call(tool_call)

    kappa_path = tmp_path / "data" / "rl" / "kappa_series.csv"
    kint_path = tmp_path / "data" / "rl" / "kappa_integrated_series.csv"
    assert kappa_path.exists()
    assert kint_path.exists()

    # Header + at least one sample row.
    assert len(kappa_path.read_text(encoding="utf-8").strip().splitlines()) >= 2
    assert len(kint_path.read_text(encoding="utf-8").strip().splitlines()) >= 2


def test_session_writes_kappa_series_on_final_response_without_prediction(tmp_path, monkeypatch):
    # This test targets the "non-tool turn" path.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BROCA_KAPPA_LOG_ENABLED", "true")
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_ENABLED", "true")
    monkeypatch.setenv("BROCA_KAPPA_LOG_FILE", str(tmp_path / "data" / "rl" / "kappa_series.csv"))
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_FILE", str(tmp_path / "data" / "rl" / "kappa_integrated_series.csv"))
    monkeypatch.setenv("BROCA_KAPPA_LOG_APPEND", "true")
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_APPEND", "true")

    _reset_singletons()

    class _LLM:
        def chat(self, messages: list, **kwargs):
            return {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}

        def extract_assistant_content(self, response):
            return response["choices"][0]["message"]["content"]

        def extract_tool_calls(self, response):
            return []

    session = ConversationSession(llm=_LLM(), tool_registry=None, internal_sensing_framework=None, world_state_aggregator=None)
    out = session.send("hi", stream=False)
    assert out == "ok"

    kappa_path = tmp_path / "data" / "rl" / "kappa_series.csv"
    kint_path = tmp_path / "data" / "rl" / "kappa_integrated_series.csv"
    assert kappa_path.exists()
    assert kint_path.exists()

    assert len(kappa_path.read_text(encoding="utf-8").strip().splitlines()) >= 2
    assert len(kint_path.read_text(encoding="utf-8").strip().splitlines()) >= 2


