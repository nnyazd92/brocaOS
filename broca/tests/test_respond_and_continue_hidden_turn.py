from __future__ import annotations

import json
from unittest.mock import Mock

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tools.primitive_toolset import DoneTool, RespondAndContinueTool


def _tool_call(call_id: str, name: str, args: str = "{}") -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": args}}


def test_hidden_turn_marks_assistant_messages_hidden(monkeypatch):
    from broca.config import config as app_config

    monkeypatch.setattr(app_config.tools, "toolset", "primitive", raising=False)

    # Hidden turns must call DONE/RESPOND_AND_CONTINUE before emitting plain text.
    # Simulate: model calls DONE, then emits final text (which should be hidden).
    r1 = {"choices": [{"message": {"role": "assistant", "content": "", "tool_calls": [_tool_call("c1", "DONE")]}}]}
    r2 = {"choices": [{"message": {"role": "assistant", "content": "hi", "tool_calls": []}}]}

    llm = Mock()
    llm.chat.side_effect = [r1, r2]
    def _extract_tool_calls(resp):
        try:
            return resp["choices"][0]["message"].get("tool_calls", []) or []
        except Exception:
            return []

    def _extract_assistant_content(resp):
        try:
            return resp["choices"][0]["message"].get("content")
        except Exception:
            return None

    llm.extract_tool_calls.side_effect = _extract_tool_calls
    llm.extract_assistant_content.side_effect = _extract_assistant_content
    llm.get_max_context_tokens.return_value = 8000
    llm.is_reasoner_model.return_value = False

    reg = ToolRegistry()
    reg.register_tool(DoneTool())
    reg.register_tool(RespondAndContinueTool())

    session = ConversationSession(llm=llm, tool_registry=reg)
    out = session.send("internal followup", stream=False, hidden_user_message=True)
    assert out == "hi"

    # User and assistant messages produced in this send() should be hidden for web UI.
    last_user = next(m for m in reversed(session.messages) if m.get("role") == "user")
    last_assistant = next(m for m in reversed(session.messages) if m.get("role") == "assistant")
    assert last_user.get("hidden") is True
    assert last_assistant.get("hidden") is True


def test_hidden_turn_requires_done_or_respond_and_continue_before_plain_text(monkeypatch):
    """
    Regression: background auto-continue turns must not emit a plain-text assistant message unless
    the model first calls DONE or RESPOND_AND_CONTINUE.
    """
    from broca.config import config as app_config

    monkeypatch.setattr(app_config.tools, "toolset", "primitive", raising=False)

    reg = ToolRegistry()
    reg.register_tool(DoneTool())
    reg.register_tool(RespondAndContinueTool())

    # 1) Model tries to answer in plain text (should be rejected in hidden turn).
    # 2) Model calls DONE.
    # 3) Model provides final answer (still hidden).
    r1 = {"choices": [{"message": {"role": "assistant", "content": "premature", "tool_calls": []}}]}
    r2 = {"choices": [{"message": {"role": "assistant", "content": "", "tool_calls": [_tool_call("c1", "DONE")]}}]}
    r3 = {"choices": [{"message": {"role": "assistant", "content": "final hidden", "tool_calls": []}}]}

    llm = Mock()
    llm.chat.side_effect = [r1, r2, r3]
    llm.get_max_context_tokens.return_value = 8000
    llm.is_reasoner_model.return_value = False

    def _extract_tool_calls(resp):
        try:
            return resp["choices"][0]["message"].get("tool_calls", []) or []
        except Exception:
            return []

    def _extract_assistant_content(resp):
        try:
            return resp["choices"][0]["message"].get("content")
        except Exception:
            return None

    llm.extract_tool_calls.side_effect = _extract_tool_calls
    llm.extract_assistant_content.side_effect = _extract_assistant_content

    session = ConversationSession(llm=llm, tool_registry=reg)
    out = session.send("internal followup", stream=False, hidden_user_message=True)
    assert out == "final hidden"

    # Ensure we actually forced a DONE tool call before accepting plain text.
    tool_msgs = [m for m in session.messages if m.get("role") == "tool"]
    assert any(m.get("name") == "DONE" for m in tool_msgs)

    # All messages in hidden send() are hidden.
    tail = session.messages[-10:]
    assert any(m.get("role") == "assistant" and m.get("content") == "premature" and m.get("hidden") is True for m in tail)
    assert any(m.get("role") == "assistant" and m.get("content") == "final hidden" and m.get("hidden") is True for m in tail)


