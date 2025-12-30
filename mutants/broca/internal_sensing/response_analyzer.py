"""
Response analyzer for extracting metrics from LLM responses.

Analyzes response text to estimate confidence, uncertainty, valence, etc.
"""

from __future__ import annotations
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import nltk
except ImportError:
    SentimentIntensityAnalyzer = None

import re
import json
import logging
import time
import numpy as np
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm import LLMClient

logger = logging.getLogger(__name__)

# Import logger utility
try:
    from ..reasoning.llm_pattern_logger import get_logger, initialize_logger
    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False


class ResponseAnalyzer:
    """
    Analyzes LLM responses to extract internal sensing metrics.
    
    Can use LLM-based semantic analysis (preferred) or regex patterns (fallback).
    """
    
    # Class-level LLM client (can be set for all instances)
    _llm_client: Optional["LLMClient"] = None
    _llm_model: str = "gpt-5-nano"
    _llm_enabled: bool = True
    
    @classmethod
    def set_llm_client(cls, llm_client: Optional["LLMClient"], model: str = "gpt-5-nano", enabled: bool = True) -> None:
        """Set LLM client for semantic analysis."""
        cls._llm_client = llm_client
        cls._llm_model = model
        cls._llm_enabled = enabled
        if llm_client:
            logger.info(f"ResponseAnalyzer LLM client set (model: {model}, enabled: {enabled})")
    
    @classmethod
    def calculate_semantic_distance(cls, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine distance between two embeddings.
        
        Returns:
            Distance (0.0-1.0), where 1.0 is completely different.
        """
        if not embedding1 or not embedding2:
            return 0.5
            
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine Similarity
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.5
            
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        
        # Distance is 1 - similarity
        # Map from [-1, 1] similarity to [0, 1] distance
        distance = (1.0 - similarity) / 2.0
        return float(distance)

    @classmethod
    def analyze_sentiment_vader(cls, text: str) -> Optional[Dict[str, float]]:
        """
        Analyze sentiment using VADER (better than TextBlob for conversation).
        """
        if SentimentIntensityAnalyzer is None:
            return None
            
        try:
            # Ensure vader_lexicon is downloaded
            try:
                nltk.data.find('sentiment/vader_lexicon.zip')
            except LookupError:
                nltk.download('vader_lexicon', quiet=True)
                
            sia = SentimentIntensityAnalyzer()
            return sia.polarity_scores(text)
        except Exception:
            return None

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
    
    
    # Logical reversal indicators (mid-stream corrections)
    REVERSAL_PATTERNS = [
        r'\b(wait|actually|on second thought|however|correction|mistake|wrong about)\b',
        r'\b(instead|rather|alternatively|revising|updating)\b',
        r'\b(I was incorrect|I should have|let me re-evaluate)\b',
    ]

    LOW_AROUSAL_PATTERNS = [
        r'\b(calm|relaxed|slow|gradual|gentle|peaceful)\b',
        r'\b(tired|exhausted|drained|low energy)\b',
    ]
    
    # Emotion category patterns
    JOY_PATTERNS = [
        r'\b(happy|joy|delighted|pleased|excited|thrilled|ecstatic)\b',
        r'\b(celebration|success|achievement|accomplishment)\b',
    ]
    
    FRUSTRATION_PATTERNS = [
        r'\b(frustrated|annoyed|irritated|aggravated|exasperated)\b',
        r'\b(difficult|challenging|problematic|troublesome)\b',
    ]
    
    CURIOSITY_PATTERNS = [
        r'\b(curious|wonder|interested|intrigued|fascinated)\b',
        r'\b(explore|investigate|discover|learn|understand)\b',
    ]
    
    # Task urgency patterns
    URGENT_PATTERNS = [
        r'\b(urgent|critical|immediate|asap|right away|now)\b',
        r'\b(deadline|time sensitive|important|priority)\b',
    ]
    
    # Engagement patterns
    HIGH_ENGAGEMENT_PATTERNS = [
        r'\b(detailed|thorough|comprehensive|extensive|in-depth)\b',
        r'\b(question|clarify|explain|elaborate|discuss)\b',
    ]
    
    LOW_ENGAGEMENT_PATTERNS = [
        r'\b(brief|short|quick|simple|basic)\b',
        r'\b(ok|sure|fine|whatever|don\'t care)\b',
    ]
    
    @classmethod
    def estimate_confidence(cls, response: str, context: Optional[List[Dict[str, str]]] = None) -> Optional[float]:
        """
        Estimate confidence level from response text.
        
        Uses LLM analysis if available, falls back to regex patterns.
        
        Args:
            response: LLM response text
            context: Optional conversation context
            
        Returns:
            Confidence estimate (0.0-1.0), or None if response is empty
        """
        if not response:
            return None
        
        # Try comprehensive LLM analysis first
        if cls._llm_enabled and cls._llm_client:
            try:
                analysis = cls.analyze_response_comprehensive(response, context)
                if analysis and analysis.get("analysis_method") == "llm":
                    return analysis.get("confidence")
            except Exception:
                pass  # Fall through to regex
        
        # Fallback to regex patterns
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
    def detect_uncertainty(cls, response: str, context: Optional[List[Dict[str, str]]] = None) -> Optional[float]:
        """
        Detect uncertainty level from response text.
        
        Uses LLM analysis if available, falls back to regex patterns.
        
        Args:
            response: LLM response text
            context: Optional conversation context
            
        Returns:
            Uncertainty level (0.0-1.0), higher = more uncertain, or None if response is empty
        """
        if not response:
            return None
        
        # Try comprehensive LLM analysis first
        if cls._llm_enabled and cls._llm_client:
            try:
                analysis = cls.analyze_response_comprehensive(response, context)
                if analysis and analysis.get("analysis_method") == "llm":
                    return analysis.get("uncertainty")
            except Exception:
                pass  # Fall through to regex
        
        # Fallback to regex patterns
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
    def compute_valence(cls, response: str, context: Optional[List[Dict[str, str]]] = None) -> Optional[Tuple[float, float]]:
        """
        Compute valence (positive/negative) from response text with optional context awareness.
        
        Uses LLM analysis if available, falls back to regex patterns.
        
        Args:
            response: LLM response text
            context: Optional conversation context (recent messages)
            
        Returns:
            Tuple of (positive_score, negative_score) both 0.0-1.0, or None if response is empty
        """
        if not response:
            return None
        
        # Try comprehensive LLM analysis first
        if cls._llm_enabled and cls._llm_client:
            try:
                analysis = cls.analyze_response_comprehensive(response, context)
                if analysis and analysis.get("analysis_method") == "llm":
                    return (analysis.get("valence_positive", 0.0), analysis.get("valence_negative", 0.0))
            except Exception:
                pass  # Fall through to regex
        
        # Fallback to regex patterns
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
        
        # Context-aware adjustment: consider user's previous sentiment
        if context:
            user_messages = [msg.get("content", "").lower() for msg in context[-3:] 
                           if msg.get("role") == "user"]
            if user_messages:
                user_text = " ".join(user_messages)
                user_positive = sum(len(re.findall(p, user_text, re.IGNORECASE)) 
                                  for p in cls.POSITIVE_PATTERNS)
                user_negative = sum(len(re.findall(p, user_text, re.IGNORECASE)) 
                                  for p in cls.NEGATIVE_PATTERNS)
                # If user was negative, assistant's positive response is more valuable
                if user_negative > user_positive:
                    positive_count += 1  # Boost positive score
                # If user was positive, maintain or slightly boost positive
                elif user_positive > user_negative:
                    positive_count += 0.5
        
        # Normalize to 0-1 range
        positive_score = min(1.0, positive_count / 5.0)
        negative_score = min(1.0, negative_count / 5.0)
        
        return (positive_score, negative_score)
    
    @classmethod
    def detect_emotion_categories(cls, response: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, float]:
        """
        Detect specific emotion categories from response text.
        
        Uses LLM analysis if available, falls back to regex patterns.
        
        Args:
            response: LLM response text
            context: Optional conversation context
            
        Returns:
            Dictionary mapping emotion categories to intensity scores (0.0-1.0)
        """
        if not response:
            return {}
        
        # Try comprehensive LLM analysis first
        if cls._llm_enabled and cls._llm_client:
            try:
                analysis = cls.analyze_response_comprehensive(response, context)
                if analysis and analysis.get("analysis_method") == "llm":
                    return analysis.get("emotions", {})
            except Exception:
                pass  # Fall through to regex
        
        # Fallback to regex patterns
        response_lower = response.lower()
        
        emotions = {}
        
        # Joy
        joy_count = sum(len(re.findall(p, response_lower, re.IGNORECASE)) 
                       for p in cls.JOY_PATTERNS)
        emotions["joy"] = min(1.0, joy_count / 3.0)
        
        # Frustration
        frustration_count = sum(len(re.findall(p, response_lower, re.IGNORECASE)) 
                              for p in cls.FRUSTRATION_PATTERNS)
        emotions["frustration"] = min(1.0, frustration_count / 3.0)
        
        # Curiosity
        curiosity_count = sum(len(re.findall(p, response_lower, re.IGNORECASE)) 
                            for p in cls.CURIOSITY_PATTERNS)
        emotions["curiosity"] = min(1.0, curiosity_count / 3.0)
        
        return emotions
    
    @classmethod
    def compute_emotion_intensity(cls, response: str, emotion_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Compute intensity scaling for detected emotions.
        
        Args:
            response: LLM response text
            emotion_scores: Dictionary of emotion category scores
            
        Returns:
            Dictionary with intensity-scaled emotion scores
        """
        if not response:
            return emotion_scores
        
        # Intensity indicators
        intensity_boosters = [
            response.count('!'),  # Exclamation marks
            response.count('very'),  # Intensifiers
            response.count('extremely'),
            response.count('incredibly'),
        ]
        
        intensity_factor = 1.0 + (sum(intensity_boosters) * 0.1)  # Up to 40% boost
        intensity_factor = min(1.4, intensity_factor)
        
        # Apply intensity scaling
        scaled_emotions = {emotion: min(1.0, score * intensity_factor) 
                          for emotion, score in emotion_scores.items()}
        
        return scaled_emotions
    
    @classmethod
    def detect_task_urgency(cls, response: str, context: Optional[List[Dict[str, str]]] = None) -> float:
        """
        Detect task urgency from response and context.
        
        Uses LLM analysis if available, falls back to regex patterns.
        
        Args:
            response: LLM response text
            context: Optional conversation context
            
        Returns:
            Urgency score (0.0-1.0), higher = more urgent
        """
        if not response:
            return 0.0
        
        # Try comprehensive LLM analysis first
        if cls._llm_enabled and cls._llm_client:
            try:
                analysis = cls.analyze_response_comprehensive(response, context)
                if analysis and analysis.get("analysis_method") == "llm":
                    return analysis.get("urgency", 0.0)
            except Exception:
                pass  # Fall through to regex
        
        # Fallback to regex patterns
        response_lower = response.lower()
        
        # Count urgency indicators in response
        urgency_count = sum(len(re.findall(p, response_lower, re.IGNORECASE)) 
                          for p in cls.URGENT_PATTERNS)
        
        # Check context for urgency
        if context:
            context_text = " ".join(msg.get("content", "").lower() for msg in context[-3:])
            context_urgency = sum(len(re.findall(p, context_text, re.IGNORECASE)) 
                               for p in cls.URGENT_PATTERNS)
            urgency_count += context_urgency * 0.5  # Context urgency weighted less
        
        # Normalize to 0-1 range
        urgency = min(1.0, urgency_count / 5.0)
        return urgency
    
    @classmethod
    def measure_engagement_level(cls, response: str, context: Optional[List[Dict[str, str]]] = None) -> float:
        """
        Measure user engagement level from conversation patterns.
        
        Uses LLM analysis if available, falls back to regex patterns.
        
        Args:
            response: LLM response text
            context: Optional conversation context
            
        Returns:
            Engagement score (0.0-1.0), higher = more engaged
        """
        if not response:
            return 0.0
        
        # Try comprehensive LLM analysis first
        if cls._llm_enabled and cls._llm_client:
            try:
                analysis = cls.analyze_response_comprehensive(response, context)
                if analysis and analysis.get("analysis_method") == "llm":
                    return analysis.get("engagement", 0.5)
            except Exception:
                pass  # Fall through to regex
        
        # Fallback to regex patterns
        response_lower = response.lower()
        
        # Count engagement indicators
        high_engagement = sum(len(re.findall(p, response_lower, re.IGNORECASE)) 
                            for p in cls.HIGH_ENGAGEMENT_PATTERNS)
        low_engagement = sum(len(re.findall(p, response_lower, re.IGNORECASE)) 
                           for p in cls.LOW_ENGAGEMENT_PATTERNS)
        
        # Factor in response length (longer responses often indicate engagement)
        length_factor = min(1.0, len(response) / 1000.0)
        
        # Factor in question count (questions indicate engagement)
        question_count = response.count('?')
        question_factor = min(1.0, question_count / 3.0)
        
        # Check context for engagement
        if context:
            user_messages = [msg.get("content", "") for msg in context[-3:] 
                           if msg.get("role") == "user"]
            if user_messages:
                user_text = " ".join(user_messages).lower()
                user_high_engagement = sum(len(re.findall(p, user_text, re.IGNORECASE)) 
                                         for p in cls.HIGH_ENGAGEMENT_PATTERNS)
                high_engagement += user_high_engagement * 0.5
        
        # Combine factors
        engagement = (high_engagement * 0.4) - (low_engagement * 0.2) + (length_factor * 0.3) + (question_factor * 0.1)
        engagement = max(0.0, min(1.0, engagement))
        
        return engagement
    
    @classmethod
    def compute_arousal(cls, response: str, context: Optional[List[Dict[str, str]]] = None) -> Optional[float]:
        """
        Compute arousal (activation level) from response text.
        
        Uses LLM analysis if available, falls back to regex patterns.
        
        Args:
            response: LLM response text
            context: Optional conversation context
            
        Returns:
            Arousal level (0.0-1.0), or None if response is empty
        """
        if not response:
            return None
        
        # Try comprehensive LLM analysis first
        if cls._llm_enabled and cls._llm_client:
            try:
                analysis = cls.analyze_response_comprehensive(response, context)
                if analysis and analysis.get("analysis_method") == "llm":
                    return analysis.get("arousal", 0.5)
            except Exception:
                pass  # Fall through to regex
        
        # Fallback to regex patterns
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
    def calculate_informational_surprise(cls, expectation: str, reality: str) -> float:
        """
        Calculate informational surprise (novelty) between expectation and reality.
        Uses keyword overlap (Jaccard distance) as a proxy for semantic surprise.
        
        Args:
            expectation: What was expected (e.g., search query, reasoning intent)
            reality: What was actually found/generated (e.g., search result, final response)
            
        Returns:
            Surprise score (0.0-1.0), higher = more surprising/novel
        """
        if not expectation or not reality:
            return 0.0
            
        def get_keywords(text):
            # Simple tokenization and filtering
            words = re.findall(r'\w+', text.lower())
            # Filter out common stop words (minimal set)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'for'}
            return set(w for w in words if len(w) > 2 and w not in stop_words)
            
        set_exp = get_keywords(expectation)
        set_real = get_keywords(reality)
        
        if not set_exp or not set_real:
            return 0.5 # Neutral surprise if no keywords found
            
        intersection = set_exp.intersection(set_real)
        union = set_exp.union(set_real)
        
        # Jaccard Similarity
        similarity = len(intersection) / len(union)
        
        # Surprise is the inverse of similarity (Distance)
        # We cap it to avoid extreme sensitivity
        surprise = 1.0 - similarity
        
        return max(0.0, min(1.0, surprise))

    @classmethod
    def analyze_thoughts(cls, thoughts: str) -> Dict[str, float]:
        """
        Analyze internal thoughts (reasoning_content) for sensing metrics.
        
        Args:
            thoughts: Internal reasoning text
            
        Returns:
            Dictionary of metrics (uncertainty, conflict, depth)
        """
        if not thoughts:
            return {"uncertainty": 0.0, "conflict": 0.0, "depth": 0.0}
            
        uncertainty = cls.detect_uncertainty(thoughts) or 0.0
        conflict = cls.detect_logical_reversals(thoughts)
        
        # Depth based on length and complexity (number of steps/lines)
        depth = min(1.0, (len(thoughts) / 1000.0) + (thoughts.count('\n') / 20.0))
        
        return {
            "uncertainty": uncertainty,
            "conflict": conflict,
            "depth": depth
        }

    @classmethod
    def detect_logical_reversals(cls, text: str) -> float:
        """
        Detect logical reversals or mid-stream corrections in text.
        
        Args:
            text: Text to analyze (response or thoughts)
            
        Returns:
            Reversal score (0.0-1.0), higher = more corrections
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        reversal_count = sum(
            len(re.findall(pattern, text_lower, re.IGNORECASE))
            for pattern in cls.REVERSAL_PATTERNS
        )
        
        # Normalize: 1 reversal = 0.3, 3+ reversals = 1.0
        return min(1.0, reversal_count * 0.33)

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
    
    @classmethod
    def analyze_response_comprehensive(
        cls,
        response: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Comprehensive LLM-based analysis of response in a single call.
        
        Returns all metrics: confidence, uncertainty, valence, emotions, engagement, arousal.
        This is more efficient than calling individual methods separately.
        
        Args:
            response: LLM response text to analyze
            context: Optional conversation context
            
        Returns:
            Dictionary with all metrics, or None if response is empty or LLM unavailable
        """
        if not response:
            return None
        
        # Use LLM if available and enabled
        if cls._llm_enabled and cls._llm_client:
            try:
                return cls._analyze_with_llm(response, context)
            except Exception as e:
                logger.warning(f"LLM analysis failed, falling back to regex: {e}")
                # Fall through to regex fallback
        
        # Fallback to individual regex-based methods
        return cls._analyze_with_regex(response, context)
    
    @classmethod
    def _analyze_with_llm(
        cls,
        response: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Analyze response using LLM in a single comprehensive call."""
        start_time = time.time()
        error_msg = None
        
        context_text = ""
        if context:
            context_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in context[-3:]
            ])
        
        prompt = f"""Analyze this LLM response and extract all internal sensing metrics.

Response to analyze:
{response}

{f'Conversation context:\n{context_text}' if context_text else ''}

Extract and return the following metrics as a JSON object:
- "confidence": float 0.0-1.0 (certainty level, higher = more confident)
- "uncertainty": float 0.0-1.0 (uncertainty level, higher = more uncertain)
- "valence_positive": float 0.0-1.0 (positive sentiment intensity)
- "valence_negative": float 0.0-1.0 (negative sentiment intensity)
- "emotions": object with keys: "joy", "frustration", "curiosity" (each float 0.0-1.0)
- "engagement": float 0.0-1.0 (engagement level, higher = more engaged)
- "arousal": float 0.0-1.0 (activation level, higher = more activated)
- "urgency": float 0.0-1.0 (task urgency, higher = more urgent)

Consider semantic meaning, not just keywords. Return JSON only."""
        
        messages = [
            {
                "role": "system",
                "content": "You are an internal sensing analyzer. Extract psychological and cognitive metrics from LLM responses. Return JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            llm_response = cls._llm_client.chat(messages, temperature=0.0)
            content = cls._llm_client.extract_assistant_content(llm_response)
            
            if not content:
                raise ValueError("Empty LLM response")
            
            # Extract JSON from response
            content = content.strip()
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)
            
            # Ensure all required fields are present with defaults
            analysis_result = {
                "confidence": float(result.get("confidence", 0.5)),
                "uncertainty": float(result.get("uncertainty", 0.0)),
                "valence_positive": float(result.get("valence_positive", 0.0)),
                "valence_negative": float(result.get("valence_negative", 0.0)),
                "emotions": result.get("emotions", {"joy": 0.0, "frustration": 0.0, "curiosity": 0.0}),
                "engagement": float(result.get("engagement", 0.5)),
                "arousal": float(result.get("arousal", 0.5)),
                "urgency": float(result.get("urgency", 0.0)),
                "analysis_method": "llm"
            }
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Log the analysis
            if HAS_LOGGER:
                logger_instance = get_logger()
                if logger_instance is None:
                    try:
                        from ..config import config
                        logger_instance = initialize_logger(
                            log_path=getattr(config.internal_sensing, 'llm_pattern_log_path', 'data/llm_pattern_matching_log.csv'),
                            enabled=getattr(config.internal_sensing, 'llm_pattern_logging_enabled', True)
                        )
                    except Exception:
                        logger_instance = None
                
                if logger_instance:
                    logger_instance.log(
                        component="ResponseAnalyzer",
                        operation="analyze_comprehensive",
                        model=cls._llm_model,
                        input_text=response,
                        input_context={"context": context} if context else None,
                        output_metrics=analysis_result,
                        latency_ms=latency_ms
                    )
            
            return analysis_result
            
        except Exception as e:
            error_msg = str(e)
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Error in LLM comprehensive analysis: {e}", exc_info=True)
            
            # Log error
            if HAS_LOGGER:
                logger_instance = get_logger()
                if logger_instance:
                    logger_instance.log(
                        component="ResponseAnalyzer",
                        operation="analyze_comprehensive",
                        model=cls._llm_model,
                        input_text=response,
                        input_context={"context": context} if context else None,
                        latency_ms=latency_ms,
                        error=error_msg
                    )
            
            raise
    
    @classmethod
    def _analyze_with_regex(
        cls,
        response: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Fallback analysis using regex patterns (existing methods)."""
        confidence = cls.estimate_confidence(response) or 0.5
        uncertainty = cls.detect_uncertainty(response) or 0.0
        valence = cls.compute_valence(response, context) or (0.0, 0.0)
        emotions = cls.detect_emotion_categories(response)
        engagement = cls.measure_engagement_level(response, context)
        arousal = cls.compute_arousal(response) or 0.5
        urgency = cls.detect_task_urgency(response, context)
        
        return {
            "confidence": confidence,
            "uncertainty": uncertainty,
            "valence_positive": valence[0],
            "valence_negative": valence[1],
            "emotions": emotions,
            "engagement": engagement,
            "arousal": arousal,
            "urgency": urgency,
            "analysis_method": "regex"
        }
    
    @classmethod
    def analyze_responses_batch(
        cls,
        responses: List[str],
        contexts: Optional[List[Optional[List[Dict[str, str]]]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch analyze multiple responses efficiently.
        
        Args:
            responses: List of response texts
            contexts: Optional list of contexts (one per response)
            
        Returns:
            List of analysis dictionaries
        """
        if not responses:
            return []
        
        if contexts is None:
            contexts = [None] * len(responses)
        
        # Use LLM batching if available
        if cls._llm_enabled and cls._llm_client and len(responses) > 1:
            try:
                return cls._analyze_batch_with_llm(responses, contexts)
            except Exception as e:
                logger.warning(f"LLM batch analysis failed, falling back to individual: {e}")
        
        # Fallback: analyze individually
        return [cls.analyze_response_comprehensive(resp, ctx) or {} for resp, ctx in zip(responses, contexts)]
    
    @classmethod
    def _analyze_batch_with_llm(
        cls,
        responses: List[str],
        contexts: List[Optional[List[Dict[str, str]]]]
    ) -> List[Dict[str, Any]]:
        """Batch analyze multiple responses in a single LLM call."""
        prompt_parts = [
            "Analyze multiple LLM responses and extract internal sensing metrics for each.",
            "",
            "For each response, extract:",
            "- confidence: float 0.0-1.0",
            "- uncertainty: float 0.0-1.0",
            "- valence_positive: float 0.0-1.0",
            "- valence_negative: float 0.0-1.0",
            "- emotions: {{joy, frustration, curiosity}} (each float 0.0-1.0)",
            "- engagement: float 0.0-1.0",
            "- arousal: float 0.0-1.0",
            "- urgency: float 0.0-1.0",
            "",
            "Return a JSON array with one object per response:",
            "[",
            "  {{",
            "    \"confidence\": 0.0-1.0,",
            "    \"uncertainty\": 0.0-1.0,",
            "    \"valence_positive\": 0.0-1.0,",
            "    \"valence_negative\": 0.0-1.0,",
            "    \"emotions\": {{\"joy\": 0.0, \"frustration\": 0.0, \"curiosity\": 0.0}},",
            "    \"engagement\": 0.0-1.0,",
            "    \"arousal\": 0.0-1.0,",
            "    \"urgency\": 0.0-1.0",
            "  }},",
            "  ...",
            "]",
            "",
            "Responses to analyze:",
            ""
        ]
        
        for i, (response, context) in enumerate(zip(responses, contexts)):
            prompt_parts.append(f"Response {i + 1}:")
            prompt_parts.append(response)
            if context:
                context_text = "\n".join([
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in context[-3:]
                ])
                prompt_parts.append(f"Context:\n{context_text}")
            prompt_parts.append("")
        
        prompt = "\n".join(prompt_parts)
        
        messages = [
            {
                "role": "system",
                "content": "You are an internal sensing analyzer. Extract psychological and cognitive metrics from LLM responses. Return JSON array only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            llm_response = cls._llm_client.chat(messages, temperature=0.0)
            content = cls._llm_client.extract_assistant_content(llm_response)
            
            if not content:
                raise ValueError("Empty LLM response")
            
            # Extract JSON array
            content = content.strip()
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Find JSON array
            json_match = re.search(r'\[[^\]]*(?:\{[^{}]*\}[^\]]*)*\]', content, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
            else:
                results = json.loads(content)
            
            # Ensure all results have required fields
            normalized_results = []
            for result in results:
                normalized_results.append({
                    "confidence": float(result.get("confidence", 0.5)),
                    "uncertainty": float(result.get("uncertainty", 0.0)),
                    "valence_positive": float(result.get("valence_positive", 0.0)),
                    "valence_negative": float(result.get("valence_negative", 0.0)),
                    "emotions": result.get("emotions", {"joy": 0.0, "frustration": 0.0, "curiosity": 0.0}),
                    "engagement": float(result.get("engagement", 0.5)),
                    "arousal": float(result.get("arousal", 0.5)),
                    "urgency": float(result.get("urgency", 0.0)),
                    "analysis_method": "llm_batch"
                })
            
            # Ensure we have the right number of results
            while len(normalized_results) < len(responses):
                normalized_results.append(normalized_results[-1] if normalized_results else {})
            normalized_results = normalized_results[:len(responses)]
            
            return normalized_results
            
        except Exception as e:
            logger.error(f"Error in LLM batch analysis: {e}", exc_info=True)
            raise

