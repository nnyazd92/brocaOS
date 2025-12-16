"""
Tests for OpenAI model configuration flexibility.

Tests that users can easily swap between GPT models (e.g., gpt-5.1, gpt-5.2)
via environment variables.
"""

from __future__ import annotations

import os
from unittest.mock import patch
import pytest

from broca.config import LLMConfig


class TestOpenAIModelConfiguration:
    """Test OpenAI model can be easily configured."""
    
    def test_openai_model_defaults_to_gpt_5_2(self):
        """
        Test that OpenAI provider defaults to gpt-5.2 when no model specified.
        
        Rationale: Ensures default behavior is preserved.
        """
        with patch.dict(os.environ, {"BROCA_LLM_PROVIDER": "openai"}, clear=False):
            # Clear any model-related env vars
            env_vars_to_clear = ["OPENAI_MODEL", "BROCA_LLM_MODEL", "DEEPSEEK_MODEL"]
            original_values = {}
            for var in env_vars_to_clear:
                original_values[var] = os.environ.get(var)
                if var in os.environ:
                    del os.environ[var]
            
            try:
                # Force reload config by creating new instance
                config = LLMConfig(provider="openai")
                assert config.model == "gpt-5.2"
            finally:
                # Restore env vars
                for var, value in original_values.items():
                    if value is not None:
                        os.environ[var] = value
    
    def test_openai_model_can_be_set_via_openai_model_env_var(self):
        """
        Test that OPENAI_MODEL env var takes precedence for OpenAI provider.
        
        Rationale: Ensures dedicated OPENAI_MODEL variable works correctly.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "openai",
            "OPENAI_MODEL": "gpt-5.1"
        }, clear=False):
            config = LLMConfig(provider="openai")
            assert config.model == "gpt-5.1"
    
    def test_openai_model_falls_back_to_broca_llm_model(self):
        """
        Test that BROCA_LLM_MODEL is used when OPENAI_MODEL is not set.
        
        Rationale: Ensures backward compatibility with BROCA_LLM_MODEL.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "openai",
            "BROCA_LLM_MODEL": "gpt-4o",
            "OPENAI_MODEL": ""  # Explicitly unset
        }, clear=False):
            # Remove OPENAI_MODEL if it exists
            if "OPENAI_MODEL" in os.environ:
                del os.environ["OPENAI_MODEL"]
            
            config = LLMConfig(provider="openai")
            assert config.model == "gpt-4o"
    
    def test_openai_model_falls_back_to_deepseek_model_env_var(self):
        """
        Test that DEEPSEEK_MODEL is used as last fallback for backward compatibility.
        
        Rationale: Ensures existing DEEPSEEK_MODEL env var still works.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "openai",
            "DEEPSEEK_MODEL": "gpt-4-turbo"
        }, clear=False):
            # Remove other model env vars
            for var in ["OPENAI_MODEL", "BROCA_LLM_MODEL"]:
                if var in os.environ:
                    del os.environ[var]
            
            config = LLMConfig(provider="openai")
            assert config.model == "gpt-4-turbo"
    
    def test_openai_model_precedence_order(self):
        """
        Test that model env var precedence is: OPENAI_MODEL > BROCA_LLM_MODEL > DEEPSEEK_MODEL > default.
        
        Rationale: Ensures precedence order is correct.
        """
        # Test OPENAI_MODEL takes highest precedence
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "openai",
            "OPENAI_MODEL": "gpt-5.1",
            "BROCA_LLM_MODEL": "gpt-4o",
            "DEEPSEEK_MODEL": "gpt-4-turbo"
        }, clear=False):
            config = LLMConfig(provider="openai")
            assert config.model == "gpt-5.1"
    
    def test_can_swap_to_gpt_5_1(self):
        """
        Test that user can easily swap from gpt-5.2 to gpt-5.1.
        
        Rationale: Main use case - easy model swapping.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "openai",
            "OPENAI_MODEL": "gpt-5.1"
        }, clear=False):
            config = LLMConfig(provider="openai")
            assert config.model == "gpt-5.1"
    
    def test_can_swap_to_other_models(self):
        """
        Test that user can swap to any other OpenAI model.
        
        Rationale: Ensures flexibility for any model name.
        """
        test_models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview"]
        
        for model_name in test_models:
            with patch.dict(os.environ, {
                "BROCA_LLM_PROVIDER": "openai",
                "OPENAI_MODEL": model_name
            }, clear=False):
                config = LLMConfig(provider="openai")
                assert config.model == model_name
    
    def test_deepseek_provider_not_affected_by_openai_model(self):
        """
        Test that OPENAI_MODEL doesn't affect DeepSeek provider.
        
        Rationale: Ensures provider isolation.
        """
        with patch.dict(os.environ, {
            "BROCA_LLM_PROVIDER": "deepseek",
            "OPENAI_MODEL": "gpt-5.1",
            "DEEPSEEK_MODEL": "deepseek-chat"
        }, clear=False):
            config = LLMConfig(provider="deepseek")
            assert config.model == "deepseek-chat"

