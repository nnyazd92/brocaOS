from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from broca.web_api import app


class _Storage:
    def __init__(self, data):
        self._data = data

    def load_conversation(self, conversation_id: str):
        return self._data

    def save_conversation(self, conversation_id: str, messages, metadata):
        self._data = {"messages": messages, "metadata": metadata}

    def list_conversations(self):
        return []


def test_conversation_updates_filters_hidden_and_includes_auto_continue_metadata():
    data = {
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "user", "content": "internal", "hidden": True},
            {"role": "assistant", "content": "hello"},
        ],
        "metadata": {
            "updated_at": "2026-01-01T00:00:00+00:00",
            "auto_continue_pending": {"status": "pending", "prompt": "Continue."},
            "auto_continue_last": {"status": "completed"},
        },
    }
    storage = _Storage(data)
    runtime = SimpleNamespace(conversation_storage=storage)

    with patch("broca.web_api.get_runtime", return_value=runtime):
        client = TestClient(app)
        resp = client.get("/api/conversations/c1/updates?after=0")
        assert resp.status_code == 200
        payload = resp.json()

        assert payload["conversation_id"] == "c1"
        # Hidden internal user message is filtered out.
        assert [m["role"] for m in payload["messages"]] == ["user", "assistant"]
        assert payload["auto_continue_pending"]["status"] == "pending"
        assert payload["auto_continue_last"]["status"] == "completed"
        assert payload["next_after"] == 2

