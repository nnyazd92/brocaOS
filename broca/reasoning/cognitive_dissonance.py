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
    
    # Measurement quality indicators
    measurement_quality: Optional[str] = None  # "measured", "estimated", "unavailable", "error"
    has_sufficient_data: bool = True  # indicates if measurement is based on actual data
    component_availability: Dict[str, bool] = field(default_factory=lambda: {
        "logical": True,
        "factual": True,
        "behavioral": True,
        "goal": True,
    })
    
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
        fact_checker: Optional[Any] = None,
        goal_manager: Optional[Any] = None
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
            goal_manager: Optional GoalManager for extracting active reasoning goals
        """
        self.self_model = self_model
        self.consistency_checker = consistency_checker
        self.epistemic_engine = epistemic_engine
        self.history_window = history_window
        self.memory_manager = memory_manager
        self.z3_validator = z3_validator
        self.fact_checker = fact_checker
        self.goal_manager = goal_manager
        
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
        
        # Commitment tracking (Festinger: commitment strength amplifies dissonance)
        # Tracks how invested the system is in specific cognitions
        self._commitment_strength: Dict[str, float] = {}  # cognition_id -> commitment (0.0-1.0)
        self._commitment_history: deque = deque(maxlen=history_window)
        
        # Dissonance reduction strategies tracking
        self._reduction_strategies: deque = deque(maxlen=history_window)
        
        # Signal manager for damping (optional)
        self._signal_manager: Optional[Any] = None
        
        logger.info("Initialized CognitiveDissonanceMonitor (with commitment tracking)")
    
    def track_commitment(
        self,
        cognition_id: str,
        commitment_strength: float,
        evidence: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track commitment strength to a cognition (Festinger's commitment principle).
        
        Higher commitment to a cognition means dissonance from contradicting it
        will be stronger. Commitment can come from:
        - Public commitment (stated publicly)
        - Effort justification (invested effort/resources)
        - Choice justification (actively chose this cognition)
        - Time invested (long-held belief)
        
        Args:
            cognition_id: Identifier for the cognition (e.g., knowledge boundary ID)
            commitment_strength: Commitment strength (0.0-1.0)
            evidence: Optional evidence for commitment (effort, time, public, etc.)
        """
        self._commitment_strength[cognition_id] = max(0.0, min(1.0, commitment_strength))
        self._commitment_history.append({
            "cognition_id": cognition_id,
            "commitment": commitment_strength,
            "evidence": evidence or {},
            "timestamp": datetime.now(timezone.utc)
        })
        logger.debug(f"Tracked commitment for {cognition_id}: {commitment_strength:.3f}")
    
    def get_commitment(self, cognition_id: str) -> float:
        """Get commitment strength for a cognition (0.0-1.0)."""
        return self._commitment_strength.get(cognition_id, 0.5)  # Default moderate commitment
    
    def record_reduction_strategy(
        self,
        strategy: str,
        effectiveness: float,
        component: str
    ) -> None:
        """
        Record dissonance reduction strategy and its effectiveness.
        
        Festinger: people use various strategies to reduce dissonance:
        - Change behavior
        - Change cognition
        - Add consonant cognitions
        - Reduce importance of dissonant cognitions
        
        Args:
            strategy: Strategy name (e.g., "change_behavior", "add_consonant_cognition")
            effectiveness: How effective the strategy was (0.0-1.0)
            component: Which component (logical, factual, behavioral, goal)
        """
        self._reduction_strategies.append({
            "strategy": strategy,
            "effectiveness": effectiveness,
            "component": component,
            "timestamp": datetime.now(timezone.utc)
        })
        logger.debug(f"Recorded reduction strategy: {strategy} (effectiveness={effectiveness:.3f})")
    
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
            f"goals={len(reasoning_goals) if reasoning_goals else 0}, "
            f"components: consistency_checker={self.consistency_checker is not None}, "
            f"fact_checker={self.fact_checker is not None}, "
            f"z3_validator={self.z3_validator is not None if self.z3_validator else False}, "
            f"memory_manager={self.memory_manager is not None}"
        )
        
        metrics = DissonanceMetrics(
            timestamp=datetime.now(timezone.utc),
            weight_logical=self.weight_logical,
            weight_factual=self.weight_factual,
            weight_behavioral=self.weight_behavioral,
            weight_goal=self.weight_goal,
            measurement_quality="measured",  # Default to measured, will update if unavailable
            has_sufficient_data=True,  # Default to True, will update if using fallbacks
        )
        
        # Measure logical dissonance (uses ConsistencyChecker)
        if response and self.consistency_checker:
            logical_dissonance = self._measure_logical_dissonance(response, conversation_context)
            if logical_dissonance is not None:
                metrics.logical_dissonance = logical_dissonance
                metrics.component_availability["logical"] = True
            else:
                # Measurement failed - use historical average or mark as unavailable
                metrics.logical_dissonance = self._get_average_logical_dissonance()
                metrics.component_availability["logical"] = len(self.logical_violations) > 0
                if not metrics.component_availability["logical"]:
                    metrics.measurement_quality = "error"
                    metrics.has_sufficient_data = False
        else:
            # Use historical average if no current measurement
            metrics.logical_dissonance = self._get_average_logical_dissonance()
            metrics.component_availability["logical"] = len(self.logical_violations) > 0
            if not metrics.component_availability["logical"]:
                metrics.measurement_quality = "estimated"
                metrics.has_sufficient_data = False
        
        # Measure factual dissonance
        if response:
            factual_dissonance = self._measure_factual_dissonance(response)
            if factual_dissonance is not None:
                metrics.factual_dissonance = factual_dissonance
                metrics.component_availability["factual"] = True
            else:
                # Measurement failed - use historical average or mark as unavailable
                metrics.factual_dissonance = self._get_average_factual_dissonance()
                metrics.component_availability["factual"] = len(self.factual_errors) > 0
                if not metrics.component_availability["factual"]:
                    metrics.measurement_quality = "error"
                    metrics.has_sufficient_data = False
        else:
            metrics.factual_dissonance = self._get_average_factual_dissonance()
            metrics.component_availability["factual"] = len(self.factual_errors) > 0
            if not metrics.component_availability["factual"]:
                metrics.measurement_quality = "estimated"
                metrics.has_sufficient_data = False
        
        # Measure behavioral dissonance
        # Try to extract tool_usage from conversation_context if not provided
        if not tool_usage and conversation_context:
            tool_usage = self._extract_tool_usage_from_context(conversation_context)
        
        if tool_usage:
            behavioral_dissonance = self._measure_behavioral_dissonance(tool_usage)
            if behavioral_dissonance is not None:
                metrics.behavioral_dissonance = behavioral_dissonance
                metrics.component_availability["behavioral"] = True
            else:
                # Measurement failed - use historical average or mark as unavailable
                metrics.behavioral_dissonance = self._get_average_behavioral_dissonance()
                metrics.component_availability["behavioral"] = len(self.behavioral_deviations) > 0
                if not metrics.component_availability["behavioral"]:
                    metrics.measurement_quality = "error"
                    metrics.has_sufficient_data = False
        else:
            metrics.behavioral_dissonance = self._get_average_behavioral_dissonance()
            metrics.component_availability["behavioral"] = len(self.behavioral_deviations) > 0
            if not metrics.component_availability["behavioral"]:
                metrics.measurement_quality = "estimated"
                metrics.has_sufficient_data = False
        
        # Measure goal-based dissonance
        # Try to extract reasoning_goals from goal_manager if not provided
        if not reasoning_goals and self.goal_manager:
            reasoning_goals = self._extract_reasoning_goals_from_goal_manager()
        
        if reasoning_goals:
            goal_dissonance = self._measure_goal_dissonance(reasoning_goals)
            if goal_dissonance is not None:
                metrics.goal_dissonance = goal_dissonance
                metrics.component_availability["goal"] = True
            else:
                # Measurement failed - use historical average or mark as unavailable
                metrics.goal_dissonance = self._get_average_goal_dissonance()
                metrics.component_availability["goal"] = len(self.goal_conflicts) > 0
                if not metrics.component_availability["goal"]:
                    metrics.measurement_quality = "error"
                    metrics.has_sufficient_data = False
        else:
            metrics.goal_dissonance = self._get_average_goal_dissonance()
            metrics.component_availability["goal"] = len(self.goal_conflicts) > 0
            if not metrics.component_availability["goal"]:
                metrics.measurement_quality = "estimated"
                metrics.has_sufficient_data = False
        
        # If no components have data, mark as unavailable
        if not any(metrics.component_availability.values()):
            metrics.measurement_quality = "unavailable"
            metrics.has_sufficient_data = False
        
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
                f"behavioral={metrics.behavioral_dissonance:.3f}, goal={metrics.goal_dissonance:.3f}, "
                f"quality={metrics.measurement_quality}, has_sufficient_data={metrics.has_sufficient_data}"
            )
        else:
            logger.debug(
                f"Measured dissonance: overall={metrics.overall_dissonance:.3f}, "
                f"logical={metrics.logical_dissonance:.3f}, factual={metrics.factual_dissonance:.3f}, "
                f"behavioral={metrics.behavioral_dissonance:.3f}, goal={metrics.goal_dissonance:.3f}, "
                f"quality={metrics.measurement_quality}, has_sufficient_data={metrics.has_sufficient_data}, "
                f"components_available={metrics.component_availability}"
            )
        
        return metrics
    
    def _measure_logical_dissonance(
        self,
        response: str,
        conversation_context: Optional[List[Dict[str, str]]]
    ) -> Optional[float]:
        """
        Measure logical dissonance using ConsistencyChecker.
        
        Based on Festinger's cognitive dissonance theory: measures discomfort from
        contradictions between stated capabilities/knowledge boundaries and actual responses.
        
        Returns:
            Dissonance score (0.0 = consistent, 1.0 = highly inconsistent), or None if measurement unavailable
        """
        if not self.consistency_checker:
            logger.debug("Logical dissonance measurement skipped: consistency_checker not available")
            return None
        
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
            logger.warning(f"Failed to measure logical dissonance: {e}. Returning None (measurement unavailable)", exc_info=True)
            return None  # Return None to indicate measurement failure, not zero dissonance
    
    def _measure_factual_dissonance(self, response: str) -> Optional[float]:
        """
        Measure factual dissonance (claims vs. knowledge boundaries).
        
        Based on Festinger's cognitive dissonance theory: measures discomfort from
        contradictions between factual claims and established knowledge boundaries.
        Uses ratio of dissonant to consonant cognitions (Festinger's key principle).
        
        Returns:
            Dissonance score (0.0 = no contradictions, 1.0 = severe contradictions), or None if measurement unavailable
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
                                conf = context["confidence_metrics"].get("overall_confidence")
                                if conf is not None:
                                    confidence_scores.append(conf)
                                else:
                                    # No confidence in metrics - use assess_source_reliability() instead of hardcoded 0.5
                                    if hasattr(self.epistemic_engine, 'validator'):
                                        try:
                                            from ..self_model.epistemic.models import SourceType, SourceMetadata
                                            # Get source from knowledge boundary
                                            source_dict = value_dict.get("source", {})
                                            if source_dict:
                                                source_type = SourceType(source_dict.get("source_type", SourceType.SYSTEM_DEFAULT))
                                                source = SourceMetadata(
                                                    source_type=source_type,
                                                    timestamp=datetime.now(timezone.utc)
                                                )
                                                assessed_reliability = self.epistemic_engine.validator.assess_source_reliability(source)
                                                confidence_scores.append(assessed_reliability)
                                                logger.debug(f"Used assessed source reliability ({assessed_reliability:.3f}) instead of hardcoded 0.5 for knowledge boundary confidence")
                                        except Exception as e2:
                                            logger.debug(f"Error assessing source reliability for knowledge boundary: {e2}")
                        except Exception:
                            pass
                    
                    if confidence_scores:
                        avg_confidence = sum(confidence_scores) / len(confidence_scores)
                        # Higher confidence knowledge boundaries -> stronger dissonance signal when violated
                        # Festinger: importance of conflicting elements amplifies dissonance
                        confidence_weight = 0.8 + (avg_confidence * 0.4)  # Range: 0.8-1.2
                        dissonance_score = min(1.0, dissonance_score * confidence_weight)
                    else:
                        # No confidence scores available - use assess_source_reliability() instead of hardcoded 0.5
                        if hasattr(self.epistemic_engine, 'validator'):
                            try:
                                from ..self_model.epistemic.models import SourceType, SourceMetadata
                                # Create a default source to assess reliability
                                default_source = SourceMetadata(
                                    source_type=SourceType.SYSTEM_DEFAULT,
                                    timestamp=datetime.now(timezone.utc)
                                )
                                assessed_reliability = self.epistemic_engine.validator.assess_source_reliability(default_source)
                                # Use assessed reliability as confidence weight (instead of hardcoded 0.5)
                                confidence_weight = 0.8 + (assessed_reliability * 0.4)  # Range: 0.8-1.2
                                dissonance_score = min(1.0, dissonance_score * confidence_weight)
                                logger.debug(f"Used assessed source reliability ({assessed_reliability:.3f}) instead of hardcoded 0.5 for factual dissonance weighting")
                            except Exception as e:
                                logger.debug(f"Error assessing source reliability for factual dissonance: {e}")
                except Exception as e:
                    logger.debug(f"Error weighting factual dissonance by epistemic confidence: {e}")
            
            # Apply Festinger's ratio principle: dissonance magnitude depends on ratio of dissonant to consonant cognitions
            # Improved formula: dissonance = dissonant / (dissonant + consonant)
            if dissonant_elements > 0 or consonant_elements > 0:
                total_elements = dissonant_elements + consonant_elements
                if total_elements > 0:
                    # Festinger's ratio: dissonant/(dissonant + consonant)
                    # This gives higher weight when dissonant elements dominate
                    dissonance_ratio = dissonant_elements / (dissonant_elements + consonant_elements)
                    
                    # Apply commitment weighting: higher commitment to violated cognitions amplifies dissonance
                    commitment_weight = 1.0
                    if violations and self._commitment_strength:
                        # Check commitment to violated knowledge boundaries
                        avg_commitment = 0.0
                        commitment_count = 0
                        for violation in violations:
                            if violation.get("type") == "knowledge_boundary":
                                # Estimate commitment based on how long knowledge boundary has existed
                                # (simplified: use epistemic confidence as proxy)
                                commitment_count += 1
                                avg_commitment += 0.7  # Default moderate commitment
                        if commitment_count > 0:
                            avg_commitment /= commitment_count
                            # Commitment amplifies dissonance: 1.0 + commitment
                            commitment_weight = 1.0 + (avg_commitment * 0.5)  # Range: 1.0-1.5
                    
                    # Combine base score with ratio-based adjustment, weighted by commitment
                    # Festinger: ratio is primary, but commitment amplifies
                    ratio_adjusted_score = (dissonance_score * 0.6) + (dissonance_ratio * 0.4)
                    ratio_adjusted_score *= commitment_weight
                    dissonance_score = min(1.0, max(dissonance_score, ratio_adjusted_score))
                    logger.debug(
                        f"Factual dissonance ratio: {dissonant_elements}/({dissonant_elements}+{consonant_elements}) = {dissonance_ratio:.3f}, "
                        f"commitment_weight={commitment_weight:.3f}, adjusted score: {dissonance_score:.3f}"
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
            logger.warning(f"Failed to measure factual dissonance: {e}. Returning None (measurement unavailable)", exc_info=True)
            # Return None to indicate measurement failure, not zero dissonance
            return None
    
    def _measure_behavioral_dissonance(self, tool_usage: List[Dict[str, Any]]) -> Optional[float]:
        """
        Measure behavioral dissonance (tool usage vs. stated patterns).
        
        Based on Festinger's cognitive dissonance theory: measures discomfort from
        actions that contradict stated behavioral patterns, preferences, or constraints.
        
        Returns:
            Dissonance score (0.0 = aligned behavior, 1.0 = severe behavioral deviation), or None if measurement unavailable
        """
        try:
            if not tool_usage:
                return None
            
            # Track violations and counts for ratio-based calculation
            violations: List[Dict[str, Any]] = []
            dissonant_actions = 0
            consonant_actions = 0
            violation_severities: List[float] = []
            
            # Extract capabilities and constraints from self model
            capabilities = [cap.get("text", str(cap)) for cap in self.self_model.capabilities]
            constraints = self.self_model.constraints
            
            # If no capabilities listed, can't measure deviation
            if not capabilities:
                return None
            
            capability_text = " ".join(capabilities).lower()
            constraint_values = [v.get("value", str(v)).lower() for v in constraints.values()]
            constraint_text = " ".join(constraint_values).lower()
            
            # Track tool usage frequency for pattern analysis
            tool_counts: Dict[str, int] = {}
            
            # Analyze each tool usage
            for tool_call in tool_usage:
                tool_name = tool_call.get("function", {}).get("name", "") if isinstance(tool_call, dict) else str(tool_call)
                if not tool_name:
                    continue
                
                tool_name_lower = tool_name.lower()
                tool_counts[tool_name_lower] = tool_counts.get(tool_name_lower, 0) + 1
                
                # Track if this action has any violation
                action_has_violation = False
                action_violation_severity = 0.0
                
                # Enhanced capability matching - check for semantic similarity
                # Split tool name into words for better matching
                tool_words = set(tool_name_lower.split("_"))
                tool_mentioned = False
                for cap in capabilities:
                    cap_lower = cap.lower()
                    cap_words = set(cap_lower.split())
                    # Check for word overlap (semantic similarity)
                    if tool_words & cap_words:  # Intersection of word sets
                        tool_mentioned = True
                        break
                    # Also check substring matches
                    if tool_name_lower in cap_lower or cap_lower in tool_name_lower:
                        tool_mentioned = True
                        break
                
                # Check for constraint violations with enhanced detection
                constraint_violation = False
                violation_type = None
                violation_severity = 0.0
                
                # Check for read-only constraint violations
                if "read-only" in constraint_text or "read only" in constraint_text:
                    # Check if tool is a write operation (more comprehensive list)
                    write_keywords = ["write", "create", "update", "delete", "modify", "edit", "save", "store", 
                                     "remove", "add", "insert", "append", "change", "alter", "set"]
                    if any(keyword in tool_name_lower for keyword in write_keywords):
                        constraint_violation = True
                        violation_type = "read_only_violation"
                        violation_severity = 0.8
                
                # Check for other constraint violations
                # Look for explicit tool restrictions in constraints
                for constraint_value in constraint_values:
                    constraint_lower = constraint_value.lower()
                    # Check if constraint explicitly mentions this tool or tool category
                    if tool_name_lower in constraint_lower or any(word in constraint_lower for word in tool_words):
                        # Check if it's a restriction (contains words like "not", "avoid", "prohibit", "forbid")
                        restriction_keywords = ["not", "avoid", "prohibit", "forbid", "never", "don't", "do not"]
                        if any(keyword in constraint_lower for keyword in restriction_keywords):
                            constraint_violation = True
                            violation_type = "explicit_constraint_violation"
                            violation_severity = max(violation_severity, 0.9)  # Very high for explicit violations
                
                # Record constraint violations
                if constraint_violation:
                    action_has_violation = True
                    action_violation_severity = max(action_violation_severity, violation_severity)
                    violations.append({
                        "type": violation_type,
                        "tool": tool_name,
                        "severity": violation_severity,
                        "description": f"Tool {tool_name} violates constraint: {violation_type}"
                    })
                
                # Check for capability mismatch (only if no constraint violation)
                if not tool_mentioned and not constraint_violation:
                    # Tool not mentioned in capabilities - potential deviation
                    # Lower severity if tool seems reasonable (common tools)
                    common_tools = ["read", "search", "get", "fetch", "list", "find", "query"]
                    is_common = any(common in tool_name_lower for common in common_tools)
                    severity = 0.2 if is_common else 0.4  # Lower for common tools
                    action_has_violation = True
                    action_violation_severity = max(action_violation_severity, severity)
                    violations.append({
                        "type": "capability_mismatch",
                        "tool": tool_name,
                        "severity": severity,
                        "description": f"Tool {tool_name} not mentioned in stated capabilities"
                    })
                
                # Count as dissonant or consonant
                if action_has_violation:
                    dissonant_actions += 1
                    violation_severities.append(action_violation_severity)
                else:
                    consonant_actions += 1
            
            # Analyze tool usage patterns for additional insights
            # Check for excessive use of same tool (might indicate inefficiency)
            pattern_violation_severity = 0.0
            if len(tool_counts) > 0:
                max_count = max(tool_counts.values())
                total_tools = len(tool_usage)
                if max_count > total_tools * 0.5 and total_tools > 3:
                    # More than 50% of tools are the same - potential inefficiency
                    most_used = [name for name, count in tool_counts.items() if count == max_count][0]
                    pattern_violation_severity = 0.2  # Low severity for pattern issues
                    violations.append({
                        "type": "inefficient_pattern",
                        "tool": most_used,
                        "severity": pattern_violation_severity,
                        "description": f"Excessive use of tool {most_used} ({max_count}/{total_tools} calls)"
                    })
                    # Pattern violations are counted separately (they affect overall pattern, not individual actions)
                    # Add to severity list but don't double-count actions
            
            # Calculate ratio-based dissonance score (Festinger's principle)
            total_actions = dissonant_actions + consonant_actions
            if total_actions == 0:
                return 0.0
            
            # Calculate average severity of violations
            avg_severity = 0.0
            if violation_severities:
                avg_severity = sum(violation_severities) / len(violation_severities)
            
            # Include pattern violation in average if present
            if pattern_violation_severity > 0.0:
                if violation_severities:
                    avg_severity = (sum(violation_severities) + pattern_violation_severity) / (len(violation_severities) + 1)
                else:
                    avg_severity = pattern_violation_severity
            
            # Calculate dissonance ratio: proportion of dissonant actions
            dissonance_ratio = dissonant_actions / total_actions
            
            # Apply commitment weighting if available (higher commitment amplifies dissonance)
            commitment_weight = 1.0
            if violations and self._commitment_strength:
                # Check commitment to violated constraints/capabilities
                avg_commitment = 0.0
                commitment_count = 0
                for violation in violations:
                    if violation.get("type") in ["read_only_violation", "explicit_constraint_violation"]:
                        commitment_count += 1
                        avg_commitment += 0.7  # Default moderate commitment to constraints
                if commitment_count > 0:
                    avg_commitment /= commitment_count
                    commitment_weight = 1.0 + (avg_commitment * 0.5)  # Range: 1.0-1.5
            
            # Combine base severity average with ratio (Festinger's approach)
            # 60% weight on severity, 40% weight on ratio
            base_score = (avg_severity * 0.6) + (dissonance_ratio * 0.4)
            
            # Apply commitment weighting
            deviation_score = min(1.0, base_score * commitment_weight)
            
            logger.debug(
                f"Behavioral dissonance: {dissonant_actions}/{total_actions} actions dissonant (ratio={dissonance_ratio:.3f}), "
                f"avg_severity={avg_severity:.3f}, commitment_weight={commitment_weight:.3f}, "
                f"final_score={deviation_score:.3f}"
            )
            
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
            
            # Track deviations (only if there were violations, or if we have a non-zero score)
            if violations or deviation_score > 0.0:
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
            logger.warning(f"Failed to measure behavioral dissonance: {e}. Returning None (measurement unavailable)", exc_info=True)
            # Return None to indicate measurement failure, not zero dissonance
            return None
    
    def _measure_goal_dissonance(self, reasoning_goals: List[Dict[str, Any]]) -> Optional[float]:
        """
        Measure goal-based dissonance (reasoning goals vs. self-model objectives).
        
        Based on Festinger's cognitive dissonance theory: measures discomfort from
        goals/actions that conflict with self-model objectives, constraints, or capabilities.
        
        Returns:
            Dissonance score (0.0 = aligned goals, 1.0 = severe goal conflicts), or None if measurement unavailable
        """
        try:
            if not reasoning_goals:
                return None
            
            # Track violations and counts for ratio-based calculation
            violations: List[Dict[str, Any]] = []
            conflicting_goals = 0
            aligned_goals = 0
            conflict_severities: List[float] = []
            goal_priorities: List[float] = []  # For importance weighting
            
            # Extract constraints and capabilities from self model
            constraints = self.self_model.constraints
            constraint_values = [v.get("value", str(v)).lower() for v in constraints.values()]
            constraint_text = " ".join(constraint_values).lower()
            capabilities = [cap.get("text", str(cap)).lower() for cap in self.self_model.capabilities]
            capability_text = " ".join(capabilities).lower()
            
            # Extract self-model objectives (if available in metadata or constraints)
            # Objectives might be in constraints with key "objectives" or in metadata
            objectives = []
            if "objectives" in constraints:
                obj_value = constraints["objectives"]
                if isinstance(obj_value, dict):
                    objectives.append(obj_value.get("value", "").lower())
                else:
                    objectives.append(str(obj_value).lower())
            
            # Convert reasoning goals to a standard format for analysis
            goals_to_check: List[Dict[str, Any]] = []
            try:
                from .goal_manager import Goal, GoalType, GoalStatus
                
                for goal_item in reasoning_goals:
                    if isinstance(goal_item, Goal):
                        goals_to_check.append({
                            "name": goal_item.name,
                            "description": goal_item.description,
                            "goal_type": getattr(goal_item, 'goal_type', None),
                            "status": getattr(goal_item, 'status', None),
                            "priority": getattr(goal_item, 'priority', 0.5),
                            "dependencies": getattr(goal_item, 'dependencies', [])
                        })
                    elif isinstance(goal_item, dict):
                        goals_to_check.append(goal_item)
            except Exception as e:
                logger.debug(f"Error converting goals: {e}")
                # Fallback: use goals as-is if conversion fails
                goals_to_check = [g if isinstance(g, dict) else {"name": str(g), "description": str(g)} 
                                 for g in reasoning_goals]
            
            # Track if there's a goal dependency conflict (affects all goals)
            has_goal_dependency_conflict = False
            dependency_conflict_severity = 0.0
            
            # Use Z3 to check if goals conflict with constraints (if available)
            if self.z3_validator and self.z3_validator.enabled and goals_to_check:
                try:
                    from .goal_manager import Goal, GoalType, GoalStatus
                    
                    # Convert to Goal objects for Z3 validation
                    goal_objects: List[Goal] = []
                    for goal_dict in goals_to_check:
                        try:
                            goal = Goal(
                                name=goal_dict.get("name", "unknown"),
                                description=goal_dict.get("description", str(goal_dict)),
                                goal_type=GoalType(goal_dict.get("goal_type", "achieve")),
                                status=GoalStatus(goal_dict.get("status", "active")),
                                priority=goal_dict.get("priority", 0.5),
                                dependencies=goal_dict.get("dependencies", [])
                            )
                            goal_objects.append(goal)
                        except Exception:
                            continue
                    
                    if goal_objects:
                        # Validate goal dependencies
                        is_valid, error, warnings = self.z3_validator.validate_goal_dependencies(goal_objects)
                        
                        if not is_valid:
                            has_goal_dependency_conflict = True
                            dependency_conflict_severity = 0.7  # High conflict for unsatisfiable goals
                            violations.append({
                                "type": "goal_dependency_conflict",
                                "severity": dependency_conflict_severity,
                                "error": error,
                                "description": f"Goal dependencies are unsatisfiable: {error}"
                            })
                except Exception as e:
                    logger.debug(f"Error in Z3 goal validation: {e}")
            
            # Check each goal against constraints and capabilities
            for goal_dict in goals_to_check:
                goal_name = goal_dict.get("name", "unknown")
                goal_description = goal_dict.get("description", str(goal_dict))
                goal_text = f"{goal_name} {goal_description}".lower()
                goal_words = set(goal_text.split())
                goal_priority = goal_dict.get("priority", 0.5)  # Default medium priority
                
                # Track if this goal has any conflict
                goal_has_conflict = False
                goal_conflict_severity = 0.0
                
                # Check for constraint violations with enhanced detection
                for constraint_value in constraint_values:
                    constraint_lower = constraint_value.lower()
                    
                    # Check for explicit constraint violations
                    # Read-only violations
                    if "read-only" in constraint_lower or "read only" in constraint_lower:
                        write_keywords = ["write", "modify", "edit", "change", "update", "delete", "create"]
                        if any(keyword in goal_text for keyword in write_keywords):
                            goal_has_conflict = True
                            goal_conflict_severity = max(goal_conflict_severity, 0.8)
                            violations.append({
                                "type": "constraint_violation",
                                "goal": goal_name,
                                "constraint": constraint_value,
                                "severity": 0.8,
                                "description": f"Goal {goal_name} violates read-only constraint"
                            })
                    
                    # Check for explicit restrictions in constraints
                    restriction_keywords = ["not", "avoid", "prohibit", "forbid", "never", "don't", "do not"]
                    if any(keyword in constraint_lower for keyword in restriction_keywords):
                        # Check if goal mentions something that's restricted
                        constraint_words = set(constraint_lower.split())
                        if goal_words & constraint_words:  # Word overlap
                            goal_has_conflict = True
                            goal_conflict_severity = max(goal_conflict_severity, 0.9)  # Very high for explicit restrictions
                            violations.append({
                                "type": "explicit_constraint_violation",
                                "goal": goal_name,
                                "constraint": constraint_value,
                                "severity": 0.9,
                                "description": f"Goal {goal_name} violates explicit restriction: {constraint_value}"
                            })
                
                # Check for capability mismatches with enhanced semantic matching
                if capabilities:
                    # Check for word overlap between goal and capabilities
                    capability_words = set()
                    for cap in capabilities:
                        capability_words.update(cap.split())
                    
                    goal_capability_overlap = goal_words & capability_words
                    goal_mentions_capability = len(goal_capability_overlap) > 0
                    
                    # Also check substring matches
                    if not goal_mentions_capability:
                        goal_mentions_capability = any(cap in goal_text or goal_text in cap for cap in capabilities)
                    
                    # Only flag mismatch if goal is substantial and clearly doesn't align
                    if not goal_mentions_capability and len(goal_text) > 15:
                        # Check if goal seems reasonable (common goal patterns)
                        common_goal_patterns = ["help", "assist", "provide", "answer", "find", "search", "get", "retrieve"]
                        is_common = any(pattern in goal_text for pattern in common_goal_patterns)
                        severity = 0.3 if is_common else 0.5  # Lower for common patterns
                        goal_has_conflict = True
                        goal_conflict_severity = max(goal_conflict_severity, severity)
                        violations.append({
                            "type": "capability_mismatch",
                            "goal": goal_name,
                            "severity": severity,
                            "description": f"Goal {goal_name} doesn't align with stated capabilities"
                        })
                
                # Check goal alignment with objectives (if available)
                if objectives:
                    objective_text = " ".join(objectives).lower()
                    objective_words = set(objective_text.split())
                    goal_objective_overlap = goal_words & objective_words
                    if len(goal_objective_overlap) == 0 and len(goal_text) > 20:
                        # Goal doesn't align with stated objectives
                        goal_has_conflict = True
                        goal_conflict_severity = max(goal_conflict_severity, 0.4)
                        violations.append({
                            "type": "objective_mismatch",
                            "goal": goal_name,
                            "severity": 0.4,
                            "description": f"Goal {goal_name} doesn't align with stated objectives"
                        })
                
                # Count goal as conflicting or aligned
                if goal_has_conflict:
                    conflicting_goals += 1
                    conflict_severities.append(goal_conflict_severity)
                    goal_priorities.append(goal_priority)
                else:
                    aligned_goals += 1
            
            # Calculate ratio-based dissonance score (Festinger's principle)
            total_goals = conflicting_goals + aligned_goals
            if total_goals == 0:
                return 0.0
            
            # Handle dependency conflicts (affect all goals)
            if has_goal_dependency_conflict:
                # Dependency conflicts mean all goals are in conflict
                conflicting_goals = total_goals
                aligned_goals = 0
            
            # Calculate weighted average severity of conflicts (weighted by goal priority)
            avg_severity = 0.0
            
            # Collect all severities including dependency conflict
            all_severities = list(conflict_severities) if conflict_severities else []
            if has_goal_dependency_conflict:
                all_severities.append(dependency_conflict_severity)
            
            if all_severities:
                if goal_priorities and len(goal_priorities) == len(conflict_severities):
                    # Weight severities by goal priority (higher priority = more weight)
                    # Include dependency conflict with average priority weight
                    weighted_sum = sum(sev * (1.0 + priority) for sev, priority in zip(conflict_severities, goal_priorities))
                    if has_goal_dependency_conflict:
                        avg_priority = sum(goal_priorities) / len(goal_priorities) if goal_priorities else 0.5
                        weighted_sum += dependency_conflict_severity * (1.0 + avg_priority)
                        weight_sum = sum(1.0 + priority for priority in goal_priorities) + (1.0 + avg_priority)
                    else:
                        weight_sum = sum(1.0 + priority for priority in goal_priorities)
                    avg_severity = weighted_sum / weight_sum
                else:
                    # Fallback to simple average if no priorities available
                    avg_severity = sum(all_severities) / len(all_severities)
            
            # Calculate dissonance ratio: proportion of conflicting goals
            dissonance_ratio = conflicting_goals / total_goals
            
            # Apply importance weighting (high-priority goal conflicts weigh more)
            importance_weight = 1.0
            if goal_priorities:
                avg_priority = sum(goal_priorities) / len(goal_priorities)
                # Higher priority amplifies dissonance: 1.0 + (priority * 0.5), range 1.0-1.5
                importance_weight = 1.0 + (avg_priority * 0.5)
            
            # Combine base severity average with ratio (Festinger's approach)
            # 60% weight on severity, 40% weight on ratio
            base_score = (avg_severity * 0.6) + (dissonance_ratio * 0.4)
            
            # Apply importance weighting
            conflict_score = min(1.0, base_score * importance_weight)
            
            logger.debug(
                f"Goal dissonance: {conflicting_goals}/{total_goals} goals conflicting (ratio={dissonance_ratio:.3f}), "
                f"avg_severity={avg_severity:.3f}, importance_weight={importance_weight:.3f}, "
                f"final_score={conflict_score:.3f}"
            )
            
            # Track conflicts (only if there were violations, or if we have a non-zero score)
            if violations or conflict_score > 0.0:
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
            logger.warning(f"Failed to measure goal dissonance: {e}. Returning None (measurement unavailable)", exc_info=True)
            # Return None to indicate measurement failure, not zero dissonance
            return None
    
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
        """
        Get aggregated dissonance metrics from history.
        
        Returns:
            Dictionary with aggregated metrics. If no history, returns structure indicating
            "insufficient data" rather than zero values (which would imply "no dissonance").
        """
        if len(self.dissonance_history) == 0:
            return {
                "overall_dissonance": 0.0,
                "logical_dissonance": 0.0,
                "factual_dissonance": 0.0,
                "behavioral_dissonance": 0.0,
                "goal_dissonance": 0.0,
                "samples": 0,
                "has_data": False,  # Indicates insufficient data vs. zero dissonance
                "measurement_quality": "unavailable",
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
        
        # Determine measurement quality from latest measurement
        latest_metrics = self.dissonance_history[-1]
        measurement_quality = latest_metrics.measurement_quality or "measured"
        has_sufficient_data = latest_metrics.has_sufficient_data if hasattr(latest_metrics, 'has_sufficient_data') else True
        
        return {
            "overall_dissonance": avg_overall,
            "logical_dissonance": avg_logical,
            "factual_dissonance": avg_factual,
            "behavioral_dissonance": avg_behavioral,
            "goal_dissonance": avg_goal,
            "trend": trend,  # Positive = increasing, negative = decreasing
            "samples": len(self.dissonance_history),
            "has_data": True,  # We have history data
            "measurement_quality": measurement_quality,
            "has_sufficient_data": has_sufficient_data,
            "component_availability": latest_metrics.component_availability if hasattr(latest_metrics, 'component_availability') else {
                "logical": True,
                "factual": True,
                "behavioral": True,
                "goal": True,
            },
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
    
    @staticmethod
    def extract_tool_usage_from_messages(messages: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Extract tool usage from conversation messages.
        
        Args:
            messages: List of conversation messages
            limit: Maximum number of messages to check (from end)
            
        Returns:
            List of tool calls extracted from messages
        """
        tool_usage = []
        for msg in messages[-limit:]:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tool_usage.extend(msg.get("tool_calls", []))
        return tool_usage
    
    def _extract_tool_usage_from_context(self, conversation_context: List[Dict[str, str]]) -> Optional[List[Dict[str, Any]]]:
        """
        Extract tool usage from conversation context.
        
        Args:
            conversation_context: List of conversation context dictionaries
            
        Returns:
            List of tool calls if found, None otherwise
        """
        try:
            # Look for tool_calls in context messages
            tool_usage = []
            for msg in conversation_context:
                if isinstance(msg, dict) and msg.get("role") == "assistant":
                    # Check if message has tool_calls (might be in different format)
                    if "tool_calls" in msg:
                        tool_calls = msg.get("tool_calls", [])
                        if isinstance(tool_calls, list):
                            tool_usage.extend(tool_calls)
            return tool_usage if tool_usage else None
        except Exception as e:
            logger.debug(f"Error extracting tool usage from context: {e}")
            return None
    
    def _extract_reasoning_goals_from_goal_manager(self) -> Optional[List[Dict[str, Any]]]:
        """
        Extract active reasoning goals from GoalManager.
        
        Returns:
            List of goal dictionaries if found, None otherwise
        """
        try:
            if not self.goal_manager:
                return None
            
            # Get active goals from goal manager
            if hasattr(self.goal_manager, 'get_active_goals'):
                active_goals = self.goal_manager.get_active_goals()
                if active_goals:
                    # Convert Goal objects to dictionaries
                    goals_list = []
                    for goal in active_goals:
                        if hasattr(goal, 'name') and hasattr(goal, 'description'):
                            goals_list.append({
                                "name": goal.name,
                                "description": goal.description,
                                "goal_type": getattr(goal, 'goal_type', None),
                                "status": getattr(goal, 'status', None),
                                "priority": getattr(goal, 'priority', 0.5),
                                "dependencies": getattr(goal, 'dependencies', [])
                            })
                    return goals_list if goals_list else None
            return None
        except Exception as e:
            logger.debug(f"Error extracting reasoning goals from goal manager: {e}")
            return None
    
    @staticmethod
    def extract_conversation_context(messages: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, str]]:
        """
        Extract conversation context from messages.
        
        Args:
            messages: List of conversation messages
            limit: Maximum number of messages to include (from end)
            
        Returns:
            List of formatted conversation context dictionaries
        """
        return [
            {"role": m.get("role", "unknown"), "content": (m.get("content") or "")[:200]}
            for m in messages[-limit:]
        ]
    
    def measure_dissonance_from_conversation(
        self,
        response: str,
        messages: List[Dict[str, Any]],
        reasoning_goals: Optional[List[Dict[str, Any]]] = None,
        emotional_context: Optional[Dict[str, float]] = None
    ) -> DissonanceMetrics:
        """
        Measure dissonance from conversation context (helper method to reduce duplication).
        
        Args:
            response: LLM response text
            messages: Full conversation message history
            reasoning_goals: Optional reasoning goals
            emotional_context: Optional emotional state
            
        Returns:
            DissonanceMetrics with measurement results
        """
        tool_usage = self.extract_tool_usage_from_messages(messages)
        conversation_context = self.extract_conversation_context(messages)
        
        return self.measure_dissonance(
            response=response,
            conversation_context=conversation_context,
            tool_usage=tool_usage if tool_usage else None,
            reasoning_goals=reasoning_goals,
            emotional_context=emotional_context
        )

