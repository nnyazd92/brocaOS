"""
Tests for OpenAI API key configuration.

Tests that OPENAI_API_KEY is used when provider is OpenAI, not DEEPSEEK_API_KEY.
"""

from __future__ import annotations

import os
from unittest.mock import patch
import pytest

from broca.config import LLMConfig


class TestOpenAIAPIKeyConfiguration:
    """Test OpenAI API key is used correctly when provider is OpenAI."""
    
    def test_openai_provider_uses_openai_api_key(self):
        """
        Test that OpenAI provider uses OPENAI_API_KEY, not DEEPSEEK_API_KEY.
        
        Rationale: Ensures correct API key is used for each provider.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-openai-key-123",
            "DEEPSEEK_API_KEY": "sk-deepseek-key-456"
        }, clear=False):
            config = LLMConfig(provider="openai")
            assert config.api_key == "sk-openai-key-123"
            assert config.api_key != "sk-deepseek-key-456"
    
    def test_openai_provider_uses_openai_api_key_when_deepseek_not_set(self):
        """
        Test that OpenAI provider uses OPENAI_API_KEY even when DEEPSEEK_API_KEY is not set.
        
        Rationale: Ensures OPENAI_API_KEY is checked first.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-openai-key-789"
        }, clear=False):
            if "DEEPSEEK_API_KEY" in os.environ:
                del os.environ["DEEPSEEK_API_KEY"]
            
            config = LLMConfig(provider="openai")
            assert config.api_key == "sk-openai-key-789"
    
    def test_openai_provider_falls_back_to_deepseek_key_only_if_openai_not_set(self):
        """
        Test that DEEPSEEK_API_KEY is only used as fallback when OPENAI_API_KEY is not set.
        
        Rationale: Ensures backward compatibility while prioritizing correct key.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "openai",
            "DEEPSEEK_API_KEY": "sk-deepseek-fallback-123"
        }, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            
            config = LLMConfig(provider="openai")
            # Should fall back to DEEPSEEK_API_KEY if OPENAI_API_KEY not available
            assert config.api_key == "sk-deepseek-fallback-123"
    
    def test_deepseek_provider_uses_deepseek_api_key(self):
        """
        Test that DeepSeek provider uses DEEPSEEK_API_KEY, not OPENAI_API_KEY.
        
        Rationale: Ensures provider isolation for API keys.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "deepseek",
            "OPENAI_API_KEY": "sk-openai-key-123",
            "DEEPSEEK_API_KEY": "sk-deepseek-key-456"
        }, clear=False):
            config = LLMConfig(provider="deepseek")
            assert config.api_key == "sk-deepseek-key-456"
            assert config.api_key != "sk-openai-key-123"

