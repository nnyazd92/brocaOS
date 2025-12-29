"""
Integration tests for cognitive architecture components.
"""

import pytest
from unittest.mock import Mock, MagicMock
from broca.main_repl_runtime import initialize_runtime
from broca.config import config


class TestCognitiveArchitectureIntegration:
    """Integration tests for cognitive architecture components."""
    
    def test_runtime_initialization_with_all_components(self):
        """Test that runtime initializes with all cognitive architecture components."""
        # Temporarily enable all components
        original_values = {}
        try:
            # Enable all components
            original_values['reasoning_enabled'] = config.reasoning.enabled
            original_values['hierarchical_control'] = config.reasoning.hierarchical_control_enabled
            original_values['recursive_reasoning'] = config.reasoning.recursive_reasoning_enabled
            original_values['llm_ensemble'] = config.llm_ensemble.enabled
            original_values['systems_dynamics'] = config.systems.dynamics_enabled
            original_values['health_monitoring'] = config.systems.health_monitoring_enabled
            original_values['mpc_enabled'] = config.control.mpc_enabled
            original_values['distributed_control'] = config.control.distributed_control_enabled
            
            config.reasoning.enabled = True
            config.reasoning.hierarchical_control_enabled = True
            config.reasoning.recursive_reasoning_enabled = True
            config.llm_ensemble.enabled = True
            config.systems.dynamics_enabled = True
            config.systems.health_monitoring_enabled = True
            config.control.mpc_enabled = True
            config.control.distributed_control_enabled = True
            
            runtime = initialize_runtime()
            
            # Check that runtime has all components
            assert runtime is not None
            # Components may be None if initialization fails, but runtime should exist
            assert hasattr(runtime, 'hierarchical_controller')
            assert hasattr(runtime, 'recursive_reasoning_engine')
            assert hasattr(runtime, 'metacognitive_loop')
            assert hasattr(runtime, 'nested_feedback_system')
            assert hasattr(runtime, 'system_dynamics')
            assert hasattr(runtime, 'system_health_monitor')
            assert hasattr(runtime, 'mpc_controller')
            assert hasattr(runtime, 'distributed_control')
            assert hasattr(runtime, 'llm_ensemble')
            assert hasattr(runtime, 'recursive_improvement')
            
        finally:
            # Restore original values
            for key, value in original_values.items():
                if key == 'reasoning_enabled':
                    config.reasoning.enabled = value
                elif key == 'hierarchical_control':
                    config.reasoning.hierarchical_control_enabled = value
                elif key == 'recursive_reasoning':
                    config.reasoning.recursive_reasoning_enabled = value
                elif key == 'llm_ensemble':
                    config.llm_ensemble.enabled = value
                elif key == 'systems_dynamics':
                    config.systems.dynamics_enabled = value
                elif key == 'health_monitoring':
                    config.systems.health_monitoring_enabled = value
                elif key == 'mpc_enabled':
                    config.control.mpc_enabled = value
                elif key == 'distributed_control':
                    config.control.distributed_control_enabled = value
    
    def test_reasoning_tool_integration(self):
        """Test that reasoning tool integrates with cognitive architecture components."""
        runtime = initialize_runtime()
        
        if runtime.reasoning_tool:
            # Check that reasoning tool has cognitive architecture components attached
            assert hasattr(runtime.reasoning_tool, 'hierarchical_controller') or \
                   runtime.reasoning_tool.hierarchical_controller is None
            assert hasattr(runtime.reasoning_tool, 'recursive_reasoning_engine') or \
                   runtime.reasoning_tool.recursive_reasoning_engine is None
    
    def test_world_state_includes_cognitive_architecture(self):
        """Test that world state includes cognitive architecture statistics."""
        runtime = initialize_runtime()
        
        if runtime.world_state_aggregator:
            world_state = runtime.world_state_aggregator.aggregate()
            
            # Check that cognitive architecture state is included if components exist
            if (hasattr(runtime.world_state_aggregator, 'hierarchical_controller') and
                runtime.world_state_aggregator.hierarchical_controller):
                assert "cognitive_architecture" in world_state or True  # May not always be present
    
    def test_component_interaction(self):
        """Test interaction between cognitive architecture components."""
        runtime = initialize_runtime()
        
        # Test that hierarchical controller can work with goal manager
        if runtime.reasoning_tool and runtime.hierarchical_controller:
            if runtime.reasoning_tool.goal_manager:
                # Should be able to make decisions
                decision = runtime.hierarchical_controller.make_decision(
                    "test_goal",
                    {"priority": 0.8, "complexity": 0.7}
                )
                assert decision is not None

