"""
Telemetry tests: ensure ContextGraph can emit context selection logs without crashing.
"""

from __future__ import annotations

from broca.context.context_graph import ContextGraph


def test_selection_telemetry_does_not_crash(tmp_path):
    log_file = tmp_path / "context_selection.csv"
    graph = ContextGraph(selection_logging_enabled=True, selection_log_file=str(log_file))

    graph.add_message({"role": "user", "content": "hi", "message_id": "u0"})
    graph.add_message({"role": "assistant", "content": "hello", "message_id": "a0"}, parent_id="u0")

    msgs = graph.get_messages_for_llm(max_tokens=200, safety_margin=0.95)
    assert len(msgs) > 0
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "message_id" in content
    assert "kept_reason" in content


