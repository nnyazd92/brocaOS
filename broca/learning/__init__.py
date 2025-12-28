"""
Procedural learning system for BrocaOS.

Enables learning from successful tool use patterns, creating reusable
procedures and skills that can be automatically applied in similar situations.

Components:
- ProceduralLearning: Learns action sequences from successful tool executions
- SkillManager: Manages learned skills and their application
- PatternExtractor: Extracts patterns from tool call sequences
- ExperienceLogger: Records successful/failed tool executions
- Reinforcement: Reinforcement learning for skill improvement
"""

from .procedural_learning import ProceduralLearner, LearnedProcedure
from .skill_manager import SkillManager, Skill, SkillType
from .pattern_extractor import PatternExtractor
from .experience_logger import ExperienceLogger, Experience
from .reinforcement import ReinforcementLearner

__all__ = [
    "ProceduralLearner",
    "LearnedProcedure",
    "SkillManager",
    "Skill",
    "SkillType",
    "PatternExtractor",
    "ExperienceLogger",
    "Experience",
    "ReinforcementLearner",
]
