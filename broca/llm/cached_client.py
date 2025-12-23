from __future__ import annotations

"""Cached LLM client that respects world_state in its cache key.

This wraps an underlying LLM-like implementation and adds a
world-state-aware request-level cache using broca.llm.cache.
"""

from typing import List, Dict, Any, Optional, Protocol
import hashlib
import json
import logging

from .cache import get_cached_response, store_cached_response
from ..world_state.aggregator import WorldStateAggregator
from ..world_state.cache_fingerprint import world_state_fingerprint

logger = logging.getLogger(__name__)


class LLMLike(Protocol):
    """Minimal protocol for the underlying LLM client.

    We intentionally keep this local to avoid importing broca.llm at
    module import time, which would create a circular dependency.
    """

    model: Optional[str]

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    @staticmethod
    def extract_assistant_content(response: Dict[str, Any]) -> str:  # pragma: no cover - thin wrapper
        ...

    @staticmethod
    def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:  # pragma: no cover - thin wrapper
        ...


def _hash_messages(messages: List[Dict[str, str]]) -> str:
    payload = json.dumps(messages, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _hash_tools(tools: Optional[List[Dict[str, Any]]]) -> str:
    if not tools:
        return "none"
    payload = json.dumps(tools, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CachedLLMClient:
    """LLM-like client that adds world-state-aware caching.

    It is designed to be drop-in compatible with the LLMClient protocol
    defined in broca.llm.__init__, but we don't import that here to avoid
    circular imports.
    """

    def __init__(
        self,
        underlying: LLMLike,
        world_state_aggregator: Optional[WorldStateAggregator] = None,
        scope: str = "broca:default",
    ) -> None:
        self._underlying = underlying
        self._world_state_aggregator = world_state_aggregator
        self._scope = scope

    @property
    def model(self) -> Optional[str]:
        # Best-effort: many clients expose .model
        return getattr(self._underlying, "model", None)

    def _build_descriptor(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: Optional[float],
    ) -> Dict[str, Any]:
        # Aggregate world state if available
        world_state: Dict[str, Any] = {}
        if self._world_state_aggregator is not None:
            try:
                world_state = self._world_state_aggregator.aggregate()
            except Exception as e:  # pragma: no cover - defensive logging
                logger.debug(
                    f"Error aggregating world state for cache: {e}",
                    exc_info=True,
                )

        ws_fp = world_state_fingerprint(world_state) if world_state else "no_world_state"

        descriptor: Dict[str, Any] = {
            "model": self.model,
            "scope": self._scope,
            "world_state_fp": ws_fp,
            "messages_hash": _hash_messages(messages),
            "tools_hash": _hash_tools(tools),
            "params": {
                "temperature": temperature,
            },
        }

        # For auditability, we also include the raw world_state timestamp if present.
        if world_state:
            ts = world_state.get("timestamp")
            if isinstance(ts, str):
                descriptor["world_state_timestamp"] = ts

        return descriptor

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        descriptor = self._build_descriptor(messages, tools=tools, temperature=temperature)
        key_json = json.dumps(descriptor, sort_keys=True, separators=(",", ":"))
        cache_key = hashlib.sha256(key_json.encode("utf-8")).hexdigest()

        cached = get_cached_response(cache_key)
        if cached is not None:
            logger.info(
                "LLM cache hit",
                extra={
                    "event": "llm_cache_hit",
                    "scope": self._scope,
                    "model": self.model,
                },
            )
            return cached

        # Cache miss: delegate to underlying client
        response = self._underlying.chat(
            messages=messages,
            temperature=temperature,
            tools=tools,
            reasoning_content=reasoning_content,
        )

        store_cached_response(
            key=cache_key,
            model=self.model or "",
            scope=self._scope,
            request_meta=descriptor,
            response=response,
        )

        logger.info(
            "LLM cache miss - stored new entry",
            extra={
                "event": "llm_cache_store",
                "scope": self._scope,
                "model": self.model,
            },
        )
        return response

    @staticmethod
    def extract_assistant_content(response: Dict[str, Any]) -> str:
        """Delegate extraction to the default client implementation.

        We import here to avoid broca.llm imports at module import time.
        """
        from .openai_client import OpenAIClient  # local import to avoid cycles

        return OpenAIClient.extract_assistant_content(response)

    @staticmethod
    def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .openai_client import OpenAIClient  # local import to avoid cycles

        return OpenAIClient.extract_tool_calls(response)
