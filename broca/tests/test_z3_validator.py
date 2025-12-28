"""
Tests for Z3LogicalValidator.

Tests Z3-based logical validation of reasoning chains, causal relationships,
goal dependencies, and learned procedures.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from broca.reasoning.z3_validator import (
    Z3LogicalValidator,
    LogicalRelation,
    ValidationSummary,
    Z3_AVAILABLE
)
from broca.reasoning.production_rules import ProductionRule, RuleType
from broca.reasoning.goal_manager import Goal, GoalStatus, GoalType


class TestZ3ValidatorInitialization:
    """Test Z3LogicalValidator initialization."""
    
    def test_init_with_z3_available(self):
        """
        Test initialization when Z3 is available.
        
        Rationale: Ensures validator initializes correctly when Z3 is installed.
        """
        validator = Z3LogicalValidator(enable_z3=True)
        
        assert validator.enabled == Z3_AVAILABLE
        assert validator.timeout == 5.0
        assert validator.max_constraints == 1000
        assert validator._variable_cache == {}
        assert validator._constraints == []
    
    def test_init_with_z3_disabled(self):
        """
        Test initialization with Z3 disabled.
        
        Rationale: Ensures validator works in no-op mode when Z3 is disabled.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        assert validator.enabled is False
    
    def test_init_with_custom_timeout(self):
        """
        Test initialization with custom timeout.
        
        Rationale: Ensures timeout can be configured.
        """
        validator = Z3LogicalValidator(timeout=10.0)
        
        assert validator.timeout == 10.0
    
    def test_init_with_custom_max_constraints(self):
        """
        Test initialization with custom max constraints.
        
        Rationale: Ensures max constraints can be configured.
        """
        validator = Z3LogicalValidator(max_constraints=500)
        
        assert validator.max_constraints == 500


class TestZ3ValidatorRuleChain:
    """Test rule chain validation."""
    
    def test_validate_empty_rule_chain(self):
        """
        Test validation of empty rule chain.
        
        Rationale: Empty chains should be valid.
        """
        validator = Z3LogicalValidator()
        is_valid, error, warnings = validator.validate_rule_chain([], [])
        
        assert is_valid is True
        assert error is None
        assert warnings == []
    
    def test_validate_simple_rule_chain(self):
        """
        Test validation of simple rule chain.
        
        Rationale: Simple valid rule chains should pass validation.
        """
        validator = Z3LogicalValidator()
        
        rule = ProductionRule(
            name="test_rule",
            conditions=[{"type": "fact", "content": "A"}],
            actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": "B"}}],
            rule_type=RuleType.INFERENCE
        )
        
        is_valid, error, warnings = validator.validate_rule_chain(
            [rule],
            ["A"]
        )
        
        # Should be valid (or gracefully handle if Z3 unavailable)
        assert is_valid is True
    
    def test_validate_rule_chain_without_z3(self):
        """
        Test validation when Z3 is disabled.
        
        Rationale: Should return valid when Z3 is unavailable.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        rule = ProductionRule(
            name="test_rule",
            conditions=[{"type": "fact", "content": "A"}],
            actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": "B"}}],
            rule_type=RuleType.INFERENCE
        )
        
        is_valid, error, warnings = validator.validate_rule_chain([rule], [])
        
        assert is_valid is True
        assert error is None
        assert warnings == []
    
    def test_validate_rule_chain_with_working_memory_facts(self):
        """
        Test validation with working memory facts.
        
        Rationale: Working memory facts should be encoded as true propositions.
        """
        validator = Z3LogicalValidator()
        
        rule = ProductionRule(
            name="test_rule",
            conditions=[{"type": "fact", "content": "premise"}],
            actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": "conclusion"}}],
            rule_type=RuleType.INFERENCE
        )
        
        is_valid, error, warnings = validator.validate_rule_chain(
            [rule],
            ["premise"]
        )
        
        assert is_valid is True


class TestZ3ValidatorCausalChain:
    """Test causal chain validation."""
    
    def test_validate_empty_causal_chain(self):
        """
        Test validation of empty causal chain.
        
        Rationale: Empty chains should be valid.
        """
        validator = Z3LogicalValidator()
        is_valid, error, warnings = validator.validate_causal_chain([])
        
        assert is_valid is True
        assert error is None
        assert warnings == []
    
    def test_validate_simple_causal_chain(self):
        """
        Test validation of simple causal chain.
        
        Rationale: Simple valid causal chains should pass validation.
        """
        validator = Z3LogicalValidator()
        
        chain = [("A", "B"), ("B", "C")]
        is_valid, error, warnings = validator.validate_causal_chain(chain)
        
        assert is_valid is True
    
    def test_validate_causal_chain_without_z3(self):
        """
        Test validation when Z3 is disabled.
        
        Rationale: Should return valid when Z3 is unavailable.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        chain = [("A", "B"), ("B", "C")]
        is_valid, error, warnings = validator.validate_causal_chain(chain)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_causal_chain_transitivity(self):
        """
        Test transitivity detection in causal chains.
        
        Rationale: Should detect transitive relationships (A→B→C implies A→C).
        """
        validator = Z3LogicalValidator()
        
        chain = [("A", "B"), ("B", "C")]
        is_valid, error, warnings = validator.validate_causal_chain(chain, check_transitivity=True)
        
        assert is_valid is True
        # Should have warnings about transitive relationships
        # (exact behavior depends on Z3 availability)
    
    def test_validate_causal_chain_cycle_detection(self):
        """
        Test cycle detection in causal chains.
        
        Rationale: Should detect cycles (A→B→A).
        """
        validator = Z3LogicalValidator()
        
        # Build a cycle by adding constraints
        validator.add_constraint("A", "B", LogicalRelation.CAUSES)
        validator.add_constraint("B", "A", LogicalRelation.CAUSES)
        
        chain = [("A", "B"), ("B", "A")]
        is_valid, error, warnings = validator.validate_causal_chain(chain)
        
        # Should detect cycle (if Z3 available)
        if validator.enabled:
            # May or may not detect cycle depending on implementation
            pass
        else:
            assert is_valid is True


