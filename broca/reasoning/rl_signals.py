"""
Reinforcement Learning signal aggregator for multi-dimensional reward signals.

Based on cognitive psychology and RL theory:
- Cognitive Dissonance Minimization (Festinger, 1957)
- Surprise Minimization (Error-Driven Learning, Active Inference)
- Curiosity Maximization (Intrinsic Motivation, ICM)
- Information Gain (Epistemic Value, KL Divergence)
- Coherence Pleasure (Understanding Reward)

Aggregates signals from:
- Affective state monitor (surprise, curiosity, coherence)
- Predictive interoception (prediction error)
- Epistemic engine (information gain)
- Cognitive dissonance monitor (dissonance)
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .cognitive_dissonance import CognitiveDissonanceMonitor, DissonanceMetrics
    from ..internal_sensing.affective_state import ComputationalAffectMonitor
    from ..internal_sensing.predictive_interoception import PredictiveInteroception
    from ..internal_sensing.cognitive_state import CognitiveStateMonitor

logger = logging.getLogger(__name__)


@dataclass
class RLSignalMetrics:
    """Multi-dimensional RL signal metrics."""
    timestamp: datetime
    dissonance_reward: float = 0.0  # 1.0 - dissonance (minimize dissonance = maximize reward)
    surprise_reward: float = 0.0  # 1.0 - surprise (minimize surprise = maximize reward)
    curiosity_reward: float = 0.0  # curiosity (maximize curiosity = maximize reward)
    information_gain_reward: float = 0.0  # info_gain (maximize information gain)
    coherence_reward: float = 0.0  # coherence_pleasure (maximize coherence)
    composite_reward: float = 0.0  # Weighted combination
    
    # Weights (configurable, should sum to ~1.0)
    weight_dissonance: float = 0.3
    weight_surprise: float = 0.2
    weight_curiosity: float = 0.2
    weight_info_gain: float = 0.15
    weight_coherence: float = 0.15
    
    def compute_composite(self) -> float:
        """
        Compute composite reward from component signals.
        
        Returns:
            Composite reward (0.0-1.0)
        """
        # Normalize weights to sum to 1.0
        total_weight = (
            self.weight_dissonance +
            self.weight_surprise +
            self.weight_curiosity +
            self.weight_info_gain +
            self.weight_coherence
        )
        
        if total_weight == 0.0:
            logger.warning("All RL signal weights are zero, using equal weights")
            self.weight_dissonance = 0.2
            self.weight_surprise = 0.2
            self.weight_curiosity = 0.2
            self.weight_info_gain = 0.2
            self.weight_coherence = 0.2
            total_weight = 1.0
        elif abs(total_weight - 1.0) > 0.01:
            # Normalize weights
            scale = 1.0 / total_weight
            self.weight_dissonance *= scale
            self.weight_surprise *= scale
            self.weight_curiosity *= scale
            self.weight_info_gain *= scale
            self.weight_coherence *= scale
        
        # Compute weighted sum
        self.composite_reward = (
            self.dissonance_reward * self.weight_dissonance +
            self.surprise_reward * self.weight_surprise +
            self.curiosity_reward * self.weight_curiosity +
            self.information_gain_reward * self.weight_info_gain +
            self.coherence_reward * self.weight_coherence
        )
        
        # Ensure bounded [0, 1]
        self.composite_reward = max(0.0, min(1.0, self.composite_reward))
        
        return self.composite_reward
    
    def get_exploration_exploitation_balance(self) -> float:
        """
        Compute exploration-exploitation balance.
        
        Returns:
            Balance score (0.0 = pure exploitation, 1.0 = pure exploration)
        """
        # Exploration: curiosity + info_gain
        exploration = (self.curiosity_reward + self.information_gain_reward) / 2.0
        
        # Exploitation: coherence + (1 - surprise) + (1 - dissonance)
        exploitation = (
            self.coherence_reward +
            self.surprise_reward +
            self.dissonance_reward
        ) / 3.0
        
        # Balance: exploration / (exploration + exploitation)
        total = exploration + exploitation
        if total == 0.0:
            return 0.5  # Balanced
        
        balance = exploration / total
        return max(0.0, min(1.0, balance))


class RLSignalAggregator:
    """
    Aggregates multiple RL signals from various sources.
    
    Collects signals from:
    - Cognitive dissonance monitor (dissonance)
    - Affective state monitor (surprise, curiosity, coherence)
    - Predictive interoception (prediction error)
    - Epistemic engine (information gain)
    """
    
    def __init__(
        self,
        weight_dissonance: float = 0.3,
        weight_surprise: float = 0.2,
        weight_curiosity: float = 0.2,
        weight_info_gain: float = 0.15,
        weight_coherence: float = 0.15,
        cognitive_dissonance_monitor: Optional["CognitiveDissonanceMonitor"] = None,
        affective_monitor: Optional["ComputationalAffectMonitor"] = None,
        predictive_interoception: Optional["PredictiveInteroception"] = None,
        epistemic_bridge: Optional[Any] = None,
    ):
        """
        Initialize RL signal aggregator.
        
        Args:
            weight_dissonance: Weight for dissonance reward signal
            weight_surprise: Weight for surprise reward signal
            weight_curiosity: Weight for curiosity reward signal
            weight_info_gain: Weight for information gain reward signal
            weight_coherence: Weight for coherence reward signal
            cognitive_dissonance_monitor: Optional CognitiveDissonanceMonitor
            affective_monitor: Optional ComputationalAffectMonitor
            predictive_interoception: Optional PredictiveInteroception
            epistemic_bridge: Optional epistemic bridge for information gain
        """
        self.weight_dissonance = weight_dissonance
        self.weight_surprise = weight_surprise
        self.weight_curiosity = weight_curiosity
        self.weight_info_gain = weight_info_gain
        self.weight_coherence = weight_coherence
        
        self.cognitive_dissonance_monitor = cognitive_dissonance_monitor
        self.affective_monitor = affective_monitor
        self.predictive_interoception = predictive_interoception
        self.epistemic_bridge = epistemic_bridge
        
        logger.info(
            f"Initialized RLSignalAggregator with weights: "
            f"dissonance={weight_dissonance:.2f}, surprise={weight_surprise:.2f}, "
            f"curiosity={weight_curiosity:.2f}, info_gain={weight_info_gain:.2f}, "
            f"coherence={weight_coherence:.2f}"
        )
    
    def compute_signals(
        self,
        dissonance_metrics: Optional["DissonanceMetrics"] = None,
        affective_state: Optional[Dict[str, Any]] = None,
        prediction_error: Optional[float] = None,
        information_gain: Optional[float] = None,
    ) -> RLSignalMetrics:
        """
        Compute all RL signals from available sources.
        
        Args:
            dissonance_metrics: Optional pre-computed dissonance metrics
            affective_state: Optional pre-computed affective state dictionary
            prediction_error: Optional pre-computed prediction error (0.0-1.0)
            information_gain: Optional pre-computed information gain (0.0-1.0)
            
        Returns:
            RLSignalMetrics with all computed signals
        """
        metrics = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            weight_dissonance=self.weight_dissonance,
            weight_surprise=self.weight_surprise,
            weight_curiosity=self.weight_curiosity,
            weight_info_gain=self.weight_info_gain,
            weight_coherence=self.weight_coherence,
        )
        
        # 1. Dissonance reward: 1.0 - dissonance (minimize dissonance = maximize reward)
        if dissonance_metrics:
            overall_dissonance = dissonance_metrics.overall_dissonance
            metrics.dissonance_reward = max(0.0, min(1.0, 1.0 - overall_dissonance))
        elif self.cognitive_dissonance_monitor:
            try:
                dissonance_data = self.cognitive_dissonance_monitor.get_aggregated_dissonance()
                overall_dissonance = dissonance_data.get("overall_dissonance", 0.0)
                metrics.dissonance_reward = max(0.0, min(1.0, 1.0 - overall_dissonance))
            except Exception as e:
                logger.debug(f"Error getting dissonance signal: {e}")
                metrics.dissonance_reward = 0.5  # Default neutral
        else:
            metrics.dissonance_reward = 0.5  # Default neutral if unavailable
        
        # 2. Surprise reward: 1.0 - surprise (minimize surprise = maximize reward)
        if affective_state:
            surprise = affective_state.get("surprise", 0.0)
            metrics.surprise_reward = max(0.0, min(1.0, 1.0 - surprise))
        elif self.affective_monitor:
            try:
                affective = self.affective_monitor.sample_affective_state()
                surprise = affective.get("surprise", 0.0)
                metrics.surprise_reward = max(0.0, min(1.0, 1.0 - surprise))
            except Exception as e:
                logger.debug(f"Error getting surprise signal: {e}")
                metrics.surprise_reward = 0.5  # Default neutral
        else:
            metrics.surprise_reward = 0.5  # Default neutral if unavailable
        
        # Also incorporate prediction error if available (as additional surprise signal)
        if prediction_error is not None:
            prediction_surprise = max(0.0, min(1.0, prediction_error))
            # Blend with affective surprise (weighted average)
            metrics.surprise_reward = (metrics.surprise_reward * 0.7) + ((1.0 - prediction_surprise) * 0.3)
        elif self.predictive_interoception:
            try:
                # Try to get recent prediction error from history
                if hasattr(self.predictive_interoception, '_prediction_errors'):
                    errors = list(self.predictive_interoception._prediction_errors)
                    if errors:
                        recent_error = errors[-1] if errors else 0.0
                        prediction_surprise = max(0.0, min(1.0, recent_error))
                        metrics.surprise_reward = (metrics.surprise_reward * 0.7) + ((1.0 - prediction_surprise) * 0.3)
            except Exception as e:
                logger.debug(f"Error getting prediction error signal: {e}")
        
        # 3. Curiosity reward: curiosity_drive (maximize curiosity = maximize reward)
        if affective_state:
            curiosity = affective_state.get("curiosity_drive", 0.0)
            metrics.curiosity_reward = max(0.0, min(1.0, curiosity))
        elif self.affective_monitor:
            try:
                affective = self.affective_monitor.sample_affective_state()
                curiosity = affective.get("curiosity_drive", 0.0)
                metrics.curiosity_reward = max(0.0, min(1.0, curiosity))
            except Exception as e:
                logger.debug(f"Error getting curiosity signal: {e}")
                metrics.curiosity_reward = 0.5  # Default moderate
        else:
            metrics.curiosity_reward = 0.5  # Default moderate if unavailable
        
        # 4. Information gain reward: information_gain (maximize info gain = maximize reward)
        if information_gain is not None:
            metrics.information_gain_reward = max(0.0, min(1.0, information_gain))
        elif self.epistemic_bridge:
            try:
                info_gain = self.epistemic_bridge.get_information_gain()
                if info_gain is not None:
                    metrics.information_gain_reward = max(0.0, min(1.0, info_gain))
                else:
                    metrics.information_gain_reward = 0.0  # No information gain
            except Exception as e:
                logger.debug(f"Error getting information gain signal: {e}")
                metrics.information_gain_reward = 0.0  # Default no gain
        else:
            metrics.information_gain_reward = 0.0  # Default no gain if unavailable
        
        # 5. Coherence reward: coherence_pleasure (maximize coherence = maximize reward)
        if affective_state:
            coherence = affective_state.get("coherence_pleasure", 0.0)
            metrics.coherence_reward = max(0.0, min(1.0, coherence))
        elif self.affective_monitor:
            try:
                affective = self.affective_monitor.sample_affective_state()
                coherence = affective.get("coherence_pleasure", 0.0)
                metrics.coherence_reward = max(0.0, min(1.0, coherence))
            except Exception as e:
                logger.debug(f"Error getting coherence signal: {e}")
                metrics.coherence_reward = 0.5  # Default moderate
        else:
            metrics.coherence_reward = 0.5  # Default moderate if unavailable
        
        # Compute composite reward
        metrics.compute_composite()
        
        logger.debug(
            f"Computed RL signals: dissonance={metrics.dissonance_reward:.3f}, "
            f"surprise={metrics.surprise_reward:.3f}, curiosity={metrics.curiosity_reward:.3f}, "
            f"info_gain={metrics.information_gain_reward:.3f}, coherence={metrics.coherence_reward:.3f}, "
            f"composite={metrics.composite_reward:.3f}"
        )
        
        return metrics
    
    def get_exploration_exploitation_balance(self, metrics: Optional[RLSignalMetrics] = None) -> float:
        """
        Get exploration-exploitation balance from metrics.
        
        Args:
            metrics: Optional pre-computed metrics, otherwise computes fresh
            
        Returns:
            Balance score (0.0 = pure exploitation, 1.0 = pure exploration)
        """
        if metrics is None:
            metrics = self.compute_signals()
        
        return metrics.get_exploration_exploitation_balance()
    
    def should_explore(self, threshold: float = 0.6) -> bool:
        """
        Determine if agent should explore based on balance.
        
        Args:
            threshold: Threshold above which to explore (default 0.6)
            
        Returns:
            True if should explore, False if should exploit
        """
        balance = self.get_exploration_exploitation_balance()
        return balance >= threshold

