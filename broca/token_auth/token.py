import base64
import json
import time
import uuid
import hmac
import hashlib
import os

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _b64url_decode(s: str) -> bytes:
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)

def generate_token(sub: str, name: str, scopes, expiry_seconds: int, secret_key: str,
                   iss: str = "broca-token-v1", aud: str = "broca-os"):
    if not secret_key:
        raise ValueError("Secret key is required for token generation (BROCA_TOKEN_SECRET or .env).")
    if isinstance(scopes, str):
        scopes_list = [s.strip() for s in scopes.split(",") if s.strip()]
    else:
        scopes_list = list(scopes)

    iat = int(time.time())
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
    }

    header_b64 = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url(signature)

    token = f"{header_b64}.{payload_b64}.{signature_b64}"
    return token, payload

def verify_token(token: str, secret_key: str, iss: str = "broca-token-v1", aud: str = "broca-os"):
    if not secret_key:
        raise ValueError("Secret key is required for token verification (BROCA_TOKEN_SECRET or .env).")

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_sig_b64 = _b64url(expected_sig)

    if not hmac.compare_digest(expected_sig_b64, signature_b64):
        raise ValueError("Invalid token signature")

    header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))

    if header.get("alg") != "HS256":
        raise ValueError("Unsupported algorithm")

    if payload.get("iss") != iss or payload.get("aud") != aud:
        raise ValueError("Invalid issuer/audience")

    now = int(time.time())
    if int(payload.get("exp", 0)) <= now:
        raise ValueError("Token has expired")

    return payload