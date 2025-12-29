"""
Mutation tests for hierarchical control system.
"""

import pytest
from unittest.mock import Mock
from broca.reasoning.hierarchical_control import HierarchicalController, ControlLevel


@pytest.fixture
def hierarchical_controller():
    """Create a hierarchical controller instance."""
    return HierarchicalController(
        goal_manager=None,
        strategic_threshold=0.8,
        tactical_threshold=0.5
    )


class TestMutationKillers:
    """
    Tests specifically designed to kill mutations.
    
    These tests verify specific behaviors that would be broken by common mutations
    like changing operators, conditions, or return values.
    """
    
    def test_strategic_threshold_enforced(self, hierarchical_controller):
        """Kills mutation: changing strategic threshold comparison."""
        decision = hierarchical_controller.make_decision(
            "goal",
            {"priority": 0.9, "complexity": 0.9}
        )
        # Should be strategic when priority and complexity are high
        assert decision.level == ControlLevel.STRATEGIC
    
    def test_tactical_threshold_enforced(self, hierarchical_controller):
        """Kills mutation: changing tactical threshold comparison."""
        decision = hierarchical_controller.make_decision(
            "goal",
            {"priority": 0.6, "complexity": 0.4}
        )
        # Should be tactical or operational, not strategic
        assert decision.level != ControlLevel.STRATEGIC
    
    def test_confidence_bounds(self, hierarchical_controller):
        """Kills mutation: returning confidence outside [0, 1]."""
        decision = hierarchical_controller.make_decision("goal", {})
        assert 0.0 <= decision.confidence <= 1.0
    
    def test_statistics_increment(self, hierarchical_controller):
        """Kills mutation: not incrementing statistics counters."""
        initial_stats = hierarchical_controller.get_control_statistics()
        initial_count = initial_stats.get("total_decisions", 0)
        
        hierarchical_controller.make_decision("goal", {})
        
        new_stats = hierarchical_controller.get_control_statistics()
        new_count = new_stats.get("total_decisions", 0)
        assert new_count > initial_count
    
    def test_level_classification_consistency(self, hierarchical_controller):
        """Kills mutation: inconsistent level classification."""
        # High priority/complexity should be strategic
        decision1 = hierarchical_controller.make_decision(
            "goal1", {"priority": 0.9, "complexity": 0.9}
        )
        
        # Low priority/complexity should be operational
        decision2 = hierarchical_controller.make_decision(
            "goal2", {"priority": 0.2, "complexity": 0.2}
        )
        
        # Strategic should have higher confidence than operational
        assert decision1.confidence >= decision2.confidence

