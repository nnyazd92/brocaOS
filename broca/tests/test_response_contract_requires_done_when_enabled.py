from __future__ import annotations

from unittest.mock import Mock

import pytest

from broca.config import config
from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tools.primitive_toolset import DoneTool, RespondAndContinueTool


def test_response_contract_reprompts_when_require_done_enabled(monkeypatch):
    """
    When RL response contract is enabled and toolset is primitive, the model must call
    DONE/RESPOND_AND_CONTINUE before a final response is accepted.
    """
    # Use env + reload so the session imports see consistent config values.
    monkeypatch.setenv("BROCA_TOOLSET", "primitive")
    monkeypatch.setenv("BROCA_RL_REQUIRE_DONE_FOR_RESPONSE", "true")
    monkeypatch.setenv("BROCA_RL_ENABLED", "true")
    monkeypatch.setenv("BROCA_TEST_MODE", "true")  # avoid reading developer .env

    import importlib
    import broca.config as cfg_mod

    importlib.reload(cfg_mod)
    cfg = cfg_mod.config

    # Fake "RL active" by providing a non-None online_policy_ranker.
    reg = ToolRegistry()
    monkeypatch.setattr(reg, "online_policy_ranker", object(), raising=False)
    reg.register_tool(DoneTool())
    reg.register_tool(RespondAndContinueTool())

    # Sanity: DONE/RESPOND should be visible in the tool buffer.
    tools_buf = reg.to_openai_format(context={}, rl_selection=None)
    names = [t.get("function", {}).get("name") for t in tools_buf]
    assert "DONE" in names
    assert "RESPOND_AND_CONTINUE" in names

    # Minimal LLM stub: always tries to respond in plain text without tool calls.
    llm = Mock()
    llm.chat.return_value = {"choices": [{"message": {"role": "assistant", "content": "hello"}}]}
    llm.extract_assistant_content.return_value = "hello"
    llm.extract_tool_calls.return_value = []

    sess = ConversationSession(llm=llm, tool_registry=reg, world_state_aggregator=None)

    # This should trigger a reprompt internally; we verify the hidden directive was injected.
    out = sess.send("hi", stream=False)
    assert isinstance(out, str)
    assert "[SYSTEM DIRECTIVE - RESPONSE CONTRACT]" in "\n".join(
        m.get("content", "") for m in sess.messages if isinstance(m, dict)
    )


