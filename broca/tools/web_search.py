"""
Web search tool implementation using Tavily API.

Provides web search capabilities to the LLM using the tavily-python client.
"""

from __future__ import annotations

import os
import logging
from typing import Dict, Any, List

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None  # type: ignore

from . import Tool

logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Web search tool using Tavily API.
    
    Allows the LLM to search the web for current information, facts, and data.
    Results are formatted for easy consumption by the LLM.
    """
    
    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the web search tool.
        
        Args:
            api_key: Tavily API key (defaults to TAVILY_API_KEY env var)
            
        Raises:
            ValueError: If tavily-python is not installed or API key is missing
        """
        if TavilyClient is None:
            raise ValueError(
                "tavily-python package is not installed. "
                "Install it with: pip install tavily-python"
            )
        
        self._api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "Tavily API key is required. "
                "Set TAVILY_API_KEY environment variable or pass api_key parameter."
            )
        
        self._client = TavilyClient(api_key=self._api_key)
        logger.info("Initialized WebSearchTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "web_search"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Search the web for current information, facts, news, and data. "
            "Use this tool when you need to find up-to-date information, verify facts, "
            "or search for specific topics on the internet. The tool returns relevant "
            "search results with titles, URLs, and content snippets."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find information on the web"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5, max: 10)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    
    def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute a web search.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5, max: 10)
            
        Returns:
            Dictionary containing:
                - "results": List of search results
                - "query": Original search query
                - "count": Number of results returned
        """
        try:
            # Clamp max_results to valid range
            max_results = max(1, min(10, max_results))
            
            logger.debug(f"Executing web search: query='{query}', max_results={max_results}")
            
            # Perform search using Tavily
            response = self._client.search(
                query=query,
                max_results=max_results,
                search_depth="basic"  # Can be "basic" or "advanced"
            )
            
            # Extract results
            results: List[Dict[str, Any]] = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0)
                })
            
            result = {
                "results": results,
                "query": query,
                "count": len(results)
            }
            
            logger.debug(f"Web search returned {len(results)} results")
            return result
            
        except Exception as e:
            logger.error(f"Error executing web search: {e}", exc_info=True)
            # Return error information in structured format
            return {
                "results": [],
                "query": query,
                "count": 0,
                "error": str(e)
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format search results for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation of search results
        """
        if result.get("error"):
            return f"Error searching the web: {result['error']}"
        
        results = result.get("results", [])
        query = result.get("query", "unknown query")
        
        if not results:
            return f"No results found for query: '{query}'"
        
        # Format results as readable text
        lines = [f"Web search results for '{query}' ({len(results)} results):\n"]
        
        for i, item in enumerate(results, 1):
            title = item.get("title", "No title")
            url = item.get("url", "")
            content = item.get("content", "")
            
            lines.append(f"{i}. {title}")
            if url:
                lines.append(f"   URL: {url}")
            if content:
                # Truncate content if too long
                content_preview = content[:300] + "..." if len(content) > 300 else content
                lines.append(f"   {content_preview}")
            lines.append("")  # Empty line between results
        
        return "\n".join(lines)

