"""
Z3-based causal chain validator for memory relationships.

Validates causal relationships (CAUSES/CAUSED_BY) in memory
for logical consistency and transitivity.
"""

from __future__ import annotations

import logging
from typing import List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from . import MemoryRecord, RelationType

logger = logging.getLogger(__name__)


class CausalChainValidator:
    """
    Validates causal chains in memory relationships.
    
    Uses Z3 to ensure causal relationships form consistent chains
    without cycles and with proper transitivity.
    """
    
    def __init__(self, enable_z3: bool = True):
        """
        Initialize causal chain validator.
        
        Args:
            enable_z3: Whether to enable Z3 validation
        """
        self.z3_validator = None
        if enable_z3:
            try:
                from ..reasoning.z3_validator import Z3LogicalValidator
                from ..config import config
                self.z3_validator = Z3LogicalValidator(
                    enable_z3=config.reasoning.z3_validation_enabled,
                    timeout=config.reasoning.z3_validation_timeout,
                    max_constraints=config.reasoning.z3_max_constraints
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Z3 validator for causal chains: {e}")
                self.z3_validator = None
    
    def validate_causal_chain(
        self,
        memories: List["MemoryRecord"],
        relationships: List[Tuple[int, int, "RelationType"]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate causal relationships form a consistent chain.
        
        Args:
            memories: List of memory records
            relationships: List of (source_id, target_id, relation_type) tuples
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.z3_validator or not self.z3_validator.enabled:
            return True, None
        
        # Extract causal relationships
        causal_chain = []
        for source_id, target_id, rel_type in relationships:
            if rel_type.value in ("causes", "caused_by"):
                source_mem = next((m for m in memories if m.id == source_id), None)
                target_mem = next((m for m in memories if m.id == target_id), None)
                if source_mem and target_mem:
                    # Normalize to (cause, effect) format
                    if rel_type.value == "causes":
                        causal_chain.append((
                            f"memory_{source_id}",
                            f"memory_{target_id}"
                        ))
                    else:  # caused_by
                        causal_chain.append((
                            f"memory_{target_id}",
                            f"memory_{source_id}"
                        ))
        
        if not causal_chain:
            return True, None
        
        is_valid, error, warnings = self.z3_validator.validate_causal_chain(
            causal_chain,
            check_transitivity=True
        )
        
        if not is_valid:
            logger.warning(f"Causal chain validation failed: {error}")
            for warning in warnings:
                logger.warning(f"Causal chain warning: {warning}")
        
        return is_valid, error
    
    def validate_single_causal_relationship(
        self,
        source_id: int,
        target_id: int,
        existing_relationships: List[Tuple[int, int, "RelationType"]],
        existing_memories: List["MemoryRecord"]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a single causal relationship before adding it.
        
        Args:
            source_id: Source memory ID
            target_id: Target memory ID
            existing_relationships: Existing relationships to check against
            existing_memories: Existing memory records
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.z3_validator or not self.z3_validator.enabled:
            return True, None
        
        # Check if this would create a cycle
        # Build graph from existing relationships
        graph: dict[int, list[int]] = {}
        for src, tgt, rel_type in existing_relationships:
            if rel_type.value in ("causes", "caused_by"):
                if src not in graph:
                    graph[src] = []
                if rel_type.value == "causes":
                    graph[src].append(tgt)
                else:  # caused_by
                    if tgt not in graph:
                        graph[tgt] = []
                    graph[tgt].append(src)
        
        # Check if adding (source_id, target_id) would create a cycle
        # by checking if there's a path from target_id to source_id
        def has_path(start: int, end: int, visited: set[int]) -> bool:
            if start == end:
                return True
            if start in visited:
                return False
            visited.add(start)
            for neighbor in graph.get(start, []):
                if has_path(neighbor, end, visited):
                    return True
            return False
        
        # Check if target can reach source (would create cycle)
        if has_path(target_id, source_id, set()):
            return False, f"Adding causal relationship {source_id}->{target_id} would create a cycle"
        
        # Validate with full chain
        new_relationships = existing_relationships + [(source_id, target_id, type("RelationType", (), {"value": "causes"})())]
        return self.validate_causal_chain(existing_memories, new_relationships)

