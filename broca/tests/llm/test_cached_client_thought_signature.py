from __future__ import annotations

from broca.llm.cached_client import CachedLLMClient
from broca.llm.gemini_client import GeminiClient


def test_cached_client_delegates_extract_thought_signature():
    underlying = GeminiClient(api_key="test-key", base_url="https://example.com", model="gemini-3.0-flash-001", use_sdk=False)
    cached = CachedLLMClient(underlying=underlying, world_state_aggregator=None, scope="test")

    resp = {
        "choices": [{"message": {"role": "assistant", "content": "hi"}}],
        "thought_signature": "sig-123",
    }
    assert cached.extract_thought_signature(resp) == "sig-123"

