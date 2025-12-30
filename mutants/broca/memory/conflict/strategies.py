"""
Conflict resolution strategies.

Implements various strategies for resolving conflicts between memories.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .. import MemoryRecord
from .models import Conflict, Resolution

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


class ResolutionStrategy(ABC):
    """Base class for conflict resolution strategies."""
    
    @abstractmethod
    def resolve(
        self,
        conflict: Conflict,
        context: Dict[str, Any]
    ) -> Resolution:
        """
        Apply resolution strategy to conflict.
        
        Args:
            conflict: Conflict to resolve
            context: Additional context for resolution
            
        Returns:
            Resolution object with action taken
        """
        pass


class RecencyResolutionStrategy(ResolutionStrategy):
    """Keep the most recent memory."""
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_orig(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_1(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = None
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_2(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(None, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_3(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, None, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_4(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=None)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_5(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_6(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_7(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, )
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_8(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: None)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_9(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = None
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_10(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(None, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_11(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, None, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_12(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=None)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_13(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_14(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_15(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, )
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_16(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: None)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_17(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at != older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_18(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = None
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_19(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(None, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_20(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, None, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_21(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=None)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_22(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_23(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_24(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, )
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_25(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: None)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_26(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = None
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_27(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(None, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_28(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, None, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_29(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=None)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_30(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_31(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_32(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, )
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_33(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: None)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_34(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action=None,
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_35(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=None,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_36(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=None,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_37(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=None
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_38(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_39(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_40(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_41(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_42(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_43(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="XXkeep_importantXX",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_44(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="KEEP_IMPORTANT",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_45(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action=None,
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_46(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=None,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_47(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=None,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_48(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=None
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_49(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_50(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_51(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_52(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_53(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_54(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="XXkeep_newXX",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    def xǁRecencyResolutionStrategyǁresolve__mutmut_55(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the newer memory."""
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        
        # If timestamps are equal, fallback to importance
        if newer.created_at == older.created_at:
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Timestamps equal, keeping higher importance memory ({higher.importance}) over lower ({lower.importance})"
            )
        
        return Resolution(
            action="KEEP_NEW",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=f"Keeping newer memory (created {newer.created_at}) over older one (created {older.created_at})"
        )
    
    xǁRecencyResolutionStrategyǁresolve__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁRecencyResolutionStrategyǁresolve__mutmut_1': xǁRecencyResolutionStrategyǁresolve__mutmut_1, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_2': xǁRecencyResolutionStrategyǁresolve__mutmut_2, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_3': xǁRecencyResolutionStrategyǁresolve__mutmut_3, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_4': xǁRecencyResolutionStrategyǁresolve__mutmut_4, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_5': xǁRecencyResolutionStrategyǁresolve__mutmut_5, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_6': xǁRecencyResolutionStrategyǁresolve__mutmut_6, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_7': xǁRecencyResolutionStrategyǁresolve__mutmut_7, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_8': xǁRecencyResolutionStrategyǁresolve__mutmut_8, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_9': xǁRecencyResolutionStrategyǁresolve__mutmut_9, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_10': xǁRecencyResolutionStrategyǁresolve__mutmut_10, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_11': xǁRecencyResolutionStrategyǁresolve__mutmut_11, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_12': xǁRecencyResolutionStrategyǁresolve__mutmut_12, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_13': xǁRecencyResolutionStrategyǁresolve__mutmut_13, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_14': xǁRecencyResolutionStrategyǁresolve__mutmut_14, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_15': xǁRecencyResolutionStrategyǁresolve__mutmut_15, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_16': xǁRecencyResolutionStrategyǁresolve__mutmut_16, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_17': xǁRecencyResolutionStrategyǁresolve__mutmut_17, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_18': xǁRecencyResolutionStrategyǁresolve__mutmut_18, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_19': xǁRecencyResolutionStrategyǁresolve__mutmut_19, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_20': xǁRecencyResolutionStrategyǁresolve__mutmut_20, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_21': xǁRecencyResolutionStrategyǁresolve__mutmut_21, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_22': xǁRecencyResolutionStrategyǁresolve__mutmut_22, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_23': xǁRecencyResolutionStrategyǁresolve__mutmut_23, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_24': xǁRecencyResolutionStrategyǁresolve__mutmut_24, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_25': xǁRecencyResolutionStrategyǁresolve__mutmut_25, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_26': xǁRecencyResolutionStrategyǁresolve__mutmut_26, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_27': xǁRecencyResolutionStrategyǁresolve__mutmut_27, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_28': xǁRecencyResolutionStrategyǁresolve__mutmut_28, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_29': xǁRecencyResolutionStrategyǁresolve__mutmut_29, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_30': xǁRecencyResolutionStrategyǁresolve__mutmut_30, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_31': xǁRecencyResolutionStrategyǁresolve__mutmut_31, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_32': xǁRecencyResolutionStrategyǁresolve__mutmut_32, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_33': xǁRecencyResolutionStrategyǁresolve__mutmut_33, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_34': xǁRecencyResolutionStrategyǁresolve__mutmut_34, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_35': xǁRecencyResolutionStrategyǁresolve__mutmut_35, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_36': xǁRecencyResolutionStrategyǁresolve__mutmut_36, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_37': xǁRecencyResolutionStrategyǁresolve__mutmut_37, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_38': xǁRecencyResolutionStrategyǁresolve__mutmut_38, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_39': xǁRecencyResolutionStrategyǁresolve__mutmut_39, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_40': xǁRecencyResolutionStrategyǁresolve__mutmut_40, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_41': xǁRecencyResolutionStrategyǁresolve__mutmut_41, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_42': xǁRecencyResolutionStrategyǁresolve__mutmut_42, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_43': xǁRecencyResolutionStrategyǁresolve__mutmut_43, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_44': xǁRecencyResolutionStrategyǁresolve__mutmut_44, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_45': xǁRecencyResolutionStrategyǁresolve__mutmut_45, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_46': xǁRecencyResolutionStrategyǁresolve__mutmut_46, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_47': xǁRecencyResolutionStrategyǁresolve__mutmut_47, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_48': xǁRecencyResolutionStrategyǁresolve__mutmut_48, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_49': xǁRecencyResolutionStrategyǁresolve__mutmut_49, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_50': xǁRecencyResolutionStrategyǁresolve__mutmut_50, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_51': xǁRecencyResolutionStrategyǁresolve__mutmut_51, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_52': xǁRecencyResolutionStrategyǁresolve__mutmut_52, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_53': xǁRecencyResolutionStrategyǁresolve__mutmut_53, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_54': xǁRecencyResolutionStrategyǁresolve__mutmut_54, 
        'xǁRecencyResolutionStrategyǁresolve__mutmut_55': xǁRecencyResolutionStrategyǁresolve__mutmut_55
    }
    
    def resolve(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁRecencyResolutionStrategyǁresolve__mutmut_orig"), object.__getattribute__(self, "xǁRecencyResolutionStrategyǁresolve__mutmut_mutants"), args, kwargs, self)
        return result 
    
    resolve.__signature__ = _mutmut_signature(xǁRecencyResolutionStrategyǁresolve__mutmut_orig)
    xǁRecencyResolutionStrategyǁresolve__mutmut_orig.__name__ = 'xǁRecencyResolutionStrategyǁresolve'


class ImportanceResolutionStrategy(ResolutionStrategy):
    """Keep the memory with higher importance."""
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_orig(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_1(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = None
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_2(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(None, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_3(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, None, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_4(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=None)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_5(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_6(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_7(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, )
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_8(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: None)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_9(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = None
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_10(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(None, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_11(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, None, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_12(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=None)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_13(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_14(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_15(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, )
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_16(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: None)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_17(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance != lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_18(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = None
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_19(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(None, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_20(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, None, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_21(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=None)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_22(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_23(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_24(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, )
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_25(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: None)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_26(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = None
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_27(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(None, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_28(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, None, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_29(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=None)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_30(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_31(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_32(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, )
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_33(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: None)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_34(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action=None,
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_35(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=None,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_36(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=None,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_37(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=None
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_38(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_39(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_40(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_41(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_42(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_43(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="XXkeep_newXX",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_44(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="KEEP_NEW",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_45(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action=None,
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_46(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=None,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_47(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=None,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_48(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=None
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_49(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_50(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_51(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_52(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_53(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_54(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="XXkeep_importantXX",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    def xǁImportanceResolutionStrategyǁresolve__mutmut_55(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by keeping the more important memory."""
        higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
        
        # If importance is equal, fallback to recency
        if higher.importance == lower.importance:
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=f"Importance equal, keeping newer memory (created {newer.created_at}) over older (created {older.created_at})"
            )
        
        return Resolution(
            action="KEEP_IMPORTANT",
            kept_memory=higher,
            archived_memory=lower,
            merged_memory=None,
            rationale=f"Keeping higher importance memory ({higher.importance}) over lower importance ({lower.importance})"
        )
    
    xǁImportanceResolutionStrategyǁresolve__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁImportanceResolutionStrategyǁresolve__mutmut_1': xǁImportanceResolutionStrategyǁresolve__mutmut_1, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_2': xǁImportanceResolutionStrategyǁresolve__mutmut_2, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_3': xǁImportanceResolutionStrategyǁresolve__mutmut_3, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_4': xǁImportanceResolutionStrategyǁresolve__mutmut_4, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_5': xǁImportanceResolutionStrategyǁresolve__mutmut_5, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_6': xǁImportanceResolutionStrategyǁresolve__mutmut_6, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_7': xǁImportanceResolutionStrategyǁresolve__mutmut_7, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_8': xǁImportanceResolutionStrategyǁresolve__mutmut_8, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_9': xǁImportanceResolutionStrategyǁresolve__mutmut_9, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_10': xǁImportanceResolutionStrategyǁresolve__mutmut_10, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_11': xǁImportanceResolutionStrategyǁresolve__mutmut_11, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_12': xǁImportanceResolutionStrategyǁresolve__mutmut_12, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_13': xǁImportanceResolutionStrategyǁresolve__mutmut_13, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_14': xǁImportanceResolutionStrategyǁresolve__mutmut_14, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_15': xǁImportanceResolutionStrategyǁresolve__mutmut_15, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_16': xǁImportanceResolutionStrategyǁresolve__mutmut_16, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_17': xǁImportanceResolutionStrategyǁresolve__mutmut_17, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_18': xǁImportanceResolutionStrategyǁresolve__mutmut_18, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_19': xǁImportanceResolutionStrategyǁresolve__mutmut_19, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_20': xǁImportanceResolutionStrategyǁresolve__mutmut_20, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_21': xǁImportanceResolutionStrategyǁresolve__mutmut_21, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_22': xǁImportanceResolutionStrategyǁresolve__mutmut_22, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_23': xǁImportanceResolutionStrategyǁresolve__mutmut_23, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_24': xǁImportanceResolutionStrategyǁresolve__mutmut_24, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_25': xǁImportanceResolutionStrategyǁresolve__mutmut_25, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_26': xǁImportanceResolutionStrategyǁresolve__mutmut_26, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_27': xǁImportanceResolutionStrategyǁresolve__mutmut_27, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_28': xǁImportanceResolutionStrategyǁresolve__mutmut_28, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_29': xǁImportanceResolutionStrategyǁresolve__mutmut_29, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_30': xǁImportanceResolutionStrategyǁresolve__mutmut_30, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_31': xǁImportanceResolutionStrategyǁresolve__mutmut_31, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_32': xǁImportanceResolutionStrategyǁresolve__mutmut_32, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_33': xǁImportanceResolutionStrategyǁresolve__mutmut_33, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_34': xǁImportanceResolutionStrategyǁresolve__mutmut_34, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_35': xǁImportanceResolutionStrategyǁresolve__mutmut_35, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_36': xǁImportanceResolutionStrategyǁresolve__mutmut_36, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_37': xǁImportanceResolutionStrategyǁresolve__mutmut_37, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_38': xǁImportanceResolutionStrategyǁresolve__mutmut_38, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_39': xǁImportanceResolutionStrategyǁresolve__mutmut_39, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_40': xǁImportanceResolutionStrategyǁresolve__mutmut_40, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_41': xǁImportanceResolutionStrategyǁresolve__mutmut_41, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_42': xǁImportanceResolutionStrategyǁresolve__mutmut_42, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_43': xǁImportanceResolutionStrategyǁresolve__mutmut_43, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_44': xǁImportanceResolutionStrategyǁresolve__mutmut_44, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_45': xǁImportanceResolutionStrategyǁresolve__mutmut_45, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_46': xǁImportanceResolutionStrategyǁresolve__mutmut_46, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_47': xǁImportanceResolutionStrategyǁresolve__mutmut_47, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_48': xǁImportanceResolutionStrategyǁresolve__mutmut_48, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_49': xǁImportanceResolutionStrategyǁresolve__mutmut_49, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_50': xǁImportanceResolutionStrategyǁresolve__mutmut_50, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_51': xǁImportanceResolutionStrategyǁresolve__mutmut_51, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_52': xǁImportanceResolutionStrategyǁresolve__mutmut_52, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_53': xǁImportanceResolutionStrategyǁresolve__mutmut_53, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_54': xǁImportanceResolutionStrategyǁresolve__mutmut_54, 
        'xǁImportanceResolutionStrategyǁresolve__mutmut_55': xǁImportanceResolutionStrategyǁresolve__mutmut_55
    }
    
    def resolve(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁImportanceResolutionStrategyǁresolve__mutmut_orig"), object.__getattribute__(self, "xǁImportanceResolutionStrategyǁresolve__mutmut_mutants"), args, kwargs, self)
        return result 
    
    resolve.__signature__ = _mutmut_signature(xǁImportanceResolutionStrategyǁresolve__mutmut_orig)
    xǁImportanceResolutionStrategyǁresolve__mutmut_orig.__name__ = 'xǁImportanceResolutionStrategyǁresolve'


class NamespacePriorityStrategy(ResolutionStrategy):
    """Resolve based on namespace hierarchy priority."""
    
    NAMESPACE_PRIORITY = {
        "user.preferences": 100,
        "user.personal_info": 90,
        "user.health": 85,
        "system.critical": 80,
        "user.interests": 70,
        "system.architecture": 60,
        "test": 10,
    }
    
    def xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_orig(self, namespace: str) -> int:
        """Get priority score for namespace."""
        for ns_prefix, priority in self.NAMESPACE_PRIORITY.items():
            if namespace.startswith(ns_prefix):
                return priority
        return 50  # Default priority
    
    def xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_1(self, namespace: str) -> int:
        """Get priority score for namespace."""
        for ns_prefix, priority in self.NAMESPACE_PRIORITY.items():
            if namespace.startswith(None):
                return priority
        return 50  # Default priority
    
    def xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_2(self, namespace: str) -> int:
        """Get priority score for namespace."""
        for ns_prefix, priority in self.NAMESPACE_PRIORITY.items():
            if namespace.startswith(ns_prefix):
                return priority
        return 51  # Default priority
    
    xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_1': xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_1, 
        'xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_2': xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_2
    }
    
    def get_namespace_priority(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_orig"), object.__getattribute__(self, "xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_namespace_priority.__signature__ = _mutmut_signature(xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_orig)
    xǁNamespacePriorityStrategyǁget_namespace_priority__mutmut_orig.__name__ = 'xǁNamespacePriorityStrategyǁget_namespace_priority'
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_orig(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_1(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = None
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_2(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(None)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_3(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = None
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_4(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(None)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_5(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 >= priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_6(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = None
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_7(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = None
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_8(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 >= priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_9(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = None
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_10(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = None
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_11(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = None
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_12(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(None, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_13(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, None, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_14(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=None)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_15(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_16(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_17(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, )
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_18(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: None)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_19(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = None
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_20(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(None, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_21(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, None, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_22(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=None)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_23(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_24(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_25(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, )
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_26(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: None)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_27(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action=None,
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_28(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=None,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_29(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=None,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_30(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=None
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_31(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_32(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_33(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_34(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_35(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_36(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="XXkeep_importantXX",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_37(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="KEEP_IMPORTANT",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_38(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action=None,
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_39(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=None,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_40(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=None,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_41(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=None
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_42(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_43(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_44(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_45(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_46(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_47(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="XXkeep_importantXX",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_48(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="KEEP_IMPORTANT",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_49(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(None, priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_50(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, None)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_51(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority2)}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_52(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, )}) over ({archived.namespace}: {min(priority1, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_53(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(None, priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_54(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, None)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_55(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority2)})"
        )
    
    def xǁNamespacePriorityStrategyǁresolve__mutmut_56(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve based on namespace priority."""
        priority1 = self.get_namespace_priority(conflict.memory1.namespace)
        priority2 = self.get_namespace_priority(conflict.memory2.namespace)
        
        if priority1 > priority2:
            kept = conflict.memory1
            archived = conflict.memory2
        elif priority2 > priority1:
            kept = conflict.memory2
            archived = conflict.memory1
        else:
            # Equal priority, fallback to importance
            higher = max(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            lower = min(conflict.memory1, conflict.memory2, key=lambda m: m.importance)
            return Resolution(
                action="keep_important",
                kept_memory=higher,
                archived_memory=lower,
                merged_memory=None,
                rationale=f"Namespace priority equal ({priority1}), keeping higher importance memory"
            )
        
        return Resolution(
            action="keep_important",
            kept_memory=kept,
            archived_memory=archived,
            merged_memory=None,
            rationale=f"Keeping memory from higher priority namespace ({kept.namespace}: {max(priority1, priority2)}) over ({archived.namespace}: {min(priority1, )})"
        )
    
    xǁNamespacePriorityStrategyǁresolve__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNamespacePriorityStrategyǁresolve__mutmut_1': xǁNamespacePriorityStrategyǁresolve__mutmut_1, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_2': xǁNamespacePriorityStrategyǁresolve__mutmut_2, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_3': xǁNamespacePriorityStrategyǁresolve__mutmut_3, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_4': xǁNamespacePriorityStrategyǁresolve__mutmut_4, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_5': xǁNamespacePriorityStrategyǁresolve__mutmut_5, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_6': xǁNamespacePriorityStrategyǁresolve__mutmut_6, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_7': xǁNamespacePriorityStrategyǁresolve__mutmut_7, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_8': xǁNamespacePriorityStrategyǁresolve__mutmut_8, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_9': xǁNamespacePriorityStrategyǁresolve__mutmut_9, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_10': xǁNamespacePriorityStrategyǁresolve__mutmut_10, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_11': xǁNamespacePriorityStrategyǁresolve__mutmut_11, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_12': xǁNamespacePriorityStrategyǁresolve__mutmut_12, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_13': xǁNamespacePriorityStrategyǁresolve__mutmut_13, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_14': xǁNamespacePriorityStrategyǁresolve__mutmut_14, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_15': xǁNamespacePriorityStrategyǁresolve__mutmut_15, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_16': xǁNamespacePriorityStrategyǁresolve__mutmut_16, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_17': xǁNamespacePriorityStrategyǁresolve__mutmut_17, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_18': xǁNamespacePriorityStrategyǁresolve__mutmut_18, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_19': xǁNamespacePriorityStrategyǁresolve__mutmut_19, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_20': xǁNamespacePriorityStrategyǁresolve__mutmut_20, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_21': xǁNamespacePriorityStrategyǁresolve__mutmut_21, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_22': xǁNamespacePriorityStrategyǁresolve__mutmut_22, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_23': xǁNamespacePriorityStrategyǁresolve__mutmut_23, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_24': xǁNamespacePriorityStrategyǁresolve__mutmut_24, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_25': xǁNamespacePriorityStrategyǁresolve__mutmut_25, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_26': xǁNamespacePriorityStrategyǁresolve__mutmut_26, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_27': xǁNamespacePriorityStrategyǁresolve__mutmut_27, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_28': xǁNamespacePriorityStrategyǁresolve__mutmut_28, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_29': xǁNamespacePriorityStrategyǁresolve__mutmut_29, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_30': xǁNamespacePriorityStrategyǁresolve__mutmut_30, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_31': xǁNamespacePriorityStrategyǁresolve__mutmut_31, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_32': xǁNamespacePriorityStrategyǁresolve__mutmut_32, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_33': xǁNamespacePriorityStrategyǁresolve__mutmut_33, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_34': xǁNamespacePriorityStrategyǁresolve__mutmut_34, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_35': xǁNamespacePriorityStrategyǁresolve__mutmut_35, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_36': xǁNamespacePriorityStrategyǁresolve__mutmut_36, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_37': xǁNamespacePriorityStrategyǁresolve__mutmut_37, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_38': xǁNamespacePriorityStrategyǁresolve__mutmut_38, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_39': xǁNamespacePriorityStrategyǁresolve__mutmut_39, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_40': xǁNamespacePriorityStrategyǁresolve__mutmut_40, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_41': xǁNamespacePriorityStrategyǁresolve__mutmut_41, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_42': xǁNamespacePriorityStrategyǁresolve__mutmut_42, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_43': xǁNamespacePriorityStrategyǁresolve__mutmut_43, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_44': xǁNamespacePriorityStrategyǁresolve__mutmut_44, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_45': xǁNamespacePriorityStrategyǁresolve__mutmut_45, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_46': xǁNamespacePriorityStrategyǁresolve__mutmut_46, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_47': xǁNamespacePriorityStrategyǁresolve__mutmut_47, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_48': xǁNamespacePriorityStrategyǁresolve__mutmut_48, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_49': xǁNamespacePriorityStrategyǁresolve__mutmut_49, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_50': xǁNamespacePriorityStrategyǁresolve__mutmut_50, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_51': xǁNamespacePriorityStrategyǁresolve__mutmut_51, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_52': xǁNamespacePriorityStrategyǁresolve__mutmut_52, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_53': xǁNamespacePriorityStrategyǁresolve__mutmut_53, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_54': xǁNamespacePriorityStrategyǁresolve__mutmut_54, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_55': xǁNamespacePriorityStrategyǁresolve__mutmut_55, 
        'xǁNamespacePriorityStrategyǁresolve__mutmut_56': xǁNamespacePriorityStrategyǁresolve__mutmut_56
    }
    
    def resolve(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNamespacePriorityStrategyǁresolve__mutmut_orig"), object.__getattribute__(self, "xǁNamespacePriorityStrategyǁresolve__mutmut_mutants"), args, kwargs, self)
        return result 
    
    resolve.__signature__ = _mutmut_signature(xǁNamespacePriorityStrategyǁresolve__mutmut_orig)
    xǁNamespacePriorityStrategyǁresolve__mutmut_orig.__name__ = 'xǁNamespacePriorityStrategyǁresolve'


class ConsensusResolutionStrategy(ResolutionStrategy):
    """Use multiple similar memories to determine consensus."""
    
    def xǁConsensusResolutionStrategyǁ__init____mutmut_orig(self, memory_manager: Optional[Any] = None) -> None:
        """
        Initialize consensus strategy.
        
        Args:
            memory_manager: Optional MemoryManager for finding similar memories
        """
        self.memory_manager = memory_manager
    
    def xǁConsensusResolutionStrategyǁ__init____mutmut_1(self, memory_manager: Optional[Any] = None) -> None:
        """
        Initialize consensus strategy.
        
        Args:
            memory_manager: Optional MemoryManager for finding similar memories
        """
        self.memory_manager = None
    
    xǁConsensusResolutionStrategyǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConsensusResolutionStrategyǁ__init____mutmut_1': xǁConsensusResolutionStrategyǁ__init____mutmut_1
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConsensusResolutionStrategyǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁConsensusResolutionStrategyǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁConsensusResolutionStrategyǁ__init____mutmut_orig)
    xǁConsensusResolutionStrategyǁ__init____mutmut_orig.__name__ = 'xǁConsensusResolutionStrategyǁ__init__'
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_orig(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_1(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_2(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = None
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_3(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(None, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_4(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, None, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_5(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=None)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_6(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_7(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_8(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, )
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_9(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: None)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_10(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = None
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_11(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(None, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_12(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, None, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_13(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=None)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_14(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_15(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_16(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, )
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_17(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: None)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_18(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action=None,
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_19(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=None,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_20(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=None,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_21(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale=None
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_22(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_23(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_24(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_25(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_26(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_27(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="XXkeep_newXX",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_28(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="KEEP_NEW",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_29(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="XXNo memory manager for consensus, using recencyXX"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_30(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="no memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_31(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="NO MEMORY MANAGER FOR CONSENSUS, USING RECENCY"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_32(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = None
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_33(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=None,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_34(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=None
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_35(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_36(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_37(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=21
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_38(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = None
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_39(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content(None)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_40(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] - similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_41(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = None
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_42(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(None, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_43(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=None)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_44(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_45(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, )
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_46(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = None
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_47(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(None)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_48(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action=None,
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_49(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=None,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_50(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=None,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_51(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=None
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_52(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_53(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_54(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_55(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_56(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_57(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="XXconsensusXX",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_58(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="CONSENSUS",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_59(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(None, exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_60(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=None)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_61(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_62(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", )
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_63(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=False)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_64(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = None
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_65(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(None, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_66(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, None, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_67(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=None)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_68(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_69(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_70(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, )
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_71(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: None)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_72(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = None
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_73(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(None, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_74(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, None, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_75(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=None)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_76(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_77(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_78(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, )
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_79(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: None)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_80(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action=None,
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_81(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=None,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_82(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=None,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_83(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale=None
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_84(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_85(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_86(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_87(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_88(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_89(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="XXkeep_newXX",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_90(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="KEEP_NEW",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="Consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_91(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="XXConsensus failed, using recencyXX"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_92(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="consensus failed, using recency"
        )
    
    def xǁConsensusResolutionStrategyǁresolve__mutmut_93(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by finding consensus among similar memories."""
        if not self.memory_manager:
            # Fallback to recency if no memory manager
            newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
            return Resolution(
                action="keep_new",
                kept_memory=newer,
                archived_memory=older,
                merged_memory=None,
                rationale="No memory manager for consensus, using recency"
            )
        
        try:
            # Find similar memories
            similar_memories = self.memory_manager.retrieve_memories(
                query=conflict.memory1.text,
                limit=20
            )
            
            # Group by semantic similarity (simple grouping)
            groups = self._cluster_by_content([conflict.memory1, conflict.memory2] + similar_memories)
            
            if groups:
                # Choose largest group as consensus
                largest_group = max(groups, key=len)
                consensus_memory = self._create_consensus_memory(largest_group)
                
                return Resolution(
                    action="consensus",
                    kept_memory=consensus_memory,
                    archived_memory=None,
                    merged_memory=consensus_memory,
                    rationale=f"Consensus from {len(largest_group)} similar memories"
                )
        except Exception as e:
            logger.warning(f"Error in consensus resolution: {e}", exc_info=True)
        
        # Fallback to recency
        newer = max(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        older = min(conflict.memory1, conflict.memory2, key=lambda m: m.created_at)
        return Resolution(
            action="keep_new",
            kept_memory=newer,
            archived_memory=older,
            merged_memory=None,
            rationale="CONSENSUS FAILED, USING RECENCY"
        )
    
    xǁConsensusResolutionStrategyǁresolve__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConsensusResolutionStrategyǁresolve__mutmut_1': xǁConsensusResolutionStrategyǁresolve__mutmut_1, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_2': xǁConsensusResolutionStrategyǁresolve__mutmut_2, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_3': xǁConsensusResolutionStrategyǁresolve__mutmut_3, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_4': xǁConsensusResolutionStrategyǁresolve__mutmut_4, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_5': xǁConsensusResolutionStrategyǁresolve__mutmut_5, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_6': xǁConsensusResolutionStrategyǁresolve__mutmut_6, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_7': xǁConsensusResolutionStrategyǁresolve__mutmut_7, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_8': xǁConsensusResolutionStrategyǁresolve__mutmut_8, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_9': xǁConsensusResolutionStrategyǁresolve__mutmut_9, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_10': xǁConsensusResolutionStrategyǁresolve__mutmut_10, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_11': xǁConsensusResolutionStrategyǁresolve__mutmut_11, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_12': xǁConsensusResolutionStrategyǁresolve__mutmut_12, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_13': xǁConsensusResolutionStrategyǁresolve__mutmut_13, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_14': xǁConsensusResolutionStrategyǁresolve__mutmut_14, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_15': xǁConsensusResolutionStrategyǁresolve__mutmut_15, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_16': xǁConsensusResolutionStrategyǁresolve__mutmut_16, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_17': xǁConsensusResolutionStrategyǁresolve__mutmut_17, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_18': xǁConsensusResolutionStrategyǁresolve__mutmut_18, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_19': xǁConsensusResolutionStrategyǁresolve__mutmut_19, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_20': xǁConsensusResolutionStrategyǁresolve__mutmut_20, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_21': xǁConsensusResolutionStrategyǁresolve__mutmut_21, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_22': xǁConsensusResolutionStrategyǁresolve__mutmut_22, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_23': xǁConsensusResolutionStrategyǁresolve__mutmut_23, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_24': xǁConsensusResolutionStrategyǁresolve__mutmut_24, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_25': xǁConsensusResolutionStrategyǁresolve__mutmut_25, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_26': xǁConsensusResolutionStrategyǁresolve__mutmut_26, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_27': xǁConsensusResolutionStrategyǁresolve__mutmut_27, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_28': xǁConsensusResolutionStrategyǁresolve__mutmut_28, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_29': xǁConsensusResolutionStrategyǁresolve__mutmut_29, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_30': xǁConsensusResolutionStrategyǁresolve__mutmut_30, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_31': xǁConsensusResolutionStrategyǁresolve__mutmut_31, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_32': xǁConsensusResolutionStrategyǁresolve__mutmut_32, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_33': xǁConsensusResolutionStrategyǁresolve__mutmut_33, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_34': xǁConsensusResolutionStrategyǁresolve__mutmut_34, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_35': xǁConsensusResolutionStrategyǁresolve__mutmut_35, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_36': xǁConsensusResolutionStrategyǁresolve__mutmut_36, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_37': xǁConsensusResolutionStrategyǁresolve__mutmut_37, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_38': xǁConsensusResolutionStrategyǁresolve__mutmut_38, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_39': xǁConsensusResolutionStrategyǁresolve__mutmut_39, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_40': xǁConsensusResolutionStrategyǁresolve__mutmut_40, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_41': xǁConsensusResolutionStrategyǁresolve__mutmut_41, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_42': xǁConsensusResolutionStrategyǁresolve__mutmut_42, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_43': xǁConsensusResolutionStrategyǁresolve__mutmut_43, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_44': xǁConsensusResolutionStrategyǁresolve__mutmut_44, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_45': xǁConsensusResolutionStrategyǁresolve__mutmut_45, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_46': xǁConsensusResolutionStrategyǁresolve__mutmut_46, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_47': xǁConsensusResolutionStrategyǁresolve__mutmut_47, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_48': xǁConsensusResolutionStrategyǁresolve__mutmut_48, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_49': xǁConsensusResolutionStrategyǁresolve__mutmut_49, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_50': xǁConsensusResolutionStrategyǁresolve__mutmut_50, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_51': xǁConsensusResolutionStrategyǁresolve__mutmut_51, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_52': xǁConsensusResolutionStrategyǁresolve__mutmut_52, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_53': xǁConsensusResolutionStrategyǁresolve__mutmut_53, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_54': xǁConsensusResolutionStrategyǁresolve__mutmut_54, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_55': xǁConsensusResolutionStrategyǁresolve__mutmut_55, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_56': xǁConsensusResolutionStrategyǁresolve__mutmut_56, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_57': xǁConsensusResolutionStrategyǁresolve__mutmut_57, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_58': xǁConsensusResolutionStrategyǁresolve__mutmut_58, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_59': xǁConsensusResolutionStrategyǁresolve__mutmut_59, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_60': xǁConsensusResolutionStrategyǁresolve__mutmut_60, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_61': xǁConsensusResolutionStrategyǁresolve__mutmut_61, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_62': xǁConsensusResolutionStrategyǁresolve__mutmut_62, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_63': xǁConsensusResolutionStrategyǁresolve__mutmut_63, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_64': xǁConsensusResolutionStrategyǁresolve__mutmut_64, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_65': xǁConsensusResolutionStrategyǁresolve__mutmut_65, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_66': xǁConsensusResolutionStrategyǁresolve__mutmut_66, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_67': xǁConsensusResolutionStrategyǁresolve__mutmut_67, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_68': xǁConsensusResolutionStrategyǁresolve__mutmut_68, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_69': xǁConsensusResolutionStrategyǁresolve__mutmut_69, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_70': xǁConsensusResolutionStrategyǁresolve__mutmut_70, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_71': xǁConsensusResolutionStrategyǁresolve__mutmut_71, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_72': xǁConsensusResolutionStrategyǁresolve__mutmut_72, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_73': xǁConsensusResolutionStrategyǁresolve__mutmut_73, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_74': xǁConsensusResolutionStrategyǁresolve__mutmut_74, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_75': xǁConsensusResolutionStrategyǁresolve__mutmut_75, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_76': xǁConsensusResolutionStrategyǁresolve__mutmut_76, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_77': xǁConsensusResolutionStrategyǁresolve__mutmut_77, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_78': xǁConsensusResolutionStrategyǁresolve__mutmut_78, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_79': xǁConsensusResolutionStrategyǁresolve__mutmut_79, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_80': xǁConsensusResolutionStrategyǁresolve__mutmut_80, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_81': xǁConsensusResolutionStrategyǁresolve__mutmut_81, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_82': xǁConsensusResolutionStrategyǁresolve__mutmut_82, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_83': xǁConsensusResolutionStrategyǁresolve__mutmut_83, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_84': xǁConsensusResolutionStrategyǁresolve__mutmut_84, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_85': xǁConsensusResolutionStrategyǁresolve__mutmut_85, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_86': xǁConsensusResolutionStrategyǁresolve__mutmut_86, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_87': xǁConsensusResolutionStrategyǁresolve__mutmut_87, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_88': xǁConsensusResolutionStrategyǁresolve__mutmut_88, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_89': xǁConsensusResolutionStrategyǁresolve__mutmut_89, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_90': xǁConsensusResolutionStrategyǁresolve__mutmut_90, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_91': xǁConsensusResolutionStrategyǁresolve__mutmut_91, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_92': xǁConsensusResolutionStrategyǁresolve__mutmut_92, 
        'xǁConsensusResolutionStrategyǁresolve__mutmut_93': xǁConsensusResolutionStrategyǁresolve__mutmut_93
    }
    
    def resolve(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConsensusResolutionStrategyǁresolve__mutmut_orig"), object.__getattribute__(self, "xǁConsensusResolutionStrategyǁresolve__mutmut_mutants"), args, kwargs, self)
        return result 
    
    resolve.__signature__ = _mutmut_signature(xǁConsensusResolutionStrategyǁresolve__mutmut_orig)
    xǁConsensusResolutionStrategyǁresolve__mutmut_orig.__name__ = 'xǁConsensusResolutionStrategyǁresolve'
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_orig(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_1(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = None
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_2(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = None
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_3(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = True
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_4(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(None):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_5(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(None, m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_6(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, None) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_7(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_8(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, ) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_9(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(None)
                    added = True
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_10(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = None
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_11(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = False
                    break
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_12(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = True
                    return
            
            if not added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_13(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if added:
                groups.append([memory])
        
        return groups
    
    def xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_14(self, memories: List[MemoryRecord]) -> List[List[MemoryRecord]]:
        """Group memories by semantic content."""
        # Simple clustering: group by text similarity
        groups: List[List[MemoryRecord]] = []
        
        for memory in memories:
            # Find group with similar content
            added = False
            for group in groups:
                # Check if similar to any memory in group
                if any(self._texts_similar(memory.text, m.text) for m in group):
                    group.append(memory)
                    added = True
                    break
            
            if not added:
                groups.append(None)
        
        return groups
    
    xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_1': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_1, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_2': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_2, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_3': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_3, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_4': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_4, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_5': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_5, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_6': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_6, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_7': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_7, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_8': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_8, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_9': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_9, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_10': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_10, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_11': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_11, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_12': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_12, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_13': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_13, 
        'xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_14': xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_14
    }
    
    def _cluster_by_content(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_orig"), object.__getattribute__(self, "xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _cluster_by_content.__signature__ = _mutmut_signature(xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_orig)
    xǁConsensusResolutionStrategyǁ_cluster_by_content__mutmut_orig.__name__ = 'xǁConsensusResolutionStrategyǁ_cluster_by_content'
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_orig(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_1(self, text1: str, text2: str, threshold: float = 1.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_2(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = None
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_3(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(None)
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_4(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.upper().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_5(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = None
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_6(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(None)
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_7(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.upper().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_8(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_9(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_10(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_11(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return True
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_12(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = None
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_13(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 | words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_14(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = None
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_15(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 & words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_16(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = None
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_17(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) * len(union) if union else 0.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_18(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 1.0
        return similarity >= threshold
    
    def xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_19(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity > threshold
    
    xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_1': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_1, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_2': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_2, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_3': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_3, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_4': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_4, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_5': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_5, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_6': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_6, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_7': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_7, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_8': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_8, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_9': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_9, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_10': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_10, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_11': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_11, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_12': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_12, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_13': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_13, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_14': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_14, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_15': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_15, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_16': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_16, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_17': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_17, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_18': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_18, 
        'xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_19': xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_19
    }
    
    def _texts_similar(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_orig"), object.__getattribute__(self, "xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _texts_similar.__signature__ = _mutmut_signature(xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_orig)
    xǁConsensusResolutionStrategyǁ_texts_similar__mutmut_orig.__name__ = 'xǁConsensusResolutionStrategyǁ_texts_similar'
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_orig(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_1(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_2(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError(None)
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_3(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("XXCannot create consensus from empty groupXX")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_4(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_5(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("CANNOT CREATE CONSENSUS FROM EMPTY GROUP")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_6(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) != 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_7(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 2:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_8(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[1]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_9(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = None
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_10(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = None
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_11(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(None)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_12(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = "XX | XX".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_13(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = None
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_14(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(None)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_15(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = None
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_16(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(None)
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_17(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(None))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_18(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = None
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_19(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(None)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_20(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = None
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_21(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(None)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_22(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=None,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_23(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=None,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_24(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=None,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_25(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=None,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_26(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=None
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_27(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_28(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_29(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_30(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            created_at=oldest_created
        )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_31(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[0].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            )
    
    def xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_32(self, memories: List[MemoryRecord]) -> MemoryRecord:
        """Create a consensus memory from a group of memories."""
        if not memories:
            raise ValueError("Cannot create consensus from empty group")
        
        if len(memories) == 1:
            return memories[0]
        
        # Combine texts (simple concatenation for now)
        texts = [m.text for m in memories]
        merged_text = " | ".join(texts)
        
        # Combine tags
        all_tags = []
        for m in memories:
            all_tags.extend(m.tags)
        merged_tags = list(set(all_tags))
        
        # Use max importance
        merged_importance = max(m.importance for m in memories)
        
        # Use oldest created_at
        oldest_created = min(m.created_at for m in memories)
        
        return MemoryRecord(
            namespace=memories[1].namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=oldest_created
        )
    
    xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_1': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_1, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_2': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_2, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_3': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_3, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_4': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_4, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_5': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_5, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_6': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_6, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_7': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_7, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_8': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_8, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_9': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_9, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_10': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_10, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_11': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_11, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_12': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_12, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_13': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_13, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_14': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_14, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_15': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_15, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_16': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_16, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_17': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_17, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_18': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_18, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_19': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_19, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_20': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_20, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_21': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_21, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_22': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_22, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_23': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_23, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_24': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_24, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_25': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_25, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_26': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_26, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_27': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_27, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_28': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_28, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_29': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_29, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_30': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_30, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_31': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_31, 
        'xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_32': xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_32
    }
    
    def _create_consensus_memory(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_orig"), object.__getattribute__(self, "xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _create_consensus_memory.__signature__ = _mutmut_signature(xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_orig)
    xǁConsensusResolutionStrategyǁ_create_consensus_memory__mutmut_orig.__name__ = 'xǁConsensusResolutionStrategyǁ_create_consensus_memory'


class SmartMergeStrategy(ResolutionStrategy):
    """Merge conflicting memories into a coherent whole."""
    
    def xǁSmartMergeStrategyǁresolve__mutmut_orig(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_1(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = None
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_2(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(None, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_3(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, None)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_4(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_5(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, )
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_6(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = None
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_7(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(None)
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_8(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(None))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_9(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags - conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_10(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = None
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_11(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(None, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_12(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, None)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_13(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_14(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, )
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_15(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = None
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_16(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(None, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_17(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, None)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_18(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_19(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, )
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_20(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = None
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_21(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=None,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_22(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=None,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_23(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=None,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_24(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=None,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_25(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=None
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_26(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_27(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_28(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_29(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_30(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_31(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action=None,
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_32(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=None,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_33(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale=None
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_34(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_35(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_36(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_37(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_38(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_39(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="XXmergeXX",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_40(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="MERGE",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="Merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_41(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="XXMerged conflicting information into coherent memoryXX"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_42(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="merged conflicting information into coherent memory"
        )
    
    def xǁSmartMergeStrategyǁresolve__mutmut_43(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by merging memories."""
        merged_text = self._merge_texts(conflict.memory1.text, conflict.memory2.text)
        
        # Combine tags (unique union)
        merged_tags = list(set(conflict.memory1.tags + conflict.memory2.tags))
        
        # Use max importance
        merged_importance = max(conflict.memory1.importance, conflict.memory2.importance)
        
        # Keep original created_at from older memory
        older_created = min(conflict.memory1.created_at, conflict.memory2.created_at)
        
        merged_memory = MemoryRecord(
            namespace=conflict.memory1.namespace,
            text=merged_text,
            importance=merged_importance,
            tags=merged_tags,
            created_at=older_created
        )
        
        return Resolution(
            action="merge",
            kept_memory=None,
            archived_memory=None,
            merged_memory=merged_memory,
            rationale="MERGED CONFLICTING INFORMATION INTO COHERENT MEMORY"
        )
    
    xǁSmartMergeStrategyǁresolve__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSmartMergeStrategyǁresolve__mutmut_1': xǁSmartMergeStrategyǁresolve__mutmut_1, 
        'xǁSmartMergeStrategyǁresolve__mutmut_2': xǁSmartMergeStrategyǁresolve__mutmut_2, 
        'xǁSmartMergeStrategyǁresolve__mutmut_3': xǁSmartMergeStrategyǁresolve__mutmut_3, 
        'xǁSmartMergeStrategyǁresolve__mutmut_4': xǁSmartMergeStrategyǁresolve__mutmut_4, 
        'xǁSmartMergeStrategyǁresolve__mutmut_5': xǁSmartMergeStrategyǁresolve__mutmut_5, 
        'xǁSmartMergeStrategyǁresolve__mutmut_6': xǁSmartMergeStrategyǁresolve__mutmut_6, 
        'xǁSmartMergeStrategyǁresolve__mutmut_7': xǁSmartMergeStrategyǁresolve__mutmut_7, 
        'xǁSmartMergeStrategyǁresolve__mutmut_8': xǁSmartMergeStrategyǁresolve__mutmut_8, 
        'xǁSmartMergeStrategyǁresolve__mutmut_9': xǁSmartMergeStrategyǁresolve__mutmut_9, 
        'xǁSmartMergeStrategyǁresolve__mutmut_10': xǁSmartMergeStrategyǁresolve__mutmut_10, 
        'xǁSmartMergeStrategyǁresolve__mutmut_11': xǁSmartMergeStrategyǁresolve__mutmut_11, 
        'xǁSmartMergeStrategyǁresolve__mutmut_12': xǁSmartMergeStrategyǁresolve__mutmut_12, 
        'xǁSmartMergeStrategyǁresolve__mutmut_13': xǁSmartMergeStrategyǁresolve__mutmut_13, 
        'xǁSmartMergeStrategyǁresolve__mutmut_14': xǁSmartMergeStrategyǁresolve__mutmut_14, 
        'xǁSmartMergeStrategyǁresolve__mutmut_15': xǁSmartMergeStrategyǁresolve__mutmut_15, 
        'xǁSmartMergeStrategyǁresolve__mutmut_16': xǁSmartMergeStrategyǁresolve__mutmut_16, 
        'xǁSmartMergeStrategyǁresolve__mutmut_17': xǁSmartMergeStrategyǁresolve__mutmut_17, 
        'xǁSmartMergeStrategyǁresolve__mutmut_18': xǁSmartMergeStrategyǁresolve__mutmut_18, 
        'xǁSmartMergeStrategyǁresolve__mutmut_19': xǁSmartMergeStrategyǁresolve__mutmut_19, 
        'xǁSmartMergeStrategyǁresolve__mutmut_20': xǁSmartMergeStrategyǁresolve__mutmut_20, 
        'xǁSmartMergeStrategyǁresolve__mutmut_21': xǁSmartMergeStrategyǁresolve__mutmut_21, 
        'xǁSmartMergeStrategyǁresolve__mutmut_22': xǁSmartMergeStrategyǁresolve__mutmut_22, 
        'xǁSmartMergeStrategyǁresolve__mutmut_23': xǁSmartMergeStrategyǁresolve__mutmut_23, 
        'xǁSmartMergeStrategyǁresolve__mutmut_24': xǁSmartMergeStrategyǁresolve__mutmut_24, 
        'xǁSmartMergeStrategyǁresolve__mutmut_25': xǁSmartMergeStrategyǁresolve__mutmut_25, 
        'xǁSmartMergeStrategyǁresolve__mutmut_26': xǁSmartMergeStrategyǁresolve__mutmut_26, 
        'xǁSmartMergeStrategyǁresolve__mutmut_27': xǁSmartMergeStrategyǁresolve__mutmut_27, 
        'xǁSmartMergeStrategyǁresolve__mutmut_28': xǁSmartMergeStrategyǁresolve__mutmut_28, 
        'xǁSmartMergeStrategyǁresolve__mutmut_29': xǁSmartMergeStrategyǁresolve__mutmut_29, 
        'xǁSmartMergeStrategyǁresolve__mutmut_30': xǁSmartMergeStrategyǁresolve__mutmut_30, 
        'xǁSmartMergeStrategyǁresolve__mutmut_31': xǁSmartMergeStrategyǁresolve__mutmut_31, 
        'xǁSmartMergeStrategyǁresolve__mutmut_32': xǁSmartMergeStrategyǁresolve__mutmut_32, 
        'xǁSmartMergeStrategyǁresolve__mutmut_33': xǁSmartMergeStrategyǁresolve__mutmut_33, 
        'xǁSmartMergeStrategyǁresolve__mutmut_34': xǁSmartMergeStrategyǁresolve__mutmut_34, 
        'xǁSmartMergeStrategyǁresolve__mutmut_35': xǁSmartMergeStrategyǁresolve__mutmut_35, 
        'xǁSmartMergeStrategyǁresolve__mutmut_36': xǁSmartMergeStrategyǁresolve__mutmut_36, 
        'xǁSmartMergeStrategyǁresolve__mutmut_37': xǁSmartMergeStrategyǁresolve__mutmut_37, 
        'xǁSmartMergeStrategyǁresolve__mutmut_38': xǁSmartMergeStrategyǁresolve__mutmut_38, 
        'xǁSmartMergeStrategyǁresolve__mutmut_39': xǁSmartMergeStrategyǁresolve__mutmut_39, 
        'xǁSmartMergeStrategyǁresolve__mutmut_40': xǁSmartMergeStrategyǁresolve__mutmut_40, 
        'xǁSmartMergeStrategyǁresolve__mutmut_41': xǁSmartMergeStrategyǁresolve__mutmut_41, 
        'xǁSmartMergeStrategyǁresolve__mutmut_42': xǁSmartMergeStrategyǁresolve__mutmut_42, 
        'xǁSmartMergeStrategyǁresolve__mutmut_43': xǁSmartMergeStrategyǁresolve__mutmut_43
    }
    
    def resolve(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSmartMergeStrategyǁresolve__mutmut_orig"), object.__getattribute__(self, "xǁSmartMergeStrategyǁresolve__mutmut_mutants"), args, kwargs, self)
        return result 
    
    resolve.__signature__ = _mutmut_signature(xǁSmartMergeStrategyǁresolve__mutmut_orig)
    xǁSmartMergeStrategyǁresolve__mutmut_orig.__name__ = 'xǁSmartMergeStrategyǁresolve'
    
    def _merge_texts(self, text1: str, text2: str) -> str:
        """Merge two texts into coherent memory."""
        # Simple merge: combine with separator
        # In a more sophisticated implementation, could use LLM to merge coherently
        return f"{text1} | {text2}"


class TemporalAwareResolutionStrategy(ResolutionStrategy):
    """Resolve conflicts considering temporal ordering and context."""
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_orig(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_1(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context != "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_2(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "XXdifferent_periodsXX":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_3(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "DIFFERENT_PERIODS":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_4(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action=None,
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_5(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale=None
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_6(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_7(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_8(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_9(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_10(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_11(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="XXkeep_bothXX",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_12(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="KEEP_BOTH",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_13(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="XXMemories about different time periods, both validXX"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_14(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_15(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="MEMORIES ABOUT DIFFERENT TIME PERIODS, BOTH VALID"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_16(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = None
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_17(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from and conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_18(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = None
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_19(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from and conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_20(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal or memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_21(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = None
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_22(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from and conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_23(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = None
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_24(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from and conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_25(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start <= mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_26(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action=None,
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_27(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=None,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_28(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=None,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_29(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=None
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_30(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_31(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_32(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_33(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_34(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_35(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="XXkeep_newXX",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_36(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="KEEP_NEW",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_37(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start <= mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_38(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action=None,
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_39(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=None,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_40(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=None,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_41(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=None
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_42(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_43(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_44(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_45(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_46(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_47(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="XXkeep_newXX",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_48(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="KEEP_NEW",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_49(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = None
        return fallback_strategy.resolve(conflict, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_50(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(None, context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_51(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, None)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_52(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(context)
    
    def xǁTemporalAwareResolutionStrategyǁresolve__mutmut_53(self, conflict: Conflict, context: Dict[str, Any]) -> Resolution:
        """Resolve by considering temporal relationships and context."""
        from .. import RelationType
        
        # Check if memories have temporal relationships
        # (This would require checking relationship manager - simplified for now)
        
        # Check temporal context from conflict
        if conflict.temporal_context == "different_periods":
            # Different time periods - likely both valid, keep both
            return Resolution(
                action="keep_both",
                kept_memory=None,
                archived_memory=None,
                merged_memory=None,
                rationale="Memories about different time periods, both valid"
            )
        
        # Check if memories have temporal metadata
        memory1_has_temporal = conflict.memory1.valid_from or conflict.memory1.valid_until
        memory2_has_temporal = conflict.memory2.valid_from or conflict.memory2.valid_until
        
        if memory1_has_temporal and memory2_has_temporal:
            # Both have temporal metadata - check ordering
            mem1_start = conflict.memory1.valid_from or conflict.memory1.created_at
            mem2_start = conflict.memory2.valid_from or conflict.memory2.created_at
            
            if mem1_start < mem2_start:
                # Memory2 is later - likely supersedes
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory2,
                    archived_memory=conflict.memory1,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem2_start}) supersedes earlier one (valid from {mem1_start}) based on temporal ordering"
                )
            elif mem2_start < mem1_start:
                # Memory1 is later
                return Resolution(
                    action="keep_new",
                    kept_memory=conflict.memory1,
                    archived_memory=conflict.memory2,
                    merged_memory=None,
                    rationale=f"Later memory (valid from {mem1_start}) supersedes earlier one (valid from {mem2_start}) based on temporal ordering"
                )
        
        # Fallback to recency strategy
        from .strategies import RecencyResolutionStrategy
        fallback_strategy = RecencyResolutionStrategy()
        return fallback_strategy.resolve(conflict, )
    
    xǁTemporalAwareResolutionStrategyǁresolve__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_1': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_1, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_2': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_2, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_3': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_3, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_4': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_4, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_5': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_5, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_6': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_6, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_7': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_7, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_8': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_8, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_9': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_9, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_10': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_10, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_11': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_11, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_12': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_12, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_13': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_13, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_14': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_14, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_15': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_15, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_16': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_16, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_17': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_17, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_18': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_18, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_19': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_19, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_20': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_20, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_21': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_21, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_22': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_22, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_23': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_23, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_24': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_24, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_25': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_25, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_26': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_26, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_27': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_27, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_28': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_28, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_29': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_29, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_30': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_30, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_31': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_31, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_32': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_32, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_33': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_33, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_34': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_34, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_35': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_35, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_36': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_36, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_37': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_37, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_38': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_38, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_39': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_39, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_40': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_40, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_41': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_41, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_42': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_42, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_43': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_43, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_44': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_44, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_45': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_45, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_46': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_46, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_47': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_47, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_48': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_48, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_49': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_49, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_50': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_50, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_51': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_51, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_52': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_52, 
        'xǁTemporalAwareResolutionStrategyǁresolve__mutmut_53': xǁTemporalAwareResolutionStrategyǁresolve__mutmut_53
    }
    
    def resolve(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTemporalAwareResolutionStrategyǁresolve__mutmut_orig"), object.__getattribute__(self, "xǁTemporalAwareResolutionStrategyǁresolve__mutmut_mutants"), args, kwargs, self)
        return result 
    
    resolve.__signature__ = _mutmut_signature(xǁTemporalAwareResolutionStrategyǁresolve__mutmut_orig)
    xǁTemporalAwareResolutionStrategyǁresolve__mutmut_orig.__name__ = 'xǁTemporalAwareResolutionStrategyǁresolve'

