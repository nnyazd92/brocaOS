"""
Fault injection tests for hierarchical control system.
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


class TestFaultInjection:
    """Fault injection tests for robustness."""
    
    def test_none_goal_manager(self):
        """Test handling of None goal manager."""
        controller = HierarchicalController(
            goal_manager=None,
            strategic_threshold=0.8,
            tactical_threshold=0.5
        )
        
        decision = controller.make_decision("goal", {})
        assert decision is not None
        assert decision.level in [ControlLevel.STRATEGIC, ControlLevel.TACTICAL, ControlLevel.OPERATIONAL]
    
    def test_invalid_threshold_values(self):
        """Test handling of invalid threshold values."""
        # Negative thresholds
        controller = HierarchicalController(
            goal_manager=None,
            strategic_threshold=-0.1,
            tactical_threshold=-0.2
        )
        decision = controller.make_decision("goal", {})
        assert decision is not None
    
    def test_missing_context_keys(self, hierarchical_controller):
        """Test handling of missing context keys."""
        decision = hierarchical_controller.make_decision("goal", {})
        assert decision is not None
    
    def test_invalid_context_values(self, hierarchical_controller):
        """Test handling of invalid context values."""
        # Negative values
        decision1 = hierarchical_controller.make_decision("goal", {"priority": -0.5})
        assert decision1 is not None
        
        # Values > 1.0
        decision2 = hierarchical_controller.make_decision("goal", {"priority": 1.5})
        assert decision2 is not None
        
        # None values
        decision3 = hierarchical_controller.make_decision("goal", {"priority": None})
        assert decision3 is not None
    
    def test_empty_goal_name(self, hierarchical_controller):
        """Test handling of empty goal name."""
        decision = hierarchical_controller.make_decision("", {})
        assert decision is not None
    
    def test_very_large_context(self, hierarchical_controller):
        """Test handling of very large context dictionary."""
        large_context = {f"key_{i}": i * 0.1 for i in range(1000)}
        decision = hierarchical_controller.make_decision("goal", large_context)
        assert decision is not None
    
    def test_corrupted_goal_manager(self):
        """Test handling of corrupted goal manager."""
        corrupted_manager = Mock()
        corrupted_manager.get_active_goals.side_effect = Exception("Corrupted")
        
        controller = HierarchicalController(
            goal_manager=corrupted_manager,
            strategic_threshold=0.8,
            tactical_threshold=0.5
        )
        
        # Should handle exception gracefully
        decision = controller.make_decision("goal", {})
        assert decision is not None

