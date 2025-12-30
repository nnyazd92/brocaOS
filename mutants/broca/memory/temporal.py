"""
Temporal utilities for memory system.

Provides helper functions for working with memory timestamps and temporal reasoning.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List, Dict
from . import MemoryRecord, RelationType
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


def x_create_temporal_context__mutmut_orig(memory: MemoryRecord, include_stats: bool = True) -> dict:
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


def x_create_temporal_context__mutmut_1(memory: MemoryRecord, include_stats: bool = False) -> dict:
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


def x_create_temporal_context__mutmut_2(memory: MemoryRecord, include_stats: bool = True) -> dict:
    """
    Create a temporal context dictionary for a memory.
    
    Args:
        memory: MemoryRecord to create context for
        include_stats: Whether to include statistical information
        
    Returns:
        Dictionary with temporal context information
    """
    now = None
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


def x_create_temporal_context__mutmut_3(memory: MemoryRecord, include_stats: bool = True) -> dict:
    """
    Create a temporal context dictionary for a memory.
    
    Args:
        memory: MemoryRecord to create context for
        include_stats: Whether to include statistical information
        
    Returns:
        Dictionary with temporal context information
    """
    now = datetime.now(None)
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


def x_create_temporal_context__mutmut_4(memory: MemoryRecord, include_stats: bool = True) -> dict:
    """
    Create a temporal context dictionary for a memory.
    
    Args:
        memory: MemoryRecord to create context for
        include_stats: Whether to include statistical information
        
    Returns:
        Dictionary with temporal context information
    """
    now = datetime.now(timezone.utc)
    age = None
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


def x_create_temporal_context__mutmut_5(memory: MemoryRecord, include_stats: bool = True) -> dict:
    """
    Create a temporal context dictionary for a memory.
    
    Args:
        memory: MemoryRecord to create context for
        include_stats: Whether to include statistical information
        
    Returns:
        Dictionary with temporal context information
    """
    now = datetime.now(timezone.utc)
    age = now + memory.created_at
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


def x_create_temporal_context__mutmut_6(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
    last_used_age = None
    
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


def x_create_temporal_context__mutmut_7(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
    last_used_age = now + memory.last_used_at
    
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


def x_create_temporal_context__mutmut_8(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
    
    context = None
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_9(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "XXcreated_atXX": memory.created_at.isoformat(),
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


def x_create_temporal_context__mutmut_10(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "CREATED_AT": memory.created_at.isoformat(),
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


def x_create_temporal_context__mutmut_11(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "XXlast_used_atXX": memory.last_used_at.isoformat(),
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


def x_create_temporal_context__mutmut_12(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "LAST_USED_AT": memory.last_used_at.isoformat(),
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


def x_create_temporal_context__mutmut_13(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "XXage_daysXX": age.days + age.seconds / 86400,
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


def x_create_temporal_context__mutmut_14(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "AGE_DAYS": age.days + age.seconds / 86400,
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


def x_create_temporal_context__mutmut_15(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "age_days": age.days - age.seconds / 86400,
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


def x_create_temporal_context__mutmut_16(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "age_days": age.days + age.seconds * 86400,
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


def x_create_temporal_context__mutmut_17(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "age_days": age.days + age.seconds / 86401,
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


def x_create_temporal_context__mutmut_18(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "XXage_humanXX": TemporalUtils.format_age(memory),
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


def x_create_temporal_context__mutmut_19(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "AGE_HUMAN": TemporalUtils.format_age(memory),
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


def x_create_temporal_context__mutmut_20(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "age_human": TemporalUtils.format_age(None),
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


def x_create_temporal_context__mutmut_21(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "XXlast_used_daysXX": last_used_age.days + last_used_age.seconds / 86400,
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


def x_create_temporal_context__mutmut_22(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "LAST_USED_DAYS": last_used_age.days + last_used_age.seconds / 86400,
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


def x_create_temporal_context__mutmut_23(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "last_used_days": last_used_age.days - last_used_age.seconds / 86400,
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


def x_create_temporal_context__mutmut_24(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "last_used_days": last_used_age.days + last_used_age.seconds * 86400,
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


def x_create_temporal_context__mutmut_25(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "last_used_days": last_used_age.days + last_used_age.seconds / 86401,
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


def x_create_temporal_context__mutmut_26(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "XXis_recent_24hXX": TemporalUtils.is_recent(memory, hours=24),
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_27(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "IS_RECENT_24H": TemporalUtils.is_recent(memory, hours=24),
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_28(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_24h": TemporalUtils.is_recent(None, hours=24),
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_29(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_24h": TemporalUtils.is_recent(memory, hours=None),
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_30(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_24h": TemporalUtils.is_recent(hours=24),
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_31(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_24h": TemporalUtils.is_recent(memory, ),
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_32(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_24h": TemporalUtils.is_recent(memory, hours=25),
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_33(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "XXis_recent_7dXX": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_34(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "IS_RECENT_7D": TemporalUtils.is_recent(memory, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_35(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_7d": TemporalUtils.is_recent(None, hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_36(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=None),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_37(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_7d": TemporalUtils.is_recent(hours=24*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_38(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_7d": TemporalUtils.is_recent(memory, ),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_39(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24 / 7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_40(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=25*7),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_41(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        "is_recent_7d": TemporalUtils.is_recent(memory, hours=24*8),
    }
    
    if include_stats:
        context.update({
            "created_date": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_42(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
        context.update(None)
    
    return context


def x_create_temporal_context__mutmut_43(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "XXcreated_dateXX": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_44(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "CREATED_DATE": memory.created_at.date().isoformat(),
            "created_time": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_45(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "XXcreated_timeXX": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_46(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "CREATED_TIME": memory.created_at.time().isoformat()[:8],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_47(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "created_time": memory.created_at.time().isoformat()[:9],
            "timezone": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_48(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "XXtimezoneXX": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_49(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "TIMEZONE": "UTC",
        })
    
    return context


def x_create_temporal_context__mutmut_50(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "timezone": "XXUTCXX",
        })
    
    return context


def x_create_temporal_context__mutmut_51(memory: MemoryRecord, include_stats: bool = True) -> dict:
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
            "timezone": "utc",
        })
    
    return context

x_create_temporal_context__mutmut_mutants : ClassVar[MutantDict] = {
'x_create_temporal_context__mutmut_1': x_create_temporal_context__mutmut_1, 
    'x_create_temporal_context__mutmut_2': x_create_temporal_context__mutmut_2, 
    'x_create_temporal_context__mutmut_3': x_create_temporal_context__mutmut_3, 
    'x_create_temporal_context__mutmut_4': x_create_temporal_context__mutmut_4, 
    'x_create_temporal_context__mutmut_5': x_create_temporal_context__mutmut_5, 
    'x_create_temporal_context__mutmut_6': x_create_temporal_context__mutmut_6, 
    'x_create_temporal_context__mutmut_7': x_create_temporal_context__mutmut_7, 
    'x_create_temporal_context__mutmut_8': x_create_temporal_context__mutmut_8, 
    'x_create_temporal_context__mutmut_9': x_create_temporal_context__mutmut_9, 
    'x_create_temporal_context__mutmut_10': x_create_temporal_context__mutmut_10, 
    'x_create_temporal_context__mutmut_11': x_create_temporal_context__mutmut_11, 
    'x_create_temporal_context__mutmut_12': x_create_temporal_context__mutmut_12, 
    'x_create_temporal_context__mutmut_13': x_create_temporal_context__mutmut_13, 
    'x_create_temporal_context__mutmut_14': x_create_temporal_context__mutmut_14, 
    'x_create_temporal_context__mutmut_15': x_create_temporal_context__mutmut_15, 
    'x_create_temporal_context__mutmut_16': x_create_temporal_context__mutmut_16, 
    'x_create_temporal_context__mutmut_17': x_create_temporal_context__mutmut_17, 
    'x_create_temporal_context__mutmut_18': x_create_temporal_context__mutmut_18, 
    'x_create_temporal_context__mutmut_19': x_create_temporal_context__mutmut_19, 
    'x_create_temporal_context__mutmut_20': x_create_temporal_context__mutmut_20, 
    'x_create_temporal_context__mutmut_21': x_create_temporal_context__mutmut_21, 
    'x_create_temporal_context__mutmut_22': x_create_temporal_context__mutmut_22, 
    'x_create_temporal_context__mutmut_23': x_create_temporal_context__mutmut_23, 
    'x_create_temporal_context__mutmut_24': x_create_temporal_context__mutmut_24, 
    'x_create_temporal_context__mutmut_25': x_create_temporal_context__mutmut_25, 
    'x_create_temporal_context__mutmut_26': x_create_temporal_context__mutmut_26, 
    'x_create_temporal_context__mutmut_27': x_create_temporal_context__mutmut_27, 
    'x_create_temporal_context__mutmut_28': x_create_temporal_context__mutmut_28, 
    'x_create_temporal_context__mutmut_29': x_create_temporal_context__mutmut_29, 
    'x_create_temporal_context__mutmut_30': x_create_temporal_context__mutmut_30, 
    'x_create_temporal_context__mutmut_31': x_create_temporal_context__mutmut_31, 
    'x_create_temporal_context__mutmut_32': x_create_temporal_context__mutmut_32, 
    'x_create_temporal_context__mutmut_33': x_create_temporal_context__mutmut_33, 
    'x_create_temporal_context__mutmut_34': x_create_temporal_context__mutmut_34, 
    'x_create_temporal_context__mutmut_35': x_create_temporal_context__mutmut_35, 
    'x_create_temporal_context__mutmut_36': x_create_temporal_context__mutmut_36, 
    'x_create_temporal_context__mutmut_37': x_create_temporal_context__mutmut_37, 
    'x_create_temporal_context__mutmut_38': x_create_temporal_context__mutmut_38, 
    'x_create_temporal_context__mutmut_39': x_create_temporal_context__mutmut_39, 
    'x_create_temporal_context__mutmut_40': x_create_temporal_context__mutmut_40, 
    'x_create_temporal_context__mutmut_41': x_create_temporal_context__mutmut_41, 
    'x_create_temporal_context__mutmut_42': x_create_temporal_context__mutmut_42, 
    'x_create_temporal_context__mutmut_43': x_create_temporal_context__mutmut_43, 
    'x_create_temporal_context__mutmut_44': x_create_temporal_context__mutmut_44, 
    'x_create_temporal_context__mutmut_45': x_create_temporal_context__mutmut_45, 
    'x_create_temporal_context__mutmut_46': x_create_temporal_context__mutmut_46, 
    'x_create_temporal_context__mutmut_47': x_create_temporal_context__mutmut_47, 
    'x_create_temporal_context__mutmut_48': x_create_temporal_context__mutmut_48, 
    'x_create_temporal_context__mutmut_49': x_create_temporal_context__mutmut_49, 
    'x_create_temporal_context__mutmut_50': x_create_temporal_context__mutmut_50, 
    'x_create_temporal_context__mutmut_51': x_create_temporal_context__mutmut_51
}

def create_temporal_context(*args, **kwargs):
    result = _mutmut_trampoline(x_create_temporal_context__mutmut_orig, x_create_temporal_context__mutmut_mutants, args, kwargs)
    return result 

create_temporal_context.__signature__ = _mutmut_signature(x_create_temporal_context__mutmut_orig)
x_create_temporal_context__mutmut_orig.__name__ = 'x_create_temporal_context'


def x_topological_sort_by_temporal_relationships__mutmut_orig(
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


def x_topological_sort_by_temporal_relationships__mutmut_1(
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
    graph: Dict[int, List[int]] = None
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


def x_topological_sort_by_temporal_relationships__mutmut_2(
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
    graph: Dict[int, List[int]] = defaultdict(None)
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


def x_topological_sort_by_temporal_relationships__mutmut_3(
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
    in_degree: Dict[int, int] = None
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


def x_topological_sort_by_temporal_relationships__mutmut_4(
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
    in_degree: Dict[int, int] = defaultdict(None)
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


def x_topological_sort_by_temporal_relationships__mutmut_5(
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
    memory_by_id: Dict[int, MemoryRecord] = None
    
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


def x_topological_sort_by_temporal_relationships__mutmut_6(
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
            in_degree[mem.id] = None
    
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


def x_topological_sort_by_temporal_relationships__mutmut_7(
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
            in_degree[mem.id] = 1
    
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


def x_topological_sort_by_temporal_relationships__mutmut_8(
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
        if source_id not in memory_by_id and target_id not in memory_by_id:
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


def x_topological_sort_by_temporal_relationships__mutmut_9(
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
        if source_id in memory_by_id or target_id not in memory_by_id:
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


def x_topological_sort_by_temporal_relationships__mutmut_10(
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
        if source_id not in memory_by_id or target_id in memory_by_id:
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


def x_topological_sort_by_temporal_relationships__mutmut_11(
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
            break
        
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


def x_topological_sort_by_temporal_relationships__mutmut_12(
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
        
        if rel_type != RelationType.PRECEDES:
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


def x_topological_sort_by_temporal_relationships__mutmut_13(
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
            graph[source_id].append(None)
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


def x_topological_sort_by_temporal_relationships__mutmut_14(
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
            in_degree[target_id] = 1
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


def x_topological_sort_by_temporal_relationships__mutmut_15(
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
            in_degree[target_id] -= 1
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


def x_topological_sort_by_temporal_relationships__mutmut_16(
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
            in_degree[target_id] += 2
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


def x_topological_sort_by_temporal_relationships__mutmut_17(
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
        elif rel_type != RelationType.FOLLOWS:
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


def x_topological_sort_by_temporal_relationships__mutmut_18(
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
            graph[target_id].append(None)
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


def x_topological_sort_by_temporal_relationships__mutmut_19(
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
            in_degree[source_id] = 1
    
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


def x_topological_sort_by_temporal_relationships__mutmut_20(
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
            in_degree[source_id] -= 1
    
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


def x_topological_sort_by_temporal_relationships__mutmut_21(
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
            in_degree[source_id] += 2
    
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


def x_topological_sort_by_temporal_relationships__mutmut_22(
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
    queue = None
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


def x_topological_sort_by_temporal_relationships__mutmut_23(
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
    queue = deque(None)
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


def x_topological_sort_by_temporal_relationships__mutmut_24(
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
    queue = deque([mem_id for mem_id, degree in in_degree.items() if degree != 0])
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


def x_topological_sort_by_temporal_relationships__mutmut_25(
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
    queue = deque([mem_id for mem_id, degree in in_degree.items() if degree == 1])
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


def x_topological_sort_by_temporal_relationships__mutmut_26(
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
    result: List[MemoryRecord] = None
    
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


def x_topological_sort_by_temporal_relationships__mutmut_27(
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
        node_id = None
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


def x_topological_sort_by_temporal_relationships__mutmut_28(
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
        if node_id not in memory_by_id:
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


def x_topological_sort_by_temporal_relationships__mutmut_29(
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
            result.append(None)
        
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


def x_topological_sort_by_temporal_relationships__mutmut_30(
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
            in_degree[neighbor] = 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Add any remaining nodes (cycles or disconnected)
    remaining = [mem for mem in memories if mem.id and mem.id not in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_31(
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
            in_degree[neighbor] += 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Add any remaining nodes (cycles or disconnected)
    remaining = [mem for mem in memories if mem.id and mem.id not in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_32(
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
            in_degree[neighbor] -= 2
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Add any remaining nodes (cycles or disconnected)
    remaining = [mem for mem in memories if mem.id and mem.id not in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_33(
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
            if in_degree[neighbor] != 0:
                queue.append(neighbor)
    
    # Add any remaining nodes (cycles or disconnected)
    remaining = [mem for mem in memories if mem.id and mem.id not in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_34(
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
            if in_degree[neighbor] == 1:
                queue.append(neighbor)
    
    # Add any remaining nodes (cycles or disconnected)
    remaining = [mem for mem in memories if mem.id and mem.id not in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_35(
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
                queue.append(None)
    
    # Add any remaining nodes (cycles or disconnected)
    remaining = [mem for mem in memories if mem.id and mem.id not in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_36(
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
    remaining = None
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_37(
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
    remaining = [mem for mem in memories if mem.id or mem.id not in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_38(
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
    remaining = [mem for mem in memories if mem.id and mem.id in [m.id for m in result if m.id]]
    if remaining:
        # Sort remaining by created_at as fallback
        remaining.sort(key=lambda m: m.created_at)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_39(
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
        remaining.sort(key=None)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_40(
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
        remaining.sort(key=lambda m: None)
        result.extend(remaining)
    
    return result


def x_topological_sort_by_temporal_relationships__mutmut_41(
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
        result.extend(None)
    
    return result

x_topological_sort_by_temporal_relationships__mutmut_mutants : ClassVar[MutantDict] = {
'x_topological_sort_by_temporal_relationships__mutmut_1': x_topological_sort_by_temporal_relationships__mutmut_1, 
    'x_topological_sort_by_temporal_relationships__mutmut_2': x_topological_sort_by_temporal_relationships__mutmut_2, 
    'x_topological_sort_by_temporal_relationships__mutmut_3': x_topological_sort_by_temporal_relationships__mutmut_3, 
    'x_topological_sort_by_temporal_relationships__mutmut_4': x_topological_sort_by_temporal_relationships__mutmut_4, 
    'x_topological_sort_by_temporal_relationships__mutmut_5': x_topological_sort_by_temporal_relationships__mutmut_5, 
    'x_topological_sort_by_temporal_relationships__mutmut_6': x_topological_sort_by_temporal_relationships__mutmut_6, 
    'x_topological_sort_by_temporal_relationships__mutmut_7': x_topological_sort_by_temporal_relationships__mutmut_7, 
    'x_topological_sort_by_temporal_relationships__mutmut_8': x_topological_sort_by_temporal_relationships__mutmut_8, 
    'x_topological_sort_by_temporal_relationships__mutmut_9': x_topological_sort_by_temporal_relationships__mutmut_9, 
    'x_topological_sort_by_temporal_relationships__mutmut_10': x_topological_sort_by_temporal_relationships__mutmut_10, 
    'x_topological_sort_by_temporal_relationships__mutmut_11': x_topological_sort_by_temporal_relationships__mutmut_11, 
    'x_topological_sort_by_temporal_relationships__mutmut_12': x_topological_sort_by_temporal_relationships__mutmut_12, 
    'x_topological_sort_by_temporal_relationships__mutmut_13': x_topological_sort_by_temporal_relationships__mutmut_13, 
    'x_topological_sort_by_temporal_relationships__mutmut_14': x_topological_sort_by_temporal_relationships__mutmut_14, 
    'x_topological_sort_by_temporal_relationships__mutmut_15': x_topological_sort_by_temporal_relationships__mutmut_15, 
    'x_topological_sort_by_temporal_relationships__mutmut_16': x_topological_sort_by_temporal_relationships__mutmut_16, 
    'x_topological_sort_by_temporal_relationships__mutmut_17': x_topological_sort_by_temporal_relationships__mutmut_17, 
    'x_topological_sort_by_temporal_relationships__mutmut_18': x_topological_sort_by_temporal_relationships__mutmut_18, 
    'x_topological_sort_by_temporal_relationships__mutmut_19': x_topological_sort_by_temporal_relationships__mutmut_19, 
    'x_topological_sort_by_temporal_relationships__mutmut_20': x_topological_sort_by_temporal_relationships__mutmut_20, 
    'x_topological_sort_by_temporal_relationships__mutmut_21': x_topological_sort_by_temporal_relationships__mutmut_21, 
    'x_topological_sort_by_temporal_relationships__mutmut_22': x_topological_sort_by_temporal_relationships__mutmut_22, 
    'x_topological_sort_by_temporal_relationships__mutmut_23': x_topological_sort_by_temporal_relationships__mutmut_23, 
    'x_topological_sort_by_temporal_relationships__mutmut_24': x_topological_sort_by_temporal_relationships__mutmut_24, 
    'x_topological_sort_by_temporal_relationships__mutmut_25': x_topological_sort_by_temporal_relationships__mutmut_25, 
    'x_topological_sort_by_temporal_relationships__mutmut_26': x_topological_sort_by_temporal_relationships__mutmut_26, 
    'x_topological_sort_by_temporal_relationships__mutmut_27': x_topological_sort_by_temporal_relationships__mutmut_27, 
    'x_topological_sort_by_temporal_relationships__mutmut_28': x_topological_sort_by_temporal_relationships__mutmut_28, 
    'x_topological_sort_by_temporal_relationships__mutmut_29': x_topological_sort_by_temporal_relationships__mutmut_29, 
    'x_topological_sort_by_temporal_relationships__mutmut_30': x_topological_sort_by_temporal_relationships__mutmut_30, 
    'x_topological_sort_by_temporal_relationships__mutmut_31': x_topological_sort_by_temporal_relationships__mutmut_31, 
    'x_topological_sort_by_temporal_relationships__mutmut_32': x_topological_sort_by_temporal_relationships__mutmut_32, 
    'x_topological_sort_by_temporal_relationships__mutmut_33': x_topological_sort_by_temporal_relationships__mutmut_33, 
    'x_topological_sort_by_temporal_relationships__mutmut_34': x_topological_sort_by_temporal_relationships__mutmut_34, 
    'x_topological_sort_by_temporal_relationships__mutmut_35': x_topological_sort_by_temporal_relationships__mutmut_35, 
    'x_topological_sort_by_temporal_relationships__mutmut_36': x_topological_sort_by_temporal_relationships__mutmut_36, 
    'x_topological_sort_by_temporal_relationships__mutmut_37': x_topological_sort_by_temporal_relationships__mutmut_37, 
    'x_topological_sort_by_temporal_relationships__mutmut_38': x_topological_sort_by_temporal_relationships__mutmut_38, 
    'x_topological_sort_by_temporal_relationships__mutmut_39': x_topological_sort_by_temporal_relationships__mutmut_39, 
    'x_topological_sort_by_temporal_relationships__mutmut_40': x_topological_sort_by_temporal_relationships__mutmut_40, 
    'x_topological_sort_by_temporal_relationships__mutmut_41': x_topological_sort_by_temporal_relationships__mutmut_41
}

def topological_sort_by_temporal_relationships(*args, **kwargs):
    result = _mutmut_trampoline(x_topological_sort_by_temporal_relationships__mutmut_orig, x_topological_sort_by_temporal_relationships__mutmut_mutants, args, kwargs)
    return result 

topological_sort_by_temporal_relationships.__signature__ = _mutmut_signature(x_topological_sort_by_temporal_relationships__mutmut_orig)
x_topological_sort_by_temporal_relationships__mutmut_orig.__name__ = 'x_topological_sort_by_temporal_relationships'
