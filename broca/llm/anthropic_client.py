from __future__ import annotations

from typing import List, Dict, Any, Optional, Iterator
import json
import logging
import random
import time
from threading import Lock

import httpx

from ..config import config

logger = logging.getLogger(__name__)


class AnthropicClient:
    """
    Thin wrapper around Anthropic's Messages API.

    Notes:
    - Anthropic is *not* OpenAI-chat-completions compatible. This client adapts Broca's
      OpenAI-shaped message/tool call format into Anthropic's `messages` schema.
    - Endpoint: POST /v1/messages
    - Auth: x-api-key
    - Versioning: anthropic-version header
    """

    # Shared global backoff gate (avoids thundering herd on 429)
    _global_rate_limit_until_monotonic: float = 0.0
    _global_rate_limit_lock: Lock = Lock()

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        anthropic_version: Optional[str] = None,
        anthropic_beta: Optional[str] = None,
        max_retries: Optional[int] = None,
        backoff_base_seconds: Optional[float] = None,
        backoff_max_seconds: Optional[float] = None,
        backoff_jitter: Optional[float] = None,
        respect_retry_after: Optional[bool] = None,
        _sleep_fn: Optional[Any] = None,
    ) -> None:
        self.api_key = api_key or config.llm.api_key
        self.base_url = base_url or config.llm.api_base
        self.model = model or config.llm.model
        self.temperature = temperature if temperature is not None else config.llm.temperature
        timeout_value = timeout if timeout is not None else config.llm.timeout
        self.anthropic_version = anthropic_version or getattr(config.llm, "anthropic_version", "2023-06-01")
        self.anthropic_beta = anthropic_beta or getattr(config.llm, "anthropic_beta", None)

        # Retry/backoff configuration (similar to GeminiClient)
        self.max_retries = (
            int(max_retries)
            if max_retries is not None
            else int(getattr(config.llm, "anthropic_max_retries", 6))
        )
        self.backoff_base_seconds = (
            float(backoff_base_seconds)
            if backoff_base_seconds is not None
            else float(getattr(config.llm, "anthropic_backoff_base_seconds", 1.0))
        )
        self.backoff_max_seconds = (
            float(backoff_max_seconds)
            if backoff_max_seconds is not None
            else float(getattr(config.llm, "anthropic_backoff_max_seconds", 60.0))
        )
        self.backoff_jitter = (
            float(backoff_jitter)
            if backoff_jitter is not None
            else float(getattr(config.llm, "anthropic_backoff_jitter", 0.25))
        )
        self.respect_retry_after = (
            bool(respect_retry_after)
            if respect_retry_after is not None
            else bool(getattr(config.llm, "anthropic_respect_retry_after", True))
        )
        self._sleep_fn = _sleep_fn or time.sleep
        self._rng = random.Random()

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_value, connect=10.0),
        )

    @staticmethod
    def _should_retry_status(status_code: int) -> bool:
        """Retry on 429 and transient server errors."""
        try:
            sc = int(status_code)
        except Exception:
            return False
        return sc in (429, 500, 502, 503, 504)

    @staticmethod
    def _parse_retry_after_header_value(value: Optional[str]) -> Optional[float]:
        """
        Parse Retry-After header value (seconds or HTTP-date). We only support
        seconds here (best-effort) to keep behavior predictable.
        """
        if not isinstance(value, str) or not value.strip():
            return None
        v = value.strip()
        # Most common form is seconds.
        try:
            sec = float(v)
            if sec >= 0:
                return sec
        except Exception:
            return None
        return None

    @classmethod
    def _parse_retry_after_seconds(cls, response: httpx.Response) -> Optional[float]:
        try:
            value = response.headers.get("retry-after")
        except Exception:
            value = None
        return cls._parse_retry_after_header_value(value)

    def _compute_backoff_seconds(self, attempt: int, *, retry_after_seconds: Optional[float]) -> float:
        """Compute exponential backoff with bounded jitter (Gemini parity)."""
        base = max(0.0, float(self.backoff_base_seconds))
        max_sleep = max(0.0, float(self.backoff_max_seconds))
        exponent = 2 ** max(0, int(attempt))
        sleep_seconds = min(max_sleep, base * exponent)

        if self.respect_retry_after and retry_after_seconds is not None:
            sleep_seconds = max(sleep_seconds, max(0.0, float(retry_after_seconds)))
            sleep_seconds = min(max_sleep, sleep_seconds)

        jitter = float(self.backoff_jitter)
        if jitter > 0.0 and sleep_seconds > 0.0:
            jitter = min(jitter, 1.0)
            low = sleep_seconds * (1.0 - jitter)
            high = sleep_seconds
            sleep_seconds = self._rng.uniform(low, high)

        return min(max_sleep, max(0.0, float(sleep_seconds)))

    def _sleep(self, seconds: float) -> None:
        self._sleep_fn(float(seconds))

    @classmethod
    def _bump_global_rate_limit(cls, seconds: float) -> None:
        try:
            seconds_f = float(seconds)
        except Exception:
            return
        if seconds_f <= 0.0:
            return
        try:
            now = float(time.monotonic())
        except Exception:
            return
        until = now + seconds_f
        with cls._global_rate_limit_lock:
            cls._global_rate_limit_until_monotonic = max(cls._global_rate_limit_until_monotonic, until)

    def _sleep_if_globally_rate_limited(self) -> None:
        while True:
            try:
                now = float(time.monotonic())
            except Exception:
                return
            with self._global_rate_limit_lock:
                until = float(self._global_rate_limit_until_monotonic)
            remaining = until - now
            if remaining <= 0.0:
                return
            self._sleep(remaining)

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "content-type": "application/json",
        }
        if isinstance(self.anthropic_beta, str) and self.anthropic_beta.strip():
            headers["anthropic-beta"] = self.anthropic_beta.strip()
        return headers

    @staticmethod
    def _to_anthropic_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for t in tools or []:
            try:
                if t.get("type") != "function":
                    continue
                fn = t.get("function") or {}
                name = fn.get("name")
                if not isinstance(name, str) or not name:
                    continue
                out.append(
                    {
                        "name": name,
                        "description": fn.get("description") or "",
                        "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
                    }
                )
            except Exception:
                continue
        return out

    @staticmethod
    def _parse_openai_tool_args(arguments: Any) -> Dict[str, Any]:
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, str) and arguments.strip():
            try:
                parsed = json.loads(arguments)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    def _to_anthropic_messages(
        self, messages: List[Dict[str, Any]]
    ) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Convert OpenAI-shaped messages to Anthropic Messages API.

        - System messages become `system` (string, concatenated).
        - Tool role messages become user messages containing tool_result blocks.
        - Assistant messages with tool_calls become assistant messages containing tool_use blocks.
        """
        system_parts: List[str] = []
        out: List[Dict[str, Any]] = []

        for m in messages or []:
            role = m.get("role")
            if role == "system":
                c = m.get("content")
                if isinstance(c, str) and c.strip():
                    system_parts.append(c.strip())
                continue

            if role == "tool":
                # OpenAI tool message: {role:"tool", tool_call_id, name, content}
                tool_use_id = m.get("tool_call_id") or m.get("id") or ""
                content = m.get("content") or ""
                if not isinstance(content, str):
                    content = str(content)
                out.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": content,
                            }
                        ],
                    }
                )
                continue

            if role == "assistant":
                blocks: List[Dict[str, Any]] = []
                c = m.get("content")
                if isinstance(c, str) and c.strip():
                    blocks.append({"type": "text", "text": c})

                tool_calls = m.get("tool_calls") or []
                if isinstance(tool_calls, list) and tool_calls:
                    for tc in tool_calls:
                        if not isinstance(tc, dict):
                            continue
                        fn = tc.get("function") or {}
                        name = fn.get("name")
                        if not isinstance(name, str) or not name:
                            continue
                        blocks.append(
                            {
                                "type": "tool_use",
                                "id": tc.get("id") or tc.get("tool_call_id") or "",
                                "name": name,
                                "input": self._parse_openai_tool_args(fn.get("arguments")),
                            }
                        )

                # Anthropic requires content; if empty, provide empty text.
                if not blocks:
                    blocks = [{"type": "text", "text": ""}]
                out.append({"role": "assistant", "content": blocks})
                continue

            # user (default)
            c = m.get("content")
            if isinstance(c, list):
                # Already blocks-ish; pass through best effort
                out.append({"role": "user", "content": c})
            else:
                out.append({"role": "user", "content": (c if isinstance(c, str) else str(c))})

        system = "\n\n".join(system_parts).strip() if system_parts else None
        return system if system else None, out

    @staticmethod
    def _to_anthropic_tool_choice(tool_choice: Any) -> Optional[Dict[str, Any]]:
        """
        Translate OpenAI tool_choice to Anthropic tool_choice (best effort).
        """
        if tool_choice is None:
            return None
        if isinstance(tool_choice, str):
            # Common OpenAI values: "auto", "none"
            if tool_choice in {"auto", "any"}:
                return {"type": "auto"}
            if tool_choice == "none":
                return {"type": "none"}
            return None
        if isinstance(tool_choice, dict):
            # OpenAI: {"type":"function","function":{"name":"X"}}
            try:
                if tool_choice.get("type") == "function":
                    name = (tool_choice.get("function") or {}).get("name")
                    if isinstance(name, str) and name:
                        return {"type": "tool", "name": name}
            except Exception:
                return None
        return None

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        reasoning_content: Optional[str] = None,
        thought_signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        temp = temperature if temperature is not None else self.temperature

        system, anthropic_messages = self._to_anthropic_messages(messages)
        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": int(getattr(config.llm, "max_tokens", 1024)),
            "messages": anthropic_messages,
            "temperature": temp,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = self._to_anthropic_tools(tools)
        tc = self._to_anthropic_tool_choice(tool_choice)
        if tc is not None:
            payload["tool_choice"] = tc

        logger.debug(
            "Sending Anthropic messages request",
            extra={
                "event": "llm_request",
                "provider": "anthropic",
                "model": self.model,
                "messages_count": len(anthropic_messages),
                "tools_count": len(payload.get("tools", []) or []),
                "has_system": bool(system),
            },
        )

        self._sleep_if_globally_rate_limited()
        max_retries = max(0, int(self.max_retries))
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                resp = self._client.post("/v1/messages", json=payload, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
                return self._to_openai_compatible_response(data)
            except httpx.HTTPStatusError as e:
                last_exc = e
                status = e.response.status_code if e.response is not None else None
                retry_after = self._parse_retry_after_seconds(e.response) if e.response is not None else None
                if (
                    status is not None
                    and self._should_retry_status(int(status))
                    and attempt < max_retries
                ):
                    wait_time = self._compute_backoff_seconds(attempt, retry_after_seconds=retry_after)
                    if int(status) == 429:
                        self._bump_global_rate_limit(wait_time)
                    logger.warning(
                        f"Anthropic API transient error {status}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})",
                        extra={
                            "event": "api_error_retry",
                            "provider": "anthropic",
                            "status_code": status,
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                            "retry_after_seconds": retry_after,
                        },
                    )
                    self._sleep(wait_time)
                    continue
                raise
            except httpx.ReadTimeout as e:
                last_exc = e
                if attempt < max_retries:
                    wait_time = self._compute_backoff_seconds(attempt, retry_after_seconds=None)
                    logger.warning(
                        f"Anthropic API timeout, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})",
                        extra={
                            "event": "api_timeout_retry",
                            "provider": "anthropic",
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                        },
                    )
                    self._sleep(wait_time)
                    continue
                raise TimeoutError("Anthropic request timed out") from e
            except httpx.RequestError as e:
                last_exc = e
                if attempt < max_retries:
                    wait_time = self._compute_backoff_seconds(attempt, retry_after_seconds=None)
                    logger.warning(
                        f"Anthropic network error, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})",
                        extra={
                            "event": "api_network_retry",
                            "provider": "anthropic",
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                        },
                    )
                    self._sleep(wait_time)
                    continue
                raise ConnectionError(f"Network error: {e}") from e

        # Should be unreachable.
        if isinstance(last_exc, httpx.ReadTimeout):
            raise TimeoutError("Anthropic request timed out") from last_exc
        if isinstance(last_exc, httpx.RequestError):
            raise ConnectionError(f"Network error: {last_exc}") from last_exc
        raise RuntimeError("Anthropic request failed") from last_exc

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        reasoning_content: Optional[str] = None,
        thought_signature: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream text deltas from Anthropic.

        Note: Broca uses streaming primarily for final responses; tool use via streaming
        is not supported in this helper (it ignores tool_use/tool_result events).
        
        Note: tool_choice parameter is accepted for Protocol compatibility but is not
        supported by Anthropic's streaming API and will be ignored.
        """
        temp = temperature if temperature is not None else self.temperature
        system, anthropic_messages = self._to_anthropic_messages(messages)
        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": int(getattr(config.llm, "max_tokens", 1024)),
            "messages": anthropic_messages,
            "temperature": temp,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = self._to_anthropic_tools(tools)
        self._sleep_if_globally_rate_limited()
        max_retries = max(0, int(self.max_retries))
        for attempt in range(max_retries + 1):
            yielded_any = False
            try:
                with self._client.stream("POST", "/v1/messages", json=payload, headers=self._headers()) as r:
                    r.raise_for_status()
                    for raw in r.iter_lines():
                        if not raw:
                            continue
                        line = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
                        line = line.strip()
                        # Anthropic streaming is SSE: "event:" and "data:" lines.
                        if line.startswith("event:"):
                            continue
                        if not line.startswith("data:"):
                            continue
                        data_str = line[len("data:") :].strip()
                        if not data_str:
                            continue
                        try:
                            evt = json.loads(data_str)
                        except Exception:
                            continue

                        etype = evt.get("type")
                        if etype == "message_stop":
                            return
                        if etype == "error":
                            try:
                                err = evt.get("error") or {}
                                msg = err.get("message") or "Anthropic stream error"
                            except Exception:
                                msg = "Anthropic stream error"
                            raise RuntimeError(msg)

                        if etype == "content_block_delta":
                            delta = evt.get("delta") or {}
                            if delta.get("type") == "text_delta":
                                text = delta.get("text")
                                if isinstance(text, str) and text:
                                    yielded_any = True
                                    yield text
                            continue
                return
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response is not None else None
                retry_after = self._parse_retry_after_seconds(e.response) if e.response is not None else None
                if (
                    not yielded_any
                    and status is not None
                    and self._should_retry_status(int(status))
                    and attempt < max_retries
                ):
                    wait_time = self._compute_backoff_seconds(attempt, retry_after_seconds=retry_after)
                    if int(status) == 429:
                        self._bump_global_rate_limit(wait_time)
                    logger.warning(
                        f"Anthropic stream transient error {status}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})",
                        extra={
                            "event": "api_error_retry_stream",
                            "provider": "anthropic",
                            "status_code": status,
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                            "retry_after_seconds": retry_after,
                        },
                    )
                    self._sleep(wait_time)
                    continue
                raise
            except httpx.ReadTimeout as e:
                if not yielded_any and attempt < max_retries:
                    wait_time = self._compute_backoff_seconds(attempt, retry_after_seconds=None)
                    logger.warning(
                        f"Anthropic stream timeout, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})",
                        extra={
                            "event": "api_timeout_retry_stream",
                            "provider": "anthropic",
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                        },
                    )
                    self._sleep(wait_time)
                    continue
                raise TimeoutError("Anthropic request timed out") from e
            except httpx.RequestError as e:
                if not yielded_any and attempt < max_retries:
                    wait_time = self._compute_backoff_seconds(attempt, retry_after_seconds=None)
                    logger.warning(
                        f"Anthropic stream network error, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})",
                        extra={
                            "event": "api_network_retry_stream",
                            "provider": "anthropic",
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                        },
                    )
                    self._sleep(wait_time)
                    continue
                raise ConnectionError(f"Network error: {e}") from e

    @staticmethod
    def _to_openai_compatible_response(anthropic_resp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Anthropic Messages API response to OpenAI-chat-completions-like shape
        expected by Broca's extract_* helpers.
        """
        content_blocks = anthropic_resp.get("content") or []
        # Produce assistant content as a best-effort concatenation of text blocks.
        text_parts: List[str] = []
        tool_calls: List[Dict[str, Any]] = []
        if isinstance(content_blocks, list):
            for b in content_blocks:
                if not isinstance(b, dict):
                    continue
                btype = b.get("type")
                if btype == "text":
                    t = b.get("text")
                    if isinstance(t, str):
                        text_parts.append(t)
                elif btype == "tool_use":
                    tool_calls.append(
                        {
                            "id": b.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": b.get("name", ""),
                                "arguments": json.dumps(b.get("input") or {}),
                            },
                        }
                    )

        message: Dict[str, Any] = {"role": "assistant", "content": "".join(text_parts) if text_parts else None}
        if tool_calls:
            message["tool_calls"] = tool_calls
            # In OpenAI schema, content is often None when tool_calls exist.
            if not text_parts:
                message["content"] = None

        return {"choices": [{"message": message}], "usage": anthropic_resp.get("usage", {})}

    @staticmethod
    def extract_assistant_content(response: Dict[str, Any]) -> str:
        try:
            return response["choices"][0]["message"].get("content") or ""
        except Exception:
            return ""

    @staticmethod
    def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            msg = response.get("choices", [{}])[0].get("message", {}) or {}
            calls = msg.get("tool_calls") or []
            return calls if isinstance(calls, list) else []
        except Exception:
            return []

