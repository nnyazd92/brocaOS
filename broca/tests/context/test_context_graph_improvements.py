"""
Tests for architectural improvements to ContextGraph.

Tests tool call chain preservation, graph integrity, thread tracking, etc.
"""

from __future__ import annotations

import pytest
from broca.context.context_graph import ContextGraph


class TestToolCallChainPreservation:
    """Test tool call chain preservation."""
    
    def test_identify_tool_call_chains(self):
        """Test identifying tool call chains."""
        graph = ContextGraph()
        
        # Create tool call chain
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "call_1", "function": {"name": "test_tool"}}],
            "message_id": "assistant1",
        }
        graph.add_message(assistant_msg)
        
        tool_result = {
            "role": "tool",
            "content": "Result",
            "tool_call_id": "call_1",
            "name": "test_tool",
            "message_id": "tool1",
        }
        graph.add_message(tool_result, parent_id="assistant1")
        
        assistant_response = {
            "role": "assistant",
            "content": "Response after tool",
            "message_id": "assistant2",
        }
        graph.add_message(assistant_response, parent_id="tool1")
        
        # Identify chains
        chains = graph._identify_tool_call_chains()
        
        # Should find at least one chain
        assert len(chains) >= 1
        # Chain should include all three messages
        for chain_id, chain_messages in chains.items():
            if "assistant1" in chain_messages:
                assert "tool1" in chain_messages
                assert "assistant2" in chain_messages
    
    def test_prune_preserves_tool_chains(self):
        """Test that pruning preserves complete tool call chains."""
        graph = ContextGraph(min_turns_retained=1)
        
        # Create tool call chain
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "call_1", "function": {"name": "test"}}],
            "message_id": "assistant1",
        }
        graph.add_message(assistant_msg)
        
        tool_result = {
            "role": "tool",
            "content": "Result",
            "tool_call_id": "call_1",
            "message_id": "tool1",
        }
        graph.add_message(tool_result, parent_id="assistant1")
        
        assistant_response = {
            "role": "assistant",
            "content": "Response",
            "message_id": "assistant2",
        }
        graph.add_message(assistant_response, parent_id="tool1")
        
        # Prune with limit that would normally break chain
        to_keep, _ = graph.prune_to_fit(1000)
        
        # If assistant1 is kept, entire chain should be kept
        if "assistant1" in to_keep:
            assert "tool1" in to_keep
            assert "assistant2" in to_keep


class TestGraphIntegrity:
    """Test graph integrity validation."""
    
    def test_validate_graph_integrity_clean_graph(self):
        """Test validation on clean graph."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        issues = graph.validate_graph_integrity()
        
        # Clean graph should have no issues
        assert len(issues) == 0
    
    def test_validate_graph_integrity_detects_inconsistency(self):
        """Test that validation detects inconsistencies."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        # Corrupt: remove child from parent
        graph.nodes["msg1"].children.remove("msg2")
        
        issues = graph.validate_graph_integrity()
        
        # Should detect inconsistency
        assert len(issues) > 0
        assert any("not in parent" in issue.lower() for issue in issues)
    
    def test_validate_graph_integrity_detects_cycles(self):
        """Test that validation detects cycles."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        # Create cycle
        graph.nodes["msg1"].parent_id = "msg2"
        
        issues = graph.validate_graph_integrity()
        
        # Should detect cycle
        assert len(issues) > 0
        assert any("cycle" in issue.lower() for issue in issues)


class TestThreadTracking:
    """Test thread ID tracking and context."""
    
    def test_get_thread_context(self):
        """Test getting context for a thread."""
        graph = ContextGraph()
        
        # Create messages in main thread
        for i in range(5):
            msg = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "message_id": f"msg{i}",
            }
            parent_id = f"msg{i-1}" if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Get thread context
        context = graph.get_thread_context()
        
        # Should return messages in thread
        assert len(context) >= 5
        assert all(m.get("message_id") in [f"msg{i}" for i in range(5)] for m in context)
    
    def test_thread_id_assignment(self):
        """Test that thread IDs are assigned correctly."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg1)
        
        # First message should set main_thread_id
        assert graph.main_thread_id == "msg1"
        assert graph.nodes["msg1"].thread_id == "msg1"


class TestMessageDataValidation:
    """Test message data validation and reconstruction."""
    
    def test_ensure_message_data(self):
        """Test ensuring all nodes have message_data."""
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg)
        
        # Remove message_data
        graph.nodes["msg1"].message_data = None
        
        # Ensure message_data
        reconstructed = graph.ensure_message_data()
        
        # Should reconstruct
        assert reconstructed == 1
        assert graph.nodes["msg1"].message_data is not None
        assert graph.nodes["msg1"].message_data["role"] == "user"
        assert graph.nodes["msg1"].message_data["content"] == "Hello"


class TestAtomicOperations:
    """Test atomic operations with context manager."""
    
    def test_context_manager_lock(self):
        """Test that context manager provides locking."""
        graph = ContextGraph()
        
        # Should be able to use as context manager
        with graph:
            msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
            graph._add_message_unsafe(msg)  # Use unsafe version inside lock
        
        # Message should be added
        assert "msg1" in graph.nodes
    
    def test_atomic_operations(self):
        """Test that operations can be atomic."""
        graph = ContextGraph()
        
        with graph:
            # Multiple operations atomically
            for i in range(5):
                msg = {
                    "role": "user",
                    "content": f"Message {i}",
                    "message_id": f"msg{i}",
                }
                parent_id = f"msg{i-1}" if i > 0 else None
                graph._add_message_unsafe(msg, parent_id=parent_id)
        
        # All messages should be added
        assert len(graph.nodes) == 5

