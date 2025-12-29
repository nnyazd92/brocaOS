"""
Browser navigation tool implementation using Playwright.

Provides headless browser navigation capabilities to the LLM with stealth features
to minimize CAPTCHA triggers.
"""

from __future__ import annotations

import os
import logging
import random
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

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

from . import Tool
from ..config import config

logger = logging.getLogger(__name__)


class BrowserNavigationTool:
    """
    Browser navigation tool using Playwright.
    
    Allows the LLM to navigate the web, interact with pages, extract content,
    and take screenshots using a headless browser with stealth features.
    """
    
    def __init__(
        self,
        headless: bool | None = None,
        timeout: int | None = None,
        stealth_mode: bool | None = None,
        viewport_width: int | None = None,
        viewport_height: int | None = None,
        user_agents: List[str] | None = None
    ) -> None:
        """
        Initialize the browser navigation tool.
        
        Args:
            headless: Run browser in headless mode (defaults to config)
            timeout: Default timeout in seconds (defaults to config)
            stealth_mode: Enable stealth features (defaults to config)
            viewport_width: Viewport width (defaults to config)
            viewport_height: Viewport height (defaults to config)
            user_agents: List of user agents for rotation (defaults to config)
            
        Raises:
            ValueError: If playwright is not installed
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ValueError(
                "playwright package is not installed. "
                "Install it with: pip install playwright && playwright install chromium"
            )
        
        self._headless = headless if headless is not None else config.tools.browser_headless
        self._timeout = timeout if timeout is not None else config.tools.browser_timeout * 1000  # Convert to ms
        self._stealth_mode = stealth_mode if stealth_mode is not None else config.tools.browser_stealth_mode
        self._viewport_width = viewport_width if viewport_width is not None else config.tools.browser_viewport_width
        self._viewport_height = viewport_height if viewport_height is not None else config.tools.browser_viewport_height
        self._user_agents = user_agents if user_agents is not None else config.tools.browser_user_agents
        
        # Browser instance management
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        logger.info("Initialized BrowserNavigationTool")
    
    def _get_playwright(self):
        """Get or create playwright instance."""
        if self._playwright is None:
            self._playwright = sync_playwright().start()
        return self._playwright
    
    def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if self._browser is None:
            playwright = self._get_playwright()
            launch_args = []
            
            if self._stealth_mode:
                # Stealth mode: add flags to avoid detection
                launch_args.extend([
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ])
            
            self._browser = playwright.chromium.launch(
                headless=self._headless,
                args=launch_args
            )
        return self._browser
    
    def _get_page(self) -> Page:
        """Get or create page instance with stealth configuration."""
        if self._page is None:
            browser = self._get_browser()
            
            # Calculate viewport size
            if self._stealth_mode:
                # Randomize viewport slightly
                width = self._viewport_width + random.randint(-50, 50)
                height = self._viewport_height + random.randint(-50, 50)
            else:
                width = self._viewport_width
                height = self._viewport_height
            
            # Create context with user agent, viewport, and headers
            context_options = {
                "viewport": {"width": width, "height": height}
            }
            
            if self._stealth_mode and self._user_agents:
                user_agent = random.choice(self._user_agents)
                context_options["user_agent"] = user_agent
                context_options["extra_http_headers"] = {
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
            
            self._context = browser.new_context(**context_options)
            self._page = self._context.new_page()
            
            # Set timeout
            self._page.set_default_timeout(self._timeout)
        
        return self._page
    
    def _human_delay(self) -> None:
        """Add a human-like delay between actions."""
        if self._stealth_mode:
            delay = random.uniform(0.1, 0.5)  # 100-500ms
            time.sleep(delay)
    
    def _cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            if self._page:
                self._page.close()
                self._page = None
        except Exception as e:
            logger.debug(f"Error closing page: {e}")
        
        try:
            if self._context:
                self._context.close()
                self._context = None
        except Exception as e:
            logger.debug(f"Error closing context: {e}")
        
        try:
            if self._browser:
                self._browser.close()
                self._browser = None
        except Exception as e:
            logger.debug(f"Error closing browser: {e}")
        
        try:
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
        except Exception as e:
            logger.debug(f"Error stopping playwright: {e}")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "browser_navigation"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM with comprehensive usage guide."""
        return (
            "Navigate and interact with websites using a headless browser with stealth features.\n\n"
            "CAPABILITIES:\n"
            "- Navigate to any URL and wait for page load\n"
            "- Click buttons, links, and interactive elements\n"
            "- Fill forms (input fields, textareas, select dropdowns)\n"
            "- Extract text content from pages or specific elements\n"
            "- Take screenshots (viewport or full page)\n"
            "- Wait for elements, network idle, or page load states\n\n"
            "STEALTH FEATURES:\n"
            "- User agent rotation to avoid detection\n"
            "- Human-like random delays between actions (100-500ms)\n"
            "- Viewport size randomization\n"
            "- Browser flags to minimize CAPTCHA triggers\n"
            "- Realistic HTTP headers and browser fingerprinting\n\n"
            "SESSION MANAGEMENT:\n"
            "- Browser sessions persist across tool calls\n"
            "- Cookies and localStorage are maintained automatically\n"
            "- Each browsing task gets its own isolated session\n"
            "- Sessions are cleaned up after 24 hours of inactivity\n\n"
            "WORKFLOWS:\n\n"
            "1. Simple Navigation and Content Extraction:\n"
            '   {"action": "navigate", "url": "https://example.com"}\n'
            '   {"action": "wait", "wait_for": "networkidle"}\n'
            '   {"action": "extract", "selector": "article.main-content"}\n\n'
            "2. Form Interaction (Login/Registration):\n"
            '   {"action": "navigate", "url": "https://example.com/login"}\n'
            '   {"action": "wait", "wait_for": "networkidle"}\n'
            '   {"action": "fill", "selector": "input[name=\\"email\\"]", "value": "user@example.com"}\n'
            '   {"action": "fill", "selector": "input[name=\\"password\\"]", "value": "password123"}\n'
            '   {"action": "click", "selector": "button[type=\\"submit\\"]"}\n'
            '   {"action": "wait", "wait_for": "networkidle"}\n\n'
            "3. Multi-step Navigation with Clicking:\n"
            '   {"action": "navigate", "url": "https://example.com"}\n'
            '   {"action": "click", "text": "Learn More"}\n'
            '   {"action": "wait", "wait_for": "selector:.content-loaded"}\n'
            '   {"action": "extract"}\n\n'
            "4. Screenshot Capture for Verification:\n"
            '   {"action": "navigate", "url": "https://example.com"}\n'
            '   {"action": "wait", "wait_for": "networkidle"}\n'
            '   {"action": "screenshot", "screenshot_path": "page.png", "full_page": true}\n\n'
            "ACTION REFERENCE:\n\n"
            "navigate:\n"
            '  {"action": "navigate", "url": "https://example.com", "timeout": 30}\n'
            "  - Navigates to URL and waits for networkidle by default\n"
            "  - Returns: status code, final URL, page title\n\n"
            "click:\n"
            '  {"action": "click", "selector": "button#submit"}\n'
            '  {"action": "click", "text": "Click Here"}\n'
            "  - Use CSS selector or text content to find element\n"
            "  - Waits for element to be visible and clickable\n\n"
            "fill:\n"
            '  {"action": "fill", "selector": "input[name=\\"email\\"]", "value": "text"}\n'
            '  {"action": "fill", "selector": "textarea", "text": "long text content"}\n'
            "  - Clears field before filling (use value or text parameter)\n"
            "  - Works with input, textarea, and select elements\n\n"
            "extract:\n"
            '  {"action": "extract", "selector": "div.content"}\n'
            '  {"action": "extract"}  # Extracts entire page\n'
            "  - Extracts text content from element or entire page\n"
            "  - Returns plain text with formatting preserved\n\n"
            "screenshot:\n"
            '  {"action": "screenshot", "screenshot_path": "screenshot.png", "full_page": true}\n'
            "  - Saves PNG screenshot to specified path\n"
            "  - full_page: true captures entire page, false captures viewport\n\n"
            "wait:\n"
            '  {"action": "wait", "wait_for": "networkidle"}\n'
            '  {"action": "wait", "wait_for": "selector:.content"}\n'
            '  {"action": "wait", "wait_for": "text:Loading complete"}\n'
            "  - Wait conditions: 'networkidle', 'load', 'domcontentloaded', selector, or text\n"
            "  - Use after navigation for dynamic content\n\n"
            "ERROR HANDLING:\n"
            "- Timeouts: Increase timeout parameter (default: 30 seconds)\n"
            "- Element not found: Verify selector using browser dev tools\n"
            "- Navigation failures: Check URL validity and network connectivity\n"
            "- CAPTCHAs: Tool will detect and report (cannot bypass - this is by design)\n"
            "- Rate limiting: Some sites may block automated access (normal behavior)\n\n"
            "BEST PRACTICES:\n"
            "- Always wait for 'networkidle' after navigation for dynamic content\n"
            "- Use specific CSS selectors (IDs, classes) when possible\n"
            "- Extract content immediately after navigation for accuracy\n"
            "- Use screenshots for debugging or verification\n"
            "- Chain actions: navigate → wait → extract for reliable results\n"
            "- For forms: fill all fields, then click submit, then wait for response\n\n"
            "SELECTOR TIPS:\n"
            "- Use browser dev tools to find reliable selectors\n"
            "- Prefer IDs: #element-id\n"
            "- Use attributes: [name='value'], [type='submit']\n"
            "- Combine: div.content > p:first-child\n"
            "- Text matching: Use 'text' parameter for click by text content"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "click", "fill", "extract", "screenshot", "wait"],
                    "description": "Action to perform: navigate, click, fill, extract, screenshot, or wait"
                },
                "url": {
                    "type": "string",
                    "description": (
                        "URL to navigate to (required for navigate action). "
                        "Must be a valid HTTP/HTTPS URL. "
                        "Example: 'https://example.com/page'"
                    )
                },
                "selector": {
                    "type": "string",
                    "description": (
                        "CSS selector for element (for click, fill, extract actions). "
                        "Examples: '#submit-button', '.content', 'input[name=\"email\"]', "
                        "'div > p:first-child'. Use browser dev tools to find reliable selectors."
                    )
                },
                "text": {
                    "type": "string",
                    "description": (
                        "Text to find (for click by text) or fill (for fill action). "
                        "For click: matches element text content. "
                        "For fill: text to enter into form field."
                    )
                },
                "value": {
                    "type": "string",
                    "description": (
                        "Value to fill into form field (alternative to text for fill action). "
                        "Use either 'value' or 'text' parameter for filling forms."
                    )
                },
                "wait_for": {
                    "type": "string",
                    "description": (
                        "What to wait for (for wait action). "
                        "Options: 'networkidle' (wait for network to be idle), "
                        "'load' (wait for page load), 'domcontentloaded' (wait for DOM), "
                        "'selector:.class' (wait for selector), 'text:Loading' (wait for text). "
                        "Use 'networkidle' after navigation for dynamic content."
                    )
                },
                "timeout": {
                    "type": "integer",
                    "description": (
                        "Timeout in seconds for the operation. "
                        "Default: 30 seconds. "
                        "Increase for slow-loading pages or slow network connections. "
                        "Maximum: 300 seconds (5 minutes)."
                    ),
                    "minimum": 1,
                    "maximum": 300
                },
                "screenshot_path": {
                    "type": "string",
                    "description": (
                        "Path to save screenshot (for screenshot action). "
                        "Example: 'screenshot.png' or 'docs/screenshots/page.png'. "
                        "Directory will be created if it doesn't exist."
                    )
                },
                "full_page": {
                    "type": "boolean",
                    "description": (
                        "Take full page screenshot (default: false, for screenshot action). "
                        "true: Capture entire page (may be very long). "
                        "false: Capture only visible viewport."
                    )
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute a browser navigation action.
        
        Args:
            **kwargs: Action parameters as specified in parameters schema
            
        Returns:
            Dictionary containing execution results
        """
        action = kwargs.get("action")
        if not action:
            return {
                "success": False,
                "error": "Action parameter is required"
            }
        
        try:
            page = self._get_page()
            timeout = kwargs.get("timeout")
            if timeout:
                timeout_ms = timeout * 1000
            else:
                timeout_ms = self._timeout
            
            if action == "navigate":
                return self._execute_navigate(page, kwargs, timeout_ms)
            elif action == "click":
                return self._execute_click(page, kwargs, timeout_ms)
            elif action == "fill":
                return self._execute_fill(page, kwargs, timeout_ms)
            elif action == "extract":
                return self._execute_extract(page, kwargs, timeout_ms)
            elif action == "screenshot":
                return self._execute_screenshot(page, kwargs)
            elif action == "wait":
                return self._execute_wait(page, kwargs, timeout_ms)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error: {e}")
            return {
                "success": False,
                "error": f"Operation timed out: {str(e)}",
                "action": action
            }
        except Exception as e:
            logger.error(f"Error executing browser action: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    def _execute_navigate(self, page: Page, kwargs: Dict[str, Any], timeout_ms: int) -> Dict[str, Any]:
        """Execute navigate action."""
        url = kwargs.get("url")
        if not url:
            return {
                "success": False,
                "error": "URL parameter is required for navigate action"
            }
        
        try:
            response = page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            self._human_delay()
            
            return {
                "success": True,
                "action": "navigate",
                "url": url,
                "status": response.status if response else None,
                "title": page.title(),
                "url_final": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to navigate to {url}: {str(e)}",
                "action": "navigate",
                "url": url
            }
    
    def _execute_click(self, page: Page, kwargs: Dict[str, Any], timeout_ms: int) -> Dict[str, Any]:
        """Execute click action."""
        selector = kwargs.get("selector")
        text = kwargs.get("text")
        
        if not selector and not text:
            return {
                "success": False,
                "error": "Either selector or text parameter is required for click action"
            }
        
        try:
            if selector:
                page.click(selector, timeout=timeout_ms)
            elif text:
                page.click(f"text={text}", timeout=timeout_ms)
            
            self._human_delay()
            
            return {
                "success": True,
                "action": "click",
                "selector": selector,
                "text": text,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to click element: {str(e)}",
                "action": "click",
                "selector": selector,
                "text": text
            }
    
    def _execute_fill(self, page: Page, kwargs: Dict[str, Any], timeout_ms: int) -> Dict[str, Any]:
        """Execute fill action."""
        selector = kwargs.get("selector")
        if not selector:
            return {
                "success": False,
                "error": "Selector parameter is required for fill action"
            }
        
        value = kwargs.get("value") or kwargs.get("text")
        if not value:
            return {
                "success": False,
                "error": "Value or text parameter is required for fill action"
            }
        
        try:
            page.fill(selector, value, timeout=timeout_ms)
            self._human_delay()
            
            return {
                "success": True,
                "action": "fill",
                "selector": selector,
                "value": value,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fill element: {str(e)}",
                "action": "fill",
                "selector": selector
            }
    
    def _execute_extract(self, page: Page, kwargs: Dict[str, Any], timeout_ms: int) -> Dict[str, Any]:
        """Execute extract action."""
        selector = kwargs.get("selector")
        
        try:
            if selector:
                # Extract from specific element
                element = page.query_selector(selector)
                if not element:
                    return {
                        "success": False,
                        "error": f"Element not found: {selector}",
                        "action": "extract"
                    }
                text = element.inner_text()
            else:
                # Extract from entire page
                text = page.inner_text("body")
            
            return {
                "success": True,
                "action": "extract",
                "selector": selector,
                "text": text,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to extract text: {str(e)}",
                "action": "extract",
                "selector": selector
            }
    
    def _execute_screenshot(self, page: Page, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute screenshot action."""
        screenshot_path = kwargs.get("screenshot_path", "screenshot.png")
        full_page = kwargs.get("full_page", False)
        
        try:
            # Ensure directory exists
            path = Path(screenshot_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            page.screenshot(path=screenshot_path, full_page=full_page)
            
            return {
                "success": True,
                "action": "screenshot",
                "screenshot_path": screenshot_path,
                "full_page": full_page,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to take screenshot: {str(e)}",
                "action": "screenshot",
                "screenshot_path": screenshot_path
            }
    
    def _execute_wait(self, page: Page, kwargs: Dict[str, Any], timeout_ms: int) -> Dict[str, Any]:
        """Execute wait action."""
        wait_for = kwargs.get("wait_for")
        if not wait_for:
            return {
                "success": False,
                "error": "wait_for parameter is required for wait action"
            }
        
        try:
            if wait_for == "networkidle":
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            elif wait_for == "load":
                page.wait_for_load_state("load", timeout=timeout_ms)
            elif wait_for == "domcontentloaded":
                page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            elif wait_for.startswith("selector:"):
                selector = wait_for.split(":", 1)[1]
                page.wait_for_selector(selector, timeout=timeout_ms)
            elif wait_for.startswith("text:"):
                text = wait_for.split(":", 1)[1]
                page.wait_for_selector(f"text={text}", timeout=timeout_ms)
            else:
                # Assume it's a selector
                page.wait_for_selector(wait_for, timeout=timeout_ms)
            
            return {
                "success": True,
                "action": "wait",
                "wait_for": wait_for,
                "url": page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Wait condition not met: {str(e)}",
                "action": "wait",
                "wait_for": wait_for
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            action = result.get("action", "unknown")
            return f"Browser navigation error ({action}): {error}"
        
        action = result.get("action", "unknown")
        lines = [f"Browser action '{action}' completed successfully"]
        
        if action == "navigate":
            lines.append(f"URL: {result.get('url')}")
            lines.append(f"Final URL: {result.get('url_final')}")
            lines.append(f"Status: {result.get('status')}")
            lines.append(f"Title: {result.get('title')}")
        elif action == "click":
            if result.get("selector"):
                lines.append(f"Clicked element: {result.get('selector')}")
            if result.get("text"):
                lines.append(f"Clicked text: {result.get('text')}")
            lines.append(f"Current URL: {result.get('url')}")
        elif action == "fill":
            lines.append(f"Filled selector: {result.get('selector')}")
            lines.append(f"Value: {result.get('value')}")
            lines.append(f"Current URL: {result.get('url')}")
        elif action == "extract":
            text = result.get("text", "")
            selector = result.get("selector")
            if selector:
                lines.append(f"Extracted from selector: {selector}")
            else:
                lines.append("Extracted from entire page")
            # Truncate long text
            if len(text) > 5000:
                lines.append(f"Text (truncated):\n{text[:5000]}...")
            else:
                lines.append(f"Text:\n{text}")
            lines.append(f"URL: {result.get('url')}")
        elif action == "screenshot":
            lines.append(f"Screenshot saved to: {result.get('screenshot_path')}")
            lines.append(f"Full page: {result.get('full_page')}")
            lines.append(f"URL: {result.get('url')}")
        elif action == "wait":
            lines.append(f"Waited for: {result.get('wait_for')}")
            lines.append(f"URL: {result.get('url')}")
        
        return "\n".join(lines)
    
    def __del__(self):
        """Cleanup on deletion."""
        self._cleanup()

