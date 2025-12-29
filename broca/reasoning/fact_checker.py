"""
Fact-checking module using web search for verifying factual claims.

Integrates with WebSearchTool to fact-check verifiable claims in responses
and detect contradictions with existing knowledge.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FactualClaim:
    """A factual claim extracted from text."""
    text: str
    claim_type: str  # "factual", "numerical", "temporal", "categorical"
    confidence: float  # 0.0-1.0, how confident we are this is a verifiable claim
    context: Optional[str] = None


@dataclass
class FactCheckResult:
    """Result of fact-checking a claim."""
    claim: FactualClaim
    verified: bool  # True if claim is verified by web search
    contradiction_score: float  # 0.0-1.0, how much the claim contradicts web results
    evidence: List[str]  # Evidence from web search
    confidence: float  # 0.0-1.0, confidence in fact-check result


class FactChecker:
    """
    Fact-checker using web search to verify factual claims.
    
    Extracts verifiable claims from text and uses web search to verify them,
    detecting contradictions with search results.
    """
    
    # Patterns for extracting factual claims
    NUMERICAL_PATTERN = re.compile(r'\b(\d+)\s*(?:year|month|day|hour|minute|second|percent|%|dollar|\$|kg|lb|mile|km|meter|m|inch|cm)\b', re.IGNORECASE)
    TEMPORAL_PATTERN = re.compile(r'\b(?:in|on|at|during|since|until|before|after)\s+(\d{4}|\w+\s+\d{1,2},?\s+\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE)
    DEFINITIVE_PATTERN = re.compile(r'\b(?:is|are|was|were|will be|has been|have been|always|never|all|every|none|no)\b', re.IGNORECASE)
    
    def __init__(
        self,
        web_search_tool: Optional[Any] = None,
        enable_web_search: bool = True,
        min_claim_confidence: float = 0.3
    ):
        """
        Initialize fact checker.
        
        Args:
            web_search_tool: WebSearchTool instance (optional, will create if None)
            enable_web_search: Whether to enable web search fact-checking
            min_claim_confidence: Minimum confidence to consider a claim verifiable
        """
        self.enable_web_search = enable_web_search
        self.min_claim_confidence = min_claim_confidence
        self._web_search_tool = web_search_tool
        
        logger.info(
            f"Initialized FactChecker "
            f"(enable_web_search={enable_web_search}, "
            f"min_claim_confidence={min_claim_confidence})"
        )
    
    def _get_web_search_tool(self) -> Optional[Any]:
        """Get or create web search tool."""
        if not self.enable_web_search:
            return None
        
        if self._web_search_tool is not None:
            return self._web_search_tool
        
        try:
            from ..tools.web_search import WebSearchTool
            self._web_search_tool = WebSearchTool()
            return self._web_search_tool
        except Exception as e:
            logger.warning(f"Failed to initialize WebSearchTool: {e}")
            return None
    
    def extract_factual_claims(self, text: str) -> List[FactualClaim]:
        """
        Extract verifiable factual claims from text.
        
        Args:
            text: Text to extract claims from
            
        Returns:
            List of FactualClaim objects
        """
        claims: List[FactualClaim] = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            # Check for numerical claims
            if self.NUMERICAL_PATTERN.search(sentence):
                confidence = 0.7  # High confidence for numerical claims
                claims.append(FactualClaim(
                    text=sentence,
                    claim_type="numerical",
                    confidence=confidence,
                    context=text[:200]  # First 200 chars as context
                ))
            
            # Check for temporal claims
            elif self.TEMPORAL_PATTERN.search(sentence):
                confidence = 0.6  # Medium-high confidence for temporal claims
                claims.append(FactualClaim(
                    text=sentence,
                    claim_type="temporal",
                    confidence=confidence,
                    context=text[:200]
                ))
            
            # Check for definitive statements (always, never, all, etc.)
            elif self.DEFINITIVE_PATTERN.search(sentence):
                # Lower confidence - these might be opinions
                confidence = 0.4
                claims.append(FactualClaim(
                    text=sentence,
                    claim_type="categorical",
                    confidence=confidence,
                    context=text[:200]
                ))
            
            # General factual claims (statements that sound factual)
            elif any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have']):
                # Lower confidence - might be opinions or subjective
                confidence = 0.3
                claims.append(FactualClaim(
                    text=sentence,
                    claim_type="factual",
                    confidence=confidence,
                    context=text[:200]
                ))
        
        # Filter by minimum confidence
        claims = [c for c in claims if c.confidence >= self.min_claim_confidence]
        
        logger.debug(f"Extracted {len(claims)} factual claims from text")
        return claims
    
    def fact_check_claim(
        self,
        claim: FactualClaim,
        existing_memories: Optional[List[Any]] = None
    ) -> FactCheckResult:
        """
        Fact-check a single claim using web search.
        
        Args:
            claim: FactualClaim to check
            existing_memories: Optional list of existing memories to check against
            
        Returns:
            FactCheckResult with verification status
        """
        if not self.enable_web_search:
            return FactCheckResult(
                claim=claim,
                verified=False,
                contradiction_score=0.0,
                evidence=[],
                confidence=0.0
            )
        
        web_search_tool = self._get_web_search_tool()
        if not web_search_tool:
            logger.debug("Web search tool not available for fact-checking")
            return FactCheckResult(
                claim=claim,
                verified=False,
                contradiction_score=0.0,
                evidence=[],
                confidence=0.0
            )
        
        try:
            # Create search query from claim
            # Extract key terms from claim text
            query = self._create_search_query(claim.text)
            
            # Perform web search
            search_result = web_search_tool.execute(query=query, max_results=5)
            
            if search_result.get("error"):
                logger.debug(f"Web search error: {search_result.get('error')}")
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    contradiction_score=0.0,
                    evidence=[],
                    confidence=0.0
                )
            
            results = search_result.get("results", [])
            if not results:
                # No results - can't verify
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    contradiction_score=0.0,
                    evidence=[],
                    confidence=0.0
                )
            
            # Analyze results for verification/contradiction
            verified, contradiction_score, evidence = self._analyze_search_results(
                claim.text,
                results
            )
            
            # Confidence based on number of results and their quality
            confidence = min(0.9, 0.5 + (len(results) * 0.1))
            
            return FactCheckResult(
                claim=claim,
                verified=verified,
                contradiction_score=contradiction_score,
                evidence=[r.get("content", "")[:200] for r in results[:3]],  # First 3 results
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error fact-checking claim: {e}", exc_info=True)
            return FactCheckResult(
                claim=claim,
                verified=False,
                contradiction_score=0.0,
                evidence=[],
                confidence=0.0
            )
    
    def _create_search_query(self, claim_text: str) -> str:
        """Create a search query from claim text."""
        # Remove common words and keep key terms
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'this', 'that', 'these', 'those'}
        words = claim_text.lower().split()
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Take first 5 key words
        query = ' '.join(key_words[:5])
        
        # If query is too short, use original text (truncated)
        if len(query) < 10:
            query = claim_text[:100]
        
        return query
    
    def _analyze_search_results(
        self,
        claim_text: str,
        results: List[Dict[str, Any]]
    ) -> Tuple[bool, float, List[str]]:
        """
        Analyze web search results to determine if claim is verified or contradicted.
        
        Args:
            claim_text: Original claim text
            results: List of search results
            
        Returns:
            Tuple of (verified, contradiction_score, evidence)
        """
        claim_lower = claim_text.lower()
        
        # Extract key terms from claim
        claim_terms = set(re.findall(r'\b\w{4,}\b', claim_lower))
        
        verified_count = 0
        contradiction_count = 0
        evidence: List[str] = []
        
        for result in results:
            content = result.get("content", "").lower()
            title = result.get("title", "").lower()
            combined = f"{title} {content}"
            
            # Check if result mentions key terms
            result_terms = set(re.findall(r'\b\w{4,}\b', combined))
            overlap = claim_terms & result_terms
            
            if len(overlap) < 2:
                # Not relevant enough
                continue
            
            evidence.append(result.get("content", "")[:200])
            
            # Simple heuristic: check for contradiction patterns
            # Look for negation words near key terms
            negation_words = {'not', 'no', 'never', 'none', 'false', 'incorrect', 'wrong', 'disproven', 'debunked'}
            has_negation = any(neg in combined for neg in negation_words)
            
            # Check for agreement patterns
            agreement_words = {'yes', 'true', 'correct', 'confirmed', 'verified', 'accurate', 'fact'}
            has_agreement = any(agr in combined for agr in agreement_words)
            
            if has_negation and not has_agreement:
                contradiction_count += 1
            elif has_agreement or (not has_negation and len(overlap) >= 3):
                verified_count += 1
        
        # Determine verification status
        total_relevant = verified_count + contradiction_count
        if total_relevant == 0:
            verified = False
            contradiction_score = 0.0
        else:
            verified = verified_count > contradiction_count
            contradiction_score = contradiction_count / total_relevant if total_relevant > 0 else 0.0
        
        return verified, contradiction_score, evidence
    
    def fact_check_response(
        self,
        response: str,
        existing_memories: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Fact-check an entire response.
        
        Args:
            response: Response text to fact-check
            existing_memories: Optional list of existing memories
            
        Returns:
            Dictionary with fact-check results:
                - claims: List of FactualClaim objects
                - results: List of FactCheckResult objects
                - overall_contradiction_score: 0.0-1.0
                - verified_claims_count: int
                - contradicted_claims_count: int
        """
        # Extract claims
        claims = self.extract_factual_claims(response)
        
        if not claims:
            return {
                "claims": [],
                "results": [],
                "overall_contradiction_score": 0.0,
                "verified_claims_count": 0,
                "contradicted_claims_count": 0
            }
        
        # Fact-check each claim
        results: List[FactCheckResult] = []
        for claim in claims:
            result = self.fact_check_claim(claim, existing_memories)
            results.append(result)
        
        # Calculate overall scores
        contradicted_count = sum(1 for r in results if r.contradiction_score > 0.5)
        verified_count = sum(1 for r in results if r.verified and r.contradiction_score < 0.3)
        
        # Overall contradiction score (weighted by claim confidence)
        if results:
            total_weight = sum(r.claim.confidence for r in results)
            if total_weight > 0:
                weighted_contradiction = sum(
                    r.contradiction_score * r.claim.confidence
                    for r in results
                ) / total_weight
            else:
                weighted_contradiction = sum(r.contradiction_score for r in results) / len(results)
        else:
            weighted_contradiction = 0.0
        
        return {
            "claims": claims,
            "results": results,
            "overall_contradiction_score": weighted_contradiction,
            "verified_claims_count": verified_count,
            "contradicted_claims_count": contradicted_count
        }

