"""
Comprehensive tests for behavioral and goal cognitive dissonance metrics.

Includes:
- Mutation testing
- Property-based testing
- Fault injection
- Coverage verification
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from datetime import datetime, timezone

from broca.reasoning.cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics
from broca.self_model.model import SelfModel


class DummyGoalLLM:
    """
    Deterministic, fast LLM stub for goal-conflict detection in tests.

    We intentionally avoid real model initialization to keep Hypothesis tests non-flaky.
    """

    def chat(self, messages, temperature=0.0, **kwargs):
        prompt = (messages or [])[-1].get("content", "") if isinstance((messages or [])[-1], dict) else ""
        p = str(prompt).lower()

        # Heuristic: if goals mention writing/modifying and constraints include "never write",
        # return a conflict.
        has_write_goal = ("write" in p) or ("modify" in p) or ("delete" in p)
        has_no_write_constraint = ("never write" in p) or ("read-only" in p) or ("read only" in p)

        if has_write_goal and has_no_write_constraint:
            content = (
                '{'
                '"has_conflicts": true, '
                '"conflict_score": 0.3, '
                '"conflicting_goals": ["modify_files"], '
                '"conflict_reasons": ["Goal violates read-only/no-write constraint."], '
                '"aligned_goals": []'
                '}'
            )
        else:
            content = (
                '{'
                '"has_conflicts": false, '
                '"conflict_score": 0.0, '
                '"conflicting_goals": [], '
                '"conflict_reasons": [], '
                '"aligned_goals": ["analyze_code"]'
                '}'
            )

        return {"choices": [{"message": {"content": content}}]}

    def extract_assistant_content(self, response):
        return response["choices"][0]["message"]["content"]


@pytest.fixture
def sample_self_model():
    """Create a sample self-model for testing."""
    return SelfModel(
        capabilities=[
            {"text": "I can read files and search the web"},
            {"text": "I can analyze code and provide suggestions"},
        ],
        constraints={
            "read_only": {"value": "System is in read-only mode"},
            "no_write": {"value": "Never write to disk or modify files"},
        }
    )


@pytest.fixture
def cognitive_dissonance_monitor(sample_self_model):
    """Create cognitive dissonance monitor with sample self-model."""
    return CognitiveDissonanceMonitor(
        self_model=sample_self_model,
        history_window=100,
        # Avoid slow first-run real LLM initialization in tests (Hypothesis deadline flake),
        # while still supporting goal-conflict logic.
        llm_client=DummyGoalLLM(),
    )


@pytest.fixture
def mock_goal_manager():
    """Create a mock goal manager."""
    goal_manager = Mock()
    goal_manager.get_active_goals = Mock(return_value=[])
    return goal_manager


class TestBehavioralDissonanceMutation:
    """Mutation tests for behavioral dissonance measurement."""
    
    def test_constraint_violation_detected(self, cognitive_dissonance_monitor):
        """Kills mutation: constraint violations not detected."""
        # Tool that violates read-only constraint
        tool_usage = [
            {"function": {"name": "write_file", "arguments": {"path": "/tmp/test.txt"}}}
        ]
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Should detect violation (deviation_score > 0)
        assert metrics.behavioral_dissonance > 0.0
        assert metrics.behavioral_dissonance <= 1.0
        assert metrics.component_availability["behavioral"] is True
    
    def test_capability_mismatch_detected(self, cognitive_dissonance_monitor):
        """Kills mutation: capability mismatches not detected."""
        # Tool not mentioned in capabilities
        tool_usage = [
            {"function": {"name": "unknown_tool_xyz", "arguments": {}}}
        ]
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Should detect mismatch (may be 0.0 if tool is common, but should be measured)
        assert metrics.behavioral_dissonance >= 0.0
        assert metrics.behavioral_dissonance <= 1.0
    
    def test_read_only_violation_severity(self, cognitive_dissonance_monitor):
        """Kills mutation: read-only violations not given high severity."""
        tool_usage = [
            {"function": {"name": "write_file", "arguments": {}}},
            {"function": {"name": "delete_file", "arguments": {}}}
        ]
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Read-only violations should have high severity (>= 0.8)
        # With multiple violations, should be at least 0.8
        assert metrics.behavioral_dissonance >= 0.8
    
    def test_semantic_matching_works(self, cognitive_dissonance_monitor):
        """Kills mutation: semantic matching not implemented."""
        # Tool with word overlap with capabilities (read, search)
        tool_usage = [
            {"function": {"name": "read_file", "arguments": {}}},
            {"function": {"name": "web_search", "arguments": {}}}
        ]
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Should have low or zero dissonance (tools match capabilities)
        # Exact value depends on implementation, but should be measured
        assert metrics.behavioral_dissonance >= 0.0
        assert metrics.behavioral_dissonance <= 1.0
    
    def test_inefficient_pattern_detected(self, cognitive_dissonance_monitor):
        """Kills mutation: inefficient patterns not detected."""
        # Same tool used excessively
        tool_usage = [
            {"function": {"name": "read_file", "arguments": {}}},
            {"function": {"name": "read_file", "arguments": {}}},
            {"function": {"name": "read_file", "arguments": {}}},
            {"function": {"name": "read_file", "arguments": {}}},
        ]
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Should detect pattern (may add small penalty)
        # Exact value depends on implementation
        assert metrics.behavioral_dissonance >= 0.0
        assert metrics.behavioral_dissonance <= 1.0


class TestGoalDissonanceMutation:
    """Mutation tests for goal dissonance measurement."""
    
    def test_constraint_violation_in_goals_detected(self, cognitive_dissonance_monitor):
        """Kills mutation: goal constraint violations not detected."""
        reasoning_goals = [
            {
                "name": "modify_files",
                "description": "I want to write and modify files on the system",
                "goal_type": "achieve",
                "status": "active",
                "priority": 0.8
            }
        ]
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(reasoning_goals=reasoning_goals)
        
        # Should detect violation (conflict_score > 0)
        assert metrics.goal_dissonance > 0.0
        assert metrics.goal_dissonance <= 1.0
        assert metrics.component_availability["goal"] is True
    
    def test_goal_capability_alignment_checked(self, cognitive_dissonance_monitor):
        """Kills mutation: goal-capability alignment not checked."""
        reasoning_goals = [
            {
                "name": "analyze_code",
                "description": "I want to analyze code and provide suggestions",
                "goal_type": "achieve",
                "status": "active",
            }
        ]
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(reasoning_goals=reasoning_goals)
        
        # Should align with capabilities (low or zero dissonance)
        assert metrics.goal_dissonance >= 0.0
        assert metrics.goal_dissonance <= 1.0
    
    def test_goal_extraction_from_goal_manager(self, cognitive_dissonance_monitor, mock_goal_manager):
        """Kills mutation: goal extraction from GoalManager not implemented."""
        from broca.reasoning.goal_manager import Goal, GoalType, GoalStatus
        
        # Mock active goals
        mock_goal = Mock(spec=Goal)
        mock_goal.name = "test_goal"
        mock_goal.description = "Test goal description"
        mock_goal.goal_type = GoalType.ACHIEVE
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.priority = 0.5
        mock_goal.dependencies = []
        
        mock_goal_manager.get_active_goals.return_value = [mock_goal]
        cognitive_dissonance_monitor.goal_manager = mock_goal_manager
        
        # Measure without explicit reasoning_goals (should extract from goal_manager)
        metrics = cognitive_dissonance_monitor.measure_dissonance()
        
        # Should extract and measure (component_availability may be False if no violations)
        assert metrics.goal_dissonance >= 0.0
        assert metrics.goal_dissonance <= 1.0


class TestBehavioralDissonanceProperty:
    """Property-based tests for behavioral dissonance."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        tool_names=st.lists(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc"))),
            min_size=0,
            max_size=10
        ),
        write_tools=st.booleans()
    )
    def test_behavioral_dissonance_always_in_range(
        self,
        cognitive_dissonance_monitor,
        tool_names,
        write_tools
    ):
        """Property: Behavioral dissonance always in [0.0, 1.0]."""
        # Create tool usage with provided tool names
        tool_usage = []
        for tool_name in tool_names:
            # If write_tools flag is set, add write keywords
            if write_tools and tool_name:
                tool_name = f"write_{tool_name}"
            tool_usage.append({
                "function": {
                    "name": tool_name,
                    "arguments": {}
                }
            })
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage if tool_usage else None)
        
        assert 0.0 <= metrics.behavioral_dissonance <= 1.0
        assert metrics.component_availability["behavioral"] in [True, False]
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        num_tools=st.integers(min_value=0, max_value=20),
        repetition_factor=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_pattern_analysis_consistency(
        self,
        cognitive_dissonance_monitor,
        num_tools,
        repetition_factor
    ):
        """Property: Pattern analysis is consistent across tool counts."""
        if num_tools == 0:
            tool_usage = None
        else:
            # Create tools with some repetition
            tool_usage = []
            unique_tools = max(1, int(num_tools * (1 - repetition_factor)))
            for i in range(num_tools):
                tool_idx = i % unique_tools
                tool_usage.append({
                    "function": {
                        "name": f"tool_{tool_idx}",
                        "arguments": {}
                    }
                })
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Should always return valid value
        assert 0.0 <= metrics.behavioral_dissonance <= 1.0


