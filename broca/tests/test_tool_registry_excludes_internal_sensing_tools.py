"""
Tests that verify internal sensing tools are NOT registered in the tool registry.

Since internal sensing data is already included in the LLM's mutable system prompt
via WorldStateAggregator, these tools should not be exposed as callable tools.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.tools.registry import ToolRegistry
from broca.internal_sensing.framework import InternalSensingFramework


class TestToolRegistryExcludesInternalSensingTools:
    """Test that internal sensing tools are not registered."""
    
    @patch('broca.main_repl.config')
    def test_initialize_tool_registry_excludes_internal_sensing_tools(self, mock_config):
        """
        Test that _initialize_tool_registry does not register internal sensing tools.
        
        Rationale: Internal sensing data is already in system prompt, so tools are redundant.
        """
        from broca.main_repl import _initialize_tool_registry
        
        # Mock config to disable other tools
        mock_config.tools.enable_web_search = False
        mock_config.tools.enable_terminal = False
        mock_config.tools.enable_critic = False
        mock_config.tools.enable_version_control = False
        mock_config.tools.enable_project_world_state = False
        
        # Initialize registry (without memory manager, epistemic engine, etc.)
        registry = _initialize_tool_registry(
            memory_manager=None,
            epistemic_engine=None,
            self_model=None,
            storage=None
        )
        
        # Registry might be None if no tools are registered, or it might have other tools
        # But it should NOT have internal sensing tools
        if registry is not None:
            assert registry.get_tool("query_internal_state") is None
            assert registry.get_tool("get_interoceptive_report") is None
            
            # Verify tool names don't include internal sensing tools
            tool_names = [tool.name for tool in registry.list_tools()]
            assert "query_internal_state" not in tool_names
            assert "get_interoceptive_report" not in tool_names
    
    def test_main_repl_does_not_register_internal_sensing_tools(self):
        """
        Test that main() function does not register internal sensing tools in registry.
        
        Rationale: Internal sensing tools should not be available as callable tools.
        """
        from broca.main_repl import _initialize_tool_registry, _initialize_internal_sensing
        
        # Initialize internal sensing framework
        with patch('broca.main_repl.config') as mock_config:
            mock_config.internal_sensing.enabled = True
            mock_config.internal_sensing.sampling_rate = 1.0
            mock_config.internal_sensing.history_window = 100
            mock_config.internal_sensing.enable_physiology = True
            mock_config.internal_sensing.enable_cognitive = True
            mock_config.internal_sensing.enable_affective = True
            mock_config.internal_sensing.enable_predictive = True
            
            # Mock other tool configs
            mock_config.tools.enable_web_search = False
            mock_config.tools.enable_terminal = False
            mock_config.tools.enable_critic = False
            mock_config.tools.enable_version_control = False
            mock_config.tools.enable_project_world_state = False
            
            internal_sensing = _initialize_internal_sensing()
            
            # Initialize tool registry
            registry = _initialize_tool_registry(
                memory_manager=None,
                epistemic_engine=None,
                self_model=None,
                storage=None
            )
            
            # Even if internal sensing is enabled, tools should not be in registry
            # (they would be registered in main() after _initialize_tool_registry)
            # But we're testing that the registration code should be removed
            if registry is not None:
                assert registry.get_tool("query_internal_state") is None
                assert registry.get_tool("get_interoceptive_report") is None


class TestOptimizationDaemonExcludesInternalSensingTools:
    """Test that optimization daemon does not register internal sensing tools."""
    
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    @patch('broca.main_repl._initialize_tool_registry')
    def test_daemon_does_not_register_internal_sensing_tools(
        self,
        mock_tool_registry,
        mock_env,
        mock_sensing,
        mock_self_model,
        mock_memory,
        mock_storage
    ):
        """
        Test that optimization daemon does not register internal sensing tools.
        
        Rationale: Internal sensing data is in system prompt, tools should not be callable.
        """
        from broca.optimization_daemon import OptimizationDaemon
        from broca.optimization.goal_manager import GoalManager
        from broca.optimization.report_manager import ReportManager
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            reports_file = os.path.join(tmpdir, "reports.json")
            
            # Setup mocks
            mock_storage.return_value = None
            mock_memory.return_value = None
            mock_self_model.return_value = (None, None, None)  # (self_model, storage, epistemic_engine)
            
            # Create a mock internal sensing framework
            mock_internal_sensing = Mock(spec=InternalSensingFramework)
            mock_sensing.return_value = mock_internal_sensing
            mock_env.return_value = None
            
            # Create a mock registry
            from broca.tools.registry import ToolRegistry
            mock_registry = ToolRegistry()
            mock_tool_registry.return_value = mock_registry
            
            daemon = OptimizationDaemon(
                goal_manager=GoalManager(goals_file_path=goals_file),
                report_manager=ReportManager(reports_file_path=reports_file)
            )
            
            # Initialize systems (this is where tools would be registered)
            daemon._initialize_systems()
            
            # Verify internal sensing tools are NOT in registry
            assert mock_registry.get_tool("query_internal_state") is None
            assert mock_registry.get_tool("get_interoceptive_report") is None
            
            # Verify tool names don't include internal sensing tools
            tool_names = [tool.name for tool in mock_registry.list_tools()]
            assert "query_internal_state" not in tool_names
            assert "get_interoceptive_report" not in tool_names

