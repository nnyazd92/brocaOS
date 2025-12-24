"""
Cognitive state monitoring for internal sensing.

Monitors cognitive states including confidence, coherence, attention,
processing depth, and uncertainty.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional, Union
from collections import deque, defaultdict
from .response_analyzer import ResponseAnalyzer

logger = logging.getLogger(__name__)


class CognitiveStateMonitor:
    """
    Monitor cognitive states.
    
    Tracks:
    - Confidence level: Certainty in responses
    - Conceptual coherence: Logical consistency
    - Attention allocation: Focus distribution
    - Processing depth: Depth of analysis
    - Uncertainty tracking: Awareness of unknowns
    """
    
    def __init__(self, history_window: int = 60) -> None:
        """
        Initialize cognitive state monitor.
        
        Args:
            history_window: Number of samples to keep in history
        """
        self.states: Dict[str, Any] = {
            "confidence_level": None,  # Unknown until first measurement
            "conceptual_coherence": None,  # Unknown until reasoning steps recorded
            "attention_allocation": {},
            "processing_depth": None,  # Unknown until operations recorded
            "uncertainty_tracking": None,  # Unknown until uncertainties recorded
        }
        
        self.history_window = history_window
        self._history: deque = deque(maxlen=history_window)
        self._confidence_history: deque = deque(maxlen=20)
        self._confidence_outcomes: Dict[str, bool] = {}
        self._reasoning_steps: List[Dict[str, Any]] = []
        self._attention_levels: Dict[str, float] = {}
        self._processing_depths: deque = deque(maxlen=20)
        self._uncertainty_history: deque = deque(maxlen=20)
        self._reasoning_patterns: List[Dict[str, str]] = []
        
        logger.info("Initialized CognitiveStateMonitor")
    
    def record_confidence(self, response_id: str, confidence: float) -> None:
        """
        Record confidence level for a response.
        
        Args:
            response_id: Unique identifier for the response
            confidence: Confidence level (0.0-1.0)
        """
        confidence = max(0.0, min(1.0, confidence))
        self._confidence_history.append({
            "response_id": response_id,
            "confidence": confidence,
            "timestamp": time.time(),
        })
        self._update_confidence_level()
    
    def record_confidence_outcome(self, response_id: str, correct: bool) -> None:
        """
        Record the actual outcome for a confidence prediction.
        
        Args:
            response_id: Unique identifier for the response
            correct: Whether the response was correct
        """
        self._confidence_outcomes[response_id] = correct
    
    def _update_confidence_level(self) -> None:
        """Update average confidence level from history."""
        if len(self._confidence_history) > 0:
            avg = sum(entry["confidence"] for entry in self._confidence_history) / len(self._confidence_history)
            self.states["confidence_level"] = avg
        else:
            self.states["confidence_level"] = None
    
    def _calculate_average_confidence(self) -> Optional[float]:
        """
        Calculate average confidence from history.
        
        Returns:
            Average confidence level (0.0-1.0), or None if no history available
        """
        if len(self._confidence_history) == 0:
            return None
        
        return sum(entry["confidence"] for entry in self._confidence_history) / len(self._confidence_history)
    
    def _calculate_calibration(self) -> Optional[float]:
        """
        Calculate confidence calibration accuracy.
        
        Returns:
            Calibration score (0.0-1.0), higher = better calibrated, or None if no data available
        """
        if len(self._confidence_history) == 0:
            return None
        
        # Calculate calibration: how well confidence predicts correctness
        calibration_scores = []
        
        for entry in self._confidence_history:
            response_id = entry["response_id"]
            confidence = entry["confidence"]
            
            if response_id in self._confidence_outcomes:
                correct = self._confidence_outcomes[response_id]
                # Perfect calibration: high confidence when correct, low when incorrect
                if correct:
                    # Higher confidence is better when correct
                    score = confidence
                else:
                    # Lower confidence is better when incorrect
                    score = 1.0 - confidence
                
                calibration_scores.append(score)
        
        if len(calibration_scores) == 0:
            return None  # No outcomes recorded yet
        
        return sum(calibration_scores) / len(calibration_scores)
    
    def record_reasoning_step(self, step_id: str, step_data: Dict[str, Any]) -> None:
        """
        Record a reasoning step.
        
        Args:
            step_id: Unique identifier for the step
            step_data: Dictionary containing premise, conclusion, etc.
        """
        self._reasoning_steps.append({
            "step_id": step_id,
            **step_data,
            "timestamp": time.time(),
        })
        # Keep only recent steps
        if len(self._reasoning_steps) > 50:
            self._reasoning_steps = self._reasoning_steps[-50:]
        
        self._update_coherence()
    
    
    def _update_coherence(self) -> None:
        """Update conceptual coherence from reasoning steps and logical reversals."""
        if not self._reasoning_steps:
            self.states["conceptual_coherence"] = None
            return
        
        # 1. Check for explicit contradictions in steps
        contradictions = 0
        total_comparisons = 0
        for i, step1 in enumerate(self._reasoning_steps):
            for step2 in self._reasoning_steps[i+1:]:
                total_comparisons += 1
                if (step1.get("premise") == step2.get("premise") and
                    step1.get("conclusion") != step2.get("conclusion")):
                    contradictions += 1
        
        step_coherence = 1.0 - (contradictions / total_comparisons) if total_comparisons > 0 else 1.0
        
        # 2. Check for logical reversals in the latest conclusion
        latest_conclusion = self._reasoning_steps[-1].get("conclusion", "")
        reversal_score = ResponseAnalyzer.detect_logical_reversals(latest_conclusion)
        
        # Coherence is reduced by reversals (mid-stream corrections)
        # A reversal score of 1.0 reduces coherence by 0.5
        final_coherence = step_coherence * (1.0 - (reversal_score * 0.5))
        
        self.states["conceptual_coherence"] = max(0.0, min(1.0, final_coherence))

    
    def _calculate_coherence(self) -> Optional[float]:
        """
        Calculate conceptual coherence from reasoning steps.
        
        Returns:
            Coherence score (0.0-1.0), or None if insufficient data
        """
        return self.states["conceptual_coherence"]
    
    def record_attention(self, topic: str, level: float) -> None:
        """
        Record attention level for a topic.
        
        Args:
            topic: Topic identifier
            level: Attention level (0.0-1.0)
        """
        level = max(0.0, min(1.0, level))
        self._attention_levels[topic] = level
        
        # Normalize attention allocation
        total = sum(self._attention_levels.values())
        if total > 1.0:
            # Normalize to sum to 1.0
            for key in self._attention_levels:
                self._attention_levels[key] /= total
        
        self.states["attention_allocation"] = self._attention_levels.copy()
    
    def record_processing_depth(self, operation_id: str, depth: int) -> None:
        """
        Record processing depth for an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            depth: Processing depth (number of levels)
        """
        self._processing_depths.append({
            "operation_id": operation_id,
            "depth": depth,
            "timestamp": time.time(),
        })
        self._update_processing_depth()
    
    def _update_processing_depth(self) -> None:
        """Update average processing depth."""
        if len(self._processing_depths) > 0:
            avg = sum(entry["depth"] for entry in self._processing_depths) / len(self._processing_depths)
            self.states["processing_depth"] = avg
        else:
            self.states["processing_depth"] = None
    
    def _calculate_average_depth(self) -> Optional[float]:
        """
        Calculate average processing depth.
        
        Returns:
            Average depth, or None if no operations recorded
        """
        if len(self._processing_depths) == 0:
            return None
        
        return sum(entry["depth"] for entry in self._processing_depths) / len(self._processing_depths)
    
    def _normalize_depth(self, depth: int, max_depth: int = 20) -> float:
        """
        Normalize processing depth to 0-1 range.
        
        Args:
            depth: Processing depth
            max_depth: Maximum expected depth
            
        Returns:
            Normalized depth (0.0-1.0)
        """
        return min(depth / max_depth, 1.0)
    
    def record_uncertainty(self, question_id: str, uncertainty: float) -> None:
        """
        Record uncertainty level for a question.
        
        Args:
            question_id: Unique identifier for the question
            uncertainty: Uncertainty level (0.0-1.0)
        """
        uncertainty = max(0.0, min(1.0, uncertainty))
        self._uncertainty_history.append({
            "question_id": question_id,
            "uncertainty": uncertainty,
            "timestamp": time.time(),
        })
        self._update_uncertainty()
    
    def _update_uncertainty(self) -> None:
        """Update average uncertainty from history."""
        if len(self._uncertainty_history) > 0:
            avg = sum(entry["uncertainty"] for entry in self._uncertainty_history) / len(self._uncertainty_history)
            self.states["uncertainty_tracking"] = avg
        else:
            self.states["uncertainty_tracking"] = None
    
    def _calculate_average_uncertainty(self) -> Optional[float]:
        """
        Calculate average uncertainty from history.
        
        Returns:
            Average uncertainty (0.0-1.0), or None if no uncertainties recorded
        """
        if len(self._uncertainty_history) == 0:
            return None
        
        return sum(entry["uncertainty"] for entry in self._uncertainty_history) / len(self._uncertainty_history)
    
    def record_reasoning_pattern(self, pattern_type: str, pattern_name: str) -> None:
        """
        Record a reasoning pattern.
        
        Args:
            pattern_type: Type of pattern (e.g., "heuristic", "algorithm")
            pattern_name: Name of the pattern
        """
        self._reasoning_patterns.append({
            "type": pattern_type,
            "name": pattern_name,
            "timestamp": time.time(),
        })
        # Keep only recent patterns
        if len(self._reasoning_patterns) > 100:
            self._reasoning_patterns = self._reasoning_patterns[-100:]
    
    def _get_reasoning_patterns(self) -> List[Dict[str, str]]:
        """
        Get recent reasoning patterns.
        
        Returns:
            List of pattern dictionaries
        """
        return self._reasoning_patterns.copy()
    
    def sample_cognitive_state(self) -> Dict[str, Any]:
        """
        Sample complete cognitive state.
        
        Returns:
            Dictionary containing all cognitive states with timestamp
        """
        # Update all states
        self._update_confidence_level()
        self._update_coherence()
        self._update_processing_depth()
        self._update_uncertainty()
        
        # Create sample with timestamp
        sample = {
            **self.states,
            "timestamp": time.time(),
        }
        
        # Add to history
        self._history.append(sample)
        
        return sample
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get history of cognitive state samples.
        
        Returns:
            List of sample dictionaries
        """
        return list(self._history)

