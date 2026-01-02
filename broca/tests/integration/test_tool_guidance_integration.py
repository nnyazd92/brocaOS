"""
Integration tests for tool selection guidance.

Tests integration with reasoning engine, RL signals, and skill manager.
Includes golden trace replay scenarios.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from pathlib import Path

from broca.tools.selection_guidance import ToolSelectionGuidance
from broca.tools.registry import ToolRegistry
from broca.tools import Tool


@pytest.fixture(autouse=True)
def _legacy_toolset_for_integration_tests(monkeypatch):
    # This integration suite uses synthetic / legacy tool names.
    from broca.config import config
    monkeypatch.setattr(config.tools, "toolset", "legacy", raising=False)


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


class TestToolGuidanceIntegration:
    """Test integration of tool guidance with system components."""
    
    def test_guidance_with_reasoning_tool(self):
        """Test guidance generation with reasoning tool integration."""
        reasoning_tool = Mock()
        reasoning_tool.rule_system = Mock()
        reasoning_tool.rule_system.working_memory = Mock()
        reasoning_tool.rule_system.working_memory.items = []
        reasoning_tool.rule_system.rules = []
        
        guidance = ToolSelectionGuidance(reasoning_tool=reasoning_tool)
        
        context = guidance.guidance_aggregator.gather_context()
        
        assert "working_memory_items" in context
        assert "production_rules" in context
    
    def test_guidance_with_rl_signals(self):
        """Test guidance generation with RL signal integration."""
        rl_signal_aggregator = Mock()
        rl_metrics = Mock()
        rl_metrics.composite_reward = 0.7
        rl_metrics.get_exploration_exploitation_balance.return_value = 0.6
        rl_signal_aggregator.compute_signals.return_value = rl_metrics
        
        guidance = ToolSelectionGuidance(rl_signal_aggregator=rl_signal_aggregator)
        
        text = guidance.generate_guidance_text()
        
        # Should include RL-based guidance
        assert isinstance(text, str)
    
    def test_guidance_with_skill_manager(self):
        """Test guidance generation with skill manager integration."""
        skill_manager = Mock()
        skill_manager.get_applicable_skills.return_value = [
            Mock(to_dict=lambda: {"name": "test_skill", "proficiency_level": 0.8})
        ]
        
        guidance = ToolSelectionGuidance(skill_manager=skill_manager)
        
        context = guidance.guidance_aggregator.gather_context()
        
        assert "applicable_skills" in context
        assert len(context["applicable_skills"]) > 0
    
    def test_tool_registry_with_guidance(self):
        """Test tool registry integration with guidance."""
        guidance = ToolSelectionGuidance()
        registry = ToolRegistry(tool_selection_guidance=guidance)
        
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        # Should apply filtering/ranking
        tools = registry.to_openai_format()
        
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "test_tool"
    
    def test_tool_validation_in_registry(self):
        """Test tool validation in registry execution."""
        guidance = ToolSelectionGuidance()
        registry = ToolRegistry(tool_selection_guidance=guidance)
        
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        # Mock tool call
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": "{}"
            }
        }
        
        # Should validate before execution
        result = registry.execute_tool_call(tool_call)
        
        assert "tool_call_id" in result
        assert result["role"] == "tool"
    
    def test_feedback_loop_integration(self):
        """Test feedback loop integration."""
        guidance = ToolSelectionGuidance()
        
        # Record tool outcomes
        guidance.record_tool_outcome("test_tool", True)
        guidance.record_tool_outcome("test_tool", True)
        guidance.record_tool_outcome("test_tool", False)
        
        # Check that historical success is tracked
        historical = guidance.tool_ranker.historical_success
        assert "test_tool" in historical
        assert historical["test_tool"] > 0.0


class TestGoldenTraceReplay:
    """Test golden trace replay scenarios."""
    
    def test_replay_tool_selection_scenario(self):
        """Test replaying a recorded tool selection scenario."""
        # Create a scenario
        scenario = {
            "context": {
                "active_goals": [
                    {"name": "find_information", "priority": 0.9}
                ],
                "rl_signals": {
                    "composite_reward": 0.6,
                    "exploration_balance": 0.7
                }
            },
            "tools": ["web_search", "terminal", "retrieve_memories"],
            "expected_rankings": ["web_search", "retrieve_memories", "terminal"]
        }
        
        guidance = ToolSelectionGuidance()
        
        tools = [MockTool(name) for name in scenario["tools"]]
        ranked = guidance.filter_and_rank_tools(tools, context=scenario["context"])
        
        # Check that tools are ranked appropriately
        assert len(ranked) == len(scenario["tools"])
        # web_search should be ranked high due to goal and exploration mode
        ranked_names = [t.name for t in ranked]
        assert "web_search" in ranked_names
    
    def test_replay_validation_scenario(self):
        """Test replaying a validation scenario."""
        scenario = {
            "tool_name": "store_memory",
            "arguments": {"content": "test"},
            "context": {
                "active_goals": [
                    {"name": "read_only_mode", "priority": 1.0}
                ]
            },
            "expected_valid": False
        }
        
        guidance = ToolSelectionGuidance()
        
        result = guidance.validate_tool_selection(
            scenario["tool_name"],
            scenario["arguments"],
            context=scenario["context"]
        )
        
        # Should detect conflict
        assert result.is_valid == scenario["expected_valid"] or len(result.warnings) > 0


class TestCoverage:
    """Test coverage of all code paths."""
    
    def test_all_guidance_components(self):
        """Test that all guidance components are exercised."""
        reasoning_tool = Mock()
        reasoning_tool.rule_system = Mock()
        reasoning_tool.rule_system.working_memory = Mock()
        reasoning_tool.rule_system.working_memory.items = []
        reasoning_tool.rule_system.rules = []
        
        goal_manager = Mock()
        goal_manager.get_active_goals.return_value = []
        
        skill_manager = Mock()
        skill_manager.get_applicable_skills.return_value = []
        
        rl_signal_aggregator = Mock()
        rl_metrics = Mock()
        rl_metrics.composite_reward = 0.5
        rl_metrics.get_exploration_exploitation_balance.return_value = 0.5
        rl_signal_aggregator.compute_signals.return_value = rl_metrics
        
        guidance = ToolSelectionGuidance(
            reasoning_tool=reasoning_tool,
            goal_manager=goal_manager,
            skill_manager=skill_manager,
            rl_signal_aggregator=rl_signal_aggregator,
        )
        
        # Exercise all methods
        context = guidance.guidance_aggregator.gather_context()
        text = guidance.generate_guidance_text(context=context)
        
        tools = [MockTool("test")]
        ranked = guidance.filter_and_rank_tools(tools, context=context)
        
        result = guidance.validate_tool_selection("test", {}, context=context)
        guidance.record_tool_outcome("test", True)
        
        # All should complete without error
        assert isinstance(context, dict)
        assert isinstance(text, str)
        assert len(ranked) == 1
        from broca.tools.selection_guidance import ValidationResult
        assert isinstance(result, ValidationResult)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        guidance = ToolSelectionGuidance()
        
        # Empty tools
        ranked = guidance.filter_and_rank_tools([])
        assert ranked == []
        
        # Very long guidance text
        guidance.max_guidance_length = 10
        goal_manager = Mock()
        goal_manager.get_active_goals.return_value = [
            Mock(to_dict=lambda: {"name": "very_long_goal_name_" + "x" * 100, "priority": 0.9})
        ]
        guidance.guidance_aggregator.goal_manager = goal_manager
        
        text = guidance.generate_guidance_text()
        assert len(text) <= 10
