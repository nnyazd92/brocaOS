"""
Self model feedback loop coordinator.

Coordinates between cognitive dissonance monitoring and self model updates,
managing periodic and threshold-based updates.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..self_model.model import SelfModel
    from ..self_model.updater import SelfModelUpdater
    from .cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics
    from ..tools.self_model_crud_tool import SelfModelCRUDTool

logger = logging.getLogger(__name__)


@dataclass
class UpdateRecord:
    """Record of a self model update."""
    timestamp: datetime
    old_dissonance: float
    new_dissonance: Optional[float] = None
    effectiveness: Optional[float] = None  # Improvement in dissonance
    update_reason: str = ""


class SelfModelFeedbackLoop:
    """
    Coordinates self model updates based on cognitive dissonance.
    
    Manages:
    - Periodic updates (scheduled intervals)
    - Threshold-based updates (when dissonance exceeds limits)
    - Update effectiveness tracking
    - Cooldown periods to prevent excessive updates
    """
    
    def __init__(
        self,
        self_model: "SelfModel",
        cognitive_dissonance_monitor: "CognitiveDissonanceMonitor",
        self_model_updater: Optional["SelfModelUpdater"] = None,
        self_model_crud_tool: Optional["SelfModelCRUDTool"] = None,
        update_cooldown_seconds: float = 300.0,
        periodic_update_interval_cycles: int = 10,
        dissonance_threshold: float = 0.3,
        critical_dissonance_threshold: float = 0.7,
        effectiveness_window: int = 20,
        use_crud_tool: bool = False
    ):
        """
        Initialize self model feedback loop.
        
        Args:
            self_model: SelfModel instance to update
            cognitive_dissonance_monitor: CognitiveDissonanceMonitor for measurements
            self_model_updater: Optional SelfModelUpdater for applying updates
            self_model_crud_tool: Optional SelfModelCRUDTool for CRUD-based updates
            update_cooldown_seconds: Minimum time between updates
            periodic_update_interval_cycles: Update every N cycles
            dissonance_threshold: Threshold for triggering updates
            critical_dissonance_threshold: Critical threshold for immediate updates
            effectiveness_window: Number of updates to track for effectiveness
            use_crud_tool: Whether to use CRUD tool instead of updater (default: False, uses updater)
        """
        self.self_model = self_model
        self.cognitive_dissonance_monitor = cognitive_dissonance_monitor
        self.self_model_updater = self_model_updater
        self.self_model_crud_tool = self_model_crud_tool
        self.use_crud_tool = use_crud_tool
        
        self.update_cooldown = update_cooldown_seconds
        self.periodic_interval = periodic_update_interval_cycles
        self.dissonance_threshold = dissonance_threshold
        self.critical_threshold = critical_dissonance_threshold
        self.effectiveness_window = effectiveness_window
        
        # Tracking
        self.last_update_time: Optional[float] = None
        self.update_count = 0
        self.update_history: deque = deque(maxlen=effectiveness_window)
        self.cycle_count_since_update = 0
        
        logger.info(f"Initialized SelfModelFeedbackLoop (use_crud_tool={use_crud_tool})")
    
    def should_update(
        self,
        dissonance_metrics: "DissonanceMetrics",
        force: bool = False
    ) -> bool:
        """
        Determine if self model should be updated.
        
        Args:
            dissonance_metrics: Current dissonance metrics
            force: Force update (ignore cooldown)
            
        Returns:
            True if update should be performed
        """
        current_time = time.time()
        overall_dissonance = dissonance_metrics.overall_dissonance
        
        # Force update always allowed
        if force:
            return True
        
        # Critical threshold: immediate update (if cooldown allows)
        if overall_dissonance > self.critical_threshold:
            if self._can_update(current_time):
                logger.warning(f"Critical dissonance ({overall_dissonance:.3f}), triggering immediate update")
                return True
        
        # Periodic update: check if interval reached
        if self.cycle_count_since_update >= self.periodic_interval:
            if overall_dissonance > self.dissonance_threshold and self._can_update(current_time):
                logger.info(f"Periodic update check: dissonance={overall_dissonance:.3f} exceeds threshold={self.dissonance_threshold}")
                return True
        
        # Threshold-based update: dissonance exceeds threshold (if cooldown allows)
        if overall_dissonance > self.dissonance_threshold:
            if self._can_update(current_time):
                logger.info(f"Dissonance ({overall_dissonance:.3f}) exceeds threshold ({self.dissonance_threshold}), triggering update")
                return True
        
        return False
    
    def _can_update(self, current_time: float) -> bool:
        """Check if update can be performed (cooldown check)."""
        if self.last_update_time is None:
            return True
        
        time_since_update = current_time - self.last_update_time
        return time_since_update >= self.update_cooldown
    
    def generate_revision_suggestions(
        self,
        dissonance_metrics: "DissonanceMetrics"
    ) -> Dict[str, Any]:
        """
        Generate revision suggestions based on dissonance dimensions.
        
        Args:
            dissonance_metrics: Current dissonance metrics
            
        Returns:
            Dictionary with suggested updates (for CRUD tool)
        """
        suggestions: Dict[str, Any] = {}
        rationale_parts = []
        
        # Logical dissonance -> update capabilities/knowledge boundaries
        if dissonance_metrics.logical_dissonance > 0.4:
            rationale_parts.append(f"High logical dissonance ({dissonance_metrics.logical_dissonance:.2f})")
            # Suggest reviewing capabilities that might be inconsistent
            suggestions["capabilities"] = []  # Could be enhanced to suggest specific updates
        
        # Factual dissonance -> update knowledge boundaries
        if dissonance_metrics.factual_dissonance > 0.4:
            rationale_parts.append(f"High factual dissonance ({dissonance_metrics.factual_dissonance:.2f})")
            suggestions["knowledge_boundaries"] = {}  # Could be enhanced to suggest specific updates
        
        # Behavioral dissonance -> update capabilities
        if dissonance_metrics.behavioral_dissonance > 0.4:
            rationale_parts.append(f"High behavioral dissonance ({dissonance_metrics.behavioral_dissonance:.2f})")
            suggestions["capabilities"] = []  # Could be enhanced to suggest capability updates
        
        # Goal dissonance -> update constraints
        if dissonance_metrics.goal_dissonance > 0.4:
            rationale_parts.append(f"High goal dissonance ({dissonance_metrics.goal_dissonance:.2f})")
            suggestions["constraints"] = {}  # Could be enhanced to suggest constraint updates
        
        rationale = "Self-model revision needed due to: " + "; ".join(rationale_parts) if rationale_parts else "Cognitive dissonance detected"
        
        return {
            "suggestions": suggestions,
            "rationale": rationale,
            "dissonance_scores": {
                "logical": dissonance_metrics.logical_dissonance,
                "factual": dissonance_metrics.factual_dissonance,
                "behavioral": dissonance_metrics.behavioral_dissonance,
                "goal": dissonance_metrics.goal_dissonance,
                "overall": dissonance_metrics.overall_dissonance
            }
        }
    
    def trigger_update(
        self,
        dissonance_metrics: "DissonanceMetrics",
        response: Optional[str] = None,
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> Optional["SelfModel"]:
        """
        Trigger self model update based on dissonance.
        
        Uses either SelfModelUpdater (default) or SelfModelCRUDTool (if use_crud_tool=True).
        
        Args:
            dissonance_metrics: Current dissonance metrics
            response: Optional response that caused dissonance
            conversation_context: Optional conversation context
            
        Returns:
            Updated SelfModel if update occurred, None otherwise
        """
        # Choose update method
        if self.use_crud_tool:
            if not self.self_model_crud_tool:
                logger.warning("SelfModelCRUDTool not available, cannot perform update")
                return None
            return self._trigger_update_via_crud(dissonance_metrics, response, conversation_context)
        else:
            if not self.self_model_updater:
                logger.warning("SelfModelUpdater not available, cannot perform update")
                return None
            return self._trigger_update_via_updater(dissonance_metrics, response, conversation_context)
    
    def _trigger_update_via_updater(
        self,
        dissonance_metrics: "DissonanceMetrics",
        response: Optional[str],
        conversation_context: Optional[List[Dict[str, str]]]
    ) -> Optional["SelfModel"]:
        """Trigger update using SelfModelUpdater (original method)."""
        
        # Record old dissonance
        old_dissonance = dissonance_metrics.overall_dissonance
        
        # Determine update reason
        if old_dissonance > self.critical_threshold:
            update_reason = "critical_dissonance"
        elif self.cycle_count_since_update >= self.periodic_interval:
            update_reason = "periodic_update"
        else:
            update_reason = "threshold_triggered"
        
        try:
            # Get consistency result if response provided
            consistency_result = None
            if response and hasattr(self.cognitive_dissonance_monitor, 'consistency_checker'):
                if self.cognitive_dissonance_monitor.consistency_checker:
                    consistency_result = self.cognitive_dissonance_monitor.consistency_checker.validate(
                        response=response,
                        self_model=self.self_model,
                        conversation_context=conversation_context
                    )
                    # Publish consistency violations into the dissonance monitor so logical/factual components
                    # remain available even when later cycles call measure_dissonance(response=None).
                    try:
                        if hasattr(self.cognitive_dissonance_monitor, "observe_consistency_result"):
                            self.cognitive_dissonance_monitor.observe_consistency_result(
                                consistency_result=consistency_result,
                                response=response,
                                conversation_context=conversation_context,
                                source="self_model_feedback.updater",
                            )
                    except Exception:
                        pass
            
            # Apply update using self model updater
            if consistency_result and not consistency_result.is_consistent:
                updated_model = self.self_model_updater.update_from_violations(
                    consistency_result=consistency_result,
                    current_model=self.self_model,
                    original_response=response or ""
                )
            else:
                # No specific violations, but still update based on dissonance
                # For now, return current model (future: could generate updates from dissonance patterns)
                logger.debug("No consistency violations to update from, skipping update")
                updated_model = self.self_model
            
            # Update reference
            if updated_model != self.self_model:
                self.self_model = updated_model
                self.cognitive_dissonance_monitor.self_model = updated_model  # Update reference in monitor
                
                # Record update
                self.last_update_time = time.time()
                self.update_count += 1
                self.cycle_count_since_update = 0
                
                # Measure new dissonance (if response available)
                new_dissonance = old_dissonance  # Default to old if can't measure
                if response:
                    # Use measure_dissonance_from_conversation if we have full messages
                    # Otherwise use measure_dissonance with automatic extraction
                    if conversation_context and isinstance(conversation_context, list) and len(conversation_context) > 0:
                        # Check if conversation_context has full message structure
                        has_full_messages = any(isinstance(msg, dict) and "tool_calls" in msg for msg in conversation_context)
                        if has_full_messages:
                            # Use helper method that extracts tool_usage automatically
                            new_metrics = self.cognitive_dissonance_monitor.measure_dissonance(
                                response=response,
                                conversation_context=conversation_context
                            )
                        else:
                            # Use basic method - it will try to extract tool_usage and reasoning_goals automatically
                            new_metrics = self.cognitive_dissonance_monitor.measure_dissonance(
                                response=response,
                                conversation_context=conversation_context
                            )
                    else:
                        # Use basic method with automatic extraction
                        new_metrics = self.cognitive_dissonance_monitor.measure_dissonance(
                            response=response,
                            conversation_context=conversation_context
                        )
                    new_dissonance = new_metrics.overall_dissonance
                
                # Compute effectiveness
                effectiveness = old_dissonance - new_dissonance  # Positive = improvement
                
                # Record update
                update_record = UpdateRecord(
                    timestamp=datetime.now(timezone.utc),
                    old_dissonance=old_dissonance,
                    new_dissonance=new_dissonance,
                    effectiveness=effectiveness,
                    update_reason=update_reason
                )
                self.update_history.append(update_record)
                
                logger.info(
                    f"Self model updated (reason: {update_reason}): "
                    f"dissonance {old_dissonance:.3f} -> {new_dissonance:.3f} "
                    f"(effectiveness: {effectiveness:+.3f})"
                )
                
                return updated_model
            else:
                logger.debug("Self model update did not change model")
                return None
                
        except Exception as e:
            logger.error(f"Error triggering self model update: {e}", exc_info=True)
            return None
    
    def _trigger_update_via_crud(
        self,
        dissonance_metrics: "DissonanceMetrics",
        response: Optional[str],
        conversation_context: Optional[List[Dict[str, str]]]
    ) -> Optional["SelfModel"]:
        """
        Trigger update using SelfModelCRUDTool based on dissonance.
        
        Generates revision suggestions from dissonance dimensions and applies via CRUD tool.
        """
        # Record old dissonance
        old_dissonance = dissonance_metrics.overall_dissonance
        
        # Determine update reason
        if old_dissonance > self.critical_threshold:
            update_reason = "critical_dissonance"
        elif self.cycle_count_since_update >= self.periodic_interval:
            update_reason = "periodic_update"
        else:
            update_reason = "threshold_triggered"
        
        try:
            # Generate revision suggestions
            revision_suggestions = self.generate_revision_suggestions(dissonance_metrics)
            suggestions = revision_suggestions["suggestions"]
            rationale = revision_suggestions["rationale"]
            
            # Apply suggestions via CRUD tool (for now, just log - actual updates would require specific entries)
            # The CRUD tool expects specific entries to create/update, so this is a placeholder
            # In practice, would need to analyze dissonance to generate specific entries
            logger.info(f"Generated revision suggestions: {suggestions}")
            logger.info(f"Rationale: {rationale}")
            
            # For now, if we have consistency violations, use them to generate specific updates
            # Otherwise, just log suggestions (actual implementation would generate specific entries)
            if response and hasattr(self.cognitive_dissonance_monitor, 'consistency_checker'):
                if self.cognitive_dissonance_monitor.consistency_checker:
                    consistency_result = self.cognitive_dissonance_monitor.consistency_checker.validate(
                        response=response,
                        self_model=self.self_model,
                        conversation_context=conversation_context
                    )
                    # Publish consistency violations into the dissonance monitor.
                    try:
                        if hasattr(self.cognitive_dissonance_monitor, "observe_consistency_result"):
                            self.cognitive_dissonance_monitor.observe_consistency_result(
                                consistency_result=consistency_result,
                                response=response,
                                conversation_context=conversation_context,
                                source="self_model_feedback.crud",
                            )
                    except Exception:
                        pass
                    if not consistency_result.is_consistent:
                        # Use updater for consistency violations (more reliable)
                        # CRUD tool would need specific entries which are harder to generate automatically
                        logger.info("Falling back to updater for consistency violations")
                        if self.self_model_updater:
                            return self._trigger_update_via_updater(dissonance_metrics, response, conversation_context)
            
            # For general dissonance without specific violations, suggestions are logged
            # Actual CRUD operations would require analyzing patterns and generating specific entries
            logger.debug("Revision suggestions generated (use CRUD tool manually or via updater for automatic updates)")
            
            # Return current model (no automatic update via CRUD tool for now)
            # The suggestions are available for manual review or future enhancement
            return None
                
        except Exception as e:
            logger.error(f"Error triggering self model update via CRUD tool: {e}", exc_info=True)
            return None
    
    def evaluate_update_effectiveness(self) -> Dict[str, Any]:
        """
        Evaluate effectiveness of recent updates.
        
        Returns:
            Dictionary with effectiveness metrics
        """
        if len(self.update_history) == 0:
            return {
                "total_updates": 0,
                "average_effectiveness": 0.0,
                "improvement_rate": 0.0
            }
        
        # Compute average effectiveness
        avg_effectiveness = sum(
            r.effectiveness for r in self.update_history if r.effectiveness is not None
        ) / len([r for r in self.update_history if r.effectiveness is not None])
        
        # Compute improvement rate (fraction of updates that improved)
        improvements = sum(1 for r in self.update_history if r.effectiveness and r.effectiveness > 0.0)
        improvement_rate = improvements / len(self.update_history) if self.update_history else 0.0
        
        return {
            "total_updates": len(self.update_history),
            "average_effectiveness": avg_effectiveness,
            "improvement_rate": improvement_rate,
            "total_improvements": improvements
        }
    
    def increment_cycle_count(self):
        """Increment cycle count since last update (for periodic updates)."""
        self.cycle_count_since_update += 1

