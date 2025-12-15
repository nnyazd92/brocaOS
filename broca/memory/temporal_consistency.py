"""
Temporal consistency checking for memory relationships.

Validates that temporal relationships (PRECEDES/FOLLOWS) are consistent
with actual temporal ordering and don't form cycles.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timezone

from . import MemoryRecord, RelationType
from .storage import MemoryStorage

logger = logging.getLogger(__name__)


class TemporalConsistencyChecker:
    """
    Checks temporal consistency of memory relationships.
    
    Validates:
    - No cycles in PRECEDES/FOLLOWS graph
    - Temporal relationships match created_at/valid_from ordering
    - No contradictory temporal relationships
    """
    
    def __init__(self, storage: MemoryStorage) -> None:
        """
        Initialize temporal consistency checker.
        
        Args:
            storage: MemoryStorage instance for querying relationships
        """
        self.storage = storage
        logger.info("Initialized TemporalConsistencyChecker")
    
    def check_consistency(self, memory_id: Optional[int] = None) -> List[str]:
        """
        Check for temporal consistency issues.
        
        Args:
            memory_id: Optional specific memory ID to check. If None, checks all memories.
            
        Returns:
            List of inconsistency descriptions (empty if all consistent)
        """
        inconsistencies: List[str] = []
        
        # Check for cycles
        cycles = self._detect_cycles(memory_id)
        for cycle in cycles:
            inconsistencies.append(f"Temporal cycle detected: {' -> '.join(map(str, cycle))}")
        
        # Check temporal ordering
        ordering_issues = self._check_temporal_ordering(memory_id)
        inconsistencies.extend(ordering_issues)
        
        return inconsistencies
    
    def validate_temporal_relationships(self, memory_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Comprehensive validation of temporal relationships.
        
        Args:
            memory_id: Optional specific memory ID to validate. If None, validates all.
            
        Returns:
            Dictionary with validation results:
            - consistent: bool
            - cycles: List of cycle descriptions
            - ordering_issues: List of ordering problems
            - contradictions: List of temporal contradictions
        """
        cycles = self._detect_cycles(memory_id)
        ordering_issues = self._check_temporal_ordering(memory_id)
        contradictions = self._find_temporal_contradictions(memory_id)
        
        consistent = len(cycles) == 0 and len(ordering_issues) == 0 and len(contradictions) == 0
        
        return {
            "consistent": consistent,
            "cycles": cycles,
            "ordering_issues": ordering_issues,
            "contradictions": contradictions,
            "total_issues": len(cycles) + len(ordering_issues) + len(contradictions)
        }
    
    def _detect_cycles(self, memory_id: Optional[int] = None) -> List[List[int]]:
        """
        Detect cycles in PRECEDES/FOLLOWS graph using DFS.
        
        Args:
            memory_id: Optional starting memory ID. If None, checks all memories.
            
        Returns:
            List of cycles (each cycle is a list of memory IDs)
        """
        # Get all temporal relationships
        temporal_relationships = self._get_temporal_relationships(memory_id)
        
        # Build adjacency list
        graph: Dict[int, List[int]] = {}
        for rel in temporal_relationships:
            source_id = rel["source_id"]
            target_id = rel["target_id"]
            relation_type = rel["relation_type"]
            
            if relation_type in [RelationType.PRECEDES.value, RelationType.FOLLOWS.value]:
                # For PRECEDES: source -> target
                # For FOLLOWS: source <- target (reverse)
                if relation_type == RelationType.PRECEDES.value:
                    if source_id not in graph:
                        graph[source_id] = []
                    graph[source_id].append(target_id)
                else:  # FOLLOWS
                    if target_id not in graph:
                        graph[target_id] = []
                    graph[target_id].append(source_id)
        
        # DFS to detect cycles
        cycles: List[List[int]] = []
        visited: Set[int] = set()
        rec_stack: Set[int] = set()
        path: List[int] = []
        
        def dfs(node: int) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle detected - find the cycle path
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle.copy())
            
            rec_stack.remove(node)
            path.pop()
        
        # Start DFS from each unvisited node
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def _check_temporal_ordering(self, memory_id: Optional[int] = None) -> List[str]:
        """
        Check that PRECEDES/FOLLOWS relationships match temporal ordering.
        
        Args:
            memory_id: Optional specific memory ID to check.
            
        Returns:
            List of ordering issue descriptions
        """
        issues: List[str] = []
        temporal_relationships = self._get_temporal_relationships(memory_id)
        
        for rel in temporal_relationships:
            source_id = rel["source_id"]
            target_id = rel["target_id"]
            relation_type = rel["relation_type"]
            
            if relation_type not in [RelationType.PRECEDES.value, RelationType.FOLLOWS.value]:
                continue
            
            # Get memory records
            source_mem = self.storage.get_memory(source_id)
            target_mem = self.storage.get_memory(target_id)
            
            if not source_mem or not target_mem:
                continue
            
            # Determine expected temporal ordering
            source_time = source_mem.valid_from if source_mem.valid_from else source_mem.created_at
            target_time = target_mem.valid_from if target_mem.valid_from else target_mem.created_at
            
            # Check if relationship matches temporal ordering
            if relation_type == RelationType.PRECEDES.value:
                # PRECEDES means source should be before target
                if source_time >= target_time:
                    issues.append(
                        f"Temporal ordering violation: Memory {source_id} PRECEDES {target_id} "
                        f"but {source_time} >= {target_time}"
                    )
            else:  # FOLLOWS
                # FOLLOWS means source should be after target
                if source_time <= target_time:
                    issues.append(
                        f"Temporal ordering violation: Memory {source_id} FOLLOWS {target_id} "
                        f"but {source_time} <= {target_time}"
                    )
        
        return issues
    
    def _find_temporal_contradictions(self, memory_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find memories with conflicting temporal relationships.
        
        Args:
            memory_id: Optional specific memory ID to check.
            
        Returns:
            List of contradiction dictionaries
        """
        contradictions: List[Dict[str, Any]] = []
        temporal_relationships = self._get_temporal_relationships(memory_id)
        
        # Group relationships by memory pairs
        relationships_by_pair: Dict[tuple, List[Dict]] = {}
        for rel in temporal_relationships:
            pair = tuple(sorted([rel["source_id"], rel["target_id"]]))
            if pair not in relationships_by_pair:
                relationships_by_pair[pair] = []
            relationships_by_pair[pair].append(rel)
        
        # Check for contradictory relationships (e.g., A PRECEDES B and B PRECEDES A)
        for pair, rels in relationships_by_pair.items():
            if len(rels) < 2:
                continue
            
            # Check if we have both PRECEDES and FOLLOWS between same pair
            has_precedes = any(r["relation_type"] == RelationType.PRECEDES.value for r in rels)
            has_follows = any(r["relation_type"] == RelationType.FOLLOWS.value for r in rels)
            
            if has_precedes and has_follows:
                contradictions.append({
                    "memory1_id": pair[0],
                    "memory2_id": pair[1],
                    "issue": "Both PRECEDES and FOLLOWS relationships exist between same memories",
                    "relationships": rels
                })
        
        return contradictions
    
    def _get_temporal_relationships(self, memory_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all temporal relationships (PRECEDES/FOLLOWS).
        
        Args:
            memory_id: Optional memory ID to filter by.
            
        Returns:
            List of relationship dictionaries
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        if memory_id:
            # Get relationships involving this memory
            cursor.execute("""
                SELECT source_id, target_id, relation_type
                FROM memory_relationships
                WHERE (source_id = ? OR target_id = ?)
                AND relation_type IN (?, ?)
            """, (memory_id, memory_id, RelationType.PRECEDES.value, RelationType.FOLLOWS.value))
        else:
            # Get all temporal relationships
            cursor.execute("""
                SELECT source_id, target_id, relation_type
                FROM memory_relationships
                WHERE relation_type IN (?, ?)
            """, (RelationType.PRECEDES.value, RelationType.FOLLOWS.value))
        
        rows = cursor.fetchall()
        return [
            {
                "source_id": row[0],
                "target_id": row[1],
                "relation_type": row[2]
            }
            for row in rows
        ]

