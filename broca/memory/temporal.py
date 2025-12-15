"""
Temporal utilities for memory system.

Provides helper functions for working with memory timestamps and temporal reasoning.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List, Dict
from . import MemoryRecord, RelationType


class TemporalUtils:
    """
    Utility class for temporal operations on memories.
    """
    
    @staticmethod
    def calculate_age(memory: MemoryRecord, reference_time: Optional[datetime] = None) -> timedelta:
        """
        Calculate how old a memory is relative to a reference time.
        
        Args:
            memory: MemoryRecord to calculate age for
            reference_time: Reference time (defaults to current time)
            
        Returns:
            timedelta representing the age of the memory
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        return reference_time - memory.created_at
    
    @staticmethod
    def format_age(memory: MemoryRecord, reference_time: Optional[datetime] = None) -> str:
        """
        Format memory age in human-readable form.
        
        Args:
            memory: MemoryRecord to format age for
            reference_time: Reference time (defaults to current time)
            
        Returns:
            Human-readable age string (e.g., "3 days ago", "2 hours ago")
        """
        age = TemporalUtils.calculate_age(memory, reference_time)
        
        if age.days > 0:
            if age.days == 1:
                return "1 day ago"
            return f"{age.days} days ago"
        elif age.seconds >= 3600:
            hours = age.seconds // 3600
            if hours == 1:
                return "1 hour ago"
            return f"{hours} hours ago"
        elif age.seconds >= 60:
            minutes = age.seconds // 60
            if minutes == 1:
                return "1 minute ago"
            return f"{minutes} minutes ago"
        else:
            return "just now"
    
    @staticmethod
    def is_recent(memory: MemoryRecord, hours: int = 24, reference_time: Optional[datetime] = None) -> bool:
        """
        Check if a memory was created recently.
        
        Args:
            memory: MemoryRecord to check
            hours: Threshold for "recent" in hours
            reference_time: Reference time (defaults to current time)
            
        Returns:
            True if memory was created within the last N hours
        """
        age = TemporalUtils.calculate_age(memory, reference_time)
        return age <= timedelta(hours=hours)
    
    @staticmethod
    def calculate_recency_score(memory: MemoryRecord, max_age: timedelta, reference_time: Optional[datetime] = None) -> float:
        """
        Calculate a recency score for a memory (0.0 = oldest, 1.0 = newest).
        
        Args:
            memory: MemoryRecord to score
            max_age: Maximum age to normalize against
            reference_time: Reference time (defaults to current time)
            
        Returns:
            Recency score between 0.0 and 1.0
        """
        age = TemporalUtils.calculate_age(memory, reference_time)
        if max_age.total_seconds() == 0:
            return 1.0  # All memories are same age
        
        # Normalize: 1.0 for newest (age = 0), 0.0 for oldest (age = max_age)
        age_seconds = age.total_seconds()
        max_age_seconds = max_age.total_seconds()
        
        if age_seconds > max_age_seconds:
            return 0.0
        
        return 1.0 - (age_seconds / max_age_seconds)
    
    @staticmethod
    def get_time_period_description(start: datetime, end: datetime) -> str:
        """
        Get a human-readable description of a time period.
        
        Args:
            start: Start datetime
            end: End datetime
            
        Returns:
            Human-readable period description
        """
        duration = end - start
        
        if duration.days > 0:
            if duration.days == 1:
                return "1 day"
            return f"{duration.days} days"
        elif duration.seconds >= 3600:
            hours = duration.seconds // 3600
            if hours == 1:
                return "1 hour"
            return f"{hours} hours"
        elif duration.seconds >= 60:
            minutes = duration.seconds // 60
            if minutes == 1:
                return "1 minute"
            return f"{minutes} minutes"
        else:
            return "a few seconds"
    
    @staticmethod
    def parse_relative_time_to_absolute(reference_time: datetime, relative_description: str) -> Optional[datetime]:
        """
        Parse a relative time description to absolute datetime.
        Simple implementation - in practice, LLM would handle complex parsing.
        
        Args:
            reference_time: Reference time to calculate from
            relative_description: Relative time description (e.g., "3 days ago")
            
        Returns:
            Absolute datetime if parsing successful, None otherwise
        """
        description = relative_description.lower().strip()
        
        # Simple parsing for common patterns
        if description == "now" or description == "today":
            return reference_time
        elif description == "yesterday":
            return reference_time - timedelta(days=1)
        
        # Try to parse "X days ago" pattern
        import re
        patterns = [
            (r'(\d+)\s+days?\s+ago', lambda m: reference_time - timedelta(days=int(m.group(1)))),
            (r'(\d+)\s+hours?\s+ago', lambda m: reference_time - timedelta(hours=int(m.group(1)))),
            (r'(\d+)\s+weeks?\s+ago', lambda m: reference_time - timedelta(weeks=int(m.group(1)))),
            (r'(\d+)\s+months?\s+ago', lambda m: reference_time - timedelta(days=int(m.group(1)) * 30)),  # Approximate
        ]
        
        for pattern, converter in patterns:
            match = re.match(pattern, description)
            if match:
                try:
                    return converter(match)
                except:
                    continue
        
        return None
    
    @staticmethod
    def compare_memories_by_age(memory1: MemoryRecord, memory2: MemoryRecord) -> int:
        """
        Compare two memories by age (for sorting).
        
        Args:
            memory1: First memory
            memory2: Second memory
            
        Returns:
            -1 if memory1 is older, 1 if memory2 is older, 0 if same age
        """
        if memory1.created_at < memory2.created_at:
            return -1  # memory1 is older
        elif memory1.created_at > memory2.created_at:
            return 1   # memory2 is older
        else:
            return 0   # same age
    
    @staticmethod
    def get_memory_timeline(memories: list[MemoryRecord], max_memories: int = 10) -> list[Tuple[MemoryRecord, str]]:
        """
        Create a timeline of memories with age descriptions.
        
        Args:
            memories: List of memories to create timeline for
            max_memories: Maximum number of memories to include
            
        Returns:
            List of (memory, age_description) tuples sorted by age
        """
        # Sort by creation time (oldest first)
        sorted_memories = sorted(memories, key=lambda m: m.created_at)
        
        # Take only the most recent ones if there are too many
        if len(sorted_memories) > max_memories:
            sorted_memories = sorted_memories[-max_memories:]
        
        # Create timeline with age descriptions
        timeline = []
        for memory in sorted_memories:
            age_desc = TemporalUtils.format_age(memory)
            timeline.append((memory, age_desc))
        
        return timeline


