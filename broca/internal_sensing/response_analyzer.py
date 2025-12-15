"""
Response analyzer for extracting metrics from LLM responses.

Analyzes response text to estimate confidence, uncertainty, valence, etc.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ResponseAnalyzer:
    """
    Analyzes LLM responses to extract internal sensing metrics.
    
    Provides heuristics for estimating:
    - Confidence levels
    - Uncertainty levels
    - Valence (positive/negative sentiment)
    - Arousal (activation level)
    """
    
    # Confidence indicators
    HIGH_CONFIDENCE_PATTERNS = [
        r'\b(certain|definitely|absolutely|clearly|obviously|undoubtedly|surely)\b',
        r'\b(know|understand|proven|established|fact)\b',
        r'\b(always|never|all|every|none)\b',
    ]
    
    LOW_CONFIDENCE_PATTERNS = [
        r'\b(maybe|perhaps|possibly|might|could|uncertain|unclear)\b',
        r'\b(think|believe|guess|assume|suppose|seem)\b',
        r'\b(probably|likely|unlikely|doubt|question)\b',
    ]
    
    # Uncertainty indicators
    UNCERTAINTY_PATTERNS = [
        r'\b(not sure|uncertain|unclear|unknown|unsure)\b',
        r'\b(maybe|perhaps|possibly|might|could)\b',
        r'\b(question|doubt|wonder|unclear)\b',
        r'\b(I don\'t know|I\'m not sure|hard to say)\b',
    ]
    
    # Positive sentiment patterns
    POSITIVE_PATTERNS = [
        r'\b(good|great|excellent|wonderful|fantastic|amazing|perfect)\b',
        r'\b(success|succeed|achieve|accomplish|complete)\b',
        r'\b(happy|pleased|satisfied|glad|delighted)\b',
        r'\b(helpful|useful|beneficial|valuable|effective)\b',
    ]
    
    # Negative sentiment patterns
    NEGATIVE_PATTERNS = [
        r'\b(bad|terrible|awful|horrible|worst|failed|error)\b',
        r'\b(problem|issue|difficulty|trouble|challenge)\b',
        r'\b(sorry|apologize|regret|unfortunately|sad)\b',
        r'\b(fail|error|mistake|wrong|incorrect|broken)\b',
    ]
    
    # Arousal indicators (activation level)
    HIGH_AROUSAL_PATTERNS = [
        r'\b(urgent|critical|important|immediate|now|quickly)\b',
        r'\b(excited|energetic|active|dynamic|intense)\b',
        r'\b(alert|focused|concentrated|attentive)\b',
    ]
    
    LOW_AROUSAL_PATTERNS = [
        r'\b(calm|relaxed|slow|gradual|gentle|peaceful)\b',
        r'\b(tired|exhausted|drained|low energy)\b',
    ]
    
    @classmethod
    def estimate_confidence(cls, response: str) -> Optional[float]:
        """
        Estimate confidence level from response text.
        
        Args:
            response: LLM response text
            
        Returns:
            Confidence estimate (0.0-1.0), or None if response is empty
        """
        if not response:
            return None
        
        response_lower = response.lower()
        
        # Count confidence indicators
        high_confidence_count = sum(
            len(re.findall(pattern, response_lower, re.IGNORECASE))
            for pattern in cls.HIGH_CONFIDENCE_PATTERNS
        )
        
        low_confidence_count = sum(
            len(re.findall(pattern, response_lower, re.IGNORECASE))
            for pattern in cls.LOW_CONFIDENCE_PATTERNS
        )
        
        # Base confidence on response length and structure
        length_factor = min(1.0, len(response) / 500.0)  # Longer = more confident (up to 500 chars)
        
        # Adjust based on confidence indicators
        indicator_factor = 0.5
        if high_confidence_count > low_confidence_count:
            indicator_factor = 0.5 + min(0.4, (high_confidence_count - low_confidence_count) * 0.1)
        elif low_confidence_count > high_confidence_count:
            indicator_factor = 0.5 - min(0.4, (low_confidence_count - high_confidence_count) * 0.1)
        
        # Combine factors
        confidence = (length_factor * 0.3 + indicator_factor * 0.7)
        
        return max(0.0, min(1.0, confidence))
    
    @classmethod
    def detect_uncertainty(cls, response: str) -> Optional[float]:
        """
        Detect uncertainty level from response text.
        
        Args:
            response: LLM response text
            
        Returns:
            Uncertainty level (0.0-1.0), higher = more uncertain, or None if response is empty
        """
        if not response:
            return None
        
        response_lower = response.lower()
        
        # Count uncertainty indicators
        uncertainty_count = sum(
            len(re.findall(pattern, response_lower, re.IGNORECASE))
            for pattern in cls.UNCERTAINTY_PATTERNS
        )
        
        # Check for question marks (questions indicate uncertainty)
        question_count = response.count('?')
        
        # Check for hedging language
        hedging_words = ['maybe', 'perhaps', 'possibly', 'might', 'could', 'seems', 'appears']
        hedging_count = sum(1 for word in hedging_words if word in response_lower)
        
        # Combine indicators
        total_indicators = uncertainty_count + question_count * 0.5 + hedging_count
        
        # Normalize to 0-1 range (assuming max ~10 indicators = high uncertainty)
        uncertainty = min(1.0, total_indicators / 10.0)
        
        return uncertainty
    
    @classmethod
    def compute_valence(cls, response: str) -> Optional[Tuple[float, float]]:
        """
        Compute valence (positive/negative) from response text.
        
        Args:
            response: LLM response text
            
        Returns:
            Tuple of (positive_score, negative_score) both 0.0-1.0, or None if response is empty
        """
        if not response:
            return None
        
        response_lower = response.lower()
        
        # Count positive indicators
        positive_count = sum(
            len(re.findall(pattern, response_lower, re.IGNORECASE))
            for pattern in cls.POSITIVE_PATTERNS
        )
        
        # Count negative indicators
        negative_count = sum(
            len(re.findall(pattern, response_lower, re.IGNORECASE))
            for pattern in cls.NEGATIVE_PATTERNS
        )
        
        # Normalize to 0-1 range
        positive_score = min(1.0, positive_count / 5.0)
        negative_score = min(1.0, negative_count / 5.0)
        
        return (positive_score, negative_score)
    
    @classmethod
    def compute_arousal(cls, response: str) -> Optional[float]:
        """
        Compute arousal (activation level) from response text.
        
        Args:
            response: LLM response text
            
        Returns:
            Arousal level (0.0-1.0), or None if response is empty
        """
        if not response:
            return None
        
        response_lower = response.lower()
        
        # Count arousal indicators
        high_arousal_count = sum(
            len(re.findall(pattern, response_lower, re.IGNORECASE))
            for pattern in cls.HIGH_AROUSAL_PATTERNS
        )
        
        low_arousal_count = sum(
            len(re.findall(pattern, response_lower, re.IGNORECASE))
            for pattern in cls.LOW_AROUSAL_PATTERNS
        )
        
        # Check for exclamation marks (indicate high arousal)
        exclamation_count = response.count('!')
        
        # Combine indicators
        arousal_indicators = high_arousal_count - low_arousal_count + exclamation_count * 0.5
        
        # Normalize to 0-1 range
        arousal = 0.5 + min(0.5, max(-0.5, arousal_indicators / 5.0))
        
        return max(0.0, min(1.0, arousal))
    
    @classmethod
    def extract_topics(cls, response: str, context: list[Dict[str, str]]) -> Dict[str, float]:
        """
        Extract topics and attention levels from response and context.
        
        Args:
            response: LLM response text
            context: Conversation context (recent messages)
            
        Returns:
            Dictionary mapping topic names to attention levels (0.0-1.0)
        """
        topics: Dict[str, float] = {}
        
        # Simple keyword-based topic extraction
        topic_keywords = {
            "mathematics": ["math", "mathematical", "equation", "formula", "calculate", "compute"],
            "programming": ["code", "program", "function", "variable", "algorithm", "python"],
            "science": ["scientific", "experiment", "research", "theory", "hypothesis"],
            "general": ["help", "assist", "question", "answer", "explain"],
        }
        
        all_text = response.lower()
        for msg in context[-3:]:  # Last 3 messages
            all_text += " " + msg.get("content", "").lower()
        
        for topic, keywords in topic_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in all_text)
            if matches > 0:
                topics[topic] = min(1.0, matches / len(keywords))
        
        # Normalize to sum to reasonable total
        total = sum(topics.values())
        if total > 1.0:
            for topic in topics:
                topics[topic] /= total
        
        return topics