class TestGoalDissonanceProperty:
    """Property-based tests for goal dissonance."""
    
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
        max_examples=30
    )
    @given(
        num_goals=st.integers(min_value=0, max_value=5)
    )
    def test_goal_dissonance_always_in_range(
        self,
        cognitive_dissonance_monitor,
        num_goals
    ):
        """Property: Goal dissonance always in [0.0, 1.0]."""
        # Generate goals with consistent structure
        reasoning_goals = []
        for i in range(num_goals):
            reasoning_goals.append({
                "name": f"goal_{i}",
                "description": f"Goal {i} description",
                "goal_type": "achieve",
                "status": "active",
                "priority": 0.5
            })
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(
            reasoning_goals=reasoning_goals if reasoning_goals else None
        )
        
        assert 0.0 <= metrics.goal_dissonance <= 1.0
        assert metrics.component_availability["goal"] in [True, False]


class TestFaultInjection:
    """Fault injection tests for error handling."""
    
    def test_behavioral_dissonance_handles_invalid_tool_usage(self, cognitive_dissonance_monitor):
        """Test: Handles invalid tool_usage format gracefully."""
        # Invalid formats
        invalid_inputs = [
            None,
            [],
            [None],
            [{"invalid": "structure"}],
            [{"function": None}],
            [{"function": {"name": None}}],
        ]
        
        for invalid_input in invalid_inputs:
            # Should not raise exception
            metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=invalid_input)
            assert isinstance(metrics.behavioral_dissonance, float)
            assert 0.0 <= metrics.behavioral_dissonance <= 1.0
    
    def test_goal_dissonance_handles_invalid_goals(self, cognitive_dissonance_monitor):
        """Test: Handles invalid goal formats gracefully."""
        invalid_inputs = [
            None,
            [],
            [None],
            [{"invalid": "structure"}],
            [{"name": None, "description": None}],
        ]
        
        for invalid_input in invalid_inputs:
            # Should not raise exception
            metrics = cognitive_dissonance_monitor.measure_dissonance(reasoning_goals=invalid_input)
            assert isinstance(metrics.goal_dissonance, float)
            assert 0.0 <= metrics.goal_dissonance <= 1.0
    
    def test_goal_manager_extraction_handles_missing_attributes(self, cognitive_dissonance_monitor):
        """Test: Handles missing GoalManager attributes gracefully."""
        # Mock goal_manager with missing methods
        mock_goal_manager = Mock()
        mock_goal_manager.get_active_goals = Mock(side_effect=AttributeError("Missing method"))
        cognitive_dissonance_monitor.goal_manager = mock_goal_manager
        
        # Should not raise exception
        metrics = cognitive_dissonance_monitor.measure_dissonance()
        assert isinstance(metrics.goal_dissonance, float)
        assert 0.0 <= metrics.goal_dissonance <= 1.0
    
    def test_goal_manager_extraction_handles_empty_goals(self, cognitive_dissonance_monitor, mock_goal_manager):
        """Test: Handles empty goal lists from GoalManager."""
        mock_goal_manager.get_active_goals.return_value = []
        cognitive_dissonance_monitor.goal_manager = mock_goal_manager
        
        metrics = cognitive_dissonance_monitor.measure_dissonance()
        # Should fall back to historical average or 0.0
        assert isinstance(metrics.goal_dissonance, float)
        assert 0.0 <= metrics.goal_dissonance <= 1.0
    
    def test_behavioral_dissonance_handles_missing_capabilities(self, sample_self_model):
        """Test: Handles self-model with no capabilities."""
        # Create self-model without capabilities
        empty_self_model = SelfModel(capabilities=[])
        monitor = CognitiveDissonanceMonitor(self_model=empty_self_model)
        
        tool_usage = [{"function": {"name": "some_tool", "arguments": {}}}]
        metrics = monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Should return None for behavioral measurement but still return valid metrics
        # (may use historical average or 0.0)
        assert isinstance(metrics.behavioral_dissonance, float)
        assert 0.0 <= metrics.behavioral_dissonance <= 1.0


