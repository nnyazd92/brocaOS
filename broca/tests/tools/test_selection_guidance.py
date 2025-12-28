"""
Tests for tool selection guidance system.

Includes mutation testing, property-based testing, and fault injection.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
from hypothesis import given, strategies as st

from broca.tools.selection_guidance import (
    ToolSelectionGuidance,
    GuidanceAggregator,
    ToolRanker,
    ToolValidator,
    ValidationResult,
    ToolRanking,
)
from broca.tools import Tool


class MockTool:
    """Mock tool for testing."""
    def __init__(self, name: str, description: str = "Test tool"):
        self.name = name
        self.description = description
        self.parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def execute(self, **kwargs):
        return {"success": True}
    
    def format_result(self, result):
        return str(result)


class TestGuidanceAggregator:
    """Test GuidanceAggregator."""
    
    def test_gather_context_with_all_components(self):
        """Test gathering context when all components are available."""
        # Setup mocks
        reasoning_tool = Mock()
        reasoning_tool.rule_system = Mock()
        reasoning_tool.rule_system.working_memory = Mock()
        reasoning_tool.rule_system.working_memory.items = [
            Mock(to_dict=lambda: {"content": "test"})
        ]
        reasoning_tool.rule_system.rules = [
            Mock(to_dict=lambda: {"name": "test_rule"})
        ]
        
        goal_manager = Mock()
        goal_manager.get_active_goals.return_value = [
            Mock(to_dict=lambda: {"name": "test_goal", "priority": 0.8})
        ]
        
        skill_manager = Mock()
        skill_manager.get_applicable_skills.return_value = [
            Mock(to_dict=lambda: {"name": "test_skill", "proficiency_level": 0.7})
        ]
        
        rl_signal_aggregator = Mock()
        rl_metrics = Mock()
        rl_metrics.composite_reward = 0.6
        rl_metrics.dissonance_reward = 0.7
        rl_metrics.surprise_reward = 0.5
        rl_metrics.curiosity_reward = 0.8
        rl_metrics.information_gain_reward = 0.4
        rl_metrics.coherence_reward = 0.9
        rl_metrics.get_exploration_exploitation_balance.return_value = 0.6
        rl_signal_aggregator.compute_signals.return_value = rl_metrics
        
        aggregator = GuidanceAggregator(
            reasoning_tool=reasoning_tool,
            rl_signal_aggregator=rl_signal_aggregator,
            skill_manager=skill_manager,
            goal_manager=goal_manager,
        )
        
        context = aggregator.gather_context()
        
        assert "active_goals" in context
        assert len(context["active_goals"]) > 0
        assert "applicable_skills" in context
        assert "rl_signals" in context
        assert context["rl_signals"]["composite_reward"] == 0.6
    
    def test_gather_context_with_no_components(self):
        """Test gathering context when no components are available."""
        aggregator = GuidanceAggregator()
        context = aggregator.gather_context()
        
        assert context["active_goals"] == []
        assert context["applicable_skills"] == []
        assert context["rl_signals"] is None
    
    def test_gather_context_handles_errors(self):
        """Test that gather_context handles errors gracefully."""
        goal_manager = Mock()
        goal_manager.get_active_goals.side_effect = Exception("Test error")
        
        aggregator = GuidanceAggregator(goal_manager=goal_manager)
        context = aggregator.gather_context()
        
        # Should return empty list on error
        assert context["active_goals"] == []


class TestToolRanker:
    """Test ToolRanker."""
    
    def test_rank_tools_basic(self):
        """Test basic tool ranking."""
        aggregator = GuidanceAggregator()
        ranker = ToolRanker(aggregator)
        
        tools = [
            MockTool("web_search"),
            MockTool("terminal"),
            MockTool("retrieve_memories"),
        ]
        
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings = ranker.rank_tools(tools, context)
        
        assert len(rankings) == 3
        assert all(isinstance(r, ToolRanking) for r in rankings)
        assert all(0.0 <= r.score <= 1.0 for r in rankings)
    
    def test_rank_tools_with_goals(self):
        """Test tool ranking with active goals."""
        aggregator = GuidanceAggregator()
        ranker = ToolRanker(aggregator)
        
        tools = [MockTool("web_search"), MockTool("terminal")]
        
        context = {
            "active_goals": [
                {"name": "find_information", "description": "find information", "priority": 0.9}
            ],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        rankings = ranker.rank_tools(tools, context)
        
        # web_search should rank higher due to goal relevance
        web_search_rank = next(r for r in rankings if r.tool_name == "web_search")
        terminal_rank = next(r for r in rankings if r.tool_name == "terminal")
        
        assert web_search_rank.score >= terminal_rank.score
    
    def test_record_tool_outcome(self):
        """Test recording tool usage outcomes."""
        aggregator = GuidanceAggregator()
        ranker = ToolRanker(aggregator)
        
        # Record some outcomes
        ranker.record_tool_outcome("test_tool", True)
        ranker.record_tool_outcome("test_tool", True)
        ranker.record_tool_outcome("test_tool", False)
        
        # Check historical success rate
        assert "test_tool" in ranker.historical_success
        assert 0.0 <= ranker.historical_success["test_tool"] <= 1.0
        # Should be ~0.67 (2 successes out of 3)
        assert ranker.historical_success["test_tool"] > 0.5


class TestToolValidator:
    """Test ToolValidator."""
    
    def test_validate_tool_selection_valid(self):
        """Test validation of valid tool selection."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        context = {
            "active_goals": [],
            "rl_signals": None,
            "production_rules": [],
        }
        
        result = validator.validate_tool_selection(
            "web_search",
            {"query": "test"},
            context
        )
        
        assert result.is_valid
        assert len(result.warnings) == 0
    
    def test_validate_tool_selection_with_goal_conflict(self):
        """Test validation detects goal conflicts."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        context = {
            "active_goals": [
                {"name": "read_only_mode", "description": "read only mode", "priority": 1.0}
            ],
            "rl_signals": None,
            "production_rules": [],
        }
        
        result = validator.validate_tool_selection(
            "store_memory",
            {"content": "test"},
            context
        )
        
        # Should detect conflict with read-only goal
        assert not result.is_valid or len(result.warnings) > 0
    
    @given(
        tool_name=st.sampled_from(["web_search", "terminal", "retrieve_memories"]),
        has_goals=st.booleans(),
        has_rl_signals=st.booleans(),
    )
    def test_validate_tool_selection_property(self, tool_name, has_goals, has_rl_signals):
        """Property: Validation always returns ValidationResult."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        context = {
            "active_goals": [{"name": "test", "priority": 0.5}] if has_goals else [],
            "rl_signals": {"composite_reward": 0.5} if has_rl_signals else None,
            "production_rules": [],
        }
        
        result = validator.validate_tool_selection(
            tool_name,
            {},
            context
        )
        
        assert isinstance(result, ValidationResult)
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.warnings, list)
        assert isinstance(result.suggestions, list)
        assert 0.0 <= result.confidence <= 1.0


