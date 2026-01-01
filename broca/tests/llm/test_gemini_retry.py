"""
Unit tests for GeminiClient retry/backoff behavior.
"""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import Mock

import httpx
import pytest

from broca.llm.gemini_client import GeminiClient


def _ok_response(payload: Dict[str, Any]) -> httpx.Response:
    request = httpx.Request("POST", "https://example.com/chat/completions")
    return httpx.Response(200, json=payload, request=request)


def _status_error(status_code: int, *, headers: Dict[str, str] | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.com/chat/completions")
    response = httpx.Response(status_code, headers=headers or {}, text="error", request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


def test_chat_retries_on_429_and_respects_retry_after(monkeypatch):
    sleep_mock = Mock()
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
        use_sdk=False,
        max_retries=1,
        backoff_base_seconds=1.0,
        backoff_max_seconds=60.0,
        backoff_jitter=0.0,
        respect_retry_after=True,
        _sleep_fn=sleep_mock,
    )

    calls: List[str] = []

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        calls.append(path)
        if len(calls) == 1:
            raise _status_error(429, headers={"Retry-After": "5"})
        return _ok_response({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

    monkeypatch.setattr(client._client, "post", fake_post)

    resp = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert resp["choices"][0]["message"]["content"] == "ok"
    sleep_mock.assert_called_once_with(5.0)
    assert calls == ["/chat/completions", "/chat/completions"]


def test_chat_exponential_backoff_no_retry_after(monkeypatch):
    sleep_mock = Mock()
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
        use_sdk=False,
        max_retries=2,
        backoff_base_seconds=1.0,
        backoff_max_seconds=60.0,
        backoff_jitter=0.0,
        respect_retry_after=True,
        _sleep_fn=sleep_mock,
    )

    attempt = 0

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        nonlocal attempt
        attempt += 1
        if attempt <= 2:
            raise _status_error(429)
        return _ok_response({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

    monkeypatch.setattr(client._client, "post", fake_post)

    _ = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert [c.args[0] for c in sleep_mock.call_args_list] == [1.0, 2.0]


def test_retry_after_parse_fault_injection_does_not_crash(monkeypatch):
    sleep_mock = Mock()
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
        use_sdk=False,
        max_retries=1,
        backoff_base_seconds=1.0,
        backoff_max_seconds=60.0,
        backoff_jitter=0.0,
        respect_retry_after=True,
        _sleep_fn=sleep_mock,
    )

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        raise _status_error(429, headers={"Retry-After": "not-a-number"})

    monkeypatch.setattr(client._client, "post", fake_post)

    with pytest.raises(httpx.HTTPStatusError):
        client.chat(messages=[{"role": "user", "content": "hi"}])

    sleep_mock.assert_called_once_with(1.0)


def test_sdk_chat_retries_on_429_before_fallback(monkeypatch):
    sleep_mock = Mock()
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
        use_sdk=False,
        max_retries=1,
        backoff_base_seconds=1.0,
        backoff_max_seconds=60.0,
        backoff_jitter=0.0,
        respect_retry_after=True,
        _sleep_fn=sleep_mock,
    )

    class FakeSdkError(Exception):
        def __init__(self):
            super().__init__("429 rate limited")
            self.status_code = 429
            self.headers = {"Retry-After": "3"}

    client._sdk_client = Mock()
    client._sdk_client.models = Mock()
    client._sdk_client.models.generate_content = Mock(side_effect=[FakeSdkError(), object()])

    monkeypatch.setattr(client, "_extract_thought_signature_from_sdk_response", lambda _resp: None)
    monkeypatch.setattr(
        client,
        "_convert_sdk_response_to_openai_format",
        lambda _resp: {"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
    )

    resp = client._chat_sdk(messages=[{"role": "user", "content": "hi"}], temperature=None, tools=None, thought_signature=None)
    assert resp["choices"][0]["message"]["content"] == "ok"
    sleep_mock.assert_called_once_with(3.0)
