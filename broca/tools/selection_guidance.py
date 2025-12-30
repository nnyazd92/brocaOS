"""
Tool selection guidance system.

Integrates reasoning engine, reinforcement learning, and skill management
to provide intelligent tool selection guidance, filtering, and validation.
"""

from __future__ import annotations

import logging
import time
import hashlib
import math
from typing import Dict, Any, List, Optional, TYPE_CHECKING, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque, defaultdict
from enum import Enum

if TYPE_CHECKING:
    from . import Tool
    from ..reasoning.integration_tool import ReasoningTool
    from ..reasoning.rl_signals import RLSignalAggregator, RLSignalMetrics
    from ..reasoning.goal_manager import GoalManager, Goal
    from ..learning.skill_manager import SkillManager, Skill
    from .selection_metrics import ToolSelectionMetrics

logger = logging.getLogger(__name__)


class ValidationStrictness(Enum):
    """Validation strictness levels."""
    ADVISORY = "advisory"  # Only warnings, no blocking
    SOFT_BLOCK = "soft_block"  # Block with low confidence, suggest alternatives
    HARD_BLOCK = "hard_block"  # Block with high confidence violations


@dataclass
class ValidationResult:
    """Result of tool selection validation."""
    is_valid: bool
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0-1.0, how confident we are in validation
    blocked: bool = False  # Whether tool execution should be blocked
    alternatives: List[str] = field(default_factory=list)  # Alternative tools to consider
    severity: str = "info"  # "info", "warning", "error"


@dataclass
class ToolRanking:
    """Ranking information for a tool."""
    tool_name: str
    score: float  # 0.0-1.0
    reasons: List[str] = field(default_factory=list)
    expected_reward: float = 0.5  # Expected RL reward from using this tool
    confidence_interval: tuple[float, float] = (0.0, 1.0)  # Lower and upper bounds
    exploration_bonus: float = 0.0  # Bonus for exploration


