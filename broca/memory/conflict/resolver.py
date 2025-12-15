"""
Conflict resolution orchestrator.

Orchestrates conflict detection and resolution using a strategy chain.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .models import Conflict, Resolution
from .strategies import (
    RecencyResolutionStrategy,
    ImportanceResolutionStrategy,
    NamespacePriorityStrategy,
    ConsensusResolutionStrategy,
    SmartMergeStrategy,
    ResolutionStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class ResolutionResult:
    """Result of conflict resolution."""
    conflict: Conflict
    resolution: Resolution
    strategy_used: str


class ConflictResolver:
    """
    Orchestrates conflict detection and resolution.
    
    Uses a strategy chain to resolve conflicts in priority order.
    """
    
    def __init__(
        self,
        memory_manager: Optional[Any] = None,
        ask_user_threshold: float = 0.7
    ) -> None:
        """
        Initialize conflict resolver.
        
        Args:
            memory_manager: Optional MemoryManager for strategies that need it
            ask_user_threshold: Confidence threshold below which to ask user
        """
        self.memory_manager = memory_manager
        self.ask_user_threshold = ask_user_threshold
        
        # Strategy chain in priority order
        self.strategy_chain: List[tuple[str, ResolutionStrategy]] = [
            ("namespace_priority", NamespacePriorityStrategy()),
            ("recency", RecencyResolutionStrategy()),
            ("importance", ImportanceResolutionStrategy()),
            ("consensus", ConsensusResolutionStrategy(memory_manager=memory_manager)),
            ("smart_merge", SmartMergeStrategy()),
        ]
        
        logger.info(f"Initialized ConflictResolver (ask_user_threshold={ask_user_threshold})")
    
    def resolve_conflicts(
        self,
        conflicts: List[Conflict],
        auto_resolve: bool = False,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[ResolutionResult]:
        """
        Apply resolution strategies to conflicts.
        
        Args:
            conflicts: List of conflicts to resolve
            auto_resolve: Whether to automatically resolve without user input
            user_context: Optional user context for resolution
            
        Returns:
            List of ResolutionResult objects
        """
        results: List[ResolutionResult] = []
        
        for conflict in conflicts:
            resolution = self._resolve_single_conflict(
                conflict,
                auto_resolve=auto_resolve,
                user_context=user_context
            )
            
            if resolution:
                results.append(ResolutionResult(
                    conflict=conflict,
                    resolution=resolution,
                    strategy_used=conflict.resolution_strategy
                ))
        
        return results
    
    def _resolve_single_conflict(
        self,
        conflict: Conflict,
        auto_resolve: bool = False,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Resolution]:
        """
        Resolve a single conflict.
        
        Args:
            conflict: Conflict to resolve
            auto_resolve: Whether to auto-resolve
            user_context: Optional user context
            
        Returns:
            Resolution object, or None if user input required
        """
        # Check if we need user confirmation
        if not auto_resolve and conflict.confidence < self.ask_user_threshold:
            # Return resolution that asks user
            return Resolution(
                action="ask_user",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale=f"Low confidence ({conflict.confidence:.2f}) requires user confirmation"
            )
        
        # Try strategies in order based on conflict's suggested strategy
        strategy_name = conflict.resolution_strategy
        
        # Find strategy by name
        strategy = None
        for name, strat in self.strategy_chain:
            if name == strategy_name:
                strategy = strat
                break
        
        # If not found, use first strategy in chain
        if strategy is None:
            strategy = self.strategy_chain[0][1]
        
        try:
            resolution = strategy.resolve(conflict, user_context or {})
            return resolution
        except Exception as e:
            logger.warning(f"Error resolving conflict with {strategy_name}: {e}", exc_info=True)
            
            # Fallback to recency strategy
            fallback_strategy = RecencyResolutionStrategy()
            return fallback_strategy.resolve(conflict, user_context or {})

