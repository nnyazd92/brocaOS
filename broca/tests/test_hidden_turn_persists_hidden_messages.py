from __future__ import annotations

from broca.repl.session import ConversationSession


class _CaptureStorage:
    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save_conversation(self, *, session_id: str, messages, metadata):
        self.saved.append({"session_id": session_id, "messages": messages, "metadata": metadata})

    def load_conversation(self, session_id: str):
        return None


class _EchoLLM:
    def __init__(self, content: str) -> None:
        self._content = content

    def chat(self, messages, **kwargs):
        return {"choices": [{"message": {"content": self._content}}]}

    def extract_assistant_content(self, response):
        return response.get("choices", [{}])[0].get("message", {}).get("content")

    def extract_tool_calls(self, response):
        return []


def test_hidden_turn_persists_hidden_user_message_and_deduped_duplicate_assistant():
    storage = _CaptureStorage()
    session = ConversationSession(storage=storage, tool_registry=None, llm=_EchoLLM("same"))
    session.messages.append({"role": "assistant", "content": "same"})

    _ = session.send("internal prompt", stream=False, hidden_user_message=True)

    assert storage.saved, "expected at least one save_conversation call"
    saved = storage.saved[-1]["messages"]

    user_msgs = [m for m in saved if isinstance(m, dict) and m.get("role") == "user"]
    assert user_msgs and user_msgs[-1].get("hidden") is True

    assistant_msgs = [m for m in saved if isinstance(m, dict) and m.get("role") == "assistant"]
    assert len(assistant_msgs) >= 2
    assert assistant_msgs[-1].get("hidden") is True


def test_hidden_turn_persists_hidden_assistant_even_when_not_duplicate():
    """
    Regression: hidden internal turns (RESPOND_AND_CONTINUE auto-continue) must not persist
    user-visible assistant messages, even when the assistant text differs from the last visible
    assistant (so the dedup-only heuristic does not trigger).
    """
    storage = _CaptureStorage()
    session = ConversationSession(storage=storage, tool_registry=None, llm=_EchoLLM("different"))
    session.messages.append({"role": "assistant", "content": "previous visible"})

    _ = session.send("internal prompt", stream=False, hidden_user_message=True)

    assert storage.saved, "expected at least one save_conversation call"
    saved = storage.saved[-1]["messages"]

    user_msgs = [m for m in saved if isinstance(m, dict) and m.get("role") == "user"]
    assert user_msgs and user_msgs[-1].get("hidden") is True

    assistant_msgs = [m for m in saved if isinstance(m, dict) and m.get("role") == "assistant"]
    assert assistant_msgs and assistant_msgs[-1].get("content") == "different"
    assert assistant_msgs[-1].get("hidden") is True
