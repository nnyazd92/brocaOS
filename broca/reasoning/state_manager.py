"""
State persistence layer for reasoning system.

Manages persistent state for rule system, goal manager, and working memory.
Provides thread-safe state loading, saving, and versioning.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from collections import deque

if TYPE_CHECKING:
    from .production_rules import ProductionRuleSystem
    from .goal_manager import GoalManager
    from .working_memory import WorkingMemory

logger = logging.getLogger(__name__)

# State schema version for evolution tracking
STATE_SCHEMA_VERSION = 2


class ReasoningStateManager:
    """
    Manages persistent state for reasoning system.
    
    Handles:
    - Rule system state (rules, history)
    - Goal manager state (goals, history)
    - Working memory state (items, associations)
    - Thread-safe operations with locks
    - Atomic writes for consistency
    - Version tracking for schema evolution
    """
    
    def __init__(
        self,
        state_file_path: str,
        auto_save_interval_seconds: float = 60.0,
        backup_enabled: bool = True
    ):
        """
        Initialize state manager.
        
        Args:
            state_file_path: Path to state JSON file
            auto_save_interval_seconds: Interval for automatic periodic saves
            backup_enabled: Whether to create backups before overwriting
        """
        self.state_file_path = state_file_path
        self.auto_save_interval = auto_save_interval_seconds
        self.backup_enabled = backup_enabled
        
        # Thread safety
        self._lock = threading.RLock()
        self._last_save_time = time.time()
        self._pending_changes = False
        
        # State version tracking
        self._state_version = 0
        self._schema_version = STATE_SCHEMA_VERSION
        
        logger.info(f"Initialized ReasoningStateManager with file: {state_file_path}")
    
    def load_state(
        self,
        rule_system: Optional["ProductionRuleSystem"] = None,
        goal_manager: Optional["GoalManager"] = None,
        working_memory: Optional["WorkingMemory"] = None,
        dissonance_monitor: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Load state from file and restore to components.
        
        Args:
            rule_system: Optional ProductionRuleSystem to restore rules to
            goal_manager: Optional GoalManager to restore goals to
            working_memory: Optional WorkingMemory to restore items to
            
        Returns:
            Dictionary containing loaded state
        """
        with self._lock:
            if not os.path.exists(self.state_file_path):
                logger.debug(f"State file does not exist: {self.state_file_path}")
                return self._create_empty_state()
            
            try:
                with open(self.state_file_path, "r") as f:
                    state_data = json.load(f)
                
                # Check schema version
                schema_version = state_data.get("schema_version", 0)
                if schema_version != self._schema_version:
                    logger.warning(
                        f"State schema version mismatch: file={schema_version}, "
                        f"current={self._schema_version}. Attempting migration..."
                    )
                    state_data = self._migrate_state(state_data, schema_version)
                
                self._state_version = state_data.get("state_version", 0)
                
                # Restore to components if provided
                if rule_system and "rule_system" in state_data:
                    self._restore_rule_system(rule_system, state_data["rule_system"])
                
                if goal_manager and "goal_manager" in state_data:
                    self._restore_goal_manager(goal_manager, state_data["goal_manager"])
                
                if working_memory and "working_memory" in state_data:
                    self._restore_working_memory(working_memory, state_data["working_memory"])

                if dissonance_monitor and "dissonance_monitor" in state_data:
                    try:
                        self._restore_dissonance_monitor(dissonance_monitor, state_data["dissonance_monitor"])
                    except Exception as e:
                        logger.warning(f"Failed to restore dissonance monitor state: {e}", exc_info=True)
                
                logger.info(f"Loaded state from {self.state_file_path} (version {self._state_version})")
                return state_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse state file {self.state_file_path}: {e}")
                return self._create_empty_state()
            except Exception as e:
                logger.error(f"Error loading state from {self.state_file_path}: {e}", exc_info=True)
                return self._create_empty_state()
    
    def save_state(
        self,
        rule_system: Optional["ProductionRuleSystem"] = None,
        goal_manager: Optional["GoalManager"] = None,
        working_memory: Optional["WorkingMemory"] = None,
        dissonance_monitor: Optional[Any] = None,
        force: bool = False
    ) -> bool:
        """
        Save current state to file.
        
        Args:
            rule_system: Optional ProductionRuleSystem to save
            goal_manager: Optional GoalManager to save
            working_memory: Optional WorkingMemory to save
            force: Force save even if no changes detected
            
        Returns:
            True if saved successfully, False otherwise
        """
        with self._lock:
            # Check if save is needed
            current_time = time.time()
            time_since_save = current_time - self._last_save_time
            
            if not force and not self._pending_changes:
                if time_since_save < self.auto_save_interval:
                    return True  # No changes and too soon for auto-save
            
            try:
                # Create backup if enabled
                if self.backup_enabled and os.path.exists(self.state_file_path):
                    backup_path = f"{self.state_file_path}.backup"
                    try:
                        import shutil
                        shutil.copy2(self.state_file_path, backup_path)
                        logger.debug(f"Created backup: {backup_path}")
                    except Exception as e:
                        logger.warning(f"Failed to create backup: {e}")
                
                # Collect state from components
                state_data = {
                    "schema_version": self._schema_version,
                    "state_version": self._state_version + 1,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                
                if rule_system:
                    state_data["rule_system"] = self._serialize_rule_system(rule_system)
                
                if goal_manager:
                    state_data["goal_manager"] = self._serialize_goal_manager(goal_manager)
                
                if working_memory:
                    state_data["working_memory"] = self._serialize_working_memory(working_memory)

                if dissonance_monitor:
                    state_data["dissonance_monitor"] = self._serialize_dissonance_monitor(dissonance_monitor)
                
                # Atomic write: write to temp file, then rename
                temp_path = f"{self.state_file_path}.tmp"
                with open(temp_path, "w") as f:
                    json.dump(state_data, f, indent=2)
                
                # Atomic rename
                os.replace(temp_path, self.state_file_path)
                
                self._state_version = state_data["state_version"]
                self._last_save_time = current_time
                self._pending_changes = False
                
                logger.debug(f"Saved state to {self.state_file_path} (version {self._state_version})")
                return True
                
            except Exception as e:
                logger.error(f"Error saving state to {self.state_file_path}: {e}", exc_info=True)
                return False
    
    def mark_changed(self):
        """Mark state as changed (triggers save on next auto-save interval)."""
        with self._lock:
            self._pending_changes = True
    
    def get_state_version(self) -> int:
        """Get current state version."""
        with self._lock:
            return self._state_version
    
    def _create_empty_state(self) -> Dict[str, Any]:
        """Create empty state structure."""
        return {
            "schema_version": self._schema_version,
            "state_version": 0,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "rule_system": {
                "rules": [],
                "history": []
            },
            "goal_manager": {
                "goals": [],
                "history": []
            },
            "working_memory": {
                "items": [],
                "associations": {}
            },
            "dissonance_monitor": {
                "dissonance_history": [],
                "logical_violations": [],
                "factual_errors": [],
                "behavioral_deviations": [],
                "behavioral_inconsistencies": [],
                "goal_conflicts": [],
                "commitment_strength": {},
            },
        }
    
    def _migrate_state(self, state_data: Dict[str, Any], from_version: int) -> Dict[str, Any]:
        """
        Migrate state from older schema version to current.
        
        Args:
            state_data: State data from file
            from_version: Schema version of loaded state
            
        Returns:
            Migrated state data
        """
        # Minimal migrations for schema evolution.
        if from_version < 2:
            state_data.setdefault("dissonance_monitor", {
                "dissonance_history": [],
                "logical_violations": [],
                "factual_errors": [],
                "behavioral_deviations": [],
                "behavioral_inconsistencies": [],
                "goal_conflicts": [],
                "commitment_strength": {},
            })

        state_data["schema_version"] = self._schema_version
        logger.info(f"Migrated state from version {from_version} to {self._schema_version}")
        return state_data

    def _serialize_dissonance_monitor(self, dissonance_monitor: Any) -> Dict[str, Any]:
        """
        Serialize CognitiveDissonanceMonitor state for persistence across restarts.

        We keep this bounded and JSON-safe. This is critical for RL continuity so dissonance
        does not reset to misleading defaults after a web server restart.
        """
        window = int(getattr(dissonance_monitor, "history_window", 100) or 100)

        def _serialize_violation_record(record: Any) -> Dict[str, Any]:
            """Serialize a violation record, converting datetime objects to ISO format."""
            if not isinstance(record, dict):
                return {}
            result = {}
            for k, v in record.items():
                if isinstance(v, datetime):
                    result[k] = v.isoformat()
                elif isinstance(v, dict):
                    # Recursively serialize nested dicts (e.g., 'violation' field)
                    result[k] = {
                        kk: vv.isoformat() if isinstance(vv, datetime) else vv
                        for kk, vv in v.items()
                    }
                else:
                    result[k] = v
            return result

        def _tail_list(obj: Any, max_items: int, serialize_records: bool = False) -> List[Any]:
            try:
                xs = list(obj)  # works for deque/list
                tail = xs[-max_items:]
                if serialize_records:
                    return [_serialize_violation_record(x) for x in tail]
                return tail
            except Exception:
                return []

        def _serialize_metrics(m: Any) -> Dict[str, Any]:
            try:
                ts = getattr(m, "timestamp", None)
                if isinstance(ts, datetime):
                    ts_s = ts.isoformat()
                else:
                    ts_s = datetime.now(timezone.utc).isoformat()
                return {
                    "timestamp": ts_s,
                    "logical_dissonance": float(getattr(m, "logical_dissonance", 0.0) or 0.0),
                    "factual_dissonance": float(getattr(m, "factual_dissonance", 0.0) or 0.0),
                    "behavioral_dissonance": float(getattr(m, "behavioral_dissonance", 0.0) or 0.0),
                    "goal_dissonance": float(getattr(m, "goal_dissonance", 0.0) or 0.0),
                    "overall_dissonance": float(getattr(m, "overall_dissonance", 0.0) or 0.0),
                    "measurement_quality": getattr(m, "measurement_quality", None),
                    "has_sufficient_data": bool(getattr(m, "has_sufficient_data", True)),
                    "component_availability": dict(getattr(m, "component_availability", {}) or {}),
                }
            except Exception:
                return {}

        # Commitment map can grow; bound to top-N by absolute strength.
        commitment = {}
        try:
            raw_commitment = getattr(dissonance_monitor, "_commitment_strength", {}) or {}
            if isinstance(raw_commitment, dict):
                items = [(str(k), float(v)) for k, v in raw_commitment.items()]
                items.sort(key=lambda kv: abs(kv[1]), reverse=True)
                commitment = {k: float(max(0.0, min(1.0, v))) for k, v in items[:500]}
        except Exception:
            commitment = {}

        history = _tail_list(getattr(dissonance_monitor, "dissonance_history", []), window)
        return {
            "history_window": window,
            "dissonance_history": [_serialize_metrics(m) for m in history if m is not None],
            "logical_violations": _tail_list(getattr(dissonance_monitor, "logical_violations", []), window, serialize_records=True),
            "factual_errors": _tail_list(getattr(dissonance_monitor, "factual_errors", []), window, serialize_records=True),
            "behavioral_deviations": _tail_list(getattr(dissonance_monitor, "behavioral_deviations", []), window, serialize_records=True),
            "behavioral_inconsistencies": _tail_list(getattr(dissonance_monitor, "behavioral_inconsistencies", []), window, serialize_records=True),
            "goal_conflicts": _tail_list(getattr(dissonance_monitor, "goal_conflicts", []), window, serialize_records=True),
            "commitment_strength": commitment,
        }

    def _restore_dissonance_monitor(self, dissonance_monitor: Any, data: Dict[str, Any]) -> None:
        """Restore CognitiveDissonanceMonitor state from a persisted snapshot."""
        if not isinstance(data, dict):
            return
        window = int(data.get("history_window") or getattr(dissonance_monitor, "history_window", 100) or 100)

        def _restore_deque(attr_name: str, values: Any) -> None:
            try:
                xs = values if isinstance(values, list) else []
                d = getattr(dissonance_monitor, attr_name, None)
                if isinstance(d, deque):
                    d.clear()
                    for v in xs[-d.maxlen:]:
                        d.append(v)
                else:
                    setattr(dissonance_monitor, attr_name, deque(xs[-window:], maxlen=window))
            except Exception:
                return

        # Restore component histories
        _restore_deque("logical_violations", data.get("logical_violations"))
        _restore_deque("factual_errors", data.get("factual_errors"))
        _restore_deque("behavioral_deviations", data.get("behavioral_deviations"))
        _restore_deque("behavioral_inconsistencies", data.get("behavioral_inconsistencies"))
        _restore_deque("goal_conflicts", data.get("goal_conflicts"))

        # Restore commitment map
        try:
            cs = data.get("commitment_strength", {})
            if isinstance(cs, dict):
                setattr(
                    dissonance_monitor,
                    "_commitment_strength",
                    {str(k): max(0.0, min(1.0, float(v))) for k, v in cs.items()},
                )
        except Exception:
            pass

        # Restore dissonance_history as DissonanceMetrics objects if possible
        try:
            from .cognitive_dissonance import DissonanceMetrics
            hist_items = data.get("dissonance_history") if isinstance(data.get("dissonance_history"), list) else []
            restored = []
            for item in hist_items[-window:]:
                if not isinstance(item, dict):
                    continue
                try:
                    ts_s = item.get("timestamp")
                    ts = datetime.fromisoformat(ts_s) if isinstance(ts_s, str) else datetime.now(timezone.utc)
                except Exception:
                    ts = datetime.now(timezone.utc)
                m = DissonanceMetrics(
                    timestamp=ts,
                    logical_dissonance=float(item.get("logical_dissonance", 0.0) or 0.0),
                    factual_dissonance=float(item.get("factual_dissonance", 0.0) or 0.0),
                    behavioral_dissonance=float(item.get("behavioral_dissonance", 0.0) or 0.0),
                    goal_dissonance=float(item.get("goal_dissonance", 0.0) or 0.0),
                    overall_dissonance=float(item.get("overall_dissonance", 0.0) or 0.0),
                    measurement_quality=item.get("measurement_quality"),
                    has_sufficient_data=bool(item.get("has_sufficient_data", True)),
                    component_availability=dict(item.get("component_availability") or {}),
                )
                restored.append(m)

            d = getattr(dissonance_monitor, "dissonance_history", None)
            if isinstance(d, deque):
                d.clear()
                for m in restored[-d.maxlen:]:
                    d.append(m)
            else:
                setattr(dissonance_monitor, "dissonance_history", deque(restored[-window:], maxlen=window))
        except Exception:
            # If we can't restore metrics objects, skip.
            pass
    
    def _serialize_rule_system(self, rule_system: "ProductionRuleSystem") -> Dict[str, Any]:
        """Serialize rule system state."""
        return {
            "rules": [rule.to_dict() for rule in rule_system.rules],
            "history": rule_system.rule_history[-100:],  # Last 100 entries
            "learning_enabled": rule_system.learning_enabled
        }
    
    def _serialize_goal_manager(self, goal_manager: "GoalManager") -> Dict[str, Any]:
        """Serialize goal manager state."""
        return {
            "goals": [goal.to_dict() for goal in goal_manager.goals.values()],
            "history": goal_manager.goal_history[-100:],  # Last 100 entries
            "next_goal_id": getattr(goal_manager, "next_goal_id", 0)
        }
    
    def _serialize_working_memory(self, working_memory: "WorkingMemory") -> Dict[str, Any]:
        """Serialize working memory state."""
        return {
            "items": [item.to_dict() for item in working_memory.items],
            "capacity": working_memory.capacity,
            "associations": getattr(working_memory, "associations", {})
        }
    
    def _restore_rule_system(self, rule_system: "ProductionRuleSystem", state: Dict[str, Any]):
        """Restore rule system from state."""
        from .production_rules import ProductionRule, RuleType
        
        # Restore rules
        rule_system.rules = []
        for rule_data in state.get("rules", []):
            try:
                rule = ProductionRule.from_dict(rule_data)
                rule_system.rules.append(rule)
            except Exception as e:
                logger.warning(f"Failed to restore rule {rule_data.get('name', 'unknown')}: {e}")
        
        # Restore history
        rule_system.rule_history = state.get("history", [])
        rule_system.learning_enabled = state.get("learning_enabled", True)
        
        logger.debug(f"Restored {len(rule_system.rules)} rules to rule system")
    
    def _restore_goal_manager(self, goal_manager: "GoalManager", state: Dict[str, Any]):
        """Restore goal manager from state."""
        from .goal_manager import Goal, GoalStatus, GoalType
        
        # Restore goals
        goal_manager.goals = {}
        for goal_data in state.get("goals", []):
            try:
                goal = Goal.from_dict(goal_data)
                goal_manager.goals[goal.name] = goal
            except Exception as e:
                logger.warning(f"Failed to restore goal {goal_data.get('name', 'unknown')}: {e}")
        
        # Restore history
        goal_manager.goal_history = state.get("history", [])
        
        if "next_goal_id" in state:
            goal_manager.next_goal_id = state["next_goal_id"]
        
        # Trigger progress computation for goals that don't have computed progress
        # This ensures progress reflects actual state, not default 0.0 values
        try:
            goal_manager.refresh_goal_progress()
        except Exception as e:
            logger.debug(f"Could not refresh goal progress after restore: {e}")
        
        logger.debug(f"Restored {len(goal_manager.goals)} goals to goal manager")
    
    def _restore_working_memory(self, working_memory: "WorkingMemory", state: Dict[str, Any]):
        """Restore working memory from state."""
        from .working_memory import WorkingMemoryItem
        
        # Restore items
        working_memory.items = []
        for item_data in state.get("items", []):
            try:
                item = WorkingMemoryItem.from_dict(item_data)
                working_memory.items.append(item)
            except Exception as e:
                logger.warning(f"Failed to restore working memory item: {e}")
        
        # Restore capacity if specified
        if "capacity" in state:
            working_memory.capacity = state["capacity"]
        
        # Restore associations if they exist
        if "associations" in state and hasattr(working_memory, "associations"):
            working_memory.associations = state["associations"]
        
        logger.debug(f"Restored {len(working_memory.items)} items to working memory")

