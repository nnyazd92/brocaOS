"""
Policy manager for environment access system.

Manages access levels, approval tokens, and audit logging.
"""

from __future__ import annotations

import uuid
import time
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

from ..access_types import AccessLevel


@dataclass
class EscalationRequest:
    """Represents a request for access level escalation."""
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_level: AccessLevel = AccessLevel.SANDBOXED
    rationale: str = ""
    approved: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None


@dataclass
class ApprovalToken:
    """Represents an approval token for operations."""
    
    token: str
    operation: str
    parameters: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    used: bool = False


class PolicyManager:
    """
    Manages access policies and approval requirements.
    
    Handles access level escalation, approval tokens, and audit logging.
    """
    
    def __init__(self, initial_level: AccessLevel = AccessLevel.SANDBOXED) -> None:
        """
        Initialize policy manager.
        
        Args:
            initial_level: Initial access level (defaults to SANDBOXED)
        """
        self.current_level = initial_level
        self.approval_tokens: Dict[str, ApprovalToken] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self._escalation_requests: Dict[str, EscalationRequest] = {}
        self._escalation_request_timestamps: List[datetime] = []  # For rate limiting
        self._rate_limit_max_requests = 5  # Max requests per time window
        self._rate_limit_window_seconds = 60  # Time window in seconds
        self._emergency_access_active = False
        self._emergency_access_expires_at: Optional[datetime] = None
        self._emergency_access_duration_seconds = 300  # 5 minutes default
    
    def request_escalation(
        self, 
        target_level: AccessLevel, 
        rationale: str
    ) -> EscalationRequest:
        """
        Request policy escalation with user approval.
        
        Args:
            target_level: Target access level
            rationale: Reason for escalation request
            
        Returns:
            EscalationRequest object (not approved by default)
            
        Raises:
            ValueError: If rate limit exceeded
        """
        # Check rate limiting
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        window_start = now - timedelta(seconds=self._rate_limit_window_seconds)
        
        # Remove old timestamps outside the window
        self._escalation_request_timestamps = [
            ts for ts in self._escalation_request_timestamps
            if ts > window_start
        ]
        
        # Check if rate limit exceeded
        if len(self._escalation_request_timestamps) >= self._rate_limit_max_requests:
            raise ValueError(
                f"Rate limit exceeded: maximum {self._rate_limit_max_requests} "
                f"escalation requests per {self._rate_limit_window_seconds} seconds"
            )
        
        # Add current request timestamp
        self._escalation_request_timestamps.append(now)
        
        request = EscalationRequest(
            target_level=target_level,
            rationale=rationale
        )
        
        self._escalation_requests[request.request_id] = request
        
        # Log escalation request
        self.log_operation(
            "escalation_request",
            {
                "request_id": request.request_id,
                "current_level": self.current_level.value,
                "target_level": target_level.value,
                "rationale": rationale
            },
            "system",
            {"approved": False}
        )
        
        return request
    
    def approve_escalation(self, request_id: str) -> bool:
        """
        Approve an escalation request.
        
        Args:
            request_id: ID of the escalation request
            
        Returns:
            True if approval successful, False otherwise
        """
        if request_id not in self._escalation_requests:
            return False
        
        request = self._escalation_requests[request_id]
        request.approved = True
        request.approved_at = datetime.now(timezone.utc)
        self.current_level = request.target_level
        
        # Log escalation approval
        self.log_operation(
            "escalation",
            {
                "request_id": request_id,
                "target_level": request.target_level.value
            },
            "user",
            {"success": True}
        )
        
        return True
    
    def generate_approval_token(
        self,
        operation: str,
        parameters: Dict[str, Any],
        expires_in_seconds: Optional[float] = None
    ) -> str:
        """
        Generate an approval token for an operation.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            expires_in_seconds: Optional expiration time in seconds
            
        Returns:
            Approval token string
        """
        token = str(uuid.uuid4())
        expires_at = None
        if expires_in_seconds is not None:
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        
        approval_token = ApprovalToken(
            token=token,
            operation=operation,
            parameters=parameters,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at
        )
        
        self.approval_tokens[token] = approval_token
        
        return token
    
    def verify_approval_token(self, token: str) -> bool:
        """
        Verify an approval token validity.
        
        Args:
            token: Approval token to verify
            
        Returns:
            True if token is valid, False otherwise
        """
        if token not in self.approval_tokens:
            return False
        
        approval_token = self.approval_tokens[token]
        
        # Check if already used
        if approval_token.used:
            return False
        
        # Check if expired
        if approval_token.expires_at is not None:
            if datetime.now(timezone.utc) > approval_token.expires_at:
                return False
        
        return True
    
    def log_operation(
        self,
        operation: str,
        parameters: Dict[str, Any],
        user_id: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Log operation with full context and result.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            user_id: User identifier
            result: Operation result
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "parameters": parameters,
            "user_id": user_id,
            "result": result,
            "access_level": self.current_level.value
        }
        
        self.audit_log.append(log_entry)
    
    def get_audit_log(
        self,
        operation: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries with optional filtering.
        
        Args:
            operation: Filter by operation name
            user_id: Filter by user ID
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        entries = self.audit_log
        
        if operation:
            entries = [e for e in entries if e.get('operation') == operation]
        
        if user_id:
            entries = [e for e in entries if e.get('user_id') == user_id]
        
        if limit:
            entries = entries[-limit:]
        
        return entries
    
    def get_escalation_request(self, request_id: str) -> Optional[EscalationRequest]:
        """
        Get an escalation request by ID.
        
        Args:
            request_id: ID of the escalation request
            
        Returns:
            EscalationRequest if found, None otherwise
        """
        return self._escalation_requests.get(request_id)
    
    def downgrade_access(self, target_level: AccessLevel) -> bool:
        """
        Downgrade access level.
        
        Args:
            target_level: Target access level (must be lower than current)
            
        Returns:
            True if downgrade successful, False otherwise
        """
        # Can only downgrade to a lower level
        if target_level.value >= self.current_level.value:
            return False
        
        old_level = self.current_level
        self.current_level = target_level
        
        # Log downgrade
        self.log_operation(
            "downgrade_access",
            {
                "old_level": old_level.value,
                "new_level": target_level.value
            },
            "user",
            {"success": True}
        )
        
        return True
    
    def request_emergency_access(self, rationale: str, duration_seconds: int = 300) -> bool:
        """
        Request emergency access level.
        
        Args:
            rationale: Reason for emergency access
            duration_seconds: Duration of emergency access (default 5 minutes)
            
        Returns:
            True if emergency access granted, False otherwise
        """
        if not rationale:
            return False
        
        self.current_level = AccessLevel.EMERGENCY
        self._emergency_access_active = True
        from datetime import timedelta
        self._emergency_access_expires_at = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
        
        # Log emergency access request
        self.log_operation(
            "request_emergency_access",
            {
                "rationale": rationale,
                "duration_seconds": duration_seconds,
                "expires_at": self._emergency_access_expires_at.isoformat()
            },
            "user",
            {"success": True, "emergency": True}
        )
        
        return True
    
    def exit_emergency_access(self) -> bool:
        """
        Exit emergency access level.
        
        Returns:
            True if exit successful, False otherwise
        """
        if not self._emergency_access_active:
            return True  # Already not in emergency, idempotent
        
        old_level = self.current_level
        self.current_level = AccessLevel.SANDBOXED  # Revert to safest level
        self._emergency_access_active = False
        self._emergency_access_expires_at = None
        
        # Log exit
        self.log_operation(
            "exit_emergency_access",
            {
                "previous_level": old_level.value
            },
            "user",
            {"success": True}
        )
        
        return True
    
    def check_emergency_access_expired(self) -> bool:
        """
        Check if emergency access has expired.
        
        Returns:
            True if expired, False otherwise
        """
        if not self._emergency_access_active:
            return False
        
        if self._emergency_access_expires_at is None:
            return False
        
        if datetime.now(timezone.utc) > self._emergency_access_expires_at:
            # Auto-expire
            self.exit_emergency_access()
            return True
        
        return False
    
    def is_emergency_access_active(self) -> bool:
        """
        Check if emergency access is currently active.
        
        Returns:
            True if emergency access is active, False otherwise
        """
        # Check expiration first
        self.check_emergency_access_expired()
        return self._emergency_access_active

