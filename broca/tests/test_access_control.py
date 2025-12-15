"""
Tests for access control enforcement.

Tests that operations are gated by access level requirements.
"""

from __future__ import annotations

import pytest

from broca.environment.tools.environment_tool import EnvironmentAccessTool
from broca.environment.access_types import AccessLevel
from broca.environment.access_control import AccessControl


class TestAccessControlEnforcement:
    """Test access level enforcement."""
    
    def test_read_sensor_allowed_at_sandboxed(self):
        """Test that reading system sensors is allowed at SANDBOXED level."""
        tool = EnvironmentAccessTool()
        tool.access_system.discover_and_register_sensors()
        
        # Get a sensor ID
        sensors = tool.access_system.sensor_registry.sensors
        if sensors:
            sensor_id = list(sensors.keys())[0]
            result = tool.execute(action="read_sensor", sensor_id=sensor_id)
            
            # Should not fail due to access level (may fail for other reasons)
            assert "access level" not in result.get("error", "").lower() or result["success"] is True
    
    def test_list_actuators_requires_supervised(self):
        """Test that listing actuators requires SUPERVISED level."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="list_actuators")
        
        assert result["success"] is False
        assert "SUPERVISED" in result["error"] or "access level" in result["error"].lower()
    
    def test_control_actuator_requires_autonomous(self):
        """Test that controlling actuators requires AUTONOMOUS level."""
        tool = EnvironmentAccessTool()
        
        # Escalate to SUPERVISED first
        result = tool.execute(
            action="request_escalation",
            target_level="SUPERVISED",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Try to control actuator at SUPERVISED (should fail)
        result = tool.execute(
            action="control_actuator",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={"path": "/tmp/test.txt", "content": "test"}
        )
        
        assert result["success"] is False
        assert "AUTONOMOUS" in result["error"] or "access level" in result["error"].lower()
    
    def test_filesystem_sensor_requires_supervised(self):
        """Test that filesystem sensors require SUPERVISED level."""
        tool = EnvironmentAccessTool()
        tool.access_system.discover_and_register_sensors()
        
        # Find a filesystem sensor
        for sensor_id, sensor in tool.access_system.sensor_registry.sensors.items():
            if getattr(sensor, 'sensor_type', None) == 'filesystem':
                result = tool.execute(action="read_sensor", sensor_id=sensor_id)
                
                # Should fail at SANDBOXED level
                assert result["success"] is False
                assert "SUPERVISED" in result["error"] or "access level" in result["error"].lower()
                break


class TestAccessControlClass:
    """Test AccessControl class directly."""
    
    def test_check_operation_access_allowed(self):
        """Test that allowed operations pass."""
        result = AccessControl.check_operation_access(
            operation="read_sensor",
            current_level=AccessLevel.SANDBOXED,
            sensor_type="system"
        )
        
        assert result.allowed is True
    
    def test_check_operation_access_denied(self):
        """Test that denied operations fail."""
        result = AccessControl.check_operation_access(
            operation="control_actuator",
            current_level=AccessLevel.SUPERVISED
        )
        
        assert result.allowed is False
        assert "AUTONOMOUS" in result.error

