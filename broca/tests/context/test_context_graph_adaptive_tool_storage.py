"""
Tests for adaptive tool-result storage in ContextGraph.

Goal: tool outputs should be bounded in-graph so token accounting and pruning stay truthful.
"""

from __future__ import annotations

from broca.context.context_graph import ContextGraph
from broca.summarization.token_estimator import estimate_messages_tokens


def test_tool_message_is_truncated_in_graph_storage():
    graph = ContextGraph(tool_content_max_chars=2000)

    tool_msg = {
        "role": "tool",
        "name": "big_tool",
        "tool_call_id": "call_1",
        "content": "A" * 20000,
        "message_id": "tool1",
    }
    graph.add_message(tool_msg)

    node = graph.nodes["tool1"]
    assert node.message_data is not None
    assert isinstance(node.message_data.get("content"), str)
    assert len(node.message_data["content"]) <= 2500  # allow marker overhead
    meta = node.message_data.get("_broca_meta", {})
    assert meta.get("_broca_truncated") is True
    assert meta.get("_broca_original_length") == 20000
    assert isinstance(meta.get("_broca_content_hash"), str) and len(meta["_broca_content_hash"]) > 0


def test_pruning_uses_bounded_tool_tokens():
    graph = ContextGraph(min_turns_retained=1, tool_content_max_chars=2000)

    # Add a small conversation then a huge tool result on the main thread.
    graph.add_message({"role": "user", "content": "hi", "message_id": "u0"})
    graph.add_message({"role": "assistant", "content": "calling tool", "message_id": "a0"}, parent_id="u0")
    graph.add_message(
        {"role": "tool", "name": "big_tool", "tool_call_id": "call_1", "content": "B" * 20000, "message_id": "t0"},
        parent_id="a0",
    )

    kept_ids, tokens = graph.prune_to_fit(max_tokens=1500, safety_margin=0.95)
    kept_msgs = [graph.nodes[mid].message_data for mid in kept_ids if mid in graph.nodes and graph.nodes[mid].message_data]
    assert estimate_messages_tokens(kept_msgs) == tokens
    assert tokens <= int(1500 * 0.95) * 1.1


