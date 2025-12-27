"""
Web search tool implementation.

Uses browser-based search (via Browse Orchestrator) with Tavily API fallback.
Provides web search capabilities to the LLM.
"""

from __future__ import annotations

import os
import logging
from typing import Dict, Any, List, Optional

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None  # type: ignore

from . import Tool
from ..config import config

logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Web search tool using browser-based search engines.
    
    Primary search method: Browser-based search (DuckDuckGo, Bing, Google)
    Emergency fallback: Tavily API (only if explicitly enabled)
    
    Allows the LLM to search the web for current information, facts, and data.
    Results are formatted for easy consumption by the LLM with citations and provenance.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        browse_orchestrator: Optional[Any] = None
    ) -> None:
        """
        Initialize the web search tool.
        
        Browser-based search is the primary method. Tavily is only used as
        emergency fallback if explicitly enabled via configuration.
        
        Args:
            api_key: Tavily API key (optional, only for emergency fallback)
            browse_orchestrator: BrowseOrchestrator instance (creates if None)
            
        Raises:
            ValueError: If browser search is not available
        """
        self._api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self._tavily_client = None
        self._browse_orchestrator = browse_orchestrator
        
        # Initialize browse orchestrator (primary method)
        try:
            if self._browse_orchestrator is None:
                from .browse_orchestrator import BrowseOrchestrator
                self._browse_orchestrator = BrowseOrchestrator()
                logger.debug("Initialized Browse Orchestrator")
        except Exception as e:
            logger.error(f"Failed to initialize Browse Orchestrator: {e}", exc_info=True)
            self._browse_orchestrator = None
        
        # Initialize Tavily client only if explicitly enabled as fallback
        if config.browse.enable_tavily_fallback and TavilyClient and self._api_key:
            try:
                self._tavily_client = TavilyClient(api_key=self._api_key)
                logger.debug("Initialized Tavily client (emergency fallback)")
            except Exception as e:
                logger.warning(f"Failed to initialize Tavily client: {e}")
        
        # Browser search is required
        if not self._browse_orchestrator:
            raise ValueError(
                "Browser-based search is required but not available. "
                "Ensure browser navigation is enabled and Playwright is installed: "
                "pip install playwright && playwright install chromium"
            )
        
        logger.info("Initialized WebSearchTool (browser-based search primary)")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "web_search"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM with comprehensive usage guide."""
        return (
            "Search the web for current information, facts, news, and data using browser-based search engines.\n\n"
            "SEARCH ENGINES:\n"
            "- DuckDuckGo (default): No API key needed, privacy-focused, excellent for general queries\n"
            "- Bing: Good for recent news and Microsoft ecosystem content\n"
            "- Google: Comprehensive results, respects rate limits\n\n"
            "USAGE:\n"
            '  {"query": "python async programming best practices", "max_results": 5}\n'
            '  {"query": "latest news about AI safety 2024", "max_results": 10}\n'
            '  {"query": "python asyncio documentation", "max_results": 3}\n\n'
            "QUERY BEST PRACTICES:\n"
            "- Be specific and descriptive with your search terms\n"
            "- Include relevant keywords and context\n"
            "- Use natural language (not boolean operators)\n"
            "- For recent information, include time context (e.g., '2024', 'latest', 'recent')\n"
            "- For technical topics, include technology names and versions\n\n"
            "RESULT INTERPRETATION:\n"
            "- Each result includes: title, URL, content snippet, and reliability score\n"
            "- Results are sorted by relevance and source quality\n"
            "- URLs are verified and accessible\n"
            "- Content snippets are extracted from actual pages\n"
            "- Domain reliability scores (0.0-1.0) help assess source quality\n\n"
            "CITATIONS AND PROVENANCE:\n"
            "- All results include trace information for auditability\n"
            "- Content hashes ensure verifiability\n"
            "- Timestamps indicate when information was accessed\n"
            "- Results can be traced back to browse trace artifacts\n\n"
            "ERROR HANDLING:\n"
            "- If search fails, verify browser navigation is enabled\n"
            "- Check Playwright installation: pip install playwright && playwright install chromium\n"
            "- Verify network connectivity\n"
            "- Some sites may block automated access (this is normal and expected)\n"
            "- Empty results may indicate the query needs refinement\n\n"
            "EXAMPLES:\n"
            "# General information search\n"
            '  {"query": "how does quantum computing work", "max_results": 5}\n\n'
            "# Recent news search\n"
            '  {"query": "breaking news technology December 2024", "max_results": 10}\n\n'
            "# Technical documentation\n"
            '  {"query": "python asyncio documentation examples", "max_results": 3}\n\n'
            "# Scientific/academic topics\n"
            '  {"query": "machine learning transformer architecture paper", "max_results": 5}'
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters with detailed descriptions."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search query to find information on the web. "
                        "Use natural language with specific keywords. "
                        "Examples: 'python async programming', 'latest AI news 2024', "
                        "'quantum computing applications'"
                    )
                },
                "max_results": {
                    "type": "integer",
                    "description": (
                        "Maximum number of results to return. "
                        "Default: 5. Maximum: 10. "
                        "Use fewer results (3-5) for focused queries, "
                        "more results (8-10) for broad topics or news searches."
                    ),
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    
    def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute a web search using browser-based search engines.
        
        Primary method: Browser-based search (DuckDuckGo, Bing, or Google)
        Fallback: Tavily API (only if explicitly enabled in config)
        
        Args:
            query: Search query string (use natural language with specific keywords)
            max_results: Maximum number of results to return (default: 5, max: 10)
            
        Returns:
            Dictionary containing:
                - "results": List of search results with title, URL, content, score
                - "query": Original search query
                - "count": Number of results returned
                - "trace_id": Task ID for browse trace (if available)
                - "error": Error message (if search failed)
        """
        try:
            # Clamp max_results to valid range
            max_results = max(1, min(10, max_results))
            
            logger.debug(f"Executing web search: query='{query}', max_results={max_results}")
            
            # Browser-based search is primary (unless Tavily-only emergency mode)
            if config.browse.tavily_fallback_only:
                # Emergency mode: Use Tavily only
                if self._tavily_client:
                    logger.info("Using Tavily (emergency fallback mode)")
                    return self._execute_tavily_search(query, max_results)
                else:
                    return {
                        "results": [],
                        "query": query,
                        "count": 0,
                        "error": "Tavily fallback mode enabled but Tavily client not available"
                    }
            
            # Primary: Browser-based search
            if not self._browse_orchestrator:
                return {
                    "results": [],
                    "query": query,
                    "count": 0,
                    "error": "Browser search not available. Install Playwright: pip install playwright && playwright install chromium"
                }
            
            try:
                result = self._browse_orchestrator.search(
                    query=query,
                    max_results=max_results,
                    engine=config.browse.default_search_engine
                )
                
                # Return browser search results (even if empty - may be valid)
                logger.debug(f"Browser search returned {result.get('count', 0)} results")
                return result
                
            except Exception as e:
                logger.error(f"Browser search failed: {e}", exc_info=True)
                
                # Try Tavily fallback only if explicitly enabled
                if config.browse.enable_tavily_fallback and self._tavily_client:
                    logger.warning("Browser search failed, trying Tavily emergency fallback")
                    return self._execute_tavily_search(query, max_results)
                
                # Return error if no fallback
                return {
                    "results": [],
                    "query": query,
                    "count": 0,
                    "error": f"Browser search failed: {str(e)}. "
                            f"Install Playwright: pip install playwright && playwright install chromium"
                }
            
        except Exception as e:
            logger.error(f"Error executing web search: {e}", exc_info=True)
            return {
                "results": [],
                "query": query,
                "count": 0,
                "error": str(e)
            }
    
    def _execute_tavily_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Execute search using Tavily API."""
        if not self._tavily_client:
            return {
                "results": [],
                "query": query,
                "count": 0,
                "error": "Tavily client not available"
            }
        
        try:
            response = self._tavily_client.search(
                query=query,
                max_results=max_results,
                search_depth="basic"
            )
            
            results: List[Dict[str, Any]] = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0)
                })
            
            logger.debug(f"Tavily search returned {len(results)} results")
            return {
                "results": results,
                "query": query,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Tavily search error: {e}", exc_info=True)
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

