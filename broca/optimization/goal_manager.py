"""
Goal management for optimization goals.

Provides functionality to load, save, and manage optimization goals from JSON file.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class GoalManager:
    """
    Manages optimization goals stored in JSON file.
    
    Provides methods to load, save, find active goals, and update goals.
    """
    
    def __init__(self, goals_file_path: Optional[str] = None) -> None:
        """
        Initialize GoalManager.
        
        Args:
            goals_file_path: Path to goals JSON file. If None, uses default from config.
        """
        if goals_file_path is None:
            from ..config import config
            goals_file_path = config.optimization.goals_file_path
        
        self.goals_file_path = goals_file_path
        logger.debug(f"Initialized GoalManager with file: {goals_file_path}")
    
    def load_goals(self) -> List[Dict[str, Any]]:
        """
        Load goals from JSON file.
        
        Returns:
            List of goal dictionaries. Returns empty list if file doesn't exist or is invalid.
        """
        if not os.path.exists(self.goals_file_path):
            logger.debug(f"Goals file does not exist: {self.goals_file_path}")
            return []
        
        try:
            with open(self.goals_file_path, "r") as f:
                goals = json.load(f)
                if not isinstance(goals, list):
                    logger.warning(f"Goals file does not contain a list: {self.goals_file_path}")
                    return []
                logger.debug(f"Loaded {len(goals)} goals from {self.goals_file_path}")
                return goals
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse goals file {self.goals_file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading goals from {self.goals_file_path}: {e}", exc_info=True)
            return []
    
    def save_goals(self, goals: List[Dict[str, Any]]) -> None:
        """
        Save goals to JSON file.
        
        Args:
            goals: List of goal dictionaries to save.
        """
        try:
            # Create parent directory if it doesn't exist
            parent_dir = os.path.dirname(self.goals_file_path)
            if parent_dir:
                Path(parent_dir).mkdir(parents=True, exist_ok=True)
            
            with open(self.goals_file_path, "w") as f:
                json.dump(goals, f, indent=2)
            
            logger.debug(f"Saved {len(goals)} goals to {self.goals_file_path}")
        except Exception as e:
            logger.error(f"Error saving goals to {self.goals_file_path}: {e}", exc_info=True)
            raise
    
    def get_active_goal(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active goal.
        
        Returns:
            Active goal dictionary if found, None otherwise.
        """
        goals = self.load_goals()
        
        for goal in goals:
            if goal.get("active", False):
                logger.debug(f"Found active goal: {goal.get('goal', 'Unknown')}")
                return goal
        
        logger.debug("No active goal found")
        return None
    
    def update_goal(self, index: int, updated_goal: Dict[str, Any]) -> None:
        """
        Update a goal at the specified index.
        
        Args:
            index: Index of goal to update
            updated_goal: Updated goal dictionary
        """
        goals = self.load_goals()
        
        if index < 0 or index >= len(goals):
            raise IndexError(f"Goal index {index} out of range")
        
        goals[index] = updated_goal
        self.save_goals(goals)
        logger.debug(f"Updated goal at index {index}")
    
    def add_goal(self, goal: Dict[str, Any]) -> None:
        """
        Add a new goal to the list.
        
        Args:
            goal: Goal dictionary to add
        """
        goals = self.load_goals()
        goals.append(goal)
        self.save_goals(goals)
        logger.debug(f"Added new goal: {goal.get('goal', 'Unknown')}")

