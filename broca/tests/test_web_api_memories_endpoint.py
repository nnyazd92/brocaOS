"""
Tests for the /api/memories endpoint in web_api.py.

Validates that advanced filters mirror RetrieveMemoriesTool, linked
relationships are surfaced, and epistemic metadata is exposed when
available.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from broca.memory import MemoryRecord, RelationType, RelationshipRecord, SourceMetadata, SourceType
from broca.web_api import app


@pytest.fixture
def client():
    return TestClient(app)


def _build_memory(memory_id: int, text: str = "Memory text", namespace: str = "ns") -> MemoryRecord:
    return MemoryRecord(
        id=memory_id,
        text=text,
        namespace=namespace,
        tags=["tag1"],
        importance=0.8,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        last_used_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        source=SourceMetadata(source_type=SourceType.USER),
    )


@patch("broca.web_api.get_runtime")
def test_get_memories_applies_filters_and_returns_links(mock_get_runtime, client):
    memory_manager = MagicMock()
    memory = _build_memory(1)
    linked_memory = _build_memory(2, text="Linked memory")
    relationship = RelationshipRecord(
        source_id=1,
        target_id=2,
        relation_type=RelationType.SUPPORTS,
        strength=0.9,
        bidirectional=False,
    )

    memory_manager.retrieve_memories.return_value = [memory]
    memory_manager.get_related_memories.return_value = [(linked_memory, relationship)]

    runtime = SimpleNamespace(memory_manager=memory_manager, tool_registry=SimpleNamespace(epistemic_engine=None))
    mock_get_runtime.return_value = runtime

    payload = {
        "query": "memory text",
        "namespaces": ["ns"],
        "namespace_exact": True,
        "tags": ["tag1"],
        "tag_mode": "all",
        "limit": 3,
        "recency_weight": 0.4,
        "include_linked": True,
        "linked_limit": 2,
    }

    response = client.post("/api/memories", json=payload)

    assert response.status_code == 200
    data = response.json()

    call_kwargs = memory_manager.retrieve_memories.call_args.kwargs
    assert call_kwargs["query"] == payload["query"]
    assert call_kwargs["namespaces"] == payload["namespaces"]
    assert call_kwargs["tag_mode"] == payload["tag_mode"]
    assert call_kwargs["limit"] == payload["limit"]
    assert call_kwargs["recency_weight"] == payload["recency_weight"]

    assert data["count"] == 1
    assert data["memories"][0]["id"] == 1
    assert data["memories"][0]["linked_memories"][0]["relationship_type"] == RelationType.SUPPORTS.value
    assert data["memories"][0]["linked_memories"][0]["direction"] == "outgoing"


@patch("broca.web_api.get_runtime")
def test_get_memories_validates_dates(mock_get_runtime, client):
    runtime = SimpleNamespace(memory_manager=MagicMock(), tool_registry=SimpleNamespace(epistemic_engine=None))
    mock_get_runtime.return_value = runtime

    response = client.post(
        "/api/memories",
        json={"query": "test", "created_after": "not-a-date"},
    )

    assert response.status_code == 400
    assert "Invalid created_after date format" in response.json()["detail"]


@patch("broca.web_api.get_runtime")
def test_get_memories_includes_epistemic_context(mock_get_runtime, client):
    memory_manager = MagicMock()
    memory = _build_memory(1)
    epistemic_payload = {
        "memories": [memory],
        "low_confidence_warnings": [{"memory_id": 1, "confidence": 0.2}],
        "confidence_stats": {"average_confidence": 0.5},
        "epistemic_context": {"source_breakdown": {"user": 1}},
    }
    memory_manager.retrieve_memories_with_epistemic.return_value = epistemic_payload
    memory_manager.get_related_memories.return_value = []

    runtime = SimpleNamespace(memory_manager=memory_manager, tool_registry=SimpleNamespace(epistemic_engine=object()))
    mock_get_runtime.return_value = runtime

    response = client.post(
        "/api/memories",
        json={"query": "epistemic", "min_confidence": 0.3},
    )

    assert response.status_code == 200
    data = response.json()

    memory_manager.retrieve_memories_with_epistemic.assert_called_once()
    assert data["low_confidence_warnings"] == epistemic_payload["low_confidence_warnings"]
    assert data["confidence_stats"] == epistemic_payload["confidence_stats"]
    assert data["memories"][0]["id"] == 1

