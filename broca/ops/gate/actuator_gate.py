"""
Minimal gate integration for BrocaOS actuator actions.

This module provides authorize_action to gate non-read actions using JWT-like tokens
issued by the Broca token service (HS256/HMAC).
"""

import os
from broca.token_auth import verify_token

def authorize_action(action, token=None, required_scopes=None, secret_key=None, iss="broca-token-v1", aud="broca-os"):
    """
    Authorize an action using a token.

    - Read actions are allowed without a token.
    - Non-read actions require a valid token with all required scopes.
    - Returns a tuple (allowed: bool, message: str).
    """
    read_actions = {"read", "read_file", "read_memory"}

    # Allow read actions without token
    if action in read_actions or (isinstance(action, str) and action.startswith("read")):
        return True, "Read action allowed without token"

    if not token:
        return False, "Missing authorization token for write/action"

    if not secret_key:
        secret_key = os.environ.get("BROCA_TOKEN_SECRET")

    try:
        payload = verify_token(token, secret_key, iss=iss, aud=aud)
    except Exception as e:
        return False, f"Token invalid: {str(e)}"

    scopes = payload.get("scopes", [])
    if not required_scopes:
        required_scopes = []

    # Ensure all required scopes are present
    if all(rs in scopes for rs in required_scopes):
        jti = payload.get("jti")
        exp = payload.get("exp")
        return True, f"Approved (jti={jti}, exp={exp})"
    else:
        return False, "Insufficient token scopes for requested action"

__all__ = ["authorize_action"]
