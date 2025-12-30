"""
Summary storage for managing session summaries, tasks, and project state.

Handles revision tracking, atomic writes, and file management.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional
import logging

from .models import SessionSummary, TasksFile, ProjectState

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


class SummaryStorage:
    """
    Manages storage of session summaries, tasks, and project state.
    
    Provides revision tracking with rollback capability and atomic writes.
    """
    
    def xǁSummaryStorageǁ__init____mutmut_orig(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_1(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = None
        self.summary_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_2(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(None)
        self.summary_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_3(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(parents=None, exist_ok=True)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_4(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(parents=True, exist_ok=None)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_5(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(exist_ok=True)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_6(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(parents=True, )
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_7(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(parents=False, exist_ok=True)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_8(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(parents=True, exist_ok=False)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def xǁSummaryStorageǁ__init____mutmut_9(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(parents=True, exist_ok=True)
        logger.debug(None)
    
    xǁSummaryStorageǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁ__init____mutmut_1': xǁSummaryStorageǁ__init____mutmut_1, 
        'xǁSummaryStorageǁ__init____mutmut_2': xǁSummaryStorageǁ__init____mutmut_2, 
        'xǁSummaryStorageǁ__init____mutmut_3': xǁSummaryStorageǁ__init____mutmut_3, 
        'xǁSummaryStorageǁ__init____mutmut_4': xǁSummaryStorageǁ__init____mutmut_4, 
        'xǁSummaryStorageǁ__init____mutmut_5': xǁSummaryStorageǁ__init____mutmut_5, 
        'xǁSummaryStorageǁ__init____mutmut_6': xǁSummaryStorageǁ__init____mutmut_6, 
        'xǁSummaryStorageǁ__init____mutmut_7': xǁSummaryStorageǁ__init____mutmut_7, 
        'xǁSummaryStorageǁ__init____mutmut_8': xǁSummaryStorageǁ__init____mutmut_8, 
        'xǁSummaryStorageǁ__init____mutmut_9': xǁSummaryStorageǁ__init____mutmut_9
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁSummaryStorageǁ__init____mutmut_orig)
    xǁSummaryStorageǁ__init____mutmut_orig.__name__ = 'xǁSummaryStorageǁ__init__'
    
    def xǁSummaryStorageǁ_get_session_summary_file__mutmut_orig(self, session_id: str, revision: Optional[int] = None) -> Path:
        """
        Get path to session summary file.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            Path to summary file
        """
        if revision is not None:
            filename = f"{session_id}_summary.rev{revision}.json"
        else:
            filename = f"{session_id}_summary.json"
        return self.summary_path / filename
    
    def xǁSummaryStorageǁ_get_session_summary_file__mutmut_1(self, session_id: str, revision: Optional[int] = None) -> Path:
        """
        Get path to session summary file.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            Path to summary file
        """
        if revision is None:
            filename = f"{session_id}_summary.rev{revision}.json"
        else:
            filename = f"{session_id}_summary.json"
        return self.summary_path / filename
    
    def xǁSummaryStorageǁ_get_session_summary_file__mutmut_2(self, session_id: str, revision: Optional[int] = None) -> Path:
        """
        Get path to session summary file.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            Path to summary file
        """
        if revision is not None:
            filename = None
        else:
            filename = f"{session_id}_summary.json"
        return self.summary_path / filename
    
    def xǁSummaryStorageǁ_get_session_summary_file__mutmut_3(self, session_id: str, revision: Optional[int] = None) -> Path:
        """
        Get path to session summary file.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            Path to summary file
        """
        if revision is not None:
            filename = f"{session_id}_summary.rev{revision}.json"
        else:
            filename = None
        return self.summary_path / filename
    
    def xǁSummaryStorageǁ_get_session_summary_file__mutmut_4(self, session_id: str, revision: Optional[int] = None) -> Path:
        """
        Get path to session summary file.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            Path to summary file
        """
        if revision is not None:
            filename = f"{session_id}_summary.rev{revision}.json"
        else:
            filename = f"{session_id}_summary.json"
        return self.summary_path * filename
    
    xǁSummaryStorageǁ_get_session_summary_file__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁ_get_session_summary_file__mutmut_1': xǁSummaryStorageǁ_get_session_summary_file__mutmut_1, 
        'xǁSummaryStorageǁ_get_session_summary_file__mutmut_2': xǁSummaryStorageǁ_get_session_summary_file__mutmut_2, 
        'xǁSummaryStorageǁ_get_session_summary_file__mutmut_3': xǁSummaryStorageǁ_get_session_summary_file__mutmut_3, 
        'xǁSummaryStorageǁ_get_session_summary_file__mutmut_4': xǁSummaryStorageǁ_get_session_summary_file__mutmut_4
    }
    
    def _get_session_summary_file(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁ_get_session_summary_file__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁ_get_session_summary_file__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_session_summary_file.__signature__ = _mutmut_signature(xǁSummaryStorageǁ_get_session_summary_file__mutmut_orig)
    xǁSummaryStorageǁ_get_session_summary_file__mutmut_orig.__name__ = 'xǁSummaryStorageǁ_get_session_summary_file'
    
    def xǁSummaryStorageǁ_get_tasks_file__mutmut_orig(self, session_id: str) -> Path:
        """Get path to tasks file for a session."""
        return self.summary_path / f"{session_id}_tasks.json"
    
    def xǁSummaryStorageǁ_get_tasks_file__mutmut_1(self, session_id: str) -> Path:
        """Get path to tasks file for a session."""
        return self.summary_path * f"{session_id}_tasks.json"
    
    xǁSummaryStorageǁ_get_tasks_file__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁ_get_tasks_file__mutmut_1': xǁSummaryStorageǁ_get_tasks_file__mutmut_1
    }
    
    def _get_tasks_file(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁ_get_tasks_file__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁ_get_tasks_file__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_tasks_file.__signature__ = _mutmut_signature(xǁSummaryStorageǁ_get_tasks_file__mutmut_orig)
    xǁSummaryStorageǁ_get_tasks_file__mutmut_orig.__name__ = 'xǁSummaryStorageǁ_get_tasks_file'
    
    def xǁSummaryStorageǁ_get_project_state_file__mutmut_orig(self) -> Path:
        """Get path to project state file (global, not per-session)."""
        return self.summary_path / "project_state.json"
    
    def xǁSummaryStorageǁ_get_project_state_file__mutmut_1(self) -> Path:
        """Get path to project state file (global, not per-session)."""
        return self.summary_path * "project_state.json"
    
    def xǁSummaryStorageǁ_get_project_state_file__mutmut_2(self) -> Path:
        """Get path to project state file (global, not per-session)."""
        return self.summary_path / "XXproject_state.jsonXX"
    
    def xǁSummaryStorageǁ_get_project_state_file__mutmut_3(self) -> Path:
        """Get path to project state file (global, not per-session)."""
        return self.summary_path / "PROJECT_STATE.JSON"
    
    xǁSummaryStorageǁ_get_project_state_file__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁ_get_project_state_file__mutmut_1': xǁSummaryStorageǁ_get_project_state_file__mutmut_1, 
        'xǁSummaryStorageǁ_get_project_state_file__mutmut_2': xǁSummaryStorageǁ_get_project_state_file__mutmut_2, 
        'xǁSummaryStorageǁ_get_project_state_file__mutmut_3': xǁSummaryStorageǁ_get_project_state_file__mutmut_3
    }
    
    def _get_project_state_file(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁ_get_project_state_file__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁ_get_project_state_file__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_project_state_file.__signature__ = _mutmut_signature(xǁSummaryStorageǁ_get_project_state_file__mutmut_orig)
    xǁSummaryStorageǁ_get_project_state_file__mutmut_orig.__name__ = 'xǁSummaryStorageǁ_get_project_state_file'
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_orig(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_1(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = None
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_2(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent * f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_3(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(None, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_4(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, None, encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_5(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding=None) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_6(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_7(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_8(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', ) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_9(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'XXwXX', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_10(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'W', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_11(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='XXutf-8XX') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_12(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='UTF-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_13(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(None, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_14(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, None, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_15(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=None, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_16(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=None)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_17(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_18(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_19(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_20(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, )
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_21(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=3, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_22(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=True)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_23(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(None)
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_24(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(None, str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_25(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), None)
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_26(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_27(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), )
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_28(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(None), str(file_path))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_29(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(None))
            logger.debug(f"Atomically wrote {file_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    def xǁSummaryStorageǁ_atomic_write__mutmut_30(self, file_path: Path, data: dict) -> None:
        """
        Write data to file atomically (temp file + rename).
        
        Args:
            file_path: Target file path
            data: Dictionary to write as JSON
        """
        # Create temp file in same directory
        temp_path = file_path.parent / f".{file_path.name}.tmp"
        
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            os.replace(str(temp_path), str(file_path))
            logger.debug(None)
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
    
    xǁSummaryStorageǁ_atomic_write__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁ_atomic_write__mutmut_1': xǁSummaryStorageǁ_atomic_write__mutmut_1, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_2': xǁSummaryStorageǁ_atomic_write__mutmut_2, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_3': xǁSummaryStorageǁ_atomic_write__mutmut_3, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_4': xǁSummaryStorageǁ_atomic_write__mutmut_4, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_5': xǁSummaryStorageǁ_atomic_write__mutmut_5, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_6': xǁSummaryStorageǁ_atomic_write__mutmut_6, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_7': xǁSummaryStorageǁ_atomic_write__mutmut_7, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_8': xǁSummaryStorageǁ_atomic_write__mutmut_8, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_9': xǁSummaryStorageǁ_atomic_write__mutmut_9, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_10': xǁSummaryStorageǁ_atomic_write__mutmut_10, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_11': xǁSummaryStorageǁ_atomic_write__mutmut_11, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_12': xǁSummaryStorageǁ_atomic_write__mutmut_12, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_13': xǁSummaryStorageǁ_atomic_write__mutmut_13, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_14': xǁSummaryStorageǁ_atomic_write__mutmut_14, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_15': xǁSummaryStorageǁ_atomic_write__mutmut_15, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_16': xǁSummaryStorageǁ_atomic_write__mutmut_16, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_17': xǁSummaryStorageǁ_atomic_write__mutmut_17, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_18': xǁSummaryStorageǁ_atomic_write__mutmut_18, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_19': xǁSummaryStorageǁ_atomic_write__mutmut_19, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_20': xǁSummaryStorageǁ_atomic_write__mutmut_20, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_21': xǁSummaryStorageǁ_atomic_write__mutmut_21, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_22': xǁSummaryStorageǁ_atomic_write__mutmut_22, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_23': xǁSummaryStorageǁ_atomic_write__mutmut_23, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_24': xǁSummaryStorageǁ_atomic_write__mutmut_24, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_25': xǁSummaryStorageǁ_atomic_write__mutmut_25, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_26': xǁSummaryStorageǁ_atomic_write__mutmut_26, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_27': xǁSummaryStorageǁ_atomic_write__mutmut_27, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_28': xǁSummaryStorageǁ_atomic_write__mutmut_28, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_29': xǁSummaryStorageǁ_atomic_write__mutmut_29, 
        'xǁSummaryStorageǁ_atomic_write__mutmut_30': xǁSummaryStorageǁ_atomic_write__mutmut_30
    }
    
    def _atomic_write(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁ_atomic_write__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁ_atomic_write__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _atomic_write.__signature__ = _mutmut_signature(xǁSummaryStorageǁ_atomic_write__mutmut_orig)
    xǁSummaryStorageǁ_atomic_write__mutmut_orig.__name__ = 'xǁSummaryStorageǁ_atomic_write'
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_orig(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_1(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = False
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_2(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = None
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_3(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(None)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_4(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup or current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_5(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = None
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_6(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(None)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_7(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = None
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_8(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = None
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_9(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(None, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_10(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, None)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_11(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_12(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, )
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_13(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(None, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_14(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, None)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_15(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_16(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, )
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_17(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(None)
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_18(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(None)
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_19(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = None
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_20(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(None)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_21(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(None, summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_22(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, None)
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_23(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(summary.model_dump())
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_24(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, )
        logger.info(f"Saved session summary for {session_id}, revision {summary.header.revision}")
    
    def xǁSummaryStorageǁsave_session_summary__mutmut_25(
        self,
        session_id: str,
        summary: SessionSummary,
        create_backup: bool = True
    ) -> None:
        """
        Save session summary with revision tracking.
        
        Args:
            session_id: Session identifier
            summary: SessionSummary to save
            create_backup: If True, create backup of previous revision
        """
        # Create backup of current revision if it exists
        current_file = self._get_session_summary_file(session_id)
        if create_backup and current_file.exists():
            try:
                current_summary = self.load_session_summary(session_id)
                if current_summary:
                    backup_revision = current_summary.header.revision
                    backup_file = self._get_session_summary_file(session_id, backup_revision)
                    shutil.copy2(current_file, backup_file)
                    logger.debug(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Save new summary
        file_path = self._get_session_summary_file(session_id)
        self._atomic_write(file_path, summary.model_dump())
        logger.info(None)
    
    xǁSummaryStorageǁsave_session_summary__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁsave_session_summary__mutmut_1': xǁSummaryStorageǁsave_session_summary__mutmut_1, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_2': xǁSummaryStorageǁsave_session_summary__mutmut_2, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_3': xǁSummaryStorageǁsave_session_summary__mutmut_3, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_4': xǁSummaryStorageǁsave_session_summary__mutmut_4, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_5': xǁSummaryStorageǁsave_session_summary__mutmut_5, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_6': xǁSummaryStorageǁsave_session_summary__mutmut_6, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_7': xǁSummaryStorageǁsave_session_summary__mutmut_7, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_8': xǁSummaryStorageǁsave_session_summary__mutmut_8, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_9': xǁSummaryStorageǁsave_session_summary__mutmut_9, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_10': xǁSummaryStorageǁsave_session_summary__mutmut_10, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_11': xǁSummaryStorageǁsave_session_summary__mutmut_11, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_12': xǁSummaryStorageǁsave_session_summary__mutmut_12, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_13': xǁSummaryStorageǁsave_session_summary__mutmut_13, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_14': xǁSummaryStorageǁsave_session_summary__mutmut_14, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_15': xǁSummaryStorageǁsave_session_summary__mutmut_15, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_16': xǁSummaryStorageǁsave_session_summary__mutmut_16, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_17': xǁSummaryStorageǁsave_session_summary__mutmut_17, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_18': xǁSummaryStorageǁsave_session_summary__mutmut_18, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_19': xǁSummaryStorageǁsave_session_summary__mutmut_19, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_20': xǁSummaryStorageǁsave_session_summary__mutmut_20, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_21': xǁSummaryStorageǁsave_session_summary__mutmut_21, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_22': xǁSummaryStorageǁsave_session_summary__mutmut_22, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_23': xǁSummaryStorageǁsave_session_summary__mutmut_23, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_24': xǁSummaryStorageǁsave_session_summary__mutmut_24, 
        'xǁSummaryStorageǁsave_session_summary__mutmut_25': xǁSummaryStorageǁsave_session_summary__mutmut_25
    }
    
    def save_session_summary(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁsave_session_summary__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁsave_session_summary__mutmut_mutants"), args, kwargs, self)
        return result 
    
    save_session_summary.__signature__ = _mutmut_signature(xǁSummaryStorageǁsave_session_summary__mutmut_orig)
    xǁSummaryStorageǁsave_session_summary__mutmut_orig.__name__ = 'xǁSummaryStorageǁsave_session_summary'
    
    def xǁSummaryStorageǁload_session_summary__mutmut_orig(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_1(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = None
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_2(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(None, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_3(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, None)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_4(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_5(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, )
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_6(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_7(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(None, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_8(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, None, encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_9(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding=None) as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_10(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open('r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_11(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_12(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', ) as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_13(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'XXrXX', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_14(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'R', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_15(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='XXutf-8XX') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_16(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='UTF-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_17(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = None
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_18(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(None)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(f"Failed to load session summary from {file_path}: {e}")
            return None
    
    def xǁSummaryStorageǁload_session_summary__mutmut_19(
        self,
        session_id: str,
        revision: Optional[int] = None
    ) -> Optional[SessionSummary]:
        """
        Load session summary.
        
        Args:
            session_id: Session identifier
            revision: Optional revision number (None for latest)
            
        Returns:
            SessionSummary if found, None otherwise
        """
        file_path = self._get_session_summary_file(session_id, revision)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SessionSummary(**data)
        except Exception as e:
            logger.error(None)
            return None
    
    xǁSummaryStorageǁload_session_summary__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁload_session_summary__mutmut_1': xǁSummaryStorageǁload_session_summary__mutmut_1, 
        'xǁSummaryStorageǁload_session_summary__mutmut_2': xǁSummaryStorageǁload_session_summary__mutmut_2, 
        'xǁSummaryStorageǁload_session_summary__mutmut_3': xǁSummaryStorageǁload_session_summary__mutmut_3, 
        'xǁSummaryStorageǁload_session_summary__mutmut_4': xǁSummaryStorageǁload_session_summary__mutmut_4, 
        'xǁSummaryStorageǁload_session_summary__mutmut_5': xǁSummaryStorageǁload_session_summary__mutmut_5, 
        'xǁSummaryStorageǁload_session_summary__mutmut_6': xǁSummaryStorageǁload_session_summary__mutmut_6, 
        'xǁSummaryStorageǁload_session_summary__mutmut_7': xǁSummaryStorageǁload_session_summary__mutmut_7, 
        'xǁSummaryStorageǁload_session_summary__mutmut_8': xǁSummaryStorageǁload_session_summary__mutmut_8, 
        'xǁSummaryStorageǁload_session_summary__mutmut_9': xǁSummaryStorageǁload_session_summary__mutmut_9, 
        'xǁSummaryStorageǁload_session_summary__mutmut_10': xǁSummaryStorageǁload_session_summary__mutmut_10, 
        'xǁSummaryStorageǁload_session_summary__mutmut_11': xǁSummaryStorageǁload_session_summary__mutmut_11, 
        'xǁSummaryStorageǁload_session_summary__mutmut_12': xǁSummaryStorageǁload_session_summary__mutmut_12, 
        'xǁSummaryStorageǁload_session_summary__mutmut_13': xǁSummaryStorageǁload_session_summary__mutmut_13, 
        'xǁSummaryStorageǁload_session_summary__mutmut_14': xǁSummaryStorageǁload_session_summary__mutmut_14, 
        'xǁSummaryStorageǁload_session_summary__mutmut_15': xǁSummaryStorageǁload_session_summary__mutmut_15, 
        'xǁSummaryStorageǁload_session_summary__mutmut_16': xǁSummaryStorageǁload_session_summary__mutmut_16, 
        'xǁSummaryStorageǁload_session_summary__mutmut_17': xǁSummaryStorageǁload_session_summary__mutmut_17, 
        'xǁSummaryStorageǁload_session_summary__mutmut_18': xǁSummaryStorageǁload_session_summary__mutmut_18, 
        'xǁSummaryStorageǁload_session_summary__mutmut_19': xǁSummaryStorageǁload_session_summary__mutmut_19
    }
    
    def load_session_summary(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁload_session_summary__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁload_session_summary__mutmut_mutants"), args, kwargs, self)
        return result 
    
    load_session_summary.__signature__ = _mutmut_signature(xǁSummaryStorageǁload_session_summary__mutmut_orig)
    xǁSummaryStorageǁload_session_summary__mutmut_orig.__name__ = 'xǁSummaryStorageǁload_session_summary'
    
    def xǁSummaryStorageǁsave_tasks__mutmut_orig(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = self._get_tasks_file(session_id)
        self._atomic_write(file_path, tasks_file.model_dump())
        logger.debug(f"Saved tasks for session {session_id}")
    
    def xǁSummaryStorageǁsave_tasks__mutmut_1(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = None
        self._atomic_write(file_path, tasks_file.model_dump())
        logger.debug(f"Saved tasks for session {session_id}")
    
    def xǁSummaryStorageǁsave_tasks__mutmut_2(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = self._get_tasks_file(None)
        self._atomic_write(file_path, tasks_file.model_dump())
        logger.debug(f"Saved tasks for session {session_id}")
    
    def xǁSummaryStorageǁsave_tasks__mutmut_3(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = self._get_tasks_file(session_id)
        self._atomic_write(None, tasks_file.model_dump())
        logger.debug(f"Saved tasks for session {session_id}")
    
    def xǁSummaryStorageǁsave_tasks__mutmut_4(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = self._get_tasks_file(session_id)
        self._atomic_write(file_path, None)
        logger.debug(f"Saved tasks for session {session_id}")
    
    def xǁSummaryStorageǁsave_tasks__mutmut_5(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = self._get_tasks_file(session_id)
        self._atomic_write(tasks_file.model_dump())
        logger.debug(f"Saved tasks for session {session_id}")
    
    def xǁSummaryStorageǁsave_tasks__mutmut_6(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = self._get_tasks_file(session_id)
        self._atomic_write(file_path, )
        logger.debug(f"Saved tasks for session {session_id}")
    
    def xǁSummaryStorageǁsave_tasks__mutmut_7(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = self._get_tasks_file(session_id)
        self._atomic_write(file_path, tasks_file.model_dump())
        logger.debug(None)
    
    xǁSummaryStorageǁsave_tasks__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁsave_tasks__mutmut_1': xǁSummaryStorageǁsave_tasks__mutmut_1, 
        'xǁSummaryStorageǁsave_tasks__mutmut_2': xǁSummaryStorageǁsave_tasks__mutmut_2, 
        'xǁSummaryStorageǁsave_tasks__mutmut_3': xǁSummaryStorageǁsave_tasks__mutmut_3, 
        'xǁSummaryStorageǁsave_tasks__mutmut_4': xǁSummaryStorageǁsave_tasks__mutmut_4, 
        'xǁSummaryStorageǁsave_tasks__mutmut_5': xǁSummaryStorageǁsave_tasks__mutmut_5, 
        'xǁSummaryStorageǁsave_tasks__mutmut_6': xǁSummaryStorageǁsave_tasks__mutmut_6, 
        'xǁSummaryStorageǁsave_tasks__mutmut_7': xǁSummaryStorageǁsave_tasks__mutmut_7
    }
    
    def save_tasks(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁsave_tasks__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁsave_tasks__mutmut_mutants"), args, kwargs, self)
        return result 
    
    save_tasks.__signature__ = _mutmut_signature(xǁSummaryStorageǁsave_tasks__mutmut_orig)
    xǁSummaryStorageǁsave_tasks__mutmut_orig.__name__ = 'xǁSummaryStorageǁsave_tasks'
    
    def xǁSummaryStorageǁload_tasks__mutmut_orig(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_1(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = None
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_2(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(None)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_3(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_4(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(None, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_5(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, None, encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_6(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding=None) as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_7(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open('r', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_8(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_9(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', ) as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_10(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'XXrXX', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_11(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'R', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_12(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='XXutf-8XX') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_13(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='UTF-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_14(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = None
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_15(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(None)
            return TasksFile(**data)
        except Exception as e:
            logger.error(f"Failed to load tasks from {file_path}: {e}")
            return TasksFile()
    
    def xǁSummaryStorageǁload_tasks__mutmut_16(self, session_id: str) -> TasksFile:
        """
        Load tasks file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TasksFile (empty if not found)
        """
        file_path = self._get_tasks_file(session_id)
        
        if not file_path.exists():
            return TasksFile()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TasksFile(**data)
        except Exception as e:
            logger.error(None)
            return TasksFile()
    
    xǁSummaryStorageǁload_tasks__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁload_tasks__mutmut_1': xǁSummaryStorageǁload_tasks__mutmut_1, 
        'xǁSummaryStorageǁload_tasks__mutmut_2': xǁSummaryStorageǁload_tasks__mutmut_2, 
        'xǁSummaryStorageǁload_tasks__mutmut_3': xǁSummaryStorageǁload_tasks__mutmut_3, 
        'xǁSummaryStorageǁload_tasks__mutmut_4': xǁSummaryStorageǁload_tasks__mutmut_4, 
        'xǁSummaryStorageǁload_tasks__mutmut_5': xǁSummaryStorageǁload_tasks__mutmut_5, 
        'xǁSummaryStorageǁload_tasks__mutmut_6': xǁSummaryStorageǁload_tasks__mutmut_6, 
        'xǁSummaryStorageǁload_tasks__mutmut_7': xǁSummaryStorageǁload_tasks__mutmut_7, 
        'xǁSummaryStorageǁload_tasks__mutmut_8': xǁSummaryStorageǁload_tasks__mutmut_8, 
        'xǁSummaryStorageǁload_tasks__mutmut_9': xǁSummaryStorageǁload_tasks__mutmut_9, 
        'xǁSummaryStorageǁload_tasks__mutmut_10': xǁSummaryStorageǁload_tasks__mutmut_10, 
        'xǁSummaryStorageǁload_tasks__mutmut_11': xǁSummaryStorageǁload_tasks__mutmut_11, 
        'xǁSummaryStorageǁload_tasks__mutmut_12': xǁSummaryStorageǁload_tasks__mutmut_12, 
        'xǁSummaryStorageǁload_tasks__mutmut_13': xǁSummaryStorageǁload_tasks__mutmut_13, 
        'xǁSummaryStorageǁload_tasks__mutmut_14': xǁSummaryStorageǁload_tasks__mutmut_14, 
        'xǁSummaryStorageǁload_tasks__mutmut_15': xǁSummaryStorageǁload_tasks__mutmut_15, 
        'xǁSummaryStorageǁload_tasks__mutmut_16': xǁSummaryStorageǁload_tasks__mutmut_16
    }
    
    def load_tasks(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁload_tasks__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁload_tasks__mutmut_mutants"), args, kwargs, self)
        return result 
    
    load_tasks.__signature__ = _mutmut_signature(xǁSummaryStorageǁload_tasks__mutmut_orig)
    xǁSummaryStorageǁload_tasks__mutmut_orig.__name__ = 'xǁSummaryStorageǁload_tasks'
    
    def xǁSummaryStorageǁsave_project_state__mutmut_orig(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(file_path, project_state.model_dump())
        logger.debug("Saved project state")
    
    def xǁSummaryStorageǁsave_project_state__mutmut_1(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = None
        self._atomic_write(file_path, project_state.model_dump())
        logger.debug("Saved project state")
    
    def xǁSummaryStorageǁsave_project_state__mutmut_2(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(None, project_state.model_dump())
        logger.debug("Saved project state")
    
    def xǁSummaryStorageǁsave_project_state__mutmut_3(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(file_path, None)
        logger.debug("Saved project state")
    
    def xǁSummaryStorageǁsave_project_state__mutmut_4(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(project_state.model_dump())
        logger.debug("Saved project state")
    
    def xǁSummaryStorageǁsave_project_state__mutmut_5(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(file_path, )
        logger.debug("Saved project state")
    
    def xǁSummaryStorageǁsave_project_state__mutmut_6(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(file_path, project_state.model_dump())
        logger.debug(None)
    
    def xǁSummaryStorageǁsave_project_state__mutmut_7(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(file_path, project_state.model_dump())
        logger.debug("XXSaved project stateXX")
    
    def xǁSummaryStorageǁsave_project_state__mutmut_8(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(file_path, project_state.model_dump())
        logger.debug("saved project state")
    
    def xǁSummaryStorageǁsave_project_state__mutmut_9(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(file_path, project_state.model_dump())
        logger.debug("SAVED PROJECT STATE")
    
    xǁSummaryStorageǁsave_project_state__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁsave_project_state__mutmut_1': xǁSummaryStorageǁsave_project_state__mutmut_1, 
        'xǁSummaryStorageǁsave_project_state__mutmut_2': xǁSummaryStorageǁsave_project_state__mutmut_2, 
        'xǁSummaryStorageǁsave_project_state__mutmut_3': xǁSummaryStorageǁsave_project_state__mutmut_3, 
        'xǁSummaryStorageǁsave_project_state__mutmut_4': xǁSummaryStorageǁsave_project_state__mutmut_4, 
        'xǁSummaryStorageǁsave_project_state__mutmut_5': xǁSummaryStorageǁsave_project_state__mutmut_5, 
        'xǁSummaryStorageǁsave_project_state__mutmut_6': xǁSummaryStorageǁsave_project_state__mutmut_6, 
        'xǁSummaryStorageǁsave_project_state__mutmut_7': xǁSummaryStorageǁsave_project_state__mutmut_7, 
        'xǁSummaryStorageǁsave_project_state__mutmut_8': xǁSummaryStorageǁsave_project_state__mutmut_8, 
        'xǁSummaryStorageǁsave_project_state__mutmut_9': xǁSummaryStorageǁsave_project_state__mutmut_9
    }
    
    def save_project_state(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁsave_project_state__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁsave_project_state__mutmut_mutants"), args, kwargs, self)
        return result 
    
    save_project_state.__signature__ = _mutmut_signature(xǁSummaryStorageǁsave_project_state__mutmut_orig)
    xǁSummaryStorageǁsave_project_state__mutmut_orig.__name__ = 'xǁSummaryStorageǁsave_project_state'
    
    def xǁSummaryStorageǁload_project_state__mutmut_orig(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_1(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = None
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_2(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_3(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(None, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_4(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, None, encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_5(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding=None) as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_6(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open('r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_7(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_8(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', ) as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_9(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'XXrXX', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_10(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'R', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_11(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding='XXutf-8XX') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_12(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding='UTF-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_13(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = None
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_14(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(None)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load project state from {file_path}: {e}")
            return ProjectState()
    
    def xǁSummaryStorageǁload_project_state__mutmut_15(self) -> ProjectState:
        """
        Load project state.
        
        Returns:
            ProjectState (empty if not found)
        """
        file_path = self._get_project_state_file()
        
        if not file_path.exists():
            return ProjectState()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(None)
            return ProjectState()
    
    xǁSummaryStorageǁload_project_state__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁload_project_state__mutmut_1': xǁSummaryStorageǁload_project_state__mutmut_1, 
        'xǁSummaryStorageǁload_project_state__mutmut_2': xǁSummaryStorageǁload_project_state__mutmut_2, 
        'xǁSummaryStorageǁload_project_state__mutmut_3': xǁSummaryStorageǁload_project_state__mutmut_3, 
        'xǁSummaryStorageǁload_project_state__mutmut_4': xǁSummaryStorageǁload_project_state__mutmut_4, 
        'xǁSummaryStorageǁload_project_state__mutmut_5': xǁSummaryStorageǁload_project_state__mutmut_5, 
        'xǁSummaryStorageǁload_project_state__mutmut_6': xǁSummaryStorageǁload_project_state__mutmut_6, 
        'xǁSummaryStorageǁload_project_state__mutmut_7': xǁSummaryStorageǁload_project_state__mutmut_7, 
        'xǁSummaryStorageǁload_project_state__mutmut_8': xǁSummaryStorageǁload_project_state__mutmut_8, 
        'xǁSummaryStorageǁload_project_state__mutmut_9': xǁSummaryStorageǁload_project_state__mutmut_9, 
        'xǁSummaryStorageǁload_project_state__mutmut_10': xǁSummaryStorageǁload_project_state__mutmut_10, 
        'xǁSummaryStorageǁload_project_state__mutmut_11': xǁSummaryStorageǁload_project_state__mutmut_11, 
        'xǁSummaryStorageǁload_project_state__mutmut_12': xǁSummaryStorageǁload_project_state__mutmut_12, 
        'xǁSummaryStorageǁload_project_state__mutmut_13': xǁSummaryStorageǁload_project_state__mutmut_13, 
        'xǁSummaryStorageǁload_project_state__mutmut_14': xǁSummaryStorageǁload_project_state__mutmut_14, 
        'xǁSummaryStorageǁload_project_state__mutmut_15': xǁSummaryStorageǁload_project_state__mutmut_15
    }
    
    def load_project_state(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁload_project_state__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁload_project_state__mutmut_mutants"), args, kwargs, self)
        return result 
    
    load_project_state.__signature__ = _mutmut_signature(xǁSummaryStorageǁload_project_state__mutmut_orig)
    xǁSummaryStorageǁload_project_state__mutmut_orig.__name__ = 'xǁSummaryStorageǁload_project_state'
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_orig(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_1(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = None
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_2(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob(None):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_3(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("XX*_summary.jsonXX"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_4(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_SUMMARY.JSON"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_5(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = None
            if filename.endswith("_summary"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_6(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith(None):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_7(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("XX_summaryXX"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_8(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_SUMMARY"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_9(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = None  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_10(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:+8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_11(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:-9]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_12(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(None)
        
        return sorted(session_ids)
    
    def xǁSummaryStorageǁlist_session_summaries__mutmut_13(self) -> list[str]:
        """
        List all session IDs that have summaries.
        
        Returns:
            List of session IDs
        """
        session_ids = set()
        
        for file_path in self.summary_path.glob("*_summary.json"):
            # Extract session_id from filename (remove _summary.json)
            filename = file_path.stem
            if filename.endswith("_summary"):
                session_id = filename[:-8]  # Remove "_summary"
                session_ids.add(session_id)
        
        return sorted(None)
    
    xǁSummaryStorageǁlist_session_summaries__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁSummaryStorageǁlist_session_summaries__mutmut_1': xǁSummaryStorageǁlist_session_summaries__mutmut_1, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_2': xǁSummaryStorageǁlist_session_summaries__mutmut_2, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_3': xǁSummaryStorageǁlist_session_summaries__mutmut_3, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_4': xǁSummaryStorageǁlist_session_summaries__mutmut_4, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_5': xǁSummaryStorageǁlist_session_summaries__mutmut_5, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_6': xǁSummaryStorageǁlist_session_summaries__mutmut_6, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_7': xǁSummaryStorageǁlist_session_summaries__mutmut_7, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_8': xǁSummaryStorageǁlist_session_summaries__mutmut_8, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_9': xǁSummaryStorageǁlist_session_summaries__mutmut_9, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_10': xǁSummaryStorageǁlist_session_summaries__mutmut_10, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_11': xǁSummaryStorageǁlist_session_summaries__mutmut_11, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_12': xǁSummaryStorageǁlist_session_summaries__mutmut_12, 
        'xǁSummaryStorageǁlist_session_summaries__mutmut_13': xǁSummaryStorageǁlist_session_summaries__mutmut_13
    }
    
    def list_session_summaries(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁSummaryStorageǁlist_session_summaries__mutmut_orig"), object.__getattribute__(self, "xǁSummaryStorageǁlist_session_summaries__mutmut_mutants"), args, kwargs, self)
        return result 
    
    list_session_summaries.__signature__ = _mutmut_signature(xǁSummaryStorageǁlist_session_summaries__mutmut_orig)
    xǁSummaryStorageǁlist_session_summaries__mutmut_orig.__name__ = 'xǁSummaryStorageǁlist_session_summaries'

