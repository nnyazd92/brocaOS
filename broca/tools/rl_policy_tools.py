"""
RL policy lifecycle tools (tool-selection ranker model + buffer).

These tools manage *how Broca chooses tools* (the RL ranker), not what actions
are allowed. For governance policy (capability gating/scopes/budgets), see
`broca/tools/policy_tools.py`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from ..config import config
from ..learning.experience_logger import ExperienceLogger
from ..rl.policy_evaluation import PolicyEvaluationStore
from ..rl.policy_versions import PolicyVersionStore


def _is_read_only() -> bool:
    return getattr(config.tools, "tools_mode", "normal") == "read_only"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _policy_store() -> PolicyVersionStore:
    return PolicyVersionStore(
        store_path=str(getattr(config.rl, "policy_versions_path", "data/rl/policy_versions.json")),
        archive_dir=str(getattr(config.rl, "policy_archive_dir", "models/rl/policy_versions")),
    )


def _eval_store() -> PolicyEvaluationStore:
    return PolicyEvaluationStore(path=str(getattr(config.rl, "policy_evaluations_path", "data/rl/policy_evaluations.json")))


def _ranker_kind(ranker: Any) -> str:
    name = ranker.__class__.__name__.lower() if ranker is not None else ""
    if "ppo" in name:
        return "ppo"
    return "online_nn"


def _active_paths_for_algorithm(algorithm: str) -> tuple[str, str]:
    if algorithm == "ppo":
        return str(config.rl.ppo_model_path), str(config.rl.ppo_buffer_path)
    return str(config.rl.model_path), str(config.rl.buffer_path)


def _sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    h = sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _model_fingerprint(path: Optional[str], *, max_bytes: int = 100_000_000, max_tensors: int = 200) -> Dict[str, Any]:
    if not isinstance(path, str) or not path:
        return {"exists": False}
    p = Path(path)
    if not p.exists():
        return {"exists": False, "path": path}
    try:
        size = int(p.stat().st_size)
    except Exception:
        size = -1
    out: Dict[str, Any] = {"exists": True, "path": str(p), "bytes": size}
    try:
        out["sha256"] = _sha256_file(p)
    except Exception:
        out["sha256"] = None

    if size < 0 or size > int(max_bytes):
        out["torch_fingerprint"] = {"available": False, "reason": "file_too_large"}
        return out

    try:
        import torch  # type: ignore
    except Exception:
        out["torch_fingerprint"] = {"available": False, "reason": "torch_unavailable"}
        return out

    try:
        ckpt = torch.load(str(p), map_location="cpu", weights_only=False)
    except Exception as e:
        out["torch_fingerprint"] = {"available": False, "reason": f"torch_load_failed:{e}"}
        return out

    state = None
    if isinstance(ckpt, dict):
        # common patterns: {"model_state_dict": ...} or {"state_dict": ...} or raw state dict.
        for key in ("model_state_dict", "state_dict"):
            if key in ckpt and isinstance(ckpt.get(key), dict):
                state = ckpt.get(key)
                break
        if state is None and all(isinstance(k, str) for k in ckpt.keys()):
            state = ckpt
    if not isinstance(state, dict):
        out["torch_fingerprint"] = {"available": False, "reason": "no_state_dict"}
        return out

    tensors = []
    for name, val in state.items():
        if len(tensors) >= int(max_tensors):
            break
        try:
            if hasattr(val, "detach"):
                t = val.detach().float().cpu()
                tensors.append({"name": str(name), "shape": list(t.shape), "l2": float(torch.linalg.norm(t).item())})
        except Exception:
            continue
    out["torch_fingerprint"] = {"available": True, "tensors": tensors, "count": len(tensors)}
    return out


class UpdatePolicyTool:
    def __init__(self, tool_registry: Any, experience_logger: Optional[ExperienceLogger] = None) -> None:
        self._registry = tool_registry
        self._experience_logger = experience_logger

    @property
    def name(self) -> str:
        return "UPDATE_POLICY"

    @property
    def description(self) -> str:
        return (
            "Run a bounded online update for the RL tool-selection ranker and optionally snapshot a candidate version. "
            "Contract: executes up to train_steps update iterations then persists ranker state."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "train_steps": {"type": "integer", "default": 1, "minimum": 0, "maximum": 1000},
                "snapshot": {"type": "boolean", "default": True},
                "label": {"type": "string"},
                "rationale": {"type": "string"},
            },
            "required": [],
        }

    def execute(self, train_steps: int = 1, snapshot: bool = True, label: str = "", rationale: str = "", **_: Any) -> Dict[str, Any]:
        if _is_read_only():
            return {"success": False, "error": "read_only_blocked"}
        ranker = getattr(self._registry, "online_policy_ranker", None)
        if ranker is None:
            return {"success": False, "error": "no_policy_ranker"}

        steps = max(0, min(1000, int(train_steps))) if isinstance(train_steps, int) else 1
        updates_ran = 0
        stop_reason = "completed"

        active_model_path, active_buffer_path = _active_paths_for_algorithm(_ranker_kind(ranker))

        def _try_update_once() -> bool:
            for m in ("_online_update", "online_update", "update", "train_step"):
                fn = getattr(ranker, m, None)
                if callable(fn):
                    fn()
                    return True
            return False

        def _try_save() -> bool:
            for m in ("_save_state", "save_state", "save"):
                fn = getattr(ranker, m, None)
                if callable(fn):
                    fn()
                    return True
            # Some rankers persist on update; treat as best-effort.
            return False

        before_sha = None
        try:
            if Path(active_model_path).exists():
                before_sha = _sha256_file(Path(active_model_path))
        except Exception:
            before_sha = None

        for _i in range(steps):
            if not _try_update_once():
                stop_reason = "no_update_method"
                break
            updates_ran += 1

        _ = _try_save()

        after_sha = None
        try:
            if Path(active_model_path).exists():
                after_sha = _sha256_file(Path(active_model_path))
        except Exception:
            after_sha = None

        candidate = None
        if bool(snapshot):
            store = _policy_store()
            candidate = store.create_version(
                algorithm=_ranker_kind(ranker),
                active_model_path=active_model_path,
                active_buffer_path=active_buffer_path,
                status="candidate",
                label=label or "",
                rationale=rationale or "",
                extra={"updates_ran": updates_ran, "stop_reason": stop_reason, "model_sha_before": before_sha, "model_sha_after": after_sha},
            )

        if self._experience_logger is not None:
            try:
                self._experience_logger.log_experience(
                    {
                        "type": "update_policy",
                        "timestamp": _now_iso(),
                        "updates_ran": updates_ran,
                        "stop_reason": stop_reason,
                        "candidate_version_id": candidate.get("version_id") if isinstance(candidate, dict) else None,
                        "success": True,
                    }
                )
            except Exception:
                pass

        return {
            "success": True,
            "algorithm": _ranker_kind(ranker),
            "updates_ran": updates_ran,
            "stop_reason": stop_reason,
            "model_sha_before": before_sha,
            "model_sha_after": after_sha,
            "candidate_version": candidate,
        }

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"UPDATE_POLICY error: {result.get('error', 'unknown')}"
        cand = result.get("candidate_version") or {}
        vid = cand.get("version_id") if isinstance(cand, dict) else None
        return f"UPDATE_POLICY: algorithm={result.get('algorithm')} updates={result.get('updates_ran')} candidate_version_id={vid}"


class EvaluatePolicyTool:
    def __init__(self, tool_registry: Any, experience_logger: Optional[ExperienceLogger] = None) -> None:
        self._registry = tool_registry
        self._experience_logger = experience_logger

    @property
    def name(self) -> str:
        return "EVALUATE_POLICY"

    @property
    def description(self) -> str:
        return "Compute simple, auditable metrics over the current policy replay buffer (optionally persist report)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 2000, "minimum": 1, "maximum": 200000},
                "persist": {"type": "boolean", "default": True},
                "label": {"type": "string"},
            },
            "required": [],
        }

    def execute(self, limit: int = 2000, persist: bool = True, label: str = "", **_: Any) -> Dict[str, Any]:
        if _is_read_only() and bool(persist):
            return {"success": False, "error": "read_only_blocked"}
        ranker = getattr(self._registry, "online_policy_ranker", None)
        if ranker is None:
            return {"success": False, "error": "no_policy_ranker"}

        lim = max(1, min(200000, int(limit))) if isinstance(limit, int) else 2000

        buf = getattr(ranker, "replay_buffer", None)
        exps = []
        if buf is not None:
            data = getattr(buf, "buffer", None)
            if isinstance(data, list):
                exps = data[-lim:]

        rewards = []
        tool_names = []
        for e in exps:
            try:
                r = float(getattr(e, "reward", 0.0))
            except Exception:
                continue
            rewards.append(r)
            tn = getattr(e, "tool_name", "")
            if isinstance(tn, str):
                tool_names.append(tn)

        stats = {
            "count": int(len(rewards)),
            "mean": float(np.mean(rewards)) if rewards else 0.0,
            "std": float(np.std(rewards)) if rewards else 0.0,
            "min": float(np.min(rewards)) if rewards else 0.0,
            "max": float(np.max(rewards)) if rewards else 0.0,
        }

        report = {
            "timestamp": _now_iso(),
            "label": label or "",
            "algorithm": _ranker_kind(ranker),
            "reward_stats": stats,
        }

        persisted = False
        if bool(persist):
            try:
                _eval_store().append(report)
                persisted = True
            except Exception:
                persisted = False

        if self._experience_logger is not None:
            try:
                self._experience_logger.log_experience({"type": "evaluate_policy", "timestamp": _now_iso(), "persisted": persisted, "success": True})
            except Exception:
                pass

        return {"success": True, "persisted": persisted, "report": {"reward_stats": stats, "algorithm": report["algorithm"], "timestamp": report["timestamp"], "label": report["label"]}}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"EVALUATE_POLICY error: {result.get('error', 'unknown')}"
        rep = result.get("report") or {}
        rs = rep.get("reward_stats") or {}
        return f"EVALUATE_POLICY: algorithm={rep.get('algorithm')} n={rs.get('count')} mean={rs.get('mean')}"


class PromotePolicyTool:
    def __init__(self, tool_registry: Any, experience_logger: Optional[ExperienceLogger] = None) -> None:
        self._registry = tool_registry
        self._experience_logger = experience_logger

    @property
    def name(self) -> str:
        return "PROMOTE_POLICY"

    @property
    def description(self) -> str:
        return "Promote a candidate version to active: restore artifacts into active paths and reload the ranker."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "version_id": {"type": "integer", "minimum": 1},
                "guard": {"type": "boolean", "default": True, "description": "If true, enforce POLICY_GUARD thresholds before promoting"},
                "guard_min_samples": {"type": "integer", "default": 50, "minimum": 1, "maximum": 1000000},
                "guard_min_mean_reward": {"type": "number", "default": 0.0, "minimum": -1000000.0, "maximum": 1000000.0},
                "guard_eval_limit": {"type": "integer", "default": 5000, "minimum": 1, "maximum": 200000},
            },
            "required": ["version_id"],
        }

    def execute(
        self,
        version_id: int,
        guard: bool = True,
        guard_min_samples: int = 50,
        guard_min_mean_reward: float = 0.0,
        guard_eval_limit: int = 5000,
        **_: Any,
    ) -> Dict[str, Any]:
        if _is_read_only():
            return {"success": False, "error": "read_only_blocked"}
        ranker = getattr(self._registry, "online_policy_ranker", None)
        if ranker is None:
            return {"success": False, "error": "no_policy_ranker"}

        algo = _ranker_kind(ranker)

        if bool(guard):
            guard_res = PolicyGuardTool().execute(
                version_id=version_id,
                min_samples=int(guard_min_samples),
                min_mean_reward=float(guard_min_mean_reward),
                eval_limit=int(guard_eval_limit),
            )
            if guard_res.get("success") and guard_res.get("allowed") is False:
                return {"success": False, "error": "guard_failed", "guard": guard_res}

        active_model_path, active_buffer_path = _active_paths_for_algorithm(algo)
        store = _policy_store()
        ok, err = store.restore_to_active_paths(version_id=int(version_id), active_model_path=active_model_path, active_buffer_path=active_buffer_path)
        if not ok:
            return {"success": False, "error": err or "restore_failed"}
        ok2, err2 = store.set_active(int(version_id))
        if not ok2:
            return {"success": False, "error": err2 or "set_active_failed"}

        # Reload ranker so in-memory matches disk (best-effort).
        try:
            from ..rl.policy_init import initialize_online_policy_ranker

            self._registry.set_online_policy_ranker(initialize_online_policy_ranker())
        except Exception:
            pass

        if self._experience_logger is not None:
            try:
                self._experience_logger.log_experience({"type": "promote_policy", "timestamp": _now_iso(), "version_id": int(version_id), "success": True})
            except Exception:
                pass

        return {"success": True, "algorithm": algo, "active_version_id": int(version_id)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"PROMOTE_POLICY error: {result.get('error', 'unknown')}"
        return f"PROMOTE_POLICY: algorithm={result.get('algorithm')} active_version_id={result.get('active_version_id')}"


class RollbackPolicyTool:
    def __init__(self, tool_registry: Any, experience_logger: Optional[ExperienceLogger] = None) -> None:
        self._registry = tool_registry
        self._experience_logger = experience_logger

    @property
    def name(self) -> str:
        return "ROLLBACK_POLICY"

    @property
    def description(self) -> str:
        return "Rollback to a prior policy version by restoring artifacts into the active paths and reloading the ranker."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"version_id": {"type": "integer", "minimum": 1}}, "required": ["version_id"]}

    def execute(self, version_id: int, **_: Any) -> Dict[str, Any]:
        if _is_read_only():
            return {"success": False, "error": "read_only_blocked"}
        ranker = getattr(self._registry, "online_policy_ranker", None)
        if ranker is None:
            return {"success": False, "error": "no_policy_ranker"}
        algo = _ranker_kind(ranker)
        active_model_path, active_buffer_path = _active_paths_for_algorithm(algo)
        store = _policy_store()
        ok, err = store.restore_to_active_paths(version_id=int(version_id), active_model_path=active_model_path, active_buffer_path=active_buffer_path)
        if not ok:
            return {"success": False, "error": err or "restore_failed"}
        ok2, err2 = store.set_active(int(version_id))
        if not ok2:
            return {"success": False, "error": err2 or "set_active_failed"}
        try:
            from ..rl.policy_init import initialize_online_policy_ranker

            self._registry.set_online_policy_ranker(initialize_online_policy_ranker())
        except Exception:
            pass
        if self._experience_logger is not None:
            try:
                self._experience_logger.log_experience({"type": "rollback_policy", "timestamp": _now_iso(), "version_id": int(version_id), "success": True})
            except Exception:
                pass
        return {"success": True, "algorithm": algo, "active_version_id": int(version_id)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"ROLLBACK_POLICY error: {result.get('error', 'unknown')}"
        return f"ROLLBACK_POLICY: algorithm={result.get('algorithm')} active_version_id={result.get('active_version_id')}"


class PolicyGuardTool:
    @property
    def name(self) -> str:
        return "POLICY_GUARD"

    @property
    def description(self) -> str:
        return "Check a candidate version's buffer reward stats against thresholds (auditable precheck for promotion)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "version_id": {"type": "integer", "minimum": 1},
                "min_samples": {"type": "integer", "default": 50, "minimum": 1},
                "min_mean_reward": {"type": "number", "default": 0.0},
                "eval_limit": {"type": "integer", "default": 5000, "minimum": 1},
            },
            "required": ["version_id"],
        }

    def execute(self, version_id: int, min_samples: int = 50, min_mean_reward: float = 0.0, eval_limit: int = 5000, **_: Any) -> Dict[str, Any]:
        store = _policy_store()
        entry = store.get(int(version_id))
        if entry is None:
            return {"success": False, "error": "version_not_found"}
        buf_path = entry.get("buffer_file")
        if not isinstance(buf_path, str) or not buf_path:
            return {"success": False, "error": "buffer_missing"}
        try:
            data = json.loads(Path(buf_path).read_text(encoding="utf-8"))
        except Exception:
            data = {}
        # Buffer schema varies; fallback to allow if unknown.
        rewards = []
        if isinstance(data, dict):
            # Try common keys
            items = data.get("experiences") or data.get("buffer") or data.get("items") or []
            if isinstance(items, list):
                for e in items[-max(1, int(eval_limit)) :]:
                    if isinstance(e, dict) and "reward" in e:
                        try:
                            rewards.append(float(e.get("reward")))
                        except Exception:
                            continue
        count = len(rewards)
        mean = float(np.mean(rewards)) if rewards else 0.0
        allowed = (count >= int(min_samples)) and (mean >= float(min_mean_reward))
        return {
            "success": True,
            "version_id": int(version_id),
            "allowed": bool(allowed),
            "stats": {"count": count, "mean": mean},
            "thresholds": {"min_samples": int(min_samples), "min_mean_reward": float(min_mean_reward)},
        }

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"POLICY_GUARD error: {result.get('error', 'unknown')}"
        return f"POLICY_GUARD: version_id={result.get('version_id')} allowed={bool(result.get('allowed'))}"


class PolicyListTool:
    @property
    def name(self) -> str:
        return "POLICY_LIST"

    @property
    def description(self) -> str:
        return "List policy (ranker) versions in the version store."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 200}}, "required": []}

    def execute(self, limit: int = 20, **_: Any) -> Dict[str, Any]:
        store = _policy_store()
        items = store.list(limit=int(limit))
        return {"success": True, "count": len(items), "versions": [v.__dict__ for v in items]}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"POLICY_LIST error: {result.get('error', 'unknown')}"
        return f"POLICY_LIST: {result.get('count')} versions"


class PolicyDiffTool:
    @property
    def name(self) -> str:
        return "POLICY_DIFF"

    @property
    def description(self) -> str:
        return "Diff two policy versions (metadata + buffer summary + model fingerprint)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from_version_id": {"type": "integer", "minimum": 1},
                "to_version_id": {"type": "integer", "minimum": 1},
                "include_buffer_summary": {"type": "boolean", "default": True},
            },
            "required": ["from_version_id", "to_version_id"],
        }

    def execute(self, from_version_id: int, to_version_id: int, include_buffer_summary: bool = True, **_: Any) -> Dict[str, Any]:
        store = _policy_store()
        a = store.get(int(from_version_id))
        b = store.get(int(to_version_id))
        if a is None or b is None:
            return {"success": False, "error": "version_not_found"}

        def _meta(e: Dict[str, Any]) -> Dict[str, Any]:
            return {k: e.get(k) for k in ("version_id", "timestamp", "status", "algorithm", "label", "rationale", "model_sha256", "buffer_sha256")}

        meta_a = _meta(a)
        meta_b = _meta(b)
        meta_diff = {}
        for k in sorted(set(meta_a.keys()) | set(meta_b.keys())):
            if meta_a.get(k) != meta_b.get(k):
                meta_diff[k] = {"from": meta_a.get(k), "to": meta_b.get(k)}

        out: Dict[str, Any] = {
            "success": True,
            "from_version_id": int(from_version_id),
            "to_version_id": int(to_version_id),
            "meta_diff": meta_diff,
            "from_meta": meta_a,
            "to_meta": meta_b,
            "from_model_fingerprint": _model_fingerprint(a.get("model_file")),
            "to_model_fingerprint": _model_fingerprint(b.get("model_file")),
        }

        if include_buffer_summary:
            out["buffer_summary"] = {"from": _buffer_summary(a.get("buffer_file")), "to": _buffer_summary(b.get("buffer_file"))}
        return out

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"POLICY_DIFF error: {result.get('error', 'unknown')}"
        md = result.get("meta_diff") or {}
        return f"POLICY_DIFF: meta_changes={len(md) if isinstance(md, dict) else 0}"


def _buffer_summary(path: Any, *, max_items: int = 5000) -> Dict[str, Any]:
    if not isinstance(path, str) or not path:
        return {"exists": False}
    p = Path(path)
    if not p.exists():
        return {"exists": False, "path": path}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"exists": True, "path": str(p), "error": "json_parse_failed"}
    # Reward stats over common buffer shapes.
    rewards = []
    if isinstance(data, dict):
        items = data.get("buffer") or data.get("experiences") or data.get("items") or []
        if isinstance(items, list):
            for e in items[-max_items:]:
                if isinstance(e, dict) and "reward" in e:
                    try:
                        rewards.append(float(e.get("reward")))
                    except Exception:
                        continue
    return {
        "exists": True,
        "path": str(p),
        "count": len(rewards),
        "mean_reward": float(np.mean(rewards)) if rewards else 0.0,
        "min_reward": float(np.min(rewards)) if rewards else 0.0,
        "max_reward": float(np.max(rewards)) if rewards else 0.0,
    }

