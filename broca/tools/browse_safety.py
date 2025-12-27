"""
Browse Safety - Safety checks and governance.

Detects and blocks unsafe actions like purchases, account modifications,
and credential entry.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse

from ..config import config

logger = logging.getLogger(__name__)


class BrowseSafety:
    """Safety checks for browse operations."""
    
    def __init__(self) -> None:
        """Initialize safety checker."""
        self._safety_config = config.browse.safety
        
        # Patterns for unsafe actions
        self._payment_patterns = [
            r"checkout",
            r"cart",
            r"payment",
            r"purchase",
            r"buy",
            r"order",
            r"billing",
            r"credit.?card",
            r"paypal",
            r"stripe"
        ]
        
        self._account_patterns = [
            r"account",
            r"profile",
            r"settings",
            r"password",
            r"change",
            r"update",
            r"delete.*account",
            r"close.*account"
        ]
        
        self._credential_patterns = [
            r"login",
            r"sign.?in",
            r"authenticate",
            r"password",
            r"credential"
        ]
        
        logger.info("Initialized BrowseSafety")
    
    def check_action_safety(
        self,
        action_type: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        form_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if an action is safe to perform.
        
        Args:
            action_type: Type of action ("navigate", "click", "fill", "submit")
            url: URL being accessed
            selector: CSS selector (for form analysis)
            form_data: Form data being submitted
            
        Returns:
            Dictionary with safety check result:
            {
                "safe": bool,
                "blocked": bool,
                "reason": str,
                "requires_approval": bool
            }
        """
        result = {
            "safe": True,
            "blocked": False,
            "reason": "",
            "requires_approval": False
        }
        
        # Check URL patterns
        if url:
            url_lower = url.lower()
            
            # Check for payment/checkout
            if any(re.search(pattern, url_lower) for pattern in self._payment_patterns):
                if self._safety_config.require_approval_for_purchases:
                    result["safe"] = False
                    result["requires_approval"] = True
                    result["reason"] = "Payment/checkout URL detected"
                    return result
                else:
                    result["blocked"] = True
                    result["reason"] = "Payment/checkout blocked by safety policy"
                    return result
            
            # Check for account modifications
            if any(re.search(pattern, url_lower) for pattern in self._account_patterns):
                if self._safety_config.require_approval_for_account_changes:
                    result["safe"] = False
                    result["requires_approval"] = True
                    result["reason"] = "Account modification URL detected"
                    return result
                else:
                    result["blocked"] = True
                    result["reason"] = "Account modification blocked by safety policy"
                    return result
        
        # Check form data for unsafe fields
        if form_data:
            form_lower = str(form_data).lower()
            
            # Check for payment fields
            payment_fields = ["card", "cvv", "expiry", "billing", "payment"]
            if any(field in form_lower for field in payment_fields):
                if self._safety_config.require_approval_for_purchases:
                    result["safe"] = False
                    result["requires_approval"] = True
                    result["reason"] = "Payment form detected"
                    return result
                else:
                    result["blocked"] = True
                    result["reason"] = "Payment form blocked by safety policy"
                    return result
            
            # Check for password fields
            if "password" in form_lower:
                domain = self._extract_domain(url) if url else ""
                
                if not self._safety_config.allow_credential_entry:
                    result["blocked"] = True
                    result["reason"] = "Credential entry blocked by safety policy"
                    return result
                
                # Check if domain is in allowlist
                if domain not in self._safety_config.allowed_login_domains:
                    result["safe"] = False
                    result["requires_approval"] = True
                    result["reason"] = f"Login form detected for domain not in allowlist: {domain}"
                    return result
        
        return result
    
    def check_captcha(self, page_content: str) -> bool:
        """
        Detect if page contains a CAPTCHA.
        
        Args:
            page_content: HTML content or text
            
        Returns:
            True if CAPTCHA detected
        """
        captcha_indicators = [
            "captcha",
            "recaptcha",
            "hcaptcha",
            "cloudflare",
            "verify you are human",
            "i'm not a robot"
        ]
        
        content_lower = page_content.lower()
        return any(indicator in content_lower for indicator in captcha_indicators)
    
    def check_paywall(self, page_content: str) -> bool:
        """
        Detect if page has a paywall.
        
        Args:
            page_content: HTML content or text
            
        Returns:
            True if paywall detected
        """
        paywall_indicators = [
            "subscribe",
            "paywall",
            "premium content",
            "members only",
            "sign up to continue",
            "free article limit"
        ]
        
        content_lower = page_content.lower()
        return any(indicator in content_lower for indicator in paywall_indicators)
    
    def check_anti_bot(self, page_content: str, url: str) -> bool:
        """
        Detect if page has anti-bot protection.
        
        Args:
            page_content: HTML content or text
            url: URL of the page
            
        Returns:
            True if anti-bot protection detected
        """
        # Check for empty or minimal content (common anti-bot pattern)
        if len(page_content.strip()) < 100:
            return True
        
        # Check for redirect loops
        if "redirect" in page_content.lower() and "location" in page_content.lower():
            return True
        
        # Check for Cloudflare challenge
        if "cloudflare" in page_content.lower() and "challenge" in page_content.lower():
            return True
        
        return False
    
    def redact_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive data from logs.
        
        Args:
            data: Data dictionary to redact
            
        Returns:
            Redacted data dictionary
        """
        if not self._safety_config.redact_sensitive_data:
            return data
        
        redacted = data.copy()
        
        # Redact cookies
        if "cookies" in redacted:
            redacted["cookies"] = "[REDACTED]"
        
        # Redact auth headers
        if "headers" in redacted:
            headers = redacted["headers"].copy()
            for key in list(headers.keys()):
                if key.lower() in ["authorization", "x-api-key", "cookie"]:
                    headers[key] = "[REDACTED]"
            redacted["headers"] = headers
        
        # Redact tokens in URLs
        if "url" in redacted:
            url = redacted["url"]
            # Remove query parameters that might contain tokens
            parsed = urlparse(url)
            if parsed.query:
                # Keep structure but redact values
                redacted["url"] = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?[REDACTED]"
        
        # Redact form values with sensitive patterns
        if "form_data" in redacted:
            form_data = redacted["form_data"].copy()
            sensitive_fields = ["password", "token", "key", "secret", "auth"]
            for key in list(form_data.keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    form_data[key] = "[REDACTED]"
            redacted["form_data"] = form_data
        
        return redacted
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""

