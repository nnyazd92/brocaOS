"""
Integration tool for reasoning system.

Provides a tool interface for the LLM to interact with the
production rule system, working memory, and goal management.
"""

from __future__ import annotations

import logging
import json
import time
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .declarative_memory import DeclarativeMemoryInterface
    from .spreading_activation import SpreadingActivation
from datetime import datetime, timezone

from .production_rules import ProductionRule, ProductionRuleSystem, RuleType
from .working_memory import WorkingMemory
from .goal_manager import GoalManager, Goal, GoalStatus, GoalType
from .rule_engine import RuleEngine

# Lazy imports to avoid circular import (declarative_memory imports MemoryManager which imports config)
# These are imported inside __init__ when actually needed

logger = logging.getLogger(__name__)


class ReasoningTool:
    """
    Tool for LLM to interact with reasoning system.
    
    Provides operations to:
    - Add/remove/query production rules
    - Add/retrieve from working memory
    - Manage goals
    - Execute reasoning cycles
    """
    
    def __init__(
        self,
        rule_system: Optional[ProductionRuleSystem] = None,
        goal_manager: Optional[GoalManager] = None,
        declarative_memory: Optional[Any] = None,
        spreading_activation: Optional[Any] = None,
        rule_engine: Optional[RuleEngine] = None,
        daemon: Optional[Any] = None,
        enable_llm_pattern_matching: Optional[bool] = None,
    ):
        """
        Initialize reasoning tool.
        
        Args:
            rule_system: Production rule system (creates default if None)
            goal_manager: Goal manager (creates default if None)
            declarative_memory: Optional DeclarativeMemoryInterface for memory integration
            spreading_activation: Optional SpreadingActivation for activation propagation
            rule_engine: Optional RuleEngine (creates default if None)
            daemon: Optional ReasoningDaemon for autonomous operation
        """
        # Lazy import to avoid circular import
        from .declarative_memory import DeclarativeMemoryInterface
        from .spreading_activation import SpreadingActivation
        
        # Create working memory with declarative memory integration if available
        working_memory = None
        if declarative_memory and spreading_activation:
            working_memory = WorkingMemory(
                declarative_memory=declarative_memory,
                spreading_activation=spreading_activation
            )
        
        # Create rule system with integrated working memory
        self.rule_system = rule_system or ProductionRuleSystem(working_memory=working_memory)
        self.goal_manager = goal_manager or GoalManager(declarative_memory=declarative_memory)
        self.declarative_memory = declarative_memory
        self.spreading_activation = spreading_activation
        self.last_cycle_time = datetime.now(timezone.utc)
        
        # Daemon reference for autonomous operation
        self.daemon = daemon
        
        # Ensure working memory is wired (in case rule_system was provided externally)
        if self.declarative_memory and self.spreading_activation:
            if hasattr(self.rule_system, 'working_memory') and self.rule_system.working_memory:
                self.rule_system.working_memory.declarative_memory = self.declarative_memory
                self.rule_system.working_memory.spreading_activation = self.spreading_activation
        
        # Create rule engine with declarative memory integration
        self.rule_engine = rule_engine or RuleEngine(
            rule_system=self.rule_system,
            declarative_memory=declarative_memory,
            enable_llm_pattern_matching=enable_llm_pattern_matching,
        )
        
        # Load system efficiency rules (Recursive Funding Phase)
        try:
            from .efficiency_rules import EFFICIENCY_RULES
            for rule in EFFICIENCY_RULES:
                if not any(r.name == rule.name for r in self.rule_system.rules):
                    self.rule_system.rules.append(rule)
            logger.info(f"Loaded {len(EFFICIENCY_RULES)} efficiency rules")
        except ImportError:
            logger.debug("No efficiency rules found to load")
        except Exception as e:
            logger.warning(f"Failed to load efficiency rules: {e}")
        
        logger.info("Initialized ReasoningTool")

    def name(self) -> str:
        """Tool identifier."""
        return "reasoning"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Interact with the cognitive reasoning system. "
            "Use this tool to add production rules (if-then rules), "
            "manage working memory, set goals, and execute reasoning cycles. "
            "The reasoning system can perform symbolic inference, goal decomposition, "
            "and automated planning based on production rules."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": [
                        "add_rule",
                        "remove_rule",
                        "list_rules",
                        "add_to_memory",
                        "retrieve_from_memory",
                        "set_goal",
                        "get_goals",
                        "update_goal_progress",
                        "execute_cycle",
                        "get_state",
                        "clear_memory",
                        "start_daemon",
                        "stop_daemon",
                        "pause_daemon",
                        "resume_daemon",
                        "get_daemon_status"
                    ]
                },
                "rule": {
                    "type": "object",
                    "description": "Production rule to add (for add_rule action)"
                },
                "rule_name": {
                    "type": "string",
                    "description": "Name of rule to remove (for remove_rule action)"
                },
                "memory_content": {
                    "type": "object",
                    "description": "Content to add to working memory (for add_to_memory action)"
                },
                "memory_pattern": {
                    "type": "object",
                    "description": "Pattern to match for retrieval (for retrieve_from_memory action)"
                },
                "goal": {
                    "type": "object",
                    "description": "Goal to set (for set_goal action)"
                },
                "goal_name": {
                    "type": "string",
                    "description": "Name of goal (for get_goals, update_goal_progress actions)"
                },
                "progress": {
                    "type": "number",
                    "description": "Progress value (0.0 to 1.0) for update_goal_progress"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for progress update"
                },
                "max_rules": {
                    "type": "integer",
                    "description": "Maximum rules to fire in execute_cycle",
                    "default": 5
                }
            },
            "required": ["action"]
        }
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute reasoning tool action.
        
        Args:
            action: Action to perform
            **kwargs: Action-specific parameters
            
        Returns:
            Dictionary with results
        """
        import os
        t0 = time.perf_counter()
        log_timings = os.getenv("BROCA_LOG_REASONING_TIMINGS", "false").lower() == "true"
        try:
            if action == "add_rule":
                return self._add_rule(**kwargs)
            elif action == "remove_rule":
                return self._remove_rule(**kwargs)
            elif action == "list_rules":
                return self._list_rules(**kwargs)
            elif action == "add_to_memory":
                return self._add_to_memory(**kwargs)
            elif action == "retrieve_from_memory":
                return self._retrieve_from_memory(**kwargs)
            elif action == "set_goal":
                return self._set_goal(**kwargs)
            elif action == "get_goals":
                return self._get_goals(**kwargs)
            elif action == "update_goal_progress":
                return self._update_goal_progress(**kwargs)
            elif action == "execute_cycle":
                return self._execute_cycle(**kwargs)
            elif action == "get_state":
                return self._get_state(**kwargs)
            elif action == "get_state_summary":
                return self._get_state_summary(**kwargs)
            elif action == "clear_memory":
                return self._clear_memory(**kwargs)
            elif action == "start_daemon":
                return self._start_daemon(**kwargs)
            elif action == "stop_daemon":
                return self._stop_daemon(**kwargs)
            elif action == "pause_daemon":
                return self._pause_daemon(**kwargs)
            elif action == "resume_daemon":
                return self._resume_daemon(**kwargs)
            elif action == "get_daemon_status":
                return self._get_daemon_status(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            logger.error(f"Error executing reasoning action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if log_timings:
                dt_ms = (time.perf_counter() - t0) * 1000.0
                logger.info(
                    "REASONING_ACTION_TIMING",
                    extra={
                        "event": "reasoning_action_timing",
                        "action": action,
                        "duration_ms": round(dt_ms, 2),
                    },
                )
    
    def _add_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Add a production rule."""
        try:
            # Validate rule structure
            if "name" not in rule:
                return {"success": False, "error": "Rule must have a name"}
            if "conditions" not in rule:
                return {"success": False, "error": "Rule must have conditions"}
            if "actions" not in rule:
                return {"success": False, "error": "Rule must have actions"}
            
            # Acquire state lock
            with self.rule_system._state_lock:
                # Convert to ProductionRule object
                production_rule = ProductionRule(
                    name=rule["name"],
                    conditions=rule["conditions"],
                    actions=rule["actions"],
                    rule_type=RuleType(rule.get("rule_type", "inference")),
                    priority=rule.get("priority", 1.0),
                    strength=rule.get("strength", 1.0),
                )
                
                self.rule_system.add_rule(production_rule)
            
            # Notify daemon of state change
            self._notify_state_change("STATE_CHANGED", {"type": "rule_added", "rule_name": rule["name"]})
            
            return {
                "success": True,
                "message": f"Added rule: {rule['name']}",
                "rule": production_rule.to_dict()
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to add rule: {str(e)}"}
    
    def _remove_rule(self, rule_name: str) -> Dict[str, Any]:
        """Remove a production rule."""
        with self.rule_system._state_lock:
            self.rule_system.remove_rule(rule_name)
        
        # Notify daemon of state change
        self._notify_state_change("STATE_CHANGED", {"type": "rule_removed", "rule_name": rule_name})
        
        return {
            "success": True,
            "message": f"Removed rule: {rule_name}"
        }
    
    def _list_rules(self) -> Dict[str, Any]:
        """List all production rules."""
        rules = [rule.to_dict() for rule in self.rule_system.rules]
        return {
            "success": True,
            "rules": rules,
            "count": len(rules)
        }
    
    def _add_to_memory(self, memory_content: Dict[str, Any]) -> Dict[str, Any]:
        """Add content to working memory."""
        added = self.rule_system.working_memory.add(memory_content)
        if added:
            return {
                "success": True,
                "message": "Added to working memory",
                "content": memory_content
            }
        else:
            return {
                "success": False,
                "error": "Failed to add to working memory (capacity reached)"
            }
    
    def _retrieve_from_memory(self, memory_pattern: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieve from working memory."""
        items = self.rule_system.working_memory.retrieve(memory_pattern)
        return {
            "success": True,
            "items": items,
            "count": len(items)
        }
    
    def _set_goal(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Set a goal."""
        try:
            # Validate goal structure
            if "name" not in goal:
                return {"success": False, "error": "Goal must have a name"}
            if "description" not in goal:
                return {"success": False, "error": "Goal must have a description"}
            
            # Acquire state lock
            with self.goal_manager._state_lock:
                # Convert to Goal object
                goal_obj = Goal(
                    name=goal["name"],
                    description=goal["description"],
                    goal_type=GoalType(goal.get("goal_type", "achieve")),
                    status=GoalStatus(goal.get("status", "active")),
                    priority=goal.get("priority", 0.5),
                    parent=goal.get("parent"),
                    dependencies=goal.get("dependencies", []),
                    success_conditions=goal.get("success_conditions", []),
                    failure_conditions=goal.get("failure_conditions", []),
                    progress=goal.get("progress", 0.0),
                    max_attempts=goal.get("max_attempts", 3),
                )
                
                if self.goal_manager.add_goal(goal_obj):
                    # Notify daemon of state change
                    self._notify_state_change("GOAL_READY", {"goal_name": goal["name"]})
                    
                    return {
                        "success": True,
                        "message": f"Set goal: {goal['name']}",
                        "goal_name": goal["name"],
                        "goal": goal_obj.to_dict()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Goal '{goal['name']}' already exists"
                    }
        except Exception as e:
            return {"success": False, "error": f"Failed to set goal: {str(e)}"}
    
    def _get_goals(self, goal_name: Optional[str] = None) -> Dict[str, Any]:
        """Get goals."""
        if goal_name:
            goal = self.goal_manager.get_goal(goal_name)
            if goal:
                return {
                    "success": True,
                    "goals": [goal.to_dict()],
                    "count": 1
                }
            else:
                return {
                    "success": False,
                    "error": f"Goal '{goal_name}' not found"
                }
        else:
            goals = [goal.to_dict() for goal in self.goal_manager.get_active_goals()]
            return {
                "success": True,
                "goals": goals,
                "count": len(goals)
            }
    
    def _update_goal_progress(self, goal_name: str, progress: float, reason: str = "") -> Dict[str, Any]:
        """Update goal progress."""
        self.goal_manager.update_goal_progress(goal_name, progress, reason)
        return {
            "success": True,
            "message": f"Updated goal '{goal_name}' progress to {progress:.2f}",
            "goal_name": goal_name,
            "progress": progress,
            "reason": reason
        }
    
    def _execute_cycle(self, max_rules: int = 5) -> Dict[str, Any]:
        """Execute a reasoning cycle."""
        # Use rule engine if available (has declarative memory integration)
        if self.rule_engine:
            results = self.rule_engine.execute_cycle(
                working_memory=self.rule_system.working_memory,
                max_rules=max_rules
            )
        else:
            # Fallback to rule system direct execution
            results = self.rule_system.execute_cycle(max_rules)
        
        # Check for queued tool calls
        queued_tools = self.rule_system.working_memory.get_queued_tools()
        
        return {
            "success": True,
            "message": f"Executed reasoning cycle, fired {len(results)} rule(s)",
            "results": results,
            "queued_tools": queued_tools,
            "cycle_time": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_state(self) -> Dict[str, Any]:
        """Get current reasoning system state."""
        return {
            "success": True,
            "state": {
                "rule_system": self.rule_system.to_dict(),
                "goal_manager": self.goal_manager.to_dict(),
                "working_memory_size": len(self.rule_system.working_memory.items),
                "active_goals_count": len(self.goal_manager.get_active_goals()),
                "ready_goals_count": len(self.goal_manager.get_ready_goals()),
                "last_cycle_time": self.last_cycle_time.isoformat()
            }
        }

    def _get_state_summary(
        self,
        max_active_goals: int = 5,
        max_goal_desc_chars: int = 100,
        lock_timeout_s: float = 0.02,
    ) -> Dict[str, Any]:
        """
        Get a lightweight reasoning state summary.

        This avoids deep serialization (`to_dict()` of rule system / working memory),
        which can be a major latency source when building world state prompts.
        """
        max_active_goals = max(0, min(20, int(max_active_goals)))
        max_goal_desc_chars = max(0, min(500, int(max_goal_desc_chars)))
        try:
            lock_timeout_s = float(lock_timeout_s)
        except Exception:
            lock_timeout_s = 0.02
        lock_timeout_s = max(0.0, min(0.5, lock_timeout_s))

        # Best-effort non-blocking lock acquisition to avoid UI hangs.
        # If a lock cannot be acquired quickly, return partial state rather than blocking.
        busy = False
        active_goals: list[dict[str, Any]] = []
        active_goals_count = 0
        ready_goals_count = 0
        total_rules = 0
        working_memory_size = 0

        # Goals
        acquired = False
        try:
            acquired = bool(self.goal_manager._state_lock.acquire(timeout=lock_timeout_s))
            if acquired:
                goals = list(self.goal_manager.get_active_goals() or [])
                goals.sort(key=lambda g: (getattr(g, "priority", 0.0), getattr(g, "created_at", 0)), reverse=True)
                active_goals_count = len(goals)
                for goal in goals[:max_active_goals]:
                    gd = {
                        "name": getattr(goal, "name", "") or "",
                        "description": (getattr(goal, "description", "") or "")[:max_goal_desc_chars],
                        "priority": float(getattr(goal, "priority", 0.0) or 0.0),
                    }
                    progress = getattr(goal, "progress", None)
                    if progress is not None:
                        try:
                            gd["progress"] = float(progress)
                        except Exception:
                            pass
                    active_goals.append(gd)
                try:
                    ready_goals_count = len(self.goal_manager.get_ready_goals() or [])
                except Exception:
                    ready_goals_count = 0
            else:
                busy = True
        except Exception:
            busy = True
        finally:
            try:
                if acquired:
                    self.goal_manager._state_lock.release()
            except Exception:
                pass

        # Rules + working memory size
        acquired = False
        try:
            acquired = bool(self.rule_system._state_lock.acquire(timeout=lock_timeout_s))
            if acquired:
                try:
                    total_rules = len(getattr(self.rule_system, "rules", []) or [])
                except Exception:
                    total_rules = 0

                # Working memory has its own lock; avoid nested lock stalls.
                wm = getattr(self.rule_system, "working_memory", None)
                if wm is not None:
                    wm_acquired = False
                    try:
                        wm_acquired = bool(getattr(wm, "_state_lock", None).acquire(timeout=lock_timeout_s))  # type: ignore[union-attr]
                        if wm_acquired:
                            working_memory_size = len(getattr(wm, "items", []) or [])
                        else:
                            busy = True
                    except Exception:
                        busy = True
                    finally:
                        try:
                            if wm_acquired:
                                getattr(wm, "_state_lock").release()  # type: ignore[union-attr]
                        except Exception:
                            pass
            else:
                busy = True
        except Exception:
            busy = True
        finally:
            try:
                if acquired:
                    self.rule_system._state_lock.release()
            except Exception:
                pass

        state: Dict[str, Any] = {
            "active_goals": active_goals,
            "active_goals_count": int(active_goals_count),
            "ready_goals_count": int(ready_goals_count),
            "total_rules": int(total_rules),
            "working_memory_size": int(working_memory_size),
            "last_cycle_time": self.last_cycle_time.isoformat(),
        }
        if busy:
            state["busy"] = True

        return {"success": True, "state": state}
    
    def _clear_memory(self) -> Dict[str, Any]:
        """Clear working memory."""
        with self.rule_system.working_memory._state_lock:
            # Create new working memory
            self.rule_system.working_memory = WorkingMemory()
        
        # Notify daemon of state change
        self._notify_state_change("STATE_CHANGED", {"type": "memory_cleared"})
        
        return {
            "success": True,
            "message": "Cleared working memory"
        }
    
    def _notify_state_change(self, event_type: str, event_data: Dict[str, Any]):
        """Notify daemon of state change for event acceleration."""
        if self.daemon:
            try:
                self.daemon.notify_event(event_type, event_data)
            except Exception as e:
                logger.warning(f"Failed to notify daemon of state change: {e}")
    
    def _start_daemon(self) -> Dict[str, Any]:
        """Start autonomous reasoning daemon."""
        if not self.daemon:
            return {
                "success": False,
                "error": "Daemon not available (not initialized)"
            }
        
        try:
            started = self.daemon.start()
            if started:
                return {
                    "success": True,
                    "message": "Reasoning daemon started"
                }
            else:
                return {
                    "success": False,
                    "error": "Daemon is already running"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start daemon: {str(e)}"
            }
    
    def _stop_daemon(self) -> Dict[str, Any]:
        """Stop autonomous reasoning daemon."""
        if not self.daemon:
            return {
                "success": False,
                "error": "Daemon not available (not initialized)"
            }
        
        try:
            stopped = self.daemon.stop()
            if stopped:
                return {
                    "success": True,
                    "message": "Reasoning daemon stopped"
                }
            else:
                return {
                    "success": False,
                    "error": "Daemon is not running"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop daemon: {str(e)}"
            }
    
    def _pause_daemon(self) -> Dict[str, Any]:
        """Pause autonomous reasoning daemon."""
        if not self.daemon:
            return {
                "success": False,
                "error": "Daemon not available (not initialized)"
            }
        
        try:
            paused = self.daemon.pause()
            if paused:
                return {
                    "success": True,
                    "message": "Reasoning daemon paused"
                }
            else:
                return {
                    "success": False,
                    "error": "Daemon is not running"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to pause daemon: {str(e)}"
            }
    
    def _resume_daemon(self) -> Dict[str, Any]:
        """Resume autonomous reasoning daemon."""
        if not self.daemon:
            return {
                "success": False,
                "error": "Daemon not available (not initialized)"
            }
        
        try:
            resumed = self.daemon.resume()
            if resumed:
                return {
                    "success": True,
                    "message": "Reasoning daemon resumed"
                }
            else:
                return {
                    "success": False,
                    "error": "Daemon is not paused"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to resume daemon: {str(e)}"
            }
    
    def _get_daemon_status(self) -> Dict[str, Any]:
        """Get daemon status."""
        if not self.daemon:
            return {
                "success": True,
                "status": "not_available",
                "message": "Daemon not initialized"
            }
        
        try:
            status = self.daemon.get_status()
            return {
                "success": True,
                "status": status
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get daemon status: {str(e)}"
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return f"Error: {error}"
        
        # Format based on action result structure
        message = result.get("message", "")
        
        # If there's a message, use it
        if message:
            return message
        
        # Format specific result types
        if "state" in result:
            return f"Reasoning system state retrieved successfully"
        elif "rules" in result:
            count = result.get("count", 0)
            return f"Found {count} production rule(s)"
        elif "goals" in result:
            count = result.get("count", 0)
            return f"Found {count} goal(s)"
        elif "results" in result or "queued_tools" in result:
            # For execute_cycle results
            results = result.get("results", [])
            queued = result.get("queued_tools", [])
            result_parts = []
            if results:
                result_parts.append(f"{len(results)} rule(s) fired")
            if queued:
                result_parts.append(f"{len(queued)} tool(s) queued")
            if result_parts:
                return f"Reasoning cycle executed: {', '.join(result_parts)}"
            else:
                return "Reasoning cycle executed"
        elif "status" in result:
            # For daemon status
            status = result.get("status", {})
            status_str = status.get("status", "unknown") if isinstance(status, dict) else str(status)
            return f"Reasoning daemon status: {status_str}"
        else:
            # Generic success message
            return "Reasoning operation completed successfully"
