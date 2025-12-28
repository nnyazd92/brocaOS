"""
Learning system integration with cognitive dissonance.

Provides interfaces for converting dissonance metrics into learning signals,
analyzing patterns for dissonance effectiveness, and adapting learning
system feedback based on cognitive dissonance measurements.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from collections import deque, defaultdict

if TYPE_CHECKING:
    from .cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics

logger = logging.getLogger(__name__)


class DissonanceLearningSignalGenerator:
    """
    Converts cognitive dissonance metrics into learning signals.
    
    Maps dissonance to learning rewards:
    - High dissonance → negative reward (avoid patterns)
    - Low dissonance → positive reward (reinforce patterns)
    - Provides reward shaping for reinforcement learning
    """
    
    def __init__(
        self,
        positive_reward_scale: float = 1.0,
        negative_reward_scale: float = -2.0,
        neutral_threshold: float = 0.2
    ):
        """
        Initialize signal generator.
        
        Args:
            positive_reward_scale: Scale factor for positive rewards (low dissonance)
            negative_reward_scale: Scale factor for negative rewards (high dissonance)
            neutral_threshold: Dissonance level below which is considered neutral/positive
        """
        self.positive_reward_scale = positive_reward_scale
        self.negative_reward_scale = negative_reward_scale
        self.neutral_threshold = neutral_threshold
        
        logger.info("Initialized DissonanceLearningSignalGenerator")
    
    def generate_reward(
        self,
        dissonance_metrics: "DissonanceMetrics",
        previous_dissonance: Optional[float] = None
    ) -> float:
        """
        Generate learning reward from dissonance metrics.
        
        Args:
            dissonance_metrics: Current dissonance metrics
            previous_dissonance: Previous overall dissonance (for trend-based rewards)
            
        Returns:
            Reward signal: positive for low/improving dissonance, negative for high/worsening
        """
        overall_dissonance = dissonance_metrics.overall_dissonance
        
        # Base reward: low dissonance = positive, high dissonance = negative
        if overall_dissonance < self.neutral_threshold:
            base_reward = self.positive_reward_scale * (1.0 - overall_dissonance / self.neutral_threshold)
        else:
            base_reward = self.negative_reward_scale * (overall_dissonance - self.neutral_threshold) / (1.0 - self.neutral_threshold)
        
        # Trend bonus: reward improvement, penalize worsening
        trend_bonus = 0.0
        if previous_dissonance is not None:
            dissonance_change = previous_dissonance - overall_dissonance  # Positive = improvement
            trend_bonus = dissonance_change * 2.0  # Amplify trend signal
        
        total_reward = base_reward + trend_bonus
        
        logger.debug(
            f"Generated reward: {total_reward:.3f} "
            f"(dissonance: {overall_dissonance:.3f}, trend: {trend_bonus:+.3f})"
        )
        
        return total_reward
    
    def generate_component_rewards(self, dissonance_metrics: "DissonanceMetrics") -> Dict[str, float]:
        """
        Generate component-specific rewards for different dissonance dimensions.
        
        Args:
            dissonance_metrics: Current dissonance metrics
            
        Returns:
            Dictionary mapping component names to reward signals
        """
        rewards = {
            "logical": self._component_reward(dissonance_metrics.logical_dissonance),
            "factual": self._component_reward(dissonance_metrics.factual_dissonance),
            "behavioral": self._component_reward(dissonance_metrics.behavioral_dissonance),
            "goal": self._component_reward(dissonance_metrics.goal_dissonance)
        }
        
        return rewards
    
    def _component_reward(self, component_dissonance: float) -> float:
        """Generate reward for a single component."""
        if component_dissonance < self.neutral_threshold:
            return self.positive_reward_scale * (1.0 - component_dissonance / self.neutral_threshold)
        else:
            return self.negative_reward_scale * (component_dissonance - self.neutral_threshold) / (1.0 - self.neutral_threshold)


class PatternDissonanceAnalyzer:
    """
    Analyzes which patterns reduce or increase dissonance.
    
    Tracks pattern effectiveness over time and identifies:
    - Patterns that consistently reduce dissonance (reinforce)
    - Patterns that consistently increase dissonance (avoid)
    - Context-dependent pattern effectiveness
    """
    
    def __init__(self, history_window: int = 100):
        """
        Initialize pattern analyzer.
        
        Args:
            history_window: Number of pattern observations to track
        """
        self.history_window = history_window
        
        # Track pattern effectiveness: pattern_id -> list of (dissonance_before, dissonance_after, timestamp)
        self.pattern_effectiveness: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_window))
        
        # Track pattern application contexts
        self.pattern_contexts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        logger.info("Initialized PatternDissonanceAnalyzer")
    
    def record_pattern_application(
        self,
        pattern_id: str,
        dissonance_before: float,
        dissonance_after: float,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Record the effect of applying a pattern on dissonance.
        
        Args:
            pattern_id: Identifier for the pattern/procedure/skill
            dissonance_before: Dissonance level before pattern application
            dissonance_after: Dissonance level after pattern application
            context: Optional context in which pattern was applied
        """
        effectiveness = dissonance_before - dissonance_after  # Positive = reduction (good)
        
        self.pattern_effectiveness[pattern_id].append({
            "timestamp": datetime.now(timezone.utc),
            "dissonance_before": dissonance_before,
            "dissonance_after": dissonance_after,
            "effectiveness": effectiveness
        })
        
        if context:
            self.pattern_contexts[pattern_id].append(context)
            # Keep only recent contexts
            if len(self.pattern_contexts[pattern_id]) > self.history_window:
                self.pattern_contexts[pattern_id] = self.pattern_contexts[pattern_id][-self.history_window:]
        
        logger.debug(
            f"Recorded pattern '{pattern_id}' effectiveness: {effectiveness:+.3f} "
            f"({dissonance_before:.3f} → {dissonance_after:.3f})"
        )
    
    def get_pattern_effectiveness(self, pattern_id: str) -> Dict[str, Any]:
        """
        Get effectiveness statistics for a pattern.
        
        Args:
            pattern_id: Pattern identifier
            
        Returns:
            Dictionary with effectiveness metrics
        """
        if pattern_id not in self.pattern_effectiveness or len(self.pattern_effectiveness[pattern_id]) == 0:
            return {
                "average_effectiveness": 0.0,
                "total_applications": 0,
                "positive_count": 0,
                "negative_count": 0,
                "reduction_rate": 0.0
            }
        
        observations = list(self.pattern_effectiveness[pattern_id])
        
        avg_effectiveness = sum(obs["effectiveness"] for obs in observations) / len(observations)
        positive_count = sum(1 for obs in observations if obs["effectiveness"] > 0.0)
        negative_count = sum(1 for obs in observations if obs["effectiveness"] < 0.0)
        reduction_rate = positive_count / len(observations) if observations else 0.0
        
        return {
            "average_effectiveness": avg_effectiveness,
            "total_applications": len(observations),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "reduction_rate": reduction_rate
        }
    
    def is_pattern_effective(self, pattern_id: str, threshold: float = 0.0) -> bool:
        """
        Check if a pattern is effective (reduces dissonance on average).
        
        Args:
            pattern_id: Pattern identifier
            threshold: Minimum average effectiveness to be considered effective
            
        Returns:
            True if pattern is effective
        """
        stats = self.get_pattern_effectiveness(pattern_id)
        return stats["average_effectiveness"] > threshold
    
    def get_most_effective_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get patterns ranked by effectiveness.
        
        Args:
            limit: Maximum number of patterns to return
            
        Returns:
            List of pattern effectiveness records sorted by average effectiveness
        """
        patterns = []
        
        for pattern_id in self.pattern_effectiveness.keys():
            stats = self.get_pattern_effectiveness(pattern_id)
            if stats["total_applications"] > 0:
                patterns.append({
                    "pattern_id": pattern_id,
                    **stats
                })
        
        # Sort by average effectiveness (descending)
        patterns.sort(key=lambda x: x["average_effectiveness"], reverse=True)
        
        return patterns[:limit]
    
    def get_least_effective_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get patterns ranked by ineffectiveness (for removal/avoidance).
        
        Args:
            limit: Maximum number of patterns to return
            
        Returns:
            List of pattern effectiveness records sorted by average effectiveness (ascending)
        """
        patterns = []
        
        for pattern_id in self.pattern_effectiveness.keys():
            stats = self.get_pattern_effectiveness(pattern_id)
            if stats["total_applications"] > 0:
                patterns.append({
                    "pattern_id": pattern_id,
                    **stats
                })
        
        # Sort by average effectiveness (ascending)
        patterns.sort(key=lambda x: x["average_effectiveness"])
        
        return patterns[:limit]


