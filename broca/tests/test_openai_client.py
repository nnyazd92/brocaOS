"""
Unit tests for OpenAIClient.

Tests the OpenAI SDK wrapper for OpenAI API, including initialization,
API request handling, response parsing, and error handling.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
from openai import OpenAI, APIConnectionError, APITimeoutError, APIError

from broca.llm.openai_client import OpenAIClient
from broca.tests.utils import build_llm_response, create_message_list


class TestOpenAIClientInitialization:
    """Test OpenAIClient initialization with various parameter combinations."""
    
    def test_init_with_defaults(self):
        """
        Test that client initializes with config values when no parameters provided.
        
        Rationale: Ensures the client falls back to config defaults correctly.
        """
        with patch('broca.llm.openai_client.config') as mock_config:
            mock_config.llm.api_key = "test-default-key"
            mock_config.llm.api_base = "https://api.openai.com/v1"
            mock_config.llm.model = "gpt-5.2"
            mock_config.llm.temperature = 0.3
            mock_config.llm.timeout = 300.0
            
            with patch('broca.llm.openai_client.OpenAI') as mock_openai_class:
                client = OpenAIClient()
                assert client.api_key == "test-default-key"
                assert client.base_url == "https://api.openai.com/v1"
                assert client.model == "gpt-5.2"
                assert isinstance(client.temperature, float)
    
    def test_init_with_custom_parameters(self):
        """
        Test that custom parameters override config defaults.
        
        Rationale: Ensures dependency injection works correctly for testing.
        """
        with patch('broca.llm.openai_client.OpenAI') as mock_openai_class:
            client = OpenAIClient(
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
        with patch('broca.llm.openai_client.OpenAI') as mock_openai_class:
            with patch('broca.llm.openai_client.config') as mock_config:
                mock_config.llm.api_key = "default-key"
                mock_config.llm.api_base = "https://api.openai.com/v1"
                mock_config.llm.model = "gpt-5.2"
                mock_config.llm.temperature = 0.3
                mock_config.llm.timeout = 300.0
                
                client = OpenAIClient(api_key="partial-key", temperature=0.7)
                assert client.api_key == "partial-key"
                assert client.temperature == 0.7
                # Other values should come from config
                assert client.model is not None
                assert client.base_url is not None


class TestOpenAIClientChat:
    """Test the chat() method for making API requests."""
    
    def test_chat_successful_request(self):
        """
        Test successful API request with proper payload and headers.
        
        Rationale: Ensures the client constructs requests correctly and handles responses.
        """
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response(content="Test response")
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(
                api_key="test-key",
                base_url="https://api.openai.com/v1",
                model="gpt-5.2",
                temperature=0.5
            )
            
            messages = create_message_list(user_messages=["Hello"])
            response = client.chat(messages)
            
            # Verify request was made correctly
            mock_openai_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            
            assert call_kwargs["model"] == "gpt-5.2"
            assert call_kwargs["messages"] == messages
            assert call_kwargs["temperature"] == 0.5
            
            # Verify response
            assert response is not None
            assert "choices" in response
    
    def test_chat_with_custom_temperature(self):
        """
        Test that temperature parameter in chat() overrides instance temperature.
        
        Rationale: Ensures per-request temperature override works correctly.
        """
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response()
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(temperature=0.3)
            
            messages = create_message_list(user_messages=["Test"])
            client.chat(messages, temperature=0.8)
            
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.8
    
    def test_chat_api_error_handling(self):
        """
        Test that API errors are properly raised.
        
        Rationale: Ensures errors from the API are propagated correctly.
        """
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.side_effect = APIError(
            message="API Error",
            request=MagicMock(),
            body=MagicMock()
        )
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = create_message_list(user_messages=["Test"])
            
            # APIError should be re-raised
            with pytest.raises(APIError):
                client.chat(messages)
    
    def test_chat_connection_error_handling(self):
        """
        Test that connection errors are converted to ConnectionError.
        
        Rationale: Ensures network failures are converted to user-friendly exceptions.
        """
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.side_effect = APIConnectionError(
            message="Connection failed",
            request=MagicMock()
        )
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = create_message_list(user_messages=["Test"])
            
            # Connection errors should be converted to ConnectionError
            with pytest.raises(ConnectionError) as exc_info:
                client.chat(messages)
            
            assert "connection" in str(exc_info.value).lower() or "network" in str(exc_info.value).lower()


class TestExtractAssistantContent:
    """Test the extract_assistant_content() static method."""
    
    def test_extract_valid_response(self):
        """
        Test extraction of content from valid API response.
        
        Rationale: Ensures the main response parsing logic works correctly.
        """
        response = build_llm_response(content="Hello, this is a test response")
        content = OpenAIClient.extract_assistant_content(response)
        assert content == "Hello, this is a test response"
    
    def test_extract_missing_content(self):
        """
        Test handling of response with missing content field.
        
        Rationale: Ensures graceful handling of malformed responses.
        """
        response = {
            "choices": [{"message": {"role": "assistant"}}]
        }
        content = OpenAIClient.extract_assistant_content(response)
        assert content == ""
    
    def test_extract_empty_choices(self):
        """
        Test handling of response with empty choices array.
        
        Rationale: Ensures the method handles edge cases without crashing.
        """
        response = {"choices": []}
        content = OpenAIClient.extract_assistant_content(response)
        assert content == ""
    
    def test_extract_missing_choices_key(self):
        """
        Test handling of response missing choices key entirely.
        
        Rationale: Ensures robust error handling for completely malformed responses.
        """
        response = {"id": "test", "model": "test-model"}
        content = OpenAIClient.extract_assistant_content(response)
        assert content == ""
    
    def test_extract_malformed_structure(self):
        """
        Test handling of completely malformed response structure.
        
        Rationale: Ensures the method never crashes, even with invalid input.
        """
        response = {"invalid": "structure"}
        content = OpenAIClient.extract_assistant_content(response)
        assert content == ""


class TestOpenAIClientTimeout:
    """Test timeout configuration and timeout error handling."""
    
    def test_init_with_default_timeout(self):
        """
        Test that client initializes with default timeout from config.
        
        Rationale: Ensures timeout is configured from config defaults.
        """
        with patch('broca.llm.openai_client.OpenAI') as mock_openai_class:
            with patch('broca.llm.openai_client.config') as mock_config:
                mock_config.llm.timeout = 300.0
                client = OpenAIClient()
                # Verify OpenAI client was initialized with timeout
                mock_openai_class.assert_called_once()
    
    def test_init_with_custom_timeout(self):
        """
        Test that custom timeout parameter is used.
        
        Rationale: Ensures timeout can be overridden per client instance.
        """
        with patch('broca.llm.openai_client.OpenAI') as mock_openai_class:
            client = OpenAIClient(timeout=180.0)
            # Verify OpenAI client was initialized
            mock_openai_class.assert_called_once()
    
    def test_chat_timeout_error(self):
        """
        Test that APITimeoutError is caught and re-raised as TimeoutError.
        
        Rationale: Ensures timeout errors are converted to user-friendly exceptions.
        """
        mock_openai_client = MagicMock()
        # APITimeoutError takes request as first positional argument
        mock_openai_client.chat.completions.create.side_effect = APITimeoutError(
            request=MagicMock()
        )
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = create_message_list(user_messages=["Test"])
            
            with pytest.raises(TimeoutError) as exc_info:
                client.chat(messages)
            
            assert "timeout" in str(exc_info.value).lower()


class TestOpenAIClientToolsParameter:
    """Test tools parameter in chat requests."""
    
    def test_chat_without_tools(self):
        """
        Test chat request without tools parameter.
        
        Rationale: Ensures backward compatibility when tools are not provided.
        """
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response(content="Response")
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = [{"role": "user", "content": "Hello"}]
            client.chat(messages)
            
            # Verify tools not in call kwargs
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "tools" not in call_kwargs
    
    def test_chat_with_tools(self):
        """
        Test chat request with tools parameter.
        
        Rationale: Ensures tools are included in API request when provided.
        """
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response(content="Response")
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = [{"role": "user", "content": "Hello"}]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "test_tool",
                        "description": "A test tool"
                    }
                }
            ]
            client.chat(messages, tools=tools)
            
            # Verify tools in call kwargs
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "tools" in call_kwargs
            assert call_kwargs["tools"] == tools
    
    def test_chat_with_tools_and_temperature(self):
        """
        Test chat request with both tools and temperature.
        
        Rationale: Ensures tools work correctly with other parameters.
        """
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = build_llm_response(content="Response")
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = [{"role": "user", "content": "Hello"}]
            tools = [{"type": "function", "function": {"name": "test_tool"}}]
            client.chat(messages, temperature=0.5, tools=tools)
            
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["tools"] == tools


class TestOpenAIClientExtractToolCalls:
    """Test tool call extraction from responses."""
    
    def test_extract_tool_calls_none(self):
        """
        Test extracting tool calls when none are present.
        
        Rationale: Ensures method returns empty list when no tool calls.
        """
        response = build_llm_response(content="Regular response")
        
        tool_calls = OpenAIClient.extract_tool_calls(response)
        
        assert tool_calls == []
    
    def test_extract_tool_calls_single(self):
        """
        Test extracting a single tool call.
        
        Rationale: Ensures single tool calls are extracted correctly.
        """
        response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "web_search",
                                    "arguments": '{"query": "test"}'
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        tool_calls = OpenAIClient.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["id"] == "call_123"
        assert tool_calls[0]["function"]["name"] == "web_search"
    
    def test_extract_tool_calls_multiple(self):
        """
        Test extracting multiple tool calls.
        
        Rationale: Ensures multiple tool calls are extracted correctly.
        """
        response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {"name": "tool1", "arguments": "{}"}
                            },
                            {
                                "id": "call_2",
                                "type": "function",
                                "function": {"name": "tool2", "arguments": "{}"}
                            }
                        ]
                    }
                }
            ]
        }
        
        tool_calls = OpenAIClient.extract_tool_calls(response)
        
        assert len(tool_calls) == 2
        assert tool_calls[0]["id"] == "call_1"
        assert tool_calls[1]["id"] == "call_2"
    
    def test_extract_tool_calls_malformed_response(self):
        """
        Test extracting tool calls from malformed response.
        
        Rationale: Ensures method handles malformed responses gracefully.
        """
        # Missing choices
        response = {}
        tool_calls = OpenAIClient.extract_tool_calls(response)
        assert tool_calls == []
        
        # Missing message
        response = {"choices": [{}]}
        tool_calls = OpenAIClient.extract_tool_calls(response)
        assert tool_calls == []
        
        # Missing tool_calls key
        response = {"choices": [{"message": {"role": "assistant"}}]}
        tool_calls = OpenAIClient.extract_tool_calls(response)
        assert tool_calls == []
    
    def test_extract_tool_calls_empty_list(self):
        """
        Test extracting tool calls when tool_calls is empty list.
        
        Rationale: Ensures empty tool_calls list is handled correctly.
        """
        response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "tool_calls": []
                    }
                }
            ]
        }
        
        tool_calls = OpenAIClient.extract_tool_calls(response)
        
        assert tool_calls == []


class TestOpenAIClientStreaming:
    """Test streaming chat completion functionality."""
    
    def test_chat_stream_yields_chunks(self):
        """
        Test that chat_stream() yields text chunks from streaming response.
        
        Rationale: Ensures streaming functionality works correctly and yields chunks.
        """
        mock_openai_client = MagicMock()
        
        # Create mock stream chunks
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta = MagicMock()
        chunk1.choices[0].delta.content = "Hello"
        
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta = MagicMock()
        chunk2.choices[0].delta.content = " world"
        
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta = MagicMock()
        chunk3.choices[0].delta.content = "!"
        
        # Empty chunk (no content)
        chunk4 = MagicMock()
        chunk4.choices = [MagicMock()]
        chunk4.choices[0].delta = MagicMock()
        chunk4.choices[0].delta.content = None
        
        mock_openai_client.chat.completions.create.return_value = [chunk1, chunk2, chunk3, chunk4]
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = create_message_list(user_messages=["Hello"])
            chunks = list(client.chat_stream(messages))
            
            # Verify chunks were yielded
            assert chunks == ["Hello", " world", "!"]
            
            # Verify stream=True was passed
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs["stream"] is True
    
    def test_chat_stream_with_temperature(self):
        """
        Test that streaming respects temperature parameter.
        
        Rationale: Ensures temperature is correctly passed to streaming requests.
        """
        mock_openai_client = MagicMock()
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta = MagicMock()
        chunk.choices[0].delta.content = "Test"
        mock_openai_client.chat.completions.create.return_value = [chunk]
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key", temperature=0.3)
            
            messages = create_message_list(user_messages=["Test"])
            list(client.chat_stream(messages, temperature=0.8))
            
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.8
    
    def test_chat_stream_error_handling(self):
        """
        Test error handling in streaming.
        
        Rationale: Ensures streaming errors are properly raised.
        """
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.side_effect = APIError(
            message="API Error",
            request=MagicMock(),
            body=MagicMock()
        )
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = create_message_list(user_messages=["Test"])
            
            with pytest.raises(APIError):
                list(client.chat_stream(messages))
    
    def test_chat_stream_with_tools_parameter(self):
        """
        Test streaming works when tools parameter is passed.
        
        Rationale: Ensures tools parameter can be passed to streaming (even if not used in final response).
        """
        mock_openai_client = MagicMock()
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta = MagicMock()
        chunk.choices[0].delta.content = "Response"
        mock_openai_client.chat.completions.create.return_value = [chunk]
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            client = OpenAIClient(api_key="test-key")
            
            messages = create_message_list(user_messages=["Test"])
            tools = [{"type": "function", "function": {"name": "test_tool"}}]
            list(client.chat_stream(messages, tools=tools))
            
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs["tools"] == tools
            assert call_kwargs["stream"] is True
    
    def test_chat_stream_models_requiring_default_temp(self):
        """
        Test temperature handling for o1/gpt-5 models in streaming.
        
        Rationale: Ensures models that only support default temperature are handled correctly.
        """
        mock_openai_client = MagicMock()
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta = MagicMock()
        chunk.choices[0].delta.content = "Test"
        mock_openai_client.chat.completions.create.return_value = [chunk]
        
        with patch('broca.llm.openai_client.OpenAI', return_value=mock_openai_client):
            # Test with o1 model and temp=0.0 (should omit temperature)
            client = OpenAIClient(api_key="test-key", model="o1", temperature=0.0)
            
            messages = create_message_list(user_messages=["Test"])
            list(client.chat_stream(messages))
            
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert "temperature" not in call_kwargs
            
            # Test with o1 model and temp=0.5 (should include temperature)
            mock_openai_client.chat.completions.create.reset_mock()
            list(client.chat_stream(messages, temperature=0.5))
            
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.5
            
            # Test with non-o1 model and temp=0.0 (should include temperature)
            client2 = OpenAIClient(api_key="test-key", model="gpt-4", temperature=0.0)
            mock_openai_client.chat.completions.create.reset_mock()
            list(client2.chat_stream(messages))
            
            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.0

