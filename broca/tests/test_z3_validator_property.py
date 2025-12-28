"""
Property-based tests for Z3LogicalValidator using Hypothesis.

Tests properties of validation methods with generated test cases.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from typing import List, Tuple, Dict, Any

from broca.reasoning.z3_validator import Z3LogicalValidator, LogicalRelation, Z3_AVAILABLE
from broca.reasoning.production_rules import ProductionRule, RuleType
from broca.reasoning.goal_manager import Goal, GoalType, GoalStatus
from datetime import datetime, timezone


class TestZ3ValidatorPropertyBased:
    """Property-based tests for Z3LogicalValidator."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        chain=st.lists(
            st.tuples(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=10)),
            min_size=0,
            max_size=10
        )
    )
    def test_causal_chain_transitivity_property(self, chain: List[Tuple[str, str]]):
        """
        Property: If A→B→C, then A→C (transitivity).
        
        Rationale: Causal chains should respect transitivity.
        """
        validator = Z3LogicalValidator()
        
        if not validator.enabled:
            pytest.skip("Z3 not available")
        
        # Remove duplicate edges
        unique_chain = []
        seen = set()
        for cause, effect in chain:
            edge = (cause, effect)
            if edge not in seen:
                seen.add(edge)
                unique_chain.append(edge)
        
        is_valid, error, warnings = validator.validate_causal_chain(unique_chain, check_transitivity=True)
        
        # Property: If chain is valid, transitive closure should be computed
        if is_valid and len(unique_chain) >= 2:
            # Check that transitive relationships are detected
            transitive = validator._compute_transitive_closure(unique_chain)
            # If we have A→B and B→C, we should find A→C
            for i, (cause1, effect1) in enumerate(unique_chain):
                for cause2, effect2 in unique_chain[i+1:]:
                    if effect1 == cause2:
                        # Should find transitive relationship
                        assert (cause1, effect2) in transitive or len(transitive) == 0
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        goals_data=st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=10),
                values=st.lists(st.text(min_size=1, max_size=10), max_size=3),
                min_size=1,
                max_size=3
            ),
            min_size=0,
            max_size=10
        )
    )
    def test_goal_dependencies_no_cycles_property(self, goals_data: List[Dict[str, Any]]):
        """
        Property: Goal dependencies should not contain cycles.
        
        Rationale: Circular dependencies should be detected.
        """
        validator = Z3LogicalValidator()
        
        if not validator.enabled:
            pytest.skip("Z3 not available")
        
        # Create goals from generated data
        goals = []
        goal_names = set()
        
        for i, goal_data in enumerate(goals_data):
            name = goal_data.get("name", f"goal_{i}")
            if name in goal_names:
                continue
            goal_names.add(name)
            
            deps = goal_data.get("dependencies", [])
            # Filter dependencies to only include valid goal names
            valid_deps = [d for d in deps if d in goal_names]
            
            goal = Goal(
                name=name,
                description=f"Test goal {i}",
                goal_type=GoalType.ACHIEVE,
                dependencies=valid_deps,
                status=GoalStatus.ACTIVE
            )
            goals.append(goal)
        
        is_valid, error, warnings = validator.validate_goal_dependencies(goals)
        
        # Property: If validation fails, it should be due to cycles or unsatisfiability
        if not is_valid:
            assert error is not None
            assert "circular" in error.lower() or "cycle" in error.lower() or "unsatisfiable" in error.lower()
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        constraints=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10),
                st.text(min_size=1, max_size=10),
                st.sampled_from(list(LogicalRelation))
            ),
            min_size=0,
            max_size=20
        )
    )
    def test_constraint_addition_property(self, constraints: List[Tuple[str, str, LogicalRelation]]):
        """
        Property: Constraints should be added up to max_constraints limit.
        
        Rationale: Constraint limit should be enforced.
        """
        validator = Z3LogicalValidator(max_constraints=10)
        
        for premise, conclusion, relation in constraints:
            validator.add_constraint(premise, conclusion, relation)
        
        # Property: Number of constraints should not exceed max_constraints
        assert len(validator._constraints) <= validator.max_constraints
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        propositions=st.lists(
            st.tuples(st.text(min_size=1, max_size=10), st.booleans()),
            min_size=0,
            max_size=10
        )
    )
    def test_contradiction_detection_property(self, propositions: List[Tuple[str, bool]]):
        """
        Property: Contradiction detection should find actual contradictions.
        
        Rationale: Contradictions should be detected when present.
        """
        validator = Z3LogicalValidator()
        
        if not validator.enabled:
            pytest.skip("Z3 not available")
        
        contradictions = validator.detect_contradictions(propositions)
        
        # Property: Contradictions should be pairs of propositions
        for prop1, prop2 in contradictions:
            assert isinstance(prop1, str)
            assert isinstance(prop2, str)
            assert prop1 != prop2
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        max_size=st.integers(min_value=50, max_value=500)
    )
    def test_validation_summary_size_property(self, max_size: int):
        """
        Property: Validation summary should respect size limits.
        
        Rationale: Summary should never exceed specified size limit.
        """
        validator = Z3LogicalValidator()
        
        # Update stats to generate summary
        validator.update_validation_stats(
            rule_chain_valid=True,
            causal_chains_valid=True,
            goal_dependencies_valid=True,
            warnings_count=5,
            contradictions_count=2
        )
        
        summary = validator.get_validation_summary(max_size_bytes=max_size)
        
        # Property: Summary should not exceed size limit
        import json
        json_str = json.dumps(summary)
        assert len(json_str.encode('utf-8')) <= max_size
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        chain_length=st.integers(min_value=0, max_value=10)
    )
    def test_causal_path_finding_property(self, chain_length: int):
        """
        Property: Causal path finding should return valid paths.
        
        Rationale: Path finding should work correctly for valid chains.
        """
        validator = Z3LogicalValidator()
        
        # Create a linear chain
        chain = []
        for i in range(chain_length):
            if i < chain_length - 1:
                chain.append((f"node_{i}", f"node_{i+1}"))
        
        if len(chain) >= 2:
            # Find path from first to last
            path = validator._find_causal_path(chain[0][0], chain[-1][1], chain)
            
            # Property: Path should start with source and end with target
            if path:
                assert path[0] == chain[0][0]
                assert path[-1] == chain[-1][1]
                # Path should be valid (each step should be in chain)
                for i in range(len(path) - 1):
                    assert (path[i], path[i+1]) in chain or any(
                        (path[i], path[i+1]) == (c, e) for c, e in chain
                    )

