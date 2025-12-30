"""
Regression tests for atomic tool-call bundle preservation.

We should never end up with assistant tool_calls in the outgoing message list
without all required tool messages; otherwise ContextGraph validation deletes
chunks and causes agent weirdness.
"""

from __future__ import annotations

import logging

from broca.context.context_graph import ContextGraph


def test_atomic_tool_bundle_kept_without_validation_deletions(caplog):
    graph = ContextGraph(min_turns_retained=1, tool_content_max_chars=2000)

    # user -> assistant(tool_calls) -> tool -> assistant
    graph.add_message({"role": "user", "content": "do thing", "message_id": "u0"})
    graph.add_message(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "x", "arguments": "{}"}}],
            "message_id": "a0",
        },
        parent_id="u0",
    )
    graph.add_message(
        {"role": "tool", "name": "x", "tool_call_id": "call_1", "content": "OK", "message_id": "t0"},
        parent_id="a0",
    )
    graph.add_message({"role": "assistant", "content": "done", "message_id": "a1"}, parent_id="t0")

    caplog.set_level(logging.WARNING)
    msgs = graph.get_messages_for_llm(max_tokens=200, safety_margin=0.95)

    # Ensure ordering is valid and no deletions were needed
    assert not any("Removed" in r.message and "incomplete tool_call sequence" in r.message for r in caplog.records)

    # If tool_calls assistant is present, tool message must also be present
    has_tool_calls = any(m.get("role") == "assistant" and m.get("tool_calls") for m in msgs)
    if has_tool_calls:
        assert any(m.get("role") == "tool" and m.get("tool_call_id") == "call_1" for m in msgs)


def test_tool_calls_skipped_if_bundle_cannot_fit(caplog):
    graph = ContextGraph(min_turns_retained=1, tool_content_max_chars=2000)

    graph.add_message({"role": "user", "content": "do big thing", "message_id": "u0"})
    graph.add_message(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "call_big", "type": "function", "function": {"name": "big", "arguments": "{}"}}],
            "message_id": "a0",
        },
        parent_id="u0",
    )
    # Big tool output (still truncated in-graph, but make budget tiny)
    graph.add_message(
        {"role": "tool", "name": "big", "tool_call_id": "call_big", "content": "Z" * 20000, "message_id": "t0"},
        parent_id="a0",
    )
    graph.add_message({"role": "assistant", "content": "done", "message_id": "a1"}, parent_id="t0")

    caplog.set_level(logging.WARNING)
    msgs = graph.get_messages_for_llm(max_tokens=50, safety_margin=0.95)

    # No validation deletions should be required; we should just skip the bundle if it can't fit.
    assert not any("Removed" in r.message and "incomplete tool_call sequence" in r.message for r in caplog.records)

    # If the assistant tool_calls is present, tool must be present too; otherwise tool_calls should be absent.
    has_tool_calls = any(m.get("role") == "assistant" and m.get("tool_calls") for m in msgs)
    has_tool = any(m.get("role") == "tool" and m.get("tool_call_id") == "call_big" for m in msgs)
    assert has_tool_calls == has_tool


