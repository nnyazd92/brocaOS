import uuid
import pytest
from broca.repl.session import ConversationSession
from broca.repl.response_guard import FALLBACK_TEMPLATE

class DummyLLMClient:
    def __init__(self, result=None, raise_exc=False):
        self._result = result
        self._raise = raise_exc
    def chat(self, *args, **kwargs):
        if self._raise:
            raise RuntimeError("dummy llm failure")
        # Simulate a typical response structure
        return {"choices": [{"message": {"content": self._result}}]}
    def chat_stream(self, *args, **kwargs):
        # Simulate empty generator
        if self._raise:
            raise RuntimeError("dummy stream failure")
        if self._result is None:
            return iter(())
        return iter((self._result,))
    def extract_assistant_content(self, response):
        try:
            return response.get('choices', [])[0].get('message', {}).get('content')
        except Exception:
            return None


def test_empty_reply_is_replaced(monkeypatch):
    session = ConversationSession(storage=None, tool_registry=None)
    session.llm = DummyLLMClient(result="")
    reply = session.send("hello", stream=False)
    assert reply is not None and reply.strip() != ""
    assert "TraceID" in reply


def test_llm_exception_fallback(monkeypatch):
    session = ConversationSession(storage=None, tool_registry=None)
    session.llm = DummyLLMClient(raise_exc=True)
    reply = session.send("trigger exception", stream=False)
    assert reply is not None and reply.strip() != ""
    assert "TraceID" in reply
