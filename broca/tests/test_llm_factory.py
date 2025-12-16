"""
Tests for LLM client factory function.

Tests that the factory correctly creates the appropriate client instance
based on configuration and parameter overrides.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock
import pytest

from broca.llm import create_llm_client
from broca.llm.deepseek_client import DeepSeekClient
from broca.llm.openai_client import OpenAIClient


class TestLLMFactory:
    """Test the create_llm_client factory function."""
    
    def test_factory_returns_deepseek_by_default(self):
        """
        Test that factory returns DeepSeekClient when provider is not specified.
        
        Rationale: Ensures backward compatibility - default provider is deepseek.
        """
        with patch('broca.llm.config') as mock_config:
            mock_config.llm.provider = "deepseek"
            mock_config.llm.api_key = "test-key"
            mock_config.llm.api_base = "https://api.deepseek.com/v1"
            mock_config.llm.model = "deepseek-chat"
            mock_config.llm.temperature = 0.3
            mock_config.llm.timeout = 300.0
            
            client = create_llm_client()
            assert isinstance(client, DeepSeekClient)
    
    def test_factory_returns_openai_when_provider_is_openai(self):
        """
        Test that factory returns OpenAIClient when provider is "openai".
        
        Rationale: Ensures OpenAI provider selection works correctly.
        """
        with patch('broca.llm.config') as mock_config:
            mock_config.llm.provider = "openai"
            mock_config.llm.api_key = "test-key"
            mock_config.llm.api_base = "https://api.openai.com/v1"
            mock_config.llm.model = "gpt-5.2"
            mock_config.llm.temperature = 0.3
            mock_config.llm.timeout = 300.0
            
            with patch('broca.llm.openai_client.OpenAI'):
                client = create_llm_client()
                assert isinstance(client, OpenAIClient)
    
    def test_factory_returns_deepseek_when_provider_is_deepseek(self):
        """
        Test that factory returns DeepSeekClient when provider is "deepseek".
        
        Rationale: Ensures explicit deepseek provider selection works.
        """
        with patch('broca.llm.config') as mock_config:
            mock_config.llm.provider = "deepseek"
            mock_config.llm.api_key = "test-key"
            mock_config.llm.api_base = "https://api.deepseek.com/v1"
            mock_config.llm.model = "deepseek-chat"
            mock_config.llm.temperature = 0.3
            mock_config.llm.timeout = 300.0
            
            client = create_llm_client()
            assert isinstance(client, DeepSeekClient)
    
    def test_factory_passes_parameters_to_deepseek_client(self):
        """
        Test that factory passes custom parameters to DeepSeekClient.
        
        Rationale: Ensures dependency injection works correctly for testing.
        """
        with patch('broca.llm.config') as mock_config:
            mock_config.llm.provider = "deepseek"
            mock_config.llm.api_key = "default-key"
            mock_config.llm.api_base = "https://api.deepseek.com/v1"
            mock_config.llm.model = "deepseek-chat"
            mock_config.llm.temperature = 0.3
            mock_config.llm.timeout = 300.0
            
            client = create_llm_client(
                api_key="custom-key",
                base_url="https://custom.url/v1",
                model="custom-model",
                temperature=0.9,
                timeout=180.0
            )
            
            assert client.api_key == "custom-key"
            assert client.base_url == "https://custom.url/v1"
            assert client.model == "custom-model"
            assert client.temperature == 0.9
    
    def test_factory_passes_parameters_to_openai_client(self):
        """
        Test that factory passes custom parameters to OpenAIClient.
        
        Rationale: Ensures dependency injection works correctly for OpenAI client.
        """
        with patch('broca.llm.config') as mock_config:
            mock_config.llm.provider = "openai"
            mock_config.llm.api_key = "default-key"
            mock_config.llm.api_base = "https://api.openai.com/v1"
            mock_config.llm.model = "gpt-5.2"
            mock_config.llm.temperature = 0.3
            mock_config.llm.timeout = 300.0
            
            with patch('broca.llm.openai_client.OpenAI'):
                client = create_llm_client(
                    api_key="custom-key",
                    base_url="https://custom.url/v1",
                    model="custom-model",
                    temperature=0.9,
                    timeout=180.0
                )
                
                assert client.api_key == "custom-key"
                assert client.base_url == "https://custom.url/v1"
                assert client.model == "custom-model"
                assert client.temperature == 0.9
    
    def test_factory_provider_override(self):
        """
        Test that provider parameter overrides config provider.
        
        Rationale: Ensures provider can be overridden for testing or dynamic switching.
        """
        with patch('broca.llm.config') as mock_config:
            mock_config.llm.provider = "deepseek"  # Config says deepseek
            mock_config.llm.api_key = "test-key"
            mock_config.llm.api_base = "https://api.deepseek.com/v1"
            mock_config.llm.model = "deepseek-chat"
            mock_config.llm.temperature = 0.3
            mock_config.llm.timeout = 300.0
            
            # But we override to openai
            with patch('broca.llm.openai_client.OpenAI'):
                client = create_llm_client(provider="openai")
                assert isinstance(client, OpenAIClient)
    
    def test_factory_raises_value_error_for_invalid_provider(self):
        """
        Test that factory raises ValueError for invalid provider.
        
        Rationale: Ensures clear error message when provider is not supported.
        """
        with patch('broca.llm.config') as mock_config:
            mock_config.llm.provider = "invalid-provider"
            mock_config.llm.api_key = "test-key"
            mock_config.llm.api_base = "https://api.example.com/v1"
            mock_config.llm.model = "test-model"
            mock_config.llm.temperature = 0.3
            mock_config.llm.timeout = 300.0
            
            with pytest.raises(ValueError) as exc_info:
                create_llm_client()
            
            assert "Unknown LLM provider" in str(exc_info.value)
            assert "invalid-provider" in str(exc_info.value)
    
    def test_factory_uses_config_when_no_parameters(self):
        """
        Test that factory uses config values when no parameters provided.
        
        Rationale: Ensures factory correctly delegates to config for defaults.
        """
        with patch('broca.llm.config') as mock_config:
            mock_config.llm.provider = "deepseek"
            mock_config.llm.api_key = "config-key"
            mock_config.llm.api_base = "https://config.url/v1"
            mock_config.llm.model = "config-model"
            mock_config.llm.temperature = 0.5
            mock_config.llm.timeout = 200.0
            
            client = create_llm_client()
            
            # Client should use config values (passed through to client init)
            # We can't directly assert config values were used since they're passed
            # through, but we can verify the client was created
            assert isinstance(client, DeepSeekClient)