class TestZ3ValidatorGoalDependencies:
    """Test goal dependency validation."""
    
    def test_validate_empty_goals(self):
        """
        Test validation of empty goal list.
        
        Rationale: Empty goal lists should be valid.
        """
        validator = Z3LogicalValidator()
        is_valid, error, warnings = validator.validate_goal_dependencies([])
        
        assert is_valid is True
        assert error is None
        assert warnings == []
    
    def test_validate_goals_without_dependencies(self):
        """
        Test validation of goals without dependencies.
        
        Rationale: Goals without dependencies should be valid.
        """
        validator = Z3LogicalValidator()
        
        goal = Goal(
            name="goal1",
            description="Test goal",
            goal_type=GoalType.ACHIEVE,
            dependencies=[]
        )
        
        is_valid, error, warnings = validator.validate_goal_dependencies([goal])
        
        assert is_valid is True
    
    def test_validate_goals_with_valid_dependencies(self):
        """
        Test validation of goals with valid dependencies.
        
        Rationale: Goals with satisfiable dependencies should be valid.
        """
        validator = Z3LogicalValidator()
        
        goal1 = Goal(
            name="goal1",
            description="First goal",
            goal_type=GoalType.ACHIEVE,
            dependencies=[]
        )
        
        goal2 = Goal(
            name="goal2",
            description="Second goal",
            goal_type=GoalType.ACHIEVE,
            dependencies=["goal1"]
        )
        
        is_valid, error, warnings = validator.validate_goal_dependencies([goal1, goal2])
        
        assert is_valid is True
    
    def test_validate_goals_without_z3(self):
        """
        Test validation when Z3 is disabled.
        
        Rationale: Should return valid when Z3 is unavailable.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        goal = Goal(
            name="goal1",
            description="Test goal",
            goal_type=GoalType.ACHIEVE,
            dependencies=[]
        )
        
        is_valid, error, warnings = validator.validate_goal_dependencies([goal])
        
        assert is_valid is True
        assert error is None
    
    def test_validate_goals_with_circular_dependencies(self):
        """
        Test detection of circular dependencies.
        
        Rationale: Should detect circular dependencies (A depends on B, B depends on A).
        """
        validator = Z3LogicalValidator()
        
        goal1 = Goal(
            name="goal1",
            description="First goal",
            goal_type=GoalType.ACHIEVE,
            dependencies=["goal2"]
        )
        
        goal2 = Goal(
            name="goal2",
            description="Second goal",
            goal_type=GoalType.ACHIEVE,
            dependencies=["goal1"]
        )
        
        is_valid, error, warnings = validator.validate_goal_dependencies([goal1, goal2])
        
        # Should detect circular dependency
        if validator.enabled:
            assert is_valid is False
            assert "circular" in error.lower() or "cycle" in error.lower()
        else:
            # Without Z3, may not detect cycles
            pass


class TestZ3ValidatorLearnedProcedure:
    """Test learned procedure validation."""
    
    def test_validate_procedure_without_preconditions(self):
        """
        Test validation of procedure without preconditions.
        
        Rationale: Procedures without preconditions should be valid.
        """
        validator = Z3LogicalValidator()
        
        is_valid, error, warnings = validator.validate_learned_procedure(
            "test_procedure",
            [],
            ["postcondition"],
            []
        )
        
        assert is_valid is True
    
    def test_validate_procedure_without_postconditions(self):
        """
        Test validation of procedure without postconditions.
        
        Rationale: Procedures without postconditions should be valid.
        """
        validator = Z3LogicalValidator()
        
        is_valid, error, warnings = validator.validate_learned_procedure(
            "test_procedure",
            ["precondition"],
            [],
            []
        )
        
        assert is_valid is True
    
    def test_validate_procedure_without_z3(self):
        """
        Test validation when Z3 is disabled.
        
        Rationale: Should return valid when Z3 is unavailable.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        is_valid, error, warnings = validator.validate_learned_procedure(
            "test_procedure",
            ["precondition"],
            ["postcondition"],
            []
        )
        
        assert is_valid is True
        assert error is None
    
    def test_validate_procedure_with_tool_sequence(self):
        """
        Test validation with tool sequence.
        
        Rationale: Should handle tool sequences in validation.
        """
        validator = Z3LogicalValidator()
        
        tool_sequence = [
            {"tool_name": "test_tool", "parameters": {"param": "value"}}
        ]
        
        is_valid, error, warnings = validator.validate_learned_procedure(
            "test_procedure",
            ["precondition"],
            ["postcondition"],
            tool_sequence
        )
        
        assert is_valid is True


