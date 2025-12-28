"""
Fault injection tests for Z3LogicalValidator.

Tests graceful degradation when Z3 fails, timeouts occur, or invalid inputs are provided.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from broca.reasoning.z3_validator import Z3LogicalValidator, LogicalRelation, Z3_AVAILABLE
from broca.reasoning.production_rules import ProductionRule, RuleType
from broca.reasoning.goal_manager import Goal, GoalType, GoalStatus


class TestZ3ValidatorFaultInjection:
    """Fault injection tests for Z3LogicalValidator."""
    
    def test_z3_solver_failure(self):
        """
        Test graceful handling when Z3 solver fails.
        
        Rationale: System should continue operating when Z3 fails.
        """
        validator = Z3LogicalValidator()
        
        if not validator.enabled:
            pytest.skip("Z3 not available")
        
        # Mock Z3 solver to raise exception
        with patch('broca.reasoning.z3_validator.Solver') as mock_solver:
            mock_instance = MagicMock()
            mock_instance.check.side_effect = Exception("Z3 solver failure")
            mock_solver.return_value = mock_instance
            
            # Should handle gracefully
            rule = ProductionRule(
                name="test_rule",
                conditions=[{"type": "fact", "content": "A"}],
                actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": "B"}}],
                rule_type=RuleType.INFERENCE
            )
            
            is_valid, error, warnings = validator.validate_rule_chain([rule], ["A"])
            
            # Should return valid=True with warnings (graceful degradation)
            assert is_valid is True
            assert len(warnings) > 0
    
    def test_z3_timeout(self):
        """
        Test handling of Z3 solver timeouts.
        
        Rationale: Timeouts should be handled gracefully.
        """
        validator = Z3LogicalValidator(timeout=0.001)  # Very short timeout
        
        if not validator.enabled:
            pytest.skip("Z3 not available")
        
        # Create complex rule chain that might timeout
        rules = []
        for i in range(100):
            rule = ProductionRule(
                name=f"rule_{i}",
                conditions=[{"type": "fact", "content": f"premise_{i}"}],
                actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": f"conclusion_{i}"}}],
                rule_type=RuleType.INFERENCE
            )
            rules.append(rule)
        
        is_valid, error, warnings = validator.validate_rule_chain(rules, [])
        
        # Should handle timeout gracefully
        assert isinstance(is_valid, bool)
        # May return unknown status, which should be handled
    
    def test_invalid_constraint_format(self):
        """
        Test handling of invalid constraint formats.
        
        Rationale: Invalid inputs should not crash the system.
        """
        validator = Z3LogicalValidator()
        
        # Try to add constraint with invalid data
        try:
            validator.add_constraint("", "", LogicalRelation.IMPLIES)  # Empty strings
            validator.add_constraint(None, None, LogicalRelation.IMPLIES)  # None values
        except Exception as e:
            # Should handle gracefully or raise appropriate error
            assert isinstance(e, (TypeError, ValueError))
    
    def test_memory_exhaustion_scenario(self):
        """
        Test handling when too many constraints are added.
        
        Rationale: Should respect max_constraints limit.
        """
        validator = Z3LogicalValidator(max_constraints=5)
        
        # Add many constraints
        for i in range(10):
            validator.add_constraint(f"premise_{i}", f"conclusion_{i}", LogicalRelation.IMPLIES)
        
        # Should not exceed max_constraints
        assert len(validator._constraints) <= validator.max_constraints
    
    def test_invalid_rule_chain(self):
        """
        Test handling of invalid rule chain data.
        
        Rationale: Invalid rules should be handled gracefully.
        """
        validator = Z3LogicalValidator()
        
        # Invalid rule (missing required fields)
        invalid_rule = Mock()
        invalid_rule.conditions = None
        invalid_rule.actions = None
        
        is_valid, error, warnings = validator.validate_rule_chain([invalid_rule], [])
        
        # Should handle gracefully
        assert isinstance(is_valid, bool)
    
    def test_invalid_goal_dependencies(self):
        """
        Test handling of invalid goal dependency data.
        
        Rationale: Invalid goals should be handled gracefully.
        """
        validator = Z3LogicalValidator()
        
        # Goal with invalid dependencies (references non-existent goal)
        goal = Goal(
            name="test_goal",
            description="Test",
            goal_type=GoalType.ACHIEVE,
            dependencies=["nonexistent_goal"],
            status=GoalStatus.ACTIVE
        )
        
        is_valid, error, warnings = validator.validate_goal_dependencies([goal])
        
        # Should handle gracefully (may be valid or invalid depending on Z3)
        assert isinstance(is_valid, bool)
    
    def test_z3_unavailable_graceful_degradation(self):
        """
        Test graceful degradation when Z3 is unavailable.
        
        Rationale: System should work without Z3.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        # All operations should work in no-op mode
        rule = ProductionRule(
            name="test_rule",
            conditions=[{"type": "fact", "content": "A"}],
            actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": "B"}}],
            rule_type=RuleType.INFERENCE
        )
        
        is_valid, error, warnings = validator.validate_rule_chain([rule], ["A"])
        assert is_valid is True
        assert error is None
        assert warnings == []
        
        is_valid, error, warnings = validator.validate_causal_chain([("A", "B")])
        assert is_valid is True
        
        goal = Goal(
            name="test_goal",
            description="Test",
            goal_type=GoalType.ACHIEVE,
            status=GoalStatus.ACTIVE
        )
        
        is_valid, error, warnings = validator.validate_goal_dependencies([goal])
        assert is_valid is True
    
    def test_validation_summary_with_errors(self):
        """
        Test validation summary generation when errors occur.
        
        Rationale: Summary should be generated even when validation fails.
        """
        validator = Z3LogicalValidator()
        
        # Update stats with error states
        validator.update_validation_stats(
            rule_chain_valid=False,
            warnings_count=10,
            contradictions_count=5
        )
        
        summary = validator.get_validation_summary()
        
        assert summary["enabled"] == validator.enabled
        assert summary["rule_chain_valid"] is False
        assert summary["warnings_count"] == 10
        assert summary["contradictions_count"] == 5

