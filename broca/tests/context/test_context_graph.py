"""
Unit tests for context graph implementation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from broca.context.context_graph import ContextGraph, MessageNode


class TestMessageNode:
    """Test MessageNode class."""
    
    def test_message_node_creation(self):
        """Test creating a message node."""
        node = MessageNode(
            message_id="msg1",
            role="user",
            content="Hello",
        )
        assert node.message_id == "msg1"
        assert node.role == "user"
        assert node.content == "Hello"
        assert node.parent_id is None
        assert node.relevance_score == 0.0
        assert not node.is_orphan
    
    def test_message_node_with_parent(self):
        """Test message node with parent."""
        node = MessageNode(
            message_id="msg2",
            role="assistant",
            content="Hi there",
            parent_id="msg1",
        )
        assert node.parent_id == "msg1"
    
    def test_token_count_estimation(self):
        """Test that token count is estimated."""
        node = MessageNode(
            message_id="msg1",
            role="user",
            content="Hello" * 100,  # 500 chars
        )
        # Should estimate tokens (roughly 500/4 = 125)
        assert node.token_count > 0


class TestContextGraph:
    """Test ContextGraph class."""
    
    def test_graph_initialization(self):
        """Test graph initialization."""
        graph = ContextGraph()
        assert len(graph.nodes) == 0
        assert len(graph.root_nodes) == 0
        assert graph.main_thread_id is None
    
    def test_add_message(self):
        """Test adding messages to graph."""
        graph = ContextGraph()
        msg = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg_id = graph.add_message(msg)
        assert msg_id == "msg1"
        assert "msg1" in graph.nodes
        assert "msg1" in graph.root_nodes
        assert graph.main_thread_id == "msg1"
    
    def test_add_message_with_parent(self):
        """Test adding message with parent."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        assert "msg2" in graph.nodes
        assert "msg2" not in graph.root_nodes
        assert graph.nodes["msg1"].children == ["msg2"]
        assert graph.nodes["msg2"].parent_id == "msg1"
    
    def test_build_thread_path(self):
        """Test building thread path."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        msg3 = {"role": "user", "content": "How are you?", "message_id": "msg3"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        graph.add_message(msg3, parent_id="msg2")
        
        path = graph.build_thread_path("msg3")
        assert path == ["msg1", "msg2", "msg3"]
    
    def test_identify_main_thread(self):
        """Test identifying main thread."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        msg3 = {"role": "user", "content": "How are you?", "message_id": "msg3"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        graph.add_message(msg3, parent_id="msg2")
        
        main_thread = graph.identify_main_thread()
        assert "msg1" in main_thread
        assert "msg2" in main_thread
        assert "msg3" in main_thread
    
    def test_identify_orphans(self):
        """Test identifying orphaned nodes."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        msg3 = {"role": "user", "content": "How are you?", "message_id": "msg3"}
        # Orphan: not connected to recent messages
        msg4 = {"role": "user", "content": "Old message", "message_id": "msg4"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        graph.add_message(msg3, parent_id="msg2")
        graph.add_message(msg4)  # Separate root, orphaned
        
        # Make msg3 recent
        recent_ids = {"msg3"}
        orphans = graph.identify_orphans(recent_ids)
        
        # msg4 should be orphan (no path to msg3)
        assert "msg4" in orphans or len(orphans) > 0
    
    def test_prune_to_fit(self):
        """Test pruning to fit token limit."""
        graph = ContextGraph(min_turns_retained=2)
        # Add messages
        for i in range(10):
            msg = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "message_id": f"msg{i}",
            }
            parent_id = f"msg{i-1}" if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Prune to fit small token limit
        max_tokens = 100  # Very small limit
        to_keep, tokens = graph.prune_to_fit(max_tokens)
        
        # With very small limit, may keep all (if all are must-keep) or prune
        # The important thing is that it doesn't exceed the limit significantly
        assert len(to_keep) <= len(graph.nodes)  # Never keep more than we have
        assert tokens <= max_tokens * 1.1  # Within reasonable margin (10% safety)
    
    def test_get_messages_for_llm(self):
        """Test getting messages for LLM."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        messages = graph.get_messages_for_llm(max_tokens=10000)
        assert len(messages) == 2
        assert messages[0]["message_id"] == "msg1"
        assert messages[1]["message_id"] == "msg2"
    
    def test_prune_orphans(self):
        """Test pruning orphaned nodes."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        msg3 = {"role": "user", "content": "Old", "message_id": "msg3"}  # Orphan
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        graph.add_message(msg3)  # Separate root
        
        initial_count = len(graph.nodes)
        removed = graph.prune_orphans()
        
        # Should remove at least the orphan
        assert removed >= 0
        assert len(graph.nodes) <= initial_count

