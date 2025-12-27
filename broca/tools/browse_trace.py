"""
Browse Trace Artifact Management.

Handles creation, storage, and replay of browse trace artifacts for
provenance and auditability.
"""

from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field

from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class BrowseBudget:
    """Budget configuration for a browse task."""
    max_actions: int = 20
    max_wallclock_ms: int = 60000
    max_domains: int = 5
    max_total_bytes: int = 10_000_000


@dataclass
class BrowseAction:
    """A single action in a browse trace."""
    type: str  # "search" | "navigate" | "click" | "extract" | ...
    timestamp: str
    url: Optional[str] = None
    selector: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class VisitedURL:
    """Information about a visited URL."""
    url: str
    timestamp: str
    redirect_chain: List[str] = field(default_factory=list)
    status_code: int = 200
    content_hash: Optional[str] = None  # SHA256 of extracted text
    screenshot_path: Optional[str] = None


@dataclass
class BrowseTrace:
    """Complete browse trace artifact."""
    session_id: str
    task_id: str
    started_at: str
    completed_at: Optional[str] = None
    budget: BrowseBudget = field(default_factory=BrowseBudget)
    actions: List[BrowseAction] = field(default_factory=list)
    visited_urls: List[VisitedURL] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    budget_exhausted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "budget": asdict(self.budget),
            "actions": [asdict(action) for action in self.actions],
            "visited_urls": [asdict(url) for url in self.visited_urls],
            "errors": self.errors,
            "budget_exhausted": self.budget_exhausted
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BrowseTrace:
        """Create from dictionary."""
        budget = BrowseBudget(**data.get("budget", {}))
        actions = [BrowseAction(**action) for action in data.get("actions", [])]
        visited_urls = [VisitedURL(**url) for url in data.get("visited_urls", [])]
        
        return cls(
            session_id=data["session_id"],
            task_id=data["task_id"],
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            budget=budget,
            actions=actions,
            visited_urls=visited_urls,
            errors=data.get("errors", []),
            budget_exhausted=data.get("budget_exhausted", False)
        )


class BrowseTraceManager:
    """Manages browse trace artifacts."""
    
    def __init__(self, storage_path: Optional[str] = None) -> None:
        """
        Initialize trace manager.
        
        Args:
            storage_path: Path to store traces (defaults to config)
        """
        self._storage_path = Path(
            storage_path or config.browse.trace_storage_path
        )
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized BrowseTraceManager with storage at {self._storage_path}")
    
    def create_trace(
        self,
        session_id: str,
        task_id: str,
        budget: Optional[BrowseBudget] = None
    ) -> BrowseTrace:
        """
        Create a new browse trace.
        
        Args:
            session_id: Browser session ID
            task_id: Task identifier
            budget: Budget configuration (defaults to config)
            
        Returns:
            BrowseTrace instance
        """
        if budget is None:
            budget = BrowseBudget(
                max_actions=config.browse.default_max_actions,
                max_wallclock_ms=config.browse.default_max_wallclock_ms,
                max_domains=config.browse.default_max_domains,
                max_total_bytes=config.browse.default_max_total_bytes
            )
        
        trace = BrowseTrace(
            session_id=session_id,
            task_id=task_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            budget=budget
        )
        
        logger.debug(f"Created browse trace for task {task_id}")
        return trace
    
    def add_action(
        self,
        trace: BrowseTrace,
        action_type: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Add an action to a trace.
        
        Args:
            trace: Browse trace
            action_type: Type of action
            url: URL (if applicable)
            selector: Selector (if applicable)
            result: Action result
            error: Error message (if applicable)
        """
        action = BrowseAction(
            type=action_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            url=url,
            selector=selector,
            result=result or {},
            error=error
        )
        
        trace.actions.append(action)
        
        # Check budget
        if len(trace.actions) >= trace.budget.max_actions:
            trace.budget_exhausted = True
            logger.warning(f"Budget exhausted: max_actions reached for task {trace.task_id}")
    
    def add_visited_url(
        self,
        trace: BrowseTrace,
        url: str,
        redirect_chain: Optional[List[str]] = None,
        status_code: int = 200,
        content_hash: Optional[str] = None,
        screenshot_path: Optional[str] = None
    ) -> None:
        """
        Add a visited URL to a trace.
        
        Args:
            trace: Browse trace
            url: Final URL
            redirect_chain: Chain of redirects
            status_code: HTTP status code
            content_hash: SHA256 hash of extracted content
            screenshot_path: Path to screenshot (if taken)
        """
        visited = VisitedURL(
            url=url,
            timestamp=datetime.now(timezone.utc).isoformat(),
            redirect_chain=redirect_chain or [],
            status_code=status_code,
            content_hash=content_hash,
            screenshot_path=screenshot_path
        )
        
        trace.visited_urls.append(visited)
        
        # Check domain budget
        unique_domains = len(set(
            self._extract_domain(u["url"]) for u in trace.visited_urls
        ))
        if unique_domains >= trace.budget.max_domains:
            trace.budget_exhausted = True
            logger.warning(f"Budget exhausted: max_domains reached for task {trace.task_id}")
    
    def add_error(self, trace: BrowseTrace, error: Dict[str, Any]) -> None:
        """
        Add an error to a trace.
        
        Args:
            trace: Browse trace
            error: Error dictionary
        """
        error["timestamp"] = datetime.now(timezone.utc).isoformat()
        trace.errors.append(error)
    
    def complete_trace(self, trace: BrowseTrace) -> None:
        """
        Mark a trace as completed and save it.
        
        Args:
            trace: Browse trace to complete
        """
        trace.completed_at = datetime.now(timezone.utc).isoformat()
        self.save_trace(trace)
    
    def save_trace(self, trace: BrowseTrace) -> str:
        """
        Save a trace to disk.
        
        Args:
            trace: Browse trace to save
            
        Returns:
            Path to saved trace file
        """
        # Generate filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{trace.task_id}_{timestamp}.json"
        filepath = self._storage_path / filename
        
        # Save trace
        with open(filepath, "w") as f:
            json.dump(trace.to_dict(), f, indent=2)
        
        logger.debug(f"Saved browse trace to {filepath}")
        return str(filepath)
    
    def load_trace(self, filepath: str) -> BrowseTrace:
        """
        Load a trace from disk.
        
        Args:
            filepath: Path to trace file
            
        Returns:
            BrowseTrace instance
        """
        with open(filepath, "r") as f:
            data = json.load(f)
        
        return BrowseTrace.from_dict(data)
    
    def find_traces(
        self,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[str]:
        """
        Find trace files matching criteria.
        
        Args:
            task_id: Task ID to filter by
            session_id: Session ID to filter by
            
        Returns:
            List of trace file paths
        """
        traces = []
        
        for filepath in self._storage_path.glob("*.json"):
            try:
                trace = self.load_trace(str(filepath))
                
                if task_id and trace.task_id != task_id:
                    continue
                if session_id and trace.session_id != session_id:
                    continue
                
                traces.append(str(filepath))
            except Exception as e:
                logger.debug(f"Error loading trace {filepath}: {e}")
                continue
        
        return sorted(traces, reverse=True)  # Most recent first
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""
    
    def compute_content_hash(self, text: str) -> str:
        """
        Compute SHA256 hash of content.
        
        Args:
            text: Text content
            
        Returns:
            SHA256 hex digest
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

