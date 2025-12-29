"""
Mutation tests for model router.
"""

import pytest
from unittest.mock import Mock
from broca.llm.model_router import (
    ModelRouter, EscalationPolicy, ModelPerformanceMetrics, TaskType
)


@pytest.fixture
def model_router():
    """Create a model router with test models."""
    models = {
        "deepseek-chat": Mock(),
        "gpt-5-nano": Mock(),
        "gpt-5-mini": Mock(),
    }
    return ModelRouter(
        models=models,
        escalation_enabled=True,
        escalation_chain=["deepseek-chat", "gpt-5-nano", "gpt-5-mini"]
    )


class TestMutationKillers:
    """
    Tests specifically designed to kill mutations.
    
    These tests verify specific behaviors that would be broken by common mutations
    like changing operators, conditions, or return values.
    """
    
    def test_success_rate_threshold_enforced(self, model_router):
        """Kills mutation: changing success rate threshold comparison."""
        # Set custom policy with specific threshold
        model_router.escalation_policy.success_rate_threshold = 0.7
        
        # Track failures to get below threshold
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=False)
        
        should_escalate = model_router.should_escalate("deepseek-chat")
        assert should_escalate is True
    
    def test_error_rate_threshold_enforced(self, model_router):
        """Kills mutation: changing error rate threshold comparison."""
        model_router.escalation_policy.error_rate_threshold = 0.3
        
        # Track many errors
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=False)
        
        should_escalate = model_router.should_escalate("deepseek-chat")
        assert should_escalate is True
    
    def test_confidence_threshold_enforced(self, model_router):
        """Kills mutation: changing confidence threshold comparison."""
        model_router.escalation_policy.confidence_threshold = 0.5
        
        # Track low confidence
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=True, confidence=0.3)
        
        should_escalate = model_router.should_escalate("deepseek-chat", confidence=0.3)
        assert should_escalate is True
    
    def test_min_attempts_enforced(self, model_router):
        """Kills mutation: not checking minimum attempts."""
        model_router.escalation_policy.min_attempts_before_escalation = 3
        
        # Track only 1 attempt (below threshold)
        model_router.track_response_quality("deepseek-chat", success=False)
        
        should_escalate = model_router.should_escalate("deepseek-chat")
        assert should_escalate is False  # Should not escalate
    
    def test_cooldown_enforced(self, model_router):
        """Kills mutation: not checking cooldown."""
        from datetime import datetime, timezone, timedelta
        
        model_router.escalation_policy.escalation_cooldown_seconds = 60.0
        
        # Set recent escalation time
        metrics = model_router.performance_tracker["deepseek-chat"]
        metrics.last_escalation_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        metrics.request_count = 5  # Above min attempts
        
        should_escalate = model_router.should_escalate("deepseek-chat")
        assert should_escalate is False  # Should not escalate due to cooldown
    
    def test_escalation_chain_order(self, model_router):
        """Kills mutation: wrong escalation chain order."""
        initial = model_router.get_current_model()
        assert initial == "deepseek-chat"  # Should start at first in chain
        
        escalated = model_router.escalate_model()
        assert escalated == "gpt-5-nano"  # Should move to next in chain
    
    def test_performance_tracking_increment(self, model_router):
        """Kills mutation: not incrementing performance counters."""
        initial_count = model_router.performance_tracker["deepseek-chat"].request_count
        
        model_router.track_response_quality("deepseek-chat", success=True)
        
        new_count = model_router.performance_tracker["deepseek-chat"].request_count
        assert new_count == initial_count + 1
    
    def test_success_rate_calculation(self, model_router):
        """Kills mutation: wrong success rate calculation."""
        metrics = model_router.performance_tracker["deepseek-chat"]
        
        # Add 3 successes and 1 error
        for _ in range(3):
            metrics.recent_successes.append("success")
        metrics.recent_errors.append("error")
        
        # Success rate should be 3/4 = 0.75
        assert metrics.success_rate == pytest.approx(0.75)
    
    def test_escalation_index_bounds(self, model_router):
        """Kills mutation: escalation index out of bounds."""
        # Escalate to max
        model_router.escalate_model()  # To nano
        model_router.escalate_model()  # To mini
        
        # Should not go beyond chain
        max_model = model_router.escalate_model()
        assert max_model == "gpt-5-mini"  # Should stay at max

