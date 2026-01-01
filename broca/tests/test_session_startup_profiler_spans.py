from __future__ import annotations

from contextlib import contextmanager
from typing import List


class FakeStartupProfiler:
    def __init__(self) -> None:
        self.stack: List[str] = []
        self.spans: List[str] = []

    @contextmanager
    def span(self, name: str):
        self.stack.append(name)
        try:
            yield
        finally:
            self.stack.pop()
            self.spans.append(name)


def test_conversation_session_emits_startup_spans(monkeypatch):
    from broca.repl.session import ConversationSession

    profiler = FakeStartupProfiler()

    def patched_update(self):
        with self._startup_span("patched_update"):
            return None

    monkeypatch.setattr(ConversationSession, "_update_system_prompt", patched_update)

    # Non-None aggregator + formatter triggers _update_system_prompt() during __init__.
    ConversationSession(
        llm=object(),
        world_state_aggregator=object(),
        startup_profiler=profiler,
    )

    # Smoke-check the key spans; exact ordering isn't important.
    assert "conversation_session.llm_client" in profiler.spans
    assert "conversation_session.update_system_prompt" in profiler.spans
    assert "patched_update" in profiler.spans

