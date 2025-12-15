"""
Conflict resolution system for memory management.

Provides conflict detection and resolution capabilities for managing
contradictory or ambiguous memories.
"""

from __future__ import annotations

from .models import Conflict, Resolution
from .detection import ConflictDetector
from .strategies import (
    ResolutionStrategy,
    RecencyResolutionStrategy,
    ImportanceResolutionStrategy,
    NamespacePriorityStrategy,
    ConsensusResolutionStrategy,
    SmartMergeStrategy
)
from .resolver import ConflictResolver, ResolutionResult
from .logger import ConflictLogger

__all__ = [
    "Conflict",
    "Resolution",
    "ConflictDetector",
    "ResolutionStrategy",
    "RecencyResolutionStrategy",
    "ImportanceResolutionStrategy",
    "NamespacePriorityStrategy",
    "ConsensusResolutionStrategy",
    "SmartMergeStrategy",
    "ConflictResolver",
    "ResolutionResult",
    "ConflictLogger"
]

