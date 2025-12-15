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
        mock.sample_internal_state.return_value = {
            "physiology": {"metrics": {"processing_latency": 0.5}},
            "cognition": {"metrics": {"confidence": 0.8, "uncertainty": 0.2}},
            "affect": {"valence": 0.6, "arousal": 0.4},
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
    def mock_project_world_state_tool(self):
        """Create a mock project world state tool."""
        mock = Mock()
        mock.get_world_state.return_value = {
            "success": True,
            "project_root": "/test/project",
            "last_updated": "2024-01-01T00:00:00Z",
            "statistics": {
                "total_files": 10,
                "total_directories": 5,
                "total_size": 1024,
            },
            "files": [{"path": "test.py", "size": 100}],
        }
        return mock
    
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
    
    def test_init_with_all_components(self, mock_internal_sensing, mock_self_model, mock_project_world_state_tool, mock_tool_registry):
        """Test initializing aggregator with all components."""
        aggregator = WorldStateAggregator(
            internal_sensing=mock_internal_sensing,
            self_model=mock_self_model,
            project_world_state_tool=mock_project_world_state_tool,
            tool_registry=mock_tool_registry,
        )
        
        assert aggregator.internal_sensing is mock_internal_sensing
        assert aggregator.self_model is mock_self_model
        assert aggregator.project_world_state_tool is mock_project_world_state_tool
        assert aggregator.tool_registry is mock_tool_registry
    
    def test_init_with_none_components(self):
        """Test initializing aggregator with no components."""
        aggregator = WorldStateAggregator()
        
        assert aggregator.internal_sensing is None
        assert aggregator.self_model is None
        assert aggregator.project_world_state_tool is None
        assert aggregator.tool_registry is None
    
    def test_aggregate_with_all_components(self, mock_internal_sensing, mock_self_model, mock_project_world_state_tool, mock_tool_registry):
        """Test aggregating world state with all components."""
        aggregator = WorldStateAggregator(
            internal_sensing=mock_internal_sensing,
            self_model=mock_self_model,
            project_world_state_tool=mock_project_world_state_tool,
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
        assert "project" in world_state
        assert "tools" in world_state
    
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
        """Test getting internal sensing state."""
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        state = aggregator.get_internal_sensing_state()
        
        # State should have "available" flag for internal use, but won't be in final aggregate
        assert state["available"] is True
        assert "current_state" in state
        assert "interoceptive_report" in state
        assert "tool_statistics" in state
        # behavioral_patterns should NOT be included
        assert "behavioral_patterns" not in state
        
        mock_internal_sensing.sample_internal_state.assert_called_once()
        mock_internal_sensing.generate_interoceptive_report.assert_called_once()
        mock_internal_sensing.get_tool_statistics.assert_called_once()
    
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
        """Test getting self-model state."""
        aggregator = WorldStateAggregator(self_model=mock_self_model)
        
        state = aggregator.get_self_model_state()
        
        # State should have "available" flag for internal use
        assert state["available"] is True
        assert "summary" in state
        assert "capabilities" in state
        assert state["capabilities"] == mock_self_model.capabilities
        assert state["constraints"] == mock_self_model.constraints
    
    def test_get_self_model_state_none(self):
        """Test getting self-model state when not available."""
        aggregator = WorldStateAggregator()
        
        state = aggregator.get_self_model_state()
        
        # Internal method still returns "available" flag for aggregator logic
        assert state["available"] is False
    
    def test_get_project_state(self, mock_project_world_state_tool):
        """Test getting project state."""
        aggregator = WorldStateAggregator(project_world_state_tool=mock_project_world_state_tool)
        
        state = aggregator.get_project_state()
        
        # State should have "available" flag for internal use
        assert state["available"] is True
        assert state["project_root"] == "/test/project"
        assert "statistics" in state
        assert state["file_count"] == 1
    
    def test_get_project_state_none(self):
        """Test getting project state when not available."""
        aggregator = WorldStateAggregator()
        
        state = aggregator.get_project_state()
        
        # Internal method still returns "available" flag for aggregator logic
        assert state["available"] is False
    
    def test_get_project_state_not_built(self):
        """Test getting project state when world state not built."""
        mock_tool = Mock()
        mock_tool.get_world_state.return_value = {
            "success": False,
            "error": "World state not built",
        }
        
        aggregator = WorldStateAggregator(project_world_state_tool=mock_tool)
        
        state = aggregator.get_project_state()
        
        # Internal method still returns "available" flag for aggregator logic
        assert state["available"] is False
        assert "error" in state
    
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
        assert info["tool_count"] == 2
        assert "memory" in info["tool_names"]
        assert "terminal" in info["tool_names"]
    
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
    
    def test_aggregate_excludes_behavioral_patterns(self, mock_internal_sensing):
        """Test that aggregated world state does NOT contain behavioral_patterns."""
        aggregator = WorldStateAggregator(internal_sensing=mock_internal_sensing)
        
        world_state = aggregator.aggregate()
        
        # internal_state should be present
        assert "internal_state" in world_state
        assert world_state["internal_state"] is not None
        
        # behavioral_patterns should NOT be in internal_state
        internal_state = world_state["internal_state"]
        assert "behavioral_patterns" not in internal_state
        # Other expected fields should still be present
        assert "interoceptive_report" in internal_state
        assert "tool_statistics" in internal_state

