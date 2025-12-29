"""
Reinforcement Learning signal aggregator for multi-dimensional reward signals.

IMPORTANT ARCHITECTURE NOTE:
============================
This module does NOT implement Q-learning or maintain Q-tables. RL signals are
computed metrics that aggregate information from various cognitive monitors to
provide reward signals for tool selection and behavior guidance.

- RL signals are computed ON-THE-FLY from current system state
- No learned state-action values (Q-values) are stored
- No Q-tables or value function approximations
- Signals are ephemeral - computed fresh each time compute_signals() is called
- Historical signal data is NOT persisted by default (see RLSignalStorage for optional persistence)

The "RL" in the name refers to the use of reward signals for guidance, not to
a full reinforcement learning algorithm. This is a signal aggregation system
that provides multi-dimensional feedback for cognitive decision-making.

COMPUTATION FLOW:
================
1. RLSignalAggregator.compute_signals() is called
2. Signals are gathered from various sources:
   - Cognitive dissonance monitor → dissonance_reward
   - Affective state monitor → surprise_reward, curiosity_reward, coherence_reward
   - Predictive interoception → prediction error (incorporated into surprise)
   - Epistemic engine → information_gain_reward
3. Signals are weighted and combined into composite_reward
4. Exploration-exploitation balance is computed
5. Metrics are returned (not stored)

PERSISTENCE:
============
By default, RL signals are NOT persisted. They are computed fresh each time.
If persistence is needed for trend analysis, use RLSignalStorage (optional).

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
    
    IMPORTANT: This is NOT a Q-learning system. Signals are computed on-the-fly
    from current system state. No Q-tables or learned values are maintained.
    
    Collects signals from:
    - Cognitive dissonance monitor (dissonance)
    - Affective state monitor (surprise, curiosity, coherence)
    - Predictive interoception (prediction error)
    - Epistemic engine (information gain)
    
    Signals are computed fresh each time compute_signals() is called. They are
    not persisted by default. For persistence, use RLSignalStorage.
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
                # Check if we have sufficient data
                has_data = dissonance_data.get("has_data", True)  # Default to True for backward compatibility
                if not has_data:
                    # Insufficient data - use neutral reward (0.5) instead of assuming zero dissonance
                    logger.debug("Insufficient dissonance data for RL signals, using neutral reward")
                    metrics.dissonance_reward = 0.5
                else:
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


class RLSignalStorage:
    """
    Optional persistence layer for RL signal history.
    
    Stores computed RL signals with timestamps for trend analysis and learning.
    This is an optional enhancement - by default, RL signals are not persisted.
    
    Usage:
        storage = RLSignalStorage(storage_path="rl_signals.json")
        storage.save_signal(metrics)
        history = storage.load_history(days=7)
    """
    
    def __init__(self, storage_path: str = "rl_signals_history.json", max_history_size: int = 10000):
        """
        Initialize RL signal storage.
        
        Args:
            storage_path: Path to JSON file for storing signal history
            max_history_size: Maximum number of signal records to keep
        """
        import json
        import os
        from pathlib import Path
        
        self.storage_path = Path(storage_path)
        self.max_history_size = max_history_size
        self._signals_history: List[Dict[str, Any]] = []
        
        # Create parent directory if needed
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history if file exists
        if self.storage_path.exists():
            self._load()
        else:
            logger.info(f"Initialized RLSignalStorage at {self.storage_path.absolute()}")
    
    def _load(self) -> None:
        """Load signal history from storage file."""
        import json
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._signals_history = data.get("signals", [])
            
            # Trim to max size if needed
            if len(self._signals_history) > self.max_history_size:
                self._signals_history = self._signals_history[-self.max_history_size:]
                logger.info(f"Trimmed signal history to {self.max_history_size} records")
            
            logger.debug(f"Loaded {len(self._signals_history)} signal records from {self.storage_path}")
            
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load RL signal history: {e}", exc_info=True)
            self._signals_history = []
    
    def save_signal(self, metrics: RLSignalMetrics) -> None:
        """
        Save a signal metrics record to history.
        
        Args:
            metrics: RLSignalMetrics instance to save
        """
        import json
        import tempfile
        import os
        
        # Convert metrics to dict
        signal_record = {
            "timestamp": metrics.timestamp.isoformat(),
            "dissonance_reward": metrics.dissonance_reward,
            "surprise_reward": metrics.surprise_reward,
            "curiosity_reward": metrics.curiosity_reward,
            "information_gain_reward": metrics.information_gain_reward,
            "coherence_reward": metrics.coherence_reward,
            "composite_reward": metrics.composite_reward,
            "exploration_balance": metrics.get_exploration_exploitation_balance(),
        }
        
        # Add to history
        self._signals_history.append(signal_record)
        
        # Trim to max size
        if len(self._signals_history) > self.max_history_size:
            self._signals_history = self._signals_history[-self.max_history_size:]
        
        # Save to file (atomic write)
        try:
            data = {
                "signals": self._signals_history,
                "last_saved": datetime.now(timezone.utc).isoformat(),
                "total_records": len(self._signals_history),
            }
            
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.storage_path.parent,
                delete=False,
                suffix='.tmp'
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False, default=str)
                tmp_path = tmp_file.name
            
            # Atomic rename
            os.replace(tmp_path, self.storage_path)
            
            logger.debug(f"Saved RL signal to {self.storage_path}")
            
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to save RL signal: {e}", exc_info=True)
            # Remove from history if save failed
            if signal_record in self._signals_history:
                self._signals_history.remove(signal_record)
    
    def load_history(self, days: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load signal history.
        
        Args:
            days: Optional number of days to look back (None = all history)
            limit: Optional maximum number of records to return
            
        Returns:
            List of signal records (most recent first)
        """
        from datetime import timedelta
        
        history = list(self._signals_history)  # Copy
        
        # Filter by days if specified
        if days is not None:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
            history = [
                record for record in history
                if datetime.fromisoformat(record["timestamp"]) >= cutoff_time
            ]
        
        # Reverse to get most recent first
        history.reverse()
        
        # Apply limit
        if limit is not None:
            history = history[:limit]
        
        return history
    
    def get_statistics(self, days: Optional[int] = 7) -> Dict[str, Any]:
        """
        Get statistics about signal history.
        
        Args:
            days: Number of days to analyze (default 7)
            
        Returns:
            Dictionary with statistics
        """
        history = self.load_history(days=days)
        
        if not history:
            return {
                "total_records": 0,
                "days": days,
                "message": "No signal history available"
            }
        
        # Extract values
        composite_rewards = [r["composite_reward"] for r in history]
        dissonance_rewards = [r["dissonance_reward"] for r in history]
        curiosity_rewards = [r["curiosity_reward"] for r in history]
        exploration_balances = [r["exploration_balance"] for r in history]
        
        def stats(values: List[float]) -> Dict[str, float]:
            if not values:
                return {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}
            mean_val = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_val = variance ** 0.5
            return {
                "mean": round(mean_val, 3),
                "min": round(min_val, 3),
                "max": round(max_val, 3),
                "std": round(std_val, 3),
            }
        
        return {
            "total_records": len(history),
            "days": days,
            "composite_reward": stats(composite_rewards),
            "dissonance_reward": stats(dissonance_rewards),
            "curiosity_reward": stats(curiosity_rewards),
            "exploration_balance": stats(exploration_balances),
        }
    
    def clear_history(self) -> None:
        """Clear all signal history."""
        self._signals_history = []
        if self.storage_path.exists():
            self.storage_path.unlink()
        logger.info("Cleared RL signal history")

