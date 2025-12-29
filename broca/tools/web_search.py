"""
Web search tool implementation.

Uses Tavily API as primary search provider with browser-based search (ddgs) as fallback.
Provides comprehensive web search capabilities including page download and content extraction.
"""

from __future__ import annotations

import os
import re
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None  # type: ignore

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

try:
    import trafilatura
except ImportError:
    trafilatura = None  # type: ignore

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

from . import Tool
from ..config import config

logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Web search tool using Tavily API as primary provider.
    
    Primary search method: Tavily API (requires TAVILY_API_KEY)
    Fallback: Browser-based search (DuckDuckGo via BrowseOrchestrator)
    
    Allows the LLM to search the web with comprehensive filtering options,
    download pages for full content processing, and extract text from HTML.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        browse_orchestrator: Optional[Any] = None
    ) -> None:
        """
        Initialize the web search tool.
        
        Tavily is the primary search method. Browser-based search is used
        as fallback when Tavily fails or is unavailable.
        
        Args:
            api_key: Tavily API key (required for primary search)
            browse_orchestrator: BrowseOrchestrator instance (creates if None, for fallback)
            
        Raises:
            ValueError: If Tavily API key is missing (browser fallback can still work)
        """
        self._api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self._tavily_client = None
        self._browse_orchestrator = browse_orchestrator
        
        # Initialize Tavily client (primary method)
        if TavilyClient and self._api_key:
            try:
                self._tavily_client = TavilyClient(api_key=self._api_key)
                logger.info("Initialized Tavily client (primary search provider)")
            except Exception as e:
                logger.warning(f"Failed to initialize Tavily client: {e}")
        elif not self._api_key:
            logger.warning(
                "TAVILY_API_KEY not provided. Tavily search will not be available. "
                "Browser-based search will be used as fallback."
            )
        
        # Initialize browse orchestrator (fallback method)
        try:
            if self._browse_orchestrator is None:
                from .browse_orchestrator import BrowseOrchestrator
                self._browse_orchestrator = BrowseOrchestrator()
                logger.debug("Initialized Browse Orchestrator (fallback)")
        except Exception as e:
            logger.warning(f"Failed to initialize Browse Orchestrator (fallback): {e}")
            self._browse_orchestrator = None
        
        # At least one search method should be available
        if not self._tavily_client and not self._browse_orchestrator:
            logger.warning(
                "Neither Tavily nor browser search is available. "
                "Web search functionality will be limited."
            )
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "web_search"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM with comprehensive usage guide."""
        return (
            "Search the web for current information, facts, news, and data using Tavily API.\n\n"
            "PRIMARY PROVIDER:\n"
            "- Tavily API: Advanced search with comprehensive filtering options, AI-generated answers, "
            "and rich content extraction. Requires TAVILY_API_KEY environment variable.\n\n"
            "FALLBACK PROVIDER:\n"
            "- Browser-based search (DuckDuckGo): Used automatically if Tavily is unavailable.\n\n"
            "SEARCH PARAMETERS:\n"
            "- query (required): The search query string\n"
            "- max_results: Number of results (1-50, default: 5)\n"
            "- search_depth: 'basic' (faster) or 'advanced' (more comprehensive, default: 'basic')\n"
            "- include_domains: List of domains to restrict search (e.g., ['example.com'])\n"
            "- exclude_domains: List of domains to exclude from results\n"
            "- include_answer: Include AI-generated answer in results (boolean, default: false)\n"
            "- include_raw_content: Include raw HTML content (boolean, default: false)\n"
            "- include_images: Include image URLs in results (boolean, default: false)\n"
            "- topic: Restrict search to specific topic category (optional)\n"
            "- days: Restrict to results from last N days (integer, optional)\n\n"
            "PAGE DOWNLOAD:\n"
            "- auto_download_top_n: Automatically download top N results (0 = disabled, default: 0)\n"
            "- download_urls: Explicit list of URLs to download and process\n"
            "- Downloaded pages are saved to /tmp with processed content included in response\n"
            "- Use downloads to get full page content when snippets are insufficient\n\n"
            "USAGE EXAMPLES:\n"
            "# Basic search\n"
            '  {"query": "python async programming best practices", "max_results": 5}\n\n'
            '# Search with domain restriction\n'
            '  {"query": "python documentation", "include_domains": ["python.org"], "max_results": 10}\n\n'
            '# Search with advanced depth and answer\n'
            '  {"query": "how does quantum computing work", "search_depth": "advanced", "include_answer": true}\n\n'
            '# Search recent news\n'
            '  {"query": "latest AI safety news", "days": 7, "max_results": 10}\n\n'
            '# Search with automatic page downloads\n'
            '  {"query": "react hooks tutorial", "max_results": 5, "auto_download_top_n": 3}\n\n'
            '# Search with explicit URL downloads\n'
            '  {"query": "machine learning basics", "max_results": 5, "download_urls": ["https://example.com/ml-guide"]}\n\n'
            "QUERY BEST PRACTICES:\n"
            "- Be specific and descriptive with search terms\n"
            "- Include relevant keywords and context\n"
            "- Use natural language (not boolean operators)\n"
            "- For recent information, use 'days' parameter or include time context\n"
            "- For technical topics, include technology names and versions\n"
            "- Use domain filters to focus on trusted sources\n\n"
            "RESULT FORMAT:\n"
            "- Each result includes: title, URL, content snippet, score, and metadata\n"
            "- Results are sorted by relevance\n"
            "- Downloaded files include file path, processed content, and content length\n"
            "- Provider used (tavily or browser_fallback) is indicated in response\n\n"
            "ERROR HANDLING:\n"
            "- If Tavily fails, browser-based search is automatically used as fallback\n"
            "- Check TAVILY_API_KEY is set for optimal performance\n"
            "- Some sites may block automated access (normal for web scraping)\n"
            "- Empty results may indicate query needs refinement"
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
                        "Default: 5. Maximum: 50. "
                        "Use fewer results (3-5) for focused queries, "
                        "more results (10-50) for comprehensive research."
                    ),
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": (
                        "Search depth: 'basic' for faster results (default), "
                        "'advanced' for more comprehensive search with deeper analysis."
                    ),
                    "default": "basic"
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Restrict search to specific domains. "
                        "Example: ['python.org', 'github.com'] to only search these domains."
                    )
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Exclude specific domains from search results. "
                        "Example: ['spam.com'] to exclude this domain."
                    )
                },
                "include_answer": {
                    "type": "boolean",
                    "description": (
                        "Include AI-generated answer in results. "
                        "Useful for getting a synthesized answer to your query."
                    ),
                    "default": False
                },
                "include_raw_content": {
                    "type": "boolean",
                    "description": (
                        "Include raw HTML content in results. "
                        "Useful for extracting full page content but increases response size."
                    ),
                    "default": False
                },
                "include_images": {
                    "type": "boolean",
                    "description": (
                        "Include image URLs in search results. "
                        "Useful when searching for visual content."
                    ),
                    "default": False
                },
                "topic": {
                    "type": "string",
                    "description": (
                        "Restrict search to specific topic category. "
                        "Use to focus on particular domains of knowledge."
                    )
                },
                "days": {
                    "type": "integer",
                    "description": (
                        "Restrict search results to content from the last N days. "
                        "Useful for finding recent news or updates. "
                        "Example: 7 for last week, 30 for last month."
                    ),
                    "minimum": 1
                },
                "auto_download_top_n": {
                    "type": "integer",
                    "description": (
                        "Automatically download and process the top N search results. "
                        "0 = disabled (default). Downloaded pages are saved to /tmp "
                        "and processed content is included in the response."
                    ),
                    "default": 0,
                    "minimum": 0
                },
                "download_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Explicit list of URLs to download and process. "
                        "Downloaded pages are saved to /tmp and processed content "
                        "is included in the response. Use this to get full content "
                        "from specific pages found in search results."
                    )
                }
            },
            "required": ["query"]
        }
    
    def execute(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        topic: Optional[str] = None,
        days: Optional[int] = None,
        auto_download_top_n: int = 0,
        download_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a web search using Tavily API (primary) or browser-based search (fallback).
        
        Args:
            query: Search query string
            max_results: Maximum number of results (1-50, default: 5)
            search_depth: "basic" or "advanced" (default: "basic")
            include_domains: List of domains to restrict search
            exclude_domains: List of domains to exclude
            include_answer: Include AI-generated answer
            include_raw_content: Include raw HTML content
            include_images: Include image URLs
            topic: Topic category to restrict search
            days: Restrict to results from last N days
            auto_download_top_n: Automatically download top N results (0 = disabled)
            download_urls: Explicit list of URLs to download
            
        Returns:
            Dictionary containing:
                - "results": List of search results
                - "query": Original search query
                - "count": Number of results
                - "provider_used": "tavily" | "browser_fallback"
                - "downloaded_files": List of downloaded file info (if any)
                - "error": Error message (if search failed)
        """
        try:
            # Clamp max_results to valid range
            max_results = max(1, min(50, max_results))
            
            logger.debug(
                f"Executing web search: query='{query}', max_results={max_results}, "
                f"search_depth={search_depth}, provider=tavily"
            )
            
            # Try Tavily first (primary method)
            if self._tavily_client:
                try:
                    result = self._execute_tavily_search(
                        query=query,
                        max_results=max_results,
                        search_depth=search_depth,
                        include_domains=include_domains,
                        exclude_domains=exclude_domains,
                        include_answer=include_answer,
                        include_raw_content=include_raw_content,
                        include_images=include_images,
                        topic=topic,
                        days=days
                    )
                    result["provider_used"] = "tavily"
                    
                    # Handle downloads
                    downloaded_files = []
                    
                    # Auto-download top N results
                    if auto_download_top_n > 0 and result.get("results"):
                        urls_to_download = [
                            r["url"] for r in result["results"][:auto_download_top_n]
                            if r.get("url")
                        ]
                        downloaded_files.extend(self._download_pages(urls_to_download))
                    
                    # Download explicit URLs
                    if download_urls:
                        downloaded_files.extend(self._download_pages(download_urls))
                    
                    if downloaded_files:
                        result["downloaded_files"] = downloaded_files
                    
                    return result
                    
                except Exception as e:
                    logger.warning(f"Tavily search failed: {e}, falling back to browser search")
                    # Fall through to browser fallback
            
            # Fallback to browser-based search
            if not self._browse_orchestrator:
                return {
                    "results": [],
                    "query": query,
                    "count": 0,
                    "provider_used": "none",
                    "error": (
                        "Neither Tavily nor browser search is available. "
                        "Set TAVILY_API_KEY for primary search, or ensure "
                        "browser navigation is enabled for fallback."
                    )
                }
            
            try:
                # Browser search doesn't support all Tavily parameters, use basic search
                logger.info("Using browser-based search (fallback)")
                result = self._browse_orchestrator.search(
                    query=query,
                    max_results=max_results,
                    engine=config.browse.default_search_engine
                )
                result["provider_used"] = "browser_fallback"
                
                # Handle downloads for browser fallback too
                downloaded_files = []
                
                if auto_download_top_n > 0 and result.get("results"):
                    urls_to_download = [
                        r["url"] for r in result["results"][:auto_download_top_n]
                        if r.get("url")
                    ]
                    downloaded_files.extend(self._download_pages(urls_to_download))
                
                if download_urls:
                    downloaded_files.extend(self._download_pages(download_urls))
                
                if downloaded_files:
                    result["downloaded_files"] = downloaded_files
                
                return result
                
            except Exception as e:
                logger.error(f"Browser search also failed: {e}", exc_info=True)
                return {
                    "results": [],
                    "query": query,
                    "count": 0,
                    "provider_used": "none",
                    "error": f"Both Tavily and browser search failed. Last error: {str(e)}"
                }
            
        except Exception as e:
            logger.error(f"Error executing web search: {e}", exc_info=True)
            return {
                "results": [],
                "query": query,
                "count": 0,
                "provider_used": "none",
                "error": str(e)
            }
    
    def _execute_tavily_search(
        self,
        query: str,
        max_results: int,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        topic: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute search using Tavily API with all parameters."""
        if not self._tavily_client:
            raise ValueError("Tavily client not available")
        
        try:
            # Build search parameters
            search_params: Dict[str, Any] = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth
            }
            
            # Add optional parameters
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            if include_answer:
                search_params["include_answer"] = True
            if include_raw_content:
                search_params["include_raw_content"] = True
            if include_images:
                search_params["include_images"] = True
            if topic:
                search_params["topic"] = topic
            if days:
                search_params["days"] = days
            
            response = self._tavily_client.search(**search_params)
            
            results: List[Dict[str, Any]] = []
            
            # Extract answer if present
            answer = response.get("answer", "")
            
            # Process results
            for item in response.get("results", []):
                result_item: Dict[str, Any] = {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0)
                }
                
                # Add raw content if requested
                if include_raw_content and "raw_content" in item:
                    result_item["raw_content"] = item.get("raw_content")
                
                # Add images if requested
                if include_images and "images" in item:
                    result_item["images"] = item.get("images", [])
                
                results.append(result_item)
            
            result_dict: Dict[str, Any] = {
                "results": results,
                "query": query,
                "count": len(results)
            }
            
            # Include answer if present
            if answer:
                result_dict["answer"] = answer
            
            logger.debug(f"Tavily search returned {len(results)} results")
            return result_dict
            
        except Exception as e:
            logger.error(f"Tavily search error: {e}", exc_info=True)
            raise
    
    def _download_pages(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Download and process web pages.
        
        Args:
            urls: List of URLs to download
            
        Returns:
            List of dictionaries with download information
        """
        if not httpx:
            logger.warning("httpx not available, cannot download pages")
            return []
        
        downloaded_files = []
        
        for url in urls:
            try:
                download_info = self._download_page(url)
                if download_info:
                    downloaded_files.append(download_info)
            except Exception as e:
                logger.warning(f"Failed to download {url}: {e}")
                downloaded_files.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        return downloaded_files
    
    def _download_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Download a single web page and extract its content.
        
        Args:
            url: URL to download
            
        Returns:
            Dictionary with download information or None if failed
        """
        if not httpx:
            return None
        
        try:
            # Download the page
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                html_content = response.text
                content_type = response.headers.get("content-type", "")
            
            # Sanitize filename
            filename = self._sanitize_filename(url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"web_search_{filename}_{timestamp}.html"
            file_path = Path("/tmp") / safe_filename
            
            # Save HTML file
            file_path.write_text(html_content, encoding="utf-8")
            
            # Extract text content
            extracted_text = self._extract_text_from_html(html_content, url)
            
            # Build result
            result = {
                "url": url,
                "file_path": str(file_path),
                "success": True,
                "content_length": len(html_content),
                "extracted_text_length": len(extracted_text),
                "content_preview": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
            }
            
            # Include full extracted text if not too large (limit to 100KB)
            if len(extracted_text) <= 100000:
                result["extracted_text"] = extracted_text
            
            logger.debug(f"Downloaded and processed {url} -> {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error downloading page {url}: {e}")
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    def _sanitize_filename(self, url: str) -> str:
        """
        Create a safe filename from URL.
        
        Args:
            url: URL to convert to filename
            
        Returns:
            Sanitized filename string
        """
        try:
            parsed = urlparse(url)
            # Use domain + path, remove query/fragment
            domain = parsed.netloc.replace("www.", "").replace(".", "_")
            path = parsed.path.strip("/").replace("/", "_")[:50]  # Limit path length
            
            # Combine and sanitize
            base_name = f"{domain}_{path}" if path else domain
            
            # Remove unsafe characters
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)
            safe_name = safe_name[:100]  # Limit total length
            
            # If empty, use hash
            if not safe_name:
                safe_name = hashlib.md5(url.encode()).hexdigest()[:16]
            
            return safe_name
        except Exception:
            # Fallback to hash
            return hashlib.md5(url.encode()).hexdigest()[:16]
    
    def _extract_text_from_html(self, html_content: str, url: str) -> str:
        """
        Extract text content from HTML using available extractors.
        
        Args:
            html_content: HTML content to extract from
            url: URL (for context/logging)
            
        Returns:
            Extracted text content
        """
        # Try trafilatura first (best for articles)
        if trafilatura:
            try:
                extracted = trafilatura.extract(html_content, url=url)
                if extracted and len(extracted.strip()) > 100:
                    logger.debug(f"Extracted text using trafilatura for {url}")
                    return extracted.strip()
            except Exception as e:
                logger.debug(f"Trafilatura extraction failed for {url}: {e}")
        
        # Fallback to BeautifulSoup
        if BeautifulSoup:
            try:
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = " ".join(chunk for chunk in chunks if chunk)
                
                if text and len(text.strip()) > 100:
                    logger.debug(f"Extracted text using BeautifulSoup for {url}")
                    return text.strip()
            except Exception as e:
                logger.debug(f"BeautifulSoup extraction failed for {url}: {e}")
        
        # Last resort: return empty string
        logger.warning(f"Could not extract text content from {url}")
        return ""
    
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
        provider = result.get("provider_used", "unknown")
        
        lines = [f"Web search results for '{query}' ({len(results)} results, provider: {provider}):\n"]
        
        # Include answer if present
        if "answer" in result:
            lines.append(f"AI-Generated Answer:\n{result['answer']}\n")
        
        # Format results
        for i, item in enumerate(results, 1):
            title = item.get("title", "No title")
            url = item.get("url", "")
            content = item.get("content", "")
            
            lines.append(f"{i}. {title}")
            if url:
                lines.append(f"   URL: {url}")
            if content:
                content_preview = content[:300] + "..." if len(content) > 300 else content
                lines.append(f"   {content_preview}")
            lines.append("")
        
        # Include downloaded files info
        if "downloaded_files" in result:
            downloaded = result["downloaded_files"]
            lines.append(f"\nDownloaded {len(downloaded)} page(s):\n")
            for file_info in downloaded:
                if file_info.get("success"):
                    lines.append(f"- {file_info['url']}")
                    lines.append(f"  Saved to: {file_info['file_path']}")
                    lines.append(f"  Content length: {file_info.get('extracted_text_length', 0)} chars")
                    if "content_preview" in file_info:
                        preview = file_info["content_preview"]
                        lines.append(f"  Preview: {preview[:200]}...")
                else:
                    lines.append(f"- {file_info['url']} (failed: {file_info.get('error', 'unknown error')})")
                lines.append("")
        
        return "\n".join(lines)
