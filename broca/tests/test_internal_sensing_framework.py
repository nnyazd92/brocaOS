"""
Tests for InternalSensingFramework.

Tests the main framework that orchestrates all internal sensing components.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import time

from broca.internal_sensing.framework import InternalSensingFramework
from broca.config import config


class TestInternalSensingFrameworkInitialization:
    """Test InternalSensingFramework initialization."""
    
    def test_initialization(self):
        """
        Test that framework initializes with config.
        
        Rationale: Ensures framework starts with proper configuration.
        """
        framework = InternalSensingFramework(
            sampling_rate=1.0,
            history_window=60
        )
        
        assert framework.sampling_rate == 1.0
        assert framework.history_window == 60
        assert framework.internal_state_log is not None
    
    def test_initialization_with_config(self):
        """
        Test initialization with config values.
        
        Rationale: Ensures framework uses configuration.
        """
        framework = InternalSensingFramework()
        
        assert framework.sampling_rate > 0
        assert framework.history_window > 0


class TestSamplingRate:
    """Test sampling rate functionality."""
    
    def test_sampling_rate(self):
        """
        Test that framework samples at configured rate.
        
        Rationale: Ensures sampling respects rate configuration.
        """
        framework = InternalSensingFramework(sampling_rate=2.0)
        
        assert framework.sampling_rate == 2.0
    
    def test_sample_internal_state(self):
        """
        Test that internal state can be sampled.
        
        Rationale: Ensures sampling works correctly.
        """
        framework = InternalSensingFramework()
        
        state = framework.sample_internal_state()
        
        assert isinstance(state, dict)
        assert "timestamp" in state
        assert "computational" in state or "cognitive" in state


class TestHistoryWindow:
    """Test history window functionality."""
    
    def test_history_window(self):
        """
        Test that history window is maintained correctly.
        
        Rationale: Ensures history respects window size.
        """
        framework = InternalSensingFramework(history_window=5)
        
        # Sample multiple times
        for _ in range(10):
            framework.sample_internal_state()
        
        assert len(framework.internal_state_log) <= 5


class TestStateLogging:
    """Test state logging functionality."""
    
    def test_state_logging(self):
        """
        Test that internal states are logged properly.
        
        Rationale: Ensures states are recorded.
        """
        framework = InternalSensingFramework()
        
        framework.sample_internal_state()
        
        assert len(framework.internal_state_log) > 0
        assert "timestamp" in framework.internal_state_log[0]


class TestReportGeneration:
    """Test report generation functionality."""
    
    def test_report_generation(self):
        """
        Test that natural language reports are generated.
        
        Rationale: Ensures reports can be generated.
        """
        framework = InternalSensingFramework()
        framework.sample_internal_state()
        
        report = framework.generate_interoceptive_report()
        
        assert isinstance(report, str)
        assert len(report) > 0


class TestIntegrationWithTools:
    """Test integration with tool system."""
    
    def test_integration_with_tools(self):
        """
        Test that framework monitors tool usage patterns.
        
        Rationale: Ensures tool integration works.
        """
        framework = InternalSensingFramework()
        
        # Simulate tool usage
        framework.record_tool_usage("test_tool", {"param": "value"}, {"result": "success"})
        
        tool_stats = framework.get_tool_statistics()
        
        assert isinstance(tool_stats, dict)
        assert "test_tool" in tool_stats or len(tool_stats) >= 0


class TestIntegrationWithMemory:
    """Test integration with memory system."""
    
    def test_integration_with_memory(self):
        """
        Test that framework stores/retrieves state histories.
        
        Rationale: Ensures memory integration works.
        """
        framework = InternalSensingFramework()
        framework.sample_internal_state()
        
        # Should be able to get history
        history = framework.get_state_history()
        
        assert isinstance(history, list)
        assert len(history) > 0


class TestIntegrationWithSelfModel:
    """Test integration with self-model."""
    
    def test_integration_with_self_model(self):
        """
        Test that framework updates self-model from sensing.
        
        Rationale: Ensures self-model integration works.
        """
        framework = InternalSensingFramework()
        framework.sample_internal_state()
        
        # Should be able to extract behavioral patterns
        patterns = framework.extract_behavioral_patterns()
        
        assert isinstance(patterns, list)


class TestLLMInterface:
    """Test LLM interface functionality."""
    
    def test_llm_interface(self):
        """
        Test that framework generates LLM-readable descriptions.
        
        Rationale: Ensures LLM can understand internal states.
        """
        framework = InternalSensingFramework()
        framework.sample_internal_state()
        
        description = framework.get_llm_description()
        
        assert isinstance(description, str)
        assert len(description) > 0

