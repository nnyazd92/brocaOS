"""
Hierarchical control architecture for cognitive reasoning.

Implements multi-level control hierarchy (strategic → tactical → operational)
similar to thalamocortical feedback systems in neuroscience.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .goal_manager import GoalManager, Goal
    from .working_memory import WorkingMemory

logger = logging.getLogger(__name__)


class ControlLevel(Enum):
    """Control hierarchy levels."""
    STRATEGIC = "strategic"      # Long-term goals, high-level planning
    TACTICAL = "tactical"        # Medium-term plans, resource allocation
    OPERATIONAL = "operational"  # Immediate actions, rule execution


@dataclass
class ControlDecision:
    """A decision made at a control level."""
    level: ControlLevel
    decision_type: str
    content: Dict[str, Any]
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    rationale: str = ""
    delegated_to: Optional[ControlLevel] = None


@dataclass
class ControlPolicy:
    """Policy for routing decisions to appropriate control levels."""
    name: str
    level: ControlLevel
    condition: Callable[[Dict[str, Any]], bool]
    priority: float = 0.5
    description: str = ""


class HierarchicalController:
    """
    Multi-level hierarchical control system.
    
    Routes decisions to appropriate control levels:
    - Strategic: Long-term goals, system-wide decisions
    - Tactical: Medium-term plans, resource allocation
    - Operational: Immediate actions, rule execution
    """
    
    def __init__(
        self,
        goal_manager: Optional["GoalManager"] = None,
        strategic_threshold: float = 0.8,
        tactical_threshold: float = 0.5
    ):
        """
        Initialize hierarchical controller.
        
        Args:
            goal_manager: Optional GoalManager for goal-based routing
            strategic_threshold: Confidence threshold for strategic decisions
            tactical_threshold: Confidence threshold for tactical decisions
        """
        self.goal_manager = goal_manager
        self.strategic_threshold = strategic_threshold
        self.tactical_threshold = tactical_threshold
        
        # Control policies for routing decisions
        self.policies: List[ControlPolicy] = []
        
        # Decision history
        self.decision_history: List[ControlDecision] = []
        
        # Initialize default policies
        self._initialize_default_policies()
        
        logger.info("Initialized HierarchicalController")
    
    def _initialize_default_policies(self):
        """Initialize default control policies."""
        # Strategic: High-level goal creation/modification
        self.policies.append(ControlPolicy(
            name="strategic_goal_management",
            level=ControlLevel.STRATEGIC,
            condition=lambda ctx: (
                ctx.get("action_type") in ["create_goal", "modify_goal", "abandon_goal"] and
                ctx.get("goal_priority", 0.0) >= self.strategic_threshold
            ),
            priority=1.0,
            description="Strategic goal management"
        ))
        
        # Tactical: Goal decomposition, resource allocation
        self.policies.append(ControlPolicy(
            name="tactical_planning",
            level=ControlLevel.TACTICAL,
            condition=lambda ctx: (
                ctx.get("action_type") in ["decompose_goal", "allocate_resources", "plan_sequence"] or
                (ctx.get("goal_priority", 0.0) >= self.tactical_threshold and
                 ctx.get("goal_priority", 0.0) < self.strategic_threshold)
            ),
            priority=0.8,
            description="Tactical planning and resource allocation"
        ))
        
        # Operational: Rule execution, immediate actions
        self.policies.append(ControlPolicy(
            name="operational_execution",
            level=ControlLevel.OPERATIONAL,
            condition=lambda ctx: (
                ctx.get("action_type") in ["execute_rule", "apply_skill", "tool_call"] or
                ctx.get("goal_priority", 0.0) < self.tactical_threshold
            ),
            priority=0.6,
            description="Operational execution"
        ))
    
    def add_policy(self, policy: ControlPolicy):
        """Add a control policy."""
        self.policies.append(policy)
        # Sort by priority (highest first)
        self.policies.sort(key=lambda p: p.priority, reverse=True)
        logger.info(f"Added control policy: {policy.name} (level: {policy.level.value})")
    
    def route_decision(
        self,
        context: Dict[str, Any],
        working_memory: Optional["WorkingMemory"] = None
    ) -> ControlDecision:
        """
        Route a decision to appropriate control level.
        
        Args:
            context: Decision context (action_type, goal_priority, etc.)
            working_memory: Optional working memory for additional context
            
        Returns:
            ControlDecision with routing information
        """
        # Enrich context with working memory state if available
        if working_memory:
            context["wm_capacity"] = len(working_memory.items) / working_memory.capacity
            context["wm_cognitive_load"] = working_memory.state.get("cognitive_load", 0.0)
            context["active_goals_count"] = len(working_memory.get_active_goals())
        
        # Enrich with goal manager state if available
        if self.goal_manager:
            try:
                active_goals = self.goal_manager.get_active_goals()
                context["active_goals_count"] = len(active_goals)
                if active_goals:
                    context["max_goal_priority"] = max(g.priority for g in active_goals)
                    context["avg_goal_priority"] = sum(g.priority for g in active_goals) / len(active_goals)
                else:
                    context["max_goal_priority"] = 0.0
                    context["avg_goal_priority"] = 0.0
            except Exception as e:
                logger.warning(f"Error reading active goals from goal_manager: {e}", exc_info=True)
                context["active_goals_count"] = 0
                context["max_goal_priority"] = 0.0
                context["avg_goal_priority"] = 0.0
        
        # Find matching policy
        matched_policy = None
        for policy in self.policies:
            try:
                if policy.condition(context):
                    matched_policy = policy
                    break
            except Exception as e:
                logger.warning(f"Error evaluating policy '{policy.name}': {e}")
                continue
        
        # Default to operational if no policy matches
        if not matched_policy:
            matched_policy = ControlPolicy(
                name="default_operational",
                level=ControlLevel.OPERATIONAL,
                condition=lambda _: True,
                priority=0.0,
                description="Default operational routing"
            )
        
        # Create decision
        decision = ControlDecision(
            level=matched_policy.level,
            decision_type=context.get("action_type", "unknown"),
            content=context,
            confidence=self._compute_confidence(context, matched_policy),
            rationale=f"Routed to {matched_policy.level.value} level via policy '{matched_policy.name}'"
        )
        
        # Check if decision should be delegated to lower level
        if matched_policy.level == ControlLevel.STRATEGIC:
            # Strategic decisions may delegate tactical components
            if context.get("requires_tactical_planning", False):
                decision.delegated_to = ControlLevel.TACTICAL
        elif matched_policy.level == ControlLevel.TACTICAL:
            # Tactical decisions may delegate operational components
            if context.get("requires_operational_execution", False):
                decision.delegated_to = ControlLevel.OPERATIONAL
        
        # Record in history
        self.decision_history.append(decision)
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
        
        logger.debug(
            f"Routed decision '{decision.decision_type}' to {decision.level.value} level "
            f"(confidence: {decision.confidence:.2f})"
        )
        
        return decision

    # Backward-compatible API (tests + older callers)
    def make_decision(self, goal_name: str, context: Dict[str, Any]) -> ControlDecision:
        """
        Backward-compatible wrapper around `route_decision`.

        The unit tests (and older code) call `make_decision(goal_name, context)`.
        We map that into the richer routing context expected by `route_decision`.
        """
        ctx = dict(context or {})
        ctx["goal_name"] = goal_name

        # Normalize priority inputs
        priority = ctx.get("goal_priority", ctx.get("priority", 0.0))
        try:
            priority_f = float(priority) if priority is not None else 0.0
        except Exception:
            priority_f = 0.0
        priority_f = max(0.0, min(1.0, priority_f))
        ctx["goal_priority"] = priority_f

        # If no explicit action_type is provided, infer one from priority so default policies apply.
        if not ctx.get("action_type"):
            if priority_f >= max(0.0, float(self.strategic_threshold)):
                ctx["action_type"] = "modify_goal"
            elif priority_f >= max(0.0, float(self.tactical_threshold)):
                ctx["action_type"] = "decompose_goal"
            else:
                ctx["action_type"] = "execute_rule"

        return self.route_decision(ctx)
    
    def _compute_confidence(
        self,
        context: Dict[str, Any],
        policy: ControlPolicy
    ) -> float:
        """Compute confidence in routing decision."""
        confidence = policy.priority
        
        # Adjust based on context quality
        if context.get("goal_priority") is not None:
            confidence = max(confidence, context.get("goal_priority", 0.0))
        
        # Adjust based on working memory state
        if context.get("wm_cognitive_load") is not None:
            # Lower cognitive load = higher confidence in routing
            wm_load = context.get("wm_cognitive_load", 0.5)
            confidence = confidence * (1.0 - wm_load * 0.3)
        
        return min(1.0, max(0.0, confidence))
    
    def get_control_statistics(self) -> Dict[str, Any]:
        """Get statistics about control decisions."""
        if not self.decision_history:
            return {"status": "no_data"}
        
        # Count decisions by level
        level_counts = {}
        for level in ControlLevel:
            level_counts[level.value] = sum(
                1 for d in self.decision_history if d.level == level
            )
        
        # Average confidence by level
        level_confidence = {}
        for level in ControlLevel:
            level_decisions = [d for d in self.decision_history if d.level == level]
            if level_decisions:
                level_confidence[level.value] = sum(
                    d.confidence for d in level_decisions
                ) / len(level_decisions)
            else:
                level_confidence[level.value] = 0.0
        
        # Delegation statistics
        delegation_count = sum(
            1 for d in self.decision_history if d.delegated_to is not None
        )
        
        return {
            "status": "ok",
            "total_decisions": len(self.decision_history),
            "decisions_by_level": level_counts,
            "avg_confidence_by_level": level_confidence,
            "delegation_count": delegation_count,
            "delegation_rate": delegation_count / len(self.decision_history) if self.decision_history else 0.0
        }
    
    def execute_at_level(
        self,
        decision: ControlDecision,
        working_memory: Optional["WorkingMemory"] = None
    ) -> Dict[str, Any]:
        """
        Execute decision at appropriate control level.
        
        Args:
            decision: ControlDecision to execute
            working_memory: Optional working memory
            
        Returns:
            Execution result
        """
        result = {
            "level": decision.level.value,
            "decision_type": decision.decision_type,
            "success": False,
            "output": None,
            "delegated": False
        }
        
        try:
            if decision.level == ControlLevel.STRATEGIC:
                result["output"] = self._execute_strategic(decision, working_memory)
            elif decision.level == ControlLevel.TACTICAL:
                result["output"] = self._execute_tactical(decision, working_memory)
            elif decision.level == ControlLevel.OPERATIONAL:
                result["output"] = self._execute_operational(decision, working_memory)
            
            result["success"] = True
            
            # Handle delegation
            if decision.delegated_to:
                result["delegated"] = True
                delegated_decision = ControlDecision(
                    level=decision.delegated_to,
                    decision_type=decision.decision_type,
                    content=decision.content,
                    confidence=decision.confidence * 0.9,  # Slight confidence reduction
                    rationale=f"Delegated from {decision.level.value} level"
                )
                delegated_result = self.execute_at_level(delegated_decision, working_memory)
                result["delegated_result"] = delegated_result
                
        except Exception as e:
            logger.error(f"Error executing decision at {decision.level.value} level: {e}", exc_info=True)
            result["error"] = str(e)
        
        return result
    
    def _execute_strategic(
        self,
        decision: ControlDecision,
        working_memory: Optional["WorkingMemory"]
    ) -> Dict[str, Any]:
        """Execute strategic-level decision."""
        action_type = decision.decision_type
        
        if action_type == "create_goal" and self.goal_manager:
            # Create high-level strategic goal
            goal_data = decision.content.get("goal_data", {})
            from .goal_manager import Goal, GoalType, GoalStatus
            goal = Goal(
                name=goal_data.get("name", "strategic_goal"),
                description=goal_data.get("description", ""),
                goal_type=GoalType(goal_data.get("goal_type", "achieve")),
                priority=goal_data.get("priority", 0.9),
                status=GoalStatus.ACTIVE
            )
            success = self.goal_manager.add_goal(goal)
            return {"goal_created": success, "goal_name": goal.name}
        
        elif action_type == "modify_goal" and self.goal_manager:
            goal_name = decision.content.get("goal_name")
            modifications = decision.content.get("modifications", {})
            goal = self.goal_manager.get_goal(goal_name)
            if goal:
                # Apply modifications
                for key, value in modifications.items():
                    if hasattr(goal, key):
                        setattr(goal, key, value)
                return {"goal_modified": True, "goal_name": goal_name}
            return {"goal_modified": False, "error": "Goal not found"}
        
        return {"action": "strategic_execution", "status": "completed"}
    
    def _execute_tactical(
        self,
        decision: ControlDecision,
        working_memory: Optional["WorkingMemory"]
    ) -> Dict[str, Any]:
        """Execute tactical-level decision."""
        action_type = decision.decision_type
        
        if action_type == "decompose_goal" and self.goal_manager:
            goal_name = decision.content.get("goal_name")
            decomposition = decision.content.get("decomposition", [])
            subgoals = self.goal_manager.decompose_goal(goal_name, decomposition)
            return {"subgoals_created": len(subgoals), "subgoals": subgoals}
        
        elif action_type == "allocate_resources":
            resources = decision.content.get("resources", {})
            # Resource allocation logic would go here
            return {"resources_allocated": resources}
        
        return {"action": "tactical_execution", "status": "completed"}
    
    def _execute_operational(
        self,
        decision: ControlDecision,
        working_memory: Optional["WorkingMemory"]
    ) -> Dict[str, Any]:
        """Execute operational-level decision."""
        action_type = decision.decision_type
        
        if action_type == "execute_rule":
            rule_name = decision.content.get("rule_name")
            rule_params = decision.content.get("rule_params", {})
            return {"rule_executed": rule_name, "params": rule_params}
        
        elif action_type == "apply_skill":
            skill_name = decision.content.get("skill_name")
            skill_params = decision.content.get("skill_params", {})
            return {"skill_applied": skill_name, "params": skill_params}
        
        elif action_type == "tool_call":
            tool_name = decision.content.get("tool_name")
            tool_params = decision.content.get("tool_params", {})
            return {"tool_called": tool_name, "params": tool_params}
        
        return {"action": "operational_execution", "status": "completed"}

