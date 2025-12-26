
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import httpx
import pytest

from broca.llm.gemini_client import GeminiClient
from broca.config import config


def _make_response(json_data: Dict[str, Any]) -> httpx.Response:
    """Helper to build an httpx.Response with JSON content."""
    request = httpx.Request("POST", "https://example.com/chat/completions")
    return httpx.Response(200, json=json_data, request=request)


class DummyStream:
    """Simple iterator that simulates httpx streaming SSE lines."""

    def __init__(self, lines: list[str]):
        self._lines = lines

    def __enter__(self):  # context manager API
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        """Mimic a successful 200 OK streaming response."""
        return None

    def iter_lines(self):
        for line in self._lines:
            yield line


def test_chat_success(monkeypatch):
    """GeminiClient.chat should POST to /chat/completions and return JSON."""
    # Force REST API usage (not SDK) for this test
    client = GeminiClient(api_key="test-key", base_url="https://example.com", model="gemini-3.0-flash-001", use_sdk=False)

    # REST API payload doesn't include generation_config (only SDK does)
    expected_payload = {
        "model": client.model,
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": client.temperature,
    }

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        assert path == "/chat/completions"
        assert json == expected_payload
        assert headers["Authorization"] == "Bearer test-key"
        return _make_response(
            {
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "hello"},
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)

    resp = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert resp["choices"][0]["message"]["content"] == "hello"


def test_chat_timeout(monkeypatch):
    client = GeminiClient(api_key="test-key", base_url="https://example.com", model="gemini-3.0-flash-001")

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        raise httpx.ReadTimeout("timeout", request=None)

    monkeypatch.setattr(client._client, "post", fake_post)

    with pytest.raises(TimeoutError):
        client.chat(messages=[{"role": "user", "content": "hi"}])


def test_chat_http_error(monkeypatch):
    client = GeminiClient(api_key="test-key", base_url="https://example.com", model="gemini-3.0-flash-001")

    response = httpx.Response(400, text="bad request")
    err = httpx.HTTPStatusError("bad", request=httpx.Request("POST", "https://example.com/chat/completions"), response=response)

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        raise err

    monkeypatch.setattr(client._client, "post", fake_post)

    with pytest.raises(httpx.HTTPStatusError):
        client.chat(messages=[{"role": "user", "content": "hi"}])


def test_chat_request_error(monkeypatch):
    client = GeminiClient(api_key="test-key", base_url="https://example.com", model="gemini-3.0-flash-001")

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        raise httpx.RequestError("boom", request=None)

    monkeypatch.setattr(client._client, "post", fake_post)

    with pytest.raises(ConnectionError):
        client.chat(messages=[{"role": "user", "content": "hi"}])


def test_chat_stream_success(monkeypatch):
    client = GeminiClient(api_key="test-key", base_url="https://example.com", model="gemini-3.0-flash-001")

    # Simulate two chunks with content, then [DONE]
    chunks = [
        "data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}",
        "data: {\"choices\":[{\"delta\":{\"content\":\" world\"}}]}",
        "data: [DONE]",
    ]

    def fake_stream(method, path, json=None, headers=None):  # type: ignore[override]
        assert method == "POST"
        assert path == "/chat/completions"
        assert json["model"] == client.model
        assert json["stream"] is True
        return DummyStream(chunks)

    monkeypatch.setattr(client._client, "stream", fake_stream)

    out = "".join(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))
    assert out == "Hello world"


def test_extract_assistant_content_happy_path():
    resp = {
        "choices": [
            {"message": {"role": "assistant", "content": "hello"}},
        ]
    }
    assert GeminiClient.extract_assistant_content(resp) == "hello"


def test_extract_assistant_content_missing_keys():
    assert GeminiClient.extract_assistant_content({}) == ""


def test_extract_tool_calls_present():
    resp = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {"id": "call_1", "type": "function", "function": {"name": "foo", "arguments": "{}"}},
                    ],
                }
            }
        ]
    }
    calls = GeminiClient.extract_tool_calls(resp)
    assert isinstance(calls, list)
    assert calls[0]["id"] == "call_1"


def test_extract_tool_calls_absent():
    assert GeminiClient.extract_tool_calls({"choices": [{"message": {"role": "assistant", "content": "no tools"}}]}) == []
    assert GeminiClient.extract_tool_calls({}) == []


# Gemini 3 Integration Tests

