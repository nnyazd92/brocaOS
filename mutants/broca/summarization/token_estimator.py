"""
Simple token estimation helper.

Uses character-based approximation (~4 chars per token) for trigger logic.
"""

from __future__ import annotations

from typing import Union, Dict, Any, List
import json
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


def x_estimate_tokens__mutmut_orig(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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


def x_estimate_tokens__mutmut_1(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
        json_str = None
        char_count = len(json_str)
    else:
        char_count = len(str(text))
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_2(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
        json_str = json.dumps(None, ensure_ascii=False)
        char_count = len(json_str)
    else:
        char_count = len(str(text))
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_3(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
        json_str = json.dumps(text, ensure_ascii=None)
        char_count = len(json_str)
    else:
        char_count = len(str(text))
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_4(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
        json_str = json.dumps(ensure_ascii=False)
        char_count = len(json_str)
    else:
        char_count = len(str(text))
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_5(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
        json_str = json.dumps(text, )
        char_count = len(json_str)
    else:
        char_count = len(str(text))
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_6(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
        json_str = json.dumps(text, ensure_ascii=True)
        char_count = len(json_str)
    else:
        char_count = len(str(text))
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_7(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
        char_count = None
    else:
        char_count = len(str(text))
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_8(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
        char_count = None
    
    # Approximate: ~4 chars per token (conservative)
    return (char_count + 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_9(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
    return (char_count + 3) / 4  # Ceiling division


def x_estimate_tokens__mutmut_10(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
    return (char_count - 3) // 4  # Ceiling division


def x_estimate_tokens__mutmut_11(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
    return (char_count + 4) // 4  # Ceiling division


def x_estimate_tokens__mutmut_12(text: Union[str, Dict[str, Any], List[Any]]) -> int:
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
    return (char_count + 3) // 5  # Ceiling division

x_estimate_tokens__mutmut_mutants : ClassVar[MutantDict] = {
'x_estimate_tokens__mutmut_1': x_estimate_tokens__mutmut_1, 
    'x_estimate_tokens__mutmut_2': x_estimate_tokens__mutmut_2, 
    'x_estimate_tokens__mutmut_3': x_estimate_tokens__mutmut_3, 
    'x_estimate_tokens__mutmut_4': x_estimate_tokens__mutmut_4, 
    'x_estimate_tokens__mutmut_5': x_estimate_tokens__mutmut_5, 
    'x_estimate_tokens__mutmut_6': x_estimate_tokens__mutmut_6, 
    'x_estimate_tokens__mutmut_7': x_estimate_tokens__mutmut_7, 
    'x_estimate_tokens__mutmut_8': x_estimate_tokens__mutmut_8, 
    'x_estimate_tokens__mutmut_9': x_estimate_tokens__mutmut_9, 
    'x_estimate_tokens__mutmut_10': x_estimate_tokens__mutmut_10, 
    'x_estimate_tokens__mutmut_11': x_estimate_tokens__mutmut_11, 
    'x_estimate_tokens__mutmut_12': x_estimate_tokens__mutmut_12
}

def estimate_tokens(*args, **kwargs):
    result = _mutmut_trampoline(x_estimate_tokens__mutmut_orig, x_estimate_tokens__mutmut_mutants, args, kwargs)
    return result 

estimate_tokens.__signature__ = _mutmut_signature(x_estimate_tokens__mutmut_orig)
x_estimate_tokens__mutmut_orig.__name__ = 'x_estimate_tokens'


def x_estimate_messages_tokens__mutmut_orig(messages: List[Dict[str, Any]]) -> int:
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


def x_estimate_messages_tokens__mutmut_1(messages: List[Dict[str, Any]]) -> int:
    """
    Estimate total token count for a list of messages.
    
    Args:
        messages: List of message dictionaries (as used in LLM API)
        
    Returns:
        Estimated total token count
    """
    total = None
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


def x_estimate_messages_tokens__mutmut_2(messages: List[Dict[str, Any]]) -> int:
    """
    Estimate total token count for a list of messages.
    
    Args:
        messages: List of message dictionaries (as used in LLM API)
        
    Returns:
        Estimated total token count
    """
    total = 1
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


def x_estimate_messages_tokens__mutmut_3(messages: List[Dict[str, Any]]) -> int:
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
        role = None
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


def x_estimate_messages_tokens__mutmut_4(messages: List[Dict[str, Any]]) -> int:
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
        role = msg.get(None, "")
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


def x_estimate_messages_tokens__mutmut_5(messages: List[Dict[str, Any]]) -> int:
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
        role = msg.get("role", None)
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


def x_estimate_messages_tokens__mutmut_6(messages: List[Dict[str, Any]]) -> int:
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
        role = msg.get("")
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


def x_estimate_messages_tokens__mutmut_7(messages: List[Dict[str, Any]]) -> int:
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
        role = msg.get("role", )
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


def x_estimate_messages_tokens__mutmut_8(messages: List[Dict[str, Any]]) -> int:
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
        role = msg.get("XXroleXX", "")
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


def x_estimate_messages_tokens__mutmut_9(messages: List[Dict[str, Any]]) -> int:
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
        role = msg.get("ROLE", "")
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


def x_estimate_messages_tokens__mutmut_10(messages: List[Dict[str, Any]]) -> int:
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
        role = msg.get("role", "XXXX")
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


def x_estimate_messages_tokens__mutmut_11(messages: List[Dict[str, Any]]) -> int:
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
        content = None
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


def x_estimate_messages_tokens__mutmut_12(messages: List[Dict[str, Any]]) -> int:
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
        content = msg.get(None, "")
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


def x_estimate_messages_tokens__mutmut_13(messages: List[Dict[str, Any]]) -> int:
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
        content = msg.get("content", None)
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


def x_estimate_messages_tokens__mutmut_14(messages: List[Dict[str, Any]]) -> int:
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
        content = msg.get("")
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


def x_estimate_messages_tokens__mutmut_15(messages: List[Dict[str, Any]]) -> int:
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
        content = msg.get("content", )
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


def x_estimate_messages_tokens__mutmut_16(messages: List[Dict[str, Any]]) -> int:
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
        content = msg.get("XXcontentXX", "")
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


def x_estimate_messages_tokens__mutmut_17(messages: List[Dict[str, Any]]) -> int:
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
        content = msg.get("CONTENT", "")
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


def x_estimate_messages_tokens__mutmut_18(messages: List[Dict[str, Any]]) -> int:
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
        content = msg.get("content", "XXXX")
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


def x_estimate_messages_tokens__mutmut_19(messages: List[Dict[str, Any]]) -> int:
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
        tool_calls = None
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


def x_estimate_messages_tokens__mutmut_20(messages: List[Dict[str, Any]]) -> int:
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
        tool_calls = msg.get(None, [])
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


def x_estimate_messages_tokens__mutmut_21(messages: List[Dict[str, Any]]) -> int:
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
        tool_calls = msg.get("tool_calls", None)
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


def x_estimate_messages_tokens__mutmut_22(messages: List[Dict[str, Any]]) -> int:
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
        tool_calls = msg.get([])
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


def x_estimate_messages_tokens__mutmut_23(messages: List[Dict[str, Any]]) -> int:
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
        tool_calls = msg.get("tool_calls", )
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


def x_estimate_messages_tokens__mutmut_24(messages: List[Dict[str, Any]]) -> int:
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
        tool_calls = msg.get("XXtool_callsXX", [])
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


def x_estimate_messages_tokens__mutmut_25(messages: List[Dict[str, Any]]) -> int:
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
        tool_calls = msg.get("TOOL_CALLS", [])
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


def x_estimate_messages_tokens__mutmut_26(messages: List[Dict[str, Any]]) -> int:
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
        tool_call_id = None
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_27(messages: List[Dict[str, Any]]) -> int:
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
        tool_call_id = msg.get(None, "")
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_28(messages: List[Dict[str, Any]]) -> int:
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
        tool_call_id = msg.get("tool_call_id", None)
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_29(messages: List[Dict[str, Any]]) -> int:
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
        tool_call_id = msg.get("")
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_30(messages: List[Dict[str, Any]]) -> int:
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
        tool_call_id = msg.get("tool_call_id", )
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_31(messages: List[Dict[str, Any]]) -> int:
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
        tool_call_id = msg.get("XXtool_call_idXX", "")
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_32(messages: List[Dict[str, Any]]) -> int:
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
        tool_call_id = msg.get("TOOL_CALL_ID", "")
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_33(messages: List[Dict[str, Any]]) -> int:
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
        tool_call_id = msg.get("tool_call_id", "XXXX")
        name = msg.get("name", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_34(messages: List[Dict[str, Any]]) -> int:
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
        name = None
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_35(messages: List[Dict[str, Any]]) -> int:
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
        name = msg.get(None, "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_36(messages: List[Dict[str, Any]]) -> int:
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
        name = msg.get("name", None)
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_37(messages: List[Dict[str, Any]]) -> int:
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
        name = msg.get("")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_38(messages: List[Dict[str, Any]]) -> int:
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
        name = msg.get("name", )
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_39(messages: List[Dict[str, Any]]) -> int:
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
        name = msg.get("XXnameXX", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_40(messages: List[Dict[str, Any]]) -> int:
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
        name = msg.get("NAME", "")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_41(messages: List[Dict[str, Any]]) -> int:
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
        name = msg.get("name", "XXXX")
        
        total += estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_42(messages: List[Dict[str, Any]]) -> int:
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
        
        total = estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_43(messages: List[Dict[str, Any]]) -> int:
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
        
        total -= estimate_tokens(role)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_44(messages: List[Dict[str, Any]]) -> int:
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
        
        total += estimate_tokens(None)
        total += estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_45(messages: List[Dict[str, Any]]) -> int:
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
        total = estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_46(messages: List[Dict[str, Any]]) -> int:
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
        total -= estimate_tokens(content) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_47(messages: List[Dict[str, Any]]) -> int:
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
        total += estimate_tokens(None) if content else 0
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_48(messages: List[Dict[str, Any]]) -> int:
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
        total += estimate_tokens(content) if content else 1
        total += estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_49(messages: List[Dict[str, Any]]) -> int:
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
        total = estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_50(messages: List[Dict[str, Any]]) -> int:
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
        total -= estimate_tokens(tool_calls) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_51(messages: List[Dict[str, Any]]) -> int:
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
        total += estimate_tokens(None) if tool_calls else 0
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_52(messages: List[Dict[str, Any]]) -> int:
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
        total += estimate_tokens(tool_calls) if tool_calls else 1
        total += estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_53(messages: List[Dict[str, Any]]) -> int:
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
        total = estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_54(messages: List[Dict[str, Any]]) -> int:
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
        total -= estimate_tokens(tool_call_id) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_55(messages: List[Dict[str, Any]]) -> int:
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
        total += estimate_tokens(None) if tool_call_id else 0
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_56(messages: List[Dict[str, Any]]) -> int:
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
        total += estimate_tokens(tool_call_id) if tool_call_id else 1
        total += estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_57(messages: List[Dict[str, Any]]) -> int:
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
        total = estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_58(messages: List[Dict[str, Any]]) -> int:
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
        total -= estimate_tokens(name) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_59(messages: List[Dict[str, Any]]) -> int:
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
        total += estimate_tokens(None) if name else 0
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_60(messages: List[Dict[str, Any]]) -> int:
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
        total += estimate_tokens(name) if name else 1
        
        # Add overhead for message structure (approximately)
        total += 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_61(messages: List[Dict[str, Any]]) -> int:
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
        total = 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_62(messages: List[Dict[str, Any]]) -> int:
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
        total -= 5  # ~20 chars overhead per message
    
    return total


def x_estimate_messages_tokens__mutmut_63(messages: List[Dict[str, Any]]) -> int:
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
        total += 6  # ~20 chars overhead per message
    
    return total

x_estimate_messages_tokens__mutmut_mutants : ClassVar[MutantDict] = {
'x_estimate_messages_tokens__mutmut_1': x_estimate_messages_tokens__mutmut_1, 
    'x_estimate_messages_tokens__mutmut_2': x_estimate_messages_tokens__mutmut_2, 
    'x_estimate_messages_tokens__mutmut_3': x_estimate_messages_tokens__mutmut_3, 
    'x_estimate_messages_tokens__mutmut_4': x_estimate_messages_tokens__mutmut_4, 
    'x_estimate_messages_tokens__mutmut_5': x_estimate_messages_tokens__mutmut_5, 
    'x_estimate_messages_tokens__mutmut_6': x_estimate_messages_tokens__mutmut_6, 
    'x_estimate_messages_tokens__mutmut_7': x_estimate_messages_tokens__mutmut_7, 
    'x_estimate_messages_tokens__mutmut_8': x_estimate_messages_tokens__mutmut_8, 
    'x_estimate_messages_tokens__mutmut_9': x_estimate_messages_tokens__mutmut_9, 
    'x_estimate_messages_tokens__mutmut_10': x_estimate_messages_tokens__mutmut_10, 
    'x_estimate_messages_tokens__mutmut_11': x_estimate_messages_tokens__mutmut_11, 
    'x_estimate_messages_tokens__mutmut_12': x_estimate_messages_tokens__mutmut_12, 
    'x_estimate_messages_tokens__mutmut_13': x_estimate_messages_tokens__mutmut_13, 
    'x_estimate_messages_tokens__mutmut_14': x_estimate_messages_tokens__mutmut_14, 
    'x_estimate_messages_tokens__mutmut_15': x_estimate_messages_tokens__mutmut_15, 
    'x_estimate_messages_tokens__mutmut_16': x_estimate_messages_tokens__mutmut_16, 
    'x_estimate_messages_tokens__mutmut_17': x_estimate_messages_tokens__mutmut_17, 
    'x_estimate_messages_tokens__mutmut_18': x_estimate_messages_tokens__mutmut_18, 
    'x_estimate_messages_tokens__mutmut_19': x_estimate_messages_tokens__mutmut_19, 
    'x_estimate_messages_tokens__mutmut_20': x_estimate_messages_tokens__mutmut_20, 
    'x_estimate_messages_tokens__mutmut_21': x_estimate_messages_tokens__mutmut_21, 
    'x_estimate_messages_tokens__mutmut_22': x_estimate_messages_tokens__mutmut_22, 
    'x_estimate_messages_tokens__mutmut_23': x_estimate_messages_tokens__mutmut_23, 
    'x_estimate_messages_tokens__mutmut_24': x_estimate_messages_tokens__mutmut_24, 
    'x_estimate_messages_tokens__mutmut_25': x_estimate_messages_tokens__mutmut_25, 
    'x_estimate_messages_tokens__mutmut_26': x_estimate_messages_tokens__mutmut_26, 
    'x_estimate_messages_tokens__mutmut_27': x_estimate_messages_tokens__mutmut_27, 
    'x_estimate_messages_tokens__mutmut_28': x_estimate_messages_tokens__mutmut_28, 
    'x_estimate_messages_tokens__mutmut_29': x_estimate_messages_tokens__mutmut_29, 
    'x_estimate_messages_tokens__mutmut_30': x_estimate_messages_tokens__mutmut_30, 
    'x_estimate_messages_tokens__mutmut_31': x_estimate_messages_tokens__mutmut_31, 
    'x_estimate_messages_tokens__mutmut_32': x_estimate_messages_tokens__mutmut_32, 
    'x_estimate_messages_tokens__mutmut_33': x_estimate_messages_tokens__mutmut_33, 
    'x_estimate_messages_tokens__mutmut_34': x_estimate_messages_tokens__mutmut_34, 
    'x_estimate_messages_tokens__mutmut_35': x_estimate_messages_tokens__mutmut_35, 
    'x_estimate_messages_tokens__mutmut_36': x_estimate_messages_tokens__mutmut_36, 
    'x_estimate_messages_tokens__mutmut_37': x_estimate_messages_tokens__mutmut_37, 
    'x_estimate_messages_tokens__mutmut_38': x_estimate_messages_tokens__mutmut_38, 
    'x_estimate_messages_tokens__mutmut_39': x_estimate_messages_tokens__mutmut_39, 
    'x_estimate_messages_tokens__mutmut_40': x_estimate_messages_tokens__mutmut_40, 
    'x_estimate_messages_tokens__mutmut_41': x_estimate_messages_tokens__mutmut_41, 
    'x_estimate_messages_tokens__mutmut_42': x_estimate_messages_tokens__mutmut_42, 
    'x_estimate_messages_tokens__mutmut_43': x_estimate_messages_tokens__mutmut_43, 
    'x_estimate_messages_tokens__mutmut_44': x_estimate_messages_tokens__mutmut_44, 
    'x_estimate_messages_tokens__mutmut_45': x_estimate_messages_tokens__mutmut_45, 
    'x_estimate_messages_tokens__mutmut_46': x_estimate_messages_tokens__mutmut_46, 
    'x_estimate_messages_tokens__mutmut_47': x_estimate_messages_tokens__mutmut_47, 
    'x_estimate_messages_tokens__mutmut_48': x_estimate_messages_tokens__mutmut_48, 
    'x_estimate_messages_tokens__mutmut_49': x_estimate_messages_tokens__mutmut_49, 
    'x_estimate_messages_tokens__mutmut_50': x_estimate_messages_tokens__mutmut_50, 
    'x_estimate_messages_tokens__mutmut_51': x_estimate_messages_tokens__mutmut_51, 
    'x_estimate_messages_tokens__mutmut_52': x_estimate_messages_tokens__mutmut_52, 
    'x_estimate_messages_tokens__mutmut_53': x_estimate_messages_tokens__mutmut_53, 
    'x_estimate_messages_tokens__mutmut_54': x_estimate_messages_tokens__mutmut_54, 
    'x_estimate_messages_tokens__mutmut_55': x_estimate_messages_tokens__mutmut_55, 
    'x_estimate_messages_tokens__mutmut_56': x_estimate_messages_tokens__mutmut_56, 
    'x_estimate_messages_tokens__mutmut_57': x_estimate_messages_tokens__mutmut_57, 
    'x_estimate_messages_tokens__mutmut_58': x_estimate_messages_tokens__mutmut_58, 
    'x_estimate_messages_tokens__mutmut_59': x_estimate_messages_tokens__mutmut_59, 
    'x_estimate_messages_tokens__mutmut_60': x_estimate_messages_tokens__mutmut_60, 
    'x_estimate_messages_tokens__mutmut_61': x_estimate_messages_tokens__mutmut_61, 
    'x_estimate_messages_tokens__mutmut_62': x_estimate_messages_tokens__mutmut_62, 
    'x_estimate_messages_tokens__mutmut_63': x_estimate_messages_tokens__mutmut_63
}

def estimate_messages_tokens(*args, **kwargs):
    result = _mutmut_trampoline(x_estimate_messages_tokens__mutmut_orig, x_estimate_messages_tokens__mutmut_mutants, args, kwargs)
    return result 

estimate_messages_tokens.__signature__ = _mutmut_signature(x_estimate_messages_tokens__mutmut_orig)
x_estimate_messages_tokens__mutmut_orig.__name__ = 'x_estimate_messages_tokens'


def x_estimate_prompt_tokens__mutmut_orig(
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


def x_estimate_prompt_tokens__mutmut_1(
    system_prompt: str = "XXXX",
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


def x_estimate_prompt_tokens__mutmut_2(
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
    total = None
    
    total += estimate_tokens(system_prompt) if system_prompt else 0
    total += estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_3(
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
    total = 1
    
    total += estimate_tokens(system_prompt) if system_prompt else 0
    total += estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_4(
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
    
    total = estimate_tokens(system_prompt) if system_prompt else 0
    total += estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_5(
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
    
    total -= estimate_tokens(system_prompt) if system_prompt else 0
    total += estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_6(
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
    
    total += estimate_tokens(None) if system_prompt else 0
    total += estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_7(
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
    
    total += estimate_tokens(system_prompt) if system_prompt else 1
    total += estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_8(
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
    total = estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_9(
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
    total -= estimate_messages_tokens(messages) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_10(
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
    total += estimate_messages_tokens(None) if messages else 0
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_11(
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
    total += estimate_messages_tokens(messages) if messages else 1
    total += estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_12(
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
    total = estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_13(
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
    total -= estimate_tokens(tools) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_14(
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
    total += estimate_tokens(None) if tools else 0
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_15(
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
    total += estimate_tokens(tools) if tools else 1
    
    # Add overhead for prompt structure
    total += 10
    
    return total


def x_estimate_prompt_tokens__mutmut_16(
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
    total = 10
    
    return total


def x_estimate_prompt_tokens__mutmut_17(
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
    total -= 10
    
    return total


def x_estimate_prompt_tokens__mutmut_18(
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
    total += 11
    
    return total

x_estimate_prompt_tokens__mutmut_mutants : ClassVar[MutantDict] = {
'x_estimate_prompt_tokens__mutmut_1': x_estimate_prompt_tokens__mutmut_1, 
    'x_estimate_prompt_tokens__mutmut_2': x_estimate_prompt_tokens__mutmut_2, 
    'x_estimate_prompt_tokens__mutmut_3': x_estimate_prompt_tokens__mutmut_3, 
    'x_estimate_prompt_tokens__mutmut_4': x_estimate_prompt_tokens__mutmut_4, 
    'x_estimate_prompt_tokens__mutmut_5': x_estimate_prompt_tokens__mutmut_5, 
    'x_estimate_prompt_tokens__mutmut_6': x_estimate_prompt_tokens__mutmut_6, 
    'x_estimate_prompt_tokens__mutmut_7': x_estimate_prompt_tokens__mutmut_7, 
    'x_estimate_prompt_tokens__mutmut_8': x_estimate_prompt_tokens__mutmut_8, 
    'x_estimate_prompt_tokens__mutmut_9': x_estimate_prompt_tokens__mutmut_9, 
    'x_estimate_prompt_tokens__mutmut_10': x_estimate_prompt_tokens__mutmut_10, 
    'x_estimate_prompt_tokens__mutmut_11': x_estimate_prompt_tokens__mutmut_11, 
    'x_estimate_prompt_tokens__mutmut_12': x_estimate_prompt_tokens__mutmut_12, 
    'x_estimate_prompt_tokens__mutmut_13': x_estimate_prompt_tokens__mutmut_13, 
    'x_estimate_prompt_tokens__mutmut_14': x_estimate_prompt_tokens__mutmut_14, 
    'x_estimate_prompt_tokens__mutmut_15': x_estimate_prompt_tokens__mutmut_15, 
    'x_estimate_prompt_tokens__mutmut_16': x_estimate_prompt_tokens__mutmut_16, 
    'x_estimate_prompt_tokens__mutmut_17': x_estimate_prompt_tokens__mutmut_17, 
    'x_estimate_prompt_tokens__mutmut_18': x_estimate_prompt_tokens__mutmut_18
}

def estimate_prompt_tokens(*args, **kwargs):
    result = _mutmut_trampoline(x_estimate_prompt_tokens__mutmut_orig, x_estimate_prompt_tokens__mutmut_mutants, args, kwargs)
    return result 

estimate_prompt_tokens.__signature__ = _mutmut_signature(x_estimate_prompt_tokens__mutmut_orig)
x_estimate_prompt_tokens__mutmut_orig.__name__ = 'x_estimate_prompt_tokens'


def x_truncate_tool_result__mutmut_orig(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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


def x_truncate_tool_result__mutmut_1(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    if isinstance(tool_result, dict):
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


def x_truncate_tool_result__mutmut_2(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    content = None
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


def x_truncate_tool_result__mutmut_3(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    content = tool_result.get(None, "")
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


def x_truncate_tool_result__mutmut_4(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    content = tool_result.get("content", None)
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


def x_truncate_tool_result__mutmut_5(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    content = tool_result.get("")
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


def x_truncate_tool_result__mutmut_6(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    content = tool_result.get("content", )
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


def x_truncate_tool_result__mutmut_7(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    content = tool_result.get("XXcontentXX", "")
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


def x_truncate_tool_result__mutmut_8(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    content = tool_result.get("CONTENT", "")
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


def x_truncate_tool_result__mutmut_9(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    content = tool_result.get("content", "XXXX")
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


def x_truncate_tool_result__mutmut_10(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    if isinstance(content, str):
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


def x_truncate_tool_result__mutmut_11(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    
    if len(content) < max_size:
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


def x_truncate_tool_result__mutmut_12(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    prefix_size = None
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


def x_truncate_tool_result__mutmut_13(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    prefix_size = int(None)
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


def x_truncate_tool_result__mutmut_14(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    prefix_size = int(max_size / 0.8)
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


def x_truncate_tool_result__mutmut_15(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    prefix_size = int(max_size * 1.8)
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


def x_truncate_tool_result__mutmut_16(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    suffix_size = None
    
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


def x_truncate_tool_result__mutmut_17(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    suffix_size = int(None)
    
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


def x_truncate_tool_result__mutmut_18(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    suffix_size = int(max_size / 0.1)
    
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


def x_truncate_tool_result__mutmut_19(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    suffix_size = int(max_size * 1.1)
    
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


def x_truncate_tool_result__mutmut_20(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    prefix = None
    suffix = content[-suffix_size:] if len(content) > suffix_size else ""
    
    # Create truncation marker
    truncated_chars = len(content) - max_size
    truncation_marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_21(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    suffix = None
    
    # Create truncation marker
    truncated_chars = len(content) - max_size
    truncation_marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_22(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    suffix = content[+suffix_size:] if len(content) > suffix_size else ""
    
    # Create truncation marker
    truncated_chars = len(content) - max_size
    truncation_marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_23(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    suffix = content[-suffix_size:] if len(content) >= suffix_size else ""
    
    # Create truncation marker
    truncated_chars = len(content) - max_size
    truncation_marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_24(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    suffix = content[-suffix_size:] if len(content) > suffix_size else "XXXX"
    
    # Create truncation marker
    truncated_chars = len(content) - max_size
    truncation_marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_25(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    truncated_chars = None
    truncation_marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_26(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    truncated_chars = len(content) + max_size
    truncation_marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_27(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    truncation_marker = None
    
    # Combine with truncation marker
    truncated_content = f"{prefix}{truncation_marker}{suffix}"
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_28(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    truncated_content = None
    
    # Return new dict with truncated content, preserving all other fields
    return {**tool_result, "content": truncated_content}


def x_truncate_tool_result__mutmut_29(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    return {**tool_result, "XXcontentXX": truncated_content}


def x_truncate_tool_result__mutmut_30(tool_result: Dict[str, Any], max_size: int) -> Dict[str, Any]:
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
    return {**tool_result, "CONTENT": truncated_content}

x_truncate_tool_result__mutmut_mutants : ClassVar[MutantDict] = {
'x_truncate_tool_result__mutmut_1': x_truncate_tool_result__mutmut_1, 
    'x_truncate_tool_result__mutmut_2': x_truncate_tool_result__mutmut_2, 
    'x_truncate_tool_result__mutmut_3': x_truncate_tool_result__mutmut_3, 
    'x_truncate_tool_result__mutmut_4': x_truncate_tool_result__mutmut_4, 
    'x_truncate_tool_result__mutmut_5': x_truncate_tool_result__mutmut_5, 
    'x_truncate_tool_result__mutmut_6': x_truncate_tool_result__mutmut_6, 
    'x_truncate_tool_result__mutmut_7': x_truncate_tool_result__mutmut_7, 
    'x_truncate_tool_result__mutmut_8': x_truncate_tool_result__mutmut_8, 
    'x_truncate_tool_result__mutmut_9': x_truncate_tool_result__mutmut_9, 
    'x_truncate_tool_result__mutmut_10': x_truncate_tool_result__mutmut_10, 
    'x_truncate_tool_result__mutmut_11': x_truncate_tool_result__mutmut_11, 
    'x_truncate_tool_result__mutmut_12': x_truncate_tool_result__mutmut_12, 
    'x_truncate_tool_result__mutmut_13': x_truncate_tool_result__mutmut_13, 
    'x_truncate_tool_result__mutmut_14': x_truncate_tool_result__mutmut_14, 
    'x_truncate_tool_result__mutmut_15': x_truncate_tool_result__mutmut_15, 
    'x_truncate_tool_result__mutmut_16': x_truncate_tool_result__mutmut_16, 
    'x_truncate_tool_result__mutmut_17': x_truncate_tool_result__mutmut_17, 
    'x_truncate_tool_result__mutmut_18': x_truncate_tool_result__mutmut_18, 
    'x_truncate_tool_result__mutmut_19': x_truncate_tool_result__mutmut_19, 
    'x_truncate_tool_result__mutmut_20': x_truncate_tool_result__mutmut_20, 
    'x_truncate_tool_result__mutmut_21': x_truncate_tool_result__mutmut_21, 
    'x_truncate_tool_result__mutmut_22': x_truncate_tool_result__mutmut_22, 
    'x_truncate_tool_result__mutmut_23': x_truncate_tool_result__mutmut_23, 
    'x_truncate_tool_result__mutmut_24': x_truncate_tool_result__mutmut_24, 
    'x_truncate_tool_result__mutmut_25': x_truncate_tool_result__mutmut_25, 
    'x_truncate_tool_result__mutmut_26': x_truncate_tool_result__mutmut_26, 
    'x_truncate_tool_result__mutmut_27': x_truncate_tool_result__mutmut_27, 
    'x_truncate_tool_result__mutmut_28': x_truncate_tool_result__mutmut_28, 
    'x_truncate_tool_result__mutmut_29': x_truncate_tool_result__mutmut_29, 
    'x_truncate_tool_result__mutmut_30': x_truncate_tool_result__mutmut_30
}

def truncate_tool_result(*args, **kwargs):
    result = _mutmut_trampoline(x_truncate_tool_result__mutmut_orig, x_truncate_tool_result__mutmut_mutants, args, kwargs)
    return result 

truncate_tool_result.__signature__ = _mutmut_signature(x_truncate_tool_result__mutmut_orig)
x_truncate_tool_result__mutmut_orig.__name__ = 'x_truncate_tool_result'