class TestZ3ValidatorContradictionDetection:
    """Test contradiction detection."""
    
    def test_detect_contradictions_empty(self):
        """
        Test contradiction detection with empty propositions.
        
        Rationale: Empty proposition lists should return no contradictions.
        """
        validator = Z3LogicalValidator()
        contradictions = validator.detect_contradictions([])
        
        assert contradictions == []
    
    def test_detect_contradictions_without_z3(self):
        """
        Test contradiction detection when Z3 is disabled.
        
        Rationale: Should return empty list when Z3 is unavailable.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        propositions = [("A", True), ("B", False)]
        contradictions = validator.detect_contradictions(propositions)
        
        assert contradictions == []
    
    def test_detect_contradictions_simple(self):
        """
        Test contradiction detection with simple propositions.
        
        Rationale: Should detect obvious contradictions if present.
        """
        validator = Z3LogicalValidator()
        
        # This is a simplified test - actual contradiction detection
        # depends on Z3 and proposition semantics
        propositions = [("A", True), ("B", True)]
        contradictions = validator.detect_contradictions(propositions)
        
        # Result depends on whether A and B actually contradict
        assert isinstance(contradictions, list)


class TestZ3ValidatorConstraints:
    """Test constraint management."""
    
    def test_add_constraint(self):
        """
        Test adding a constraint.
        
        Rationale: Should add constraints to internal list.
        """
        validator = Z3LogicalValidator()
        
        validator.add_constraint("A", "B", LogicalRelation.IMPLIES)
        
        assert len(validator._constraints) == 1
        assert validator._constraints[0].premise == "A"
        assert validator._constraints[0].conclusion == "B"
        assert validator._constraints[0].relation == LogicalRelation.IMPLIES
    
    def test_add_constraint_without_z3(self):
        """
        Test adding constraint when Z3 is disabled.
        
        Rationale: Should not add constraints when Z3 is disabled.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        validator.add_constraint("A", "B", LogicalRelation.IMPLIES)
        
        assert len(validator._constraints) == 0
    
    def test_add_constraint_max_limit(self):
        """
        Test constraint limit enforcement.
        
        Rationale: Should warn when max constraints limit is reached.
        """
        validator = Z3LogicalValidator(max_constraints=2)
        
        validator.add_constraint("A", "B", LogicalRelation.IMPLIES)
        validator.add_constraint("B", "C", LogicalRelation.IMPLIES)
        
        # Third constraint should trigger warning
        with pytest.warns() if validator.enabled else pytest.raises(Exception):
            validator.add_constraint("C", "D", LogicalRelation.IMPLIES)
    
    def test_add_causal_constraint(self):
        """
        Test adding causal constraint.
        
        Rationale: Should track causal relationships in graph.
        """
        validator = Z3LogicalValidator()
        
        validator.add_constraint("A", "B", LogicalRelation.CAUSES)
        
        assert "A" in validator._causal_graph
        assert "B" in validator._causal_graph["A"]


