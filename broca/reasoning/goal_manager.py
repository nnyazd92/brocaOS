"""
Goal management for cognitive reasoning.

Implements hierarchical goal representation, decomposition,
and pursuit similar to SOAR and ACT-R goal systems.
"""

from __future__ import annotations

import logging
import json
import threading
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager

if TYPE_CHECKING:
    from .declarative_memory import DeclarativeMemoryInterface

logger = logging.getLogger(__name__)


class GoalStatus(Enum):
    """Status of a goal."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class GoalType(Enum):
    """Types of goals."""
    ACHIEVE = "achieve"      # Achieve a state
    MAINTAIN = "maintain"    # Maintain a state
    PERFORM = "perform"      # Perform an action
    LEARN = "learn"          # Learn something
    EXPLORE = "explore"      # Explore possibilities


@dataclass
class Goal:
    """
    A goal in the cognitive architecture.
    
    Represents desired states or outcomes that the system
    should work towards achieving.
    """
    
    name: str
    description: str
    goal_type: GoalType = GoalType.ACHIEVE
    status: GoalStatus = GoalStatus.ACTIVE
    priority: float = 0.5  # 0.0 to 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Goal structure
    parent: Optional[str] = None  # Parent goal name
    children: List[str] = field(default_factory=list)  # Child goal names
    dependencies: List[str] = field(default_factory=list)  # Goals that must be completed first
    
    # Success criteria
    success_conditions: List[Dict[str, Any]] = field(default_factory=list)
    failure_conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Progress tracking
    progress: Optional[float] = None  # 0.0 to 1.0, None means not computed yet
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = 0
    max_attempts: int = 3
    
    # Resources
    required_resources: List[str] = field(default_factory=list)
    allocated_resources: List[str] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert goal to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "goal_type": self.goal_type.value,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "parent": self.parent,
            "children": self.children,
            "dependencies": self.dependencies,
            "success_conditions": self.success_conditions,
            "failure_conditions": self.failure_conditions,
            "progress": self.progress,  # Store None if not computed, actual value if computed
            "last_updated": self.last_updated.isoformat(),
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "required_resources": self.required_resources,
            "allocated_resources": self.allocated_resources,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @staticmethod
    def _parse_progress(progress_value: Any) -> Optional[float]:
        """Parse progress value, handling None and 0.0 cases."""
        if progress_value is None:
            return None  # Not computed
        elif isinstance(progress_value, (int, float)) and progress_value == 0.0:
            # Could be default 0.0 from old code - set to None to trigger recomputation
            return None
        else:
            # progress > 0.0, so it was computed - keep it
            return float(progress_value)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Goal:
        """Create goal from dictionary representation."""
        return cls(
            name=data["name"],
            description=data["description"],
            goal_type=GoalType(data.get("goal_type", "achieve")),
            status=GoalStatus(data.get("status", "active")),
            priority=data.get("priority", 0.5),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            parent=data.get("parent"),
            children=data.get("children", []),
            dependencies=data.get("dependencies", []),
            success_conditions=data.get("success_conditions", []),
            failure_conditions=data.get("failure_conditions", []),
            # Don't default to 0.0 - None means not computed yet
            # If progress is 0.0, it might be a default value from old code
            # We'll set it to None and let refresh_goal_progress recompute it
            # If progress > 0.0, we know it was computed, so keep it
            progress=cls._parse_progress(data.get("progress")),
            last_updated=datetime.fromisoformat(data["last_updated"]) if "last_updated" in data else datetime.now(timezone.utc),
            attempts=data.get("attempts", 0),
            max_attempts=data.get("max_attempts", 3),
            required_resources=data.get("required_resources", []),
            allocated_resources=data.get("allocated_resources", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
    
    def update_progress(self, progress: float, reason: str = ""):
        """Update goal progress."""
        old_progress = self.progress
        self.progress = max(0.0, min(1.0, progress))
        self.last_updated = datetime.now(timezone.utc)
        
        old_str = f"{old_progress:.2f}" if old_progress is not None else "None"
        progress_change = (self.progress - old_progress) if old_progress is not None else self.progress
        
        logger.info(
            f"Goal progress updated: name={self.name}, progress={old_str} -> {self.progress:.3f} "
            f"(change={progress_change:+.3f}), status={self.status.value}, "
            f"reason={reason or 'none'}",
            extra={
                "event": "goal_progress_updated",
                "goal_name": self.name,
                "old_progress": old_progress,
                "new_progress": self.progress,
                "progress_change": progress_change,
                "status": self.status.value,
                "reason": reason or "",
            }
        )
        
        # Check if goal is completed
        if self.progress >= 1.0:
            old_status = self.status
            self.status = GoalStatus.COMPLETED
            logger.info(
                f"Goal completed: name={self.name}, final_progress={self.progress:.3f}, "
                f"status_change={old_status.value} -> {self.status.value}",
                extra={
                    "event": "goal_completed",
                    "goal_name": self.name,
                    "final_progress": self.progress,
                    "old_status": old_status.value,
                    "new_status": self.status.value,
                }
            )
    
    def increment_attempts(self):
        """Increment attempt count and check for failure."""
        self.attempts += 1
        self.last_updated = datetime.now(timezone.utc)
        
        if self.attempts >= self.max_attempts:
            old_status = self.status
            self.status = GoalStatus.FAILED
            logger.warning(
                f"Goal failed: name={self.name}, attempts={self.attempts}/{self.max_attempts}, "
                f"status_change={old_status.value} -> {self.status.value}",
                extra={
                    "event": "goal_failed",
                    "goal_name": self.name,
                    "attempts": self.attempts,
                    "max_attempts": self.max_attempts,
                    "old_status": old_status.value,
                    "new_status": self.status.value,
                }
            )
    
    def is_ready(self, completed_goals: List[str]) -> bool:
        """Check if goal is ready to work on (dependencies satisfied)."""
        if self.status != GoalStatus.ACTIVE:
            return False
        
        # Check dependencies
        for dep in self.dependencies:
            if dep not in completed_goals:
                return False
        
        return True
    
    def add_child(self, child_name: str):
        """Add a child goal."""
        if child_name not in self.children:
            self.children.append(child_name)
    
    def remove_child(self, child_name: str):
        """Remove a child goal."""
        if child_name in self.children:
            self.children.remove(child_name)


class GoalManager:
    """
    Manages hierarchical goal structures.
    
    Supports goal decomposition, prioritization, dependency
    resolution, and progress tracking.
    """
    
    def __init__(
        self, 
        declarative_memory: Optional["DeclarativeMemoryInterface"] = None,
        cognitive_dissonance_monitor: Optional[Any] = None,
        rule_system: Optional[Any] = None,
        working_memory: Optional[Any] = None
    ):
        """
        Initialize goal manager.
        
        Args:
            declarative_memory: Optional DeclarativeMemoryInterface for memory integration
            cognitive_dissonance_monitor: Optional cognitive dissonance monitor for progress computation
            rule_system: Optional rule system for progress computation
            working_memory: Optional working memory for progress computation
        """
        self.goals: Dict[str, Goal] = {}  # name -> Goal
        self.goal_history: List[Dict[str, Any]] = []
        self.next_goal_id: int = 1
        self.declarative_memory = declarative_memory
        
        # Thread safety for state synchronization
        self._state_lock = threading.RLock()
        
        # Note: Z3 validator has been removed. Use the z3_validate tool instead
        # for LLM-driven logical validation when needed.
        
        # Optional references for progress computation
        self._cognitive_dissonance_monitor = cognitive_dissonance_monitor
        self._rule_system = rule_system
        self._working_memory = working_memory
        
        # Default goals
        self._add_default_goals()
    
    @contextmanager
    def acquire_state_lock(self, timeout: Optional[float] = None):
        """
        Context manager for acquiring state lock.
        
        Args:
            timeout: Optional timeout in seconds (None = no timeout)
        """
        acquired = self._state_lock.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError(f"Failed to acquire state lock within {timeout}s")
        try:
            yield
        finally:
            self._state_lock.release()
    
    def _add_default_goals(self):
        """Add default system goals."""
        # Root goal: Be a helpful cognitive assistant
        root_goal = Goal(
            name="be_helpful_cognitive_assistant",
            description="Be a helpful, capable cognitive assistant that can reason, learn, and solve problems",
            goal_type=GoalType.MAINTAIN,
            priority=1.0,
            status=GoalStatus.ACTIVE
        )
        self.add_goal(root_goal)
        
        # Core goal: Minimize cognitive dissonance (highest priority after root)
        dissonance_goal = Goal(
            name="minimize_cognitive_dissonance",
            description="Maintain alignment with self-model by minimizing cognitive dissonance across all dimensions (logical, factual, behavioral, goal-based)",
            goal_type=GoalType.MAINTAIN,
            priority=1.0,  # Highest priority
            status=GoalStatus.ACTIVE,
            parent="be_helpful_cognitive_assistant",
            dependencies=[],
            success_conditions=[
                {"type": "overall_dissonance", "operator": "<", "value": 0.2},
                {"type": "no_critical_dissonance", "operator": "==", "value": True}
            ],
            progress=None  # Will be computed from actual dissonance measurements
        )
        self.add_goal(dissonance_goal)
        root_goal.add_child("minimize_cognitive_dissonance")
        
        # Subgoal: Implement cognitive reasoning capabilities
        reasoning_goal = Goal(
            name="implement_cognitive_reasoning",
            description="Implement production rule system and cognitive reasoning capabilities",
            goal_type=GoalType.ACHIEVE,
            priority=0.9,
            status=GoalStatus.ACTIVE,
            parent="be_helpful_cognitive_assistant",
            dependencies=[],
            progress=None  # Will be computed from actual rule system state
        )
        self.add_goal(reasoning_goal)
        
        # Add as child of root
        root_goal.add_child("implement_cognitive_reasoning")
    
    def add_goal(self, goal: Goal) -> bool:
        """Add a goal to the manager."""
        with self._state_lock:
            if goal.name in self.goals:
                logger.warning(f"Goal '{goal.name}' already exists")
                return False
            
            # Note: Z3 validation has been removed. Use the z3_validate tool instead
            # for LLM-driven logical validation when needed.
                    # Continue with goal addition even if validation fails
            
            self.goals[goal.name] = goal
        
            # Record in history
            self.goal_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "add",
                "goal": goal.name,
                "description": goal.description
            })
            
            # Retrieve goal-related memories when goal becomes active
            if goal.status == GoalStatus.ACTIVE and self.declarative_memory:
                try:
                    memories = self.declarative_memory.get_context_for_goal(goal.name, limit=5)
                    if memories:
                        logger.debug(f"Retrieved {len(memories)} memories for new active goal: {goal.name}")
                except Exception as e:
                    logger.error(f"Error retrieving memories for goal {goal.name}: {e}", exc_info=True)
            
            logger.info(
                f"Added goal: name={goal.name}, type={goal.goal_type.value}, "
                f"status={goal.status.value}, priority={goal.priority:.3f}, "
                f"parent={goal.parent}, dependencies={len(goal.dependencies)}, "
                f"children={len(goal.children)}, total_goals={len(self.goals)}",
                extra={
                    "event": "goal_added",
                    "goal_name": goal.name,
                    "goal_type": goal.goal_type.value,
                    "status": goal.status.value,
                    "priority": goal.priority,
                    "parent": goal.parent,
                    "dependencies_count": len(goal.dependencies),
                    "children_count": len(goal.children),
                    "total_goals": len(self.goals),
                }
            )
            return True
    
    def remove_goal(self, goal_name: str) -> bool:
        """Remove a goal by name."""
        with self._state_lock:
            if goal_name not in self.goals:
                return False
            
            # Remove from parent's children list if has parent
            goal = self.goals[goal_name]
            if goal.parent and goal.parent in self.goals:
                self.goals[goal.parent].remove_child(goal_name)
            
            # Remove from children's parent references
            for child_name in goal.children:
                if child_name in self.goals:
                    self.goals[child_name].parent = None
            
            # Record removal in history
            self.goal_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "remove",
                "goal": goal_name,
                "status": goal.status.value,
                "priority": goal.priority,
            })
            
            del self.goals[goal_name]
            
            logger.info(
                f"Removed goal: name={goal_name}, had_parent={goal.parent is not None}, "
                f"had_children={len(goal.children)}, remaining_goals={len(self.goals)}",
                extra={
                    "event": "goal_removed",
                    "goal_name": goal_name,
                    "goal_status": goal.status.value,
                    "goal_priority": goal.priority,
                    "had_parent": goal.parent is not None,
                    "children_count": len(goal.children),
                    "remaining_goals": len(self.goals),
                }
            )
            return True
    
    def get_goal(self, goal_name: str) -> Optional[Goal]:
        """Get a goal by name."""
        return self.goals.get(goal_name)
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        return [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]
    
    def get_ready_goals(self) -> List[Goal]:
        """
        Get goals that are ready to work on.
        
        Returns active goals whose dependencies are satisfied.
        """
        completed_goals = [g.name for g in self.goals.values() 
                          if g.status == GoalStatus.COMPLETED]
        
        ready_goals = []
        for goal in self.get_active_goals():
            if goal.is_ready(completed_goals):
                ready_goals.append(goal)
        
        # Sort by priority (highest first), then creation time
        ready_goals.sort(key=lambda g: (g.priority, g.created_at), reverse=True)
        return ready_goals
    
    def get_next_goal(self) -> Optional[Goal]:
        """
        Get the highest priority ready goal.
        
        If declarative memory is available, retrieves memories related to ready goals
        to provide context for goal decision-making.
        """
        ready_goals = self.get_ready_goals()
        if not ready_goals:
            return None
        
        # Retrieve memories related to top ready goals
        if self.declarative_memory and ready_goals:
            try:
                # Retrieve memories for top 3 ready goals
                for goal in ready_goals[:3]:
                    memories = self.declarative_memory.get_context_for_goal(goal.name, limit=3)
                    if memories:
                        logger.debug(f"Retrieved {len(memories)} memories for ready goal: {goal.name}")
            except Exception as e:
                logger.error(f"Error retrieving memories for ready goals: {e}", exc_info=True)
        
        return ready_goals[0]
    
    def decompose_goal(self, goal_name: str, decomposition: List[Dict[str, Any]]) -> List[str]:
        """
        Decompose a goal into subgoals.
        
        Returns list of created subgoal names.
        """
        if goal_name not in self.goals:
            logger.warning(f"Cannot decompose non-existent goal: {goal_name}")
            return []
        
        parent_goal = self.goals[goal_name]
        created_subgoals = []
        
        for i, subgoal_data in enumerate(decomposition):
            subgoal_name = f"{goal_name}_sub{i+1}"
            
            subgoal = Goal(
                name=subgoal_name,
                description=subgoal_data.get("description", f"Subgoal {i+1} of {goal_name}"),
                goal_type=GoalType(subgoal_data.get("goal_type", "achieve")),
                status=GoalStatus.ACTIVE,
                priority=subgoal_data.get("priority", parent_goal.priority * 0.9),
                parent=goal_name,
                dependencies=subgoal_data.get("dependencies", []),
                success_conditions=subgoal_data.get("success_conditions", []),
                failure_conditions=subgoal_data.get("failure_conditions", []),
            )
            
            if self.add_goal(subgoal):
                parent_goal.add_child(subgoal_name)
                created_subgoals.append(subgoal_name)
        
        logger.info(
            f"Decomposed goal: name={goal_name}, subgoals_created={len(created_subgoals)}, "
            f"total_goals={len(self.goals)}",
            extra={
                "event": "goal_decomposed",
                "goal_name": goal_name,
                "subgoals_created": len(created_subgoals),
                "subgoal_names": created_subgoals,
                "total_goals": len(self.goals),
            }
        )
        return created_subgoals
    
    def update_goal_progress(self, goal_name: str, progress: float, reason: str = ""):
        """Update progress of a goal."""
        with self._state_lock:
            if goal_name not in self.goals:
                logger.warning(f"Cannot update progress of non-existent goal: {goal_name}")
                return
            
            goal = self.goals[goal_name]
            goal.update_progress(progress, reason)
            
            # Record in history
            self.goal_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "update_progress",
                "goal": goal_name,
                "progress": progress,
                "reason": reason
            })
            
            # Store goal progress to declarative memory
            if self.declarative_memory:
                try:
                    self.declarative_memory.store_goal_progress(
                        goal_name=goal_name,
                        progress=progress,
                        description=reason
                    )
                except Exception as e:
                    logger.error(f"Error storing goal progress to declarative memory: {e}", exc_info=True)
    
    def update_dissonance_goal_progress(self, overall_dissonance: float, critical_threshold: float = 0.7):
        """
        Update progress of the minimize_cognitive_dissonance goal based on actual dissonance.
        
        Args:
            overall_dissonance: Current overall cognitive dissonance score (0.0-1.0)
            critical_threshold: Critical threshold for considering goal failed
        """
        goal_name = "minimize_cognitive_dissonance"
        if goal_name not in self.goals:
            return  # Goal doesn't exist yet
        
        # Progress is inverse of dissonance (low dissonance = high progress)
        # Clamp to [0, 1] range
        progress = max(0.0, min(1.0, 1.0 - overall_dissonance))
        
        # Update progress
        reason = f"Dissonance: {overall_dissonance:.3f}"
        self.update_goal_progress(goal_name, progress, reason)
        
        logger.info(
            f"Dissonance goal progress updated: name={goal_name}, dissonance={overall_dissonance:.3f}, "
            f"progress={progress:.3f}, critical_threshold={critical_threshold}",
            extra={
                "event": "dissonance_goal_progress_updated",
                "goal_name": goal_name,
                "overall_dissonance": overall_dissonance,
                "progress": progress,
                "critical_threshold": critical_threshold,
            }
        )
        
        # Check if goal should be marked as failed (critical dissonance)
        if overall_dissonance > critical_threshold:
            goal = self.goals[goal_name]
            if goal.status != GoalStatus.FAILED:
                old_status = goal.status
                goal.status = GoalStatus.FAILED
                logger.warning(
                    f"Goal marked as failed due to critical dissonance: name={goal_name}, "
                    f"dissonance={overall_dissonance:.3f} > threshold={critical_threshold}, "
                    f"status_change={old_status.value} -> {goal.status.value}",
                    extra={
                        "event": "goal_failed_critical_dissonance",
                        "goal_name": goal_name,
                        "dissonance": overall_dissonance,
                        "critical_threshold": critical_threshold,
                        "old_status": old_status.value,
                        "new_status": goal.status.value,
                    }
                )
    
    def _compute_goal_progress(
        self, 
        goal: Goal,
        overall_dissonance: Optional[float] = None,
        rule_system_state: Optional[Dict[str, Any]] = None,
        working_memory_size: Optional[int] = None
    ) -> Optional[float]:
        """
        Compute goal progress from actual system state.
        
        Args:
            goal: Goal to compute progress for
            overall_dissonance: Optional overall cognitive dissonance (0.0-1.0)
            rule_system_state: Optional rule system state dict
            working_memory_size: Optional working memory size
            
        Returns:
            Computed progress (0.0-1.0) or None if cannot be computed
        """
        # For minimize_cognitive_dissonance: compute from dissonance
        if goal.name == "minimize_cognitive_dissonance":
            if overall_dissonance is not None:
                # Progress is inverse of dissonance (low dissonance = high progress)
                return max(0.0, min(1.0, 1.0 - overall_dissonance))
            elif self._cognitive_dissonance_monitor:
                try:
                    dissonance_data = self._cognitive_dissonance_monitor.get_aggregated_dissonance()
                    # Check if we have sufficient data
                    has_data = dissonance_data.get("has_data", True)  # Default to True for backward compatibility
                    if not has_data:
                        # Insufficient data - return None to indicate cannot compute
                        logger.debug("Cannot compute progress for minimize_cognitive_dissonance: insufficient dissonance data")
                        return None
                    overall_dissonance = dissonance_data.get("overall_dissonance", 0.0)
                    return max(0.0, min(1.0, 1.0 - overall_dissonance))
                except Exception as e:
                    logger.debug(f"Error computing dissonance progress: {e}")
                    return None
            else:
                return None
        
        # For implement_cognitive_reasoning: compute from rule system and working memory
        elif goal.name == "implement_cognitive_reasoning":
            progress_components = []
            
            # Component 1: Rule system (30% weight)
            if rule_system_state is not None:
                rules = rule_system_state.get("rules", [])
                total_rules = len(rules)
                # Consider reasoning implemented if we have at least 5 rules
                rule_progress = min(1.0, total_rules / 5.0) if total_rules > 0 else 0.0
                progress_components.append(("rules", rule_progress, 0.3))
            elif self._rule_system:
                try:
                    rules = getattr(self._rule_system, 'rules', [])
                    total_rules = len(rules)
                    rule_progress = min(1.0, total_rules / 5.0) if total_rules > 0 else 0.0
                    progress_components.append(("rules", rule_progress, 0.3))
                except Exception as e:
                    logger.debug(f"Error getting rule system state: {e}")
            
            # Component 2: Working memory (20% weight)
            if working_memory_size is not None:
                # Consider working memory active if size > 0
                wm_progress = 1.0 if working_memory_size > 0 else 0.0
                progress_components.append(("working_memory", wm_progress, 0.2))
            elif self._working_memory:
                try:
                    wm_size = len(getattr(self._working_memory, 'items', []))
                    wm_progress = 1.0 if wm_size > 0 else 0.0
                    progress_components.append(("working_memory", wm_progress, 0.2))
                except Exception as e:
                    logger.debug(f"Error getting working memory state: {e}")
            
            # Component 3: Goal manager itself (50% weight) - base progress
            # If we have goals and they're being managed, that's progress
            base_progress = 0.5 if len(self.goals) > 0 else 0.0
            progress_components.append(("base", base_progress, 0.5))
            
            # Compute weighted average
            if progress_components:
                total_weight = sum(w for _, _, w in progress_components)
                if total_weight > 0:
                    weighted_sum = sum(p * w for _, p, w in progress_components)
                    return max(0.0, min(1.0, weighted_sum / total_weight))
            
            return None
        
        # For be_helpful_cognitive_assistant: compute from child goals
        elif goal.name == "be_helpful_cognitive_assistant":
            if goal.children:
                # Average progress of child goals
                child_progresses = []
                for child_name in goal.children:
                    if child_name in self.goals:
                        child_goal = self.goals[child_name]
                        if child_goal.progress is not None:
                            child_progresses.append(child_goal.progress)
                
                if child_progresses:
                    return sum(child_progresses) / len(child_progresses)
            
            return None
        
        # For other goals: cannot compute automatically
        return None
    
    def refresh_goal_progress(
        self,
        overall_dissonance: Optional[float] = None,
        rule_system_state: Optional[Dict[str, Any]] = None,
        working_memory_size: Optional[int] = None
    ) -> None:
        """
        Refresh progress for all goals that can be computed from current state.
        
        Args:
            overall_dissonance: Optional overall cognitive dissonance
            rule_system_state: Optional rule system state dict
            working_memory_size: Optional working memory size
        """
        with self._state_lock:
            for goal in self.goals.values():
                if goal.status == GoalStatus.ACTIVE:
                    computed_progress = self._compute_goal_progress(
                        goal,
                        overall_dissonance=overall_dissonance,
                        rule_system_state=rule_system_state,
                        working_memory_size=working_memory_size
                    )
                    if computed_progress is not None:
                        # Only update if progress was actually computed
                        if goal.progress != computed_progress:
                            old_progress = goal.progress
                            goal.update_progress(computed_progress, "Computed from system state")
                            logger.info(
                                f"Goal progress refreshed: name={goal.name}, "
                                f"progress={old_progress} -> {computed_progress:.3f}",
                                extra={
                                    "event": "goal_progress_refreshed",
                                    "goal_name": goal.name,
                                    "old_progress": old_progress,
                                    "new_progress": computed_progress,
                                }
                            )
        
        # Log summary of active goals
        active_goals = self.get_active_goals()
        if active_goals:
            avg_progress = sum(g.progress or 0.0 for g in active_goals) / len(active_goals)
            logger.info(
                f"Goal progress refresh complete: active_goals={len(active_goals)}, "
                f"avg_progress={avg_progress:.3f}, total_goals={len(self.goals)}",
                extra={
                    "event": "goal_progress_refresh_complete",
                    "active_goals_count": len(active_goals),
                    "avg_progress": avg_progress,
                    "total_goals": len(self.goals),
                }
            )
    
    def complete_goal(self, goal_name: str):
        """
        Mark a goal as completed.
        
        Stores completion to declarative memory.
        """
        if goal_name not in self.goals:
            logger.warning(f"Cannot complete non-existent goal: {goal_name}")
            return
        
        goal = self.goals[goal_name]
        old_status = goal.status
        old_progress = goal.progress
        
        self.update_goal_progress(goal_name, 1.0, "Goal completed")
        
        # Record completion in history
        self.goal_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "complete",
            "goal": goal_name,
            "old_status": old_status.value if old_status else None,
            "old_progress": old_progress,
        })
        
        # Store completion to declarative memory
        stored_to_memory = False
        if self.declarative_memory:
            try:
                self.declarative_memory.store_reasoning_result(
                    content=f"Goal '{goal_name}' completed: {goal.description}",
                    source="goal_completion",
                    tags=[goal_name, "goal", "completed"],
                    namespace=f"{self.declarative_memory.reasoning_namespace}/goals/{goal_name}",
                    importance=0.9
                )
                stored_to_memory = True
            except Exception as e:
                logger.error(f"Error storing goal completion to declarative memory: {e}", exc_info=True)
        
        logger.info(
            f"Goal completed: name={goal_name}, status_change={old_status.value if old_status else None} -> {goal.status.value}, "
            f"final_progress={goal.progress:.3f}, stored_to_memory={stored_to_memory}, "
            f"remaining_active_goals={len(self.get_active_goals())}",
            extra={
                "event": "goal_completed_manually",
                "goal_name": goal_name,
                "old_status": old_status.value if old_status else None,
                "new_status": goal.status.value,
                "final_progress": goal.progress,
                "stored_to_memory": stored_to_memory,
                "remaining_active_goals": len(self.get_active_goals()),
            }
        )
    
    def get_goal_tree(self, root_goal_name: str) -> Dict[str, Any]:
        """Get hierarchical tree structure for a goal."""
        if root_goal_name not in self.goals:
            return {}
        
        goal = self.goals[root_goal_name]
        tree = goal.to_dict()
        tree["children"] = []
        
        for child_name in goal.children:
            child_tree = self.get_goal_tree(child_name)
            if child_tree:
                tree["children"].append(child_tree)
        
        return tree
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager to dictionary representation."""
        return {
            "goals": {name: goal.to_dict() for name, goal in self.goals.items()},
            "goal_history": self.goal_history[-50:],  # Last 50 entries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GoalManager:
        """Create manager from dictionary representation."""
        manager = cls()
        manager.goals = {name: Goal.from_dict(goal_data) 
                        for name, goal_data in data.get("goals", {}).items()}
        manager.goal_history = data.get("goal_history", [])
        return manager
