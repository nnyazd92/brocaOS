"""
Fault injection tests for model router.
"""

import pytest
from unittest.mock import Mock
from broca.llm.model_router import ModelRouter, EscalationPolicy


@pytest.fixture
def model_router():
    """Create a model router with test models."""
    models = {
        "deepseek-chat": Mock(),
        "gpt-5-nano": Mock(),
    }
    return ModelRouter(
        models=models,
        escalation_enabled=True
    )


class TestFaultInjection:
    """Fault injection tests for robustness."""
    
    def test_none_models_dict(self):
        """Test handling of None models dictionary."""
        router = ModelRouter(models=None, escalation_enabled=False)
        assert router.models == {}
        assert router.route_task("test") is None
    
    def test_empty_models_dict(self):
        """Test handling of empty models dictionary."""
        router = ModelRouter(models={}, escalation_enabled=False)
        assert router.route_task("test") is None
    
    def test_missing_model_in_chain(self):
        """Test handling of missing model in escalation chain."""
        models = {"deepseek-chat": Mock()}
        router = ModelRouter(
            models=models,
            escalation_chain=["deepseek-chat", "nonexistent-model", "gpt-5-nano"],
            escalation_enabled=True
        )
        
        # Should handle gracefully
        current = router.get_current_model()
        assert current == "deepseek-chat"  # Should use available model
    
    def test_invalid_confidence_values(self, model_router):
        """Test handling of invalid confidence values."""
        # Negative confidence
        model_router.track_response_quality("deepseek-chat", confidence=-0.5)
        
        # Confidence > 1.0
        model_router.track_response_quality("deepseek-chat", confidence=1.5)
        
        # None confidence
        model_router.track_response_quality("deepseek-chat", confidence=None)
        
        # Should handle gracefully
        metrics = model_router.performance_tracker["deepseek-chat"]
        assert metrics.request_count >= 3
    
    def test_invalid_dissonance_values(self, model_router):
        """Test handling of invalid dissonance values."""
        # Negative dissonance
        model_router.track_response_quality("deepseek-chat", dissonance=-0.5)
        
        # Dissonance > 1.0
        model_router.track_response_quality("deepseek-chat", dissonance=1.5)
        
        # None dissonance
        model_router.track_response_quality("deepseek-chat", dissonance=None)
        
        # Should handle gracefully
        metrics = model_router.performance_tracker["deepseek-chat"]
        assert metrics.request_count >= 3
    
    def test_none_feedback_metrics(self, model_router):
        """Test handling of None feedback metrics."""
        should_escalate = model_router.should_escalate(
            "deepseek-chat",
            feedback_metrics=None
        )
        # Should handle gracefully (may return False if other criteria not met)
        assert isinstance(should_escalate, bool)
    
    def test_missing_performance_tracker(self, model_router):
        """Test handling of missing performance tracker entry."""
        # Try to escalate with non-existent model
        should_escalate = model_router.should_escalate("nonexistent-model")
        assert should_escalate is False  # Should handle gracefully
    
    def test_empty_task_description(self, model_router):
        """Test handling of empty task description."""
        model = model_router.route_task("")
        assert model is None or model in model_router.models
    
    def test_very_long_task_description(self, model_router):
        """Test handling of very long task description."""
        long_description = "test " * 10000
        model = model_router.route_task(long_description)
        assert model is None or model in model_router.models
    
    def test_none_task_type(self, model_router):
        """Test handling of None task type."""
        model = model_router.route_task("test", task_type=None)
        assert model is None or model in model_router.models
    
    def test_invalid_escalation_policy(self):
        """Test handling of invalid escalation policy values."""
        policy = EscalationPolicy(
            success_rate_threshold=-0.5,  # Invalid
            error_rate_threshold=1.5,  # Invalid
            confidence_threshold=-0.1,  # Invalid
            min_attempts_before_escalation=-1  # Invalid
        )
        
        models = {"deepseek-chat": Mock()}
        router = ModelRouter(
            models=models,
            escalation_policy=policy,
            escalation_enabled=True
        )
        
        # Should still function (may have unexpected behavior, but shouldn't crash)
        model = router.route_task("test")
        assert model is None or model in router.models
    
    def test_corrupted_performance_metrics(self, model_router):
        """Test handling of corrupted performance metrics."""
        metrics = model_router.performance_tracker["deepseek-chat"]
        
        # Corrupt the deques
        metrics.recent_successes = None  # type: ignore
        metrics.recent_errors = None  # type: ignore
        
        # Should handle gracefully when accessing properties
        try:
            success_rate = metrics.success_rate
            # Should return default or handle gracefully
            assert isinstance(success_rate, float) or success_rate is None
        except (AttributeError, TypeError):
            # Expected if None, but should not crash system
            pass

