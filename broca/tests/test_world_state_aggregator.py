"""
Tests for world state aggregator.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from broca.world_state.aggregator import WorldStateAggregator
from broca.self_model.model import SelfModel
from broca.internal_sensing.framework import InternalSensingFramework


class TestWorldStateAggregator:
    """Test world state aggregator functionality."""
    
    @pytest.fixture
    def mock_internal_sensing(self):
        """Create a mock internal sensing framework."""
        mock = Mock(spec=InternalSensingFramework)
        # Mock interoception with all sub-components
        mock.interoception = Mock()
        mock.interoception.physiology = Mock()
        mock.interoception.cognition = Mock()
        mock.interoception.affect = Mock()
        mock.interoception.affect.get_motivational_drives.return_value = {"exploration": 0.7, "completion": 0.5}
        mock.interoception.affect.get_satisfaction_patterns.return_value = [
            {"task_id": "task1", "type": "satisfaction", "level": 0.8, "timestamp": 1234567890}
        ]
        mock.interoception.cognition._get_reasoning_patterns.return_value = [
            {"type": "heuristic", "name": "pattern1", "timestamp": 1234567890}
        ]
        mock.interoception.detect_anomalies.return_value = [
            {"type": "cognitive_state_change", "metric": "confidence_level", "change": 0.2}
        ]
        mock.interoception.measure_self_awareness_quality.return_value = 0.85
        mock.interoception.track_interoceptive_accuracy.return_value = {
            "prediction_accuracy": 0.75,
            "overall_accuracy": 0.75
        }
        
        mock.sample_internal_state.return_value = {
            "computational": {"metrics": {"processing_latency": 0.5}},
            "cognitive": {"metrics": {"confidence": 0.8, "uncertainty": 0.2}},
            "affective": {"valence": 0.6, "arousal": 0.4},
            "predictive": {
                "resources": {"cpu_load": 0.3},
                "cognitive": {"confidence": 0.85},
                "affective": {"valence": 0.65},
                "error_probability": 0.1
            }
        }
        mock.generate_interoceptive_report.return_value = "Current state: stable"
        mock.get_tool_statistics.return_value = {"memory": 5, "terminal": 3}
        mock.extract_behavioral_patterns.return_value = [
            {"type": "tool_usage", "tool": "memory", "frequency": 5}
        ]
        return mock
    
    @pytest.fixture
    def mock_self_model(self):
        """Create a mock self-model."""
        return SelfModel(
            capabilities=["Test capability 1", "Test capability 2"],
            knowledge_boundaries={"test_boundary": "value"},
            constraints={"test_constraint": "value"},
            metadata={"version": 1, "last_updated": "2024-01-01T00:00:00Z"},
        )
    
    @pytest.fixture
    def mock_tool_registry(self):
        """Create a mock tool registry."""
        mock = Mock()
        tool1 = Mock()
        tool1.name = "memory"
        tool2 = Mock()
        tool2.name = "terminal"
        mock.list_tools.return_value = [tool1, tool2]
        return mock
    
    def test_init_with_all_components(self, mock_internal_sensing, mock_self_model, mock_tool_registry):
        """Test initializing aggregator with all components."""
        aggregator = WorldStateAggregator(
            internal_sensing=mock_internal_sensing,
            self_model=mock_self_model,
            tool_registry=mock_tool_registry,
        )
        
        assert aggregator.internal_sensing is mock_internal_sensing
        assert aggregator.self_model is mock_self_model
        assert aggregator.tool_registry is mock_tool_registry
    
    def test_init_with_none_components(self):
        """Test initializing aggregator with no components."""
        aggregator = WorldStateAggregator()
        
        assert aggregator.internal_sensing is None
        assert aggregator.self_model is None
        assert aggregator.tool_registry is None
    
    def test_aggregate_with_all_components(self, mock_internal_sensing, mock_self_model, mock_tool_registry):
        """Test aggregating world state with all components."""
        aggregator = WorldStateAggregator(
            internal_sensing=mock_internal_sensing,
            self_model=mock_self_model,
            tool_registry=mock_tool_registry,
        )
        
        world_state = aggregator.aggregate()
        
        assert "timestamp" in world_state
        # Should have clean hierarchical structure without "sections" wrapper
        assert "sections" not in world_state
        # All available sections should be present at top level
        assert "system" in world_state
        assert "self_model" in world_state
        assert "internal_state" in world_state
        assert "tools_registry" in world_state
        # Tools should be included on first call (hash changed from None)
        assert "tools" in world_state
        # Project should NOT be in world state (tool is now callable, not in aggregator)
        assert "project" not in world_state
    
    def test_aggregate_with_no_components(self):
        """Test aggregating world state with no components."""
        aggregator = WorldStateAggregator()
        
        world_state = aggregator.aggregate()
        
        assert "timestamp" in world_state
        # Should have clean hierarchical structure without "sections" wrapper
        assert "sections" not in world_state
        # System info should always be present
        assert "system" in world_state
        # Unavailable sections should be omitted (not present with "available": False)
        assert "internal_state" not in world_state
        assert "self_model" not in world_state
        assert "project" not in world_state
        assert "tools" not in world_state
    
    def test_get_internal_sensing_state(self, mock_internal_sensing):
        """Test getting internal sensing state with all new fields."""
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        state = aggregator.get_internal_sensing_state()
        
        # State should have "available" flag for internal use, but won't be in final aggregate
        assert state["available"] is True
        assert "current_state" in state
        assert "interoceptive_report" in state
        assert "tool_statistics" in state
        
        # New fields should be included
        assert "predictive" in state
        assert "behavioral_patterns" in state
        assert "anomalies" in state
        assert "quality_metrics" in state
        assert "motivational_state" in state
        assert "reasoning_patterns" in state
        
        # Verify predictive data
        assert state["predictive"]["resources"]["cpu_load"] == 0.3
        assert state["predictive"]["error_probability"] == 0.1
        
        # Verify behavioral patterns
        assert len(state["behavioral_patterns"]) == 1
        assert state["behavioral_patterns"][0]["type"] == "tool_usage"
        
        # Verify anomalies
        assert len(state["anomalies"]) == 1
        assert state["anomalies"][0]["type"] == "cognitive_state_change"
        
        # Verify quality metrics
        assert state["quality_metrics"]["self_awareness_quality"] == 0.85
        assert "prediction_accuracy" in state["quality_metrics"]["interoceptive_accuracy"]
        
        # Verify motivational state
        assert "drives" in state["motivational_state"]
        assert state["motivational_state"]["drives"]["exploration"] == 0.7
        assert "satisfaction_patterns" in state["motivational_state"]
        
        # Verify reasoning patterns
        assert len(state["reasoning_patterns"]) == 1
        assert state["reasoning_patterns"][0]["type"] == "heuristic"
        
        mock_internal_sensing.sample_internal_state.assert_called_once()
        mock_internal_sensing.generate_interoceptive_report.assert_called_once()
        mock_internal_sensing.get_tool_statistics.assert_called_once()
        mock_internal_sensing.extract_behavioral_patterns.assert_called_once()
        mock_internal_sensing.interoception.detect_anomalies.assert_called_once()
        mock_internal_sensing.interoception.measure_self_awareness_quality.assert_called_once()
        mock_internal_sensing.interoception.track_interoceptive_accuracy.assert_called_once()
    
    def test_get_internal_sensing_state_none(self):
        """Test getting internal sensing state when not available."""
        aggregator = WorldStateAggregator()
        
        state = aggregator.get_internal_sensing_state()
        
        # Internal method still returns "available" flag for aggregator logic
        assert state["available"] is False
    
    def test_get_internal_sensing_state_error(self):
        """Test getting internal sensing state when error occurs."""
        mock_sensing = Mock()
        mock_sensing.sample_internal_state.side_effect = Exception("Test error")
        
        aggregator = WorldStateAggregator(internal_sensing=mock_sensing)
        
        state = aggregator.get_internal_sensing_state()
        
        assert state["available"] is False
        assert "error" in state
    
    def test_get_self_model_state(self, mock_self_model):
        """Test getting self-model state (defaults to mild reduction)."""
        aggregator = WorldStateAggregator(self_model=mock_self_model)
        
        state = aggregator.get_self_model_state()
        
        # State should have "available" flag for internal use
        assert state["available"] is True
        assert "summary" in state
        assert "capabilities" in state
        # With mild reduction (default), capabilities are strings, not full dicts
        assert isinstance(state["capabilities"], list)
        # The mock_self_model has string capabilities, so they should match
        assert len(state["capabilities"]) == len(mock_self_model.capabilities)
        assert "constraints" in state
    
    def test_get_self_model_state_none(self):
        """Test getting self-model state when not available."""
        aggregator = WorldStateAggregator()
        
        state = aggregator.get_self_model_state()
        
        # Internal method still returns "available" flag for aggregator logic
        assert state["available"] is False
    
    def test_get_system_info(self):
        """Test getting system information."""
        aggregator = WorldStateAggregator()
        
        info = aggregator.get_system_info()
        
        # System info should always be available
        assert info["available"] is True
        assert "current_datetime" in info
        assert "current_date" in info
        assert "current_time" in info
        assert "platform" in info
        assert "python_version" in info
        assert "working_directory" in info
    
    def test_get_tools_info(self, mock_tool_registry):
        """Test getting tools information."""
        aggregator = WorldStateAggregator(tool_registry=mock_tool_registry)
        
        info = aggregator.get_tools_info()
        
        # State should have "available" flag for internal use
        assert info["available"] is True
        assert "tools_registry" in info
        assert "version" in info["tools_registry"]
        assert "hash" in info["tools_registry"]
        # First call should include tools
        assert "tools" in info
        assert info["tools"]["count"] == 2
        assert "memory" in info["tools"]["names"]
        assert "terminal" in info["tools"]["names"]
    
    def test_get_tools_info_none(self):
        """Test getting tools information when not available."""
        aggregator = WorldStateAggregator()
        
        info = aggregator.get_tools_info()
        
        # Internal method still returns "available" flag for aggregator logic
        assert info["available"] is False
    
    def test_aggregate_partial_components(self, mock_self_model, mock_tool_registry):
        """Test aggregating with only some components."""
        aggregator = WorldStateAggregator(
            self_model=mock_self_model,
            tool_registry=mock_tool_registry,
        )
        
        world_state = aggregator.aggregate()
        
        # Should have clean hierarchical structure without "sections" wrapper
        assert "sections" not in world_state
        # Only available sections should be present
        assert "system" in world_state  # Always available
        assert "self_model" in world_state
        assert "tools" in world_state
        # Unavailable sections should be omitted
        assert "internal_state" not in world_state
        assert "project" not in world_state
    
    def test_aggregate_includes_all_internal_sensing_fields(self, mock_internal_sensing):
        """Test that aggregated world state includes all new internal sensing fields."""
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        world_state = aggregator.aggregate()
        
        # internal_state should be present
        assert "internal_state" in world_state
        assert world_state["internal_state"] is not None
        
        internal_state = world_state["internal_state"]
        
        # Core fields should be present
        assert "interoceptive_report" in internal_state
        assert "tool_statistics" in internal_state
        
        # New fields should be included
        assert "predictive" in internal_state
        assert "behavioral_patterns" in internal_state
        assert "anomalies" in internal_state
        assert "quality_metrics" in internal_state
        assert "motivational_state" in internal_state
        assert "reasoning_patterns" in internal_state
        
        # Verify predictive data structure
        assert "resources" in internal_state["predictive"]
        assert "error_probability" in internal_state["predictive"]
        
        # Verify quality metrics structure
        assert "self_awareness_quality" in internal_state["quality_metrics"]
        assert "interoceptive_accuracy" in internal_state["quality_metrics"]
        
        # Verify motivational state structure
        assert "drives" in internal_state["motivational_state"]
        assert "satisfaction_patterns" in internal_state["motivational_state"]
    
    def test_aggregate_omits_empty_internal_sensing_fields(self):
        """Test that empty internal sensing fields are omitted from world state."""
        mock_empty = Mock(spec=InternalSensingFramework)
        mock_empty.interoception = Mock()
        mock_empty.interoception.physiology = Mock()
        mock_empty.interoception.cognition = Mock()
        mock_empty.interoception.affect = Mock()
        mock_empty.interoception.affect.get_motivational_drives.return_value = {}
        mock_empty.interoception.affect.get_satisfaction_patterns.return_value = []
        mock_empty.interoception.cognition._get_reasoning_patterns.return_value = []
        mock_empty.interoception.detect_anomalies.return_value = []
        mock_empty.interoception.measure_self_awareness_quality.return_value = None
        mock_empty.interoception.track_interoceptive_accuracy.return_value = {}
        
        mock_empty.sample_internal_state.return_value = {
            "computational": {"metrics": {"processing_latency": 0.5}},
            "cognitive": {"metrics": {"confidence": 0.8}},
            "affective": {"valence": 0.6},
            # No predictive field
        }
        mock_empty.generate_interoceptive_report.return_value = "Current state: stable"
        mock_empty.get_tool_statistics.return_value = {}
        mock_empty.extract_behavioral_patterns.return_value = []
        
        aggregator = WorldStateAggregator(internal_sensing=mock_empty)
        world_state = aggregator.aggregate()
        
        internal_state = world_state["internal_state"]
        
        # Core fields should still be present
        assert "interoceptive_report" in internal_state
        assert "tool_statistics" in internal_state
        
        # Empty fields should be omitted
        assert "predictive" not in internal_state
        assert "behavioral_patterns" not in internal_state
        assert "anomalies" not in internal_state
        assert "quality_metrics" not in internal_state
        assert "motivational_state" not in internal_state
        assert "reasoning_patterns" not in internal_state
    
    def test_aggregate_includes_valence(self, mock_internal_sensing):
        """Test that valence appears in world state affect section."""
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        world_state = aggregator.aggregate()
        
        # internal_state should be present
        assert "internal_state" in world_state
        assert "affect" in world_state["internal_state"]
        
        # Valence should be in affect section
        affect = world_state["internal_state"]["affect"]
        assert "valence" in affect
        assert isinstance(affect["valence"], float)
        assert -1.0 <= affect["valence"] <= 1.0
    
    def test_valence_in_system_prompt(self, mock_internal_sensing):
        """Test that valence appears in formatted world state."""
        from broca.world_state.formatter import WorldStateFormatter
        
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        formatter = WorldStateFormatter()
        
        world_state = aggregator.aggregate()
        formatted = formatter.format(world_state)
        
        # Formatted JSON should contain valence
        assert "valence" in formatted
        # Should be in affect section
        assert '"affect"' in formatted or '"valence"' in formatted


class TestSelfModelReduction:
    """Test self-model reduction levels."""
    
    @pytest.fixture
    def mock_self_model_with_sources(self):
        """Create a self-model with source metadata."""
        from broca.self_model.source import Source
        return SelfModel(
            capabilities=[
                {"text": "Test capability 1", "source": Source.system_default().to_dict()},
                {"text": "Test capability 2", "source": Source.from_memory(memory_id=123).to_dict()},
            ],
            knowledge_boundaries={
                "test_boundary": {
                    "value": "boundary value",
                    "source": Source.system_default().to_dict()
                }
            },
            constraints={
                "test_constraint": {
                    "value": "constraint value",
                    "source": Source.user_input().to_dict()
                }
            },
            metadata={
                "version": 1,
                "last_updated": "2024-01-01T00:00:00Z",
                "confidence": 0.8,
                "extra_field": "should be removed in moderate"
            },
        )
    
    def test_get_self_model_state_none_reduction(self, mock_self_model_with_sources):
        """Test getting self-model state with no reduction (full data)."""
        aggregator = WorldStateAggregator(
            self_model=mock_self_model_with_sources,
            self_model_reduction_level="none"
        )
        
        state = aggregator.get_self_model_state()
        
        assert state["available"] is True
        assert "summary" in state
        assert "capabilities" in state
        assert "knowledge_boundaries" in state
        assert "constraints" in state
        assert "metadata" in state
        
        # Verify full data with sources
        assert len(state["capabilities"]) == 2
        assert isinstance(state["capabilities"][0], dict)
        assert "text" in state["capabilities"][0]
        assert "source" in state["capabilities"][0]
        
        assert isinstance(state["knowledge_boundaries"]["test_boundary"], dict)
        assert "value" in state["knowledge_boundaries"]["test_boundary"]
        assert "source" in state["knowledge_boundaries"]["test_boundary"]
        
        assert isinstance(state["constraints"]["test_constraint"], dict)
        assert "value" in state["constraints"]["test_constraint"]
        assert "source" in state["constraints"]["test_constraint"]
        
        # Full metadata
        assert "extra_field" in state["metadata"]
    
    def test_get_self_model_state_mild_reduction(self, mock_self_model_with_sources):
        """Test getting self-model state with mild reduction (no sources, all fields)."""
        aggregator = WorldStateAggregator(
            self_model=mock_self_model_with_sources,
            self_model_reduction_level="mild"
        )
        
        state = aggregator.get_self_model_state()
        
        assert state["available"] is True
        assert "summary" in state
        assert "capabilities" in state
        assert "knowledge_boundaries" in state
        assert "constraints" in state
        assert "metadata" in state
        
        # Verify no sources, but all fields present
        assert len(state["capabilities"]) == 2
        assert isinstance(state["capabilities"][0], str)  # Just strings, not dicts
        assert state["capabilities"][0] == "Test capability 1"
        assert state["capabilities"][1] == "Test capability 2"
        
        assert isinstance(state["knowledge_boundaries"]["test_boundary"], str)
        assert state["knowledge_boundaries"]["test_boundary"] == "boundary value"
        
        assert isinstance(state["constraints"]["test_constraint"], str)
        assert state["constraints"]["test_constraint"] == "constraint value"
        
        # Full metadata still present
        assert "extra_field" in state["metadata"]
    
    def test_get_self_model_state_moderate_reduction(self, mock_self_model_with_sources):
        """Test getting self-model state with moderate reduction (category summaries)."""
        aggregator = WorldStateAggregator(
            self_model=mock_self_model_with_sources,
            self_model_reduction_level="moderate"
        )
        
        state = aggregator.get_self_model_state()
        
        assert state["available"] is True
        assert "summary" in state
        assert "capabilities" in state
        assert "knowledge_boundaries" in state
        assert "constraints" in state
        assert "metadata" in state
        
        # Verify category summaries (strings, not lists/dicts)
        assert isinstance(state["capabilities"], str)
        assert "Capabilities span" in state["capabilities"] or "Capabilities include" in state["capabilities"]
        assert "Total: 2 capabilities" in state["capabilities"] or "2" in state["capabilities"]
        
        assert isinstance(state["knowledge_boundaries"], str)
        assert "Knowledge boundaries" in state["knowledge_boundaries"]
        assert "test_boundary" in state["knowledge_boundaries"] or "boundary value" in state["knowledge_boundaries"]
        
        assert isinstance(state["constraints"], str)
        assert "Constraints" in state["constraints"]
        assert "test_constraint" in state["constraints"] or "constraint value" in state["constraints"]
        
        # Minimal metadata only
        assert "version" in state["metadata"]
        assert "last_updated" in state["metadata"]
        assert "extra_field" not in state["metadata"]
        assert "confidence" not in state["metadata"]
    
    def test_get_self_model_state_heavy_reduction(self, mock_self_model_with_sources):
        """Test getting self-model state with heavy reduction (single sentence per field)."""
        aggregator = WorldStateAggregator(
            self_model=mock_self_model_with_sources,
            self_model_reduction_level="heavy"
        )
        
        state = aggregator.get_self_model_state()
        
        assert state["available"] is True
        assert "summary" in state
        # Fields should be present as single sentence summaries
        assert "capabilities" in state
        assert "knowledge_boundaries" in state
        assert "constraints" in state
        assert "metadata" not in state  # Metadata not included in heavy
        
        # Verify single sentence summaries
        assert isinstance(state["capabilities"], str)
        assert isinstance(state["knowledge_boundaries"], str)
        assert isinstance(state["constraints"], str)
        
        # Summary should be minimal
        assert "Self-Model Summary" in state["summary"]
        assert "Version" in state["summary"]
        assert "Contains" in state["summary"]
    
    def test_reduction_level_defaults_to_mild(self, mock_self_model_with_sources):
        """Test that reduction level defaults to mild when not specified."""
        aggregator = WorldStateAggregator(self_model=mock_self_model_with_sources)
        
        state = aggregator.get_self_model_state()
        
        # Should use mild reduction (default)
        assert isinstance(state["capabilities"][0], str)  # Strings, not dicts
        assert "extra_field" in state["metadata"]  # Full metadata
    
    def test_reduction_handles_empty_data(self):
        """Test that reduction levels handle empty self-model data."""
        empty_model = SelfModel(
            capabilities=[],
            knowledge_boundaries={},
            constraints={},
            metadata={"version": 1, "last_updated": "2024-01-01T00:00:00Z"}
        )
        
        for level in ["none", "mild", "moderate", "heavy"]:
            aggregator = WorldStateAggregator(
                self_model=empty_model,
                self_model_reduction_level=level
            )
            state = aggregator.get_self_model_state()
            
            assert state["available"] is True
            assert "summary" in state
            
            if level == "none":
                # Full data structure, empty list
                assert "capabilities" in state
                assert state["capabilities"] == []
            elif level == "mild":
                # Empty list
                assert "capabilities" in state
                assert state["capabilities"] == []
            elif level == "moderate":
                # String: "No capabilities defined."
                assert "capabilities" in state
                assert isinstance(state["capabilities"], str)
                assert "No capabilities defined" in state["capabilities"]
            elif level == "heavy":
                # String: "No capabilities defined."
                assert "capabilities" in state
                assert isinstance(state["capabilities"], str)
                assert "No capabilities defined" in state["capabilities"]
    
    def test_analyze_capabilities_themes(self):
        """Test theme analysis groups capabilities correctly."""
        from broca.self_model.source import Source
        capabilities = [
            {"text": "General conversation and assistance", "source": Source.system_default().to_dict()},
            {"text": "Tool usage (memory, web search, terminal)", "source": Source.system_default().to_dict()},
            {"text": "Code execution and analysis", "source": Source.system_default().to_dict()},
            {"text": "Information retrieval and synthesis", "source": Source.system_default().to_dict()},
            {"text": "Mathematical problem solving", "source": Source.system_default().to_dict()},
        ]
        
        aggregator = WorldStateAggregator()
        themes = aggregator._analyze_capabilities_themes(capabilities)
        
        assert "conversation" in themes
        assert "tools" in themes
        assert "code" in themes
        assert "information" in themes
        assert "mathematics" in themes
        assert len(themes["conversation"]) == 1
        assert len(themes["tools"]) == 1
        assert len(themes["code"]) == 1
    
    def test_summarize_capabilities_moderate_with_themes(self):
        """Test moderate capability summary groups by theme."""
        from broca.self_model.source import Source
        capabilities = [
            {"text": "General conversation and assistance", "source": Source.system_default().to_dict()},
            {"text": "Tool usage (memory, web search, terminal)", "source": Source.system_default().to_dict()},
            {"text": "Code execution and analysis", "source": Source.system_default().to_dict()},
            {"text": "Information retrieval", "source": Source.system_default().to_dict()},
        ]
        
        aggregator = WorldStateAggregator()
        summary = aggregator._summarize_capabilities_moderate(capabilities)
        
        assert isinstance(summary, str)
        assert "Capabilities span" in summary or "Capabilities include" in summary
        assert "Total: 4 capabilities" in summary or "4" in summary
    
    def test_summarize_capabilities_heavy_large_model(self):
        """Test heavy capability summary for large model (158 capabilities)."""
        from broca.self_model.source import Source
        # Create a large set of capabilities
        capabilities = []
        for i in range(158):
            capabilities.append({
                "text": f"Capability {i}: General task {i}",
                "source": Source.system_default().to_dict()
            })
        
        aggregator = WorldStateAggregator()
        summary = aggregator._summarize_capabilities_heavy(capabilities)
        
        assert isinstance(summary, str)
        assert "158" in summary or "Comprehensive" in summary
        # Should be a single sentence, not listing all 158
        assert summary.count(",") < 10  # Not too many commas
    
    def test_summarize_knowledge_boundaries_moderate_grouped(self):
        """Test moderate knowledge boundaries summary groups by type."""
        from broca.self_model.source import Source
        knowledge_boundaries = {
            "training_cutoff": {
                "value": "unknown",
                "source": Source.system_default().to_dict()
            },
            "real_time_info": {
                "value": "requires web search or tools",
                "source": Source.system_default().to_dict()
            },
        }
        
        aggregator = WorldStateAggregator()
        summary = aggregator._summarize_knowledge_boundaries_moderate(knowledge_boundaries)
        
        assert isinstance(summary, str)
        assert "Knowledge boundaries" in summary
        assert "training_cutoff" in summary or "temporal" in summary
        assert "real_time_info" in summary or "access" in summary
    
    def test_summarize_constraints_moderate_grouped(self):
        """Test moderate constraints summary groups by category."""
        from broca.self_model.source import Source
        constraints = {
            "cannot_execute_arbitrary_code": {
                "value": "limited to whitelisted terminal commands",
                "source": Source.system_default().to_dict()
            },
            "cannot_access_internet_directly": {
                "value": "requires web search tool",
                "source": Source.system_default().to_dict()
            },
        }
        
        aggregator = WorldStateAggregator()
        summary = aggregator._summarize_constraints_moderate(constraints)
        
        assert isinstance(summary, str)
        assert "Constraints" in summary
        assert "cannot_execute" in summary or "safety" in summary or "access" in summary
    
    def test_aggregate_with_reduction_levels(self, mock_self_model_with_sources):
        """Test that aggregate() respects reduction levels."""
        for level in ["none", "mild", "moderate", "heavy"]:
            aggregator = WorldStateAggregator(
                self_model=mock_self_model_with_sources,
                self_model_reduction_level=level
            )
            
            world_state = aggregator.aggregate()
            
            assert "self_model" in world_state
            self_model = world_state["self_model"]
            assert "summary" in self_model
            
            # Verify minimal summary format
            assert "Self-Model Summary" in self_model["summary"]
            assert "Version" in self_model["summary"]
            assert "Contains" in self_model["summary"]
            
            if level == "none":
                # Full data with sources
                assert "capabilities" in self_model
                assert isinstance(self_model["capabilities"], list)
                assert isinstance(self_model["capabilities"][0], dict)
                assert "source" in self_model["capabilities"][0]
            elif level == "mild":
                # Strings, no sources
                assert "capabilities" in self_model
                assert isinstance(self_model["capabilities"], list)
                assert isinstance(self_model["capabilities"][0], str)
            elif level == "moderate":
                # Category summaries (strings)
                assert "capabilities" in self_model
                assert isinstance(self_model["capabilities"], str)
                assert "Capabilities span" in self_model["capabilities"] or "Capabilities include" in self_model["capabilities"]
                assert "Total:" in self_model["capabilities"] or "capabilities" in self_model["capabilities"]
            elif level == "heavy":
                # Single sentence summaries (strings)
                assert "capabilities" in self_model
                assert isinstance(self_model["capabilities"], str)
                assert "Capable" in self_model["capabilities"] or "Comprehensive" in self_model["capabilities"] or "Core capabilities" in self_model["capabilities"] or "No capabilities" in self_model["capabilities"]


class TestPhysiologyHealthAggregation:
    """Test physiology health aggregation and telemetry filtering."""
    
    @pytest.fixture
    def mock_internal_sensing(self):
        """Create a mock internal sensing framework with computational state."""
        mock = Mock(spec=InternalSensingFramework)
        # Mock interoception with all sub-components
        mock.interoception = Mock()
        mock.interoception.physiology = Mock()
        mock.interoception.cognition = Mock()
        mock.interoception.affect = Mock()
        mock.interoception.affect.get_motivational_drives.return_value = {}
        mock.interoception.affect.get_satisfaction_patterns.return_value = []
        mock.interoception.cognition._get_reasoning_patterns.return_value = []
        mock.interoception.detect_anomalies.return_value = []
        mock.interoception.measure_self_awareness_quality.return_value = None
        mock.interoception.track_interoceptive_accuracy.return_value = {}
        
        mock.sample_internal_state.return_value = {
            "computational": {
                "computational_load": 0.09,
                "memory_pressure": 0.59,
                "processing_latency": 0.011,
                "cpu_per_core": [0.1, 0.2, 0.3],
                "disk_io": {"read_bytes": 1000000},
                "network_io": {"bytes_sent": 2000000},
            },
            "cognitive": {"metrics": {"confidence": 0.8}},
            "affective": {"valence": 0.6},
        }
        mock.generate_interoceptive_report.return_value = "Current state: stable"
        mock.get_tool_statistics.return_value = {"memory": 5}
        mock.extract_behavioral_patterns.return_value = []
        return mock
    
    def test_aggregate_physiology_health(self):
        """Test that health aggregation extracts only essential metrics."""
        aggregator = WorldStateAggregator()
        
        computational_state = {
            "computational_load": 0.09,
            "memory_pressure": 0.59,
            "processing_latency": 0.011,  # 11ms in seconds
            "cpu_per_core": [0.1, 0.2, 0.3, 0.4],
            "cpu_times": {"user": 100.0, "system": 50.0},
            "cpu_statistics": {"context_switches": 1000},
            "disk_io": {"read_bytes": 1000000, "write_bytes": 500000},
            "network_io": {"bytes_sent": 2000000, "bytes_recv": 3000000},
            "system_uptime": 0.5,
            "process_count": 0.3,
            "swap_usage": 0.1,
            "memory_breakdown": {"used": 0.6, "free": 0.4},
        }
        
        health = aggregator._aggregate_physiology_health(computational_state)
        
        # Should only have health dict with essential metrics
        assert "health" in health
        assert health["health"]["cpu_load"] == 0.09
        assert health["health"]["mem_pressure"] == 0.59
        assert health["health"]["latency_ms"] == 11.0  # Converted from 0.011 seconds
        
        # Should not have any telemetry fields
        assert "cpu_per_core" not in health
        assert "cpu_times" not in health
        assert "disk_io" not in health
        assert "network_io" not in health
    
    def test_aggregate_physiology_filters_telemetry(self):
        """Test that detailed telemetry fields are excluded."""
        aggregator = WorldStateAggregator()
        
        computational_state = {
            "computational_load": 0.15,
            "memory_pressure": 0.45,
            "processing_latency": 0.025,
            "cpu_per_core": [0.1, 0.2],
            "cpu_times": {"user": 100.0},
            "cpu_frequency": 0.8,
            "cpu_statistics": {"interrupts": 500},
            "memory_breakdown": {"used": 0.6},
            "swap_usage": 0.2,
            "disk_usage_root": 0.7,
            "disk_io": {"read_count": 100},
            "network_io": {"bytes_sent": 1000},
            "network_connections_count": 0.5,
            "system_uptime": 0.3,
            "process_count": 0.4,
            "user_count": 0.1,
        }
        
        health = aggregator._aggregate_physiology_health(computational_state)
        
        # Verify only health metrics present
        health_dict = health["health"]
        assert len(health_dict) == 3
        assert "cpu_load" in health_dict
        assert "mem_pressure" in health_dict
        assert "latency_ms" in health_dict
        
        # Verify telemetry fields excluded
        telemetry_fields = [
            "cpu_per_core", "cpu_times", "cpu_frequency", "cpu_statistics",
            "memory_breakdown", "swap_usage", "disk_usage_root", "disk_io",
            "network_io", "network_connections_count", "system_uptime",
            "process_count", "user_count"
        ]
        for field in telemetry_fields:
            assert field not in health
    
    def test_aggregate_physiology_handles_missing_fields(self):
        """Test that health aggregation handles missing fields gracefully."""
        aggregator = WorldStateAggregator()
        
        # Test with only some fields
        computational_state = {
            "computational_load": 0.2,
            # memory_pressure missing
            # processing_latency missing
        }
        
        health = aggregator._aggregate_physiology_health(computational_state)
        
        assert "health" in health
        assert health["health"]["cpu_load"] == 0.2
        assert "mem_pressure" not in health["health"]
        assert "latency_ms" not in health["health"]
        
        # Test with empty state
        empty_health = aggregator._aggregate_physiology_health({})
        assert "health" in empty_health
        assert len(empty_health["health"]) == 0
    
    def test_aggregate_physiology_converts_latency(self):
        """Test that processing_latency is converted to milliseconds."""
        aggregator = WorldStateAggregator()
        
        # Test latency in seconds (< 1.0)
        computational_state_seconds = {
            "computational_load": 0.1,
            "memory_pressure": 0.5,
            "processing_latency": 0.011,  # 11ms
        }
        health = aggregator._aggregate_physiology_health(computational_state_seconds)
        assert health["health"]["latency_ms"] == 11.0
        
        # Test latency already in milliseconds (>= 1.0)
        computational_state_ms = {
            "computational_load": 0.1,
            "memory_pressure": 0.5,
            "processing_latency": 25.0,  # Already in ms
        }
        health = aggregator._aggregate_physiology_health(computational_state_ms)
        assert health["health"]["latency_ms"] == 25.0
    
    def test_aggregate_includes_health_summary(self, mock_internal_sensing):
        """Test that aggregate() includes health summary instead of full physiology."""
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        world_state = aggregator.aggregate()
        
        assert "internal_state" in world_state
        assert "physiology" in world_state["internal_state"]
        
        physiology = world_state["internal_state"]["physiology"]
        # Should have health dict, not full computational state
        assert "health" in physiology
        assert "cpu_load" in physiology["health"] or "mem_pressure" in physiology["health"] or "latency_ms" in physiology["health"]
        
        # Should not have telemetry fields
        assert "cpu_per_core" not in physiology
        assert "disk_io" not in physiology
        assert "network_io" not in physiology


class TestToolRegistryVersioning:
    """Test tool registry versioning and conditional inclusion."""
    
    @pytest.fixture
    def mock_tool_registry(self):
        """Create a mock tool registry."""
        from broca.tools.registry import ToolRegistry
        registry = ToolRegistry()
        tool1 = Mock()
        tool1.name = "memory"
        tool2 = Mock()
        tool2.name = "terminal"
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        return registry
    
    @pytest.fixture
    def mock_self_model(self):
        """Create a mock self-model."""
        return SelfModel(
            capabilities=["Test capability 1"],
            knowledge_boundaries={},
            constraints={},
            metadata={"version": 1, "last_updated": "2024-01-01T00:00:00Z"},
        )
    
    def test_get_registry_hash(self):
        """Test that registry hash is computed correctly."""
        from broca.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Empty registry
        hash1 = registry.get_registry_hash()
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex digest length
        
        # Add a tool
        tool1 = Mock()
        tool1.name = "test_tool"
        registry.register_tool(tool1)
        hash2 = registry.get_registry_hash()
        assert hash2 != hash1
        
        # Add another tool
        tool2 = Mock()
        tool2.name = "another_tool"
        registry.register_tool(tool2)
        hash3 = registry.get_registry_hash()
        assert hash3 != hash2
        assert hash3 != hash1
    
    def test_get_registry_version(self):
        """Test that registry version format is correct."""
        from broca.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        version = registry.get_registry_version()
        
        assert isinstance(version, str)
        assert version.startswith("v")
        assert len(version) == 9  # "v" + 8 chars
        
        # Version should match first 8 chars of hash
        hash_str = registry.get_registry_hash()
        assert version == f"v{hash_str[:8]}"
    
    def test_get_tools_info_returns_registry_id(self, mock_tool_registry):
        """Test that get_tools_info returns registry ID structure."""
        aggregator = WorldStateAggregator(tool_registry=mock_tool_registry)
        
        info = aggregator.get_tools_info()
        
        assert info["available"] is True
        assert "tools_registry" in info
        assert "version" in info["tools_registry"]
        assert "hash" in info["tools_registry"]
        assert info["tools_registry"]["refresh_on_change"] is True
        assert info["tools_registry"]["version"].startswith("v")
        assert len(info["tools_registry"]["hash"]) == 64
    
    def test_get_tools_info_includes_tools_on_first_call(self, mock_tool_registry):
        """Test that tools are included on first call."""
        aggregator = WorldStateAggregator(tool_registry=mock_tool_registry)
        
        info = aggregator.get_tools_info()
        
        # First call should include tools
        assert "tools" in info
        assert info["tools"]["count"] == 2
        assert "memory" in info["tools"]["names"]
        assert "terminal" in info["tools"]["names"]
    
    def test_get_tools_info_includes_tools_when_hash_changes(self, mock_tool_registry):
        """Test that tools are included when registry hash changes."""
        aggregator = WorldStateAggregator(tool_registry=mock_tool_registry)
        
        # First call - should include tools
        info1 = aggregator.get_tools_info()
        assert "tools" in info1
        hash1 = info1["tools_registry"]["hash"]
        
        # Second call with same registry - should not include tools
        info2 = aggregator.get_tools_info()
        assert "tools" not in info2
        assert info2["tools_registry"]["hash"] == hash1
        
        # Add a new tool to change hash
        new_tool = Mock()
        new_tool.name = "new_tool"
        mock_tool_registry.register_tool(new_tool)
        
        # Third call with changed registry - should include tools again
        info3 = aggregator.get_tools_info()
        assert "tools" in info3
        assert info3["tools"]["count"] == 3
        assert "new_tool" in info3["tools"]["names"]
        assert info3["tools_registry"]["hash"] != hash1
    
    def test_get_tools_info_omits_tools_when_hash_unchanged(self, mock_tool_registry):
        """Test that tools are omitted when hash is unchanged."""
        aggregator = WorldStateAggregator(tool_registry=mock_tool_registry)
        
        # First call - includes tools
        info1 = aggregator.get_tools_info()
        assert "tools" in info1
        hash1 = info1["tools_registry"]["hash"]
        
        # Second call - should omit tools
        info2 = aggregator.get_tools_info()
        assert "tools" not in info2
        assert info2["tools_registry"]["hash"] == hash1
        
        # Third call - should still omit tools
        info3 = aggregator.get_tools_info()
        assert "tools" not in info3
        assert info3["tools_registry"]["hash"] == hash1
    
    def test_aggregate_includes_registry_id(self, mock_tool_registry, mock_self_model):
        """Test that aggregate() includes tools_registry structure."""
        aggregator = WorldStateAggregator(
            tool_registry=mock_tool_registry,
            self_model=mock_self_model
        )
        
        world_state = aggregator.aggregate()
        
        assert "tools_registry" in world_state
        assert "version" in world_state["tools_registry"]
        assert "hash" in world_state["tools_registry"]
        assert world_state["tools_registry"]["refresh_on_change"] is True
    
    def test_aggregate_conditionally_includes_tools(self, mock_tool_registry, mock_self_model):
        """Test that aggregate() conditionally includes tools based on hash change."""
        aggregator = WorldStateAggregator(
            tool_registry=mock_tool_registry,
            self_model=mock_self_model
        )
        
        # First aggregate - should include tools
        world_state1 = aggregator.aggregate()
        assert "tools" in world_state1
        assert "tools_registry" in world_state1
        hash1 = world_state1["tools_registry"]["hash"]
        
        # Second aggregate - should not include tools (hash unchanged)
        world_state2 = aggregator.aggregate()
        assert "tools" not in world_state2
        assert world_state2["tools_registry"]["hash"] == hash1
        
        # Add tool and aggregate again - should include tools
        new_tool = Mock()
        new_tool.name = "new_tool"
        mock_tool_registry.register_tool(new_tool)
        
        world_state3 = aggregator.aggregate()
        assert "tools" in world_state3
        assert world_state3["tools_registry"]["hash"] != hash1


class TestMemoryIndexPointer:
    """Test memory index pointer structure."""
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Create a mock memory manager with storage and namespace_index."""
        from unittest.mock import Mock
        from broca.memory.storage import MemoryStorage
        from broca.memory.namespace_index import NamespaceIndexGenerator
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            namespace_index = NamespaceIndexGenerator(storage)
            
            mock_manager = Mock()
            mock_manager.storage = storage
            mock_manager.namespace_index = namespace_index
            return mock_manager
    
    def test_get_memory_index_returns_pointer(self, mock_memory_manager):
        """Test that get_memory_namespace_hierarchy returns compact pointer structure."""
        aggregator = WorldStateAggregator(memory_manager=mock_memory_manager)
        
        info = aggregator.get_memory_namespace_hierarchy()
        
        assert info["available"] is True
        assert "memory_index" in info
        assert "root" in info["memory_index"]
        assert "schema_version" in info["memory_index"]
        assert "last_indexed" in info["memory_index"]
        assert "fetch" in info["memory_index"]
    
    def test_get_memory_index_includes_root(self, mock_memory_manager):
        """Test that memory_index includes root as 'broca/'."""
        aggregator = WorldStateAggregator(memory_manager=mock_memory_manager)
        
        info = aggregator.get_memory_namespace_hierarchy()
        
        assert info["memory_index"]["root"] == "broca/"
    
    def test_get_memory_index_includes_schema_version(self, mock_memory_manager):
        """Test that memory_index includes schema_version."""
        aggregator = WorldStateAggregator(memory_manager=mock_memory_manager)
        
        info = aggregator.get_memory_namespace_hierarchy()
        
        assert "schema_version" in info["memory_index"]
        assert info["memory_index"]["schema_version"] == "v0.1"
    
    def test_get_memory_index_includes_last_indexed(self, mock_memory_manager):
        """Test that memory_index includes last_indexed timestamp."""
        aggregator = WorldStateAggregator(memory_manager=mock_memory_manager)
        
        info = aggregator.get_memory_namespace_hierarchy()
        
        assert "last_indexed" in info["memory_index"]
        assert info["memory_index"]["last_indexed"] is not None
        # Should be ISO format timestamp
        from datetime import datetime
        datetime.fromisoformat(info["memory_index"]["last_indexed"])
    
    def test_get_memory_index_includes_fetch_instruction(self, mock_memory_manager):
        """Test that memory_index includes fetch instruction."""
        aggregator = WorldStateAggregator(memory_manager=mock_memory_manager)
        
        info = aggregator.get_memory_namespace_hierarchy()
        
        assert info["memory_index"]["fetch"] == "retrieve_memories(query)"
    
    def test_get_memory_index_handles_missing_manager(self):
        """Test that get_memory_namespace_hierarchy handles missing memory_manager."""
        aggregator = WorldStateAggregator()
        
        info = aggregator.get_memory_namespace_hierarchy()
        
        assert info["available"] is False
    
    def test_aggregate_includes_memory_index(self, mock_memory_manager):
        """Test that aggregate() includes memory_index structure."""
        aggregator = WorldStateAggregator(memory_manager=mock_memory_manager)
        
        world_state = aggregator.aggregate()
        
        assert "memory" in world_state
        assert "memory_index" in world_state["memory"]
        assert world_state["memory"]["memory_index"]["root"] == "broca/"


