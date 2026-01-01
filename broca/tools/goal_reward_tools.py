"""
Learning/Goals macro tools.

These tools are part of the explicit action space and are intended to be:
- functional (no placeholders)
- auditable (persist + log experiences)
- integrated with the existing Broca learning and reasoning systems
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import config
from ..learning.experience_logger import ExperienceLogger
from ..reasoning.goal_manager import Goal, GoalManager, GoalStatus, GoalType
from ..reasoning.goal_snapshots import GoalSnapshotStore, serialize_goal_manager
from ..reasoning.state_manager import ReasoningStateManager


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass


def _normalize_goal_dict(goal_data: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(goal_data)
    if "name" in cleaned and isinstance(cleaned["name"], str):
        cleaned["name"] = cleaned["name"].strip()
    if "description" in cleaned and isinstance(cleaned["description"], str):
        cleaned["description"] = cleaned["description"].strip()
    return cleaned


def _parse_goal_type(value: Any) -> GoalType:
    if isinstance(value, GoalType):
        return value
    if isinstance(value, str):
        return GoalType(value.strip().lower())
    return GoalType.ACHIEVE


def _parse_goal_status(value: Any) -> GoalStatus:
    if isinstance(value, GoalStatus):
        return value
    if isinstance(value, str):
        return GoalStatus(value.strip().lower())
    return GoalStatus.ACTIVE


class SetGoalsTool:
    """
    Macro tool to manage the live GoalManager.

    This tool:
    - upserts/removes/suspends goals in the reasoning GoalManager
    - persists to reasoning state file (when enabled)
    - logs an experience via the learning system
    """

    _protected_goal_names = {
        "be_helpful_cognitive_assistant",
        "minimize_cognitive_dissonance",
        "implement_cognitive_reasoning",
    }

    def __init__(
        self,
        *,
        goal_manager: GoalManager,
        experience_logger: Optional[ExperienceLogger] = None,
        state_file_path: Optional[str] = None,
        snapshots_file_path: Optional[str] = None,
    ) -> None:
        self._goal_manager = goal_manager
        self._experience_logger = experience_logger
        self._state_file_path = state_file_path or getattr(config.reasoning, "state_file_path", "data/reasoning_state.json")
        self._snapshots_file_path = snapshots_file_path or getattr(config.reasoning, "goal_snapshots_file_path", "data/goal_snapshots.json")
        self._snapshot_store = GoalSnapshotStore(self._snapshots_file_path)

    @property
    def name(self) -> str:
        return "SET_GOALS"

    @property
    def description(self) -> str:
        return (
            "Manage the active goal set in the reasoning system. Supports upserting goals, "
            "suspending other goals, and removing goals. Persists to reasoning state and logs "
            "a learning experience for auditability."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["set_active", "upsert", "remove", "snapshot", "list_versions", "diff", "rollback"],
                    "default": "set_active",
                    "description": "set_active=upsert then optionally suspend others; upsert=only add/update; remove=delete goals by name",
                },
                "goals": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Goals to create/update (dicts compatible with Goal.from_dict())",
                },
                "remove_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Goal names to remove (used when mode=remove)",
                },
                "suspend_others": {
                    "type": "boolean",
                    "default": True,
                    "description": "When mode=set_active: suspend other non-protected goals not mentioned",
                },
                "allow_remove_protected": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, allow removing core system goals (dangerous)",
                },
                "persist": {
                    "type": "boolean",
                    "default": True,
                    "description": "Persist updated goal manager to reasoning state file (if enabled)",
                },
                "snapshot": {"type": "boolean", "default": True, "description": "Create an explicit goal snapshot after mutation"},
                "snapshot_label": {"type": "string", "description": "Optional label for the snapshot/checkpoint"},
                "snapshot_id": {"type": "integer", "description": "Snapshot ID (for rollback/diff)"},
                "from_snapshot_id": {"type": "integer", "description": "Diff base snapshot ID"},
                "to_snapshot_id": {"type": "integer", "description": "Diff target snapshot ID (optional; defaults to current)"},
                "limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 200},
                "rationale": {"type": "string", "description": "Why these goal changes are being made"},
            },
            "required": ["mode"],
        }

    def execute(
        self,
        mode: str = "set_active",
        goals: Optional[List[Dict[str, Any]]] = None,
        remove_names: Optional[List[str]] = None,
        suspend_others: bool = True,
        allow_remove_protected: bool = False,
        persist: bool = True,
        snapshot: bool = True,
        snapshot_label: Optional[str] = None,
        snapshot_id: Optional[int] = None,
        from_snapshot_id: Optional[int] = None,
        to_snapshot_id: Optional[int] = None,
        limit: int = 20,
        rationale: Optional[str] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        # Read-only policy: allow audit-only modes, block mutation.
        if getattr(config.tools, "tools_mode", "normal") == "read_only":
            allowed = {"list_versions", "diff"}
            mode_check = (mode or "").strip().lower()
            if mode_check not in allowed:
                return {"success": False, "error": "read_only_blocked", "mode": mode_check}

        goals = goals or []
        remove_names = remove_names or []
        mode_norm = (mode or "set_active").strip().lower()
        if mode_norm not in {"set_active", "upsert", "remove", "snapshot", "list_versions", "diff", "rollback"}:
            return {"success": False, "error": f"invalid_mode:{mode}"}

        # Audit modes
        if mode_norm == "list_versions":
            metas = self._snapshot_store.list(limit=limit)
            return {
                "success": True,
                "mode": mode_norm,
                "snapshots_file": self._snapshots_file_path,
                "count": len(metas),
                "snapshots": [asdict(m) for m in metas],
            }

        if mode_norm == "diff":
            base_id = int(from_snapshot_id or 0)
            if base_id <= 0:
                return {"success": False, "error": "from_snapshot_id_required"}
            base = self._snapshot_store.get(base_id)
            if base is None or not isinstance(base.get("goal_manager"), dict):
                return {"success": False, "error": "from_snapshot_not_found"}
            if to_snapshot_id is not None and int(to_snapshot_id) > 0:
                target_entry = self._snapshot_store.get(int(to_snapshot_id))
                if target_entry is None or not isinstance(target_entry.get("goal_manager"), dict):
                    return {"success": False, "error": "to_snapshot_not_found"}
                target_state = target_entry["goal_manager"]
                target_ref = {"type": "snapshot", "snapshot_id": int(to_snapshot_id)}
            else:
                target_state = serialize_goal_manager(self._goal_manager)
                target_ref = {"type": "current"}
            diff = self._snapshot_store.diff(base["goal_manager"], target_state)
            return {
                "success": True,
                "mode": mode_norm,
                "from_snapshot_id": base_id,
                "to": target_ref,
                "diff": diff,
            }

        if mode_norm == "rollback":
            sid = int(snapshot_id or 0)
            if sid <= 0:
                return {"success": False, "error": "snapshot_id_required"}
            with self._goal_manager.acquire_state_lock(timeout=2.0):
                ok, err = self._snapshot_store.rollback(self._goal_manager, sid)
                if not ok:
                    return {"success": False, "error": err or "rollback_failed"}
            persisted = False
            if persist and getattr(config.reasoning, "state_persistence_enabled", True):
                try:
                    sm = ReasoningStateManager(state_file_path=self._state_file_path, backup_enabled=True)
                    sm.save_state(goal_manager=self._goal_manager, force=True)
                    persisted = True
                except Exception:
                    persisted = False
            if self._experience_logger is not None:
                try:
                    self._experience_logger.log_experience(
                        {
                            "type": "set_goals",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "mode": mode_norm,
                            "rollback_snapshot_id": sid,
                            "rationale": rationale or "",
                            "success": True,
                        }
                    )
                except Exception:
                    pass
            return {
                "success": True,
                "mode": mode_norm,
                "rollback_snapshot_id": sid,
                "persisted": persisted,
                "active_goals": [g.to_dict() for g in self._goal_manager.get_active_goals()],
            }

        added: List[str] = []
        updated: List[str] = []
        suspended: List[str] = []
        removed: List[str] = []
        protected_blocked: List[str] = []

        with self._goal_manager.acquire_state_lock(timeout=2.0):
            if mode_norm == "remove":
                for raw in remove_names:
                    name = raw.strip() if isinstance(raw, str) else ""
                    if not name:
                        continue
                    if (not allow_remove_protected) and name in self._protected_goal_names:
                        protected_blocked.append(name)
                        continue
                    if self._goal_manager.remove_goal(name):
                        removed.append(name)

            else:
                seen_names: List[str] = []
                for raw_goal in goals:
                    if not isinstance(raw_goal, dict):
                        continue
                    gdict = _normalize_goal_dict(raw_goal)
                    name = gdict.get("name")
                    desc = gdict.get("description")
                    if not isinstance(name, str) or not name.strip():
                        return {"success": False, "error": "goal_missing_name"}
                    if not isinstance(desc, str) or not desc.strip():
                        return {"success": False, "error": f"goal_missing_description:{name}"}
                    name = name.strip()
                    seen_names.append(name)

                    existing = self._goal_manager.get_goal(name)
                    if existing is None:
                        goal = Goal(
                            name=name,
                            description=desc.strip(),
                            goal_type=_parse_goal_type(gdict.get("goal_type", "achieve")),
                            status=_parse_goal_status(gdict.get("status", "active")),
                            priority=_clamp01(float(gdict.get("priority", 0.5))),
                        )
                        goal.parent = gdict.get("parent") if isinstance(gdict.get("parent"), str) else None
                        goal.dependencies = list(gdict.get("dependencies") or [])
                        goal.success_conditions = list(gdict.get("success_conditions") or [])
                        goal.failure_conditions = list(gdict.get("failure_conditions") or [])
                        goal.tags = list(gdict.get("tags") or [])
                        goal.metadata = dict(gdict.get("metadata") or {})
                        if mode_norm == "set_active":
                            goal.status = GoalStatus.ACTIVE
                        if self._goal_manager.add_goal(goal):
                            added.append(name)
                            existing = goal
                        else:
                            existing = self._goal_manager.get_goal(name)

                    if existing is not None:
                        # Update fields (upsert semantics)
                        changed = False
                        if isinstance(desc, str) and desc.strip() and existing.description != desc.strip():
                            existing.description = desc.strip()
                            changed = True
                        if "goal_type" in gdict:
                            gt = _parse_goal_type(gdict.get("goal_type"))
                            if existing.goal_type != gt:
                                existing.goal_type = gt
                                changed = True
                        if "priority" in gdict:
                            pr = _clamp01(float(gdict.get("priority", existing.priority)))
                            if existing.priority != pr:
                                existing.priority = pr
                                changed = True
                        if "status" in gdict and mode_norm != "set_active":
                            st = _parse_goal_status(gdict.get("status"))
                            if existing.status != st:
                                existing.status = st
                                changed = True
                        if mode_norm == "set_active" and existing.status != GoalStatus.ACTIVE:
                            existing.status = GoalStatus.ACTIVE
                            changed = True

                        # Hierarchy + deps + conditions
                        if "parent" in gdict:
                            parent = gdict.get("parent")
                            if parent is not None and not isinstance(parent, str):
                                parent = None
                            if existing.parent != parent:
                                existing.parent = parent
                                changed = True
                        if "dependencies" in gdict:
                            deps = list(gdict.get("dependencies") or [])
                            if existing.dependencies != deps:
                                existing.dependencies = deps
                                changed = True
                        if "success_conditions" in gdict:
                            sc = list(gdict.get("success_conditions") or [])
                            if existing.success_conditions != sc:
                                existing.success_conditions = sc
                                changed = True
                        if "failure_conditions" in gdict:
                            fc = list(gdict.get("failure_conditions") or [])
                            if existing.failure_conditions != fc:
                                existing.failure_conditions = fc
                                changed = True
                        if "tags" in gdict:
                            tags = list(gdict.get("tags") or [])
                            if existing.tags != tags:
                                existing.tags = tags
                                changed = True
                        if "metadata" in gdict:
                            md = dict(gdict.get("metadata") or {})
                            if existing.metadata != md:
                                existing.metadata = md
                                changed = True

                        if changed and name not in added:
                            updated.append(name)
                        existing.last_updated = datetime.now(timezone.utc)

                        # Fix parent<->child linkage best-effort
                        if isinstance(existing.parent, str) and existing.parent in self._goal_manager.goals:
                            self._goal_manager.goals[existing.parent].add_child(existing.name)

                if mode_norm == "set_active" and suspend_others:
                    keep = set([n for n in seen_names if isinstance(n, str) and n])
                    for g in self._goal_manager.goals.values():
                        if g.name in self._protected_goal_names:
                            continue
                        if g.name in keep:
                            continue
                        if g.status == GoalStatus.ACTIVE:
                            g.status = GoalStatus.SUSPENDED
                            g.last_updated = datetime.now(timezone.utc)
                            suspended.append(g.name)

        # Persist to reasoning state file
        persisted = False
        if persist and getattr(config.reasoning, "state_persistence_enabled", True):
            try:
                sm = ReasoningStateManager(state_file_path=self._state_file_path, backup_enabled=True)
                sm.save_state(goal_manager=self._goal_manager, force=True)
                persisted = True
            except Exception:
                persisted = False

        # Log as learning experience
        if self._experience_logger is not None:
            try:
                self._experience_logger.log_experience(
                    {
                        "type": "set_goals",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "mode": mode_norm,
                        "added": added,
                        "updated": updated,
                        "suspended": suspended,
                        "removed": removed,
                        "blocked_protected": protected_blocked,
                        "rationale": rationale or "",
                        "success": True,
                    }
                )
            except Exception:
                pass

        snapshot_entry = None
        if snapshot or mode_norm == "snapshot":
            try:
                snapshot_entry = self._snapshot_store.create_snapshot(
                    self._goal_manager,
                    label=(snapshot_label or ""),
                    rationale=rationale or "",
                )
            except Exception:
                snapshot_entry = None

        return {
            "success": True,
            "mode": mode_norm,
            "added": added,
            "updated": updated,
            "suspended": suspended,
            "removed": removed,
            "blocked_protected": protected_blocked,
            "persisted": persisted,
            "snapshot": snapshot_entry,
            "active_goals": [g.to_dict() for g in self._goal_manager.get_active_goals()],
        }

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"SET_GOALS error: {result.get('error', 'unknown')}"
        return (
            f"SET_GOALS: added={len(result.get('added', []))} updated={len(result.get('updated', []))} "
            f"suspended={len(result.get('suspended', []))} removed={len(result.get('removed', []))} "
            f"persisted={bool(result.get('persisted'))}"
        )


class DesignRewardTool:
    """
    Macro tool to adjust reward shaping parameters (online_nn + PPO).

    This tool:
    - updates in-memory config.rl parameters used by reward shaping
    - optionally persists a human/audit-friendly record to JSON
    - logs an experience for the learning system
    """

    def __init__(
        self,
        *,
        experience_logger: Optional[ExperienceLogger] = None,
        design_file_path: Optional[str] = None,
    ) -> None:
        self._experience_logger = experience_logger
        self._design_file = Path(design_file_path or getattr(config.rl, "reward_design_path", "data/rl/reward_design.json"))

    @property
    def name(self) -> str:
        return "DESIGN_REWARD"

    @property
    def description(self) -> str:
        return (
            "Design/adjust the RL reward shaping parameters (success/failure reward, latency penalty, quality bonus). "
            "Applies changes immediately and records an audit entry."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "set", "history"],
                    "default": "set",
                    "description": "get=read current + persisted values; set=update; history=show recent changes",
                },
                "reward_success": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "reward_failure": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "time_penalty_factor": {"type": "number", "minimum": 0.0},
                "max_latency_penalty": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "quality_bonus_factor": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "persist": {"type": "boolean", "default": True},
                "limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 200},
                "rationale": {"type": "string"},
            },
            "required": [],
        }

    def execute(
        self,
        action: str = "set",
        reward_success: Optional[float] = None,
        reward_failure: Optional[float] = None,
        time_penalty_factor: Optional[float] = None,
        max_latency_penalty: Optional[float] = None,
        quality_bonus_factor: Optional[float] = None,
        persist: bool = True,
        limit: int = 20,
        rationale: Optional[str] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        act = (action or "set").strip().lower()
        if act not in {"get", "set", "history"}:
            return {"success": False, "error": f"invalid_action:{action}"}

        # Read-only policy: allow get/history, block set.
        if getattr(config.tools, "tools_mode", "normal") == "read_only" and act == "set":
            return {"success": False, "error": "read_only_blocked", "action": act}

        if act == "history":
            try:
                if not self._design_file.exists():
                    return {"success": True, "action": act, "history": [], "count": 0, "design_file": str(self._design_file)}
                existing = json.loads(self._design_file.read_text(encoding="utf-8"))
                history = list((existing.get("history") or [])) if isinstance(existing, dict) else []
                history = [h for h in history if isinstance(h, dict)]
                history = history[-max(1, int(limit)) :]
                return {"success": True, "action": act, "history": history, "count": len(history), "design_file": str(self._design_file)}
            except Exception as e:
                return {"success": False, "error": f"history_read_failed:{e}"}

        if act == "get":
            persisted = None
            try:
                if self._design_file.exists():
                    persisted = json.loads(self._design_file.read_text(encoding="utf-8"))
            except Exception:
                persisted = None
            return {
                "success": True,
                "action": act,
                "current_runtime": {
                    "reward_success": float(config.rl.reward_success),
                    "reward_failure": float(config.rl.reward_failure),
                    "time_penalty_factor": float(config.rl.time_penalty_factor),
                    "max_latency_penalty": float(config.rl.max_latency_penalty),
                    "quality_bonus_factor": float(config.rl.quality_bonus_factor),
                },
                "persisted": persisted,
                "design_file": str(self._design_file),
            }

        before = {
            "reward_success": float(config.rl.reward_success),
            "reward_failure": float(config.rl.reward_failure),
            "time_penalty_factor": float(config.rl.time_penalty_factor),
            "max_latency_penalty": float(config.rl.max_latency_penalty),
            "quality_bonus_factor": float(config.rl.quality_bonus_factor),
        }

        if reward_success is not None:
            config.rl.reward_success = _clamp01(float(reward_success))
        if reward_failure is not None:
            config.rl.reward_failure = _clamp01(float(reward_failure))
        if time_penalty_factor is not None:
            config.rl.time_penalty_factor = max(0.0, float(time_penalty_factor))
        if max_latency_penalty is not None:
            config.rl.max_latency_penalty = _clamp01(float(max_latency_penalty))
        if quality_bonus_factor is not None:
            config.rl.quality_bonus_factor = _clamp01(float(quality_bonus_factor))

        after = {
            "reward_success": float(config.rl.reward_success),
            "reward_failure": float(config.rl.reward_failure),
            "time_penalty_factor": float(config.rl.time_penalty_factor),
            "max_latency_penalty": float(config.rl.max_latency_penalty),
            "quality_bonus_factor": float(config.rl.quality_bonus_factor),
        }

        changed = {k: {"before": before[k], "after": after[k]} for k in before.keys() if before[k] != after[k]}
        timestamp = datetime.now(timezone.utc).isoformat()

        persisted = False
        if persist:
            try:
                existing: Dict[str, Any] = {}
                if self._design_file.exists():
                    existing = json.loads(self._design_file.read_text(encoding="utf-8"))
                history = list(existing.get("history") or [])
                history.append(
                    {
                        "timestamp": timestamp,
                        "changed": changed,
                        "rationale": rationale or "",
                        "applied": True,
                    }
                )
                record = {
                    "current": after,
                    "history": history[-200:],  # cap growth
                    "last_updated": timestamp,
                }
                _atomic_write_json(self._design_file, record)
                persisted = True
            except Exception:
                persisted = False

        if self._experience_logger is not None:
            try:
                self._experience_logger.log_experience(
                    {
                        "type": "design_reward",
                        "timestamp": timestamp,
                        "changed": changed,
                        "rationale": rationale or "",
                        "success": True,
                    }
                )
            except Exception:
                pass

        return {
            "success": True,
            "action": act,
            "changed": changed,
            "current": after,
            "persisted": persisted,
            "design_file": str(self._design_file),
        }

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"DESIGN_REWARD error: {result.get('error', 'unknown')}"
        changed = result.get("changed") or {}
        return f"DESIGN_REWARD: updated {len(changed)} field(s), persisted={bool(result.get('persisted'))}"
