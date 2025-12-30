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
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


class ConflictEvolutionTracker:
    """
    Tracks evolution of conflicts over time.
    
    Provides methods to:
    - Track conflict history between specific memories
    - Get evolution statistics for a memory
    - Analyze resolution trends over time
    """
    
    def xǁConflictEvolutionTrackerǁ__init____mutmut_orig(self, storage: MemoryStorage) -> None:
        """
        Initialize conflict evolution tracker.
        
        Args:
            storage: MemoryStorage instance (contains conflict_log table)
        """
        self.storage = storage
        logger.info("Initialized ConflictEvolutionTracker")
    
    def xǁConflictEvolutionTrackerǁ__init____mutmut_1(self, storage: MemoryStorage) -> None:
        """
        Initialize conflict evolution tracker.
        
        Args:
            storage: MemoryStorage instance (contains conflict_log table)
        """
        self.storage = None
        logger.info("Initialized ConflictEvolutionTracker")
    
    def xǁConflictEvolutionTrackerǁ__init____mutmut_2(self, storage: MemoryStorage) -> None:
        """
        Initialize conflict evolution tracker.
        
        Args:
            storage: MemoryStorage instance (contains conflict_log table)
        """
        self.storage = storage
        logger.info(None)
    
    def xǁConflictEvolutionTrackerǁ__init____mutmut_3(self, storage: MemoryStorage) -> None:
        """
        Initialize conflict evolution tracker.
        
        Args:
            storage: MemoryStorage instance (contains conflict_log table)
        """
        self.storage = storage
        logger.info("XXInitialized ConflictEvolutionTrackerXX")
    
    def xǁConflictEvolutionTrackerǁ__init____mutmut_4(self, storage: MemoryStorage) -> None:
        """
        Initialize conflict evolution tracker.
        
        Args:
            storage: MemoryStorage instance (contains conflict_log table)
        """
        self.storage = storage
        logger.info("initialized conflictevolutiontracker")
    
    def xǁConflictEvolutionTrackerǁ__init____mutmut_5(self, storage: MemoryStorage) -> None:
        """
        Initialize conflict evolution tracker.
        
        Args:
            storage: MemoryStorage instance (contains conflict_log table)
        """
        self.storage = storage
        logger.info("INITIALIZED CONFLICTEVOLUTIONTRACKER")
    
    xǁConflictEvolutionTrackerǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictEvolutionTrackerǁ__init____mutmut_1': xǁConflictEvolutionTrackerǁ__init____mutmut_1, 
        'xǁConflictEvolutionTrackerǁ__init____mutmut_2': xǁConflictEvolutionTrackerǁ__init____mutmut_2, 
        'xǁConflictEvolutionTrackerǁ__init____mutmut_3': xǁConflictEvolutionTrackerǁ__init____mutmut_3, 
        'xǁConflictEvolutionTrackerǁ__init____mutmut_4': xǁConflictEvolutionTrackerǁ__init____mutmut_4, 
        'xǁConflictEvolutionTrackerǁ__init____mutmut_5': xǁConflictEvolutionTrackerǁ__init____mutmut_5
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictEvolutionTrackerǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁConflictEvolutionTrackerǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁConflictEvolutionTrackerǁ__init____mutmut_orig)
    xǁConflictEvolutionTrackerǁ__init____mutmut_orig.__name__ = 'xǁConflictEvolutionTrackerǁ__init__'
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_orig(
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_1(
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
        cursor = None
        
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_2(
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
        cursor.execute(None, (memory1_id, memory2_id, memory2_id, memory1_id))
        
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_3(
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
        """, None)
        
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_4(
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
        cursor.execute((memory1_id, memory2_id, memory2_id, memory1_id))
        
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_5(
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
        """, )
        
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_6(
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
        
        rows = None
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_7(
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
        history = None
        
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_8(
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
            metadata = None
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_9(
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
            if row[16]:  # metadata column
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_10(
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
                    metadata = None
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_11(
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
                    metadata = json.loads(None)
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_12(
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
                    metadata = json.loads(row[16])
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_13(
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
            
            history.append(None)
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_14(
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
                "XXidXX": row[0],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_15(
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
                "ID": row[0],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_16(
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
                "id": row[1],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_17(
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
                "XXtimestampXX": row[1],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_18(
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
                "TIMESTAMP": row[1],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_19(
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
                "timestamp": row[2],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_20(
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
                "XXmemory1_idXX": row[2],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_21(
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
                "MEMORY1_ID": row[2],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_22(
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
                "memory1_id": row[3],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_23(
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
                "XXmemory2_idXX": row[3],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_24(
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
                "MEMORY2_ID": row[3],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_25(
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
                "memory2_id": row[4],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_26(
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
                "XXconflict_typeXX": row[4],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_27(
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
                "CONFLICT_TYPE": row[4],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_28(
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
                "conflict_type": row[5],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_29(
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
                "XXconfidenceXX": row[5],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_30(
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
                "CONFIDENCE": row[5],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_31(
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
                "confidence": row[6],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_32(
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
                "XXdetection_methodXX": row[6],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_33(
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
                "DETECTION_METHOD": row[6],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_34(
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
                "detection_method": row[7],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_35(
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
                "XXresolution_strategyXX": row[7],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_36(
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
                "RESOLUTION_STRATEGY": row[7],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_37(
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
                "resolution_strategy": row[8],
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
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_38(
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
                "XXresolution_actionXX": row[8],
                "kept_memory_id": row[9],
                "archived_memory_id": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_39(
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
                "RESOLUTION_ACTION": row[8],
                "kept_memory_id": row[9],
                "archived_memory_id": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_40(
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
                "resolution_action": row[9],
                "kept_memory_id": row[9],
                "archived_memory_id": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_41(
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
                "XXkept_memory_idXX": row[9],
                "archived_memory_id": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_42(
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
                "KEPT_MEMORY_ID": row[9],
                "archived_memory_id": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_43(
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
                "kept_memory_id": row[10],
                "archived_memory_id": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_44(
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
                "XXarchived_memory_idXX": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_45(
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
                "ARCHIVED_MEMORY_ID": row[10],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_46(
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
                "archived_memory_id": row[11],
                "merged_memory_id": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_47(
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
                "XXmerged_memory_idXX": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_48(
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
                "MERGED_MEMORY_ID": row[11],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_49(
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
                "merged_memory_id": row[12],
                "user_involved": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_50(
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
                "XXuser_involvedXX": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_51(
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
                "USER_INVOLVED": bool(row[12]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_52(
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
                "user_involved": bool(None),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_53(
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
                "user_involved": bool(row[13]),
                "user_decision": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_54(
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
                "XXuser_decisionXX": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_55(
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
                "USER_DECISION": row[13],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_56(
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
                "user_decision": row[14],
                "rationale": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_57(
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
                "XXrationaleXX": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_58(
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
                "RATIONALE": row[14],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_59(
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
                "rationale": row[15],
                "metadata": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_60(
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
                "XXmetadataXX": metadata
            })
        
        return history
    
    def xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_61(
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
                "METADATA": metadata
            })
        
        return history
    
    xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_1': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_1, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_2': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_2, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_3': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_3, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_4': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_4, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_5': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_5, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_6': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_6, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_7': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_7, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_8': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_8, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_9': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_9, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_10': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_10, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_11': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_11, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_12': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_12, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_13': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_13, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_14': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_14, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_15': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_15, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_16': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_16, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_17': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_17, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_18': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_18, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_19': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_19, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_20': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_20, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_21': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_21, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_22': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_22, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_23': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_23, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_24': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_24, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_25': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_25, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_26': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_26, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_27': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_27, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_28': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_28, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_29': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_29, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_30': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_30, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_31': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_31, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_32': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_32, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_33': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_33, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_34': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_34, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_35': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_35, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_36': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_36, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_37': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_37, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_38': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_38, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_39': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_39, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_40': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_40, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_41': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_41, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_42': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_42, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_43': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_43, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_44': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_44, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_45': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_45, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_46': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_46, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_47': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_47, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_48': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_48, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_49': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_49, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_50': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_50, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_51': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_51, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_52': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_52, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_53': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_53, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_54': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_54, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_55': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_55, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_56': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_56, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_57': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_57, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_58': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_58, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_59': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_59, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_60': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_60, 
        'xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_61': xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_61
    }
    
    def track_conflict_history(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_orig"), object.__getattribute__(self, "xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_mutants"), args, kwargs, self)
        return result 
    
    track_conflict_history.__signature__ = _mutmut_signature(xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_orig)
    xǁConflictEvolutionTrackerǁtrack_conflict_history__mutmut_orig.__name__ = 'xǁConflictEvolutionTrackerǁtrack_conflict_history'
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_orig(
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_1(
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
        cursor = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_2(
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
        cursor.execute(None, (memory_id, memory_id))
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_3(
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
        """, None)
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_4(
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
        cursor.execute((memory_id, memory_id))
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_5(
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
        """, )
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_6(
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
        
        rows = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_7(
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
        
        if rows:
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_8(
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
                "XXtotal_conflictsXX": 0,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_9(
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
                "TOTAL_CONFLICTS": 0,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_10(
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
                "total_conflicts": 1,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_11(
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
                "XXconfidence_historyXX": [],
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_12(
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
                "CONFIDENCE_HISTORY": [],
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_13(
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
                "XXstrategy_changesXX": {},
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_14(
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
                "STRATEGY_CHANGES": {},
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_15(
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
                "XXaction_distributionXX": {}
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_16(
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
                "ACTION_DISTRIBUTION": {}
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_17(
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
        confidence_history = None
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_18(
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
        confidence_history = [row[3] for row in rows]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_19(
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
        conflict_types = None
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_20(
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
        conflict_types = [row[2] for row in rows]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_21(
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
        strategies = None
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_22(
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
        strategies = [row[4] for row in rows]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_23(
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
        actions = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_24(
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
        actions = [row[5] for row in rows]
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_25(
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
        confidence_changes = None
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_26(
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
        if len(confidence_history) >= 1:
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_27(
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
        if len(confidence_history) > 2:
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_28(
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
            for i in range(None, len(confidence_history)):
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_29(
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
            for i in range(1, None):
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_30(
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
            for i in range(len(confidence_history)):
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_31(
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
            for i in range(1, ):
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_32(
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
            for i in range(2, len(confidence_history)):
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_33(
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
                change = None
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_34(
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
                change = confidence_history[i] + confidence_history[i-1]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_35(
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
                change = confidence_history[i] - confidence_history[i + 1]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_36(
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
                change = confidence_history[i] - confidence_history[i-2]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_37(
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
                confidence_changes.append(None)
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_38(
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
                    "XXfromXX": confidence_history[i-1],
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_39(
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
                    "FROM": confidence_history[i-1],
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_40(
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
                    "from": confidence_history[i + 1],
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_41(
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
                    "from": confidence_history[i-2],
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_42(
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
                    "XXtoXX": confidence_history[i],
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_43(
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
                    "TO": confidence_history[i],
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_44(
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
                    "XXchangeXX": change,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_45(
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
                    "CHANGE": change,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_46(
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
                    "XXtimestampXX": rows[i][0]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_47(
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
                    "TIMESTAMP": rows[i][0]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_48(
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
                    "timestamp": rows[i][1]
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_49(
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
        strategy_changes = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_50(
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
        strategy_changes = Counter(None)
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_51(
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
        action_distribution = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_52(
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
        action_distribution = Counter(None)
        
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_53(
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
            "XXtotal_conflictsXX": len(rows),
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_54(
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
            "TOTAL_CONFLICTS": len(rows),
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_55(
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
            "XXconfidence_historyXX": confidence_history,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_56(
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
            "CONFIDENCE_HISTORY": confidence_history,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_57(
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
            "XXconfidence_changesXX": confidence_changes,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_58(
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
            "CONFIDENCE_CHANGES": confidence_changes,
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
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_59(
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
            "XXaverage_confidenceXX": sum(confidence_history) / len(confidence_history) if confidence_history else 0.0,
            "min_confidence": min(confidence_history) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_60(
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
            "AVERAGE_CONFIDENCE": sum(confidence_history) / len(confidence_history) if confidence_history else 0.0,
            "min_confidence": min(confidence_history) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_61(
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
            "average_confidence": sum(confidence_history) * len(confidence_history) if confidence_history else 0.0,
            "min_confidence": min(confidence_history) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_62(
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
            "average_confidence": sum(None) / len(confidence_history) if confidence_history else 0.0,
            "min_confidence": min(confidence_history) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_63(
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
            "average_confidence": sum(confidence_history) / len(confidence_history) if confidence_history else 1.0,
            "min_confidence": min(confidence_history) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_64(
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
            "XXmin_confidenceXX": min(confidence_history) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_65(
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
            "MIN_CONFIDENCE": min(confidence_history) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_66(
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
            "min_confidence": min(None) if confidence_history else 0.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_67(
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
            "min_confidence": min(confidence_history) if confidence_history else 1.0,
            "max_confidence": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_68(
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
            "XXmax_confidenceXX": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_69(
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
            "MAX_CONFIDENCE": max(confidence_history) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_70(
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
            "max_confidence": max(None) if confidence_history else 0.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_71(
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
            "max_confidence": max(confidence_history) if confidence_history else 1.0,
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_72(
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
            "XXconfidence_trendXX": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_73(
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
            "CONFIDENCE_TREND": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_74(
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
            "confidence_trend": "XXincreasingXX" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_75(
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
            "confidence_trend": "INCREASING" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_76(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 or confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_77(
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
            "confidence_trend": "increasing" if len(confidence_changes) >= 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_78(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 1 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_79(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[+1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_80(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-2]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_81(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["XXchangeXX"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_82(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["CHANGE"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_83(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] >= 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_84(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 1 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_85(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "XXdecreasingXX" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_86(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "DECREASING" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_87(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 or confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_88(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) >= 0 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_89(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 1 and confidence_changes[-1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_90(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[+1]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_91(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-2]["change"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_92(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["XXchangeXX"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_93(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["CHANGE"] < 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_94(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] <= 0 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_95(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 1 else "stable",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_96(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "XXstableXX",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_97(
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
            "confidence_trend": "increasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] > 0 else "decreasing" if len(confidence_changes) > 0 and confidence_changes[-1]["change"] < 0 else "STABLE",
            "strategy_changes": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_98(
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
            "XXstrategy_changesXX": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_99(
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
            "STRATEGY_CHANGES": dict(strategy_changes),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_100(
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
            "strategy_changes": dict(None),
            "action_distribution": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_101(
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
            "XXaction_distributionXX": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_102(
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
            "ACTION_DISTRIBUTION": dict(action_distribution),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_103(
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
            "action_distribution": dict(None),
            "conflict_types": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_104(
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
            "XXconflict_typesXX": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_105(
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
            "CONFLICT_TYPES": dict(Counter(conflict_types)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_106(
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
            "conflict_types": dict(None),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_107(
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
            "conflict_types": dict(Counter(None)),
            "first_conflict": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_108(
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
            "XXfirst_conflictXX": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_109(
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
            "FIRST_CONFLICT": rows[0][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_110(
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
            "first_conflict": rows[1][0] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_111(
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
            "first_conflict": rows[0][1] if rows else None,
            "last_conflict": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_112(
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
            "XXlast_conflictXX": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_113(
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
            "LAST_CONFLICT": rows[-1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_114(
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
            "last_conflict": rows[+1][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_115(
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
            "last_conflict": rows[-2][0] if rows else None
        }
    
    def xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_116(
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
            "last_conflict": rows[-1][1] if rows else None
        }
    
    xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_1': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_1, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_2': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_2, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_3': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_3, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_4': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_4, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_5': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_5, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_6': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_6, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_7': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_7, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_8': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_8, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_9': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_9, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_10': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_10, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_11': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_11, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_12': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_12, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_13': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_13, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_14': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_14, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_15': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_15, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_16': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_16, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_17': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_17, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_18': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_18, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_19': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_19, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_20': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_20, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_21': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_21, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_22': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_22, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_23': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_23, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_24': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_24, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_25': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_25, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_26': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_26, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_27': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_27, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_28': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_28, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_29': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_29, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_30': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_30, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_31': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_31, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_32': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_32, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_33': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_33, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_34': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_34, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_35': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_35, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_36': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_36, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_37': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_37, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_38': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_38, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_39': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_39, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_40': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_40, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_41': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_41, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_42': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_42, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_43': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_43, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_44': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_44, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_45': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_45, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_46': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_46, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_47': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_47, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_48': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_48, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_49': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_49, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_50': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_50, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_51': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_51, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_52': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_52, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_53': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_53, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_54': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_54, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_55': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_55, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_56': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_56, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_57': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_57, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_58': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_58, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_59': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_59, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_60': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_60, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_61': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_61, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_62': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_62, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_63': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_63, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_64': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_64, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_65': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_65, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_66': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_66, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_67': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_67, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_68': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_68, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_69': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_69, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_70': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_70, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_71': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_71, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_72': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_72, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_73': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_73, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_74': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_74, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_75': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_75, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_76': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_76, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_77': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_77, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_78': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_78, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_79': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_79, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_80': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_80, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_81': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_81, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_82': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_82, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_83': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_83, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_84': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_84, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_85': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_85, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_86': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_86, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_87': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_87, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_88': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_88, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_89': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_89, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_90': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_90, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_91': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_91, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_92': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_92, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_93': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_93, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_94': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_94, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_95': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_95, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_96': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_96, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_97': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_97, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_98': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_98, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_99': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_99, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_100': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_100, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_101': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_101, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_102': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_102, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_103': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_103, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_104': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_104, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_105': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_105, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_106': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_106, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_107': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_107, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_108': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_108, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_109': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_109, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_110': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_110, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_111': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_111, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_112': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_112, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_113': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_113, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_114': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_114, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_115': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_115, 
        'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_116': xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_116
    }
    
    def get_conflict_evolution_stats(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_orig"), object.__getattribute__(self, "xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_conflict_evolution_stats.__signature__ = _mutmut_signature(xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_orig)
    xǁConflictEvolutionTrackerǁget_conflict_evolution_stats__mutmut_orig.__name__ = 'xǁConflictEvolutionTrackerǁget_conflict_evolution_stats'
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_orig(self) -> Dict[str, Any]:
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_1(self) -> Dict[str, Any]:
        """
        Analyze trends in conflict resolution over time.
        
        Returns:
            Dictionary with resolution trend statistics
        """
        self.storage._ensure_connection()
        cursor = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_2(self) -> Dict[str, Any]:
        """
        Analyze trends in conflict resolution over time.
        
        Returns:
            Dictionary with resolution trend statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Get all conflict resolutions
        cursor.execute(None)
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_3(self) -> Dict[str, Any]:
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
        
        rows = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_4(self) -> Dict[str, Any]:
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
        
        if rows:
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_5(self) -> Dict[str, Any]:
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
                "XXtotal_resolutionsXX": 0,
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_6(self) -> Dict[str, Any]:
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
                "TOTAL_RESOLUTIONS": 0,
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_7(self) -> Dict[str, Any]:
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
                "total_resolutions": 1,
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_8(self) -> Dict[str, Any]:
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
                "XXby_strategyXX": {},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_9(self) -> Dict[str, Any]:
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
                "BY_STRATEGY": {},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_10(self) -> Dict[str, Any]:
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
                "XXby_actionXX": {},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_11(self) -> Dict[str, Any]:
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
                "BY_ACTION": {},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_12(self) -> Dict[str, Any]:
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
                "XXauto_vs_userXX": {"auto": 0, "user": 0},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_13(self) -> Dict[str, Any]:
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
                "AUTO_VS_USER": {"auto": 0, "user": 0},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_14(self) -> Dict[str, Any]:
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
                "auto_vs_user": {"XXautoXX": 0, "user": 0},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_15(self) -> Dict[str, Any]:
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
                "auto_vs_user": {"AUTO": 0, "user": 0},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_16(self) -> Dict[str, Any]:
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
                "auto_vs_user": {"auto": 1, "user": 0},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_17(self) -> Dict[str, Any]:
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
                "auto_vs_user": {"auto": 0, "XXuserXX": 0},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_18(self) -> Dict[str, Any]:
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
                "auto_vs_user": {"auto": 0, "USER": 0},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_19(self) -> Dict[str, Any]:
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
                "auto_vs_user": {"auto": 0, "user": 1},
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_20(self) -> Dict[str, Any]:
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
                "XXtrends_over_timeXX": []
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_21(self) -> Dict[str, Any]:
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
                "TRENDS_OVER_TIME": []
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_22(self) -> Dict[str, Any]:
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
        strategies = None
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_23(self) -> Dict[str, Any]:
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
        strategies = [row[2] for row in rows]
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_24(self) -> Dict[str, Any]:
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
        actions = None
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_25(self) -> Dict[str, Any]:
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
        actions = [row[3] for row in rows]
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_26(self) -> Dict[str, Any]:
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
        user_involved = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_27(self) -> Dict[str, Any]:
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
        user_involved = [bool(None) for row in rows]
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_28(self) -> Dict[str, Any]:
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
        user_involved = [bool(row[4]) for row in rows]
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_29(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_30(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(None)
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_31(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: None)
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_32(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: {"XXtotalXX": 0, "by_strategy": Counter(), "by_action": Counter()})
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_33(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: {"TOTAL": 0, "by_strategy": Counter(), "by_action": Counter()})
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_34(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 1, "by_strategy": Counter(), "by_action": Counter()})
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_35(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "XXby_strategyXX": Counter(), "by_action": Counter()})
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_36(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "BY_STRATEGY": Counter(), "by_action": Counter()})
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_37(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "by_strategy": Counter(), "XXby_actionXX": Counter()})
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_38(self) -> Dict[str, Any]:
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
        trends_by_period: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "by_strategy": Counter(), "BY_ACTION": Counter()})
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_39(self) -> Dict[str, Any]:
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
            timestamp_str = None
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_40(self) -> Dict[str, Any]:
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
            timestamp_str = row[1]
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_41(self) -> Dict[str, Any]:
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
                timestamp = None
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_42(self) -> Dict[str, Any]:
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
                timestamp = datetime.fromisoformat(None)
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_43(self) -> Dict[str, Any]:
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
                period_key = None
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_44(self) -> Dict[str, Any]:
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
                period_key = None
            
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_45(self) -> Dict[str, Any]:
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
                period_key = "XXunknownXX"
            
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_46(self) -> Dict[str, Any]:
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
                period_key = "UNKNOWN"
            
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_47(self) -> Dict[str, Any]:
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
            
            trends_by_period[period_key]["total"] = 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_48(self) -> Dict[str, Any]:
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
            
            trends_by_period[period_key]["total"] -= 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_49(self) -> Dict[str, Any]:
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
            
            trends_by_period[period_key]["XXtotalXX"] += 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_50(self) -> Dict[str, Any]:
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
            
            trends_by_period[period_key]["TOTAL"] += 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_51(self) -> Dict[str, Any]:
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
            
            trends_by_period[period_key]["total"] += 2
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_52(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["by_strategy"][row[1]] = 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_53(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["by_strategy"][row[1]] -= 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_54(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["XXby_strategyXX"][row[1]] += 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_55(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["BY_STRATEGY"][row[1]] += 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_56(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["by_strategy"][row[2]] += 1
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_57(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["by_strategy"][row[1]] += 2
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_58(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["by_action"][row[2]] = 1
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_59(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["by_action"][row[2]] -= 1
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_60(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["XXby_actionXX"][row[2]] += 1
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_61(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["BY_ACTION"][row[2]] += 1
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_62(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["by_action"][row[3]] += 1
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_63(self) -> Dict[str, Any]:
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
            trends_by_period[period_key]["by_action"][row[2]] += 2
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_64(self) -> Dict[str, Any]:
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
        trends_over_time = None
        
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_65(self) -> Dict[str, Any]:
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
                "XXperiodXX": period,
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_66(self) -> Dict[str, Any]:
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
                "PERIOD": period,
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_67(self) -> Dict[str, Any]:
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
                "XXtotalXX": data["total"],
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_68(self) -> Dict[str, Any]:
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
                "TOTAL": data["total"],
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_69(self) -> Dict[str, Any]:
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
                "total": data["XXtotalXX"],
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_70(self) -> Dict[str, Any]:
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
                "total": data["TOTAL"],
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_71(self) -> Dict[str, Any]:
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
                "XXby_strategyXX": dict(data["by_strategy"]),
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_72(self) -> Dict[str, Any]:
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
                "BY_STRATEGY": dict(data["by_strategy"]),
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_73(self) -> Dict[str, Any]:
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
                "by_strategy": dict(None),
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_74(self) -> Dict[str, Any]:
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
                "by_strategy": dict(data["XXby_strategyXX"]),
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_75(self) -> Dict[str, Any]:
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
                "by_strategy": dict(data["BY_STRATEGY"]),
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_76(self) -> Dict[str, Any]:
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
                "XXby_actionXX": dict(data["by_action"])
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_77(self) -> Dict[str, Any]:
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
                "BY_ACTION": dict(data["by_action"])
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_78(self) -> Dict[str, Any]:
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
                "by_action": dict(None)
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_79(self) -> Dict[str, Any]:
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
                "by_action": dict(data["XXby_actionXX"])
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_80(self) -> Dict[str, Any]:
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
                "by_action": dict(data["BY_ACTION"])
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_81(self) -> Dict[str, Any]:
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
            for period, data in sorted(None)
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_82(self) -> Dict[str, Any]:
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
            "XXtotal_resolutionsXX": len(rows),
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_83(self) -> Dict[str, Any]:
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
            "TOTAL_RESOLUTIONS": len(rows),
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
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_84(self) -> Dict[str, Any]:
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
            "XXby_strategyXX": dict(Counter(strategies)),
            "by_action": dict(Counter(actions)),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_85(self) -> Dict[str, Any]:
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
            "BY_STRATEGY": dict(Counter(strategies)),
            "by_action": dict(Counter(actions)),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_86(self) -> Dict[str, Any]:
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
            "by_strategy": dict(None),
            "by_action": dict(Counter(actions)),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_87(self) -> Dict[str, Any]:
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
            "by_strategy": dict(Counter(None)),
            "by_action": dict(Counter(actions)),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_88(self) -> Dict[str, Any]:
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
            "XXby_actionXX": dict(Counter(actions)),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_89(self) -> Dict[str, Any]:
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
            "BY_ACTION": dict(Counter(actions)),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_90(self) -> Dict[str, Any]:
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
            "by_action": dict(None),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_91(self) -> Dict[str, Any]:
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
            "by_action": dict(Counter(None)),
            "auto_vs_user": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_92(self) -> Dict[str, Any]:
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
            "XXauto_vs_userXX": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_93(self) -> Dict[str, Any]:
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
            "AUTO_VS_USER": {
                "auto": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_94(self) -> Dict[str, Any]:
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
                "XXautoXX": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_95(self) -> Dict[str, Any]:
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
                "AUTO": sum(1 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_96(self) -> Dict[str, Any]:
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
                "auto": sum(None),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_97(self) -> Dict[str, Any]:
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
                "auto": sum(2 for u in user_involved if not u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_98(self) -> Dict[str, Any]:
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
                "auto": sum(1 for u in user_involved if u),
                "user": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_99(self) -> Dict[str, Any]:
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
                "XXuserXX": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_100(self) -> Dict[str, Any]:
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
                "USER": sum(1 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_101(self) -> Dict[str, Any]:
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
                "user": sum(None)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_102(self) -> Dict[str, Any]:
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
                "user": sum(2 for u in user_involved if u)
            },
            "trends_over_time": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_103(self) -> Dict[str, Any]:
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
            "XXtrends_over_timeXX": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_104(self) -> Dict[str, Any]:
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
            "TRENDS_OVER_TIME": trends_over_time,
            "most_common_strategy": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_105(self) -> Dict[str, Any]:
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
            "XXmost_common_strategyXX": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_106(self) -> Dict[str, Any]:
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
            "MOST_COMMON_STRATEGY": Counter(strategies).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_107(self) -> Dict[str, Any]:
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
            "most_common_strategy": Counter(strategies).most_common(None)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_108(self) -> Dict[str, Any]:
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
            "most_common_strategy": Counter(None).most_common(1)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_109(self) -> Dict[str, Any]:
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
            "most_common_strategy": Counter(strategies).most_common(2)[0][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_110(self) -> Dict[str, Any]:
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
            "most_common_strategy": Counter(strategies).most_common(1)[1][0] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_111(self) -> Dict[str, Any]:
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
            "most_common_strategy": Counter(strategies).most_common(1)[0][1] if strategies else None,
            "most_common_action": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_112(self) -> Dict[str, Any]:
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
            "XXmost_common_actionXX": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_113(self) -> Dict[str, Any]:
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
            "MOST_COMMON_ACTION": Counter(actions).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_114(self) -> Dict[str, Any]:
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
            "most_common_action": Counter(actions).most_common(None)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_115(self) -> Dict[str, Any]:
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
            "most_common_action": Counter(None).most_common(1)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_116(self) -> Dict[str, Any]:
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
            "most_common_action": Counter(actions).most_common(2)[0][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_117(self) -> Dict[str, Any]:
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
            "most_common_action": Counter(actions).most_common(1)[1][0] if actions else None
        }
    
    def xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_118(self) -> Dict[str, Any]:
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
            "most_common_action": Counter(actions).most_common(1)[0][1] if actions else None
        }
    
    xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_1': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_1, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_2': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_2, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_3': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_3, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_4': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_4, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_5': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_5, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_6': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_6, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_7': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_7, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_8': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_8, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_9': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_9, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_10': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_10, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_11': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_11, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_12': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_12, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_13': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_13, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_14': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_14, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_15': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_15, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_16': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_16, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_17': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_17, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_18': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_18, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_19': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_19, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_20': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_20, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_21': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_21, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_22': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_22, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_23': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_23, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_24': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_24, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_25': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_25, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_26': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_26, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_27': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_27, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_28': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_28, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_29': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_29, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_30': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_30, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_31': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_31, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_32': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_32, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_33': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_33, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_34': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_34, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_35': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_35, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_36': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_36, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_37': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_37, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_38': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_38, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_39': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_39, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_40': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_40, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_41': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_41, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_42': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_42, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_43': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_43, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_44': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_44, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_45': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_45, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_46': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_46, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_47': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_47, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_48': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_48, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_49': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_49, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_50': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_50, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_51': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_51, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_52': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_52, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_53': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_53, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_54': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_54, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_55': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_55, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_56': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_56, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_57': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_57, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_58': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_58, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_59': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_59, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_60': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_60, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_61': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_61, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_62': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_62, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_63': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_63, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_64': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_64, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_65': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_65, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_66': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_66, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_67': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_67, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_68': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_68, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_69': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_69, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_70': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_70, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_71': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_71, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_72': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_72, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_73': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_73, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_74': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_74, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_75': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_75, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_76': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_76, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_77': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_77, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_78': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_78, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_79': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_79, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_80': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_80, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_81': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_81, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_82': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_82, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_83': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_83, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_84': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_84, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_85': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_85, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_86': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_86, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_87': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_87, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_88': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_88, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_89': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_89, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_90': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_90, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_91': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_91, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_92': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_92, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_93': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_93, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_94': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_94, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_95': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_95, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_96': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_96, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_97': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_97, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_98': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_98, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_99': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_99, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_100': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_100, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_101': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_101, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_102': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_102, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_103': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_103, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_104': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_104, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_105': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_105, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_106': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_106, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_107': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_107, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_108': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_108, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_109': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_109, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_110': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_110, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_111': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_111, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_112': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_112, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_113': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_113, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_114': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_114, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_115': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_115, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_116': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_116, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_117': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_117, 
        'xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_118': xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_118
    }
    
    def get_resolution_trends(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_orig"), object.__getattribute__(self, "xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_resolution_trends.__signature__ = _mutmut_signature(xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_orig)
    xǁConflictEvolutionTrackerǁget_resolution_trends__mutmut_orig.__name__ = 'xǁConflictEvolutionTrackerǁget_resolution_trends'

