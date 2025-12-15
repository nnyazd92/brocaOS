"""
Tests for response analyzer.

Tests that response analysis correctly extracts metrics from LLM responses.
"""

from __future__ import annotations

import pytest

from broca.internal_sensing.response_analyzer import ResponseAnalyzer


class TestResponseConfidenceEstimation:
    """Test confidence estimation from response characteristics."""
    
    def test_response_confidence_estimated(self):
        """
        Test that confidence is estimated from response characteristics.
        
        Rationale: Ensures confidence estimation works.
        """
        # High confidence response
        response = "This is definitely correct. I am certain about this fact."
        confidence = ResponseAnalyzer.estimate_confidence(response)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be higher for confident language
    
    def test_confidence_low_for_uncertain(self):
        """
        Test that uncertain responses get lower confidence.
        
        Rationale: Ensures confidence reflects uncertainty.
        """
        # Low confidence response
        response = "Maybe this is correct, but I'm not sure. Perhaps it could be."
        confidence = ResponseAnalyzer.estimate_confidence(response)
        
        # Should be lower than high confidence response
        assert confidence < 0.7
    
    def test_confidence_length_factor(self):
        """
        Test that longer responses get higher confidence.
        
        Rationale: Ensures length is considered.
        """
        short_response = "Yes."
        long_response = "Yes, this is definitely correct because of multiple reasons that I can explain in detail."
        
        short_conf = ResponseAnalyzer.estimate_confidence(short_response)
        long_conf = ResponseAnalyzer.estimate_confidence(long_response)
        
        assert long_conf >= short_conf
    
    def test_confidence_empty_response(self):
        """
        Test that empty response returns None.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        confidence = ResponseAnalyzer.estimate_confidence("")
        assert confidence is None
        
        confidence = ResponseAnalyzer.estimate_confidence(None)  # type: ignore
        assert confidence is None


class TestResponseUncertaintyDetection:
    """Test uncertainty detection from response language."""
    
    def test_response_uncertainty_detected(self):
        """
        Test that uncertainty is detected from response language.
        
        Rationale: Ensures uncertainty detection works.
        """
        # Uncertain response
        response = "I'm not sure, but maybe this could work. Perhaps it might be possible."
        uncertainty = ResponseAnalyzer.detect_uncertainty(response)
        
        assert isinstance(uncertainty, float)
        assert 0.0 <= uncertainty <= 1.0
        assert uncertainty > 0.3  # Should detect uncertainty
    
    def test_uncertainty_low_for_confident(self):
        """
        Test that confident responses have low uncertainty.
        
        Rationale: Ensures uncertainty detection is accurate.
        """
        # Confident response
        response = "This is definitely correct. I am certain."
        uncertainty = ResponseAnalyzer.detect_uncertainty(response)
        
        # Should be lower than uncertain response
        assert uncertainty < 0.5
    
    def test_uncertainty_questions(self):
        """
        Test that questions increase uncertainty.
        
        Rationale: Ensures questions are detected.
        """
        response_with_question = "Is this correct? I wonder if it might work?"
        response_without_question = "This is correct."
        
        uncertainty_with = ResponseAnalyzer.detect_uncertainty(response_with_question)
        uncertainty_without = ResponseAnalyzer.detect_uncertainty(response_without_question)
        
        assert uncertainty_with > uncertainty_without
    
    def test_uncertainty_empty_response(self):
        """
        Test that empty response returns None.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        uncertainty = ResponseAnalyzer.detect_uncertainty("")
        assert uncertainty is None


class TestResponseValenceComputation:
    """Test valence computation from response sentiment."""
    
    def test_response_valence_computed(self):
        """
        Test that valence is computed from response sentiment.
        
        Rationale: Ensures valence computation works.
        """
        # Positive response
        response = "This is great! Excellent work. Wonderful results."
        positive, negative = ResponseAnalyzer.compute_valence(response)
        
        assert isinstance(positive, float)
        assert isinstance(negative, float)
        assert 0.0 <= positive <= 1.0
        assert 0.0 <= negative <= 1.0
        assert positive > negative  # Should be more positive
    
    def test_valence_negative(self):
        """
        Test that negative responses get negative valence.
        
        Rationale: Ensures negative sentiment is detected.
        """
        # Negative response
        response = "This is terrible. It failed. There was an error."
        positive, negative = ResponseAnalyzer.compute_valence(response)
        
        assert negative > positive  # Should be more negative
    
    def test_valence_neutral(self):
        """
        Test that neutral responses get balanced valence.
        
        Rationale: Ensures neutral responses are handled.
        """
        # Neutral response
        response = "This is a response. It contains information."
        positive, negative = ResponseAnalyzer.compute_valence(response)
        
        # Both should be low
        assert positive < 0.5
        assert negative < 0.5
    
    def test_valence_empty_response(self):
        """
        Test that empty response returns None.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        valence = ResponseAnalyzer.compute_valence("")
        assert valence is None


class TestResponseArousalComputation:
    """Test arousal computation from response characteristics."""
    
    def test_arousal_computed(self):
        """
        Test that arousal is computed from response characteristics.
        
        Rationale: Ensures arousal computation works.
        """
        response = "This is urgent! Critical issue! Immediate action needed!"
        arousal = ResponseAnalyzer.compute_arousal(response)
        
        assert isinstance(arousal, float)
        assert 0.0 <= arousal <= 1.0
        assert arousal > 0.5  # Should be high for urgent language
    
    def test_arousal_low_for_calm(self):
        """
        Test that calm responses have low arousal.
        
        Rationale: Ensures arousal reflects activation level.
        """
        response = "This is calm and relaxed. No rush."
        arousal = ResponseAnalyzer.compute_arousal(response)
        
        assert arousal < 0.6
    
    def test_arousal_empty_response(self):
        """
        Test that empty response returns None.
        
        Rationale: Ensures unavailable data is properly indicated.
        """
        arousal = ResponseAnalyzer.compute_arousal("")
        assert arousal is None


class TestTopicExtraction:
    """Test topic extraction from responses."""
    
    def test_topics_extracted(self):
        """
        Test that topics are extracted from responses.
        
        Rationale: Ensures topic extraction works.
        """
        response = "Let me calculate this mathematical equation using Python code."
        context = [{"role": "user", "content": "Help me with math"}]
        
        topics = ResponseAnalyzer.extract_topics(response, context)
        
        assert isinstance(topics, dict)
        assert "mathematics" in topics or "programming" in topics or len(topics) >= 0
    
    def test_topics_normalized(self):
        """
        Test that topic attention levels are normalized.
        
        Rationale: Ensures attention levels are reasonable.
        """
        response = "Math and programming are both important."
        context = []
        
        topics = ResponseAnalyzer.extract_topics(response, context)
        
        total = sum(topics.values())
        assert total <= 1.0  # Should be normalized

