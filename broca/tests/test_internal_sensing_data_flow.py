"""
Tests for internal sensing data flow.

Verifies complete data flow from recording methods through state updates,
sampling, and aggregation.
"""

from __future__ import annotations

import time
from unittest.mock import Mock, patch
import pytest

from broca.internal_sensing.framework import InternalSensingFramework
from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor
from broca.internal_sensing.integrated_interoception import IntegratedInteroception
from broca.world_state.aggregator import WorldStateAggregator


class TestDataFlowTracing:
    """Test complete data flow from recording to aggregation."""
    
    def test_record_confidence_updates_state_immediately(self):
        """
        Test that record_confidence() updates self.states immediately.
        
        Rationale: Verifies data flow step 1 - recording updates state.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially at default
        assert monitor.states["confidence_level"] == 0.5
        
        # Record confidence
        monitor.record_confidence("test1", 0.8)
        
        # State should be updated immediately
        assert monitor.states["confidence_level"] == 0.8
        assert len(monitor._confidence_history) == 1
    
    def test_record_uncertainty_updates_state_immediately(self):
        """
        Test that record_uncertainty() updates self.states immediately.
        
        Rationale: Verifies data flow step 1 - recording updates state.
        """
        monitor = CognitiveStateMonitor()
        
        # Initially at default
        assert monitor.states["uncertainty_tracking"] == 0.0
        
        # Record uncertainty
        monitor.record_uncertainty("test1", 0.6)
        
        # State should be updated immediately
        assert monitor.states["uncertainty_tracking"] == 0.6
        assert len(monitor._uncertainty_history) == 1
    
    def test_sample_cognitive_state_includes_updated_states(self):
        """
        Test that sample_cognitive_state() returns updated states.
        
        Rationale: Verifies data flow step 2 - sampling returns updated states.
        """
        monitor = CognitiveStateMonitor()
        
        # Record data
        monitor.record_confidence("test1", 0.7)
        monitor.record_uncertainty("test1", 0.5)
        
        # Sample state
        sample = monitor.sample_cognitive_state()
        
        # Sample should include updated values
        assert sample["confidence_level"] == 0.7
        assert sample["uncertainty_tracking"] == 0.5
        assert "timestamp" in sample
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_sample_resources_updates_metrics(self, mock_psutil):
        """
        Test that sample_resources() updates self.metrics.
        
        Rationale: Verifies data flow step 2 - sampling updates metrics.
        """
        monitor = ComputationalPhysiologyMonitor()
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.virtual_memory.return_value = Mock(percent=50.0)
        
        # Sample resources
        sample = monitor.sample_resources()
        
        # Metrics should be updated
        assert monitor.metrics["computational_load"] > 0.0
        assert monitor.metrics["memory_pressure"] > 0.0
        assert sample["computational_load"] == monitor.metrics["computational_load"]
        assert "timestamp" in sample
    
    def test_generate_interoceptive_awareness_includes_updated_states(self):
        """
        Test that generate_interoceptive_awareness() includes updated states from all components.
        
        Rationale: Verifies data flow step 3 - integration includes all states.
        """
        interoception = IntegratedInteroception()
        
        # Record data
        interoception.cognition.record_confidence("test1", 0.9)
        interoception.cognition.record_uncertainty("test1", 0.3)
        
        # Generate awareness
        state = interoception.generate_interoceptive_awareness()
        
        # Should include updated cognitive states
        assert "cognitive" in state
        assert state["cognitive"]["confidence_level"] == 0.9
        assert state["cognitive"]["uncertainty_tracking"] == 0.3
        assert "computational" in state
        assert "affective" in state
        assert "predictive" in state
    
    def test_sample_internal_state_returns_unified_state(self):
        """
        Test that sample_internal_state() returns state with updated metrics.
        
        Rationale: Verifies data flow step 4 - framework sampling returns unified state.
        """
        framework = InternalSensingFramework()
        
        # Record data
        framework.interoception.cognition.record_confidence("test1", 0.85)
        
        # Sample state
        state = framework.sample_internal_state()
        
        # Should include updated cognitive state
        assert "cognitive" in state
        assert state["cognitive"]["confidence_level"] == 0.85
    
    def test_get_internal_sensing_state_includes_quality_metrics(self):
        """
        Test that get_internal_sensing_state() includes quality_metrics.
        
        Rationale: Verifies data flow step 5 - aggregator includes quality metrics.
        """
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        # Get internal sensing state
        sensing_state = aggregator.get_internal_sensing_state()
        
        # Should include quality_metrics
        assert sensing_state["available"] is True
        assert "quality_metrics" in sensing_state
        assert "self_awareness_quality" in sensing_state["quality_metrics"]
        assert "interoceptive_accuracy" in sensing_state["quality_metrics"]
    
    def test_aggregate_includes_internal_state(self):
        """
        Test that aggregate() includes internal_state with updated metrics.
        
        Rationale: Verifies data flow step 6 - world state includes internal state.
        """
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        # Record data
        framework.interoception.cognition.record_confidence("test1", 0.75)
        
        # Aggregate world state
        world_state = aggregator.aggregate()
        
        # Should include internal_state with updated metrics
        assert "internal_state" in world_state
        internal_state = world_state["internal_state"]
        assert "cognition" in internal_state
        assert internal_state["cognition"]["confidence_level"] == 0.75
        assert "quality_metrics" in internal_state


class TestEndToEndDataFlow:
    """Test complete end-to-end data flow."""
    
    def test_complete_flow_from_recording_to_world_state(self):
        """
        Test complete flow from recording through aggregation.
        
        Rationale: Verifies entire data flow works correctly end-to-end.
        """
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        # Step 1: Record data
        framework.interoception.cognition.record_confidence("resp1", 0.8)
        framework.interoception.cognition.record_uncertainty("q1", 0.4)
        
        # Step 2: Verify state updated
        assert framework.interoception.cognition.states["confidence_level"] == 0.8
        assert framework.interoception.cognition.states["uncertainty_tracking"] == 0.4
        
        # Step 3: Sample internal state
        state = framework.sample_internal_state()
        assert state["cognitive"]["confidence_level"] == 0.8
        assert state["cognitive"]["uncertainty_tracking"] == 0.4
        
        # Step 4: Get internal sensing state
        sensing_state = aggregator.get_internal_sensing_state()
        assert sensing_state["current_state"]["cognitive"]["confidence_level"] == 0.8
        
        # Step 5: Aggregate world state
        world_state = aggregator.aggregate()
        assert world_state["internal_state"]["cognition"]["confidence_level"] == 0.8
        assert world_state["internal_state"]["cognition"]["uncertainty_tracking"] == 0.4
    
    def test_multiple_recordings_accumulate_in_moving_average(self):
        """
        Test that multiple recordings accumulate in moving average.
        
        Rationale: Verifies moving averages work correctly in complete flow.
        """
        framework = InternalSensingFramework()
        
        # Record multiple values
        framework.interoception.cognition.record_confidence("resp1", 0.6)
        framework.interoception.cognition.record_confidence("resp2", 0.7)
        framework.interoception.cognition.record_confidence("resp3", 0.8)
        
        # State should be average of all values
        assert framework.interoception.cognition.states["confidence_level"] == pytest.approx(0.7, abs=0.01)
        
        # Sample should reflect average
        state = framework.sample_internal_state()
        assert state["cognitive"]["confidence_level"] == pytest.approx(0.7, abs=0.01)
    
    def test_quality_metrics_included_in_complete_flow(self):
        """
        Test that quality metrics are included throughout the flow.
        
        Rationale: Verifies quality metrics flow correctly to world state.
        """
        framework = InternalSensingFramework()
        aggregator = WorldStateAggregator(internal_sensing=framework)
        
        # Generate a prediction cycle (first call generates prediction, second validates it)
        framework.sample_internal_state()  # First call - generates prediction
        framework.sample_internal_state()  # Second call - validates prediction
        
        # Get internal sensing state
        sensing_state = aggregator.get_internal_sensing_state()
        assert "quality_metrics" in sensing_state
        assert "self_awareness_quality" in sensing_state["quality_metrics"]
        
        # Aggregate world state
        world_state = aggregator.aggregate()
        assert "quality_metrics" in world_state["internal_state"]
        assert "self_awareness_quality" in world_state["internal_state"]["quality_metrics"]

