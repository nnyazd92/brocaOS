"""
Feedback loop system for reasoning.

Implements reinforcing (positive) and balancing (negative) feedback loops
to continuously improve reasoning performance.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics
    from .rl_signals import RLSignalAggregator, RLSignalMetrics
    from ..learning.integration_tool import LearningTool
    from ..internal_sensing.affective_state import ComputationalAffectMonitor
    from ..internal_sensing.predictive_interoception import PredictiveInteroception

logger = logging.getLogger(__name__)


@dataclass
class CycleMetrics:
    """Metrics for a reasoning cycle."""
    cycle_number: int
    timestamp: datetime
    duration: float
    rules_fired: int
    rules_successful: int = 0
    rules_failed: int = 0
    goals_processed: int = 0
    goals_completed: int = 0
    memory_retrievals: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate for rules."""
        if self.rules_fired == 0:
            return 0.0
        return self.rules_successful / self.rules_fired
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.rules_fired == 0:
            return 0.0
        return self.rules_failed / self.rules_fired


@dataclass
class FeedbackMetrics:
    """Aggregated feedback metrics."""
    window_size: int
    success_rate: float = 0.0
    error_rate: float = 0.0
    avg_cycle_duration: float = 0.0
    goal_completion_rate: float = 0.0
    rule_effectiveness: Dict[str, float] = field(default_factory=dict)
    goal_progress_trends: Dict[str, float] = field(default_factory=dict)
    memory_retrieval_effectiveness: float = 0.0
    # Cognitive dissonance metrics
    overall_dissonance: float = 0.0
    logical_dissonance: float = 0.0
    factual_dissonance: float = 0.0
    behavioral_dissonance: float = 0.0
    goal_dissonance: float = 0.0
    dissonance_trend: str = "stable"  # "increasing", "decreasing", "stable"
    has_sufficient_dissonance_data: bool = False  # True only when real measurements exist


