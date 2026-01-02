from __future__ import annotations

from typing import List, Dict, Any, Optional, Iterator
import json
import logging

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

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        anthropic_version: Optional[str] = None,
        anthropic_beta: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or config.llm.api_key
        self.base_url = base_url or config.llm.api_base
        self.model = model or config.llm.model
        self.temperature = temperature if temperature is not None else config.llm.temperature
        timeout_value = timeout if timeout is not None else config.llm.timeout
        self.anthropic_version = anthropic_version or getattr(config.llm, "anthropic_version", "2023-06-01")
        self.anthropic_beta = anthropic_beta or getattr(config.llm, "anthropic_beta", None)

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_value, connect=10.0),
        )

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

        try:
            resp = self._client.post("/v1/messages", json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
            return self._to_openai_compatible_response(data)
        except httpx.ReadTimeout as e:
            raise TimeoutError("Anthropic request timed out") from e
        except httpx.RequestError as e:
            raise ConnectionError(f"Network error: {e}") from e
        except httpx.HTTPStatusError:
            raise

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
        thought_signature: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream text deltas from Anthropic.

        Note: Broca uses streaming primarily for final responses; tool use via streaming
        is not supported in this helper (it ignores tool_use/tool_result events).
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

        with self._client.stream("POST", "/v1/messages", json=payload, headers=self._headers()) as r:
            r.raise_for_status()
            for raw in r.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
                line = line.strip()
                # Anthropic streaming is SSE: "event:" and "data:" lines.
                if line.startswith("event:"):
                    # We rely on JSON 'type' for behavior; event name is informational.
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
                    # Surface error as a best-effort exception to callers.
                    try:
                        err = evt.get("error") or {}
                        msg = err.get("message") or "Anthropic stream error"
                    except Exception:
                        msg = "Anthropic stream error"
                    raise RuntimeError(msg)

                # Text deltas arrive as content_block_delta/text_delta.
                if etype == "content_block_delta":
                    delta = evt.get("delta") or {}
                    if delta.get("type") == "text_delta":
                        text = delta.get("text")
                        if isinstance(text, str) and text:
                            yield text
                    # Tool input JSON arrives as input_json_delta; ignore here (tool calls
                    # are handled via non-streaming fallback in ConversationSession).
                    continue

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

