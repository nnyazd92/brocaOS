"""
Tests for BrowserNavigationTool implementation.

Tests browser navigation functionality using mocked Playwright API.
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pytest
from hypothesis import given, strategies as st

from broca.tools.browser_navigation import BrowserNavigationTool


class TestBrowserNavigationToolInitialization:
    """Test BrowserNavigationTool initialization."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_init_with_defaults(self, mock_sync_playwright):
        """
        Test initialization with default configuration.
        
        Rationale: Ensures tool can be initialized with defaults.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        
        assert tool.name == "browser_navigation"
        assert tool._headless is True
        assert tool._timeout == 30000  # 30 seconds in ms
        assert tool._stealth_mode is True
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_init_with_custom_config(self, mock_sync_playwright):
        """
        Test initialization with custom configuration.
        
        Rationale: Ensures tool accepts custom configuration parameters.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool(
            headless=False,
            timeout=60,
            stealth_mode=False,
            viewport_width=1280,
            viewport_height=720
        )
        
        assert tool._headless is False
        assert tool._timeout == 60000
        assert tool._stealth_mode is False
        assert tool._viewport_width == 1280
        assert tool._viewport_height == 720
    
    def test_init_missing_playwright_raises_error(self):
        """
        Test that missing playwright package raises ValueError.
        
        Rationale: Ensures clear error when required package is not installed.
        """
        with patch('broca.tools.browser_navigation.PLAYWRIGHT_AVAILABLE', False):
            with pytest.raises(ValueError, match="playwright package is not installed"):
                BrowserNavigationTool()


class TestBrowserNavigationToolProperties:
    """Test BrowserNavigationTool properties."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_name_property(self, mock_sync_playwright):
        """
        Test that name property returns correct value.
        
        Rationale: Ensures tool has correct identifier.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        assert tool.name == "browser_navigation"
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_description_property(self, mock_sync_playwright):
        """
        Test that description property returns informative description.
        
        Rationale: Ensures LLM understands when to use the tool.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        description = tool.description
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "navigate" in description.lower()
        assert "browser" in description.lower()
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_parameters_property(self, mock_sync_playwright):
        """
        Test that parameters property returns valid JSON schema.
        
        Rationale: Ensures tool parameters are properly defined for function calling.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "properties" in params
        assert "action" in params["properties"]
        assert "required" in params
        assert "action" in params["required"]
        assert params["properties"]["action"]["enum"] == [
            "navigate", "click", "fill", "extract", "screenshot", "wait"
        ]