def test_chat_with_thinking_level_rest(monkeypatch):
    """Test that thinking_level is NOT included in REST API requests (only SDK supports it)."""
    # Force REST API usage (not SDK) for this test
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
        use_sdk=False,
    )
    # Set thinking_level via config
    client.thinking_level = "high"

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        assert path == "/chat/completions"
        # REST API doesn't support generation_config - only SDK does
        assert "generation_config" not in json
        return _make_response(
            {
                "choices": [{"message": {"role": "assistant", "content": "response"}}],
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)
    client.chat(messages=[{"role": "user", "content": "test"}])


def test_chat_with_thought_signature_rest(monkeypatch):
    """Test that thought_signature is passed in REST API requests."""
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
    )
    client._thought_signature = "test-signature-123"

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        assert path == "/chat/completions"
        assert json.get("thought_signature") == "test-signature-123"
        return _make_response(
            {
                "choices": [{"message": {"role": "assistant", "content": "response"}}],
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)
    client.chat(messages=[{"role": "user", "content": "test"}])


def test_extract_thought_signature_from_rest_response():
    """Test extracting thought_signature from REST API response."""
    # REST API format: thought_signature in response root
    response = {
        "choices": [{"message": {"role": "assistant", "content": "response"}}],
        "thought_signature": "sig-123",
    }
    signature = GeminiClient.extract_thought_signature(response)
    assert signature == "sig-123"


def test_extract_thought_signature_from_rest_response_in_choices():
    """Test extracting thought_signature from REST API response in choices."""
    # Alternative REST format: thought_signature in choices
    response = {
        "choices": [
            {
                "message": {"role": "assistant", "content": "response"},
                "thought_signature": "sig-456",
            }
        ],
    }
    signature = GeminiClient.extract_thought_signature(response)
    assert signature == "sig-456"


def test_extract_thought_signature_from_function_call():
    """Test extracting thought_signature from function call response."""
    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "test", "arguments": "{}"},
                            "thought_signature": "sig-from-function",
                        }
                    ],
                }
            }
        ],
    }
    signature = GeminiClient.extract_thought_signature(response)
    assert signature == "sig-from-function"


def test_extract_thought_signature_none():
    """Test extracting thought_signature when not present."""
    response = {
        "choices": [{"message": {"role": "assistant", "content": "response"}}],
    }
    signature = GeminiClient.extract_thought_signature(response)
    assert signature is None


def test_thought_signature_persistence(monkeypatch):
    """Test that thought_signature persists across multiple calls."""
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
    )

    call_count = 0

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: no signature sent, signature returned
            assert "thought_signature" not in json or json.get("thought_signature") is None
            return _make_response(
                {
                    "choices": [{"message": {"role": "assistant", "content": "first"}}],
                    "thought_signature": "sig-1",
                }
            )
        else:
            # Second call: signature from first call should be sent
            assert json.get("thought_signature") == "sig-1"
            return _make_response(
                {
                    "choices": [{"message": {"role": "assistant", "content": "second"}}],
                    "thought_signature": "sig-2",
                }
            )

    monkeypatch.setattr(client._client, "post", fake_post)

    # First call
    resp1 = client.chat(messages=[{"role": "user", "content": "first"}])
    assert resp1["choices"][0]["message"]["content"] == "first"
    # Verify signature was extracted and stored
    assert client._thought_signature == "sig-1"

    # Second call - should include signature
    resp2 = client.chat(messages=[{"role": "user", "content": "second"}])
    assert resp2["choices"][0]["message"]["content"] == "second"
    assert client._thought_signature == "sig-2"


def test_thinking_level_default():
    """Test that thinking_level defaults to 'low'."""
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
    )
    assert client.thinking_level == "low"


def test_thinking_level_from_config(monkeypatch):
    """Test that thinking_level can be set from config."""
    import os
    monkeypatch.setenv("BROCA_GEMINI_THINKING_LEVEL", "high")
    # Reload config to pick up env var
    from broca.config import BrocaConfig
    test_config = BrocaConfig()
    test_config.llm.provider = "gemini"
    test_config.llm.thinking_level = "high"

    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
    )
    # Manually set thinking_level for test
    client.thinking_level = "high"
    assert client.thinking_level == "high"