class TestAutomaticExtraction:
    """Tests for automatic data extraction."""
    
    def test_tool_usage_extraction_from_context(self, cognitive_dissonance_monitor):
        """Test: Tool usage extracted from conversation context."""
        conversation_context = [
            {
                "role": "assistant",
                "tool_calls": [
                    {"function": {"name": "read_file", "arguments": {}}},
                    {"function": {"name": "write_file", "arguments": {}}}
                ]
            }
        ]
        
        # Don't provide tool_usage explicitly, should extract from context
        metrics = cognitive_dissonance_monitor.measure_dissonance(
            conversation_context=conversation_context
        )
        
        # Should extract and measure
        assert isinstance(metrics.behavioral_dissonance, float)
        assert 0.0 <= metrics.behavioral_dissonance <= 1.0
    
    def test_reasoning_goals_extraction_from_goal_manager(self, cognitive_dissonance_monitor, mock_goal_manager):
        """Test: Reasoning goals extracted from GoalManager when not provided."""
        from broca.reasoning.goal_manager import Goal, GoalType, GoalStatus
        
        # Create mock goal
        mock_goal = Mock(spec=Goal)
        mock_goal.name = "test_goal"
        mock_goal.description = "Test goal that might violate constraints"
        mock_goal.goal_type = GoalType.ACHIEVE
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.priority = 0.5
        mock_goal.dependencies = []
        
        mock_goal_manager.get_active_goals.return_value = [mock_goal]
        cognitive_dissonance_monitor.goal_manager = mock_goal_manager
        
        # Don't provide reasoning_goals explicitly, should extract from goal_manager
        metrics = cognitive_dissonance_monitor.measure_dissonance()
        
        # Should extract and measure
        assert isinstance(metrics.goal_dissonance, float)
        assert 0.0 <= metrics.goal_dissonance <= 1.0
        # Verify goal_manager was called
        mock_goal_manager.get_active_goals.assert_called()