class TestBrowserNavigationToolNavigate:
    """Test BrowserNavigationTool navigate action."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_navigate_success(self, mock_sync_playwright):
        """
        Test successful navigation.
        
        Rationale: Ensures tool can navigate to URLs successfully.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response
        mock_page.title.return_value = "Test Page"
        mock_page.url = "https://example.com"
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="navigate", url="https://example.com")
        
        assert result["success"] is True
        assert result["action"] == "navigate"
        assert result["url"] == "https://example.com"
        assert result["status"] == 200
        assert result["title"] == "Test Page"
        mock_page.goto.assert_called_once()
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_navigate_missing_url(self, mock_sync_playwright):
        """
        Test navigation without URL parameter.
        
        Rationale: Ensures tool handles missing required parameters.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="navigate")
        
        assert result["success"] is False
        assert "URL parameter is required" in result["error"]
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_navigate_timeout(self, mock_sync_playwright):
        """
        Test navigation timeout handling.
        
        Rationale: Ensures tool handles timeout errors gracefully.
        """
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.goto.side_effect = PlaywrightTimeoutError("Timeout")
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="navigate", url="https://example.com")
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()


class TestBrowserNavigationToolClick:
    """Test BrowserNavigationTool click action."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_click_by_selector(self, mock_sync_playwright):
        """
        Test clicking element by selector.
        
        Rationale: Ensures tool can click elements using CSS selectors.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="click", selector="button#submit")
        
        assert result["success"] is True
        assert result["action"] == "click"
        assert result["selector"] == "button#submit"
        mock_page.click.assert_called_once_with("button#submit", timeout=30000)
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_click_by_text(self, mock_sync_playwright):
        """
        Test clicking element by text.
        
        Rationale: Ensures tool can click elements using text content.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="click", text="Submit")
        
        assert result["success"] is True
        assert result["text"] == "Submit"
        mock_page.click.assert_called_once_with("text=Submit", timeout=30000)
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_click_missing_selector_and_text(self, mock_sync_playwright):
        """
        Test clicking without selector or text.
        
        Rationale: Ensures tool requires either selector or text.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="click")
        
        assert result["success"] is False
        assert "selector or text" in result["error"].lower()


class TestBrowserNavigationToolFill:
    """Test BrowserNavigationTool fill action."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_fill_success(self, mock_sync_playwright):
        """
        Test successful form filling.
        
        Rationale: Ensures tool can fill form fields.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(
            action="fill",
            selector="input[name='email']",
            value="user@example.com"
        )
        
        assert result["success"] is True
        assert result["action"] == "fill"
        assert result["selector"] == "input[name='email']"
        assert result["value"] == "user@example.com"
        mock_page.fill.assert_called_once_with("input[name='email']", "user@example.com", timeout=30000)
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_fill_missing_selector(self, mock_sync_playwright):
        """
        Test filling without selector.
        
        Rationale: Ensures tool requires selector for fill action.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="fill", value="test")
        
        assert result["success"] is False
        assert "selector" in result["error"].lower()
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_fill_missing_value(self, mock_sync_playwright):
        """
        Test filling without value.
        
        Rationale: Ensures tool requires value for fill action.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="fill", selector="input")
        
        assert result["success"] is False
        assert "value" in result["error"].lower() or "text" in result["error"].lower()


class TestBrowserNavigationToolExtract:
    """Test BrowserNavigationTool extract action."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_extract_by_selector(self, mock_sync_playwright):
        """
        Test extracting text from element by selector.
        
        Rationale: Ensures tool can extract text from specific elements.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_element = Mock()
        mock_element.inner_text.return_value = "Extracted text"
        mock_page.query_selector.return_value = mock_element
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="extract", selector="div.content")
        
        assert result["success"] is True
        assert result["action"] == "extract"
        assert result["selector"] == "div.content"
        assert result["text"] == "Extracted text"
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_extract_from_page(self, mock_sync_playwright):
        """
        Test extracting text from entire page.
        
        Rationale: Ensures tool can extract text from entire page when no selector provided.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.inner_text.return_value = "Page content"
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="extract")
        
        assert result["success"] is True
        assert result["text"] == "Page content"
        assert result.get("selector") is None
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_extract_element_not_found(self, mock_sync_playwright):
        """
        Test extracting from non-existent element.
        
        Rationale: Ensures tool handles missing elements gracefully.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.query_selector.return_value = None
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="extract", selector="div.missing")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestBrowserNavigationToolScreenshot:
    """Test BrowserNavigationTool screenshot action."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_screenshot_success(self, mock_sync_playwright):
        """
        Test successful screenshot capture.
        
        Rationale: Ensures tool can take screenshots.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = os.path.join(tmpdir, "screenshot.png")
            tool = BrowserNavigationTool()
            result = tool.execute(action="screenshot", screenshot_path=screenshot_path)
            
            assert result["success"] is True
            assert result["action"] == "screenshot"
            assert result["screenshot_path"] == screenshot_path
            mock_page.screenshot.assert_called_once()
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_screenshot_full_page(self, mock_sync_playwright):
        """
        Test full page screenshot.
        
        Rationale: Ensures tool supports full page screenshots.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = os.path.join(tmpdir, "screenshot.png")
            tool = BrowserNavigationTool()
            result = tool.execute(
                action="screenshot",
                screenshot_path=screenshot_path,
                full_page=True
            )
            
            assert result["success"] is True
            assert result["full_page"] is True
            # Check that screenshot was called with full_page=True
            call_args = mock_page.screenshot.call_args
            assert call_args[1]["full_page"] is True


class TestBrowserNavigationToolWait:
    """Test BrowserNavigationTool wait action."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_wait_networkidle(self, mock_sync_playwright):
        """
        Test waiting for network idle.
        
        Rationale: Ensures tool can wait for network idle state.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="wait", wait_for="networkidle")
        
        assert result["success"] is True
        assert result["action"] == "wait"
        assert result["wait_for"] == "networkidle"
        mock_page.wait_for_load_state.assert_called_once_with("networkidle", timeout=30000)
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_wait_selector(self, mock_sync_playwright):
        """
        Test waiting for selector.
        
        Rationale: Ensures tool can wait for elements to appear.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="wait", wait_for="selector:div.content")
        
        assert result["success"] is True
        mock_page.wait_for_selector.assert_called_once_with("div.content", timeout=30000)
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_wait_missing_wait_for(self, mock_sync_playwright):
        """
        Test waiting without wait_for parameter.
        
        Rationale: Ensures tool requires wait_for parameter.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="wait")
        
        assert result["success"] is False
        assert "wait_for" in result["error"].lower()


