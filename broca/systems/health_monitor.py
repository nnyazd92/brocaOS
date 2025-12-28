"""
System health monitoring and stability analysis.

Implements health monitoring with adaptive reconfiguration.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

if TYPE_CHECKING:
    from .dynamics import SystemDynamicsModel

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNSTABLE = "unstable"


@dataclass
class HealthMetric:
    """A health metric."""
    name: str
    value: float
    threshold_warning: float = 0.5
    threshold_critical: float = 0.3
    weight: float = 1.0


@dataclass
class HealthReport:
    """System health report."""
    timestamp: datetime
    overall_health: float
    status: HealthStatus
    metrics: Dict[str, HealthMetric]
    issues: List[str]
    recommendations: List[str]
    stability_score: float = 0.5


class SystemHealthMonitor:
    """
    System health monitor with adaptive reconfiguration.
    
    Monitors system health and stability, detects issues,
    and recommends reconfigurations.
    """
    
    def __init__(
        self,
        system_dynamics: Optional["SystemDynamicsModel"] = None,
        health_threshold_warning: float = 0.6,
        health_threshold_critical: float = 0.4,
        stability_threshold: float = 0.5
    ):
        """
        Initialize system health monitor.
        
        Args:
            system_dynamics: Optional SystemDynamicsModel for dynamics analysis
            health_threshold_warning: Health threshold for warnings
            health_threshold_critical: Health threshold for critical status
            stability_threshold: Stability threshold
        """
        self.system_dynamics = system_dynamics
        self.health_threshold_warning = health_threshold_warning
        self.health_threshold_critical = health_threshold_critical
        self.stability_threshold = stability_threshold
        
        # Health history
        self.health_history: deque = deque(maxlen=1000)
        
        # Reconfiguration history
        self.reconfigurations: List[Dict[str, Any]] = []
        
        logger.info("Initialized SystemHealthMonitor")
    
    def assess_health(self) -> HealthReport:
        """
        Assess current system health.
        
        Returns:
            HealthReport with health status and recommendations
        """
        metrics = {}
        issues = []
        recommendations = []
        
        # Get metrics from system dynamics if available
        if self.system_dynamics:
            dynamics_stats = self.system_dynamics.get_statistics()
            
            # Extract metrics
            if "variables" in dynamics_stats:
                for var_name, var_data in dynamics_stats["variables"].items():
                    value = var_data.get("value", 0.5)
                    
                    # Determine thresholds based on variable type
                    if var_name == "dissonance":
                        # Low dissonance is good
                        threshold_warning = 0.5
                        threshold_critical = 0.7
                        health_value = 1.0 - value  # Invert for health
                    elif var_name == "confidence":
                        # High confidence is good
                        threshold_warning = 0.5
                        threshold_critical = 0.3
                        health_value = value
                    elif var_name == "performance":
                        # High performance is good
                        threshold_warning = 0.6
                        threshold_critical = 0.4
                        health_value = value
                    elif var_name == "cognitive_load":
                        # Low load is good
                        threshold_warning = 0.6
                        threshold_critical = 0.8
                        health_value = 1.0 - value  # Invert for health
                    else:
                        # Generic
                        threshold_warning = 0.5
                        threshold_critical = 0.3
                        health_value = value
                    
                    metrics[var_name] = HealthMetric(
                        name=var_name,
                        value=health_value,
                        threshold_warning=threshold_warning,
                        threshold_critical=threshold_critical
                    )
                    
                    # Check for issues
                    if health_value < threshold_critical:
                        issues.append(f"{var_name} is critical ({health_value:.2f} < {threshold_critical:.2f})")
                        recommendations.append(f"Immediate action needed for {var_name}")
                    elif health_value < threshold_warning:
                        issues.append(f"{var_name} is degraded ({health_value:.2f} < {threshold_warning:.2f})")
                        recommendations.append(f"Monitor and adjust {var_name}")
            
            stability_score = dynamics_stats.get("current_stability", 0.5)
        else:
            stability_score = 0.5
        
        # Compute overall health
        if metrics:
            # Weighted average
            total_weight = sum(m.weight for m in metrics.values())
            if total_weight > 0:
                overall_health = sum(m.value * m.weight for m in metrics.values()) / total_weight
            else:
                overall_health = 0.5
        else:
            overall_health = 0.5
        
        # Determine status
        if overall_health < self.health_threshold_critical:
            status = HealthStatus.CRITICAL
        elif overall_health < self.health_threshold_warning:
            status = HealthStatus.DEGRADED
        elif stability_score < self.stability_threshold:
            status = HealthStatus.UNSTABLE
        else:
            status = HealthStatus.HEALTHY
        
        # Generate recommendations based on status
        if status == HealthStatus.CRITICAL:
            recommendations.append("System is in critical state - immediate reconfiguration needed")
        elif status == HealthStatus.DEGRADED:
            recommendations.append("System health is degraded - consider reconfiguration")
        elif status == HealthStatus.UNSTABLE:
            recommendations.append("System is unstable - stabilize before proceeding")
        
        # Create report
        report = HealthReport(
            timestamp=datetime.now(timezone.utc),
            overall_health=overall_health,
            status=status,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            stability_score=stability_score
        )
        
        self.health_history.append(report)
        
        return report
    
    def recommend_reconfiguration(
        self,
        health_report: Optional[HealthReport] = None
    ) -> Dict[str, Any]:
        """
        Recommend system reconfiguration based on health.
        
        Args:
            health_report: Optional health report (if None, assesses first)
            
        Returns:
            Reconfiguration recommendations
        """
        if health_report is None:
            health_report = self.assess_health()
        
        reconfig = {
            "recommended": False,
            "priority": "low",
            "changes": [],
            "rationale": ""
        }
        
        if health_report.status == HealthStatus.CRITICAL:
            reconfig["recommended"] = True
            reconfig["priority"] = "critical"
            reconfig["rationale"] = "System is in critical state"
            
            # Recommend specific changes based on issues
            for issue in health_report.issues:
                if "dissonance" in issue.lower():
                    reconfig["changes"].append({
                        "component": "cognitive_dissonance",
                        "action": "reduce_dissonance",
                        "method": "self_model_update"
                    })
                elif "confidence" in issue.lower():
                    reconfig["changes"].append({
                        "component": "confidence",
                        "action": "increase_confidence",
                        "method": "gather_more_evidence"
                    })
                elif "performance" in issue.lower():
                    reconfig["changes"].append({
                        "component": "performance",
                        "action": "improve_performance",
                        "method": "optimize_rules"
                    })
                elif "cognitive_load" in issue.lower():
                    reconfig["changes"].append({
                        "component": "cognitive_load",
                        "action": "reduce_load",
                        "method": "reduce_working_memory_items"
                    })
        
        elif health_report.status == HealthStatus.DEGRADED:
            reconfig["recommended"] = True
            reconfig["priority"] = "medium"
            reconfig["rationale"] = "System health is degraded"
            
            # Less aggressive changes
            for issue in health_report.issues[:2]:  # Top 2 issues
                if "dissonance" in issue.lower():
                    reconfig["changes"].append({
                        "component": "cognitive_dissonance",
                        "action": "monitor_and_adjust",
                        "method": "gradual_adjustment"
                    })
        
        elif health_report.status == HealthStatus.UNSTABLE:
            reconfig["recommended"] = True
            reconfig["priority"] = "high"
            reconfig["rationale"] = "System is unstable"
            reconfig["changes"].append({
                "component": "stability",
                "action": "stabilize",
                "method": "reduce_feedback_strength"
            })
        
        if reconfig["recommended"]:
            # Record reconfiguration
            self.reconfigurations.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "recommendation": reconfig
            })
            logger.info(f"Recommended reconfiguration: {reconfig['rationale']}")
        
        return reconfig
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about system health."""
        if not self.health_history:
            return {"status": "no_data"}
        
        # Count by status
        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = sum(
                1 for r in self.health_history if r.status == status
            )
        
        # Average health
        avg_health = sum(r.overall_health for r in self.health_history) / len(self.health_history)
        
        # Current health
        current_health = self.health_history[-1].overall_health if self.health_history else 0.5
        
        return {
            "total_assessments": len(self.health_history),
            "status_counts": status_counts,
            "avg_health": avg_health,
            "current_health": current_health,
            "reconfigurations_recommended": len(self.reconfigurations)
        }

