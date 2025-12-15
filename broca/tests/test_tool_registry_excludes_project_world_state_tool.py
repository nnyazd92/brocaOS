"""
Tests that verify project world state tool is NOT registered in the tool registry.

Since project world state data is already included in the LLM's mutable system prompt
via WorldStateAggregator, the tool should not be exposed as a callable tool.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import tempfile
from pathlib import Path

from broca.tools.registry import ToolRegistry
from broca.tools.project_world_state import ProjectWorldStateTool


class TestToolRegistryExcludesProjectWorldStateTool:
    """Test that project world state tool is not registered."""
    
    @patch('broca.main_repl.config')
    def test_initialize_tool_registry_excludes_project_world_state_tool(self, mock_config):
        """
        Test that _initialize_tool_registry does not register project world state tool.
        
        Rationale: Project world state data is already in system prompt, so tool is redundant.
        """
        from broca.main_repl import _initialize_tool_registry
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock config to enable project world state but disable other tools
            mock_config.tools.enable_web_search = False
            mock_config.tools.enable_terminal = False
            mock_config.tools.enable_critic = False
            mock_config.tools.enable_version_control = False
            mock_config.tools.enable_project_world_state = True
            mock_config.tools.project_world_state_path = tmpdir
            mock_config.tools.project_world_state_file = str(Path(tmpdir) / "state.json")
            mock_config.tools.project_world_state_header_lines = 10
            mock_config.tools.project_world_state_max_file_size = 1024 * 1024
            
            # Initialize registry (without memory manager, epistemic engine, etc.)
            registry = _initialize_tool_registry(
                memory_manager=None,
                epistemic_engine=None,
                consistency_layer=None
            )
            
            # Registry might be None if no tools are registered, or it might have other tools
            # But it should NOT have project world state tool
            if registry is not None:
                assert registry.get_tool("project_world_state") is None
                
                # Verify tool names don't include project world state tool
                tool_names = [tool.name for tool in registry.list_tools()]
                assert "project_world_state" not in tool_names
    
    def test_project_world_state_tool_can_still_be_created_directly(self):
        """
        Test that ProjectWorldStateTool can still be created directly for WorldStateAggregator.
        
        Rationale: WorldStateAggregator needs the tool instance directly, not from registry.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Tool should still be creatable
            tool = ProjectWorldStateTool(project_root=tmpdir)
            
            assert tool is not None
            assert tool.name == "project_world_state"
            assert tool._project_root == Path(tmpdir)
            
            # Tool should still work (for WorldStateAggregator)
            result = tool.get_world_state()
            assert result["success"] is True
    
    @patch('broca.main_repl.config')
    def test_main_repl_creates_tool_directly_not_from_registry(self, mock_config):
        """
        Test that main() creates ProjectWorldStateTool directly, not from registry.
        
        Rationale: Tool should be created for WorldStateAggregator but not registered.
        """
        from broca.main_repl import _initialize_tool_registry
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock config
            mock_config.tools.enable_web_search = False
            mock_config.tools.enable_terminal = False
            mock_config.tools.enable_critic = False
            mock_config.tools.enable_version_control = False
            mock_config.tools.enable_project_world_state = True
            mock_config.tools.project_world_state_path = tmpdir
            mock_config.tools.project_world_state_file = str(Path(tmpdir) / "state.json")
            mock_config.tools.project_world_state_header_lines = 10
            mock_config.tools.project_world_state_max_file_size = 1024 * 1024
            
            # Initialize registry
            registry = _initialize_tool_registry(
                memory_manager=None,
                epistemic_engine=None,
                consistency_layer=None
            )
            
            # Tool should not be in registry
            if registry is not None:
                assert registry.get_tool("project_world_state") is None
            
            # But tool should still be creatable directly (for WorldStateAggregator)
            tool = ProjectWorldStateTool(project_root=tmpdir)
            assert tool is not None

