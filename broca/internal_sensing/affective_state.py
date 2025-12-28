"""
Affective state monitoring for internal sensing.

Monitors affective states including valence, arousal, curiosity, and satisfaction.
"""

from __future__ import annotations
from .response_analyzer import ResponseAnalyzer

import time
import logging
import math
from collections import deque
from typing import Dict, Any, List, Optional, TYPE_CHECKING, Union
from datetime import datetime, timezone

# Import data quality utilities
try:
    from .data_quality import (
        DataQuality,
        assess_data_quality,
        uncertainty_for_missing_data,
    )
    HAS_DATA_QUALITY = True
except ImportError:
    HAS_DATA_QUALITY = False

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None  # type: ignore

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

if TYPE_CHECKING:
    from .cognitive_state import CognitiveStateMonitor

logger = logging.getLogger(__name__)


class ComputationalAffectMonitor:
    """
    Monitor computational affective states.
    
    Tracks:
    - Valence: Positive/negative evaluation (-1 to 1)
    - Arousal: Activation level (0-1)
    - Certainty affect: Emotional aspect of confidence
    - Curiosity drive: Motivation to explore
    - Coherence pleasure: Satisfaction from understanding
    """
    
    def __init__(self, moving_avg_window: int = 20) -> None:
        """
        Initialize computational affect monitor.
        
        Args:
            moving_avg_window: Number of samples to include in moving average
        """
        # Initialize with default neutral values (never None)
        self.affective_states: Dict[str, Any] = {
            "valence": 0.0,  # Neutral (range: -1 to 1)
            "valence_dimensions": {  # Multi-dimensional valence tracking
                "achievement": 0.0,  # Task success/failure (-1 to 1)
                "social": 0.0,  # Social/interaction quality (-1 to 1)
                "epistemic": 0.0,  # Knowledge/understanding quality (-1 to 1)
            },
            "arousal": 0.5,  # Moderate (range: 0 to 1)
            "certainty_affect": 0.5,  # Moderate (range: 0 to 1)
            "curiosity_drive": 0.5,  # Moderate (range: 0 to 1)
            "coherence_pleasure": 0.5,  # Moderate (range: 0 to 1)
            "surprise": 0.0,  # No surprise initially (range: 0 to 1)
            "surprise_short_term": 0.0,  # Immediate surprise
            "surprise_long_term": 0.0,  # Trend-based surprise
        }
        
        # Moving average tracking for each metric
        self._moving_avg_window = moving_avg_window
        self._valence_history: deque = deque(maxlen=moving_avg_window)
        self._valence_timestamps: deque = deque(maxlen=moving_avg_window)  # For temporal dynamics
        self._valence_dimensions_history: Dict[str, deque] = {
            "achievement": deque(maxlen=moving_avg_window),
            "social": deque(maxlen=moving_avg_window),
            "epistemic": deque(maxlen=moving_avg_window),
        }
        self._arousal_history: deque = deque(maxlen=moving_avg_window)
        self._certainty_affect_history: deque = deque(maxlen=moving_avg_window)
        self._curiosity_drive_history: deque = deque(maxlen=moving_avg_window)
        self._coherence_pleasure_history: deque = deque(maxlen=moving_avg_window)
        self._surprise_history: deque = deque(maxlen=moving_avg_window)
        self._surprise_short_term_history: deque = deque(maxlen=5)  # Short window for immediate surprise
        self._surprise_long_term_history: deque = deque(maxlen=moving_avg_window)  # Long window for trend
        
        # DO NOT initialize moving averages with baseline values
        # This was causing values to get "stuck" at baseline when real values matched baseline
        # Instead, let moving averages build naturally from actual recorded data
        # The affective_states dictionary still has defaults which will be used until data is recorded
        
        self._motivational_drives: Dict[str, float] = {}
        # Use bounded deque to prevent unbounded memory growth
        # Limit to last 1000 satisfaction/frustration patterns
        self._satisfaction_patterns: deque = deque(maxlen=1000)
        
        # Context tracking for context-aware valence
        self._recent_tool_outcomes: deque = deque(maxlen=20)  # Track recent tool success/failure
        self._recent_task_context: deque = deque(maxlen=10)  # Track task context
        
        # Embedding service for semantic analysis (optional)
        self._embedding_service: Optional[Any] = None
        
        # Epistemic bridge for second-order metacognition (optional)
        self._epistemic_bridge: Optional[Any] = None
        
        # Emotional appraisal and regulation (optional, for dissonance/learning integration)
        self._emotional_appraisal_engine: Optional[Any] = None
        self._emotional_regulator: Optional[Any] = None
        
        # Emotional regulation history
        self._regulation_history: deque = deque(maxlen=100)
        
        # Signal manager for damping (optional)
        self._signal_manager: Optional[Any] = None
        
        logger.info("Initialized ComputationalAffectMonitor")
    
    def set_embedding_service(self, embedding_service: Optional[Any]) -> None:
        """
        Set embedding service for semantic analysis.
        
        Args:
            embedding_service: Embedding service with generate_embedding method
        """
        self._embedding_service = embedding_service
    
    def set_epistemic_bridge(self, epistemic_bridge: Optional[Any]) -> None:
        """
        Set epistemic bridge for second-order metacognition integration.
        
        Args:
            epistemic_bridge: EpistemicBridge instance
        """
        self._epistemic_bridge = epistemic_bridge
        logger.info("Set epistemic bridge for ComputationalAffectMonitor")
    
    def set_emotional_appraisal_engine(self, appraisal_engine: Optional[Any]) -> None:
        """
        Set emotional appraisal engine for cognitive dissonance integration.
        
        Args:
            appraisal_engine: CognitiveAppraisalEngine instance
        """
        self._emotional_appraisal_engine = appraisal_engine
        logger.info("Set emotional appraisal engine for ComputationalAffectMonitor")
    
    def set_emotional_regulator(self, regulator: Optional[Any]) -> None:
        """
        Set emotional regulator for homeostatic regulation.
        
        Args:
            regulator: HomeostaticEmotionalRegulator instance
        """
        self._emotional_regulator = regulator
        logger.info("Set emotional regulator for ComputationalAffectMonitor")
    
    def _compute_exponential_weighted_average(self, history: deque, timestamps: Optional[deque] = None, decay_rate: float = 0.1) -> float:
        """
        Compute exponential weighted average with recency weighting.
        
        Args:
            history: History of values
            timestamps: Optional timestamps for temporal weighting
            decay_rate: Exponential decay rate (higher = more weight on recent)
            
        Returns:
            Weighted average
        """
        if len(history) == 0:
            return 0.0
        
        if timestamps is None or len(timestamps) == 0:
            # Simple exponential weighting by position (most recent = highest weight)
            weights = [math.exp(-decay_rate * (len(history) - i - 1)) for i in range(len(history))]
            total_weight = sum(weights)
            weighted_sum = sum(val * weight for val, weight in zip(history, weights))
            return weighted_sum / total_weight if total_weight > 0 else 0.0
        else:
            # Temporal weighting based on actual timestamps
            current_time = time.time()
            weights = []
            values = list(history)
            ts_list = list(timestamps)
            
            for i, ts in enumerate(ts_list):
                time_diff = current_time - ts
                weight = math.exp(-decay_rate * time_diff)
                weights.append(weight)
            
            total_weight = sum(weights)
            weighted_sum = sum(val * weight for val, weight in zip(values, weights))
            return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _compute_semantic_valence(self, text: str) -> Optional[float]:
        """
        Compute valence using embedding-based semantic analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Valence score (-1.0 to 1.0) or None if unavailable
        """
        if not self._embedding_service or not text:
            return None
        
        try:
            # Generate embedding for the text
            embedding = self._embedding_service.generate_embedding(text)
            if not embedding:
                return None
            
            # Positive and negative reference embeddings (simple approach)
            # In a more sophisticated system, these could be learned or context-dependent
            positive_refs = [
                "This is great! Excellent work. Success!",
                "Perfect! Well done. I'm happy with this.",
                "Wonderful! This is exactly what I needed."
            ]
            negative_refs = [
                "This is bad. Failure. Error occurred.",
                "This is wrong. I'm disappointed.",
                "This didn't work. Something went wrong."
            ]
            
            # Compute similarity to positive and negative references
            positive_similarities = []
            negative_similarities = []
            
            for pos_ref in positive_refs:
                try:
                    pos_emb = self._embedding_service.generate_embedding(pos_ref)
                    if pos_emb and np is not None:
                        similarity = ResponseAnalyzer.calculate_semantic_distance(embedding, pos_emb)
                        # Convert distance to similarity (1 - distance)
                        positive_similarities.append(1.0 - similarity)
                except Exception:
                    pass
            
            for neg_ref in negative_refs:
                try:
                    neg_emb = self._embedding_service.generate_embedding(neg_ref)
                    if neg_emb and np is not None:
                        similarity = ResponseAnalyzer.calculate_semantic_distance(embedding, neg_emb)
                        # Convert distance to similarity (1 - distance)
                        negative_similarities.append(1.0 - similarity)
                except Exception:
                    pass
            
            if not positive_similarities and not negative_similarities:
                return None
            
            avg_positive = sum(positive_similarities) / len(positive_similarities) if positive_similarities else 0.0
            avg_negative = sum(negative_similarities) / len(negative_similarities) if negative_similarities else 0.0
            
            # Valence is difference normalized to -1 to 1
            if avg_positive + avg_negative == 0:
                return 0.0
            
            valence = (avg_positive - avg_negative) / (avg_positive + avg_negative)
            return max(-1.0, min(1.0, valence))
            
        except Exception as e:
            logger.debug(f"Error computing semantic valence: {e}")
            return None
    
    def record_tool_outcome(self, tool_name: str, success: bool, context: Optional[str] = None, reliability: Optional[float] = None) -> None:
        """
        Record tool execution outcome for context-aware valence.
        
        Args:
            tool_name: Name of the tool
            success: Whether execution was successful
            context: Optional context about the task
            reliability: Optional tool reliability from epistemic engine (0.0-1.0)
        """
        # Get reliability from epistemic bridge if not provided
        if reliability is None and self._epistemic_bridge:
            reliability = self._epistemic_bridge.get_tool_reliability(tool_name)
        
        self._recent_tool_outcomes.append({
            "tool_name": tool_name,
            "success": success,
            "timestamp": time.time(),
            "context": context,
            "reliability": reliability,
        })
    
    def record_task_context(self, task_type: str, success: Optional[bool] = None) -> None:
        """
        Record task context for context-aware valence.
        
        Args:
            task_type: Type of task (e.g., "code_generation", "question_answering")
            success: Optional success indicator
        """
        self._recent_task_context.append({
            "task_type": task_type,
            "success": success,
            "timestamp": time.time(),
        })
    
    def _compute_context_aware_valence_adjustment(self) -> float:
        """
        Compute valence adjustment based on context (tool outcomes, task success).
        
        Returns:
            Adjustment factor (-1.0 to 1.0)
        """
        if len(self._recent_tool_outcomes) == 0 and len(self._recent_task_context) == 0:
            return 0.0
        
        adjustment = 0.0
        weight_sum = 0.0
        
        # Weight recent outcomes more heavily
        current_time = time.time()
        for outcome in self._recent_tool_outcomes:
            age = current_time - outcome.get("timestamp", current_time)
            weight = math.exp(-0.1 * age)  # Exponential decay
            if outcome.get("success", False):
                adjustment += weight * 0.3  # Positive adjustment for success
            else:
                adjustment -= weight * 0.3  # Negative adjustment for failure
            weight_sum += weight
        
        for context in self._recent_task_context:
            age = current_time - context.get("timestamp", current_time)
            weight = math.exp(-0.1 * age)
            success = context.get("success")
            if success is True:
                adjustment += weight * 0.2
            elif success is False:
                adjustment -= weight * 0.2
            weight_sum += weight
        
        if weight_sum > 0:
            adjustment = adjustment / weight_sum
        
        return max(-1.0, min(1.0, adjustment))
    
    def compute_valence(self, positive_score: float, negative_score: float, 
                       context_adjustment: Optional[float] = None) -> None:
        """
        Compute valence from positive and negative scores using temporal dynamics.
        
        Args:
            positive_score: Positive evaluation score (0.0-1.0)
            negative_score: Negative evaluation score (0.0-1.0)
            context_adjustment: Optional context-based adjustment (-1.0 to 1.0)
        """
        positive_score = max(0.0, min(1.0, positive_score))
        negative_score = max(0.0, min(1.0, negative_score))
        
        # Valence is difference: positive - negative, normalized to -1 to 1
        if positive_score + negative_score == 0:
            valence = 0.0
        else:
            valence = (positive_score - negative_score) / (positive_score + negative_score)
        
        valence = max(-1.0, min(1.0, valence))
        
        # Apply context adjustment if provided
        if context_adjustment is not None:
            valence = max(-1.0, min(1.0, valence + context_adjustment * 0.3))
        
        # Update with temporal dynamics (exponential weighted average)
        self._valence_history.append(valence)
        self._valence_timestamps.append(time.time())
        
        if len(self._valence_history) > 0:
            # Use exponential weighted average instead of simple moving average
            raw_valence = self._compute_exponential_weighted_average(
                self._valence_history, 
                self._valence_timestamps,
                decay_rate=0.15  # Higher decay = more weight on recent
            )
            # Update through SignalManager if available (hybrid approach)
            self.affective_states["valence"] = self._update_damped_signal("affect.valence", raw_valence)
    
    
    def compute_valence_from_text(self, text: str, use_semantic: bool = True) -> None:
        """
        Compute valence directly from text using VADER, semantic analysis, and context.
        
        Args:
            text: Text to analyze
            use_semantic: Whether to use semantic (embedding-based) analysis
        """
        if not text:
            return
        
        valence = None
        semantic_valence = None
        
        # Try VADER first (fast, lexical-based)
        vader_scores = ResponseAnalyzer.analyze_sentiment_vader(text)
        if vader_scores:
            # VADER compound score is -1.0 to 1.0
            valence = max(-1.0, min(1.0, vader_scores['compound']))
        # Fallback to TextBlob
        elif TextBlob is not None:
            try:
                blob = TextBlob(text)
                valence = max(-1.0, min(1.0, blob.sentiment.polarity))
            except Exception:
                pass
        
        # Try semantic analysis if available (more nuanced, context-aware)
        if use_semantic:
            semantic_valence = self._compute_semantic_valence(text)
        
        # Combine lexical and semantic valence (weighted average)
        if valence is not None and semantic_valence is not None:
            # Weight: 60% semantic (more nuanced), 40% lexical (faster, more reliable for clear cases)
            final_valence = (semantic_valence * 0.6) + (valence * 0.4)
        elif semantic_valence is not None:
            final_valence = semantic_valence
        elif valence is not None:
            final_valence = valence
        else:
            return  # No valence computed
        
        # Apply context-aware adjustment
        context_adj = self._compute_context_aware_valence_adjustment()
        if context_adj != 0.0:
            final_valence = max(-1.0, min(1.0, final_valence + context_adj * 0.2))
        
        # Update with temporal dynamics (exponential weighted average)
        old_valence = self.affective_states.get("valence", 0.0)
        self._valence_history.append(final_valence)
        self._valence_timestamps.append(time.time())
        
        if len(self._valence_history) > 0:
            new_valence = self._compute_exponential_weighted_average(
                self._valence_history,
                self._valence_timestamps,
                decay_rate=0.15
            )
            # Update through SignalManager if available (hybrid approach)
            damped_valence = self._update_damped_signal("affect.valence", new_valence)
            self.affective_states["valence"] = damped_valence
            logger.debug(f"Updated valence: {old_valence:.3f} -> {new_valence:.3f} -> {damped_valence:.3f} (computed={final_valence:.3f}, semantic={semantic_valence}, context_adj={context_adj:.3f}, history_len={len(self._valence_history)})")

    
    def compute_valence_from_conversation_history(self, messages: List[Dict[str, Any]], 
                                                  use_semantic: bool = True) -> None:
        """
        Compute valence from conversation history with context awareness.
        
        Args:
            messages: List of message dictionaries with "role" and "content" keys
            use_semantic: Whether to use semantic analysis
        """
        if not messages:
            # Empty conversation - don't update (keep existing moving average)
            logger.debug("compute_valence_from_conversation_history: empty messages, keeping existing moving average")
            return
        
        # Filter out system and tool messages, keep only user and assistant
        conversation_texts = []
        user_messages = []
        assistant_messages = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Only include user and assistant messages
            if role in ("user", "assistant") and content:
                conversation_texts.append(str(content))
                if role == "user":
                    user_messages.append(str(content))
                elif role == "assistant":
                    assistant_messages.append(str(content))
        
        if not conversation_texts:
            # No user/assistant messages - don't update (keep existing moving average)
            logger.debug("compute_valence_from_conversation_history: no user/assistant messages, keeping existing moving average")
            return
        
        # Compute multi-dimensional valence
        # Achievement: Based on task completion, tool success
        achievement_valence = 0.0
        if len(self._recent_tool_outcomes) > 0:
            recent_successes = sum(1 for o in self._recent_tool_outcomes if o.get("success", False))
            recent_total = len(self._recent_tool_outcomes)
            if recent_total > 0:
                achievement_valence = (recent_successes / recent_total) * 2.0 - 1.0  # -1 to 1
            
            # Enhance with epistemic tool reliability if available
            if self._epistemic_bridge:
                epistemic_context = self._epistemic_bridge.get_epistemic_valence_context()
                tool_success_rate = epistemic_context.get("tool_success_rate", 0.5)
                # Blend achievement valence with epistemic tool success rate
                achievement_valence = (achievement_valence * 0.7) + ((tool_success_rate * 2.0 - 1.0) * 0.3)
        
        # Social: Based on user-assistant interaction quality
        social_valence = 0.0
        if user_messages and assistant_messages:
            # Analyze last few exchanges for social quality
            recent_user = " ".join(user_messages[-3:]) if len(user_messages) >= 3 else " ".join(user_messages)
            recent_assistant = " ".join(assistant_messages[-3:]) if len(assistant_messages) >= 3 else " ".join(assistant_messages)
            # Use sentiment of both sides
            user_sentiment = ResponseAnalyzer.analyze_sentiment_vader(recent_user)
            assistant_sentiment = ResponseAnalyzer.analyze_sentiment_vader(recent_assistant)
            if user_sentiment and assistant_sentiment:
                # Social valence is average of both, weighted toward user
                social_valence = (user_sentiment['compound'] * 0.7 + assistant_sentiment['compound'] * 0.3)
        
        # Epistemic: Based on understanding, coherence, confidence
        epistemic_valence = 0.0
        # This will be updated from cognitive states in update_from_cognitive
        
        # Update dimension histories
        self._valence_dimensions_history["achievement"].append(achievement_valence)
        self._valence_dimensions_history["social"].append(social_valence)
        self._valence_dimensions_history["epistemic"].append(epistemic_valence)
        
        # Compute overall valence from dimensions (weighted average)
        dim_weights = {"achievement": 0.4, "social": 0.3, "epistemic": 0.3}
        overall_valence = (
            achievement_valence * dim_weights["achievement"] +
            social_valence * dim_weights["social"] +
            epistemic_valence * dim_weights["epistemic"]
        )
        
        # Also compute from text for comparison/validation
        combined_text = " ".join(conversation_texts)
        logger.debug(f"compute_valence_from_conversation_history: processing {len(conversation_texts)} messages, total_length={len(combined_text)}")
        
        # Compute text-based valence
        text_valence = None
        vader_scores = ResponseAnalyzer.analyze_sentiment_vader(combined_text)
        if vader_scores:
            text_valence = vader_scores['compound']
        
        # Combine dimension-based and text-based (dimension-based is more context-aware)
        if text_valence is not None:
            final_valence = (overall_valence * 0.7) + (text_valence * 0.3)
        else:
            final_valence = overall_valence
        
        # Apply context adjustment
        context_adj = self._compute_context_aware_valence_adjustment()
        if context_adj != 0.0:
            final_valence = max(-1.0, min(1.0, final_valence + context_adj * 0.2))
        
        # Update with temporal dynamics
        old_valence = self.affective_states.get("valence", 0.0)
        self._valence_history.append(final_valence)
        self._valence_timestamps.append(time.time())
        
        if len(self._valence_history) > 0:
            new_valence = self._compute_exponential_weighted_average(
                self._valence_history,
                self._valence_timestamps,
                decay_rate=0.15
            )
            # Update through SignalManager if available (hybrid approach)
            damped_valence = self._update_damped_signal("affect.valence", new_valence)
            self.affective_states["valence"] = damped_valence
            
            # Update dimension states
            for dim in ["achievement", "social", "epistemic"]:
                if len(self._valence_dimensions_history[dim]) > 0:
                    dim_avg = self._compute_exponential_weighted_average(
                        self._valence_dimensions_history[dim],
                        None,  # No timestamps for dimensions yet
                        decay_rate=0.15
                    )
                    self.affective_states["valence_dimensions"][dim] = dim_avg
            
            logger.debug(f"Updated valence: {old_valence:.3f} -> {new_valence:.3f} (dims: achievement={achievement_valence:.3f}, social={social_valence:.3f}, epistemic={epistemic_valence:.3f}, context_adj={context_adj:.3f})")
    
    def compute_arousal(self, activation_level: float, 
                       task_complexity: Optional[float] = None,
                       resource_pressure: Optional[float] = None,
                       cognitive_load: Optional[float] = None,
                       tool_call_count: Optional[int] = None,
                       reasoning_steps: Optional[int] = None) -> None:
        """
        Compute arousal from activation level with context integration.
        
        Args:
            activation_level: Base activation level (0.0-1.0)
            task_complexity: Optional task complexity factor (0.0-1.0)
            resource_pressure: Optional computational resource pressure (0.0-1.0)
            cognitive_load: Optional cognitive load indicator (0.0-1.0)
            tool_call_count: Optional number of tool calls in current operation
            reasoning_steps: Optional number of reasoning steps
        """
        base_arousal = max(0.0, min(1.0, activation_level))
        
        # Integrate task complexity (more complex tasks = higher arousal)
        complexity_factor = 0.0
        if task_complexity is not None:
            complexity_factor = task_complexity * 0.2  # Up to 20% increase
        
        # Integrate resource pressure (high pressure = higher arousal)
        pressure_factor = 0.0
        if resource_pressure is not None:
            pressure_factor = resource_pressure * 0.15  # Up to 15% increase
        
        # Integrate cognitive load (high load = higher arousal)
        load_factor = 0.0
        if cognitive_load is not None:
            load_factor = cognitive_load * 0.15  # Up to 15% increase
        
        # Integrate tool call count (more tools = higher arousal)
        tool_factor = 0.0
        if tool_call_count is not None:
            # Normalize: 0 tools = 0, 5+ tools = 1.0
            normalized_tools = min(1.0, tool_call_count / 5.0)
            tool_factor = normalized_tools * 0.1  # Up to 10% increase
        
        # Integrate reasoning steps (more steps = higher arousal)
        reasoning_factor = 0.0
        if reasoning_steps is not None:
            # Normalize: 0 steps = 0, 10+ steps = 1.0
            normalized_steps = min(1.0, reasoning_steps / 10.0)
            reasoning_factor = normalized_steps * 0.1  # Up to 10% increase
        
        # Combine all factors
        arousal = base_arousal + complexity_factor + pressure_factor + load_factor + tool_factor + reasoning_factor
        arousal = max(0.0, min(1.0, arousal))
        
        logger.debug(f"compute_arousal: base={base_arousal:.3f}, complexity={complexity_factor:.3f}, "
                    f"pressure={pressure_factor:.3f}, load={load_factor:.3f}, tools={tool_factor:.3f}, "
                    f"reasoning={reasoning_factor:.3f}, final={arousal:.3f}")
        
        # Update moving average
        old_arousal = self.affective_states.get("arousal", 0.5)
        self._arousal_history.append(arousal)
        if len(self._arousal_history) > 0:
            new_arousal = sum(self._arousal_history) / len(self._arousal_history)
            # Update through SignalManager if available (hybrid approach)
            damped_arousal = self._update_damped_signal("affect.arousal", new_arousal)
            self.affective_states["arousal"] = damped_arousal
            logger.debug(f"Updated arousal: {old_arousal:.3f} -> {new_arousal:.3f} -> {damped_arousal:.3f} (computed={arousal:.3f}, history_len={len(self._arousal_history)})")
    
    def update_certainty_affect(self, confidence: float, 
                                calibration_error: Optional[float] = None,
                                confidence_accuracy_correlation: Optional[float] = None) -> None:
        """
        Update certainty affect from confidence with calibration awareness.
        
        Args:
            confidence: Confidence level (0.0-1.0)
            calibration_error: Optional Expected Calibration Error (ECE) (0.0-1.0, lower is better)
            confidence_accuracy_correlation: Optional correlation between confidence and accuracy (-1.0 to 1.0)
        """
        base_certainty = max(0.0, min(1.0, confidence))
        
        # Adjust based on calibration quality
        # If poorly calibrated, reduce certainty affect (uncertainty about certainty)
        calibration_adjustment = 0.0
        if calibration_error is not None:
            # High calibration error = low trust in confidence estimates
            # Reduce certainty affect proportionally
            calibration_adjustment = -calibration_error * 0.3  # Up to 30% reduction
        
        # Adjust based on confidence-accuracy correlation
        correlation_adjustment = 0.0
        if confidence_accuracy_correlation is not None:
            # Positive correlation = good, negative = bad
            # If correlation is low/negative, reduce certainty affect
            if confidence_accuracy_correlation < 0.5:
                correlation_adjustment = -(0.5 - confidence_accuracy_correlation) * 0.2  # Up to 20% reduction
        
        # Combine adjustments
        certainty = base_certainty + calibration_adjustment + correlation_adjustment
        certainty = max(0.0, min(1.0, certainty))
        
        logger.debug(f"update_certainty_affect: base={base_certainty:.3f}, calibration_adj={calibration_adjustment:.3f}, "
                    f"correlation_adj={correlation_adjustment:.3f}, final={certainty:.3f}")
        
        # Update moving average
        self._certainty_affect_history.append(certainty)
        if len(self._certainty_affect_history) > 0:
            self.affective_states["certainty_affect"] = sum(self._certainty_affect_history) / len(self._certainty_affect_history)
    
    
    def _compute_kl_divergence(self, prior: Dict[str, float], posterior: Dict[str, float]) -> float:
        """
        Compute KL divergence between prior and posterior belief distributions.
        
        Args:
            prior: Prior probability distribution (normalized)
            posterior: Posterior probability distribution (normalized)
            
        Returns:
            KL divergence (0.0-1.0, normalized)
        """
        if not prior or not posterior:
            return 0.0
        
        # Ensure both distributions are normalized
        prior_sum = sum(prior.values())
        posterior_sum = sum(posterior.values())
        
        if prior_sum == 0 or posterior_sum == 0:
            return 0.0
        
        prior_norm = {k: v / prior_sum for k, v in prior.items()}
        posterior_norm = {k: v / posterior_sum for k, v in posterior.items()}
        
        # Compute KL divergence: D_KL(posterior || prior)
        kl = 0.0
        all_keys = set(prior_norm.keys()) | set(posterior_norm.keys())
        
        for key in all_keys:
            p_post = posterior_norm.get(key, 1e-10)  # Avoid log(0)
            p_prior = prior_norm.get(key, 1e-10)
            
            if p_post > 0:
                kl += p_post * math.log(p_post / p_prior)
        
        # Normalize KL divergence to 0-1 range (assuming max KL is around 2.0 for practical purposes)
        normalized_kl = min(1.0, kl / 2.0)
        return normalized_kl
    
    def _compute_novelty_from_embeddings(self, new_text: str, recent_texts: List[str]) -> Optional[float]:
        """
        Compute novelty based on embedding distance from recent texts.
        
        Args:
            new_text: New text to evaluate
            recent_texts: List of recent texts for comparison
            
        Returns:
            Novelty score (0.0-1.0) or None if unavailable
        """
        if not self._embedding_service or not new_text or not recent_texts:
            return None
        
        try:
            new_emb = self._embedding_service.generate_embedding(new_text)
            if not new_emb:
                return None
            
            distances = []
            for recent_text in recent_texts[-5:]:  # Compare with last 5 recent texts
                try:
                    recent_emb = self._embedding_service.generate_embedding(recent_text)
                    if recent_emb:
                        distance = ResponseAnalyzer.calculate_semantic_distance(new_emb, recent_emb)
                        distances.append(distance)
                except Exception:
                    pass
            
            if distances:
                # Novelty is average distance (higher distance = more novel)
                avg_distance = sum(distances) / len(distances)
                return avg_distance
            
            return None
        except Exception as e:
            logger.debug(f"Error computing novelty: {e}")
            return None
    
    def compute_curiosity_drive(self, uncertainty: float, interest: float,
                              prediction_error: Optional[float] = None,
                              information_gain: Optional[float] = None,
                              novelty: Optional[float] = None,
                              exploration_ratio: Optional[float] = None) -> None:
        """
        Compute curiosity drive with information-theoretic measures.
        
        Args:
            uncertainty: Uncertainty level (0.0-1.0)
            interest: Interest level (0.0-1.0)
            prediction_error: Optional prediction error from PredictiveInteroception (0.0-1.0)
            information_gain: Optional information gain (KL divergence) (0.0-1.0)
            novelty: Optional novelty score from embeddings (0.0-1.0)
            exploration_ratio: Optional ratio of exploratory vs exploitative actions (0.0-1.0)
        """
        uncertainty = max(0.0, min(1.0, uncertainty))
        interest = max(0.0, min(1.0, interest))
        surprise = self.affective_states.get("surprise", 0.0)
        
        # Get information gain from epistemic bridge if not provided
        if information_gain is None and self._epistemic_bridge:
            information_gain = self._epistemic_bridge.get_information_gain()
        
        # Base curiosity from uncertainty, interest, and surprise
        base_curiosity = (uncertainty * 0.3 + interest * 0.25 + surprise * 0.25)
        
        # Add prediction error as curiosity signal (higher error = more curiosity)
        prediction_factor = 0.0
        if prediction_error is not None:
            prediction_factor = prediction_error * 0.15  # Up to 15% increase
        
        # Add information gain (KL divergence) as curiosity signal
        info_gain_factor = 0.0
        if information_gain is not None:
            info_gain_factor = information_gain * 0.15  # Up to 15% increase
        
        # Add novelty detection as curiosity signal
        novelty_factor = 0.0
        if novelty is not None:
            novelty_factor = novelty * 0.15  # Up to 15% increase
        
        # Adjust based on exploration-exploitation balance
        exploration_factor = 0.0
        if exploration_ratio is not None:
            # Higher exploration ratio = higher curiosity
            exploration_factor = exploration_ratio * 0.1  # Up to 10% increase
        
        # Combine all factors
        curiosity = base_curiosity + prediction_factor + info_gain_factor + novelty_factor + exploration_factor
        curiosity = max(0.0, min(1.0, curiosity))
        
        logger.debug(f"compute_curiosity_drive: base={base_curiosity:.3f}, prediction={prediction_factor:.3f}, "
                    f"info_gain={info_gain_factor:.3f}, novelty={novelty_factor:.3f}, "
                    f"exploration={exploration_factor:.3f}, final={curiosity:.3f}")
        
        # Update moving average
        self._curiosity_drive_history.append(curiosity)
        if len(self._curiosity_drive_history) > 0:
            self.affective_states["curiosity_drive"] = sum(self._curiosity_drive_history) / len(self._curiosity_drive_history)

    
    
    def update_coherence_pleasure(self, coherence: float,
                                 semantic_coherence: Optional[float] = None,
                                 logical_consistency: Optional[float] = None,
                                 understanding_depth: Optional[float] = None,
                                 resolution_satisfaction: Optional[float] = None) -> None:
        """
        Update coherence pleasure with enhanced metrics.
        
        Args:
            coherence: Base coherence level (0.0-1.0)
            semantic_coherence: Optional semantic coherence from embeddings (0.0-1.0)
            logical_consistency: Optional logical consistency score (0.0-1.0)
            understanding_depth: Optional processing depth / reasoning chain length (0.0-1.0)
            resolution_satisfaction: Optional satisfaction from resolving contradictions (0.0-1.0)
        """
        base_coherence = max(0.0, min(1.0, coherence))
        certainty = self.affective_states.get("certainty_affect", 0.5)
        
        # Base pleasure from coherence and certainty
        base_pleasure = (base_coherence * 0.5) + (certainty * 0.2)
        
        # Add semantic coherence if available
        semantic_factor = 0.0
        if semantic_coherence is not None:
            semantic_factor = semantic_coherence * 0.15  # Up to 15% increase
        
        # Add logical consistency if available
        consistency_factor = 0.0
        if logical_consistency is not None:
            consistency_factor = logical_consistency * 0.1  # Up to 10% increase
        
        # Add understanding depth if available
        depth_factor = 0.0
        if understanding_depth is not None:
            depth_factor = understanding_depth * 0.05  # Up to 5% increase
        
        # Add resolution satisfaction if available
        resolution_factor = 0.0
        if resolution_satisfaction is not None:
            resolution_factor = resolution_satisfaction * 0.1  # Up to 10% increase
        
        # Combine all factors
        pleasure = base_pleasure + semantic_factor + consistency_factor + depth_factor + resolution_factor
        pleasure = max(0.0, min(1.0, pleasure))
        
        logger.debug(f"update_coherence_pleasure: base={base_pleasure:.3f}, semantic={semantic_factor:.3f}, "
                    f"consistency={consistency_factor:.3f}, depth={depth_factor:.3f}, "
                    f"resolution={resolution_factor:.3f}, final={pleasure:.3f}")
        
        # Update moving average
        self._coherence_pleasure_history.append(pleasure)
        if len(self._coherence_pleasure_history) > 0:
            self.affective_states["coherence_pleasure"] = sum(self._coherence_pleasure_history) / len(self._coherence_pleasure_history)

    
    
    def update_surprise(self, prediction_error: float,
                       kl_divergence: Optional[float] = None,
                       semantic_surprise: Optional[float] = None,
                       contextual_weight: Optional[float] = None) -> None:
        """
        Update surprise with multi-scale and information-theoretic measures.
        
        Args:
            prediction_error: Base prediction error (0.0-1.0)
            kl_divergence: Optional KL divergence for information-theoretic surprise (0.0-1.0)
            semantic_surprise: Optional semantic surprise from embeddings (0.0-1.0)
            contextual_weight: Optional importance/relevance weight (0.0-1.0)
        """
        base_surprise = max(0.0, min(1.0, prediction_error))
        
        # Use KL divergence if available (more principled than simple difference)
        if kl_divergence is not None:
            # Combine prediction error and KL divergence
            surprise = (base_surprise * 0.6) + (kl_divergence * 0.4)
        else:
            surprise = base_surprise
        
        # Add semantic surprise if available
        if semantic_surprise is not None:
            # Blend semantic and prediction-based surprise
            surprise = (surprise * 0.7) + (semantic_surprise * 0.3)
        
        # Apply contextual weighting (more important surprises count more)
        if contextual_weight is not None:
            surprise = surprise * (0.5 + contextual_weight * 0.5)  # Scale by importance
        
        surprise = max(0.0, min(1.0, surprise))
        
        # Update multi-scale surprise
        # Short-term: immediate surprise (last few samples)
        self._surprise_short_term_history.append(surprise)
        short_term = 0.0
        if len(self._surprise_short_term_history) > 0:
            short_term = sum(self._surprise_short_term_history) / len(self._surprise_short_term_history)
            self.affective_states["surprise_short_term"] = short_term
        
        # Long-term: trend-based surprise (moving average)
        self._surprise_long_term_history.append(surprise)
        long_term = 0.0
        if len(self._surprise_long_term_history) > 0:
            long_term = sum(self._surprise_long_term_history) / len(self._surprise_long_term_history)
            self.affective_states["surprise_long_term"] = long_term
        
        # Overall surprise (weighted combination of short and long term)
        if len(self._surprise_short_term_history) > 0 and len(self._surprise_long_term_history) > 0:
            # Short-term gets more weight (immediate reactions)
            overall_surprise = (short_term * 0.6) + (long_term * 0.4)
        elif len(self._surprise_short_term_history) > 0:
            overall_surprise = short_term
        elif len(self._surprise_long_term_history) > 0:
            overall_surprise = long_term
        else:
            overall_surprise = surprise
        
        # Update moving average
        self._surprise_history.append(overall_surprise)
        if len(self._surprise_history) > 0:
            self.affective_states["surprise"] = sum(self._surprise_history) / len(self._surprise_history)
        
        logger.debug(f"update_surprise: base={base_surprise:.3f}, kl={kl_divergence}, "
                    f"semantic={semantic_surprise}, context={contextual_weight}, "
                    f"short_term={short_term:.3f}, long_term={long_term:.3f}, final={overall_surprise:.3f}")

    def update_from_cognitive(self, cognitive_monitor: "CognitiveStateMonitor") -> None:
        """
        Update affective states from cognitive monitor.
        
        Args:
            cognitive_monitor: CognitiveStateMonitor instance
        """
        # Update certainty affect from confidence (always update, using defaults if None)
        confidence = cognitive_monitor.states.get("confidence_level")
        if confidence is not None:
            logger.debug(f"update_from_cognitive: updating certainty_affect from confidence={confidence:.3f}")
            self.update_certainty_affect(confidence)
        
        # Update coherence pleasure from coherence (always update, using defaults if None)
        coherence = cognitive_monitor.states.get("conceptual_coherence")
        if coherence is not None:
            logger.debug(f"update_from_cognitive: updating coherence_pleasure from coherence={coherence:.3f}")
            self.update_coherence_pleasure(coherence)
        
        # Update curiosity from uncertainty (always update, using defaults if None)
        uncertainty = cognitive_monitor.states.get("uncertainty_tracking", 0.0)
        # Use attention as proxy for interest
        attention_allocation = cognitive_monitor.states.get("attention_allocation", {})
        attention_total = sum(attention_allocation.values())
        interest = min(attention_total, 1.0) if attention_total > 0 else 0.0
        
        # Get prediction error if available from predictive interoception
        # (This would need to be passed in or accessed via a reference)
        prediction_error = None  # Will be set by integrated_interoception if available
        
        logger.debug(f"update_from_cognitive: updating curiosity_drive from uncertainty={uncertainty:.3f}, interest={interest:.3f}")
        self.compute_curiosity_drive(uncertainty, interest, prediction_error=prediction_error)
    
    def record_motivational_drive(self, drive_type: str, level: float) -> None:
        """
        Record a motivational drive.
        
        Args:
            drive_type: Type of drive (e.g., "exploration", "completion")
            level: Drive level (0.0-1.0)
        """
        self._motivational_drives[drive_type] = max(0.0, min(1.0, level))
    
    def get_motivational_drives(self) -> Dict[str, float]:
        """
        Get current motivational drives.
        
        Returns:
            Dictionary of drive types to levels
        """
        return self._motivational_drives.copy()
    
    def record_satisfaction(self, task_id: str, level: float) -> None:
        """
        Record satisfaction level for a task.
        
        Args:
            task_id: Unique identifier for the task
            level: Satisfaction level (0.0-1.0)
        """
        self._satisfaction_patterns.append({
            "task_id": task_id,
            "type": "satisfaction",
            "level": max(0.0, min(1.0, level)),
            "timestamp": time.time(),
        })
    
    def record_frustration(self, task_id: str, level: float) -> None:
        """
        Record frustration level for a task.
        
        Args:
            task_id: Unique identifier for the task
            level: Frustration level (0.0-1.0)
        """
        self._satisfaction_patterns.append({
            "task_id": task_id,
            "type": "frustration",
            "level": max(0.0, min(1.0, level)),
            "timestamp": time.time(),
        })
    
    def get_satisfaction_patterns(self) -> List[Dict[str, Any]]:
        """
        Get satisfaction/frustration patterns.
        
        Returns:
            List of pattern dictionaries
        """
        # Convert deque to list for compatibility
        return list(self._satisfaction_patterns)
    
    def sample_affective_state(self) -> Dict[str, Any]:
        """
        Sample complete affective state.
        
        Returns:
            Dictionary containing all affective states with timestamp.
            All values are computed from temporal dynamics when available,
            otherwise uses defaults until data is recorded.
        """
        # Update states from temporal dynamics when history exists
        # This ensures we return weighted average values when available, defaults otherwise
        if len(self._valence_history) > 0:
            raw_valence = self._compute_exponential_weighted_average(
                self._valence_history, self._valence_timestamps, decay_rate=0.15
            )
            # Update through SignalManager if available (hybrid approach)
            self.affective_states["valence"] = self._update_damped_signal("affect.valence", raw_valence)
            # Update dimensions
            for dim in ["achievement", "social", "epistemic"]:
                if len(self._valence_dimensions_history[dim]) > 0:
                    self.affective_states["valence_dimensions"][dim] = self._compute_exponential_weighted_average(
                        self._valence_dimensions_history[dim], None, decay_rate=0.15
                    )
        if len(self._arousal_history) > 0:
            raw_arousal = sum(self._arousal_history) / len(self._arousal_history)
            # Update through SignalManager if available (hybrid approach)
            self.affective_states["arousal"] = self._update_damped_signal("affect.arousal", raw_arousal)
        if len(self._certainty_affect_history) > 0:
            self.affective_states["certainty_affect"] = sum(self._certainty_affect_history) / len(self._certainty_affect_history)
        if len(self._curiosity_drive_history) > 0:
            self.affective_states["curiosity_drive"] = sum(self._curiosity_drive_history) / len(self._curiosity_drive_history)
        if len(self._coherence_pleasure_history) > 0:
            self.affective_states["coherence_pleasure"] = sum(self._coherence_pleasure_history) / len(self._coherence_pleasure_history)
        if len(self._surprise_history) > 0:
            self.affective_states["surprise"] = sum(self._surprise_history) / len(self._surprise_history)
        if len(self._surprise_short_term_history) > 0:
            self.affective_states["surprise_short_term"] = sum(self._surprise_short_term_history) / len(self._surprise_short_term_history)
        if len(self._surprise_long_term_history) > 0:
            self.affective_states["surprise_long_term"] = sum(self._surprise_long_term_history) / len(self._surprise_long_term_history)
        
        result = {
            **self.affective_states,
            "motivational_drives": self._motivational_drives.copy(),
            "timestamp": time.time(),
        }
        
        # Add data quality indicators
        if HAS_DATA_QUALITY:
            if "data_quality" not in result:
                result["data_quality"] = {}
            
            # Assess data quality for each metric based on history length
            result["data_quality"]["valence"] = assess_data_quality(len(self._valence_history)).value
            result["data_quality"]["arousal"] = assess_data_quality(len(self._arousal_history)).value
            result["data_quality"]["certainty_affect"] = assess_data_quality(len(self._certainty_affect_history)).value
            result["data_quality"]["curiosity_drive"] = assess_data_quality(len(self._curiosity_drive_history)).value
            result["data_quality"]["coherence_pleasure"] = assess_data_quality(len(self._coherence_pleasure_history)).value
            result["data_quality"]["surprise"] = assess_data_quality(len(self._surprise_history)).value
        
        return result
    
    def update_from_epistemic(self) -> None:
        """
        Update affective state from epistemic engine via bridge.
        
        This method should be called periodically to sync with epistemic metrics.
        """
        if not self._epistemic_bridge:
            return
        
        try:
            # Get epistemic confidence for certainty affect
            epistemic_confidence = self._epistemic_bridge.get_aggregated_confidence()
            if epistemic_confidence:
                epistemic_conf = epistemic_confidence.get("overall_confidence", 0.5)
                calibration_error = epistemic_confidence.get("calibration_error")
                reliability = epistemic_confidence.get("reliability")
                
                # Update certainty affect with epistemic metrics
                self.update_certainty_affect(
                    confidence=epistemic_conf,
                    calibration_error=calibration_error,
                    confidence_accuracy_correlation=reliability,
                )
            
            # Get epistemic uncertainty for curiosity drive
            epistemic_uncertainty = self._epistemic_bridge.get_aggregated_uncertainty()
            if epistemic_uncertainty:
                total_uncertainty = epistemic_uncertainty.get("total", 0.0)
                information_gain = self._epistemic_bridge.get_information_gain()
                
                # Use attention as proxy for interest (would need to get from cognitive)
                interest = 0.5  # Default
                
                # Update curiosity drive with epistemic information gain
                self.compute_curiosity_drive(
                    uncertainty=total_uncertainty,
                    interest=interest,
                    information_gain=information_gain,
                )
            
            # Get epistemic valence context for multi-dimensional valence
            epistemic_context = self._epistemic_bridge.get_epistemic_valence_context()
            if epistemic_context:
                # Update epistemic dimension of valence
                knowledge_confidence = epistemic_context.get("knowledge_confidence", 0.5)
                epistemic_valence = (knowledge_confidence - 0.5) * 2.0  # -1 to 1
                
                # Update epistemic dimension history
                self._valence_dimensions_history["epistemic"].append(epistemic_valence)
                
                # Update overall valence if dimensions are being tracked
                if len(self._valence_dimensions_history["epistemic"]) > 0:
                    # Recompute overall valence with updated epistemic dimension
                    dim_weights = {"achievement": 0.4, "social": 0.3, "epistemic": 0.3}
                    achievement = sum(self._valence_dimensions_history["achievement"]) / len(self._valence_dimensions_history["achievement"]) if self._valence_dimensions_history["achievement"] else 0.0
                    social = sum(self._valence_dimensions_history["social"]) / len(self._valence_dimensions_history["social"]) if self._valence_dimensions_history["social"] else 0.0
                    epistemic = sum(self._valence_dimensions_history["epistemic"]) / len(self._valence_dimensions_history["epistemic"])
                    
                    overall_valence = (
                        achievement * dim_weights["achievement"] +
                        social * dim_weights["social"] +
                        epistemic * dim_weights["epistemic"]
                    )
                    
                    # Update valence history
                    self._valence_history.append(overall_valence)
                    self._valence_timestamps.append(time.time())
                    self.affective_states["valence_dimensions"]["epistemic"] = epistemic_valence
            
        except Exception as e:
            logger.warning(f"Error updating affective state from epistemic: {e}", exc_info=True)
    
    def serialize_histories(self) -> Dict[str, Any]:
        """
        Serialize moving average histories for persistence.
        
        Returns:
            Dictionary mapping history names to lists of float values
        """
        result: Dict[str, Any] = {
            "valence_history": list(self._valence_history),
            "valence_timestamps": list(self._valence_timestamps),
            "valence_dimensions_history": {
                dim: list(history) for dim, history in self._valence_dimensions_history.items()
            },
            "arousal_history": list(self._arousal_history),
            "certainty_affect_history": list(self._certainty_affect_history),
            "curiosity_drive_history": list(self._curiosity_drive_history),
            "coherence_pleasure_history": list(self._coherence_pleasure_history),
            "surprise_history": list(self._surprise_history),
            "surprise_short_term_history": list(self._surprise_short_term_history),
            "surprise_long_term_history": list(self._surprise_long_term_history),
        }
        return result
    
    def deserialize_histories(self, histories: Dict[str, Any]) -> None:
        """
        Deserialize moving average histories from persistence.
        
        Args:
            histories: Dictionary mapping history names to lists of float values
        """
        # Restore valence history
        if "valence_history" in histories:
            self._valence_history.clear()
            for value in histories["valence_history"]:
                self._valence_history.append(value)
            if len(self._valence_history) > 0:
                # Use exponential weighted average if timestamps available
                if "valence_timestamps" in histories and len(histories["valence_timestamps"]) == len(self._valence_history):
                    self._valence_timestamps.clear()
                    for ts in histories["valence_timestamps"]:
                        self._valence_timestamps.append(ts)
                    raw_valence = self._compute_exponential_weighted_average(
                        self._valence_history, self._valence_timestamps, decay_rate=0.15
                    )
                else:
                    raw_valence = sum(self._valence_history) / len(self._valence_history)
                # Update through SignalManager if available (hybrid approach)
                self.affective_states["valence"] = self._update_damped_signal("affect.valence", raw_valence)
            logger.debug(f"Restored {len(self._valence_history)} valence history entries")
        
        # Restore valence dimensions history
        if "valence_dimensions_history" in histories:
            dim_histories = histories["valence_dimensions_history"]
            if isinstance(dim_histories, dict):
                for dim, values in dim_histories.items():
                    if dim in self._valence_dimensions_history:
                        self._valence_dimensions_history[dim].clear()
                        for value in values:
                            self._valence_dimensions_history[dim].append(value)
                        if len(self._valence_dimensions_history[dim]) > 0:
                            self.affective_states["valence_dimensions"][dim] = self._compute_exponential_weighted_average(
                                self._valence_dimensions_history[dim], None, decay_rate=0.15
                            )
        
        # Restore arousal history
        if "arousal_history" in histories:
            self._arousal_history.clear()
            for value in histories["arousal_history"]:
                self._arousal_history.append(value)
            if len(self._arousal_history) > 0:
                self.affective_states["arousal"] = sum(self._arousal_history) / len(self._arousal_history)
            logger.debug(f"Restored {len(self._arousal_history)} arousal history entries")
        
        # Restore certainty_affect history
        if "certainty_affect_history" in histories:
            self._certainty_affect_history.clear()
            for value in histories["certainty_affect_history"]:
                self._certainty_affect_history.append(value)
            if len(self._certainty_affect_history) > 0:
                self.affective_states["certainty_affect"] = sum(self._certainty_affect_history) / len(self._certainty_affect_history)
            logger.debug(f"Restored {len(self._certainty_affect_history)} certainty_affect history entries")
        
        # Restore curiosity_drive history
        if "curiosity_drive_history" in histories:
            self._curiosity_drive_history.clear()
            for value in histories["curiosity_drive_history"]:
                self._curiosity_drive_history.append(value)
            if len(self._curiosity_drive_history) > 0:
                self.affective_states["curiosity_drive"] = sum(self._curiosity_drive_history) / len(self._curiosity_drive_history)
            logger.debug(f"Restored {len(self._curiosity_drive_history)} curiosity_drive history entries")
        
        # Restore coherence_pleasure history
        if "coherence_pleasure_history" in histories:
            self._coherence_pleasure_history.clear()
            for value in histories["coherence_pleasure_history"]:
                self._coherence_pleasure_history.append(value)
            if len(self._coherence_pleasure_history) > 0:
                self.affective_states["coherence_pleasure"] = sum(self._coherence_pleasure_history) / len(self._coherence_pleasure_history)
            logger.debug(f"Restored {len(self._coherence_pleasure_history)} coherence_pleasure history entries")
        
        # Restore surprise history
        if "surprise_history" in histories:
            self._surprise_history.clear()
            for value in histories["surprise_history"]:
                self._surprise_history.append(value)
            if len(self._surprise_history) > 0:
                self.affective_states["surprise"] = sum(self._surprise_history) / len(self._surprise_history)
            logger.debug(f"Restored {len(self._surprise_history)} surprise history entries")
        
        # Restore surprise short-term history
        if "surprise_short_term_history" in histories:
            self._surprise_short_term_history.clear()
            for value in histories["surprise_short_term_history"]:
                self._surprise_short_term_history.append(value)
            if len(self._surprise_short_term_history) > 0:
                self.affective_states["surprise_short_term"] = sum(self._surprise_short_term_history) / len(self._surprise_short_term_history)
            logger.debug(f"Restored {len(self._surprise_short_term_history)} surprise_short_term history entries")
        
        # Restore surprise long-term history
        if "surprise_long_term_history" in histories:
            self._surprise_long_term_history.clear()
            for value in histories["surprise_long_term_history"]:
                self._surprise_long_term_history.append(value)
            if len(self._surprise_long_term_history) > 0:
                self.affective_states["surprise_long_term"] = sum(self._surprise_long_term_history) / len(self._surprise_long_term_history)
            logger.debug(f"Restored {len(self._surprise_long_term_history)} surprise_long_term history entries")
    
    def get_current_state(self) -> Dict[str, float]:
        """
        Get current emotional state.
        
        Returns:
            Dictionary with current emotional state values
        """
        return {
            "valence": self.affective_states["valence"],
            "arousal": self.affective_states["arousal"],
            "certainty_affect": self.affective_states["certainty_affect"],
            "curiosity_drive": self.affective_states["curiosity_drive"],
            "coherence_pleasure": self.affective_states["coherence_pleasure"],
            "surprise": self.affective_states["surprise"],
        }
    
    def update_from_dissonance(
        self,
        dissonance_metrics: Dict[str, Any],
        current_goals: Optional[List[Dict[str, Any]]] = None,
        coping_resources: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Update emotional state based on cognitive dissonance metrics.
        
        Args:
            dissonance_metrics: Dissonance metrics dictionary or DissonanceMetrics object
            current_goals: Optional list of current goals for appraisal
            coping_resources: Optional coping resources dictionary
        """
        if not self._emotional_appraisal_engine:
            logger.debug("No emotional appraisal engine set, skipping dissonance update")
            return
        
        try:
            from .emotional_appraisal import DissonanceEmotionalMapper
            
            # Convert to DissonanceMetrics if needed
            if isinstance(dissonance_metrics, dict):
                from ..reasoning.cognitive_dissonance import DissonanceMetrics
                metrics = DissonanceMetrics(
                    timestamp=dissonance_metrics.get("timestamp", datetime.now(timezone.utc)),
                    logical_dissonance=dissonance_metrics.get("logical_dissonance", 0.0),
                    factual_dissonance=dissonance_metrics.get("factual_dissonance", 0.0),
                    behavioral_dissonance=dissonance_metrics.get("behavioral_dissonance", 0.0),
                    goal_dissonance=dissonance_metrics.get("goal_dissonance", 0.0),
                    overall_dissonance=dissonance_metrics.get("overall_dissonance", 0.0)
                )
                metrics.compute_overall()
            else:
                metrics = dissonance_metrics
            
            # Appraise the dissonance
            appraisal = self._emotional_appraisal_engine.appraise_dissonance(
                dissonance_metrics=metrics,
                current_goals=current_goals or [],
                coping_resources=coping_resources or {}
            )
            
            # Map to emotional changes
            mapper = DissonanceEmotionalMapper()
            emotion_mapping = mapper.map_to_emotion(metrics, appraisal)
            
            # Apply emotional changes
            old_valence = self.affective_states["valence"]
            old_arousal = self.affective_states["arousal"]
            old_curiosity = self.affective_states["curiosity_drive"]
            
            # Update valence
            new_valence = max(-1.0, min(1.0, old_valence + emotion_mapping.valence_delta))
            self.compute_valence(
                positive_score=max(0.0, new_valence) if new_valence > 0 else 0.0,
                negative_score=max(0.0, -new_valence) if new_valence < 0 else 0.0
            )
            
            # Update arousal
            new_arousal = max(0.0, min(1.0, old_arousal + emotion_mapping.arousal_delta))
            self.affective_states["arousal"] = new_arousal
            self._arousal_history.append(new_arousal)
            if len(self._arousal_history) > 0:
                self.affective_states["arousal"] = sum(self._arousal_history) / len(self._arousal_history)
            
            # Update curiosity
            new_curiosity = max(0.0, min(1.0, old_curiosity + emotion_mapping.curiosity_delta))
            self.affective_states["curiosity_drive"] = new_curiosity
            self._curiosity_drive_history.append(new_curiosity)
            if len(self._curiosity_drive_history) > 0:
                self.affective_states["curiosity_drive"] = sum(self._curiosity_drive_history) / len(self._curiosity_drive_history)
            
            # Update surprise
            if emotion_mapping.surprise_delta > 0.0:
                self.affective_states["surprise"] = min(1.0, self.affective_states["surprise"] + emotion_mapping.surprise_delta)
                self._surprise_history.append(self.affective_states["surprise"])
            
            logger.debug(
                f"Updated affect from dissonance: valence {old_valence:.3f}→{self.affective_states['valence']:.3f}, "
                f"arousal {old_arousal:.3f}→{self.affective_states['arousal']:.3f}, "
                f"curiosity {old_curiosity:.3f}→{self.affective_states['curiosity_drive']:.3f}"
            )
            
        except Exception as e:
            logger.error(f"Error updating affect from dissonance: {e}", exc_info=True)
    
    def update_from_learning_outcome(
        self,
        outcome: Dict[str, Any],
        expected_outcome: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update emotional state based on learning outcome.
        
        Args:
            outcome: Learning outcome dictionary with success, effectiveness, dissonance_reduction, etc.
            expected_outcome: Optional expected outcome for comparison
        """
        if not self._emotional_appraisal_engine:
            logger.debug("No emotional appraisal engine set, skipping learning outcome update")
            return
        
        try:
            from .emotional_appraisal import LearningOutcomeAppraiser
            
            appraiser = LearningOutcomeAppraiser()
            emotion_mapping = appraiser.appraise_and_map(outcome, expected_outcome)
            
            # Apply emotional changes
            old_valence = self.affective_states["valence"]
            old_arousal = self.affective_states["arousal"]
            old_curiosity = self.affective_states["curiosity_drive"]
            
            # Update valence
            new_valence = max(-1.0, min(1.0, old_valence + emotion_mapping.valence_delta))
            self.compute_valence(
                positive_score=max(0.0, new_valence) if new_valence > 0 else 0.0,
                negative_score=max(0.0, -new_valence) if new_valence < 0 else 0.0
            )
            
            # Update arousal
            new_arousal = max(0.0, min(1.0, old_arousal + emotion_mapping.arousal_delta))
            self.affective_states["arousal"] = new_arousal
            self._arousal_history.append(new_arousal)
            if len(self._arousal_history) > 0:
                self.affective_states["arousal"] = sum(self._arousal_history) / len(self._arousal_history)
            
            # Update curiosity
            new_curiosity = max(0.0, min(1.0, old_curiosity + emotion_mapping.curiosity_delta))
            self.affective_states["curiosity_drive"] = new_curiosity
            self._curiosity_drive_history.append(new_curiosity)
            if len(self._curiosity_drive_history) > 0:
                self.affective_states["curiosity_drive"] = sum(self._curiosity_drive_history) / len(self._curiosity_drive_history)
            
            logger.debug(
                f"Updated affect from learning outcome: valence {old_valence:.3f}→{self.affective_states['valence']:.3f}, "
                f"arousal {old_arousal:.3f}→{self.affective_states['arousal']:.3f}"
            )
            
        except Exception as e:
            logger.error(f"Error updating affect from learning outcome: {e}", exc_info=True)
    
    def get_emotional_regulation_needs(self) -> Dict[str, Any]:
        """
        Get current emotional regulation needs based on homeostatic regulator.
        
        Returns:
            Dictionary with regulation needs (priority, strategy, adjustments)
        """
        if not self._emotional_regulator:
            return {
                "needs_regulation": False,
                "priority": 0.0
            }
        
        try:
            current_state = self.get_current_state()
            regulation_signal = self._emotional_regulator.compute_regulation_signal(current_state)
            
            # Record in history (convert RegulationSignal to dict for storage)
            from .emotional_regulation import RegulationSignal
            signal_dict = {
                "valence_adjustment": regulation_signal.valence_adjustment,
                "arousal_adjustment": regulation_signal.arousal_adjustment,
                "curiosity_adjustment": regulation_signal.curiosity_adjustment,
                "strategy": regulation_signal.strategy,
                "priority": regulation_signal.priority
            }
            self._regulation_history.append({
                "timestamp": time.time(),
                "signal": signal_dict,
                "current_state": current_state.copy()
            })
            
            return {
                "needs_regulation": regulation_signal.priority > 0.2,
                "priority": regulation_signal.priority,
                "strategy": regulation_signal.strategy,
                "valence_adjustment": regulation_signal.valence_adjustment,
                "arousal_adjustment": regulation_signal.arousal_adjustment,
                "curiosity_adjustment": regulation_signal.curiosity_adjustment
            }
        except Exception as e:
            logger.error(f"Error computing emotional regulation needs: {e}", exc_info=True)
            return {
                "needs_regulation": False,
                "priority": 0.0
            }
    
    def record_emotional_response(
        self,
        dissonance_before: float,
        dissonance_after: float,
        emotion_state: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Record emotional response to dissonance change.
        
        Args:
            dissonance_before: Dissonance before event
            dissonance_after: Dissonance after event
            emotion_state: Optional emotional state at time of response
        """
        if emotion_state is None:
            emotion_state = self.get_current_state()
        
        response_record = {
            "timestamp": time.time(),
            "dissonance_before": dissonance_before,
            "dissonance_after": dissonance_after,
            "dissonance_change": dissonance_before - dissonance_after,
            "emotion_state": emotion_state.copy()
        }
        
        # Store in regulation history (reuse the same deque)
        self._regulation_history.append(response_record)
        
        logger.debug(
            f"Recorded emotional response: dissonance {dissonance_before:.3f}→{dissonance_after:.3f}, "
            f"valence={emotion_state.get('valence', 0.0):.3f}"
        )

