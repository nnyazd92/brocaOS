"""
Cognitive dissonance measurement system.

Measures multi-dimensional drift from self-model:
- Logical dissonance: Contradictions with capabilities/knowledge boundaries
- Factual dissonance: Claims contradicting self-model facts
- Behavioral dissonance: Actions not matching stated preferences/patterns
- Goal-based dissonance: Goals/actions not aligned with self-model objectives
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
        weight_goal: float = 0.2
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
        """
        self.self_model = self_model
        self.consistency_checker = consistency_checker
        self.epistemic_engine = epistemic_engine
        self.history_window = history_window
        
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

        Args:
            response: Optional LLM response to check
            conversation_context: Optional conversation context for consistency checking
            tool_usage: Optional list of tool usage patterns
            reasoning_goals: Optional list of reasoning system goals
            emotional_context: Optional emotional state dictionary (affects dissonance sensitivity)
            
        Returns:
            DissonanceMetrics with all component scores
        """
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
        """Measure logical dissonance using ConsistencyChecker."""
        if not self.consistency_checker:
            return 0.0
        
        try:
            consistency_result = self.consistency_checker.validate(
                response=response,
                self_model=self.self_model,
                conversation_context=conversation_context
            )
            
            # Logical dissonance is the severity score (0.0 = consistent, 1.0 = highly inconsistent)
            dissonance = consistency_result.severity
            
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
            logical_violations = [
                v for v in consistency_result.violations
                if v.get("type") == "logical"
            ]
            if logical_violations:
                self.logical_violations.append({
                    "timestamp": datetime.now(timezone.utc),
                    "violations": logical_violations,
                    "severity": dissonance
                })
            
            return dissonance
            
        except Exception as e:
            logger.error(f"Error measuring logical dissonance: {e}", exc_info=True)
            return 0.0  # Default to no dissonance on error
    
    def _measure_factual_dissonance(self, response: str) -> float:
        """Measure factual dissonance (claims vs. knowledge boundaries) with epistemic weighting."""
        try:
            # Extract knowledge boundaries from self model
            knowledge_boundaries = self.self_model.knowledge_boundaries
            
            # Use historical average of factual errors as base
            base_dissonance = 0.0
            if len(self.factual_errors) > 0:
                base_dissonance = sum(e.get("severity", 0.0) for e in self.factual_errors) / len(self.factual_errors)
            
            # Weight by epistemic confidence if available
            if self.epistemic_engine and self.self_model.epistemic_layer and knowledge_boundaries:
                try:
                    # Get average confidence from knowledge boundaries
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
                        confidence_weight = 0.8 + (avg_confidence * 0.4)  # Range: 0.8-1.2
                        base_dissonance = min(1.0, base_dissonance * confidence_weight)
                except Exception as e:
                    logger.debug(f"Error weighting factual dissonance by epistemic confidence: {e}")
            
            # If no history, return 0 (no factual dissonance detected)
            return base_dissonance
            
        except Exception as e:
            logger.error(f"Error measuring factual dissonance: {e}", exc_info=True)
            return 0.0
    
    def _measure_behavioral_dissonance(self, tool_usage: List[Dict[str, Any]]) -> float:
        """Measure behavioral dissonance (tool usage vs. stated patterns)."""
        try:
            # Extract capabilities from self model
            capabilities = [cap.get("text", str(cap)) for cap in self.self_model.capabilities]
            capability_text = " ".join(capabilities).lower()
            
            # Simple heuristic: check if tool usage aligns with stated capabilities
            # Tools that aren't mentioned in capabilities might indicate behavioral drift
            
            # For now, use a simple pattern: if tools are used that don't align with capabilities
            # This is a simplified version - in practice, could analyze tool usage patterns more deeply
            
            # Track behavioral deviations
            deviation_score = 0.0
            
            # If no capabilities listed, can't measure deviation
            if not capabilities:
                return 0.0
            
            # Simple check: if tools are used, assume some alignment (refined later)
            # For now, return low default value
            deviation_score = 0.1  # Low default - refined in future iterations
            
            if deviation_score > 0.0:
                self.behavioral_deviations.append({
                    "timestamp": datetime.now(timezone.utc),
                    "tool_usage": tool_usage,
                    "deviation_score": deviation_score
                })
            
            return deviation_score
            
        except Exception as e:
            logger.error(f"Error measuring behavioral dissonance: {e}", exc_info=True)
            return 0.0
    
    def _measure_goal_dissonance(self, reasoning_goals: List[Dict[str, Any]]) -> float:
        """Measure goal-based dissonance (reasoning goals vs. self-model objectives)."""
        try:
            # Extract self-model objectives from capabilities and constraints
            capabilities = [cap.get("text", str(cap)) for cap in self.self_model.capabilities]
            
            # Simple heuristic: check if reasoning goals align with self-model capabilities/constraints
            # Goals that conflict with constraints indicate goal dissonance
            
            # Extract constraints
            constraints = self.self_model.constraints
            constraint_values = [v.get("value", str(v)) for v in constraints.values()]
            
            # For now, use a simple pattern: check if goals align with capabilities
            # This is simplified - in practice, could do semantic analysis
            
            # Track goal conflicts
            conflict_score = 0.0
            
            # If no goals, no conflict
            if not reasoning_goals:
                return 0.0
            
            # Simple check: assume some alignment (refined later)
            # For now, return low default value
            conflict_score = 0.05  # Low default - refined in future iterations
            
            if conflict_score > 0.0:
                self.goal_conflicts.append({
                    "timestamp": datetime.now(timezone.utc),
                    "goals": reasoning_goals,
                    "conflict_score": conflict_score
                })
            
            return conflict_score
            
        except Exception as e:
            logger.error(f"Error measuring goal dissonance: {e}", exc_info=True)
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

