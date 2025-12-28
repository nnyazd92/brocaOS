"""
Tests for web search fact-checking integration.

Tests FactChecker with web search, including fault injection.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from broca.reasoning.fact_checker import FactChecker, FactualClaim, FactCheckResult


@pytest.fixture
def fact_checker():
    """Create fact checker with web search enabled."""
    return FactChecker(enable_web_search=True)


class TestFactCheckerWebIntegration:
    """Test web search fact-checking integration."""
    
    def test_extract_factual_claims(self, fact_checker):
        """Test extraction of factual claims from text."""
        text = "The Earth is approximately 4.5 billion years old. In 2024, Python 3.12 was released."
        
        claims = fact_checker.extract_factual_claims(text)
        
        assert len(claims) > 0
        assert all(isinstance(c, FactualClaim) for c in claims)
        assert all(c.confidence >= fact_checker.min_claim_confidence for c in claims)
    
    def test_fact_check_claim_with_web_search(self, fact_checker):
        """Test fact-checking a claim using web search."""
        claim = FactualClaim(
            text="The Earth is round",
            claim_type="factual",
            confidence=0.7
        )
        
        with patch.object(fact_checker, '_get_web_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool.execute.return_value = {
                "results": [
                    {
                        "title": "Earth is Round",
                        "content": "The Earth is indeed round, as confirmed by scientific evidence.",
                        "url": "https://example.com"
                    }
                ],
                "count": 1
            }
            mock_get_tool.return_value = mock_tool
            
            result = fact_checker.fact_check_claim(claim)
            
            assert isinstance(result, FactCheckResult)
            assert result.claim == claim
            assert isinstance(result.verified, bool)
            assert 0.0 <= result.contradiction_score <= 1.0
    
    def test_fact_check_response(self, fact_checker):
        """Test fact-checking an entire response."""
        response = "The speed of light is 300,000 km/s. The moon is made of cheese."
        
        with patch.object(fact_checker, '_get_web_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool.execute.return_value = {
                "results": [
                    {
                        "title": "Speed of Light",
                        "content": "The speed of light is approximately 299,792 km/s.",
                        "url": "https://example.com"
                    }
                ],
                "count": 1
            }
            mock_get_tool.return_value = mock_tool
            
            result = fact_checker.fact_check_response(response)
            
            assert "claims" in result
            assert "results" in result
            assert "overall_contradiction_score" in result
            assert isinstance(result["overall_contradiction_score"], float)
            assert 0.0 <= result["overall_contradiction_score"] <= 1.0
    
    def test_web_search_failure_graceful_degradation(self, fact_checker):
        """Test graceful degradation when web search fails."""
        claim = FactualClaim(
            text="Test claim",
            claim_type="factual",
            confidence=0.7
        )
        
        with patch.object(fact_checker, '_get_web_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool.execute.return_value = {
                "results": [],
                "error": "Web search failed",
                "count": 0
            }
            mock_get_tool.return_value = mock_tool
            
            result = fact_checker.fact_check_claim(claim)
            
            # Should return result even on failure
            assert isinstance(result, FactCheckResult)
            assert result.verified == False
            assert result.contradiction_score == 0.0
    
    def test_web_search_timeout_handling(self, fact_checker):
        """Test handling of web search timeouts."""
        claim = FactualClaim(
            text="Test claim",
            claim_type="factual",
            confidence=0.7
        )
        
        with patch.object(fact_checker, '_get_web_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool.execute.side_effect = TimeoutError("Search timeout")
            mock_get_tool.return_value = mock_tool
            
            result = fact_checker.fact_check_claim(claim)
            
            # Should handle timeout gracefully
            assert isinstance(result, FactCheckResult)
            assert result.verified == False
    
    def test_web_search_unavailable(self, fact_checker):
        """Test behavior when web search tool is unavailable."""
        claim = FactualClaim(
            text="Test claim",
            claim_type="factual",
            confidence=0.7
        )
        
        with patch.object(fact_checker, '_get_web_search_tool', return_value=None):
            result = fact_checker.fact_check_claim(claim)
            
            # Should return result indicating no verification
            assert isinstance(result, FactCheckResult)
            assert result.verified == False
            assert result.confidence == 0.0
    
    def test_fact_checker_without_web_search(self):
        """Test fact checker with web search disabled."""
        fact_checker = FactChecker(enable_web_search=False)
        
        response = "Test response with factual claims."
        
        result = fact_checker.fact_check_response(response)
        
        # Should still extract claims but not verify them
        assert "claims" in result
        assert "overall_contradiction_score" in result
        assert result["overall_contradiction_score"] == 0.0  # No verification = no contradictions detected

