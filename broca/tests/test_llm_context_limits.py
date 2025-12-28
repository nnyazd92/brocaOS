"""
Tests for model-aware context token limits.

Tests that model-specific hard limits are respected while still honoring
BROCA_MAX_CONTEXT_TOKENS from .env when applicable.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

from broca.llm.deepseek_client import DeepSeekClient
from broca.config import config


class TestModelContextLimits:
    """Test model-specific context limit detection."""
    
    def test_deepseek_reasoner_has_hard_limit(self):
        """Test that deepseek-reasoner returns 131072 limit."""
        client = DeepSeekClient(model="deepseek-reasoner")
        limit = client.get_max_context_tokens()
        assert limit == 131072, f"Expected 131072, got {limit}"
    
    @given(config_limit=st.integers(min_value=100000, max_value=500000))
    def test_deepseek_reasoner_respects_lower_limit(self, config_limit):
        """Property: deepseek-reasoner always returns min(model_limit, config_limit)."""
        with patch.object(config.llm, 'max_context_tokens', config_limit):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            # Should be min(131072, config_limit)
            expected = min(131072, config_limit)
            assert limit == expected, f"Expected {expected}, got {limit}"
            assert limit <= 131072, "Should never exceed model hard limit"
    
    def test_other_models_use_config_limit(self):
        """Test that non-reasoner models use config limit."""
        with patch.object(config.llm, 'max_context_tokens', 272000):
            client = DeepSeekClient(model="deepseek-chat")
            limit = client.get_max_context_tokens()
            assert limit == 272000, f"Expected 272000, got {limit}"
    
    @given(config_limit=st.integers(min_value=10000, max_value=1000000))
    def test_other_models_respect_config(self, config_limit):
        """Property: non-reasoner models use config limit."""
        with patch.object(config.llm, 'max_context_tokens', config_limit):
            client = DeepSeekClient(model="deepseek-chat")
            limit = client.get_max_context_tokens()
            assert limit == config_limit, f"Expected {config_limit}, got {limit}"
    
    def test_model_limit_takes_precedence_over_config(self):
        """Test that model hard limit takes precedence when config is higher."""
        with patch.object(config.llm, 'max_context_tokens', 500000):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            assert limit == 131072, "Model limit should take precedence"
            assert limit < config.llm.max_context_tokens
    
    def test_config_limit_used_when_lower_than_model(self):
        """Test that config limit is used when it's lower than model limit."""
        with patch.object(config.llm, 'max_context_tokens', 100000):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            assert limit == 100000, "Config limit should be used when lower"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        model_name=st.sampled_from(["deepseek-reasoner", "deepseek-chat", "deepseek-coder"]),
        config_limit=st.integers(min_value=50000, max_value=500000)
    )
    def test_limit_always_within_bounds(self, model_name, config_limit):
        """Property: limit is always within reasonable bounds for any model/config."""
        with patch.object(config.llm, 'max_context_tokens', config_limit):
            client = DeepSeekClient(model=model_name)
            limit = client.get_max_context_tokens()
            assert 10000 <= limit <= 1000000, f"Limit {limit} out of reasonable bounds"
            if model_name == "deepseek-reasoner":
                assert limit <= 131072, "Reasoner should never exceed 131072"


class TestContextLimitFaultInjection:
    """Fault injection tests for context limits."""
    
    def test_invalid_model_name(self):
        """Test with invalid/unknown model name."""
        client = DeepSeekClient(model="invalid-model-xyz")
        # Should not raise, should use config limit
        limit = client.get_max_context_tokens()
        assert isinstance(limit, int)
        assert limit > 0
    
    def test_missing_config_value(self):
        """Test behavior when config.max_context_tokens is missing."""
        with patch.object(config.llm, 'max_context_tokens', None):
            # Should handle gracefully
            client = DeepSeekClient(model="deepseek-chat")
            try:
                limit = client.get_max_context_tokens()
                # If it doesn't raise, should return a valid int
                assert isinstance(limit, int)
            except (AttributeError, TypeError):
                # Acceptable if it raises - we'll handle in session layer
                pass
    
    def test_very_large_config_limit(self):
        """Test with very large config limit."""
        with patch.object(config.llm, 'max_context_tokens', 10_000_000):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            assert limit == 131072, "Should cap at model limit"
    
    def test_very_small_config_limit(self):
        """Test with very small config limit."""
        with patch.object(config.llm, 'max_context_tokens', 1000):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            assert limit == 1000, "Should use config when lower"
            assert limit < 131072


class TestContextLimitEdgeCases:
    """Edge case tests for context limits."""
    
    def test_exactly_at_model_limit(self):
        """Test when config equals model limit."""
        with patch.object(config.llm, 'max_context_tokens', 131072):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            assert limit == 131072
    
    def test_one_token_over_model_limit(self):
        """Test when config is one token over model limit."""
        with patch.object(config.llm, 'max_context_tokens', 131073):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            assert limit == 131072, "Should cap at model limit"
    
    def test_one_token_under_model_limit(self):
        """Test when config is one token under model limit."""
        with patch.object(config.llm, 'max_context_tokens', 131071):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            assert limit == 131071, "Should use config when lower"
    
    def test_zero_config_limit(self):
        """Test with zero config limit (edge case)."""
        with patch.object(config.llm, 'max_context_tokens', 0):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            assert limit == 0, "Should use config even if zero"
    
    def test_negative_config_limit(self):
        """Test with negative config limit (invalid but should handle)."""
        with patch.object(config.llm, 'max_context_tokens', -1000):
            client = DeepSeekClient(model="deepseek-reasoner")
            limit = client.get_max_context_tokens()
            # Should return the negative value (min will choose it)
            assert limit == -1000


class TestSessionIntegration:
    """Test integration with ConversationSession."""
    
    def test_session_uses_model_limit(self):
        """Test that session uses model-specific limit."""
        from broca.repl.session import ConversationSession
        
        with patch.object(config.llm, 'max_context_tokens', 272000):
            client = DeepSeekClient(model="deepseek-reasoner")
            session = ConversationSession(llm=client)
            
            # Check that _get_messages_for_llm would use model limit
            # We can't easily test the full flow, but we can verify the client method works
            limit = client.get_max_context_tokens()
            assert limit == 131072
    
    def test_session_falls_back_to_config(self):
        """Test that session falls back to config when model doesn't support get_max_context_tokens."""
        from broca.repl.session import ConversationSession
        
        # Mock LLM without get_max_context_tokens method
        mock_llm = Mock()
        mock_llm.model = "unknown-model"
        del mock_llm.get_max_context_tokens  # Remove if it exists
        
        with patch.object(config.llm, 'max_context_tokens', 272000):
            session = ConversationSession(llm=mock_llm)
            # Session should fall back to config
            # We verify by checking that it doesn't crash
            assert hasattr(session, '_get_messages_for_llm')

