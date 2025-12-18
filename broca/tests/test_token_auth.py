import os
import time
import pytest
from broca.token_auth.token import generate_token, verify_token
from broca.token_auth.defaults import get_default_identity

def test_token_roundtrip(monkeypatch):
    monkeypatch.setenv("BROCA_TOKEN_SECRET", "supersecret123")
    token, payload = generate_token(
        sub="nick.yazdani",
        name="Nick Yazdani",
        scopes=["filesystem:write","project:write","memory:write"],
        expiry_seconds=5,
        secret_key="supersecret123",
    )
    assert "sub" in payload and payload["sub"] == "nick.yazdani"
    verified = verify_token(token, "supersecret123")
    assert verified["sub"] == "nick.yazdani"

def test_token_expired(monkeypatch):
    monkeypatch.setenv("BROCA_TOKEN_SECRET", "supersecret123")
    token, payload = generate_token(
        sub="nick.yazdani",
        name="Nick Yazdani",
        scopes=["filesystem:write"],
        expiry_seconds=1,
        secret_key="supersecret123",
    )
    time.sleep(2)
    import pytest
    with pytest.raises(ValueError):
        verify_token(token, "supersecret123")

def test_invalid_signature(monkeypatch):
    monkeypatch.setenv("BROCA_TOKEN_SECRET", "supersecret123")
    token, payload = generate_token(
        sub="nick.yazdani",
        name="Nick Yazdani",
        scopes=["filesystem:write"],
        expiry_seconds=10,
        secret_key="supersecret123",
    )
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(ValueError):
        verify_token(tampered, "supersecret123")

def test_wrong_issuer_aud(monkeypatch):
    monkeypatch.setenv("BROCA_TOKEN_SECRET", "supersecret123")
    token, payload = generate_token(
        sub="nick.yazdani",
        name="Nick Yazdani",
        scopes=["filesystem:write"],
        expiry_seconds=10,
        secret_key="supersecret123",
        iss="broca-token-v1",
        aud="broca-os",
    )
    # verify with wrong issuer
    with pytest.raises(ValueError):
        verify_token(token, "supersecret123", iss="wrong-iss", aud="broca-os")