"""
Golden trace replay tests for model router escalation scenarios.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock
from broca.llm.model_router import ModelRouter
from broca.reasoning.feedback_loop import FeedbackMetrics


@pytest.fixture
def golden_traces_dir(tmp_path):
    """Create a temporary directory for golden traces."""
    traces_dir = tmp_path / "golden_traces"
    traces_dir.mkdir()
    return traces_dir


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


class TestGoldenTraceReplay:
    """Golden trace replay tests for model router."""
    
    def test_escalation_scenario_low_success_rate(self, model_router, golden_traces_dir):
        """Test golden trace for escalation due to low success rate."""
        # Create a golden trace
        trace = {
            "scenario": "escalation_low_success_rate",
            "inputs": [
                {"model": "deepseek-chat", "success": False, "confidence": 0.6},
                {"model": "deepseek-chat", "success": False, "confidence": 0.5},
                {"model": "deepseek-chat", "success": False, "confidence": 0.4},
                {"model": "deepseek-chat", "success": True, "confidence": 0.7},
                {"model": "deepseek-chat", "success": False, "confidence": 0.3},
            ],
            "expected_outputs": [
                {"should_escalate": True, "next_model": "gpt-5-nano"}
            ]
        }
        
        trace_file = golden_traces_dir / "escalation_low_success.json"
        with open(trace_file, 'w') as f:
            json.dump(trace, f, indent=2)
        
        # Replay trace
        for input_data in trace["inputs"]:
            model_router.track_response_quality(
                input_data["model"],
                success=input_data["success"],
                confidence=input_data["confidence"]
            )
        
        # Verify escalation
        should_escalate = model_router.should_escalate("deepseek-chat")
        expected = trace["expected_outputs"][0]
        
        assert should_escalate == expected["should_escalate"]
        
        if should_escalate:
            escalated = model_router.escalate_model()
            assert escalated == expected["next_model"]
    
    def test_escalation_scenario_low_confidence(self, model_router, golden_traces_dir):
        """Test golden trace for escalation due to low confidence."""
        trace = {
            "scenario": "escalation_low_confidence",
            "inputs": [
                {"model": "deepseek-chat", "success": True, "confidence": 0.3},
                {"model": "deepseek-chat", "success": True, "confidence": 0.4},
                {"model": "deepseek-chat", "success": True, "confidence": 0.35},
            ],
            "expected_outputs": [
                {"should_escalate": True, "next_model": "gpt-5-nano"}
            ]
        }
        
        trace_file = golden_traces_dir / "escalation_low_confidence.json"
        with open(trace_file, 'w') as f:
            json.dump(trace, f, indent=2)
        
        # Replay trace
        for input_data in trace["inputs"]:
            model_router.track_response_quality(
                input_data["model"],
                success=input_data["success"],
                confidence=input_data["confidence"]
            )
        
        # Verify escalation
        should_escalate = model_router.should_escalate(
            "deepseek-chat",
            confidence=0.35
        )
        expected = trace["expected_outputs"][0]
        
        assert should_escalate == expected["should_escalate"]
    
    def test_escalation_scenario_feedback_metrics(self, model_router, golden_traces_dir):
        """Test golden trace for escalation with feedback metrics."""
        trace = {
            "scenario": "escalation_feedback_metrics",
            "inputs": [
                {
                    "feedback_metrics": {
                        "success_rate": 0.5,
                        "error_rate": 0.4,
                        "avg_cycle_duration": 1.0
                    },
                    "confidence": 0.6,
                    "dissonance": 0.4
                }
            ],
            "expected_outputs": [
                {"should_escalate": True}
            ]
        }
        
        trace_file = golden_traces_dir / "escalation_feedback.json"
        with open(trace_file, 'w') as f:
            json.dump(trace, f, indent=2)
        
        # Replay trace
        input_data = trace["inputs"][0]
        feedback_metrics = FeedbackMetrics(
            window_size=100,
            success_rate=input_data["feedback_metrics"]["success_rate"],
            error_rate=input_data["feedback_metrics"]["error_rate"],
            avg_cycle_duration=input_data["feedback_metrics"]["avg_cycle_duration"]
        )
        
        # Track some requests
        for _ in range(5):
            model_router.track_response_quality("deepseek-chat", success=True)
        
        should_escalate = model_router.should_escalate(
            "deepseek-chat",
            feedback_metrics=feedback_metrics,
            confidence=input_data["confidence"],
            dissonance=input_data["dissonance"]
        )
        
        expected = trace["expected_outputs"][0]
        assert should_escalate == expected["should_escalate"]
    
    def test_no_escalation_scenario_good_performance(self, model_router, golden_traces_dir):
        """Test golden trace for no escalation when performance is good."""
        trace = {
            "scenario": "no_escalation_good_performance",
            "inputs": [
                {"model": "deepseek-chat", "success": True, "confidence": 0.8},
                {"model": "deepseek-chat", "success": True, "confidence": 0.85},
                {"model": "deepseek-chat", "success": True, "confidence": 0.9},
            ],
            "expected_outputs": [
                {"should_escalate": False}
            ]
        }
        
        trace_file = golden_traces_dir / "no_escalation_good.json"
        with open(trace_file, 'w') as f:
            json.dump(trace, f, indent=2)
        
        # Replay trace
        for input_data in trace["inputs"]:
            model_router.track_response_quality(
                input_data["model"],
                success=input_data["success"],
                confidence=input_data["confidence"]
            )
        
        # Verify no escalation
        should_escalate = model_router.should_escalate("deepseek-chat")
        expected = trace["expected_outputs"][0]
        
        assert should_escalate == expected["should_escalate"]

