"""
Tests for CitationBuilder implementation.

Tests citation building functionality.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest

from broca.tools.citation_builder import CitationBuilder, Citation
from broca.tools.browse_trace import BrowseTrace, VisitedURL
from datetime import datetime, timezone


class TestCitationBuilder:
    """Test CitationBuilder."""
    
    def test_build_citations(self):
        """Test building citations from claims and trace."""
        domain_reputation = {
            "allowlist": {
                "gov": {
                    "domains": ["*.gov"],
                    "score": 10
                }
            },
            "default_score": 0
        }
        
        builder = CitationBuilder(domain_reputation)
        
        # Create a mock trace
        trace = BrowseTrace(
            session_id="session123",
            task_id="task456",
            started_at=datetime.now(timezone.utc).isoformat()
        )
        
        trace.visited_urls.append(VisitedURL(
            url="https://example.gov/page",
            timestamp=datetime.now(timezone.utc).isoformat(),
            content_hash="hash123"
        ))
        
        claims = [
            {"text": "Test claim", "url": "https://example.gov/page"}
        ]
        
        citations = builder.build_citations(claims, trace)
        
        assert len(citations) == 1
        assert citations[0].url == "https://example.gov/page"
    
    def test_format_citations(self):
        """Test formatting citations."""
        builder = CitationBuilder()
        
        citations = [
            Citation(
                url="https://example.com",
                timestamp=datetime.now(timezone.utc).isoformat(),
                content_hash="hash123",
                title="Example",
                domain="example.com",
                reliability_score=0.8
            )
        ]
        
        formatted = builder.format_citations(citations)
        
        assert "Citations:" in formatted
        assert "example.com" in formatted

