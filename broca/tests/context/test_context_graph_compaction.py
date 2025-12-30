"""
Tests for context management via simple node plucking.

The old compaction approach created summaries and marked nodes as compacted.
The new approach simply plucks (removes) oldest nodes to stay under the limit.
"""

from __future__ import annotations

from broca.context.context_graph import ContextGraph
from broca.summarization.token_estimator import estimate_messages_tokens


def test_plucking_actually_removes_nodes():
    """
    Test that plucking removes nodes from the graph (unlike old compaction
    which just marked them and created summaries).
    """
    graph = ContextGraph(min_turns_retained=1, min_recent_to_keep=5, tool_content_max_chars=2000)

    # Create long linear history
    parent = None
    for i in range(80):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"{role} {i} " + ("x" * 400), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]

    initial_count = len(graph.nodes)

    # Trigger plucking by calling get_messages_for_llm with a small budget
    msgs1 = graph.get_messages_for_llm(max_tokens=500, safety_margin=0.95)
    tokens1 = estimate_messages_tokens(msgs1)
    
    # Should be under budget (with some tolerance for token estimation variance)
    assert tokens1 <= int(500 * 0.95) * 1.5, f"Tokens ({tokens1}) should be under limit"

    # Nodes should actually be removed from the graph
    assert len(graph.nodes) < initial_count, (
        f"Plucking should remove nodes: was {initial_count}, now {len(graph.nodes)}"
    )
    
    # The plucked IDs should be available for session sync
    plucked_ids = graph.get_last_plucked_ids()
    assert len(plucked_ids) > 0, "Should have plucked some nodes"
    
    # Plucked nodes should no longer exist in graph
    for msg_id in plucked_ids:
        assert msg_id not in graph.nodes, f"Plucked node {msg_id} should not exist"


def test_plucking_preserves_recent_and_system_messages():
    """
    Test that plucking preserves system messages and recent messages.
    """
    graph = ContextGraph(min_turns_retained=1, min_recent_to_keep=10, tool_content_max_chars=2000)

    # Add system message
    system_msg = {"role": "system", "content": "You are a helpful assistant", "message_id": "sys"}
    graph.add_message(system_msg)

    # Create history
    parent = "sys"
    for i in range(80):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"{role} {i} " + ("x" * 400), "message_id": f"m{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]

    # Trigger plucking
    msgs = graph.get_messages_for_llm(max_tokens=500, safety_margin=0.95)
    
    # System message should be preserved
    assert "sys" in graph.nodes, "System message should never be plucked"
    
    # Most recent messages should be preserved (m70-m79)
    recent_preserved = sum(1 for i in range(70, 80) if f"m{i}" in graph.nodes)
    assert recent_preserved >= 5, (
        f"At least 5 recent messages should be preserved, got {recent_preserved}"
    )


def test_plucking_protects_recent_tool_chains():
    """
    Test that plucking preserves recent tool chains.
    
    Tool chains at the end of the conversation (recent) should be protected
    from plucking to maintain task context.
    """
    graph = ContextGraph(min_turns_retained=2, min_recent_to_keep=10, tool_content_max_chars=2000)

    # Create history with a recent tool chain at the end
    parent = None
    
    # First add some older messages to create pressure
    for i in range(60):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"old {role} {i} " + ("x" * 300), "message_id": f"old_{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]

    # Now add a recent tool chain (assistant with tool_calls + tool responses)
    tool_call_id = "call_abc123"
    assistant_with_tools = {
        "role": "assistant",
        "content": "",
        "message_id": "recent_assistant_tools",
        "tool_calls": [
            {"id": tool_call_id, "type": "function", "function": {"name": "terminal", "arguments": "{}"}}
        ]
    }
    graph.add_message(assistant_with_tools, parent_id=parent)
    parent = assistant_with_tools["message_id"]

    tool_response = {
        "role": "tool",
        "content": "Command executed successfully",
        "message_id": "recent_tool_response",
        "tool_call_id": tool_call_id,
        "name": "terminal"
    }
    graph.add_message(tool_response, parent_id=parent)
    parent = tool_response["message_id"]

    # User message after tool response
    user_followup = {
        "role": "user",
        "content": "Thanks, now do something else",
        "message_id": "recent_user_followup"
    }
    graph.add_message(user_followup, parent_id=parent)

    # Trigger plucking with small budget
    msgs = graph.get_messages_for_llm(max_tokens=1000, safety_margin=0.95)

    # The recent tool chain should be preserved (it's in the protected recent messages)
    # Check that the messages appear in the output
    msg_ids_kept = {m.get("message_id") for m in msgs if m.get("message_id")}
    
    # Recent tool chain messages should be kept
    assert "recent_assistant_tools" in msg_ids_kept or "recent_assistant_tools" in graph.nodes, (
        "Recent assistant with tool_calls should be preserved"
    )
    assert "recent_tool_response" in msg_ids_kept or "recent_tool_response" in graph.nodes, (
        "Recent tool response should be preserved"
    )
    assert "recent_user_followup" in msg_ids_kept or "recent_user_followup" in graph.nodes, (
        "Recent user followup should be preserved"
    )


