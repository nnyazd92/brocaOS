from __future__ import annotations

import json
from pathlib import Path

import pytest

from broca.config import config
from broca.tools.policy_tools import (
    CommitApprovalTool,
    EvaluateActionTool,
    GetAuditLogTool,
    GetPolicyTool,
    RequestPolicyChangeTool,
    SetPolicyTool,
)
from broca.tools.primitive_io import WriteFileTool
from broca.tools.primitive_io import ExecuteTool
from broca.tools.registry import ToolRegistry
from broca.token_auth.token import generate_token


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


def test_evaluate_action_blocks_write_outside_roots(tmp_path: Path):
    original = _patch_governance_paths(tmp_path)
    try:
        tool = EvaluateActionTool()
        res = tool.execute(tool_name="WRITE_FILE", arguments={"path": "/etc/passwd", "content": "x"})
        assert res["success"] is True
        assert res["decision"]["allowed"] is False
        assert res["decision"]["reason"] in {"path_outside_write_roots", "path_required"}
    finally:
        _restore_governance_paths(original)


def test_registry_enforces_governance_policy_on_write(tmp_path: Path):
    original = _patch_governance_paths(tmp_path)
    try:
        reg = ToolRegistry()
        reg.register_tool(WriteFileTool())

        tool_call = {
            "id": "tc1",
            "type": "function",
            "function": {"name": "WRITE_FILE", "arguments": json.dumps({"path": "/etc/passwd", "content": "x"})},
        }
        out = reg.execute_tool_call(tool_call)
        assert out.get("_success") is False
        assert "Blocked by governance policy" in out.get("content", "")
    finally:
        _restore_governance_paths(original)


def test_registry_blocks_execute_when_budget_exceeded(tmp_path: Path):
    original = _patch_governance_paths(tmp_path)
    try:
        _ = SetPolicyTool().execute(delta={"budgets": {"max_exec_ms_per_minute": 1}}, tighten_only=True)

        reg = ToolRegistry()
        reg.register_tool(ExecuteTool())

        cwd = str(Path(config.tools.governance_project_root))
        tool_call = {
            "id": "tc2",
            "type": "function",
            "function": {"name": "EXECUTE", "arguments": json.dumps({"cmd": "echo hi", "timeout": 60, "cwd": cwd})},
        }
        out = reg.execute_tool_call(tool_call)
        assert out.get("_success") is False
        assert "Blocked by governance policy" in out.get("content", "")
        assert "budget_exceeded" in out.get("content", "")
    finally:
        _restore_governance_paths(original)


def test_request_and_commit_policy_change_with_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    original = _patch_governance_paths(tmp_path)
    try:
        monkeypatch.setenv("BROCA_TOKEN_SECRET", "test_secret_123")

        # First tighten: disable EXECUTE.
        s = SetPolicyTool().execute(delta={"tools": {"EXECUTE": {"enabled": False}}}, note="disable", tighten_only=True)
        assert s["success"] is True

        pol = GetPolicyTool().execute()
        assert pol["success"] is True
        assert pol["policy"]["tools"]["EXECUTE"]["enabled"] is False

        # Request expansion: re-enable EXECUTE.
        req = RequestPolicyChangeTool().execute(proposal={"tools": {"EXECUTE": {"enabled": True}}}, note="enable")
        assert req["success"] is True
        request_id = req["request"]["request_id"]

        scopes = ["policy:change", f"policy_request:{request_id}"]
        token, _payload = generate_token(
            sub="tester",
            name="tester",
            scopes=scopes,
            expiry_seconds=60,
            secret_key="test_secret_123",
        )

        committed = CommitApprovalTool().execute(request_id=request_id, approval_token=token, note="approved")
        assert committed["success"] is True

        pol2 = GetPolicyTool().execute()
        assert pol2["success"] is True
        assert pol2["policy"]["tools"]["EXECUTE"]["enabled"] is True

        audit = GetAuditLogTool().execute(limit=50)
        assert audit["success"] is True
        assert audit["count"] >= 2
        assert any(isinstance(e, dict) and "hash" in e for e in audit["entries"])
    finally:
        _restore_governance_paths(original)


def test_corrupt_policy_file_fault_injection(tmp_path: Path):
    original = _patch_governance_paths(tmp_path)
    try:
        policy_path = Path(config.tools.governance_policy_path)
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text("{not json", encoding="utf-8")

        res = GetPolicyTool().execute()
        assert res["success"] is True
        assert isinstance(res["policy"], dict)
    finally:
        _restore_governance_paths(original)


def test_exec_budget_blocks_execute_preflight(tmp_path: Path):
    original = _patch_governance_paths(tmp_path)
    try:
        # Tighten budgets so a single EXECUTE is blocked (estimated by timeout).
        _ = SetPolicyTool().execute(
            delta={"budgets": {"max_exec_ms_per_minute": 1}},
            tighten_only=True,
        )

        tool = EvaluateActionTool()
        res = tool.execute(
            tool_name="EXECUTE",
            arguments={"cmd": "echo hi", "timeout": 60, "cwd": str(Path(config.tools.governance_project_root))},
        )
        assert res["success"] is True
        assert res["decision"]["allowed"] is False
        assert res["decision"]["reason"] == "budget_exceeded"
        assert res["decision"]["matched_rule"] == "budgets.max_exec_ms_per_minute"
    finally:
        _restore_governance_paths(original)


def test_web_budget_blocks_web_fetch_preflight(tmp_path: Path):
    original = _patch_governance_paths(tmp_path)
    try:
        _ = SetPolicyTool().execute(
            delta={"budgets": {"max_web_bytes_per_minute": 1}},
            tighten_only=True,
        )

        tool = EvaluateActionTool()
        res = tool.execute(tool_name="WEB_FETCH", arguments={"url": "https://example.com", "max_bytes": 100})
        assert res["success"] is True
        assert res["decision"]["allowed"] is False
        assert res["decision"]["reason"] == "budget_exceeded"
        assert res["decision"]["matched_rule"] == "budgets.max_web_bytes_per_minute"
    finally:
        _restore_governance_paths(original)
