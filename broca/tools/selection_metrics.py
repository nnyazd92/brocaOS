"""
Metrics collection for tool selection guidance.

Tracks guidance effectiveness, validation catch rate, and ranking accuracy.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


@dataclass
class GuidanceSuggestion:
    """Record of a guidance suggestion."""
    tool_name: str
    rank: int
    score: float
    timestamp: datetime
    followed: bool = False
    outcome: Optional[bool] = None  # Success/failure if followed


@dataclass
class ValidationRecord:
    """Record of a validation event."""
    tool_name: str
    timestamp: datetime
    blocked: bool
    confidence: float
    warnings_count: int
    alternatives_provided: int


@dataclass
class RankingRecord:
    """Record of a ranking event."""
    tool_name: str
    rank: int
    score: float
    timestamp: datetime
    outcome: Optional[bool] = None  # Success/failure
    reward: Optional[float] = None


class ToolSelectionMetrics:
    """
    Collects and analyzes metrics for tool selection guidance.
    
    Tracks:
    - Guidance effectiveness (did suggestions get followed?)
    - Validation catch rate (how often validation catches issues?)
    - Ranking accuracy (did high-ranked tools perform well?)
    - Tool selection patterns over time
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            window_size: Number of records to keep in history
        """
        self.window_size = window_size
        
        # Guidance suggestions
        self._guidance_suggestions: deque = deque(maxlen=window_size)
        self._suggestions_by_tool: Dict[str, List[GuidanceSuggestion]] = defaultdict(list)
        
        # Validation records
        self._validation_records: deque = deque(maxlen=window_size)
        self._validations_by_tool: Dict[str, List[ValidationRecord]] = defaultdict(list)
        
        # Ranking records
        self._ranking_records: deque = deque(maxlen=window_size)
        self._rankings_by_tool: Dict[str, List[RankingRecord]] = defaultdict(list)
        
        logger.info(f"Initialized ToolSelectionMetrics (window_size={window_size})")
    
    def record_guidance_suggestion(
        self,
        tool_name: str,
        rank: int,
        score: float
    ):
        """
        Record a guidance suggestion.
        
        Args:
            tool_name: Suggested tool name
            rank: Rank of suggestion (1 = highest)
            score: Relevance score
        """
        suggestion = GuidanceSuggestion(
            tool_name=tool_name,
            rank=rank,
            score=score,
            timestamp=datetime.now(timezone.utc)
        )
        self._guidance_suggestions.append(suggestion)
        self._suggestions_by_tool[tool_name].append(suggestion)
        
        # Limit per-tool history
        if len(self._suggestions_by_tool[tool_name]) > 100:
            self._suggestions_by_tool[tool_name] = self._suggestions_by_tool[tool_name][-100:]
    
    def record_guidance_followed(
        self,
        tool_name: str,
        outcome: bool,
        reward: Optional[float] = None
    ):
        """
        Record that a guidance suggestion was followed.
        
        Args:
            tool_name: Tool that was used
            outcome: Whether tool execution was successful
            reward: Optional reward value
        """
        # Find most recent suggestion for this tool
        for suggestion in reversed(self._guidance_suggestions):
            if suggestion.tool_name == tool_name and not suggestion.followed:
                suggestion.followed = True
                suggestion.outcome = outcome
                break
        
        # Also update ranking records if available
        for ranking in reversed(self._ranking_records):
            if ranking.tool_name == tool_name and ranking.outcome is None:
                ranking.outcome = outcome
                if reward is not None:
                    ranking.reward = reward
                break
    
    def record_validation(
        self,
        tool_name: str,
        blocked: bool,
        confidence: float,
        warnings_count: int,
        alternatives_count: int
    ):
        """
        Record a validation event.
        
        Args:
            tool_name: Tool that was validated
            blocked: Whether tool was blocked
            confidence: Validation confidence
            warnings_count: Number of warnings
            alternatives_count: Number of alternatives suggested
        """
        record = ValidationRecord(
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc),
            blocked=blocked,
            confidence=confidence,
            warnings_count=warnings_count,
            alternatives_provided=alternatives_count
        )
        self._validation_records.append(record)
        self._validations_by_tool[tool_name].append(record)
        
        # Limit per-tool history
        if len(self._validations_by_tool[tool_name]) > 100:
            self._validations_by_tool[tool_name] = self._validations_by_tool[tool_name][-100:]
    
    def record_ranking(
        self,
        tool_name: str,
        rank: int,
        score: float
    ):
        """
        Record a tool ranking.
        
        Args:
            tool_name: Ranked tool name
            rank: Rank position (1 = highest)
            score: Ranking score
        """
        record = RankingRecord(
            tool_name=tool_name,
            rank=rank,
            score=score,
            timestamp=datetime.now(timezone.utc)
        )
        self._ranking_records.append(record)
        self._rankings_by_tool[tool_name].append(record)
        
        # Limit per-tool history
        if len(self._rankings_by_tool[tool_name]) > 100:
            self._rankings_by_tool[tool_name] = self._rankings_by_tool[tool_name][-100:]
    
    def get_effectiveness_metrics(self) -> Dict[str, float]:
        """
        Get guidance effectiveness metrics.
        
        Returns:
            Dictionary with effectiveness metrics
        """
        if len(self._guidance_suggestions) == 0:
            return {
                "guidance_effectiveness": 0.0,
                "suggestions_made": 0,
                "suggestions_followed": 0,
                "follow_rate": 0.0,
                "success_rate_when_followed": 0.0,
            }
        
        suggestions_made = len(self._guidance_suggestions)
        suggestions_followed = sum(1 for s in self._guidance_suggestions if s.followed)
        follow_rate = suggestions_followed / suggestions_made if suggestions_made > 0 else 0.0
        
        # Success rate when followed
        followed_suggestions = [s for s in self._guidance_suggestions if s.followed and s.outcome is not None]
        success_count = sum(1 for s in followed_suggestions if s.outcome)
        success_rate = success_count / len(followed_suggestions) if followed_suggestions else 0.0
        
        # Overall effectiveness (follow rate * success rate)
        guidance_effectiveness = follow_rate * success_rate if success_rate > 0 else follow_rate * 0.5
        
        return {
            "guidance_effectiveness": guidance_effectiveness,
            "suggestions_made": suggestions_made,
            "suggestions_followed": suggestions_followed,
            "follow_rate": follow_rate,
            "success_rate_when_followed": success_rate,
        }
    
    def get_validation_metrics(self) -> Dict[str, float]:
        """
        Get validation metrics.
        
        Returns:
            Dictionary with validation metrics
        """
        if len(self._validation_records) == 0:
            return {
                "validation_catch_rate": 0.0,
                "block_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_warnings": 0.0,
                "avg_alternatives": 0.0,
            }
        
        total_validations = len(self._validation_records)
        warnings_count = sum(1 for r in self._validation_records if r.warnings_count > 0)
        blocks_count = sum(1 for r in self._validation_records if r.blocked)
        
        catch_rate = warnings_count / total_validations if total_validations > 0 else 0.0
        block_rate = blocks_count / total_validations if total_validations > 0 else 0.0
        
        avg_confidence = sum(r.confidence for r in self._validation_records) / total_validations
        avg_warnings = sum(r.warnings_count for r in self._validation_records) / total_validations
        avg_alternatives = sum(r.alternatives_provided for r in self._validation_records) / total_validations
        
        return {
            "validation_catch_rate": catch_rate,
            "block_rate": block_rate,
            "avg_confidence": avg_confidence,
            "avg_warnings": avg_warnings,
            "avg_alternatives": avg_alternatives,
        }
    
    def get_ranking_metrics(self) -> Dict[str, float]:
        """
        Get ranking accuracy metrics.
        
        Returns:
            Dictionary with ranking metrics
        """
        if len(self._ranking_records) == 0:
            return {
                "ranking_accuracy": 0.0,
                "avg_rank_of_successful_tools": 0.0,
                "correlation_score_rank": 0.0,
            }
        
        # Calculate correlation between rank and success
        successful_tools = [r for r in self._ranking_records if r.outcome is True]
        failed_tools = [r for r in self._ranking_records if r.outcome is False]
        
        if successful_tools:
            avg_rank_successful = sum(r.rank for r in successful_tools) / len(successful_tools)
        else:
            avg_rank_successful = 0.0
        
        if failed_tools:
            avg_rank_failed = sum(r.rank for r in failed_tools) / len(failed_tools)
        else:
            avg_rank_failed = float('inf')
        
        # Ranking accuracy: lower rank (better) for successful tools
        if avg_rank_successful > 0 and avg_rank_failed != float('inf'):
            # Good ranking: successful tools have lower (better) ranks
            ranking_accuracy = max(0.0, 1.0 - (avg_rank_successful / max(avg_rank_failed, avg_rank_successful)))
        else:
            ranking_accuracy = 0.5  # Neutral if no data
        
        # Correlation between score and outcome
        records_with_outcome = [r for r in self._ranking_records if r.outcome is not None]
        if len(records_with_outcome) > 1:
            scores = [r.score for r in records_with_outcome]
            outcomes = [1.0 if r.outcome else 0.0 for r in records_with_outcome]
            
            # Simple correlation (Pearson's r approximation)
            mean_score = sum(scores) / len(scores)
            mean_outcome = sum(outcomes) / len(outcomes)
            
            numerator = sum((s - mean_score) * (o - mean_outcome) for s, o in zip(scores, outcomes))
            score_var = sum((s - mean_score) ** 2 for s in scores)
            outcome_var = sum((o - mean_outcome) ** 2 for o in outcomes)
            
            if score_var > 0 and outcome_var > 0:
                correlation = numerator / (score_var * outcome_var) ** 0.5
                correlation_score_rank = max(0.0, min(1.0, (correlation + 1) / 2))  # Normalize to [0, 1]
            else:
                correlation_score_rank = 0.5
        else:
            correlation_score_rank = 0.5
        
        return {
            "ranking_accuracy": ranking_accuracy,
            "avg_rank_of_successful_tools": avg_rank_successful,
            "correlation_score_rank": correlation_score_rank,
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in a single dictionary.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            "guidance": self.get_effectiveness_metrics(),
            "validation": self.get_validation_metrics(),
            "ranking": self.get_ranking_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def get_tool_metrics(self, tool_name: str) -> Dict[str, Any]:
        """
        Get metrics for a specific tool.
        
        Args:
            tool_name: Tool name
            
        Returns:
            Dictionary with tool-specific metrics
        """
        suggestions = self._suggestions_by_tool.get(tool_name, [])
        validations = self._validations_by_tool.get(tool_name, [])
        rankings = self._rankings_by_tool.get(tool_name, [])
        
        # Guidance metrics for this tool
        suggestions_followed = sum(1 for s in suggestions if s.followed)
        follow_rate = suggestions_followed / len(suggestions) if suggestions else 0.0
        
        # Validation metrics for this tool
        blocks_count = sum(1 for v in validations if v.blocked)
        block_rate = blocks_count / len(validations) if validations else 0.0
        
        # Ranking metrics for this tool
        avg_rank = sum(r.rank for r in rankings) / len(rankings) if rankings else 0.0
        avg_score = sum(r.score for r in rankings) / len(rankings) if rankings else 0.0
        
        return {
            "tool_name": tool_name,
            "suggestions_count": len(suggestions),
            "follow_rate": follow_rate,
            "validations_count": len(validations),
            "block_rate": block_rate,
            "rankings_count": len(rankings),
            "avg_rank": avg_rank,
            "avg_score": avg_score,
        }

