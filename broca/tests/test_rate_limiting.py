"""
Tests for rate limiting on escalation requests.

Tests that escalation requests are rate limited.
"""

from __future__ import annotations

import pytest
import time

from broca.environment.policy.manager import PolicyManager
from broca.environment.access_types import AccessLevel


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_enforced(self):
        """Test that rate limit is enforced on escalation requests."""
        manager = PolicyManager()
        
        # Make max requests
        for i in range(manager._rate_limit_max_requests):
            request = manager.request_escalation(AccessLevel.SUPERVISED, f"Request {i}")
            assert request is not None
        
        # Next request should fail
        with pytest.raises(ValueError, match="Rate limit exceeded"):
            manager.request_escalation(AccessLevel.SUPERVISED, "Should fail")
    
    def test_rate_limit_resets_after_window(self):
        """Test that rate limit resets after time window."""
        manager = PolicyManager()
        manager._rate_limit_window_seconds = 0.1  # Very short window for testing
        
        # Make max requests
        for i in range(manager._rate_limit_max_requests):
            manager.request_escalation(AccessLevel.SUPERVISED, f"Request {i}")
        
        # Wait for window to expire
        time.sleep(0.15)
        
        # Should be able to make another request
        request = manager.request_escalation(AccessLevel.SUPERVISED, "After window")
        assert request is not None
    
    def test_rate_limit_tracks_timestamps(self):
        """Test that rate limiting tracks request timestamps."""
        manager = PolicyManager()
        
        # Make a request
        manager.request_escalation(AccessLevel.SUPERVISED, "Test")
        
        # Should have one timestamp
        assert len(manager._escalation_request_timestamps) == 1

