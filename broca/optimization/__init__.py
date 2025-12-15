"""
Optimization goal management and daemon functionality.

This module provides classes for managing optimization goals and reports,
as well as the daemon that implements the autonomous optimization feedback loop.
"""

from __future__ import annotations

from .goal_manager import GoalManager
from .report_manager import ReportManager

__all__ = ["GoalManager", "ReportManager"]

