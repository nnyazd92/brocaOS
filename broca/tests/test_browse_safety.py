"""
Tests for BrowseSafety implementation.

Tests safety checks and governance.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

from broca.tools.browse_safety import BrowseSafety


class TestBrowseSafety:
    """Test BrowseSafety."""
    
    def test_check_action_safety_payment_url(self):
        """Test detecting payment URLs."""
        safety = BrowseSafety()
        
        result = safety.check_action_safety("navigate", url="https://example.com/checkout")
        
        assert result["requires_approval"] is True or result["blocked"] is True
        assert "payment" in result["reason"].lower() or "checkout" in result["reason"].lower()
    
    def test_check_action_safety_account_url(self):
        """Test detecting account modification URLs."""
        safety = BrowseSafety()
        
        result = safety.check_action_safety("navigate", url="https://example.com/account/settings")
        
        assert result["requires_approval"] is True or result["blocked"] is True
    
    def test_check_captcha(self):
        """Test CAPTCHA detection."""
        safety = BrowseSafety()
        
        html_with_captcha = '<div class="recaptcha">Verify you are human</div>'
        
        assert safety.check_captcha(html_with_captcha) is True
    
    def test_check_paywall(self):
        """Test paywall detection."""
        safety = BrowseSafety()
        
        html_with_paywall = '<div>Subscribe to continue reading</div>'
        
        assert safety.check_paywall(html_with_paywall) is True
    
    def test_redact_sensitive_data(self):
        """Test sensitive data redaction."""
        safety = BrowseSafety()
        
        data = {
            "cookies": "session=abc123",
            "headers": {
                "Authorization": "Bearer token123",
                "Content-Type": "application/json"
            },
            "url": "https://example.com?token=secret"
        }
        
        redacted = safety.redact_sensitive_data(data)
        
        assert redacted["cookies"] == "[REDACTED]"
        assert redacted["headers"]["Authorization"] == "[REDACTED]"

