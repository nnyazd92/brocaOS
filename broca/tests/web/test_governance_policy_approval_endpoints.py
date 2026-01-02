from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from broca.config import config
from broca.governance.policy import GovernanceEngine
from broca.web_api import app


def _patch_governance_paths(tmp_path: Path):
    original = {
        "policy_path": config.tools.governance_policy_path,
        "requests_path": config.tools.governance_requests_path,
        "audit_path": config.tools.governance_audit_log_path,
        "project_root": config.tools.governance_project_root,
    }
    config.tools.governance_policy_path = str(tmp_path / "policy.json")
    config.tools.governance_requests_path = str(tmp_path / "requests.json")
    config.tools.governance_audit_log_path = str(tmp_path / "audit.jsonl")
    config.tools.governance_project_root = str(tmp_path / "root")
    Path(config.tools.governance_project_root).mkdir(parents=True, exist_ok=True)
    return original


def _restore_governance_paths(original: dict):
    config.tools.governance_policy_path = original["policy_path"]
    config.tools.governance_requests_path = original["requests_path"]
    config.tools.governance_audit_log_path = original["audit_path"]
    config.tools.governance_project_root = original["project_root"]


def test_policy_request_token_and_commit_endpoints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    original = _patch_governance_paths(tmp_path)
    try:
        monkeypatch.setenv("BROCA_TOKEN_SECRET", "test_secret_123")
        monkeypatch.setenv("BROCA_ADMIN_API_KEY", "admin123")

        eng = GovernanceEngine()
        req = eng.request_policy_change(proposal={"tools": {"EXECUTE": {"enabled": False}}}, note="disable execute")
        request_id = req["request_id"]

        client = TestClient(app)

        lst = client.get("/api/governance/requests?status=pending&limit=50")
        assert lst.status_code == 200
        ids = [r.get("request_id") for r in lst.json().get("requests", [])]
        assert request_id in ids

        tok = client.post(
            f"/api/governance/requests/{request_id}/token",
            headers={"X-Broca-Admin-Key": "admin123"},
            json={"expiry_seconds": 60, "sub": "operator", "name": "operator"},
        )
        assert tok.status_code == 200
        token = tok.json()["token"]

        commit = client.post(
            f"/api/governance/requests/{request_id}/commit",
            json={"approval_token": token, "note": "approved"},
        )
        assert commit.status_code == 200
        assert commit.json()["request_id"] == request_id
        assert isinstance(commit.json()["applied_version"], dict)

        req2 = client.get(f"/api/governance/requests/{request_id}")
        assert req2.status_code == 200
        assert req2.json()["request"]["status"] == "applied"
    finally:
        _restore_governance_paths(original)


def test_policy_request_reject_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    original = _patch_governance_paths(tmp_path)
    try:
        monkeypatch.setenv("BROCA_ADMIN_API_KEY", "admin123")
        monkeypatch.setenv("BROCA_TOKEN_SECRET", "test_secret_123")

        eng = GovernanceEngine()
        req = eng.request_policy_change(proposal={"tools": {"EXECUTE": {"enabled": True}}}, note="enable execute")
        request_id = req["request_id"]

        client = TestClient(app)
        resp = client.post(
            f"/api/governance/requests/{request_id}/reject?note=nope",
            headers={"X-Broca-Admin-Key": "admin123"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

        req2 = client.get(f"/api/governance/requests/{request_id}")
        assert req2.status_code == 200
        assert req2.json()["request"]["status"] == "rejected"
    finally:
        _restore_governance_paths(original)

