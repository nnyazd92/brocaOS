"""
Production rules for symbolic reasoning.

Implements production rules (if-then rules) that can match patterns in
working memory and execute actions (add/remove/modify memory, trigger
tool calls, or modify goals).
"""

from __future__ import annotations

import logging
import json
import hashlib
import threading
from typing import Dict, Any, List, Optional, Union, Callable, TYPE_CHECKING, Set
from enum import Enum
from datetime import datetime, timezone
from dataclasses import dataclass, field
from contextlib import contextmanager
from .working_memory import WorkingMemory, WorkingMemoryItem

if TYPE_CHECKING:
    from .llm_pattern_matcher import LLMPatternMatcher

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of production rules."""
    INFERENCE = "inference"  # Adds new facts based on existing ones
    ACTION = "action"       # Triggers actions or tool calls
    GOAL = "goal"          # Creates or modifies goals
    CONSTRAIN = "constraint" # Constrains possible actions
    META = "meta"          # Rules about rules


@dataclass
class ProductionRule:
    """
    A production rule (if-then rule) for cognitive reasoning.
    
    Conditions are patterns to match against working memory.
    Actions are executed when conditions are satisfied.
    """
    
    name: str
    conditions: List[Dict[str, Any]]  # List of condition patterns
    actions: List[Dict[str, Any]]     # List of actions to execute
    rule_type: RuleType = RuleType.INFERENCE
    priority: float = 1.0  # Higher priority rules fire first
    strength: float = 1.0  # Rule strength (for learning)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_fired: Optional[datetime] = None
    fire_count: int = 0
    pattern_matcher: Optional["LLMPatternMatcher"] = None  # Optional LLM pattern matcher
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary representation."""
        return {
            "name": self.name,
            "conditions": self.conditions,
            "actions": self.actions,
            "rule_type": self.rule_type.value,
            "priority": self.priority,
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
            "last_fired": self.last_fired.isoformat() if self.last_fired else None,
            "fire_count": self.fire_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProductionRule:
        """Create rule from dictionary representation."""
        return cls(
            name=data["name"],
            conditions=data["conditions"],
            actions=data["actions"],
            rule_type=RuleType(data.get("rule_type", "inference")),
            priority=data.get("priority", 1.0),
            strength=data.get("strength", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            last_fired=datetime.fromisoformat(data["last_fired"]) if data.get("last_fired") else None,
            fire_count=data.get("fire_count", 0),
        )
    
    def matches(self, working_memory: WorkingMemory) -> bool:
        """
        Check if rule conditions match working memory.
        
        This is a simple implementation - in practice, you'd want
        a pattern matcher that can handle variables, negation, etc.
        """
        # Simple matching: check if each condition exists in working memory
        for condition in self.conditions:
            # Look for pattern in working memory items
            found = False
            for wm_item in working_memory.items:
                if self._pattern_matches(condition, wm_item.content):
                    found = True
                    break
            if not found:
                return False
        return True
    
    def _pattern_matches(self, pattern: Union[Dict[str, Any], str], content: Union[Dict[str, Any], str]) -> bool:
        """Check if pattern matches memory content."""
        # Use LLM pattern matcher if available
        if self.pattern_matcher is not None:
            # Convert to dict format for LLM matcher
            pattern_dict = pattern if isinstance(pattern, dict) else {"text": pattern}
            content_dict = content if isinstance(content, dict) else {"text": content}
            return self.pattern_matcher.match(pattern_dict, content_dict)
        
        # Fallback to legacy dict subset/equality matching
        # Handle None values
        if pattern is None or content is None:
            return False
        
        # Handle string patterns
        if isinstance(pattern, str):
            if isinstance(content, str):
                # String-to-string comparison
                return pattern == content
            elif isinstance(content, dict):
                # String pattern against dict content: convert dict to string for comparison
                content_str = str(content)
                return pattern in content_str or pattern == content_str
            else:
                # String pattern against other types: convert both to string
                return str(pattern) == str(content)
        
        # Handle string content with dict pattern
        if isinstance(content, str):
            # Dict pattern can't match string content
            return False
        
        # Both should be dicts at this point, but check to be safe
        if not isinstance(pattern, dict) or not isinstance(content, dict):
            return False
        
        # Simple equality check for dict-to-dict matching
        for key, value in pattern.items():
            if key not in content:
                return False
            if isinstance(value, dict) and isinstance(content[key], dict):
                # Recursive check for nested dicts
                if not self._pattern_matches(value, content[key]):
                    return False
            elif value != content[key]:
                return False
        return True
    
    def execute(self, working_memory: WorkingMemory, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute rule actions.
        
        Returns list of results from executed actions.
        """
        context = context or {}
        results = []
        
        for action in self.actions:
            action_type = action.get("type", "add_to_memory")
            action_result = self._execute_action(action_type, action, working_memory, context)
            results.append(action_result)
        
        # Update rule statistics
        self.last_fired = datetime.now(timezone.utc)
        self.fire_count += 1
        
        logger.info(
            f"Rule fired: name={self.name}, type={self.rule_type.value}, "
            f"priority={self.priority:.3f}, strength={self.strength:.3f}, "
            f"fire_count={self.fire_count}, actions_executed={len(results)}",
            extra={
                "event": "production_rule_fired",
                "rule_name": self.name,
                "rule_type": self.rule_type.value,
                "priority": self.priority,
                "strength": self.strength,
                "fire_count": self.fire_count,
                "actions_executed": len(results),
                "last_fired": self.last_fired.isoformat(),
            }
        )
        return results
    
    def _execute_action(self, action_type: str, action: Dict[str, Any], 
                       working_memory: WorkingMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific action type."""
        if action_type == "add_to_memory":
            # Add new fact to working memory
            content = action.get("content", {})
            working_memory.add(content)
            return {"type": "add_to_memory", "content": content}
        
        elif action_type == "remove_from_memory":
            # Remove matching items from working memory
            pattern = action.get("pattern", {})
            removed = working_memory.remove_matching(pattern)
            return {"type": "remove_from_memory", "pattern": pattern, "removed_count": removed}
        
        elif action_type == "modify_memory":
            # Modify matching items in working memory
            pattern = action.get("pattern", {})
            modification = action.get("modification", {})
            modified = working_memory.modify_matching(pattern, modification)
            return {"type": "modify_memory", "pattern": pattern, "modification": modification, "modified_count": modified}
        
        elif action_type == "trigger_tool":
            # Trigger a tool call (queued for execution)
            tool_name = action.get("tool_name")
            parameters = action.get("parameters", {})
            # Get loop detector from context if available
            loop_detector = context.get("loop_detector") if context else None
            working_memory.queue_tool_call(tool_name, parameters, loop_detector=loop_detector)
            return {"type": "trigger_tool", "tool_name": tool_name, "parameters": parameters}
        
        elif action_type == "create_goal":
            # Create a new goal
            goal_data = action.get("goal", {})
            working_memory.add_goal(goal_data)
            return {"type": "create_goal", "goal": goal_data}
        
        elif action_type == "log_message":
            # Log a message
            message = action.get("message", "")
            logger.info(f"Rule '{self.name}': {message}")
            return {"type": "log_message", "message": message}
        
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return {"type": "unknown", "action": action}


class ProductionRuleSystem:
    """
    System for managing and executing production rules.
    
    Maintains a set of rules, selects rules to fire based on
    working memory, and executes rule actions.
    """
    
    def __init__(
        self, 
        working_memory: Optional[WorkingMemory] = None,
        pattern_matcher: Optional["LLMPatternMatcher"] = None
    ):
        self.rules: List[ProductionRule] = []
        self.working_memory = working_memory or WorkingMemory()
        self.rule_history: List[Dict[str, Any]] = []
        self.learning_enabled: bool = True
        self.pattern_matcher = pattern_matcher
        
        # Thread safety for state synchronization
        self._state_lock = threading.RLock()

        # Cached compiled index over all rule condition patterns (rebuilt when rules change).
        self._compiled_conditions_key: Optional[str] = None
        self._compiled_conditions_set: Optional[Any] = None
        self._compiled_condition_patterns: List[Dict[str, Any]] = []
        self._compiled_condition_meta: List[tuple[int, int]] = []  # (rule_idx, condition_idx)
        self._compiled_condition_counts: List[int] = []
        
        # Default inference rules
        self._add_default_rules()
    
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
    
    def _add_default_rules(self):
        """Add default inference rules."""
        # Rule: If we have a goal to implement something, create subgoal to analyze codebase
        self.add_rule(ProductionRule(
            name="goal_to_analyze_codebase",
            conditions=[
                {"type": "goal", "goal_type": "implementation", "status": "active"}
            ],
            actions=[
                {
                    "type": "create_goal",
                    "goal": {
                        "name": "analyze_codebase",
                        "description": "Analyze codebase structure for implementation",
                        "priority": 0.8,
                        "dependencies": [],
                        "status": "active"
                    }
                }
            ],
            rule_type=RuleType.GOAL,
            priority=1.5
        ))
        
        # Rule: If analyzing codebase and haven't examined files, create file examination subgoal
        self.add_rule(ProductionRule(
            name="analyze_codebase_files",
            conditions=[
                {"type": "goal", "name": "analyze_codebase", "status": "active"},
                {"type": "memory", "content_type": "codebase_analysis", "status": "not_started"}
            ],
            actions=[
                {
                    "type": "create_goal", 
                    "goal": {
                        "name": "examine_files",
                        "description": "Examine key files in codebase",
                        "priority": 0.9,
                        "dependencies": ["analyze_codebase"],
                        "status": "active"
                    }
                }
            ],
            rule_type=RuleType.GOAL,
            priority=1.2
        ))
        
        # Rule: If we need to examine files, trigger file listing tool
        self.add_rule(ProductionRule(
            name="examine_files_trigger",
            conditions=[
                {"type": "goal", "name": "examine_files", "status": "active"},
                {"type": "state", "files_examined": False}
            ],
            actions=[
                {
                    "type": "trigger_tool",
                    "tool_name": "EXECUTE",
                    "parameters": {
                        "cmd": "find . -name '*.py' -type f | head -20",
                        "cwd": ".",
                        "timeout": 60,
                        "env_allowlist": [],
                    }
                }
            ],
            rule_type=RuleType.ACTION,
            priority=1.0
        ))
        
        # Rule: Inference - If multiple related memories, create synthesis
        self.add_rule(ProductionRule(
            name="synthesize_related_memories",
            conditions=[
                {"type": "memory", "tags": {"contains": "related"}},
                {"type": "state", "synthesis_created": False}
            ],
            actions=[
                {
                    "type": "add_to_memory",
                    "content": {
                        "type": "synthesis",
                        "description": "Synthesis of related memories",
                        "source": "inference_rule",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            ],
            rule_type=RuleType.INFERENCE,
            priority=0.8
        ))
    
    def add_rule(self, rule: ProductionRule):
        """Add a rule to the system."""
        with self._state_lock:
            # Set pattern matcher on rule if available
            if self.pattern_matcher is not None:
                rule.pattern_matcher = self.pattern_matcher
            self.rules.append(rule)
            # Invalidate compiled condition index (rules changed)
            self._compiled_conditions_key = None
            logger.info(
                f"Added production rule: name={rule.name}, type={rule.rule_type.value}, "
                f"priority={rule.priority:.3f}, strength={rule.strength:.3f}, "
                f"conditions={len(rule.conditions)}, actions={len(rule.actions)}, "
                f"total_rules={len(self.rules)}",
                extra={
                    "event": "production_rule_added",
                    "rule_name": rule.name,
                    "rule_type": rule.rule_type.value,
                    "priority": rule.priority,
                    "strength": rule.strength,
                    "conditions_count": len(rule.conditions),
                    "actions_count": len(rule.actions),
                    "total_rules": len(self.rules),
                }
            )
    
    def remove_rule(self, rule_name: str):
        """Remove a rule by name."""
        with self._state_lock:
            removed_count = len(self.rules)
            self.rules = [r for r in self.rules if r.name != rule_name]
            removed_count -= len(self.rules)
            
            if removed_count > 0:
                # Invalidate compiled condition index (rules changed)
                self._compiled_conditions_key = None
                logger.info(
                    f"Removed production rule: name={rule_name}, "
                    f"remaining_rules={len(self.rules)}",
                    extra={
                        "event": "production_rule_removed",
                        "rule_name": rule_name,
                        "remaining_rules": len(self.rules),
                    }
                )
    
    def _ensure_compiled_condition_index(self) -> None:
        """
        Build (or reuse) a compiled index over all rule condition patterns.

        This enables conservative prefiltering of condition candidates per working-memory item,
        avoiding an O(rules × conditions × wm_items) scan.
        """
        patterns: List[Dict[str, Any]] = []
        meta: List[tuple[int, int]] = []
        counts: List[int] = []

        for ridx, rule in enumerate(self.rules):
            ccount = 0
            for cidx, cond in enumerate(rule.conditions or []):
                if isinstance(cond, dict):
                    patterns.append(cond)
                else:
                    patterns.append({"text": str(cond)})
                meta.append((ridx, cidx))
                ccount += 1
            counts.append(ccount)

        try:
            payload = json.dumps(patterns, sort_keys=True, ensure_ascii=False, default=str)
            key = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
        except Exception:
            key = None

        if key and key == self._compiled_conditions_key and self._compiled_conditions_set is not None:
            return

        try:
            from broca.matching import CompiledPatternSet

            cps = CompiledPatternSet(patterns)
        except Exception as e:
            logger.warning(f"Failed to compile rule condition patterns: {e}", exc_info=True)
            cps = None

        self._compiled_conditions_key = key
        self._compiled_conditions_set = cps
        self._compiled_condition_patterns = patterns
        self._compiled_condition_meta = meta
        self._compiled_condition_counts = counts

    def match_rules(self, working_memory: Optional[WorkingMemory] = None) -> List[ProductionRule]:
        """
        Find rules whose conditions match working memory.

        Uses a conservative compiled prefilter (hard constraints + keyword/regex) to avoid
        repeated cartesian scans each cycle. When available, ranks candidates by text
        similarity (ANN/text ranking) to enable early-stop evaluation.
        """
        wm = working_memory or self.working_memory
        with self._state_lock:
            self._ensure_compiled_condition_index()
            cps = self._compiled_conditions_set
            patterns = self._compiled_condition_patterns
            meta = self._compiled_condition_meta
            counts = self._compiled_condition_counts

        if not self.rules or not patterns or not meta:
            return []

        # Track which conditions have been satisfied per rule.
        satisfied: List[Set[int]] = [set() for _ in self.rules]
        remaining_rules = set(i for i, c in enumerate(counts) if c > 0)

        # Optional ranking surface (LocalPatternMatcher exposes it; LLM matcher may not).
        ranker = getattr(self.pattern_matcher, "rank_text_candidates", None) if self.pattern_matcher is not None else None
        pattern_texts: Optional[List[str]] = getattr(cps, "pattern_texts", None) if cps is not None else None

        # Iterate over working-memory items once; mark any matched conditions.
        evaluated_conditions = 0
        matched_conditions = 0

        def _legacy_match(pattern: Any, content: Any) -> bool:
            if pattern is None or content is None:
                return False
            if isinstance(pattern, str):
                if isinstance(content, str):
                    return pattern == content
                if isinstance(content, dict):
                    s = str(content)
                    return pattern in s or pattern == s
                return str(pattern) == str(content)
            if isinstance(content, str):
                return False
            if not isinstance(pattern, dict) or not isinstance(content, dict):
                return False
            for k, v in pattern.items():
                if k not in content:
                    return False
                cv = content.get(k)
                if isinstance(v, dict) and isinstance(cv, dict):
                    if not _legacy_match(v, cv):
                        return False
                elif v != cv:
                    return False
            return True

        def _extract_query_text(content: Dict[str, Any]) -> str:
            # Keep this conservative + cheap: prefer explicit text fields, otherwise fall back to a small dump.
            for k, v in (content or {}).items():
                if isinstance(v, str) and k.lower() in {"text", "message", "query"} and v.strip():
                    return v
            try:
                return json.dumps(content, ensure_ascii=False, default=str)[:2000]
            except Exception:
                return str(content)[:2000]

        for wm_item in wm.items:
            content = wm_item.content
            if not isinstance(content, dict):
                continue

            # Stage (1): hard-key + conservative prefiltering to find candidate conditions for this content.
            try:
                candidate_idxs = cps.candidate_indices_for_content(content) if cps is not None else list(range(len(patterns)))
            except Exception:
                candidate_idxs = list(range(len(patterns)))

            if not candidate_idxs:
                continue

            # Stage (2): rank candidates by text similarity (ordering only; never drops candidates).
            ordered_idxs: List[int] = list(candidate_idxs)
            if ranker is not None and pattern_texts is not None and any(pattern_texts[i] for i in candidate_idxs):
                q = _extract_query_text(content)
                if q.strip():
                    try:
                        ranked = ranker(q, pattern_texts, top_k=min(max(25, len(candidate_idxs)), len(pattern_texts)))
                        ranked_set = set(ordered_idxs)
                        ordered_idxs = [i for i in getattr(ranked, "indices", []) if i in ranked_set] + [i for i in ordered_idxs if i not in set(getattr(ranked, "indices", []))]
                    except Exception:
                        ordered_idxs = list(candidate_idxs)

            # Stage (3): full structured/operator match, early-stopping when possible.
            for cond_idx in ordered_idxs:
                if cond_idx < 0 or cond_idx >= len(meta):
                    continue
                rule_idx, condition_idx = meta[cond_idx]
                if rule_idx not in remaining_rules:
                    continue
                if condition_idx in satisfied[rule_idx]:
                    continue

                evaluated_conditions += 1
                try:
                    if self.pattern_matcher is not None:
                        ok = self.pattern_matcher.match(patterns[cond_idx], content)
                    else:
                        ok = _legacy_match(patterns[cond_idx], content)
                except Exception:
                    ok = False

                if ok:
                    matched_conditions += 1
                    satisfied[rule_idx].add(condition_idx)
                    if len(satisfied[rule_idx]) >= counts[rule_idx]:
                        remaining_rules.discard(rule_idx)
                        if not remaining_rules:
                            break
            if not remaining_rules:
                break

        matched_rules: List[ProductionRule] = []
        for ridx, rule in enumerate(self.rules):
            if counts[ridx] > 0 and len(satisfied[ridx]) >= counts[ridx]:
                matched_rules.append(rule)

        matched_rules.sort(key=lambda r: (r.priority, r.strength), reverse=True)
        top_priority = matched_rules[0].priority if matched_rules else 0.0

        log_level = logging.INFO if matched_rules else logging.DEBUG
        logger.log(
            log_level,
            f"Rule matching complete: evaluated_rules={len(self.rules)}, matched={len(matched_rules)}, "
            f"evaluated_conditions={evaluated_conditions}, matched_conditions={matched_conditions}, "
            f"total_conditions={len(patterns)}, top_priority={top_priority:.3f}",
            extra={
                "event": "production_rules_matched",
                "evaluated_count": len(self.rules),
                "matched_count": len(matched_rules),
                "total_rules": len(self.rules),
                "matched_rule_names": [r.name for r in matched_rules],
                "top_priority": top_priority,
                "evaluated_conditions": evaluated_conditions,
                "matched_conditions": matched_conditions,
                "total_conditions": len(patterns),
            },
        )

        return matched_rules
    
    def execute_cycle(self, max_rules: int = 5) -> List[Dict[str, Any]]:
        """
        Execute one reasoning cycle.
        
        Returns list of action results from fired rules.
        """
        matched_rules = self.match_rules()
        if not matched_rules:
            logger.debug(
                "Rule cycle execution: no rules matched",
                extra={
                    "event": "rule_cycle_no_matches",
                    "total_rules": len(self.rules),
                }
            )
            return []
        
        # Limit number of rules to fire
        rules_to_fire = matched_rules[:max_rules]
        all_results = []
        fired_count = 0
        error_count = 0
        
        for rule in rules_to_fire:
            try:
                results = rule.execute(self.working_memory)
                all_results.extend(results)
                fired_count += 1
                
                # Record in history
                self.rule_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "rule": rule.name,
                    "results": results
                })
                
                # Limit history size
                if len(self.rule_history) > 100:
                    self.rule_history = self.rule_history[-100:]
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error executing rule '{rule.name}': {e}", exc_info=True)
                continue
        
        logger.info(
            f"Rule cycle execution complete: matched={len(matched_rules)}, "
            f"fired={fired_count}/{len(rules_to_fire)}, errors={error_count}, "
            f"results_generated={len(all_results)}",
            extra={
                "event": "production_rule_cycle_executed",
                "matched_count": len(matched_rules),
                "fired_count": fired_count,
                "attempted_count": len(rules_to_fire),
                "error_count": error_count,
                "results_count": len(all_results),
                "fired_rule_names": [r.name for r in rules_to_fire[:fired_count]],
            }
        )
        
        return all_results
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system to dictionary representation."""
        return {
            "rules": [rule.to_dict() for rule in self.rules],
            "working_memory": self.working_memory.to_dict(),
            "rule_history": self.rule_history[-20:],  # Last 20 entries
            "learning_enabled": self.learning_enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProductionRuleSystem:
        """Create system from dictionary representation."""
        system = cls()
        system.rules = [ProductionRule.from_dict(rule_data) for rule_data in data.get("rules", [])]
        system.working_memory = WorkingMemory.from_dict(data.get("working_memory", {}))
        system.rule_history = data.get("rule_history", [])
        system.learning_enabled = data.get("learning_enabled", True)
        return system
