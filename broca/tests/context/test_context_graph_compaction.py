"""
Tests for proactive history compaction.

Key property: compaction must be stable under ConversationSession-style replay
of full history into the graph each turn (no re-inflation).
"""

from __future__ import annotations

from broca.context.context_graph import ContextGraph
from broca.summarization.token_estimator import estimate_messages_tokens


def test_compaction_creates_summary_and_prevents_reinflation():
    graph = ContextGraph(min_turns_retained=1, tool_content_max_chars=2000)

    # Create long linear history
    parent = None
    for i in range(80):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"{role} {i} " + ("x" * 400), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]

    # Trigger compaction by calling get_messages_for_llm with a small budget
    msgs1 = graph.get_messages_for_llm(max_tokens=500, safety_margin=0.95)
    tokens1 = estimate_messages_tokens(msgs1)
    assert tokens1 <= int(500 * 0.95) * 1.15

    # There should be at least one summary node in the graph
    summary_nodes = [n for n in graph.nodes.values() if n.message_data and n.message_data.get("_broca_summary")]
    assert len(summary_nodes) >= 1

    # Find a compacted message and ensure replay doesn't re-inflate it
    compacted = [n for n in graph.nodes.values() if getattr(n, "is_compacted", False)]
    assert len(compacted) > 0
    some = compacted[0]

    # Simulate ConversationSession replay: re-add the original message with full content
    graph.add_message({"role": some.role, "content": "FULL" * 5000, "message_id": some.message_id})
    assert graph.nodes[some.message_id].is_compacted is True
    assert graph.nodes[some.message_id].message_data is None


