"""
Report management for optimization cycle reports.

Provides functionality to load, save, and manage optimization cycle reports from JSON file.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ReportManager:
    """
    Manages optimization cycle reports stored in JSON file.
    
    Provides methods to load, save, find latest reports, and add new reports.
    """
    
    def __init__(self, reports_file_path: Optional[str] = None) -> None:
        """
        Initialize ReportManager.
        
        Args:
            reports_file_path: Path to reports JSON file. If None, uses default from config.
        """
        if reports_file_path is None:
            from ..config import config
            reports_file_path = config.optimization.reports_file_path
        
        self.reports_file_path = reports_file_path
        logger.debug(f"Initialized ReportManager with file: {reports_file_path}")
    
    def load_reports(self) -> List[Dict[str, Any]]:
        """
        Load reports from JSON file.
        
        Returns:
            List of report dictionaries. Returns empty list if file doesn't exist or is invalid.
        """
        if not os.path.exists(self.reports_file_path):
            logger.debug(f"Reports file does not exist: {self.reports_file_path}")
            return []
        
        try:
            with open(self.reports_file_path, "r") as f:
                reports = json.load(f)
                if not isinstance(reports, list):
                    logger.warning(f"Reports file does not contain a list: {self.reports_file_path}")
                    return []
                logger.debug(f"Loaded {len(reports)} reports from {self.reports_file_path}")
                return reports
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse reports file {self.reports_file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading reports from {self.reports_file_path}: {e}", exc_info=True)
            return []
    
    def save_reports(self, reports: List[Dict[str, Any]]) -> None:
        """
        Save reports to JSON file.
        
        Args:
            reports: List of report dictionaries to save.
        """
        try:
            # Create parent directory if it doesn't exist
            parent_dir = os.path.dirname(self.reports_file_path)
            if parent_dir:
                Path(parent_dir).mkdir(parents=True, exist_ok=True)
            
            with open(self.reports_file_path, "w") as f:
                json.dump(reports, f, indent=2)
            
            logger.debug(f"Saved {len(reports)} reports to {self.reports_file_path}")
        except Exception as e:
            logger.error(f"Error saving reports to {self.reports_file_path}: {e}", exc_info=True)
            raise
    
    def get_latest_report(self, goal: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest report for a specific goal.
        
        Args:
            goal: Goal string to find latest report for
        
        Returns:
            Latest report dictionary for the goal if found, None otherwise.
        """
        reports = self.load_reports()
        
        # Filter reports for this goal
        goal_reports = [r for r in reports if r.get("goal") == goal]
        
        if not goal_reports:
            logger.debug(f"No reports found for goal: {goal}")
            return None
        
        # Sort by cycle_number descending to get latest
        goal_reports.sort(key=lambda x: x.get("cycle_number", 0), reverse=True)
        
        latest = goal_reports[0]
        logger.debug(f"Found latest report for goal '{goal}': cycle {latest.get('cycle_number')}")
        return latest
    
    def add_report(self, report: Dict[str, Any]) -> None:
        """
        Add a new report to the list.
        
        Args:
            report: Report dictionary to add
        """
        reports = self.load_reports()
        reports.append(report)
        self.save_reports(reports)
        logger.debug(f"Added new report for goal '{report.get('goal', 'Unknown')}': cycle {report.get('cycle_number')}")

