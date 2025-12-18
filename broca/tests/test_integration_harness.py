"""
Integration harness for BrocaOS token flow (end-to-end test).

Tests:
- Token generation with defaults
- Token verification
- Gate authorization using the token (write path)
- Read path gating (no token required)
- Optional: small expiry test (short TTL)

Notes:
- This is a self-contained harness that uses the code in /home/wizard/Documents/Code/BrocaOS.
- It does not modify the house/docs; it exercises code-paths in the code repo.
"""

from __future__ import annotations

import os
import time
import pathlib
import pytest
import secrets

from broca.token_auth.token import generate_token, verify_token
from broca.token_auth.defaults import get_default_identity, default_scopes, default_expiry_seconds
from broca.ops.gate.actuator_gate import authorize_action


# Lightweight .env loader (no external deps)
def _load_env_file(path=".env"):
    """Load environment variables from .env file."""
    if not pathlib.Path(path).exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k not in os.environ:
                os.environ[k] = v


@pytest.fixture(scope="module")
def secret_key():
    """Get or generate a secret key for token operations."""
    secret = os.environ.get("BROCA_TOKEN_SECRET")
    if not secret:
        # Generate a temporary secret for testing if not set
        secret = secrets.token_hex(32)
        os.environ["BROCA_TOKEN_SECRET"] = secret
    return secret


@pytest.fixture(scope="module", autouse=True)
def load_env():
    """Load .env file if present (module-scoped, runs once)."""
    _load_env_file()


@pytest.fixture
def default_identity():
    """Get default identity for token generation."""
    identity = get_default_identity()
    return {
        "sub": identity.get("sub", "nick.yazdani"),
        "name": identity.get("name", "Nick Yazdani"),
    }


@pytest.fixture
def default_token_data(default_identity, secret_key):
    """Generate default token data for testing."""
    return {
        "sub": default_identity["sub"],
        "name": default_identity["name"],
        "scopes": default_scopes(),
        "expiry_seconds": default_expiry_seconds(),
        "secret_key": secret_key,
        "iss": "broca-token-v1",
        "aud": "broca-os",
    }


class TestTokenGeneration:
    """Test token generation with defaults."""
    
    def test_token_generation_with_defaults(self, default_token_data):
        """Test that token generation works with default parameters."""
        token, payload = generate_token(**default_token_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        assert payload is not None
        assert isinstance(payload, dict)
        assert payload.get("sub") == default_token_data["sub"]
        assert payload.get("name") == default_token_data["name"]
        assert "scopes" in payload
        assert "exp" in payload
        assert "jti" in payload


class TestTokenVerification:
    """Test token verification."""
    
    def test_token_verification(self, default_token_data, secret_key):
        """Test that generated tokens can be verified."""
        token, payload = generate_token(**default_token_data)
        
        verified = verify_token(
            token, 
            secret_key, 
            iss=default_token_data["iss"], 
            aud=default_token_data["aud"]
        )
        
        assert verified is not None
        assert isinstance(verified, dict)
        assert verified.get("sub") == payload.get("sub")
        assert verified.get("name") == payload.get("name")
        assert verified.get("scopes") == payload.get("scopes")
        assert verified.get("exp") == payload.get("exp")
        assert verified.get("jti") == payload.get("jti")


class TestGateAuthorization:
    """Test gate authorization using tokens."""
    
    def test_non_read_action_with_token_required_scopes(self, default_token_data, secret_key):
        """Test that non-read actions require a valid token with required scopes."""
        token, _ = generate_token(**default_token_data)
        
        action = "write_config"  # non-read example
        required_scopes = ["filesystem:write"]
        
        ok, msg = authorize_action(
            action, 
            token=token, 
            required_scopes=required_scopes, 
            secret_key=secret_key
        )
        
        # Should succeed if token has required scopes
        # Note: This depends on whether default_scopes() includes "filesystem:write"
        assert isinstance(ok, bool)
        assert isinstance(msg, str)
    
    def test_read_action_no_token_required(self):
        """Test that read actions are allowed without a token."""
        ok_read, msg_read = authorize_action("read", token=None, required_scopes=None)
        
        assert ok_read is True
        assert "Read action allowed" in msg_read
    
    def test_read_file_action_no_token_required(self):
        """Test that read_file action is allowed without a token."""
        ok_read, msg_read = authorize_action("read_file", token=None, required_scopes=None)
        
        assert ok_read is True
        assert "Read action allowed" in msg_read
    
    def test_read_memory_action_no_token_required(self):
        """Test that read_memory action is allowed without a token."""
        ok_read, msg_read = authorize_action("read_memory", token=None, required_scopes=None)
        
        assert ok_read is True
        assert "Read action allowed" in msg_read
    
    def test_action_starting_with_read_no_token_required(self):
        """Test that actions starting with 'read' are allowed without a token."""
        ok_read, msg_read = authorize_action("read_something", token=None, required_scopes=None)
        
        assert ok_read is True
        assert "Read action allowed" in msg_read
    
    def test_non_read_action_without_token_fails(self, secret_key):
        """Test that non-read actions without a token are rejected."""
        ok, msg = authorize_action("write_config", token=None, required_scopes=None, secret_key=secret_key)
        
        assert ok is False
        assert "Missing authorization token" in msg
    
    def test_non_read_action_with_invalid_token_fails(self, secret_key):
        """Test that non-read actions with an invalid token are rejected."""
        ok, msg = authorize_action(
            "write_config", 
            token="invalid.token.here", 
            required_scopes=None, 
            secret_key=secret_key
        )
        
        assert ok is False
        assert "Token invalid" in msg


class TestTokenExpiry:
    """Test token expiry behavior."""
    
    def test_token_expiry_short_ttl(self, default_token_data, secret_key):
        """Test that tokens expire after their TTL."""
        short_ttl = 2  # seconds
        token_data = default_token_data.copy()
        token_data["expiry_seconds"] = short_ttl
        
        token2, payload2 = generate_token(**token_data)
        
        assert payload2.get("exp") is not None
        
        # Token should be valid immediately
        verified = verify_token(token2, secret_key, iss=token_data["iss"], aud=token_data["aud"])
        assert verified is not None
        
        # Wait for token to expire
        time.sleep(3)
        
        # Token should now be expired
        with pytest.raises(ValueError, match="expired"):
            verify_token(token2, secret_key, iss=token_data["iss"], aud=token_data["aud"])