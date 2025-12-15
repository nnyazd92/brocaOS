"""
Test utilities and helper functions for Broca REPL tests.

This module provides helper functions for constructing test data,
building mock responses, and capturing log output.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from io import StringIO


def create_message_list(
    system: Optional[str] = None,
    user_messages: Optional[List[str]] = None,
    assistant_messages: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    Create a message list for testing conversation history.
    
    Args:
        system: Optional system message content
        user_messages: List of user message contents
        assistant_messages: List of assistant message contents (must match user_messages length)
    
    Returns:
        List of message dictionaries in conversation order
        
    Example:
        >>> msgs = create_message_list(
        ...     system="You are helpful",
        ...     user_messages=["Hi", "How are you?"],
        ...     assistant_messages=["Hello!", "I'm good"]
        ... )
    """
    messages: List[Dict[str, str]] = []
    
    if system:
        messages.append({"role": "system", "content": system})
    
    if user_messages:
        if assistant_messages and len(assistant_messages) != len(user_messages):
            raise ValueError("assistant_messages must match user_messages length")
        
        for i, user_msg in enumerate(user_messages):
            messages.append({"role": "user", "content": user_msg})
            if assistant_messages:
                messages.append({"role": "assistant", "content": assistant_messages[i]})
    
    return messages


def build_llm_response(
    content: str = "Test response",
    usage: Optional[Dict[str, int]] = None,
    finish_reason: str = "stop"
) -> Dict[str, Any]:
    """
    Build a mock LLM API response dictionary.
    
    Args:
        content: Assistant message content
        usage: Token usage dictionary (defaults to sample values)
        finish_reason: Finish reason for the completion
    
    Returns:
        Dictionary matching DeepSeek API response format
    """
    if usage is None:
        usage = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": finish_reason
            }
        ],
        "usage": usage
    }


def build_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """
    Build an error response structure for testing error handling.
    
    Args:
        status_code: HTTP status code
        error_message: Error message
    
    Returns:
        Dictionary representing an error response
    """
    return {
        "error": {
            "message": error_message,
            "type": "api_error",
            "code": status_code
        }
    }


class LogCapture:
    """
    Context manager for capturing log output during tests.
    
    Example:
        >>> with LogCapture() as logs:
        ...     logger.info("Test message")
        >>> assert "Test message" in logs.getvalue()
    """
    
    def __init__(self, logger_name: Optional[str] = None, level: int = logging.DEBUG):
        """
        Initialize log capture.
        
        Args:
            logger_name: Name of logger to capture (None for root logger)
            level: Log level to capture
        """
        self.logger_name = logger_name
        self.level = level
        self.stream = StringIO()
        self.handler: Optional[logging.Handler] = None
    
    def __enter__(self) -> StringIO:
        """Start capturing logs."""
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(self.level)
        formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
        self.handler.setFormatter(formatter)
        
        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.handler)
        logger.setLevel(self.level)
        
        return self.stream
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop capturing logs and clean up."""
        if self.handler:
            logger = logging.getLogger(self.logger_name)
            logger.removeHandler(self.handler)

