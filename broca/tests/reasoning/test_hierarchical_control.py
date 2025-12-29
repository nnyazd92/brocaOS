"""
Unit tests for hierarchical control system.
"""

import pytest
from unittest.mock import Mock, MagicMock
from broca.reasoning.hierarchical_control import HierarchicalController, ControlLevel, ControlDecision


@pytest.fixture
def mock_goal_manager():
    """Create a mock goal manager."""
    manager = Mock()
    manager.get_active_goals.return_value = []
    manager.get_goal_by_name.return_value = None
    return manager


@pytest.fixture
def hierarchical_controller(mock_goal_manager):
    """Create a hierarchical controller instance."""
    return HierarchicalController(
        goal_manager=mock_goal_manager,
        strategic_threshold=0.8,
        tactical_threshold=0.5
    )


class TestHierarchicalController:
    """Unit tests for HierarchicalController."""
    
    def test_init(self, hierarchical_controller):
        """Test controller initialization."""
        assert hierarchical_controller is not None
        assert hierarchical_controller.strategic_threshold == 0.8
        assert hierarchical_controller.tactical_threshold == 0.5
    
    def test_make_decision_strategic(self, hierarchical_controller):
        """Test strategic level decision."""
        decision = hierarchical_controller.make_decision(
            goal_name="test_goal",
            context={"priority": 0.9, "complexity": 0.8}
        )
        assert decision.level == ControlLevel.STRATEGIC
        assert decision.confidence >= 0.0
        assert decision.confidence <= 1.0
    
    def test_make_decision_tactical(self, hierarchical_controller):
        """Test tactical level decision."""
        decision = hierarchical_controller.make_decision(
            goal_name="test_goal",
            context={"priority": 0.6, "complexity": 0.4}
        )
        assert decision.level in [ControlLevel.TACTICAL, ControlLevel.OPERATIONAL]
    
    def test_make_decision_operational(self, hierarchical_controller):
        """Test operational level decision."""
        decision = hierarchical_controller.make_decision(
            goal_name="test_goal",
            context={"priority": 0.3, "complexity": 0.2}
        )
        assert decision.level == ControlLevel.OPERATIONAL
    
    def test_get_control_statistics(self, hierarchical_controller):
        """Test statistics retrieval."""
        # Make some decisions
        hierarchical_controller.make_decision("goal1", {"priority": 0.9})
        hierarchical_controller.make_decision("goal2", {"priority": 0.5})
        
        stats = hierarchical_controller.get_control_statistics()
        assert stats["status"] != "no_data"
        assert "total_decisions" in stats
        assert stats["total_decisions"] >= 2
    
    def test_decision_with_none_goal_manager(self):
        """Test decision making when goal manager is None."""
        controller = HierarchicalController(
            goal_manager=None,
            strategic_threshold=0.8,
            tactical_threshold=0.5
        )
        decision = controller.make_decision("test_goal", {})
        assert decision is not None
        assert decision.level in [ControlLevel.STRATEGIC, ControlLevel.TACTICAL, ControlLevel.OPERATIONAL]

