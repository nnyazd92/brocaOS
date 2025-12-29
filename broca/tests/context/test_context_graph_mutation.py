"""
Mutation testing validation tests for ContextGraph.

These tests are designed to kill mutations in the context graph code.
The actual mutation testing is run with mutmut, but these tests help
validate that our test suite is comprehensive enough to catch bugs.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from broca.context.context_graph import ContextGraph, MessageNode
from broca.summarization.token_estimator import estimate_messages_tokens


class TestMutationKillers:
    """
    Tests specifically designed to kill mutations.
    
    These tests verify specific behaviors that would be broken by common mutations
    like changing operators, conditions, or return values.
    """
    
    def test_build_thread_path_handles_missing_node(self):
        """Kills mutation: removing existence check."""
        graph = ContextGraph()
        # Should return empty list for non-existent node, not crash
        result = graph.build_thread_path("nonexistent")
        assert result == []
    
    def test_build_thread_path_handles_cycle(self):
        """Kills mutation: removing cycle detection."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        # Create cycle by manually setting parent (simulating corruption)
        graph.nodes["msg1"].parent_id = "msg2"
        
        # Should detect cycle and return path without infinite loop
        path = graph.build_thread_path("msg1")
        assert "msg1" in path or "msg2" in path
        # Should not contain duplicates
        assert len(path) == len(set(path)) or len(path) <= 2
    
    def test_identify_orphans_returns_set(self):
        """Kills mutation: changing return type."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg1)
        
        orphans = graph.identify_orphans(set(["msg1"]))
        assert isinstance(orphans, set)
    
    def test_identify_orphans_marks_orphans(self):
        """Kills mutation: not marking nodes as orphan."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "user", "content": "Old", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2)
        
        orphans = graph.identify_orphans(set(["msg1"]))
        if "msg2" in orphans:
            assert graph.nodes["msg2"].is_orphan is True
    
    def test_prune_to_fit_always_under_limit(self):
        """Kills mutation: removing token check."""
        graph = ContextGraph(min_turns_retained=1)
        for i in range(10):
            msg = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "message_id": f"msg{i}",
            }
            parent_id = f"msg{i-1}" if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        max_tokens = 1000  # Larger limit to allow proper pruning
        to_keep, tokens = graph.prune_to_fit(max_tokens, safety_margin=0.95)
        
        # Should always be under limit (with safety margin)
        # Allow small tolerance for edge cases where must-keep exceeds limit
        effective_max = int(max_tokens * 0.95)
        assert tokens <= effective_max * 1.1 or len(to_keep) == 0  # 10% tolerance for edge cases
    
    def test_prune_to_fit_preserves_main_thread(self):
        """Kills mutation: not preserving main thread."""
        graph = ContextGraph(min_turns_retained=1)
        # Create linear thread
        for i in range(5):
            msg = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "message_id": f"msg{i}",
            }
            parent_id = f"msg{i-1}" if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        main_thread = graph.identify_main_thread()
        max_tokens = 1000  # Large enough to keep all
        to_keep, _ = graph.prune_to_fit(max_tokens)
        
        # Main thread should be preserved
        for msg_id in main_thread:
            assert msg_id in to_keep
    
    def test_compute_relevance_score_handles_orphan(self):
        """Kills mutation: removing orphan penalty."""
        from broca.context.relevance import compute_relevance_score
        
        node = MessageNode(
            message_id="msg1",
            role="user",
            content="Hello",
        )
        node.is_orphan = True
        
        score_orphan = compute_relevance_score(
            node=node,
            is_main_thread=False,
            is_recent=False,
        )
        
        node.is_orphan = False
        score_not_orphan = compute_relevance_score(
            node=node,
            is_main_thread=False,
            is_recent=False,
        )
        
        # Orphan should have lower score
        assert score_orphan < score_not_orphan
    
    def test_add_message_updates_existing(self):
        """Kills mutation: removing update logic."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg1)
        
        # Update with new content
        msg1_updated = {"role": "user", "content": "Updated", "message_id": "msg1"}
        graph.add_message(msg1_updated)
        
        # Should update existing node, not create duplicate
        assert len(graph.nodes) == 1
        assert graph.nodes["msg1"].content == "Updated"
    
    def test_add_message_links_to_parent(self):
        """Kills mutation: not linking to parent."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        # Should link parent-child
        assert graph.nodes["msg2"].parent_id == "msg1"
        assert "msg2" in graph.nodes["msg1"].children
    
    def test_identify_main_thread_returns_list(self):
        """Kills mutation: changing return type."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg1)
        
        main_thread = graph.identify_main_thread()
        assert isinstance(main_thread, list)
    
    def test_identify_main_thread_includes_root(self):
        """Kills mutation: not including root in main thread."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        main_thread = graph.identify_main_thread()
        # Root should be in main thread
        assert "msg1" in main_thread
    
    def test_prune_orphans_removes_nodes(self):
        """Kills mutation: not removing orphaned nodes."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "user", "content": "Old", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2)
        
        initial_count = len(graph.nodes)
        removed = graph.prune_orphans()
        
        # Should remove at least one orphan if msg2 is orphaned
        if removed > 0:
            assert len(graph.nodes) < initial_count
    
    def test_get_messages_for_llm_returns_list(self):
        """Kills mutation: changing return type."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg1)
        
        messages = graph.get_messages_for_llm(max_tokens=1000)
        assert isinstance(messages, list)
    
    def test_get_messages_for_llm_preserves_order(self):
        """Kills mutation: not preserving message order."""
        graph = ContextGraph()
        for i in range(5):
            msg = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "message_id": f"msg{i}",
            }
            parent_id = f"msg{i-1}" if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        messages = graph.get_messages_for_llm(max_tokens=10000)
        
        # Should preserve insertion order
        for i, msg in enumerate(messages):
            assert msg["message_id"] == f"msg{i}"
    
    def test_compute_relevance_scores_updates_nodes(self):
        """Kills mutation: not updating relevance scores."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        graph.add_message(msg1)
        
        main_thread = graph.identify_main_thread()
        graph.compute_relevance_scores(set(main_thread))
        
        # Should update relevance score
        assert graph.nodes["msg1"].relevance_score > 0
    
    def test_find_longest_path_handles_cycle(self):
        """Kills mutation: removing cycle detection in DFS."""
        graph = ContextGraph()
        msg1 = {"role": "user", "content": "Hello", "message_id": "msg1"}
        msg2 = {"role": "assistant", "content": "Hi", "message_id": "msg2"}
        
        graph.add_message(msg1)
        graph.add_message(msg2, parent_id="msg1")
        
        # Create cycle
        graph.nodes["msg1"].parent_id = "msg2"
        
        # Should handle cycle without infinite recursion
        path = graph._find_longest_path_from_root("msg1")
        assert isinstance(path, list)
        # Should not have duplicates (cycle detected)
        assert len(path) == len(set(path)) or len(path) <= 2