class TestToolSelectionGuidance:
    """Test ToolSelectionGuidance."""
    
    def test_generate_guidance_text_empty(self):
        """Test guidance generation with no context."""
        guidance = ToolSelectionGuidance()
        text = guidance.generate_guidance_text()
        
        assert isinstance(text, str)
        # Should be empty or minimal when no context
    
    def test_generate_guidance_text_with_goals(self):
        """Test guidance generation with active goals."""
        goal_manager = Mock()
        goal_manager.get_active_goals.return_value = [
            Mock(to_dict=lambda: {"name": "test_goal", "priority": 0.9})
        ]
        
        guidance = ToolSelectionGuidance(goal_manager=goal_manager)
        text = guidance.generate_guidance_text()
        
        assert isinstance(text, str)
        assert len(text) > 0
    
    def test_filter_and_rank_tools(self):
        """Test tool filtering and ranking."""
        guidance = ToolSelectionGuidance()
        
        tools = [
            MockTool("web_search"),
            MockTool("terminal"),
            MockTool("retrieve_memories"),
        ]
        
        ranked = guidance.filter_and_rank_tools(tools)
        
        assert len(ranked) == 3
        assert all(isinstance(t, MockTool) for t in ranked)
        # Tools should be reordered by rank
    
    def test_validate_tool_selection(self):
        """Test tool selection validation."""
        guidance = ToolSelectionGuidance()
        
        result = guidance.validate_tool_selection(
            "web_search",
            {"query": "test"},
        )
        
        assert isinstance(result, ValidationResult)
    
    def test_record_tool_outcome(self):
        """Test recording tool outcomes."""
        guidance = ToolSelectionGuidance()
        
        # Should not raise
        guidance.record_tool_outcome("test_tool", True)
        guidance.record_tool_outcome("test_tool", False)
    
    def test_guidance_text_length_limit(self):
        """Test that guidance text respects length limit."""
        guidance = ToolSelectionGuidance(max_guidance_length=100)
        
        # Create context that would generate long guidance
        goal_manager = Mock()
        goal_manager.get_active_goals.return_value = [
            Mock(to_dict=lambda: {"name": f"goal_{i}", "priority": 0.9})
            for i in range(20)
        ]
        guidance.guidance_aggregator.goal_manager = goal_manager
        
        text = guidance.generate_guidance_text()
        
        assert len(text) <= 100


class TestFaultInjection:
    """Test fault injection scenarios."""
    
    def test_guidance_aggregator_handles_missing_attributes(self):
        """Test that aggregator handles missing attributes gracefully."""
        reasoning_tool = Mock()
        reasoning_tool.rule_system = None  # Missing attribute
        
        aggregator = GuidanceAggregator(reasoning_tool=reasoning_tool)
        context = aggregator.gather_context()
        
        # Should not raise, should return empty context
        assert isinstance(context, dict)
    
    def test_tool_ranker_handles_empty_tools(self):
        """Test ranker handles empty tool list."""
        aggregator = GuidanceAggregator()
        ranker = ToolRanker(aggregator)
        
        rankings = ranker.rank_tools([], {})
        
        assert rankings == []
    
    def test_validator_handles_none_context(self):
        """Test validator handles None context."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        # Should not raise
        result = validator.validate_tool_selection("test_tool", {}, context=None)
        assert isinstance(result, ValidationResult)


class TestMutationTesting:
    """Mutation testing scenarios."""
    
    def test_guidance_with_mutated_goals(self):
        """Test guidance generation with mutated goal data."""
        goal_manager = Mock()
        # Mutated: goals with invalid structure
        goal_manager.get_active_goals.return_value = [
            Mock(to_dict=lambda: {"invalid": "structure"})
        ]
        
        guidance = ToolSelectionGuidance(goal_manager=goal_manager)
        text = guidance.generate_guidance_text()
        
        # Should handle gracefully
        assert isinstance(text, str)
    
    def test_ranking_with_mutated_rl_signals(self):
        """Test ranking with mutated RL signal data."""
        aggregator = GuidanceAggregator()
        ranker = ToolRanker(aggregator)
        
        tools = [MockTool("web_search")]
        
        # Mutated: invalid RL signal structure
        context = {
            "active_goals": [],
            "rl_signals": {"invalid": "structure", "composite_reward": "not_a_number"},
            "applicable_skills": [],
            "working_memory_items": [],
        }
        
        # Should handle gracefully
        rankings = ranker.rank_tools(tools, context)
        assert len(rankings) == 1

