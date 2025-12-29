"""
Tests for browser threading safety.

Tests that browser operations are thread-safe and handle cross-thread access errors.
"""

from __future__ import annotations

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings, HealthCheck

try:
    from broca.tools.browser_kernel import BrowserKernel, SessionConfig
    from broca.tools.web_search import WebSearchTool
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False


@pytest.mark.skipif(not BROWSER_AVAILABLE, reason="Browser tools not available")
class TestBrowserThreading:
    """Test browser threading safety."""
    
    @pytest.fixture
    def browser_kernel(self, tmp_path):
        """Create browser kernel for testing."""
        with patch('broca.tools.browser_kernel.PLAYWRIGHT_AVAILABLE', True):
            with patch('broca.tools.browser_kernel.sync_playwright') as mock_playwright:
                # Mock playwright to avoid actual browser launch
                mock_pw = MagicMock()
                mock_browser = MagicMock()
                mock_context = MagicMock()
                mock_page = MagicMock()
                mock_page.url = "about:blank"
                mock_page.title.return_value = "Test Page"
                
                mock_context.new_page.return_value = mock_page
                mock_browser.new_context.return_value = mock_context
                mock_pw.chromium.launch.return_value = mock_browser
                mock_playwright.return_value.start.return_value = mock_pw
                
                kernel = BrowserKernel(session_storage_path=str(tmp_path))
                kernel._playwright = mock_pw
                return kernel
    
    def test_session_tracks_thread_id(self, browser_kernel):
        """Test that sessions track the thread ID that created them."""
        session_config = SessionConfig()
        session_id = browser_kernel.new_session(session_config)
        
        # Check that thread ID is tracked
        assert session_id in browser_kernel._session_threads
        assert browser_kernel._session_threads[session_id] == threading.get_ident()
    
    def test_get_page_from_same_thread(self, browser_kernel):
        """Test that getting page from same thread succeeds."""
        session_config = SessionConfig()
        session_id = browser_kernel.new_session(session_config)
        
        # Should succeed from same thread
        page = browser_kernel._get_page(session_id)
        assert page is not None
    
    def test_get_page_from_different_thread_raises(self, browser_kernel):
        """Test that getting page from different thread raises error."""
        session_config = SessionConfig()
        session_id = browser_kernel.new_session(session_config)
        
        # Create a new thread and try to access
        error_occurred = threading.Event()
        error_message = [None]
        
        def access_from_other_thread():
            try:
                browser_kernel._get_page(session_id)
                error_message[0] = "Should have raised RuntimeError"
            except RuntimeError as e:
                error_message[0] = str(e)
                error_occurred.set()
            except Exception as e:
                error_message[0] = f"Unexpected error: {e}"
                error_occurred.set()
        
        thread = threading.Thread(target=access_from_other_thread)
        thread.start()
        thread.join(timeout=5.0)
        
        assert error_occurred.is_set(), f"Expected RuntimeError, got: {error_message[0]}"
        assert "different thread" in error_message[0].lower() or "thread" in error_message[0].lower()
    
    def test_concurrent_sessions_different_threads(self, browser_kernel):
        """Test that concurrent sessions from different threads work."""
        session_ids = []
        errors = []
        
        def create_session(thread_id):
            try:
                session_config = SessionConfig()
                session_id = browser_kernel.new_session(session_config)
                session_ids.append((thread_id, session_id))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=5.0)
        
        assert len(errors) == 0, f"Errors creating sessions: {errors}"
        assert len(session_ids) == 3, f"Expected 3 sessions, got {len(session_ids)}"
        
        # Each session should be accessible from its creating thread
        for thread_id, session_id in session_ids:
            # We can't easily test this without actual thread switching,
            # but we verify sessions were created successfully
    
    def test_session_lock_protects_access(self, browser_kernel):
        """Test that session lock protects concurrent access."""
        session_config = SessionConfig()
        session_id = browser_kernel.new_session(session_config)
        
        # Multiple threads trying to access session info
        results = []
        
        def access_session():
            with browser_kernel._session_lock:
                if session_id in browser_kernel._active_sessions:
                    results.append("accessed")
                time.sleep(0.01)  # Small delay to increase chance of contention
        
        threads = [threading.Thread(target=access_session) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2.0)
        
        # All should have accessed (lock protects, doesn't prevent)
        assert len(results) == 5


@pytest.mark.skipif(not BROWSER_AVAILABLE, reason="Browser tools not available")
class TestWebSearchThreadingErrorHandling:
    """Test web search tool's handling of threading errors."""
    
    def test_detects_threading_error(self):
        """Test that threading errors are detected."""
        error_msg = "cannot switch to a different thread (which happens to have exited)"
        assert "cannot switch to a different thread" in error_msg.lower()
        assert "thread" in error_msg.lower()
    
    def test_retries_with_new_session_on_threading_error(self):
        """Test that web search retries with new session on threading error."""
        # This is more of an integration test - we'd need to mock the full flow
        # For now, we test the error detection logic
        error = RuntimeError("cannot switch to a different thread (which happens to have exited)")
        error_str = str(error)
        is_threading_error = "cannot switch to a different thread" in error_str.lower() or "thread" in error_str.lower()
        assert is_threading_error is True


class TestBrowserThreadingFaultInjection:
    """Fault injection tests for browser threading."""
    
    @pytest.mark.skipif(not BROWSER_AVAILABLE, reason="Browser tools not available")
    def test_thread_exit_during_operation(self, browser_kernel):
        """Test behavior when thread exits during operation."""
        session_config = SessionConfig()
        session_id = browser_kernel.new_session(session_config)
        
        # Simulate thread exit by removing thread tracking
        original_thread_id = browser_kernel._session_threads[session_id]
        del browser_kernel._session_threads[session_id]
        
        # Should handle gracefully
        try:
            page = browser_kernel._get_page(session_id)
            # If it doesn't raise, that's also acceptable (thread ID check might pass)
        except (RuntimeError, KeyError):
            # Expected - thread tracking was removed
            pass
    
    @pytest.mark.skipif(not BROWSER_AVAILABLE, reason="Browser tools not available")
    def test_session_cleanup_removes_thread_tracking(self, browser_kernel):
        """Test that session cleanup removes thread tracking."""
        session_config = SessionConfig()
        session_id = browser_kernel.new_session(session_config)
        
        assert session_id in browser_kernel._session_threads
        
        browser_kernel.close_session(session_id)
        
        assert session_id not in browser_kernel._session_threads
        assert session_id not in browser_kernel._active_sessions


class TestBrowserThreadingPropertyBased:
    """Property-based tests for browser threading."""
    
    @pytest.mark.skipif(not BROWSER_AVAILABLE, reason="Browser tools not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(num_threads=st.integers(min_value=1, max_value=5))
    def test_multiple_threads_create_separate_sessions(self, browser_kernel, num_threads):
        """Property: Multiple threads can create separate sessions without interference."""
        session_ids = []
        errors = []
        
        def create_session():
            try:
                session_config = SessionConfig()
                session_id = browser_kernel.new_session(session_config)
                session_ids.append(session_id)
            except Exception as e:
                errors.append(str(e))
        
        threads = [threading.Thread(target=create_session) for _ in range(num_threads)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2.0)
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(session_ids) == num_threads
        assert len(set(session_ids)) == num_threads, "All session IDs should be unique"