class LearningFeedbackAdapter:
    """
    Adapts learning system feedback from cognitive dissonance.
    
    Provides interfaces for:
    - Converting dissonance metrics to learning feedback
    - Adjusting learning parameters based on dissonance
    - Filtering learning suggestions by dissonance effectiveness
    """
    
    def __init__(
        self,
        signal_generator: Optional[DissonanceLearningSignalGenerator] = None,
        pattern_analyzer: Optional[PatternDissonanceAnalyzer] = None
    ):
        """
        Initialize feedback adapter.
        
        Args:
            signal_generator: Optional signal generator (creates default if None)
            pattern_analyzer: Optional pattern analyzer (creates default if None)
        """
        self.signal_generator = signal_generator or DissonanceLearningSignalGenerator()
        self.pattern_analyzer = pattern_analyzer or PatternDissonanceAnalyzer()
        
        logger.info("Initialized LearningFeedbackAdapter")
    
    def adapt_learning_suggestions(
        self,
        suggestions: List[Dict[str, Any]],
        current_dissonance: Optional[float] = None,
        emotional_context: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Adapt learning suggestions based on dissonance and emotional context.
        
        Args:
            suggestions: List of learning suggestions (procedures, skills, etc.)
            current_dissonance: Current dissonance level (optional, for prioritization)
            emotional_context: Optional emotional state dictionary
            
        Returns:
            Filtered and prioritized suggestions
        """
        if not suggestions:
            return []
        
        adapted = []
        
        for suggestion in suggestions:
            pattern_id = suggestion.get("name") or suggestion.get("pattern_id") or str(id(suggestion))
            
            # Get pattern effectiveness if available
            effectiveness_stats = self.pattern_analyzer.get_pattern_effectiveness(pattern_id)
            
            # Filter out ineffective patterns if dissonance is high
            if current_dissonance and current_dissonance > 0.5:
                if effectiveness_stats["average_effectiveness"] < -0.1:  # Pattern increases dissonance
                    continue  # Skip this suggestion
            
            # Add effectiveness score to suggestion
            adapted_suggestion = suggestion.copy()
            adapted_suggestion["dissonance_effectiveness"] = effectiveness_stats["average_effectiveness"]
            adapted_suggestion["dissonance_reduction_rate"] = effectiveness_stats["reduction_rate"]
            
            # Boost priority for effective patterns
            priority = suggestion.get("priority", 0.5)
            if effectiveness_stats["average_effectiveness"] > 0.0:
                priority += 0.2 * effectiveness_stats["average_effectiveness"]  # Boost by effectiveness
            elif effectiveness_stats["average_effectiveness"] < 0.0:
                priority += 0.5 * effectiveness_stats["average_effectiveness"]  # Penalize by ineffectiveness
            
            # Adjust priority based on emotional context
            if emotional_context:
                valence = emotional_context.get("valence", 0.0)
                # If negative valence, prefer patterns that reduce dissonance (emotionally beneficial)
                if valence < -0.3 and effectiveness_stats["average_effectiveness"] > 0.0:
                    priority += 0.1  # Additional boost for emotionally beneficial patterns
                # If positive valence, maintain standards (don't over-prioritize)
                elif valence > 0.3:
                    priority *= 0.95  # Slight reduction to maintain standards
            
            adapted_suggestion["priority"] = min(1.0, max(0.0, priority))
            adapted.append(adapted_suggestion)
        
        # Sort by adapted priority
        adapted.sort(key=lambda x: x.get("priority", 0.0), reverse=True)
        
        return adapted
    
    def generate_learning_feedback(
        self,
        dissonance_before: float,
        dissonance_after: float,
        applied_pattern_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate learning feedback from dissonance change.
        
        Args:
            dissonance_before: Dissonance before action
            dissonance_after: Dissonance after action
            applied_pattern_id: Optional pattern/procedure/skill ID that was applied
            context: Optional context
            
        Returns:
            Dictionary with learning feedback information
        """
        dissonance_change = dissonance_before - dissonance_after  # Positive = reduction (good)
        
        # Generate reward signal
        from .cognitive_dissonance import DissonanceMetrics
        metrics_after = DissonanceMetrics(
            timestamp=datetime.now(timezone.utc),
            overall_dissonance=dissonance_after
        )
        reward = self.signal_generator.generate_reward(metrics_after, dissonance_before)
        
        feedback = {
            "dissonance_before": dissonance_before,
            "dissonance_after": dissonance_after,
            "dissonance_change": dissonance_change,
            "reward": reward,
            "success": dissonance_change > 0.0,  # Reduction is success
            "improvement_magnitude": abs(dissonance_change)
        }
        
        # Record pattern effectiveness if pattern ID provided
        if applied_pattern_id:
            self.pattern_analyzer.record_pattern_application(
                pattern_id=applied_pattern_id,
                dissonance_before=dissonance_before,
                dissonance_after=dissonance_after,
                context=context
            )
            feedback["pattern_id"] = applied_pattern_id
        
        return feedback

