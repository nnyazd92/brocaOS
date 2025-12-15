"""
Tests for DeepSeekClient tool support.

Tests the integration of tools parameter and tool call extraction.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import httpx

from broca.llm.deepseek_client import DeepSeekClient
from broca.tests.utils import build_llm_response


class TestDeepSeekClientToolsParameter:
    """Test tools parameter in chat requests."""
    
    def test_chat_without_tools(self):
        """
        Test chat request without tools parameter.
        
        Rationale: Ensures backward compatibility when tools are not provided.
        """
        mock_httpx = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = build_llm_response(content="Response")
        mock_httpx.post.return_value = mock_response
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        messages = [{"role": "user", "content": "Hello"}]
        client.chat(messages)
        
        # Verify tools not in payload
        call_args = mock_httpx.post.call_args
        payload = call_args[1]["json"]
        assert "tools" not in payload
    
    def test_chat_with_tools(self):
        """
        Test chat request with tools parameter.
        
        Rationale: Ensures tools are included in API request when provided.
        """
        mock_httpx = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = build_llm_response(content="Response")
        mock_httpx.post.return_value = mock_response
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
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
        
        # Verify tools in payload
        call_args = mock_httpx.post.call_args
        payload = call_args[1]["json"]
        assert "tools" in payload
        assert payload["tools"] == tools
    
    def test_chat_with_tools_and_temperature(self):
        """
        Test chat request with both tools and temperature.
        
        Rationale: Ensures tools work correctly with other parameters.
        """
        mock_httpx = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = build_llm_response(content="Response")
        mock_httpx.post.return_value = mock_response
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"type": "function", "function": {"name": "test_tool"}}]
        client.chat(messages, temperature=0.5, tools=tools)
        
        call_args = mock_httpx.post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.5
        assert payload["tools"] == tools


class TestDeepSeekClientExtractToolCalls:
    """Test tool call extraction from responses."""
    
    def test_extract_tool_calls_none(self):
        """
        Test extracting tool calls when none are present.
        
        Rationale: Ensures method returns empty list when no tool calls.
        """
        response = build_llm_response(content="Regular response")
        
        tool_calls = DeepSeekClient.extract_tool_calls(response)
        
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
        
        tool_calls = DeepSeekClient.extract_tool_calls(response)
        
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
        
        tool_calls = DeepSeekClient.extract_tool_calls(response)
        
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
        tool_calls = DeepSeekClient.extract_tool_calls(response)
        assert tool_calls == []
        
        # Missing message
        response = {"choices": [{}]}
        tool_calls = DeepSeekClient.extract_tool_calls(response)
        assert tool_calls == []
        
        # Missing tool_calls key
        response = {"choices": [{"message": {"role": "assistant"}}]}
        tool_calls = DeepSeekClient.extract_tool_calls(response)
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
        
        tool_calls = DeepSeekClient.extract_tool_calls(response)
        
        assert tool_calls == []


class TestDeepSeekClientToolIntegration:
    """Test full integration of tools with chat."""
    
    def test_chat_with_tools_returns_response(self):
        """
        Test that chat with tools still returns normal response structure.
        
        Rationale: Ensures tools don't break normal response handling.
        """
        mock_httpx = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = build_llm_response(content="Response")
        mock_httpx.post.return_value = mock_response
        
        client = DeepSeekClient(api_key="test-key")
        client._client = mock_httpx
        
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"type": "function", "function": {"name": "test_tool"}}]
        response = client.chat(messages, tools=tools)
        
        assert "choices" in response
        assert len(response["choices"]) > 0
    
    def test_extract_tool_calls_from_actual_response(self):
        """
        Test extracting tool calls from actual API response format.
        
        Rationale: Ensures tool call extraction works with real response format.
        """
        response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "deepseek-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_abc123",
                                "type": "function",
                                "function": {
                                    "name": "web_search",
                                    "arguments": '{"query": "Python programming", "max_results": 5}'
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        tool_calls = DeepSeekClient.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "web_search"
        assert "query" in tool_calls[0]["function"]["arguments"]

