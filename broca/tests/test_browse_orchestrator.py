"""
Tests for BrowseOrchestrator implementation.

Tests high-level browse orchestration functionality.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest

from broca.tools.browse_orchestrator import BrowseOrchestrator


class TestBrowseOrchestratorInitialization:
    """Test BrowseOrchestrator initialization."""
    
    @patch('broca.tools.browse_orchestrator.BrowserKernel')
    @patch('broca.tools.browse_orchestrator.BrowseTraceManager')
    @patch('broca.tools.browse_orchestrator.CitationBuilder')
    @patch('broca.tools.browse_orchestrator.BrowseSafety')
    def test_init_creates_components(self, mock_safety, mock_citation, mock_trace, mock_kernel):
        """Test that initialization creates all components."""
        orchestrator = BrowseOrchestrator()
        
        assert orchestrator._kernel is not None
        assert orchestrator._trace_manager is not None
        assert orchestrator._citation_builder is not None
        assert orchestrator._safety is not None


class TestBrowseOrchestratorSearch:
    """Test search functionality."""
    
    @patch('broca.tools.browse_orchestrator.BrowserKernel')
    @patch('broca.tools.browse_orchestrator.BrowseTraceManager')
    @patch('broca.tools.browse_orchestrator.CitationBuilder')
    @patch('broca.tools.browse_orchestrator.BrowseSafety')
    def test_search_returns_results(self, mock_safety, mock_citation, mock_trace, mock_kernel):
        """Test that search returns results."""
        mock_kernel_instance = Mock()
        mock_kernel_instance.new_session.return_value = "session123"
        mock_kernel_instance.search.return_value = [
            {"title": "Test", "url": "https://example.com", "snippet": "Test snippet", "rank": 1, "displayed_domain": "example.com"}
        ]
        mock_kernel.return_value = mock_kernel_instance
        
        mock_trace_instance = Mock()
        mock_trace_instance.create_trace.return_value = Mock()
        mock_trace.return_value = mock_trace_instance
        
        orchestrator = BrowseOrchestrator(browser_kernel=mock_kernel_instance, trace_manager=mock_trace_instance)
        
        result = orchestrator.search("test query", max_results=1)
        
        assert result["count"] >= 0
        assert "query" in result
        assert "results" in result


class TestBrowseOrchestratorExtract:
    """Test extraction functionality."""
    
    @patch('broca.tools.browse_orchestrator.BrowserKernel')
    @patch('broca.tools.browse_orchestrator.BrowseTraceManager')
    @patch('broca.tools.browse_orchestrator.CitationBuilder')
    @patch('broca.tools.browse_orchestrator.BrowseSafety')
    def test_extract_article(self, mock_safety, mock_citation, mock_trace, mock_kernel):
        """Test article extraction."""
        mock_kernel_instance = Mock()
        mock_kernel_instance.new_session.return_value = "session123"
        mock_kernel_instance.goto.return_value = {"success": True, "status": 200}
        mock_kernel_instance.get_text.return_value = {
            "success": True,
            "text": "Extracted text",
            "extraction_method": "readability"
        }
        mock_kernel.return_value = mock_kernel_instance
        
        mock_trace_instance = Mock()
        mock_trace_instance.create_trace.return_value = Mock()
        mock_trace_instance.compute_content_hash.return_value = "hash123"
        mock_trace.return_value = mock_trace_instance
        
        orchestrator = BrowseOrchestrator(browser_kernel=mock_kernel_instance, trace_manager=mock_trace_instance)
        
        result = orchestrator.extract_article("https://example.com")
        
        assert result.get("success") is True
        assert "text" in result

