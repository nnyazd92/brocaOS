from __future__ import annotations

from typing import Any, Dict, List

import httpx
import pytest

from broca.llm.anthropic_client import AnthropicClient


def _make_response(json_data: Dict[str, Any]) -> httpx.Response:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(200, json=json_data, request=request)


def test_chat_success_text_only(monkeypatch):
    client = AnthropicClient(api_key="test-key", base_url="https://api.anthropic.com", model="claude-test", timeout=30.0, max_retries=0)

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        assert path == "/v1/messages"
        assert headers["x-api-key"] == "test-key"
        assert "anthropic-version" in headers
        assert json["model"] == "claude-test"
        assert json["messages"][0]["role"] == "user"
        return _make_response(
            {
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Hello"}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)
    resp = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert AnthropicClient.extract_assistant_content(resp) == "Hello"
    assert AnthropicClient.extract_tool_calls(resp) == []


def test_chat_tool_use_maps_to_openai_tool_calls(monkeypatch):
    client = AnthropicClient(api_key="test-key", base_url="https://api.anthropic.com", model="claude-test", timeout=30.0, max_retries=0)

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        assert path == "/v1/messages"
        # Tool schema should be in Anthropic format
        assert json["tools"][0]["name"] == "READ_FILE"
        assert "input_schema" in json["tools"][0]
        return _make_response(
            {
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "toolu_1", "name": "READ_FILE", "input": {"path": "README.md"}},
                ],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "READ_FILE",
                "description": "read a file",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
            },
        }
    ]
    resp = client.chat(messages=[{"role": "user", "content": "read it"}], tools=tools)
    calls = AnthropicClient.extract_tool_calls(resp)
    assert calls and calls[0]["function"]["name"] == "READ_FILE"
    assert calls[0]["id"] == "toolu_1"


def test_openai_tool_messages_become_tool_result_blocks(monkeypatch):
    client = AnthropicClient(api_key="test-key", base_url="https://api.anthropic.com", model="claude-test", timeout=30.0, max_retries=0)

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        assert path == "/v1/messages"
        # Tool result should have been converted into a user tool_result block
        msgs: List[Dict[str, Any]] = json["messages"]
        assert msgs[-1]["role"] == "user"
        assert msgs[-1]["content"][0]["type"] == "tool_result"
        assert msgs[-1]["content"][0]["tool_use_id"] == "call_1"
        assert "OK" in msgs[-1]["content"][0]["content"]
        return _make_response(
            {
                "id": "msg_2",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Done"}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)
    messages = [
        {"role": "user", "content": "go"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "READ_FILE", "arguments": "{\"path\":\"README.md\"}"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "name": "READ_FILE", "content": "OK"},
    ]
    resp = client.chat(messages=messages)
    assert AnthropicClient.extract_assistant_content(resp) == "Done"


def test_chat_timeout_maps_to_timeout_error(monkeypatch):
    client = AnthropicClient(api_key="test-key", base_url="https://api.anthropic.com", model="claude-test", max_retries=0)

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        raise httpx.ReadTimeout("timeout", request=None)

    monkeypatch.setattr(client._client, "post", fake_post)
    with pytest.raises(TimeoutError):
        client.chat(messages=[{"role": "user", "content": "hi"}])


class DummyStream:
    def __init__(self, lines: list[str]):
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        return None

    def iter_lines(self):
        for line in self._lines:
            yield line


def test_chat_stream_yields_text_deltas_until_message_stop(monkeypatch):
    client = AnthropicClient(api_key="test-key", base_url="https://api.anthropic.com", model="claude-test", max_retries=0)

    lines = [
        "event: message_start",
        "data: {\"type\":\"message_start\",\"message\":{\"id\":\"msg_1\"}}",
        "event: content_block_delta",
        "data: {\"type\":\"content_block_delta\",\"delta\":{\"type\":\"text_delta\",\"text\":\"Hello\"}}",
        "data: {\"type\":\"content_block_delta\",\"delta\":{\"type\":\"text_delta\",\"text\":\" world\"}}",
        "event: message_stop",
        "data: {\"type\":\"message_stop\"}",
    ]

    def fake_stream(method, path, json=None, headers=None):  # type: ignore[override]
        assert method == "POST"
        assert path == "/v1/messages"
        assert json["stream"] is True
        return DummyStream(lines)

    monkeypatch.setattr(client._client, "stream", fake_stream)
    out = "".join(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))
    assert out == "Hello world"


def test_chat_stream_ignores_tool_input_json_delta(monkeypatch):
    client = AnthropicClient(api_key="test-key", base_url="https://api.anthropic.com", model="claude-test", max_retries=0)


def test_chat_retries_on_429_then_succeeds(monkeypatch):
    client = AnthropicClient(
        api_key="test-key",
        base_url="https://api.anthropic.com",
        model="claude-test",
        max_retries=2,
        backoff_base_seconds=0.0,
        backoff_jitter=0.0,
        respect_retry_after=True,
        _sleep_fn=lambda _s: None,
    )

    calls = {"n": 0}

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        calls["n"] += 1
        if calls["n"] < 3:
            req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            resp = httpx.Response(429, headers={"retry-after": "0"}, request=req)
            raise httpx.HTTPStatusError("rate limited", request=req, response=resp)
        return _make_response(
            {
                "id": "msg_ok",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "OK"}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)
    resp = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert AnthropicClient.extract_assistant_content(resp) == "OK"
    assert calls["n"] == 3

    lines = [
        "data: {\"type\":\"content_block_delta\",\"delta\":{\"type\":\"input_json_delta\",\"partial_json\":\"{\\\"path\\\":\\\"README.md\\\"\"}}",
        "data: {\"type\":\"content_block_delta\",\"delta\":{\"type\":\"input_json_delta\",\"partial_json\":\"}\"}}",
        "data: {\"type\":\"message_stop\"}",
    ]

    def fake_stream(method, path, json=None, headers=None):  # type: ignore[override]
        return DummyStream(lines)

    monkeypatch.setattr(client._client, "stream", fake_stream)
    out = "".join(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))
    assert out == ""


