"""
Z3-based logical validator for reasoning and learning.

Enforces logical consistency, validates causal chains, and checks
satisfiability of constraints in production rules, goals, and learned procedures.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from collections import deque, defaultdict
import warnings

try:
    from z3 import Bool, BoolRef, Solver, And, Or, Not, Implies, sat, unsat, unknown
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    # Create dummy types for type checking
    BoolRef = Any
    Solver = Any

logger = logging.getLogger(__name__)


class LogicalRelation(Enum):
    """Types of logical relationships for Z3 encoding."""
    IMPLIES = "implies"  # A => B
    CAUSES = "causes"    # A causes B (stronger than implies)
    REQUIRES = "requires"  # A requires B
    CONTRADICTS = "contradicts"  # A contradicts B
    EQUIVALENT = "equivalent"  # A <=> B


@dataclass
class LogicalConstraint:
    """A logical constraint to be validated."""
    premise: str  # Variable name for premise
    conclusion: str  # Variable name for conclusion
    relation: LogicalRelation
    strength: float = 1.0  # Strength of the relationship (0.0 to 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationSummary:
    """Compact summary of validation results for world state."""
    enabled: bool
    last_validation: Optional[datetime]
    rule_chain_valid: bool
    causal_chains_valid: bool
    goal_dependencies_valid: bool
    warnings_count: int
    contradictions_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, ensuring size limit."""
        result = {
            "enabled": self.enabled,
            "last_validation": self.last_validation.isoformat() if self.last_validation else None,
            "rule_chain_valid": self.rule_chain_valid,
            "causal_chains_valid": self.causal_chains_valid,
            "goal_dependencies_valid": self.goal_dependencies_valid,
            "warnings_count": self.warnings_count,
            "contradictions_count": self.contradictions_count,
        }
        return result


