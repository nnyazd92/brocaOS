"""
Browser Kernel - Low-level Playwright wrapper with session management.

Provides persistent browser sessions, navigation primitives, extraction,
and search capabilities. This is the foundation layer that
Browse Orchestrator builds upon.
"""

from __future__ import annotations

import os
import json
import logging
import random
import time
import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, TypedDict
from pathlib import Path
from dataclasses import dataclass, asdict

try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None  # type: ignore
    Browser = None  # type: ignore
    BrowserContext = None  # type: ignore
    Page = None  # type: ignore
    PlaywrightTimeoutError = None  # type: ignore
    PLAYWRIGHT_AVAILABLE = False

from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    """Configuration for a browser session."""
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    locale: str = "en-US"
    timezone: Optional[str] = None
    proxy: Optional[str] = None
    headless: bool = True
    stealth_mode: bool = True


class BrowserKernel:
    """
    Low-level browser kernel with session management.
    
    Provides persistent browser sessions, navigation primitives,
    extraction capabilities, and search functionality.
    """
    
    def __init__(self, session_storage_path: Optional[str] = None) -> None:
        """
        Initialize the browser kernel.
        
        Args:
            session_storage_path: Path to store session data (defaults to config)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ValueError(
                "playwright package is not installed. "
                "Install it with: pip install playwright && playwright install chromium"
            )
        
        self._session_storage_path = Path(
            session_storage_path or config.browse.session_storage_path
        )
        self._session_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Session registry (SQLite)
        self._registry_path = self._session_storage_path / "sessions.db"
        self._init_registry()
        
        # Active sessions: session_id -> (playwright, browser, context, page, config)
        self._active_sessions: Dict[str, tuple] = {}
        
        # Playwright instance (shared)
        self._playwright = None
        
        logger.info(f"Initialized BrowserKernel with storage at {self._session_storage_path}")
    
    def _init_registry(self) -> None:
        """Initialize session registry database."""
        conn = sqlite3.connect(self._registry_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                config_json TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()
    
    def _get_playwright(self):
        """Get or create shared playwright instance."""
        if self._playwright is None:
            self._playwright = sync_playwright().start()
        return self._playwright
    
    def new_session(self, session_config: Optional[SessionConfig] = None) -> str:
        """
        Create a new browser session.
        
        Args:
            session_config: Session configuration (defaults to config-based)
            
        Returns:
            Session ID string
        """
        if session_config is None:
            session_config = SessionConfig(
                viewport_width=config.tools.browser_viewport_width,
                viewport_height=config.tools.browser_viewport_height,
                headless=config.tools.browser_headless,
                stealth_mode=config.tools.browser_stealth_mode
            )
        
        # Generate session ID
        session_id = hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}{random.random()}".encode()
        ).hexdigest()[:16]
        
        # Create session directory
        session_dir = self._session_storage_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Launch browser and create page
        playwright = self._get_playwright()
        launch_args = []
        
        if session_config.stealth_mode:
            launch_args.extend([
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ])
        
        browser = playwright.chromium.launch(
            headless=session_config.headless,
            args=launch_args
        )
        
        # Calculate viewport size
        if session_config.stealth_mode:
            width = session_config.viewport_width + random.randint(-50, 50)
            height = session_config.viewport_height + random.randint(-50, 50)
        else:
            width = session_config.viewport_width
            height = session_config.viewport_height
        
        # Create context with user_agent, viewport, and headers
        context_options = {
            "viewport": {"width": width, "height": height}
        }
        
        # Set user agent
        if session_config.user_agent:
            context_options["user_agent"] = session_config.user_agent
        elif session_config.stealth_mode and config.tools.browser_user_agents:
            user_agent = random.choice(config.tools.browser_user_agents)
            context_options["user_agent"] = user_agent
        
        # Set extra HTTP headers for stealth mode
        if session_config.stealth_mode:
            context_options["extra_http_headers"] = {
                "Accept-Language": session_config.locale,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        
        context = browser.new_context(**context_options)
        page = context.new_page()
        
        # Set default timeout
        page.set_default_timeout(config.tools.browser_timeout * 1000)
        
        # Store active session
        self._active_sessions[session_id] = (playwright, browser, context, page, session_config)
        
        # Register in database
        conn = sqlite3.connect(self._registry_path)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO sessions (session_id, created_at, last_accessed, config_json, is_active) VALUES (?, ?, ?, ?, ?)",
            (session_id, now, now, json.dumps(asdict(session_config)), 1)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Created new browser session: {session_id}")
        return session_id
    
    def close_session(self, session_id: str) -> None:
        """
        Close a browser session and clean up resources.
        
        Args:
            session_id: Session ID to close
        """
        if session_id not in self._active_sessions:
            logger.warning(f"Session {session_id} not found in active sessions")
            return
        
        playwright, browser, context, page, _ = self._active_sessions[session_id]
        
        try:
            # Save cookies and localStorage before closing
            self._save_session_state(session_id, page)
            
            page.close()
            context.close()
            browser.close()
        except Exception as e:
            logger.debug(f"Error closing session {session_id}: {e}")
        
        del self._active_sessions[session_id]
        
        # Update registry
        conn = sqlite3.connect(self._registry_path)
        conn.execute(
            "UPDATE sessions SET is_active = 0 WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Closed browser session: {session_id}")
    
    def list_sessions(self) -> List[str]:
        """
        List all active sessions.
        
        Returns:
            List of session IDs
        """
        return list(self._active_sessions.keys())
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with session information
        """
        if session_id not in self._active_sessions:
            return {"error": "Session not found"}
        
        _, _, _, page, session_config = self._active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "url": page.url,
            "title": page.title(),
            "config": asdict(session_config)
        }
    
    def _get_page(self, session_id: str) -> Page:
        """Get page for a session."""
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        _, _, _, page, _ = self._active_sessions[session_id]
        return page
    
    def _save_session_state(self, session_id: str, page: Page) -> None:
        """Save cookies and localStorage for a session."""
        session_dir = self._session_storage_path / session_id
        
        try:
            # Save cookies
            cookies = page.context.cookies()
            with open(session_dir / "cookies.json", "w") as f:
                json.dump(cookies, f, indent=2)
            
            # Save localStorage (via JS)
            try:
                local_storage = page.evaluate("() => JSON.stringify(localStorage)")
                with open(session_dir / "local_storage.json", "w") as f:
                    f.write(local_storage)
            except Exception as e:
                logger.debug(f"Could not save localStorage: {e}")
        except Exception as e:
            logger.debug(f"Error saving session state: {e}")
    
    def _load_session_state(self, session_id: str, page: Page) -> None:
        """Load cookies and localStorage for a session."""
        session_dir = self._session_storage_path / session_id
        
        try:
            # Load cookies
            cookies_path = session_dir / "cookies.json"
            if cookies_path.exists():
                with open(cookies_path, "r") as f:
                    cookies = json.load(f)
                    page.context.add_cookies(cookies)
        except Exception as e:
            logger.debug(f"Error loading session state: {e}")
    
    def _human_delay(self, stealth_mode: bool) -> None:
        """Add human-like delay if stealth mode is enabled."""
        if stealth_mode:
            delay = random.uniform(0.1, 0.5)
            time.sleep(delay)
    
    # Navigation & Interaction Primitives
    
    def goto(
        self,
        session_id: str,
        url: str,
        wait_until: str = "networkidle",
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            session_id: Session ID
            url: URL to navigate to
            wait_until: Wait condition ("networkidle", "load", "domcontentloaded")
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Dictionary with navigation result
        """
        try:
            page = self._get_page(session_id)
            _, _, _, _, session_config = self._active_sessions[session_id]
            
            response = page.goto(url, timeout=timeout_ms, wait_until=wait_until)
            self._human_delay(session_config.stealth_mode)
            
            return {
                "success": True,
                "url": url,
                "url_final": page.url,
                "status": response.status if response else None,
                "title": page.title()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def click(
        self,
        session_id: str,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """
        Click an element.
        
        Args:
            session_id: Session ID
            selector: CSS selector
            text: Text to click (alternative to selector)
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Dictionary with click result
        """
        try:
            page = self._get_page(session_id)
            _, _, _, session_config = self._active_sessions[session_id]
            
            if selector:
                page.click(selector, timeout=timeout_ms)
            elif text:
                page.click(f"text={text}", timeout=timeout_ms)
            else:
                return {"success": False, "error": "Either selector or text required"}
            
            self._human_delay(session_config.stealth_mode)
            
            return {
                "success": True,
                "selector": selector,
                "text": text,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "selector": selector,
                "text": text
            }
    
    def type(
        self,
        session_id: str,
        selector: str,
        text: str,
        clear: bool = True,
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """
        Type text into an element.
        
        Args:
            session_id: Session ID
            selector: CSS selector
            text: Text to type
            clear: Clear field before typing
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Dictionary with type result
        """
        try:
            page = self._get_page(session_id)
            _, _, _, session_config = self._active_sessions[session_id]
            
            if clear:
                page.fill(selector, text, timeout=timeout_ms)
            else:
                page.type(selector, text, timeout=timeout_ms)
            
            self._human_delay(session_config.stealth_mode)
            
            return {
                "success": True,
                "selector": selector,
                "text": text,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "selector": selector
            }
    
    def scroll(
        self,
        session_id: str,
        delta_y: Optional[int] = None,
        to: Optional[str] = None,
        steps: int = 10
    ) -> Dict[str, Any]:
        """
        Scroll the page.
        
        Args:
            session_id: Session ID
            delta_y: Pixels to scroll (positive = down, negative = up)
            to: Scroll to position ("top" or "bottom")
            steps: Number of scroll steps (for smooth scrolling)
            
        Returns:
            Dictionary with scroll result
        """
        try:
            page = self._get_page(session_id)
            
            if to == "top":
                page.evaluate("window.scrollTo(0, 0)")
            elif to == "bottom":
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            elif delta_y is not None:
                for _ in range(steps):
                    page.evaluate(f"window.scrollBy(0, {delta_y // steps})")
                    time.sleep(0.01)
            
            return {
                "success": True,
                "delta_y": delta_y,
                "to": to,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def wait_for(
        self,
        session_id: str,
        condition: str,
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """
        Wait for a condition.
        
        Args:
            session_id: Session ID
            condition: Condition to wait for (selector, "networkidle", "load", "domcontentloaded", or milliseconds)
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Dictionary with wait result
        """
        try:
            page = self._get_page(session_id)
            
            if condition == "networkidle":
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            elif condition == "load":
                page.wait_for_load_state("load", timeout=timeout_ms)
            elif condition == "domcontentloaded":
                page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            elif condition.startswith("selector:"):
                selector = condition.split(":", 1)[1]
                page.wait_for_selector(selector, timeout=timeout_ms)
            elif condition.startswith("text:"):
                text = condition.split(":", 1)[1]
                page.wait_for_selector(f"text={text}", timeout=timeout_ms)
            elif condition.isdigit():
                # Milliseconds
                time.sleep(int(condition) / 1000.0)
            else:
                # Assume it's a selector
                page.wait_for_selector(condition, timeout=timeout_ms)
            
            return {
                "success": True,
                "condition": condition,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "condition": condition
            }
    
    def execute_js(self, session_id: str, script: str) -> Dict[str, Any]:
        """
        Execute JavaScript in the page context.
        
        Args:
            session_id: Session ID
            script: JavaScript code to execute
            
        Returns:
            Dictionary with execution result
        """
        try:
            page = self._get_page(session_id)
            result = page.evaluate(script)
            
            return {
                "success": True,
                "result": result,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # Extraction & Capture
    
    def get_html(self, session_id: str) -> Dict[str, Any]:
        """
        Get HTML content of the current page.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with HTML, URL, and timestamp
        """
        try:
            page = self._get_page(session_id)
            html = page.content()
            
            return {
                "success": True,
                "html": html,
                "url": page.url,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_text(
        self,
        session_id: str,
        mode: str = "readability",
        max_chars: int = 50000
    ) -> Dict[str, Any]:
        """
        Extract text from the current page.
        
        Args:
            session_id: Session ID
            mode: Extraction mode ("readability", "trafilatura", "dom", "raw")
            max_chars: Maximum characters to extract
            
        Returns:
            Dictionary with extracted text
        """
        try:
            page = self._get_page(session_id)
            html = page.content()
            
            text = ""
            extraction_method = ""
            
            if mode == "readability":
                try:
                    from readability.readability import Document
                    doc = Document(html)
                    text = doc.summary()
                    extraction_method = "readability"
                except ImportError:
                    logger.warning("readability-lxml not available, falling back to trafilatura")
                    mode = "trafilatura"
                except Exception as e:
                    logger.debug(f"Readability extraction failed: {e}, trying trafilatura")
                    mode = "trafilatura"
            
            if mode == "trafilatura" and not text:
                try:
                    import trafilatura
                    text = trafilatura.extract(html)
                    extraction_method = "trafilatura"
                except ImportError:
                    logger.warning("trafilatura not available, falling back to DOM")
                    mode = "dom"
                except Exception as e:
                    logger.debug(f"Trafilatura extraction failed: {e}, trying DOM")
                    mode = "dom"
            
            if mode == "dom" and not text:
                # DOM extraction with boilerplate removal
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "lxml")
                    
                    # Remove script, style, nav, header, footer
                    for tag in soup(["script", "style", "nav", "header", "footer"]):
                        tag.decompose()
                    
                    # Try to find main content areas
                    main = soup.find("main") or soup.find("article") or soup.find("body")
                    if main:
                        text = main.get_text(separator="\n", strip=True)
                    else:
                        text = soup.get_text(separator="\n", strip=True)
                    
                    extraction_method = "dom"
                except ImportError:
                    logger.warning("beautifulsoup4 not available, using raw extraction")
                    mode = "raw"
                except Exception as e:
                    logger.debug(f"DOM extraction failed: {e}, using raw")
                    mode = "raw"
            
            if mode == "raw" and not text:
                # Raw HTML text extraction
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "html.parser")
                    text = soup.get_text(separator="\n", strip=True)
                    extraction_method = "raw"
                except ImportError:
                    # Last resort: use Playwright's inner_text
                    text = page.inner_text("body")
                    extraction_method = "playwright_inner_text"
            
            # Truncate if needed
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            return {
                "success": True,
                "text": text,
                "extraction_method": extraction_method,
                "url": page.url,
                "length": len(text)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mode": mode
            }
    
    def query(
        self,
        session_id: str,
        selector: str,
        attr: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query elements using a selector.
        
        Args:
            session_id: Session ID
            selector: CSS selector
            attr: Attribute to extract (None = inner_text)
            limit: Maximum number of elements to return
            
        Returns:
            List of dictionaries with element data
        """
        try:
            page = self._get_page(session_id)
            elements = page.query_selector_all(selector)[:limit]
            
            results = []
            for element in elements:
                if attr:
                    value = element.get_attribute(attr)
                else:
                    value = element.inner_text()
                
                results.append({
                    "selector": selector,
                    "attr": attr,
                    "value": value
                })
            
            return results
        except Exception as e:
            logger.error(f"Error querying elements: {e}")
            return []
    
    def screenshot(
        self,
        session_id: str,
        full_page: bool = True,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Take a screenshot.
        
        Args:
            session_id: Session ID
            full_page: Take full page screenshot
            path: Path to save screenshot (optional)
            
        Returns:
            Dictionary with screenshot result
        """
        try:
            page = self._get_page(session_id)
            
            if not path:
                # Generate path
                session_dir = self._session_storage_path / session_id
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                path = str(session_dir / f"screenshot_{timestamp}.png")
            
            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            page.screenshot(path=path, full_page=full_page)
            
            return {
                "success": True,
                "path": path,
                "full_page": full_page,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    def download(self, session_id: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a file.
        
        Args:
            session_id: Session ID
            url: URL to download (None = current page)
            
        Returns:
            Dictionary with download result
        """
        # This is a placeholder - Playwright download handling is async
        # For now, return error suggesting manual download
        return {
            "success": False,
            "error": "Download functionality not yet implemented. Use goto() to navigate to download URL."
        }
    
    def extract_pdf(self, file_ref: str) -> Dict[str, str]:
        """
        Extract text from a PDF file.
        
        Args:
            file_ref: Path to PDF file
            
        Returns:
            Dictionary with text and metadata
        """
        try:
            import PyPDF2
            
            with open(file_ref, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text_parts = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text_parts.append(page.extract_text())
                
                text = "\n".join(text_parts)
                
                return {
                    "text": text,
                    "metadata": {
                        "num_pages": len(pdf_reader.pages),
                        "title": pdf_reader.metadata.get("/Title", "") if pdf_reader.metadata else ""
                    }
                }
        except ImportError:
            return {
                "error": "PyPDF2 not installed. Install with: pip install PyPDF2"
            }
        except Exception as e:
            return {
                "error": str(e)
            }
    
    # Search Primitive
    
    def search(
        self,
        session_id: str,
        engine: str,
        query: str,
        recency_days: Optional[int] = None,
        site_filter: Optional[str] = None,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform a web search using browser automation.
        
        Args:
            session_id: Session ID
            engine: Search engine ("ddg", "bing", "google")
            query: Search query
            recency_days: Filter by recency (days)
            site_filter: Filter by site (e.g., "example.com")
            count: Number of results to return
            
        Returns:
            List of search result dictionaries
        """
        try:
            if engine == "ddg":
                # Use library as primary method (more reliable, avoids bot detection)
                # Fallback to Playwright if library not available
                library_results = self._search_duckduckgo_with_library(query, count)
                if library_results:
                    return library_results
                # If library not available or failed, try Playwright scraping
                logger.debug("[DDG] Library method unavailable or returned no results, trying Playwright")
                page = self._get_page(session_id)
                return self._search_duckduckgo(page, query, count)
            elif engine == "bing":
                page = self._get_page(session_id)
                return self._search_bing(page, query, count)
            elif engine == "google":
                page = self._get_page(session_id)
                return self._search_google(page, query, count)
            else:
                return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _search_duckduckgo_with_library(self, query: str, count: int) -> List[Dict[str, Any]]:
        """
        Primary method for DuckDuckGo search using duckduckgo_search library.
        
        This is more reliable than Playwright scraping because it uses DuckDuckGo's
        internal APIs and avoids bot detection. Playwright is used as fallback only
        if this library is not available.
        """
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=count))
                # Convert to our format
                formatted = []
                for r in results:
                    from urllib.parse import urlparse
                    parsed = urlparse(r.get("href", ""))
                    formatted.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                        "rank": len(formatted) + 1,
                        "displayed_domain": parsed.netloc,
                        "timestamp": None
                    })
                logger.info(f"[DDG] Library method returned {len(formatted)} results")
                return formatted
        except ImportError:
            logger.debug("[DDG] duckduckgo_search library not available")
            return []
        except Exception as e:
            logger.warning(f"[DDG] duckduckgo_search library error: {e}")
            return []
    
    def _search_duckduckgo(self, page: Page, query: str, count: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo with fallback selectors."""
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            logger.debug(f"[DDG] Navigating to {search_url}")
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            logger.debug(f"[DDG] Navigation complete. Title: {page.title()}, URL: {page.url}")
            
            # Try multiple selectors in order
            selectors = [
                ".result",
                "[data-result]",
                ".web-result",
                "article[data-testid='result']",
                ".result-link",
                "div.result",
                "li.result",
                "a.result__a",  # Sometimes results are links themselves
            ]
            
            result_elements = []
            used_selector = None
            title_selector = None
            snippet_selector = None
            
            # Try to find result container
            for selector in selectors:
                try:
                    logger.debug(f"[DDG] Trying selector: {selector}")
                    page.wait_for_selector(selector, timeout=5000)
                    result_elements = page.query_selector_all(selector)[:count]
                    if result_elements:
                        logger.info(f"[DDG] Found {len(result_elements)} result elements with selector: {selector}")
                        used_selector = selector
                        break
                except PlaywrightTimeoutError:
                    logger.debug(f"[DDG] Selector {selector} not found, trying next")
                    continue
            
            if not result_elements:
                page_title = ""
                page_url = ""
                try:
                    page_title = page.title()
                    page_url = page.url
                except Exception:
                    pass
                logger.error(f"[DDG] All selectors failed. Page title: {page_title}, URL: {page_url}")
                # Return empty - library method should have been tried first
                return []
            
            # Extract results
            results = []
            for idx, element in enumerate(result_elements, 1):
                try:
                    # Try multiple title/snippet selector combinations
                    title = None
                    url = None
                    snippet = None
                    
                    # Try common title selectors
                    title_selectors = [".result__a", "a.result__a", "h2 a", "a", ".result-title", "h2"]
                    for ts in title_selectors:
                        title_elem = element.query_selector(ts)
                        if title_elem:
                            title = title_elem.inner_text()
                            url = title_elem.get_attribute("href") or element.get_attribute("href") or ""
                            break
                    
                    # Try common snippet selectors
                    snippet_selectors = [".result__snippet", ".result-snippet", ".snippet", "p"]
                    for ss in snippet_selectors:
                        snippet_elem = element.query_selector(ss)
                        if snippet_elem:
                            snippet = snippet_elem.inner_text()
                            break
                    
                    # If we have at least a title or URL, include the result
                    if title or url:
                        # Extract domain from URL
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc
                        
                        results.append({
                            "title": title or "",
                            "url": url or "",
                            "snippet": snippet or "",
                            "rank": idx,
                            "displayed_domain": domain,
                            "timestamp": None
                        })
                    else:
                        logger.debug(f"[DDG] Skipping result {idx}: no title or URL found")
                except Exception as e:
                    logger.warning(f"[DDG] Failed to extract result {idx}: {e}")
                    continue
            
            logger.info(f"[DDG] Search completed: {len(results)} results extracted using selector: {used_selector}")
            return results
            
        except Exception as e:
            logger.error(f"[DDG] Playwright search error: {e}", exc_info=True)
            # Return empty - library method should have been tried first
            return []
    
    def _search_bing(self, page: Page, query: str, count: int) -> List[Dict[str, Any]]:
        """Search using Bing with fallback selectors."""
        try:
            search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
            logger.debug(f"[Bing] Navigating to {search_url}")
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            logger.debug(f"[Bing] Navigation complete. Title: {page.title()}, URL: {page.url}")
            
            # Try multiple selectors in order
            selectors = [
                ".b_algo",
                "li.b_algo",
                "[data-bm]",
                ".b_title h2 a",
                "ol#b_results > li",
                ".b_algoheader",
            ]
            
            result_elements = []
            used_selector = None
            
            # Try to find result container
            for selector in selectors:
                try:
                    logger.debug(f"[Bing] Trying selector: {selector}")
                    page.wait_for_selector(selector, timeout=5000)
                    result_elements = page.query_selector_all(selector)[:count]
                    if result_elements:
                        logger.info(f"[Bing] Found {len(result_elements)} result elements with selector: {selector}")
                        used_selector = selector
                        break
                except PlaywrightTimeoutError:
                    logger.debug(f"[Bing] Selector {selector} not found, trying next")
                    continue
            
            if not result_elements:
                logger.error(f"[Bing] All selectors failed. Page title: {page.title()}, URL: {page.url}")
                return []
            
            # Extract results
            results = []
            for idx, element in enumerate(result_elements, 1):
                try:
                    # Try multiple title/snippet selector combinations
                    title = None
                    url = None
                    snippet = None
                    
                    # Try common title selectors
                    title_selectors = ["h2 a", "h2 > a", ".b_title a", "a.b_title", "a"]
                    for ts in title_selectors:
                        title_elem = element.query_selector(ts)
                        if title_elem:
                            title = title_elem.inner_text()
                            url = title_elem.get_attribute("href") or ""
                            break
                    
                    # Try common snippet selectors
                    snippet_selectors = [".b_caption p", ".b_caption", "p", ".b_snippet", ".b_lineClamp2"]
                    for ss in snippet_selectors:
                        snippet_elem = element.query_selector(ss)
                        if snippet_elem:
                            snippet = snippet_elem.inner_text()
                            break
                    
                    # If we have at least a title or URL, include the result
                    if title or url:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc
                        
                        results.append({
                            "title": title or "",
                            "url": url or "",
                            "snippet": snippet or "",
                            "rank": idx,
                            "displayed_domain": domain,
                            "timestamp": None
                        })
                    else:
                        logger.debug(f"[Bing] Skipping result {idx}: no title or URL found")
                except Exception as e:
                    logger.warning(f"[Bing] Failed to extract result {idx}: {e}")
                    continue
            
            logger.info(f"[Bing] Search completed: {len(results)} results extracted using selector: {used_selector}")
            return results
            
        except Exception as e:
            logger.error(f"[Bing] Search error: {e}", exc_info=True)
            return []
    
    def _search_google(self, page: Page, query: str, count: int) -> List[Dict[str, Any]]:
        """Search using Google with fallback selectors."""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            logger.debug(f"[Google] Navigating to {search_url}")
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            logger.debug(f"[Google] Navigation complete. Title: {page.title()}, URL: {page.url}")
            
            # Try multiple selectors in order
            selectors = [
                ".g",
                "div.g",
                "[data-ved]",
                ".tF2Cxc",
                ".yuRUbf",
                "div[data-hveid]",
            ]
            
            result_elements = []
            used_selector = None
            
            # Try to find result container
            for selector in selectors:
                try:
                    logger.debug(f"[Google] Trying selector: {selector}")
                    page.wait_for_selector(selector, timeout=5000)
                    result_elements = page.query_selector_all(selector)[:count]
                    if result_elements:
                        logger.info(f"[Google] Found {len(result_elements)} result elements with selector: {selector}")
                        used_selector = selector
                        break
                except PlaywrightTimeoutError:
                    logger.debug(f"[Google] Selector {selector} not found, trying next")
                    continue
            
            if not result_elements:
                logger.error(f"[Google] All selectors failed. Page title: {page.title()}, URL: {page.url}")
                return []
            
            # Extract results
            results = []
            for idx, element in enumerate(result_elements, 1):
                try:
                    # Try multiple title/snippet selector combinations
                    title = None
                    url = None
                    snippet = None
                    
                    # Try common title selectors
                    title_selectors = ["h3", "h3 span", ".LC20lb", "a h3", ".DKV0Md"]
                    for ts in title_selectors:
                        title_elem = element.query_selector(ts)
                        if title_elem:
                            title = title_elem.inner_text()
                            break
                    
                    # Try common link selectors
                    link_selectors = ["a", "a[href]", ".yuRUbf a", ".g a"]
                    for ls in link_selectors:
                        link_elem = element.query_selector(ls)
                        if link_elem:
                            url = link_elem.get_attribute("href") or ""
                            if url and not url.startswith("/search"):
                                break
                    
                    # Try common snippet selectors
                    snippet_selectors = [".VwiC3b", ".s", ".st", ".IsZvec", ".MUxGbd"]
                    for ss in snippet_selectors:
                        snippet_elem = element.query_selector(ss)
                        if snippet_elem:
                            snippet = snippet_elem.inner_text()
                            break
                    
                    # If we have at least a title or URL, include the result
                    if title or url:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc
                        
                        results.append({
                            "title": title or "",
                            "url": url or "",
                            "snippet": snippet or "",
                            "rank": idx,
                            "displayed_domain": domain,
                            "timestamp": None
                        })
                    else:
                        logger.debug(f"[Google] Skipping result {idx}: no title or URL found")
                except Exception as e:
                    logger.warning(f"[Google] Failed to extract result {idx}: {e}")
                    continue
            
            logger.info(f"[Google] Search completed: {len(results)} results extracted using selector: {used_selector}")
            return results
            
        except Exception as e:
            logger.error(f"[Google] Search error: {e}", exc_info=True)
            return []
    
    def cleanup_stale_sessions(self) -> None:
        """Clean up stale sessions (>24h inactive)."""
        conn = sqlite3.connect(self._registry_path)
        cutoff = datetime.now(timezone.utc).timestamp() - (config.browse.session_ttl_hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
        
        cursor = conn.execute(
            "SELECT session_id FROM sessions WHERE last_accessed < ? AND is_active = 1",
            (cutoff_iso,)
        )
        
        stale_sessions = [row[0] for row in cursor.fetchall()]
        
        for session_id in stale_sessions:
            if session_id in self._active_sessions:
                self.close_session(session_id)
        
        conn.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        # Close all active sessions (if they exist)
        if hasattr(self, '_active_sessions'):
            for session_id in list(self._active_sessions.keys()):
                try:
                    self.close_session(session_id)
                except Exception:
                    pass
        
        # Stop playwright (if it exists)
        if hasattr(self, '_playwright') and self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass

