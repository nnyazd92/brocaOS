"""
Integration tests for model router.
"""

import pytest
from unittest.mock import Mock, MagicMock
from broca.llm.model_router import ModelRouter
from broca.reasoning.feedback_loop import FeedbackMetrics


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    return Mock()


@pytest.fixture
def model_router(mock_llm_client):
    """Create a model router with test models."""
    models = {
        "deepseek-chat": mock_llm_client,
        "gpt-5-nano": mock_llm_client,
        "gpt-5-mini": mock_llm_client,
    }
    return ModelRouter(
        models=models,
        escalation_enabled=True,
        escalation_chain=["deepseek-chat", "gpt-5-nano", "gpt-5-mini"]
    )


class TestModelRouterIntegration:
    """Integration tests for model router."""
    
    def test_escalation_flow_end_to_end(self, model_router):
        """Test complete escalation flow."""
        # Start with cheapest model
        initial = model_router.get_current_model()
        assert initial == "deepseek-chat"
        
        # Track poor performance
        for _ in range(5):
            model_router.track_response_quality(
                "deepseek-chat",
                success=False,
                confidence=0.3,
                dissonance=0.5
            )
        
        # Should escalate
        should_escalate = model_router.should_escalate(
            "deepseek-chat",
            confidence=0.3,
            dissonance=0.5
        )
        assert should_escalate is True
        
        # Escalate
        escalated = model_router.escalate_model()
        assert escalated == "gpt-5-nano"
    
    def test_feedback_metrics_integration(self, model_router):
        """Test integration with FeedbackMetrics."""
        feedback_metrics = FeedbackMetrics(
            window_size=100,
            success_rate=0.5,  # Below threshold
            error_rate=0.4,  # Above threshold
            avg_cycle_duration=1.0
        )
        
        # Track some requests
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=True)
        
        should_escalate = model_router.should_escalate(
            "deepseek-chat",
            feedback_metrics=feedback_metrics
        )
        assert should_escalate is True
    
    def test_route_task_with_escalation_integration(self, model_router):
        """Test routing with escalation integration."""
        # Track poor performance
        for _ in range(5):
            model_router.track_response_quality(
                "deepseek-chat",
                success=False,
                confidence=0.3
            )
        
        # Route with escalation
        model = model_router.route_task_with_escalation(
            "Test task",
            confidence=0.3
        )
        
        # Should escalate to next model
        assert model == "gpt-5-nano"
    
    def test_performance_tracking_accumulation(self, model_router):
        """Test that performance metrics accumulate correctly."""
        # Track mixed performance
        for i in range(10):
            success = i % 3 != 0  # 2/3 success rate
            confidence = 0.5 + (0.3 if success else -0.2)
            model_router.track_response_quality(
                "deepseek-chat",
                success=success,
                confidence=confidence
            )
        
        metrics = model_router.performance_tracker["deepseek-chat"]
        assert metrics.request_count == 10
        assert metrics.success_count > 0
        assert len(metrics.recent_confidence) == 10
    
    def test_escalation_cooldown_integration(self, model_router):
        """Test escalation cooldown integration."""
        from datetime import datetime, timezone, timedelta
        
        model_router.escalation_policy.escalation_cooldown_seconds = 60.0
        
        # Track poor performance
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=False)
        
        # Set recent escalation
        metrics = model_router.performance_tracker["deepseek-chat"]
        metrics.last_escalation_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        
        # Should not escalate due to cooldown
        should_escalate = model_router.should_escalate("deepseek-chat")
        assert should_escalate is False
        
        # After cooldown, should escalate
        metrics.last_escalation_time = datetime.now(timezone.utc) - timedelta(seconds=120)
        should_escalate = model_router.should_escalate("deepseek-chat")
        assert should_escalate is True
    
    def test_multiple_models_performance_tracking(self, model_router):
        """Test tracking performance for multiple models."""
        # Track performance for different models
        model_router.track_response_quality("deepseek-chat", success=True, confidence=0.8)
        model_router.track_response_quality("gpt-5-nano", success=True, confidence=0.9)
        model_router.track_response_quality("gpt-5-mini", success=True, confidence=0.95)
        
        # Each should have separate metrics
        assert model_router.performance_tracker["deepseek-chat"].request_count == 1
        assert model_router.performance_tracker["gpt-5-nano"].request_count == 1
        assert model_router.performance_tracker["gpt-5-mini"].request_count == 1

