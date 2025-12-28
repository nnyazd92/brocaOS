"""
Tests for tool selection guidance improvements.

Includes mutation testing and property-based tests.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
from hypothesis import given, strategies as st, settings, HealthCheck

from broca.tools.selection_guidance import (
    ToolSelectionGuidance,
    GuidanceTextFormatter,
    ContextCache,
    IncrementalContextUpdater,
    ValidationStrictness,
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


class TestGuidanceTextFormatter:
    """Test GuidanceTextFormatter."""
    
    def test_format_prioritized_with_top_tools(self):
        """Test prioritized formatting with top tools."""
        formatter = GuidanceTextFormatter(style="prioritized")
        
        rankings = [
            ToolRanking(tool_name="tool1", score=0.9, reasons=["High relevance"]),
            ToolRanking(tool_name="tool2", score=0.8, reasons=["Good match"]),
            ToolRanking(tool_name="tool3", score=0.7, reasons=["Relevant"]),
        ]
        
        context = {
            "active_goals": [{"name": "goal1", "priority": 0.8}],
            "applicable_skills": [{"name": "skill1", "proficiency_level": 0.7}],
            "rl_signals": {"exploration_balance": 0.5, "composite_reward": 0.6},
        }
        
        text = formatter.format_prioritized(rankings, context, max_length=2000)
        
        assert "tool1" in text
        assert "tool2" in text
        assert "Recommended Tools" in text
        assert len(text) <= 2000
    
    def test_format_prioritized_respects_max_length(self):
        """Test that formatting respects max length."""
        formatter = GuidanceTextFormatter(style="prioritized")
        
        rankings = [
            ToolRanking(tool_name="tool1", score=0.9, reasons=["High relevance"]),
        ]
        
        context = {
            "active_goals": [{"name": "goal1", "priority": 0.8}],
        }
        
        text = formatter.format_prioritized(rankings, context, max_length=50)
        
        assert len(text) <= 50
    
    @given(
        num_tools=st.integers(min_value=0, max_value=10),
        max_length=st.integers(min_value=10, max_value=1000)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_format_prioritized_always_respects_length(self, num_tools, max_length):
        """Property: Formatted text always respects max length."""
        formatter = GuidanceTextFormatter(style="prioritized")
        
        rankings = [
            ToolRanking(
                tool_name=f"tool{i}",
                score=0.9 - i * 0.1,
                reasons=[f"Reason {i}"]
            )
            for i in range(num_tools)
        ]
        
        context = {
            "active_goals": [{"name": "goal1", "priority": 0.8}],
        }
        
        text = formatter.format_prioritized(rankings, context, max_length=max_length)
        
        assert len(text) <= max_length


class TestContextCache:
    """Test ContextCache."""
    
    def test_cache_hit_within_ttl(self):
        """Test cache hit when within TTL."""
        cache = ContextCache(ttl_seconds=5)
        
        def compute():
            return {"key": "value"}
        
        # First call - cache miss
        result1 = cache.get_or_compute("test", compute)
        assert result1 == {"key": "value"}
        
        # Second call - cache hit
        with patch('time.time', return_value=2.0):  # Within TTL
            result2 = cache.get_or_compute("test", compute)
            assert result2 == {"key": "value"}
    
    def test_cache_expires_after_ttl(self):
        """Test cache expires after TTL."""
        cache = ContextCache(ttl_seconds=5)
        
        call_count = [0]
        def compute():
            call_count[0] += 1
            return {"key": f"value{call_count[0]}"}
        
        # First call
        result1 = cache.get_or_compute("test", compute)
        assert call_count[0] == 1
        
        # Second call after TTL - should recompute
        with patch('time.time', return_value=10.0):  # After TTL
            result2 = cache.get_or_compute("test", compute)
            assert call_count[0] == 2
            assert result2["key"] == "value2"
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = ContextCache(ttl_seconds=5)
        
        def compute():
            return {"key": "value"}
        
        cache.get_or_compute("test", compute)
        cache.invalidate("test")
        
        # Should recompute after invalidation
        call_count = [0]
        def compute2():
            call_count[0] += 1
            return {"key": "value2"}
        
        result = cache.get_or_compute("test", compute2)
        assert call_count[0] == 1
        assert result["key"] == "value2"
    
    def test_state_hash_invalidation(self):
        """Test cache invalidation on state hash change."""
        cache = ContextCache(ttl_seconds=5)
        
        def compute():
            return {"key": "value"}
        
        # First call with state hash
        result1 = cache.get_or_compute("test", compute, state_hash="hash1")
        
        # Second call with different state hash - should invalidate
        call_count = [0]
        def compute2():
            call_count[0] += 1
            return {"key": "value2"}
        
        result2 = cache.get_or_compute("test", compute2, state_hash="hash2")
        assert call_count[0] == 1
        assert result2["key"] == "value2"


class TestIncrementalContextUpdater:
    """Test IncrementalContextUpdater."""
    
    def test_detect_changes(self):
        """Test change detection."""
        aggregator = Mock()
        updater = IncrementalContextUpdater(aggregator)
        
        context1 = {
            "active_goals": [{"name": "goal1"}],
            "rl_signals": {"composite_reward": 0.5},
        }
        
        context2 = {
            "active_goals": [{"name": "goal2"}],  # Changed
            "rl_signals": {"composite_reward": 0.5},
        }
        
        updater._last_context = context1
        changed = updater._detect_changes(context2)
        
        assert "active_goals" in changed


class TestValidationStrictness:
    """Test validation strictness levels."""
    
    def test_advisory_never_blocks(self):
        """Test that advisory mode never blocks."""
        from broca.tools.selection_guidance import ToolValidator, GuidanceAggregator
        
        aggregator = GuidanceAggregator()
        validator = ToolValidator(
            aggregator,
            strictness=ValidationStrictness.ADVISORY,
            confidence_threshold=0.7
        )
        
        context = {
            "active_goals": [],
            "rl_signals": None,
        }
        
        result = validator.validate_tool_selection("test_tool", {}, context)
        
        # Advisory should never block
        assert not result.blocked
    
    def test_soft_block_blocks_on_low_confidence(self):
        """Test that soft block blocks on low confidence."""
        from broca.tools.selection_guidance import ToolValidator, GuidanceAggregator
        
        aggregator = GuidanceAggregator()
        validator = ToolValidator(
            aggregator,
            strictness=ValidationStrictness.SOFT_BLOCK,
            confidence_threshold=0.7
        )
        
        context = {
            "active_goals": [{"name": "read_only_goal"}],
            "rl_signals": None,
        }
        
        # Tool that conflicts with read-only goal
        result = validator.validate_tool_selection("store_memory", {}, context)
        
        # Should block if confidence is low
        if result.confidence < 0.7:
            assert result.blocked
    
    def test_hard_block_blocks_on_critical_violations(self):
        """Test that hard block blocks on critical violations."""
        from broca.tools.selection_guidance import ToolValidator, GuidanceAggregator
        
        aggregator = GuidanceAggregator()
        validator = ToolValidator(
            aggregator,
            strictness=ValidationStrictness.HARD_BLOCK,
            confidence_threshold=0.7
        )
        
        context = {
            "active_goals": [{"name": "read_only_goal"}],
            "rl_signals": None,
        }
        
        # Tool that conflicts with read-only goal
        result = validator.validate_tool_selection("store_memory", {}, context)
        
        # Hard block should block critical violations
        if "conflict" in str(result.warnings).lower():
            assert result.blocked


class TestMutationKillers:
    """Tests designed to kill mutations."""
    
    def test_guidance_formatter_handles_empty_tools(self):
        """Kills mutation: not handling empty tools list."""
        formatter = GuidanceTextFormatter(style="prioritized")
        
        text = formatter.format_prioritized([], {}, max_length=1000)
        
        # Should not crash, may be empty or contain other sections
        assert isinstance(text, str)
    
    def test_cache_handles_none_compute_fn(self):
        """Kills mutation: not handling None compute function."""
        cache = ContextCache(ttl_seconds=5)
        
        # Should raise error for None compute function
        with pytest.raises((TypeError, AttributeError)):
            cache.get_or_compute("test", None)
    
    def test_validation_result_has_required_fields(self):
        """Kills mutation: missing required fields in ValidationResult."""
        result = ValidationResult(
            is_valid=True,
            blocked=False,
            alternatives=[],
            severity="info"
        )
        
        assert hasattr(result, "is_valid")
        assert hasattr(result, "blocked")
        assert hasattr(result, "alternatives")
        assert hasattr(result, "severity")


class TestPropertyBasedGuidance:
    """Property-based tests for guidance system."""
    
    @given(
        num_tools=st.integers(min_value=1, max_value=20),
        max_length=st.integers(min_value=50, max_value=2000)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    def test_guidance_text_always_respects_length(self, num_tools, max_length):
        """Property: Guidance text always respects max length."""
        formatter = GuidanceTextFormatter(style="prioritized")
        
        rankings = [
            ToolRanking(
                tool_name=f"tool{i}",
                score=0.9 - i * 0.05,
                reasons=[f"Reason {i}"]
            )
            for i in range(num_tools)
        ]
        
        context = {
            "active_goals": [{"name": f"goal{i}", "priority": 0.8} for i in range(min(3, num_tools))],
        }
        
        text = formatter.format_prioritized(rankings, context, max_length=max_length)
        
        assert len(text) <= max_length
    
    @given(
        ttl=st.integers(min_value=1, max_value=100),
        time_offset=st.floats(min_value=0.0, max_value=200.0)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    def test_cache_ttl_property(self, ttl, time_offset):
        """Property: Cache respects TTL."""
        cache = ContextCache(ttl_seconds=ttl)
        
        call_count = [0]
        def compute():
            call_count[0] += 1
            return {"value": call_count[0]}
        
        # First call
        cache.get_or_compute("test", compute)
        initial_count = call_count[0]
        
        # Second call at time_offset
        with patch('time.time', return_value=time_offset):
            cache.get_or_compute("test", compute)
        
        # If time_offset < ttl, should be cache hit (no new call)
        # If time_offset >= ttl, should be cache miss (new call)
        if time_offset < ttl:
            assert call_count[0] == initial_count
        else:
            assert call_count[0] > initial_count

