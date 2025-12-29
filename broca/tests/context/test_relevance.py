"""
Unit tests for relevance scoring.
"""

import pytest
from datetime import datetime, timezone, timedelta
from broca.context.context_graph import MessageNode
from broca.context.relevance import compute_relevance_score


class TestRelevanceScoring:
    """Test relevance scoring algorithms."""
    
    def test_basic_relevance(self):
        """Test basic relevance scoring."""
        node = MessageNode(
            message_id="msg1",
            role="user",
            content="Hello",
        )
        score = compute_relevance_score(
            node=node,
            is_main_thread=True,
            is_recent=True,
        )
        assert score > 0
        assert isinstance(score, float)
    
    def test_main_thread_boost(self):
        """Test that main thread messages get boost."""
        node = MessageNode(
            message_id="msg1",
            role="user",
            content="Hello",
        )
        score_main = compute_relevance_score(
            node=node,
            is_main_thread=True,
            is_recent=False,
            main_thread_boost=2.0,
        )
        score_not_main = compute_relevance_score(
            node=node,
            is_main_thread=False,
            is_recent=False,
            main_thread_boost=2.0,
        )
        assert score_main > score_not_main
    
    def test_recency_boost(self):
        """Test that recent messages get boost."""
        node = MessageNode(
            message_id="msg1",
            role="user",
            content="Hello",
        )
        score_recent = compute_relevance_score(
            node=node,
            is_main_thread=False,
            is_recent=True,
        )
        score_not_recent = compute_relevance_score(
            node=node,
            is_main_thread=False,
            is_recent=False,
        )
        assert score_recent > score_not_recent
    
    def test_orphan_penalty(self):
        """Test that orphaned nodes get penalty."""
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
        
        assert score_orphan < score_not_orphan
    
    def test_role_adjustments(self):
        """Test role-based score adjustments."""
        user_node = MessageNode(
            message_id="msg1",
            role="user",
            content="Hello",
        )
        tool_node = MessageNode(
            message_id="msg2",
            role="tool",
            content="Result",
        )
        
        user_score = compute_relevance_score(
            node=user_node,
            is_main_thread=False,
            is_recent=False,
        )
        tool_score = compute_relevance_score(
            node=tool_node,
            is_main_thread=False,
            is_recent=False,
        )
        
        # User messages should generally score higher than tool messages
        assert user_score > tool_score
    
    def test_combined_factors(self):
        """Test that multiple factors combine correctly."""
        node = MessageNode(
            message_id="msg1",
            role="user",
            content="Hello",
        )
        # Main thread + recent should score highest
        score_high = compute_relevance_score(
            node=node,
            is_main_thread=True,
            is_recent=True,
            main_thread_boost=2.0,
        )
        # Not main thread + not recent should score lower
        score_low = compute_relevance_score(
            node=node,
            is_main_thread=False,
            is_recent=False,
            main_thread_boost=2.0,
        )
        assert score_high > score_low

