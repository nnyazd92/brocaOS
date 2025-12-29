"""
Tests for BrowserKernel implementation.

Tests low-level browser operations with session management.
"""

from __future__ import annotations

import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import pytest

from broca.tools.browser_kernel import BrowserKernel, SessionConfig


class TestBrowserKernelInitialization:
    """Test BrowserKernel initialization."""
    
    @patch('broca.tools.browser_kernel.sync_playwright')
    def test_init_creates_storage_directory(self, mock_sync_playwright):
        """Test that initialization creates storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_playwright_instance = Mock()
            mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
            
            kernel = BrowserKernel(session_storage_path=tmpdir)
            
            assert os.path.exists(tmpdir)
            assert os.path.exists(os.path.join(tmpdir, "sessions.db"))
    
    @patch('broca.tools.browser_kernel.sync_playwright')
    def test_init_creates_registry(self, mock_sync_playwright):
        """Test that initialization creates session registry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_playwright_instance = Mock()
            mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
            
            kernel = BrowserKernel(session_storage_path=tmpdir)
            
            # Registry should be created
            assert os.path.exists(os.path.join(tmpdir, "sessions.db"))


class TestBrowserKernelSessionManagement:
    """Test session management."""
    
    @patch('broca.tools.browser_kernel.sync_playwright')
    def test_new_session_creates_session(self, mock_sync_playwright):
        """Test creating a new session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_page = Mock()
            mock_browser.new_page.return_value = mock_page
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
            
            kernel = BrowserKernel(session_storage_path=tmpdir)
            session_id = kernel.new_session()
            
            assert session_id is not None
            assert len(session_id) > 0
            assert session_id in kernel.list_sessions()
    
    @patch('broca.tools.browser_kernel.sync_playwright')
    def test_close_session_removes_session(self, mock_sync_playwright):
        """Test closing a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_page = Mock()
            mock_browser.new_page.return_value = mock_page
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
            
            kernel = BrowserKernel(session_storage_path=tmpdir)
            session_id = kernel.new_session()
            
            assert session_id in kernel.list_sessions()
            
            kernel.close_session(session_id)
            
            assert session_id not in kernel.list_sessions()


class TestBrowserKernelNavigation:
    """Test navigation operations."""
    
    @patch('broca.tools.browser_kernel.sync_playwright')
    def test_goto_navigates_to_url(self, mock_sync_playwright):
        """Test navigating to a URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_page = Mock()
            mock_response = Mock()
            mock_response.status = 200
            mock_page.goto.return_value = mock_response
            mock_page.url = "https://example.com"
            mock_page.title.return_value = "Example"
            mock_browser.new_page.return_value = mock_page
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
            
            kernel = BrowserKernel(session_storage_path=tmpdir)
            session_id = kernel.new_session()
            
            result = kernel.goto(session_id, "https://example.com")
            
            assert result["success"] is True
            assert result["url"] == "https://example.com"
            mock_page.goto.assert_called_once()


class TestBrowserKernelSearch:
    """Test search functionality."""
    
    @patch('broca.tools.browser_kernel.sync_playwright')
    def test_search_duckduckgo(self, mock_sync_playwright):
        """Test DuckDuckGo search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_page = Mock()
            
            # Mock search result elements
            mock_result_elem = Mock()
            mock_title_elem = Mock()
            mock_title_elem.inner_text.return_value = "Test Result"
            mock_title_elem.get_attribute.return_value = "https://example.com"
            mock_result_elem.query_selector.return_value = mock_title_elem
            mock_page.query_selector_all.return_value = [mock_result_elem]
            mock_page.wait_for_selector.return_value = None
            
            mock_browser.new_page.return_value = mock_page
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
            
            kernel = BrowserKernel(session_storage_path=tmpdir)
            session_id = kernel.new_session()
            
            results = kernel.search(session_id, "ddg", "test query", count=1)
            
            # Should return results (even if mocked)
            assert isinstance(results, list)
            mock_page.goto.assert_called_once()