def create_temporal_context(memory: MemoryRecord, include_stats: bool = True) -> dict:
    """
    Create a temporal context dictionary for a memory.
    
    Args:
        memory: MemoryRecord to create context for
        include_stats: Whether to include statistical information
        
    Returns:
        Dictionary with temporal context information
    """
    now = datetime.now(timezone.utc)
    age = now - memory.created_at
    last_used_age = now - memory.last_used_at
    
    context = {
        "created_at": memory.created_at.isoformat(),
        "last_used_at": memory.last_used_at.isoformat(),
        "age_days": age.days + age.seconds / 86400,
        "age_human": TemporalUtils.format_age(memory),
        "last_used_days": last_used_age.days + last_used_age.seconds / 86400,
        "is_recent_24h": TemporalUtils.is_recent(memory, hours=24),
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def topological_sort_by_temporal_relationships(
    memories: List[MemoryRecord],
    relationships: Dict[tuple, RelationType]
) -> List[MemoryRecord]:
    """
    Perform topological sort on memories based on temporal relationships.
    
    Args:
        memories: List of memories to sort
        relationships: Dictionary mapping (source_id, target_id) tuples to RelationType
        
    Returns:
        List of memories in topological order (chronological based on PRECEDES/FOLLOWS)
    """
    from collections import defaultdict, deque
    
    # Build adjacency list and in-degree count
    graph: Dict[int, List[int]] = defaultdict(list)
    in_degree: Dict[int, int] = defaultdict(int)
    memory_by_id: Dict[int, MemoryRecord] = {mem.id: mem for mem in memories if mem.id}
    
    # Initialize in-degrees
    for mem in memories:
        if mem.id:
            in_degree[mem.id] = 0
    
    # Build graph from relationships
    for (source_id, target_id), rel_type in relationships.items():
        if source_id not in memory_by_id or target_id not in memory_by_id:
            continue
        
        if rel_type == RelationType.PRECEDES:
            # source PRECEDES target: source -> target
            graph[source_id].append(target_id)
            in_degree[target_id] += 1
        elif rel_type == RelationType.FOLLOWS:
            # source FOLLOWS target: target -> source (reverse)
            graph[target_id].append(source_id)
            in_degree[source_id] += 1
    
    # Kahn's algorithm for topological sort
    queue = deque([mem_id for mem_id, degree in in_degree.items() if degree == 0])
    result: List[MemoryRecord] = []
    
    while queue:
        node_id = queue.popleft()
        if node_id in memory_by_id:
            result.append(memory_by_id[node_id])
        
        for neighbor in graph[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Add any remaining nodes (cycles or disconnected)
    remaining = [mem for mem in memories if mem.id and mem.id not in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result
