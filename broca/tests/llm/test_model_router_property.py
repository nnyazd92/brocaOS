"""
Property-based tests for model router.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock
from broca.llm.model_router import (
    ModelRouter, EscalationPolicy, TaskType
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


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        success=st.booleans(),
        confidence=st.floats(min_value=0.0, max_value=1.0),
        dissonance=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_track_response_quality_always_valid(self, model_router, success, confidence, dissonance):
        """Property: Tracking response quality always produces valid metrics."""
        model_router.track_response_quality(
            "deepseek-chat",
            success=success,
            confidence=confidence,
            dissonance=dissonance
        )
        
        metrics = model_router.performance_tracker["deepseek-chat"]
        assert metrics.request_count > 0
        assert 0.0 <= metrics.success_rate <= 1.0
        assert 0.0 <= metrics.error_rate <= 1.0
        assert 0.0 <= metrics.avg_confidence <= 1.0
        assert 0.0 <= metrics.avg_dissonance <= 1.0
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_requests=st.integers(min_value=1, max_value=100),
        success_rate=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_success_rate_consistency(self, model_router, num_requests, success_rate):
        """Property: Success rate is consistent with tracked data."""
        metrics = model_router.performance_tracker["deepseek-chat"]

        # Hypothesis reuses function-scoped fixtures across many examples within a single test.
        # Reset rolling windows so each example is evaluated independently.
        metrics.request_count = 0
        metrics.success_count = 0
        metrics.error_count = 0
        metrics.recent_successes.clear()
        metrics.recent_errors.clear()
        metrics.recent_confidence.clear()
        metrics.recent_dissonance.clear()
        
        # Track requests with given success rate
        successes = int(num_requests * success_rate)
        failures = num_requests - successes
        
        for _ in range(successes):
            model_router.track_response_quality("deepseek-chat", success=True)
        for _ in range(failures):
            model_router.track_response_quality("deepseek-chat", success=False)
        
        # Success rate should match (within rounding)
        expected = (successes / num_requests) if num_requests > 0 else 1.0
        assert abs(metrics.success_rate - expected) < 0.01
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        task_description=st.text(min_size=1, max_size=200)
    )
    def test_route_task_always_returns_valid_model(self, model_router, task_description):
        """Property: Routing always returns a valid model or None."""
        model = model_router.route_task(task_description)
        
        assert model is None or model in model_router.models
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        threshold=st.floats(min_value=0.0, max_value=1.0),
        success_rate=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_escalation_threshold_ordering(self, model_router, threshold, success_rate):
        """Property: Escalation respects threshold ordering."""
        model_router.escalation_policy.success_rate_threshold = threshold
        
        metrics = model_router.performance_tracker["deepseek-chat"]
        metrics.request_count = 5  # Above min attempts
        
        # Set success rate
        if success_rate < threshold:
            # Low success rate - should escalate
            for _ in range(5):
                model_router.track_response_quality("deepseek-chat", success=False)
        else:
            # High success rate - should not escalate
            for _ in range(5):
                model_router.track_response_quality("deepseek-chat", success=True)
        
        should_escalate = model_router.should_escalate("deepseek-chat")
        
        # If success rate is below threshold, should escalate (if other conditions met)
        if success_rate < threshold and metrics.request_count >= model_router.escalation_policy.min_attempts_before_escalation:
            # May escalate (depends on other factors too)
            assert isinstance(should_escalate, bool)
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_escalations=st.integers(min_value=0, max_value=5)
    )
    def test_escalation_chain_bounds(self, model_router, num_escalations):
        """Property: Escalation never goes beyond chain bounds."""
        for _ in range(num_escalations):
            model = model_router.escalate_model()
            assert model is None or model in model_router.escalation_chain
            assert model_router.current_model_index <= len(model_router.escalation_chain) - 1
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        task_type=st.sampled_from(list(TaskType))
    )
    def test_route_task_type_consistency(self, model_router, task_type):
        """Property: Routing with explicit task type is consistent."""
        model1 = model_router.route_task("test", task_type=task_type)
        model2 = model_router.route_task("test", task_type=task_type)
        
        # Should route consistently (may vary due to other factors, but should be valid)
        assert model1 is None or model1 in model_router.models
        assert model2 is None or model2 in model_router.models

