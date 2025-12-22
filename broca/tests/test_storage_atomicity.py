"""
Tests for SummaryStorage atomic write/load operations.

Tests atomicity, backup creation, and failure scenarios.
"""

from __future__ import annotations

import tempfile
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from broca.summarization.storage import SummaryStorage
from broca.summarization.models import SessionSummary, SummaryHeader, SummaryBlocks, TasksFile, Task


@pytest.fixture
def temp_storage_dir():
    """Temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def storage(temp_storage_dir):
    """SummaryStorage instance."""
    return SummaryStorage(summary_path=temp_storage_dir)


class TestStorageAtomicity:
    """Tests for atomic write operations."""
    
    def test_atomic_write_creates_temp_file_first(self, storage, temp_storage_dir):
        """Test that atomic write creates temp file before replacing."""
        session_id = "test_session"
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="Test goal")
        )
        
        # Save summary
        storage.save_session_summary(session_id, summary)
        
        # Verify main file exists and is valid JSON
        summary_file = Path(temp_storage_dir) / f"{session_id}_summary.json"
        assert summary_file.exists()
        
        with open(summary_file, 'r') as f:
            data = json.load(f)
            assert data["header"]["session_id"] == session_id
    
    def test_atomic_write_cleanup_temp_on_error(self, storage, temp_storage_dir):
        """Test that temp file is cleaned up on write error."""
        session_id = "test_session"
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="Test goal")
        )
        
        # Simulate write error
        with patch('builtins.open', side_effect=IOError("Write failed")):
            try:
                storage.save_session_summary(session_id, summary)
                pytest.fail("Should have raised IOError")
            except IOError:
                pass
        
        # Verify temp file doesn't exist
        temp_file = Path(temp_storage_dir) / f".{session_id}_summary.json.tmp"
        assert not temp_file.exists()
    
    def test_atomic_write_survives_process_interruption(self, storage, temp_storage_dir):
        """Test that atomic write survives simulated process interruption."""
        session_id = "test_session"
        
        # Create initial summary
        summary1 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="Original goal")
        )
        
        storage.save_session_summary(session_id, summary1)
        
        # Verify original exists
        summary_file = Path(temp_storage_dir) / f"{session_id}_summary.json"
        assert summary_file.exists()
        
        # Simulate partial write (create temp but don't complete)
        temp_file = summary_file.parent / f".{summary_file.name}.tmp"
        with open(temp_file, 'w') as f:
            f.write("invalid json{")  # Incomplete write
        
        # Verify original file still exists and is valid
        assert summary_file.exists()
        loaded = storage.load_session_summary(session_id)
        assert loaded is not None
        assert loaded.summary_blocks.current_goal == "Original goal"
        
        # Clean up temp
        if temp_file.exists():
            temp_file.unlink()
    
    def test_save_creates_backup_on_update(self, storage, temp_storage_dir):
        """Test that saving creates backup of previous revision."""
        session_id = "test_session"
        
        # Initial summary
        summary1 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="Original goal")
        )
        
        storage.save_session_summary(session_id, summary1, create_backup=True)
        
        # Update summary
        summary2 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(current_goal="Updated goal")
        )
        
        storage.save_session_summary(session_id, summary2, create_backup=True)
        
        # Verify backup exists
        backup_file = Path(temp_storage_dir) / f"{session_id}_summary.rev0.json"
        assert backup_file.exists()
        
        # Verify backup contains original
        backup_summary = storage.load_session_summary(session_id, revision=0)
        assert backup_summary is not None
        assert backup_summary.summary_blocks.current_goal == "Original goal"
        
        # Verify current is updated
        current_summary = storage.load_session_summary(session_id)
        assert current_summary is not None
        assert current_summary.summary_blocks.current_goal == "Updated goal"
    
    def test_save_no_backup_on_first_save(self, storage, temp_storage_dir):
        """Test that first save doesn't create backup."""
        session_id = "test_session"
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="First goal")
        )
        
        storage.save_session_summary(session_id, summary, create_backup=True)
        
        # No backup files should exist
        backup_files = list(Path(temp_storage_dir).glob(f"{session_id}_summary.rev*.json"))
        assert len(backup_files) == 0
    
    def test_backup_creation_failure_doesnt_prevent_save(self, storage, temp_storage_dir):
        """Test that backup creation failure doesn't prevent saving."""
        session_id = "test_session"
        
        # Initial summary
        summary1 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="Original")
        )
        
        storage.save_session_summary(session_id, summary1)
        
        # Update with backup failure simulation
        summary2 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(current_goal="Updated")
        )
        
        # Simulate backup failure
        with patch('shutil.copy2', side_effect=IOError("Backup failed")):
            # Should still save successfully
            storage.save_session_summary(session_id, summary2, create_backup=True)
        
        # Verify save succeeded
        loaded = storage.load_session_summary(session_id)
        assert loaded is not None
        assert loaded.summary_blocks.current_goal == "Updated"
    
    def test_load_nonexistent_summary_returns_none(self, storage):
        """Test that loading nonexistent summary returns None."""
        result = storage.load_session_summary("nonexistent_session")
        assert result is None
    
    def test_load_nonexistent_revision_returns_none(self, storage, temp_storage_dir):
        """Test that loading nonexistent revision returns None."""
        session_id = "test_session"
        
        summary = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="Test")
        )
        
        storage.save_session_summary(session_id, summary)
        
        # Try to load nonexistent revision
        result = storage.load_session_summary(session_id, revision=999)
        assert result is None
    
    def test_load_invalid_json_returns_none(self, storage, temp_storage_dir):
        """Test that loading invalid JSON returns None."""
        session_id = "test_session"
        summary_file = Path(temp_storage_dir) / f"{session_id}_summary.json"
        
        # Write invalid JSON
        with open(summary_file, 'w') as f:
            f.write("invalid json{")
        
        result = storage.load_session_summary(session_id)
        assert result is None
    
    def test_save_tasks_atomic(self, storage, temp_storage_dir):
        """Test that saving tasks uses atomic write."""
        from broca.summarization.models import TasksFile, Task
        
        session_id = "test_session"
        tasks = TasksFile(
            tasks=[
                Task(
                    id="task_1",
                    description="Test task",
                    status="pending",
                    created_at="2024-01-01T00:00:00Z"
                )
            ]
        )
        
        storage.save_tasks(session_id, tasks)
        
        # Verify file exists and is valid
        tasks_file = Path(temp_storage_dir) / f"{session_id}_tasks.json"
        assert tasks_file.exists()
        
        loaded = storage.load_tasks(session_id)
        assert len(loaded.tasks) == 1
        assert loaded.tasks[0].id == "task_1"
    
    def test_load_tasks_nonexistent_returns_empty(self, storage):
        """Test that loading nonexistent tasks returns empty TasksFile."""
        result = storage.load_tasks("nonexistent_session")
        assert isinstance(result, TasksFile)
        assert len(result.tasks) == 0
    
    def test_list_session_summaries(self, storage, temp_storage_dir):
        """Test listing all session summaries."""
        # Create multiple summaries
        for i in range(3):
            session_id = f"session_{i}"
            summary = SessionSummary(
                header=SummaryHeader(
                    session_id=session_id,
                    created_at="2024-01-01T00:00:00Z",
                    last_updated_at="2024-01-01T00:00:00Z",
                    revision=0
                ),
                summary_blocks=SummaryBlocks(current_goal=f"Goal {i}")
            )
            storage.save_session_summary(session_id, summary)
        
        # List summaries
        session_ids = storage.list_session_summaries()
        
        assert len(session_ids) == 3
        assert "session_0" in session_ids
        assert "session_1" in session_ids
        assert "session_2" in session_ids
        
        # Should be sorted
        assert session_ids == sorted(session_ids)
    
    def test_list_session_summaries_ignores_backups(self, storage, temp_storage_dir):
        """Test that listing summaries ignores backup files."""
        session_id = "test_session"
        
        summary1 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T00:00:00Z",
                revision=0
            ),
            summary_blocks=SummaryBlocks(current_goal="Original")
        )
        
        storage.save_session_summary(session_id, summary1)
        
        summary2 = SessionSummary(
            header=SummaryHeader(
                session_id=session_id,
                created_at="2024-01-01T00:00:00Z",
                last_updated_at="2024-01-01T01:00:00Z",
                revision=1
            ),
            summary_blocks=SummaryBlocks(current_goal="Updated")
        )
        
        storage.save_session_summary(session_id, summary2, create_backup=True)
        
        # List should only show one session (not duplicates from backups)
        session_ids = storage.list_session_summaries()
        assert len(session_ids) == 1
        assert session_id in session_ids

