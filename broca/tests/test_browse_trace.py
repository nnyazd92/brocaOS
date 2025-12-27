"""
Tests for BrowseTrace implementation.

Tests trace artifact management.
"""

from __future__ import annotations

import os
import tempfile
import json
from unittest.mock import Mock, patch
import pytest

from broca.tools.browse_trace import BrowseTraceManager, BrowseTrace, BrowseBudget, BrowseAction


class TestBrowseTraceManager:
    """Test BrowseTraceManager."""
    
    def test_create_trace(self):
        """Test creating a new trace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BrowseTraceManager(storage_path=tmpdir)
            trace = manager.create_trace("session123", "task456")
            
            assert trace.session_id == "session123"
            assert trace.task_id == "task456"
            assert trace.started_at is not None
    
    def test_add_action(self):
        """Test adding an action to a trace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BrowseTraceManager(storage_path=tmpdir)
            trace = manager.create_trace("session123", "task456")
            
            manager.add_action(trace, "navigate", url="https://example.com")
            
            assert len(trace.actions) == 1
            assert trace.actions[0].type == "navigate"
    
    def test_save_trace(self):
        """Test saving a trace to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BrowseTraceManager(storage_path=tmpdir)
            trace = manager.create_trace("session123", "task456")
            
            filepath = manager.save_trace(trace)
            
            assert os.path.exists(filepath)
            
            # Verify content
            with open(filepath, "r") as f:
                data = json.load(f)
                assert data["session_id"] == "session123"
                assert data["task_id"] == "task456"
    
    def test_load_trace(self):
        """Test loading a trace from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BrowseTraceManager(storage_path=tmpdir)
            trace = manager.create_trace("session123", "task456")
            filepath = manager.save_trace(trace)
            
            loaded = manager.load_trace(filepath)
            
            assert loaded.session_id == trace.session_id
            assert loaded.task_id == trace.task_id

