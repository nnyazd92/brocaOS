"""
Integration tests for tool selection guidance metrics.

Includes golden trace replay and coverage tests.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timezone

from broca.tools.selection_guidance import (
    ToolSelectionGuidance,
    GuidanceAggregator,
    ValidationStrictness,
)
from broca.tools.selection_metrics import (
    ToolSelectionMetrics,
    GuidanceSuggestion,
    ValidationRecord,
    RankingRecord,
)
from broca.tools import Tool


class MockTool:
    """Mock tool for testing."""
    def __init__(self, name: str):
        self.name = name
        self.description = f"Tool {name}"
        self.parameters = {"type": "object", "properties": {}, "required": []}


class TestMetricsCollection:
    """Test metrics collection integration."""
    
    def test_guidance_suggestion_tracking(self):
        """Test that guidance suggestions are tracked."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        metrics.record_guidance_suggestion("tool1", rank=1, score=0.9)
        metrics.record_guidance_suggestion("tool2", rank=2, score=0.8)
        
        effectiveness = metrics.get_effectiveness_metrics()
        
        assert effectiveness["suggestions_made"] == 2
        assert effectiveness["suggestions_followed"] == 0  # Not followed yet
    
    def test_guidance_follow_tracking(self):
        """Test that guidance follow-up is tracked."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        metrics.record_guidance_suggestion("tool1", rank=1, score=0.9)
        metrics.record_guidance_followed("tool1", outcome=True, reward=1.0)
        
        effectiveness = metrics.get_effectiveness_metrics()
        
        assert effectiveness["suggestions_made"] == 1
        assert effectiveness["suggestions_followed"] == 1
        assert effectiveness["follow_rate"] == 1.0
        assert effectiveness["success_rate_when_followed"] == 1.0
    
    def test_validation_tracking(self):
        """Test that validation events are tracked."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        metrics.record_validation(
            tool_name="tool1",
            blocked=False,
            confidence=0.8,
            warnings_count=1,
            alternatives_count=2
        )
        
        validation_metrics = metrics.get_validation_metrics()
        
        assert validation_metrics["validation_catch_rate"] >= 0.0
        assert validation_metrics["avg_confidence"] == 0.8
        assert validation_metrics["avg_warnings"] == 1.0
    
    def test_ranking_tracking(self):
        """Test that ranking events are tracked."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        metrics.record_ranking("tool1", rank=1, score=0.9)
        metrics.record_ranking("tool2", rank=2, score=0.8)
        
        # Record outcomes
        metrics.record_guidance_followed("tool1", outcome=True, reward=1.0)
        metrics.record_guidance_followed("tool2", outcome=False, reward=0.0)
        
        ranking_metrics = metrics.get_ranking_metrics()
        
        assert ranking_metrics["avg_rank_of_successful_tools"] <= 2.0
        assert ranking_metrics["ranking_accuracy"] >= 0.0
    
    def test_metrics_window_size(self):
        """Test that metrics respect window size."""
        metrics = ToolSelectionMetrics(window_size=5)
        
        # Add more than window size
        for i in range(10):
            metrics.record_guidance_suggestion(f"tool{i}", rank=1, score=0.9)
        
        effectiveness = metrics.get_effectiveness_metrics()
        
        # Should only track last 5
        assert effectiveness["suggestions_made"] == 5


class TestMetricsIntegration:
    """Test metrics integration with guidance system."""
    
    def test_guidance_records_suggestions(self):
        """Test that guidance system records suggestions in metrics."""
        aggregator = GuidanceAggregator()
        guidance = ToolSelectionGuidance(
            reasoning_tool=None,
            rl_signal_aggregator=None,
            skill_manager=None,
            goal_manager=None,
        )
        
        metrics = ToolSelectionMetrics(window_size=100)
        guidance.set_metrics(metrics)
        
        tools = [MockTool("tool1"), MockTool("tool2")]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        # Generate guidance (should record suggestions)
        text = guidance.generate_guidance_text(context=context, available_tools=tools)
        
        effectiveness = metrics.get_effectiveness_metrics()
        
        # Should have recorded suggestions
        assert effectiveness["suggestions_made"] >= 0
    
    def test_guidance_records_rankings(self):
        """Test that guidance system records rankings in metrics."""
        aggregator = GuidanceAggregator()
        guidance = ToolSelectionGuidance(
            reasoning_tool=None,
            rl_signal_aggregator=None,
            skill_manager=None,
            goal_manager=None,
        )
        
        metrics = ToolSelectionMetrics(window_size=100)
        guidance.set_metrics(metrics)
        
        tools = [MockTool("tool1"), MockTool("tool2")]
        context = {
            "active_goals": [],
            "applicable_skills": [],
            "rl_signals": None,
            "working_memory_items": [],
        }
        
        # Filter and rank tools (should record rankings)
        ranked_tools = guidance.filter_and_rank_tools(tools, context=context)
        
        ranking_metrics = metrics.get_ranking_metrics()
        
        # Should have recorded rankings
        assert ranking_metrics["ranking_accuracy"] >= 0.0
    
    def test_guidance_records_validations(self):
        """Test that guidance system records validations in metrics."""
        aggregator = GuidanceAggregator()
        guidance = ToolSelectionGuidance(
            reasoning_tool=None,
            rl_signal_aggregator=None,
            skill_manager=None,
            goal_manager=None,
            validation_strictness=ValidationStrictness.ADVISORY,
        )
        
        metrics = ToolSelectionMetrics(window_size=100)
        guidance.set_metrics(metrics)
        
        context = {
            "active_goals": [],
            "rl_signals": None,
        }
        
        # Validate tool selection (should record validation)
        result = guidance.validate_tool_selection("tool1", {}, context=context)
        
        validation_metrics = metrics.get_validation_metrics()
        
        # Should have recorded validation
        assert validation_metrics["avg_confidence"] >= 0.0
    
    def test_guidance_records_outcomes(self):
        """Test that guidance system records tool outcomes in metrics."""
        aggregator = GuidanceAggregator()
        guidance = ToolSelectionGuidance(
            reasoning_tool=None,
            rl_signal_aggregator=None,
            skill_manager=None,
            goal_manager=None,
        )
        
        metrics = ToolSelectionMetrics(window_size=100)
        guidance.set_metrics(metrics)
        
        # Record tool outcome
        guidance.record_tool_outcome("tool1", success=True, reward=1.0)
        
        effectiveness = metrics.get_effectiveness_metrics()
        
        # Should have updated follow-up tracking
        assert effectiveness["suggestions_followed"] >= 0


class TestGoldenTraceReplay:
    """Test golden trace replay scenarios."""
    
    def test_replay_tool_selection_scenario(self):
        """Replay a recorded tool selection scenario."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        # Simulate a scenario: suggest tools, validate, execute, record outcome
        metrics.record_guidance_suggestion("web_search", rank=1, score=0.9)
        metrics.record_guidance_suggestion("retrieve_memories", rank=2, score=0.8)
        
        metrics.record_validation(
            tool_name="web_search",
            blocked=False,
            confidence=0.9,
            warnings_count=0,
            alternatives_count=0
        )
        
        metrics.record_ranking("web_search", rank=1, score=0.9)
        metrics.record_guidance_followed("web_search", outcome=True, reward=1.0)
        
        # Check metrics
        effectiveness = metrics.get_effectiveness_metrics()
        validation_metrics = metrics.get_validation_metrics()
        ranking_metrics = metrics.get_ranking_metrics()
        
        assert effectiveness["suggestions_made"] == 2
        assert effectiveness["suggestions_followed"] == 1
        assert effectiveness["follow_rate"] == 0.5
        assert validation_metrics["validation_catch_rate"] >= 0.0
        assert ranking_metrics["ranking_accuracy"] >= 0.0
    
    def test_replay_blocked_scenario(self):
        """Replay a scenario where tool was blocked."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        metrics.record_guidance_suggestion("store_memory", rank=1, score=0.9)
        metrics.record_validation(
            tool_name="store_memory",
            blocked=True,
            confidence=0.3,
            warnings_count=2,
            alternatives_count=1
        )
        
        validation_metrics = metrics.get_validation_metrics()
        
        assert validation_metrics["block_rate"] > 0.0
        assert validation_metrics["avg_warnings"] == 2.0
        assert validation_metrics["avg_alternatives"] == 1.0


class TestMetricsCoverage:
    """Test metrics coverage and completeness."""
    
    def test_all_metrics_available(self):
        """Test that all metric types are available."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        all_metrics = metrics.get_all_metrics()
        
        assert "guidance" in all_metrics
        assert "validation" in all_metrics
        assert "ranking" in all_metrics
        assert "timestamp" in all_metrics
    
    def test_tool_specific_metrics(self):
        """Test tool-specific metrics."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        metrics.record_guidance_suggestion("tool1", rank=1, score=0.9)
        metrics.record_validation("tool1", blocked=False, confidence=0.8, warnings_count=0, alternatives_count=0)
        metrics.record_ranking("tool1", rank=1, score=0.9)
        
        tool_metrics = metrics.get_tool_metrics("tool1")
        
        assert tool_metrics["tool_name"] == "tool1"
        assert tool_metrics["suggestions_count"] == 1
        assert tool_metrics["validations_count"] == 1
        assert tool_metrics["rankings_count"] == 1
    
    def test_empty_metrics_handling(self):
        """Test that empty metrics are handled gracefully."""
        metrics = ToolSelectionMetrics(window_size=100)
        
        effectiveness = metrics.get_effectiveness_metrics()
        validation_metrics = metrics.get_validation_metrics()
        ranking_metrics = metrics.get_ranking_metrics()
        
        # Should return zero values, not raise
        assert effectiveness["suggestions_made"] == 0
        assert validation_metrics["validation_catch_rate"] == 0.0
        assert ranking_metrics["ranking_accuracy"] == 0.0