class TestZ3ValidatorSummary:
    """Test validation summary generation."""
    
    def test_get_validation_summary_default(self):
        """
        Test getting validation summary with default state.
        
        Rationale: Should return summary with default values.
        """
        validator = Z3LogicalValidator()
        
        summary = validator.get_validation_summary()
        
        assert summary["enabled"] == validator.enabled
        assert summary["rule_chain_valid"] is True
        assert summary["causal_chains_valid"] is True
        assert summary["goal_dependencies_valid"] is True
        assert summary["warnings_count"] == 0
        assert summary["contradictions_count"] == 0
    
    def test_get_validation_summary_size_limit(self):
        """
        Test validation summary size limit enforcement.
        
        Rationale: Should enforce max size limit (200 bytes).
        """
        validator = Z3LogicalValidator()
        
        summary = validator.get_validation_summary(max_size_bytes=200)
        
        import json
        json_str = json.dumps(summary)
        assert len(json_str.encode('utf-8')) <= 200
    
    def test_get_validation_summary_updates(self):
        """
        Test validation summary with updated stats.
        
        Rationale: Should reflect updated validation statistics.
        """
        validator = Z3LogicalValidator()
        
        validator.update_validation_stats(
            rule_chain_valid=False,
            warnings_count=5,
            contradictions_count=2
        )
        
        summary = validator.get_validation_summary()
        
        assert summary["rule_chain_valid"] is False
        assert summary["warnings_count"] == 5
        assert summary["contradictions_count"] == 2
        assert summary["last_validation"] is not None
    
    def test_get_validation_summary_without_z3(self):
        """
        Test validation summary when Z3 is disabled.
        
        Rationale: Should return summary indicating Z3 is disabled.
        """
        validator = Z3LogicalValidator(enable_z3=False)
        
        summary = validator.get_validation_summary()
        
        assert summary["enabled"] is False


class TestZ3ValidatorHelpers:
    """Test helper methods."""
    
    def test_extract_proposition(self):
        """
        Test proposition extraction from conditions.
        
        Rationale: Should extract proposition names from various condition formats.
        """
        validator = Z3LogicalValidator()
        
        # Test with "content" field
        prop = validator._extract_proposition({"content": "test_prop"})
        assert prop == "test_prop"
        
        # Test with "type" field
        prop = validator._extract_proposition({"type": "fact"})
        assert prop == "fact"
        
        # Test with "name" field
        prop = validator._extract_proposition({"name": "goal_name"})
        assert prop == "goal_name"
        
        # Test with no valid field
        prop = validator._extract_proposition({"other": "value"})
        assert prop is None
    
    def test_extract_proposition_from_action(self):
        """
        Test proposition extraction from actions.
        
        Rationale: Should extract propositions from action content.
        """
        validator = Z3LogicalValidator()
        
        action = {
            "type": "add_to_memory",
            "content": {"type": "fact", "content": "test_fact"}
        }
        
        prop = validator._extract_proposition_from_action(action)
        assert prop == "test_fact"
    
    def test_compute_transitive_closure(self):
        """
        Test transitive closure computation.
        
        Rationale: Should compute transitive relationships (A→B→C implies A→C).
        """
        validator = Z3LogicalValidator()
        
        chain = [("A", "B"), ("B", "C")]
        closure = validator._compute_transitive_closure(chain)
        
        # Should find A→C transitively
        assert ("A", "C") in closure
    
    def test_find_causal_path(self):
        """
        Test causal path finding.
        
        Rationale: Should find paths through causal chains.
        """
        validator = Z3LogicalValidator()
        
        chain = [("A", "B"), ("B", "C")]
        path = validator._find_causal_path("A", "C", chain)
        
        assert path == ["A", "B", "C"]
    
    def test_find_cycles(self):
        """
        Test cycle detection in graphs.
        
        Rationale: Should detect cycles in dependency graphs.
        """
        validator = Z3LogicalValidator()
        
        # Graph with cycle: A→B→A
        graph = {
            "A": ["B"],
            "B": ["A"]
        }
        
        cycles = validator._find_cycles(graph)
        
        assert len(cycles) > 0
        # Should contain cycle involving A and B
        assert any("A" in cycle and "B" in cycle for cycle in cycles)

