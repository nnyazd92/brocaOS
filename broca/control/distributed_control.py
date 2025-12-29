"""
Distributed control for multi-component coordination.

Implements distributed control for coordinating multiple system components.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..reasoning.goal_manager import GoalManager

logger = logging.getLogger(__name__)


class ComponentRole(Enum):
    """Roles of system components."""
    COORDINATOR = "coordinator"
    WORKER = "worker"
    MONITOR = "monitor"


@dataclass
class Component:
    """A system component in distributed control."""
    component_id: str
    name: str
    role: ComponentRole
    state: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CoordinationMessage:
    """Message for component coordination."""
    from_component: str
    to_component: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DistributedControlSystem:
    """
    Distributed control system for multi-component coordination.
    
    Coordinates multiple system components to achieve goals.
    """
    
    def __init__(
        self,
        goal_manager: Optional["GoalManager"] = None
    ):
        """
        Initialize distributed control system.
        
        Args:
            goal_manager: Optional GoalManager for goal-based coordination
        """
        self.goal_manager = goal_manager
        
        # Components
        self.components: Dict[str, Component] = {}
        
        # Message queue
        self.message_queue: List[CoordinationMessage] = []
        
        # Coordination history
        self.coordination_history: List[Dict[str, Any]] = []
        
        logger.info("Initialized DistributedControlSystem")
    
    def register_component(
        self,
        component_id: str,
        name: str,
        role: ComponentRole,
        capabilities: Optional[List[str]] = None
    ):
        """Register a component."""
        component = Component(
            component_id=component_id,
            name=name,
            role=role,
            capabilities=capabilities or []
        )
        
        self.components[component_id] = component
        
        logger.info(f"Registered component: {name} ({role.value})")
    
    def update_component_state(
        self,
        component_id: str,
        state: Dict[str, Any]
    ):
        """Update component state."""
        if component_id not in self.components:
            logger.warning(f"Component {component_id} not found")
            return
        
        self.components[component_id].state.update(state)
        self.components[component_id].last_update = datetime.now(timezone.utc)
    
    def send_message(
        self,
        from_component: str,
        to_component: str,
        message_type: str,
        content: Dict[str, Any]
    ):
        """Send coordination message."""
        message = CoordinationMessage(
            from_component=from_component,
            to_component=to_component,
            message_type=message_type,
            content=content
        )
        
        self.message_queue.append(message)
        
        logger.debug(f"Sent message: {from_component} -> {to_component} ({message_type})")
    
    def coordinate_components(
        self,
        goal_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coordinate components to achieve goal.
        
        Args:
            goal_name: Optional goal name to coordinate for
            
        Returns:
            Coordination result
        """
        # Get active goal if not specified
        if goal_name and self.goal_manager:
            goal = self.goal_manager.get_goal(goal_name)
        elif self.goal_manager:
            goal = self.goal_manager.get_next_goal()
        else:
            goal = None
        
        if not goal:
            return {"status": "no_goal", "coordinated": False}
        
        # Find coordinator component
        coordinator = None
        for component in self.components.values():
            if component.role == ComponentRole.COORDINATOR:
                coordinator = component
                break
        
        if not coordinator:
            # No coordinator, use first component
            if self.components:
                coordinator = list(self.components.values())[0]
            else:
                return {"status": "no_components", "coordinated": False}
        
        # Coordinate: assign tasks to worker components
        workers = [c for c in self.components.values() if c.role == ComponentRole.WORKER]
        
        if not workers:
            return {"status": "no_workers", "coordinated": False}
        
        # Assign tasks based on capabilities
        assignments = []
        for worker in workers:
            # Check if worker has relevant capabilities
            if goal:
                # Simple capability matching
                task = {
                    "component": worker.component_id,
                    "task": f"work_on_goal_{goal.name}",
                    "priority": goal.priority
                }
                assignments.append(task)
                
                # Send assignment message
                self.send_message(
                    from_component=coordinator.component_id,
                    to_component=worker.component_id,
                    message_type="task_assignment",
                    content=task
                )
        
        # Record coordination
        coordination_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "goal": goal.name if goal else None,
            "coordinator": coordinator.component_id,
            "assignments": assignments
        }
        self.coordination_history.append(coordination_record)
        
        logger.info(
            f"Coordinated {len(assignments)} components for goal: "
            f"{goal.name if goal else 'unknown'}"
        )
        
        return {
            "status": "coordinated",
            "coordinated": True,
            "goal": goal.name if goal else None,
            "assignments": len(assignments)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about distributed control."""
        component_counts = {}
        for role in ComponentRole:
            component_counts[role.value] = sum(
                1 for c in self.components.values() if c.role == role
            )
        
        return {
            "total_components": len(self.components),
            "components_by_role": component_counts,
            "messages_queued": len(self.message_queue),
            "coordination_events": len(self.coordination_history)
        }

