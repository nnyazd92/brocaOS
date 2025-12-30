"""
Tests for simple oldest-first node plucking.

The key property of plucking is that it ACTUALLY REMOVES nodes from the graph,
unlike the old token trimming which only filtered the output but let the
underlying data grow unbounded.
"""

from __future__ import annotations

import pytest

from broca.context.context_graph import ContextGraph
from broca.summarization.token_estimator import estimate_messages_tokens


def test_pluck_oldest_removes_nodes_from_graph():
    """Plucking should actually remove nodes, not just filter output."""
    graph = ContextGraph(min_recent_to_keep=5)
    
    # Add 20 messages
    parent = None
    for i in range(20):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 100), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    assert len(graph.nodes) == 20
    
    # Pluck with a very small token limit to force plucking
    plucked = graph.pluck_oldest_until_under_limit(max_tokens=500)
    
    # Nodes should actually be removed
    assert len(graph.nodes) < 20, f"Expected nodes to be removed, but still have {len(graph.nodes)}"
    assert len(plucked) > 0, "Expected some nodes to be plucked"
    
    # Plucked IDs should no longer exist in graph
    for msg_id in plucked:
        assert msg_id not in graph.nodes, f"Plucked node {msg_id} should not exist in graph"
        assert msg_id not in graph._message_order, f"Plucked node {msg_id} should not be in message order"


def test_pluck_preserves_system_messages():
    """System messages should never be plucked."""
    graph = ContextGraph(min_recent_to_keep=3)
    
    # Add system message first
    system_msg = {"role": "system", "content": "You are a helpful assistant", "message_id": "sys1"}
    graph.add_message(system_msg)
    
    # Add more messages to create pressure
    parent = "sys1"
    for i in range(20):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 100), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    # Force aggressive plucking
    plucked = graph.pluck_oldest_until_under_limit(max_tokens=200)
    
    # System message should still exist
    assert "sys1" in graph.nodes, "System message should never be plucked"
    assert "sys1" not in plucked, "System message should not be in plucked list"


def test_pluck_preserves_recent_messages():
    """Recent N messages should be protected from plucking."""
    graph = ContextGraph(min_recent_to_keep=5)
    
    # Add 20 messages
    parent = None
    for i in range(20):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 100), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    # Force plucking
    plucked = graph.pluck_oldest_until_under_limit(max_tokens=300)
    
    # Check that most recent 5 are still there
    recent_ids = [f"m{i}" for i in range(15, 20)]  # m15, m16, m17, m18, m19
    for msg_id in recent_ids:
        assert msg_id in graph.nodes, f"Recent message {msg_id} should be preserved"
        assert msg_id not in plucked, f"Recent message {msg_id} should not be plucked"


def test_pluck_oldest_first():
    """Plucking should remove oldest messages first."""
    graph = ContextGraph(min_recent_to_keep=3)
    
    # Add 15 messages
    parent = None
    for i in range(15):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 50), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    # Force plucking - should remove oldest first
    plucked = graph.pluck_oldest_until_under_limit(max_tokens=300)
    
    if plucked:
        # Plucked messages should be among the oldest
        oldest_ids = [f"m{i}" for i in range(min(len(plucked), 5))]
        # At least some of the oldest should be plucked
        plucked_set = set(plucked)
        oldest_in_plucked = [mid for mid in oldest_ids if mid in plucked_set]
        assert len(oldest_in_plucked) > 0, "Oldest messages should be plucked first"


def test_no_pluck_when_under_limit():
    """When already under limit, nothing should be plucked."""
    graph = ContextGraph(min_recent_to_keep=3)
    
    # Add just a few messages
    parent = None
    for i in range(5):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Short {i}", "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    initial_count = len(graph.nodes)
    
    # Generous token limit
    plucked = graph.pluck_oldest_until_under_limit(max_tokens=100000)
    
    assert len(plucked) == 0, "Nothing should be plucked when under limit"
    assert len(graph.nodes) == initial_count, "Node count should not change"


def test_get_messages_for_llm_triggers_plucking():
    """get_messages_for_llm should pluck nodes when over limit."""
    graph = ContextGraph(min_recent_to_keep=5)
    
    # Add many messages
    parent = None
    for i in range(30):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 100), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    initial_count = len(graph.nodes)
    
    # Get messages with tight limit - should trigger plucking
    messages = graph.get_messages_for_llm(max_tokens=500, safety_margin=0.95)
    
    # Graph should have fewer nodes now
    assert len(graph.nodes) < initial_count, "Plucking should reduce node count"
    
    # Last plucked IDs should be available
    plucked_ids = graph.get_last_plucked_ids()
    assert len(plucked_ids) > 0, "Should have plucked some nodes"