class FeedbackLoopManager:
    """
    Manages feedback loops for reasoning system.
    
    Implements:
    - Reinforcing loops: Boost successful patterns
    - Balancing loops: Correct deviations, maintain stability
    - Metrics tracking: Monitor performance over time
    """
    
    def __init__(
        self,
        reinforcing_enabled: bool = True,
        balancing_enabled: bool = True,
        metrics_window_size: int = 100,
        success_rate_threshold: float = 0.7,
        error_rate_threshold: float = 0.3,
        cognitive_dissonance_monitor: Optional["CognitiveDissonanceMonitor"] = None,
        dissonance_threshold: float = 0.3,
        learning_system: Optional["LearningTool"] = None,
        rl_signal_aggregator: Optional["RLSignalAggregator"] = None,
        rl_signals_enabled: bool = True,
        surprise_threshold: float = 0.3,
        curiosity_threshold: float = 0.5,
        exploration_ratio: float = 0.6
    ):
        """
        Initialize feedback loop manager.
        
        Args:
            reinforcing_enabled: Enable reinforcing feedback loops
            balancing_enabled: Enable balancing feedback loops
            metrics_window_size: Number of cycles to track for metrics
            success_rate_threshold: Threshold for successful performance
            error_rate_threshold: Threshold for error detection
            cognitive_dissonance_monitor: Optional CognitiveDissonanceMonitor for tracking dissonance
            dissonance_threshold: Threshold for triggering dissonance-based corrections
            learning_system: Optional LearningTool for learning-reasoning integration
            rl_signal_aggregator: Optional RLSignalAggregator for multi-signal RL feedback
            rl_signals_enabled: Enable multi-signal RL feedback (default: True)
            surprise_threshold: Threshold for surprise-based feedback
            curiosity_threshold: Threshold for curiosity-based feedback
            exploration_ratio: Balance between exploration and exploitation
        """
        self.reinforcing_enabled = reinforcing_enabled
        self.balancing_enabled = balancing_enabled
        self.metrics_window_size = metrics_window_size
        self.success_rate_threshold = success_rate_threshold
        self.error_rate_threshold = error_rate_threshold
        self.cognitive_dissonance_monitor = cognitive_dissonance_monitor
        self.dissonance_threshold = dissonance_threshold
        self.learning_system = learning_system
        self.rl_signal_aggregator = rl_signal_aggregator
        self.rl_signals_enabled = rl_signals_enabled
        self.surprise_threshold = surprise_threshold
        self.curiosity_threshold = curiosity_threshold
        self.exploration_ratio = exploration_ratio
        
        # Metrics tracking
        self.metrics_history: deque = deque(maxlen=metrics_window_size)
        self.cycle_number = 0
        
        # Rule effectiveness tracking
        self.rule_effectiveness: Dict[str, Dict[str, Any]] = {}  # rule_name -> {successes, failures, strength_boost}
        
        # Goal progress tracking
        self.goal_progress_history: Dict[str, List[float]] = {}  # goal_name -> [progress values]
        
        logger.info(f"Initialized FeedbackLoopManager (RL signals: {'enabled' if rl_signals_enabled else 'disabled'})")
    
    def evaluate_cycle_outcomes(self, cycle_outcome: Dict[str, Any]) -> FeedbackMetrics:
        """
        Evaluate cycle outcomes and compute metrics.
        
        Args:
            cycle_outcome: Dictionary with cycle results
            
        Returns:
            FeedbackMetrics with computed metrics
        """
        self.cycle_number += 1
        
        # Extract cycle data
        duration = cycle_outcome.get("duration", 0.0)
        rules_fired = cycle_outcome.get("rules_fired", 0)
        results = cycle_outcome.get("results", [])
        goals_processed = cycle_outcome.get("goals_processed", 0)
        
        # Analyze results to determine success/failure
        rules_successful = 0
        rules_failed = 0
        errors = []
        
        for result in results:
            if result.get("type") == "error" or "error" in result:
                rules_failed += 1
                errors.append(result.get("error", "Unknown error"))
            else:
                rules_successful += 1
        
        # Create metrics
        metrics = CycleMetrics(
            cycle_number=self.cycle_number,
            timestamp=datetime.now(timezone.utc),
            duration=duration,
            rules_fired=rules_fired,
            rules_successful=rules_successful,
            rules_failed=rules_failed,
            goals_processed=goals_processed,
            errors=errors
        )
        
        # Add to history
        self.metrics_history.append(metrics)
        
        # Compute aggregated metrics
        return self._compute_aggregated_metrics()
    
    def apply_feedback(
        self,
        metrics: FeedbackMetrics,
        emotional_state: Optional[Dict[str, float]] = None
    ):
        """
        Apply feedback loops based on metrics and emotional state.
        
        Args:
            metrics: Computed feedback metrics
            emotional_state: Optional current emotional state dictionary
        """
        # Adjust feedback parameters based on emotional state
        if emotional_state:
            self._adjust_feedback_by_emotion(metrics, emotional_state)
        
        if self.reinforcing_enabled:
            self._apply_reinforcing_feedback(metrics, emotional_state)
        
        if self.balancing_enabled:
            self._apply_balancing_feedback(metrics, emotional_state)
        
        # Apply RL-based feedback (multi-signal or dissonance-only)
        if self.rl_signals_enabled and self.rl_signal_aggregator:
            self._apply_rl_feedback(metrics, emotional_state)
        else:
            # Fallback to dissonance-only feedback for backward compatibility
            self._apply_dissonance_feedback(metrics)
    
    def _compute_aggregated_metrics(self) -> FeedbackMetrics:
        """Compute aggregated metrics from history."""
        if not self.metrics_history:
            return FeedbackMetrics(window_size=self.metrics_window_size)
        
        # Aggregate success/error rates
        total_rules = sum(m.rules_fired for m in self.metrics_history)
        total_successful = sum(m.rules_successful for m in self.metrics_history)
        total_failed = sum(m.rules_failed for m in self.metrics_history)
        
        success_rate = total_successful / total_rules if total_rules > 0 else 0.0
        error_rate = total_failed / total_rules if total_rules > 0 else 0.0
        
        # Average cycle duration
        avg_duration = sum(m.duration for m in self.metrics_history) / len(self.metrics_history)
        
        # Goal completion rate
        total_goals = sum(m.goals_processed for m in self.metrics_history)
        total_completed = sum(m.goals_completed for m in self.metrics_history)
        goal_completion_rate = total_completed / total_goals if total_goals > 0 else 0.0
        
        # Rule effectiveness (from tracked rules)
        rule_effectiveness = {}
        for rule_name, stats in self.rule_effectiveness.items():
            total = stats.get("successes", 0) + stats.get("failures", 0)
            if total > 0:
                rule_effectiveness[rule_name] = stats.get("successes", 0) / total
        
        # Goal progress trends
        goal_trends = {}
        for goal_name, progress_history in self.goal_progress_history.items():
            if len(progress_history) >= 2:
                # Calculate trend (positive = improving, negative = declining)
                trend = progress_history[-1] - progress_history[0]
                goal_trends[goal_name] = trend
        
        # Cognitive dissonance metrics (if available)
        overall_dissonance = 0.0
        logical_dissonance = 0.0
        factual_dissonance = 0.0
        behavioral_dissonance = 0.0
        goal_dissonance = 0.0
        dissonance_trend = "stable"
        has_sufficient_dissonance_data = False
        
        if self.cognitive_dissonance_monitor:
            dissonance_data = self.cognitive_dissonance_monitor.get_aggregated_dissonance()
            # Check if we have sufficient data - must have both has_data AND has_sufficient_data
            has_data = dissonance_data.get("has_data", False)
            has_sufficient_data = dissonance_data.get("has_sufficient_data", False)
            
            if not has_data or not has_sufficient_data:
                # Insufficient data - use 0.0 (neutral) and mark as insufficient
                # Do NOT log warnings - this is expected when no measurements exist yet
                overall_dissonance = 0.0
                logical_dissonance = 0.0
                factual_dissonance = 0.0
                behavioral_dissonance = 0.0
                goal_dissonance = 0.0
                has_sufficient_dissonance_data = False
            else:
                # We have real measurements - use them
                overall_dissonance = dissonance_data.get("overall_dissonance", 0.0)
                logical_dissonance = dissonance_data.get("logical_dissonance", 0.0)
                factual_dissonance = dissonance_data.get("factual_dissonance", 0.0)
                behavioral_dissonance = dissonance_data.get("behavioral_dissonance", 0.0)
                goal_dissonance = dissonance_data.get("goal_dissonance", 0.0)
                has_sufficient_dissonance_data = True
            
            trend_analysis = self.cognitive_dissonance_monitor.get_trend_analysis()
            dissonance_trend = trend_analysis.get("trend", "stable")
        
        return FeedbackMetrics(
            window_size=len(self.metrics_history),
            success_rate=success_rate,
            error_rate=error_rate,
            avg_cycle_duration=avg_duration,
            goal_completion_rate=goal_completion_rate,
            rule_effectiveness=rule_effectiveness,
            goal_progress_trends=goal_trends,
            overall_dissonance=overall_dissonance,
            logical_dissonance=logical_dissonance,
            factual_dissonance=factual_dissonance,
            behavioral_dissonance=behavioral_dissonance,
            goal_dissonance=goal_dissonance,
            dissonance_trend=dissonance_trend,
            has_sufficient_dissonance_data=has_sufficient_dissonance_data
        )
    
    def _apply_reinforcing_feedback(
        self,
        metrics: FeedbackMetrics,
        emotional_state: Optional[Dict[str, float]] = None
    ):
        """Apply reinforcing (positive) feedback loops."""
        # Amplify with learning system if available
        if self.learning_system:
            self._amplify_with_learning(metrics)
        
        # Adjust by emotional state: stronger reinforcement if positive valence
        if emotional_state:
            valence = emotional_state.get("valence", 0.0)
            if valence > 0.3:
                # Positive emotions strengthen reinforcing feedback
                logger.debug(f"Positive valence ({valence:.2f}) strengthens reinforcing feedback")
        
        # Reinforce successful rules
        for rule_name, effectiveness in metrics.rule_effectiveness.items():
            if effectiveness >= self.success_rate_threshold:
                # Boost rule strength
                self._boost_rule_strength(rule_name, boost_amount=0.1 * effectiveness)
                logger.debug(f"Reinforced rule '{rule_name}' (effectiveness: {effectiveness:.2f})")
        
        # Reinforce successful goal patterns
        for goal_name, trend in metrics.goal_progress_trends.items():
            if trend > 0.1:  # Positive progress trend
                self._boost_goal_priority(goal_name, boost_amount=0.05)
                logger.debug(f"Reinforced goal '{goal_name}' (trend: {trend:.2f})")
        
        # If overall success rate is high, maintain current strategies
        if metrics.success_rate >= self.success_rate_threshold:
            logger.debug(f"High success rate ({metrics.success_rate:.2f}), maintaining strategies")
        
        # Reinforce successful rules
        for rule_name, effectiveness in metrics.rule_effectiveness.items():
            if effectiveness >= self.success_rate_threshold:
                # Boost rule strength
                self._boost_rule_strength(rule_name, boost_amount=0.1 * effectiveness)
                logger.debug(f"Reinforced rule '{rule_name}' (effectiveness: {effectiveness:.2f})")
        
        # Reinforce successful goal patterns
        for goal_name, trend in metrics.goal_progress_trends.items():
            if trend > 0.1:  # Positive progress trend
                self._boost_goal_priority(goal_name, boost_amount=0.05)
                logger.debug(f"Reinforced goal '{goal_name}' (trend: {trend:.2f})")
        
        # If overall success rate is high, maintain current strategies
        if metrics.success_rate >= self.success_rate_threshold:
            logger.debug(f"High success rate ({metrics.success_rate:.2f}), maintaining strategies")
    
    def _apply_balancing_feedback(
        self,
        metrics: FeedbackMetrics,
        emotional_state: Optional[Dict[str, float]] = None
    ):
        """Apply balancing (negative) feedback loops."""
        # Adjust by emotional state: stronger balancing if negative valence
        if emotional_state:
            valence = emotional_state.get("valence", 0.0)
            if valence < -0.3:
                # Negative emotions strengthen balancing feedback (corrective action)
                logger.debug(f"Negative valence ({valence:.2f}) strengthens balancing feedback")
        
        # Detect and correct error patterns
        if metrics.error_rate > self.error_rate_threshold:
            logger.warning(f"High error rate detected ({metrics.error_rate:.2f}), applying corrections")
            self._reduce_error_prone_rules(metrics)
            self._trigger_strategy_reassessment()
        
        # Detect performance degradation
        if metrics.avg_cycle_duration > 5.0:  # Cycles taking too long
            logger.warning(f"Slow cycle performance ({metrics.avg_cycle_duration:.2f}s), adjusting")
            self._adjust_performance_parameters()
        
        # Detect goal stagnation
        for goal_name, trend in metrics.goal_progress_trends.items():
            if trend < -0.1:  # Negative progress trend
                logger.warning(f"Goal '{goal_name}' showing negative trend ({trend:.2f})")
                self._suggest_goal_revision(goal_name)
        # Detect and correct error patterns
        if metrics.error_rate > self.error_rate_threshold:
            logger.warning(f"High error rate detected ({metrics.error_rate:.2f}), applying corrections")
            self._reduce_error_prone_rules(metrics)
            self._trigger_strategy_reassessment()
        
        # Detect performance degradation
        if metrics.avg_cycle_duration > 5.0:  # Cycles taking too long
            logger.warning(f"Slow cycle performance ({metrics.avg_cycle_duration:.2f}s), adjusting")
            self._adjust_performance_parameters()
        
        # Detect goal stagnation
        for goal_name, trend in metrics.goal_progress_trends.items():
            if trend < -0.1:  # Negative progress trend
                logger.warning(f"Goal '{goal_name}' showing negative trend ({trend:.2f})")
                self._suggest_goal_revision(goal_name)
    
    def _boost_rule_strength(self, rule_name: str, boost_amount: float):
        """Boost strength of a rule."""
        if rule_name not in self.rule_effectiveness:
            self.rule_effectiveness[rule_name] = {
                "successes": 0,
                "failures": 0,
                "strength_boost": 0.0
            }
        
        self.rule_effectiveness[rule_name]["strength_boost"] += boost_amount
        # Cap boost at reasonable level
        self.rule_effectiveness[rule_name]["strength_boost"] = min(
            2.0, self.rule_effectiveness[rule_name]["strength_boost"]
        )
    
    def _boost_goal_priority(self, goal_name: str, boost_amount: float):
        """Boost priority of a goal."""
        # This would need access to goal manager
        # For now, just track it
        logger.debug(f"Would boost goal '{goal_name}' priority by {boost_amount}")
    
    def _reduce_error_prone_rules(self, metrics: FeedbackMetrics):
        """Reduce strength/priority of error-prone rules."""
        for rule_name, effectiveness in metrics.rule_effectiveness.items():
            if effectiveness < 0.3:  # Low effectiveness
                if rule_name in self.rule_effectiveness:
                    self.rule_effectiveness[rule_name]["strength_boost"] -= 0.1
                    self.rule_effectiveness[rule_name]["strength_boost"] = max(
                        -1.0, self.rule_effectiveness[rule_name]["strength_boost"]
                    )
                    logger.debug(f"Reduced strength for error-prone rule '{rule_name}'")
    
    def _trigger_strategy_reassessment(self):
        """Trigger reassessment of reasoning strategies."""
        logger.info("Triggering strategy reassessment due to high error rate")
        # This could trigger goal decomposition, rule revision, etc.
    
    def _adjust_performance_parameters(self):
        """Adjust performance-related parameters."""
        logger.info("Adjusting performance parameters due to slow cycles")
        # This could adjust working memory capacity, rule limits, etc.
    
    def _suggest_goal_revision(self, goal_name: str):
        """Suggest revision or decomposition of a goal."""
        logger.info(f"Suggesting revision for goal '{goal_name}' due to stagnation")
        # This could trigger goal decomposition or revision
    
    def _apply_rl_feedback(
        self,
        metrics: FeedbackMetrics,
        emotional_state: Optional[Dict[str, float]] = None
    ):
        """
        Apply multi-signal RL feedback based on all available signals.
        
        Uses composite reward from dissonance, surprise, curiosity, info gain, and coherence.
        """
        if not self.rl_signal_aggregator:
            # Fallback to dissonance-only
            self._apply_dissonance_feedback(metrics)
            return
        
        try:
            # Compute all RL signals
            rl_metrics = self.rl_signal_aggregator.compute_signals(
                affective_state=emotional_state
            )
            
            # Apply signal-specific feedback
            self._apply_surprise_feedback(rl_metrics, metrics)
            self._apply_curiosity_feedback(rl_metrics, metrics)
            self._apply_info_gain_feedback(rl_metrics, metrics)
            self._apply_coherence_feedback(rl_metrics, metrics)
            self._apply_dissonance_feedback_from_rl(rl_metrics, metrics)
            
            # Use composite reward for overall strategy
            if rl_metrics.composite_reward > 0.7:
                logger.debug(f"High composite reward ({rl_metrics.composite_reward:.3f}), reinforcing strategies")
            elif rl_metrics.composite_reward < 0.3:
                logger.warning(f"Low composite reward ({rl_metrics.composite_reward:.3f}), triggering corrections")
                self._trigger_rl_corrections(rl_metrics, metrics)
            
            # Check exploration-exploitation balance
            balance = rl_metrics.get_exploration_exploitation_balance()
            if balance >= self.exploration_ratio:
                logger.debug(f"High exploration balance ({balance:.3f}), encouraging exploration")
            else:
                logger.debug(f"High exploitation balance ({balance:.3f}), focusing on known strategies")
                
        except Exception as e:
            logger.warning(f"Error applying RL feedback, falling back to dissonance-only: {e}", exc_info=True)
            self._apply_dissonance_feedback(metrics)
    
    def _apply_surprise_feedback(
        self,
        rl_metrics: "RLSignalMetrics",
        metrics: FeedbackMetrics
    ):
        """Apply feedback based on surprise signal (minimize surprise)."""
        surprise = 1.0 - rl_metrics.surprise_reward  # Convert reward back to surprise
        
        if surprise > self.surprise_threshold:
            logger.warning(f"High surprise detected ({surprise:.3f}), improving prediction models")
            # Trigger prediction model improvements
            # This could trigger:
            # - Update predictive interoception models
            # - Adjust prediction strategies
            # - Increase attention to prediction errors
    
    def _apply_curiosity_feedback(
        self,
        rl_metrics: "RLSignalMetrics",
        metrics: FeedbackMetrics
    ):
        """Apply feedback based on curiosity signal (maximize curiosity for exploration)."""
        curiosity = rl_metrics.curiosity_reward
        
        if curiosity > self.curiosity_threshold:
            logger.debug(f"High curiosity ({curiosity:.3f}), encouraging exploration")
            # Encourage exploration behaviors:
            # - Explore novel states/actions
            # - Try new strategies
            # - Seek information-rich experiences
        elif curiosity < 0.2:
            logger.debug(f"Low curiosity ({curiosity:.3f}), focusing on exploitation")
            # Focus on known successful strategies
    
    def _apply_info_gain_feedback(
        self,
        rl_metrics: "RLSignalMetrics",
        metrics: FeedbackMetrics
    ):
        """Apply feedback based on information gain signal."""
        info_gain = rl_metrics.information_gain_reward
        
        if info_gain > 0.5:
            logger.debug(f"High information gain ({info_gain:.3f}), reinforcing learning behaviors")
            # Reinforce information-acquiring behaviors:
            # - Boost strategies that lead to new knowledge
            # - Encourage verification of uncertain knowledge
        elif info_gain < 0.1:
            logger.debug(f"Low information gain ({info_gain:.3f}), knowledge is stable")
    
    def _apply_coherence_feedback(
        self,
        rl_metrics: "RLSignalMetrics",
        metrics: FeedbackMetrics
    ):
        """Apply feedback based on coherence signal."""
        coherence = rl_metrics.coherence_reward
        
        if coherence < 0.3:
            logger.warning(f"Low coherence ({coherence:.3f}), triggering contradiction resolution")
            # Trigger coherence improvements:
            # - Resolve contradictions
            # - Update self-model for consistency
            # - Improve logical consistency
        elif coherence > 0.7:
            logger.debug(f"High coherence ({coherence:.3f}), maintaining consistency")
    
    def _apply_dissonance_feedback_from_rl(
        self,
        rl_metrics: "RLSignalMetrics",
        metrics: FeedbackMetrics
    ):
        """Apply dissonance feedback using RL signal (for consistency with multi-signal approach)."""
        # CRITICAL: Only process dissonance feedback if we have sufficient real data
        if not metrics.has_sufficient_dissonance_data:
            return
        
        dissonance_reward = rl_metrics.dissonance_reward
        dissonance = 1.0 - dissonance_reward  # Convert reward back to dissonance
        
        if dissonance < self.dissonance_threshold:
            logger.debug(f"Low dissonance ({dissonance:.3f}), maintaining strategies")
        elif dissonance > self.dissonance_threshold:
            logger.warning(
                f"High cognitive dissonance detected ({dissonance:.3f}), "
                f"trend: {metrics.dissonance_trend}"
            )
            self._trigger_dissonance_corrections(metrics)
    
    def _trigger_rl_corrections(
        self,
        rl_metrics: "RLSignalMetrics",
        metrics: FeedbackMetrics
    ):
        """Trigger corrections based on low composite reward."""
        logger.info(
            f"Triggering RL corrections: composite_reward={rl_metrics.composite_reward:.3f}, "
            f"dissonance={1.0 - rl_metrics.dissonance_reward:.3f}, "
            f"surprise={1.0 - rl_metrics.surprise_reward:.3f}, "
            f"curiosity={rl_metrics.curiosity_reward:.3f}, "
            f"info_gain={rl_metrics.information_gain_reward:.3f}, "
            f"coherence={rl_metrics.coherence_reward:.3f}"
        )
        
        # Could trigger:
        # - Self-model updates (if dissonance/coherence low)
        # - Prediction model improvements (if surprise high)
        # - Strategy reassessment (if composite reward low)
        # - Goal revision (if multiple signals indicate problems)
    
    def _apply_dissonance_feedback(self, metrics: FeedbackMetrics):
        """Apply feedback based on cognitive dissonance metrics (backward compatibility)."""
        if not self.cognitive_dissonance_monitor:
            return
        
        # CRITICAL: Only process dissonance feedback if we have sufficient real data
        # Skip entirely if data is insufficient (no warnings, no corrections)
        if not metrics.has_sufficient_dissonance_data:
            return
        
        # When dissonance is low, maintain current strategies (reinforcing)
        if metrics.overall_dissonance < self.dissonance_threshold:
            logger.debug(f"Low dissonance ({metrics.overall_dissonance:.3f}), maintaining strategies")
            return
        
        # When dissonance is high, trigger corrections (balancing)
        if metrics.overall_dissonance > self.dissonance_threshold:
            logger.warning(
                f"High cognitive dissonance detected ({metrics.overall_dissonance:.3f}), "
                f"trend: {metrics.dissonance_trend}"
            )
            self._trigger_dissonance_corrections(metrics)
    
    def _trigger_dissonance_corrections(self, metrics: FeedbackMetrics):
        """Trigger corrections when dissonance is high."""
        # This will be connected to self-model update system
        # For now, log the need for correction
        logger.info(
            f"Triggering dissonance corrections: "
            f"overall={metrics.overall_dissonance:.3f}, "
            f"logical={metrics.logical_dissonance:.3f}, "
            f"factual={metrics.factual_dissonance:.3f}, "
            f"behavioral={metrics.behavioral_dissonance:.3f}, "
            f"goal={metrics.goal_dissonance:.3f}"
        )
        
        # Could trigger:
        # - Self-model updates
        # - Strategy reassessment
        # - Goal revision
        # - Rule adjustments
    
    def _amplify_with_learning(self, metrics: FeedbackMetrics):
        """
        Amplify feedback loops using learning system insights.
        
        Uses learned patterns and skills to enhance feedback effectiveness.
        """
        if not self.learning_system:
            return
        
        try:
            # Get learned patterns that correlate with low dissonance
            if hasattr(metrics, 'overall_dissonance') and metrics.overall_dissonance < self.dissonance_threshold:
                # Low dissonance: reinforce successful patterns
                # Get applicable procedures/skills from learning system
                context = {
                    "dissonance": metrics.overall_dissonance,
                    "success_rate": metrics.success_rate,
                    "error_rate": metrics.error_rate
                }
                
                # Get learning suggestions that reduce dissonance
                suggestions = self.learning_system.execute("get_learning_suggestions", context=context)
                
                if suggestions.get("success") and suggestions.get("suggestions"):
                    logger.debug(f"Learning system suggests {len(suggestions['suggestions'])} patterns for reinforcement")
            
        except Exception as e:
            logger.debug(f"Error amplifying feedback with learning: {e}", exc_info=True)
    
    def _adjust_feedback_by_emotion(
        self,
        metrics: FeedbackMetrics,
        emotional_state: Dict[str, float]
    ):
        """
        Adjust feedback parameters based on emotional state.
        
        Args:
            metrics: Feedback metrics
            emotional_state: Current emotional state
        """
        valence = emotional_state.get("valence", 0.0)
        arousal = emotional_state.get("arousal", 0.5)
        
        # High negative valence: increase error sensitivity (be more corrective)
        if valence < -0.3:
            # Amplify error detection
            effective_error_threshold = self.error_rate_threshold * 0.9  # Lower threshold (more sensitive)
            if metrics.error_rate > effective_error_threshold:
                logger.debug(f"High negative valence amplifies error detection (threshold: {effective_error_threshold:.2f})")
        
        # High positive valence: increase success threshold (maintain standards)
        elif valence > 0.3:
            # Maintain success standards even when feeling good
            effective_success_threshold = self.success_rate_threshold
            logger.debug(f"Positive valence maintains success standards (threshold: {effective_success_threshold:.2f})")
        
        # High arousal: increase responsiveness (react faster)
        if arousal > 0.7:
            logger.debug(f"High arousal ({arousal:.2f}) increases feedback responsiveness")
        
        # Low arousal: decrease responsiveness (be more conservative)
        elif arousal < 0.3:
            logger.debug(f"Low arousal ({arousal:.2f}) decreases feedback responsiveness")
    
    def track_rule_execution(self, rule_name: str, success: bool):
        """Track rule execution for effectiveness calculation."""
        if rule_name not in self.rule_effectiveness:
            self.rule_effectiveness[rule_name] = {
                "successes": 0,
                "failures": 0,
                "strength_boost": 0.0
            }
        
        if success:
            self.rule_effectiveness[rule_name]["successes"] += 1
        else:
            self.rule_effectiveness[rule_name]["failures"] += 1
    
    def track_goal_progress(self, goal_name: str, progress: float):
        """Track goal progress for trend analysis."""
        if goal_name not in self.goal_progress_history:
            self.goal_progress_history[goal_name] = []
        
        self.goal_progress_history[goal_name].append(progress)
        # Keep only recent history
        if len(self.goal_progress_history[goal_name]) > 50:
            self.goal_progress_history[goal_name] = self.goal_progress_history[goal_name][-50:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics."""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        metrics = self._compute_aggregated_metrics()
        
        return {
            "cycles_tracked": len(self.metrics_history),
            "success_rate": metrics.success_rate,
            "error_rate": metrics.error_rate,
            "avg_cycle_duration": metrics.avg_cycle_duration,
            "goal_completion_rate": metrics.goal_completion_rate,
            "rule_effectiveness_count": len(metrics.rule_effectiveness),
            "goal_trends_count": len(metrics.goal_progress_trends)
        }

