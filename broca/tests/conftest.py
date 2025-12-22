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
    mock_client.extract_tool_calls = DeepSeekClient.extract_tool_calls
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


# Summarizer test fixtures

@pytest.fixture
def sample_events() -> list[Dict[str, Any]]:
    """
    Sample event list for summarizer testing.
    
    Returns a list of typical conversation events with event_ids.
    """
    return [
        {"event_id": "evt_1", "type": "user_message", "content": "Hello, I need help with Python"},
        {"event_id": "evt_2", "type": "assistant_message", "content": "I'd be happy to help! What do you need?"},
        {"event_id": "evt_3", "type": "tool_call", "tool_name": "code_search", "tool_args": {"query": "python function"}},
        {"event_id": "evt_4", "type": "tool_result", "tool_name": "code_search", "tool_result": {"results": ["func1", "func2"]}},
        {"event_id": "evt_5", "type": "user_message", "content": "Thank you!"}
    ]


@pytest.fixture
def large_event_list() -> list[Dict[str, Any]]:
    """
    Large event list for testing with many events.
    
    Returns a list of 50+ events for stress testing.
    """
    events = []
    for i in range(50):
        events.append({
            "event_id": f"evt_{i}",
            "type": "user_message" if i % 2 == 0 else "assistant_message",
            "content": f"Message {i}: " + "x" * 100  # Long content
        })
    return events


@pytest.fixture
def minimal_summary_dict() -> Dict[str, Any]:
    """
    Minimal valid summary dictionary.
    
    Returns the smallest valid summary structure for testing.
    """
    return {
        "summary_patch": {
            "current_goal": "Test goal",
            "what_we_built": [],
            "open_questions": [],
            "constraints": [],
            "next_steps": []
        },
        "extracted": {},
        "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
    }


@pytest.fixture
def large_summary_dict() -> Dict[str, Any]:
    """
    Large summary dictionary for testing token limits.
    
    Returns a summary that exceeds typical token limits.
    """
    large_text = "x" * 5000  # Very long text
    return {
        "summary_patch": {
            "current_goal": large_text,
            "what_we_built": [large_text[:1000]] * 20,
            "open_questions": [large_text[:1000]] * 20,
            "constraints": [large_text[:1000]] * 10,
            "next_steps": [large_text[:1000]] * 20
        },
        "extracted": {
            "facts_added": [
                {"text": large_text[:500], "confidence": "high", "event_ids": [f"evt_{i}"]}
                for i in range(30)
            ],
            "decisions_added": [
                {"text": large_text[:500], "reasoning": large_text[:500], "event_ids": [f"evt_{i}"]}
                for i in range(30, 40)
            ],
            "tasks_added": [
                {"id": f"task_{i}", "description": large_text[:500], "event_ids": [f"evt_{i}"]}
                for i in range(40, 50)
            ]
        },
        "bookkeeping": {"new_last_summarized_event_id": "evt_50"}
    }


@pytest.fixture
def mock_llm_response_json() -> Dict[str, Any]:
    """
    Mock LLM response as JSON string content.
    
    Returns a typical summary response that an LLM would return.
    """
    return {
        "summary_patch": {
            "current_goal": "Implement comprehensive testing",
            "what_we_built": ["Test framework", "Mock fixtures"],
            "open_questions": ["Should we add more tests?"],
            "constraints": ["Must maintain backward compatibility"],
            "next_steps": ["Run mutation testing", "Check coverage"]
        },
        "extracted": {
            "facts_added": [
                {"text": "Testing is important", "confidence": "high", "event_ids": ["evt_1", "evt_2"]}
            ],
            "decisions_added": [
                {"text": "Use TDD approach", "reasoning": "Better code quality", "event_ids": ["evt_3"]}
            ],
            "tasks_added": [
                {"id": "task_1", "description": "Write tests", "event_ids": ["evt_4"]}
            ]
        },
        "bookkeeping": {"new_last_summarized_event_id": "evt_5"}
    }


@pytest.fixture
def mock_llm_response_markdown() -> str:
    """
    Mock LLM response wrapped in markdown code blocks.
    
    Returns a JSON response wrapped in ```json code fences.
    """
    json_content = {
        "summary_patch": {"current_goal": "Test goal"},
        "extracted": {},
        "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
    }
    import json
    return f"```json\n{json.dumps(json_content)}\n```"


@pytest.fixture
def mock_llm_response_with_trailing() -> str:
    """
    Mock LLM response with trailing text after JSON.
    
    Returns a JSON response followed by explanatory text.
    """
    json_content = {
        "summary_patch": {"current_goal": "Test goal"},
        "extracted": {},
        "bookkeeping": {"new_last_summarized_event_id": "evt_1"}
    }
    import json
    return json.dumps(json_content) + "\n\nThis is a valid JSON response above."

