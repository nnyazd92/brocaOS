"""
Cognitive dissonance measurement system.

Based on Festinger's Cognitive Dissonance Theory (1957):
Measures psychological discomfort from holding contradictory beliefs, attitudes, or values.

Key principles implemented:
1. Multi-dimensional measurement (logical, factual, behavioral, goal-based)
2. Importance weighting: Higher confidence contradictions amplify dissonance (epistemic confidence)
3. Ratio-based calculation: Dissonance magnitude depends on ratio of dissonant to consonant cognitions
4. Number of dissonant elements: More contradictions increase overall dissonance

Measures multi-dimensional drift from self-model:
- Logical dissonance: Contradictions with capabilities/knowledge boundaries
- Factual dissonance: Claims contradicting self-model facts (uses ratio of dissonant/consonant elements)
- Behavioral dissonance: Actions not matching stated preferences/patterns
- Goal-based dissonance: Goals/actions not aligned with self-model objectives

Reference: Festinger, L. (1957). A Theory of Cognitive Dissonance. Stanford University Press.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..self_model.model import SelfModel
    from ..self_model.consistency import ConsistencyChecker, ConsistencyResult
    from ..self_model.epistemic.engine import MetacognitiveEngine

logger = logging.getLogger(__name__)


@dataclass
class DissonanceMetrics:
    """Multi-dimensional cognitive dissonance metrics."""
    timestamp: datetime
    logical_dissonance: float = 0.0  # 0.0-1.0
    factual_dissonance: float = 0.0  # 0.0-1.0
    behavioral_dissonance: float = 0.0  # 0.0-1.0
    goal_dissonance: float = 0.0  # 0.0-1.0
    overall_dissonance: float = 0.0  # 0.0-1.0 (weighted composite)
    
    # Weights for aggregation (should sum to 1.0)
    weight_logical: float = 0.3
    weight_factual: float = 0.3
    weight_behavioral: float = 0.2
    weight_goal: float = 0.2
    
    def compute_overall(self) -> float:
        """Compute overall dissonance from component scores."""
        self.overall_dissonance = (
            self.logical_dissonance * self.weight_logical +
            self.factual_dissonance * self.weight_factual +
            self.behavioral_dissonance * self.weight_behavioral +
            self.goal_dissonance * self.weight_goal
        )
        return self.overall_dissonance


class CognitiveDissonanceMonitor:
    """
    Monitors cognitive dissonance across multiple dimensions.
    
    Measures drift from self-model through:
    - Logical inconsistencies (via ConsistencyChecker)
    - Factual errors (claims vs. knowledge boundaries)
    - Behavioral deviations (tool usage vs. stated patterns)
    - Goal misalignment (reasoning goals vs. self-model objectives)
    """
    
    def __init__(
        self,
        self_model: "SelfModel",
        consistency_checker: Optional["ConsistencyChecker"] = None,
        epistemic_engine: Optional["MetacognitiveEngine"] = None,
        history_window: int = 100,
        weight_logical: float = 0.3,
        weight_factual: float = 0.3,
        weight_behavioral: float = 0.2,
        weight_goal: float = 0.2,
        memory_manager: Optional[Any] = None,
        z3_validator: Optional[Any] = None,
        fact_checker: Optional[Any] = None
    ):
        """
        Initialize cognitive dissonance monitor.
        
        Args:
            self_model: SelfModel instance to compare against
            consistency_checker: Optional ConsistencyChecker for logical/factual checks
            epistemic_engine: Optional MetacognitiveEngine for epistemic confidence weighting
            history_window: Number of measurements to keep in history
            weight_logical: Weight for logical dissonance in overall score
            weight_factual: Weight for factual dissonance in overall score
            weight_behavioral: Weight for behavioral dissonance in overall score
            weight_goal: Weight for goal dissonance in overall score
            memory_manager: Optional MemoryManager for memory conflict detection
            z3_validator: Optional Z3LogicalValidator for logical validation
            fact_checker: Optional FactChecker for web search fact-checking
        """
        self.self_model = self_model
        self.consistency_checker = consistency_checker
        self.epistemic_engine = epistemic_engine
        self.history_window = history_window
        self.memory_manager = memory_manager
        self.z3_validator = z3_validator
        self.fact_checker = fact_checker
        
        # Weights for aggregation (must sum to ~1.0)
        total_weight = weight_logical + weight_factual + weight_behavioral + weight_goal
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Dissonance weights sum to {total_weight}, normalizing to 1.0")
            scale = 1.0 / total_weight if total_weight > 0 else 1.0
            weight_logical *= scale
            weight_factual *= scale
            weight_behavioral *= scale
            weight_goal *= scale
        
        self.weight_logical = weight_logical
        self.weight_factual = weight_factual
        self.weight_behavioral = weight_behavioral
        self.weight_goal = weight_goal
        
        # Historical tracking
        self.dissonance_history: deque = deque(maxlen=history_window)
        
        # Component-level tracking
        self.logical_violations: deque = deque(maxlen=history_window)
        self.factual_errors: deque = deque(maxlen=history_window)
        self.behavioral_deviations: deque = deque(maxlen=history_window)
        self.goal_conflicts: deque = deque(maxlen=history_window)
        
        # Measurement tracking (for diagnostics)
        self._measurement_errors: deque = deque(maxlen=history_window)
        self._measurement_success_count = 0
        self._measurement_failure_count = 0
        
        # Signal manager for damping (optional)
        self._signal_manager: Optional[Any] = None
        
        logger.info("Initialized CognitiveDissonanceMonitor")
    
    def measure_dissonance(
        self,
        response: Optional[str] = None,
        conversation_context: Optional[List[Dict[str, str]]] = None,
        tool_usage: Optional[List[Dict[str, Any]]] = None,
        reasoning_goals: Optional[List[Dict[str, Any]]] = None,
        emotional_context: Optional[Dict[str, float]] = None
    ) -> DissonanceMetrics:
        """
        Measure multi-dimensional cognitive dissonance.
        
        Based on Festinger's cognitive dissonance theory (1957): measures discomfort from
        holding contradictory beliefs, attitudes, or values. Multi-dimensional approach tracks:
        - Logical: contradictions with capabilities/knowledge boundaries
        - Factual: claims contradicting self-model facts
        - Behavioral: actions not matching stated preferences/patterns
        - Goal-based: goals/actions not aligned with self-model objectives
        
        Dissonance magnitude follows Festinger's principles:
        - Importance of conflicting elements (weighted by epistemic confidence)
        - Ratio of dissonant to consonant cognitions
        - Number of dissonant elements

        Args:
            response: Optional LLM response to check
            conversation_context: Optional conversation context for consistency checking
            tool_usage: Optional list of tool usage patterns
            reasoning_goals: Optional list of reasoning system goals
            emotional_context: Optional emotional state dictionary (affects dissonance sensitivity)
            
        Returns:
            DissonanceMetrics with all component scores
        """
        logger.debug(
            f"Measuring cognitive dissonance: response={'present' if response else 'none'}, "
            f"tool_usage={len(tool_usage) if tool_usage else 0}, "
            f"goals={len(reasoning_goals) if reasoning_goals else 0}"
        )
        
        metrics = DissonanceMetrics(
            timestamp=datetime.now(timezone.utc),
            weight_logical=self.weight_logical,
            weight_factual=self.weight_factual,
            weight_behavioral=self.weight_behavioral,
            weight_goal=self.weight_goal
        )
        
        # Measure logical dissonance (uses ConsistencyChecker)
        if response and self.consistency_checker:
            logical_dissonance = self._measure_logical_dissonance(response, conversation_context)
            metrics.logical_dissonance = logical_dissonance
        else:
            # Use historical average if no current measurement
            metrics.logical_dissonance = self._get_average_logical_dissonance()
        
        # Measure factual dissonance
        if response:
            factual_dissonance = self._measure_factual_dissonance(response)
            metrics.factual_dissonance = factual_dissonance
        else:
            metrics.factual_dissonance = self._get_average_factual_dissonance()
        
        # Measure behavioral dissonance
        if tool_usage:
            behavioral_dissonance = self._measure_behavioral_dissonance(tool_usage)
            metrics.behavioral_dissonance = behavioral_dissonance
        else:
            metrics.behavioral_dissonance = self._get_average_behavioral_dissonance()
        
        # Measure goal-based dissonance
        if reasoning_goals:
            goal_dissonance = self._measure_goal_dissonance(reasoning_goals)
            metrics.goal_dissonance = goal_dissonance
        else:
            metrics.goal_dissonance = self._get_average_goal_dissonance()
        
        # Compute overall dissonance
        metrics.compute_overall()
        
        # Adjust sensitivity based on emotional context (high negative valence amplifies perception)
        if emotional_context:
            valence = emotional_context.get("valence", 0.0)
            if valence < -0.3:
                # High negative valence amplifies dissonance perception (emotional amplification)
                emotional_amplification = 1.0 + (abs(valence) - 0.3) * 0.3  # Up to 30% amplification
                metrics.overall_dissonance = min(1.0, metrics.overall_dissonance * emotional_amplification)
                logger.debug(f"Emotional amplification: valence={valence:.2f}, amplification={emotional_amplification:.2f}")
        
        # Update through SignalManager if available (hybrid approach)
        if self._signal_manager:
            try:
                # Update all dissonance signals
                metrics.overall_dissonance = self._signal_manager.update("dissonance.level", metrics.overall_dissonance)
                metrics.logical_dissonance = self._signal_manager.update("dissonance.logical", metrics.logical_dissonance)
                metrics.factual_dissonance = self._signal_manager.update("dissonance.factual", metrics.factual_dissonance)
                metrics.behavioral_dissonance = self._signal_manager.update("dissonance.behavioral", metrics.behavioral_dissonance)
                metrics.goal_dissonance = self._signal_manager.update("dissonance.goal", metrics.goal_dissonance)
            except Exception as e:
                logger.debug(f"Error updating dissonance signals through SignalManager: {e}")
        
        # Store in history
        self.dissonance_history.append(metrics)
        self._measurement_success_count += 1
        
        # Log measurement results (info level for non-zero values, debug for zero)
        if metrics.overall_dissonance > 0.0:
            logger.info(
                f"Cognitive dissonance measured: overall={metrics.overall_dissonance:.3f}, "
                f"logical={metrics.logical_dissonance:.3f}, factual={metrics.factual_dissonance:.3f}, "
                f"behavioral={metrics.behavioral_dissonance:.3f}, goal={metrics.goal_dissonance:.3f}"
            )
        else:
            logger.debug(
                f"Measured dissonance: overall={metrics.overall_dissonance:.3f}, "
                f"logical={metrics.logical_dissonance:.3f}, factual={metrics.factual_dissonance:.3f}, "
                f"behavioral={metrics.behavioral_dissonance:.3f}, goal={metrics.goal_dissonance:.3f}"
            )
        
        return metrics
    
    def _measure_logical_dissonance(
        self,
        response: str,
        conversation_context: Optional[List[Dict[str, str]]]
    ) -> float:
        """
        Measure logical dissonance using ConsistencyChecker.
        
        Based on Festinger's cognitive dissonance theory: measures discomfort from
        contradictions between stated capabilities/knowledge boundaries and actual responses.
        
        Returns:
            Dissonance score (0.0 = consistent, 1.0 = highly inconsistent)
        """
        if not self.consistency_checker:
            logger.debug("Logical dissonance measurement skipped: consistency_checker not available")
            return 0.0
        
        try:
            consistency_result = self.consistency_checker.validate(
                response=response,
                self_model=self.self_model,
                conversation_context=conversation_context
            )
            
            # Logical dissonance is the severity score (0.0 = consistent, 1.0 = highly inconsistent)
            dissonance = consistency_result.severity
            
            # Extract logical violations first (needed for epistemic weighting)
            logical_violations = [
                v for v in consistency_result.violations
                if v.get("type") == "logical"
            ]
            
            # Weight by epistemic confidence if available
            if self.epistemic_engine and self.self_model.epistemic_layer:
                # Try to get epistemic context for the violation
                # Higher confidence contradictions amplify dissonance
                confidence_weight = 1.0
                try:
                    # Get average confidence from self-model capabilities/constraints involved
                    # This is a simplified approach - in practice, could analyze specific violations
                    if logical_violations:
                        # Use a simple heuristic: if epistemic layer has high-confidence items, weight more
                        # In future, could map specific violations to knowledge items
                        confidence_weight = 1.2  # Amplify high-confidence contradictions
                except Exception as e:
                    logger.debug(f"Error getting epistemic confidence for logical dissonance: {e}")
                
                dissonance = min(1.0, dissonance * confidence_weight)
            
            # Track violations
            if logical_violations:
                self.logical_violations.append({
                    "timestamp": datetime.now(timezone.utc),
                    "violations": logical_violations,
                    "severity": dissonance
                })
            
            return dissonance
            
        except Exception as e:
            self._measurement_failure_count += 1
            self._measurement_errors.append({
                "method": "_measure_logical_dissonance",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc)
            })
            logger.warning(f"Failed to measure logical dissonance: {e}. Returning 0.0 (no dissonance detected)", exc_info=True)
            return 0.0  # Default to no dissonance on error (distinguish from actual zero)
    
    def _measure_factual_dissonance(self, response: str) -> float:
        """
        Measure factual dissonance (claims vs. knowledge boundaries).
        
        Based on Festinger's cognitive dissonance theory: measures discomfort from
        contradictions between factual claims and established knowledge boundaries.
        Uses ratio of dissonant to consonant cognitions (Festinger's key principle).
        
        Returns:
            Dissonance score (0.0 = no contradictions, 1.0 = severe contradictions)
        """
        try:
            dissonance_score = 0.0
            violations: List[Dict[str, Any]] = []
            dissonant_elements = 0
            consonant_elements = 0
            
            # 1. Extract factual claims from response
            if self.fact_checker:
                try:
                    # Get existing memories for comparison
                    existing_memories = []
                    if self.memory_manager:
                        try:
                            existing_memories = self.memory_manager.storage.get_all_memories()
                        except Exception:
                            pass
                    
                    fact_check_result = self.fact_checker.fact_check_response(
                        response,
                        existing_memories
                    )
                    
                    # Use contradiction score from fact-checking
                    contradiction_score = fact_check_result.get("overall_contradiction_score", 0.0)
                    contradicted_count = fact_check_result.get("contradicted_claims_count", 0)
                    
                    if contradiction_score > 0.0:
                        dissonance_score = max(dissonance_score, contradiction_score)
                        dissonant_elements += contradicted_count
                        # Count total claims checked (dissonant + consonant)
                        total_claims = fact_check_result.get("total_claims_checked", contradicted_count)
                        consonant_elements += max(0, total_claims - contradicted_count)
                        violations.append({
                            "type": "web_fact_check",
                            "severity": contradiction_score,
                            "contradicted_claims": contradicted_count,
                            "description": f"Web search fact-checking found {contradicted_count} contradicted claims"
                        })
                except Exception as e:
                    logger.debug(f"Error in fact-checking: {e}")
            
            # 2. Check against knowledge boundaries using semantic similarity
            knowledge_boundaries = self.self_model.knowledge_boundaries
            if knowledge_boundaries and self.memory_manager:
                try:
                    from ..memory import MemoryRecord
                    from ..memory.conflict.detection import ConflictDetector
                    
                    # Create temporary memory from response
                    temp_memory = MemoryRecord(
                        namespace="temp",
                        text=response,
                        importance=0.5
                    )
                    
                    # Get existing memories related to knowledge boundaries
                    boundary_memories: List[MemoryRecord] = []
                    for key, value_dict in knowledge_boundaries.items():
                        value = value_dict.get("value", str(value_dict))
                        # Search for memories related to this boundary
                        try:
                            related = self.memory_manager.retrieve_memories(
                                query=f"{key} {value}",
                                limit=5
                            )
                            boundary_memories.extend(related)
                        except Exception:
                            pass
                    
                    if boundary_memories:
                        conflict_detector = ConflictDetector(
                            memory_manager=self.memory_manager,
                            similarity_threshold=0.85,
                            contradiction_threshold=0.7
                        )
                        
                        conflicts = conflict_detector.detect_conflicts(temp_memory, boundary_memories)
                        
                        if conflicts:
                            # Calculate dissonance from conflicts
                            max_conflict_confidence = max(c.confidence for c in conflicts)
                            boundary_dissonance = max_conflict_confidence
                            dissonance_score = max(dissonance_score, boundary_dissonance)
                            dissonant_elements += len(conflicts)
                            # Count boundaries checked (some may be consonant)
                            consonant_elements += max(0, len(boundary_memories) - len(conflicts))
                            
                            violations.append({
                                "type": "knowledge_boundary",
                                "severity": boundary_dissonance,
                                "conflicts_count": len(conflicts),
                                "description": f"Response conflicts with {len(conflicts)} knowledge boundaries"
                            })
                except Exception as e:
                    logger.debug(f"Error checking knowledge boundaries: {e}")
            
            # 3. Use Z3 to check logical consistency of claims
            if self.z3_validator and self.z3_validator.enabled:
                try:
                    # Get existing memories for Z3 validation
                    existing_memories = []
                    if self.memory_manager:
                        try:
                            existing_memories = self.memory_manager.storage.get_all_memories()
                        except Exception:
                            pass
                    
                    z3_result = self.z3_validator.detect_comprehensive_contradictions(
                        response,
                        existing_memories,
                        memory_manager=self.memory_manager,
                        use_web_search=False,  # Already did web search above
                        fact_checker=None  # Already did fact-checking above
                    )
                    
                    z3_contradiction_score = z3_result.get("overall_contradiction_score", 0.0)
                    if z3_contradiction_score > 0.0:
                        dissonance_score = max(dissonance_score, z3_contradiction_score)
                        z3_contradictions = z3_result.get("total_contradictions", 0)
                        dissonant_elements += z3_contradictions
                        # Z3 checks logical consistency - count total statements checked
                        total_statements = z3_result.get("total_statements_checked", z3_contradictions)
                        consonant_elements += max(0, total_statements - z3_contradictions)
                        violations.append({
                            "type": "z3_logical",
                            "severity": z3_contradiction_score,
                            "contradictions_count": z3_contradictions,
                            "description": f"Z3 validation found {z3_contradictions} logical contradictions"
                        })
                except Exception as e:
                    logger.debug(f"Error in Z3 validation: {e}")
            
            # 4. Weight by epistemic confidence if available
            if self.epistemic_engine and self.self_model.epistemic_layer and knowledge_boundaries:
                try:
                    confidence_scores = []
                    for key, value_dict in knowledge_boundaries.items():
                        try:
                            from ..self_model.epistemic.ids import generate_knowledge_boundary_id
                            value = value_dict.get("value", str(value_dict))
                            kid = generate_knowledge_boundary_id(key, value)
                            context = self.epistemic_engine.get_epistemic_context(kid)
                            if context and context.get("confidence_metrics"):
                                conf = context["confidence_metrics"].get("overall_confidence", 0.5)
                                confidence_scores.append(conf)
                        except Exception:
                            pass
                    
                    if confidence_scores:
                        avg_confidence = sum(confidence_scores) / len(confidence_scores)
                        # Higher confidence knowledge boundaries -> stronger dissonance signal when violated
                        # Festinger: importance of conflicting elements amplifies dissonance
                        confidence_weight = 0.8 + (avg_confidence * 0.4)  # Range: 0.8-1.2
                        dissonance_score = min(1.0, dissonance_score * confidence_weight)
                except Exception as e:
                    logger.debug(f"Error weighting factual dissonance by epistemic confidence: {e}")
            
            # Apply Festinger's ratio principle: dissonance magnitude depends on ratio of dissonant to consonant cognitions
            if dissonant_elements > 0 or consonant_elements > 0:
                total_elements = dissonant_elements + consonant_elements
                if total_elements > 0:
                    # Ratio-based adjustment: higher ratio of dissonant elements increases dissonance
                    dissonance_ratio = dissonant_elements / total_elements
                    # Combine base score with ratio-based adjustment (weighted average)
                    ratio_adjusted_score = (dissonance_score * 0.7) + (dissonance_ratio * 0.3)
                    dissonance_score = min(1.0, max(dissonance_score, ratio_adjusted_score))
                    logger.debug(
                        f"Factual dissonance ratio: {dissonant_elements}/{total_elements} = {dissonance_ratio:.3f}, "
                        f"adjusted score: {dissonance_score:.3f}"
                    )
            
            # Track violations
            if violations:
                self.factual_errors.append({
                    "timestamp": datetime.now(timezone.utc),
                    "violations": violations,
                    "severity": dissonance_score
                })
            
            return dissonance_score
            
        except Exception as e:
            self._measurement_failure_count += 1
            self._measurement_errors.append({
                "method": "_measure_factual_dissonance",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc)
            })
            logger.warning(f"Failed to measure factual dissonance: {e}. Returning 0.0 (no dissonance detected)", exc_info=True)
            return 0.0
    
    def _measure_behavioral_dissonance(self, tool_usage: List[Dict[str, Any]]) -> float:
        """
        Measure behavioral dissonance (tool usage vs. stated patterns).
        
        Based on Festinger's cognitive dissonance theory: measures discomfort from
        actions that contradict stated behavioral patterns, preferences, or constraints.
        
        Returns:
            Dissonance score (0.0 = aligned behavior, 1.0 = severe behavioral deviation)
        """
        try:
            if not tool_usage:
                return 0.0
            
            deviation_score = 0.0
            violations: List[Dict[str, Any]] = []
            
            # Extract capabilities and constraints from self model
            capabilities = [cap.get("text", str(cap)) for cap in self.self_model.capabilities]
            constraints = self.self_model.constraints
            
            # If no capabilities listed, can't measure deviation
            if not capabilities:
                return 0.0
            
            capability_text = " ".join(capabilities).lower()
            constraint_values = [v.get("value", str(v)).lower() for v in constraints.values()]
            
            # Analyze each tool usage
            for tool_call in tool_usage:
                tool_name = tool_call.get("function", {}).get("name", "") if isinstance(tool_call, dict) else str(tool_call)
                if not tool_name:
                    continue
                
                tool_name_lower = tool_name.lower()
                
                # Check if tool is mentioned in capabilities
                tool_mentioned = any(tool_name_lower in cap.lower() or cap.lower() in tool_name_lower 
                                    for cap in capabilities)
                
                # Check for constraint violations
                constraint_violation = False
                violation_type = None
                
                # Check for read-only constraint violations
                if "read" in " ".join(constraint_values) and "read-only" in " ".join(constraint_values).lower():
                    # Check if tool is a write operation
                    write_tools = ["write", "create", "update", "delete", "modify", "edit", "save", "store"]
                    if any(write in tool_name_lower for write in write_tools):
                        constraint_violation = True
                        violation_type = "read_only_violation"
                        deviation_score = max(deviation_score, 0.8)  # High deviation for constraint violation
                        violations.append({
                            "type": violation_type,
                            "tool": tool_name,
                            "severity": 0.8,
                            "description": f"Tool {tool_name} violates read-only constraint"
                        })
                
                # Check for capability mismatch
                if not tool_mentioned and not constraint_violation:
                    # Tool not mentioned in capabilities - potential deviation
                    deviation_score = max(deviation_score, 0.3)  # Medium deviation
                    violations.append({
                        "type": "capability_mismatch",
                        "tool": tool_name,
                        "severity": 0.3,
                        "description": f"Tool {tool_name} not mentioned in stated capabilities"
                    })
            
            # Use Z3 to validate tool usage chains for logical consistency
            if self.z3_validator and self.z3_validator.enabled and len(tool_usage) > 1:
                try:
                    # Extract tool sequence
                    tool_sequence = [
                        {
                            "tool_name": tc.get("function", {}).get("name", "") if isinstance(tc, dict) else str(tc),
                            "arguments": tc.get("function", {}).get("arguments", {}) if isinstance(tc, dict) else {}
                        }
                        for tc in tool_usage
                    ]
                    
                    # Check for logical inconsistencies in tool sequence
                    # This is simplified - in practice would have more sophisticated validation
                    # For now, check if tools conflict with each other
                    tool_names = [ts["tool_name"] for ts in tool_sequence if ts["tool_name"]]
                    
                    # Check for contradictory tool patterns (e.g., read then write same file)
                    # This is a simplified check
                    if len(set(tool_names)) < len(tool_names):
                        # Duplicate tools might indicate inefficiency but not necessarily contradiction
                        pass
                    
                    # Could add more sophisticated Z3 validation here
                except Exception as e:
                    logger.debug(f"Error in Z3 tool usage validation: {e}")
            
            # Track deviations
            if violations:
                self.behavioral_deviations.append({
                    "timestamp": datetime.now(timezone.utc),
                    "tool_usage": tool_usage,
                    "violations": violations,
                    "deviation_score": deviation_score
                })
            
            return deviation_score
            
        except Exception as e:
            self._measurement_failure_count += 1
            self._measurement_errors.append({
                "method": "_measure_behavioral_dissonance",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc)
            })
            logger.warning(f"Failed to measure behavioral dissonance: {e}. Returning 0.0 (no dissonance detected)", exc_info=True)
            return 0.0
    
    def _measure_goal_dissonance(self, reasoning_goals: List[Dict[str, Any]]) -> float:
        """
        Measure goal-based dissonance (reasoning goals vs. self-model objectives).
        
        Based on Festinger's cognitive dissonance theory: measures discomfort from
        goals/actions that conflict with self-model objectives, constraints, or capabilities.
        
        Returns:
            Dissonance score (0.0 = aligned goals, 1.0 = severe goal conflicts)
        """
        try:
            if not reasoning_goals:
                return 0.0
            
            conflict_score = 0.0
            violations: List[Dict[str, Any]] = []
            
            # Extract constraints from self model
            constraints = self.self_model.constraints
            constraint_values = [v.get("value", str(v)).lower() for v in constraints.values()]
            capabilities = [cap.get("text", str(cap)).lower() for cap in self.self_model.capabilities]
            
            # Use Z3 to check if goals conflict with constraints
            if self.z3_validator and self.z3_validator.enabled:
                try:
                    from .goal_manager import Goal, GoalType, GoalStatus
                    
                    # Convert reasoning goals to Goal objects if needed
                    goals_to_check: List[Goal] = []
                    for goal_dict in reasoning_goals:
                        if isinstance(goal_dict, Goal):
                            goals_to_check.append(goal_dict)
                        else:
                            # Try to create Goal from dict
                            try:
                                goal = Goal(
                                    name=goal_dict.get("name", "unknown"),
                                    description=goal_dict.get("description", str(goal_dict)),
                                    goal_type=GoalType(goal_dict.get("goal_type", "achieve")),
                                    status=GoalStatus(goal_dict.get("status", "active")),
                                    priority=goal_dict.get("priority", 0.5),
                                    dependencies=goal_dict.get("dependencies", [])
                                )
                                goals_to_check.append(goal)
                            except Exception:
                                # Skip invalid goals
                                continue
                    
                    if goals_to_check:
                        # Validate goal dependencies
                        is_valid, error, warnings = self.z3_validator.validate_goal_dependencies(goals_to_check)
                        
                        if not is_valid:
                            conflict_score = max(conflict_score, 0.7)  # High conflict for unsatisfiable goals
                            violations.append({
                                "type": "goal_dependency_conflict",
                                "severity": 0.7,
                                "error": error,
                                "description": f"Goal dependencies are unsatisfiable: {error}"
                            })
                        
                        # Check each goal against constraints
                        for goal in goals_to_check:
                            goal_text = f"{goal.name} {goal.description}".lower()
                            
                            # Check for constraint violations
                            for constraint_value in constraint_values:
                                # Simple heuristic: check if goal conflicts with constraint
                                # This is simplified - in practice would use semantic analysis
                                
                                # Check for explicit constraint violations
                                if "read-only" in constraint_value and any(word in goal_text for word in ["write", "modify", "edit", "change"]):
                                    conflict_score = max(conflict_score, 0.8)
                                    violations.append({
                                        "type": "constraint_violation",
                                        "goal": goal.name,
                                        "constraint": constraint_value,
                                        "severity": 0.8,
                                        "description": f"Goal {goal.name} violates constraint: {constraint_value}"
                                    })
                                
                                # Check for capability mismatches
                                if capabilities:
                                    goal_mentions_capability = any(cap in goal_text for cap in capabilities)
                                    if not goal_mentions_capability and len(goal_text) > 20:
                                        # Goal doesn't align with stated capabilities
                                        conflict_score = max(conflict_score, 0.4)
                                        violations.append({
                                            "type": "capability_mismatch",
                                            "goal": goal.name,
                                            "severity": 0.4,
                                            "description": f"Goal {goal.name} doesn't align with stated capabilities"
                                        })
                except Exception as e:
                    logger.debug(f"Error in Z3 goal validation: {e}")
            
            # Track conflicts
            if violations:
                self.goal_conflicts.append({
                    "timestamp": datetime.now(timezone.utc),
                    "goals": reasoning_goals,
                    "violations": violations,
                    "conflict_score": conflict_score
                })
            
            return conflict_score
            
        except Exception as e:
            self._measurement_failure_count += 1
            self._measurement_errors.append({
                "method": "_measure_goal_dissonance",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc)
            })
            logger.warning(f"Failed to measure goal dissonance: {e}. Returning 0.0 (no dissonance detected)", exc_info=True)
            return 0.0
    
    def _get_average_logical_dissonance(self) -> float:
        """Get average logical dissonance from history."""
        if len(self.logical_violations) == 0:
            return 0.0
        return sum(v.get("severity", 0.0) for v in self.logical_violations) / len(self.logical_violations)
    
    def _get_average_factual_dissonance(self) -> float:
        """Get average factual dissonance from history."""
        if len(self.factual_errors) == 0:
            return 0.0
        return sum(e.get("severity", 0.0) for e in self.factual_errors) / len(self.factual_errors)
    
    def _get_average_behavioral_dissonance(self) -> float:
        """Get average behavioral dissonance from history."""
        if len(self.behavioral_deviations) == 0:
            return 0.0
        return sum(d.get("deviation_score", 0.0) for d in self.behavioral_deviations) / len(self.behavioral_deviations)
    
    def _get_average_goal_dissonance(self) -> float:
        """Get average goal dissonance from history."""
        if len(self.goal_conflicts) == 0:
            return 0.0
        return sum(c.get("conflict_score", 0.0) for c in self.goal_conflicts) / len(self.goal_conflicts)
    
    def set_memory_manager(self, memory_manager: Any) -> None:
        """Set memory manager for factual dissonance measurement."""
        self.memory_manager = memory_manager
    
    def set_z3_validator(self, z3_validator: Any) -> None:
        """Set Z3 validator for logical validation."""
        self.z3_validator = z3_validator
    
    def set_fact_checker(self, fact_checker: Any) -> None:
        """Set fact checker for web search fact-checking."""
        self.fact_checker = fact_checker
    
    def get_aggregated_dissonance(self) -> Dict[str, Any]:
        """Get aggregated dissonance metrics from history."""
        if len(self.dissonance_history) == 0:
            return {
                "overall_dissonance": 0.0,
                "logical_dissonance": 0.0,
                "factual_dissonance": 0.0,
                "behavioral_dissonance": 0.0,
                "goal_dissonance": 0.0,
                "samples": 0
            }
        
        # Compute averages
        avg_overall = sum(m.overall_dissonance for m in self.dissonance_history) / len(self.dissonance_history)
        avg_logical = sum(m.logical_dissonance for m in self.dissonance_history) / len(self.dissonance_history)
        avg_factual = sum(m.factual_dissonance for m in self.dissonance_history) / len(self.dissonance_history)
        avg_behavioral = sum(m.behavioral_dissonance for m in self.dissonance_history) / len(self.dissonance_history)
        avg_goal = sum(m.goal_dissonance for m in self.dissonance_history) / len(self.dissonance_history)
        
        # Compute trend (increasing/decreasing)
        if len(self.dissonance_history) >= 2:
            recent = self.dissonance_history[-1].overall_dissonance
            earlier = self.dissonance_history[0].overall_dissonance
            trend = recent - earlier
        else:
            trend = 0.0
        
        return {
            "overall_dissonance": avg_overall,
            "logical_dissonance": avg_logical,
            "factual_dissonance": avg_factual,
            "behavioral_dissonance": avg_behavioral,
            "goal_dissonance": avg_goal,
            "trend": trend,  # Positive = increasing, negative = decreasing
            "samples": len(self.dissonance_history),
            "latest": {
                "overall": self.dissonance_history[-1].overall_dissonance,
                "timestamp": self.dissonance_history[-1].timestamp.isoformat()
            }
        }
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """Analyze dissonance trends over time."""
        if len(self.dissonance_history) < 2:
            return {
                "trend": "insufficient_data",
                "component_drifts": {}
            }
        
        # Compute trends for each component
        recent_scores = {
            "logical": self.dissonance_history[-1].logical_dissonance,
            "factual": self.dissonance_history[-1].factual_dissonance,
            "behavioral": self.dissonance_history[-1].behavioral_dissonance,
            "goal": self.dissonance_history[-1].goal_dissonance
        }
        
        # Use first half vs. second half for trend
        mid_point = len(self.dissonance_history) // 2
        earlier_avg = {
            "logical": sum(m.logical_dissonance for m in list(self.dissonance_history)[:mid_point]) / mid_point if mid_point > 0 else 0.0,
            "factual": sum(m.factual_dissonance for m in list(self.dissonance_history)[:mid_point]) / mid_point if mid_point > 0 else 0.0,
            "behavioral": sum(m.behavioral_dissonance for m in list(self.dissonance_history)[:mid_point]) / mid_point if mid_point > 0 else 0.0,
            "goal": sum(m.goal_dissonance for m in list(self.dissonance_history)[:mid_point]) / mid_point if mid_point > 0 else 0.0
        }
        
        component_drifts = {}
        for component in ["logical", "factual", "behavioral", "goal"]:
            drift = recent_scores[component] - earlier_avg[component]
            component_drifts[component] = {
                "drift": drift,
                "direction": "increasing" if drift > 0.1 else "decreasing" if drift < -0.1 else "stable"
            }
        
        # Overall trend
        overall_trend = self.dissonance_history[-1].overall_dissonance - self.dissonance_history[0].overall_dissonance
        trend_direction = "increasing" if overall_trend > 0.1 else "decreasing" if overall_trend < -0.1 else "stable"
        
        return {
            "trend": trend_direction,
            "trend_magnitude": overall_trend,
            "component_drifts": component_drifts
        }
    
    def get_measurement_diagnostics(self) -> Dict[str, Any]:
        """
        Get diagnostics about measurement success/failure rates.
        
        Returns:
            Dictionary with measurement statistics
        """
        total_measurements = self._measurement_success_count + self._measurement_failure_count
        success_rate = (self._measurement_success_count / total_measurements * 100.0) if total_measurements > 0 else 0.0
        
        return {
            "total_measurements": total_measurements,
            "successful_measurements": self._measurement_success_count,
            "failed_measurements": self._measurement_failure_count,
            "success_rate_percent": round(success_rate, 2),
            "recent_errors": list(self._measurement_errors)[-10:] if self._measurement_errors else [],
            "dependencies": {
                "consistency_checker": self.consistency_checker is not None,
                "fact_checker": self.fact_checker is not None,
                "z3_validator": self.z3_validator is not None and (self.z3_validator.enabled if hasattr(self.z3_validator, 'enabled') else False),
                "memory_manager": self.memory_manager is not None,
                "epistemic_engine": self.epistemic_engine is not None
            }
        }