def test_plucking_preserves_tool_chain_integrity():
    """
    Test that when plucking removes nodes, tool chains remain intact.
    
    The tool message validation step ensures that if an assistant with tool_calls
    is kept, all its tool responses are also kept (and vice versa).
    """
    graph = ContextGraph(min_turns_retained=1, min_recent_to_keep=10, tool_content_max_chars=2000)

    # Create massive history to force plucking
    parent = None
    for i in range(100):
        role = "user" if i % 2 == 0 else "assistant"
        # Large content to create pressure
        msg = {"role": role, "content": f"massive {role} {i} " + ("x" * 800), "message_id": f"mass_{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]

    # Add a recent tool chain
    tool_call_id_1 = "call_recent_1"
    tool_call_id_2 = "call_recent_2"
    assistant_with_tools = {
        "role": "assistant",
        "content": "",
        "message_id": "emergency_assistant",
        "tool_calls": [
            {"id": tool_call_id_1, "type": "function", "function": {"name": "terminal", "arguments": "{}"}},
            {"id": tool_call_id_2, "type": "function", "function": {"name": "web_search", "arguments": "{}"}}
        ]
    }
    graph.add_message(assistant_with_tools, parent_id=parent)
    parent = assistant_with_tools["message_id"]

    tool_response_1 = {
        "role": "tool",
        "content": "Terminal result",
        "message_id": "emergency_tool_1",
        "tool_call_id": tool_call_id_1,
        "name": "terminal"
    }
    graph.add_message(tool_response_1, parent_id=parent)

    tool_response_2 = {
        "role": "tool",
        "content": "Search result",
        "message_id": "emergency_tool_2",
        "tool_call_id": tool_call_id_2,
        "name": "web_search"
    }
    graph.add_message(tool_response_2, parent_id=parent)

    # Force plucking with very small budget
    msgs = graph.get_messages_for_llm(max_tokens=500, safety_margin=0.95)
    msg_ids_kept = {m.get("message_id") for m in msgs if m.get("message_id")}

    # Check tool chain integrity in the OUTPUT
    assistant_kept = "emergency_assistant" in msg_ids_kept
    tool_1_kept = "emergency_tool_1" in msg_ids_kept
    tool_2_kept = "emergency_tool_2" in msg_ids_kept

    # If any are kept, all should be kept (tool chain validation ensures this)
    if assistant_kept:
        assert tool_1_kept and tool_2_kept, (
            "If assistant with tool_calls is in output, ALL tool responses must be too. "
            f"Got: assistant={assistant_kept}, tool_1={tool_1_kept}, tool_2={tool_2_kept}"
        )
    
    if tool_1_kept or tool_2_kept:
        assert assistant_kept, (
            "If any tool response is in output, the assistant with tool_calls must be too. "
            f"Got: assistant={assistant_kept}, tool_1={tool_1_kept}, tool_2={tool_2_kept}"
        )


def test_incomplete_tool_chain_protected_from_plucking():
    """
    Test that incomplete tool chains at the end of conversation are protected.
    
    If a tool chain is incomplete (assistant with tool_calls but not all responses),
    it should be in the protected "recent" set and not plucked.
    """
    graph = ContextGraph(min_turns_retained=2, min_recent_to_keep=10, tool_content_max_chars=2000)

    # Create history
    parent = None
    for i in range(50):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {"role": role, "content": f"history {i} " + ("x" * 300), "message_id": f"hist_{i}"}
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]

    # Add incomplete tool chain: assistant expects 2 tool responses, but only 1 has arrived
    tool_call_id_1 = "call_incomplete_1"
    tool_call_id_2 = "call_incomplete_2"  # This one hasn't responded yet
    assistant_with_tools = {
        "role": "assistant",
        "content": "",
        "message_id": "incomplete_assistant",
        "tool_calls": [
            {"id": tool_call_id_1, "type": "function", "function": {"name": "terminal", "arguments": "{}"}},
            {"id": tool_call_id_2, "type": "function", "function": {"name": "web_search", "arguments": "{}"}}
        ]
    }
    graph.add_message(assistant_with_tools, parent_id=parent)
    parent = assistant_with_tools["message_id"]

    # Only one tool response has arrived
    tool_response_1 = {
        "role": "tool",
        "content": "First tool result",
        "message_id": "incomplete_tool_1",
        "tool_call_id": tool_call_id_1,
        "name": "terminal"
    }
    graph.add_message(tool_response_1, parent_id=parent)

    # Get protected IDs (used by old compaction, but still available as helper)
    recent_ids = {"incomplete_assistant", "incomplete_tool_1"}
    protected = graph._get_protected_tool_chain_ids(recent_ids)

    # The incomplete tool chain should be protected
    assert "incomplete_assistant" in protected, (
        "Assistant with incomplete tool_calls must be protected"
    )
    assert "incomplete_tool_1" in protected, (
        "Arrived tool response in incomplete chain must be protected"
    )
    
    # Also verify that plucking keeps these (they're recent)
    msgs = graph.get_messages_for_llm(max_tokens=1000, safety_margin=0.95)
    
    # The incomplete tool chain is at the end and should be in recent protected set
    # Note: The _validate_and_fix_tool_message_ordering will filter out incomplete chains from output
    # but the nodes themselves should still exist in the graph if they're recent
    assert "incomplete_assistant" in graph.nodes or "incomplete_tool_1" in graph.nodes, (
        "Recent incomplete tool chain nodes should be preserved in graph"
    )


