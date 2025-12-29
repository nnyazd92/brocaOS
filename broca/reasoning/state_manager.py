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

if TYPE_CHECKING:
    from .production_rules import ProductionRuleSystem
    from .goal_manager import GoalManager
    from .working_memory import WorkingMemory

logger = logging.getLogger(__name__)

# State schema version for evolution tracking
STATE_SCHEMA_VERSION = 1


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
        working_memory: Optional["WorkingMemory"] = None
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
            }
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
        # For now, just update schema version
        # In future, add migration logic for schema changes
        state_data["schema_version"] = self._schema_version
        logger.info(f"Migrated state from version {from_version} to {self._schema_version}")
        return state_data
    
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