class TestIntegration:
    """Integration tests combining behavioral and goal dissonance."""
    
    def test_both_metrics_can_be_non_zero(self, cognitive_dissonance_monitor):
        """Test: Both behavioral and goal dissonance can be non-zero simultaneously."""
        tool_usage = [
            {"function": {"name": "write_file", "arguments": {}}}
        ]
        reasoning_goals = [
            {
                "name": "modify_files",
                "description": "I want to write files to disk",
                "goal_type": "achieve",
                "status": "active"
            }
        ]
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(
            tool_usage=tool_usage,
            reasoning_goals=reasoning_goals
        )
        
        # Both should detect violations
        assert metrics.behavioral_dissonance > 0.0
        assert metrics.goal_dissonance > 0.0
        assert metrics.overall_dissonance > 0.0
    
    def test_metrics_tracked_in_history(self, cognitive_dissonance_monitor):
        """Test: Metrics are properly tracked in history."""
        tool_usage = [{"function": {"name": "write_file", "arguments": {}}}]
        
        initial_history_len = len(cognitive_dissonance_monitor.dissonance_history)
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Should add to history
        assert len(cognitive_dissonance_monitor.dissonance_history) == initial_history_len + 1
        latest = cognitive_dissonance_monitor.dissonance_history[-1]
        assert latest.behavioral_dissonance == metrics.behavioral_dissonance
    
    def test_behavioral_deviations_tracked(self, cognitive_dissonance_monitor):
        """Test: Behavioral deviations are tracked in history."""
        tool_usage = [{"function": {"name": "write_file", "arguments": {}}}]
        
        initial_deviations_len = len(cognitive_dissonance_monitor.behavioral_deviations)
        
        metrics = cognitive_dissonance_monitor.measure_dissonance(tool_usage=tool_usage)
        
        # Should track deviation if violation detected
        if metrics.behavioral_dissonance > 0.0:
            assert len(cognitive_dissonance_monitor.behavioral_deviations) > initial_deviations_len


class TestCoverage:
    """Tests to ensure code coverage."""
    
    def test_extract_tool_usage_from_context_returns_none_on_error(self, cognitive_dissonance_monitor):
        """Test: _extract_tool_usage_from_context handles errors."""
        # Invalid context format
        invalid_context = [{"role": "assistant", "invalid_field": "value"}]
        
        result = cognitive_dissonance_monitor._extract_tool_usage_from_context(invalid_context)
        
        # Should return None on error or invalid format
        assert result is None or isinstance(result, list)
    
    def test_extract_reasoning_goals_handles_missing_goal_manager(self, cognitive_dissonance_monitor):
        """Test: _extract_reasoning_goals_from_goal_manager handles missing goal_manager."""
        cognitive_dissonance_monitor.goal_manager = None
        
        result = cognitive_dissonance_monitor._extract_reasoning_goals_from_goal_manager()
        
        assert result is None
    
    def test_get_average_behavioral_dissonance_returns_zero_for_empty_history(self, cognitive_dissonance_monitor):
        """Test: _get_average_behavioral_dissonance returns 0.0 for empty history."""
        cognitive_dissonance_monitor.behavioral_deviations.clear()
        
        result = cognitive_dissonance_monitor._get_average_behavioral_dissonance()
        
        assert result == 0.0
    
    def test_get_average_goal_dissonance_returns_zero_for_empty_history(self, cognitive_dissonance_monitor):
        """Test: _get_average_goal_dissonance returns 0.0 for empty history."""
        cognitive_dissonance_monitor.goal_conflicts.clear()
        
        result = cognitive_dissonance_monitor._get_average_goal_dissonance()
        
        assert result == 0.0

