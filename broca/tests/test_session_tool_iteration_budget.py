from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry


class _NoopTool:
    name = "noop"
    description = "No-op tool"
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs):
        return {"ok": True}

    def format_result(self, result):
        return str(result)


@dataclass
class _CallRecord:
    tools: Optional[list]
    tool_choice: Optional[dict]


class _BudgetAwareDummyLLM:
    """
    Emits tool_calls whenever tools are advertised; emits a final response when tools are disabled.
    """

    def __init__(self, final_text: str = "final"):
        self.final_text = final_text
        self.calls: List[_CallRecord] = []

    def chat(self, messages: list, tools: Optional[list] = None, tool_choice: Optional[dict] = None, **kwargs):
        self.calls.append(_CallRecord(tools=tools, tool_choice=tool_choice))
        if tools:
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": f"call_{len(self.calls)}",
                                    "type": "function",
                                    "function": {"name": "noop", "arguments": "{}"},
                                }
                            ],
                        }
                    }
                ]
            }
        return {"choices": [{"message": {"role": "assistant", "content": self.final_text}}]}

    def extract_assistant_content(self, response: Dict[str, Any]):
        return response.get("choices", [{}])[0].get("message", {}).get("content")

    def extract_tool_calls(self, response: Dict[str, Any]):
        return response.get("choices", [{}])[0].get("message", {}).get("tool_calls") or []


class _StubbornDummyLLM(_BudgetAwareDummyLLM):
    """
    Still emits tool_calls even when tools are disabled for a few attempts, then complies.
    """

    def __init__(self, stubborn_attempts: int = 2, final_text: str = "final"):
        super().__init__(final_text=final_text)
        self._stubborn_attempts = stubborn_attempts
        self._disabled_calls = 0

    def chat(self, messages: list, tools: Optional[list] = None, tool_choice: Optional[dict] = None, **kwargs):
        self.calls.append(_CallRecord(tools=tools, tool_choice=tool_choice))
        if tools:
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": f"call_{len(self.calls)}",
                                    "type": "function",
                                    "function": {"name": "noop", "arguments": "{}"},
                                }
                            ],
                        }
                    }
                ]
            }

        self._disabled_calls += 1
        if self._disabled_calls <= self._stubborn_attempts:
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": f"call_disabled_{self._disabled_calls}",
                                    "type": "function",
                                    "function": {"name": "noop", "arguments": "{}"},
                                }
                            ],
                        }
                    }
                ]
            }
        return {"choices": [{"message": {"role": "assistant", "content": self.final_text}}]}


def _make_session(llm, monkeypatch) -> ConversationSession:
    # This test uses a synthetic tool name; ensure the registry is in legacy toolset mode.
    from broca.config import config
    monkeypatch.setattr(config.tools, "toolset", "legacy", raising=False)
    registry = ToolRegistry()
    registry.register_tool(_NoopTool())
    return ConversationSession(llm=llm, tool_registry=registry, storage=None)


def test_tool_iteration_budget_disables_tools_at_30(monkeypatch):
    llm = _BudgetAwareDummyLLM(final_text="ok")
    session = _make_session(llm, monkeypatch)

    reply = session.send("do stuff", stream=False)
    assert reply == "ok"

    assert len(llm.calls) >= 1
    assert not llm.calls[-1].tools  # hard stop: tools disabled
    assert len([c for c in llm.calls if c.tools]) == 29


@pytest.mark.parametrize("threshold", [20, 25, 28, 29, 30])
def test_tool_iteration_budget_injects_warnings_at_thresholds(threshold: int, monkeypatch):
    llm = _BudgetAwareDummyLLM(final_text="ok")
    session = _make_session(llm, monkeypatch)

    _ = session.send("do stuff", stream=False)

    warning_msgs = [
        m
        for m in session.messages
        if isinstance(m, dict)
        and m.get("role") == "user"
        and m.get("hidden") is True
        and isinstance(m.get("content"), str)
        and f"{threshold}/30" in m.get("content")
    ]
    assert warning_msgs, f"missing warning for threshold={threshold}"


def test_tool_iteration_budget_reprompts_until_final_text_when_stubborn(monkeypatch):
    llm = _StubbornDummyLLM(stubborn_attempts=2, final_text="ok")
    session = _make_session(llm, monkeypatch)
    session._max_tool_iterations = 3  # keep test fast; semantics must hold for any max

    reply = session.send("do stuff", stream=False)
    assert reply == "ok"

    disabled_calls = [c for c in llm.calls if not c.tools]
    assert len(disabled_calls) >= 1
