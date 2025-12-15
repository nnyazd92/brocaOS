"""
Tests for PolicyManager implementation.

Tests policy escalation, approval tokens, and audit logging.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from broca.environment.policy.manager import PolicyManager
from broca.environment.access_types import AccessLevel


class TestPolicyManagerInitialization:
    """Test PolicyManager initialization."""
    
    def test_init_defaults_to_sandboxed(self):
        """Test that policy manager defaults to SANDBOXED level."""
        manager = PolicyManager()
        
        assert manager.current_level == AccessLevel.SANDBOXED
        assert isinstance(manager.approval_tokens, dict)
        assert isinstance(manager.audit_log, list)
    
    def test_init_with_custom_level(self):
        """Test initialization with custom access level."""
        manager = PolicyManager(initial_level=AccessLevel.SUPERVISED)
        
        assert manager.current_level == AccessLevel.SUPERVISED


class TestPolicyManagerEscalation:
    """Test policy escalation functionality."""
    
    def test_request_escalation_creates_request(self):
        """Test that escalation request is created."""
        manager = PolicyManager()
        
        request = manager.request_escalation(AccessLevel.SUPERVISED, "Test rationale")
        
        assert request is not None
        assert request.target_level == AccessLevel.SUPERVISED
        assert request.rationale == "Test rationale"
        assert request.approved is False
    
    def test_escalation_requires_user_approval(self):
        """Test that escalation requires explicit user approval."""
        manager = PolicyManager()
        
        request = manager.request_escalation(AccessLevel.SUPERVISED, "Test")
        
        # Without approval, level should not change
        assert manager.current_level == AccessLevel.SANDBOXED
        assert request.approved is False
    
    def test_approve_escalation_changes_level(self):
        """Test that approving escalation changes access level."""
        manager = PolicyManager()
        
        request = manager.request_escalation(AccessLevel.SUPERVISED, "Test")
        manager.approve_escalation(request.request_id)
        
        assert manager.current_level == AccessLevel.SUPERVISED
        assert request.approved is True
    
    def test_escalation_logged_in_audit(self):
        """Test that escalations are logged in audit log."""
        manager = PolicyManager()
        
        request = manager.request_escalation(AccessLevel.SUPERVISED, "Test")
        manager.approve_escalation(request.request_id)
        
        assert len(manager.audit_log) > 0
        # Check for escalation operation in audit log
        assert any(
            entry.get('operation') == 'escalation' and 
            entry.get('parameters', {}).get('target_level') == AccessLevel.SUPERVISED.value
            for entry in manager.audit_log
        )


class TestPolicyManagerApprovalTokens:
    """Test approval token system."""
    
    def test_generate_approval_token(self):
        """Test generating an approval token."""
        manager = PolicyManager()
        
        token = manager.generate_approval_token("test_operation", {"param": "value"})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        assert token in manager.approval_tokens
    
    def test_verify_approval_token_valid(self):
        """Test verifying a valid approval token."""
        manager = PolicyManager()
        
        token = manager.generate_approval_token("test_operation", {"param": "value"})
        result = manager.verify_approval_token(token)
        
        assert result is True
    
    def test_verify_approval_token_invalid(self):
        """Test verifying an invalid approval token."""
        manager = PolicyManager()
        
        result = manager.verify_approval_token("invalid_token")
        assert result is False
    
    def test_approval_token_expires(self):
        """Test that approval tokens can expire."""
        manager = PolicyManager()
        
        token = manager.generate_approval_token("test_operation", {}, expires_in_seconds=0.1)
        
        import time
        time.sleep(0.2)
        
        result = manager.verify_approval_token(token)
        assert result is False


class TestPolicyManagerAuditLog:
    """Test audit logging functionality."""
    
    def test_log_operation(self):
        """Test logging an operation."""
        manager = PolicyManager()
        
        manager.log_operation("test_operation", {"param": "value"}, "user123", {"success": True})
        
        assert len(manager.audit_log) > 0
        assert manager.audit_log[-1]['operation'] == "test_operation"
        assert manager.audit_log[-1]['user_id'] == "user123"
    
    def test_audit_log_contains_timestamp(self):
        """Test that audit log entries contain timestamps."""
        manager = PolicyManager()
        
        manager.log_operation("test_operation", {}, "user123", {})
        
        entry = manager.audit_log[-1]
        assert 'timestamp' in entry
        assert isinstance(entry['timestamp'], (str, datetime))
    
    def test_get_audit_log_filtered(self):
        """Test getting filtered audit log entries."""
        manager = PolicyManager()
        
        manager.log_operation("operation1", {}, "user1", {})
        manager.log_operation("operation2", {}, "user2", {})
        manager.log_operation("operation1", {}, "user1", {})
        
        filtered = manager.get_audit_log(operation="operation1")
        
        assert len(filtered) == 2
        assert all(entry['operation'] == "operation1" for entry in filtered)

