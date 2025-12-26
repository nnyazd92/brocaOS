"""ANSI escape sequence repair utility.

Fixes broken ANSI escape sequences in LLM output where the escape character
(\x1b) is missing, causing codes like [1;32m instead of \x1b[1;32m.
"""
from __future__ import annotations

import re

# Pattern to match valid ANSI escape sequences (with escape character)
_VALID_ANSI_PATTERN = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', re.UNICODE)

# Pattern to match broken ANSI sequences (missing escape character)
# Matches patterns like [1;32m, [0m, [31m, etc.
# Negative lookbehind ensures it's not already part of a valid sequence
_BROKEN_ANSI_PATTERN = re.compile(
    r'(?<!\x1b)(?<!\\033)'  # Not preceded by \x1b or \033 (octal)
    r'\[([0-9]+(?:;[0-9]+)*)m',  # ANSI code pattern [numbers;numbers]m
    re.UNICODE
)


def repair_ansi_codes(text: str) -> str:
    """
    Repair broken ANSI escape sequences by adding missing escape characters.
    
    Detects ANSI code patterns that are missing the escape character (like
    [1;32m instead of \x1b[1;32m) and prepends \x1b to fix them.
    
    Args:
        text: Text that may contain broken ANSI escape sequences
        
    Returns:
        Text with broken ANSI codes repaired (valid codes unchanged)
        
    Examples:
        >>> repair_ansi_codes("[1;32mHELLO[0m")
        '\\x1b[1;32mHELLO\\x1b[0m'
        
        >>> repair_ansi_codes("\\x1b[1;32mHELLO\\x1b[0m")
        '\\x1b[1;32mHELLO\\x1b[0m'
        
        >>> repair_ansi_codes("Normal text [1;32m colored [0m text")
        'Normal text \\x1b[1;32m colored \\x1b[0m text'
    """
    if not text:
        return text
    
    # Check if text already contains valid ANSI sequences
    # If it does, we need to be more careful about what we repair
    has_valid_ansi = bool(_VALID_ANSI_PATTERN.search(text))
    
    # Find all positions where valid ANSI sequences occur
    # We'll use this to avoid repairing sequences that are part of valid codes
    valid_positions = set()
    if has_valid_ansi:
        for match in _VALID_ANSI_PATTERN.finditer(text):
            # Mark all character positions in this valid sequence
            valid_positions.update(range(match.start(), match.end()))
    
    # Find broken ANSI sequences and repair them
    def replace_broken(match: re.Match) -> str:
        # Check if this match overlaps with a valid ANSI sequence
        match_start = match.start()
        match_end = match.end()
        if valid_positions and any(pos in valid_positions for pos in range(match_start, match_end)):
            # This is part of a valid sequence, don't repair
            return match.group(0)
        
        # Check if the character before the match is part of a valid sequence
        # This helps catch cases where the escape char might be just before
        if match_start > 0 and (match_start - 1) in valid_positions:
            return match.group(0)
        
        # This is a broken sequence, repair it by prepending escape character
        return '\x1b' + match.group(0)
    
    # Replace broken ANSI codes
    repaired = _BROKEN_ANSI_PATTERN.sub(replace_broken, text)
    
    return repaired

