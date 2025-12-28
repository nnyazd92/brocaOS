"""
Unit tests for model router.
"""

import pytest
from unittest.mock import Mock, MagicMock
from broca.llm.model_router import (
    ModelRouter, ModelCapability, ModelPerformanceMetrics,
    EscalationPolicy, TaskType
)


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


class TestModelRouter:
    """Unit tests for ModelRouter."""
    
    def test_init(self, model_router):
        """Test router initialization."""
        assert model_router is not None
        assert len(model_router.models) == 3
        assert model_router.escalation_enabled is True
        assert len(model_router.escalation_chain) == 3
    
    def test_register_model(self, model_router, mock_llm_client):
        """Test model registration."""
        model_router.register_model("test-model", mock_llm_client)
        assert "test-model" in model_router.models
        assert "test-model" in model_router.capabilities
        assert "test-model" in model_router.performance_tracker
    
    def test_route_task(self, model_router):
        """Test basic task routing."""
        model = model_router.route_task("Analyze this reasoning problem")
        assert model is not None
        assert model in model_router.models
    
    def test_route_task_reasoning(self, model_router):
        """Test routing for reasoning tasks."""
        model = model_router.route_task(
            "Reason about this logic problem",
            task_type=TaskType.REASONING
        )
        assert model is not None
    
    def test_route_task_planning(self, model_router):
        """Test routing for planning tasks."""
        model = model_router.route_task(
            "Plan a sequence of steps",
            task_type=TaskType.PLANNING
        )
        assert model is not None
    
    def test_get_current_model(self, model_router):
        """Test getting current model in escalation chain."""
        current = model_router.get_current_model()
        assert current is not None
        assert current in model_router.escalation_chain
    
    def test_escalate_model(self, model_router):
        """Test model escalation."""
        initial_model = model_router.get_current_model()
        escalated = model_router.escalate_model()
        
        assert escalated is not None
        assert escalated != initial_model or model_router.current_model_index == len(model_router.escalation_chain) - 1
    
    def test_track_response_quality(self, model_router):
        """Test tracking response quality."""
        model_router.track_response_quality("deepseek-chat", success=True, confidence=0.8)
        
        metrics = model_router.performance_tracker["deepseek-chat"]
        assert metrics.request_count == 1
        assert metrics.success_count == 1
        assert len(metrics.recent_confidence) == 1
    
    def test_should_escalate_low_success_rate(self, model_router):
        """Test escalation triggered by low success rate."""
        # Track multiple failures
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=False)
        
        should_escalate = model_router.should_escalate("deepseek-chat")
        assert should_escalate is True
    
    def test_should_escalate_low_confidence(self, model_router):
        """Test escalation triggered by low confidence."""
        # Track low confidence responses
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=True, confidence=0.3)
        
        should_escalate = model_router.should_escalate("deepseek-chat", confidence=0.3)
        assert should_escalate is True
    
    def test_should_escalate_min_attempts(self, model_router):
        """Test that escalation requires minimum attempts."""
        # Track only 1 failure (below min_attempts threshold)
        model_router.track_response_quality("deepseek-chat", success=False)
        
        should_escalate = model_router.should_escalate("deepseek-chat")
        assert should_escalate is False  # Should not escalate yet
    
    def test_route_task_with_escalation(self, model_router):
        """Test routing with escalation support."""
        # Track poor performance
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=False, confidence=0.3)
        
        model = model_router.route_task_with_escalation(
            "Test task",
            confidence=0.3
        )
        assert model is not None
    
    def test_get_model(self, model_router, mock_llm_client):
        """Test getting model client."""
        client = model_router.get_model("deepseek-chat")
        assert client == mock_llm_client
    
    def test_infer_task_type(self, model_router):
        """Test task type inference."""
        assert model_router._infer_task_type("reason about this") == TaskType.REASONING
        assert model_router._infer_task_type("plan the steps") == TaskType.PLANNING
        assert model_router._infer_task_type("write code") == TaskType.CODE
        assert model_router._infer_task_type("create something") == TaskType.CREATIVE


class TestModelPerformanceMetrics:
    """Unit tests for ModelPerformanceMetrics."""
    
    def test_success_rate(self):
        """Test success rate calculation."""
        metrics = ModelPerformanceMetrics(model_name="test")
        metrics.recent_successes.append("success1")
        metrics.recent_successes.append("success2")
        metrics.recent_errors.append("error1")
        
        assert metrics.success_rate == pytest.approx(2.0 / 3.0)
    
    def test_error_rate(self):
        """Test error rate calculation."""
        metrics = ModelPerformanceMetrics(model_name="test")
        metrics.recent_successes.append("success1")
        metrics.recent_errors.append("error1")
        metrics.recent_errors.append("error2")
        
        assert metrics.error_rate == pytest.approx(2.0 / 3.0)
    
    def test_avg_confidence(self):
        """Test average confidence calculation."""
        metrics = ModelPerformanceMetrics(model_name="test")
        metrics.recent_confidence.append(0.8)
        metrics.recent_confidence.append(0.6)
        metrics.recent_confidence.append(0.7)
        
        assert metrics.avg_confidence == pytest.approx(0.7)
    
    def test_avg_dissonance(self):
        """Test average dissonance calculation."""
        metrics = ModelPerformanceMetrics(model_name="test")
        metrics.recent_dissonance.append(0.2)
        metrics.recent_dissonance.append(0.4)
        metrics.recent_dissonance.append(0.3)
        
        assert metrics.avg_dissonance == pytest.approx(0.3)

