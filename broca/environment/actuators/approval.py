"""
Approval system for actuator operations.

Provides multi-layer approval system with token-based verification.

The approval workflow:
1. Request approval: Create an approval request for an actuator operation
2. Approve request: User approves the request (sets approved=True)
3. Generate token: Generate a reusable approval token from an approved request
4. Verify token: Verify token is valid (not expired, exists in system)
5. Use token: Use token in control_actuator operation

Tokens are reusable until expiration. Once expired, they cannot be used.
"""

from __future__ import annotations

import uuid
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from broca.token_auth.token import verify_token as verify_jwt_token
from broca.token_auth.defaults import get_default_identity
import json
import time as time_module
import hmac
import hashlib
import base64

logger = logging.getLogger(__name__)


def _b64url(data: bytes) -> str:
    """Base64 URL-safe encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


@dataclass
class ApprovalRequest:
    """
    Represents an approval request for an actuator operation.
    
    Created when requesting approval for an operation. Must be approved
    (approved=True) before a token can be generated.
    
    Attributes:
        request_id: Unique identifier for the request (UUID)
        operation: Name of the operation being requested
        parameters: Operation-specific parameters
        rationale: Reason/justification for the operation
        safety_analysis: Safety analysis results (risk_level, requires_approval)
        approved: Whether the request has been approved (default: False)
        created_at: Timestamp when request was created (UTC)
        actuator_id: ID of the actuator this request is for (optional, for scope determination)
    """
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    safety_analysis: Dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actuator_id: Optional[str] = None


@dataclass
class ApprovalToken:
    """
    Represents an approval token for actuator operations.
    
    Tokens are reusable until expiration. The `used` field is present for
    future extensibility but is not currently enforced (tokens remain reusable).
    
    Attributes:
        token: Unique token string identifier
        request_id: ID of the approval request this token was generated from
        expires_at: Expiration timestamp (UTC)
        used: Whether token has been used (currently not enforced for reusable tokens)
    """
    
    token: str
    request_id: str
    expires_at: datetime
    used: bool = False  # Note: Currently not enforced - tokens are reusable until expiration


@dataclass
class VerificationResult:
    """
    Result of approval token verification.
    
    Returned by verify_approval() to indicate whether a token is valid.
    
    Attributes:
        valid: True if token is valid and can be used, False otherwise
        error: Error message explaining why token is invalid (if valid=False)
    """
    
    valid: bool
    error: Optional[str] = None


class ApprovalSystem:
    """
    Multi-layer approval system for actuator operations.
    
    Provides token-based approval workflow for actuator operations. The workflow is:
    
    1. Request Approval: Create an approval request for an operation
    2. Approve Request: Set request.approved = True (typically by user/admin)
    3. Generate Token: Create a reusable JWT token from an approved request
    4. Verify Token: Check token validity before use (supports JWT and legacy UUID tokens)
    5. Use Token: Provide token when calling control_actuator
    
    Tokens are reusable until expiration (default: 5 minutes). Once expired,
    they cannot be used and a new token must be generated.
    
    Tokens are now JWT format (unified with token_auth system), but legacy UUID
    tokens are still supported for backward compatibility.
    
    Attributes:
        approval_chain: List of all approval requests (historical record)
        tokens: Dictionary mapping token strings to ApprovalToken objects (for legacy UUID tokens)
        emergency_override: Emergency override flag (for bypassing approval)
        _approval_requests: Internal dictionary mapping request_id to ApprovalRequest
    """
    
    # Map actuator types to required scopes
    ACTUATOR_SCOPE_MAP: Dict[str, List[str]] = {
        "filesystem_actuator": ["filesystem:write"],
        "default": ["filesystem:write", "project:write", "memory:write"],  # Default scopes for unknown actuators
    }
    
    def __init__(self) -> None:
        """
        Initialize approval system.
        
        Creates empty approval chain, token store, and request registry.
        """
        self.approval_chain: List[ApprovalRequest] = []
        self.tokens: Dict[str, ApprovalToken] = {}  # Legacy UUID token storage
        self.emergency_override = False
        self._approval_requests: Dict[str, ApprovalRequest] = {}  # request_id -> ApprovalRequest
        logger.debug("Initialized ApprovalSystem")
    
    def request_approval(
        self,
        operation: str,
        parameters: Dict[str, Any],
        rationale: str,
        actuator_id: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Create approval request with safety analysis.
        
        This is the first step in the approval workflow. Creates a request that
        must be approved before a token can be generated.
        
        Args:
            operation: Operation name (e.g., "create_file", "delete_file")
            parameters: Operation parameters (specific to the operation)
            rationale: Reason/justification for the operation
            
        Returns:
            ApprovalRequest object (initially with approved=False)
            
        Example:
            >>> request = approval_system.request_approval(
            ...     operation="create_file",
            ...     parameters={"path": "/tmp/test.txt", "content": "data"},
            ...     rationale="Creating test file for validation"
            ... )
            >>> # Later: request.approved = True
            >>> # Then: token = approval_system.generate_token(request.request_id)
        """
        # Perform safety analysis
        safety_analysis = self._analyze_safety(operation, parameters)
        
        request = ApprovalRequest(
            operation=operation,
            parameters=parameters,
            rationale=rationale,
            safety_analysis=safety_analysis,
            actuator_id=actuator_id
        )
        
        self.approval_chain.append(request)
        self._approval_requests[request.request_id] = request
        
        logger.info(
            f"Created approval request '{request.request_id}' for operation '{operation}' "
            f"(risk_level: {safety_analysis.get('risk_level', 'unknown')})"
        )
        return request
    
    def verify_approval(self, token: str, required_scopes: Optional[List[str]] = None, actuator_id: Optional[str] = None) -> VerificationResult:
        """
        Verify approval token validity.
        
        Checks that the token exists, is not expired, and is valid for use.
        Supports both JWT tokens (from token_auth) and legacy UUID tokens.
        Tokens are reusable until expiration.
        
        Args:
            token: Approval token string to verify (JWT or legacy UUID)
            required_scopes: Optional list of required scopes (for JWT tokens)
            
        Returns:
            VerificationResult with valid=True if token is valid, valid=False otherwise.
            Error message is provided in the error field when validation fails.
        """
        if not token:
            logger.warning("Token verification attempted with empty/None token")
            return VerificationResult(valid=False, error="Token is required")
        
        # Determine required scopes if not provided but actuator_id is
        if required_scopes is None and actuator_id:
            if actuator_id in self.ACTUATOR_SCOPE_MAP:
                required_scopes = self.ACTUATOR_SCOPE_MAP[actuator_id]
            else:
                required_scopes = self.ACTUATOR_SCOPE_MAP.get("default", ["filesystem:write", "project:write", "memory:write"])
        
        # Try to verify as JWT token first
        if "." in token and len(token.split(".")) == 3:
            # Looks like a JWT token
            return self._verify_jwt_token(token, required_scopes)
        
        # Fall back to legacy UUID token verification
        return self._verify_legacy_token(token)
    
    def _verify_jwt_token(self, token: str, required_scopes: Optional[List[str]] = None) -> VerificationResult:
        """
        Verify JWT token using token_auth.
        
        Args:
            token: JWT token string
            required_scopes: Optional list of required scopes
            
        Returns:
            VerificationResult
        """
        secret_key = os.environ.get("BROCA_TOKEN_SECRET")
        if not secret_key:
            logger.warning("BROCA_TOKEN_SECRET not set, cannot verify JWT token")
            return VerificationResult(
                valid=False,
                error="JWT token verification requires BROCA_TOKEN_SECRET environment variable"
            )
        
        try:
            payload = verify_jwt_token(token, secret_key)
        except ValueError as e:
            logger.warning(f"JWT token verification failed: {str(e)}")
            return VerificationResult(valid=False, error=f"Invalid JWT token: {str(e)}")
        
        # Check scopes if required
        if required_scopes:
            token_scopes = payload.get("scopes", [])
            missing_scopes = [scope for scope in required_scopes if scope not in token_scopes]
            if missing_scopes:
                logger.warning(
                    f"JWT token missing required scopes: {missing_scopes} "
                    f"(token has: {token_scopes})"
                )
                return VerificationResult(
                    valid=False,
                    error=f"Insufficient token scopes. Required: {required_scopes}, token has: {token_scopes}"
                )
        
        # Optionally verify request_id if present in payload
        request_id = payload.get("request_id")
        if request_id and request_id in self._approval_requests:
            request = self._approval_requests[request_id]
            if not request.approved:
                logger.warning(f"JWT token references unapproved request: {request_id}")
                return VerificationResult(
                    valid=False,
                    error=f"Token references unapproved request: {request_id}"
                )
        
        logger.debug(f"JWT token verification successful (jti: {payload.get('jti', 'unknown')})")
        return VerificationResult(valid=True)
    
    def _verify_legacy_token(self, token: str) -> VerificationResult:
        """
        Verify legacy UUID token (backward compatibility).
        
        Args:
            token: Legacy UUID token string
            
        Returns:
            VerificationResult
        """
        if token not in self.tokens:
            logger.warning(f"Legacy token verification failed: token not found (token: {token[:8]}...)")
            return VerificationResult(
                valid=False, 
                error=f"Approval token not found. The token may be invalid or may have been generated by a different approval system instance."
            )
        
        approval_token = self.tokens[token]
        now = datetime.now(timezone.utc)
        
        # Check expiration (tokens expire at the expires_at timestamp)
        if now > approval_token.expires_at:
            logger.warning(
                f"Legacy token verification failed: token expired "
                f"(expired_at: {approval_token.expires_at.isoformat()}, "
                f"now: {now.isoformat()})"
            )
            return VerificationResult(
                valid=False, 
                error=f"Approval token expired at {approval_token.expires_at.isoformat()}. Request a new approval token."
            )
        
        logger.debug(f"Legacy token verification successful (token: {token[:8]}..., request_id: {approval_token.request_id})")
        return VerificationResult(valid=True)
    
    def generate_token(self, request_id: str, expires_in_seconds: float = 300.0, actuator_id: Optional[str] = None) -> str:
        """
        Generate approval token for an approved request.
        
        Creates a reusable JWT token that can be used for actuator operations until expiration.
        The token is tied to the approval request and inherits the request's approval status.
        
        Args:
            request_id: ID of the approval request (must exist and be approved)
            expires_in_seconds: Token expiration time in seconds (default: 300 = 5 minutes)
            actuator_id: Optional actuator ID to determine required scopes
            
        Returns:
            JWT approval token string
            
        Raises:
            ValueError: If request_id not found, request is not approved, or secret key is missing
            
        Example:
            >>> request = approval_system.request_approval("create_file", {...}, "reason")
            >>> request.approved = True
            >>> token = approval_system.generate_token(request.request_id, expires_in_seconds=600)
            >>> # Token is now valid for 10 minutes
        """
        # Verify request exists
        if request_id not in self._approval_requests:
            logger.error(f"Token generation failed: approval request '{request_id}' not found")
            raise ValueError(
                f"Approval request '{request_id}' not found. "
                f"Ensure the request was created via request_approval() first."
            )
        
        request = self._approval_requests[request_id]
        
        # Verify request is approved
        if not request.approved:
            logger.error(f"Token generation failed: approval request '{request_id}' is not approved")
            raise ValueError(
                f"Approval request '{request_id}' is not approved. "
                f"Tokens can only be generated from approved requests. "
                f"Approve the request first by setting request.approved = True"
            )
        
        # Get secret key for JWT generation
        secret_key = os.environ.get("BROCA_TOKEN_SECRET")
        if not secret_key:
            logger.error("Token generation failed: BROCA_TOKEN_SECRET not set")
            raise ValueError(
                "BROCA_TOKEN_SECRET environment variable is required for token generation. "
                "Set it in your environment or .env file."
            )
        
        # Determine scopes based on actuator_id (from request or parameter)
        request_actuator_id = actuator_id or request.actuator_id
        if request_actuator_id and request_actuator_id in self.ACTUATOR_SCOPE_MAP:
            scopes = self.ACTUATOR_SCOPE_MAP[request_actuator_id]
        else:
            scopes = self.ACTUATOR_SCOPE_MAP.get("default", ["filesystem:write", "project:write", "memory:write"])
        
        # Get identity for token
        identity = get_default_identity()
        
        # Generate JWT token with request_id in payload for traceability
        token = self._generate_jwt_with_request_id(
            sub=identity.get("sub", "broca-system"),
            name=identity.get("name", "Broca System"),
            scopes=scopes,
            expiry_seconds=int(expires_in_seconds),
            secret_key=secret_key,
            request_id=request_id
        )
        
        # Store minimal metadata for backward compatibility and tracking
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        approval_token = ApprovalToken(
            token=token,
            request_id=request_id,
            expires_at=expires_at
        )
        self.tokens[token] = approval_token  # Store for backward compatibility
        
        logger.info(
            f"Generated JWT approval token for request '{request_id}' "
            f"(expires_at: {expires_at.isoformat()}, expires_in: {expires_in_seconds}s, "
            f"scopes: {scopes})"
        )
        return token
    
    def _generate_jwt_with_request_id(
        self,
        sub: str,
        name: str,
        scopes: List[str],
        expiry_seconds: int,
        secret_key: str,
        request_id: str,
        iss: str = "broca-token-v1",
        aud: str = "broca-os"
    ) -> str:
        """
        Generate JWT token with custom request_id claim.
        
        Similar to token_auth.generate_token but includes request_id in payload.
        """
        if isinstance(scopes, str):
            scopes_list = [s.strip() for s in scopes.split(",") if s.strip()]
        else:
            scopes_list = list(scopes)
        
        iat = int(time_module.time())
        exp = int(iat + int(expiry_seconds))
        jti = uuid.uuid4().hex
        
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": sub,
            "name": name,
            "scopes": scopes_list,
            "iat": iat,
            "exp": exp,
            "jti": jti,
            "iss": iss,
            "aud": aud,
            "request_id": request_id,  # Custom claim for traceability
        }
        
        header_b64 = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        payload_b64 = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        signature_b64 = _b64url(signature)
        
        token = f"{header_b64}.{payload_b64}.{signature_b64}"
        return token
    
    def get_approval_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """
        Get an approval request by ID.
        
        Retrieves an approval request from the internal registry. Useful for
        checking request status, approval state, or retrieving request details.
        
        Args:
            request_id: ID of the approval request to retrieve
            
        Returns:
            ApprovalRequest object if found, None if not found
            
        Example:
            >>> request = approval_system.get_approval_request("request-uuid")
            >>> if request:
            ...     print(f"Request approved: {request.approved}")
            ...     print(f"Operation: {request.operation}")
        """
        return self._approval_requests.get(request_id)
    
    def _analyze_safety(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze safety of an operation to determine risk level.
        
        Performs basic risk assessment based on operation name. Used to
        categorize operations for safety reporting.
        
        Risk Levels:
        - low: Read operations, non-destructive actions
        - medium: Modify operations, data changes
        - high: Delete operations, destructive actions
        
        Args:
            operation: Operation name to analyze
            parameters: Operation parameters (currently not used for analysis)
            
        Returns:
            Dictionary with:
            - risk_level: "low", "medium", or "high"
            - requires_approval: True if risk_level is medium or high
            
        Example:
            >>> analysis = approval_system._analyze_safety("delete_file", {"path": "/tmp/x"})
            >>> print(analysis["risk_level"])  # "high"
        """
        risk_level = "low"
        
        # Determine risk level based on operation type
        if "delete" in operation.lower() or "remove" in operation.lower():
            risk_level = "high"
        elif "modify" in operation.lower() or "change" in operation.lower():
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "requires_approval": risk_level in ["medium", "high"]
        }

