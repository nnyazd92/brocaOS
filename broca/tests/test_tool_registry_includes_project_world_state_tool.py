"""
Tests that verify project world state tool IS registered in the tool registry.

Since project world state data is no longer included in the LLM's mutable system prompt
via WorldStateAggregator, the tool should be exposed as a callable tool.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import tempfile
from pathlib import Path

from broca.tools.registry import ToolRegistry
from broca.tools.project_world_state import ProjectWorldStateTool


class TestToolRegistryIncludesProjectWorldStateTool:
    """Test that project world state tool is registered."""
    
    @patch('broca.main_repl.config')
    def test_initialize_tool_registry_includes_project_world_state_tool(self, mock_config):
        """
        Test that _initialize_tool_registry registers project world state tool.
        
        Rationale: Project world state tool should be callable since it's no longer in system prompt.
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
            
            # Registry should have project world state tool
            assert registry is not None
            tool = registry.get_tool("project_world_state")
            assert tool is not None
            assert tool.name == "project_world_state"
            
            # Verify tool names include project world state tool
            tool_names = [tool.name for tool in registry.list_tools()]
            assert "project_world_state" in tool_names
    
    def test_project_world_state_tool_can_be_created_directly(self):
        """
        Test that ProjectWorldStateTool can be created directly.
        
        Rationale: Tool should be creatable and usable.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Tool should be creatable
            tool = ProjectWorldStateTool(project_root=tmpdir)
            
            assert tool is not None
            assert tool.name == "project_world_state"
            assert tool._project_root == Path(tmpdir)
            
            # Tool should work
            result = tool.get_world_state()
            assert result["success"] is True
    
    @patch('broca.main_repl.config')
    def test_main_repl_registers_tool_in_registry(self, mock_config):
        """
        Test that _initialize_tool_registry registers ProjectWorldStateTool.
        
        Rationale: Tool should be registered in registry for LLM to call.
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
            
            # Tool should be in registry
            assert registry is not None
            tool = registry.get_tool("project_world_state")
            assert tool is not None
            assert tool.name == "project_world_state"

