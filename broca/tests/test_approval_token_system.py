"""
Tests for approval token system integration.

Tests requesting, approving, and using approval tokens for actuator operations.
"""

from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from broca.environment.tools.environment_tool import EnvironmentAccessTool
from broca.environment.access_types import AccessLevel


class TestRequestActuatorApproval:
    """Test requesting approval for actuator operations."""
    
    def test_request_actuator_approval(self):
        """Test requesting approval for an actuator operation."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS first (required for approval token generation)
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Request approval for actuator operation
        result = tool.execute(
            action="request_actuator_approval",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={"path": "/tmp/test.txt", "content": "test"},
            rationale="Test file creation"
        )
        
        assert result["success"] is True
        assert "approval_request_id" in result
        assert "safety_analysis" in result
    
    def test_request_actuator_approval_missing_parameters(self):
        """Test requesting approval without required parameters."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="request_actuator_approval")
        
        assert result["success"] is False
        assert "actuator_id" in result["error"].lower() or "operation" in result["error"].lower()


class TestApproveActuatorRequest:
    """Test approving actuator approval requests."""
    
    def test_approve_actuator_request(self):
        """Test approving an actuator approval request."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Request approval
        result = tool.execute(
            action="request_actuator_approval",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={"path": "/tmp/test.txt", "content": "test"},
            rationale="Test"
        )
        approval_request_id = result["approval_request_id"]
        
        # Approve it
        result = tool.execute(
            action="approve_actuator_request",
            approval_request_id=approval_request_id
        )
        
        assert result["success"] is True
        assert "approval_token" in result or "token" in result
    
    def test_approve_actuator_request_missing_id(self):
        """Test approving without approval_request_id."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(action="approve_actuator_request")
        
        assert result["success"] is False
        assert "approval_request_id" in result["error"].lower()


class TestGenerateApprovalToken:
    """Test generating approval tokens."""
    
    def test_generate_approval_token(self):
        """Test generating an approval token."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Request approval
        result = tool.execute(
            action="request_actuator_approval",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={"path": "/tmp/test.txt", "content": "test"},
            rationale="Test"
        )
        approval_request_id = result["approval_request_id"]
        
        # Approve the request first
        tool.execute(action="approve_actuator_request", approval_request_id=approval_request_id)
        
        # Generate token
        result = tool.execute(
            action="generate_approval_token",
            approval_request_id=approval_request_id
        )
        
        assert result["success"] is True
        assert "approval_token" in result or "token" in result
        assert len(result.get("approval_token", result.get("token", ""))) > 0
    
    def test_generate_approval_token_requires_autonomous(self):
        """Test that generating tokens requires AUTONOMOUS level."""
        tool = EnvironmentAccessTool()
        
        # At SANDBOXED level, should fail
        result = tool.execute(
            action="generate_approval_token",
            approval_request_id="test_id"
        )
        
        assert result["success"] is False
        assert "AUTONOMOUS" in result["error"] or "access level" in result["error"].lower()


class TestVerifyApprovalToken:
    """Test verifying approval tokens."""
    
    def test_verify_approval_token_valid(self):
        """Test verifying a valid approval token."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Request approval and approve it
        result = tool.execute(
            action="request_actuator_approval",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={"path": "/tmp/test.txt", "content": "test"},
            rationale="Test"
        )
        approval_request_id = result["approval_request_id"]
        
        # Approve and get token
        result = tool.execute(
            action="approve_actuator_request",
            approval_request_id=approval_request_id
        )
        token = result.get("approval_token")
        
        # Verify token
        result = tool.execute(
            action="verify_approval_token",
            approval_token=token
        )
        
        assert result["success"] is True
        assert result["valid"] is True
    
    def test_verify_approval_token_invalid(self):
        """Test verifying an invalid approval token."""
        tool = EnvironmentAccessTool()
        
        result = tool.execute(
            action="verify_approval_token",
            approval_token="invalid_token"
        )
        
        assert result["success"] is True  # Verification itself succeeds
        assert result["valid"] is False


class TestUseApprovalTokenForActuator:
    """Test using approval tokens for actuator operations."""
    
    def test_control_actuator_with_approval_token(self):
        """Test controlling actuator with valid approval token."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            
            # Request approval and approve it to get token
            result = tool.execute(
                action="request_actuator_approval",
                actuator_id="filesystem_actuator",
                operation="create_file",
                parameters={"path": str(test_file), "content": "test content"},
                rationale="Test"
            )
            approval_request_id = result["approval_request_id"]
            
            # Approve to get token
            result = tool.execute(
                action="approve_actuator_request",
                approval_request_id=approval_request_id
            )
            token = result.get("approval_token")
            
            # Use token to control actuator
            result = tool.execute(
                action="control_actuator",
                actuator_id="filesystem_actuator",
                operation="create_file",
                parameters={
                    "path": str(test_file),
                    "content": "test content",
                    "approval_token": token
                }
            )
            
            assert result["success"] is True
            assert test_file.exists()
    
    def test_control_actuator_with_invalid_token(self):
        """Test controlling actuator with invalid token fails."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        result = tool.execute(
            action="control_actuator",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={
                "path": "/tmp/test.txt",
                "content": "test",
                "approval_token": "invalid_token"
            }
        )
        
        assert result["success"] is False
        assert "token" in result["error"].lower() or "approval" in result["error"].lower()

