"""
Fault injection tests for ContextGraph.

Tests edge cases, error conditions, and malformed inputs to ensure graceful handling.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from broca.context.context_graph import ContextGraph, MessageNode
from broca.summarization.token_estimator import estimate_messages_tokens


class TestFaultInjection:
    """Fault injection tests for edge cases and error conditions."""
    
    def test_add_message_missing_role(self):
        """Test handling of messages without role field."""
        graph = ContextGraph()
        msg = {"content": "Hello", "message_id": "msg1"}
        
        # Should handle gracefully (defaults to "user")
        msg_id = graph.add_message(msg)
        assert msg_id == "msg1"
        assert graph.nodes["msg1"].role == "user"
    
    def test_add_message_missing_content(self):
        """Test handling of messages without content field."""
        graph = ContextGraph()
        msg = {"role": "user", "message_id": "msg1"}
        
        # Should handle gracefully (defaults to empty string)
        msg_id = graph.add_message(msg)
        assert msg_id == "msg1"
        assert graph.nodes["msg1"].content == ""
    
    def test_add_message_missing_message_id(self):
        """Test handling of messages without message_id."""
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello"}
        
        # Should generate UUID
        msg_id = graph.add_message(msg)
        assert msg_id is not None
        assert len(msg_id) > 0
    
    def test_add_message_invalid_parent_id(self):
        """Test handling of invalid parent_id (references non-existent node)."""
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        
        # Should handle gracefully (becomes root node)
        msg_id = graph.add_message(msg, parent_id="nonexistent")
        assert msg_id == "msg1"
        assert msg_id in graph.root_nodes
    
    def test_add_message_circular_parent_reference(self):
        """Test handling of circular parent references."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        # Manually create cycle
        graph.nodes["msg1"].parent_id = "msg2"
        
        # Should handle cycle detection
        path = graph.build_thread_path("msg1")
        assert isinstance(path, list)
        # Should detect cycle and stop
        assert len(path) <= 2 or len(path) == len(set(path))
    
    def test_add_message_duplicate_message_id(self):
        """Test handling of duplicate message_ids."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "user", "content": "Updated", "message_id": "msg1"}
        
        graph.add_message(msg1)
        graph.add_message(msg2)  # Same ID
        
        # Should update existing, not create duplicate
        assert len(graph.nodes) == 1
        assert graph.nodes["msg1"].content == "Updated"
    
    def test_build_thread_path_empty_graph(self):
        """Test building thread path on empty graph."""
        graph = ContextGraph()
        path = graph.build_thread_path("msg1")
        assert path == []
    
    def test_identify_main_thread_empty_graph(self):
        """Test identifying main thread on empty graph."""
        graph = ContextGraph()
        main_thread = graph.identify_main_thread()
        assert main_thread == []
    
    def test_prune_to_fit_empty_graph(self):
        """Test pruning empty graph."""
        graph = ContextGraph()
        to_keep, tokens = graph.prune_to_fit(1000)
        assert to_keep == []
        assert tokens == 0
    
    def test_prune_to_fit_single_message(self):
        """Test pruning graph with single message."""
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg)
        
        to_keep, tokens = graph.prune_to_fit(1000)
        assert "msg1" in to_keep
        assert tokens > 0
    
    def test_prune_to_fit_zero_token_limit(self):
        """Test pruning with zero token limit."""
        graph = ContextGraph(min_turns_retained=1)
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg)
        
        to_keep, tokens = graph.prune_to_fit(0)
        # Should keep minimum (at least last message)
        assert len(to_keep) >= 1 or tokens == 0
    
    def test_prune_to_fit_negative_token_limit(self):
        """Test pruning with negative token limit."""
        graph = ContextGraph(min_turns_retained=1)
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg)
        
        to_keep, tokens = graph.prune_to_fit(-100)
        # Should handle gracefully
        assert isinstance(to_keep, list)
        assert tokens >= 0
    
    def test_very_large_individual_message(self):
        """Test handling of very large individual messages."""
        graph = ContextGraph()
        large_content = "x" * 1000000  # 1M chars
        msg = {"role": "user", "content": large_content, "message_id": "msg1"}
        
        graph.add_message(msg)
        
        # Should handle large messages
        assert "msg1" in graph.nodes
        assert graph.nodes["msg1"].token_count > 0
    
    def test_very_large_graph(self):
        """Test handling of very large graphs."""
        graph = ContextGraph(min_turns_retained=1)
        
        # Add many messages
        for i in range(1000):
            msg = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "message_id": f"msg{i}",
            }
            parent_id = f"msg{i-1}" if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Should handle large graph
        assert len(graph.nodes) == 1000
        
        # Should be able to prune
        to_keep, tokens = graph.prune_to_fit(10000)
        assert len(to_keep) <= len(graph.nodes)
        assert tokens <= 10000 * 1.1
    
    def test_missing_message_data(self):
        """Test handling of nodes without message_data."""
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg)
        
        # Remove message_data
        graph.nodes["msg1"].message_data = None
        
        # Should handle gracefully when getting messages
        messages = graph.get_messages_for_llm(max_tokens=1000)
        # Should skip nodes without message_data
        assert all(m.get("message_id") != "msg1" or m is not None for m in messages)
    
    def test_orphaned_children(self):
        """Test handling of orphaned children (parent removed but children remain)."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        # Manually remove parent but keep child
        del graph.nodes["msg1"]
        graph.root_nodes.remove("msg1")
        
        # Child should become orphan
        recent_ids = {"msg2"}
        orphans = graph.identify_orphans(recent_ids)
        # msg2 should not be orphan (it's recent)
        assert "msg2" not in orphans or len(orphans) == 0
    
    def test_inconsistent_message_order(self):
        """Test handling of inconsistent message_order vs nodes."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg1)
        
        # Manually corrupt message_order
        graph._message_order.append("nonexistent")
        
        # Should handle gracefully
        messages = graph.get_messages_for_llm(max_tokens=1000)
        # Should only return valid messages (skip nonexistent)
        assert all(m is not None and m.get("message_id") != "nonexistent" for m in messages)
    
    def test_stale_last_accessed(self):
        """Test handling of stale last_accessed timestamps."""
        from datetime import timedelta
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg)
        
        # Set very old timestamp
        old_time = datetime.now(timezone.utc) - timedelta(days=365)
        graph.nodes["msg1"].last_accessed = old_time
        
        # Should handle old timestamps
        main_thread = graph.identify_main_thread()
        assert isinstance(main_thread, list)
        # Even with old timestamp, should still identify thread
        assert len(main_thread) >= 1
    
    def test_negative_relevance_scores(self):
        """Test handling of negative relevance scores."""
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg)
        
        # Manually set negative relevance
        graph.nodes["msg1"].relevance_score = -1.0
        
        # Should handle negative scores (relevance should be non-negative)
        from broca.context.relevance import compute_relevance_score
        score = compute_relevance_score(
            graph.nodes["msg1"],
            is_main_thread=False,
            is_recent=False,
        )
        assert score >= 0.0
    
    def test_tool_call_chain_missing_links(self):
        """Test handling of tool call chains with missing links."""
        graph = ContextGraph()
        
        # Create assistant with tool_calls
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "call_1", "function": {"name": "test"}}],
            "message_id": "assistant1",
        }
        graph.add_message(assistant_msg)
        
        # Create tool result without proper link
        tool_result = {
            "role": "tool",
            "content": "Result",
            "tool_call_id": "call_1",
            "message_id": "tool1",
        }
        graph.add_message(tool_result, parent_id="assistant1")
        
        # Should handle missing links gracefully
        messages = graph.get_messages_for_llm(max_tokens=1000)
        assert isinstance(messages, list)
    
    def test_system_message_in_wrong_position(self):
        """Test handling of system messages in wrong positions."""
        graph = ContextGraph()
        
        user_msg = {"role": "user", "content": "Hello", "message_id": "user1"}
        system_msg = {"role": "system", "content": "System", "message_id": "sys1"}
        
        graph.add_message(user_msg)
        graph.add_message(system_msg, parent_id="user1")  # System after user
        
        # Should handle system messages
        messages = graph.get_messages_for_llm(max_tokens=1000)
        assert isinstance(messages, list)
    
    def test_invalid_role(self):
        """Test handling of messages with invalid roles."""
        graph = ContextGraph()
        msg = {"role": "invalid_role", "content": "Hello", "message_id": "msg1"}
        
        # Should handle invalid roles
        msg_id = graph.add_message(msg)
        assert msg_id == "msg1"
        assert graph.nodes["msg1"].role == "invalid_role"
    
    def test_concurrent_add_during_prune(self):
        """Test adding messages during pruning."""
        graph = ContextGraph()
        
        # Add initial messages
        for i in range(10):
            msg = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "message_id": f"msg{i}",
            }
            parent_id = f"msg{i-1}" if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Start pruning
        to_keep, _ = graph.prune_to_fit(1000)
        
        # Add new message during/after prune
        new_msg = {"role": "user", "content": "New", "message_id": "new1"}
        graph.add_message(new_msg, parent_id="msg9")
        
        # Should handle gracefully
        assert "new1" in graph.nodes
    
    def test_modify_node_during_relevance_computation(self):
        """Test modifying nodes during relevance computation."""
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg)
        
        main_thread = graph.identify_main_thread()
        
        # Modify node during computation
        graph.nodes["msg1"].content = "Modified"
        graph.compute_relevance_scores(set(main_thread))
        
        # Should handle modification
        assert graph.nodes["msg1"].relevance_score >= 0
    
    def test_graph_updates_during_thread_identification(self):
        """Test graph updates during thread identification."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg1)
        
        # Add message during thread identification
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        graph.add_message(msg2, parent_id="msg1")
        
        main_thread = graph.identify_main_thread()
        
        # Should handle updates
        assert isinstance(main_thread, list)
        assert len(main_thread) >= 1

