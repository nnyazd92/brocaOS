"""
JSON repair and error diagnosis utilities for tool arguments.

Provides functions to attempt JSON repair for common issues and generate
detailed error messages to help LLMs fix malformed JSON.
"""

from __future__ import annotations

import json
import re
from typing import Dict, Any, Optional, Tuple


def attempt_json_repair(json_str: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Attempt to repair common JSON issues and parse.
    
    Tries multiple repair strategies in order:
    1. Direct parse (if already valid)
    2. Fix unterminated strings
    3. Fix unescaped quotes in strings
    4. Fix missing commas
    5. Fix trailing commas
    
    Args:
        json_str: JSON string that may be malformed
        
    Returns:
        Tuple of (parsed_dict, error_message)
        - If successful: (dict, None)
        - If failed: (None, detailed_error_message)
    """
    if not json_str or json_str.strip() == "":
        return {}, None
    
    # Try direct parse first
    try:
        return json.loads(json_str), None
    except json.JSONDecodeError:
        pass
    
    # Try repair strategies
    repaired = json_str
    
    # Strategy 1: Fix unterminated strings
    try:
        repaired = _fix_unterminated_strings(repaired)
        return json.loads(repaired), None
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Fix unescaped quotes
    try:
        repaired = _fix_unescaped_quotes(json_str)
        return json.loads(repaired), None
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Fix missing commas
    try:
        repaired = _fix_missing_commas(json_str)
        return json.loads(repaired), None
    except json.JSONDecodeError:
        pass
    
    # Strategy 4: Fix trailing commas
    try:
        repaired = _fix_trailing_commas(json_str)
        return json.loads(repaired), None
    except json.JSONDecodeError:
        pass
    
    # All repair attempts failed
    # Try to parse to get detailed error for diagnosis
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        error_msg = diagnose_json_error(json_str, e)
        return None, error_msg
    
    # Should never reach here
    return None, "Unknown JSON parsing error"


def _fix_unterminated_strings(json_str: str) -> str:
    """Fix unterminated strings by closing them at the end."""
    # Simple heuristic: if the string ends with an odd number of unescaped quotes,
    # we might have an unterminated string
    result = json_str
    depth = 0
    in_string = False
    escape_next = False
    
    for i, char in enumerate(json_str):
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
        
        if not in_string:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
    
    # If we're still in a string at the end, close it
    if in_string:
        result = json_str + '"'
    
    return result


def _fix_unescaped_quotes(json_str: str) -> str:
    """Fix unescaped quotes within string values."""
    result = []
    i = 0
    in_string = False
    escape_next = False
    
    while i < len(json_str):
        char = json_str[i]
        
        if escape_next:
            escape_next = False
            result.append(char)
            i += 1
            continue
        
        if char == '\\':
            escape_next = True
            result.append(char)
            i += 1
            continue
        
        if char == '"':
            if in_string:
                # Check if this is the end of the string or an unescaped quote
                # Look ahead to see if next non-whitespace is : or ,
                j = i + 1
                while j < len(json_str) and json_str[j] in ' \t\n\r':
                    j += 1
                
                if j < len(json_str) and json_str[j] in ':,}':
                    # Likely end of string
                    in_string = False
                    result.append(char)
                else:
                    # Likely unescaped quote - escape it
                    result.append('\\')
                    result.append(char)
            else:
                in_string = True
                result.append(char)
            i += 1
            continue
        
        result.append(char)
        i += 1
    
    return ''.join(result)


def _fix_missing_commas(json_str: str) -> str:
    """Fix missing commas between JSON elements."""
    result = []
    i = 0
    
    while i < len(json_str):
        char = json_str[i]
        result.append(char)
        
        # Look for patterns like: "key": "value" "next_key" or } "key"
        if char in '"}':
            # Look ahead
            j = i + 1
            # Skip whitespace
            while j < len(json_str) and json_str[j] in ' \t\n\r':
                j += 1
            
            if j < len(json_str):
                next_char = json_str[j]
                # Need comma between } and " or between " and "
                if (char == '}' and next_char == '"') or (char == '"' and next_char == '"'):
                    result.append(',')
        
        i += 1
    
    return ''.join(result)


def _fix_trailing_commas(json_str: str) -> str:
    """Remove trailing commas before } or ]."""
    # Remove trailing commas before closing braces/brackets
    result = re.sub(r',(\s*[}\]])', r'\1', json_str)
    return result


def diagnose_json_error(json_str: str, error: json.JSONDecodeError) -> str:
    """
    Generate a detailed error diagnosis for JSON parsing errors.
    
    Args:
        json_str: The malformed JSON string
        error: The JSONDecodeError that occurred
        
    Returns:
        Detailed error message with snippet and suggestions
    """
    position = error.pos
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Extract problematic snippet
    snippet = extract_problematic_snippet(json_str, position)
    
    # Generate suggestion
    suggestion = suggest_json_fix(error_type, position, snippet)
    
    # Build detailed error message
    lines = [
        "Invalid JSON in tool arguments.",
        "",
        f"Error: {error_msg}",
        f"Position: {position} (character {position})",
        "",
        "Problematic JSON snippet:",
        snippet,
        "",
        suggestion,
        "",
        "Please ensure all strings are properly quoted and escaped, all commas are present, and the JSON is properly formatted."
    ]
    
    return "\n".join(lines)


def extract_problematic_snippet(json_str: str, position: int, context: int = 50) -> str:
    """
    Extract JSON snippet around the error position.
    
    Args:
        json_str: The JSON string
        position: Character position where error occurred
        context: Number of characters to show before and after
        
    Returns:
        Snippet with position indicator
    """
    start = max(0, position - context)
    end = min(len(json_str), position + context)
    
    snippet = json_str[start:end]
    
    # Show where the error is
    relative_pos = position - start
    indicator = " " * relative_pos + "^" + " (error here)"
    
    # Show line number and column if possible
    lines_before = json_str[:position].count('\n')
    col = position - json_str.rfind('\n', 0, position) - 1
    
    return f"{snippet}\n{indicator}\nLine {lines_before + 1}, column {col + 1}"


def suggest_json_fix(error_type: str, position: int, snippet: str) -> str:
    """
    Suggest how to fix a JSON error.
    
    Args:
        error_type: Type of JSON error
        position: Position where error occurred
        snippet: The problematic snippet
        
    Returns:
        Suggestion string
    """
    suggestions = []
    
    if "Unterminated string" in error_type or "Unterminated" in snippet.lower():
        suggestions.append("- Unterminated string detected. Ensure all string values are properly closed with a closing quote.")
        suggestions.append("- Check for missing closing quotes, especially in multi-line strings.")
    
    if '"' in snippet and snippet.count('"') % 2 != 0:
        suggestions.append("- Unescaped quotes in string detected. Use \\\" to include quotes within string values.")
        suggestions.append("- Example: Use {\"key\": \"value with \\\"quotes\\\"\"} instead of {\"key\": \"value with \"quotes\"\"}")
    
    if "Expecting" in snippet or "Expecting" in error_type:
        if ',' in snippet:
            suggestions.append("- Missing comma between JSON elements. Add commas between object properties or array elements.")
        elif ':' in snippet:
            suggestions.append("- Missing colon between key and value in object property.")
    
    if '}' in snippet or ']' in snippet:
        # Check for trailing commas
        if ',' in snippet[-20:]:
            suggestions.append("- Trailing comma detected. Remove commas before closing braces } or brackets ].")
    
    if not suggestions:
        suggestions.append("- Review the JSON structure around the error position.")
        suggestions.append("- Ensure proper quoting, escaping, and comma placement.")
    
    return "Suggestions:\n" + "\n".join(f"  {s}" for s in suggestions)

