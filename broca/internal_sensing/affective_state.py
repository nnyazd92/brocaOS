"""
Affective state monitoring for internal sensing.

Monitors affective states including valence, arousal, curiosity, and satisfaction.
"""

from __future__ import annotations
from .response_analyzer import ResponseAnalyzer

import time
import logging
from collections import deque
from typing import Dict, Any, List, Optional, TYPE_CHECKING, Union

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None  # type: ignore

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
        self.affective_states: Dict[str, float] = {
            "valence": 0.0,  # Neutral (range: -1 to 1)
            "arousal": 0.5,  # Moderate (range: 0 to 1)
            "certainty_affect": 0.5,  # Moderate (range: 0 to 1)
            "curiosity_drive": 0.5,  # Moderate (range: 0 to 1)
            "coherence_pleasure": 0.5,  # Moderate (range: 0 to 1)
            "surprise": 0.0,  # No surprise initially (range: 0 to 1)
        }
        
        # Moving average tracking for each metric
        self._moving_avg_window = moving_avg_window
        self._valence_history: deque = deque(maxlen=moving_avg_window)
        self._arousal_history: deque = deque(maxlen=moving_avg_window)
        self._certainty_affect_history: deque = deque(maxlen=moving_avg_window)
        self._curiosity_drive_history: deque = deque(maxlen=moving_avg_window)
        self._coherence_pleasure_history: deque = deque(maxlen=moving_avg_window)
        self._surprise_history: deque = deque(maxlen=moving_avg_window)
        
        self._motivational_drives: Dict[str, float] = {}
        # Use bounded deque to prevent unbounded memory growth
        # Limit to last 1000 satisfaction/frustration patterns
        self._satisfaction_patterns: deque = deque(maxlen=1000)
        
        logger.info("Initialized ComputationalAffectMonitor")
    
    def compute_valence(self, positive_score: float, negative_score: float) -> None:
        """
        Compute valence from positive and negative scores using moving average.
        
        Args:
            positive_score: Positive evaluation score (0.0-1.0)
            negative_score: Negative evaluation score (0.0-1.0)
        """
        positive_score = max(0.0, min(1.0, positive_score))
        negative_score = max(0.0, min(1.0, negative_score))
        
        # Valence is difference: positive - negative, normalized to -1 to 1
        if positive_score + negative_score == 0:
            valence = 0.0
        else:
            valence = (positive_score - negative_score) / (positive_score + negative_score)
        
        valence = max(-1.0, min(1.0, valence))
        
        # Update moving average
        self._valence_history.append(valence)
        if len(self._valence_history) > 0:
            self.affective_states["valence"] = sum(self._valence_history) / len(self._valence_history)
    
    
    def compute_valence_from_text(self, text: str) -> None:
        """
        Compute valence directly from text using VADER (fallback to TextBlob) with moving average.
        
        Args:
            text: Text to analyze
        """
        if not text:
            return
        
        valence = None
            
        # Try VADER first
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
        
        # Update moving average if we got a value
        if valence is not None:
            self._valence_history.append(valence)
            if len(self._valence_history) > 0:
                self.affective_states["valence"] = sum(self._valence_history) / len(self._valence_history)

    
    def compute_valence_from_conversation_history(self, messages: List[Dict[str, Any]]) -> None:
        """
        Compute valence from conversation history, excluding system and tool messages.
        
        Args:
            messages: List of message dictionaries with "role" and "content" keys
        """
        if not messages:
            # Empty conversation - leave valence as None
            return
        
        # Filter out system and tool messages, keep only user and assistant
        conversation_texts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Only include user and assistant messages
            if role in ("user", "assistant") and content:
                conversation_texts.append(str(content))
        
        if not conversation_texts:
            # No user/assistant messages - leave valence as None
            return
        
        # Combine all conversation text
        combined_text = " ".join(conversation_texts)
        
        # Compute valence from combined text (will update moving average)
        self.compute_valence_from_text(combined_text)
    
    def compute_arousal(self, activation_level: float) -> None:
        """
        Compute arousal from activation level using moving average.
        
        Args:
            activation_level: Activation level (0.0-1.0)
        """
        arousal = max(0.0, min(1.0, activation_level))
        
        # Update moving average
        self._arousal_history.append(arousal)
        if len(self._arousal_history) > 0:
            self.affective_states["arousal"] = sum(self._arousal_history) / len(self._arousal_history)
    
    def update_certainty_affect(self, confidence: float) -> None:
        """
        Update certainty affect from confidence level using moving average.
        
        Args:
            confidence: Confidence level (0.0-1.0)
        """
        certainty = max(0.0, min(1.0, confidence))
        
        # Update moving average
        self._certainty_affect_history.append(certainty)
        if len(self._certainty_affect_history) > 0:
            self.affective_states["certainty_affect"] = sum(self._certainty_affect_history) / len(self._certainty_affect_history)
    
    
    def compute_curiosity_drive(self, uncertainty: float, interest: float) -> None:
        """
        Compute curiosity drive from uncertainty, interest, and surprise using moving average.
        
        Args:
            uncertainty: Uncertainty level (0.0-1.0)
            interest: Interest level (0.0-1.0)
        """
        uncertainty = max(0.0, min(1.0, uncertainty))
        interest = max(0.0, min(1.0, interest))
        surprise = self.affective_states.get("surprise", 0.0)
        
        # Curiosity is driven by uncertainty, interest, and surprise (novelty)
        # Weighted: 40% uncertainty, 30% interest, 30% surprise
        curiosity = (uncertainty * 0.4 + interest * 0.3 + surprise * 0.3)
        curiosity = max(0.0, min(1.0, curiosity))
        
        # Update moving average
        self._curiosity_drive_history.append(curiosity)
        if len(self._curiosity_drive_history) > 0:
            self.affective_states["curiosity_drive"] = sum(self._curiosity_drive_history) / len(self._curiosity_drive_history)

    
    
    def update_coherence_pleasure(self, coherence: float) -> None:
        """
        Update coherence pleasure from coherence level and certainty using moving average.
        
        Args:
            coherence: Coherence level (0.0-1.0)
        """
        certainty = self.affective_states.get("certainty_affect", 0.5)
        # Pleasure increases with coherence and certainty
        pleasure = (coherence * 0.7) + (certainty * 0.3)
        pleasure = max(0.0, min(1.0, pleasure))
        
        # Update moving average
        self._coherence_pleasure_history.append(pleasure)
        if len(self._coherence_pleasure_history) > 0:
            self.affective_states["coherence_pleasure"] = sum(self._coherence_pleasure_history) / len(self._coherence_pleasure_history)

    
    
    def update_surprise(self, prediction_error: float) -> None:
        """
        Update surprise state based on prediction error (novelty/unexpectedness) using moving average.
        
        Args:
            prediction_error: Magnitude of difference between predicted and actual (0.0-1.0)
        """
        surprise = max(0.0, min(1.0, prediction_error))
        
        # Update moving average
        self._surprise_history.append(surprise)
        if len(self._surprise_history) > 0:
            self.affective_states["surprise"] = sum(self._surprise_history) / len(self._surprise_history)

    def update_from_cognitive(self, cognitive_monitor: "CognitiveStateMonitor") -> None:
        """
        Update affective states from cognitive monitor.
        
        Args:
            cognitive_monitor: CognitiveStateMonitor instance
        """
        # Update certainty affect from confidence (always update, using defaults if None)
        confidence = cognitive_monitor.states.get("confidence_level")
        if confidence is not None:
            self.update_certainty_affect(confidence)
        
        # Update coherence pleasure from coherence (always update, using defaults if None)
        coherence = cognitive_monitor.states.get("conceptual_coherence")
        if coherence is not None:
            self.update_coherence_pleasure(coherence)
        
        # Update curiosity from uncertainty (always update, using defaults if None)
        uncertainty = cognitive_monitor.states.get("uncertainty_tracking", 0.0)
        # Use attention as proxy for interest
        attention_allocation = cognitive_monitor.states.get("attention_allocation", {})
        attention_total = sum(attention_allocation.values())
        interest = min(attention_total, 1.0) if attention_total > 0 else 0.0
        
        self.compute_curiosity_drive(uncertainty, interest)
    
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
            Dictionary containing all affective states with timestamp
        """
        return {
            **self.affective_states,
            "motivational_drives": self._motivational_drives.copy(),
            "timestamp": time.time(),
        }

