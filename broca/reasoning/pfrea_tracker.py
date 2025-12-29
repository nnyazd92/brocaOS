"""
PFREA Compliance Tracker

Tracks PFREA (Plan-Forecast-Replan-Execute-Assess) loop compliance metrics,
generates audit reports, and monitors enforcement across all entry points.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)


class PFREAEventType(Enum):
    """Types of PFREA events."""
    TRANSITION = "transition"
    ENFORCEMENT = "enforcement"
    BYPASS = "bypass"
    VIOLATION = "violation"
    PLAN_EXTRACTED = "plan_extracted"
    FORECAST_EXTRACTED = "forecast_extracted"
    ACTION_RECORDED = "action_recorded"
    ASSESSMENT_GENERATED = "assessment_generated"


@dataclass
class PFREAEvent:
    """A single PFREA event for audit trail."""
    timestamp: datetime
    phase: Optional[str]  # LoopPhase value or None
    plan_id: Optional[str]
    event_type: str  # PFREAEventType value
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


class PFREATracker:
    """
    Tracks PFREA compliance metrics and generates audit reports.
    
    Features:
    - Track all PFREA phase transitions with timestamps
    - Count bypasses (with reasons)
    - Calculate compliance percentage
    - Track average time per phase
    - Detect violations (execution without plan/forecast)
    - Generate compliance reports
    """
    
    def __init__(
        self,
        max_events: int = 10000,
        enabled: bool = True
    ):
        """
        Initialize PFREA tracker.
        
        Args:
            max_events: Maximum number of events to keep in memory
            enabled: Whether tracking is enabled
        """
        self.enabled = enabled
        self.max_events = max_events
        
        # Event history (FIFO queue)
        self.events: deque = deque(maxlen=max_events)
        
        # Metrics counters
        self._phase_transitions: Dict[str, int] = defaultdict(int)
        self._bypasses: Dict[str, int] = defaultdict(int)  # reason -> count
        self._violations: List[PFREAEvent] = []
        self._plan_extractions: int = 0
        self._forecast_extractions: int = 0
        self._action_recordings: int = 0
        self._assessments: int = 0
        
        # Phase timing
        self._phase_start_times: Dict[str, datetime] = {}  # plan_id -> phase -> start_time
        self._phase_durations: List[Dict[str, Any]] = []  # List of phase duration records
        
        # Compliance tracking
        self._total_enforcements: int = 0
        self._total_bypasses: int = 0
        self._total_violations: int = 0
        
        logger.info(f"Initialized PFREA tracker (enabled={enabled}, max_events={max_events})")
    
    def record_event(
        self,
        event_type: PFREAEventType,
        phase: Optional[str] = None,
        plan_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a PFREA event.
        
        Args:
            event_type: Type of event
            phase: Current PFREA phase
            plan_id: Plan ID if applicable
            session_id: Session ID if applicable
            context: Additional context dictionary
        """
        if not self.enabled:
            return
        
        event = PFREAEvent(
            timestamp=datetime.now(timezone.utc),
            phase=phase,
            plan_id=plan_id,
            event_type=event_type.value,
            context=context or {},
            session_id=session_id,
        )
        
        self.events.append(event)
        
        # Update metrics
        if event_type == PFREAEventType.TRANSITION:
            if phase:
                self._phase_transitions[phase] += 1
        elif event_type == PFREAEventType.BYPASS:
            reason = context.get("reason", "unknown") if context else "unknown"
            self._bypasses[reason] += 1
            self._total_bypasses += 1
        elif event_type == PFREAEventType.VIOLATION:
            self._violations.append(event)
            self._total_violations += 1
        elif event_type == PFREAEventType.PLAN_EXTRACTED:
            self._plan_extractions += 1
        elif event_type == PFREAEventType.FORECAST_EXTRACTED:
            self._forecast_extractions += 1
        elif event_type == PFREAEventType.ACTION_RECORDED:
            self._action_recordings += 1
        elif event_type == PFREAEventType.ASSESSMENT_GENERATED:
            self._assessments += 1
        elif event_type == PFREAEventType.ENFORCEMENT:
            self._total_enforcements += 1
    
    def record_phase_transition(
        self,
        from_phase: Optional[str],
        to_phase: str,
        plan_id: Optional[str] = None,
        session_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """
        Record a phase transition.
        
        Args:
            from_phase: Previous phase
            to_phase: New phase
            plan_id: Plan ID if applicable
            session_id: Session ID if applicable
            reason: Reason for transition
        """
        context = {
            "from_phase": from_phase,
            "to_phase": to_phase,
            "reason": reason or "unknown",
        }
        
        self.record_event(
            event_type=PFREAEventType.TRANSITION,
            phase=to_phase,
            plan_id=plan_id,
            session_id=session_id,
            context=context,
        )
        
        # Track phase timing
        if plan_id:
            phase_key = f"{plan_id}:{to_phase}"
            self._phase_start_times[phase_key] = datetime.now(timezone.utc)
            
            # Record duration of previous phase if it exists
            if from_phase:
                prev_phase_key = f"{plan_id}:{from_phase}"
                if prev_phase_key in self._phase_start_times:
                    start_time = self._phase_start_times[prev_phase_key]
                    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                    self._phase_durations.append({
                        "plan_id": plan_id,
                        "phase": from_phase,
                        "duration_seconds": duration,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
    
    def record_bypass(
        self,
        reason: str,
        justification: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a PFREA bypass (legitimate or otherwise).
        
        Args:
            reason: Reason for bypass (e.g., "title_generation")
            justification: Justification for why bypass is acceptable
            session_id: Session ID if applicable
            context: Additional context
        """
        bypass_context = {
            "reason": reason,
            "justification": justification,
            **(context or {}),
        }
        
        self.record_event(
            event_type=PFREAEventType.BYPASS,
            phase=None,
            plan_id=None,
            session_id=session_id,
            context=bypass_context,
        )
    
    def record_violation(
        self,
        violation_type: str,
        description: str,
        plan_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a PFREA violation (execution without proper phases).
        
        Args:
            violation_type: Type of violation (e.g., "execution_without_plan")
            description: Description of the violation
            plan_id: Plan ID if applicable
            session_id: Session ID if applicable
            context: Additional context
        """
        violation_context = {
            "violation_type": violation_type,
            "description": description,
            **(context or {}),
        }
        
        self.record_event(
            event_type=PFREAEventType.VIOLATION,
            phase=None,
            plan_id=plan_id,
            session_id=session_id,
            context=violation_context,
        )
        
        logger.warning(
            f"PFREA violation detected: {violation_type} - {description}",
            extra={
                "event": "pfrea_violation",
                "violation_type": violation_type,
                "description": description,
                "plan_id": plan_id,
                "session_id": session_id,
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current PFREA compliance metrics.
        
        Returns:
            Dictionary with comprehensive metrics
        """
        total_events = len(self.events)
        total_enforcements = self._total_enforcements
        total_bypasses = self._total_bypasses
        total_violations = self._total_violations
        
        # Calculate compliance percentage
        total_operations = total_enforcements + total_bypasses
        if total_operations > 0:
            compliance_percentage = (total_enforcements / total_operations) * 100.0
        else:
            compliance_percentage = 100.0  # No operations yet
        
        # Calculate average phase durations
        phase_avg_durations: Dict[str, float] = {}
        phase_duration_counts: Dict[str, int] = defaultdict(int)
        phase_duration_sums: Dict[str, float] = defaultdict(float)
        
        for duration_record in self._phase_durations:
            phase = duration_record["phase"]
            duration = duration_record["duration_seconds"]
            phase_duration_counts[phase] += 1
            phase_duration_sums[phase] += duration
        
        for phase, count in phase_duration_counts.items():
            phase_avg_durations[phase] = phase_duration_sums[phase] / count
        
        # Calculate phase distribution
        total_transitions = sum(self._phase_transitions.values())
        phase_distribution: Dict[str, float] = {}
        if total_transitions > 0:
            for phase, count in self._phase_transitions.items():
                phase_distribution[phase] = (count / total_transitions) * 100.0
        
        # Calculate replan rate
        replan_count = self._phase_transitions.get("re_plan", 0)
        plan_count = self._plan_extractions
        replan_rate = (replan_count / plan_count * 100.0) if plan_count > 0 else 0.0
        
        return {
            "enabled": self.enabled,
            "total_events": total_events,
            "total_enforcements": total_enforcements,
            "total_bypasses": total_bypasses,
            "total_violations": total_violations,
            "compliance_percentage": round(compliance_percentage, 2),
            "plan_extractions": self._plan_extractions,
            "forecast_extractions": self._forecast_extractions,
            "action_recordings": self._action_recordings,
            "assessments": self._assessments,
            "phase_transitions": dict(self._phase_transitions),
            "phase_distribution_percent": phase_distribution,
            "average_phase_durations_seconds": phase_avg_durations,
            "replan_rate_percent": round(replan_rate, 2),
            "bypasses_by_reason": dict(self._bypasses),
            "violations_count": len(self._violations),
            "recent_violations": [
                v.to_dict() for v in self._violations[-10:]  # Last 10 violations
            ],
        }
    
    def get_audit_trail(
        self,
        session_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        event_type: Optional[PFREAEventType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get audit trail of PFREA events.
        
        Args:
            session_id: Filter by session ID
            plan_id: Filter by plan ID
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        filtered_events = []
        
        for event in self.events:
            # Apply filters
            if session_id and event.session_id != session_id:
                continue
            if plan_id and event.plan_id != plan_id:
                continue
            if event_type and event.event_type != event_type.value:
                continue
            
            filtered_events.append(event.to_dict())
            
            if len(filtered_events) >= limit:
                break
        
        return filtered_events
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive compliance report.
        
        Returns:
            Dictionary with compliance analysis
        """
        metrics = self.get_metrics()
        
        # Determine compliance status
        compliance_percentage = metrics["compliance_percentage"]
        if compliance_percentage >= 95.0:
            status = "excellent"
        elif compliance_percentage >= 80.0:
            status = "good"
        elif compliance_percentage >= 60.0:
            status = "fair"
        else:
            status = "poor"
        
        # Analyze violations
        violation_analysis = {
            "total": len(self._violations),
            "by_type": defaultdict(int),
        }
        
        for violation in self._violations:
            violation_type = violation.context.get("violation_type", "unknown")
            violation_analysis["by_type"][violation_type] += 1
        
        violation_analysis["by_type"] = dict(violation_analysis["by_type"])
        
        return {
            "status": status,
            "compliance_percentage": compliance_percentage,
            "metrics": metrics,
            "violation_analysis": violation_analysis,
            "recommendations": self._generate_recommendations(metrics, violation_analysis),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        violation_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations based on metrics and violations."""
        recommendations = []
        
        compliance = metrics["compliance_percentage"]
        if compliance < 95.0:
            recommendations.append(
                f"Compliance is {compliance:.1f}% - target is 95%. Review bypasses and violations."
            )
        
        if violation_analysis["total"] > 0:
            recommendations.append(
                f"{violation_analysis['total']} violations detected. Review violation types and address root causes."
            )
        
        if metrics["replan_rate_percent"] > 50.0:
            recommendations.append(
                f"Replan rate is {metrics['replan_rate_percent']:.1f}% - plans may need better initial validation."
            )
        
        if metrics["total_bypasses"] > metrics["total_enforcements"] * 0.1:
            recommendations.append(
                f"Bypass rate is high ({metrics['total_bypasses']} bypasses vs {metrics['total_enforcements']} enforcements). "
                "Review if bypasses are legitimate."
            )
        
        return recommendations
    
    def check_compliance_and_warn(
        self,
        compliance_threshold: float = 0.95,
        violation_alert_threshold: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Check compliance and log warnings if thresholds are exceeded.
        
        Args:
            compliance_threshold: Minimum compliance percentage (0.0-1.0)
            violation_alert_threshold: Maximum violations before alerting
            
        Returns:
            Warning dictionary if thresholds exceeded, None otherwise
        """
        if not self.enabled:
            return None
        
        metrics = self.get_metrics()
        compliance_percentage = metrics["compliance_percentage"] / 100.0  # Convert to 0.0-1.0
        violation_count = metrics["violations_count"]
        
        warnings = []
        
        # Check compliance threshold
        if compliance_percentage < compliance_threshold:
            warnings.append({
                "type": "low_compliance",
                "message": f"PFREA compliance is {metrics['compliance_percentage']:.1f}% (threshold: {compliance_threshold*100:.1f}%)",
                "severity": "warning",
                "compliance_percentage": metrics["compliance_percentage"],
                "threshold": compliance_threshold * 100,
            })
            logger.warning(
                f"PFREA compliance below threshold: {metrics['compliance_percentage']:.1f}% (target: {compliance_threshold*100:.1f}%)",
                extra={
                    "event": "pfrea_compliance_warning",
                    "compliance_percentage": metrics["compliance_percentage"],
                    "threshold": compliance_threshold * 100,
                    "total_enforcements": metrics["total_enforcements"],
                    "total_bypasses": metrics["total_bypasses"],
                }
            )
        
        # Check violation threshold
        if violation_count >= violation_alert_threshold:
            warnings.append({
                "type": "high_violations",
                "message": f"PFREA violations exceed threshold: {violation_count} (threshold: {violation_alert_threshold})",
                "severity": "error",
                "violation_count": violation_count,
                "threshold": violation_alert_threshold,
            })
            logger.error(
                f"PFREA violations exceed alert threshold: {violation_count} violations (threshold: {violation_alert_threshold})",
                extra={
                    "event": "pfrea_violation_alert",
                    "violation_count": violation_count,
                    "threshold": violation_alert_threshold,
                    "recent_violations": metrics.get("recent_violations", [])[:5],
                }
            )
        
        if warnings:
            return {
                "warnings": warnings,
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        return None


# Global tracker instance
_global_tracker: Optional[PFREATracker] = None


def get_pfrea_tracker() -> PFREATracker:
    """Get or create global PFREA tracker instance."""
    global _global_tracker
    
    if _global_tracker is None:
        from .config import ReasoningConfig
        _global_tracker = PFREATracker(
            enabled=getattr(ReasoningConfig, 'pfrea_metrics_enabled', True),
        )
    
    return _global_tracker

