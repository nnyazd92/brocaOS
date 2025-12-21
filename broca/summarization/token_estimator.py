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

