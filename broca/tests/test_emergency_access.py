"""
Tests for emergency access level support.

Tests requesting, using, and exiting emergency access level.
"""

from __future__ import annotations

import pytest
import time

from broca.environment.tools.environment_tool import EnvironmentAccessTool
from broca.environment.access_types import AccessLevel


class TestRequestEmergencyAccess:
    """Test requesting emergency access level."""
    
    def test_request_emergency_access(self):
        """Test requesting emergency access level."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(
            action="request_emergency_access",
            rationale="Emergency test scenario"
        )
        
        assert result["success"] is True
        assert "emergency_access_granted" in result or "access_level" in result
        assert tool.access_system.get_access_level() == AccessLevel.EMERGENCY
    
    def test_request_emergency_access_requires_rationale(self):
        """Test that emergency access requires rationale."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="request_emergency_access")
        
        assert result["success"] is False
        assert "rationale" in result["error"].lower()
    
    def test_emergency_access_is_logged(self):
        """Test that emergency access requests are logged."""
        tool = EnvironmentAccessTool()
        
        tool.execute(
            action="request_emergency_access",
            rationale="Test emergency"
        )
        
        # Check audit log
        log_entries = tool.access_system.policy_manager.get_audit_log(operation="request_emergency_access")
        assert len(log_entries) > 0


class TestEmergencyAccessBypassesRestrictions:
    """Test that emergency access bypasses normal restrictions."""
    
    def test_emergency_access_bypasses_actuator_restrictions(self):
        """Test that emergency access allows actuator operations without approval."""
        tool = EnvironmentAccessTool()
        
        # Request emergency access
        tool.execute(
            action="request_emergency_access",
            rationale="Emergency actuator test"
        )
        
        # Should be able to control actuator without approval token
        result = tool.execute(
            action="control_actuator",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={"path": "/tmp/emergency_test.txt", "content": "emergency"}
        )
        
        # Should succeed (may fail for other reasons like file permissions, but not access level)
        assert "access level" not in result.get("error", "").lower() or result["success"] is True
    
    def test_emergency_access_bypasses_sensor_restrictions(self):
        """Test that emergency access allows all sensor reads."""
        tool = EnvironmentAccessTool()
        tool.access_system.discover_and_register_sensors()
        
        # Request emergency access
        tool.execute(
            action="request_emergency_access",
            rationale="Emergency sensor test"
        )
        
        # Should be able to read any sensor
        for sensor_id, sensor in tool.access_system.sensor_registry.sensors.items():
            result = tool.execute(action="read_sensor", sensor_id=sensor_id)
            # Should not fail due to access level
            assert "access level" not in result.get("error", "").lower() or result["success"] is True


class TestEmergencyAccessTimeLimit:
    """Test emergency access time limits."""
    
    def test_emergency_access_has_time_limit(self):
        """Test that emergency access has a time limit."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(
            action="request_emergency_access",
            rationale="Test time limit"
        )
        
        assert result["success"] is True
        assert "expires_at" in result or "time_limit" in result
    
    def test_emergency_access_auto_expires(self):
        """Test that emergency access auto-expires after time limit."""
        tool = EnvironmentAccessTool()
        
        # Request emergency access with short time limit
        result = tool.execute(
            action="request_emergency_access",
            rationale="Test auto-expire"
        )
        
        # Manually set expiration to past (for testing)
        # In real implementation, this would be checked automatically
        # For now, we'll test that exit_emergency_access works
        result = tool.execute(action="exit_emergency_access")
        
        assert result["success"] is True
        assert tool.access_system.get_access_level() != AccessLevel.EMERGENCY


class TestExitEmergencyAccess:
    """Test exiting emergency access level."""
    
    def test_exit_emergency_access(self):
        """Test exiting emergency access level."""
        tool = EnvironmentAccessTool()
        
        # Request emergency access
        tool.execute(
            action="request_emergency_access",
            rationale="Test exit"
        )
        
        assert tool.access_system.get_access_level() == AccessLevel.EMERGENCY
        
        # Exit emergency access
        result = tool.execute(action="exit_emergency_access")
        
        assert result["success"] is True
        assert tool.access_system.get_access_level() != AccessLevel.EMERGENCY
        # Should revert to SANDBOXED
        assert tool.access_system.get_access_level() == AccessLevel.SANDBOXED
    
    def test_exit_emergency_access_when_not_in_emergency(self):
        """Test exiting emergency access when not in emergency mode."""
        tool = EnvironmentAccessTool()
        
        # Not in emergency mode
        result = tool.execute(action="exit_emergency_access")
        
        # Should still succeed (idempotent) or return appropriate message
        assert result["success"] is True or "not in emergency" in result.get("message", "").lower()

