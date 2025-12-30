import json
from typing import Any, Dict, List, Optional

import pytest

from broca.llm.cached_client import CachedLLMClient
import broca.llm.cache as cache_mod


class FakeLLM:
    def __init__(self, model: Optional[str] = "fake-model") -> None:
        self.model = model
        self.call_count = 0
        self._last_request: Dict[str, Any] = {}

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_content: Optional[str] = None,
        thought_signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.call_count += 1
        self._last_request = {
            "messages": messages,
            "temperature": temperature,
            "tools": tools,
            "reasoning_content": reasoning_content,
        }
        return {"id": self.call_count, "content": f"response-{self.call_count}"}


class FakeAggregator:
    def __init__(self, world_state: Dict[str, Any]):
        self._world_state = world_state
        self.call_count = 0

    def aggregate(self) -> Dict[str, Any]:
        self.call_count += 1
        return self._world_state


class FailingAggregator:
    def aggregate(self) -> Dict[str, Any]:  # pragma: no cover - error path
        raise RuntimeError("failed to aggregate world state")


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    """Isolate cache by redirecting to an in-memory dict.

    We monkeypatch get_cached_response / store_cached_response so tests do not
    touch the real SQLite cache on disk.
    """

    store: Dict[str, Dict[str, Any]] = {}

    def fake_get_cached_response(key: str) -> Optional[Dict[str, Any]]:
        entry = store.get(key)
        if entry is None:
            return None
        # Return a deep-ish copy to avoid mutation issues
        return json.loads(json.dumps(entry["response"]))

    def fake_store_cached_response(
        key: str,
        model: str,
        scope: Optional[str],
        request_meta: Dict[str, Any],
        response: Dict[str, Any],
    ) -> None:
        store[key] = {
            "model": model,
            "scope": scope,
            "request_meta": json.loads(json.dumps(request_meta)),
            "response": json.loads(json.dumps(response)),
        }

    monkeypatch.setattr(cache_mod, "get_cached_response", fake_get_cached_response)
    monkeypatch.setattr(cache_mod, "store_cached_response", fake_store_cached_response)

    # Also patch the names imported into cached_client module
    import broca.llm.cached_client as cc_mod

    monkeypatch.setattr(cc_mod, "get_cached_response", fake_get_cached_response)
    monkeypatch.setattr(cc_mod, "store_cached_response", fake_store_cached_response)

    return store


def test_cache_hit_same_world_state(isolated_cache):
    agg = FakeAggregator({"timestamp": "2025-01-01T00:00:00Z", "value": 1})
    underlying = FakeLLM()

    client = CachedLLMClient(
        underlying=underlying,
        world_state_aggregator=agg,
        scope="broca:test",
    )

    messages = [{"role": "user", "content": "Hello"}]

    first = client.chat(messages=messages, temperature=0.1, tools=None)
    second = client.chat(messages=messages, temperature=0.1, tools=None)

    assert underlying.call_count == 1
    assert first == second

    # Inspect stored request_meta to ensure world_state fingerprint and scope
    # are present and stable across calls.
    assert len(isolated_cache) == 1
    (key, entry), = isolated_cache.items()
    meta = entry["request_meta"]
    assert meta["scope"] == "broca:test"
    assert meta["world_state_fp"] != "no_world_state"
    assert meta["messages_hash"]
    assert meta["tools_hash"] == "none"


def test_cache_miss_different_world_state(isolated_cache):
    agg1 = FakeAggregator({"timestamp": "2025-01-01T00:00:00Z", "value": 1})
    agg2 = FakeAggregator({"timestamp": "2025-01-01T00:01:00Z", "value": 2})

    underlying = FakeLLM()

    client1 = CachedLLMClient(underlying=underlying, world_state_aggregator=agg1, scope="broca:test")
    client2 = CachedLLMClient(underlying=underlying, world_state_aggregator=agg2, scope="broca:test")

    messages = [{"role": "user", "content": "Hello"}]

    r1 = client1.chat(messages=messages, temperature=0.1, tools=None)
    r2 = client2.chat(messages=messages, temperature=0.1, tools=None)

    assert underlying.call_count == 2
    assert r1 != r2

    # Expect two different cache entries for the two aggregators.
    # The world_state_fingerprint helper may bucket or de-noise fields
    # (e.g., timestamps), so we only require that the cache entries and
    # their descriptors are distinct, not necessarily that the raw
    # world_state_fp strings differ.
    assert len(isolated_cache) == 2
    metas = [entry["request_meta"] for entry in isolated_cache.values()]
    assert metas[0] != metas[1]


def test_aggregator_failure_uses_no_world_state(isolated_cache, monkeypatch):
    # Ensure that when the aggregator fails, we still proceed and use a
    # descriptor that yields a stable cache key ("no_world_state").
    failing_agg = FailingAggregator()
    underlying = FakeLLM()

    client = CachedLLMClient(underlying=underlying, world_state_aggregator=failing_agg, scope="broca:test")

    messages = [{"role": "user", "content": "Hi"}]

    first = client.chat(messages=messages, temperature=0.2, tools=None)
    second = client.chat(messages=messages, temperature=0.2, tools=None)

    # Even though aggregator fails, we should still get caching behaviour
    assert underlying.call_count == 1
    assert first == second

    # And the stored descriptor should indicate that no world state was used.
    assert len(isolated_cache) == 1
    (key, entry), = isolated_cache.items()
    assert entry["request_meta"]["world_state_fp"] == "no_world_state"


def test_scope_separates_cache_entries(isolated_cache):
    agg = FakeAggregator({"timestamp": "2025-01-01T00:00:00Z", "value": 1})
    underlying = FakeLLM()

    client1 = CachedLLMClient(underlying=underlying, world_state_aggregator=agg, scope="broca:scope1")
    client2 = CachedLLMClient(underlying=underlying, world_state_aggregator=agg, scope="broca:scope2")

    messages = [{"role": "user", "content": "Hello"}]

    r1 = client1.chat(messages=messages, temperature=0.1, tools=None)
    r2 = client2.chat(messages=messages, temperature=0.1, tools=None)

    assert underlying.call_count == 2
    assert r1 != r2

    scopes = {entry["scope"] for entry in isolated_cache.values()}
    assert scopes == {"broca:scope1", "broca:scope2"}


def test_tools_and_temperature_affect_cache_key(isolated_cache):
    agg = FakeAggregator({"timestamp": "2025-01-01T00:00:00Z", "value": 1})
    underlying = FakeLLM()
    client = CachedLLMClient(underlying=underlying, world_state_aggregator=agg, scope="broca:test")

    messages = [{"role": "user", "content": "Hello"}]

    tools1 = [{"name": "tool_a", "description": "A"}]
    tools2 = [{"name": "tool_b", "description": "B"}]

    # Same messages, world_state, and scope, but different tools and temperatures
    r1 = client.chat(messages=messages, temperature=0.1, tools=tools1)
    r2 = client.chat(messages=messages, temperature=0.1, tools=tools2)
    r3 = client.chat(messages=messages, temperature=0.9, tools=tools1)

    assert underlying.call_count == 3
    assert {r1["id"], r2["id"], r3["id"]} == {1, 2, 3}

    # We expect three distinct cache entries because tools_hash and params.temperature
    # are part of the descriptor used for the cache key.
    assert len(isolated_cache) == 3

    metas = list(entry["request_meta"] for entry in isolated_cache.values())
    tools_hashes = {m["tools_hash"] for m in metas}
    temps = {m["params"]["temperature"] for m in metas}

    assert len(tools_hashes) == 2  # tools1 vs tools2
    assert temps == {0.1, 0.9}
