"""
Skill management for learned procedures.

Manages learned skills with success rates, confidence scores,
and automatic application in appropriate contexts.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SkillType(Enum):
    """Types of skills."""
    PROCEDURAL = "procedural"      # Tool sequence skills
    ANALYTICAL = "analytical"      # Analysis/pattern recognition
    CREATIVE = "creative"          # Creative/generation tasks
    TECHNICAL = "technical"        # Technical/system tasks
    SOCIAL = "social"             # Communication/interaction


@dataclass
class Skill:
    """
    A learned skill that can be applied automatically.
    
    Represents expertise in a specific domain with associated
    success metrics, confidence, and application patterns.
    """
    
    name: str
    skill_type: SkillType
    description: str
    
    # Proficiency metrics
    proficiency_level: float = 0.0  # 0.0 to 1.0
    confidence: float = 0.5         # 0.0 to 1.0
    experience_points: int = 0
    
    # Success tracking
    success_count: int = 0
    failure_count: int = 0
    total_applications: int = 0
    
    # Application patterns
    trigger_patterns: List[Dict[str, Any]] = field(default_factory=list)
    required_context: List[Dict[str, Any]] = field(default_factory=list)
    excluded_context: List[Dict[str, Any]] = field(default_factory=list)
    
    # Learning parameters
    learning_rate: float = 0.1
    decay_rate: float = 0.01
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    last_improved: Optional[datetime] = None
    
    # Cognitive dissonance integration
    dissonance_impact_history: List[Dict[str, Any]] = field(default_factory=list)  # History of dissonance changes when skill applied
    average_dissonance_impact: float = 0.0  # Average change in dissonance (positive = reduction, negative = increase)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "skill_type": self.skill_type.value,
            "description": self.description,
            "proficiency_level": self.proficiency_level,
            "confidence": self.confidence,
            "experience_points": self.experience_points,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_applications": self.total_applications,
            "trigger_patterns": self.trigger_patterns,
            "required_context": self.required_context,
            "excluded_context": self.excluded_context,
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "last_improved": self.last_improved.isoformat() if self.last_improved else None,
            "average_dissonance_impact": self.average_dissonance_impact,
            "dissonance_impact_count": len(self.dissonance_impact_history),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Skill:
        return cls(
            name=data["name"],
            skill_type=SkillType(data["skill_type"]),
            description=data["description"],
            proficiency_level=data.get("proficiency_level", 0.0),
            confidence=data.get("confidence", 0.5),
            experience_points=data.get("experience_points", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            total_applications=data.get("total_applications", 0),
            trigger_patterns=data.get("trigger_patterns", []),
            required_context=data.get("required_context", []),
            excluded_context=data.get("excluded_context", []),
            learning_rate=data.get("learning_rate", 0.1),
            decay_rate=data.get("decay_rate", 0.01),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            last_improved=datetime.fromisoformat(data["last_improved"]) if data.get("last_improved") else None,
            dissonance_impact_history=data.get("dissonance_impact_history", []),
            average_dissonance_impact=data.get("average_dissonance_impact", 0.0),
        )
    
    def success_rate(self) -> float:
        """Calculate success rate of this skill."""
        if self.total_applications == 0:
            return 0.0
        return self.success_count / self.total_applications
    
    def record_success(self, improvement: float = 0.01):
        """Record a successful skill application."""
        self.success_count += 1
        self.total_applications += 1
        self.experience_points += 10
        self.last_used = datetime.now(timezone.utc)
        
        # Increase proficiency and confidence
        old_proficiency = self.proficiency_level
        self.proficiency_level = min(1.0, self.proficiency_level + improvement)
        self.confidence = min(1.0, self.confidence + self.learning_rate * 0.05)
        
        if self.proficiency_level > old_proficiency:
            self.last_improved = self.last_used
    
    def record_failure(self):
        """Record a failed skill application."""
        self.failure_count += 1
        self.total_applications += 1
        self.experience_points += 1  # Still learn from failures
        self.last_used = datetime.now(timezone.utc)
        
        # Decrease confidence but maintain some proficiency
        self.confidence = max(0.1, self.confidence - self.learning_rate * 0.1)
    
    def apply_decay(self, days_passed: float = 1.0):
        """Apply skill decay over time."""
        # Skills decay when not used
        decay_amount = self.decay_rate * days_passed
        self.proficiency_level = max(0.1, self.proficiency_level - decay_amount)
        self.confidence = max(0.1, self.confidence - decay_amount * 0.5)
    
    def update_from_dissonance(self, dissonance_before: float, dissonance_after: float):
        """
        Update skill based on dissonance impact.
        
        Args:
            dissonance_before: Dissonance level before skill application
            dissonance_after: Dissonance level after skill application
        """
        dissonance_change = dissonance_before - dissonance_after  # Positive = reduction (good)
        
        # Record in history
        self.dissonance_impact_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dissonance_before": dissonance_before,
            "dissonance_after": dissonance_after,
            "dissonance_change": dissonance_change
        })
        
        # Keep history limited
        if len(self.dissonance_impact_history) > 100:
            self.dissonance_impact_history = self.dissonance_impact_history[-100:]
        
        # Update average impact (exponential moving average)
        if len(self.dissonance_impact_history) == 1:
            self.average_dissonance_impact = dissonance_change
        else:
            self.average_dissonance_impact = (
                self.learning_rate * dissonance_change +
                (1.0 - self.learning_rate) * self.average_dissonance_impact
            )
        
        # Adjust proficiency based on dissonance impact
        if dissonance_change > 0.0:  # Reduced dissonance
            improvement = min(0.05, dissonance_change * 0.1)  # Small improvement
            self.proficiency_level = min(1.0, self.proficiency_level + improvement)
            self.confidence = min(1.0, self.confidence + improvement * 0.5)
            if self.proficiency_level > 0.0:  # Only update if improved
                self.last_improved = datetime.now(timezone.utc)
        elif dissonance_change < -0.1:  # Increased dissonance significantly
            penalty = min(0.1, abs(dissonance_change) * 0.2)
            self.proficiency_level = max(0.1, self.proficiency_level - penalty)
            self.confidence = max(0.1, self.confidence - penalty * 0.5)


class SkillManager:
    """
    Manages learned skills and their application.
    
    Tracks skill proficiency, suggests skills for given contexts,
    and handles skill improvement through experience.
    """
    
    def __init__(self, max_skills: int = 50):
        self.skills: Dict[str, Skill] = {}
        self.max_skills = max_skills
        
        # Default skills
        self._add_default_skills()
        
        logger.info(f"Initialized SkillManager with {len(self.skills)} default skills")
    
    def _add_default_skills(self):
        """Add default skills based on system capabilities."""
        # Code analysis skill
        code_analysis_skill = Skill(
            name="code_analysis",
            skill_type=SkillType.TECHNICAL,
            description="Analyze codebase structure and files",
            proficiency_level=0.7,
            confidence=0.8,
            trigger_patterns=[
                {"type": "goal", "name": "analyze_codebase"},
                {"type": "task", "domain": "code_analysis"},
            ],
        )
        self.skills[code_analysis_skill.name] = code_analysis_skill
        
        # Information retrieval skill
        info_retrieval_skill = Skill(
            name="information_retrieval",
            skill_type=SkillType.ANALYTICAL,
            description="Retrieve and synthesize information from memories",
            proficiency_level=0.8,
            confidence=0.9,
            trigger_patterns=[
                {"type": "task", "needs_information": True},
                {"type": "goal", "goal_type": "learn"},
            ],
        )
        self.skills[info_retrieval_skill.name] = info_retrieval_skill
        
        # Problem solving skill
        problem_solving_skill = Skill(
            name="problem_solving",
            skill_type=SkillType.ANALYTICAL,
            description="Solve complex problems through decomposition and analysis",
            proficiency_level=0.6,
            confidence=0.7,
            trigger_patterns=[
                {"type": "task", "complexity": "high"},
                {"type": "goal", "goal_type": "achieve", "difficulty": "high"},
            ],
        )
        self.skills[problem_solving_skill.name] = problem_solving_skill
    
    def add_skill(self, skill: Skill) -> bool:
        """Add a skill to the manager."""
        if skill.name in self.skills:
            logger.warning(f"Skill '{skill.name}' already exists")
            return False
        
        # Enforce max skills limit
        if len(self.skills) >= self.max_skills:
            # Remove lowest proficiency skill
            lowest_skill = min(self.skills.values(), key=lambda s: s.proficiency_level)
            del self.skills[lowest_skill.name]
            logger.info(f"Removed low-proficiency skill '{lowest_skill.name}' to make room")
        
        self.skills[skill.name] = skill
        logger.info(f"Added skill: {skill.name}")
        return True
    
    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(skill_name)
    
    def get_applicable_skills(self, context: Dict[str, Any]) -> List[Skill]:
        """
        Get skills applicable to current context.
        
        Args:
            context: Current context with memory items, goals, state
            
        Returns:
            List of applicable skills sorted by proficiency and confidence
        """
        applicable = []
        
        for skill in self.skills.values():
            if self._skill_applicable(skill, context):
                applicable.append(skill)
        
        # Sort by combined score: proficiency, confidence, and dissonance impact
        # Skills that reduce dissonance get priority boost
        applicable.sort(
            key=lambda s: (
                s.proficiency_level,
                s.confidence,
                max(0.0, s.average_dissonance_impact)  # Boost for positive dissonance reduction
            ),
            reverse=True
        )
        
        return applicable
    
    def _skill_applicable(self, skill: Skill, context: Dict[str, Any]) -> bool:
        """Check if skill is applicable to current context."""
        # Extract context components
        memory_items = context.get("memory_items", [])
        active_goals = context.get("active_goals", [])
        system_state = context.get("system_state", {})
        
        # Check if context matches any trigger pattern
        has_trigger = False
        for pattern in skill.trigger_patterns:
            # Check memory items
            if self._pattern_matches_any(pattern, memory_items):
                has_trigger = True
                break
            # Check active goals
            if self._pattern_matches_any(pattern, active_goals):
                has_trigger = True
                break
            # Check system state
            if self._pattern_matches(pattern, system_state):
                has_trigger = True
                break
        
        if not has_trigger:
            return False
        
        # Check required context
        for pattern in skill.required_context:
            found = False
            # Check all context components
            for items in [memory_items, active_goals]:
                if self._pattern_matches_any(pattern, items):
                    found = True
                    break
            if self._pattern_matches(pattern, system_state):
                found = True
            
            if not found:
                return False
        
        # Check excluded context
        for pattern in skill.excluded_context:
            # If excluded pattern matches, skill is not applicable
            for items in [memory_items, active_goals]:
                if self._pattern_matches_any(pattern, items):
                    return False
            if self._pattern_matches(pattern, system_state):
                return False
        
        return True
    
    def _pattern_matches(self, pattern: Dict[str, Any], item: Dict[str, Any]) -> bool:
        """Check if pattern matches item."""
        for key, value in pattern.items():
            if key not in item:
                return False
            if isinstance(value, dict) and isinstance(item[key], dict):
                if not self._pattern_matches(value, item[key]):
                    return False
            elif value != item[key]:
                return False
        return True
    
    def _pattern_matches_any(self, pattern: Dict[str, Any], items: List[Dict[str, Any]]) -> bool:
        """Check if pattern matches any item in list."""
        for item in items:
            if self._pattern_matches(pattern, item):
                return True
        return False
    
    def suggest_skill_actions(self, skill: Skill, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest actions based on skill and context.
        
        Returns:
            List of suggested tool calls or procedures
        """
        suggestions = []
        
        # Based on skill type, suggest appropriate actions
        if skill.skill_type == SkillType.TECHNICAL:
            suggestions.append({
                "type": "tool_call",
                "tool_name": "terminal",
                "parameters": {"command": "Analyze relevant code or system"},
                "reason": f"Apply {skill.name} skill for technical analysis"
            })
        elif skill.skill_type == SkillType.ANALYTICAL:
            suggestions.append({
                "type": "tool_call",
                "tool_name": "retrieve_memories",
                "parameters": {"query": "Relevant information for analysis", "limit": 10},
                "reason": f"Apply {skill.name} skill for information analysis"
            })
        elif skill.skill_type == SkillType.PROCEDURAL:
            suggestions.append({
                "type": "procedure",
                "procedure_name": f"apply_{skill.name}_procedure",
                "reason": f"Apply learned procedure for {skill.name}"
            })
        
        return suggestions
    
    def update_skill_from_experience(self, skill_name: str, success: bool, 
                                   improvement: float = 0.01):
        """Update skill based on experience outcome."""
        if skill_name not in self.skills:
            logger.warning(f"Skill '{skill_name}' not found for experience update")
            return
        
        skill = self.skills[skill_name]
        
        if success:
            skill.record_success(improvement)
            logger.info(f"Skill '{skill_name}' improved to proficiency {skill.proficiency_level:.2f}")
        else:
            skill.record_failure()
            logger.info(f"Skill '{skill_name}' recorded failure")
    
    def retire_high_dissonance_skills(self, max_dissonance_threshold: float = -0.2, min_applications: int = 5):
        """
        Retire skills that consistently increase dissonance.
        
        Args:
            max_dissonance_threshold: Maximum average dissonance impact (negative = increases dissonance)
            min_applications: Minimum number of applications before considering retirement
            
        Returns:
            List of retired skill names
        """
        retired = []
        
        for skill_name, skill in list(self.skills.items()):
            # Skip if not enough data
            if len(skill.dissonance_impact_history) < min_applications:
                continue
            
            # Check if skill consistently increases dissonance
            if skill.average_dissonance_impact < max_dissonance_threshold:
                retired.append(skill_name)
                del self.skills[skill_name]
                logger.info(f"Retired high-dissonance skill '{skill_name}' (avg impact: {skill.average_dissonance_impact:.3f})")
        
        return retired
    
    def apply_time_decay(self, days_passed: float = 1.0):
        """Apply time-based decay to all skills."""
        for skill in self.skills.values():
            skill.apply_decay(days_passed)
        logger.info(f"Applied time decay to {len(self.skills)} skills")
    
    def get_top_skills(self, limit: int = 10) -> List[Skill]:
        """Get top skills by proficiency."""
        sorted_skills = sorted(self.skills.values(), 
                             key=lambda s: s.proficiency_level, 
                             reverse=True)
        return sorted_skills[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager to dictionary representation."""
        return {
            "skills": {name: skill.to_dict() for name, skill in self.skills.items()},
            "max_skills": self.max_skills,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SkillManager:
        """Create manager from dictionary representation."""
        manager = cls(max_skills=data.get("max_skills", 50))
        manager.skills = {
            name: Skill.from_dict(skill_data) 
            for name, skill_data in data.get("skills", {}).items()
        }
        return manager
