"""
Comprehensive tests for approval workflow integration.

Tests the complete approval workflow including edge cases and error scenarios.
"""

from __future__ import annotations

import pytest
import tempfile
import time
from pathlib import Path

from broca.environment.tools.environment_tool import EnvironmentAccessTool
from broca.environment.access_types import AccessLevel


class TestApprovalWorkflowIntegration:
    """Test complete approval workflow integration."""
    
    def test_full_workflow_request_approve_use(self):
        """Test complete workflow: request → approve → use token."""
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
            
            # Request approval
            result = tool.execute(
                action="request_actuator_approval",
                actuator_id="filesystem_actuator",
                operation="create_file",
                parameters={"path": str(test_file), "content": "test"},
                rationale="Test file creation"
            )
            assert result["success"] is True
            approval_request_id = result["approval_request_id"]
            
            # Approve request
            result = tool.execute(
                action="approve_actuator_request",
                approval_request_id=approval_request_id
            )
            assert result["success"] is True
            token = result.get("approval_token")
            assert token is not None
            
            # Use token
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
    
    def test_token_reuse_until_expiration(self):
        """Test that tokens can be reused multiple times until expiration."""
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
            # Request approval and approve it
            result = tool.execute(
                action="request_actuator_approval",
                actuator_id="filesystem_actuator",
                operation="create_file",
                parameters={"path": str(Path(tmpdir) / "test1.txt"), "content": "test1"},
                rationale="Test"
            )
            approval_request_id = result["approval_request_id"]
            
            result = tool.execute(
                action="approve_actuator_request",
                approval_request_id=approval_request_id
            )
            token = result.get("approval_token")
            
            # Use token multiple times - should work since tokens are reusable
            for i in range(3):
                test_file = Path(tmpdir) / f"test_{i}.txt"
                result = tool.execute(
                    action="control_actuator",
                    actuator_id="filesystem_actuator",
                    operation="create_file",
                    parameters={
                        "path": str(test_file),
                        "content": f"test {i}",
                        "approval_token": token
                    }
                )
                assert result["success"] is True, f"Token reuse attempt {i+1} failed: {result.get('error')}"
                assert test_file.exists()
    
    def test_token_verification_expired_token(self):
        """Test that expired tokens are properly rejected."""
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
        
        # Manually create a token with very short expiration
        from broca.environment.actuators.approval import ApprovalSystem
        approval_system = tool.access_system.approval_system
        request = approval_system.get_approval_request(approval_request_id)
        request.approved = True
        
        # Generate token with 0.1 second expiration
        token = approval_system.generate_token(approval_request_id, expires_in_seconds=0.1)
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Try to use expired token
        result = tool.execute(
            action="control_actuator",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={
                "path": "/tmp/test.txt",
                "content": "test",
                "approval_token": token
            }
        )
        assert result["success"] is False
        assert "expired" in result["error"].lower() or "token" in result["error"].lower()
    
    def test_token_verification_nonexistent_token(self):
        """Test that non-existent tokens are properly rejected with clear error."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Try to use non-existent token
        result = tool.execute(
            action="control_actuator",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={
                "path": "/tmp/test.txt",
                "content": "test",
                "approval_token": "nonexistent-token-12345"
            }
        )
        assert result["success"] is False
        assert "token" in result["error"].lower()
        assert "not found" in result["error"].lower() or "invalid" in result["error"].lower()
    
    def test_verify_approval_token_action(self):
        """Test the verify_approval_token action directly."""
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
        
        # Verify invalid token
        result = tool.execute(
            action="verify_approval_token",
            approval_token="invalid-token"
        )
        assert result["success"] is True  # Verification action succeeds
        assert result["valid"] is False
        assert result.get("error") is not None
    
    def test_direct_token_usage_without_approve_action(self):
        """Test using a token directly in control_actuator without going through approve_actuator_request."""
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
        
        # Manually approve and generate token (simulating direct token generation)
        from broca.environment.actuators.approval import ApprovalSystem
        approval_system = tool.access_system.approval_system
        request = approval_system.get_approval_request(approval_request_id)
        request.approved = True
        token = approval_system.generate_token(approval_request_id)
        
        # Use token directly
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
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
    
    def test_multiple_concurrent_approval_requests(self):
        """Test multiple concurrent approval requests."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Create multiple approval requests
        approval_request_ids = []
        for i in range(3):
            result = tool.execute(
                action="request_actuator_approval",
                actuator_id="filesystem_actuator",
                operation="create_file",
                parameters={"path": f"/tmp/test{i}.txt", "content": f"test{i}"},
                rationale=f"Test {i}"
            )
            assert result["success"] is True
            approval_request_ids.append(result["approval_request_id"])
        
        # Approve all and use tokens
        tokens = []
        for approval_request_id in approval_request_ids:
            result = tool.execute(
                action="approve_actuator_request",
                approval_request_id=approval_request_id
            )
            assert result["success"] is True
            tokens.append(result.get("approval_token"))
        
        # All tokens should be valid
        for token in tokens:
            result = tool.execute(
                action="verify_approval_token",
                approval_token=token
            )
            assert result["success"] is True
            assert result["valid"] is True
    
    def test_error_message_clarity(self):
        """Test that error messages are clear and helpful."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Test non-existent token error
        result = tool.execute(
            action="control_actuator",
            actuator_id="filesystem_actuator",
            operation="create_file",
            parameters={
                "path": "/tmp/test.txt",
                "content": "test",
                "approval_token": "invalid-token-123"
            }
        )
        assert result["success"] is False
        assert "error" in result
        error_msg = result["error"].lower()
        # Error should mention token
        assert "token" in error_msg or "approval" in error_msg
    
    def test_operation_without_approval_when_not_required(self):
        """Test operations that don't require approval can be executed directly."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Operations like read_file don't require approval
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            result = tool.execute(
                action="control_actuator",
                actuator_id="filesystem_actuator",
                operation="read_file",
                parameters={"path": str(test_file)}
            )
            assert result["success"] is True
            assert "content" in result.get("data", {})
    
    def test_token_validation_edge_cases(self):
        """Test edge cases in token validation."""
        tool = EnvironmentAccessTool()
        
        # Escalate to AUTONOMOUS
        result = tool.execute(
            action="request_escalation",
            target_level="AUTONOMOUS",
            rationale="Test"
        )
        request_id = result["request_id"]
        tool.execute(action="approve_escalation", request_id=request_id)
        
        # Test empty token string
        result = tool.execute(
            action="verify_approval_token",
            approval_token=""
        )
        assert result["success"] is False  # Should fail validation
        assert "required" in result["error"].lower()
        
        # Test None token (should be handled gracefully)
        result = tool.execute(
            action="verify_approval_token",
            approval_token=None
        )
        assert result["success"] is False
        assert "required" in result["error"].lower()