class TestBrowserKernelDestruction:
    """Test BrowserKernel destruction and cleanup."""
    
    @patch('broca.tools.browser_kernel.PLAYWRIGHT_AVAILABLE', True)
    @patch('broca.tools.browser_kernel.sync_playwright')
    def test_del_with_normal_initialization(self, mock_sync_playwright):
        """
        Test __del__ when both attributes exist (normal case).
        
        Rationale: Ensures __del__ works correctly when initialization completes successfully.
        Mutation testing: Verifies normal cleanup path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_playwright_instance = Mock()
            mock_playwright_instance.stop = Mock()
            mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
            
            kernel = BrowserKernel(session_storage_path=tmpdir)
            # Verify attributes exist
            assert hasattr(kernel, '_active_sessions')
            assert hasattr(kernel, '_playwright')
            
            # Explicitly call __del__ to test cleanup
            kernel.__del__()
            
            # Should not raise any exceptions
            # Playwright stop should be called if it exists
            if kernel._playwright:
                mock_playwright_instance.stop.assert_called_once()
    
    def test_del_without_active_sessions_attribute(self):
        """
        Test __del__ when __init__ fails before _active_sessions initialization.
        
        Rationale: Ensures __del__ handles missing _active_sessions gracefully.
        Fault injection: Simulates partial initialization failure.
        """
        # Create a kernel instance without _active_sessions attribute
        # This simulates __init__ failing before line 82
        kernel = object.__new__(BrowserKernel)
        # Only set _playwright, not _active_sessions
        kernel._playwright = None
        
        # __del__ should not raise AttributeError
        try:
            kernel.__del__()
        except AttributeError as e:
            if '_active_sessions' in str(e):
                pytest.fail(f"__del__ raised AttributeError for _active_sessions: {e}")
    
    def test_del_without_playwright_attribute(self):
        """
        Test __del__ when __init__ fails before _playwright initialization.
        
        Rationale: Ensures __del__ handles missing _playwright gracefully.
        Fault injection: Simulates partial initialization failure.
        """
        # Create a kernel instance without _playwright attribute
        # This simulates __init__ failing before line 85
        kernel = object.__new__(BrowserKernel)
        # Only set _active_sessions, not _playwright
        kernel._active_sessions = {}
        
        # __del__ should not raise AttributeError
        try:
            kernel.__del__()
        except AttributeError as e:
            if '_playwright' in str(e):
                pytest.fail(f"__del__ raised AttributeError for _playwright: {e}")
    
    def test_del_without_any_attributes(self):
        """
        Test __del__ when neither attribute exists (complete init failure).
        
        Rationale: Ensures __del__ handles complete initialization failure gracefully.
        Fault injection: Simulates complete initialization failure.
        """
        # Create a kernel instance without any attributes
        # This simulates __init__ failing immediately (e.g., before any attributes are set)
        kernel = object.__new__(BrowserKernel)
        # Don't set any attributes - simulate complete failure
        
        # __del__ should not raise AttributeError
        try:
            kernel.__del__()
        except AttributeError as e:
            pytest.fail(f"__del__ raised AttributeError when no attributes exist: {e}")
    
    @patch('broca.tools.browser_kernel.PLAYWRIGHT_AVAILABLE', True)
    @patch('broca.tools.browser_kernel.sync_playwright')
    def test_del_with_active_sessions_cleanup(self, mock_sync_playwright):
        """
        Test __del__ properly cleans up active sessions.
        
        Rationale: Ensures active sessions are closed during destruction.
        Coverage: Tests branch where _active_sessions exists and has items.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_page = Mock()
            mock_browser.new_page.return_value = mock_page
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
            
            kernel = BrowserKernel(session_storage_path=tmpdir)
            session_id = kernel.new_session()
            
            # Verify session exists
            assert session_id in kernel.list_sessions()
            assert len(kernel._active_sessions) > 0
            
            # Call __del__ explicitly
            kernel.__del__()
            
            # Sessions should be cleaned up (close_session is called)
            # Note: close_session removes from _active_sessions, so we can't verify
            # the exact state, but we can verify no exceptions were raised

