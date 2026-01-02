"""
Tests for process-wide Gemini 429 rate-limit coordination.
"""

from __future__ import annotations

from typing import Any, Dict

import httpx

from broca.llm.gemini_client import GeminiClient


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return float(self.now)

    def sleep(self, seconds: float) -> None:
        s = float(seconds)
        self.sleeps.append(s)
        self.now += s


def _ok_response(payload: Dict[str, Any]) -> httpx.Response:
    request = httpx.Request("POST", "https://example.com/chat/completions")
    return httpx.Response(200, json=payload, request=request)


def _status_error(status_code: int, *, headers: Dict[str, str] | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.com/chat/completions")
    response = httpx.Response(status_code, headers=headers or {}, text="error", request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


def test_global_rate_limit_sleeps_before_request(monkeypatch):
    clock = _FakeClock()
    monkeypatch.setattr("broca.llm.gemini_client.time.monotonic", clock.monotonic)

    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
        use_sdk=False,
        max_retries=0,
        backoff_jitter=0.0,
        _sleep_fn=clock.sleep,
    )

    called = {"n": 0}

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        called["n"] += 1
        return _ok_response({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

    monkeypatch.setattr(client._client, "post", fake_post)

    GeminiClient._bump_global_rate_limit(5.0)
    resp = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert resp["choices"][0]["message"]["content"] == "ok"
    assert clock.sleeps == [5.0]
    assert called["n"] == 1


def test_429_bumps_global_rate_limit_window(monkeypatch):
    clock = _FakeClock()
    monkeypatch.setattr("broca.llm.gemini_client.time.monotonic", clock.monotonic)

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
        _sleep_fn=clock.sleep,
    )

    calls: list[str] = []

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        calls.append(path)
        if len(calls) == 1:
            raise _status_error(429, headers={"Retry-After": "3"})
        return _ok_response({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

    monkeypatch.setattr(client._client, "post", fake_post)

    _ = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert clock.sleeps == [3.0]
    with GeminiClient._global_rate_limit_lock:
        assert GeminiClient._global_rate_limit_until_monotonic == 3.0

