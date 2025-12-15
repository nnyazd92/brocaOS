"""
Conflict and Resolution data models.

Defines the Conflict and Resolution structures for conflict detection and resolution.
"""

from __future__ import annotations

from typing import Optional, Literal
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, field_validator

from .. import MemoryRecord


class Conflict(BaseModel):
    """
    Represents a detected conflict between two memories.
    
    Attributes:
        memory1: First memory in the conflict
        memory2: Second memory in the conflict
        conflict_type: Type of conflict (contradiction, ambiguity, update)
        confidence: Confidence score from 0.0 to 1.0
        evidence: Description of why this is a conflict
        resolution_strategy: Suggested resolution strategy
        detected_at: Timestamp when conflict was detected
        temporal_gap: Time difference between conflicting memories
        temporal_context: Temporal relationship context ("same_period", "different_periods", "unknown")
    """
    
    memory1: MemoryRecord = Field(..., description="First memory in the conflict")
    memory2: MemoryRecord = Field(..., description="Second memory in the conflict")
    conflict_type: Literal["contradiction", "ambiguity", "update"] = Field(
        ..., description="Type of conflict"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0"
    )
    evidence: str = Field(..., min_length=1, description="Description of why this is a conflict")
    resolution_strategy: str = Field(
        ..., description="Suggested resolution strategy"
    )
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when conflict was detected"
    )
    temporal_gap: Optional[timedelta] = Field(
        default=None,
        description="Time difference between conflicting memories"
    )
    temporal_context: Optional[Literal["same_period", "different_periods", "unknown"]] = Field(
        default=None,
        description="Temporal relationship context"
    )
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is in range [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {v}")
        return v


class Resolution(BaseModel):
    """
    Result of conflict resolution.
    
    Attributes:
        action: Resolution action taken
        kept_memory: Memory that was kept (if any)
        archived_memory: Memory that was archived (if any)
        merged_memory: Memory created by merging (if any)
        rationale: Explanation of the resolution
    """
    
    action: Literal["keep_both", "keep_new", "keep_old", "keep_important", "consensus", "merge", "ask_user"] = Field(
        ..., description="Resolution action taken"
    )
    kept_memory: Optional[MemoryRecord] = Field(
        default=None, description="Memory that was kept"
    )
    archived_memory: Optional[MemoryRecord] = Field(
        default=None, description="Memory that was archived"
    )
    merged_memory: Optional[MemoryRecord] = Field(
        default=None, description="Memory created by merging"
    )
    rationale: str = Field(..., min_length=1, description="Explanation of the resolution")

