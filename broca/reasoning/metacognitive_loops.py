"""
Metacognitive monitoring loops.

Implements monitoring of monitoring processes (second-order metacognition)
integrated with epistemic engine for confidence calibration.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

if TYPE_CHECKING:
    from ..self_model.epistemic.engine import MetacognitiveEngine
    from .recursive_reasoning import RecursiveReasoningEngine

logger = logging.getLogger(__name__)


class MonitoringLevel(Enum):
    """Levels of metacognitive monitoring."""
    ZERO_ORDER = "zero_order"      # Direct cognition
    FIRST_ORDER = "first_order"     # Monitoring cognition
    SECOND_ORDER = "second_order"   # Monitoring the monitor


@dataclass
class MetacognitiveState:
    """State of metacognitive monitoring."""
    level: MonitoringLevel
    confidence: float
    calibration_error: float
    awareness: float  # How aware the system is of its own state
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MonitoringCycle:
    """A cycle of metacognitive monitoring."""
    cycle_id: str
    level: MonitoringLevel
    target: str  # What is being monitored
    observations: List[Dict[str, Any]] = field(default_factory=list)
    conclusions: Dict[str, Any] = field(default_factory=dict)
    confidence_updates: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class MetacognitiveLoop:
    """
    Metacognitive monitoring loop.
    
    Monitors cognitive processes and can monitor itself (second-order metacognition).
    """
    
    def __init__(
        self,
        epistemic_engine: Optional["MetacognitiveEngine"] = None,
        recursive_reasoning: Optional["RecursiveReasoningEngine"] = None,
        max_monitoring_depth: int = 2
    ):
        """
        Initialize metacognitive loop.
        
        Args:
            epistemic_engine: Optional MetacognitiveEngine for confidence tracking
            recursive_reasoning: Optional RecursiveReasoningEngine for recursive monitoring
            max_monitoring_depth: Maximum depth of monitoring (0=direct, 1=monitor, 2=monitor monitor)
        """
        self.epistemic_engine = epistemic_engine
        self.recursive_reasoning = recursive_reasoning
        self.max_monitoring_depth = max_monitoring_depth
        
        # State tracking
        self.metacognitive_states: deque = deque(maxlen=100)
        self.monitoring_cycles: List[MonitoringCycle] = []
        self.next_cycle_id: int = 1
        
        # Current monitoring state
        self.current_monitoring_depth: int = 0
        
        logger.info(
            f"Initialized MetacognitiveLoop "
            f"(max_depth={max_monitoring_depth})"
        )
    
    def monitor_cognition(
        self,
        cognitive_process: str,
        process_state: Dict[str, Any],
        depth: int = 0
    ) -> Dict[str, Any]:
        """
        Monitor a cognitive process.
        
        Args:
            cognitive_process: Name/type of cognitive process
            process_state: Current state of the process
            depth: Current monitoring depth
            
        Returns:
            Monitoring result with observations and recommendations
        """
        # Safety: prevent infinite recursion
        if depth > self.max_monitoring_depth:
            logger.warning(f"Monitoring depth limit reached ({depth} > {self.max_monitoring_depth})")
            return {
                "monitoring_level": depth,
                "observations": [],
                "conclusions": {"status": "depth_limit_reached"},
                "recommendations": []
            }
        
        self.current_monitoring_depth = depth
        
        # Create monitoring cycle
        cycle_id = f"monitoring_cycle_{self.next_cycle_id}"
        self.next_cycle_id += 1
        
        cycle = MonitoringCycle(
            cycle_id=cycle_id,
            level=MonitoringLevel.FIRST_ORDER if depth == 0 else MonitoringLevel.SECOND_ORDER,
            target=cognitive_process
        )
        
        try:
            # Step 1: Observe the cognitive process
            observations = self._observe_process(cognitive_process, process_state, depth)
            cycle.observations = observations
            
            # Step 2: Analyze observations
            analysis = self._analyze_observations(observations, process_state, depth)
            cycle.conclusions = analysis
            
            # Step 3: Update confidence if epistemic engine available
            if self.epistemic_engine and depth == 0:
                confidence_updates = self._update_confidence(analysis, cognitive_process)
                cycle.confidence_updates = confidence_updates
            
            # Step 4: Generate recommendations
            recommendations = self._generate_recommendations(analysis, depth)
            
            # Step 5: If confidence is low or issues detected, monitor the monitoring
            if depth < self.max_monitoring_depth and self._should_monitor_monitoring(analysis):
                logger.debug(f"Triggering second-order monitoring (depth {depth + 1})")
                meta_monitoring = self.monitor_cognition(
                    cognitive_process=f"monitoring_of_{cognitive_process}",
                    process_state={
                        "monitored_process": cognitive_process,
                        "monitoring_observations": observations,
                        "monitoring_analysis": analysis
                    },
                    depth=depth + 1
                )
                analysis["meta_monitoring"] = meta_monitoring
                recommendations.extend(meta_monitoring.get("recommendations", []))
            
            cycle.completed_at = datetime.now(timezone.utc)
            self.monitoring_cycles.append(cycle)
            
            # Limit history
            if len(self.monitoring_cycles) > 1000:
                self.monitoring_cycles = self.monitoring_cycles[-1000:]
            
            # Update metacognitive state
            self._update_metacognitive_state(cycle, analysis)
            
            return {
                "monitoring_level": depth,
                "cycle_id": cycle_id,
                "observations": observations,
                "conclusions": analysis,
                "recommendations": recommendations,
                "confidence_updates": cycle.confidence_updates
            }
            
        except Exception as e:
            logger.error(f"Error in metacognitive monitoring: {e}", exc_info=True)
            cycle.completed_at = datetime.now(timezone.utc)
            cycle.conclusions = {"error": str(e), "status": "failed"}
            return {
                "monitoring_level": depth,
                "cycle_id": cycle_id,
                "observations": [],
                "conclusions": {"error": str(e), "status": "failed"},
                "recommendations": []
            }
    
    def _observe_process(
        self,
        cognitive_process: str,
        process_state: Dict[str, Any],
        depth: int
    ) -> List[Dict[str, Any]]:
        """Observe the cognitive process."""
        observations = []
        
        # Observe confidence
        confidence = process_state.get("confidence", 0.5)
        observations.append({
            "type": "confidence",
            "value": confidence,
            "assessment": "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
        })
        
        # Observe performance metrics
        if "performance" in process_state:
            perf = process_state["performance"]
            observations.append({
                "type": "performance",
                "metrics": perf
            })
        
        # Observe errors or issues
        if "errors" in process_state:
            observations.append({
                "type": "errors",
                "count": len(process_state["errors"]),
                "errors": process_state["errors"][:5]  # Limit to 5
            })
        
        # Observe resource usage
        if "resource_usage" in process_state:
            observations.append({
                "type": "resource_usage",
                "usage": process_state["resource_usage"]
            })
        
        # For second-order monitoring, observe the monitoring itself
        if depth > 0:
            observations.append({
                "type": "monitoring_quality",
                "depth": depth,
                "monitored_process": process_state.get("monitored_process", "unknown")
            })
        
        return observations
    
    def _analyze_observations(
        self,
        observations: List[Dict[str, Any]],
        process_state: Dict[str, Any],
        depth: int
    ) -> Dict[str, Any]:
        """Analyze observations to draw conclusions."""
        analysis = {
            "status": "normal",
            "confidence_level": "medium",
            "issues_detected": [],
            "strengths": [],
            "calibration_quality": "unknown"
        }
        
        # Analyze confidence
        confidence_obs = next((o for o in observations if o.get("type") == "confidence"), None)
        if confidence_obs:
            conf_value = confidence_obs.get("value", 0.5)
            if conf_value > 0.7:
                analysis["confidence_level"] = "high"
                analysis["strengths"].append("high_confidence")
            elif conf_value < 0.4:
                analysis["confidence_level"] = "low"
                analysis["issues_detected"].append("low_confidence")
                analysis["status"] = "needs_attention"
        
        # Analyze errors
        error_obs = next((o for o in observations if o.get("type") == "errors"), None)
        if error_obs and error_obs.get("count", 0) > 0:
            analysis["issues_detected"].append("errors_present")
            analysis["status"] = "needs_attention"
            if error_obs.get("count", 0) > 3:
                analysis["status"] = "critical"
        
        # Analyze performance
        perf_obs = next((o for o in observations if o.get("type") == "performance"), None)
        if perf_obs:
            perf_metrics = perf_obs.get("metrics", {})
            if perf_metrics.get("success_rate", 1.0) < 0.7:
                analysis["issues_detected"].append("low_success_rate")
                analysis["status"] = "needs_attention"
        
        # Calibration quality (if epistemic engine available)
        if self.epistemic_engine and depth == 0:
            # Check if confidence is well-calibrated
            # This would use epistemic engine's calibration metrics
            analysis["calibration_quality"] = "good"  # Placeholder
        
        return analysis
    
    def _update_confidence(
        self,
        analysis: Dict[str, Any],
        cognitive_process: str
    ) -> List[Dict[str, Any]]:
        """Update confidence based on monitoring analysis."""
        if not self.epistemic_engine:
            return []
        
        updates = []
        
        # If issues detected, reduce confidence
        if analysis.get("status") == "needs_attention":
            # This would update epistemic confidence
            # For now, just record the update
            updates.append({
                "type": "confidence_adjustment",
                "direction": "decrease",
                "reason": "issues_detected",
                "process": cognitive_process
            })
        elif analysis.get("status") == "normal" and analysis.get("confidence_level") == "high":
            updates.append({
                "type": "confidence_adjustment",
                "direction": "maintain",
                "reason": "high_confidence_maintained",
                "process": cognitive_process
            })
        
        return updates
    
    def _generate_recommendations(
        self,
        analysis: Dict[str, Any],
        depth: int
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if analysis.get("status") == "critical":
            recommendations.append({
                "priority": "high",
                "action": "immediate_intervention",
                "reason": "Critical issues detected"
            })
        elif analysis.get("status") == "needs_attention":
            recommendations.append({
                "priority": "medium",
                "action": "review_and_adjust",
                "reason": "Issues detected that need attention"
            })
        
        # Low confidence recommendations
        if analysis.get("confidence_level") == "low":
            recommendations.append({
                "priority": "medium",
                "action": "gather_more_evidence",
                "reason": "Low confidence - need more information"
            })
        
        # Calibration recommendations
        if analysis.get("calibration_quality") == "poor":
            recommendations.append({
                "priority": "low",
                "action": "recalibrate_confidence",
                "reason": "Confidence calibration needs improvement"
            })
        
        return recommendations
    
    def _should_monitor_monitoring(self, analysis: Dict[str, Any]) -> bool:
        """Determine if we should monitor the monitoring process."""
        # Monitor monitoring if:
        # 1. Critical issues detected
        # 2. Low confidence
        # 3. Calibration quality is poor
        
        if analysis.get("status") == "critical":
            return True
        
        if analysis.get("confidence_level") == "low":
            return True
        
        if analysis.get("calibration_quality") == "poor":
            return True
        
        return False
    
    def _update_metacognitive_state(
        self,
        cycle: MonitoringCycle,
        analysis: Dict[str, Any]
    ):
        """Update overall metacognitive state."""
        # Compute awareness (how well the system knows its own state)
        awareness = 0.5  # Base awareness
        
        # Increase awareness if monitoring is working well
        if analysis.get("status") == "normal":
            awareness += 0.2
        
        # Increase awareness if we have good observations
        if len(cycle.observations) > 2:
            awareness += 0.1
        
        # Decrease awareness if issues detected
        if analysis.get("issues_detected"):
            awareness -= 0.1 * len(analysis.get("issues_detected", []))
        
        awareness = max(0.0, min(1.0, awareness))
        
        # Get confidence from analysis
        confidence_map = {"high": 0.8, "medium": 0.5, "low": 0.3}
        confidence = confidence_map.get(analysis.get("confidence_level", "medium"), 0.5)
        
        state = MetacognitiveState(
            level=cycle.level,
            confidence=confidence,
            calibration_error=0.1,  # Placeholder - would use epistemic engine
            awareness=awareness
        )
        
        self.metacognitive_states.append(state)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about metacognitive monitoring."""
        if not self.monitoring_cycles:
            return {"status": "no_data"}
        
        completed = [c for c in self.monitoring_cycles if c.completed_at]
        first_order = [c for c in self.monitoring_cycles if c.level == MonitoringLevel.FIRST_ORDER]
        second_order = [c for c in self.monitoring_cycles if c.level == MonitoringLevel.SECOND_ORDER]
        
        # Average awareness
        if self.metacognitive_states:
            avg_awareness = sum(s.awareness for s in self.metacognitive_states) / len(self.metacognitive_states)
            avg_confidence = sum(s.confidence for s in self.metacognitive_states) / len(self.metacognitive_states)
        else:
            avg_awareness = 0.0
            avg_confidence = 0.0
        
        return {
            "total_cycles": len(self.monitoring_cycles),
            "completed_cycles": len(completed),
            "first_order_cycles": len(first_order),
            "second_order_cycles": len(second_order),
            "avg_awareness": avg_awareness,
            "avg_confidence": avg_confidence,
            "current_monitoring_depth": self.current_monitoring_depth
        }

