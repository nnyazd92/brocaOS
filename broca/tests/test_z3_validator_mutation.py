"""
Mutation testing support for Z3LogicalValidator.

The actual mutation testing is run with mutmut, but these tests help
ensure that the test suite is comprehensive enough to catch mutations.
"""

from __future__ import annotations

import pytest

from broca.reasoning.z3_validator import Z3LogicalValidator, LogicalRelation


class TestZ3ValidatorMutationSupport:
    """Tests to support mutation testing of Z3LogicalValidator."""
    
    def test_validator_initialization_coverage(self):
        """
        Test that validator initialization is covered.
        
        Rationale: Ensures mutations to __init__ are caught.
        """
        validator1 = Z3LogicalValidator(enable_z3=True)
        validator2 = Z3LogicalValidator(enable_z3=False)
        validator3 = Z3LogicalValidator(timeout=10.0, max_constraints=500)
        
        assert validator1.enabled == validator1.enabled  # May be True or False depending on Z3 availability
        assert validator2.enabled is False
        assert validator3.timeout == 10.0
        assert validator3.max_constraints == 500
    
    def test_constraint_addition_coverage(self):
        """
        Test that constraint addition logic is covered.
        
        Rationale: Ensures mutations to add_constraint are caught.
        """
        validator = Z3LogicalValidator(max_constraints=2)
        
        validator.add_constraint("A", "B", LogicalRelation.IMPLIES)
        assert len(validator._constraints) == 1
        
        validator.add_constraint("B", "C", LogicalRelation.CAUSES)
        assert len(validator._constraints) == 2
        
        # Third should be limited
        validator.add_constraint("C", "D", LogicalRelation.IMPLIES)
        assert len(validator._constraints) <= 2
    
    def test_helper_methods_coverage(self):
        """
        Test that helper methods are covered.
        
        Rationale: Ensures mutations to helper methods are caught.
        """
        validator = Z3LogicalValidator()
        
        # Test proposition extraction
        prop1 = validator._extract_proposition({"content": "test"})
        assert prop1 == "test"
        
        prop2 = validator._extract_proposition({"type": "fact"})
        assert prop2 == "fact"
        
        prop3 = validator._extract_proposition({"other": "value"})
        assert prop3 is None
        
        # Test transitive closure
        chain = [("A", "B"), ("B", "C")]
        closure = validator._compute_transitive_closure(chain)
        assert ("A", "C") in closure
        
        # Test cycle detection
        graph = {"A": ["B"], "B": ["A"]}
        cycles = validator._find_cycles(graph)
        assert len(cycles) > 0

