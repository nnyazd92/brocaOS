"""
Conflict logging and audit system.

Logs all conflict detection and resolution activities for audit and undo.
"""

from __future__ import annotations

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

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


class ConflictLogger:
    """
    Logs conflict detection and resolution activities.
    
    Stores conflict logs in the same database as memories for consistency.
    """
    
    def xǁConflictLoggerǁ__init____mutmut_orig(self, storage: Any) -> None:
        """
        Initialize conflict logger.
        
        Args:
            storage: MemoryStorage instance (will add conflict tables)
        """
        self.storage = storage
        self._ensure_tables()
        logger.info("Initialized ConflictLogger")
    
    def xǁConflictLoggerǁ__init____mutmut_1(self, storage: Any) -> None:
        """
        Initialize conflict logger.
        
        Args:
            storage: MemoryStorage instance (will add conflict tables)
        """
        self.storage = None
        self._ensure_tables()
        logger.info("Initialized ConflictLogger")
    
    def xǁConflictLoggerǁ__init____mutmut_2(self, storage: Any) -> None:
        """
        Initialize conflict logger.
        
        Args:
            storage: MemoryStorage instance (will add conflict tables)
        """
        self.storage = storage
        self._ensure_tables()
        logger.info(None)
    
    def xǁConflictLoggerǁ__init____mutmut_3(self, storage: Any) -> None:
        """
        Initialize conflict logger.
        
        Args:
            storage: MemoryStorage instance (will add conflict tables)
        """
        self.storage = storage
        self._ensure_tables()
        logger.info("XXInitialized ConflictLoggerXX")
    
    def xǁConflictLoggerǁ__init____mutmut_4(self, storage: Any) -> None:
        """
        Initialize conflict logger.
        
        Args:
            storage: MemoryStorage instance (will add conflict tables)
        """
        self.storage = storage
        self._ensure_tables()
        logger.info("initialized conflictlogger")
    
    def xǁConflictLoggerǁ__init____mutmut_5(self, storage: Any) -> None:
        """
        Initialize conflict logger.
        
        Args:
            storage: MemoryStorage instance (will add conflict tables)
        """
        self.storage = storage
        self._ensure_tables()
        logger.info("INITIALIZED CONFLICTLOGGER")
    
    xǁConflictLoggerǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictLoggerǁ__init____mutmut_1': xǁConflictLoggerǁ__init____mutmut_1, 
        'xǁConflictLoggerǁ__init____mutmut_2': xǁConflictLoggerǁ__init____mutmut_2, 
        'xǁConflictLoggerǁ__init____mutmut_3': xǁConflictLoggerǁ__init____mutmut_3, 
        'xǁConflictLoggerǁ__init____mutmut_4': xǁConflictLoggerǁ__init____mutmut_4, 
        'xǁConflictLoggerǁ__init____mutmut_5': xǁConflictLoggerǁ__init____mutmut_5
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictLoggerǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁConflictLoggerǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁConflictLoggerǁ__init____mutmut_orig)
    xǁConflictLoggerǁ__init____mutmut_orig.__name__ = 'xǁConflictLoggerǁ__init__'
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_orig(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_1(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = None
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_2(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute(None)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_3(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute(None)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_4(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute(None)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_5(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("XXCREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)XX")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_6(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("create index if not exists idx_conflict_timestamp on conflict_log(timestamp desc)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_7(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS IDX_CONFLICT_TIMESTAMP ON CONFLICT_LOG(TIMESTAMP DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_8(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute(None)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_9(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("XXCREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)XX")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_10(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("create index if not exists idx_conflict_type on conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_11(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS IDX_CONFLICT_TYPE ON CONFLICT_LOG(CONFLICT_TYPE)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_12(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute(None)
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_13(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("XXCREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)XX")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_14(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("create index if not exists idx_resolution_conflict on resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_15(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS IDX_RESOLUTION_CONFLICT ON RESOLUTION_HISTORY(CONFLICT_LOG_ID)")
        
        self.storage._connection.commit()
        logger.debug("Created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_16(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug(None)
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_17(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("XXCreated conflict log tablesXX")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_18(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("created conflict log tables")
    
    def xǁConflictLoggerǁ_ensure_tables__mutmut_19(self) -> None:
        """Ensure conflict log tables exist."""
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Create conflict_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                memory1_id INTEGER,
                memory2_id INTEGER,
                conflict_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_method TEXT NOT NULL,
                resolution_strategy TEXT NOT NULL,
                resolution_action TEXT NOT NULL,
                kept_memory_id INTEGER,
                archived_memory_id INTEGER,
                merged_memory_id INTEGER,
                user_involved BOOLEAN DEFAULT FALSE,
                user_decision TEXT,
                rationale TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create resolution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_log_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conflict_log_id) REFERENCES conflict_log(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_timestamp ON conflict_log(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflict_log(conflict_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_conflict ON resolution_history(conflict_log_id)")
        
        self.storage._connection.commit()
        logger.debug("CREATED CONFLICT LOG TABLES")
    
    xǁConflictLoggerǁ_ensure_tables__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictLoggerǁ_ensure_tables__mutmut_1': xǁConflictLoggerǁ_ensure_tables__mutmut_1, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_2': xǁConflictLoggerǁ_ensure_tables__mutmut_2, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_3': xǁConflictLoggerǁ_ensure_tables__mutmut_3, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_4': xǁConflictLoggerǁ_ensure_tables__mutmut_4, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_5': xǁConflictLoggerǁ_ensure_tables__mutmut_5, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_6': xǁConflictLoggerǁ_ensure_tables__mutmut_6, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_7': xǁConflictLoggerǁ_ensure_tables__mutmut_7, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_8': xǁConflictLoggerǁ_ensure_tables__mutmut_8, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_9': xǁConflictLoggerǁ_ensure_tables__mutmut_9, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_10': xǁConflictLoggerǁ_ensure_tables__mutmut_10, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_11': xǁConflictLoggerǁ_ensure_tables__mutmut_11, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_12': xǁConflictLoggerǁ_ensure_tables__mutmut_12, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_13': xǁConflictLoggerǁ_ensure_tables__mutmut_13, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_14': xǁConflictLoggerǁ_ensure_tables__mutmut_14, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_15': xǁConflictLoggerǁ_ensure_tables__mutmut_15, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_16': xǁConflictLoggerǁ_ensure_tables__mutmut_16, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_17': xǁConflictLoggerǁ_ensure_tables__mutmut_17, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_18': xǁConflictLoggerǁ_ensure_tables__mutmut_18, 
        'xǁConflictLoggerǁ_ensure_tables__mutmut_19': xǁConflictLoggerǁ_ensure_tables__mutmut_19
    }
    
    def _ensure_tables(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictLoggerǁ_ensure_tables__mutmut_orig"), object.__getattribute__(self, "xǁConflictLoggerǁ_ensure_tables__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _ensure_tables.__signature__ = _mutmut_signature(xǁConflictLoggerǁ_ensure_tables__mutmut_orig)
    xǁConflictLoggerǁ_ensure_tables__mutmut_orig.__name__ = 'xǁConflictLoggerǁ_ensure_tables'
    
    def xǁConflictLoggerǁlog_conflict__mutmut_orig(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_1(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = True,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_2(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "XXsemanticXX"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_3(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "SEMANTIC"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_4(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = None
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_5(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_6(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_7(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_8(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory or resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_9(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_10(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory or resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_11(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_12(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory or resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_13(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = None
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_14(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "XXevidenceXX": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_15(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "EVIDENCE": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_16(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "XXresolution_rationaleXX": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_17(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "RESOLUTION_RATIONALE": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_18(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute(None, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_19(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, None)
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_20(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute((
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_21(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, )
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_22(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(None).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_23(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(None)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_24(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = None
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_25(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute(None, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_26(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, None)
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_27(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute((log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_28(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, )
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_29(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "XXkeptXX", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_30(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "KEPT", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_31(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(None).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_32(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute(None, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_33(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, None)
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_34(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute((log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_35(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, )
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_36(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "XXarchivedXX", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_37(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "ARCHIVED", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_38(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(None).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_39(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute(None, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_40(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, None)
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_41(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute((log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_42(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, )
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_43(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "XXmergedXX", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_44(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "MERGED", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_45(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(None).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(f"Logged conflict {log_id}")
        
        return log_id
    
    def xǁConflictLoggerǁlog_conflict__mutmut_46(
        self,
        conflict: Conflict,
        resolution: Resolution,
        user_involved: bool = False,
        user_decision: Optional[str] = None,
        detection_method: str = "semantic"
    ) -> int:
        """
        Log conflict detection and resolution.
        
        Args:
            conflict: Conflict that was detected
            resolution: Resolution that was applied
            user_involved: Whether user was involved in resolution
            user_decision: Optional user decision
            detection_method: Method used to detect conflict
            
        Returns:
            Log entry ID
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        memory1_id = conflict.memory1.id if conflict.memory1.id else None
        memory2_id = conflict.memory2.id if conflict.memory2.id else None
        kept_id = resolution.kept_memory.id if resolution.kept_memory and resolution.kept_memory.id else None
        archived_id = resolution.archived_memory.id if resolution.archived_memory and resolution.archived_memory.id else None
        merged_id = resolution.merged_memory.id if resolution.merged_memory and resolution.merged_memory.id else None
        
        metadata = {
            "evidence": conflict.evidence,
            "resolution_rationale": resolution.rationale
        }
        
        cursor.execute("""
            INSERT INTO conflict_log (
                timestamp, memory1_id, memory2_id, conflict_type, confidence,
                detection_method, resolution_strategy, resolution_action,
                kept_memory_id, archived_memory_id, merged_memory_id,
                user_involved, user_decision, rationale, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            memory1_id,
            memory2_id,
            conflict.conflict_type,
            conflict.confidence,
            detection_method,
            conflict.resolution_strategy,
            resolution.action,
            kept_id,
            archived_id,
            merged_id,
            user_involved,
            user_decision,
            resolution.rationale,
            json.dumps(metadata)
        ))
        
        log_id = cursor.lastrowid
        
        # Log resolution history
        if kept_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, kept_id, "kept", datetime.now(timezone.utc).isoformat()))
        
        if archived_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, archived_id, "archived", datetime.now(timezone.utc).isoformat()))
        
        if merged_id:
            cursor.execute("""
                INSERT INTO resolution_history (conflict_log_id, memory_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (log_id, merged_id, "merged", datetime.now(timezone.utc).isoformat()))
        
        self.storage._connection.commit()
        logger.debug(None)
        
        return log_id
    
    xǁConflictLoggerǁlog_conflict__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictLoggerǁlog_conflict__mutmut_1': xǁConflictLoggerǁlog_conflict__mutmut_1, 
        'xǁConflictLoggerǁlog_conflict__mutmut_2': xǁConflictLoggerǁlog_conflict__mutmut_2, 
        'xǁConflictLoggerǁlog_conflict__mutmut_3': xǁConflictLoggerǁlog_conflict__mutmut_3, 
        'xǁConflictLoggerǁlog_conflict__mutmut_4': xǁConflictLoggerǁlog_conflict__mutmut_4, 
        'xǁConflictLoggerǁlog_conflict__mutmut_5': xǁConflictLoggerǁlog_conflict__mutmut_5, 
        'xǁConflictLoggerǁlog_conflict__mutmut_6': xǁConflictLoggerǁlog_conflict__mutmut_6, 
        'xǁConflictLoggerǁlog_conflict__mutmut_7': xǁConflictLoggerǁlog_conflict__mutmut_7, 
        'xǁConflictLoggerǁlog_conflict__mutmut_8': xǁConflictLoggerǁlog_conflict__mutmut_8, 
        'xǁConflictLoggerǁlog_conflict__mutmut_9': xǁConflictLoggerǁlog_conflict__mutmut_9, 
        'xǁConflictLoggerǁlog_conflict__mutmut_10': xǁConflictLoggerǁlog_conflict__mutmut_10, 
        'xǁConflictLoggerǁlog_conflict__mutmut_11': xǁConflictLoggerǁlog_conflict__mutmut_11, 
        'xǁConflictLoggerǁlog_conflict__mutmut_12': xǁConflictLoggerǁlog_conflict__mutmut_12, 
        'xǁConflictLoggerǁlog_conflict__mutmut_13': xǁConflictLoggerǁlog_conflict__mutmut_13, 
        'xǁConflictLoggerǁlog_conflict__mutmut_14': xǁConflictLoggerǁlog_conflict__mutmut_14, 
        'xǁConflictLoggerǁlog_conflict__mutmut_15': xǁConflictLoggerǁlog_conflict__mutmut_15, 
        'xǁConflictLoggerǁlog_conflict__mutmut_16': xǁConflictLoggerǁlog_conflict__mutmut_16, 
        'xǁConflictLoggerǁlog_conflict__mutmut_17': xǁConflictLoggerǁlog_conflict__mutmut_17, 
        'xǁConflictLoggerǁlog_conflict__mutmut_18': xǁConflictLoggerǁlog_conflict__mutmut_18, 
        'xǁConflictLoggerǁlog_conflict__mutmut_19': xǁConflictLoggerǁlog_conflict__mutmut_19, 
        'xǁConflictLoggerǁlog_conflict__mutmut_20': xǁConflictLoggerǁlog_conflict__mutmut_20, 
        'xǁConflictLoggerǁlog_conflict__mutmut_21': xǁConflictLoggerǁlog_conflict__mutmut_21, 
        'xǁConflictLoggerǁlog_conflict__mutmut_22': xǁConflictLoggerǁlog_conflict__mutmut_22, 
        'xǁConflictLoggerǁlog_conflict__mutmut_23': xǁConflictLoggerǁlog_conflict__mutmut_23, 
        'xǁConflictLoggerǁlog_conflict__mutmut_24': xǁConflictLoggerǁlog_conflict__mutmut_24, 
        'xǁConflictLoggerǁlog_conflict__mutmut_25': xǁConflictLoggerǁlog_conflict__mutmut_25, 
        'xǁConflictLoggerǁlog_conflict__mutmut_26': xǁConflictLoggerǁlog_conflict__mutmut_26, 
        'xǁConflictLoggerǁlog_conflict__mutmut_27': xǁConflictLoggerǁlog_conflict__mutmut_27, 
        'xǁConflictLoggerǁlog_conflict__mutmut_28': xǁConflictLoggerǁlog_conflict__mutmut_28, 
        'xǁConflictLoggerǁlog_conflict__mutmut_29': xǁConflictLoggerǁlog_conflict__mutmut_29, 
        'xǁConflictLoggerǁlog_conflict__mutmut_30': xǁConflictLoggerǁlog_conflict__mutmut_30, 
        'xǁConflictLoggerǁlog_conflict__mutmut_31': xǁConflictLoggerǁlog_conflict__mutmut_31, 
        'xǁConflictLoggerǁlog_conflict__mutmut_32': xǁConflictLoggerǁlog_conflict__mutmut_32, 
        'xǁConflictLoggerǁlog_conflict__mutmut_33': xǁConflictLoggerǁlog_conflict__mutmut_33, 
        'xǁConflictLoggerǁlog_conflict__mutmut_34': xǁConflictLoggerǁlog_conflict__mutmut_34, 
        'xǁConflictLoggerǁlog_conflict__mutmut_35': xǁConflictLoggerǁlog_conflict__mutmut_35, 
        'xǁConflictLoggerǁlog_conflict__mutmut_36': xǁConflictLoggerǁlog_conflict__mutmut_36, 
        'xǁConflictLoggerǁlog_conflict__mutmut_37': xǁConflictLoggerǁlog_conflict__mutmut_37, 
        'xǁConflictLoggerǁlog_conflict__mutmut_38': xǁConflictLoggerǁlog_conflict__mutmut_38, 
        'xǁConflictLoggerǁlog_conflict__mutmut_39': xǁConflictLoggerǁlog_conflict__mutmut_39, 
        'xǁConflictLoggerǁlog_conflict__mutmut_40': xǁConflictLoggerǁlog_conflict__mutmut_40, 
        'xǁConflictLoggerǁlog_conflict__mutmut_41': xǁConflictLoggerǁlog_conflict__mutmut_41, 
        'xǁConflictLoggerǁlog_conflict__mutmut_42': xǁConflictLoggerǁlog_conflict__mutmut_42, 
        'xǁConflictLoggerǁlog_conflict__mutmut_43': xǁConflictLoggerǁlog_conflict__mutmut_43, 
        'xǁConflictLoggerǁlog_conflict__mutmut_44': xǁConflictLoggerǁlog_conflict__mutmut_44, 
        'xǁConflictLoggerǁlog_conflict__mutmut_45': xǁConflictLoggerǁlog_conflict__mutmut_45, 
        'xǁConflictLoggerǁlog_conflict__mutmut_46': xǁConflictLoggerǁlog_conflict__mutmut_46
    }
    
    def log_conflict(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictLoggerǁlog_conflict__mutmut_orig"), object.__getattribute__(self, "xǁConflictLoggerǁlog_conflict__mutmut_mutants"), args, kwargs, self)
        return result 
    
    log_conflict.__signature__ = _mutmut_signature(xǁConflictLoggerǁlog_conflict__mutmut_orig)
    xǁConflictLoggerǁlog_conflict__mutmut_orig.__name__ = 'xǁConflictLoggerǁlog_conflict'
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_orig(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_1(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = None
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_2(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute(None)
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_3(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("XXSELECT COUNT(*) FROM conflict_logXX")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_4(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("select count(*) from conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_5(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM CONFLICT_LOG")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_6(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = None
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_7(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[1]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_8(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute(None)
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_9(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("XXSELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSEXX")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_10(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("select count(*) from conflict_log where user_involved = false")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_11(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM CONFLICT_LOG WHERE USER_INVOLVED = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_12(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = None
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_13(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[1]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_14(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute(None)
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_15(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("XXSELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUEXX")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_16(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("select count(*) from conflict_log where user_involved = true")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_17(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM CONFLICT_LOG WHERE USER_INVOLVED = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_18(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = None
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_19(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[1]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_20(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute(None)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_21(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = None
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_22(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[1]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_23(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[2] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_24(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "XXtotal_conflictsXX": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_25(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "TOTAL_CONFLICTS": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_26(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "XXauto_resolvedXX": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_27(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "AUTO_RESOLVED": auto_resolved,
            "user_resolved": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_28(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "XXuser_resolvedXX": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_29(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "USER_RESOLVED": user_resolved,
            "by_type": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_30(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "XXby_typeXX": by_type
        }
    
    def xǁConflictLoggerǁget_conflict_stats__mutmut_31(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        # Total conflicts
        cursor.execute("SELECT COUNT(*) FROM conflict_log")
        total_conflicts = cursor.fetchone()[0]
        
        # Auto resolved (no user involvement)
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = FALSE")
        auto_resolved = cursor.fetchone()[0]
        
        # User resolved
        cursor.execute("SELECT COUNT(*) FROM conflict_log WHERE user_involved = TRUE")
        user_resolved = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT conflict_type, COUNT(*) 
            FROM conflict_log 
            GROUP BY conflict_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_conflicts": total_conflicts,
            "auto_resolved": auto_resolved,
            "user_resolved": user_resolved,
            "BY_TYPE": by_type
        }
    
    xǁConflictLoggerǁget_conflict_stats__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictLoggerǁget_conflict_stats__mutmut_1': xǁConflictLoggerǁget_conflict_stats__mutmut_1, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_2': xǁConflictLoggerǁget_conflict_stats__mutmut_2, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_3': xǁConflictLoggerǁget_conflict_stats__mutmut_3, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_4': xǁConflictLoggerǁget_conflict_stats__mutmut_4, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_5': xǁConflictLoggerǁget_conflict_stats__mutmut_5, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_6': xǁConflictLoggerǁget_conflict_stats__mutmut_6, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_7': xǁConflictLoggerǁget_conflict_stats__mutmut_7, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_8': xǁConflictLoggerǁget_conflict_stats__mutmut_8, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_9': xǁConflictLoggerǁget_conflict_stats__mutmut_9, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_10': xǁConflictLoggerǁget_conflict_stats__mutmut_10, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_11': xǁConflictLoggerǁget_conflict_stats__mutmut_11, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_12': xǁConflictLoggerǁget_conflict_stats__mutmut_12, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_13': xǁConflictLoggerǁget_conflict_stats__mutmut_13, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_14': xǁConflictLoggerǁget_conflict_stats__mutmut_14, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_15': xǁConflictLoggerǁget_conflict_stats__mutmut_15, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_16': xǁConflictLoggerǁget_conflict_stats__mutmut_16, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_17': xǁConflictLoggerǁget_conflict_stats__mutmut_17, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_18': xǁConflictLoggerǁget_conflict_stats__mutmut_18, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_19': xǁConflictLoggerǁget_conflict_stats__mutmut_19, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_20': xǁConflictLoggerǁget_conflict_stats__mutmut_20, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_21': xǁConflictLoggerǁget_conflict_stats__mutmut_21, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_22': xǁConflictLoggerǁget_conflict_stats__mutmut_22, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_23': xǁConflictLoggerǁget_conflict_stats__mutmut_23, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_24': xǁConflictLoggerǁget_conflict_stats__mutmut_24, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_25': xǁConflictLoggerǁget_conflict_stats__mutmut_25, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_26': xǁConflictLoggerǁget_conflict_stats__mutmut_26, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_27': xǁConflictLoggerǁget_conflict_stats__mutmut_27, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_28': xǁConflictLoggerǁget_conflict_stats__mutmut_28, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_29': xǁConflictLoggerǁget_conflict_stats__mutmut_29, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_30': xǁConflictLoggerǁget_conflict_stats__mutmut_30, 
        'xǁConflictLoggerǁget_conflict_stats__mutmut_31': xǁConflictLoggerǁget_conflict_stats__mutmut_31
    }
    
    def get_conflict_stats(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictLoggerǁget_conflict_stats__mutmut_orig"), object.__getattribute__(self, "xǁConflictLoggerǁget_conflict_stats__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_conflict_stats.__signature__ = _mutmut_signature(xǁConflictLoggerǁget_conflict_stats__mutmut_orig)
    xǁConflictLoggerǁget_conflict_stats__mutmut_orig.__name__ = 'xǁConflictLoggerǁget_conflict_stats'
    
    def xǁConflictLoggerǁget_undo_history__mutmut_orig(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_1(self, limit: int = 11) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_2(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = None
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_3(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute(None, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_4(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, None)
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_5(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute((limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_6(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, )
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_7(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "XXidXX": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_8(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "ID": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_9(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[1],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_10(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "XXtimestampXX": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_11(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "TIMESTAMP": row[1],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_12(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[2],
                "action": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_13(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "XXactionXX": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_14(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "ACTION": row[2],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_15(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[3],
                "rationale": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_16(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "XXrationaleXX": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_17(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "RATIONALE": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_undo_history__mutmut_18(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get undo history for conflicts.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of undo records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, resolution_action, rationale
            FROM conflict_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "rationale": row[4]
            }
            for row in cursor.fetchall()
        ]
    
    xǁConflictLoggerǁget_undo_history__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictLoggerǁget_undo_history__mutmut_1': xǁConflictLoggerǁget_undo_history__mutmut_1, 
        'xǁConflictLoggerǁget_undo_history__mutmut_2': xǁConflictLoggerǁget_undo_history__mutmut_2, 
        'xǁConflictLoggerǁget_undo_history__mutmut_3': xǁConflictLoggerǁget_undo_history__mutmut_3, 
        'xǁConflictLoggerǁget_undo_history__mutmut_4': xǁConflictLoggerǁget_undo_history__mutmut_4, 
        'xǁConflictLoggerǁget_undo_history__mutmut_5': xǁConflictLoggerǁget_undo_history__mutmut_5, 
        'xǁConflictLoggerǁget_undo_history__mutmut_6': xǁConflictLoggerǁget_undo_history__mutmut_6, 
        'xǁConflictLoggerǁget_undo_history__mutmut_7': xǁConflictLoggerǁget_undo_history__mutmut_7, 
        'xǁConflictLoggerǁget_undo_history__mutmut_8': xǁConflictLoggerǁget_undo_history__mutmut_8, 
        'xǁConflictLoggerǁget_undo_history__mutmut_9': xǁConflictLoggerǁget_undo_history__mutmut_9, 
        'xǁConflictLoggerǁget_undo_history__mutmut_10': xǁConflictLoggerǁget_undo_history__mutmut_10, 
        'xǁConflictLoggerǁget_undo_history__mutmut_11': xǁConflictLoggerǁget_undo_history__mutmut_11, 
        'xǁConflictLoggerǁget_undo_history__mutmut_12': xǁConflictLoggerǁget_undo_history__mutmut_12, 
        'xǁConflictLoggerǁget_undo_history__mutmut_13': xǁConflictLoggerǁget_undo_history__mutmut_13, 
        'xǁConflictLoggerǁget_undo_history__mutmut_14': xǁConflictLoggerǁget_undo_history__mutmut_14, 
        'xǁConflictLoggerǁget_undo_history__mutmut_15': xǁConflictLoggerǁget_undo_history__mutmut_15, 
        'xǁConflictLoggerǁget_undo_history__mutmut_16': xǁConflictLoggerǁget_undo_history__mutmut_16, 
        'xǁConflictLoggerǁget_undo_history__mutmut_17': xǁConflictLoggerǁget_undo_history__mutmut_17, 
        'xǁConflictLoggerǁget_undo_history__mutmut_18': xǁConflictLoggerǁget_undo_history__mutmut_18
    }
    
    def get_undo_history(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictLoggerǁget_undo_history__mutmut_orig"), object.__getattribute__(self, "xǁConflictLoggerǁget_undo_history__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_undo_history.__signature__ = _mutmut_signature(xǁConflictLoggerǁget_undo_history__mutmut_orig)
    xǁConflictLoggerǁget_undo_history__mutmut_orig.__name__ = 'xǁConflictLoggerǁget_undo_history'
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_orig(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_1(self, limit: int = 11) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_2(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = None
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_3(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute(None, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_4(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, None)
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_5(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute((limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_6(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, )
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_7(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "XXidXX": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_8(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "ID": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_9(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[1],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_10(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "XXconflict_log_idXX": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_11(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "CONFLICT_LOG_ID": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_12(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[2],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_13(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "XXmemory_idXX": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_14(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "MEMORY_ID": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_15(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[3],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_16(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "XXactionXX": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_17(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "ACTION": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_18(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[4],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_19(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "XXtimestampXX": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_20(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "TIMESTAMP": row[4],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_21(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[5],
                "resolution_action": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_22(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "XXresolution_actionXX": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_23(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "RESOLUTION_ACTION": row[5],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_24(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[6],
                "rationale": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_25(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "XXrationaleXX": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_26(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "RATIONALE": row[6]
            }
            for row in cursor.fetchall()
        ]
    
    def xǁConflictLoggerǁget_resolution_history__mutmut_27(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get resolution history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of resolution history records
        """
        self.storage._ensure_connection()
        cursor = self.storage._connection.cursor()
        
        cursor.execute("""
            SELECT rh.id, rh.conflict_log_id, rh.memory_id, rh.action, rh.timestamp,
                   cl.resolution_action, cl.rationale
            FROM resolution_history rh
            JOIN conflict_log cl ON rh.conflict_log_id = cl.id
            ORDER BY rh.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                "id": row[0],
                "conflict_log_id": row[1],
                "memory_id": row[2],
                "action": row[3],
                "timestamp": row[4],
                "resolution_action": row[5],
                "rationale": row[7]
            }
            for row in cursor.fetchall()
        ]
    
    xǁConflictLoggerǁget_resolution_history__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁConflictLoggerǁget_resolution_history__mutmut_1': xǁConflictLoggerǁget_resolution_history__mutmut_1, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_2': xǁConflictLoggerǁget_resolution_history__mutmut_2, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_3': xǁConflictLoggerǁget_resolution_history__mutmut_3, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_4': xǁConflictLoggerǁget_resolution_history__mutmut_4, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_5': xǁConflictLoggerǁget_resolution_history__mutmut_5, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_6': xǁConflictLoggerǁget_resolution_history__mutmut_6, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_7': xǁConflictLoggerǁget_resolution_history__mutmut_7, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_8': xǁConflictLoggerǁget_resolution_history__mutmut_8, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_9': xǁConflictLoggerǁget_resolution_history__mutmut_9, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_10': xǁConflictLoggerǁget_resolution_history__mutmut_10, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_11': xǁConflictLoggerǁget_resolution_history__mutmut_11, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_12': xǁConflictLoggerǁget_resolution_history__mutmut_12, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_13': xǁConflictLoggerǁget_resolution_history__mutmut_13, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_14': xǁConflictLoggerǁget_resolution_history__mutmut_14, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_15': xǁConflictLoggerǁget_resolution_history__mutmut_15, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_16': xǁConflictLoggerǁget_resolution_history__mutmut_16, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_17': xǁConflictLoggerǁget_resolution_history__mutmut_17, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_18': xǁConflictLoggerǁget_resolution_history__mutmut_18, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_19': xǁConflictLoggerǁget_resolution_history__mutmut_19, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_20': xǁConflictLoggerǁget_resolution_history__mutmut_20, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_21': xǁConflictLoggerǁget_resolution_history__mutmut_21, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_22': xǁConflictLoggerǁget_resolution_history__mutmut_22, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_23': xǁConflictLoggerǁget_resolution_history__mutmut_23, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_24': xǁConflictLoggerǁget_resolution_history__mutmut_24, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_25': xǁConflictLoggerǁget_resolution_history__mutmut_25, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_26': xǁConflictLoggerǁget_resolution_history__mutmut_26, 
        'xǁConflictLoggerǁget_resolution_history__mutmut_27': xǁConflictLoggerǁget_resolution_history__mutmut_27
    }
    
    def get_resolution_history(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁConflictLoggerǁget_resolution_history__mutmut_orig"), object.__getattribute__(self, "xǁConflictLoggerǁget_resolution_history__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_resolution_history.__signature__ = _mutmut_signature(xǁConflictLoggerǁget_resolution_history__mutmut_orig)
    xǁConflictLoggerǁget_resolution_history__mutmut_orig.__name__ = 'xǁConflictLoggerǁget_resolution_history'