class GuidanceAggregator:
    """
    Aggregates guidance signals from multiple sources.
    
    Combines information from:
    - Reasoning engine (goals, working memory, production rules)
    - RL signal aggregator (rewards, exploration-exploitation)
    - Skill manager (applicable skills, suggested actions)
    - Goal manager (active goals, requirements)
    """
    
    def __init__(
        self,
        reasoning_tool: Optional["ReasoningTool"] = None,
        rl_signal_aggregator: Optional["RLSignalAggregator"] = None,
        skill_manager: Optional["SkillManager"] = None,
        goal_manager: Optional["GoalManager"] = None,
        policy_ranker: Optional[Any] = None,
    ):
        self.reasoning_tool = reasoning_tool
        self.rl_signal_aggregator = rl_signal_aggregator
        self.skill_manager = skill_manager
        self.goal_manager = goal_manager
        self.policy_ranker = policy_ranker
        # TTL cache for policy predictions
        self._policy_cache = {}
        self._policy_cache_ttl = 2.0  # seconds
    
    def gather_context(self) -> Dict[str, Any]:
        """
        Gather current context from all sources.
        
        Returns:
            Dictionary with context information
        """
        context: Dict[str, Any] = {
            "active_goals": [],
            "working_memory_items": [],
            "applicable_skills": [],
            "rl_signals": None,
            "production_rules": [],
        }
        
        # Get active goals
        if self.goal_manager:
            try:
                active_goals = self.goal_manager.get_active_goals()
                context["active_goals"] = [goal.to_dict() for goal in active_goals]
            except Exception as e:
                logger.debug(f"Error getting active goals: {e}")
        
        # Get working memory items
        if self.reasoning_tool and hasattr(self.reasoning_tool, 'rule_system'):
            try:
                wm = self.reasoning_tool.rule_system.working_memory
                if wm:
                    context["working_memory_items"] = [
                        item.to_dict() if hasattr(item, 'to_dict') else str(item)
                        for item in wm.items[:10]  # Limit to recent items
                    ]
            except Exception as e:
                logger.debug(f"Error getting working memory: {e}")
        
        # Get applicable skills
        if self.skill_manager:
            try:
                skill_context = {
                    "active_goals": context["active_goals"],
                    "memory_items": context["working_memory_items"],
                    "system_state": {}
                }
                applicable_skills = self.skill_manager.get_applicable_skills(skill_context)
                context["applicable_skills"] = [
                    skill.to_dict() for skill in applicable_skills[:5]  # Top 5 skills
                ]
            except Exception as e:
                logger.debug(f"Error getting applicable skills: {e}")
        
        # Get RL signals
        if self.rl_signal_aggregator:
            try:
                rl_metrics = self.rl_signal_aggregator.compute_signals()
                context["rl_signals"] = {
                    "composite_reward": rl_metrics.composite_reward,
                    "dissonance_reward": rl_metrics.dissonance_reward,
                    "surprise_reward": rl_metrics.surprise_reward,
                    "curiosity_reward": rl_metrics.curiosity_reward,
                    "information_gain_reward": rl_metrics.information_gain_reward,
                    "coherence_reward": rl_metrics.coherence_reward,
                    "exploration_balance": rl_metrics.get_exploration_exploitation_balance(),
                }
            except Exception as e:
                logger.debug(f"Error getting RL signals: {e}")
        
        # Get production rules (if available)
        if self.reasoning_tool and hasattr(self.reasoning_tool, 'rule_system'):
            try:
                rule_system = self.reasoning_tool.rule_system
                if rule_system:
                    context["production_rules"] = [
                        rule.to_dict() for rule in rule_system.rules[:10]  # Top 10 rules
                    ]
            except Exception as e:
                logger.debug(f"Error getting production rules: {e}")
        

    def get_policy_rankings(self, tools: List["Tool"], context: Dict[str, Any]) -> List[ToolRanking]:
        """Use PolicyRanker to produce ToolRanking list sorted by predicted probability.

        Returns empty list if no policy_ranker is configured.
        """
        if not self.policy_ranker:
            return []

        # Simple cache key based on tools names and a short-time window
        key = hashlib.sha256(("|".join([t.name for t in tools]) + str(int(time.time()//self._policy_cache_ttl))).encode()).hexdigest()
        now = time.time()
        if key in self._policy_cache:
            val, ts = self._policy_cache[key]
            if now - ts < self._policy_cache_ttl:
                return val

        try:
            probs = self.policy_ranker.predict_distribution(context, tools)
            rankings: List[ToolRanking] = []
            for t in tools:
                name = t.name
                score = float(probs.get(name, 0.0))
                rankings.append(ToolRanking(tool_name=name, score=score, expected_reward=score))

            rankings.sort(key=lambda r: r.score, reverse=True)
            self._policy_cache[key] = (rankings, now)
            return rankings
        except Exception as e:
            logger.debug(f"PolicyRanker error: {e}")
            return []


        return context


class ContextCache:
    """
    Cache for context data with TTL and invalidation.
    
    Reduces redundant context gathering by caching results
    with time-to-live (TTL) and invalidation on state changes.
    """
    
    def __init__(self, ttl_seconds: int = 5):
        """
        Initialize context cache.
        
        Args:
            ttl_seconds: Time-to-live for cached context (default: 5 seconds)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Dict[str, Any], float]] = {}  # key -> (context, timestamp)
        self._cache_key_hash: Optional[str] = None
    
    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Dict[str, Any]],
        state_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cached context or compute if expired/invalid.
        
        Args:
            key: Cache key
            compute_fn: Function to compute context if cache miss
            state_hash: Optional hash of system state for invalidation
            
        Returns:
            Context dictionary
        """
        current_time = time.time()
        
        # Invalidate if state hash changed
        if state_hash and state_hash != self._cache_key_hash:
            self._cache.clear()
            self._cache_key_hash = state_hash
            logger.debug("Context cache invalidated due to state change")
        
        # Check cache
        if key in self._cache:
            cached_context, timestamp = self._cache[key]
            age = current_time - timestamp
            
            if age < self.ttl_seconds:
                logger.debug(f"Context cache hit for key '{key}' (age: {age:.2f}s)")
                return cached_context
            else:
                logger.debug(f"Context cache expired for key '{key}' (age: {age:.2f}s)")
                del self._cache[key]
        
        # Cache miss - compute
        logger.debug(f"Context cache miss for key '{key}', computing...")
        context = compute_fn()
        self._cache[key] = (context, current_time)
        
        return context
    
    def invalidate(self, key: Optional[str] = None):
        """
        Invalidate cache entry or entire cache.
        
        Args:
            key: Optional specific key to invalidate, None to clear all
        """
        if key:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Invalidated cache entry for key '{key}'")
        else:
            self._cache.clear()
            self._cache_key_hash = None
            logger.debug("Cleared entire context cache")
    
    def get_state_hash(self, context: Dict[str, Any]) -> str:
        """
        Compute hash of context state for invalidation.
        
        Args:
            context: Context dictionary
            
        Returns:
            Hash string
        """
        # Create stable hash from key context components
        key_parts = [
            str(len(context.get("active_goals", []))),
            str(len(context.get("applicable_skills", []))),
            str(context.get("rl_signals", {}).get("composite_reward", 0.0)),
        ]
        hash_input = "|".join(key_parts)
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


class IncrementalContextUpdater:
    """
    Incremental context updater for delta-based updates.
    
    Only updates changed components of context instead of
    recomputing everything.
    """
    
    def __init__(self, guidance_aggregator: "GuidanceAggregator"):
        self.guidance_aggregator = guidance_aggregator
        self._last_context: Optional[Dict[str, Any]] = None
        self._last_update_time: float = 0.0
    
    def update_context(
        self,
        base_context: Dict[str, Any],
        changed_components: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update context incrementally.
        
        Args:
            base_context: Base context to update
            changed_components: Optional list of component names that changed
            
        Returns:
            Updated context
        """
        if changed_components is None:
            # If no specific components, check what might have changed
            changed_components = self._detect_changes(base_context)
        
        updated_context = base_context.copy()
        
        # Update only changed components
        if "active_goals" in changed_components and self.guidance_aggregator.goal_manager:
            try:
                active_goals = self.guidance_aggregator.goal_manager.get_active_goals()
                updated_context["active_goals"] = [goal.to_dict() for goal in active_goals]
            except Exception as e:
                logger.debug(f"Error updating active_goals: {e}")
        
        if "applicable_skills" in changed_components and self.guidance_aggregator.skill_manager:
            try:
                skill_context = {
                    "active_goals": updated_context.get("active_goals", []),
                    "memory_items": updated_context.get("working_memory_items", []),
                    "system_state": {}
                }
                applicable_skills = self.guidance_aggregator.skill_manager.get_applicable_skills(skill_context)
                updated_context["applicable_skills"] = [
                    skill.to_dict() for skill in applicable_skills[:5]
                ]
            except Exception as e:
                logger.debug(f"Error updating applicable_skills: {e}")
        
        if "rl_signals" in changed_components and self.guidance_aggregator.rl_signal_aggregator:
            try:
                rl_metrics = self.guidance_aggregator.rl_signal_aggregator.compute_signals()
                updated_context["rl_signals"] = {
                    "composite_reward": rl_metrics.composite_reward,
                    "dissonance_reward": rl_metrics.dissonance_reward,
                    "surprise_reward": rl_metrics.surprise_reward,
                    "curiosity_reward": rl_metrics.curiosity_reward,
                    "information_gain_reward": rl_metrics.information_gain_reward,
                    "coherence_reward": rl_metrics.coherence_reward,
                    "exploration_balance": rl_metrics.get_exploration_exploitation_balance(),
                }
            except Exception as e:
                logger.debug(f"Error updating rl_signals: {e}")
        
        self._last_context = updated_context
        self._last_update_time = time.time()
        
        return updated_context
    
    def _detect_changes(self, current_context: Dict[str, Any]) -> List[str]:
        """Detect which context components have changed."""
        if self._last_context is None:
            return ["active_goals", "applicable_skills", "rl_signals", "working_memory_items"]
        
        changed = []
        
        # Compare active goals
        current_goals = current_context.get("active_goals", [])
        last_goals = self._last_context.get("active_goals", [])
        if len(current_goals) != len(last_goals) or current_goals != last_goals:
            changed.append("active_goals")
        
        # Compare RL signals (check composite reward)
        current_reward = current_context.get("rl_signals", {}).get("composite_reward", 0.0)
        last_reward = self._last_context.get("rl_signals", {}).get("composite_reward", 0.0)
        if abs(current_reward - last_reward) > 0.1:  # Significant change
            changed.append("rl_signals")
        
        # Always check skills (they depend on goals)
        if changed:
            changed.append("applicable_skills")
        
        return changed if changed else ["rl_signals"]  # At least update RL signals periodically


class TemporalContextTracker:
    """
    Tracks recent tool usage patterns for temporal context.
    """
    
    def __init__(self, window_size: int = 20):
        """
        Initialize temporal context tracker.
        
        Args:
            window_size: Number of recent tool usages to track
        """
        self.window_size = window_size
        self._recent_tools: deque = deque(maxlen=window_size)
        self._tool_sequences: List[List[str]] = []  # Recent tool sequences
    
    def record_tool_usage(self, tool_name: str):
        """Record a tool usage."""
        self._recent_tools.append({
            "tool_name": tool_name,
            "timestamp": time.time()
        })
    
    def get_recent_patterns(self) -> Dict[str, Any]:
        """
        Get recent tool usage patterns.
        
        Returns:
            Dictionary with pattern information
        """
        if len(self._recent_tools) == 0:
            return {
                "recent_tools": [],
                "tool_frequency": {},
                "common_sequences": []
            }
        
        # Count tool frequency
        tool_frequency: Dict[str, int] = defaultdict(int)
        for usage in self._recent_tools:
            tool_frequency[usage["tool_name"]] += 1
        
        # Get recent tool names
        recent_tool_names = [u["tool_name"] for u in self._recent_tools]
        
        return {
            "recent_tools": recent_tool_names[-5:],  # Last 5 tools
            "tool_frequency": dict(tool_frequency),
            "common_sequences": self._extract_sequences(recent_tool_names)
        }
    
    def _extract_sequences(self, tool_names: List[str]) -> List[List[str]]:
        """Extract common 2-tool sequences."""
        if len(tool_names) < 2:
            return []
        
        sequences: Dict[tuple, int] = defaultdict(int)
        for i in range(len(tool_names) - 1):
            seq = (tool_names[i], tool_names[i + 1])
            sequences[seq] += 1
        
        # Return most common sequences
        sorted_sequences = sorted(sequences.items(), key=lambda x: x[1], reverse=True)
        return [[t1, t2] for (t1, t2), count in sorted_sequences[:3]]


class ToolRelationshipGraph:
    """
    Learns and tracks tool co-occurrence patterns.
    """
    
    def __init__(self):
        """Initialize tool relationship graph."""
        self._co_occurrence: Dict[tuple[str, str], int] = defaultdict(int)
        self._tool_success_pairs: Dict[tuple[str, str], List[bool]] = defaultdict(list)
    
    def record_tool_pair(self, tool1: str, tool2: str, success: bool = True):
        """
        Record that two tools were used together.
        
        Args:
            tool1: First tool name
            tool2: Second tool name
            success: Whether the pair was successful
        """
        # Record both directions (undirected graph)
        pair = tuple(sorted([tool1, tool2]))
        self._co_occurrence[pair] += 1
        self._tool_success_pairs[pair].append(success)
        
        # Limit history
        if len(self._tool_success_pairs[pair]) > 100:
            self._tool_success_pairs[pair] = self._tool_success_pairs[pair][-100:]
    
    def get_related_tools(self, tool_name: str, min_co_occurrence: int = 2) -> List[tuple[str, float]]:
        """
        Get tools that are frequently used with the given tool.
        
        Args:
            tool_name: Tool name
            min_co_occurrence: Minimum co-occurrence count
            
        Returns:
            List of (tool_name, success_rate) tuples, sorted by success rate
        """
        related: List[tuple[str, float]] = []
        
        for (t1, t2), count in self._co_occurrence.items():
            if count < min_co_occurrence:
                continue
            
            if t1 == tool_name:
                other = t2
            elif t2 == tool_name:
                other = t1
            else:
                continue
            
            # Calculate success rate for this pair
            successes = self._tool_success_pairs[(t1, t2)]
            if len(successes) > 0:
                success_rate = sum(successes) / len(successes)
                related.append((other, success_rate))
        
        # Sort by success rate (highest first)
        related.sort(key=lambda x: x[1], reverse=True)
        return related
    
    def get_relationship_strength(self, tool1: str, tool2: str) -> float:
        """
        Get relationship strength between two tools.
        
        Args:
            tool1: First tool name
            tool2: Second tool name
            
        Returns:
            Relationship strength (0.0-1.0)
        """
        pair = tuple(sorted([tool1, tool2]))
        count = self._co_occurrence.get(pair, 0)
        
        if count == 0:
            return 0.0
        
        # Normalize by max co-occurrence (simple heuristic)
        max_count = max(self._co_occurrence.values()) if self._co_occurrence else 1
        return min(1.0, count / max(max_count, 1))


class MultiArmedBanditRanker:
    """
    Multi-armed bandit ranker using UCB1 algorithm.
    
    Balances exploration vs exploitation for tool selection.
    """
    
    def __init__(self, exploration_factor: float = 0.1, base_ranker: Optional["ToolRanker"] = None):
        """
        Initialize multi-armed bandit ranker.
        
        Args:
            exploration_factor: Exploration constant (higher = more exploration)
            base_ranker: Optional base ranker for initial scores
        """
        self.exploration_factor = exploration_factor
        self.base_ranker = base_ranker
        self._tool_pulls: Dict[str, int] = defaultdict(int)  # Number of times tool was selected
        self._tool_rewards: Dict[str, List[float]] = defaultdict(list)  # Reward history
        self._total_pulls = 0
    
    def rank_tools(
        self,
        tools: List["Tool"],
        context: Dict[str, Any],
        base_rankings: Optional[List[ToolRanking]] = None
    ) -> List[ToolRanking]:
        """
        Rank tools using UCB1 algorithm.
        
        Args:
            tools: List of available tools
            context: Current context
            base_rankings: Optional base rankings from simple ranker
            
        Returns:
            List of ToolRanking objects with UCB1 scores
        """
        if base_rankings is None and self.base_ranker:
            base_rankings = self.base_ranker.rank_tools(tools, context)
        
        ucb_rankings: List[ToolRanking] = []
        
        for tool in tools:
            tool_name = tool.name
            
            # Get base score
            base_score = 0.5
            if base_rankings:
                base_ranking = next((r for r in base_rankings if r.tool_name == tool_name), None)
                if base_ranking:
                    base_score = base_ranking.score
            
            # Calculate average reward
            rewards = self._tool_rewards.get(tool_name, [])
            avg_reward = sum(rewards) / len(rewards) if rewards else base_score
            
            # Calculate UCB1 value
            pulls = self._tool_pulls.get(tool_name, 0)
            if pulls == 0:
                # Never pulled - high exploration value
                ucb_value = 1.0
                exploration_bonus = 0.5
            else:
                # UCB1 formula: avg_reward + c * sqrt(ln(total_pulls) / pulls)
                exploration_term = self.exploration_factor * math.sqrt(
                    math.log(max(1, self._total_pulls)) / max(1, pulls)
                )
                ucb_value = avg_reward + exploration_term
                exploration_bonus = exploration_term
            
            # Normalize to [0, 1]
            ucb_value = max(0.0, min(1.0, ucb_value))
            
            # Confidence interval (simplified)
            confidence_lower = max(0.0, avg_reward - exploration_term)
            confidence_upper = min(1.0, avg_reward + exploration_term)
            
            # Get reasons from base ranking if available
            reasons = []
            if base_rankings:
                base_ranking = next((r for r in base_rankings if r.tool_name == tool_name), None)
                if base_ranking:
                    reasons = base_ranking.reasons.copy()
            
            if exploration_bonus > 0.1:
                reasons.append(f"Exploration bonus: {exploration_bonus:.2f}")
            
            ucb_rankings.append(ToolRanking(
                tool_name=tool_name,
                score=ucb_value,
                reasons=reasons,
                expected_reward=avg_reward,
                confidence_interval=(confidence_lower, confidence_upper),
                exploration_bonus=exploration_bonus
            ))
        
        # Sort by UCB1 score (highest first)
        ucb_rankings.sort(key=lambda r: r.score, reverse=True)
        
        return ucb_rankings
    
    def record_tool_selection(self, tool_name: str, reward: float):
        """
        Record tool selection and reward for learning.
        
        Args:
            tool_name: Tool that was selected
            reward: Reward received (0.0-1.0)
        """
        self._tool_pulls[tool_name] += 1
        self._total_pulls += 1
        
        # Record reward
        self._tool_rewards[tool_name].append(reward)
        
        # Limit history
        if len(self._tool_rewards[tool_name]) > 100:
            self._tool_rewards[tool_name] = self._tool_rewards[tool_name][-100:]


class GuidanceTextFormatter:
    """
    Formats guidance text with prioritization and context-awareness.
    """
    
    def __init__(self, style: str = "prioritized"):
        """
        Initialize guidance text formatter.
        
        Args:
            style: Formatting style ("concise", "detailed", "prioritized")
        """
        self.style = style
    
    def format_prioritized(
        self,
        top_tools: List[ToolRanking],
        context: Dict[str, Any],
        max_length: int = 2000
    ) -> str:
        """
        Format guidance text with prioritized tool suggestions.
        
        Args:
            top_tools: Top ranked tools
            context: Current context
            max_length: Maximum text length
            
        Returns:
            Formatted guidance text
        """
        sections: List[str] = []
        
        # 1. Goals section
        active_goals = context.get("active_goals", [])
        if active_goals:
            high_priority = [g for g in active_goals if g.get("priority", 0) > 0.7]
            if high_priority:
                goal_names = [g.get("name", "") for g in high_priority[:3]]
                sections.append(f"**Active Goals**: {', '.join(goal_names)}")
        
        # 2. Skills section
        applicable_skills = context.get("applicable_skills", [])
        if applicable_skills:
            top_skills = applicable_skills[:2]
            skill_info = []
            for skill in top_skills:
                name = skill.get("name", "")
                proficiency = skill.get("proficiency_level", 0.5)
                skill_info.append(f"{name} ({proficiency:.0%})")
            sections.append(f"**Applicable Skills**: {', '.join(skill_info)}")
        
        # 3. RL Signals section
        rl_signals = context.get("rl_signals")
        if rl_signals:
            exploration_balance = rl_signals.get("exploration_balance", 0.5)
            composite_reward = rl_signals.get("composite_reward", 0.5)
            
            if exploration_balance > 0.6:
                sections.append("**Mode**: Exploration - prioritize information-gathering tools")
            elif exploration_balance < 0.4:
                sections.append("**Mode**: Exploitation - prioritize proven tools")
            
            if composite_reward < 0.3:
                sections.append("**Status**: Low reward - consider tools that improve coherence")
        
        # 4. Top Tools section (prioritized)
        if top_tools:
            tool_suggestions = []
            for i, ranking in enumerate(top_tools[:3], 1):
                tool_name = ranking.tool_name
                score = ranking.score
                confidence = (ranking.confidence_interval[1] - ranking.confidence_interval[0]) / 2
                
                # Get primary reason
                primary_reason = ranking.reasons[0] if ranking.reasons else "High relevance"
                
                tool_suggestions.append(
                    f"{i}. **{tool_name}** (score: {score:.2f}, confidence: {confidence:.2f}) - {primary_reason}"
                )
            
            if tool_suggestions:
                sections.append("**Recommended Tools**:\n" + "\n".join(tool_suggestions))
        
        # Combine sections
        guidance_text = "\n\n".join(sections)
        
        # Truncate if needed
        if len(guidance_text) > max_length:
            # Try to keep top tools section
            if "**Recommended Tools**" in guidance_text:
                tools_section_start = guidance_text.find("**Recommended Tools**")
                if tools_section_start < max_length * 0.7:
                    # Keep everything up to and including tools section
                    guidance_text = guidance_text[:max_length]
                    # Cut at last complete line
                    last_newline = guidance_text.rfind("\n")
                    if last_newline > max_length * 0.8:
                        guidance_text = guidance_text[:last_newline]
                else:
                    # Truncate earlier sections
                    guidance_text = guidance_text[:max_length]
            else:
                guidance_text = guidance_text[:max_length]
        
        return guidance_text


class ToolRanker:
    """
    Ranks tools based on context and expected rewards.
    """
    
    def __init__(
        self,
        guidance_aggregator: GuidanceAggregator,
        historical_success: Optional[Dict[str, float]] = None,
    ):
        self.guidance_aggregator = guidance_aggregator
        self.historical_success = historical_success or {}
        # Track tool usage for success rate calculation
        self._tool_usage_history: Dict[str, deque] = {}
    
    def rank_tools(
        self,
        tools: List["Tool"],
        context: Dict[str, Any]
    ) -> List[ToolRanking]:
        """
        Rank tools by relevance and expected reward.
        
        Args:
            tools: List of available tools
            context: Current context from GuidanceAggregator
            
        Returns:
            List of ToolRanking objects, sorted by score (highest first)
        """
        rankings: List[ToolRanking] = []
        
        active_goals = context.get("active_goals", [])
        applicable_skills = context.get("applicable_skills", [])
        rl_signals = context.get("rl_signals")
        working_memory_items = context.get("working_memory_items", [])
        
        for tool in tools:
            ranking = self._rank_tool(tool, active_goals, applicable_skills, rl_signals, working_memory_items)
            rankings.append(ranking)
        
        # Sort by score (highest first)
        rankings.sort(key=lambda r: r.score, reverse=True)
        
        return rankings
    
    def _rank_tool(
        self,
        tool: "Tool",
        active_goals: List[Dict[str, Any]],
        applicable_skills: List[Dict[str, Any]],
        rl_signals: Optional[Dict[str, float]],
        working_memory_items: List[Any],
    ) -> ToolRanking:
        """Rank a single tool."""
        score = 0.5  # Base score
        reasons: List[str] = []
        expected_reward = 0.5
        
        tool_name = tool.name
        
        # 1. Check if tool is needed for active goals
        goal_relevance = self._check_goal_relevance(tool_name, active_goals)
        if goal_relevance > 0:
            score += goal_relevance * 0.3
            reasons.append(f"Relevant to {len([g for g in active_goals if self._tool_matches_goal(tool_name, g)])} active goal(s)")
        
        # 2. Check if tool is suggested by applicable skills
        skill_relevance = self._check_skill_relevance(tool_name, applicable_skills)
        if skill_relevance > 0:
            score += skill_relevance * 0.25
            reasons.append(f"Suggested by {len([s for s in applicable_skills if self._tool_matches_skill(tool_name, s)])} applicable skill(s)")
        
        # 3. Use RL signals for expected reward
        if rl_signals:
            # Base expected reward on composite reward
            expected_reward = rl_signals.get("composite_reward", 0.5)
            
            # Adjust based on exploration-exploitation balance
            exploration_balance = rl_signals.get("exploration_balance", 0.5)
            
            # If high exploration, boost tools that provide information
            if exploration_balance > 0.6:
                if tool_name in ["web_search", "retrieve_memories", "browse"]:
                    score += 0.2
                    reasons.append("High exploration mode - information-gathering tool")
            # If high exploitation, boost tools with high historical success
            elif exploration_balance < 0.4:
                historical_score = self.historical_success.get(tool_name, 0.5)
                score += historical_score * 0.2
                reasons.append(f"High exploitation mode - historically successful tool")
        
        # 4. Historical success rate
        historical_score = self.historical_success.get(tool_name, 0.5)
        score += historical_score * 0.15
        if historical_score > 0.7:
            reasons.append("High historical success rate")
        
        # 5. Working memory context matching
        wm_relevance = self._check_working_memory_relevance(tool_name, working_memory_items)
        if wm_relevance > 0:
            score += wm_relevance * 0.1
            reasons.append("Relevant to working memory context")
        
        # Normalize score to [0, 1]
        score = max(0.0, min(1.0, score))
        
        return ToolRanking(
            tool_name=tool_name,
            score=score,
            reasons=reasons,
            expected_reward=expected_reward
        )
    
    def _check_goal_relevance(self, tool_name: str, active_goals: List[Dict[str, Any]]) -> float:
        """Check how relevant a tool is to active goals."""
        relevance = 0.0
        for goal in active_goals:
            if self._tool_matches_goal(tool_name, goal):
                # Weight by goal priority
                priority = goal.get("priority", 0.5)
                relevance += priority
        return min(1.0, relevance / max(1, len(active_goals)))
    
    def _tool_matches_goal(self, tool_name: str, goal: Dict[str, Any]) -> bool:
        """Check if tool matches goal requirements."""
        description = goal.get("description", "").lower()
        name = goal.get("name", "").lower()
        
        # Simple keyword matching (can be enhanced)
        tool_keywords = {
            "terminal": ["execute", "run", "command", "script", "code"],
            "web_search": ["search", "find", "information", "lookup"],
            "retrieve_memories": ["remember", "recall", "memory", "past"],
            "store_memory": ["remember", "save", "store", "learn"],
            "reasoning": ["reason", "think", "plan", "goal"],
        }
        
        keywords = tool_keywords.get(tool_name, [])
        for keyword in keywords:
            if keyword in description or keyword in name:
                return True
        return False
    
    def _check_skill_relevance(self, tool_name: str, applicable_skills: List[Dict[str, Any]]) -> float:
        """Check how relevant a tool is to applicable skills."""
        relevance = 0.0
        for skill in applicable_skills:
            if self._tool_matches_skill(tool_name, skill):
                # Weight by skill proficiency
                proficiency = skill.get("proficiency_level", 0.5)
                relevance += proficiency
        return min(1.0, relevance / max(1, len(applicable_skills)))
    
    def _tool_matches_skill(self, tool_name: str, skill: Dict[str, Any]) -> bool:
        """Check if tool matches skill suggestions."""
        # Check skill's suggested actions
        skill_type = skill.get("skill_type", "")
        skill_name = skill.get("name", "").lower()
        
        # Map skill types to tools
        skill_tool_map = {
            "technical": ["terminal", "environment_access"],
            "analytical": ["retrieve_memories", "web_search", "reasoning"],
            "procedural": ["terminal", "reasoning"],
        }
        
        suggested_tools = skill_tool_map.get(skill_type, [])
        if tool_name in suggested_tools:
            return True
        
        # Check if tool name appears in skill name/description
        description = skill.get("description", "").lower()
        if tool_name in skill_name or tool_name in description:
            return True
        
        return False
    
    def _check_working_memory_relevance(self, tool_name: str, working_memory_items: List[Any]) -> float:
        """Check if tool is relevant to working memory context."""
        # Simple heuristic: if working memory has tool-related items
        if not working_memory_items:
            return 0.0
        
        # Check if any WM item mentions the tool
        wm_text = " ".join([str(item) for item in working_memory_items]).lower()
        if tool_name in wm_text:
            return 0.5
        
        return 0.0
    
    def record_tool_outcome(self, tool_name: str, success: bool):
        """Record tool usage outcome for historical success tracking."""
        if tool_name not in self._tool_usage_history:
            self._tool_usage_history[tool_name] = deque(maxlen=100)
        
        self._tool_usage_history[tool_name].append(1.0 if success else 0.0)
        
        # Update historical success rate
        history = self._tool_usage_history[tool_name]
        if len(history) > 0:
            self.historical_success[tool_name] = sum(history) / len(history)


class ToolValidator:
    """
    Validates tool selections against constraints with configurable strictness.
    """
    
    def __init__(
        self,
        guidance_aggregator: GuidanceAggregator,
        strictness: ValidationStrictness = ValidationStrictness.ADVISORY,
        confidence_threshold: float = 0.7,
    ):
        self.guidance_aggregator = guidance_aggregator
        self.strictness = strictness
        self.confidence_threshold = confidence_threshold
    
    def validate_tool_selection(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a tool selection against constraints.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            context: Current context
            
        Returns:
            ValidationResult with validation status and suggestions
        """
        warnings: List[str] = []
        suggestions: List[str] = []
        confidence = 1.0
        
        active_goals = context.get("active_goals", [])
        rl_signals = context.get("rl_signals")
        
        # 1. Check goal constraints
        goal_validation = self._validate_against_goals(tool_name, active_goals)
        if not goal_validation["valid"]:
            warnings.extend(goal_validation["warnings"])
            suggestions.extend(goal_validation["suggestions"])
            confidence *= 0.7
        
        # 2. Check RL recommendations
        if rl_signals:
            rl_validation = self._validate_against_rl_signals(tool_name, rl_signals)
            if not rl_validation["valid"]:
                warnings.extend(rl_validation["warnings"])
                suggestions.extend(rl_validation["suggestions"])
                confidence *= 0.9  # RL validation is softer
        
        # 3. Check production rules (if available)
        production_rules = context.get("production_rules", [])
        if production_rules:
            rule_validation = self._validate_against_rules(tool_name, production_rules)
            if not rule_validation["valid"]:
                warnings.extend(rule_validation["warnings"])
                confidence *= 0.8
        
        # Determine if tool should be blocked based on strictness
        blocked = False
        severity = "info"
        
        if self.strictness == ValidationStrictness.ADVISORY:
            # Never block, only warn
            blocked = False
            severity = "warning" if warnings else "info"
        elif self.strictness == ValidationStrictness.SOFT_BLOCK:
            # Block if confidence is below threshold
            if confidence < self.confidence_threshold and len(warnings) > 0:
                blocked = True
                severity = "warning"
        elif self.strictness == ValidationStrictness.HARD_BLOCK:
            # Block if confidence is below threshold or critical violations
            critical_violations = any("conflict" in w.lower() or "violates" in w.lower() for w in warnings)
            if confidence < self.confidence_threshold or critical_violations:
                blocked = True
                severity = "error"
        
        # Generate alternative suggestions if blocking
        alternatives: List[str] = []
        if blocked and suggestions:
            # Extract tool names from suggestions
            for suggestion in suggestions:
                if "try" in suggestion.lower() or "consider" in suggestion.lower():
                    # Try to extract tool name
                    words = suggestion.lower().split()
                    for i, word in enumerate(words):
                        if word in ["try", "consider", "use"] and i + 1 < len(words):
                            potential_tool = words[i + 1].strip(".,")
                            if potential_tool not in alternatives:
                                alternatives.append(potential_tool)
        
        is_valid = not blocked
        
        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            suggestions=suggestions,
            confidence=confidence,
            blocked=blocked,
            alternatives=alternatives,
            severity=severity
        )
    
    def _validate_against_goals(
        self,
        tool_name: str,
        active_goals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate tool against active goals."""
        result = {"valid": True, "warnings": [], "suggestions": []}
        
        # Check if tool conflicts with goal constraints
        for goal in active_goals:
            goal_name = goal.get("name", "")
            goal_type = goal.get("goal_type", "")
            
            # Check for read-only goals
            if "read_only" in goal_name.lower() or "readonly" in goal_name.lower():
                write_tools = ["store_memory", "update_memory", "delete_memory", "terminal"]
                if tool_name in write_tools:
                    result["valid"] = False
                    result["warnings"].append(
                        f"Tool '{tool_name}' may conflict with read-only goal '{goal_name}'"
                    )
                    result["suggestions"].append("Consider using read-only alternatives")
        
        return result
    
    def _validate_against_rl_signals(
        self,
        tool_name: str,
        rl_signals: Dict[str, float]
    ) -> Dict[str, Any]:
        """Validate tool against RL signal recommendations."""
        result = {"valid": True, "warnings": [], "suggestions": []}
        
        exploration_balance = rl_signals.get("exploration_balance", 0.5)
        composite_reward = rl_signals.get("composite_reward", 0.5)
        
        # If low composite reward, suggest tools that might improve it
        if composite_reward < 0.3:
            info_tools = ["web_search", "retrieve_memories", "reasoning"]
            if tool_name not in info_tools:
                result["warnings"].append(
                    f"Low composite reward ({composite_reward:.2f}). Consider information-gathering tools."
                )
                result["suggestions"].extend([f"Try {tool} for better reward" for tool in info_tools[:2]])
        
        return result
    
    def _validate_against_rules(
        self,
        tool_name: str,
        production_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate tool against production rules."""
        result = {"valid": True, "warnings": []}
        
        # Check if any rule suggests a different tool
        for rule in production_rules:
            actions = rule.get("actions", [])
            for action in actions:
                if action.get("type") == "suggest_tool":
                    suggested_tool = action.get("tool_name")
                    if suggested_tool and suggested_tool != tool_name:
                        # Soft warning - rule suggests different tool
                        result["warnings"].append(
                            f"Rule '{rule.get('name')}' suggests tool '{suggested_tool}'"
                        )
        
        return result


class ToolSelectionGuidance:
    """
    Main orchestrator for tool selection guidance.
    
    Provides:
    - Natural language guidance for system prompt
    - Tool filtering and ranking
    - Post-selection validation
    """
    
    def __init__(
        self,
        reasoning_tool: Optional["ReasoningTool"] = None,
        rl_signal_aggregator: Optional["RLSignalAggregator"] = None,
        skill_manager: Optional["SkillManager"] = None,
        goal_manager: Optional["GoalManager"] = None,
        max_guidance_length: int = 2000,
        guidance_text_style: str = "prioritized",
        ranking_algorithm: str = "simple",
        validation_strictness: ValidationStrictness = ValidationStrictness.ADVISORY,
        validation_confidence_threshold: float = 0.7,
        context_cache_ttl_seconds: int = 5,
        exploration_factor: float = 0.1,
    ):
        self.guidance_aggregator = GuidanceAggregator(
            reasoning_tool=reasoning_tool,
            rl_signal_aggregator=rl_signal_aggregator,
            skill_manager=skill_manager,
            goal_manager=goal_manager,
            policy_ranker=None
        )
        
        # Initialize base ranker
        self.base_ranker = ToolRanker(self.guidance_aggregator)
        
        # Initialize advanced rankers if enabled
        self.mab_ranker: Optional[MultiArmedBanditRanker] = None
        if ranking_algorithm in ["multi_armed_bandit", "learned"]:
            self.mab_ranker = MultiArmedBanditRanker(
                exploration_factor=exploration_factor,
                base_ranker=self.base_ranker
            )
        
        # Use MAB ranker if enabled, otherwise base ranker
        self.tool_ranker = self.mab_ranker if self.mab_ranker else self.base_ranker
        
        # Initialize validator with strictness
        self.tool_validator = ToolValidator(
            self.guidance_aggregator,
            strictness=validation_strictness,
            confidence_threshold=validation_confidence_threshold
        )
        
        # Initialize text formatter
        self.text_formatter = GuidanceTextFormatter(style=guidance_text_style)
        
        # Initialize context cache
        self.context_cache = ContextCache(ttl_seconds=context_cache_ttl_seconds)
        self.incremental_updater = IncrementalContextUpdater(self.guidance_aggregator)

        # attach policy ranker to guidance aggregator if available
        try:
            from broca.rl.policy import PolicyRanker
            pr = PolicyRanker()
            pr.load_model(None)
            self.guidance_aggregator.policy_ranker = pr
        except Exception:
            self.guidance_aggregator.policy_ranker = None
        
        # Initialize temporal tracker and relationship graph
        self.temporal_tracker = TemporalContextTracker()
        self.tool_relationships = ToolRelationshipGraph()
        
        # Initialize metrics (optional, will be set if enabled)
        self.metrics: Optional["ToolSelectionMetrics"] = None
        
        self.max_guidance_length = max_guidance_length
        self.guidance_text_style = guidance_text_style
        self.ranking_algorithm = ranking_algorithm
        self._last_tool_used: Optional[str] = None
        self._last_context: Optional[Dict[str, Any]] = None
        
        logger.info(
            f"Initialized ToolSelectionGuidance "
            f"(style={guidance_text_style}, ranking={ranking_algorithm}, strictness={validation_strictness.value})"
        )
    
    def set_metrics(self, metrics: "ToolSelectionMetrics"):
        """Set metrics collector for observability."""
        self.metrics = metrics
    
    def generate_guidance_text(
        self,
        context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List["Tool"]] = None
    ) -> str:
        """
        Generate natural language guidance text for system prompt.
        
        Args:
            context: Optional pre-computed context (will gather if None)
            available_tools: Optional list of available tools
            
        Returns:
            Guidance text string (empty if no guidance available)
        """
        # Use cached context if available
        if context is None:
            def compute_context():
                return self.guidance_aggregator.gather_context()
            
            cache_key = "guidance_context"
            state_hash = None
            if hasattr(self, '_last_context'):
                state_hash = self.context_cache.get_state_hash(self._last_context)
            
            context = self.context_cache.get_or_compute(
                cache_key,
                compute_context,
                state_hash=state_hash
            )
            self._last_context = context
        
        # Get tool rankings if tools provided
        top_tools: List[ToolRanking] = []
        if available_tools and len(available_tools) > 0:
            rankings = self.tool_ranker.rank_tools(available_tools, context)
            # If learned ranking algorithm is selected, incorporate policy_ranker predictions
            if self.ranking_algorithm == 'learned' and hasattr(self.guidance_aggregator, 'get_policy_rankings'):
                policy_rankings = self.guidance_aggregator.get_policy_rankings(available_tools, context)
                if policy_rankings:
                    # Combine rankings: weighted average of base score and policy score
                    alpha = 0.7
                    policy_scores = {r.tool_name: r.score for r in policy_rankings}
                    for r in rankings:
                        policy_score = policy_scores.get(r.tool_name, 0.0)
                        r.score = alpha * policy_score + (1 - alpha) * r.score
                    rankings.sort(key=lambda r: r.score, reverse=True)
            top_tools = [r for r in rankings if r.score > 0.6][:3]
        
        # Record guidance suggestions in metrics
        if self.metrics and top_tools:
            for i, ranking in enumerate(top_tools[:3], 1):
                self.metrics.record_guidance_suggestion(
                    tool_name=ranking.tool_name,
                    rank=i,
                    score=ranking.score
                )
        
        # Use formatter for enhanced text
        if self.guidance_text_style == "prioritized" and top_tools:
            guidance_text = self.text_formatter.format_prioritized(
                top_tools,
                context,
                max_length=self.max_guidance_length
            )
        else:
            # Fallback to simple formatting
            guidance_parts: List[str] = []
            
            # 1. Active goals guidance
            active_goals = context.get("active_goals", [])
            if active_goals:
                high_priority_goals = [g for g in active_goals if g.get("priority", 0) > 0.7]
                if high_priority_goals:
                    goal_names = [g.get("name", "") for g in high_priority_goals[:3]]
                    guidance_parts.append(
                        f"Active high-priority goals: {', '.join(goal_names)}. "
                        "Consider tools that help achieve these goals."
                    )
            
            # 2. Applicable skills guidance
            applicable_skills = context.get("applicable_skills", [])
            if applicable_skills:
                top_skills = applicable_skills[:2]
                skill_names = [s.get("name", "") for s in top_skills]
                guidance_parts.append(
                    f"Applicable skills: {', '.join(skill_names)}. "
                    "These skills suggest relevant tool usage patterns."
                )
            
            # 3. RL signal guidance
            rl_signals = context.get("rl_signals")
            if rl_signals:
                exploration_balance = rl_signals.get("exploration_balance", 0.5)
                composite_reward = rl_signals.get("composite_reward", 0.5)
                
                if exploration_balance > 0.6:
                    guidance_parts.append(
                        "Exploration mode: Consider information-gathering tools "
                        "(web_search, retrieve_memories) to discover new knowledge."
                    )
                elif exploration_balance < 0.4:
                    guidance_parts.append(
                        "Exploitation mode: Prefer tools with high historical success rates."
                    )
                
                if composite_reward < 0.3:
                    guidance_parts.append(
                        "Low composite reward detected. Consider tools that reduce "
                        "dissonance or increase information gain."
                    )
            
            # 4. Tool ranking guidance
            if top_tools:
                tool_names = [r.tool_name for r in top_tools]
                guidance_parts.append(
                    f"Highly relevant tools for current context: {', '.join(tool_names)}."
                )
            
            # Combine and truncate if needed
            guidance_text = " ".join(guidance_parts)
            
            if len(guidance_text) > self.max_guidance_length:
                guidance_text = guidance_text[:self.max_guidance_length]
                last_period = guidance_text.rfind(". ")
                if last_period > self.max_guidance_length * 0.8:
                    guidance_text = guidance_text[:last_period + 1]
        
        return guidance_text
    
    def filter_and_rank_tools(
        self,
        tools: List["Tool"],
        context: Optional[Dict[str, Any]] = None
    ) -> List["Tool"]:
        """
        Filter and rank tools based on context.
        
        Args:
            tools: List of available tools
            context: Optional pre-computed context
            
        Returns:
            Filtered and ranked list of tools (same tools, reordered)
        """
        # Use cached context if available
        if context is None:
            def compute_context():
                return self.guidance_aggregator.gather_context()
            
            cache_key = "ranking_context"
            state_hash = None
            if hasattr(self, '_last_context'):
                state_hash = self.context_cache.get_state_hash(self._last_context)
            
            context = self.context_cache.get_or_compute(
                cache_key,
                compute_context,
                state_hash=state_hash
            )
        
        # Get base rankings for MAB ranker
        base_rankings = None
        if self.mab_ranker and self.base_ranker:
            base_rankings = self.base_ranker.rank_tools(tools, context)
        
        # Rank tools (MAB ranker will use base rankings if available)
        if self.mab_ranker:
            rankings = self.mab_ranker.rank_tools(tools, context, base_rankings=base_rankings)
        else:
            rankings = self.tool_ranker.rank_tools(tools, context)
        
        # Incorporate temporal patterns
        temporal_patterns = self.temporal_tracker.get_recent_patterns()
        if temporal_patterns.get("recent_tools"):
            # Boost tools that follow recent patterns
            recent_tools = temporal_patterns["recent_tools"]
            for ranking in rankings:
                if ranking.tool_name in recent_tools:
                    ranking.score += 0.1  # Small boost for temporal relevance
                    ranking.reasons.append("Recently used tool")
        
        # Incorporate tool relationships
        for ranking in rankings:
            related = self.tool_relationships.get_related_tools(ranking.tool_name)
            if related:
                # Boost if related tools have high success rate
                avg_related_success = sum(rate for _, rate in related[:3]) / len(related[:3]) if related else 0.0
                if avg_related_success > 0.7:
                    ranking.score += 0.05
                    ranking.reasons.append("Works well with other tools")
        
        # Re-sort after adjustments
        rankings.sort(key=lambda r: r.score, reverse=True)
        
        # Record rankings in metrics
        if self.metrics:
            for i, ranking in enumerate(rankings, 1):
                self.metrics.record_ranking(
                    tool_name=ranking.tool_name,
                    rank=i,
                    score=ranking.score
                )
        
        # Create mapping from tool name to tool object
        tool_map = {tool.name: tool for tool in tools}
        
        # Return tools in ranked order (highest score first)
        ranked_tools = []
        for ranking in rankings:
            if ranking.tool_name in tool_map:
                ranked_tools.append(tool_map[ranking.tool_name])
        
        # Include any tools not in rankings (shouldn't happen, but safety)
        ranked_names = {r.tool_name for r in rankings}
        for tool in tools:
            if tool.name not in ranked_names:
                ranked_tools.append(tool)
        
        return ranked_tools
    
    def validate_tool_selection(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate a tool selection.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            context: Optional pre-computed context
            
        Returns:
            ValidationResult
        """
        if context is None:
            context = self.guidance_aggregator.gather_context()
        
        result = self.tool_validator.validate_tool_selection(
            tool_name, arguments, context
        )
        
        # Record validation in metrics
        if self.metrics:
            self.metrics.record_validation(
                tool_name=tool_name,
                blocked=result.blocked,
                confidence=result.confidence,
                warnings_count=len(result.warnings),
                alternatives_count=len(result.alternatives)
            )
        
        return result
    
    def record_tool_outcome(self, tool_name: str, success: bool, reward: Optional[float] = None):
        """
        Record tool usage outcome for learning.
        
        Args:
            tool_name: Tool that was used
            success: Whether tool execution was successful
            reward: Optional reward value (0.0-1.0), computed from success if None
        """
        # Record in base ranker
        self.base_ranker.record_tool_outcome(tool_name, success)
        
        # Record in MAB ranker if enabled
        if self.mab_ranker:
            computed_reward = reward if reward is not None else (1.0 if success else 0.0)
            self.mab_ranker.record_tool_selection(tool_name, computed_reward)
        
        # Record in temporal tracker
        self.temporal_tracker.record_tool_usage(tool_name)
        
        # Record tool relationships (with previous tool if available)
        if hasattr(self, '_last_tool_used') and self._last_tool_used:
            self.tool_relationships.record_tool_pair(
                self._last_tool_used,
                tool_name,
                success=success
            )
        
        self._last_tool_used = tool_name
        
        # Record in metrics that suggestion was followed
        if self.metrics:
            computed_reward = reward if reward is not None else (1.0 if success else 0.0)
            self.metrics.record_guidance_followed(
                tool_name=tool_name,
                outcome=success,
                reward=computed_reward
            )
        
        # Invalidate context cache on tool usage (state changed)
        self.context_cache.invalidate()

