from __future__ import annotations

import json
from types import SimpleNamespace


class _FakeLLM:
    def __init__(self, responses):
        self._responses = list(responses)

    def chat(self, _messages, tools=None, tool_choice=None):
        assert self._responses, "LLM called more times than expected"
        return self._responses.pop(0)

    def extract_tool_calls(self, response):
        return response.get("tool_calls", []) if isinstance(response, dict) else []

    def extract_assistant_content(self, response):
        return response.get("content") if isinstance(response, dict) else None


class _FakeToolRegistry:
    def __init__(self) -> None:
        self._force_final_response = False
        self.calls = []

    @property
    def force_final_response(self) -> bool:
        return bool(self._force_final_response)

    def start_turn(self, _turn_no: int) -> None:
        self._force_final_response = False

    def get_rl_selection(self, context=None):
        return None

    def to_openai_format(self, context=None, rl_selection=None):
        return [] if self._force_final_response else [{"type": "function", "function": {"name": "DONE", "parameters": {}}}]

    def execute_tool_call(self, tool_call):
        name = tool_call.get("function", {}).get("name")
        self.calls.append(name)
        if name == "DONE":
            self._force_final_response = True
            return {"role": "tool", "name": "DONE", "content": "DONE ok"}
        if name == "EXECUTE":
            raise AssertionError("EXECUTE must not run while force_final_response is active")
        return {"role": "tool", "name": name or "unknown", "content": "ok"}


def _tool_call(call_id: str, name: str, args: str = "{}"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": args}}


def test_stream_response_force_final_response_reprompts_and_finishes():
    from broca.web_api import stream_response

    llm = _FakeLLM(
        responses=[
            {"tool_calls": [_tool_call("c1", "DONE")], "content": ""},
            {"tool_calls": [_tool_call("c2", "EXECUTE", "{\"cmd\":\"echo hi\"}")], "content": ""},
            {"tool_calls": [], "content": "final answer"},
        ]
    )
    session = SimpleNamespace(
        messages=[],
        llm=llm,
        internal_sensing_framework=None,
        world_state_aggregator=None,
        _update_system_prompt=lambda: None,
        _get_messages_for_llm=lambda: [],
    )
    rt = SimpleNamespace(tool_registry=_FakeToolRegistry(), world_state_aggregator=None)
    storage = SimpleNamespace(
        load_conversation=lambda _cid: {"metadata": {}},
        save_conversation=lambda _cid, _msgs, _meta: None,
    )

    chunks = list(stream_response(rt, storage, session, "cid", "hello", web_search_enabled=True))
    events = [json.loads(c) for c in chunks if c.strip()]

    # 1) DONE executed, 2) force_final_response tool_calls were reprompted (warning), 3) final text delivered.
    assert rt.tool_registry.calls == ["DONE"]
    assert any(e.get("type") == "warning" and e.get("warning") == "tools_disabled_force_final_response" for e in events)
    assert any(e.get("type") == "text" and "final answer" in e.get("content", "") for e in events)


def test_stream_response_empty_final_after_done_reprompts():
    from broca.web_api import stream_response

    llm = _FakeLLM(
        responses=[
            {"tool_calls": [_tool_call("c1", "DONE")], "content": ""},
            {"tool_calls": [], "content": ""},  # empty final response (should reprompt, not emit generic apology)
            {"tool_calls": [], "content": "final answer"},
        ]
    )
    session = SimpleNamespace(
        messages=[],
        llm=llm,
        internal_sensing_framework=None,
        world_state_aggregator=None,
        _update_system_prompt=lambda: None,
        _get_messages_for_llm=lambda: [],
    )
    rt = SimpleNamespace(tool_registry=_FakeToolRegistry(), world_state_aggregator=None)
    storage = SimpleNamespace(
        load_conversation=lambda _cid: {"metadata": {}},
        save_conversation=lambda _cid, _msgs, _meta: None,
    )

    chunks = list(stream_response(rt, storage, session, "cid", "hello", web_search_enabled=True))
    events = [json.loads(c) for c in chunks if c.strip()]

    assert rt.tool_registry.calls == ["DONE"]
    assert any(e.get("type") == "warning" and e.get("warning") == "empty_final_response" for e in events)
    assert any(e.get("type") == "text" and "final answer" in e.get("content", "") for e in events)