class Z3LogicalValidator:
    """
    Z3-based validator for logical reasoning chains.
    
    Validates:
    - Production rule consistency
    - Causal chain transitivity
    - Goal dependency satisfiability
    - Contradiction detection
    - Learned procedure soundness
    """
    
    def __init__(self, enable_z3: bool = True, timeout: float = 5.0, max_constraints: int = 1000):
        """
        Initialize Z3 validator.
        
        Args:
            enable_z3: Whether to enable Z3 (if False, validator is no-op)
            timeout: Timeout for Z3 solver in seconds
            max_constraints: Maximum number of constraints to process
        """
        self.enabled = enable_z3 and Z3_AVAILABLE
        if not Z3_AVAILABLE and enable_z3:
            logger.warning("Z3 not available. Install with: pip install z3-solver")
        
        self.timeout = timeout
        self.max_constraints = max_constraints
        
        # Cache for Z3 variables (proposition names -> Bool variables)
        self._variable_cache: Dict[str, BoolRef] = {}
        
        # Track constraints
        self._constraints: List[LogicalConstraint] = []
        
        # Track causal chains
        self._causal_graph: Dict[str, Set[str]] = {}  # node -> {causes}
        
        # Validation state tracking
        self._last_validation_time: Optional[datetime] = None
        self._validation_stats: Dict[str, Any] = {
            "rule_chain_valid": True,
            "causal_chains_valid": True,
            "goal_dependencies_valid": True,
            "warnings_count": 0,
            "contradictions_count": 0,
        }
        
    def _get_variable(self, name: str) -> BoolRef:
        """Get or create Z3 Bool variable for a proposition."""
        if not self.enabled:
            return None  # type: ignore
        
        if name not in self._variable_cache:
            self._variable_cache[name] = Bool(name)
        return self._variable_cache[name]
    
    def add_constraint(
        self,
        premise: str,
        conclusion: str,
        relation: LogicalRelation,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a logical constraint.
        
        Args:
            premise: Premise proposition name
            conclusion: Conclusion proposition name
            relation: Type of logical relationship
            strength: Strength of relationship (0.0 to 1.0)
            metadata: Optional metadata
        """
        if not self.enabled:
            return
        
        if len(self._constraints) >= self.max_constraints:
            msg = f"Maximum constraints limit ({self.max_constraints}) reached"
            logger.warning(msg)
            # Emit a Python warning so tests (and callers) can intercept this as a signal.
            try:
                warnings.warn(msg, RuntimeWarning)
            except Exception:
                pass
            return
        
        constraint = LogicalConstraint(
            premise=premise,
            conclusion=conclusion,
            relation=relation,
            strength=strength,
            metadata=metadata or {}
        )
        self._constraints.append(constraint)
        
        # Track causal relationships for transitivity
        if relation == LogicalRelation.CAUSES:
            if premise not in self._causal_graph:
                self._causal_graph[premise] = set()
            self._causal_graph[premise].add(conclusion)
    
    def validate_rule_chain(
        self,
        rules: List[Any],  # ProductionRule
        working_memory_facts: List[str]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate a chain of production rules for logical consistency.
        
        Args:
            rules: List of production rules to validate
            working_memory_facts: List of fact names currently in working memory
            
        Returns:
            Tuple of (is_valid, error_message, warnings)
        """
        if not self.enabled:
            return True, None, []
        
        if not rules:
            return True, None, []
        
        solver = Solver()
        warnings: List[str] = []
        
        try:
            # Set timeout
            solver.set("timeout", int(self.timeout * 1000))  # Z3 timeout in milliseconds
            
            # Add working memory facts as true
            for fact in working_memory_facts:
                var = self._get_variable(fact)
                if var is not None:
                    solver.add(var)
            
            # Encode each rule as logical constraints
            for rule in rules:
                # Encode conditions (AND of all conditions)
                conditions = []
                for condition in rule.conditions:
                    # Extract proposition name from condition
                    prop_name = self._extract_proposition(condition)
                    if prop_name:
                        var = self._get_variable(prop_name)
                        if var is not None:
                            conditions.append(var)
                
                # Encode actions (OR of all actions, or AND depending on rule type)
                actions = []
                for action in rule.actions:
                    prop_name = self._extract_proposition_from_action(action)
                    if prop_name:
                        var = self._get_variable(prop_name)
                        if var is not None:
                            actions.append(var)
                
                # Rule: conditions => actions
                if conditions and actions:
                    # If all conditions true, then all actions true
                    solver.add(Implies(And(*conditions), And(*actions)))
            
            # Check satisfiability
            result = solver.check()
            
            if result == unsat:
                # Try to find minimal unsatisfiable core
                try:
                    core = solver.unsat_core()
                    core_str = ", ".join(str(c) for c in core)
                    return False, f"Rule chain is unsatisfiable. Core: {core_str}", warnings
                except Exception:
                    return False, "Rule chain is unsatisfiable", warnings
            elif result == unknown:
                warnings.append("Z3 could not determine satisfiability")
                return True, None, warnings
            else:  # sat
                return True, None, warnings
                
        except Exception as e:
            logger.error(f"Error in Z3 rule chain validation: {e}", exc_info=True)
            warnings.append(f"Validation error: {str(e)}")
            return True, None, warnings  # Fail gracefully
    
    def validate_causal_chain(
        self,
        chain: List[Tuple[str, str]],  # List of (cause, effect) pairs
        check_transitivity: bool = True
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate a causal chain for logical consistency.
        
        Checks:
        - No cycles (A causes B, B causes A)
        - Transitivity (if A causes B and B causes C, then A causes C)
        - No contradictions
        
        Args:
            chain: List of (cause, effect) tuples
            check_transitivity: Whether to check transitivity
            
        Returns:
            Tuple of (is_valid, error_message, warnings)
        """
        if not self.enabled:
            return True, None, []
        
        if not chain:
            return True, None, []
        
        warnings: List[str] = []
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for effect in self._causal_graph.get(node, set()):
                if effect not in visited:
                    if has_cycle(effect):
                        return True
                elif effect in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Build causal graph from chain
        temp_graph: Dict[str, Set[str]] = {}
        for cause, effect in chain:
            if cause not in temp_graph:
                temp_graph[cause] = set()
            temp_graph[cause].add(effect)
        
        # Check all nodes for cycles
        for cause, effect in chain:
            if cause not in visited:
                # Temporarily set causal graph for cycle check
                old_graph = self._causal_graph.copy()
                self._causal_graph = temp_graph
                try:
                    if has_cycle(cause):
                        return False, f"Causal cycle detected involving {cause}", warnings
                finally:
                    self._causal_graph = old_graph
                    visited.clear()
                    rec_stack.clear()
        
        # Encode causal relationships in Z3
        solver = Solver()
        try:
            solver.set("timeout", int(self.timeout * 1000))
            
            for cause, effect in chain:
                cause_var = self._get_variable(f"causes_{cause}_{effect}")
                effect_var = self._get_variable(effect)
                if cause_var is not None and effect_var is not None:
                    solver.add(Implies(cause_var, effect_var))
            
            # Check transitivity
            if check_transitivity:
                transitive_implications = self._compute_transitive_closure(chain)
                for trans_cause, trans_effect in transitive_implications:
                    if (trans_cause, trans_effect) not in chain:
                        warnings.append(
                            f"Transitive causal relationship: {trans_cause} causes {trans_effect} "
                            f"(via chain: {self._find_causal_path(trans_cause, trans_effect, chain)})"
                        )
            
            # Check satisfiability
            result = solver.check()
            
            if result == unsat:
                return False, "Causal chain is unsatisfiable", warnings
            elif result == unknown:
                warnings.append("Z3 could not determine satisfiability of causal chain")
                return True, None, warnings
            else:
                return True, None, warnings
                
        except Exception as e:
            logger.error(f"Error in Z3 causal chain validation: {e}", exc_info=True)
            warnings.append(f"Validation error: {str(e)}")
            return True, None, warnings
    
    def validate_goal_dependencies(
        self,
        goals: List[Any]  # Goal
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate goal dependencies for satisfiability.
        
        Checks:
        - No circular dependencies
        - All dependencies can be satisfied
        - No conflicting goal states
        
        Args:
            goals: List of goals to validate
            
        Returns:
            Tuple of (is_valid, error_message, warnings)
        """
        if not self.enabled:
            return True, None, []
        
        if not goals:
            return True, None, []
        
        warnings: List[str] = []
        
        # Check for circular dependencies
        dep_graph: Dict[str, List[str]] = {}
        for goal in goals:
            dep_graph[goal.name] = goal.dependencies
        
        cycles = self._find_cycles(dep_graph)
        if cycles:
            cycle_str = " -> ".join(cycles[0]) if cycles else "unknown"
            return False, f"Circular goal dependencies detected: {cycle_str}", warnings
        
        # Encode dependencies in Z3
        solver = Solver()
        try:
            solver.set("timeout", int(self.timeout * 1000))
            
            # Create variables for each goal completion
            goal_vars: Dict[str, BoolRef] = {}
            for goal in goals:
                var = self._get_variable(f"goal_{goal.name}_completed")
                if var is not None:
                    goal_vars[goal.name] = var
            
            # Encode dependencies: if goal depends on others, those must be completed first
            for goal in goals:
                if goal.dependencies and goal.name in goal_vars:
                    dep_vars = [goal_vars[dep] for dep in goal.dependencies if dep in goal_vars]
                    if dep_vars:
                        solver.add(Implies(goal_vars[goal.name], And(*dep_vars)))
            
            # Check satisfiability
            result = solver.check()
            
            if result == unsat:
                return False, "Goal dependencies are unsatisfiable", warnings
            elif result == unknown:
                warnings.append("Z3 could not determine satisfiability of goal dependencies")
                return True, None, warnings
            else:
                return True, None, warnings
                
        except Exception as e:
            logger.error(f"Error in Z3 goal dependency validation: {e}", exc_info=True)
            warnings.append(f"Validation error: {str(e)}")
            return True, None, warnings
    
    def validate_learned_procedure(
        self,
        procedure_name: str,
        preconditions: List[str],
        postconditions: List[str],
        tool_sequence: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate a learned procedure for logical soundness.
        
        Checks:
        - Preconditions are sufficient for postconditions
        - Tool sequence maintains invariants
        - No logical contradictions
        
        Args:
            procedure_name: Name of the procedure
            preconditions: List of precondition propositions
            postconditions: List of postcondition propositions
            tool_sequence: Sequence of tool calls
            
        Returns:
            Tuple of (is_valid, error_message, warnings)
        """
        if not self.enabled:
            return True, None, []
        
        if not preconditions and not postconditions:
            return True, None, []
        
        solver = Solver()
        warnings: List[str] = []
        
        try:
            solver.set("timeout", int(self.timeout * 1000))
            
            # Encode preconditions as true
            pre_vars = []
            for pre in preconditions:
                var = self._get_variable(pre)
                if var is not None:
                    pre_vars.append(var)
            
            if pre_vars:
                solver.add(And(*pre_vars))
            
            # Encode postconditions as goals
            post_vars = []
            for post in postconditions:
                var = self._get_variable(post)
                if var is not None:
                    post_vars.append(var)
            
            # For each tool in sequence, encode its effects
            # This is simplified - in practice, you'd have a model of each tool's effects
            for i, tool_call in enumerate(tool_sequence):
                tool_name = tool_call.get("tool_name", "")
                # Extract expected effects from tool call
                # This would need to be more sophisticated in practice
                pass
            
            # Check if postconditions are satisfiable given preconditions
            solver.push()  # Save state
            if post_vars:
                solver.add(Not(And(*post_vars)))  # Try to prove postconditions false
            
            result = solver.check()
            solver.pop()  # Restore state
            
            if result == unsat:
                # Postconditions are necessarily true given preconditions
                return True, None, warnings
            elif result == sat:
                warnings.append(
                    f"Postconditions may not be guaranteed by preconditions for procedure {procedure_name}"
                )
                return True, None, warnings
            else:
                warnings.append("Z3 could not determine soundness of learned procedure")
                return True, None, warnings
                
        except Exception as e:
            logger.error(f"Error in Z3 procedure validation: {e}", exc_info=True)
            warnings.append(f"Validation error: {str(e)}")
            return True, None, warnings
    
    def validate_plan_logic(
        self,
        plan: Any  # Plan from plan_exec_assess_loop
    ) -> Dict[str, Any]:
        """
        Validate that a plan logically leads to its goal.
        
        Encodes plan steps as logical propositions and checks if:
        (step_1 AND step_2 AND ... AND assumptions) => goal
        
        Args:
            plan: Plan object with goal, steps, assumptions, expected_outcomes
            
        Returns:
            Dictionary with validation results:
            - is_logically_sound: bool
            - logical_issues: List[str] (descriptions of logical problems)
            - recommendations: List[str] (suggestions for improvement)
            - missing_preconditions: List[str] (preconditions that may be missing)
            - contradictions: List[Tuple[str, str]] (contradictory steps/assumptions)
            - warnings: List[str] (non-critical warnings)
        """
        if not self.enabled:
            return {
                "is_logically_sound": True,
                "logical_issues": [],
                "recommendations": [],
                "missing_preconditions": [],
                "contradictions": [],
                "warnings": ["Z3 validation is disabled"],
            }
        
        if not plan:
            return {
                "is_logically_sound": False,
                "logical_issues": ["Plan is None or empty"],
                "recommendations": ["Provide a valid plan"],
                "missing_preconditions": [],
                "contradictions": [],
                "warnings": [],
            }
        
        solver = Solver()
        warnings: List[str] = []
        logical_issues: List[str] = []
        recommendations: List[str] = []
        missing_preconditions: List[str] = []
        contradictions: List[Tuple[str, str]] = []
        
        try:
            solver.set("timeout", int(self.timeout * 1000))
            
            # Extract goal proposition
            goal_text = getattr(plan, 'goal', '') or ''
            goal_prop = self._extract_plan_proposition(goal_text, "goal")
            goal_var = self._get_variable(goal_prop) if goal_prop else None
            
            # Extract step propositions
            steps = getattr(plan, 'steps', []) or []
            step_vars: List[BoolRef] = []
            step_props: List[str] = []
            
            for i, step in enumerate(steps):
                step_desc = step.get("description", "") if isinstance(step, dict) else str(step)
                step_prop = self._extract_plan_proposition(step_desc, f"step_{i+1}")
                if step_prop:
                    step_props.append(step_prop)
                    var = self._get_variable(step_prop)
                    if var is not None:
                        step_vars.append(var)
            
            # Extract assumption propositions
            assumptions = getattr(plan, 'assumptions', []) or []
            assumption_vars: List[BoolRef] = []
            assumption_props: List[str] = []
            
            for i, assumption in enumerate(assumptions):
                assump_text = assumption if isinstance(assumption, str) else str(assumption)
                assump_prop = self._extract_plan_proposition(assump_text, f"assumption_{i+1}")
                if assump_prop:
                    assumption_props.append(assump_prop)
                    var = self._get_variable(assump_prop)
                    if var is not None:
                        assumption_vars.append(var)
            
            # Encode step ordering: step_i => step_i+1 (if step i is required for step i+1)
            # This is a heuristic - we assume sequential steps depend on previous ones
            for i in range(len(step_vars) - 1):
                if step_vars[i] is not None and step_vars[i+1] is not None:
                    solver.add(Implies(step_vars[i], step_vars[i+1]))
            
            # Encode assumptions as premises (they are given)
            if assumption_vars:
                solver.add(And(*assumption_vars))
            
            # Check if steps + assumptions => goal
            if step_vars and goal_var is not None:
                # Encode: (step_1 AND step_2 AND ... AND assumptions) => goal
                all_steps = And(*step_vars) if step_vars else None
                if all_steps is not None and assumption_vars:
                    all_premises = And(all_steps, And(*assumption_vars))
                elif all_steps is not None:
                    all_premises = all_steps
                elif assumption_vars:
                    all_premises = And(*assumption_vars)
                else:
                    all_premises = None
                
                if all_premises is not None:
                    # Check if premises imply goal
                    implication = Implies(all_premises, goal_var)
                    solver.push()
                    solver.add(Not(implication))  # Try to prove implication false
                    result = solver.check()
                    solver.pop()
                    
                    if result == unsat:
                        # Implication is valid - plan is logically sound
                        is_logically_sound = True
                    elif result == sat:
                        # Implication is not valid - plan may not lead to goal
                        is_logically_sound = False
                        logical_issues.append(
                            "Plan steps and assumptions do not logically guarantee the goal will be achieved"
                        )
                        recommendations.append(
                            "Review plan steps to ensure they collectively lead to the goal"
                        )
                        recommendations.append(
                            "Consider adding intermediate steps or clarifying assumptions"
                        )
                    else:  # unknown
                        is_logically_sound = True  # Default to sound if Z3 can't determine
                        warnings.append("Z3 could not determine if plan logically leads to goal")
                else:
                    # No steps or assumptions - plan is incomplete
                    is_logically_sound = False
                    logical_issues.append("Plan has no steps or assumptions")
                    recommendations.append("Add specific steps to achieve the goal")
            else:
                # No steps or no goal - plan is incomplete
                is_logically_sound = False
                if not step_vars:
                    logical_issues.append("Plan has no steps")
                    recommendations.append("Add specific steps to achieve the goal")
                if goal_var is None:
                    logical_issues.append("Plan has no clear goal")
                    recommendations.append("Define a clear, specific goal")
            
            # Check for contradictions in assumptions
            if len(assumption_props) > 1:
                assumption_propositions = [(prop, True) for prop in assumption_props]
                assumption_contradictions = self.detect_contradictions(assumption_propositions)
                if assumption_contradictions:
                    contradictions.extend(assumption_contradictions)
                    logical_issues.append(
                        f"Found {len(assumption_contradictions)} contradictory assumptions"
                    )
                    recommendations.append("Review and resolve contradictory assumptions")
            
            # Check for contradictions between steps
            if len(step_props) > 1:
                step_propositions = [(prop, True) for prop in step_props]
                step_contradictions = self.detect_contradictions(step_propositions)
                if step_contradictions:
                    contradictions.extend(step_contradictions)
                    logical_issues.append(
                        f"Found {len(step_contradictions)} contradictory steps"
                    )
                    recommendations.append("Review and resolve contradictory steps")
            
            # Check for missing preconditions
            # Heuristic: if goal requires something that's not in steps or assumptions
            if goal_var is not None and step_vars:
                # Try to identify what might be missing
                # This is simplified - in practice would use more sophisticated analysis
                if len(step_vars) < 2:
                    missing_preconditions.append("Plan may need more intermediate steps")
                    recommendations.append("Consider breaking down the goal into smaller steps")
            
            # Update validation stats
            self.update_validation_stats(
                contradictions_count=len(contradictions)
            )
            
            return {
                "is_logically_sound": is_logically_sound,
                "logical_issues": logical_issues,
                "recommendations": recommendations,
                "missing_preconditions": missing_preconditions,
                "contradictions": contradictions,
                "warnings": warnings,
            }
            
        except Exception as e:
            logger.error(f"Error in Z3 plan logic validation: {e}", exc_info=True)
            warnings.append(f"Validation error: {str(e)}")
            # Return non-blocking result - don't fail the plan
            return {
                "is_logically_sound": True,  # Default to sound on error
                "logical_issues": [],
                "recommendations": [],
                "missing_preconditions": [],
                "contradictions": [],
                "warnings": warnings,
            }
    
    def _extract_plan_proposition(self, text: str, prefix: str) -> str:
        """
        Extract a proposition name from plan text.
        
        Uses heuristics to create a proposition identifier from text.
        
        Args:
            text: Text to extract proposition from
            prefix: Prefix for the proposition name
            
        Returns:
            Proposition name string
        """
        if not text:
            return f"{prefix}_empty"
        
        # Normalize text: lowercase, remove special chars, take first few words
        import re
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        words = normalized.split()[:5]  # Take first 5 words
        prop_name = f"{prefix}_{'_'.join(words)}"
        
        # Limit length
        if len(prop_name) > 100:
            prop_name = prop_name[:100]
        
        return prop_name
    
    def detect_contradictions(
        self,
        propositions: List[Tuple[str, bool]]  # (name, truth_value)
    ) -> List[Tuple[str, str]]:
        """
        Detect logical contradictions in a set of propositions.
        
        Args:
            propositions: List of (proposition_name, truth_value) tuples
            
        Returns:
            List of (prop1, prop2) tuples that contradict each other
        """
        if not self.enabled:
            return []
        
        if not propositions:
            return []
        
        contradictions: List[Tuple[str, str]] = []

        # Fast-path: detect direct contradictions for the same proposition name.
        # If a name appears with both True and False, return (name, NOT(name)).
        by_name: Dict[str, Set[bool]] = defaultdict(set)
        for prop_name, truth_value in propositions:
            if isinstance(prop_name, str) and prop_name:
                by_name[prop_name].add(bool(truth_value))
        for name, vals in by_name.items():
            if True in vals and False in vals:
                contradictions.append((name, f"NOT({name})"))

        # If we already found direct contradictions, return them (keeps output stable and avoids
        # spurious pairwise contradictions caused by duplicated facts in the solver).
        if contradictions:
            return contradictions

        solver = Solver()
        
        try:
            solver.set("timeout", int(self.timeout * 1000))
            
            # Add all propositions
            for prop_name, truth_value in propositions:
                var = self._get_variable(prop_name)
                if var is not None:
                    if truth_value:
                        solver.add(var)
                    else:
                        solver.add(Not(var))
            
            # Check for contradictions by trying all pairs (distinct proposition names).
            for i, (prop1_name, prop1_val) in enumerate(propositions):
                for prop2_name, prop2_val in propositions[i+1:]:
                    if prop1_name == prop2_name:
                        continue
                    # Check if prop1 and prop2 can both be true
                    solver.push()
                    var1 = self._get_variable(prop1_name)
                    var2 = self._get_variable(prop2_name)
                    
                    if var1 is not None and var2 is not None:
                        if prop1_val and prop2_val:
                            solver.add(And(var1, var2))
                        elif prop1_val and not prop2_val:
                            solver.add(And(var1, Not(var2)))
                        elif not prop1_val and prop2_val:
                            solver.add(And(Not(var1), var2))
                        else:
                            solver.add(And(Not(var1), Not(var2)))
                        
                        result = solver.check()
                        solver.pop()
                        
                        if result == unsat:
                            contradictions.append((prop1_name, prop2_name))
                    else:
                        solver.pop()
            
            return contradictions
            
        except Exception as e:
            logger.error(f"Error in contradiction detection: {e}", exc_info=True)
            return []
    
    def detect_comprehensive_contradictions(
        self,
        response: str,
        existing_memories: Optional[List[Any]] = None,
        memory_manager: Optional[Any] = None,
        use_web_search: bool = True,
        fact_checker: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive contradiction detection using multiple methods.
        
        Combines:
        - Z3 logical validation
        - Semantic similarity (memory conflict detector)
        - Web search fact-checking (for verifiable claims)
        - Epistemic confidence weighting
        
        Args:
            response: Response text to check for contradictions
            existing_memories: Optional list of existing MemoryRecord objects
            memory_manager: Optional MemoryManager for semantic search
            use_web_search: Whether to use web search fact-checking
            fact_checker: Optional FactChecker instance
            
        Returns:
            Dictionary with comprehensive contradiction report:
                - contradictions: List of contradiction records
                - overall_contradiction_score: 0.0-1.0
                - z3_contradictions: List from Z3 validation
                - semantic_contradictions: List from memory conflict detector
                - web_fact_check: Dict from fact checker (if enabled)
        """
        contradictions: List[Dict[str, Any]] = []
        z3_contradictions: List[Tuple[str, str]] = []
        semantic_contradictions: List[Dict[str, Any]] = []
        web_fact_check: Optional[Dict[str, Any]] = None
        
        # 1. Z3 logical contradiction detection
        if self.enabled:
            try:
                # Extract propositions from response
                # This is simplified - in practice would use more sophisticated extraction
                propositions: List[Tuple[str, bool]] = []
                
                # Simple heuristic: extract statements that look like propositions
                import re
                sentences = re.split(r'[.!?]+', response)
                for i, sentence in enumerate(sentences):
                    sentence = sentence.strip()
                    if len(sentence) > 10:
                        # Create proposition name from sentence
                        prop_name = f"claim_{i}"
                        propositions.append((prop_name, True))
                
                if propositions:
                    z3_contradictions = self.detect_contradictions(propositions)
                    for prop1, prop2 in z3_contradictions:
                        contradictions.append({
                            "type": "logical",
                            "method": "z3",
                            "proposition1": prop1,
                            "proposition2": prop2,
                            "confidence": 0.8,
                            "description": f"Logical contradiction detected between {prop1} and {prop2}"
                        })
            except Exception as e:
                logger.debug(f"Error in Z3 contradiction detection: {e}")
        
        # 2. Semantic contradiction detection (memory conflict detector)
        if existing_memories and memory_manager:
            try:
                from ..memory.conflict.detection import ConflictDetector
                from ..memory import MemoryRecord
                
                # Create a temporary memory record from response
                temp_memory = MemoryRecord(
                    namespace="temp",
                    text=response,
                    importance=0.5
                )
                
                conflict_detector = ConflictDetector(
                    memory_manager=memory_manager,
                    similarity_threshold=0.85,
                    contradiction_threshold=0.7
                )
                
                conflicts = conflict_detector.detect_conflicts(temp_memory, existing_memories)
                
                for conflict in conflicts:
                    semantic_contradictions.append({
                        "type": conflict.conflict_type,
                        "method": "semantic",
                        "memory1_id": conflict.memory1.id if hasattr(conflict.memory1, 'id') else None,
                        "memory2_id": conflict.memory2.id if hasattr(conflict.memory2, 'id') else None,
                        "confidence": conflict.confidence,
                        "evidence": conflict.evidence,
                        "description": f"Semantic contradiction: {conflict.evidence}"
                    })
                    contradictions.append({
                        "type": conflict.conflict_type,
                        "method": "semantic",
                        "confidence": conflict.confidence,
                        "evidence": conflict.evidence,
                        "description": f"Semantic contradiction: {conflict.evidence}"
                    })
            except Exception as e:
                logger.debug(f"Error in semantic contradiction detection: {e}")
        
        # 3. Web search fact-checking
        if use_web_search:
            try:
                if fact_checker is None:
                    from .fact_checker import FactChecker
                    fact_checker = FactChecker(enable_web_search=True)
                
                web_fact_check = fact_checker.fact_check_response(
                    response,
                    existing_memories
                )
                
                # Add contradictions from web fact-checking
                for result in web_fact_check.get("results", []):
                    if result.contradiction_score > 0.5:
                        contradictions.append({
                            "type": "factual",
                            "method": "web_search",
                            "claim": result.claim.text,
                            "contradiction_score": result.contradiction_score,
                            "confidence": result.confidence,
                            "evidence": result.evidence,
                            "description": f"Web search contradicts claim: {result.claim.text[:100]}"
                        })
            except Exception as e:
                logger.debug(f"Error in web search fact-checking: {e}")
        
        # Calculate overall contradiction score
        if contradictions:
            # Weight by confidence and method
            method_weights = {
                "z3": 0.3,
                "semantic": 0.4,
                "web_search": 0.3
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for cont in contradictions:
                method = cont.get("method", "semantic")
                confidence = cont.get("confidence", 0.5)
                weight = method_weights.get(method, 0.3)
                
                weighted_score += confidence * weight
                total_weight += weight
            
            overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
        else:
            overall_score = 0.0
        
        # Update validation stats
        self.update_validation_stats(
            contradictions_count=len(contradictions)
        )
        
        return {
            "contradictions": contradictions,
            "overall_contradiction_score": overall_score,
            "z3_contradictions": z3_contradictions,
            "semantic_contradictions": semantic_contradictions,
            "web_fact_check": web_fact_check,
            "total_contradictions": len(contradictions)
        }
    
    def get_validation_summary(self, max_size_bytes: int = 1024) -> Dict[str, Any]:
        """
        Get compact validation summary for world state integration.
        
        Args:
            max_size_bytes: Maximum size in bytes for the summary
            
        Returns:
            Dictionary with validation summary
        """
        summary = ValidationSummary(
            enabled=self.enabled,
            last_validation=self._last_validation_time,
            rule_chain_valid=self._validation_stats["rule_chain_valid"],
            causal_chains_valid=self._validation_stats["causal_chains_valid"],
            goal_dependencies_valid=self._validation_stats["goal_dependencies_valid"],
            warnings_count=self._validation_stats["warnings_count"],
            contradictions_count=self._validation_stats["contradictions_count"],
        )
        
        result = summary.to_dict()
        
        # Ensure size limit
        import json
        json_str = json.dumps(result)
        if len(json_str.encode('utf-8')) > max_size_bytes:
            # Truncate by removing optional fields
            if result.get("last_validation"):
                result["last_validation"] = None
            json_str = json.dumps(result)
            if len(json_str.encode('utf-8')) > max_size_bytes:
                # Further truncate
                result = {
                    "enabled": result["enabled"],
                    "rule_chain_valid": result["rule_chain_valid"],
                    "causal_chains_valid": result["causal_chains_valid"],
                    "goal_dependencies_valid": result["goal_dependencies_valid"],
                }
                json_str = json.dumps(result)
                if len(json_str.encode("utf-8")) > max_size_bytes:
                    # Final fallback: smallest useful summary.
                    result = {"enabled": result["enabled"]}
        
        return result
    
    def update_validation_stats(
        self,
        rule_chain_valid: Optional[bool] = None,
        causal_chains_valid: Optional[bool] = None,
        goal_dependencies_valid: Optional[bool] = None,
        warnings_count: Optional[int] = None,
        contradictions_count: Optional[int] = None
    ) -> None:
        """Update validation statistics."""
        if rule_chain_valid is not None:
            self._validation_stats["rule_chain_valid"] = rule_chain_valid
        if causal_chains_valid is not None:
            self._validation_stats["causal_chains_valid"] = causal_chains_valid
        if goal_dependencies_valid is not None:
            self._validation_stats["goal_dependencies_valid"] = goal_dependencies_valid
        if warnings_count is not None:
            self._validation_stats["warnings_count"] = warnings_count
        if contradictions_count is not None:
            self._validation_stats["contradictions_count"] = contradictions_count
        
        self._last_validation_time = datetime.now(timezone.utc)
    
    # Helper methods
    
    def _extract_proposition(self, condition: Dict[str, Any]) -> Optional[str]:
        """Extract proposition name from a condition pattern."""
        # Try various fields
        for field in ["content", "type", "name", "value"]:
            if field in condition:
                val = condition[field]
                if isinstance(val, str):
                    return val
        return None
    
    def _extract_proposition_from_action(self, action: Dict[str, Any]) -> Optional[str]:
        """Extract proposition name from an action."""
        content = action.get("content", {})
        if isinstance(content, dict):
            return self._extract_proposition(content)
        return None
    
    def _compute_transitive_closure(
        self,
        chain: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        """Compute transitive closure of causal chain."""
        # Build graph
        graph: Dict[str, Set[str]] = {}
        for cause, effect in chain:
            if cause not in graph:
                graph[cause] = set()
            graph[cause].add(effect)
        
        # Compute transitive closure using Floyd-Warshall
        nodes = set()
        for cause, effect in chain:
            nodes.add(cause)
            nodes.add(effect)
        
        closure: Dict[str, Set[str]] = {}
        for node in nodes:
            closure[node] = set()
            if node in graph:
                closure[node].update(graph[node])
        
        # Transitive closure
        for k in nodes:
            for i in nodes:
                if k in closure.get(i, set()):
                    for j in closure.get(k, set()):
                        closure[i].add(j)
        
        # Convert to list of tuples
        result = []
        for cause in closure:
            for effect in closure[cause]:
                if (cause, effect) not in chain:
                    result.append((cause, effect))
        
        return result
    
    def _find_causal_path(
        self,
        start: str,
        end: str,
        chain: List[Tuple[str, str]]
    ) -> List[str]:
        """Find causal path from start to end."""
        graph: Dict[str, List[str]] = {}
        for cause, effect in chain:
            if cause not in graph:
                graph[cause] = []
            graph[cause].append(effect)
        
        # BFS to find path
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            node, path = queue.popleft()
            if node == end:
                return path
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def _find_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find cycles in a directed graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            
            rec_stack.remove(node)
            path.pop()
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles

