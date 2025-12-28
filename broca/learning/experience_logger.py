"""
Experience logging for reinforcement learning.

Records successful/failed tool executions and experiences
for learning and improvement.
"""

from __future__ import annotations

import logging
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Experience:
    """
    An experience for reinforcement learning.
    
    Represents an action, its outcome, and the resulting state,
    used for learning what works and what doesn't.
    """
    
    experience_type: str
    data: Dict[str, Any]
    outcome: str  # "success", "failure", "partial"
    reward: float = 0.0  # Reinforcement learning reward
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_type": self.experience_type,
            "data": self.data,
            "outcome": self.outcome,
            "reward": self.reward,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Experience:
        return cls(
            experience_type=data["experience_type"],
            data=data["data"],
            outcome=data["outcome"],
            reward=data.get("reward", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc),
        )


class ExperienceLogger:
    """
    Logs experiences for reinforcement learning.
    
    Records successful and failed tool executions, maintains
    experience history, and provides data for learning algorithms.
    """
    
    def __init__(self, max_experiences: int = 1000, storage_path: Optional[str] = None, auto_save: bool = True):
        """
        Initialize ExperienceLogger.
        
        Args:
            max_experiences: Maximum number of experiences to maintain in memory
            storage_path: Path to JSON file for persistence. If None, uses default from data/experiences.json
            auto_save: If True, automatically save on each experience log
        """
        self.max_experiences = max_experiences
        self.auto_save = auto_save
        
        # Set storage path
        if storage_path is None:
            # Default to data/experiences.json
            storage_path = "data/experiences.json"
        self.storage_path = Path(storage_path)
        
        # Create parent directory if needed
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing experiences if file exists
        self.experiences: List[Experience] = []
        if self.storage_path.exists():
            try:
                self.load()
                logger.info(f"Loaded {len(self.experiences)} experiences from {self.storage_path}")
            except Exception as e:
                logger.warning(f"Failed to load experiences from {self.storage_path}: {e}, starting empty")
                self.experiences = []
        else:
            logger.info(f"Initialized ExperienceLogger with capacity {max_experiences} (new file)")
    
    def log_experience(self, experience_data: Dict[str, Any]) -> bool:
        """
        Log an experience.
        
        Args:
            experience_data: Experience data dictionary
            
        Returns:
            True if successfully logged
        """
        try:
            # Extract experience components
            exp_type = experience_data.get("type", "unknown")
            outcome = experience_data.get("outcome", "success" if experience_data.get("success", False) else "failure")
            reward = experience_data.get("reward", 1.0 if outcome == "success" else -1.0)
            
            experience = Experience(
                experience_type=exp_type,
                data=experience_data,
                outcome=outcome,
                reward=reward,
            )
            
            self.experiences.append(experience)
            
            # Limit experiences
            if len(self.experiences) > self.max_experiences:
                self.experiences = self.experiences[-self.max_experiences:]
            
            logger.debug(f"Logged experience: {exp_type} ({outcome})")
            
            # Auto-save if enabled
            if self.auto_save:
                try:
                    self.save()
                except Exception as e:
                    logger.warning(f"Failed to auto-save after logging experience: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log experience: {e}")
            return False
    
    def get_recent_experiences(self, limit: int = 100) -> List[Experience]:
        """Get most recent experiences."""
        return self.experiences[-limit:] if self.experiences else []
    
    def get_successful_experiences(self, limit: int = 100) -> List[Experience]:
        """Get successful experiences."""
        successful = [exp for exp in self.experiences if exp.outcome == "success"]
        return successful[-limit:] if successful else []
    
    def get_failed_experiences(self, limit: int = 100) -> List[Experience]:
        """Get failed experiences."""
        failed = [exp for exp in self.experiences if exp.outcome == "failure"]
        return failed[-limit:] if failed else []
    
    def get_experiences_by_type(self, exp_type: str, limit: int = 100) -> List[Experience]:
        """Get experiences by type."""
        filtered = [exp for exp in self.experiences if exp.experience_type == exp_type]
        return filtered[-limit:] if filtered else []
    
    def calculate_success_rate(self, exp_type: Optional[str] = None) -> float:
        """Calculate success rate for experiences."""
        if not self.experiences:
            return 0.0
        
        if exp_type:
            filtered = [exp for exp in self.experiences if exp.experience_type == exp_type]
            if not filtered:
                return 0.0
            successful = sum(1 for exp in filtered if exp.outcome == "success")
            return successful / len(filtered)
        else:
            successful = sum(1 for exp in self.experiences if exp.outcome == "success")
            return successful / len(self.experiences)
    
    def clear_experiences(self):
        """Clear all experiences."""
        self.experiences = []
        logger.info("Cleared all experiences")
        
        # Auto-save if enabled
        if self.auto_save:
            try:
                self.save()
            except Exception as e:
                logger.warning(f"Failed to auto-save after clearing experiences: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert logger to dictionary representation."""
        return {
            "experiences": [exp.to_dict() for exp in self.experiences[-500:]],  # Last 500
            "max_experiences": self.max_experiences,
        }
    
    def load(self) -> None:
        """
        Load experiences from storage file.
        
        Raises:
            OSError: If file cannot be read
            json.JSONDecodeError: If file is not valid JSON
        """
        if not self.storage_path.exists():
            logger.debug(f"Experiences file does not exist: {self.storage_path}")
            return
        
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Load experiences
            self.experiences = [
                Experience.from_dict(exp_data)
                for exp_data in data.get("experiences", [])
            ]
            
            # Update max_experiences if present in data
            if "max_experiences" in data:
                self.max_experiences = data["max_experiences"]
            
            # Limit to max_experiences (keep most recent)
            if len(self.experiences) > self.max_experiences:
                self.experiences = self.experiences[-self.max_experiences:]
            
            logger.debug(f"Loaded {len(self.experiences)} experiences from {self.storage_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse experiences file {self.storage_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading experiences from {self.storage_path}: {e}", exc_info=True)
            raise
    
    def save(self) -> None:
        """
        Save experiences to storage file using atomic write.
        
        Uses temp file + rename pattern for safety.
        Only saves the most recent experiences (up to max_experiences).
        
        Raises:
            OSError: If file cannot be written
        """
        try:
            # Prepare data structure (save last 500 experiences to avoid huge files)
            save_limit = min(500, self.max_experiences)
            experiences_to_save = self.experiences[-save_limit:] if len(self.experiences) > save_limit else self.experiences
            
            data = {
                "experiences": [exp.to_dict() for exp in experiences_to_save],
                "max_experiences": self.max_experiences,
                "total_experiences": len(self.experiences),
                "saved_count": len(experiences_to_save),
                "last_saved": datetime.now(timezone.utc).isoformat(),
            }
            
            # Atomic write: write to temp file, then rename
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.storage_path.parent,
                delete=False,
                suffix='.tmp',
                encoding='utf-8'
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False, default=str)
                tmp_path = tmp_file.name
            
            # Atomic rename
            os.replace(tmp_path, self.storage_path)
            
            logger.debug(f"Saved {len(experiences_to_save)} experiences to {self.storage_path}")
        except (OSError, IOError, json.JSONEncodeError) as e:
            logger.error(f"Failed to save experiences to {self.storage_path}: {e}", exc_info=True)
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExperienceLogger:
        """Create logger from dictionary representation."""
        logger = cls(max_experiences=data.get("max_experiences", 1000), storage_path=None, auto_save=False)
        logger.experiences = [Experience.from_dict(exp_data) for exp_data in data.get("experiences", [])]
        return logger
