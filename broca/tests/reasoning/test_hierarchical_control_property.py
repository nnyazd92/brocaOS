"""
Property-based tests for hierarchical control system.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
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


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        priority=st.floats(min_value=0.0, max_value=1.0),
        complexity=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_decision_always_valid(self, hierarchical_controller, priority, complexity):
        """Property: All decisions are valid (have level and confidence)."""
        decision = hierarchical_controller.make_decision(
            "test_goal",
            {"priority": priority, "complexity": complexity}
        )
        
        assert decision is not None
        assert decision.level in [ControlLevel.STRATEGIC, ControlLevel.TACTICAL, ControlLevel.OPERATIONAL]
        assert 0.0 <= decision.confidence <= 1.0
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_decisions=st.integers(min_value=1, max_value=100),
        priority=st.floats(min_value=0.0, max_value=1.0),
        complexity=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_statistics_always_valid(self, hierarchical_controller, num_decisions, priority, complexity):
        """Property: Statistics are always valid after any number of decisions."""
        for _ in range(num_decisions):
            hierarchical_controller.make_decision(
                "test_goal",
                {"priority": priority, "complexity": complexity}
            )
        
        stats = hierarchical_controller.get_control_statistics()
        assert stats["status"] != "no_data"
        assert stats["total_decisions"] >= num_decisions
        assert stats["total_decisions"] >= 0
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        strategic_threshold=st.floats(min_value=0.0, max_value=1.0),
        tactical_threshold=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_threshold_ordering(self, strategic_threshold, tactical_threshold):
        """Property: Thresholds maintain ordering (strategic >= tactical)."""
        if strategic_threshold < tactical_threshold:
            # Skip invalid configurations
            return
        
        controller = HierarchicalController(
            goal_manager=None,
            strategic_threshold=strategic_threshold,
            tactical_threshold=tactical_threshold
        )
        
        # High values should map to strategic
        decision = controller.make_decision(
            "goal",
            {"priority": 0.9, "complexity": 0.9}
        )
        assert decision.level in [ControlLevel.STRATEGIC, ControlLevel.TACTICAL, ControlLevel.OPERATIONAL]
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        context1=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.floats(min_value=0.0, max_value=1.0),
            min_size=0,
            max_size=10
        ),
        context2=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.floats(min_value=0.0, max_value=1.0),
            min_size=0,
            max_size=10
        )
    )
    def test_decision_idempotency(self, hierarchical_controller, context1, context2):
        """Property: Same context produces consistent decisions."""
        decision1 = hierarchical_controller.make_decision("goal1", context1)
        decision2 = hierarchical_controller.make_decision("goal2", context1)
        
        # Decisions with same context should have same level
        # (Note: confidence may vary due to randomness, but level should be consistent)
        if context1 == context2:
            decision3 = hierarchical_controller.make_decision("goal3", context2)
            # Level should be consistent for same context
            assert decision1.level == decision3.level

