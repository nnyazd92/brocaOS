"""
Token authorization package for BrocaOS (code repo).

Exports:
- generate_token, verify_token from broca.token_auth.token
- get_default_identity, default_scopes, default_expiry_seconds from defaults
"""
from .token import generate_token, verify_token
from .defaults import get_default_identity, default_scopes, default_expiry_seconds  # convenience

__all__ = [
    "generate_token",
    "verify_token",
    "get_default_identity",
    "default_scopes",
    "default_expiry_seconds",
]