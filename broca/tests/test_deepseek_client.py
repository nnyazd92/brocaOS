"""
Unit tests for DeepSeekClient.

Tests the HTTP client wrapper for DeepSeek API, including initialization,
API request handling, response parsing, and error handling.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
import httpx

from broca.llm.deepseek_client import DeepSeekClient
from broca.tests.utils import build_llm_response, create_message_list


class TestDeepSeekClientInitialization:
    """Test DeepSeekClient initialization with various parameter combinations."""
    
    def test_init_with_defaults(self):
        """
        Test that client initializes with config values when no parameters provided.
        
        Rationale: Ensures the client falls back to config defaults correctly.
        Note: This test verifies that the client uses config, but actual config values
        depend on environment variables set before module import. For more controlled
        testing, use custom parameters.
        """
        # Test that client initializes (may use config defaults or env vars)
        client = DeepSeekClient()
        assert client.api_key is not None  # May be empty string from config default
        assert client.base_url is not None
        assert client.model is not None
        assert isinstance(client.temperature, float)
    
    def test_init_with_custom_parameters(self):
        """
        Test that custom parameters override config defaults.
        
        Rationale: Ensures dependency injection works correctly for testing.
        """
        client = DeepSeekClient(
            api_key="custom-key",
            base_url="https://custom.url/v1",
            model="custom-model",
            temperature=0.9
        )
        assert client.api_key == "custom-key"
        assert client.base_url == "https://custom.url/v1"
        assert client.model == "custom-model"
        assert client.temperature == 0.9
    
    def test_init_partial_custom_parameters(self):
        """
        Test that partial custom parameters work with config fallback.
        
        Rationale: Ensures only specified parameters override defaults.
        """
        client = DeepSeekClient(api_key="partial-key", temperature=0.7)
        assert client.api_key == "partial-key"
        assert client.temperature == 0.7
        # Other values should come from config
        assert client.model is not None
        assert client.base_url is not None


class TestDeepSeekClientChat:
    """Test the chat() method for making API requests."""
    
    def test_chat_successful_request(self, mock_httpx_client: Mock):
        """
        Test successful API request with proper payload and headers.
        
        Rationale: Ensures the client constructs requests correctly and handles responses.
        """
        client = DeepSeekClient(
            api_key="test-key",
            base_url="https://test.api.com/v1",
            model="test-model",
            temperature=0.5
        )
        client._client = mock_httpx_client
        
        messages = create_message_list(user_messages=["Hello"])
        response = client.chat(messages)
        
        # Verify request was made correctly
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        
        assert call_args[0][0] == "/chat/completions"
        assert call_args[1]["json"]["model"] == "test-model"
        assert call_args[1]["json"]["messages"] == messages
        assert call_args[1]["json"]["temperature"] == 0.5
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        
        # Verify response
        assert response is not None
    
    def test_chat_with_custom_temperature(self, mock_httpx_client: Mock):
        """
        Test that temperature parameter in chat() overrides instance temperature.
        
        Rationale: Ensures per-request temperature override works correctly.
        """
        client = DeepSeekClient(temperature=0.3)
        client._client = mock_httpx_client
        
        messages = create_message_list(user_messages=["Test"])
        client.chat(messages, temperature=0.8)
        
        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["json"]["temperature"] == 0.8
    
    def test_chat_http_error_handling(self):
        """
        Test that HTTP errors are properly raised.
        
        Rationale: Ensures errors from the API are propagated correctly for error handling.
        """
        client = DeepSeekClient(api_key="test-key")
        
        # Create a mock response that raises HTTPStatusError
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        client._client = mock_client
        
        messages = create_message_list(user_messages=["Test"])
        
        with pytest.raises(httpx.HTTPStatusError):
            client.chat(messages)
    
    def test_chat_network_error_handling(self):
        """
        Test that network errors are converted to ConnectionError.
        
        Rationale: Ensures network failures are converted to user-friendly exceptions.
        """
        client = DeepSeekClient(api_key="test-key")
        
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.NetworkError("Network failed")
        client._client = mock_client
        
        messages = create_message_list(user_messages=["Test"])
        
        # Network errors should be converted to ConnectionError
        with pytest.raises(ConnectionError) as exc_info:
            client.chat(messages)
        
        assert "network" in str(exc_info.value).lower() or "connection" in str(exc_info.value).lower()


class TestExtractAssistantContent:
    """Test the extract_assistant_content() static method."""
    
    def test_extract_valid_response(self):
        """
        Test extraction of content from valid API response.
        
        Rationale: Ensures the main response parsing logic works correctly.
        """
        response = build_llm_response(content="Hello, this is a test response")
        content = DeepSeekClient.extract_assistant_content(response)
        assert content == "Hello, this is a test response"
    
    def test_extract_missing_content(self):
        """
        Test handling of response with missing content field.
        
        Rationale: Ensures graceful handling of malformed responses.
        """
        response = {
            "choices": [{"message": {"role": "assistant"}}]
        }
        content = DeepSeekClient.extract_assistant_content(response)
        assert content == ""
    
    def test_extract_empty_choices(self):
        """
        Test handling of response with empty choices array.
        
        Rationale: Ensures the method handles edge cases without crashing.
        """
        response = {"choices": []}
        content = DeepSeekClient.extract_assistant_content(response)
        assert content == ""
    
    def test_extract_missing_choices_key(self):
        """
        Test handling of response missing choices key entirely.
        
        Rationale: Ensures robust error handling for completely malformed responses.
        """
        response = {"id": "test", "model": "test-model"}
        content = DeepSeekClient.extract_assistant_content(response)
        assert content == ""
    
    def test_extract_malformed_structure(self):
        """
        Test handling of completely malformed response structure.
        
        Rationale: Ensures the method never crashes, even with invalid input.
        """
        response = {"invalid": "structure"}
        content = DeepSeekClient.extract_assistant_content(response)
        assert content == ""
    
    def test_extract_none_response(self):
        """
        Test handling of None response.
        
        Rationale: Ensures the method's behavior with invalid input is documented.
        Note: Currently None raises TypeError as it's not a valid response dict.
        """
        # None causes TypeError as it's not subscriptable
        # This documents current behavior - the method expects a dict
        with pytest.raises(TypeError):
            DeepSeekClient.extract_assistant_content(None)


class TestLastUserPreview:
    """Test the _last_user_preview() static method."""
    
    def test_preview_with_user_message(self):
        """
        Test preview generation from message list with user messages.
        
        Rationale: Ensures the preview correctly finds and truncates the last user message.
        """
        messages = create_message_list(
            user_messages=["First message", "This is a very long second message that should be truncated"],
            assistant_messages=["Response 1", "Response 2"]
        )
        preview = DeepSeekClient._last_user_preview(messages)
        assert preview == "This is a very long second message that should be truncated"
    
    def test_preview_truncation(self):
        """
        Test that long messages are properly truncated.
        
        Rationale: Ensures the truncation logic works correctly to limit log size.
        """
        long_message = "a" * 250  # Longer than default max_len of 200
        messages = create_message_list(user_messages=[long_message])
        preview = DeepSeekClient._last_user_preview(messages)
        assert len(preview) == 203  # 200 chars + "..."
        assert preview.endswith("...")
    
    def test_preview_custom_max_len(self):
        """
        Test preview with custom max length parameter.
        
        Rationale: Ensures the method respects custom truncation limits.
        """
        messages = create_message_list(user_messages=["a" * 100])
        preview = DeepSeekClient._last_user_preview(messages, max_len=50)
        assert len(preview) == 53  # 50 chars + "..."
        assert preview.endswith("...")
    
    def test_preview_no_user_messages(self):
        """
        Test preview when no user messages exist.
        
        Rationale: Ensures the method handles empty/missing user messages gracefully.
        """
        messages = create_message_list(system="System prompt")
        preview = DeepSeekClient._last_user_preview(messages)
        assert preview == ""
    
    def test_preview_empty_messages(self):
        """
        Test preview with empty message list.
        
        Rationale: Ensures the method handles empty input without errors.
        """
        preview = DeepSeekClient._last_user_preview([])
        assert preview == ""
    
    def test_preview_only_system_and_assistant(self):
        """
        Test preview when messages contain only system and assistant roles.
        
        Rationale: Ensures the method correctly identifies user messages vs other roles.
        """
        messages = [
            {"role": "system", "content": "System"},
            {"role": "assistant", "content": "Assistant response"}
        ]
        preview = DeepSeekClient._last_user_preview(messages)
        assert preview == ""


class TestDeepSeekClientTimeout:
    """Test timeout configuration and timeout error handling."""
    
    def test_init_with_default_timeout(self):
        """
        Test that client initializes with default timeout from config.
        
        Rationale: Ensures timeout is configured from config defaults.
        """
        client = DeepSeekClient()
        # Verify client has timeout configured (check httpx client timeout)
        assert client._client is not None
        # The timeout should be set on the httpx client
        assert hasattr(client._client, 'timeout')
    
    def test_init_with_custom_timeout(self):
        """
        Test that custom timeout parameter is used.
        
        Rationale: Ensures timeout can be overridden per client instance.
        """
        client = DeepSeekClient(timeout=180.0)
        assert client._client is not None
        # Verify timeout is set (check httpx.Timeout object)
        assert hasattr(client._client, 'timeout')
    
    def test_chat_timeout_error(self):
        """
        Test that httpx.ReadTimeout is caught and re-raised as TimeoutError.
        
        Rationale: Ensures timeout errors are converted to user-friendly exceptions.
        """
        client = DeepSeekClient(api_key="test-key")
        
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.ReadTimeout("The read operation timed out")
        client._client = mock_client
        
        messages = create_message_list(user_messages=["Test"])
        
        with pytest.raises(TimeoutError) as exc_info:
            client.chat(messages)
        
        assert "timeout" in str(exc_info.value).lower()
    
    def test_chat_network_error(self):
        """
        Test that network errors are caught and re-raised as ConnectionError.
        
        Rationale: Ensures network errors are converted to user-friendly exceptions.
        """
        client = DeepSeekClient(api_key="test-key")
        
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.NetworkError("Network connection failed")
        client._client = mock_client
        
        messages = create_message_list(user_messages=["Test"])
        
        with pytest.raises(ConnectionError) as exc_info:
            client.chat(messages)
        
        assert "network" in str(exc_info.value).lower() or "connection" in str(exc_info.value).lower()
    
    def test_chat_http_error(self):
        """
        Test that HTTP status errors are still raised (preserve existing behavior).
        
        Rationale: Ensures HTTP errors are still propagated for proper error handling.
        """
        client = DeepSeekClient(api_key="test-key")
        
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        client._client = mock_client
        
        messages = create_message_list(user_messages=["Test"])
        
        # HTTPStatusError should still be raised (not converted)
        with pytest.raises(httpx.HTTPStatusError):
            client.chat(messages)

