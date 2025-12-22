"""
Simple token estimation helper.

Uses character-based approximation (~4 chars per token) for trigger logic.
"""

from __future__ import annotations

from typing import Union, Dict, Any, List
import json


def estimate_tokens(text: Union[str, Dict[str, Any], List[Any]]) -> int:
    """
    Estimate token count from text or structured data.
    
    Uses a simple approximation: ~4 characters per token (conservative estimate
    for English text, works reasonably well for code too).
    
    Args:
        text: String, dict, or list to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if isinstance(text, (dict, list)):
        # Serialize to JSON string for structured data
        json_str = json.dumps(text, ensure_ascii=False)
        char_count = len(json_str)
    else:
        char_count = len(str(text))
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """
    Estimate total token count for a list of messages.
    
    Args:
        messages: List of message dictionaries (as used in LLM API)
        
    Returns:
        Estimated total token count
    """
    total = 0
    for msg in messages:
        # Estimate tokens for each field
        role = msg.get("role", "")
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])
        tool_call_id = msg.get("tool_call_id", "")
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def estimate_prompt_tokens(
    system_prompt: str = "",
    messages: List[Dict[str, Any]] = None,
    tools: List[Dict[str, Any]] = None
) -> int:
    """
    Estimate total prompt token count.
    
    Args:
        system_prompt: System prompt text
        messages: List of conversation messages
        tools: List of tool definitions
        
    Returns:
        Estimated total token count
    """
    total = 0
    
    total += estimate_tokens(system_prompt) if system_prompt else 0
    total += estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def truncate_tool_result(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
    """
    Truncate tool result content if too large.
    
    Preserves structure and metadata while truncating content. Keeps first 80% and
    last 10% of content with a truncation marker in between.
    
    Args:
        tool_result: Tool result dictionary with 'content' field
        max_size: Maximum size in characters for the content
        
    Returns:
        Tool result with truncated content if needed, otherwise unchanged
    """
    if not isinstance(tool_result, dict):
        return tool_result
    
    content = tool_result.get("content", "")
    if not isinstance(content, str):
        return tool_result
    
    if len(content) <= max_size:
        return tool_result
    
    # Calculate sizes for prefix and suffix
    # Keep first 80% and last 10% of max_size
    prefix_size = int(max_size * 0.8)
    suffix_size = int(max_size * 0.1)
    
    # Extract prefix and suffix
    prefix = content[:prefix_size]
    suffix = content[-suffix_size:] if len(content) > suffix_size else ""
    
    # Create truncation marker
    truncated_chars = len(content) - max_size
    truncation_marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}

