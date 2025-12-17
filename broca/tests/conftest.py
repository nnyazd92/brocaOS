"""
Pytest configuration and shared fixtures for Broca REPL tests.

This module provides reusable fixtures for mocking external dependencies
and creating test data structures.
"""

from __future__ import annotations

import os
import tempfile
from typing import Dict, Any, Generator
from unittest.mock import Mock, MagicMock

import pytest

from broca.llm.deepseek_client import DeepSeekClient


@pytest.fixture
def mock_llm_response() -> Dict[str, Any]:
    """
    Standard mock response structure from DeepSeek API.
    
    Returns a dictionary matching the expected API response format.
    """
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from the LLM."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    }


@pytest.fixture
def mock_llm_client(mock_llm_response: Dict[str, Any]) -> Mock:
    """
    Mock DeepSeekClient that returns predictable responses.
    
    The mock's chat() method returns the mock_llm_response fixture,
    and extract_assistant_content() works with the standard response format.
    """
    mock_client = Mock(spec=DeepSeekClient)
    mock_client.chat.return_value = mock_llm_response
    mock_client.extract_assistant_content = DeepSeekClient.extract_assistant_content
    return mock_client


@pytest.fixture
def sample_messages() -> list[Dict[str, str]]:
    """
    Sample message list for testing conversation history.
    
    Includes system, user, and assistant messages in a typical conversation pattern.
    """
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "What is 2+2?"}
    ]


@pytest.fixture
def temp_log_file() -> Generator[str, None, None]:
    """
    Temporary log file fixture for isolated logging tests.
    
    Creates a temporary file and cleans it up after the test completes.
    Yields the file path.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def mock_httpx_client() -> Mock:
    """
    Mock httpx.Client for testing HTTP requests without making real calls.
    
    Returns a mock that can be configured to return specific responses
    for POST requests to /chat/completions.
    """
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Mocked response"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    }
    mock_response.raise_for_status = Mock()  # Callable that does nothing
    mock_client.post.return_value = mock_response
    return mock_client


@pytest.fixture
def env_vars_override(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Fixture to temporarily override environment variables for config testing.
    
    Cleans up environment variables after test completion to ensure test isolation.
    """
    # Save original values
    original_env = {}
    env_keys = [
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_API_BASE",
        "DEEPSEEK_MODEL",
        "DEEPSEEK_TEMPERATURE",
        "BROCA_LOG_LEVEL",
        "BROCA_LOG_FILE"
    ]
    
    for key in env_keys:
        original_env[key] = os.environ.get(key)
        if key in os.environ:
            monkeypatch.delenv(key, raising=False)
    
    yield
    
    # Restore original values
    for key, value in original_env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


@pytest.fixture
def normal_tools_mode(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Fixture to ensure tools run in normal mode for tests.
    
    Sets BROCA_TOOLS_MODE to "normal" to allow tool execution and validation.
    This is needed because some tests may run in environments where read_only mode is set.
    """
    monkeypatch.setenv("BROCA_TOOLS_MODE", "normal")
    yield

