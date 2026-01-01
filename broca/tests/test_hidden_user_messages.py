from __future__ import annotations

from broca.repl.session import ConversationSession


class _DummyLLM:
    def chat(self, messages, **kwargs):
        return {"choices": [{"message": {"content": "ok"}}]}

    def extract_assistant_content(self, response):
        return response.get("choices", [{}])[0].get("message", {}).get("content")

    def extract_tool_calls(self, response):
        return []


def test_hidden_user_message_flag_is_set():
    session = ConversationSession(storage=None, tool_registry=None)
    session.llm = _DummyLLM()

    _ = session.send("internal prompt", stream=False, hidden_user_message=True)

    # The most recent user message should be hidden.
    user_msgs = [m for m in session.messages if isinstance(m, dict) and m.get("role") == "user"]
    assert user_msgs, "expected at least one user message"
    assert user_msgs[-1].get("hidden") is True


class _EchoLLM:
    def __init__(self, content: str) -> None:
        self._content = content

    def chat(self, messages, **kwargs):
        return {"choices": [{"message": {"content": self._content}}]}

    def extract_assistant_content(self, response):
        return response.get("choices", [{}])[0].get("message", {}).get("content")

    def extract_tool_calls(self, response):
        return []


def test_hidden_turn_dedupes_exact_duplicate_assistant_message():
    session = ConversationSession(storage=None, tool_registry=None)
    session.llm = _EchoLLM("same")
    session.messages.append({"role": "assistant", "content": "same"})

    _ = session.send("internal prompt", stream=False, hidden_user_message=True)

    assistant_msgs = [m for m in session.messages if isinstance(m, dict) and m.get("role") == "assistant"]
    assert len(assistant_msgs) >= 2
    assert assistant_msgs[-1].get("hidden") is True
