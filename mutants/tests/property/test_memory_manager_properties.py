from datetime import datetime, timedelta, timezone
from typing import List, Set

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from broca.memory import RelationType


NAMESPACE_POOL = ["team.alpha", "team.alpha.sub", "team.beta", "team.gamma"]
TAG_POOL = ["red", "blue", "green", "yellow", "orange"]
TOKEN_POOL = ["alpha", "beta", "gamma", "delta", "epsilon"]


def reset_memory_manager_state(memory_manager) -> None:
    conn = memory_manager.storage._connection
    conn.execute("DELETE FROM memory_relationships")
    conn.execute("DELETE FROM memories")
    conn.commit()
    memory_manager.vector_index.clear()


def memory_entry_strategy():
    return st.fixed_dictionaries(
        {
            "namespace": st.sampled_from(NAMESPACE_POOL),
            "tags": st.lists(st.sampled_from(TAG_POOL), max_size=3, unique=True),
            "text": st.text(min_size=5, max_size=50),
            "importance": st.floats(min_value=0.05, max_value=1.0, allow_nan=False, allow_infinity=False),
        }
    )


@settings(
    max_examples=25,
    suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.function_scoped_fixture],
)
@given(
    entries=st.lists(memory_entry_strategy(), min_size=3, max_size=8),
    tag_filter=st.lists(st.sampled_from(TAG_POOL), min_size=1, max_size=2, unique=True),
    namespace_exact=st.booleans(),
)
def test_store_and_retrieve_respects_tags_and_namespaces(memory_manager, entries, tag_filter, namespace_exact):
    reset_memory_manager_state(memory_manager)
    stored_records = []
    for entry in entries:
        mem_id, _, _ = memory_manager.store_memory(
            namespace=entry["namespace"],
            text=entry["text"],
            importance=entry["importance"],
            tags=entry["tags"],
            auto_link=False,
            deduplicate=False,
        )
        stored_records.append((mem_id, entry))

    namespace_to_query = entries[0]["namespace"]

    results = memory_manager.retrieve_memories(
        query="",
        namespaces=[namespace_to_query],
        tags=tag_filter,
        tag_mode="all",
        namespace_exact=namespace_exact,
        limit=20,
    )

    def namespace_matches(candidate: str) -> bool:
        return candidate == namespace_to_query if namespace_exact else namespace_to_query in candidate

    expected_ids = {
        mem_id
        for mem_id, entry in stored_records
        if namespace_matches(entry["namespace"]) and all(tag in entry["tags"] for tag in tag_filter)
    }

    result_ids = {record.id for record in results}
    assert result_ids == expected_ids


@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    base_term=st.sampled_from(TOKEN_POOL),
    and_terms=st.sets(st.sampled_from(TOKEN_POOL), max_size=2),
    or_terms=st.sets(st.sampled_from(TOKEN_POOL), max_size=2),
    not_terms=st.sets(st.sampled_from(TOKEN_POOL), max_size=1),
)
def test_boolean_queries_respect_and_or_not(memory_manager, base_term, and_terms, or_terms, not_terms):
    reset_memory_manager_state(memory_manager)
    # Avoid degenerate cases with no filtering signals
    assume_tokens = set(and_terms) | set(or_terms) | set(not_terms) | {base_term}
    assume(bool(assume_tokens))  # ensure non-empty
    effective_or_terms = {term for term in or_terms if term != base_term}
    assume(bool(and_terms or effective_or_terms or not_terms))  # ensure boolean operators participate

    query_parts: List[str] = [base_term]
    for token in sorted(and_terms):
        query_parts.extend(["AND", token])
    for token in sorted(effective_or_terms):
        query_parts.extend(["OR", token])
    for token in sorted(not_terms):
        query_parts.extend(["NOT", token])
    query = " ".join(query_parts)

    matching_tokens: Set[str] = {base_term} | set(and_terms) | effective_or_terms
    candidate_tokens = matching_tokens | {"context"}
    alternate_tokens = (effective_or_terms if effective_or_terms else {base_term}) | {"context"}
    excluded_tokens = set(not_terms) | {"context"}

    candidates = [
        ("match-all", candidate_tokens),
        ("match-or", alternate_tokens),
        ("excluded", excluded_tokens),
    ]

    for label, tokens in candidates:
        text = " ".join(sorted(tokens | {"memo"}))
        memory_manager.store_memory(
            namespace="logic.test",
            text=text,
            importance=0.5,
            tags=[label],
            auto_link=False,
            deduplicate=False,
        )

    results = memory_manager.retrieve_memories(
        query=query,
        namespace="logic.test",
        namespace_exact=True,
        limit=5,
    )

    def matches(tokens: Set[str]) -> bool:
        if any(term in tokens for term in not_terms):
            return False
        if any(term not in tokens for term in and_terms):
            return False
        if base_term in tokens:
            return True
        if or_terms:
            return any(term in tokens for term in or_terms)
        return False

    expected_labels = {label for label, tokens in candidates if matches(tokens)}
    result_labels = {label for record in results for label in record.tags}
    assert result_labels == expected_labels


@settings(
    max_examples=6,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(order=st.permutations(["alpha", "beta", "gamma"]))
def test_temporal_ordering_respects_precedes_links(memory_manager, order):
    reset_memory_manager_state(memory_manager)
    stored_ids = {}
    now = datetime.now(timezone.utc)
    for idx, token in enumerate(order):
        created_at = now + timedelta(seconds=idx)
        memory_manager.storage._connection.execute(
            "INSERT INTO memories (namespace, tags, text, importance, created_at, last_used_at, embedding, valid_from, valid_until, temporal_scope, source_type, source_metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "timeline.events",
                '["chronology"]',
                f"{token} event",
                0.6,
                created_at.isoformat(),
                created_at.isoformat(),
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        )
        mem_id = memory_manager.storage._connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        stored_ids[token] = mem_id
        memory_manager.vector_index.add_vector(mem_id, memory_manager.embedding_service.generate_embedding(token))
    memory_manager.storage._connection.commit()

    for first, second in zip(order, order[1:]):
        memory_manager.link_memories(
            stored_ids[first],
            stored_ids[second],
            RelationType.PRECEDES,
            strength=0.9,
        )

    results = memory_manager.retrieve_memories(
        query="event",
        namespace="timeline.events",
        namespace_exact=True,
        order_by_temporal=True,
        limit=3,
    )
    assert [record.text for record in results] == [f"{token} event" for token in order]
