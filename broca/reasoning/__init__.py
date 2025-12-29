"""
Production rule system for BrocaOS.

Implements a production rule engine that can reason over memories,
perform logical inference, and execute condition-action rules.

Components:
- ProductionRules: Individual if-then rules
- ProductionRuleSystem: Manages and executes rules
- RuleEngine: Matches rules against working memory
- PatternMatcher: Matches conditions against memory patterns
- WorkingMemory: Active memory buffer
- GoalManager: Goal representation and management
- ReasoningTool: Integration tool for LLM interaction
"""

from .production_rules import ProductionRule, ProductionRuleSystem, RuleType
from .rule_engine import RuleEngine
from .pattern_matcher import PatternMatcher
from .working_memory import WorkingMemory
from .goal_manager import GoalManager, Goal, GoalStatus, GoalType
from .integration_tool import ReasoningTool
from .config import ReasoningConfig

# Note: DeclarativeMemoryInterface and SpreadingActivation are not exported here
# to avoid circular imports (they import MemoryManager which imports config).
# Import them directly: from .declarative_memory import DeclarativeMemoryInterface

# Note: StateManager, Daemon, and FeedbackLoopManager are not exported here
# to avoid circular imports. Import them directly when needed.

__all__ = [
    "ProductionRule",
    "ProductionRuleSystem", 
    "RuleType",
    "RuleEngine",
    "PatternMatcher",
    "WorkingMemory",
    "GoalManager",
    "Goal",
    "GoalStatus",
    "GoalType",
    "ReasoningTool",
    "ReasoningConfig",
]
