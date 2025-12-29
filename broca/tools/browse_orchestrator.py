"""
Browse Orchestrator - High-level agent-facing layer for web browsing.

Provides search, navigation, extraction, and citation capabilities
while enforcing budgets, safety, and provenance tracking.
"""

from __future__ import annotations

import json
import logging
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

from .browser_kernel import BrowserKernel, SessionConfig
from .browse_trace import BrowseTraceManager, BrowseTrace, BrowseBudget
from .citation_builder import CitationBuilder
from .browse_safety import BrowseSafety
from ..config import config

logger = logging.getLogger(__name__)


class BrowseOrchestrator:
    """
    High-level browse orchestrator.
    
    Provides agent-facing APIs for web browsing while managing
    sessions, budgets, traces, citations, and safety.
    """
    
    def __init__(
        self,
        browser_kernel: Optional[BrowserKernel] = None,
        trace_manager: Optional[BrowseTraceManager] = None,
        citation_builder: Optional[CitationBuilder] = None,
        safety: Optional[BrowseSafety] = None
    ) -> None:
        """
        Initialize browse orchestrator.
        
        Args:
            browser_kernel: Browser kernel instance (creates new if None)
            trace_manager: Trace manager instance (creates new if None)
            citation_builder: Citation builder instance (creates new if None)
            safety: Safety checker instance (creates new if None)
        """
        self._kernel = browser_kernel or BrowserKernel()
        self._trace_manager = trace_manager or BrowseTraceManager()
        self._safety = safety or BrowseSafety()
        
        # Load domain reputation for citation builder
        self._domain_reputation = self._load_domain_reputation()
        self._citation_builder = citation_builder or CitationBuilder(self._domain_reputation)
        
        # Active task traces: task_id -> BrowseTrace
        self._active_traces: Dict[str, BrowseTrace] = {}
        
        # Task sessions: task_id -> session_id
        self._task_sessions: Dict[str, str] = {}
        
        logger.info("Initialized BrowseOrchestrator")
    
    def _load_domain_reputation(self) -> Dict[str, Any]:
        """Load domain reputation data."""
        try:
            rep_file = Path(config.browse.domain_reputation_file)
            if rep_file.exists():
                with open(rep_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load domain reputation: {e}")
        
        return {}
    
    def _get_or_create_session(self, task_id: str) -> str:
        """Get or create browser session for a task."""
        if task_id not in self._task_sessions:
            session_config = SessionConfig(
                viewport_width=config.tools.browser_viewport_width,
                viewport_height=config.tools.browser_viewport_height,
                headless=config.tools.browser_headless,
                stealth_mode=config.tools.browser_stealth_mode
            )
            session_id = self._kernel.new_session(session_config)
            self._task_sessions[task_id] = session_id
            logger.debug(f"Created session {session_id} for task {task_id}")
        
        return self._task_sessions[task_id]
    
    def _get_or_create_trace(self, task_id: str, session_id: str) -> BrowseTrace:
        """Get or create browse trace for a task."""
        if task_id not in self._active_traces:
            trace = self._trace_manager.create_trace(session_id, task_id)
            self._active_traces[task_id] = trace
            logger.debug(f"Created trace for task {task_id}")
        
        return self._active_traces[task_id]
    
    def _check_budget(self, trace: BrowseTrace) -> bool:
        """Check if budget is exhausted."""
        if trace.budget_exhausted:
            return False
        
        # Check wallclock time
        if trace.completed_at:
            started = datetime.fromisoformat(trace.started_at.replace("Z", "+00:00"))
            completed = datetime.fromisoformat(trace.completed_at.replace("Z", "+00:00"))
            elapsed_ms = (completed - started).total_seconds() * 1000
            
            if elapsed_ms >= trace.budget.max_wallclock_ms:
                trace.budget_exhausted = True
                logger.warning(f"Budget exhausted: max_wallclock_ms reached")
                return False
        
        return True
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        engine: str = "auto",
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            engine: Search engine ("auto", "ddg", "bing", "google")
            task_id: Task identifier (for trace tracking)
            
        Returns:
            Dictionary with search results
        """
        if task_id is None:
            task_id = f"search_{hashlib.md5(query.encode()).hexdigest()[:8]}"
        
        session_id = self._get_or_create_session(task_id)
        trace = self._get_or_create_trace(task_id, session_id)
        
        # Check budget
        if not self._check_budget(trace):
            return {
                "results": [],
                "query": query,
                "count": 0,
                "error": "Budget exhausted",
                "trace_id": task_id
            }
        
        # Determine engine
        if engine == "auto":
            engine = config.browse.default_search_engine
        
        # Perform search
        try:
            search_results = self._kernel.search(
                session_id=session_id,
                engine=engine,
                query=query,
                count=max_results
            )
            
            # Add to trace
            self._trace_manager.add_action(
                trace,
                action_type="search",
                result={"query": query, "engine": engine, "count": len(search_results)}
            )
            
            # Format results (compatible with WebSearchTool format)
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("snippet", ""),
                    "score": 1.0 - (result.get("rank", 1) - 1) * 0.1  # Simple scoring
                })
            
            return {
                "results": formatted_results,
                "query": query,
                "count": len(formatted_results),
                "trace_id": task_id
            }
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            self._trace_manager.add_error(trace, {"type": "search", "error": str(e)})
            
            return {
                "results": [],
                "query": query,
                "count": 0,
                "error": str(e),
                "trace_id": task_id
            }
    
    def open_top_k(
        self,
        urls: List[str],
        max_actions: int = 10,
        task_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Open and extract content from top K URLs.
        
        Args:
            urls: List of URLs to open
            max_actions: Maximum number of actions to perform
            task_id: Task identifier
            
        Returns:
            List of extraction results
        """
        if task_id is None:
            task_id = f"open_top_k_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        session_id = self._get_or_create_session(task_id)
        trace = self._get_or_create_trace(task_id, session_id)
        
        results = []
        
        for url in urls[:max_actions]:
            if not self._check_budget(trace):
                break
            
            try:
                # Navigate
                nav_result = self._kernel.goto(session_id, url)
                
                if not nav_result.get("success"):
                    continue
                
                # Extract
                extract_result = self.extract_article(url, task_id=task_id)
                
                # Add to trace
                self._trace_manager.add_visited_url(
                    trace,
                    url=url,
                    status_code=nav_result.get("status", 200),
                    content_hash=extract_result.get("content_hash")
                )
                
                results.append(extract_result)
            except Exception as e:
                logger.error(f"Error opening {url}: {e}")
                self._trace_manager.add_error(trace, {"type": "open_url", "url": url, "error": str(e)})
        
        return results
    
    def extract_article(
        self,
        url: str,
        mode: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract article content from a URL.
        
        Args:
            url: URL to extract from
            mode: Extraction mode (defaults to config preference)
            task_id: Task identifier
            
        Returns:
            Dictionary with extracted content
        """
        if task_id is None:
            task_id = f"extract_{hashlib.md5(url.encode()).hexdigest()[:8]}"
        
        session_id = self._get_or_create_session(task_id)
        trace = self._get_or_create_trace(task_id, session_id)
        
        # Navigate first
        nav_result = self._kernel.goto(session_id, url)
        if not nav_result.get("success"):
            return {
                "success": False,
                "error": nav_result.get("error", "Navigation failed"),
                "url": url
            }
        
        # Try extraction modes in order
        if mode is None:
            modes = config.browse.extraction_mode_preference
        else:
            modes = [mode]
        
        extraction_result = None
        extraction_method = None
        
        for extraction_mode in modes:
            try:
                result = self._kernel.get_text(
                    session_id,
                    mode=extraction_mode,
                    max_chars=config.browse.max_extracted_chars
                )
                
                if result.get("success") and result.get("text"):
                    extraction_result = result
                    extraction_method = result.get("extraction_method", extraction_mode)
                    break
            except Exception as e:
                logger.debug(f"Extraction mode {extraction_mode} failed: {e}")
                continue
        
        if not extraction_result or not extraction_result.get("text"):
            return {
                "success": False,
                "error": "All extraction methods failed",
                "url": url,
                "modes_attempted": modes
            }
        
        text = extraction_result["text"]
        content_hash = self._trace_manager.compute_content_hash(text)
        
        # Add to trace
        self._trace_manager.add_action(
            trace,
            action_type="extract",
            url=url,
            result={
                "extraction_method": extraction_method,
                "length": len(text),
                "content_hash": content_hash
            }
        )
        
        self._trace_manager.add_visited_url(
            trace,
            url=url,
            status_code=nav_result.get("status", 200),
            content_hash=content_hash
        )
        
        return {
            "success": True,
            "url": url,
            "text": text,
            "extraction_method": extraction_method,
            "content_hash": content_hash,
            "length": len(text)
        }
    
    def validate_sources(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate source quality of search results.
        
        Args:
            results: List of search result dictionaries
            
        Returns:
            Dictionary with validation results
        """
        validated = []
        rejected = []
        
        for result in results:
            url = result.get("url", "")
            # Extract domain
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc
            except Exception:
                domain = ""
            
            # Compute reliability using same logic as citation builder
            reliability = self._compute_reliability_score(domain)
            
            result["reliability_score"] = reliability
            result["domain"] = domain
            
            # Filter by reliability threshold (configurable, default 0.3)
            if reliability >= 0.3:
                validated.append(result)
            else:
                rejected.append(result)
        
        return {
            "validated": validated,
            "rejected": rejected,
            "total": len(results),
            "validated_count": len(validated)
        }
    
    def build_citations(
        self,
        claims: List[Dict[str, Any]],
        task_id: str
    ) -> List[Dict[str, Any]]:
        """
        Build citations for claims from a browse trace.
        
        Args:
            claims: List of claim dictionaries
            task_id: Task identifier
            
        Returns:
            List of citation dictionaries
        """
        if task_id not in self._active_traces:
            return []
        
        trace = self._active_traces[task_id]
        citations = self._citation_builder.build_citations(claims, trace)
        
        return [citation.to_dict() for citation in citations]
    
    def complete_task(self, task_id: str) -> str:
        """
        Complete a task and save its trace.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path to saved trace file
        """
        if task_id not in self._active_traces:
            logger.warning(f"Task {task_id} not found in active traces")
            return ""
        
        trace = self._active_traces[task_id]
        self._trace_manager.complete_trace(trace)
        
        # Clean up session if needed (optional - could keep for reuse)
        # session_id = self._task_sessions.get(task_id)
        # if session_id:
        #     self._kernel.close_session(session_id)
        
        trace_path = self._trace_manager.save_trace(trace)
        del self._active_traces[task_id]
        
        logger.info(f"Completed task {task_id}, trace saved to {trace_path}")
        return trace_path
    
    def _compute_reliability_score(self, domain: str) -> float:
        """Compute reliability score for a domain."""
        if not self._domain_reputation:
            return 0.5
        
        allowlist = self._domain_reputation.get("allowlist", {})
        denylist = self._domain_reputation.get("denylist", {})
        default_score = self._domain_reputation.get("default_score", 0)
        
        # Check allowlist
        for category, data in allowlist.items():
            domains = data.get("domains", [])
            score = data.get("score", 0)
            
            for pattern in domains:
                if self._domain_matches(pattern, domain):
                    return min(score / 10.0, 1.0)
        
        # Check denylist
        for category, data in denylist.items():
            domains = data.get("domains", [])
            score = data.get("score", 0)
            
            for pattern in domains:
                if self._domain_matches(pattern, domain):
                    return max(score / 10.0, 0.0)
        
        # Default score
        return max(min(default_score / 10.0, 1.0), 0.0)
    
    def _domain_matches(self, pattern: str, domain: str) -> bool:
        """Check if domain matches a pattern."""
        if pattern == domain:
            return True
        
        if pattern.startswith("*."):
            suffix = pattern[2:]
            return domain.endswith("." + suffix) or domain == suffix
        
        return False

