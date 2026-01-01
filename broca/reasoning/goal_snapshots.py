"""
Goal snapshot persistence for audit + rollback.

This is intentionally separate from ReasoningStateManager:
- ReasoningStateManager persists the *live* state for restarts.
- GoalSnapshotStore persists explicit, user-initiated checkpoints and supports diff/rollback.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .goal_manager import Goal, GoalManager


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


def _canonical_goal_state(goal_manager_state: Dict[str, Any]) -> str:
    # Stable canonical JSON for hashing (sort goals by name; drop volatile fields).
    goals = [g for g in (goal_manager_state.get("goals") or []) if isinstance(g, dict)]
    def _strip(g: Dict[str, Any]) -> Dict[str, Any]:
        keep = dict(g)
        for k in ("created_at", "last_updated", "progress", "attempts"):
            keep.pop(k, None)
        return keep
    goals_sorted = sorted([_strip(g) for g in goals], key=lambda d: str(d.get("name", "")))
    canonical = {"goals": goals_sorted, "next_goal_id": goal_manager_state.get("next_goal_id", 0)}
    return json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def serialize_goal_manager(goal_manager: GoalManager) -> Dict[str, Any]:
    return {
        "goals": [g.to_dict() for g in goal_manager.goals.values()],
        "history": list(goal_manager.goal_history[-100:]),
        "next_goal_id": getattr(goal_manager, "next_goal_id", 0),
    }


def restore_goal_manager(goal_manager: GoalManager, state: Dict[str, Any]) -> None:
    goal_manager.goals = {}
    for goal_data in state.get("goals", []) or []:
        if not isinstance(goal_data, dict):
            continue
        try:
            g = Goal.from_dict(goal_data)
            goal_manager.goals[g.name] = g
        except Exception:
            continue
    goal_manager.goal_history = list(state.get("history", []) or [])
    if "next_goal_id" in state:
        try:
            goal_manager.next_goal_id = int(state["next_goal_id"])
        except Exception:
            pass
    try:
        goal_manager.refresh_goal_progress()
    except Exception:
        pass


@dataclass(frozen=True)
class GoalSnapshotMeta:
    snapshot_id: int
    timestamp: str
    label: str
    rationale: str
    sha256: str


class GoalSnapshotStore:
    """
    Append-only snapshot store with a bounded history.
    """

    def __init__(self, path: str, *, max_history: int = 200) -> None:
        self.path = Path(path)
        self.max_history = max(1, int(max_history))

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"current_snapshot_id": 0, "history": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"current_snapshot_id": 0, "history": []}
            history = data.get("history")
            if not isinstance(history, list):
                history = []
            return {"current_snapshot_id": int(data.get("current_snapshot_id", 0) or 0), "history": history}
        except Exception:
            return {"current_snapshot_id": 0, "history": []}

    def _save(self, data: Dict[str, Any]) -> None:
        _atomic_write_json(self.path, data)

    def list(self, limit: int = 20) -> List[GoalSnapshotMeta]:
        data = self._load()
        entries = [e for e in (data.get("history") or []) if isinstance(e, dict)]
        entries = entries[-max(1, int(limit)) :]
        metas: List[GoalSnapshotMeta] = []
        for e in entries:
            try:
                metas.append(
                    GoalSnapshotMeta(
                        snapshot_id=int(e.get("snapshot_id")),
                        timestamp=str(e.get("timestamp", "")),
                        label=str(e.get("label", "")),
                        rationale=str(e.get("rationale", "")),
                        sha256=str(e.get("sha256", "")),
                    )
                )
            except Exception:
                continue
        return metas

    def get(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        data = self._load()
        for e in (data.get("history") or []):
            if not isinstance(e, dict):
                continue
            if int(e.get("snapshot_id", -1)) == int(snapshot_id):
                return e
        return None

    def create_snapshot(self, goal_manager: GoalManager, *, label: str = "", rationale: str = "") -> Dict[str, Any]:
        data = self._load()
        current_id = int(data.get("current_snapshot_id", 0) or 0)
        next_id = current_id + 1
        timestamp = datetime.now(timezone.utc).isoformat()

        gm_state = serialize_goal_manager(goal_manager)
        canonical = _canonical_goal_state(gm_state)
        digest = _sha256_text(canonical)

        entry = {
            "snapshot_id": next_id,
            "timestamp": timestamp,
            "label": label or "",
            "rationale": rationale or "",
            "sha256": digest,
            "goal_manager": gm_state,
        }
        history = [e for e in (data.get("history") or []) if isinstance(e, dict)]
        history.append(entry)
        history = history[-self.max_history :]
        out = {"current_snapshot_id": next_id, "history": history, "last_updated": timestamp}
        self._save(out)
        return entry

    def diff(self, a_state: Dict[str, Any], b_state: Dict[str, Any]) -> Dict[str, Any]:
        def idx(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
            goals = [g for g in (state.get("goals") or []) if isinstance(g, dict)]
            return {str(g.get("name", "")): g for g in goals if isinstance(g.get("name"), str) and g.get("name")}

        a = idx(a_state)
        b = idx(b_state)
        added = sorted([n for n in b.keys() if n not in a])
        removed = sorted([n for n in a.keys() if n not in b])
        changed: Dict[str, Any] = {}

        keys = [
            "description",
            "goal_type",
            "status",
            "priority",
            "parent",
            "dependencies",
            "success_conditions",
            "failure_conditions",
            "tags",
            "metadata",
        ]
        for name in sorted(set(a.keys()) & set(b.keys())):
            diffs: Dict[str, Any] = {}
            for k in keys:
                av = a[name].get(k)
                bv = b[name].get(k)
                if av != bv:
                    diffs[k] = {"from": av, "to": bv}
            if diffs:
                changed[name] = diffs
        return {"added": added, "removed": removed, "changed": changed}

    def rollback(self, goal_manager: GoalManager, snapshot_id: int) -> Tuple[bool, Optional[str]]:
        entry = self.get(snapshot_id)
        if entry is None:
            return False, "snapshot_not_found"
        gm = entry.get("goal_manager")
        if not isinstance(gm, dict):
            return False, "invalid_snapshot_payload"
        restore_goal_manager(goal_manager, gm)
        return True, None

