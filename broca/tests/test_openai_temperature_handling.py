"""
Tests for OpenAI temperature parameter handling.

Some OpenAI models (like o1) don't support temperature=0.0 and require
temperature=1.0 or omitting the parameter entirely.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest

from broca.llm.openai_client import OpenAIClient
from broca.tests.utils import build_llm_response, create_message_list


class TestOpenAITemperatureHandling:
    """Test temperature parameter handling for OpenAI models."""
    
    def test_temperature_0_0_is_omitted_for_models_that_dont_support_it(self):
        """
        Test that temperature=0.0 is omitted from request for models that don't support it.
        
        Rationale: Some models (o1, gpt-5, etc.) only support default temperature (1.0).
        """
        # Test with o1 model
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(
                api_key="test-key",
                model="o1-preview",
                temperature=0.0  # This should be handled specially
            )
            
            messages = create_message_list(user_messages=["Hello"])
            client.chat(messages)
            
            # Verify temperature was omitted (not in call kwargs)
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "temperature" not in call_kwargs
        
        # Test with gpt-5 model
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(
                api_key="test-key",
                model="gpt-5.2",
                temperature=0.0  # This should also be handled specially
            )
            
            messages = create_message_list(user_messages=["Hello"])
            client.chat(messages)
            
            # Verify temperature was omitted (not in call kwargs)
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "temperature" not in call_kwargs
    
    def test_temperature_0_0_works_for_models_that_support_it(self):
        """
        Test that temperature=0.0 is included for models that support it (gpt-4, gpt-3.5, etc.).
        
        Rationale: Most models support temperature=0.0, only some special models don't.
        """
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(
                api_key="test-key",
                model="gpt-4",
                temperature=0.0
            )
            
            messages = create_message_list(user_messages=["Hello"])
            client.chat(messages)
            
            # Verify temperature was included
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "temperature" in call_kwargs
            assert call_kwargs["temperature"] == 0.0
    
    def test_temperature_0_3_works_for_all_models(self):
        """
        Test that non-zero temperatures work for all models.
        
        Rationale: Non-zero temperatures should always be included.
        """
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(
                api_key="test-key",
                model="o1-preview",
                temperature=0.3
            )
            
            messages = create_message_list(user_messages=["Hello"])
            client.chat(messages)
            
            # Verify temperature was included
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "temperature" in call_kwargs
            assert call_kwargs["temperature"] == 0.3
    
    def test_temperature_override_in_chat_method(self):
        """
        Test that temperature override in chat() method also respects model limitations.
        
        Rationale: Per-request temperature overrides should also handle model restrictions.
        """
        # Test with o1 model
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(
                api_key="test-key",
                model="o1-preview",
                temperature=0.5  # Instance default
            )
            
            messages = create_message_list(user_messages=["Hello"])
            # Override to 0.0 in chat call
            client.chat(messages, temperature=0.0)
            
            # Verify temperature was omitted (not in call kwargs)
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "temperature" not in call_kwargs
        
        # Test with gpt-5 model
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(
                api_key="test-key",
                model="gpt-5.2",
                temperature=0.5  # Instance default
            )
            
            messages = create_message_list(user_messages=["Hello"])
            # Override to 0.0 in chat call
            client.chat(messages, temperature=0.0)
            
            # Verify temperature was omitted (not in call kwargs)
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "temperature" not in call_kwargs

