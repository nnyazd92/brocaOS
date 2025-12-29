"""
Citation Builder - Creates citations from browse traces.

Provides citation schema and building functionality for
provenance and auditability.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from .browse_trace import BrowseTrace, VisitedURL

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation for a claim or piece of information."""
    url: str
    timestamp: str  # ISO format
    content_hash: str  # SHA256
    extracted_span: Optional[str] = None  # Relevant quote
    title: Optional[str] = None
    domain: str = ""
    reliability_score: float = 0.0  # 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Citation:
        """Create from dictionary."""
        return cls(**data)


class CitationBuilder:
    """Builds citations from browse traces and visited URLs."""
    
    def __init__(self, domain_reputation: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize citation builder.
        
        Args:
            domain_reputation: Domain reputation data (loaded from config file)
        """
        self._domain_reputation = domain_reputation or {}
        logger.info("Initialized CitationBuilder")
    
    def build_citations(
        self,
        claims: List[Dict[str, Any]],
        browse_trace: BrowseTrace
    ) -> List[Citation]:
        """
        Build citations for claims from a browse trace.
        
        Args:
            claims: List of claim dictionaries with 'text' and optional 'url'
            browse_trace: Browse trace containing visited URLs
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        # Create a mapping of URLs to visited URL info
        url_map = {url.url: url for url in browse_trace.visited_urls}
        
        for claim in claims:
            claim_url = claim.get("url")
            claim_text = claim.get("text", "")
            extracted_span = claim.get("extracted_span")
            
            if claim_url and claim_url in url_map:
                visited = url_map[claim_url]
                citation = self._create_citation_from_visited(
                    visited,
                    extracted_span=extracted_span,
                    title=claim.get("title")
                )
                citations.append(citation)
            elif claim_url:
                # URL not in trace, create citation from URL only
                citation = self._create_citation_from_url(
                    claim_url,
                    extracted_span=extracted_span,
                    title=claim.get("title")
                )
                citations.append(citation)
        
        return citations
    
    def _create_citation_from_visited(
        self,
        visited: VisitedURL,
        extracted_span: Optional[str] = None,
        title: Optional[str] = None
    ) -> Citation:
        """Create citation from VisitedURL."""
        domain = self._extract_domain(visited.url)
        reliability_score = self._compute_reliability_score(domain)
        
        return Citation(
            url=visited.url,
            timestamp=visited.timestamp,
            content_hash=visited.content_hash or "",
            extracted_span=extracted_span,
            title=title,
            domain=domain,
            reliability_score=reliability_score
        )
    
    def _create_citation_from_url(
        self,
        url: str,
        extracted_span: Optional[str] = None,
        title: Optional[str] = None
    ) -> Citation:
        """Create citation from URL only."""
        from datetime import datetime, timezone
        
        domain = self._extract_domain(url)
        reliability_score = self._compute_reliability_score(domain)
        
        return Citation(
            url=url,
            timestamp=datetime.now(timezone.utc).isoformat(),
            content_hash="",  # Unknown
            extracted_span=extracted_span,
            title=title,
            domain=domain,
            reliability_score=reliability_score
        )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""
    
    def _compute_reliability_score(self, domain: str) -> float:
        """
        Compute reliability score for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            Reliability score (0.0-1.0)
        """
        if not self._domain_reputation:
            return 0.5  # Default neutral score
        
        allowlist = self._domain_reputation.get("allowlist", {})
        denylist = self._domain_reputation.get("denylist", {})
        default_score = self._domain_reputation.get("default_score", 0)
        
        # Check allowlist
        for category, data in allowlist.items():
            domains = data.get("domains", [])
            score = data.get("score", 0)
            
            for pattern in domains:
                if self._domain_matches(pattern, domain):
                    # Normalize score to 0.0-1.0 (assuming max score is 10)
                    return min(score / 10.0, 1.0)
        
        # Check denylist
        for category, data in denylist.items():
            domains = data.get("domains", [])
            score = data.get("score", 0)
            
            for pattern in domains:
                if self._domain_matches(pattern, domain):
                    # Normalize score to 0.0-1.0 (assuming min score is -10)
                    return max(score / 10.0, 0.0)
        
        # Default score (normalize to 0.0-1.0)
        return max(min(default_score / 10.0, 1.0), 0.0)
    
    def _domain_matches(self, pattern: str, domain: str) -> bool:
        """
        Check if domain matches a pattern.
        
        Supports wildcards like "*.example.com"
        """
        if pattern == domain:
            return True
        
        if pattern.startswith("*."):
            suffix = pattern[2:]  # Remove "*."
            return domain.endswith("." + suffix) or domain == suffix
        
        return False
    
    def format_citations(self, citations: List[Citation]) -> str:
        """
        Format citations for display.
        
        Args:
            citations: List of citations
            
        Returns:
            Formatted string
        """
        if not citations:
            return ""
        
        lines = ["Citations:"]
        
        for i, citation in enumerate(citations, 1):
            lines.append(f"\n[{i}] {citation.title or citation.url}")
            if citation.extracted_span:
                lines.append(f"    Quote: \"{citation.extracted_span[:200]}...\"")
            lines.append(f"    URL: {citation.url}")
            lines.append(f"    Domain: {citation.domain}")
            lines.append(f"    Reliability: {citation.reliability_score:.2f}")
            lines.append(f"    Accessed: {citation.timestamp}")
            if citation.content_hash:
                lines.append(f"    Content Hash: {citation.content_hash[:16]}...")
        
        return "\n".join(lines)

