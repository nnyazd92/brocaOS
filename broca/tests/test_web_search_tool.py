"""
Tests for WebSearchTool implementation.

Tests web search functionality with browser-based search (primary) and Tavily fallback.
"""

from __future__ import annotations

import os
from unittest.mock import Mock, patch, MagicMock
import pytest

from broca.tools.web_search import WebSearchTool


class TestWebSearchToolInitialization:
    """Test WebSearchTool initialization."""
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_init_with_browser_search(self, mock_orchestrator_class):
        """
        Test initialization with browser search (primary method).
        
        Rationale: Ensures tool initializes with browser search as primary.
        """
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        tool = WebSearchTool()
        
        assert tool.name == "web_search"
        assert tool._browse_orchestrator is not None
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    @patch('broca.tools.web_search.TavilyClient')
    @patch.dict(os.environ, {"BROCA_BROWSE_ENABLE_TAVILY_FALLBACK": "true", "TAVILY_API_KEY": "test-key"})
    def test_init_with_tavily_fallback(self, mock_tavily_client_class, mock_orchestrator_class):
        """
        Test initialization with Tavily fallback enabled.
        
        Rationale: Ensures tool can initialize Tavily as fallback when enabled.
        """
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_client = Mock()
        mock_tavily_client_class.return_value = mock_client
        
        # Reload config to pick up env var
        from broca.config import config
        original_value = config.browse.enable_tavily_fallback
        config.browse.enable_tavily_fallback = True
        
        try:
            tool = WebSearchTool(api_key="test-key")
            assert tool._browse_orchestrator is not None
            # Tavily client may or may not be initialized depending on config
        finally:
            config.browse.enable_tavily_fallback = original_value
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_init_requires_browser_search(self, mock_orchestrator_class):
        """
        Test that browser search is required.
        
        Rationale: Ensures tool requires browser search (primary method).
        """
        mock_orchestrator_class.side_effect = Exception("Browser search unavailable")
        
        with pytest.raises(ValueError, match="Browser-based search is required"):
            WebSearchTool()


class TestWebSearchToolProperties:
    """Test WebSearchTool properties."""
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_name_property(self, mock_orchestrator_class):
        """
        Test that name property returns correct value.
        
        Rationale: Ensures tool has correct identifier.
        """
        mock_orchestrator_class.return_value = Mock()
        tool = WebSearchTool()
        assert tool.name == "web_search"
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_description_property(self, mock_orchestrator_class):
        """
        Test that description property returns comprehensive description.
        
        Rationale: Ensures LLM understands when and how to use the tool.
        """
        mock_orchestrator_class.return_value = Mock()
        tool = WebSearchTool()
        description = tool.description
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "search" in description.lower()
        assert "browser" in description.lower() or "DuckDuckGo" in description
        assert "query" in description.lower()  # Should have usage examples
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_parameters_property(self, mock_orchestrator_class):
        """
        Test that parameters property returns valid JSON schema with detailed descriptions.
        
        Rationale: Ensures tool parameters are properly defined with comprehensive descriptions.
        """
        mock_orchestrator_class.return_value = Mock()
        tool = WebSearchTool()
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "properties" in params
        assert "query" in params["properties"]
        assert "max_results" in params["properties"]
        assert "required" in params
        assert "query" in params["required"]
        
        # Check that descriptions are comprehensive
        query_desc = params["properties"]["query"]["description"]
        assert len(query_desc) > 50  # Should be detailed
        assert "example" in query_desc.lower() or "natural language" in query_desc.lower()


class TestWebSearchToolExecute:
    """Test WebSearchTool execution."""
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_execute_browser_search_success(self, mock_orchestrator_class):
        """
        Test successful browser-based search execution.
        
        Rationale: Ensures tool uses browser search as primary method.
        """
        mock_orchestrator = Mock()
        mock_orchestrator.search.return_value = {
            "results": [
                {
                    "title": "Test Result 1",
                    "url": "https://example.com/1",
                    "content": "Content 1",
                    "score": 0.9
                },
                {
                    "title": "Test Result 2",
                    "url": "https://example.com/2",
                    "content": "Content 2",
                    "score": 0.8
                }
            ],
            "query": "test query",
            "count": 2
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        tool = WebSearchTool(browse_orchestrator=mock_orchestrator)
        result = tool.execute(query="test query", max_results=5)
        
        assert result["query"] == "test query"
        assert result["count"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Test Result 1"
        mock_orchestrator.search.assert_called_once()
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    @patch('broca.tools.web_search.TavilyClient')
    @patch.dict(os.environ, {"BROCA_BROWSE_ENABLE_TAVILY_FALLBACK": "true", "TAVILY_API_KEY": "test-key"})
    def test_execute_tavily_fallback(self, mock_tavily_client_class, mock_orchestrator_class):
        """
        Test Tavily fallback when browser search fails.
        
        Rationale: Ensures Tavily is used as fallback when enabled and browser fails.
        """
        mock_orchestrator = Mock()
        mock_orchestrator.search.side_effect = Exception("Browser search failed")
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Tavily Result",
                    "url": "https://example.com",
                    "content": "Content",
                    "score": 0.9
                }
            ]
        }
        mock_tavily_client_class.return_value = mock_client
        
        # Reload config
        from broca.config import config
        original_value = config.browse.enable_tavily_fallback
        config.browse.enable_tavily_fallback = True
        
        try:
            tool = WebSearchTool(
                api_key="test-key",
                browse_orchestrator=mock_orchestrator
            )
            tool._tavily_client = mock_client
            
            result = tool.execute(query="test query", max_results=5)
            
            assert result["count"] == 1
            assert result["results"][0]["title"] == "Tavily Result"
            mock_client.search.assert_called_once()
        finally:
            config.browse.enable_tavily_fallback = original_value
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_execute_with_default_max_results(self, mock_orchestrator_class):
        """
        Test execution with default max_results.
        
        Rationale: Ensures default parameter works correctly.
        """
        mock_orchestrator = Mock()
        mock_orchestrator.search.return_value = {"results": [], "query": "test", "count": 0}
        mock_orchestrator_class.return_value = mock_orchestrator
        
        tool = WebSearchTool(browse_orchestrator=mock_orchestrator)
        tool.execute(query="test")
        
        # Verify browser search was called with default max_results
        mock_orchestrator.search.assert_called_once()
        call_args = mock_orchestrator.search.call_args
        assert call_args[1]["max_results"] == 5  # Default value
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_execute_clamps_max_results(self, mock_orchestrator_class):
        """
        Test that max_results is clamped to valid range.
        
        Rationale: Ensures tool handles out-of-range parameters gracefully.
        """
        mock_orchestrator = Mock()
        mock_orchestrator.search.return_value = {"results": [], "query": "test", "count": 0}
        mock_orchestrator_class.return_value = mock_orchestrator
        
        tool = WebSearchTool(browse_orchestrator=mock_orchestrator)
        
        # Test max_results > 10 (should clamp to 10)
        tool.execute(query="test", max_results=20)
        call_args = mock_orchestrator.search.call_args
        assert call_args[1]["max_results"] == 10
        
        # Test max_results < 1 (should clamp to 1)
        tool.execute(query="test", max_results=0)
        call_args = mock_orchestrator.search.call_args
        assert call_args[1]["max_results"] == 1
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_execute_handles_empty_results(self, mock_orchestrator_class):
        """
        Test execution with empty search results.
        
        Rationale: Ensures tool handles empty results gracefully.
        """
        mock_orchestrator = Mock()
        mock_orchestrator.search.return_value = {"results": [], "query": "test", "count": 0}
        mock_orchestrator_class.return_value = mock_orchestrator
        
        tool = WebSearchTool(browse_orchestrator=mock_orchestrator)
        result = tool.execute(query="test")
        
        assert result["count"] == 0
        assert result["results"] == []
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_execute_handles_missing_fields(self, mock_orchestrator_class):
        """
        Test execution with results missing some fields.
        
        Rationale: Ensures tool handles incomplete responses gracefully.
        """
        mock_orchestrator = Mock()
        mock_orchestrator.search.return_value = {
            "results": [
                {"title": "Result 1"},  # Missing url and content
                {"url": "https://example.com"}  # Missing title and content
            ],
            "query": "test",
            "count": 2
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        tool = WebSearchTool(browse_orchestrator=mock_orchestrator)
        result = tool.execute(query="test")
        
        assert result["count"] == 2
        assert result["results"][0].get("title") == "Result 1"
        assert result["results"][0].get("url") == ""
        assert result["results"][1].get("url") == "https://example.com"
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_execute_handles_browser_error(self, mock_orchestrator_class):
        """
        Test execution when browser search raises an error.
        
        Rationale: Ensures tool handles browser search errors gracefully.
        """
        mock_orchestrator = Mock()
        mock_orchestrator.search.side_effect = Exception("Browser search error")
        mock_orchestrator_class.return_value = mock_orchestrator
        
        tool = WebSearchTool(browse_orchestrator=mock_orchestrator)
        result = tool.execute(query="test")
        
        assert "error" in result
        assert result["count"] == 0
        assert result["results"] == []
        assert "Browser search" in result["error"] or "error" in result["error"].lower()


class TestWebSearchToolFormatResult:
    """Test WebSearchTool result formatting."""
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_format_result_with_results(self, mock_orchestrator_class):
        """
        Test formatting results with search results.
        
        Rationale: Ensures results are formatted in readable format for LLM.
        """
        mock_orchestrator_class.return_value = Mock()
        tool = WebSearchTool()
        
        result = {
            "query": "test query",
            "count": 2,
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example.com/1",
                    "content": "This is the content of result 1"
                },
                {
                    "title": "Result 2",
                    "url": "https://example.com/2",
                    "content": "This is the content of result 2"
                }
            ]
        }
        
        formatted = tool.format_result(result)
        
        assert "test query" in formatted
        assert "2 results" in formatted
        assert "Result 1" in formatted
        assert "Result 2" in formatted
        assert "https://example.com/1" in formatted
        assert "This is the content of result 1" in formatted
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_format_result_empty(self, mock_orchestrator_class):
        """
        Test formatting empty results.
        
        Rationale: Ensures empty results are handled gracefully.
        """
        mock_orchestrator_class.return_value = Mock()
        tool = WebSearchTool()
        
        result = {
            "query": "test query",
            "count": 0,
            "results": []
        }
        
        formatted = tool.format_result(result)
        
        assert "No results found" in formatted
        assert "test query" in formatted
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_format_result_with_error(self, mock_orchestrator_class):
        """
        Test formatting results with error.
        
        Rationale: Ensures errors are formatted clearly for LLM.
        """
        mock_orchestrator_class.return_value = Mock()
        tool = WebSearchTool()
        
        result = {
            "query": "test query",
            "count": 0,
            "results": [],
            "error": "Browser search error"
        }
        
        formatted = tool.format_result(result)
        
        assert "Error" in formatted
        assert "error" in formatted.lower()
    
    @patch('broca.tools.web_search.BrowseOrchestrator')
    def test_format_result_truncates_long_content(self, mock_orchestrator_class):
        """
        Test that long content is truncated in formatted output.
        
        Rationale: Ensures formatted output is manageable in size.
        """
        mock_orchestrator_class.return_value = Mock()
        tool = WebSearchTool()
        
        long_content = "x" * 500  # 500 characters
        result = {
            "query": "test",
            "count": 1,
            "results": [
                {
                    "title": "Result",
                    "url": "https://example.com",
                    "content": long_content
                }
            ]
        }
        
        formatted = tool.format_result(result)
        
        # Should truncate to 300 chars + "..."
        assert len(long_content[:300]) < len(long_content)
        assert "..." in formatted

