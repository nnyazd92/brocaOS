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
from typing import Dict, Any, Optional, TYPE_CHECKING, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..internal_sensing.data_quality import measurement_uncertainty_from_quality

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

    # --- Raw / intermediate signals (for debugging + learning) ---
    # Convention: raw_* are in "signal space" where higher means "more of the thing".
    # Rewards are typically in "reward space" where higher means "better".
    schema_version: int = 4
    dissonance_raw: Optional[float] = None  # overall_dissonance (0..1); higher = more dissonance
    has_dissonance_data: Optional[bool] = None
    dissonance_estimator: Optional[str] = None  # "measured" | "estimated_llm" | "unavailable"
    dissonance_uncertainty: Optional[float] = None  # 0..1

    raw_surprise: Optional[float] = None  # higher = more surprising (0..1)
    surprise_short_term: Optional[float] = None
    surprise_long_term: Optional[float] = None
    prediction_error_raw: Optional[float] = None  # 0..1
    prediction_error_recent_avg: Optional[float] = None  # 0..1
    calibrated_surprise: Optional[float] = None  # 0..1, calibrated (e.g., NLL-based)
    surprise_source: Optional[str] = None  # e.g., "affective", "affective+prediction_error", "affective+calibrated_prediction"
    surprise_has_data: Optional[bool] = None
    surprise_data_quality: Optional[str] = None  # e.g., "high|medium|low|insufficient|missing"
    surprise_estimator: Optional[str] = None  # "affective" | "estimated_llm" | "unavailable"
    surprise_uncertainty: Optional[float] = None  # 0..1

    curiosity_raw: Optional[float] = None  # curiosity_drive (0..1)
    curiosity_has_data: Optional[bool] = None
    curiosity_data_quality: Optional[str] = None
    curiosity_estimator: Optional[str] = None
    curiosity_uncertainty: Optional[float] = None  # 0..1
    coherence_raw: Optional[float] = None  # coherence_pleasure (0..1)
    coherence_has_data: Optional[bool] = None
    coherence_data_quality: Optional[str] = None
    coherence_estimator: Optional[str] = None
    coherence_uncertainty: Optional[float] = None  # 0..1
    info_gain_raw: Optional[float] = None  # info_gain (0..1)
    info_gain_source: Optional[str] = None  # e.g., "epistemic_bridge", "provided", "unavailable"
    info_gain_has_data: Optional[bool] = None
    info_gain_estimator: Optional[str] = None  # "epistemic_bridge" | "provided" | "estimated_llm" | "unavailable"
    info_gain_uncertainty: Optional[float] = None  # 0..1

    # --- Epistemic uncertainty (separate from measurement uncertainty) ---
    epistemic_uncertainty_total: Optional[float] = None
    epistemic_uncertainty_epistemic: Optional[float] = None
    epistemic_uncertainty_aleatoric: Optional[float] = None
    epistemic_uncertainty_model: Optional[float] = None
    epistemic_uncertainty_data_quality: Optional[str] = None
    epistemic_uncertainty_sample_size: Optional[int] = None
    epistemic_uncertainty_has_data: Optional[bool] = None
    
    def compute_composite(self) -> float:
        """
        Compute composite reward from component signals.
        
        Returns:
            Composite reward (0.0-1.0)
        """
        # Clamp component rewards to [0, 1] (defensive against out-of-range inputs)
        self.dissonance_reward = max(0.0, min(1.0, float(self.dissonance_reward)))
        self.surprise_reward = max(0.0, min(1.0, float(self.surprise_reward)))
        self.curiosity_reward = max(0.0, min(1.0, float(self.curiosity_reward)))
        self.information_gain_reward = max(0.0, min(1.0, float(self.information_gain_reward)))
        self.coherence_reward = max(0.0, min(1.0, float(self.coherence_reward)))

        # Normalize weights to sum to 1.0
        total_weight = (
            self.weight_dissonance +
            self.weight_surprise +
            self.weight_curiosity +
            self.weight_info_gain +
            self.weight_coherence
        )
        
        # Treat extremely tiny totals as zero to avoid overflow when normalizing.
        # (Hypothesis can generate denormal/near-zero floats that would otherwise produce inf weights.)
        if total_weight == 0.0 or total_weight < 1e-12:
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
        
        # Ensure composite is within convex hull of components (defensive vs float drift).
        min_component = min(
            self.dissonance_reward,
            self.surprise_reward,
            self.curiosity_reward,
            self.information_gain_reward,
            self.coherence_reward,
        )
        max_component = max(
            self.dissonance_reward,
            self.surprise_reward,
            self.curiosity_reward,
            self.information_gain_reward,
            self.coherence_reward,
        )
        self.composite_reward = max(min_component, min(max_component, self.composite_reward))

        # Ensure bounded [0, 1]
        self.composite_reward = max(0.0, min(1.0, float(self.composite_reward)))
        
        logger.info(
            f"RL signal metrics computed: composite={self.composite_reward:.4f}, "
            f"dissonance={self.dissonance_reward:.4f}, surprise={self.surprise_reward:.4f}, "
            f"curiosity={self.curiosity_reward:.4f}, info_gain={self.information_gain_reward:.4f}, "
            f"coherence={self.coherence_reward:.4f}, exploration_balance={self.get_exploration_exploitation_balance():.4f}",
            extra={
                "event": "rl_signal_metrics_computed",
                "composite_reward": self.composite_reward,
                "dissonance_reward": self.dissonance_reward,
                "surprise_reward": self.surprise_reward,
                "curiosity_reward": self.curiosity_reward,
                "information_gain_reward": self.information_gain_reward,
                "coherence_reward": self.coherence_reward,
                "exploration_balance": self.get_exploration_exploitation_balance(),
            }
        )
        
        return self.composite_reward
    
    def get_exploration_exploitation_balance(self) -> float:
        """
        Compute exploration-exploitation balance based on Active Inference theory.
        
        Based on Expected Free Energy decomposition:
        G = G_epistemic + G_pragmatic
        
        Exploration (epistemic value) is driven by:
        - Curiosity: intrinsic motivation to learn
        - Information gain: expected learning opportunity  
        - Prediction error: world model needs updating
        - Surprise: unexpected events trigger exploration
        - Dissonance: inconsistent beliefs require exploration
        
        Exploitation (pragmatic value) is driven by:
        - Coherence: world model is accurate
        - Low surprise: predictable environment
        - Low dissonance: consistent beliefs
        
        IMPORTANT: Uses RAW signal values, not inverted reward values.
        
        Returns:
            Balance score (0.0 = pure exploitation, 1.0 = pure exploration)
        
        References:
        - Friston, K. (2010). The free-energy principle
        - Schwartenbeck et al. (2019). Computational mechanisms of curiosity
        """
        # Get raw values, falling back to derived values if unavailable
        curiosity = self.curiosity_raw if self.curiosity_raw is not None else self.curiosity_reward
        info_gain = self.info_gain_raw if self.info_gain_raw is not None else self.information_gain_reward
        prediction_error = self.prediction_error_raw if self.prediction_error_raw is not None else 0.0
        raw_surprise = self.raw_surprise if self.raw_surprise is not None else (1.0 - self.surprise_reward)
        coherence = self.coherence_raw if self.coherence_raw is not None else self.coherence_reward
        dissonance = self.dissonance_raw if self.dissonance_raw is not None else (1.0 - self.dissonance_reward)
        
        # ================================================================
        # EXPLORATION DRIVE (epistemic value - information seeking)
        # High values = should explore more
        # ================================================================
        exploration_signals = [
            curiosity,          # Intrinsic motivation
            info_gain,          # Expected learning
            prediction_error,   # World model errors → explore to fix
            raw_surprise,       # Unexpected → explore to understand
            dissonance,         # Inconsistent beliefs → explore to resolve
        ]
        exploration = sum(exploration_signals) / len(exploration_signals)
        
        # ================================================================
        # EXPLOITATION DRIVE (pragmatic value - goal directed)
        # High values = should exploit more
        # ================================================================
        exploitation_signals = [
            coherence,              # World model is good
            1.0 - raw_surprise,     # Predictable environment
            1.0 - dissonance,       # Consistent beliefs
            1.0 - prediction_error, # Low prediction error
        ]
        exploitation = sum(exploitation_signals) / len(exploitation_signals)
        
        # Balance: exploration / (exploration + exploitation)
        total = exploration + exploitation
        if total == 0.0:
            return 0.5  # Default to balanced
        
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
        estimator: Optional[Any] = None,
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
        self.estimator = estimator
        
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

        def _quality_is_usable(q: Optional[str]) -> bool:
            # We treat missing/insufficient as "not real" (should not drive reward without estimation).
            if not q:
                return True
            qn = str(q).strip().lower()
            return qn not in ("missing", "insufficient")

        def _meas_unc(q: Optional[str], sample_size: Optional[int] = None) -> float:
            return measurement_uncertainty_from_quality(q, sample_size=sample_size)
        
        # 1. Dissonance reward: 1.0 - dissonance (minimize dissonance = maximize reward)
        if dissonance_metrics:
            # IMPORTANT: dissonance_metrics can represent an "estimated/insufficient" measurement
            # (e.g., when response=None and most components are unavailable). In that case we must
            # not allow the default numeric values to create strong reward gradients.
            has_sufficient = bool(getattr(dissonance_metrics, "has_sufficient_data", True))
            component_availability = getattr(dissonance_metrics, "component_availability", None)
            any_component = True
            if isinstance(component_availability, dict):
                any_component = any(bool(v) for v in component_availability.values())
            if not has_sufficient or not any_component:
                metrics.has_dissonance_data = False
                metrics.dissonance_raw = None
                metrics.dissonance_reward = 0.5  # neutral when insufficient
                metrics.dissonance_estimator = "unavailable"
                metrics.dissonance_uncertainty = 1.0
            else:
                overall_dissonance = float(getattr(dissonance_metrics, "overall_dissonance", 0.0))
                overall_dissonance = max(0.0, min(1.0, overall_dissonance))
                metrics.has_dissonance_data = True
                metrics.dissonance_raw = overall_dissonance
                metrics.dissonance_reward = max(0.0, min(1.0, 1.0 - overall_dissonance))
                metrics.dissonance_estimator = "measured"
                # Measurement uncertainty: increase when fewer components are available / low history.
                comp_av = getattr(dissonance_metrics, "component_availability", {}) or {}
                try:
                    available = sum(1 for v in comp_av.values() if v)
                    total = max(1, len(comp_av))
                    comp_factor = 1.0 - (available / total)
                except Exception:
                    comp_factor = 0.3
                try:
                    history_size = int(getattr(dissonance_metrics, "history_size", 0) or 0)
                except Exception:
                    history_size = 0
                # Approximate quality from history size
                if history_size >= 20:
                    q = "high"
                elif history_size >= 10:
                    q = "medium"
                elif history_size >= 5:
                    q = "low"
                elif history_size > 0:
                    q = "insufficient"
                else:
                    q = "missing"
                metrics.dissonance_uncertainty = max(0.0, min(1.0, _meas_unc(q, sample_size=history_size) + comp_factor * 0.3))
        elif self.cognitive_dissonance_monitor:
            try:
                dissonance_data = self.cognitive_dissonance_monitor.get_aggregated_dissonance()
                # Check if we have sufficient data
                has_data = bool(dissonance_data.get("has_data", True))  # backward compatibility default
                has_sufficient_data = bool(dissonance_data.get("has_sufficient_data", True))
                metrics.has_dissonance_data = bool(has_data and has_sufficient_data)

                if not (has_data and has_sufficient_data):
                    # Missing/low-quality data: DO NOT interpret defaults as real measurements.
                    # Use estimator if available, otherwise fall back to neutral.
                    if self.estimator and hasattr(self.estimator, "estimate_dissonance"):
                        try:
                            est_dissonance, _est_uncertainty = self.estimator.estimate_dissonance(
                                context={"dissonance_data": dissonance_data}
                            )
                            overall_dissonance = max(0.0, min(1.0, float(est_dissonance)))
                            metrics.dissonance_raw = overall_dissonance
                            metrics.dissonance_reward = max(0.0, min(1.0, 1.0 - overall_dissonance))
                            metrics.dissonance_estimator = "estimated_llm"
                            try:
                                metrics.dissonance_uncertainty = max(0.0, min(1.0, float(_est_uncertainty)))
                            except Exception:
                                metrics.dissonance_uncertainty = None
                        except Exception as e:
                            logger.debug(f"Dissonance estimation failed, using neutral reward: {e}")
                            metrics.dissonance_reward = 0.5
                            metrics.dissonance_estimator = "unavailable"
                    else:
                        metrics.dissonance_reward = 0.5
                        metrics.dissonance_estimator = "unavailable"
                else:
                    overall_dissonance = dissonance_data.get("overall_dissonance", 0.0)
                    metrics.dissonance_raw = overall_dissonance
                    metrics.dissonance_reward = max(0.0, min(1.0, 1.0 - overall_dissonance))
                    metrics.dissonance_estimator = "measured"
                    comp_av = dissonance_data.get("component_availability", {}) or {}
                    try:
                        available = sum(1 for v in comp_av.values() if v)
                        total = max(1, len(comp_av))
                        comp_factor = 1.0 - (available / total)
                    except Exception:
                        comp_factor = 0.3
                    try:
                        history_size = int(dissonance_data.get("history_size", 0) or 0)
                    except Exception:
                        history_size = 0
                    if history_size >= 20:
                        q = "high"
                    elif history_size >= 10:
                        q = "medium"
                    elif history_size >= 5:
                        q = "low"
                    elif history_size > 0:
                        q = "insufficient"
                    else:
                        q = "missing"
                    metrics.dissonance_uncertainty = max(0.0, min(1.0, _meas_unc(q, sample_size=history_size) + comp_factor * 0.3))
            except Exception as e:
                logger.debug(f"Error getting dissonance signal: {e}")
                metrics.has_dissonance_data = None
                metrics.dissonance_reward = 0.5  # Default neutral
                metrics.dissonance_estimator = "unavailable"
        else:
            metrics.has_dissonance_data = None
            metrics.dissonance_reward = 0.5  # Default neutral if unavailable
            metrics.dissonance_estimator = "unavailable"
        
        # 2. Surprise reward: 1.0 - surprise (minimize surprise = maximize reward)
        surprise_source = "unavailable"
        if affective_state:
            surprise = affective_state.get("surprise", 0.0)
            try:
                metrics.raw_surprise = max(0.0, min(1.0, float(surprise)))
            except Exception:
                metrics.raw_surprise = None
            metrics.surprise_short_term = affective_state.get("surprise_short_term")
            metrics.surprise_long_term = affective_state.get("surprise_long_term")
            metrics.surprise_reward = max(0.0, min(1.0, 1.0 - surprise))
            surprise_source = "affective"
            q = (affective_state.get("data_quality") or {}).get("surprise") if isinstance(affective_state.get("data_quality"), dict) else None
            metrics.surprise_data_quality = q
            metrics.surprise_has_data = _quality_is_usable(q)
            metrics.surprise_estimator = "affective" if metrics.surprise_has_data else None
            metrics.surprise_uncertainty = _meas_unc(q)
        elif self.affective_monitor:
            try:
                affective = self.affective_monitor.sample_affective_state()
                surprise = affective.get("surprise", 0.0)
                try:
                    metrics.raw_surprise = max(0.0, min(1.0, float(surprise)))
                except Exception:
                    metrics.raw_surprise = None
                metrics.surprise_short_term = affective.get("surprise_short_term")
                metrics.surprise_long_term = affective.get("surprise_long_term")
                q = (affective.get("data_quality") or {}).get("surprise") if isinstance(affective.get("data_quality"), dict) else None
                metrics.surprise_data_quality = q
                metrics.surprise_has_data = _quality_is_usable(q)
                if metrics.surprise_has_data:
                    metrics.surprise_reward = max(0.0, min(1.0, 1.0 - surprise))
                    surprise_source = "affective"
                    metrics.surprise_estimator = "affective"
                    metrics.surprise_uncertainty = _meas_unc(q)
                else:
                    # Low-quality/missing affective surprise: estimate if possible
                    if self.estimator and hasattr(self.estimator, "estimate_surprise"):
                        try:
                            est_s, est_u = self.estimator.estimate_surprise(context={"affective_state": affective})
                            est_s = max(0.0, min(1.0, float(est_s)))
                            metrics.raw_surprise = est_s
                            metrics.surprise_reward = max(0.0, min(1.0, 1.0 - est_s))
                            surprise_source = "estimated_llm"
                            metrics.surprise_estimator = "estimated_llm"
                            metrics.surprise_uncertainty = max(0.0, min(1.0, float(est_u)))
                        except Exception as e:
                            logger.debug(f"Surprise estimation failed: {e}")
                            metrics.surprise_reward = 0.5
                            metrics.surprise_estimator = "unavailable"
                    else:
                        metrics.surprise_reward = 0.5
                        metrics.surprise_estimator = "unavailable"
            except Exception as e:
                logger.debug(f"Error getting surprise signal: {e}")
                metrics.surprise_reward = 0.5  # Default neutral
                metrics.surprise_estimator = "unavailable"
        else:
            metrics.surprise_reward = 0.5  # Default neutral if unavailable
            metrics.surprise_estimator = "unavailable"
        
        # Also incorporate prediction error if available (as additional surprise signal)
        if prediction_error is not None:
            prediction_surprise = max(0.0, min(1.0, prediction_error))
            metrics.prediction_error_raw = prediction_surprise
            # Blend with affective surprise (weighted average)
            metrics.surprise_reward = (metrics.surprise_reward * 0.7) + ((1.0 - prediction_surprise) * 0.3)
            surprise_source = "affective+prediction_error" if surprise_source == "affective" else "prediction_error"
        elif self.predictive_interoception:
            try:
                # Try to get recent prediction error from history
                if hasattr(self.predictive_interoception, '_prediction_errors'):
                    errors = list(self.predictive_interoception._prediction_errors)
                    if errors:
                        recent_error = errors[-1] if errors else 0.0
                        prediction_surprise = max(0.0, min(1.0, recent_error))
                        metrics.prediction_error_raw = prediction_surprise
                        try:
                            if len(errors) >= 3:
                                metrics.prediction_error_recent_avg = float(sum(errors[-3:]) / 3.0)
                            else:
                                metrics.prediction_error_recent_avg = float(recent_error)
                        except Exception:
                            metrics.prediction_error_recent_avg = None

                        # Prefer a calibrated surprise signal if available
                        calibrated = None
                        if hasattr(self.predictive_interoception, "get_rl_surprise_signal"):
                            try:
                                calibrated = float(self.predictive_interoception.get_rl_surprise_signal())
                            except Exception:
                                calibrated = None

                        if calibrated is not None:
                            calibrated = max(0.0, min(1.0, calibrated))
                            metrics.calibrated_surprise = calibrated
                            metrics.surprise_reward = (metrics.surprise_reward * 0.7) + ((1.0 - calibrated) * 0.3)
                            surprise_source = "affective+calibrated_prediction" if surprise_source == "affective" else "calibrated_prediction"
                        else:
                            metrics.surprise_reward = (metrics.surprise_reward * 0.7) + ((1.0 - prediction_surprise) * 0.3)
                            surprise_source = "affective+prediction_error" if surprise_source == "affective" else "prediction_error"
            except Exception as e:
                logger.debug(f"Error getting prediction error signal: {e}")
        
        metrics.surprise_source = surprise_source
        
        # 3. Curiosity reward: curiosity_drive (maximize curiosity = maximize reward)
        if affective_state:
            curiosity = affective_state.get("curiosity_drive", 0.0)
            try:
                metrics.curiosity_raw = max(0.0, min(1.0, float(curiosity)))
            except Exception:
                metrics.curiosity_raw = None
            metrics.curiosity_reward = max(0.0, min(1.0, curiosity))
            q = (affective_state.get("data_quality") or {}).get("curiosity_drive") if isinstance(affective_state.get("data_quality"), dict) else None
            metrics.curiosity_data_quality = q
            metrics.curiosity_has_data = _quality_is_usable(q)
            metrics.curiosity_estimator = "affective" if metrics.curiosity_has_data else None
            metrics.curiosity_uncertainty = _meas_unc(q)
        elif self.affective_monitor:
            try:
                affective = self.affective_monitor.sample_affective_state()
                curiosity = affective.get("curiosity_drive", 0.0)
                try:
                    metrics.curiosity_raw = max(0.0, min(1.0, float(curiosity)))
                except Exception:
                    metrics.curiosity_raw = None
                q = (affective.get("data_quality") or {}).get("curiosity_drive") if isinstance(affective.get("data_quality"), dict) else None
                metrics.curiosity_data_quality = q
                metrics.curiosity_has_data = _quality_is_usable(q)
                if metrics.curiosity_has_data:
                    metrics.curiosity_reward = max(0.0, min(1.0, curiosity))
                    metrics.curiosity_estimator = "affective"
                    metrics.curiosity_uncertainty = _meas_unc(q)
                else:
                    if self.estimator and hasattr(self.estimator, "estimate_curiosity"):
                        try:
                            est_c, est_u = self.estimator.estimate_curiosity(context={"affective_state": affective})
                            est_c = max(0.0, min(1.0, float(est_c)))
                            metrics.curiosity_raw = est_c
                            metrics.curiosity_reward = est_c
                            metrics.curiosity_estimator = "estimated_llm"
                            metrics.curiosity_uncertainty = max(0.0, min(1.0, float(est_u)))
                        except Exception as e:
                            logger.debug(f"Curiosity estimation failed: {e}")
                            metrics.curiosity_reward = 0.5
                            metrics.curiosity_estimator = "unavailable"
                    else:
                        metrics.curiosity_reward = 0.5
                        metrics.curiosity_estimator = "unavailable"
            except Exception as e:
                logger.debug(f"Error getting curiosity signal: {e}")
                metrics.curiosity_reward = 0.5  # Default moderate
                metrics.curiosity_estimator = "unavailable"
        else:
            metrics.curiosity_reward = 0.5  # Default moderate if unavailable
            metrics.curiosity_estimator = "unavailable"
        
        # 4. Information gain reward: information_gain (maximize info gain = maximize reward)
        if information_gain is not None:
            metrics.info_gain_source = "provided"
            try:
                metrics.info_gain_raw = max(0.0, min(1.0, float(information_gain)))
            except Exception:
                metrics.info_gain_raw = None
            metrics.information_gain_reward = max(0.0, min(1.0, information_gain))
            metrics.info_gain_has_data = True
            metrics.info_gain_estimator = "provided"
            metrics.info_gain_uncertainty = _meas_unc("high")
        elif self.epistemic_bridge:
            try:
                info = None
                if hasattr(self.epistemic_bridge, "get_information_gain_info"):
                    info = self.epistemic_bridge.get_information_gain_info()
                if isinstance(info, dict):
                    metrics.info_gain_source = "epistemic_bridge"
                    metrics.info_gain_has_data = bool(info.get("has_data", False))
                    metrics.info_gain_estimator = str(info.get("estimator", "epistemic_bridge"))
                    sample_size = info.get("sample_size")
                    try:
                        sample_size_i = int(sample_size) if sample_size is not None else None
                    except Exception:
                        sample_size_i = None
                    val = info.get("value")
                    if metrics.info_gain_has_data and val is not None:
                        try:
                            metrics.info_gain_raw = max(0.0, min(1.0, float(val)))
                        except Exception:
                            metrics.info_gain_raw = None
                        metrics.information_gain_reward = max(0.0, min(1.0, float(metrics.info_gain_raw or 0.0)))
                        # Measurement uncertainty for info gain depends on sample size and estimator quality.
                        est = str(metrics.info_gain_estimator or "")
                        q = "high"
                        if est == "estimated_inputs":
                            q = "low"
                        metrics.info_gain_uncertainty = _meas_unc(q, sample_size=sample_size_i)
                    else:
                        # Missing/low-quality epistemic info gain -> estimate if possible.
                        if self.estimator and hasattr(self.estimator, "estimate_information_gain"):
                            try:
                                est_ig, est_u = self.estimator.estimate_information_gain(context={"epistemic_info": info})
                                est_ig = max(0.0, min(1.0, float(est_ig)))
                                metrics.info_gain_raw = est_ig
                                metrics.information_gain_reward = est_ig
                                metrics.info_gain_estimator = "estimated_llm"
                                metrics.info_gain_uncertainty = max(0.0, min(1.0, float(est_u)))
                            except Exception as e:
                                logger.debug(f"Info gain estimation failed: {e}")
                                metrics.info_gain_source = "unavailable"
                                metrics.information_gain_reward = 0.0
                                metrics.info_gain_estimator = "unavailable"
                        else:
                            metrics.info_gain_source = "unavailable"
                            metrics.information_gain_reward = 0.0
                            metrics.info_gain_estimator = "unavailable"
                else:
                    info_gain = self.epistemic_bridge.get_information_gain()
                    metrics.info_gain_source = "epistemic_bridge"
                    try:
                        metrics.info_gain_raw = max(0.0, min(1.0, float(info_gain)))
                    except Exception:
                        metrics.info_gain_raw = None
                    metrics.information_gain_reward = max(0.0, min(1.0, float(info_gain)))
                    metrics.info_gain_has_data = True
                    metrics.info_gain_estimator = "epistemic_bridge"
                    metrics.info_gain_uncertainty = _meas_unc("medium")
            except Exception as e:
                logger.debug(f"Error getting information gain signal: {e}")
                metrics.info_gain_source = "error"
                metrics.information_gain_reward = 0.0  # Default no gain
                metrics.info_gain_has_data = None
                metrics.info_gain_estimator = "unavailable"
        else:
            metrics.info_gain_source = "unavailable"
            metrics.information_gain_reward = 0.0  # Default no gain if unavailable
            metrics.info_gain_has_data = None
            metrics.info_gain_estimator = "unavailable"
        
        # 5. Coherence reward: coherence_pleasure (maximize coherence = maximize reward)
        if affective_state:
            coherence = affective_state.get("coherence_pleasure", 0.0)
            try:
                metrics.coherence_raw = max(0.0, min(1.0, float(coherence)))
            except Exception:
                metrics.coherence_raw = None
            metrics.coherence_reward = max(0.0, min(1.0, coherence))
            q = (affective_state.get("data_quality") or {}).get("coherence_pleasure") if isinstance(affective_state.get("data_quality"), dict) else None
            metrics.coherence_data_quality = q
            metrics.coherence_has_data = _quality_is_usable(q)
            metrics.coherence_estimator = "affective" if metrics.coherence_has_data else None
            metrics.coherence_uncertainty = _meas_unc(q)
        elif self.affective_monitor:
            try:
                affective = self.affective_monitor.sample_affective_state()
                coherence = affective.get("coherence_pleasure", 0.0)
                try:
                    metrics.coherence_raw = max(0.0, min(1.0, float(coherence)))
                except Exception:
                    metrics.coherence_raw = None
                q = (affective.get("data_quality") or {}).get("coherence_pleasure") if isinstance(affective.get("data_quality"), dict) else None
                metrics.coherence_data_quality = q
                metrics.coherence_has_data = _quality_is_usable(q)
                if metrics.coherence_has_data:
                    metrics.coherence_reward = max(0.0, min(1.0, coherence))
                    metrics.coherence_estimator = "affective"
                    metrics.coherence_uncertainty = _meas_unc(q)
                else:
                    if self.estimator and hasattr(self.estimator, "estimate_coherence"):
                        try:
                            est_coh, est_u = self.estimator.estimate_coherence(context={"affective_state": affective})
                            est_coh = max(0.0, min(1.0, float(est_coh)))
                            metrics.coherence_raw = est_coh
                            metrics.coherence_reward = est_coh
                            metrics.coherence_estimator = "estimated_llm"
                            metrics.coherence_uncertainty = max(0.0, min(1.0, float(est_u)))
                        except Exception as e:
                            logger.debug(f"Coherence estimation failed: {e}")
                            metrics.coherence_reward = 0.5
                            metrics.coherence_estimator = "unavailable"
                    else:
                        metrics.coherence_reward = 0.5
                        metrics.coherence_estimator = "unavailable"
            except Exception as e:
                logger.debug(f"Error getting coherence signal: {e}")
                metrics.coherence_reward = 0.5  # Default moderate
                metrics.coherence_estimator = "unavailable"
        else:
            metrics.coherence_reward = 0.5  # Default moderate if unavailable
            metrics.coherence_estimator = "unavailable"
        
        # Compute composite reward
        metrics.compute_composite()

        # Epistemic uncertainty (separate from measurement uncertainty)
        if self.epistemic_bridge and hasattr(self.epistemic_bridge, "get_aggregated_uncertainty"):
            try:
                eu = self.epistemic_bridge.get_aggregated_uncertainty()
                if isinstance(eu, dict):
                    metrics.epistemic_uncertainty_total = eu.get("total")
                    metrics.epistemic_uncertainty_epistemic = eu.get("epistemic")
                    metrics.epistemic_uncertainty_aleatoric = eu.get("aleatoric")
                    metrics.epistemic_uncertainty_model = eu.get("model")
                    metrics.epistemic_uncertainty_data_quality = eu.get("data_quality")
                    try:
                        metrics.epistemic_uncertainty_sample_size = int(eu.get("sample_size", 0) or 0)
                    except Exception:
                        metrics.epistemic_uncertainty_sample_size = None
                    try:
                        metrics.epistemic_uncertainty_has_data = bool(eu.get("has_data", False))
                    except Exception:
                        metrics.epistemic_uncertainty_has_data = None
            except Exception:
                pass
        
        logger.info(
            f"RL signals computed: composite={metrics.composite_reward:.4f}, "
            f"dissonance={metrics.dissonance_reward:.4f}, surprise={metrics.surprise_reward:.4f}, "
            f"curiosity={metrics.curiosity_reward:.4f}, info_gain={metrics.information_gain_reward:.4f}, "
            f"coherence={metrics.coherence_reward:.4f}, exploration_balance={metrics.get_exploration_exploitation_balance():.4f}",
            extra={
                "event": "rl_signals_computed",
                "composite_reward": metrics.composite_reward,
                "dissonance_reward": metrics.dissonance_reward,
                "surprise_reward": metrics.surprise_reward,
                "curiosity_reward": metrics.curiosity_reward,
                "information_gain_reward": metrics.information_gain_reward,
                "coherence_reward": metrics.coherence_reward,
                "exploration_balance": metrics.get_exploration_exploitation_balance(),
                "has_dissonance": dissonance_metrics is not None or self.cognitive_dissonance_monitor is not None,
                "has_affective": affective_state is not None or self.affective_monitor is not None,
                "has_prediction_error": prediction_error is not None or self.predictive_interoception is not None,
                "has_info_gain": information_gain is not None or self.epistemic_bridge is not None,
            }
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
        # Primary driver: curiosity (intrinsic motivation)
        try:
            metrics = self.compute_signals()
            if metrics.curiosity_reward >= threshold:
                return True
        except Exception:
            pass

        # Fallback: exploration/exploitation balance
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

