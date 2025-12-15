"""
Tests for GoalManager.

Tests goal loading, saving, active goal selection, and goal updates.
"""

from __future__ import annotations

import pytest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

from broca.optimization.goal_manager import GoalManager


class TestGoalManagerInitialization:
    """Test GoalManager initialization."""
    
    def test_init_with_file_path(self):
        """
        Test initialization with file path.
        
        Rationale: Ensures GoalManager can be initialized with a custom file path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            assert manager.goals_file_path == goals_file
    
    def test_init_with_default_path(self):
        """
        Test initialization with default path.
        
        Rationale: Ensures GoalManager uses default path when none provided.
        """
        manager = GoalManager()
        
        assert manager.goals_file_path is not None
        assert isinstance(manager.goals_file_path, str)


class TestGoalManagerLoadSave:
    """Test goal loading and saving."""
    
    def test_load_goals_empty_file(self):
        """
        Test loading goals from empty file.
        
        Rationale: Ensures empty file returns empty list.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            Path(goals_file).touch()
            
            manager = GoalManager(goals_file_path=goals_file)
            goals = manager.load_goals()
            
            assert goals == []
    
    def test_load_goals_nonexistent_file(self):
        """
        Test loading goals from nonexistent file.
        
        Rationale: Ensures nonexistent file returns empty list.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "nonexistent.json")
            
            manager = GoalManager(goals_file_path=goals_file)
            goals = manager.load_goals()
            
            assert goals == []
    
    def test_load_goals_valid_file(self):
        """
        Test loading goals from valid JSON file.
        
        Rationale: Ensures valid goals are loaded correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            test_goals = [
                {
                    "goal": "Learn more about X",
                    "active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
            
            with open(goals_file, "w") as f:
                json.dump(test_goals, f)
            
            manager = GoalManager(goals_file_path=goals_file)
            goals = manager.load_goals()
            
            assert len(goals) == 1
            assert goals[0]["goal"] == "Learn more about X"
            assert goals[0]["active"] is True
    
    def test_save_goals(self):
        """
        Test saving goals to file.
        
        Rationale: Ensures goals are saved correctly to JSON file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            test_goals = [
                {
                    "goal": "Learn more about X",
                    "active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
            
            manager.save_goals(test_goals)
            
            assert os.path.exists(goals_file)
            with open(goals_file, "r") as f:
                loaded = json.load(f)
                assert len(loaded) == 1
                assert loaded[0]["goal"] == "Learn more about X"
    
    def test_save_creates_directory(self):
        """
        Test that save creates parent directory if needed.
        
        Rationale: Ensures save works even if parent directory doesn't exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "subdir", "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            test_goals = [{"goal": "Test", "active": True}]
            manager.save_goals(test_goals)
            
            assert os.path.exists(goals_file)


class TestGoalManagerActiveGoal:
    """Test active goal selection."""
    
    def test_get_active_goal_single_active(self):
        """
        Test getting active goal when one exists.
        
        Rationale: Ensures active goal is correctly identified.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            test_goals = [
                {
                    "goal": "Goal 1",
                    "active": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "goal": "Goal 2",
                    "active": True,
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z"
                }
            ]
            manager.save_goals(test_goals)
            
            active = manager.get_active_goal()
            
            assert active is not None
            assert active["goal"] == "Goal 2"
            assert active["active"] is True
    
    def test_get_active_goal_no_active(self):
        """
        Test getting active goal when none exists.
        
        Rationale: Ensures None is returned when no active goal.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            test_goals = [
                {
                    "goal": "Goal 1",
                    "active": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
            manager.save_goals(test_goals)
            
            active = manager.get_active_goal()
            
            assert active is None
    
    def test_get_active_goal_empty_list(self):
        """
        Test getting active goal from empty list.
        
        Rationale: Ensures None is returned when no goals exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            active = manager.get_active_goal()
            
            assert active is None


class TestGoalManagerUpdate:
    """Test goal updates."""
    
    def test_update_goal(self):
        """
        Test updating a goal.
        
        Rationale: Ensures goals can be updated correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            test_goals = [
                {
                    "goal": "Goal 1",
                    "active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
            manager.save_goals(test_goals)
            
            updated_goal = {
                "goal": "Goal 1 Updated",
                "active": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z"
            }
            
            manager.update_goal(0, updated_goal)
            
            goals = manager.load_goals()
            assert len(goals) == 1
            assert goals[0]["goal"] == "Goal 1 Updated"
            assert goals[0]["active"] is False
    
    def test_add_goal(self):
        """
        Test adding a new goal.
        
        Rationale: Ensures new goals can be added.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            new_goal = {
                "goal": "New Goal",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            manager.add_goal(new_goal)
            
            goals = manager.load_goals()
            assert len(goals) == 1
            assert goals[0]["goal"] == "New Goal"


class TestGoalManagerConstraints:
    """Test constraints field in goals."""
    
    def test_load_goals_with_constraints(self):
        """
        Test loading goals with constraints field.
        
        Rationale: Ensures goals with constraints are loaded correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            test_goals = [
                {
                    "goal": "Learn more about X",
                    "active": True,
                    "constraints": ["No terminal access", "Use only memory tools"],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
            
            with open(goals_file, "w") as f:
                json.dump(test_goals, f)
            
            manager = GoalManager(goals_file_path=goals_file)
            goals = manager.load_goals()
            
            assert len(goals) == 1
            assert goals[0]["goal"] == "Learn more about X"
            assert "constraints" in goals[0]
            assert goals[0]["constraints"] == ["No terminal access", "Use only memory tools"]
    
    def test_load_goals_without_constraints(self):
        """
        Test loading goals without constraints field (backward compatibility).
        
        Rationale: Ensures goals without constraints still work.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            test_goals = [
                {
                    "goal": "Learn more about X",
                    "active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
            
            with open(goals_file, "w") as f:
                json.dump(test_goals, f)
            
            manager = GoalManager(goals_file_path=goals_file)
            goals = manager.load_goals()
            
            assert len(goals) == 1
            assert goals[0]["goal"] == "Learn more about X"
            # Should not raise KeyError when constraints is missing
            assert goals[0].get("constraints") is None or goals[0].get("constraints") == []
    
    def test_save_goals_with_constraints(self):
        """
        Test saving goals with constraints field.
        
        Rationale: Ensures constraints are saved correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            test_goals = [
                {
                    "goal": "Learn more about X",
                    "active": True,
                    "constraints": ["Constraint 1", "Constraint 2"],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
            
            manager.save_goals(test_goals)
            
            assert os.path.exists(goals_file)
            with open(goals_file, "r") as f:
                loaded = json.load(f)
                assert len(loaded) == 1
                assert loaded[0]["goal"] == "Learn more about X"
                assert "constraints" in loaded[0]
                assert loaded[0]["constraints"] == ["Constraint 1", "Constraint 2"]
    
    def test_get_active_goal_with_constraints(self):
        """
        Test getting active goal with constraints.
        
        Rationale: Ensures active goal retrieval includes constraints.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_file = os.path.join(tmpdir, "goals.json")
            manager = GoalManager(goals_file_path=goals_file)
            
            test_goals = [
                {
                    "goal": "Goal 1",
                    "active": False,
                    "constraints": ["Constraint A"],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "goal": "Goal 2",
                    "active": True,
                    "constraints": ["Constraint B", "Constraint C"],
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z"
                }
            ]
            manager.save_goals(test_goals)
            
            active = manager.get_active_goal()
            
            assert active is not None
            assert active["goal"] == "Goal 2"
            assert "constraints" in active
            assert active["constraints"] == ["Constraint B", "Constraint C"]

