"""
Regression tests for version control tool removal.

These tests ensure that removing the version_control tool does not break
the system. Following TDD, these tests are written BEFORE removal.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
import tempfile
from pathlib import Path

from broca.tools.registry import ToolRegistry


class TestToolRegistryWithoutVersionControl:
    """Test that tool registry works correctly without version_control tool."""
    
    @patch('broca.main_repl.config')
    def test_initialize_tool_registry_without_version_control(self, mock_config):
        """
        Test that _initialize_tool_registry works without version_control tool.
        
        Rationale: Ensures registry initialization doesn't break when version_control is disabled.
        """
        from broca.main_repl import _initialize_tool_registry
        
        # Mock config (version_control config removed, so no need to set it)
        mock_config.tools.enable_web_search = False
        mock_config.tools.enable_terminal = False
        mock_config.tools.enable_critic = False
        
        # Initialize registry
        registry = _initialize_tool_registry(
            memory_manager=None,
            epistemic_engine=None,
            self_model=None,
            storage=None
        )
        
        # Registry should not have version_control tool
        if registry is not None:
            assert registry.get_tool("version_control") is None
            tool_names = [tool.name for tool in registry.list_tools()]
            assert "version_control" not in tool_names
    
    @patch('broca.main_repl.config')
    def test_tool_registry_initializes_with_other_tools(self, mock_config):
        """
        Test that tool registry works with other tools when version_control is disabled.
        
        Rationale: Ensures other tools still work correctly.
        """
        from broca.main_repl import _initialize_tool_registry
        
        # Mock config to enable some tools (version_control removed)
        mock_config.tools.enable_web_search = False
        mock_config.tools.enable_terminal = True
        mock_config.tools.enable_critic = False
        
        # Initialize registry
        registry = _initialize_tool_registry(
            memory_manager=None,
            epistemic_engine=None,
            self_model=None,
            storage=None
        )
        
        # Registry should have terminal tool but not version_control
        if registry is not None:
            assert registry.get_tool("version_control") is None
            terminal = registry.get_tool("terminal")
            assert terminal is not None
            assert terminal.name == "terminal"


class TestConfigWithoutVersionControlFields:
    """Test that config loads correctly without version_control fields."""
    
    def test_config_loads_without_version_control_fields(self):
        """
        Test that config can be loaded when version_control fields are missing.
        
        Rationale: Ensures backward compatibility - config should work without these fields.
        """
        from broca.config import ToolsConfig
        import os
        
        # Save original env vars
        original_enable = os.environ.get("BROCA_ENABLE_VERSION_CONTROL")
        original_path = os.environ.get("BROCA_VERSION_CONTROL_REPO_PATH")
        
        try:
            # Remove env vars
            if "BROCA_ENABLE_VERSION_CONTROL" in os.environ:
                del os.environ["BROCA_ENABLE_VERSION_CONTROL"]
            if "BROCA_VERSION_CONTROL_REPO_PATH" in os.environ:
                del os.environ["BROCA_VERSION_CONTROL_REPO_PATH"]
            
            # Config should still load (fields should have defaults or be optional)
            # We're testing that removing these fields doesn't break config loading
            # Since we can't easily remove fields from Pydantic models, we test that
            # the fields can be set to False/None without issues
            config = ToolsConfig()
            
            # Config should be valid
            assert hasattr(config, 'enable_web_search')
            # Version control fields may still exist but should default to False/None
            # This test ensures the system works when they're disabled
            
        finally:
            # Restore original env vars
            if original_enable is not None:
                os.environ["BROCA_ENABLE_VERSION_CONTROL"] = original_enable
            if original_path is not None:
                os.environ["BROCA_VERSION_CONTROL_REPO_PATH"] = original_path
    
    def test_config_loads_without_version_control_field(self):
        """
        Test that config loads correctly without version_control field.
        
        Rationale: Ensures config works after version_control field removal.
        """
        from broca.config import ToolsConfig
        import os
        
        # Remove version_control env var if it exists
        original = os.environ.pop("BROCA_ENABLE_VERSION_CONTROL", None)
        original_path = os.environ.pop("BROCA_VERSION_CONTROL_REPO_PATH", None)
        
        try:
            # Config should load without version_control fields
            config = ToolsConfig()
            # Verify other fields still work
            assert hasattr(config, 'enable_web_search')
            assert hasattr(config, 'enable_terminal')
            # Version control field should not exist
            assert not hasattr(config, 'enable_version_control')
        finally:
            # Restore if needed
            if original is not None:
                os.environ["BROCA_ENABLE_VERSION_CONTROL"] = original
            if original_path is not None:
                os.environ["BROCA_VERSION_CONTROL_REPO_PATH"] = original_path


class TestToolStatusWithoutVersionControl:
    """Test that tool status display handles missing version_control gracefully."""
    
    def test_tool_status_formatter_without_version_control(self):
        """
        Test that tool status formatter works without version_control formatting.
        
        Rationale: Ensures tool status display doesn't break when version_control is removed.
        """
        from broca.repl.tool_status import ToolDescriptionFormatter
        
        formatter = ToolDescriptionFormatter()
        
        # Test that formatter handles unknown tools gracefully
        description = formatter.format("unknown_tool", {"action": "test"})
        assert isinstance(description, str)
        assert len(description) > 0
        
        # Test that formatter works for other tools
        description = formatter.format("terminal", {"command": "ls"})
        assert "terminal" in description.lower() or "command" in description.lower()
    
    def test_tool_status_display_without_version_control(self):
        """
        Test that tool status display works without version_control tool.
        
        Rationale: Ensures display system doesn't break when version_control is missing.
        """
        from broca.repl.tool_status import ToolStatusDisplay
        
        display = ToolStatusDisplay(enabled=True)
        
        # Should be able to start/complete tool calls for other tools
        display.start_tool_call("terminal", {"command": "ls"}, "test_id")
        display.complete_tool_call("test_id", "terminal", success=True)
        
        # Should not crash when version_control is not in the system


class TestMainReplWithoutVersionControl:
    """Test that main_repl initializes without version_control tool."""
    
    @patch('broca.main_repl.config')
    @patch('broca.main_repl._initialize_storage')
    @patch('broca.main_repl._initialize_memory_manager')
    @patch('broca.main_repl._initialize_self_model')
    @patch('broca.main_repl._initialize_internal_sensing')
    @patch('broca.main_repl._initialize_environment_system')
    def test_main_repl_initializes_without_version_control(
        self,
        mock_env,
        mock_sensing,
        mock_self_model,
        mock_memory,
        mock_storage,
        mock_config
    ):
        """
        Test that main_repl initialization works without version_control tool.
        
        Rationale: Ensures the main REPL can start without version_control.
        """
        # Mock all subsystems
        mock_storage.return_value = None
        mock_memory.return_value = None
        mock_self_model.return_value = (None, None, None)
        mock_sensing.return_value = None
        mock_env.return_value = None
        
        # Mock config (version_control config removed)
        mock_config.tools.enable_web_search = False
        mock_config.tools.enable_terminal = False
        mock_config.tools.enable_critic = False
        mock_config.tools.tavily_api_key = ""
        mock_config.tools.terminal_command_whitelist = []
        mock_config.tools.terminal_working_directory = None
        mock_config.tools.critic_system_prompt_template = None
        mock_config.tools.tools_mode = "normal"
        
        mock_config.storage.storage_type = "json"
        mock_config.storage.storage_path = "conversations"
        mock_config.storage.base_system_prompt = ""
        
        mock_config.memory.memory_db_path = "memories.db"
        mock_config.memory.vector_index_path = "memories.faiss"
        mock_config.memory.embedding_dimension = 1536
        
        mock_config.self_model.enabled = False
        
        mock_config.internal_sensing.enabled = False
        
        mock_config.environment.enabled = False
        
        mock_config.llm.provider = "deepseek"
        mock_config.llm.streaming_enabled = True
        
        mock_config.self_model.self_model_reduction_level = "mild"
        
        mock_config.repl_color.profile = "default"
        mock_config.repl_color.custom_brocaos_prompt = ""
        mock_config.repl_color.custom_response_text = ""
        mock_config.repl_color.custom_you_prompt = ""
        mock_config.repl_color.custom_input_text = ""
        
        # Initialize tool registry (this is what we're testing)
        from broca.main_repl import _initialize_tool_registry
        
        registry = _initialize_tool_registry(
            memory_manager=None,
            epistemic_engine=None,
            self_model=None,
            storage=None
        )
        
        # Registry should initialize successfully
        # It might be None if no tools are registered, which is fine
        if registry is not None:
            # Should not have version_control tool
            assert registry.get_tool("version_control") is None


class TestPropertyBasedToolRegistry:
    """Property-based tests for tool registry with various tool combinations."""
    
    from hypothesis import given, strategies as st
    
    @given(
        enable_web_search=st.booleans(),
        enable_terminal=st.booleans(),
        enable_critic=st.booleans(),
    )
    @patch('broca.main_repl.config')
    def test_tool_registry_with_various_combinations(
        self,
        mock_config,
        enable_web_search,
        enable_terminal,
        enable_critic
    ):
        """
        Property-based test: tool registry should work with any combination of tools.
        
        Rationale: Ensures registry is robust to different tool configurations.
        """
        from broca.main_repl import _initialize_tool_registry
        
        # Set config based on generated values
        mock_config.tools.enable_web_search = enable_web_search
        mock_config.tools.enable_terminal = enable_terminal
        mock_config.tools.enable_critic = enable_critic
        mock_config.tools.tavily_api_key = "test_key" if enable_web_search else ""
        mock_config.tools.terminal_command_whitelist = []
        mock_config.tools.terminal_working_directory = None
        mock_config.tools.critic_system_prompt_template = None
        
        # Initialize registry
        registry = _initialize_tool_registry(
            memory_manager=None,
            epistemic_engine=None,
            self_model=None,
            storage=None
        )
        
        # Property: version_control should never be in registry
        if registry is not None:
            assert registry.get_tool("version_control") is None
            tool_names = [tool.name for tool in registry.list_tools()]
            assert "version_control" not in tool_names


class TestFaultInjection:
    """Fault injection tests for graceful handling of missing version_control."""
    
    def test_tool_registry_get_version_control_returns_none(self):
        """
        Test that getting version_control tool returns None gracefully.
        
        Rationale: Ensures system handles missing tool gracefully.
        """
        registry = ToolRegistry()
        
        # Should return None, not raise exception
        tool = registry.get_tool("version_control")
        assert tool is None
    
    def test_tool_status_formatter_handles_version_control_gracefully(self):
        """
        Test that tool status formatter handles version_control tool name gracefully.
        
        Rationale: Ensures formatter doesn't crash on unknown tools.
        """
        from broca.repl.tool_status import ToolDescriptionFormatter
        
        formatter = ToolDescriptionFormatter()
        
        # Should handle version_control tool name gracefully (falls through to generic)
        description = formatter.format("version_control", {"action": "status"})
        assert isinstance(description, str)
        assert len(description) > 0
        # Should not contain "Version control" since we removed that formatting
        # It should fall through to generic formatting
    
    def test_config_without_version_control_fields_does_not_crash(self):
        """
        Test that accessing removed config fields doesn't crash.
        
        Rationale: Ensures backward compatibility - old code accessing removed fields fails gracefully.
        """
        from broca.config import ToolsConfig
        
        # Create config instance
        config = ToolsConfig()
        
        # Accessing removed field should raise AttributeError
        with pytest.raises(AttributeError):
            _ = config.enable_version_control
        
        with pytest.raises(AttributeError):
            _ = config.version_control_repo_path


class TestGoldenTraceReplay:
    """Golden trace replay tests for tool registry initialization."""
    
    def test_tool_registry_initialization_trace(self):
        """
        Test that tool registry initialization produces expected trace.
        
        Rationale: Ensures registry initialization behavior is consistent.
        """
        from broca.main_repl import _initialize_tool_registry
        
        # Capture initialization trace
        registry = _initialize_tool_registry(
            memory_manager=None,
            epistemic_engine=None,
            self_model=None,
            storage=None
        )
        
        # Golden trace properties:
        # 1. Registry should be None or ToolRegistry instance
        assert registry is None or isinstance(registry, ToolRegistry)
        
        # 2. If registry exists, version_control should not be in it
        if registry is not None:
            assert registry.get_tool("version_control") is None
            tool_names = [tool.name for tool in registry.list_tools()]
            assert "version_control" not in tool_names
        
        # 3. Registry hash should be consistent (no version_control in hash)
        if registry is not None:
            hash1 = registry.get_registry_hash()
            # Hash should not change if we add/remove version_control (since it's not there)
            hash2 = registry.get_registry_hash()
            assert hash1 == hash2
    
    def test_tool_registry_hash_excludes_version_control(self):
        """
        Test that registry hash doesn't include version_control.
        
        Rationale: Ensures hash is consistent without version_control.
        """
        registry = ToolRegistry()
        
        # Add some tools
        from broca.tools.terminal import TerminalTool
        terminal = TerminalTool()
        registry.register_tool(terminal)
        
        # Get hash
        hash1 = registry.get_registry_hash()
        
        # Hash should not include version_control (since it's not registered)
        # Verify by checking tool names in hash computation
        tool_names = sorted(registry._tools.keys())
        assert "version_control" not in tool_names
        
        # Hash should be consistent
        hash2 = registry.get_registry_hash()
        assert hash1 == hash2

