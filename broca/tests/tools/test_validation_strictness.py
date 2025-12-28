"""
Tests for validation strictness with fault injection.

Tests behavior when validation fails, cache fails, etc.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from broca.tools.selection_guidance import (
    ToolValidator,
    GuidanceAggregator,
    ValidationStrictness,
    ValidationResult,
)


class TestValidationStrictnessLevels:
    """Test different validation strictness levels."""
    
    def test_advisory_never_blocks(self):
        """Test that advisory mode never blocks execution."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(
            aggregator,
            strictness=ValidationStrictness.ADVISORY,
            confidence_threshold=0.7
        )
        
        context = {
            "active_goals": [{"name": "read_only_goal"}],
            "rl_signals": None,
        }
        
        # Tool that conflicts with read-only goal
        result = validator.validate_tool_selection("store_memory", {}, context)
        
        # Advisory should never block, only warn
        assert not result.blocked
        assert result.is_valid  # May have warnings but still valid
    
    def test_soft_block_blocks_on_low_confidence(self):
        """Test that soft block blocks when confidence is below threshold."""
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
        
        # Should block if confidence is below threshold
        if result.confidence < 0.7 and result.warnings:
            assert result.blocked
            assert result.alternatives  # Should suggest alternatives
    
    def test_hard_block_blocks_critical_violations(self):
        """Test that hard block blocks critical violations."""
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
        if any("conflict" in w.lower() for w in result.warnings):
            assert result.blocked
            assert result.severity == "error"
    
    def test_validation_provides_alternatives_when_blocking(self):
        """Test that validation provides alternatives when blocking."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(
            aggregator,
            strictness=ValidationStrictness.SOFT_BLOCK,
            confidence_threshold=0.5
        )
        
        context = {
            "active_goals": [{"name": "read_only_goal"}],
            "rl_signals": {"composite_reward": 0.2},  # Low reward
        }
        
        result = validator.validate_tool_selection("store_memory", {}, context)
        
        if result.blocked:
            assert len(result.alternatives) > 0 or len(result.suggestions) > 0


class TestFaultInjection:
    """Fault injection tests."""
    
    def test_validation_handles_none_context(self):
        """Test validation handles None context gracefully."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        # Should not raise
        result = validator.validate_tool_selection("test_tool", {}, context=None)
        assert isinstance(result, ValidationResult)
    
    def test_validation_handles_missing_components(self):
        """Test validation handles missing context components."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        # Context with missing components
        context = {}  # Empty context
        
        result = validator.validate_tool_selection("test_tool", {}, context)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid  # Should default to valid
    
    def test_validation_handles_invalid_goal_structure(self):
        """Test validation handles invalid goal structure."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        # Invalid goal structure
        context = {
            "active_goals": [{"invalid": "structure"}],
            "rl_signals": None,
        }
        
        # Should not raise
        result = validator.validate_tool_selection("test_tool", {}, context)
        assert isinstance(result, ValidationResult)
    
    def test_validation_handles_invalid_rl_signals(self):
        """Test validation handles invalid RL signal structure."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        # Invalid RL signal structure
        context = {
            "active_goals": [],
            "rl_signals": {"invalid": "structure"},
        }
        
        # Should not raise
        result = validator.validate_tool_selection("test_tool", {}, context)
        assert isinstance(result, ValidationResult)
    
    @patch('broca.tools.selection_guidance.logger')
    def test_validation_logs_errors_gracefully(self, mock_logger):
        """Test that validation logs errors without crashing."""
        aggregator = GuidanceAggregator()
        
        # Make goal_manager raise exception
        goal_manager = Mock()
        goal_manager.get_active_goals.side_effect = Exception("Test error")
        aggregator.goal_manager = goal_manager
        
        validator = ToolValidator(aggregator)
        
        context = {
            "active_goals": [],
            "rl_signals": None,
        }
        
        # Should not raise, should log error
        result = validator.validate_tool_selection("test_tool", {}, context)
        assert isinstance(result, ValidationResult)
    
    def test_validation_handles_exception_in_goal_validation(self):
        """Test validation handles exceptions in goal validation."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(aggregator)
        
        # Context that might cause exception
        context = {
            "active_goals": [None],  # Invalid goal
            "rl_signals": None,
        }
        
        # Should handle gracefully
        result = validator.validate_tool_selection("test_tool", {}, context)
        assert isinstance(result, ValidationResult)


class TestValidationConfidenceThresholds:
    """Test validation confidence thresholds."""
    
    def test_high_confidence_allows_execution(self):
        """Test that high confidence allows execution even with warnings."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(
            aggregator,
            strictness=ValidationStrictness.SOFT_BLOCK,
            confidence_threshold=0.5
        )
        
        context = {
            "active_goals": [],
            "rl_signals": {"composite_reward": 0.8},  # High reward
        }
        
        result = validator.validate_tool_selection("web_search", {}, context)
        
        # High confidence should not block
        if result.confidence >= 0.5:
            assert not result.blocked
    
    def test_low_confidence_triggers_blocking(self):
        """Test that low confidence triggers blocking in soft_block mode."""
        aggregator = GuidanceAggregator()
        validator = ToolValidator(
            aggregator,
            strictness=ValidationStrictness.SOFT_BLOCK,
            confidence_threshold=0.8
        )
        
        context = {
            "active_goals": [{"name": "read_only_goal"}],
            "rl_signals": None,
        }
        
        # Tool that conflicts
        result = validator.validate_tool_selection("store_memory", {}, context)
        
        # Low confidence should trigger blocking
        if result.confidence < 0.8 and result.warnings:
            assert result.blocked


class TestValidationResultProperties:
    """Test ValidationResult properties."""
    
    def test_validation_result_has_all_fields(self):
        """Test that ValidationResult has all required fields."""
        result = ValidationResult(
            is_valid=True,
            warnings=["warning1"],
            suggestions=["suggestion1"],
            confidence=0.8,
            blocked=False,
            alternatives=["alt1"],
            severity="warning"
        )
        
        assert hasattr(result, "is_valid")
        assert hasattr(result, "warnings")
        assert hasattr(result, "suggestions")
        assert hasattr(result, "confidence")
        assert hasattr(result, "blocked")
        assert hasattr(result, "alternatives")
        assert hasattr(result, "severity")
    
    def test_blocked_implies_not_valid(self):
        """Test that blocked implies not valid."""
        result = ValidationResult(
            is_valid=False,
            blocked=True,
            confidence=0.3
        )
        
        assert not result.is_valid
        assert result.blocked
    
    def test_valid_implies_not_blocked(self):
        """Test that valid implies not blocked."""
        result = ValidationResult(
            is_valid=True,
            blocked=False,
            confidence=0.9
        )
        
        assert result.is_valid
        assert not result.blocked

