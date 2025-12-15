"""
Conflict logging and audit system.

Logs all conflict detection and resolution activities for audit and undo.
"""

from __future__ import annotations

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .models import Conflict, Resolution

logger = logging.getLogger(__name__)


class ConflictLogger:
    """
    Logs conflict detection and resolution activities.
    
    Stores conflict logs in the same database as memories for consistency.
    """
    
    def __init__(self, storage: Any) -> None:
        """
        Initialize conflict logger.
        
        Args:
            storage: MemoryStorage instance (will add conflict tables)
        """
        self.storage = storage
        self._ensure_tables()
        logger.info("Initialized ConflictLogger")
    
    def _ensure_tables(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def log_conflict(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def get_conflict_stats(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def get_undo_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def get_resolution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]

