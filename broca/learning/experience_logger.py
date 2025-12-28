"""
Experience logging for reinforcement learning.

Records successful/failed tool executions and experiences
for learning and improvement.
"""

from __future__ import annotations

import logging
import json
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
    
    def __init__(self, max_experiences: int = 1000):
        self.experiences: List[Experience] = []
        self.max_experiences = max_experiences
        
        logger.info(f"Initialized ExperienceLogger with capacity {max_experiences}")
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert logger to dictionary representation."""
        return {
            "experiences": [exp.to_dict() for exp in self.experiences[-500:]],  # Last 500
            "max_experiences": self.max_experiences,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExperienceLogger:
        """Create logger from dictionary representation."""
        logger = cls(max_experiences=data.get("max_experiences", 1000))
        logger.experiences = [Experience.from_dict(exp_data) for exp_data in data.get("experiences", [])]
        return logger