def test_pluck_maintains_message_order():
    """After plucking, remaining messages should maintain correct order."""
    graph = ContextGraph(min_recent_to_keep=5)
    
    # Add messages
    parent = None
    for i in range(20):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 100), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    # Pluck some
    graph.pluck_oldest_until_under_limit(max_tokens=600)
    
    # Get remaining messages
    messages = graph.get_messages_for_llm(max_tokens=100000)
    
    # Verify order: each subsequent message should have higher index
    prev_idx = -1
    for msg in messages:
        msg_id = msg.get("message_id", "")
        if msg_id.startswith("m"):
            idx = int(msg_id[1:])
            assert idx > prev_idx, f"Messages should be in order: {prev_idx} should come before {idx}"
            prev_idx = idx


def test_pluck_updates_parent_child_links():
    """When a node is plucked, parent-child links should be updated."""
    graph = ContextGraph(min_recent_to_keep=3)
    
    # Add 10 messages
    parent = None
    for i in range(10):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 50), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    # Pluck oldest
    plucked = graph.pluck_oldest_until_under_limit(max_tokens=200)
    
    # Validate graph integrity
    issues = graph.validate_graph_integrity()
    assert len(issues) == 0, f"Graph should have no integrity issues after plucking: {issues}"


def test_get_last_plucked_ids():
    """get_last_plucked_ids should return IDs from last plucking operation."""
    graph = ContextGraph(min_recent_to_keep=3)
    
    # Add messages
    parent = None
    for i in range(15):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 80), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    # First pluck
    plucked1 = graph.pluck_oldest_until_under_limit(max_tokens=400)
    last1 = graph.get_last_plucked_ids()
    assert last1 == plucked1, "get_last_plucked_ids should return same as pluck return"
    
    # Second pluck (might not pluck anything if already under)
    plucked2 = graph.pluck_oldest_until_under_limit(max_tokens=400)
    last2 = graph.get_last_plucked_ids()
    assert last2 == plucked2


def test_pluck_with_empty_graph():
    """Plucking an empty graph should be a no-op."""
    graph = ContextGraph(min_recent_to_keep=5)
    
    plucked = graph.pluck_oldest_until_under_limit(max_tokens=100)
    
    assert plucked == []
    assert len(graph.nodes) == 0


def test_plucked_nodes_are_tombstoned_and_not_readded():
    """
    ConversationSession replays full history into the graph each turn.
    Plucked nodes must remain excluded (tombstoned) so replay doesn't re-inflate them.
    """
    graph = ContextGraph(min_recent_to_keep=3)

    parent = None
    for i in range(20):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 100), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]

    plucked = graph.pluck_oldest_until_under_limit(max_tokens=300)
    assert plucked, "Expected some nodes to be plucked"

    # Replay plucked IDs: they should not be re-added.
    for mid in plucked[:5]:
        graph.add_message({"role": "user", "content": "replay", "message_id": mid})
        assert mid not in graph.nodes, f"Tombstoned/plucked id {mid} should not be re-added"


def test_token_count_actually_decreases():
    """After plucking, total token count should actually decrease."""
    graph = ContextGraph(min_recent_to_keep=5)
    
    # Add many messages
    parent = None
    for i in range(30):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"Message {i} " + ("x" * 200), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]
    
    # Calculate initial tokens
    initial_messages = [n.message_data for n in graph.nodes.values() if n.message_data]
    initial_tokens = estimate_messages_tokens(initial_messages)
    
    # Pluck
    target_limit = initial_tokens // 3
    graph.pluck_oldest_until_under_limit(max_tokens=target_limit)
    
    # Calculate final tokens
    final_messages = [n.message_data for n in graph.nodes.values() if n.message_data]
    final_tokens = estimate_messages_tokens(final_messages)
    
    assert final_tokens < initial_tokens, (
        f"Token count should decrease after plucking. "
        f"Initial: {initial_tokens}, Final: {final_tokens}"
    )
    assert final_tokens <= target_limit, (
        f"Final tokens ({final_tokens}) should be under limit ({target_limit})"
    )
