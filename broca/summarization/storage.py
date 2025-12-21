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


class SummaryStorage:
    """
    Manages storage of session summaries, tasks, and project state.
    
    Provides revision tracking with rollback capability and atomic writes.
    """
    
    def __init__(self, summary_path: str | Path) -> None:
        """
        Initialize summary storage.
        
        Args:
            summary_path: Directory where summary files will be stored
        """
        self.summary_path = Path(summary_path)
        self.summary_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized SummaryStorage with path: {self.summary_path}")
    
    def _get_session_summary_file(self, session_id: str, revision: Optional[int] = None) -> Path:
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
    
    def _get_tasks_file(self, session_id: str) -> Path:
        """Get path to tasks file for a session."""
        return self.summary_path / f"{session_id}_tasks.json"
    
    def _get_project_state_file(self) -> Path:
        """Get path to project state file (global, not per-session)."""
        return self.summary_path / "project_state.json"
    
    def _atomic_write(self, file_path: Path, data: dict) -> None:
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
    
    def save_session_summary(
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
    
    def load_session_summary(
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
    
    def save_tasks(self, session_id: str, tasks_file: TasksFile) -> None:
        """
        Save tasks file.
        
        Args:
            session_id: Session identifier
            tasks_file: TasksFile to save
        """
        file_path = self._get_tasks_file(session_id)
        self._atomic_write(file_path, tasks_file.model_dump())
        logger.debug(f"Saved tasks for session {session_id}")
    
    def load_tasks(self, session_id: str) -> TasksFile:
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
    
    def save_project_state(self, project_state: ProjectState) -> None:
        """
        Save project state.
        
        Args:
            project_state: ProjectState to save
        """
        file_path = self._get_project_state_file()
        self._atomic_write(file_path, project_state.model_dump())
        logger.debug("Saved project state")
    
    def load_project_state(self) -> ProjectState:
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
    
    def list_session_summaries(self) -> list[str]:
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