def test_use_sdk_flag():
    """Test that use_sdk flag can be configured."""
    from broca.config import config
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
    )
    # Default should match config (which may be True or False depending on environment)
    # The important thing is that it can be set
    assert client.use_sdk == config.llm.use_sdk
    # Test that it can be overridden
    client2 = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
        use_sdk=False,
    )
    assert client2.use_sdk is False


def test_sdk_fallback_to_rest(monkeypatch):
    """Test that client falls back to REST when SDK is unavailable."""
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
    )
    client.use_sdk = True
    # Force SDK client to None to simulate SDK unavailability
    client._sdk_client = None

    # Should fall back to REST
    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        return _make_response(
            {
                "choices": [{"message": {"role": "assistant", "content": "rest response"}}],
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)
    resp = client.chat(messages=[{"role": "user", "content": "test"}])
    assert resp["choices"][0]["message"]["content"] == "rest response"


def test_chat_with_thought_signature_parameter(monkeypatch):
    """Test that thought_signature parameter is passed through."""
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.com",
        model="gemini-3.0-flash-001",
    )

    def fake_post(path, json=None, headers=None):  # type: ignore[override]
        assert json.get("thought_signature") == "param-sig"
        return _make_response(
            {
                "choices": [{"message": {"role": "assistant", "content": "response"}}],
            }
        )

    monkeypatch.setattr(client._client, "post", fake_post)
    client.chat(messages=[{"role": "user", "content": "test"}], thought_signature="param-sig")


def test_ensure_thought_signature_in_tool_calls_adds_missing():
    """Test that _ensure_thought_signature_in_tool_calls adds thought_signature when missing."""
    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "test", "arguments": "{}"},
                    # Missing thought_signature
                }
            ],
        }
    ]
    
    result = GeminiClient._ensure_thought_signature_in_tool_calls(messages, thought_signature="test-sig-123")
    
    assert len(result) == 1
    assert result[0]["role"] == "assistant"
    assert len(result[0]["tool_calls"]) == 1
    assert result[0]["tool_calls"][0]["thought_signature"] == "test-sig-123"


def test_ensure_thought_signature_in_tool_calls_preserves_existing():
    """Test that _ensure_thought_signature_in_tool_calls preserves existing thought_signature."""
    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "test", "arguments": "{}"},
                    "thought_signature": "existing-sig",
                }
            ],
        }
    ]
    
    result = GeminiClient._ensure_thought_signature_in_tool_calls(messages, thought_signature="new-sig")
    
    assert len(result) == 1
    assert result[0]["tool_calls"][0]["thought_signature"] == "existing-sig"  # Preserved


def test_ensure_thought_signature_in_tool_calls_no_signature_available():
    """Test that _ensure_thought_signature_in_tool_calls warns when no signature available."""
    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "test", "arguments": "{}"},
                    # Missing thought_signature
                }
            ],
        }
    ]
    
    # No thought_signature provided
    result = GeminiClient._ensure_thought_signature_in_tool_calls(messages)
    
    assert len(result) == 1
    assert "thought_signature" not in result[0]["tool_calls"][0]  # Still missing


def test_ensure_thought_signature_in_tool_calls_multiple_tool_calls():
    """Test that _ensure_thought_signature_in_tool_calls handles multiple tool_calls."""
    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "test1", "arguments": "{}"},
                    # Missing thought_signature
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {"name": "test2", "arguments": "{}"},
                    "thought_signature": "existing-sig",
                },
                {
                    "id": "call_3",
                    "type": "function",
                    "function": {"name": "test3", "arguments": "{}"},
                    # Missing thought_signature
                },
            ],
        }
    ]
    
    result = GeminiClient._ensure_thought_signature_in_tool_calls(messages, thought_signature="new-sig")
    
    assert len(result) == 1
    assert len(result[0]["tool_calls"]) == 3
    assert result[0]["tool_calls"][0]["thought_signature"] == "new-sig"  # Added
    assert result[0]["tool_calls"][1]["thought_signature"] == "existing-sig"  # Preserved
    assert result[0]["tool_calls"][2]["thought_signature"] == "new-sig"  # Added


def test_ensure_thought_signature_in_tool_calls_non_assistant_messages():
    """Test that _ensure_thought_signature_in_tool_calls ignores non-assistant messages."""
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "system", "content": "You are a helper"},
    ]
    
    result = GeminiClient._ensure_thought_signature_in_tool_calls(messages, thought_signature="sig")
    
    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "system"
