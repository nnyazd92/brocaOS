"""
Property-based tests for ranking algorithms.

Tests ranking algorithm properties like monotonicity and consistency.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock
from typing import List
from hypothesis import given, strategies as st, settings, HealthCheck

from broca.tools.selection_guidance import (
    MultiArmedBanditRanker,
    ToolRanker,
    GuidanceAggregator,
    ToolRanking,
)
from broca.tools import Tool


class MockTool:
    """Mock tool for testing."""
    def __init__(self, name: str):
        self.name = name
        self.description = f"Tool {name}"
        self.parameters = {"type": "object", "properties": {}, "required": []}


class TestRankingProperties:
    """Property-based tests for ranking algorithms."""
    
    @given(
        num_tools=st.integers(min_value=1, max_value=20),
        exploration_factor=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_ranking_monotonicity(self, num_tools, exploration_factor):
        """Property: Rankings are monotonic (higher score = better rank)."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(
            exploration_factor=exploration_factor,
            base_ranker=base_ranker
        )
        
        tools = [MockTool(f"tool{i}") for i in range(num_tools)]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings = mab_ranker.rank_tools(tools, context)
        
        # Check monotonicity: scores should be non-increasing
        for i in range(len(rankings) - 1):
            assert rankings[i].score >= rankings[i + 1].score, \
                f"Ranking not monotonic: rank {i} score {rankings[i].score} < rank {i+1} score {rankings[i+1].score}"
    
    @given(
        num_tools=st.integers(min_value=1, max_value=20)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    def test_ranking_completeness(self, num_tools):
        """Property: All tools appear in rankings."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(base_ranker=base_ranker)
        
        tools = [MockTool(f"tool{i}") for i in range(num_tools)]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings = mab_ranker.rank_tools(tools, context)
        
        # All tools should be ranked
        assert len(rankings) == num_tools
        
        # All tool names should appear
        ranked_names = {r.tool_name for r in rankings}
        tool_names = {t.name for t in tools}
        assert ranked_names == tool_names
    
    @given(
        num_tools=st.integers(min_value=1, max_value=20),
        exploration_factor=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    def test_ranking_score_bounds(self, num_tools, exploration_factor):
        """Property: All ranking scores are in [0, 1]."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(
            exploration_factor=exploration_factor,
            base_ranker=base_ranker
        )
        
        tools = [MockTool(f"tool{i}") for i in range(num_tools)]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings = mab_ranker.rank_tools(tools, context)
        
        for ranking in rankings:
            assert 0.0 <= ranking.score <= 1.0, \
                f"Score {ranking.score} out of bounds for tool {ranking.tool_name}"
    
    @given(
        num_tools=st.integers(min_value=1, max_value=20)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    def test_ranking_consistency(self, num_tools):
        """Property: Rankings are consistent (same input = same output)."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(base_ranker=base_ranker)
        
        tools = [MockTool(f"tool{i}") for i in range(num_tools)]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings1 = mab_ranker.rank_tools(tools, context)
        rankings2 = mab_ranker.rank_tools(tools, context)
        
        # Rankings should be identical (no randomness in base case)
        assert len(rankings1) == len(rankings2)
        for r1, r2 in zip(rankings1, rankings2):
            assert r1.tool_name == r2.tool_name
            assert abs(r1.score - r2.score) < 0.001  # Allow small floating point differences


class TestMultiArmedBandit:
    """Tests for MultiArmedBanditRanker."""
    
    def test_exploration_bonus_for_unexplored_tools(self):
        """Test that unexplored tools get exploration bonus."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(
            exploration_factor=0.5,
            base_ranker=base_ranker
        )
        
        tools = [MockTool("tool1"), MockTool("tool2")]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings = mab_ranker.rank_tools(tools, context)
        
        # Unexplored tools should have high scores (exploration bonus)
        for ranking in rankings:
            if ranking.exploration_bonus > 0:
                assert ranking.score >= 0.5  # Should be boosted
    
    def test_exploitation_after_learning(self):
        """Test that ranking improves after learning."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(
            exploration_factor=0.1,
            base_ranker=base_ranker
        )
        
        tools = [MockTool("tool1"), MockTool("tool2")]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        # Initial rankings
        rankings1 = mab_ranker.rank_tools(tools, context)
        
        # Record successful usage of tool1
        mab_ranker.record_tool_selection("tool1", reward=1.0)
        mab_ranker.record_tool_selection("tool1", reward=1.0)
        
        # Record failed usage of tool2
        mab_ranker.record_tool_selection("tool2", reward=0.0)
        
        # New rankings should favor tool1
        rankings2 = mab_ranker.rank_tools(tools, context)
        
        # Tool1 should be ranked higher (or at least have higher expected reward)
        tool1_ranking = next(r for r in rankings2 if r.tool_name == "tool1")
        tool2_ranking = next(r for r in rankings2 if r.tool_name == "tool2")
        
        assert tool1_ranking.expected_reward > tool2_ranking.expected_reward
    
    def test_confidence_intervals(self):
        """Test that confidence intervals are provided."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(base_ranker=base_ranker)
        
        tools = [MockTool("tool1")]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings = mab_ranker.rank_tools(tools, context)
        
        for ranking in rankings:
            assert hasattr(ranking, "confidence_interval")
            assert len(ranking.confidence_interval) == 2
            lower, upper = ranking.confidence_interval
            assert lower <= ranking.score <= upper


class TestRankingEdgeCases:
    """Test edge cases for ranking."""
    
    def test_empty_tools_list(self):
        """Test ranking with empty tools list."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(base_ranker=base_ranker)
        
        rankings = mab_ranker.rank_tools([], {})
        
        assert rankings == []
    
    def test_single_tool(self):
        """Test ranking with single tool."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(base_ranker=base_ranker)
        
        tools = [MockTool("tool1")]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings = mab_ranker.rank_tools(tools, context)
        
        assert len(rankings) == 1
        assert rankings[0].tool_name == "tool1"
    
    def test_ranking_with_none_context(self):
        """Test ranking handles None context gracefully."""
        aggregator = GuidanceAggregator()
        base_ranker = ToolRanker(aggregator)
        mab_ranker = MultiArmedBanditRanker(base_ranker=base_ranker)
        
        tools = [MockTool("tool1")]
        
        # Should not raise
        rankings = mab_ranker.rank_tools(tools, None)
        assert len(rankings) == 1