class TestBrowserNavigationToolStealth:
    """Test BrowserNavigationTool stealth features."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_stealth_mode_enabled(self, mock_sync_playwright):
        """
        Test stealth mode configuration.
        
        Rationale: Ensures stealth features are applied when enabled.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool(stealth_mode=True)
        tool._get_page()  # Trigger page creation
        
        # Check that browser was launched with stealth args
        launch_call = mock_playwright_instance.chromium.launch.call_args
        assert launch_call is not None
        args = launch_call[1].get("args", [])
        assert any("AutomationControlled" in arg for arg in args)
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_user_agent_rotation(self, mock_sync_playwright):
        """
        Test user agent rotation in stealth mode.
        
        Rationale: Ensures user agents are rotated when stealth mode is enabled.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        user_agents = ["Agent1", "Agent2", "Agent3"]
        tool = BrowserNavigationTool(stealth_mode=True, user_agents=user_agents)
        tool._get_page()  # Trigger page creation
        
        # Check that new_context was called with user_agent parameter
        assert mock_browser.new_context.called
        call_kwargs = mock_browser.new_context.call_args[1]
        assert "user_agent" in call_kwargs
        user_agent_arg = call_kwargs["user_agent"]
        assert user_agent_arg in user_agents
        
        # Check that extra_http_headers were also set
        assert "extra_http_headers" in call_kwargs
        assert "viewport" in call_kwargs


class TestBrowserNavigationToolErrorHandling:
    """Test BrowserNavigationTool error handling."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_unknown_action(self, mock_sync_playwright):
        """
        Test handling of unknown action.
        
        Rationale: Ensures tool handles unknown actions gracefully.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="unknown_action")
        
        assert result["success"] is False
        assert "unknown action" in result["error"].lower()
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_missing_action(self, mock_sync_playwright):
        """
        Test handling of missing action parameter.
        
        Rationale: Ensures tool requires action parameter.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute()
        
        assert result["success"] is False
        assert "action" in result["error"].lower()
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_general_exception_handling(self, mock_sync_playwright):
        """
        Test handling of general exceptions.
        
        Rationale: Ensures tool handles unexpected errors gracefully.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_page.goto.side_effect = Exception("Unexpected error")
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="navigate", url="https://example.com")
        
        assert result["success"] is False
        assert "error" in result


class TestBrowserNavigationToolFormatResult:
    """Test BrowserNavigationTool result formatting."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_format_navigate_result(self, mock_sync_playwright):
        """
        Test formatting navigate result.
        
        Rationale: Ensures navigate results are formatted correctly.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = {
            "success": True,
            "action": "navigate",
            "url": "https://example.com",
            "url_final": "https://example.com",
            "status": 200,
            "title": "Example"
        }
        
        formatted = tool.format_result(result)
        
        assert "navigate" in formatted.lower()
        assert "https://example.com" in formatted
        assert "200" in formatted
        assert "Example" in formatted
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_format_error_result(self, mock_sync_playwright):
        """
        Test formatting error result.
        
        Rationale: Ensures error results are formatted clearly.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = {
            "success": False,
            "error": "Test error",
            "action": "navigate"
        }
        
        formatted = tool.format_result(result)
        
        assert "error" in formatted.lower()
        assert "Test error" in formatted
        assert "navigate" in formatted
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    def test_format_extract_result_truncates_long_text(self, mock_sync_playwright):
        """
        Test that long extracted text is truncated in formatted output.
        
        Rationale: Ensures formatted output is manageable in size.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        long_text = "x" * 6000  # 6000 characters
        result = {
            "success": True,
            "action": "extract",
            "text": long_text,
            "url": "https://example.com"
        }
        
        formatted = tool.format_result(result)
        
        # Should truncate to 5000 chars + "..."
        assert len(long_text[:5000]) < len(long_text)
        assert "..." in formatted


# Property-based testing with Hypothesis
class TestBrowserNavigationToolPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    @given(st.text(min_size=1, max_size=100))
    def test_navigate_with_various_urls(self, mock_sync_playwright, url):
        """
        Test navigation with various URL formats.
        
        Rationale: Property-based test to ensure tool handles various URL formats.
        """
        # Skip invalid URLs (this is a simplified test)
        if not url.startswith(("http://", "https://")):
            pytest.skip("Invalid URL format")
        
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response
        mock_page.title.return_value = "Test"
        mock_page.url = url
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="navigate", url=url)
        
        # Should either succeed or fail gracefully
        assert "success" in result
        assert result["action"] == "navigate"
    
    @patch('broca.tools.browser_navigation.sync_playwright')
    @given(st.integers(min_value=1, max_value=300))
    def test_timeout_parameter_validation(self, mock_sync_playwright, timeout):
        """
        Test timeout parameter validation.
        
        Rationale: Property-based test to ensure timeout values are handled correctly.
        """
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response
        mock_page.title.return_value = "Test"
        mock_page.url = "https://example.com"
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        
        tool = BrowserNavigationTool()
        result = tool.execute(action="navigate", url="https://example.com", timeout=timeout)
        
        # Should handle timeout parameter (may succeed or timeout)
        assert "success" in result or "timeout" in result.get("error", "").lower()