class TestRepoPointer:
    """Test repo pointer structure."""
    
    @pytest.fixture
    def mock_directory_generator(self, tmp_path):
        """Create a real directory structure generator with temp directory."""
        from broca.world_state.directory_structure import DirectoryStructureGenerator
        
        # Create some test files and directories
        (tmp_path / "file1.txt").write_text("test")
        (tmp_path / "file2.py").write_text("test")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("test")
        
        generator = DirectoryStructureGenerator(root_path=str(tmp_path))
        return generator
    
    def test_get_directory_tree_hash(self, mock_directory_generator):
        """Test that directory tree hash is computed correctly."""
        hash1 = mock_directory_generator.get_directory_tree_hash()
        
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex digest length
        
        # Hash should be consistent for same structure
        hash2 = mock_directory_generator.get_directory_tree_hash()
        assert hash2 == hash1
    
    def test_get_last_scan(self, mock_directory_generator):
        """Test that last_scan timestamp is tracked."""
        # Initially should be None
        assert mock_directory_generator.get_last_scan() is None
        
        # After calling get_directory_hierarchy, should have timestamp
        mock_directory_generator.get_directory_hierarchy()
        last_scan = mock_directory_generator.get_last_scan()
        
        assert last_scan is not None
        # Should be ISO format timestamp
        from datetime import datetime
        datetime.fromisoformat(last_scan)
    
    def test_get_broca_house_structure_returns_repo_pointer(self, mock_directory_generator):
        """Test that get_broca_house_structure returns compact repo pointer structure."""
        aggregator = WorldStateAggregator(directory_structure_generator=mock_directory_generator)
        
        info = aggregator.get_broca_house_structure()
        
        assert info["available"] is True
        assert "repo" in info
        assert "root" in info["repo"]
        assert "tree_hash" in info["repo"]
        assert "last_scan" in info["repo"]
        assert "note" in info
    
    def test_get_broca_house_structure_includes_root(self, mock_directory_generator):
        """Test that repo pointer includes root path."""
        aggregator = WorldStateAggregator(directory_structure_generator=mock_directory_generator)
        
        info = aggregator.get_broca_house_structure()
        
        assert info["repo"]["root"] == str(mock_directory_generator.root_path)
    
    def test_get_broca_house_structure_includes_tree_hash(self, mock_directory_generator):
        """Test that repo pointer includes tree hash."""
        aggregator = WorldStateAggregator(directory_structure_generator=mock_directory_generator)
        
        info = aggregator.get_broca_house_structure()
        
        assert "tree_hash" in info["repo"]
        assert len(info["repo"]["tree_hash"]) == 64  # SHA256 hex digest
        # Hash should match direct call
        expected_hash = mock_directory_generator.get_directory_tree_hash()
        assert info["repo"]["tree_hash"] == expected_hash
    
    def test_get_broca_house_structure_includes_last_scan(self, mock_directory_generator):
        """Test that repo pointer includes last_scan timestamp."""
        aggregator = WorldStateAggregator(directory_structure_generator=mock_directory_generator)
        
        info = aggregator.get_broca_house_structure()
        
        assert "last_scan" in info["repo"]
        assert info["repo"]["last_scan"] is not None
        # Should be ISO format timestamp
        from datetime import datetime
        datetime.fromisoformat(info["repo"]["last_scan"])
    
    def test_get_broca_house_structure_includes_note(self, mock_directory_generator):
        """Test that repo pointer includes note field."""
        aggregator = WorldStateAggregator(directory_structure_generator=mock_directory_generator)
        
        info = aggregator.get_broca_house_structure()
        
        assert "note" in info
        assert "terminal" in info["note"].lower() or "list files" in info["note"].lower()
    
    def test_get_broca_house_structure_handles_missing_generator(self):
        """Test that get_broca_house_structure handles missing generator."""
        aggregator = WorldStateAggregator()
        
        info = aggregator.get_broca_house_structure()
        
        assert info["available"] is False
    
    def test_aggregate_includes_repo_pointer(self, mock_directory_generator):
        """Test that aggregate() includes repo pointer structure."""
        aggregator = WorldStateAggregator(directory_structure_generator=mock_directory_generator)
        
        world_state = aggregator.aggregate()
        
        assert "repo" in world_state
        assert "root" in world_state["repo"]
        assert "tree_hash" in world_state["repo"]
        assert "last_scan" in world_state["repo"]
    
    def test_aggregate_omits_directory_hierarchy(self, mock_directory_generator):
        """Test that aggregate() does not include old directory_hierarchy structure."""
        aggregator = WorldStateAggregator(directory_structure_generator=mock_directory_generator)
        
        world_state = aggregator.aggregate()
        
        # Should not have broca_house with directory_hierarchy
        if "broca_house" in world_state:
            assert "directory_hierarchy" not in world_state["broca_house"]
        # Should have repo instead
        assert "repo" in world_state

