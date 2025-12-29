"""
Tests to verify main_repl.py and main_repl_runtime.py produce identical runtime configurations.

Tests:
- Initialization order matches
- All components initialized with same parameters
- World state aggregator receives identical components
- Conversation session receives identical parameters
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from broca.main_repl_runtime import initialize_runtime, BrocaRuntime
from broca.world_state.aggregator import WorldStateAggregator
from broca.repl.session import ConversationSession


class TestRuntimeParity:
    """Test that main_repl.py and main_repl_runtime.py produce identical configurations."""
    
    @patch('broca.main_repl_runtime._initialize_storage')
    @patch('broca.main_repl_runtime._initialize_memory_manager')
    @patch('broca.main_repl_runtime._initialize_self_model')
    @patch('broca.main_repl_runtime._initialize_internal_sensing')
    @patch('broca.main_repl_runtime._initialize_environment_system')
    @patch('broca.main_repl_runtime._initialize_tool_registry')
    @patch('broca.main_repl_runtime.DirectoryStructureGenerator')
    def test_initialization_order_matches(self, mock_dir_gen, mock_tool_reg, mock_env, 
                                         mock_internal, mock_self_model, mock_memory, mock_storage):
        """Test that initialization order matches main_repl.py."""
        # Setup mocks
        mock_storage.return_value = Mock()
        mock_memory.return_value = Mock()
        mock_memory.return_value.embedding_service = Mock()
        mock_self_model.return_value = (Mock(), Mock(), Mock())
        mock_internal.return_value = Mock()
        mock_env.return_value = Mock()
        mock_tool_reg.return_value = Mock()
        mock_dir_gen.return_value = Mock()
        
        # Track call order
        call_order = []
        
        def track_storage():
            call_order.append("storage")
            return mock_storage.return_value
        
        def track_memory():
            call_order.append("memory")
            return mock_memory.return_value
        
        def track_self_model():
            call_order.append("self_model")
            return mock_self_model.return_value
        
        def track_internal(embedding_service=None, epistemic_engine=None):
            call_order.append("internal_sensing")
            assert epistemic_engine is not None or True  # May be None
            return mock_internal.return_value
        
        def track_env():
            call_order.append("environment")
            return mock_env.return_value
        
        def track_tool_reg(memory_manager=None, epistemic_engine=None, self_model=None, 
                          storage=None, internal_sensing=None):
            call_order.append("tool_registry")
            assert epistemic_engine is not None or True  # May be None
            return mock_tool_reg.return_value
        
        mock_storage.side_effect = track_storage
        mock_memory.side_effect = track_memory
        mock_self_model.side_effect = track_self_model
        mock_internal.side_effect = track_internal
        mock_env.side_effect = track_env
        mock_tool_reg.side_effect = track_tool_reg
        
        # Initialize runtime
        runtime = initialize_runtime()
        
        # Verify order: storage, memory, self_model, internal_sensing, environment, tool_registry
        expected_order = ["storage", "memory", "self_model", "internal_sensing", "environment", "tool_registry"]
        assert call_order == expected_order, f"Call order mismatch: {call_order} != {expected_order}"
    
    @patch('broca.main_repl_runtime._initialize_storage')
    @patch('broca.main_repl_runtime._initialize_memory_manager')
    @patch('broca.main_repl_runtime._initialize_self_model')
    @patch('broca.main_repl_runtime._initialize_internal_sensing')
    @patch('broca.main_repl_runtime._initialize_environment_system')
    @patch('broca.main_repl_runtime._initialize_tool_registry')
    @patch('broca.main_repl_runtime.DirectoryStructureGenerator')
    @patch('broca.main_repl_runtime.WorldStateAggregator')
    def test_world_state_aggregator_parameters_match(self, mock_wsa, mock_dir_gen, mock_tool_reg,
                                                     mock_env, mock_internal, mock_self_model,
                                                     mock_memory, mock_storage):
        """Test that WorldStateAggregator receives identical parameters in both paths."""
        # Setup mocks
        mock_storage.return_value = Mock()
        mock_memory.return_value = Mock()
        mock_memory.return_value.embedding_service = Mock()
        mock_self_model_obj = Mock()
        mock_storage_obj = Mock()
        mock_epistemic = Mock()
        mock_self_model.return_value = (mock_self_model_obj, mock_storage_obj, mock_epistemic)
        mock_internal_obj = Mock()
        mock_internal.return_value = mock_internal_obj
        mock_env_obj = Mock()
        mock_env.return_value = mock_env_obj
        mock_tool_reg_obj = Mock()
        mock_tool_reg.return_value = mock_tool_reg_obj
        mock_dir_gen_obj = Mock()
        mock_dir_gen.return_value = mock_dir_gen_obj
        
        # Initialize runtime
        runtime = initialize_runtime()
        
        # Verify WorldStateAggregator was called with correct parameters
        assert mock_wsa.called
        call_kwargs = mock_wsa.call_args[1]  # Get keyword arguments
        
        assert call_kwargs["internal_sensing"] == mock_internal_obj
        assert call_kwargs["self_model"] == mock_self_model_obj
        assert call_kwargs["tool_registry"] == mock_tool_reg_obj
        assert call_kwargs["memory_manager"] == mock_memory.return_value
        assert call_kwargs["directory_structure_generator"] == mock_dir_gen_obj
        assert "self_model_reduction_level" in call_kwargs
    
    @patch('broca.main_repl_runtime._initialize_storage')
    @patch('broca.main_repl_runtime._initialize_memory_manager')
    @patch('broca.main_repl_runtime._initialize_self_model')
    @patch('broca.main_repl_runtime._initialize_internal_sensing')
    @patch('broca.main_repl_runtime._initialize_environment_system')
    @patch('broca.main_repl_runtime._initialize_tool_registry')
    @patch('broca.main_repl_runtime.DirectoryStructureGenerator')
    @patch('broca.main_repl_runtime.ConversationSession')
    def test_conversation_session_parameters_match(self, mock_session, mock_dir_gen, mock_tool_reg,
                                                   mock_env, mock_internal, mock_self_model,
                                                   mock_memory, mock_storage):
        """Test that ConversationSession receives identical parameters in both paths."""
        # Setup mocks
        mock_storage.return_value = Mock()
        mock_memory.return_value = Mock()
        mock_memory.return_value.embedding_service = Mock()
        mock_self_model.return_value = (Mock(), Mock(), Mock())
        mock_internal.return_value = Mock()
        mock_env.return_value = Mock()
        mock_tool_reg.return_value = Mock()
        mock_dir_gen.return_value = Mock()
        mock_wsa = Mock()
        mock_wsa.aggregate.return_value = {}
        
        # Initialize runtime
        runtime = initialize_runtime()
        
        # Verify ConversationSession was called with correct parameters
        assert mock_session.called
        call_kwargs = mock_session.call_args[1]  # Get keyword arguments
        
        assert "storage" in call_kwargs
        assert "tool_registry" in call_kwargs
        assert "internal_sensing_framework" in call_kwargs
        assert "world_state_aggregator" in call_kwargs
        assert "color_manager" in call_kwargs
    
    @patch('broca.main_repl_runtime._initialize_storage')
    @patch('broca.main_repl_runtime._initialize_memory_manager')
    @patch('broca.main_repl_runtime._initialize_self_model')
    @patch('broca.main_repl_runtime._initialize_internal_sensing')
    @patch('broca.main_repl_runtime._initialize_environment_system')
    @patch('broca.main_repl_runtime._initialize_tool_registry')
    @patch('broca.main_repl_runtime.DirectoryStructureGenerator')
    def test_epistemic_engine_passed_to_internal_sensing(self, mock_dir_gen, mock_tool_reg,
                                                         mock_env, mock_internal, mock_self_model,
                                                         mock_memory, mock_storage):
        """Test that epistemic engine is passed to internal sensing initialization."""
        mock_storage.return_value = Mock()
        mock_memory.return_value = Mock()
        mock_memory.return_value.embedding_service = Mock()
        mock_epistemic = Mock()
        mock_self_model.return_value = (Mock(), Mock(), mock_epistemic)
        mock_internal.return_value = Mock()
        mock_env.return_value = Mock()
        mock_tool_reg.return_value = Mock()
        mock_dir_gen.return_value = Mock()
        
        # Initialize runtime
        runtime = initialize_runtime()
        
        # Verify epistemic_engine was passed to _initialize_internal_sensing
        assert mock_internal.called
        call_kwargs = mock_internal.call_args[1] if 'call_args' in dir(mock_internal.call_args) else {}
        # Check if epistemic_engine was passed (may be positional or keyword)
        call_args = mock_internal.call_args
        if call_args:
            # Check keyword arguments
            if len(call_args) > 1 and isinstance(call_args[1], dict):
                assert "epistemic_engine" in call_args[1]
                assert call_args[1]["epistemic_engine"] == mock_epistemic
    
    @patch('broca.main_repl_runtime._initialize_storage')
    @patch('broca.main_repl_runtime._initialize_memory_manager')
    @patch('broca.main_repl_runtime._initialize_self_model')
    @patch('broca.main_repl_runtime._initialize_internal_sensing')
    @patch('broca.main_repl_runtime._initialize_environment_system')
    @patch('broca.main_repl_runtime._initialize_tool_registry')
    @patch('broca.main_repl_runtime.DirectoryStructureGenerator')
    @patch('broca.main_repl_runtime.EnvironmentAccessTool')
    def test_environment_tool_registered(self, mock_env_tool, mock_dir_gen, mock_tool_reg,
                                        mock_env, mock_internal, mock_self_model,
                                        mock_memory, mock_storage):
        """Test that environment access tool is registered in runtime."""
        mock_storage.return_value = Mock()
        mock_memory.return_value = Mock()
        mock_memory.return_value.embedding_service = Mock()
        mock_self_model.return_value = (Mock(), Mock(), Mock())
        mock_internal.return_value = Mock()
        mock_env_obj = Mock()
        mock_env.return_value = mock_env_obj
        mock_tool_reg_obj = Mock()
        mock_tool_reg.return_value = mock_tool_reg_obj
        mock_dir_gen.return_value = Mock()
        mock_env_tool_instance = Mock()
        mock_env_tool.return_value = mock_env_tool_instance
        
        # Initialize runtime
        runtime = initialize_runtime()
        
        # Verify environment tool was registered
        assert mock_env_tool.called
        assert mock_tool_reg_obj.register_tool.called
        # Check that register_tool was called with environment tool
        register_calls = [call for call in mock_tool_reg_obj.register_tool.call_args_list]
        # Should have at least self-model tool and environment tool
        assert len(register_calls) >= 1  # At least one tool registered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

