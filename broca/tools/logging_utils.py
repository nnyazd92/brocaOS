"""
Logging utilities for tool call logging.

Provides helper functions for consistent, structured logging of tool calls
with proper truncation and formatting.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from ..config import config

logger = logging.getLogger(__name__)

# Default truncation limits
DEFAULT_MAX_STRING_LENGTH = 1000
DEFAULT_MAX_LIST_ITEMS = 100
DEFAULT_MAX_DICT_ITEMS = 50


def truncate_for_logging(data: Any, max_string_length: int = DEFAULT_MAX_STRING_LENGTH) -> Any:
    """
    Truncate data structures for logging to prevent unwieldy logs.
    
    Args:
        data: Data to truncate (string, list, dict, or other)
        max_string_length: Maximum length for strings
        
    Returns:
        Truncated data structure
    """
    if isinstance(data, str):
        if len(data) > max_string_length:
            return data[:max_string_length] + f"... (truncated, {len(data)} total chars)"
        return data
    
    if isinstance(data, list):
        if len(data) > DEFAULT_MAX_LIST_ITEMS:
            truncated = data[:DEFAULT_MAX_LIST_ITEMS]
            return truncated + [f"... (truncated, {len(data)} total items)"]
        return data
    
    if isinstance(data, dict):
        if len(data) > DEFAULT_MAX_DICT_ITEMS:
            items = list(data.items())[:DEFAULT_MAX_DICT_ITEMS]
            truncated = dict(items)
            truncated["..."] = f"truncated, {len(data)} total keys"
            return truncated
        return data
    
    # For other types, convert to string and truncate
    data_str = str(data)
    if len(data_str) > max_string_length:
        return data_str[:max_string_length] + "... (truncated)"
    return data


def log_tool_call_received(tool_call: Dict[str, Any], logger_instance: logging.Logger = None) -> None:
    """
    Log that a tool call was received from the LLM.
    
    Args:
        tool_call: Raw tool call dictionary from LLM
        logger_instance: Optional logger instance (defaults to module logger)
    """
    log = logger_instance or logger
    
    function_info = tool_call.get("function", {})
    tool_name = function_info.get("name", "unknown")
    tool_call_id = tool_call.get("id", "")
    arguments_str = function_info.get("arguments", "{}")
    
    # Parse arguments for logging (may fail, that's OK)
    try:
        arguments = json.loads(arguments_str) if arguments_str else {}
        arguments_log = truncate_for_logging(arguments) if not config.logging.log_tool_results_full else arguments
    except (json.JSONDecodeError, TypeError):
        arguments_log = arguments_str[:200] if len(arguments_str) > 200 else arguments_str
    
    log.info(
        f"Tool call received: {tool_name}",
        extra={
            "event": "tool_call_received",
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "arguments": arguments_log,
            "raw_tool_call": tool_call if config.logging.level == "DEBUG" else None
        }
    )


def log_tool_execution_start(
    tool_name: str,
    arguments: Dict[str, Any],
    tool_call_id: str = "",
    logger_instance: logging.Logger = None
) -> None:
    """
    Log that tool execution is starting.
    
    Args:
        tool_name: Name of the tool being executed
        arguments: Parsed tool arguments
        tool_call_id: Tool call ID from LLM
        logger_instance: Optional logger instance (defaults to module logger)
    """
    log = logger_instance or logger
    
    arguments_log = truncate_for_logging(arguments) if not config.logging.log_tool_results_full else arguments
    
    log.info(
        f"Executing tool: {tool_name}",
        extra={
            "event": "tool_call_executing",
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "arguments": arguments_log
        }
    )


def log_tool_result(
    tool_name: str,
    result: Dict[str, Any],
    formatted_result: str,
    tool_call_id: str = "",
    execution_time_ms: float = 0.0,
    logger_instance: logging.Logger = None
) -> None:
    """
    Log tool execution result.
    
    Args:
        tool_name: Name of the tool that was executed
        result: Raw tool result dictionary
        formatted_result: Formatted result string sent to LLM
        tool_call_id: Tool call ID from LLM
        execution_time_ms: Execution duration in milliseconds
        logger_instance: Optional logger instance (defaults to module logger)
    """
    log = logger_instance or logger
    
    # Truncate results unless full logging is enabled
    result_log = result if config.logging.log_tool_results_full else truncate_for_logging(result)
    formatted_log = (
        formatted_result
        if config.logging.log_tool_results_full or len(formatted_result) <= DEFAULT_MAX_STRING_LENGTH
        else formatted_result[:DEFAULT_MAX_STRING_LENGTH] + f"... (truncated, {len(formatted_result)} total chars)"
    )
    
    log.info(
        f"Tool execution completed: {tool_name}",
        extra={
            "event": "tool_call_result",
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "result": result_log,
            "formatted_result": formatted_log,
            "execution_time_ms": execution_time_ms
        }
    )

