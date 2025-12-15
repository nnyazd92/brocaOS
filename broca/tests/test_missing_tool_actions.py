"""
Tests for missing tool actions.

Tests approve_escalation, check_escalation_status, downgrade_access, list_actuators, control_actuator.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from broca.environment.tools.environment_tool import EnvironmentAccessTool
from broca.environment.access_types import AccessLevel


class TestApproveEscalationAction:
    """Test approve_escalation action."""
    
    def test_approve_escalation_success(self):
        """Test successfully approving an escalation."""
        tool = EnvironmentAccessTool()
        
        # Create an escalation request first
        result = tool.execute(
            action="request_escalation",
            target_level="SUPERVISED",
            rationale="Test escalation"
        )
        request_id = result["request_id"]
        
        # Approve it
        result = tool.execute(action="approve_escalation", request_id=request_id)
        
        assert result["success"] is True
        assert tool.access_system.get_access_level() == AccessLevel.SUPERVISED
    
    def test_approve_escalation_missing_request_id(self):
        """Test approving escalation without request_id."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="approve_escalation")
        
        assert result["success"] is False
        assert "request_id" in result["error"].lower()
    
    def test_approve_escalation_invalid_request_id(self):
        """Test approving escalation with invalid request_id."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="approve_escalation", request_id="invalid_id")
        
        assert result["success"] is False


class TestCheckEscalationStatusAction:
    """Test check_escalation_status action."""
    
    def test_check_escalation_status_exists(self):
        """Test checking status of existing escalation request."""
        tool = EnvironmentAccessTool()
        
        # Create an escalation request
        result = tool.execute(
            action="request_escalation",
            target_level="SUPERVISED",
            rationale="Test"
        )
        request_id = result["request_id"]
        
        # Check its status
        result = tool.execute(action="check_escalation_status", request_id=request_id)
        
        assert result["success"] is True
        assert result["request_id"] == request_id
        assert "approved" in result
    
    def test_check_escalation_status_missing_request_id(self):
        """Test checking status without request_id."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="check_escalation_status")
        
        assert result["success"] is False
        assert "request_id" in result["error"].lower()
    
    def test_check_escalation_status_not_found(self):
        """Test checking status of non-existent request."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="check_escalation_status", request_id="nonexistent")
        
        assert result["success"] is False


class TestDowngradeAccessAction:
    """Test downgrade_access action."""
    
    def test_downgrade_access_from_supervised(self):
        """Test downgrading from SUPERVISED to SANDBOXED."""
        tool = EnvironmentAccessTool()
        
        # First escalate
        result = tool.execute(
            action="request_escalation",
            target_level="SUPERVISED",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Now downgrade
        result = tool.execute(action="downgrade_access", target_level="SANDBOXED")
        
        assert result["success"] is True
        assert tool.access_system.get_access_level() == AccessLevel.SANDBOXED
    
    def test_downgrade_access_missing_target_level(self):
        """Test downgrading without target_level."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="downgrade_access")
        
        assert result["success"] is False
        assert "target_level" in result["error"].lower()


class TestListActuatorsAction:
    """Test list_actuators action."""
    
    def test_list_actuators_requires_supervised(self):
        """Test listing actuators requires SUPERVISED access level."""
        tool = EnvironmentAccessTool()
        
        # Should fail at SANDBOXED level
        result = tool.execute(action="list_actuators")
        
        assert result["success"] is False
        assert "SUPERVISED" in result["error"] or "access level" in result["error"].lower()
    
    def test_list_actuators_with_supervised_access(self):
        """Test listing available actuators with SUPERVISED access."""
        tool = EnvironmentAccessTool()
        
        # Escalate to SUPERVISED
        result = tool.execute(
            action="request_escalation",
            target_level="SUPERVISED",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Now should work
        result = tool.execute(action="list_actuators")
        
        assert result["success"] is True
        assert "actuators" in result
        assert "count" in result
        assert isinstance(result["actuators"], list)


class TestControlActuatorAction:
    """Test control_actuator action."""
    
    def test_control_actuator_missing_parameters(self):
        """Test controlling actuator without required parameters."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="control_actuator")
        
        assert result["success"] is False
        assert "actuator_id" in result["error"].lower() or "operation" in result["error"].lower()
    
    def test_control_actuator_requires_approval(self):
        """Test that actuator control requires approval."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(
            action="control_actuator",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={"path": "/tmp/test.txt", "content": "test"}
        )
        
        # Should require approval or fail due to access level
        assert result["success"] is False or "approval" in result.get("message", "").lower()

