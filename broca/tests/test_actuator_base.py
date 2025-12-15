"""
Tests for actuator base classes and protocol compliance.
"""

from __future__ import annotations

import pytest
from abc import ABC

from broca.environment.actuators.base import Actuator, ActivationResult, DeactivationResult


class TestActuatorProtocol:
    """Test actuator protocol compliance."""
    
    def test_actuator_is_abstract(self):
        """Test that Actuator is an abstract base class."""
        assert issubclass(Actuator, ABC)
        
        # Cannot instantiate directly
        with pytest.raises(TypeError):
            Actuator("test", 0.5)
    
    def test_actuator_has_required_methods(self):
        """Test that Actuator defines required abstract methods."""
        assert hasattr(Actuator, 'activate')
        assert hasattr(Actuator, 'deactivate')
        assert hasattr(Actuator, 'emergency_stop')


class TestActuatorInitialization:
    """Test actuator initialization."""
    
    def test_actuator_has_safety_interlock(self):
        """Test that actuators have safety interlocks."""
        from broca.environment.actuators.base import Actuator
        from unittest.mock import Mock
        
        # Create a concrete implementation for testing
        class TestActuator(Actuator):
            def activate(self, parameters):
                return ActivationResult(success=True)
            
            def deactivate(self):
                return DeactivationResult(success=True)
            
            def emergency_stop(self):
                return DeactivationResult(success=True)
        
        actuator = TestActuator("test_actuator", 0.5)
        
        assert actuator.id == "test_actuator"
        assert actuator.max_power == 0.5
        assert actuator.current_state == 'idle'
        assert actuator.safety_interlock is not None

