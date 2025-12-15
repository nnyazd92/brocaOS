"""
Tests for ReportManager.

Tests report loading, saving, latest report retrieval, and report structure validation.
"""

from __future__ import annotations

import pytest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

from broca.optimization.report_manager import ReportManager


class TestReportManagerInitialization:
    """Test ReportManager initialization."""
    
    def test_init_with_file_path(self):
        """
        Test initialization with file path.
        
        Rationale: Ensures ReportManager can be initialized with a custom file path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            manager = ReportManager(reports_file_path=reports_file)
            
            assert manager.reports_file_path == reports_file
    
    def test_init_with_default_path(self):
        """
        Test initialization with default path.
        
        Rationale: Ensures ReportManager uses default path when none provided.
        """
        manager = ReportManager()
        
        assert manager.reports_file_path is not None
        assert isinstance(manager.reports_file_path, str)


class TestReportManagerLoadSave:
    """Test report loading and saving."""
    
    def test_load_reports_empty_file(self):
        """
        Test loading reports from empty file.
        
        Rationale: Ensures empty file returns empty list.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            Path(reports_file).touch()
            
            manager = ReportManager(reports_file_path=reports_file)
            reports = manager.load_reports()
            
            assert reports == []
    
    def test_load_reports_nonexistent_file(self):
        """
        Test loading reports from nonexistent file.
        
        Rationale: Ensures nonexistent file returns empty list.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "nonexistent.json")
            
            manager = ReportManager(reports_file_path=reports_file)
            reports = manager.load_reports()
            
            assert reports == []
    
    def test_load_reports_valid_file(self):
        """
        Test loading reports from valid JSON file.
        
        Rationale: Ensures valid reports are loaded correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            test_reports = [
                {
                    "goal": "Learn more about X",
                    "cycle_number": 1,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "actions_taken": ["tool1", "tool2"],
                    "findings": "Summary of what was discovered",
                    "next_steps": "What should be done next"
                }
            ]
            
            with open(reports_file, "w") as f:
                json.dump(test_reports, f)
            
            manager = ReportManager(reports_file_path=reports_file)
            reports = manager.load_reports()
            
            assert len(reports) == 1
            assert reports[0]["goal"] == "Learn more about X"
            assert reports[0]["cycle_number"] == 1
            assert reports[0]["actions_taken"] == ["tool1", "tool2"]
    
    def test_save_reports(self):
        """
        Test saving reports to file.
        
        Rationale: Ensures reports are saved correctly to JSON file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            manager = ReportManager(reports_file_path=reports_file)
            
            test_reports = [
                {
                    "goal": "Learn more about X",
                    "cycle_number": 1,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "actions_taken": ["tool1"],
                    "findings": "Test findings",
                    "next_steps": "Test next steps"
                }
            ]
            
            manager.save_reports(test_reports)
            
            assert os.path.exists(reports_file)
            with open(reports_file, "r") as f:
                loaded = json.load(f)
                assert len(loaded) == 1
                assert loaded[0]["goal"] == "Learn more about X"
                assert loaded[0]["cycle_number"] == 1
    
    def test_save_creates_directory(self):
        """
        Test that save creates parent directory if needed.
        
        Rationale: Ensures save works even if parent directory doesn't exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "subdir", "reports.json")
            manager = ReportManager(reports_file_path=reports_file)
            
            test_reports = [{"goal": "Test", "cycle_number": 1}]
            manager.save_reports(test_reports)
            
            assert os.path.exists(reports_file)


class TestReportManagerGetLatest:
    """Test latest report retrieval."""
    
    def test_get_latest_report_single_goal(self):
        """
        Test getting latest report for a specific goal.
        
        Rationale: Ensures latest report for a goal is correctly identified.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            manager = ReportManager(reports_file_path=reports_file)
            
            test_reports = [
                {
                    "goal": "Goal 1",
                    "cycle_number": 1,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "actions_taken": [],
                    "findings": "First cycle",
                    "next_steps": ""
                },
                {
                    "goal": "Goal 1",
                    "cycle_number": 2,
                    "timestamp": "2024-01-02T00:00:00Z",
                    "actions_taken": [],
                    "findings": "Second cycle",
                    "next_steps": ""
                },
                {
                    "goal": "Goal 2",
                    "cycle_number": 1,
                    "timestamp": "2024-01-03T00:00:00Z",
                    "actions_taken": [],
                    "findings": "Other goal",
                    "next_steps": ""
                }
            ]
            manager.save_reports(test_reports)
            
            latest = manager.get_latest_report("Goal 1")
            
            assert latest is not None
            assert latest["goal"] == "Goal 1"
            assert latest["cycle_number"] == 2
            assert latest["findings"] == "Second cycle"
    
    def test_get_latest_report_no_reports(self):
        """
        Test getting latest report when no reports exist.
        
        Rationale: Ensures None is returned when no reports exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            manager = ReportManager(reports_file_path=reports_file)
            
            latest = manager.get_latest_report("Goal 1")
            
            assert latest is None
    
    def test_get_latest_report_goal_not_found(self):
        """
        Test getting latest report for goal that doesn't exist.
        
        Rationale: Ensures None is returned when goal has no reports.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            manager = ReportManager(reports_file_path=reports_file)
            
            test_reports = [
                {
                    "goal": "Goal 1",
                    "cycle_number": 1,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "actions_taken": [],
                    "findings": "Test",
                    "next_steps": ""
                }
            ]
            manager.save_reports(test_reports)
            
            latest = manager.get_latest_report("Goal 2")
            
            assert latest is None


class TestReportManagerAddReport:
    """Test adding reports."""
    
    def test_add_report(self):
        """
        Test adding a new report.
        
        Rationale: Ensures new reports can be added correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            manager = ReportManager(reports_file_path=reports_file)
            
            new_report = {
                "goal": "New Goal",
                "cycle_number": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actions_taken": ["tool1"],
                "findings": "Test findings",
                "next_steps": "Test next steps"
            }
            
            manager.add_report(new_report)
            
            reports = manager.load_reports()
            assert len(reports) == 1
            assert reports[0]["goal"] == "New Goal"
            assert reports[0]["cycle_number"] == 1
    
    def test_add_report_increments_cycle(self):
        """
        Test that adding multiple reports for same goal increments cycle number.
        
        Rationale: Ensures cycle numbers are correctly incremented.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_file = os.path.join(tmpdir, "reports.json")
            manager = ReportManager(reports_file_path=reports_file)
            
            report1 = {
                "goal": "Goal 1",
                "cycle_number": 1,
                "timestamp": "2024-01-01T00:00:00Z",
                "actions_taken": [],
                "findings": "",
                "next_steps": ""
            }
            manager.add_report(report1)
            
            report2 = {
                "goal": "Goal 1",
                "cycle_number": 2,
                "timestamp": "2024-01-02T00:00:00Z",
                "actions_taken": [],
                "findings": "",
                "next_steps": ""
            }
            manager.add_report(report2)
            
            reports = manager.load_reports()
            assert len(reports) == 2
            assert reports[0]["cycle_number"] == 1
            assert reports[1]["cycle_number"] == 2

