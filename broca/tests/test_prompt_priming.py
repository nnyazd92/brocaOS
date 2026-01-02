"""
Tests for prompt priming ("PRIMED MEMORY") behavior.

Implements TDD coverage for:
- Session-scoped primed memory in world state aggregation
- ConversationSession integration (priming on user prompts)
- Skip logic for internal simulated monologue prompts
- Fault injection (memory retrieval failures)
"""

from __future__ import annotations

import json
from unittest.mock import Mock

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume

from broca.config import config
from broca.memory import MemoryRecord
from broca.memory import RelationshipRecord, RelationType
from broca.memory.priming import (
    build_cue_query,
    build_structured_priming_card,
    build_priming_card,
    mmr_select,
)
from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator


def _extract_world_state_json(system_prompt: str) -> dict:
    json_start = system_prompt.find("{")
    assert json_start != -1, "Expected JSON world state in system prompt"
    return json.loads(system_prompt[json_start:])


def test_world_state_primed_memory_is_session_scoped(tmp_path):
    agg = WorldStateAggregator(shared_state_path=tmp_path / "shared_state.json")

    agg.set_primed_memory(
        session_id="s1",
        query_preview="q",
        memory_id=123,
        namespace="n1",
        text="hello",
        truncated=False,
    )

    assert "primed_memory" in agg.aggregate(session_id="s1")
    assert "primed_memory" not in agg.aggregate(session_id="s2")
    assert "primed_memory" not in agg.aggregate()

    agg.clear_primed_memory("s1")
    assert "primed_memory" not in agg.aggregate(session_id="s1")


