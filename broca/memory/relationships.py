"""
Relationship management for memory system.

Manages relationships between memories including linking, unlinking,
graph traversal, and auto-detection.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone

from . import MemoryRecord, RelationshipRecord, RelationType
from .storage import MemoryStorage

logger = logging.getLogger(__name__)


class RelationshipManager:
    """
    Manages relationships between memories.
    
    Provides methods for creating, querying, and managing typed relationships
    between memories, including auto-detection based on similarity, conflicts,
    and namespace hierarchy.
    """
    
    def __init__(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        logger.info("Initialized RelationshipManager")
    
    def link(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def unlink(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def get_related(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def get_relationship_graph(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def auto_detect_relationships(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected

