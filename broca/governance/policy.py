"""
Governance policy: declarative capability gating, scopes, budgets, approvals, audit.

This is intentionally distinct from the RL "policy ranker" (tool selection policy).
Governance policy answers: "What is Broca allowed to do right now?"

Design goals:
- Persistent across restarts (policy + requests + audit log).
- Minimal, typed-ish schema (JSON) with tighten-only deltas by default.
- Tamper-evident audit log (hash-chained JSONL).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import config
from ..token_auth.token import get_token_secret, verify_token


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw)
    except Exception:
        return None


def _norm_path(p: str) -> str:
    try:
        return str(Path(p).expanduser().resolve())
    except Exception:
        return str(Path(p).expanduser().absolute())


def _within_roots(target: str, roots: List[str]) -> bool:
    try:
        t = Path(_norm_path(target))
        for r in roots:
            rp = Path(_norm_path(r))
            try:
                t.relative_to(rp)
                return True
            except Exception:
                continue
        return False
    except Exception:
        return False


def _subset(new: List[str], old: List[str]) -> bool:
    return set(new).issubset(set(old))


def _clamp_int(x: Any, lo: int, hi: int, default: int) -> int:
    try:
        v = int(x)
    except Exception:
        return default
    return max(lo, min(hi, v))


def _ts_to_epoch_seconds(ts: Any) -> Optional[float]:
    """
    Convert a stored timestamp (float epoch or ISO string) into epoch seconds.
    """
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str) and ts.strip():
        s = ts.strip()
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return float(dt.timestamp())
        except Exception:
            return None
    return None


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    matched_rule: str
    normalized: Dict[str, Any]
    estimated_cost: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "allowed": bool(self.allowed),
            "requires_approval": bool(self.requires_approval),
            "reason": self.reason,
            "matched_rule": self.matched_rule,
            "normalized": self.normalized,
            "estimated_cost": self.estimated_cost,
        }


class GovernanceAuditLog:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self._path.exists():
            return "0" * 64
        try:
            # Read tail-ish by scanning backwards; file is expected small-ish.
            lines = self._path.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines):
                try:
                    obj = json.loads(line)
                    h = obj.get("hash")
                    if isinstance(h, str) and len(h) == 64:
                        return h
                except Exception:
                    continue
        except Exception:
            return "0" * 64
        return "0" * 64

    def append(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        prev = self._last_hash()
        material = dict(entry)
        material["prev_hash"] = prev
        # Stable hash over canonical JSON of material (excluding final hash).
        payload = json.dumps(material, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")
        h = sha256(payload).hexdigest()
        material["hash"] = h
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(material, separators=(",", ":"), sort_keys=True, ensure_ascii=False) + "\n")
        return material

    def query(self, *, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        limit_i = _clamp_int(limit, 1, 5000, 100)
        if not self._path.exists():
            return []
        out: List[Dict[str, Any]] = []
        try:
            for line in self._path.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if event_type and obj.get("event_type") != event_type:
                    continue
                out.append(obj)
        except Exception:
            return out[-limit_i:]
        return out[-limit_i:]

    def sum_cost_since(
        self,
        *,
        since_epoch: float,
        event_type: str,
        tool_name: str,
        cost_key: str,
        max_scan: int = 20000,
    ) -> float:
        """
        Sum a cost field from action_result records since a given epoch timestamp.

        This is used for simple per-minute budget enforcement.
        """
        if not self._path.exists():
            return 0.0
        total = 0.0
        scanned = 0
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return 0.0

        for line in reversed(lines):
            if scanned >= int(max_scan):
                break
            scanned += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if not isinstance(obj, dict):
                continue
            if obj.get("event_type") != event_type:
                continue
            if obj.get("tool") != tool_name:
                continue
            ts = _ts_to_epoch_seconds(obj.get("ts"))
            if ts is None:
                continue
            if ts < float(since_epoch):
                # Because log is append-only, once we pass the window we can stop.
                break
            cost = obj.get("cost")
            if not isinstance(cost, dict):
                continue
            try:
                val = float(cost.get(cost_key, 0.0) or 0.0)
            except Exception:
                val = 0.0
            total += val
        return float(total)


class GovernancePolicyStore:
    """
    Persistent policy store with version history.

    File format:
    {
      "schema_version": 1,
      "active_version_id": 1,
      "versions": [{"version_id": 1, "created_at": "...", "note": "...", "policy": {...}}],
    }
    """

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _default_policy(self) -> Dict[str, Any]:
        project_root = (getattr(config.tools, "governance_project_root", "") or "").strip()
        if not project_root:
            project_root = os.getcwd()
        home = str(Path.home())
        return {
            "tools": {
                # Explicit capability gates for high-risk actuators.
                "WRITE_FILE": {"enabled": True},
                "APPEND_FILE": {"enabled": True},
                "PATCH_FILE": {"enabled": True},
                "EXECUTE": {"enabled": True},
                "WEB_FETCH": {"enabled": True},
                "WEB_SEARCH": {"enabled": bool(getattr(config.tools, "enable_web_search", True))},
            },
            "filesystem": {
                "read_roots": [project_root, "/tmp", home],
                "write_roots": [project_root, "/tmp"],
            },
            "exec": {
                "cwd_roots": [project_root],
                # If empty, defer to existing ExecuteTool allowlist semantics.
                "command_whitelist": list(getattr(config.tools, "execute_command_whitelist", []) or []),
                "env_allowlist": ["PATH"],
            },
            "web": {
                "allow_domains": [],  # empty => allow any
                "max_bytes_per_fetch": 2_000_000,
            },
            "budgets": {
                "max_exec_ms_per_minute": 120_000,
                "max_web_bytes_per_minute": 10_000_000,
            },
            "project_root": project_root,
        }

    def load(self) -> Dict[str, Any]:
        raw = _load_json(self._path)
        if not isinstance(raw, dict):
            raw = {
                "schema_version": 1,
                "active_version_id": 1,
                "versions": [
                    {
                        "version_id": 1,
                        "created_at": _now_iso(),
                        "note": "default",
                        "policy": self._default_policy(),
                    }
                ],
            }
            _atomic_write_json(self._path, raw)
        return raw

    def get_effective_policy(self) -> Dict[str, Any]:
        state = self.load()
        active = int(state.get("active_version_id") or 1)
        versions = state.get("versions") or []
        chosen: Optional[Dict[str, Any]] = None
        for v in versions:
            if isinstance(v, dict) and int(v.get("version_id") or 0) == active:
                chosen = v.get("policy") if isinstance(v.get("policy"), dict) else None
                break
        return chosen if isinstance(chosen, dict) else self._default_policy()

    def set_policy(self, *, delta: Dict[str, Any], note: str = "", tighten_only: bool = True) -> Dict[str, Any]:
        state = self.load()
        versions = list(state.get("versions") or [])
        active_policy = self.get_effective_policy()
        merged, err = apply_policy_delta(active_policy, delta, tighten_only=tighten_only)
        if err:
            raise ValueError(err)
        next_id = 1
        if versions:
            try:
                next_id = max(int(v.get("version_id") or 0) for v in versions if isinstance(v, dict)) + 1
            except Exception:
                next_id = len(versions) + 1
        versions.append({"version_id": next_id, "created_at": _now_iso(), "note": note or "", "policy": merged})
        state["versions"] = versions
        state["active_version_id"] = next_id
        _atomic_write_json(self._path, state)
        return {"version_id": next_id, "created_at": versions[-1]["created_at"], "note": note or ""}


class GovernancePolicyRequests:
    """
    Persistent request store for non-monotone policy changes.
    """

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        raw = _load_json(self._path)
        if not isinstance(raw, dict):
            raw = {"schema_version": 1, "requests": []}
            _atomic_write_json(self._path, raw)
        return raw

    def create(self, *, proposal: Dict[str, Any], note: str = "") -> Dict[str, Any]:
        state = self.load()
        reqs = list(state.get("requests") or [])
        rid = sha256(f"{_now_iso()}|{json.dumps(proposal, sort_keys=True)}".encode("utf-8")).hexdigest()[:16]
        req = {"request_id": rid, "created_at": _now_iso(), "note": note or "", "proposal": proposal, "status": "pending"}
        reqs.append(req)
        state["requests"] = reqs
        _atomic_write_json(self._path, state)
        return req

    def get(self, request_id: str) -> Optional[Dict[str, Any]]:
        state = self.load()
        for r in state.get("requests") or []:
            if isinstance(r, dict) and r.get("request_id") == request_id:
                return r
        return None

    def list(self, *, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        state = self.load()
        reqs = [r for r in (state.get("requests") or []) if isinstance(r, dict)]
        if isinstance(status, str) and status.strip():
            st = status.strip().lower()
            reqs = [r for r in reqs if str(r.get("status") or "").lower() == st]
        try:
            reqs.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        except Exception:
            pass
        lim = _clamp_int(limit, 1, 5000, 100)
        return reqs[:lim]

    def mark_applied(self, request_id: str, *, applied_version_id: int) -> bool:
        state = self.load()
        changed = False
        reqs = []
        for r in state.get("requests") or []:
            if not isinstance(r, dict):
                continue
            if r.get("request_id") == request_id and r.get("status") == "pending":
                r = dict(r)
                r["status"] = "applied"
                r["applied_at"] = _now_iso()
                r["applied_version_id"] = int(applied_version_id)
                changed = True
            reqs.append(r)
        if changed:
            state["requests"] = reqs
            _atomic_write_json(self._path, state)
        return changed

    def mark_rejected(self, request_id: str, *, note: str = "") -> bool:
        state = self.load()
        changed = False
        reqs = []
        for r in state.get("requests") or []:
            if not isinstance(r, dict):
                continue
            if r.get("request_id") == request_id and r.get("status") == "pending":
                r = dict(r)
                r["status"] = "rejected"
                r["rejected_at"] = _now_iso()
                if note:
                    r["rejected_note"] = str(note)[:2000]
                changed = True
            reqs.append(r)
        if changed:
            state["requests"] = reqs
            _atomic_write_json(self._path, state)
        return changed


def apply_policy_delta(current: Dict[str, Any], delta: Dict[str, Any], *, tighten_only: bool) -> Tuple[Dict[str, Any], Optional[str]]:
    if not isinstance(delta, dict):
        return current, "delta_must_be_object"

    cur = json.loads(json.dumps(current))  # deep copy (json-safe)
    tools_delta = delta.get("tools")
    if tools_delta is not None:
        if not isinstance(tools_delta, dict):
            return current, "delta.tools_must_be_object"
        cur.setdefault("tools", {})
        for tool_name, tcfg in tools_delta.items():
            if not isinstance(tool_name, str) or not isinstance(tcfg, dict):
                continue
            cur.setdefault("tools", {}).setdefault(tool_name, {})
            enabled_new = tcfg.get("enabled")
            if isinstance(enabled_new, bool):
                enabled_old = bool((cur.get("tools") or {}).get(tool_name, {}).get("enabled", True))
                if tighten_only and enabled_old is False and enabled_new is True:
                    return current, f"tighten_only_disallows_enabling:{tool_name}"
                if tighten_only and enabled_old is True and enabled_new is True:
                    pass
                cur["tools"][tool_name]["enabled"] = enabled_new

    fs_delta = delta.get("filesystem")
    if fs_delta is not None:
        if not isinstance(fs_delta, dict):
            return current, "delta.filesystem_must_be_object"
        cur.setdefault("filesystem", {})
        for k in ("read_roots", "write_roots"):
            if k not in fs_delta:
                continue
            v = fs_delta.get(k)
            if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
                return current, f"delta.filesystem.{k}_must_be_list_of_strings"
            new_roots = [_norm_path(x) for x in v]
            old_roots = [_norm_path(x) for x in (cur.get("filesystem", {}).get(k) or []) if isinstance(x, str)]
            if tighten_only and old_roots and not _subset(new_roots, old_roots):
                return current, f"tighten_only_disallows_expanding:{k}"
            cur["filesystem"][k] = new_roots

    exec_delta = delta.get("exec")
    if exec_delta is not None:
        if not isinstance(exec_delta, dict):
            return current, "delta.exec_must_be_object"
        cur.setdefault("exec", {})
        if "cwd_roots" in exec_delta:
            v = exec_delta.get("cwd_roots")
            if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
                return current, "delta.exec.cwd_roots_must_be_list_of_strings"
            new_roots = [_norm_path(x) for x in v]
            old_roots = [_norm_path(x) for x in (cur.get("exec", {}).get("cwd_roots") or []) if isinstance(x, str)]
            if tighten_only and old_roots and not _subset(new_roots, old_roots):
                return current, "tighten_only_disallows_expanding:exec.cwd_roots"
            cur["exec"]["cwd_roots"] = new_roots
        if "command_whitelist" in exec_delta:
            v = exec_delta.get("command_whitelist")
            if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
                return current, "delta.exec.command_whitelist_must_be_list_of_strings"
            new = [x.strip() for x in v]
            old = [x.strip() for x in (cur.get("exec", {}).get("command_whitelist") or []) if isinstance(x, str)]
            if tighten_only and old and not _subset(new, old):
                return current, "tighten_only_disallows_expanding:exec.command_whitelist"
            cur["exec"]["command_whitelist"] = new
        if "env_allowlist" in exec_delta:
            v = exec_delta.get("env_allowlist")
            if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
                return current, "delta.exec.env_allowlist_must_be_list_of_strings"
            new = [x.strip() for x in v]
            old = [x.strip() for x in (cur.get("exec", {}).get("env_allowlist") or []) if isinstance(x, str)]
            if tighten_only and old and not _subset(new, old):
                return current, "tighten_only_disallows_expanding:exec.env_allowlist"
            cur["exec"]["env_allowlist"] = new

    web_delta = delta.get("web")
    if web_delta is not None:
        if not isinstance(web_delta, dict):
            return current, "delta.web_must_be_object"
        cur.setdefault("web", {})
        if "allow_domains" in web_delta:
            v = web_delta.get("allow_domains")
            if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
                return current, "delta.web.allow_domains_must_be_list_of_strings"
            new = [x.strip().lower() for x in v]
            old = [x.strip().lower() for x in (cur.get("web", {}).get("allow_domains") or []) if isinstance(x, str)]
            if tighten_only and old and not _subset(new, old):
                return current, "tighten_only_disallows_expanding:web.allow_domains"
            cur["web"]["allow_domains"] = new
        if "max_bytes_per_fetch" in web_delta:
            v = _clamp_int(web_delta.get("max_bytes_per_fetch"), 1, 50_000_000, 2_000_000)
            oldv = _clamp_int((cur.get("web", {}) or {}).get("max_bytes_per_fetch"), 1, 50_000_000, 2_000_000)
            if tighten_only and v > oldv:
                return current, "tighten_only_disallows_increasing:web.max_bytes_per_fetch"
            cur["web"]["max_bytes_per_fetch"] = v

    budgets_delta = delta.get("budgets")
    if budgets_delta is not None:
        if not isinstance(budgets_delta, dict):
            return current, "delta.budgets_must_be_object"
        cur.setdefault("budgets", {})
        for k in ("max_exec_ms_per_minute", "max_web_bytes_per_minute"):
            if k not in budgets_delta:
                continue
            v = _clamp_int(budgets_delta.get(k), 1, 10_000_000_000, _clamp_int(cur.get("budgets", {}).get(k), 1, 10_000_000_000, 1_000_000))
            oldv = _clamp_int(cur.get("budgets", {}).get(k), 1, 10_000_000_000, v)
            if tighten_only and v > oldv:
                return current, f"tighten_only_disallows_increasing:budgets.{k}"
            cur["budgets"][k] = v

    return cur, None


class GovernanceEngine:
    """
    Main entry point for policy evaluation and persistence.
    """

    def __init__(self) -> None:
        self._policy_store = GovernancePolicyStore(str(getattr(config.tools, "governance_policy_path", "data/governance/policy.json")))
        self._requests = GovernancePolicyRequests(str(getattr(config.tools, "governance_requests_path", "data/governance/policy_requests.json")))
        self._audit = GovernanceAuditLog(str(getattr(config.tools, "governance_audit_log_path", "data/governance/audit_log.jsonl")))

    def effective_policy(self) -> Dict[str, Any]:
        return self._policy_store.get_effective_policy()

    def audit(self) -> GovernanceAuditLog:
        return self._audit

    def evaluate_action(self, tool_name: str, arguments: Dict[str, Any]) -> PolicyDecision:
        policy = self.effective_policy()
        normalized: Dict[str, Any] = {}
        estimated: Dict[str, Any] = {}

        def tool_enabled(name: str) -> bool:
            t = (policy.get("tools") or {}).get(name) if isinstance(policy.get("tools"), dict) else None
            if isinstance(t, dict) and isinstance(t.get("enabled"), bool):
                return bool(t.get("enabled"))
            return True

        # Default allow if no policy configured for this tool.
        if not isinstance(tool_name, str) or not tool_name:
            return PolicyDecision(False, False, "tool_name_required", "invalid", {}, {})

        # Filesystem actions
        if tool_name in {"READ_FILE", "STAT_PATH", "LIST_DIR"}:
            if tool_name == "LIST_DIR":
                path = arguments.get("path", ".")
            else:
                path = arguments.get("path")
            if not isinstance(path, str) or not path.strip():
                return PolicyDecision(False, False, "path_required", "filesystem", {}, {})
            p = _norm_path(path)
            normalized["path"] = p
            roots = [str(x) for x in (policy.get("filesystem", {}) or {}).get("read_roots", []) if isinstance(x, str)]
            if roots and not _within_roots(p, roots):
                return PolicyDecision(False, False, "path_outside_read_roots", "filesystem.read_roots", normalized, {})
            return PolicyDecision(True, False, "allowed", "filesystem.read_roots", normalized, {})

        if tool_name in {"WRITE_FILE", "APPEND_FILE", "PATCH_FILE"}:
            if not tool_enabled(tool_name):
                return PolicyDecision(False, False, "tool_disabled", f"tools.{tool_name}.enabled", {}, {})
            path = arguments.get("path")
            if not isinstance(path, str) or not path.strip():
                return PolicyDecision(False, False, "path_required", "filesystem", {}, {})
            p = _norm_path(path)
            normalized["path"] = p
            roots = [str(x) for x in (policy.get("filesystem", {}) or {}).get("write_roots", []) if isinstance(x, str)]
            if roots and not _within_roots(p, roots):
                return PolicyDecision(False, False, "path_outside_write_roots", "filesystem.write_roots", normalized, {})
            return PolicyDecision(True, False, "allowed", "filesystem.write_roots", normalized, {})

        # Process execution
        if tool_name == "EXECUTE":
            if not tool_enabled("EXECUTE"):
                return PolicyDecision(False, False, "tool_disabled", "tools.EXECUTE.enabled", {}, {})
            cmd = arguments.get("cmd")
            cwd = arguments.get("cwd", os.getcwd())
            if not isinstance(cmd, str) or not cmd.strip():
                return PolicyDecision(False, False, "cmd_required", "exec", {}, {})
            if not isinstance(cwd, str) or not cwd.strip():
                cwd = os.getcwd()
            cwd_n = _norm_path(cwd)
            normalized["cwd"] = cwd_n
            roots = [str(x) for x in (policy.get("exec", {}) or {}).get("cwd_roots", []) if isinstance(x, str)]
            if roots and not _within_roots(cwd_n, roots):
                return PolicyDecision(False, False, "cwd_outside_allowed_roots", "exec.cwd_roots", normalized, {})
            # Base command extraction similar to ExecuteTool.
            base = ""
            try:
                import shlex

                parts = shlex.split(cmd.strip())
                for part in parts:
                    if "=" in part and not part.startswith(("./", "/")) and part.split("=", 1)[0].isidentifier():
                        continue
                    base = part
                    break
            except Exception:
                base = cmd.strip().split()[0] if cmd.strip().split() else ""
            normalized["base_command"] = base
            allowlist = [str(x) for x in (policy.get("exec", {}) or {}).get("command_whitelist", []) if isinstance(x, str) and x.strip()]
            if allowlist:
                if base not in allowlist:
                    return PolicyDecision(False, False, "command_not_allowed", "exec.command_whitelist", normalized, {"base_command": base, "allowed": allowlist})
            env_allowlist = arguments.get("env_allowlist") or []
            requested_env = [x for x in env_allowlist if isinstance(x, str) and x.strip()]
            allowed_env = [str(x) for x in (policy.get("exec", {}) or {}).get("env_allowlist", []) if isinstance(x, str) and x.strip()]
            if allowed_env:
                bad = [x for x in requested_env if x not in set(allowed_env)]
                if bad:
                    return PolicyDecision(False, False, "env_var_not_allowed", "exec.env_allowlist", normalized, {"disallowed": bad, "allowed": allowed_env})
            # budget estimate
            timeout = arguments.get("timeout", 60)
            est_timeout_s = _clamp_int(timeout, 1, 600, 60)
            estimated["exec_timeout_s"] = est_timeout_s
            estimated["exec_estimated_ms"] = int(est_timeout_s * 1000)

            # Budget enforcement: per-minute exec ms.
            budgets = policy.get("budgets") if isinstance(policy.get("budgets"), dict) else {}
            try:
                max_ms = int(budgets.get("max_exec_ms_per_minute")) if budgets and budgets.get("max_exec_ms_per_minute") is not None else None
            except Exception:
                max_ms = None
            if isinstance(max_ms, int) and max_ms > 0:
                now = datetime.now(timezone.utc).timestamp()
                used = self._audit.sum_cost_since(
                    since_epoch=float(now - 60.0),
                    event_type="action_result",
                    tool_name="EXECUTE",
                    cost_key="execution_time_ms",
                )
                projected = float(used) + float(estimated["exec_estimated_ms"])
                if projected > float(max_ms):
                    return PolicyDecision(
                        False,
                        False,
                        "budget_exceeded",
                        "budgets.max_exec_ms_per_minute",
                        normalized,
                        {
                            "budget": {"max_exec_ms_per_minute": int(max_ms), "used_exec_ms_last_minute": float(used), "estimated_exec_ms": float(estimated["exec_estimated_ms"])},
                        },
                    )
            return PolicyDecision(True, False, "allowed", "exec", normalized, estimated)

        # Web
        if tool_name in {"WEB_FETCH", "WEB_SEARCH"}:
            if not tool_enabled(tool_name):
                return PolicyDecision(False, False, "tool_disabled", f"tools.{tool_name}.enabled", {}, {})
            if tool_name == "WEB_SEARCH":
                return PolicyDecision(True, False, "allowed", "web.search", {}, {})
            url = arguments.get("url")
            if not isinstance(url, str) or not url.strip():
                return PolicyDecision(False, False, "url_required", "web", {}, {})
            normalized["url"] = url.strip()
            try:
                from urllib.parse import urlparse

                host = urlparse(url.strip()).hostname or ""
            except Exception:
                host = ""
            normalized["host"] = host
            allow_domains = [str(x).lower() for x in (policy.get("web", {}) or {}).get("allow_domains", []) if isinstance(x, str) and x.strip()]
            if allow_domains and host and host.lower() not in allow_domains:
                return PolicyDecision(False, False, "domain_not_allowed", "web.allow_domains", normalized, {"allowed_domains": allow_domains})
            max_bytes = arguments.get("max_bytes", (policy.get("web", {}) or {}).get("max_bytes_per_fetch", 2_000_000))
            estimated["max_bytes"] = _clamp_int(max_bytes, 1, 20_000_000, 2_000_000)

            # Budget enforcement: per-minute web bytes.
            budgets = policy.get("budgets") if isinstance(policy.get("budgets"), dict) else {}
            try:
                max_b = int(budgets.get("max_web_bytes_per_minute")) if budgets and budgets.get("max_web_bytes_per_minute") is not None else None
            except Exception:
                max_b = None
            if isinstance(max_b, int) and max_b > 0:
                now = datetime.now(timezone.utc).timestamp()
                used = self._audit.sum_cost_since(
                    since_epoch=float(now - 60.0),
                    event_type="action_result",
                    tool_name="WEB_FETCH",
                    cost_key="bytes",
                )
                projected = float(used) + float(estimated["max_bytes"])
                if projected > float(max_b):
                    return PolicyDecision(
                        False,
                        False,
                        "budget_exceeded",
                        "budgets.max_web_bytes_per_minute",
                        normalized,
                        {
                            "budget": {"max_web_bytes_per_minute": int(max_b), "used_web_bytes_last_minute": float(used), "estimated_web_bytes": float(estimated["max_bytes"])},
                        },
                    )
            return PolicyDecision(True, False, "allowed", "web", normalized, estimated)

        # Default: allow tool calls that are not explicitly scoped yet.
        return PolicyDecision(True, False, "allowed", "default_allow", {}, {})

    def set_policy_tighten_only(self, delta: Dict[str, Any], *, note: str = "") -> Dict[str, Any]:
        return self._policy_store.set_policy(delta=delta, note=note, tighten_only=True)

    def request_policy_change(self, proposal: Dict[str, Any], *, note: str = "") -> Dict[str, Any]:
        return self._requests.create(proposal=proposal, note=note)

    def get_policy_change_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        return self._requests.get(request_id)

    def list_policy_change_requests(self, *, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self._requests.list(status=status, limit=limit)

    def reject_policy_change_request(self, request_id: str, *, note: str = "") -> bool:
        return self._requests.mark_rejected(request_id, note=note)

    def commit_approved_request(self, request_id: str, approval_token: str, *, note: str = "") -> Dict[str, Any]:
        req = self._requests.get(request_id)
        if not req or not isinstance(req.get("proposal"), dict):
            raise ValueError("request_not_found")
        if req.get("status") != "pending":
            raise ValueError("request_not_pending")
        if not isinstance(approval_token, str) or not approval_token.strip():
            raise ValueError("approval_token_required")

        secret = get_token_secret()
        payload = verify_token(approval_token.strip(), secret)
        scopes = payload.get("scopes") or []
        if isinstance(scopes, str):
            scopes = [s.strip() for s in scopes.split(",") if s.strip()]
        scopes = list(scopes) if isinstance(scopes, list) else []
        needed = {f"policy_request:{request_id}", "policy:change"}
        if not needed.issubset(set(scopes)):
            raise ValueError("token_missing_required_scopes")

        version = self._policy_store.set_policy(delta=req["proposal"], note=note or f"approved:{request_id}", tighten_only=False)
        _ = self._requests.mark_applied(request_id, applied_version_id=int(version["version_id"]))
        return {"request_id": request_id, "applied_version": version}
