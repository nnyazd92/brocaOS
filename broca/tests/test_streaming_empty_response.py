import pytest
from broca.repl.session import ConversationSession


class DummyLLM:
    """Simulate an LLM client that supports chat_stream but yields no chunks."""

    def chat_stream(self, messages, tools=None, reasoning_content=None, thought_signature=None):
        # Yield nothing to simulate empty streaming
        if False:
            yield

    def chat(self, messages, tools=None, reasoning_content=None, thought_signature=None):
        # Fallback non-streaming: return a minimal assistant message
        return {"choices": [{"message": {"content": "", "role": "assistant"}}]}

    def extract_assistant_content(self, resp):
        try:
            return resp["choices"][0]["message"].get("content", "")
        except Exception:
            return ""


def test_streaming_no_chunks_injects_fallback(monkeypatch, tmp_path):
    # Create a session with a dummy LLM that streams no chunks
    dummy = DummyLLM()
    session = ConversationSession(system_prompt=None, llm=dummy, storage=None)

    # Send a message with streaming enabled
    reply = session.send("Hello", stream=True)

    # The reply should not be an empty string; it should be the fallback injected by response_guard
    assert reply is not None
    assert reply != ""
    assert "[automatic fallback]" in reply

    # And the last assistant message in session.messages should be the same fallback
    assistant_msgs = [m for m in session.messages if m.get("role") == "assistant"]
    assert assistant_msgs
    assert assistant_msgs[-1].get("content") == reply
