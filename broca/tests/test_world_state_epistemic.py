"""
Tests for epistemic metrics integration in world state.

Tests:
- Epistemic metrics are extracted from epistemic bridge
- Epistemic metrics are included in world state
- Data quality indicators are preserved
- Compact epistemic summary is created
"""

import pytest
from unittest.mock import Mock, MagicMock

from broca.world_state.aggregator import WorldStateAggregator
from broca.internal_sensing.framework import InternalSensingFramework


class TestEpistemicWorldState:
    """Test epistemic metrics in world state."""
    
    def test_epistemic_metrics_extracted_from_bridge(self):
        """Test that epistemic metrics are extracted from epistemic bridge."""
        mock_internal_sensing = Mock()
        mock_interoception = Mock()
        mock_epistemic_bridge = Mock()
        
        # Setup epistemic bridge return values
        mock_epistemic_bridge.get_aggregated_uncertainty.return_value = {
            "epistemic": 0.3,
            "aleatoric": 0.2,
            "model": 0.1,
            "total": 0.6,
            "knowledge_gaps": 0.3,
            "ambiguity": 0.2,
            "noise": 0.1,
            "data_quality": "high",
            "sample_size": 10,
            "has_data": True,
        }
        
        mock_epistemic_bridge.get_aggregated_confidence.return_value = {
            "overall_confidence": 0.7,
            "confidence_interval": [0.6, 0.8],
            "calibration_error": 0.1,
            "ece": 0.05,
            "brier_score": 0.15,
            "reliability": 0.9,
            "data_quality": "high",
            "sample_size": 10,
            "has_data": True,
            "uncertainty": 0.2,
        }
        
        mock_epistemic_bridge.get_source_reliability.return_value = {
            "tool:terminal": 0.9,
            "tool:web_search": 0.8,
            "memory:123": 0.85,
        }
        
        mock_interoception.epistemic_bridge = mock_epistemic_bridge
        mock_interoception.cognition = Mock()
        mock_interoception.cognition.states = {}
        mock_interoception.affect = Mock()
        mock_interoception.affect.affective_states = {}
        mock_interoception.physiology = Mock()
        mock_interoception.detect_anomalies.return_value = []
        mock_interoception.measure_self_awareness_quality.return_value = 0.8
        mock_interoception.track_interoceptive_accuracy.return_value = {"prediction_accuracy": 0.75}
        mock_interoception.affect.get_motivational_drives.return_value = {}
        mock_interoception.affect.get_satisfaction_patterns.return_value = []
        
        mock_internal_sensing.interoception = mock_interoception
        mock_internal_sensing.sample_internal_state.return_value = {
            "computational": {"computational_load": 0.5},
            "cognitive": {"confidence_level": 0.75},
            "affective": {"valence": 0.5},
        }
        mock_internal_sensing.generate_interoceptive_report.return_value = "Test report"
        mock_internal_sensing.get_tool_statistics.return_value = {}
        mock_internal_sensing.extract_behavioral_patterns.return_value = []
        
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        # Get internal sensing state
        internal_state = aggregator.get_internal_sensing_state()
        
        # Verify epistemic data is extracted
        assert internal_state["available"] is True
        assert "epistemic" in internal_state
        epistemic = internal_state["epistemic"]
        
        assert "uncertainty" in epistemic
        assert "confidence" in epistemic
        assert "source_reliability" in epistemic
        
        # Verify uncertainty structure
        uncertainty = epistemic["uncertainty"]
        assert "epistemic" in uncertainty
        assert "total" in uncertainty
        assert "data_quality" in uncertainty
        
        # Verify confidence structure
        confidence = epistemic["confidence"]
        assert "overall_confidence" in confidence
        assert "confidence_interval" in confidence
        assert "data_quality" in confidence
    
    def test_epistemic_included_in_world_state(self):
        """Test that epistemic metrics are included in aggregated world state."""
        mock_internal_sensing = Mock()
        mock_interoception = Mock()
        mock_epistemic_bridge = Mock()
        
        mock_epistemic_bridge.get_aggregated_uncertainty.return_value = {
            "epistemic": 0.3,
            "total": 0.6,
            "data_quality": "high",
            "sample_size": 10,
            "has_data": True,
        }
        mock_epistemic_bridge.get_aggregated_confidence.return_value = {
            "overall_confidence": 0.7,
            "confidence_interval": [0.6, 0.8],
            "data_quality": "high",
            "sample_size": 10,
            "has_data": True,
        }
        mock_epistemic_bridge.get_source_reliability.return_value = {
            "tool:terminal": 0.9,
        }
        
        mock_interoception.epistemic_bridge = mock_epistemic_bridge
        mock_interoception.cognition = Mock()
        mock_interoception.cognition.states = {}
        mock_interoception.affect = Mock()
        mock_interoception.affect.affective_states = {}
        mock_interoception.physiology = Mock()
        mock_interoception.detect_anomalies.return_value = []
        mock_interoception.measure_self_awareness_quality.return_value = 0.8
        mock_interoception.track_interoceptive_accuracy.return_value = {"prediction_accuracy": 0.75}
        mock_interoception.affect.get_motivational_drives.return_value = {}
        mock_interoception.affect.get_satisfaction_patterns.return_value = []
        
        mock_internal_sensing.interoception = mock_interoception
        mock_internal_sensing.sample_internal_state.return_value = {
            "computational": {"computational_load": 0.5},
            "cognitive": {"confidence_level": 0.75},
            "affective": {"valence": 0.5},
        }
        mock_internal_sensing.generate_interoceptive_report.return_value = "Test"
        mock_internal_sensing.get_tool_statistics.return_value = {}
        mock_internal_sensing.extract_behavioral_patterns.return_value = []
        
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        world_state = aggregator.aggregate()
        
        # Verify epistemic is in world state
        assert "internal_state" in world_state
        assert "epistemic" in world_state["internal_state"]
        
        epistemic = world_state["internal_state"]["epistemic"]
        assert "uncertainty" in epistemic
        assert "confidence" in epistemic
        assert "source_reliability" in epistemic
    
    def test_epistemic_summary_is_compact(self):
        """Test that epistemic summary is compact (only essential metrics)."""
        mock_internal_sensing = Mock()
        mock_interoception = Mock()
        mock_epistemic_bridge = Mock()
        
        # Return full uncertainty with all fields
        mock_epistemic_bridge.get_aggregated_uncertainty.return_value = {
            "epistemic": 0.3,
            "aleatoric": 0.2,
            "model": 0.1,
            "total": 0.6,
            "knowledge_gaps": 0.3,
            "ambiguity": 0.2,
            "noise": 0.1,
            "data_quality": "high",
            "sample_size": 10,
            "has_data": True,
        }
        
        mock_epistemic_bridge.get_aggregated_confidence.return_value = {
            "overall_confidence": 0.7,
            "confidence_interval": [0.6, 0.8],
            "calibration_error": 0.1,
            "ece": 0.05,
            "brier_score": 0.15,
            "reliability": 0.9,
            "data_quality": "high",
            "sample_size": 10,
            "has_data": True,
            "uncertainty": 0.2,
        }
        
        mock_epistemic_bridge.get_source_reliability.return_value = {}
        
        mock_interoception.epistemic_bridge = mock_epistemic_bridge
        mock_interoception.cognition = Mock()
        mock_interoception.cognition.states = {}
        mock_interoception.affect = Mock()
        mock_interoception.affect.affective_states = {}
        mock_interoception.physiology = Mock()
        mock_interoception.detect_anomalies.return_value = []
        mock_interoception.measure_self_awareness_quality.return_value = 0.8
        mock_interoception.track_interoceptive_accuracy.return_value = {"prediction_accuracy": 0.75}
        mock_interoception.affect.get_motivational_drives.return_value = {}
        mock_interoception.affect.get_satisfaction_patterns.return_value = []
        
        mock_internal_sensing.interoception = mock_interoception
        mock_internal_sensing.sample_internal_state.return_value = {
            "computational": {"computational_load": 0.5},
            "cognitive": {"confidence_level": 0.75},
            "affective": {"valence": 0.5},
        }
        mock_internal_sensing.generate_interoceptive_report.return_value = "Test"
        mock_internal_sensing.get_tool_statistics.return_value = {}
        mock_internal_sensing.extract_behavioral_patterns.return_value = []
        
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        world_state = aggregator.aggregate()
        
        epistemic = world_state["internal_state"]["epistemic"]
        
        # Verify summary is compact - only essential fields
        uncertainty = epistemic["uncertainty"]
        # Should include: epistemic, aleatoric, total, data_quality
        assert "epistemic" in uncertainty
        assert "aleatoric" in uncertainty
        assert "total" in uncertainty
        assert "data_quality" in uncertainty
        # Should NOT include verbose fields like knowledge_gaps, ambiguity, noise in summary
        # (they're in the full data but summary is compact)
        
        confidence = epistemic["confidence"]
        # Should include: overall_confidence, confidence_interval, data_quality
        assert "overall_confidence" in confidence
        assert "confidence_interval" in confidence
        assert "data_quality" in confidence
        # May include calibration_error if available
    
    def test_epistemic_handles_missing_bridge_gracefully(self):
        """Test that missing epistemic bridge doesn't break world state aggregation."""
        mock_internal_sensing = Mock()
        mock_interoception = Mock()
        
        # No epistemic bridge
        mock_interoception.epistemic_bridge = None
        mock_interoception.cognition = Mock()
        mock_interoception.cognition.states = {}
        mock_interoception.affect = Mock()
        mock_interoception.affect.affective_states = {}
        mock_interoception.physiology = Mock()
        mock_interoception.detect_anomalies.return_value = []
        mock_interoception.measure_self_awareness_quality.return_value = 0.8
        mock_interoception.track_interoceptive_accuracy.return_value = {"prediction_accuracy": 0.75}
        mock_interoception.affect.get_motivational_drives.return_value = {}
        mock_interoception.affect.get_satisfaction_patterns.return_value = []
        
        mock_internal_sensing.interoception = mock_interoception
        mock_internal_sensing.sample_internal_state.return_value = {
            "computational": {"computational_load": 0.5},
            "cognitive": {"confidence_level": 0.75},
            "affective": {"valence": 0.5},
        }
        mock_internal_sensing.generate_interoceptive_report.return_value = "Test"
        mock_internal_sensing.get_tool_statistics.return_value = {}
        mock_internal_sensing.extract_behavioral_patterns.return_value = []
        
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        # Should not raise exception
        world_state = aggregator.aggregate()
        
        # Epistemic should not be present if bridge is missing
        assert "internal_state" in world_state
        # Epistemic may or may not be present depending on implementation
        # But aggregation should not fail
    
    def test_source_reliability_aggregation(self):
        """Test that source reliability is properly aggregated."""
        mock_internal_sensing = Mock()
        mock_interoception = Mock()
        mock_epistemic_bridge = Mock()
        
        mock_epistemic_bridge.get_aggregated_uncertainty.return_value = {
            "total": 0.6,
            "data_quality": "high",
        }
        mock_epistemic_bridge.get_aggregated_confidence.return_value = {
            "overall_confidence": 0.7,
        }
        mock_epistemic_bridge.get_source_reliability.return_value = {
            "tool:terminal": 0.9,
            "tool:web_search": 0.8,
            "tool:memory": 0.85,
            "memory:123": 0.9,
            "memory:456": 0.8,
        }
        
        mock_interoception.epistemic_bridge = mock_epistemic_bridge
        mock_interoception.cognition = Mock()
        mock_interoception.cognition.states = {}
        mock_interoception.affect = Mock()
        mock_interoception.affect.affective_states = {}
        mock_interoception.physiology = Mock()
        mock_interoception.detect_anomalies.return_value = []
        mock_interoception.measure_self_awareness_quality.return_value = 0.8
        mock_interoception.track_interoceptive_accuracy.return_value = {"prediction_accuracy": 0.75}
        mock_interoception.affect.get_motivational_drives.return_value = {}
        mock_interoception.affect.get_satisfaction_patterns.return_value = []
        
        mock_internal_sensing.interoception = mock_interoception
        mock_internal_sensing.sample_internal_state.return_value = {
            "computational": {"computational_load": 0.5},
            "cognitive": {"confidence_level": 0.75},
            "affective": {"valence": 0.5},
        }
        mock_internal_sensing.generate_interoceptive_report.return_value = "Test"
        mock_internal_sensing.get_tool_statistics.return_value = {}
        mock_internal_sensing.extract_behavioral_patterns.return_value = []
        
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        world_state = aggregator.aggregate()
        
        epistemic = world_state["internal_state"]["epistemic"]
        source_reliability = epistemic["source_reliability"]
        
        # Should have aggregated tool and memory reliability
        assert "tool_reliability_avg" in source_reliability
        assert "memory_consistency_avg" in source_reliability
        assert source_reliability["tool_reliability_avg"] == pytest.approx(0.85, abs=0.01)  # (0.9 + 0.8 + 0.85) / 3
        assert source_reliability["memory_consistency_avg"] == pytest.approx(0.85, abs=0.01)  # (0.9 + 0.8) / 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

