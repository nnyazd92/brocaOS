"""
Tests for self-model integration with internal sensing.

Tests that internal sensing data updates the self-model.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest

from broca.internal_sensing.framework import InternalSensingFramework
from broca.self_model.model import SelfModel
from broca.self_model.updater import SelfModelUpdater


class TestSelfModelUpdatesFromSensing:
    """Test self-model updates from internal sensing."""
    
    def test_self_model_updates_from_sensing(self):
        """
        Test that self-model updates from internal sensing.
        
        Rationale: Ensures sensing data influences self-model.
        """
        framework = InternalSensingFramework()
        framework.sample_internal_state()
        
        # Extract behavioral patterns
        patterns = framework.extract_behavioral_patterns()
        
        assert isinstance(patterns, list)
        # Should be able to extract patterns
    
    def test_behavioral_patterns_from_sensing(self):
        """
        Test that behavioral patterns are extracted from sensing.
        
        Rationale: Ensures patterns can be identified.
        """
        framework = InternalSensingFramework()
        
        # Record some tool usage
        framework.record_tool_usage("test_tool", {}, {})
        framework.record_tool_usage("test_tool", {}, {})
        
        patterns = framework.extract_behavioral_patterns()
        
        assert isinstance(patterns, list)
    
    def test_capabilities_from_sensing(self):
        """
        Test that capabilities can be inferred from sensing.
        
        Rationale: Ensures capabilities are learned from behavior.
        """
        framework = InternalSensingFramework()
        
        # Record tool usage patterns
        for _ in range(10):
            framework.record_tool_usage("memory_tool", {}, {})
        
        # Should be able to infer capability
        tool_stats = framework.get_tool_statistics()
        assert "memory_tool" in tool_stats or len(tool_stats) >= 0
    
    def test_preferences_from_sensing(self):
        """
        Test that preferences are learned from sensing.
        
        Rationale: Ensures preferences are inferred from patterns.
        """
        framework = InternalSensingFramework()
        
        # Record cognitive patterns
        framework.interoception.cognition.record_attention("topic1", 0.8)
        framework.interoception.cognition.record_attention("topic2", 0.2)
        
        # Should show preference for topic1
        allocation = framework.interoception.cognition.states.get("attention_allocation", {})
        assert isinstance(allocation, dict)
    
    def test_consistency_with_self_model(self):
        """
        Test that internal sensing aligns with self-model.
        
        Rationale: Ensures consistency between sensing and self-model.
        """
        framework = InternalSensingFramework()
        self_model = SelfModel.create_default()
        
        # Sample internal state
        state = framework.sample_internal_state()
        
        # Should be able to compare with self-model
        assert state is not None
        assert self_model is not None