@given(
    session_id_a=st.text(min_size=1, max_size=30),
    session_id_b=st.text(min_size=1, max_size=30),
    memory_text=st.text(min_size=1, max_size=200),
)
@settings(
    max_examples=60,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_world_state_primed_memory_session_scoping_property(tmp_path, session_id_a, session_id_b, memory_text):
    assume(session_id_a.strip())
    assume(session_id_b.strip())
    assume(session_id_a.strip() != session_id_b.strip())

    agg = WorldStateAggregator(shared_state_path=tmp_path / "shared_state.json")
    agg.set_primed_memory(
        session_id=session_id_a,
        query_preview="q",
        memory_id=1,
        namespace="ns",
        text=memory_text,
        truncated=False,
    )

    ws_a = agg.aggregate(session_id=session_id_a)
    ws_b = agg.aggregate(session_id=session_id_b)
    assert ws_a.get("primed_memory", {}).get("text")
    assert "primed_memory" not in ws_b


def test_conversation_session_primes_memory_and_injects_into_system_prompt(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_skip = config.memory.prompt_priming_skip_internal_monologue
    original_top_k = getattr(config.memory, "prompt_priming_top_k", 1)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    original_mmr_lambda = getattr(config.memory, "prompt_priming_mmr_lambda", 0.7)
    original_graph_hops = getattr(config.memory, "prompt_priming_graph_hops", 0)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_skip_internal_monologue = True
        config.memory.prompt_priming_top_k = 3
        config.memory.prompt_priming_max_items = 2
        config.memory.prompt_priming_mmr_lambda = 0.5
        config.memory.prompt_priming_graph_hops = 0

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                # Deterministic query embedding.
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def __init__(self):
                self._vectors = {
                    1: [0.8, 0.6, 0.0],   # A
                    2: [0.79, 0.61, 0.0],  # B (near-duplicate of A)
                    3: [0.7, 0.0, 0.714],  # C (diverse)
                }

            def get_vector_by_memory_id(self, memory_id: int):
                return self._vectors.get(int(memory_id))

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                # Return a fixed candidate set, already ranked by relevance.
                candidates = [
                    MemoryRecord(id=1, namespace="test.ns", text="MEM_A", importance=0.5),
                    MemoryRecord(id=2, namespace="test.ns", text="MEM_B", importance=0.5),
                    MemoryRecord(id=3, namespace="test.ns", text="MEM_C", importance=0.5),
                ]
                return candidates[: int(limit)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(
            llm=llm,
            world_state_aggregator=agg,
            base_system_prompt="Base prompt",
            session_id="s1",
        )

        session._prime_memory_for_user_prompt("Tell me about Q", hidden_user_message=False)
        session._update_system_prompt()

        ws = agg.aggregate(session_id="s1")
        assert ws["primed_memory"]["items"][0]["id"] == 1
        assert ws["primed_memory"]["items"][1]["id"] == 3
        assert "PRIMED MEMORY" in ws["primed_memory"]["text"]
        # Structured card may not include raw memory text; it must include provenance.
        assert "id=1" in ws["primed_memory"]["text"]
        assert "id=3" in ws["primed_memory"]["text"]

        system_prompt = session.messages[0]["content"]
        parsed = _extract_world_state_json(system_prompt)
        assert "primed_memory" in parsed
        assert "primed_memory_prompt" in parsed
        assert "PRIMED MEMORY:" in parsed["primed_memory_prompt"]
        assert "id=1" in parsed["primed_memory_prompt"]
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_skip_internal_monologue = original_skip
        config.memory.prompt_priming_top_k = original_top_k
        config.memory.prompt_priming_max_items = original_max_items
        config.memory.prompt_priming_mmr_lambda = original_mmr_lambda
        config.memory.prompt_priming_graph_hops = original_graph_hops


def test_prompt_priming_skips_internal_simulated_monologue(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_skip = config.memory.prompt_priming_skip_internal_monologue
    original_thought_enabled = getattr(config.memory, "thought_priming_enabled", False)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_skip_internal_monologue = True
        config.memory.thought_priming_enabled = False

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [MemoryRecord(id=1, namespace="ns", text="A", importance=0.5)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")

        # Seed primed memory.
        session._prime_memory_for_user_prompt("user prompt", hidden_user_message=False)
        assert "primed_memory" in agg.aggregate(session_id="s1")

        # Internal monologue prompt should not re-prime (and should not call retrieval).
        internal = "INTERNAL SIMULATED MONOLOGUE (Recursive Thought Loop)\nfoo"
        session._prime_memory_for_user_prompt(internal, hidden_user_message=False)
        assert agg.aggregate(session_id="s1")["primed_memory"]["items"][0]["id"] == 1
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_skip_internal_monologue = original_skip
        config.memory.thought_priming_enabled = original_thought_enabled


def test_thought_priming_opt_in_sets_thought_slot(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_skip = config.memory.prompt_priming_skip_internal_monologue
    original_thought_enabled = getattr(config.memory, "thought_priming_enabled", False)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_skip_internal_monologue = True
        config.memory.thought_priming_enabled = True

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [MemoryRecord(id=1, namespace="ns", text="A", importance=0.5)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        internal = "INTERNAL SIMULATED MONOLOGUE (Recursive Thought Loop)\nfoo"
        session._prime_memory_for_user_prompt(internal, hidden_user_message=False)

        ws = agg.aggregate(session_id="s1")
        assert "primed_memory_thought" in ws
        assert "PRIMED MEMORY" in ws["primed_memory_thought"]["text"]
        # Should not set chat/legacy slots for thought priming.
        assert "primed_memory_chat" not in ws
        assert "primed_memory" not in ws
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_skip_internal_monologue = original_skip
        config.memory.thought_priming_enabled = original_thought_enabled


def test_prompt_priming_fault_injection_retrieve_failure_clears(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    try:
        config.memory.prompt_priming_enabled = True

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()
                self._fail = False

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                if self._fail:
                    raise RuntimeError("boom")
                return [MemoryRecord(id=1, namespace="ns", text="A", importance=0.5)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")

        session._prime_memory_for_user_prompt("user prompt", hidden_user_message=False)
        assert "primed_memory" in agg.aggregate(session_id="s1")

        mm._fail = True
        session._prime_memory_for_user_prompt("new prompt", hidden_user_message=False)
        assert "primed_memory" not in agg.aggregate(session_id="s1")
    finally:
        config.memory.prompt_priming_enabled = original_enabled


def test_prompt_priming_fault_injection_embedding_failure_clears(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    try:
        config.memory.prompt_priming_enabled = True

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def __init__(self):
                self.fail = False

            def generate_embedding(self, text: str):
                if self.fail:
                    raise RuntimeError("embedding boom")
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [MemoryRecord(id=1, namespace="ns", text="A", importance=0.5)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")

        session._prime_memory_for_user_prompt("user prompt", hidden_user_message=False)
        assert "primed_memory" in agg.aggregate(session_id="s1")

        mm.embedding_service.fail = True
        session._prime_memory_for_user_prompt("new prompt", hidden_user_message=False)
        assert "primed_memory" not in agg.aggregate(session_id="s1")
    finally:
        config.memory.prompt_priming_enabled = original_enabled


def test_prompt_priming_self_hit_is_skipped(tmp_path):
    """
    If the top retrieved memory is basically the prompt itself (e.g., exact text match),
    we should skip it to reduce interference.
    """
    original_enabled = config.memory.prompt_priming_enabled
    original_skip = config.memory.prompt_priming_skip_internal_monologue
    original_top_k = getattr(config.memory, "prompt_priming_top_k", 1)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_skip_internal_monologue = True
        config.memory.prompt_priming_top_k = 3
        config.memory.prompt_priming_max_items = 1

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def __init__(self):
                self._vectors = {
                    1: [1.0, 0.0, 0.0],
                    2: [0.9, 0.1, 0.0],
                }

            def get_vector_by_memory_id(self, memory_id: int):
                return self._vectors.get(int(memory_id))

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                # Candidate 1 is an exact echo of the user prompt ("self-hit").
                # Candidate 2 is the next best actual memory.
                return [
                    MemoryRecord(id=1, namespace="ns", text="Tell me about Q", importance=0.5),
                    MemoryRecord(id=2, namespace="ns", text="ACTUAL_MEM", importance=0.5),
                ][: int(limit)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        session._prime_memory_for_user_prompt("Tell me about Q", hidden_user_message=False)

        ws = agg.aggregate(session_id="s1")
        assert ws["primed_memory"]["items"][0]["id"] == 2
        # Ensure debug metadata is present and reports the skip.
        assert ws["primed_memory"]["selection"]["debug"]["self_hit_skipped_count"] == 1
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_skip_internal_monologue = original_skip
        config.memory.prompt_priming_top_k = original_top_k
        config.memory.prompt_priming_max_items = original_max_items


def test_prompt_priming_repeats_are_downweighted_across_topic_shift(tmp_path):
    """
    If the same memory keeps winning, but the user changes topic, we should rotate/downweight
    the repeat to reduce interference.
    """
    original_enabled = config.memory.prompt_priming_enabled
    original_skip = config.memory.prompt_priming_skip_internal_monologue
    original_top_k = getattr(config.memory, "prompt_priming_top_k", 1)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    original_graph_hops = getattr(config.memory, "prompt_priming_graph_hops", 0)
    original_interference_weight = getattr(config.memory, "prompt_priming_interference_weight", 0.0)
    original_repeat_weight = getattr(config.memory, "prompt_priming_topic_repeat_penalty_weight", 0.0)
    original_topic_thr = getattr(config.memory, "prompt_priming_topic_jaccard_threshold", 0.35)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_skip_internal_monologue = True
        config.memory.prompt_priming_top_k = 3
        config.memory.prompt_priming_max_items = 1
        config.memory.prompt_priming_graph_hops = 0
        config.memory.prompt_priming_interference_weight = 0.0  # isolate repeat penalty
        config.memory.prompt_priming_topic_repeat_penalty_weight = 10.0
        config.memory.prompt_priming_topic_jaccard_threshold = 0.9  # make different intents count as shift

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def __init__(self):
                self._vectors = {
                    1: [1.0, 0.0, 0.0],   # best match
                    2: [0.95, 0.05, 0.0],  # almost as good
                }

            def get_vector_by_memory_id(self, memory_id: int):
                return self._vectors.get(int(memory_id))

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [
                    MemoryRecord(id=1, namespace="ns", text="MEM_1", importance=0.5),
                    MemoryRecord(id=2, namespace="ns", text="MEM_2", importance=0.5),
                ][: int(limit)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")

        # First topic -> should pick 1.
        session._prime_memory_for_user_prompt("Build a parser", hidden_user_message=False)
        ws1 = agg.aggregate(session_id="s1")
        assert ws1["primed_memory"]["items"][0]["id"] == 1

        # New topic shift -> should rotate away from 1 (repeat-penalized) to 2.
        session._prime_memory_for_user_prompt("Write unit tests", hidden_user_message=False)
        ws2 = agg.aggregate(session_id="s1")
        assert ws2["primed_memory"]["items"][0]["id"] == 2
        assert ws2["primed_memory"]["selection"]["debug"]["topic_changed"] is True
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_skip_internal_monologue = original_skip
        config.memory.prompt_priming_top_k = original_top_k
        config.memory.prompt_priming_max_items = original_max_items
        config.memory.prompt_priming_graph_hops = original_graph_hops
        config.memory.prompt_priming_interference_weight = original_interference_weight
        config.memory.prompt_priming_topic_repeat_penalty_weight = original_repeat_weight
        config.memory.prompt_priming_topic_jaccard_threshold = original_topic_thr


def test_build_cue_query_contains_required_sections():
    cue_text, cue = build_cue_query(
        user_text="Implement foo in src/app.py and don't break tests; run pytest",
        recent_messages=[
            {"role": "assistant", "content": "What do you want to do next?"},
            {"role": "user", "content": "Fix the bug."},
        ],
        affect={"valence": -0.2, "arousal": 0.7},
        goals=["Ship feature X"],
    )
    assert isinstance(cue_text, str) and cue_text
    assert "USER_PROMPT:" in cue_text
    assert "TASK_TYPE:" in cue_text
    assert "GOALS:" in cue_text
    assert "INTENT:" in cue_text
    assert "ENTITIES:" in cue_text
    assert "CONSTRAINTS:" in cue_text
    assert "AFFECT:" in cue_text
    assert "src/app.py" in cue_text
    assert isinstance(cue, dict)


def test_prime_memory_uses_cue_query_for_embedding(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_graph_hops = getattr(config.memory, "prompt_priming_graph_hops", 0)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_graph_hops = 0

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def __init__(self):
                self.last_text = None

            def generate_embedding(self, text: str):
                self.last_text = text
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [MemoryRecord(id=1, namespace="ns", text="A", importance=0.5)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        session._prime_memory_for_user_prompt("Implement foo in src/app.py", hidden_user_message=False)

        assert isinstance(mm.embedding_service.last_text, str)
        assert "USER_PROMPT:" in mm.embedding_service.last_text
        assert "TASK_TYPE:" in mm.embedding_service.last_text
        assert "src/app.py" in mm.embedding_service.last_text
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_graph_hops = original_graph_hops


def test_spreading_activation_adds_one_hop_related(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_graph_hops = getattr(config.memory, "prompt_priming_graph_hops", 0)
    original_seed_count = getattr(config.memory, "prompt_priming_graph_seed_count", 1)
    original_graph_limit = getattr(config.memory, "prompt_priming_graph_limit", 5)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_graph_hops = 1
        config.memory.prompt_priming_graph_seed_count = 1
        config.memory.prompt_priming_graph_limit = 3
        config.memory.prompt_priming_max_items = 2

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def __init__(self):
                self.v = {
                    1: [1.0, 0.0, 0.0],  # seed
                    99: [0.0, 1.0, 0.0],  # diverse neighbor
                }

            def get_vector_by_memory_id(self, memory_id: int):
                return self.v.get(int(memory_id))

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [MemoryRecord(id=1, namespace="ns", text="SEED", importance=0.5)]

            def get_related_memories(self, memory_id: int, **kwargs):
                assert memory_id == 1
                rel = RelationshipRecord(
                    source_id=1,
                    target_id=99,
                    relation_type=RelationType.ELABORATES,
                    strength=1.0,
                    bidirectional=False,
                )
                return [(MemoryRecord(id=99, namespace="ns", text="NEIGHBOR", importance=0.5), rel)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        session._prime_memory_for_user_prompt("Tell me about seed", hidden_user_message=False)

        ws = agg.aggregate(session_id="s1")
        ids = [it.get("id") for it in ws["primed_memory"]["items"]]
        assert 1 in ids
        assert 99 in ids
        assert "NEIGHBOR" in ws["primed_memory"]["text"]
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_graph_hops = original_graph_hops
        config.memory.prompt_priming_graph_seed_count = original_seed_count
        config.memory.prompt_priming_graph_limit = original_graph_limit
        config.memory.prompt_priming_max_items = original_max_items


def test_spreading_activation_failure_does_not_clear_base_priming(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_graph_hops = getattr(config.memory, "prompt_priming_graph_hops", 0)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_graph_hops = 1

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [MemoryRecord(id=1, namespace="ns", text="A", importance=0.5)]

            def get_related_memories(self, memory_id: int, **kwargs):
                raise RuntimeError("graph boom")

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        session._prime_memory_for_user_prompt("user prompt", hidden_user_message=False)
        ws = agg.aggregate(session_id="s1")
        assert ws["primed_memory"]["items"][0]["id"] == 1
        assert "A" in ws["primed_memory"]["text"]
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_graph_hops = original_graph_hops


@given(
    user_text=st.text(min_size=1, max_size=500),
    valence=st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=60, suppress_health_check=[HealthCheck.too_slow])
def test_build_cue_query_property(user_text, valence):
    cue_text, cue = build_cue_query(user_text=user_text, recent_messages=None, affect={"valence": valence})
    assert isinstance(cue_text, str) and cue_text.endswith("\n")
    assert "USER_PROMPT:" in cue_text
    assert "TASK_TYPE:" in cue_text
    assert "AFFECT:" in cue_text
    assert isinstance(cue, dict)


def test_bm25_rerank_can_override_vector_ties(tmp_path):
    """
    Two-stage ranking: vector retrieval gives a candidate set; BM25 keyword scoring
    reranks within it so literal matches win in ties.
    """
    original_enabled = config.memory.prompt_priming_enabled
    original_top_k = getattr(config.memory, "prompt_priming_top_k", 8)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    original_bm25_weight = getattr(config.memory, "prompt_priming_bm25_weight", 0.0)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_top_k = 2
        config.memory.prompt_priming_max_items = 1
        config.memory.prompt_priming_bm25_weight = 1.0

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                # Equal cosine similarity for both candidates.
                return [1.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [
                    MemoryRecord(id=1, namespace="ns", tags=["misc"], text="Unrelated content", importance=0.5),
                    MemoryRecord(id=2, namespace="ns", tags=["misc"], text="Contains magic_keyword here", importance=0.5),
                ][: int(limit)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        session._prime_memory_for_user_prompt("Find magic_keyword", hidden_user_message=False)
        ws = agg.aggregate(session_id="s1")
        assert ws["primed_memory"]["items"][0]["id"] == 2
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_top_k = original_top_k
        config.memory.prompt_priming_max_items = original_max_items
        config.memory.prompt_priming_bm25_weight = original_bm25_weight


def test_goal_congruency_biases_selection(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_top_k = getattr(config.memory, "prompt_priming_top_k", 8)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    original_goal_weight = getattr(config.memory, "prompt_priming_goal_weight", 0.0)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_top_k = 2
        config.memory.prompt_priming_max_items = 1
        config.memory.prompt_priming_goal_weight = 1.0

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [
                    MemoryRecord(id=1, namespace="ns", tags=["project:alpha"], text="general note", importance=0.5),
                    MemoryRecord(id=2, namespace="ns", tags=["goal:ship_feature_x"], text="feature X details", importance=0.5),
                ][: int(limit)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        # Inject a goal manager stub into the session.
        class _GM:
            def get_active_goals(self):
                return [{"goal": "Ship feature X"}]
        session._goal_manager = _GM()

        session._prime_memory_for_user_prompt("Work on this", hidden_user_message=False)
        ws = agg.aggregate(session_id="s1")
        assert ws["primed_memory"]["items"][0]["id"] == 2
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_top_k = original_top_k
        config.memory.prompt_priming_max_items = original_max_items
        config.memory.prompt_priming_goal_weight = original_goal_weight


def test_affect_congruency_biases_selection_via_tags(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_top_k = getattr(config.memory, "prompt_priming_top_k", 8)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    original_affect_weight = getattr(config.memory, "prompt_priming_affect_weight", 0.0)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_top_k = 2
        config.memory.prompt_priming_max_items = 1
        config.memory.prompt_priming_affect_weight = 1.0

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [
                    MemoryRecord(id=1, namespace="ns", tags=["valence:positive"], text="happy memory", importance=0.5),
                    MemoryRecord(id=2, namespace="ns", tags=["valence:negative"], text="sad memory", importance=0.5),
                ][: int(limit)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        # Provide an internal sensing framework stub with negative valence.
        class _Aff:
            affective_states = {"valence": -0.8}

        class _Intero:
            affect = _Aff()

        class _ISF:
            interoception = _Intero()

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1", internal_sensing_framework=_ISF())
        session._prime_memory_for_user_prompt("reflect", hidden_user_message=False)
        ws = agg.aggregate(session_id="s1")
        assert ws["primed_memory"]["items"][0]["id"] == 2
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_top_k = original_top_k
        config.memory.prompt_priming_max_items = original_max_items
        config.memory.prompt_priming_affect_weight = original_affect_weight


def test_structured_priming_card_contains_sections():
    card = build_structured_priming_card(
        query_preview="Fix bug",
        cue_meta={"task_type": "coding", "intent": "Fix bug", "entities": ["src/app.py"], "constraints": ["no regressions"], "affect": {"valence": -0.3}, "goals": ["Ship feature X"]},
        selection={"strategy": "topk"},
        items=[
            {
                "id": 1,
                "namespace": "ns",
                "text": "Line1.\nLine2.\nLine3.\nLine4.",
                "importance": 0.6,
                "created_at": "2024-01-01T00:00:00Z",
                "last_used_at": "2024-01-02T00:00:00Z",
                "source_type": "user",
                "why": {"sim": 0.8, "bm25": 0.2, "goal": 0.5, "affect": 0.6, "recency": 0.4, "usage": 0.7},
            }
        ],
        conflicts=[{"type": "contradicts", "id": 9, "preview": "Conflicting memory..."}],
        unknowns=["Need verification"],
    )
    assert "PRIMED MEMORY" in card
    assert "Why it matches" in card
    assert "Provenance" in card
    assert "Confidence" in card
    assert "Last used" in card
    assert "Key facts" in card
    assert "Action implications" in card
    assert "Known conflicts/unknowns" in card


def test_temporal_recency_bias_prefers_newer(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_top_k = getattr(config.memory, "prompt_priming_top_k", 8)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    original_recency_weight = getattr(config.memory, "prompt_priming_recency_weight", 0.0)
    original_usage_weight = getattr(config.memory, "prompt_priming_usage_weight", 0.0)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_top_k = 2
        config.memory.prompt_priming_max_items = 1
        config.memory.prompt_priming_recency_weight = 1.0
        config.memory.prompt_priming_usage_weight = 0.0

        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                older = MemoryRecord(id=1, namespace="ns", tags=[], text="OLD", importance=0.5, created_at=now - timedelta(days=10), last_used_at=now - timedelta(days=10))
                newer = MemoryRecord(id=2, namespace="ns", tags=[], text="NEW", importance=0.5, created_at=now - timedelta(hours=2), last_used_at=now - timedelta(days=10))
                return [older, newer][: int(limit)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        session._prime_memory_for_user_prompt("prompt", hidden_user_message=False)
        ws = agg.aggregate(session_id="s1")
        assert ws["primed_memory"]["items"][0]["id"] == 2
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_top_k = original_top_k
        config.memory.prompt_priming_max_items = original_max_items
        config.memory.prompt_priming_recency_weight = original_recency_weight
        config.memory.prompt_priming_usage_weight = original_usage_weight


def test_interference_penalty_eventually_rotates_winner(tmp_path):
    original_enabled = config.memory.prompt_priming_enabled
    original_top_k = getattr(config.memory, "prompt_priming_top_k", 8)
    original_max_items = getattr(config.memory, "prompt_priming_max_items", 1)
    original_interference_weight = getattr(config.memory, "prompt_priming_interference_weight", 0.0)
    try:
        config.memory.prompt_priming_enabled = True
        config.memory.prompt_priming_top_k = 2
        config.memory.prompt_priming_max_items = 1
        config.memory.prompt_priming_interference_weight = 1.0

        class _Storage:
            def get_schema_version(self):
                return 1

        class _NamespaceIndex:
            def get_last_indexed(self):
                return "2024-01-01T00:00:00Z"

            def get_namespace_hierarchy(self):
                return {}

        class _EmbeddingService:
            def generate_embedding(self, text: str):
                return [1.0, 0.0]

        class _VectorIndex:
            def get_vector_by_memory_id(self, memory_id: int):
                return [1.0, 0.0]

        class _MemoryManager:
            def __init__(self):
                self.storage = _Storage()
                self.namespace_index = _NamespaceIndex()
                self.embedding_service = _EmbeddingService()
                self.vector_index = _VectorIndex()

            def retrieve_memories(self, query: str, *, limit: int = 5, query_embedding=None, **kwargs):
                return [
                    MemoryRecord(id=1, namespace="ns", tags=[], text="A", importance=0.5),
                    MemoryRecord(id=2, namespace="ns", tags=[], text="B", importance=0.5),
                ][: int(limit)]

        mm = _MemoryManager()
        agg = WorldStateAggregator(memory_manager=mm, shared_state_path=tmp_path / "shared_state.json")

        llm = Mock()
        llm.chat.return_value = {"choices": [{"message": {"content": "ok"}}]}
        llm.extract_assistant_content = Mock(return_value="ok")
        llm.extract_tool_calls = Mock(return_value=[])

        session = ConversationSession(llm=llm, world_state_aggregator=agg, session_id="s1")
        # Run several primes; without penalty, id=1 would always win due to stable ordering.
        seen = []
        for _ in range(4):
            session._prime_memory_for_user_prompt("prompt", hidden_user_message=False)
            ws = agg.aggregate(session_id="s1")
            seen.append(ws["primed_memory"]["items"][0]["id"])
        assert 2 in seen
    finally:
        config.memory.prompt_priming_enabled = original_enabled
        config.memory.prompt_priming_top_k = original_top_k
        config.memory.prompt_priming_max_items = original_max_items
        config.memory.prompt_priming_interference_weight = original_interference_weight


def test_mmr_select_diversifies_when_lambda_low():
    query = [1.0, 0.0, 0.0]
    candidates = ["A", "B", "C"]
    candidate_vectors = [
        [0.8, 0.6, 0.0],    # A
        [0.79, 0.61, 0.0],  # B (near-duplicate of A)
        [0.7, 0.0, 0.714],  # C (diverse)
    ]

    selected = mmr_select(
        query_vector=query,
        candidates=candidates,
        candidate_vectors=candidate_vectors,
        k=2,
        lambda_mult=0.5,
    )
    assert selected == ["A", "C"]


def test_build_priming_card_contains_required_fields():
    card = build_priming_card(
        query_preview="hello",
        items=[
            {"id": 1, "namespace": "ns", "score": 0.9, "text": "A"},
            {"id": 2, "namespace": "ns", "score": 0.7, "text": "B"},
        ],
        selection={"strategy": "mmr", "top_k": 3, "max_items": 2, "lambda": 0.5},
    )
    assert "PRIMED MEMORY:" in card
    assert "Query:" in card
    assert "[1]" in card and "[2]" in card
    assert "A" in card and "B" in card
