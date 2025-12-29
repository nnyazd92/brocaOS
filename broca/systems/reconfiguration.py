"""
Adaptive system reconfiguration.

Implements reconfiguration based on health monitoring.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass

if TYPE_CHECKING:
    from .health_monitor import SystemHealthMonitor, HealthReport

logger = logging.getLogger(__name__)


class ReconfigurationManager:
    """
    Manages adaptive system reconfiguration.
    
    Applies reconfigurations recommended by health monitor.
    """
    
    def __init__(
        self,
        health_monitor: Optional["SystemHealthMonitor"] = None
    ):
        """
        Initialize reconfiguration manager.
        
        Args:
            health_monitor: Optional SystemHealthMonitor
        """
        self.health_monitor = health_monitor
        
        # Reconfiguration history
        self.applied_reconfigurations: List[Dict[str, Any]] = []
        
        logger.info("Initialized ReconfigurationManager")
    
    def apply_reconfiguration(
        self,
        reconfiguration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply a reconfiguration.
        
        Args:
            reconfiguration: Reconfiguration recommendation
            
        Returns:
            Result of reconfiguration
        """
        result = {
            "success": False,
            "changes_applied": [],
            "errors": []
        }
        
        if not reconfiguration.get("recommended", False):
            result["errors"].append("Reconfiguration not recommended")
            return result
        
        changes = reconfiguration.get("changes", [])
        
        for change in changes:
            try:
                applied = self._apply_change(change)
                if applied:
                    result["changes_applied"].append(change)
                else:
                    result["errors"].append(f"Failed to apply change: {change.get('action', 'unknown')}")
            except Exception as e:
                logger.error(f"Error applying reconfiguration change: {e}", exc_info=True)
                result["errors"].append(f"Error: {str(e)}")
        
        result["success"] = len(result["changes_applied"]) > 0
        
        if result["success"]:
            # Record applied reconfiguration
            self.applied_reconfigurations.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reconfiguration": reconfiguration,
                "result": result
            })
            logger.info(f"Applied reconfiguration: {len(result['changes_applied'])} changes")
        
        return result
    
    def _apply_change(self, change: Dict[str, Any]) -> bool:
        """Apply a single reconfiguration change."""
        component = change.get("component")
        action = change.get("action")
        method = change.get("method")
        
        logger.debug(f"Applying change: {component}/{action} via {method}")
        
        # In a full implementation, this would actually modify system components
        # For now, we just log the change
        
        if component == "cognitive_dissonance":
            if action == "reduce_dissonance":
                # Would trigger self-model update
                logger.info("Would trigger self-model update to reduce dissonance")
                return True
            elif action == "monitor_and_adjust":
                logger.info("Would enable enhanced monitoring for dissonance")
                return True
        
        elif component == "confidence":
            if action == "increase_confidence":
                logger.info("Would gather more evidence to increase confidence")
                return True
        
        elif component == "performance":
            if action == "improve_performance":
                logger.info("Would optimize rules to improve performance")
                return True
        
        elif component == "cognitive_load":
            if action == "reduce_load":
                logger.info("Would reduce working memory items to reduce load")
                return True
        
        elif component == "stability":
            if action == "stabilize":
                logger.info("Would reduce feedback strength to stabilize")
                return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about reconfigurations."""
        return {
            "total_applied": len(self.applied_reconfigurations),
            "successful": sum(1 for r in self.applied_reconfigurations if r.get("result", {}).get("success", False)),
            "failed": sum(1 for r in self.applied_reconfigurations if not r.get("result", {}).get("success", False))
        }

