"""
Conflict evolution tracking.

Tracks how conflicts between memories evolve over time, including
confidence changes, resolution strategy changes, and trends.
"""

from __future__ import annotations

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import Counter, defaultdict

from ..storage import MemoryStorage

logger = logging.getLogger(__name__)


class ConflictEvolutionTracker:
    """
    Tracks evolution of conflicts over time.
    
    Provides methods to:
    - Track conflict history between specific memories
    - Get evolution statistics for a memory
    - Analyze resolution trends over time
    """
    
    def __init__(self, storage: MemoryStorage) -> None:
        """
        Initialize conflict evolution tracker.
        
        Args:
            storage: MemoryStorage instance (contains conflict_log table)
        """
        self.storage = storage
        logger.info("Initialized ConflictEvolutionTracker")
    
    def track_conflict_history(
        self,
        memory1_id: int,
        memory2_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get history of conflicts between two memories.
        
        Args:
            memory1_id: ID of first memory
            memory2_id: ID of second memory
            
        Returns:
            List of conflict history records, ordered chronologically (oldest first)
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Query conflict_log for all conflicts between these memories (in either direction)
        cursor.execute("""
            SELECT id, timestamp, memory1_id, memory2_id, conflict_type, confidence,
                   detection_method, resolution_strategy, resolution_action,
                   kept_memory_id, archived_memory_id, merged_memory_id,
                   user_involved, user_decision, rationale, metadata
            FROM conflict_log
            WHERE (memory1_id = ? AND memory2_id = ?)
               OR (memory1_id = ? AND memory2_id = ?)
            ORDER BY timestamp ASC
        """, (memory1_id, memory2_id, memory2_id, memory1_id))
        
        rows = cursor.fetchall()
        history = []
        
        for row in rows:
            metadata = {}
            if row[15]:  # metadata column
                try:
                    metadata = json.loads(row[15])
                except (json.JSONDecodeError, TypeError):
                    pass
            
            history.append({
                "id": row[0],
                "timestamp": row[1],
                "memory1_id": row[2],
                "memory2_id": row[3],
                "conflict_type": row[4],
                "confidence": row[5],
                "detection_method": row[6],
                "resolution_strategy": row[7],
                "resolution_action": row[8],
                "kept_memory_id": row[9],
                "archived_memory_id": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def get_conflict_evolution_stats(
        self,
        memory_id: int
    ) -> Dict[str, Any]:
        """
        Get statistics about how conflicts involving a memory evolved.
        
        Args:
            memory_id: ID of memory to analyze
            
        Returns:
            Dictionary with evolution statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Get all conflicts involving this memory
        cursor.execute("""
            SELECT timestamp, conflict_type, confidence, resolution_strategy, resolution_action
            FROM conflict_log
            WHERE memory1_id = ? OR memory2_id = ?
            ORDER BY timestamp ASC
        """, (memory_id, memory_id))
        
        rows = cursor.fetchall()
        
        if not rows:
            return {
                "total_conflicts": 0,
                "confidence_history": [],
                "strategy_changes": {},
                "action_distribution": {}
            }
        
        # Analyze evolution
        confidence_history = [row[2] for row in rows]
        conflict_types = [row[1] for row in rows]
        strategies = [row[3] for row in rows]
        actions = [row[4] for row in rows]
        
        # Calculate confidence changes
        confidence_changes = []
        if len(confidence_history) > 1:
            for i in range(1, len(confidence_history)):
                change = confidence_history[i] - confidence_history[i-1]
                confidence_changes.append({
                    "from": confidence_history[i-1],
                    "to": confidence_history[i],
                    "change": change,
                    "timestamp": rows[i][0]
                })
        
        # Strategy changes
        strategy_changes = Counter(strategies)
        
        # Action distribution
        action_distribution = Counter(actions)
        
        return {
            "total_conflicts": len(rows),
            "confidence_history": confidence_history,
            "confidence_changes": confidence_changes,
            "average_confidence": sum(confidence_history) / len(confidence_history) if confidence_history else 0.0,
            "min_confidence": min(confidence_history) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def get_resolution_trends(self) -> Dict[str, Any]:
        """
        Analyze trends in conflict resolution over time.
        
        Returns:
            Dictionary with resolution trend statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Get all conflict resolutions
        cursor.execute("""
            SELECT timestamp, resolution_strategy, resolution_action, user_involved
            FROM conflict_log
            ORDER BY timestamp ASC
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            return {
                "total_resolutions": 0,
                "by_strategy": {},
                "by_action": {},
                "auto_vs_user": {"auto": 0, "user": 0},
                "trends_over_time": []
            }
        
        # Analyze trends
        strategies = [row[1] for row in rows]
        actions = [row[2] for row in rows]
        user_involved = [bool(row[3]) for row in rows]
        
        # Group by time periods (daily for now)
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "by_strategy": Counter(), "by_action": Counter()})
        
        for row in rows:
            timestamp_str = row[0]
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                period_key = timestamp.date().isoformat()
            except (ValueError, AttributeError):
                period_key = "unknown"
            
            trends_by_period[period_key]["total"] += 1
            trends_by_period[period_key]["by_strategy"][row[1]] += 1
            trends_by_period[period_key]["by_action"][row[2]] += 1
        
        # Convert to list format
        trends_over_time = [
            {
                "period": period,
                "total": data["total"],
                "by_strategy": dict(data["by_strategy"]),
                "by_action": dict(data["by_action"])
            }
            for period, data in sorted(trends_by_period.items())
        ]
        
        return {
            "total_resolutions": len(rows),
            "by_strategy": dict(Counter(strategies)),
            "by_action": dict(Counter(actions)),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }

