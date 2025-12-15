"""
Tests for WebSearchTool implementation.

Tests web search functionality using mocked Tavily API.
"""

from __future__ import annotations

import os
from unittest.mock import Mock, patch, MagicMock
import pytest

from broca.tools.web_search import WebSearchTool


class TestWebSearchToolInitialization:
    """Test WebSearchTool initialization."""
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_init_with_api_key(self, mock_tavily_client_class):
        """
        Test initialization with provided API key.
        
        Rationale: Ensures tool can be initialized with explicit API key.
        """
        mock_client = Mock()
        mock_tavily_client_class.return_value = mock_client
        
        tool = WebSearchTool(api_key="test-api-key")
        
        assert tool.name == "web_search"
        assert tool._api_key == "test-api-key"
        mock_tavily_client_class.assert_called_once_with(api_key="test-api-key")
    
    @patch.dict(os.environ, {"TAVILY_API_KEY": "env-api-key"})
    @patch('broca.tools.web_search.TavilyClient')
    def test_init_with_env_var(self, mock_tavily_client_class):
        """
        Test initialization with API key from environment variable.
        
        Rationale: Ensures tool can use environment variable for API key.
        """
        mock_client = Mock()
        mock_tavily_client_class.return_value = mock_client
        
        tool = WebSearchTool()
        
        assert tool._api_key == "env-api-key"
        mock_tavily_client_class.assert_called_once_with(api_key="env-api-key")
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('broca.tools.web_search.TavilyClient')
    def test_init_missing_api_key_raises_error(self, mock_tavily_client_class):
        """
        Test that missing API key raises ValueError.
        
        Rationale: Ensures tool requires API key for initialization.
        """
        with pytest.raises(ValueError, match="API key is required"):
            WebSearchTool()
    
    def test_init_missing_tavily_package_raises_error(self):
        """
        Test that missing tavily-python package raises ValueError.
        
        Rationale: Ensures clear error when required package is not installed.
        """
        with patch('broca.tools.web_search.TavilyClient', None):
            with pytest.raises(ValueError, match="tavily-python package is not installed"):
                WebSearchTool(api_key="test-key")


class TestWebSearchToolProperties:
    """Test WebSearchTool properties."""
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_name_property(self, mock_tavily_client_class):
        """
        Test that name property returns correct value.
        
        Rationale: Ensures tool has correct identifier.
        """
        tool = WebSearchTool(api_key="test-key")
        assert tool.name == "web_search"
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_description_property(self, mock_tavily_client_class):
        """
        Test that description property returns informative description.
        
        Rationale: Ensures LLM understands when to use the tool.
        """
        tool = WebSearchTool(api_key="test-key")
        description = tool.description
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "search" in description.lower()
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_parameters_property(self, mock_tavily_client_class):
        """
        Test that parameters property returns valid JSON schema.
        
        Rationale: Ensures tool parameters are properly defined for function calling.
        """
        tool = WebSearchTool(api_key="test-key")
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "properties" in params
        assert "query" in params["properties"]
        assert "max_results" in params["properties"]
        assert "required" in params
        assert "query" in params["required"]


class TestWebSearchToolExecute:
    """Test WebSearchTool execution."""
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_execute_success(self, mock_tavily_client_class):
        """
        Test successful web search execution.
        
        Rationale: Ensures tool can execute searches and return structured results.
        """
        mock_client = Mock()
        mock_client.search.return_value = {
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
            ]
        }
        mock_tavily_client_class.return_value = mock_client
        
        tool = WebSearchTool(api_key="test-key")
        result = tool.execute(query="test query", max_results=5)
        
        assert result["query"] == "test query"
        assert result["count"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Test Result 1"
        assert result["results"][0]["url"] == "https://example.com/1"
        mock_client.search.assert_called_once_with(
            query="test query",
            max_results=5,
            search_depth="basic"
        )
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_execute_with_default_max_results(self, mock_tavily_client_class):
        """
        Test execution with default max_results.
        
        Rationale: Ensures default parameter works correctly.
        """
        mock_client = Mock()
        mock_client.search.return_value = {"results": []}
        mock_tavily_client_class.return_value = mock_client
        
        tool = WebSearchTool(api_key="test-key")
        tool.execute(query="test")
        
        mock_client.search.assert_called_once_with(
            query="test",
            max_results=5,
            search_depth="basic"
        )
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_execute_clamps_max_results(self, mock_tavily_client_class):
        """
        Test that max_results is clamped to valid range.
        
        Rationale: Ensures tool handles out-of-range parameters gracefully.
        """
        mock_client = Mock()
        mock_client.search.return_value = {"results": []}
        mock_tavily_client_class.return_value = mock_client
        
        tool = WebSearchTool(api_key="test-key")
        
        # Test max_results > 10
        tool.execute(query="test", max_results=20)
        mock_client.search.assert_called_with(
            query="test",
            max_results=10,
            search_depth="basic"
        )
        
        # Test max_results < 1
        tool.execute(query="test", max_results=0)
        mock_client.search.assert_called_with(
            query="test",
            max_results=1,
            search_depth="basic"
        )
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_execute_handles_empty_results(self, mock_tavily_client_class):
        """
        Test execution with empty search results.
        
        Rationale: Ensures tool handles empty results gracefully.
        """
        mock_client = Mock()
        mock_client.search.return_value = {"results": []}
        mock_tavily_client_class.return_value = mock_client
        
        tool = WebSearchTool(api_key="test-key")
        result = tool.execute(query="test")
        
        assert result["count"] == 0
        assert result["results"] == []
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_execute_handles_missing_fields(self, mock_tavily_client_class):
        """
        Test execution with results missing some fields.
        
        Rationale: Ensures tool handles incomplete API responses gracefully.
        """
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [
                {"title": "Result 1"},  # Missing url and content
                {"url": "https://example.com"}  # Missing title and content
            ]
        }
        mock_tavily_client_class.return_value = mock_client
        
        tool = WebSearchTool(api_key="test-key")
        result = tool.execute(query="test")
        
        assert result["count"] == 2
        assert result["results"][0].get("title") == "Result 1"
        assert result["results"][0].get("url") == ""
        assert result["results"][1].get("url") == "https://example.com"
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_execute_handles_api_error(self, mock_tavily_client_class):
        """
        Test execution when API raises an error.
        
        Rationale: Ensures tool handles API errors gracefully.
        """
        mock_client = Mock()
        mock_client.search.side_effect = Exception("API Error")
        mock_tavily_client_class.return_value = mock_client
        
        tool = WebSearchTool(api_key="test-key")
        result = tool.execute(query="test")
        
        assert "error" in result
        assert result["count"] == 0
        assert result["results"] == []
        assert result["error"] == "API Error"


class TestWebSearchToolFormatResult:
    """Test WebSearchTool result formatting."""
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_format_result_with_results(self, mock_tavily_client_class):
        """
        Test formatting results with search results.
        
        Rationale: Ensures results are formatted in readable format for LLM.
        """
        mock_tavily_client_class.return_value = Mock()
        tool = WebSearchTool(api_key="test-key")
        
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
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_format_result_empty(self, mock_tavily_client_class):
        """
        Test formatting empty results.
        
        Rationale: Ensures empty results are handled gracefully.
        """
        mock_tavily_client_class.return_value = Mock()
        tool = WebSearchTool(api_key="test-key")
        
        result = {
            "query": "test query",
            "count": 0,
            "results": []
        }
        
        formatted = tool.format_result(result)
        
        assert "No results found" in formatted
        assert "test query" in formatted
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_format_result_with_error(self, mock_tavily_client_class):
        """
        Test formatting results with error.
        
        Rationale: Ensures errors are formatted clearly for LLM.
        """
        mock_tavily_client_class.return_value = Mock()
        tool = WebSearchTool(api_key="test-key")
        
        result = {
            "query": "test query",
            "count": 0,
            "results": [],
            "error": "API Error"
        }
        
        formatted = tool.format_result(result)
        
        assert "Error" in formatted
        assert "API Error" in formatted
    
    @patch('broca.tools.web_search.TavilyClient')
    def test_format_result_truncates_long_content(self, mock_tavily_client_class):
        """
        Test that long content is truncated in formatted output.
        
        Rationale: Ensures formatted output is manageable in size.
        """
        mock_tavily_client_class.return_value = Mock()
        tool = WebSearchTool(api_key="test-key")
        
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

