"""
Validation utilities for summarization.

Provides drift detection, compression ratio validation, and evidence verification.
"""

from __future__ import annotations

import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from .event_logger import EventLogger
from .models import SessionSummary
from .token_estimator import estimate_tokens

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


class SummarizationValidator:
    """
    Validates summarization results for drift and quality.
    
    Provides methods to verify evidence pointers, check compression ratios,
    and detect inconsistencies.
    
    Includes caching for event ID sets to improve performance on large sessions.
    """
    
    # Maximum number of sessions to cache
    MAX_CACHE_SIZE = 100
    
    def xǁSummarizationValidatorǁ__init____mutmut_orig(self, event_logger: EventLogger) -> None:
        """
        Initialize validator.
        
        Args:
            event_logger: EventLogger instance for accessing raw events
        """
        self.event_logger = event_logger
        # Cache: session_id -> (event_ids_set, file_mtime)
        self._event_ids_cache: Dict[str, Tuple[set[str], float]] = {}
    
    def xǁSummarizationValidatorǁ__init____mutmut_1(self, event_logger: EventLogger) -> None:
        """
        Initialize validator.
        
        Args:
            event_logger: EventLogger instance for accessing raw events
        """
        self.event_logger = None
        # Cache: session_id -> (event_ids_set, file_mtime)
        self._event_ids_cache: Dict[str, Tuple[set[str], float]] = {}
    
    def xǁSummarizationValidatorǁ__init____mutmut_2(self, event_logger: EventLogger) -> None:
        """
        Initialize validator.
        
        Args:
            event_logger: EventLogger instance for accessing raw events
        """
        self.event_logger = event_logger
        # Cache: session_id -> (event_ids_set, file_mtime)
        self._event_ids_cache: Dict[str, Tuple[set[str], float]] = None
    
    xǁSummarizationValidatorǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummarizationValidatorǁ__init____mutmut_1': xǁSummarizationValidatorǁ__init____mutmut_1, 
        'xǁSummarizationValidatorǁ__init____mutmut_2': xǁSummarizationValidatorǁ__init____mutmut_2
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummarizationValidatorǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁSummarizationValidatorǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁSummarizationValidatorǁ__init____mutmut_orig)
    xǁSummarizationValidatorǁ__init____mutmut_orig.__name__ = 'xǁSummarizationValidatorǁ__init__'
    
    def xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_orig(self, session_id: str) -> Optional[float]:
        """Get modification time of event log file."""
        log_file = self.event_logger._get_log_file(session_id)
        if log_file.exists():
            return os.path.getmtime(log_file)
        return None
    
    def xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_1(self, session_id: str) -> Optional[float]:
        """Get modification time of event log file."""
        log_file = None
        if log_file.exists():
            return os.path.getmtime(log_file)
        return None
    
    def xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_2(self, session_id: str) -> Optional[float]:
        """Get modification time of event log file."""
        log_file = self.event_logger._get_log_file(None)
        if log_file.exists():
            return os.path.getmtime(log_file)
        return None
    
    def xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_3(self, session_id: str) -> Optional[float]:
        """Get modification time of event log file."""
        log_file = self.event_logger._get_log_file(session_id)
        if log_file.exists():
            return os.path.getmtime(None)
        return None
    
    xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_1': xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_1, 
        'xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_2': xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_2, 
        'xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_3': xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_3
    }
    
    def _get_log_file_mtime(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_orig"), object.__getattribute__(self, "xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_log_file_mtime.__signature__ = _mutmut_signature(xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_orig)
    xǁSummarizationValidatorǁ_get_log_file_mtime__mutmut_orig.__name__ = 'xǁSummarizationValidatorǁ_get_log_file_mtime'
    
    def xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_orig(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if not use_cache:
            return None
        
        if session_id not in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = self._event_ids_cache[session_id]
        current_mtime = self._get_log_file_mtime(session_id)
        
        # Cache is valid if file mtime matches
        if current_mtime == cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    def xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_1(
        self,
        session_id: str,
        use_cache: bool = False
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if not use_cache:
            return None
        
        if session_id not in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = self._event_ids_cache[session_id]
        current_mtime = self._get_log_file_mtime(session_id)
        
        # Cache is valid if file mtime matches
        if current_mtime == cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    def xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_2(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if use_cache:
            return None
        
        if session_id not in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = self._event_ids_cache[session_id]
        current_mtime = self._get_log_file_mtime(session_id)
        
        # Cache is valid if file mtime matches
        if current_mtime == cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    def xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_3(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if not use_cache:
            return None
        
        if session_id in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = self._event_ids_cache[session_id]
        current_mtime = self._get_log_file_mtime(session_id)
        
        # Cache is valid if file mtime matches
        if current_mtime == cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    def xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_4(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if not use_cache:
            return None
        
        if session_id not in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = None
        current_mtime = self._get_log_file_mtime(session_id)
        
        # Cache is valid if file mtime matches
        if current_mtime == cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    def xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_5(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if not use_cache:
            return None
        
        if session_id not in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = self._event_ids_cache[session_id]
        current_mtime = None
        
        # Cache is valid if file mtime matches
        if current_mtime == cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    def xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_6(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if not use_cache:
            return None
        
        if session_id not in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = self._event_ids_cache[session_id]
        current_mtime = self._get_log_file_mtime(None)
        
        # Cache is valid if file mtime matches
        if current_mtime == cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    def xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_7(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> Optional[set[str]]:
        """
        Get event IDs set from cache if valid, otherwise None.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Cached event IDs set if cache is valid, None otherwise
        """
        if not use_cache:
            return None
        
        if session_id not in self._event_ids_cache:
            return None
        
        cached_set, cached_mtime = self._event_ids_cache[session_id]
        current_mtime = self._get_log_file_mtime(session_id)
        
        # Cache is valid if file mtime matches
        if current_mtime != cached_mtime:
            return cached_set
        
        # Cache invalid, remove it
        del self._event_ids_cache[session_id]
        return None
    
    xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_1': xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_1, 
        'xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_2': xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_2, 
        'xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_3': xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_3, 
        'xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_4': xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_4, 
        'xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_5': xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_5, 
        'xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_6': xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_6, 
        'xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_7': xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_7
    }
    
    def _get_cached_event_ids_set(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_orig"), object.__getattribute__(self, "xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_cached_event_ids_set.__signature__ = _mutmut_signature(xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_orig)
    xǁSummarizationValidatorǁ_get_cached_event_ids_set__mutmut_orig.__name__ = 'xǁSummarizationValidatorǁ_get_cached_event_ids_set'
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_orig(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._event_ids_cache))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_1(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = False
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._event_ids_cache))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_2(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._event_ids_cache))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_3(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) > self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._event_ids_cache))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_4(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = None
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_5(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(None)
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_6(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(None))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_7(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._event_ids_cache))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = None
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_8(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._event_ids_cache))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(None)
        self._event_ids_cache[session_id] = (event_ids_set, current_mtime)
    
    def xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_9(
        self,
        session_id: str,
        event_ids_set: set[str],
        use_cache: bool = True
    ) -> None:
        """
        Cache event IDs set for a session.
        
        Args:
            session_id: Session identifier
            event_ids_set: Event IDs set to cache
            use_cache: Whether to use cache
        """
        if not use_cache:
            return
        
        # Enforce cache size limit (LRU: remove oldest if needed)
        if len(self._event_ids_cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._event_ids_cache))
            del self._event_ids_cache[oldest_key]
        
        current_mtime = self._get_log_file_mtime(session_id)
        self._event_ids_cache[session_id] = None
    
    xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_1': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_1, 
        'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_2': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_2, 
        'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_3': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_3, 
        'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_4': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_4, 
        'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_5': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_5, 
        'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_6': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_6, 
        'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_7': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_7, 
        'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_8': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_8, 
        'xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_9': xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_9
    }
    
    def _set_cached_event_ids_set(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_orig"), object.__getattribute__(self, "xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _set_cached_event_ids_set.__signature__ = _mutmut_signature(xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_orig)
    xǁSummarizationValidatorǁ_set_cached_event_ids_set__mutmut_orig.__name__ = 'xǁSummarizationValidatorǁ_set_cached_event_ids_set'
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_orig(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_1(
        self,
        session_id: str,
        use_cache: bool = False
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_2(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = None
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_3(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(None, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_4(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, None)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_5(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_6(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, )
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_7(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_8(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = None
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_9(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(None)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_10(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(None, event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_11(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, None, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_12(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, None)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_13(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(event_ids_set, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_14(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, use_cache)
        
        return event_ids_set
    
    def xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_15(
        self,
        session_id: str,
        use_cache: bool = True
    ) -> set[str]:
        """
        Get event IDs set, using cache if available.
        
        Args:
            session_id: Session identifier
            use_cache: Whether to use cache
            
        Returns:
            Set of event IDs
        """
        # Try cache first
        cached_set = self._get_cached_event_ids_set(session_id, use_cache)
        if cached_set is not None:
            return cached_set
        
        # Cache miss or invalid, load from event logger
        event_ids_set = self.event_logger.get_event_ids_set(session_id)
        
        # Store in cache
        self._set_cached_event_ids_set(session_id, event_ids_set, )
        
        return event_ids_set
    
    xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_1': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_1, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_2': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_2, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_3': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_3, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_4': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_4, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_5': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_5, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_6': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_6, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_7': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_7, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_8': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_8, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_9': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_9, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_10': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_10, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_11': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_11, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_12': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_12, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_13': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_13, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_14': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_14, 
        'xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_15': xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_15
    }
    
    def _get_event_ids_set(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_orig"), object.__getattribute__(self, "xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_event_ids_set.__signature__ = _mutmut_signature(xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_orig)
    xǁSummarizationValidatorǁ_get_event_ids_set__mutmut_orig.__name__ = 'xǁSummarizationValidatorǁ_get_event_ids_set'
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_orig(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_1(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_2(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_3(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary or previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_4(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental or previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_5(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = None
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_6(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = None
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_7(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(None, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_8(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, None)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_9(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_10(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, )
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_11(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = None
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_12(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(None, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_13(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, None)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_14(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_15(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, )
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_16(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = None
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_17(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = None
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_18(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(None)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_19(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid not in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_20(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(None)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_21(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = None
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_22(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(None)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_23(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_24(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(None)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_25(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = None
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_26(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = None
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_27(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = None
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_28(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(None, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_29(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, None)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_30(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_31(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, )
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_32(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = None
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_33(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = None
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_34(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = None  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_35(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = None
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_36(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 1
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_37(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = None
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_38(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_39(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_40(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(None)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_41(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = None
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_42(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = True
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_43(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found or evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_44(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items = 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_45(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items -= 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_46(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 2
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_47(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "XXvalidXX": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_48(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "VALID": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_49(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) != 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_50(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 1,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_51(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "XXmissing_event_idsXX": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_52(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "MISSING_EVENT_IDS": missing_event_ids,
            "total_evidence_items": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_53(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "XXtotal_evidence_itemsXX": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_54(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "TOTAL_EVIDENCE_ITEMS": total_items,
            "verified_items": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_55(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "XXverified_itemsXX": verified_items
        }
    
    def xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_56(
        self,
        session_id: str,
        summary: SessionSummary,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Verify that all evidence event IDs exist in the event log.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to validate
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache (default: True)
            
        Returns:
            Dictionary with validation results:
            - valid: bool - True if all event IDs exist
            - missing_event_ids: List[str] - List of missing event IDs
            - total_evidence_items: int - Total number of evidence items
            - verified_items: int - Number of items with all event IDs verified
        """
        # Determine which event IDs to validate
        if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
            # Incremental validation: only validate evidence referencing new events
            last_summarized_id = previous_summary.header.last_summarized_event_id
            new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
            all_event_ids = self._get_event_ids_set(session_id, use_cache)
            
            # Filter evidence to only validate items referencing new events
            # Evidence pointing only to old events is skipped (already validated)
            evidence_to_validate = []
            for evidence_item in summary.evidence:
                # Check if this evidence item references any new events
                has_new_events = any(eid in new_event_ids for eid in evidence_item.event_ids)
                if has_new_events:
                    evidence_to_validate.append(evidence_item)
                # Also validate if any event_id doesn't exist in all events (missing event)
                # This catches invalid event IDs even if they're "old"
                has_invalid_event = any(eid not in all_event_ids for eid in evidence_item.event_ids)
                if has_invalid_event:
                    evidence_to_validate.append(evidence_item)
            
            # Use filtered evidence for validation
            evidence_to_check = evidence_to_validate
            event_ids_in_log = all_event_ids
        else:
            # Full validation: check all event IDs
            event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
            evidence_to_check = summary.evidence
        
        missing_event_ids = []
        total_items = len(summary.evidence)  # Always report total evidence items
        verified_items = 0
        
        for evidence_item in evidence_to_check:
            all_found = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    all_found = False
            
            if all_found and evidence_item.event_ids:
                verified_items += 1
        
        return {
            "valid": len(missing_event_ids) == 0,
            "missing_event_ids": missing_event_ids,
            "total_evidence_items": total_items,
            "VERIFIED_ITEMS": verified_items
        }
    
    xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_1': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_1, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_2': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_2, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_3': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_3, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_4': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_4, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_5': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_5, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_6': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_6, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_7': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_7, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_8': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_8, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_9': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_9, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_10': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_10, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_11': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_11, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_12': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_12, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_13': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_13, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_14': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_14, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_15': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_15, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_16': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_16, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_17': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_17, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_18': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_18, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_19': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_19, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_20': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_20, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_21': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_21, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_22': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_22, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_23': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_23, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_24': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_24, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_25': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_25, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_26': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_26, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_27': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_27, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_28': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_28, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_29': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_29, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_30': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_30, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_31': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_31, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_32': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_32, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_33': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_33, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_34': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_34, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_35': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_35, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_36': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_36, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_37': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_37, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_38': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_38, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_39': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_39, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_40': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_40, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_41': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_41, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_42': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_42, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_43': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_43, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_44': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_44, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_45': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_45, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_46': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_46, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_47': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_47, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_48': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_48, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_49': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_49, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_50': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_50, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_51': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_51, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_52': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_52, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_53': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_53, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_54': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_54, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_55': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_55, 
        'xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_56': xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_56
    }
    
    def verify_evidence_event_ids(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_orig"), object.__getattribute__(self, "xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_mutants"), args, kwargs, self)
        return result 
    
    verify_evidence_event_ids.__signature__ = _mutmut_signature(xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_orig)
    xǁSummarizationValidatorǁverify_evidence_event_ids__mutmut_orig.__name__ = 'xǁSummarizationValidatorǁverify_evidence_event_ids'
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_orig(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_1(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = None
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_2(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = "XXXX"
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_3(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = None
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_4(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get(None, "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_5(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", None)
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_6(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_7(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", )
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_8(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("XXcontentXX", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_9(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("CONTENT", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_10(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "XXXX")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_11(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = None
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_12(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get(None, {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_13(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", None)
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_14(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get({})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_15(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", )
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_16(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("XXtool_argsXX", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_17(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("TOOL_ARGS", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_18(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = None
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_19(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get(None, {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_20(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", None)
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_21(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get({})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_22(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", )
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_23(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("XXtool_resultXX", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_24(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("TOOL_RESULT", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_25(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text = content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_26(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text -= content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_27(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content - " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_28(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + "XX XX"
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_29(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text = json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_30(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text -= json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_31(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) - " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_32(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(None) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_33(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + "XX XX"
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_34(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text = json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_35(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text -= json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_36(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) - " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_37(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(None) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_38(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + "XX XX"
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_39(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = None
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_40(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(None)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_41(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = None
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_42(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = None
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_43(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " - " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_44(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) - " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_45(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " - " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_46(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) - " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_47(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " - " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_48(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) - " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_49(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " - " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_50(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal - " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_51(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + "XX XX" +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_52(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(None) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_53(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            "XX XX".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_54(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + "XX XX" +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_55(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(None) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_56(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            "XX XX".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_57(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + "XX XX" +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_58(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(None) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_59(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            "XX XX".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_60(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + "XX XX" +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_61(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(None)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_62(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            "XX XX".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_63(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = None
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_64(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(None)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_65(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens != 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_66(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 1:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_67(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = None
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_68(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 1.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_69(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = None
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_70(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens * summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_71(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "XXcompression_ratioXX": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_72(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "COMPRESSION_RATIO": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_73(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "XXraw_tokensXX": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_74(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "RAW_TOKENS": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_75(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "XXsummary_tokensXX": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_76(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "SUMMARY_TOKENS": summary_tokens,
            "meets_threshold": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_77(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "XXmeets_thresholdXX": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_78(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "MEETS_THRESHOLD": compression_ratio >= 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_79(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio > 5.0
        }
    
    def xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_80(
        self,
        events: List[Dict[str, Any]],
        summary: SessionSummary
    ) -> Dict[str, Any]:
        """
        Check compression ratio between raw events and summary.
        
        Args:
            events: List of raw events that were summarized
            summary: SessionSummary result
            
        Returns:
            Dictionary with compression metrics:
            - compression_ratio: float - Ratio of raw tokens to summary tokens
            - raw_tokens: int - Estimated tokens in raw events
            - summary_tokens: int - Estimated tokens in summary
            - meets_threshold: bool - True if ratio > 5.0 (typical good compression)
        """
        # Estimate tokens in raw events
        raw_text = ""
        for event in events:
            content = event.get("content", "")
            tool_args = event.get("tool_args", {})
            tool_result = event.get("tool_result", {})
            if content:
                raw_text += content + " "
            if tool_args:
                import json
                raw_text += json.dumps(tool_args) + " "
            if tool_result:
                import json
                raw_text += json.dumps(tool_result) + " "
        
        raw_tokens = estimate_tokens(raw_text)
        
        # Estimate tokens in summary
        blocks = summary.summary_blocks
        summary_text = (
            blocks.current_goal + " " +
            " ".join(blocks.what_we_built) + " " +
            " ".join(blocks.open_questions) + " " +
            " ".join(blocks.constraints) + " " +
            " ".join(blocks.next_steps)
        )
        summary_tokens = estimate_tokens(summary_text)
        
        if summary_tokens == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = raw_tokens / summary_tokens
        
        return {
            "compression_ratio": compression_ratio,
            "raw_tokens": raw_tokens,
            "summary_tokens": summary_tokens,
            "meets_threshold": compression_ratio >= 6.0
        }
    
    xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_1': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_1, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_2': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_2, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_3': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_3, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_4': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_4, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_5': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_5, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_6': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_6, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_7': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_7, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_8': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_8, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_9': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_9, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_10': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_10, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_11': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_11, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_12': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_12, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_13': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_13, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_14': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_14, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_15': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_15, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_16': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_16, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_17': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_17, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_18': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_18, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_19': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_19, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_20': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_20, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_21': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_21, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_22': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_22, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_23': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_23, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_24': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_24, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_25': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_25, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_26': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_26, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_27': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_27, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_28': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_28, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_29': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_29, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_30': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_30, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_31': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_31, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_32': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_32, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_33': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_33, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_34': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_34, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_35': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_35, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_36': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_36, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_37': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_37, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_38': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_38, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_39': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_39, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_40': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_40, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_41': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_41, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_42': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_42, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_43': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_43, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_44': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_44, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_45': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_45, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_46': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_46, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_47': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_47, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_48': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_48, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_49': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_49, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_50': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_50, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_51': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_51, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_52': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_52, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_53': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_53, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_54': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_54, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_55': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_55, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_56': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_56, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_57': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_57, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_58': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_58, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_59': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_59, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_60': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_60, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_61': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_61, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_62': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_62, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_63': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_63, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_64': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_64, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_65': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_65, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_66': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_66, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_67': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_67, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_68': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_68, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_69': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_69, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_70': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_70, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_71': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_71, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_72': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_72, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_73': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_73, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_74': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_74, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_75': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_75, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_76': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_76, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_77': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_77, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_78': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_78, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_79': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_79, 
        'xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_80': xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_80
    }
    
    def check_compression_ratio(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_orig"), object.__getattribute__(self, "xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_mutants"), args, kwargs, self)
        return result 
    
    check_compression_ratio.__signature__ = _mutmut_signature(xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_orig)
    xǁSummarizationValidatorǁcheck_compression_ratio__mutmut_orig.__name__ = 'xǁSummarizationValidatorǁcheck_compression_ratio'
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_orig(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_1(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_2(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_3(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is not None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_4(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary or previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_5(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental or previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_6(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = None
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_7(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = None
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_8(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(None, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_9(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, None)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_10(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_11(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, )
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_12(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = None
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_13(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(None, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_14(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, None)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_15(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_16(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, )
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_17(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = None
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_18(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = None
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_19(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(None, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_20(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, None)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_21(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_22(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, )
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_23(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = None
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_24(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get(None) for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_25(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("XXevent_idXX") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_26(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("EVENT_ID") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_27(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get(None)}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_28(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("XXevent_idXX")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_29(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("EVENT_ID")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_30(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = None
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_31(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = None
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_32(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 1
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_33(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = None
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_34(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = True
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_35(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_36(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(None)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_37(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = None
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_38(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = False
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_39(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift = 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_40(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift -= 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_41(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 2
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_42(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "XXhas_driftXX": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_43(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "HAS_DRIFT": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_44(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) >= 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_45(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 1,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_46(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "XXmissing_event_idsXX": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_47(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "MISSING_EVENT_IDS": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_48(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "XXevidence_items_with_driftXX": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_49(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "EVIDENCE_ITEMS_WITH_DRIFT": evidence_items_with_drift,
            "total_evidence_items": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_50(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "XXtotal_evidence_itemsXX": len(summary.evidence)
        }
    
    def xǁSummarizationValidatorǁdetect_drift__mutmut_51(
        self,
        session_id: str,
        summary: SessionSummary,
        events: Optional[List[Dict[str, Any]]] = None,
        previous_summary: Optional[SessionSummary] = None,
        use_incremental: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect drift in summary (evidence pointers that don't exist).
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to check
            events: Optional list of events (if None, loads from event log using cache)
            previous_summary: Optional previous summary for incremental validation
            use_incremental: Whether to use incremental validation (default: False)
            use_cache: Whether to use event ID cache when events is None (default: True)
            
        Returns:
            Dictionary with drift detection results:
            - has_drift: bool - True if drift detected
            - missing_event_ids: List[str] - Missing event IDs
            - evidence_items_with_drift: int - Number of evidence items with missing IDs
        """
        if events is None:
            # Determine which event IDs to check
            if use_incremental and previous_summary and previous_summary.header.last_summarized_event_id:
                # Incremental validation: only check events after last_summarized_event_id
                last_summarized_id = previous_summary.header.last_summarized_event_id
                new_event_ids = self.event_logger.get_event_ids_after(session_id, last_summarized_id)
                all_event_ids = self._get_event_ids_set(session_id, use_cache)
                # For drift detection, we check all evidence against all events
                # but only report drift for new events (incremental check)
                event_ids_in_log = all_event_ids
            else:
                # Use optimized method with caching
                event_ids_in_log = self._get_event_ids_set(session_id, use_cache)
        else:
            # Build set from provided events
            event_ids_in_log = {e.get("event_id") for e in events if e.get("event_id")}
        
        missing_event_ids = []
        evidence_items_with_drift = 0
        
        for evidence_item in summary.evidence:
            item_has_drift = False
            for event_id in evidence_item.event_ids:
                if event_id not in event_ids_in_log:
                    missing_event_ids.append(event_id)
                    item_has_drift = True
            
            if item_has_drift:
                evidence_items_with_drift += 1
        
        return {
            "has_drift": len(missing_event_ids) > 0,
            "missing_event_ids": missing_event_ids,
            "evidence_items_with_drift": evidence_items_with_drift,
            "TOTAL_EVIDENCE_ITEMS": len(summary.evidence)
        }
    
    xǁSummarizationValidatorǁdetect_drift__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummarizationValidatorǁdetect_drift__mutmut_1': xǁSummarizationValidatorǁdetect_drift__mutmut_1, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_2': xǁSummarizationValidatorǁdetect_drift__mutmut_2, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_3': xǁSummarizationValidatorǁdetect_drift__mutmut_3, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_4': xǁSummarizationValidatorǁdetect_drift__mutmut_4, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_5': xǁSummarizationValidatorǁdetect_drift__mutmut_5, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_6': xǁSummarizationValidatorǁdetect_drift__mutmut_6, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_7': xǁSummarizationValidatorǁdetect_drift__mutmut_7, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_8': xǁSummarizationValidatorǁdetect_drift__mutmut_8, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_9': xǁSummarizationValidatorǁdetect_drift__mutmut_9, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_10': xǁSummarizationValidatorǁdetect_drift__mutmut_10, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_11': xǁSummarizationValidatorǁdetect_drift__mutmut_11, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_12': xǁSummarizationValidatorǁdetect_drift__mutmut_12, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_13': xǁSummarizationValidatorǁdetect_drift__mutmut_13, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_14': xǁSummarizationValidatorǁdetect_drift__mutmut_14, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_15': xǁSummarizationValidatorǁdetect_drift__mutmut_15, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_16': xǁSummarizationValidatorǁdetect_drift__mutmut_16, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_17': xǁSummarizationValidatorǁdetect_drift__mutmut_17, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_18': xǁSummarizationValidatorǁdetect_drift__mutmut_18, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_19': xǁSummarizationValidatorǁdetect_drift__mutmut_19, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_20': xǁSummarizationValidatorǁdetect_drift__mutmut_20, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_21': xǁSummarizationValidatorǁdetect_drift__mutmut_21, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_22': xǁSummarizationValidatorǁdetect_drift__mutmut_22, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_23': xǁSummarizationValidatorǁdetect_drift__mutmut_23, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_24': xǁSummarizationValidatorǁdetect_drift__mutmut_24, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_25': xǁSummarizationValidatorǁdetect_drift__mutmut_25, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_26': xǁSummarizationValidatorǁdetect_drift__mutmut_26, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_27': xǁSummarizationValidatorǁdetect_drift__mutmut_27, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_28': xǁSummarizationValidatorǁdetect_drift__mutmut_28, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_29': xǁSummarizationValidatorǁdetect_drift__mutmut_29, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_30': xǁSummarizationValidatorǁdetect_drift__mutmut_30, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_31': xǁSummarizationValidatorǁdetect_drift__mutmut_31, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_32': xǁSummarizationValidatorǁdetect_drift__mutmut_32, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_33': xǁSummarizationValidatorǁdetect_drift__mutmut_33, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_34': xǁSummarizationValidatorǁdetect_drift__mutmut_34, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_35': xǁSummarizationValidatorǁdetect_drift__mutmut_35, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_36': xǁSummarizationValidatorǁdetect_drift__mutmut_36, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_37': xǁSummarizationValidatorǁdetect_drift__mutmut_37, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_38': xǁSummarizationValidatorǁdetect_drift__mutmut_38, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_39': xǁSummarizationValidatorǁdetect_drift__mutmut_39, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_40': xǁSummarizationValidatorǁdetect_drift__mutmut_40, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_41': xǁSummarizationValidatorǁdetect_drift__mutmut_41, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_42': xǁSummarizationValidatorǁdetect_drift__mutmut_42, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_43': xǁSummarizationValidatorǁdetect_drift__mutmut_43, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_44': xǁSummarizationValidatorǁdetect_drift__mutmut_44, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_45': xǁSummarizationValidatorǁdetect_drift__mutmut_45, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_46': xǁSummarizationValidatorǁdetect_drift__mutmut_46, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_47': xǁSummarizationValidatorǁdetect_drift__mutmut_47, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_48': xǁSummarizationValidatorǁdetect_drift__mutmut_48, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_49': xǁSummarizationValidatorǁdetect_drift__mutmut_49, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_50': xǁSummarizationValidatorǁdetect_drift__mutmut_50, 
        'xǁSummarizationValidatorǁdetect_drift__mutmut_51': xǁSummarizationValidatorǁdetect_drift__mutmut_51
    }
    
    def detect_drift(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummarizationValidatorǁdetect_drift__mutmut_orig"), object.__getattribute__(self, "xǁSummarizationValidatorǁdetect_drift__mutmut_mutants"), args, kwargs, self)
        return result 
    
    detect_drift.__signature__ = _mutmut_signature(xǁSummarizationValidatorǁdetect_drift__mutmut_orig)
    xǁSummarizationValidatorǁdetect_drift__mutmut_orig.__name__ = 'xǁSummarizationValidatorǁdetect_drift'

