"""
Governance policy tools.

These tools manage *allowed actions* (capability gating, scopes, budgets, approvals),
independent of what the agent "wants" to do.

This is intentionally distinct from RL policy lifecycle tooling (ranker model versions).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..governance.policy import GovernanceEngine


class GetPolicyTool:
    @property
    def name(self) -> str:
        return "GET_POLICY"

    @property
    def description(self) -> str:
        return "Return the effective governance policy currently enforced (post-merge of defaults + overrides)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **_: Any) -> Dict[str, Any]:
        eng = GovernanceEngine()
        return {"success": True, "policy": eng.effective_policy()}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"GET_POLICY error: {result.get('error', 'unknown')}"
        pol = result.get("policy") or {}
        return f"GET_POLICY: ok\n\n{pol}"


class SetPolicyTool:
    @property
    def name(self) -> str:
        return "SET_POLICY"

    @property
    def description(self) -> str:
        return (
            "Apply a restricted governance policy delta (tighten-only by default). "
            "Use this to enter safer mode (reduce scopes/budgets/disable tools). "
            "For expansions, use REQUEST_POLICY_CHANGE + COMMIT_APPROVAL."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "delta": {"type": "object", "description": "Policy delta to apply"},
                "note": {"type": "string", "description": "Optional note/rationale"},
                "tighten_only": {"type": "boolean", "default": True, "description": "If true, only allow monotone tightening"},
            },
            "required": ["delta"],
        }

    def execute(self, delta: Dict[str, Any], note: str = "", tighten_only: bool = True, **_: Any) -> Dict[str, Any]:
        if not tighten_only:
            return {
                "success": False,
                "error": "expansion_disallowed",
                "message": "Non-monotone policy expansion must go through REQUEST_POLICY_CHANGE + COMMIT_APPROVAL.",
            }
        try:
            eng = GovernanceEngine()
            ver = eng.set_policy_tighten_only(delta, note=note or "")
            eng.audit().append(
                {
                    "ts": ver.get("created_at"),
                    "event_type": "policy_set",
                    "tighten_only": True,
                    "note": note or "",
                    "version_id": ver.get("version_id"),
                }
            )
            return {"success": True, "applied_version": ver}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"SET_POLICY error: {result.get('error', 'unknown')}"
        v = result.get("applied_version") or {}
        return f"SET_POLICY: version_id={v.get('version_id')}"


class RequestPolicyChangeTool:
    @property
    def name(self) -> str:
        return "REQUEST_POLICY_CHANGE"

    @property
    def description(self) -> str:
        return (
            "Create a human-approval request for non-monotone governance policy changes "
            "(enabling tools, expanding scopes/budgets). Returns a request_id and required token scopes."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proposal": {"type": "object", "description": "Requested policy delta (may expand scopes)"},
                "note": {"type": "string", "description": "Optional note/rationale"},
            },
            "required": ["proposal"],
        }

    def execute(self, proposal: Dict[str, Any], note: str = "", **_: Any) -> Dict[str, Any]:
        try:
            eng = GovernanceEngine()
            req = eng.request_policy_change(proposal, note=note or "")
            required_scopes = ["policy:change", f"policy_request:{req['request_id']}"]
            eng.audit().append(
                {
                    "ts": req.get("created_at"),
                    "event_type": "policy_request",
                    "request_id": req.get("request_id"),
                    "note": note or "",
                    "required_scopes": required_scopes,
                }
            )
            return {"success": True, "request": req, "required_scopes": required_scopes}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"REQUEST_POLICY_CHANGE error: {result.get('error', 'unknown')}"
        req = result.get("request") or {}
        scopes = result.get("required_scopes") or []
        return f"REQUEST_POLICY_CHANGE: request_id={req.get('request_id')} required_scopes={scopes}"


class CommitApprovalTool:
    @property
    def name(self) -> str:
        return "COMMIT_APPROVAL"

    @property
    def description(self) -> str:
        return (
            "Commit a human approval token for a previously created policy change request. "
            "Applies the request's policy delta and updates the active governance policy version."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "Request ID from REQUEST_POLICY_CHANGE"},
                "approval_token": {"type": "string", "description": "JWT token with scopes policy:change and policy_request:<id>"},
                "note": {"type": "string", "description": "Optional note"},
            },
            "required": ["request_id", "approval_token"],
        }

    def execute(self, request_id: str, approval_token: str, note: str = "", **_: Any) -> Dict[str, Any]:
        try:
            eng = GovernanceEngine()
            res = eng.commit_approved_request(request_id=request_id, approval_token=approval_token, note=note or "")
            eng.audit().append(
                {
                    "ts": res.get("applied_version", {}).get("created_at"),
                    "event_type": "policy_commit",
                    "request_id": request_id,
                    "note": note or "",
                    "applied_version_id": res.get("applied_version", {}).get("version_id"),
                }
            )
            return {"success": True, **res}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"COMMIT_APPROVAL error: {result.get('error', 'unknown')}"
        v = result.get("applied_version") or {}
        return f"COMMIT_APPROVAL: request_id={result.get('request_id')} version_id={v.get('version_id')}"


class EvaluateActionTool:
    @property
    def name(self) -> str:
        return "EVALUATE_ACTION"

    @property
    def description(self) -> str:
        return (
            "Preflight an intended action against the effective governance policy. "
            "Returns allowed/denied, matched rule, and normalized fields (e.g., resolved paths)."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Tool/action name (e.g., WRITE_FILE, EXECUTE)"},
                "arguments": {"type": "object", "description": "Proposed tool arguments"},
            },
            "required": ["tool_name", "arguments"],
        }

    def execute(self, tool_name: str, arguments: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        eng = GovernanceEngine()
        decision = eng.evaluate_action(tool_name=str(tool_name), arguments=arguments if isinstance(arguments, dict) else {})
        return {"success": True, "decision": decision.as_dict()}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"EVALUATE_ACTION error: {result.get('error', 'unknown')}"
        dec = result.get("decision") or {}
        return f"EVALUATE_ACTION: allowed={bool(dec.get('allowed'))} reason={dec.get('reason')}"


class GetAuditLogTool:
    @property
    def name(self) -> str:
        return "GET_AUDIT_LOG"

    @property
    def description(self) -> str:
        return "Return governance audit log entries (immutable append-only JSONL, hash chained)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Optional event type filter (e.g., policy_set, action_attempt)"},
                "limit": {"type": "integer", "default": 100, "minimum": 1, "maximum": 5000},
            },
            "required": [],
        }

    def execute(self, event_type: Optional[str] = None, limit: int = 100, **_: Any) -> Dict[str, Any]:
        eng = GovernanceEngine()
        entries = eng.audit().query(limit=limit, event_type=event_type if isinstance(event_type, str) and event_type else None)
        return {"success": True, "count": len(entries), "entries": entries}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"GET_AUDIT_LOG error: {result.get('error', 'unknown')}"
        return f"GET_AUDIT_LOG: {result.get('count')} entries"

