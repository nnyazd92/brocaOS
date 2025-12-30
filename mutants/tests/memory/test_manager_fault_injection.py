import json

import pytest


def test_retrieve_memories_handles_vector_index_failure(memory_manager, monkeypatch):
    memory_manager.store_memory(
        namespace="fault.test",
        text="resilient memory",
        importance=0.7,
        tags=["resilience"],
        auto_link=False,
        deduplicate=False,
    )

    def boom(*args, **kwargs):
        raise RuntimeError("vector search failed")

    monkeypatch.setattr(memory_manager.vector_index, "search_similar", boom)
    results = memory_manager.retrieve_memories(query="anything", limit=5)
    assert results == []


def test_rebuild_index_handles_corrupted_embeddings(memory_manager):
    cursor = memory_manager.storage._connection.cursor()
    cursor.execute(
        """
        INSERT INTO memories (namespace, tags, text, importance, created_at, last_used_at, embedding, valid_from, valid_until, temporal_scope, source_type, source_metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "fault.corruption",
            json.dumps(["broken"]),
            "corrupted embedding",
            0.4,
            "2024-01-01T00:00:00+00:00",
            "2024-01-01T00:00:00+00:00",
            json.dumps([1.0, 2.0]),  # Wrong dimension on purpose
            None,
            None,
            None,
            None,
            None,
        ),
    )
    memory_id = cursor.lastrowid
    memory_manager.storage._connection.commit()

    # Ensure vector index is empty and attempt to rebuild from storage
    memory_manager.vector_index.clear()
    memory_manager._rebuild_index_from_storage()

    # Corrupted embedding should be skipped without raising
    assert memory_manager.vector_index.get_count() == 0
    assert memory_id in {mem.id for mem in memory_manager.storage.get_all_memories()}


def test_namespace_search_failure_returns_empty(memory_manager, monkeypatch):
    def raise_storage(*args, **kwargs):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(memory_manager.storage, "search_by_namespace", raise_storage)
    results = memory_manager.retrieve_memories(query="fallback", namespace="fault.test", limit=3)
    assert results == []
