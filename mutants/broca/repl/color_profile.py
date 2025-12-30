"""
Color profile system for REPL customization.

Provides color profiles for customizing REPL appearance including
prompts, input, and response text colors.
"""

from __future__ import annotations

import sys
from typing import Dict, Optional


# ANSI escape code constants
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"

# Standard colors (foreground)
ANSI_BLACK = "\033[30m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"
ANSI_MAGENTA = "\033[35m"
ANSI_CYAN = "\033[36m"
ANSI_WHITE = "\033[37m"

# Bright colors
ANSI_BRIGHT_BLACK = "\033[90m"
ANSI_BRIGHT_RED = "\033[91m"
ANSI_BRIGHT_GREEN = "\033[92m"
ANSI_BRIGHT_YELLOW = "\033[93m"
ANSI_BRIGHT_BLUE = "\033[94m"
ANSI_BRIGHT_MAGENTA = "\033[95m"
ANSI_BRIGHT_CYAN = "\033[96m"
ANSI_BRIGHT_WHITE = "\033[97m"
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


def x_ansi_color__mutmut_orig(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_1(code: int, use_256: bool = True) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_2(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 1 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_3(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 < code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_4(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code < 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_5(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 256:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_6(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(None, 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_7(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), None)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_8(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_9(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), )}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_10(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(None, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_11(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, None), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_12(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_13(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, ), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_14(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 31), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_15(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 98)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_16(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 31 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_17(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 < code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_18(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code < 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_19(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 38:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_20(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 91 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_21(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 < code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_22(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code < 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_23(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 98:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 97)}m"


def x_ansi_color__mutmut_24(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(None, 97)}m"


def x_ansi_color__mutmut_25(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), None)}m"


def x_ansi_color__mutmut_26(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(97)}m"


def x_ansi_color__mutmut_27(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), )}m"


def x_ansi_color__mutmut_28(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(None, 30), 97)}m"


def x_ansi_color__mutmut_29(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, None), 97)}m"


def x_ansi_color__mutmut_30(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(30), 97)}m"


def x_ansi_color__mutmut_31(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, ), 97)}m"


def x_ansi_color__mutmut_32(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 31), 97)}m"


def x_ansi_color__mutmut_33(code: int, use_256: bool = False) -> str:
    """
    Generate ANSI color code.
    
    Args:
        code: Color code (0-255 for 256-color mode, 30-37/90-97 for standard)
        use_256: If True, use 256-color mode (38;5;XX), else use standard (XX)
        
    Returns:
        ANSI escape sequence string
    """
    if use_256:
        if 0 <= code <= 255:
            return f"\033[38;5;{code}m"
        else:
            # Fallback to standard if out of range
            return f"\033[{min(max(code, 30), 97)}m"
    else:
        # Standard color codes
        if 30 <= code <= 37:
            return f"\033[{code}m"
        elif 90 <= code <= 97:
            return f"\033[{code}m"
        else:
            # Clamp to valid range
            return f"\033[{min(max(code, 30), 98)}m"

x_ansi_color__mutmut_mutants : ClassVar[MutantDict] = {
'x_ansi_color__mutmut_1': x_ansi_color__mutmut_1, 
    'x_ansi_color__mutmut_2': x_ansi_color__mutmut_2, 
    'x_ansi_color__mutmut_3': x_ansi_color__mutmut_3, 
    'x_ansi_color__mutmut_4': x_ansi_color__mutmut_4, 
    'x_ansi_color__mutmut_5': x_ansi_color__mutmut_5, 
    'x_ansi_color__mutmut_6': x_ansi_color__mutmut_6, 
    'x_ansi_color__mutmut_7': x_ansi_color__mutmut_7, 
    'x_ansi_color__mutmut_8': x_ansi_color__mutmut_8, 
    'x_ansi_color__mutmut_9': x_ansi_color__mutmut_9, 
    'x_ansi_color__mutmut_10': x_ansi_color__mutmut_10, 
    'x_ansi_color__mutmut_11': x_ansi_color__mutmut_11, 
    'x_ansi_color__mutmut_12': x_ansi_color__mutmut_12, 
    'x_ansi_color__mutmut_13': x_ansi_color__mutmut_13, 
    'x_ansi_color__mutmut_14': x_ansi_color__mutmut_14, 
    'x_ansi_color__mutmut_15': x_ansi_color__mutmut_15, 
    'x_ansi_color__mutmut_16': x_ansi_color__mutmut_16, 
    'x_ansi_color__mutmut_17': x_ansi_color__mutmut_17, 
    'x_ansi_color__mutmut_18': x_ansi_color__mutmut_18, 
    'x_ansi_color__mutmut_19': x_ansi_color__mutmut_19, 
    'x_ansi_color__mutmut_20': x_ansi_color__mutmut_20, 
    'x_ansi_color__mutmut_21': x_ansi_color__mutmut_21, 
    'x_ansi_color__mutmut_22': x_ansi_color__mutmut_22, 
    'x_ansi_color__mutmut_23': x_ansi_color__mutmut_23, 
    'x_ansi_color__mutmut_24': x_ansi_color__mutmut_24, 
    'x_ansi_color__mutmut_25': x_ansi_color__mutmut_25, 
    'x_ansi_color__mutmut_26': x_ansi_color__mutmut_26, 
    'x_ansi_color__mutmut_27': x_ansi_color__mutmut_27, 
    'x_ansi_color__mutmut_28': x_ansi_color__mutmut_28, 
    'x_ansi_color__mutmut_29': x_ansi_color__mutmut_29, 
    'x_ansi_color__mutmut_30': x_ansi_color__mutmut_30, 
    'x_ansi_color__mutmut_31': x_ansi_color__mutmut_31, 
    'x_ansi_color__mutmut_32': x_ansi_color__mutmut_32, 
    'x_ansi_color__mutmut_33': x_ansi_color__mutmut_33
}

def ansi_color(*args, **kwargs):
    result = _mutmut_trampoline(x_ansi_color__mutmut_orig, x_ansi_color__mutmut_mutants, args, kwargs)
    return result 

ansi_color.__signature__ = _mutmut_signature(x_ansi_color__mutmut_orig)
x_ansi_color__mutmut_orig.__name__ = 'x_ansi_color'


def ansi_reset() -> str:
    """Get ANSI reset code."""
    return ANSI_RESET

# Export constant for convenience
ansi_reset_code = ANSI_RESET


class ColorProfile:
    """
    Base class for color profiles.
    
    Defines colors for different REPL elements:
    - brocaos_prompt: Color for "BrocaOS> " prompt
    - response_text: Color for assistant response text
    - you_prompt: Color for "you> " prompt
    - input_text: Color for user input text
    - success_indicator: Color for success indicator (✓)
    - error_indicator: Color for error indicator (✗)
    """
    
    def xǁColorProfileǁ__init____mutmut_orig(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_1(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "XXXX",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_2(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = "XXXX"
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_3(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = None
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_4(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt and ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_5(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or "XXXX"
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_6(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = None
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_7(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text and ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_8(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or "XXXX"
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_9(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = None
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_10(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt and ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_11(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or "XXXX"
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_12(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = None
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_13(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text and ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_14(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or "XXXX"
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_15(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = None
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_16(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator and ""
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_17(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or "XXXX"
        self.error_indicator = error_indicator or ""
    
    def xǁColorProfileǁ__init____mutmut_18(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = None
    
    def xǁColorProfileǁ__init____mutmut_19(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator and ""
    
    def xǁColorProfileǁ__init____mutmut_20(
        self,
        brocaos_prompt: str,
        response_text: str,
        you_prompt: str,
        input_text: str,
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize color profile.
        
        Args:
            brocaos_prompt: ANSI color code for BrocaOS prompt
            response_text: ANSI color code for response text
            you_prompt: ANSI color code for you prompt
            input_text: ANSI color code for input text
            success_indicator: ANSI color code for success indicator (✓)
            error_indicator: ANSI color code for error indicator (✗)
        """
        self.brocaos_prompt = brocaos_prompt or ""
        self.response_text = response_text or ""
        self.you_prompt = you_prompt or ""
        self.input_text = input_text or ""
        self.success_indicator = success_indicator or ""
        self.error_indicator = error_indicator or "XXXX"
    
    xǁColorProfileǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorProfileǁ__init____mutmut_1': xǁColorProfileǁ__init____mutmut_1, 
        'xǁColorProfileǁ__init____mutmut_2': xǁColorProfileǁ__init____mutmut_2, 
        'xǁColorProfileǁ__init____mutmut_3': xǁColorProfileǁ__init____mutmut_3, 
        'xǁColorProfileǁ__init____mutmut_4': xǁColorProfileǁ__init____mutmut_4, 
        'xǁColorProfileǁ__init____mutmut_5': xǁColorProfileǁ__init____mutmut_5, 
        'xǁColorProfileǁ__init____mutmut_6': xǁColorProfileǁ__init____mutmut_6, 
        'xǁColorProfileǁ__init____mutmut_7': xǁColorProfileǁ__init____mutmut_7, 
        'xǁColorProfileǁ__init____mutmut_8': xǁColorProfileǁ__init____mutmut_8, 
        'xǁColorProfileǁ__init____mutmut_9': xǁColorProfileǁ__init____mutmut_9, 
        'xǁColorProfileǁ__init____mutmut_10': xǁColorProfileǁ__init____mutmut_10, 
        'xǁColorProfileǁ__init____mutmut_11': xǁColorProfileǁ__init____mutmut_11, 
        'xǁColorProfileǁ__init____mutmut_12': xǁColorProfileǁ__init____mutmut_12, 
        'xǁColorProfileǁ__init____mutmut_13': xǁColorProfileǁ__init____mutmut_13, 
        'xǁColorProfileǁ__init____mutmut_14': xǁColorProfileǁ__init____mutmut_14, 
        'xǁColorProfileǁ__init____mutmut_15': xǁColorProfileǁ__init____mutmut_15, 
        'xǁColorProfileǁ__init____mutmut_16': xǁColorProfileǁ__init____mutmut_16, 
        'xǁColorProfileǁ__init____mutmut_17': xǁColorProfileǁ__init____mutmut_17, 
        'xǁColorProfileǁ__init____mutmut_18': xǁColorProfileǁ__init____mutmut_18, 
        'xǁColorProfileǁ__init____mutmut_19': xǁColorProfileǁ__init____mutmut_19, 
        'xǁColorProfileǁ__init____mutmut_20': xǁColorProfileǁ__init____mutmut_20
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorProfileǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁColorProfileǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁColorProfileǁ__init____mutmut_orig)
    xǁColorProfileǁ__init____mutmut_orig.__name__ = 'xǁColorProfileǁ__init__'
    
    def xǁColorProfileǁapply_color__mutmut_orig(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(self, color_type, "")
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_1(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = None
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_2(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(None, color_type, "")
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_3(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(self, None, "")
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_4(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(self, color_type, None)
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_5(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(color_type, "")
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_6(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(self, "")
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_7(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(self, color_type, )
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_8(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(self, color_type, "XXXX")
        if not color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    def xǁColorProfileǁapply_color__mutmut_9(self, text: str, color_type: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply ("brocaos_prompt", "response_text", etc.)
            
        Returns:
            Colorized text with reset code
        """
        color_code = getattr(self, color_type, "")
        if color_code:
            return text
        
        return f"{color_code}{text}{ANSI_RESET}"
    
    xǁColorProfileǁapply_color__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorProfileǁapply_color__mutmut_1': xǁColorProfileǁapply_color__mutmut_1, 
        'xǁColorProfileǁapply_color__mutmut_2': xǁColorProfileǁapply_color__mutmut_2, 
        'xǁColorProfileǁapply_color__mutmut_3': xǁColorProfileǁapply_color__mutmut_3, 
        'xǁColorProfileǁapply_color__mutmut_4': xǁColorProfileǁapply_color__mutmut_4, 
        'xǁColorProfileǁapply_color__mutmut_5': xǁColorProfileǁapply_color__mutmut_5, 
        'xǁColorProfileǁapply_color__mutmut_6': xǁColorProfileǁapply_color__mutmut_6, 
        'xǁColorProfileǁapply_color__mutmut_7': xǁColorProfileǁapply_color__mutmut_7, 
        'xǁColorProfileǁapply_color__mutmut_8': xǁColorProfileǁapply_color__mutmut_8, 
        'xǁColorProfileǁapply_color__mutmut_9': xǁColorProfileǁapply_color__mutmut_9
    }
    
    def apply_color(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorProfileǁapply_color__mutmut_orig"), object.__getattribute__(self, "xǁColorProfileǁapply_color__mutmut_mutants"), args, kwargs, self)
        return result 
    
    apply_color.__signature__ = _mutmut_signature(xǁColorProfileǁapply_color__mutmut_orig)
    xǁColorProfileǁapply_color__mutmut_orig.__name__ = 'xǁColorProfileǁapply_color'


class DefaultColorProfile(ColorProfile):
    """Default color profile - subtle colors."""
    
    def xǁDefaultColorProfileǁ__init____mutmut_orig(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_1(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=None,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_2(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=None,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_3(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=None,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_4(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=None,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_5(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=None,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_6(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=None
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_7(self):
        """Initialize default color profile."""
        super().__init__(
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_8(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_9(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_10(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_11(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            error_indicator=ANSI_RED
        )
    
    def xǁDefaultColorProfileǁ__init____mutmut_12(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_BRIGHT_WHITE,  # Bright white for good visibility
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            )
    
    xǁDefaultColorProfileǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDefaultColorProfileǁ__init____mutmut_1': xǁDefaultColorProfileǁ__init____mutmut_1, 
        'xǁDefaultColorProfileǁ__init____mutmut_2': xǁDefaultColorProfileǁ__init____mutmut_2, 
        'xǁDefaultColorProfileǁ__init____mutmut_3': xǁDefaultColorProfileǁ__init____mutmut_3, 
        'xǁDefaultColorProfileǁ__init____mutmut_4': xǁDefaultColorProfileǁ__init____mutmut_4, 
        'xǁDefaultColorProfileǁ__init____mutmut_5': xǁDefaultColorProfileǁ__init____mutmut_5, 
        'xǁDefaultColorProfileǁ__init____mutmut_6': xǁDefaultColorProfileǁ__init____mutmut_6, 
        'xǁDefaultColorProfileǁ__init____mutmut_7': xǁDefaultColorProfileǁ__init____mutmut_7, 
        'xǁDefaultColorProfileǁ__init____mutmut_8': xǁDefaultColorProfileǁ__init____mutmut_8, 
        'xǁDefaultColorProfileǁ__init____mutmut_9': xǁDefaultColorProfileǁ__init____mutmut_9, 
        'xǁDefaultColorProfileǁ__init____mutmut_10': xǁDefaultColorProfileǁ__init____mutmut_10, 
        'xǁDefaultColorProfileǁ__init____mutmut_11': xǁDefaultColorProfileǁ__init____mutmut_11, 
        'xǁDefaultColorProfileǁ__init____mutmut_12': xǁDefaultColorProfileǁ__init____mutmut_12
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDefaultColorProfileǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁDefaultColorProfileǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁDefaultColorProfileǁ__init____mutmut_orig)
    xǁDefaultColorProfileǁ__init____mutmut_orig.__name__ = 'xǁDefaultColorProfileǁ__init__'


class DarkColorProfile(ColorProfile):
    """Dark theme color profile - bright colors on dark background."""
    
    def xǁDarkColorProfileǁ__init____mutmut_orig(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_1(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=None,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_2(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=None,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_3(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=None,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_4(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=None,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_5(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=None,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_6(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=None
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_7(self):
        """Initialize dark color profile."""
        super().__init__(
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_8(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_9(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_10(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_11(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )
    
    def xǁDarkColorProfileǁ__init____mutmut_12(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            )
    
    xǁDarkColorProfileǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDarkColorProfileǁ__init____mutmut_1': xǁDarkColorProfileǁ__init____mutmut_1, 
        'xǁDarkColorProfileǁ__init____mutmut_2': xǁDarkColorProfileǁ__init____mutmut_2, 
        'xǁDarkColorProfileǁ__init____mutmut_3': xǁDarkColorProfileǁ__init____mutmut_3, 
        'xǁDarkColorProfileǁ__init____mutmut_4': xǁDarkColorProfileǁ__init____mutmut_4, 
        'xǁDarkColorProfileǁ__init____mutmut_5': xǁDarkColorProfileǁ__init____mutmut_5, 
        'xǁDarkColorProfileǁ__init____mutmut_6': xǁDarkColorProfileǁ__init____mutmut_6, 
        'xǁDarkColorProfileǁ__init____mutmut_7': xǁDarkColorProfileǁ__init____mutmut_7, 
        'xǁDarkColorProfileǁ__init____mutmut_8': xǁDarkColorProfileǁ__init____mutmut_8, 
        'xǁDarkColorProfileǁ__init____mutmut_9': xǁDarkColorProfileǁ__init____mutmut_9, 
        'xǁDarkColorProfileǁ__init____mutmut_10': xǁDarkColorProfileǁ__init____mutmut_10, 
        'xǁDarkColorProfileǁ__init____mutmut_11': xǁDarkColorProfileǁ__init____mutmut_11, 
        'xǁDarkColorProfileǁ__init____mutmut_12': xǁDarkColorProfileǁ__init____mutmut_12
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDarkColorProfileǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁDarkColorProfileǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁDarkColorProfileǁ__init____mutmut_orig)
    xǁDarkColorProfileǁ__init____mutmut_orig.__name__ = 'xǁDarkColorProfileǁ__init__'


class LightColorProfile(ColorProfile):
    """Light theme color profile - darker colors on light background."""
    
    def xǁLightColorProfileǁ__init____mutmut_orig(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_1(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=None,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_2(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=None,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_3(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=None,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_4(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=None,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_5(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=None,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_6(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=None
        )
    
    def xǁLightColorProfileǁ__init____mutmut_7(self):
        """Initialize light color profile."""
        super().__init__(
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_8(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_9(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_10(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_11(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            error_indicator=ANSI_RED
        )
    
    def xǁLightColorProfileǁ__init____mutmut_12(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            )
    
    xǁLightColorProfileǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁLightColorProfileǁ__init____mutmut_1': xǁLightColorProfileǁ__init____mutmut_1, 
        'xǁLightColorProfileǁ__init____mutmut_2': xǁLightColorProfileǁ__init____mutmut_2, 
        'xǁLightColorProfileǁ__init____mutmut_3': xǁLightColorProfileǁ__init____mutmut_3, 
        'xǁLightColorProfileǁ__init____mutmut_4': xǁLightColorProfileǁ__init____mutmut_4, 
        'xǁLightColorProfileǁ__init____mutmut_5': xǁLightColorProfileǁ__init____mutmut_5, 
        'xǁLightColorProfileǁ__init____mutmut_6': xǁLightColorProfileǁ__init____mutmut_6, 
        'xǁLightColorProfileǁ__init____mutmut_7': xǁLightColorProfileǁ__init____mutmut_7, 
        'xǁLightColorProfileǁ__init____mutmut_8': xǁLightColorProfileǁ__init____mutmut_8, 
        'xǁLightColorProfileǁ__init____mutmut_9': xǁLightColorProfileǁ__init____mutmut_9, 
        'xǁLightColorProfileǁ__init____mutmut_10': xǁLightColorProfileǁ__init____mutmut_10, 
        'xǁLightColorProfileǁ__init____mutmut_11': xǁLightColorProfileǁ__init____mutmut_11, 
        'xǁLightColorProfileǁ__init____mutmut_12': xǁLightColorProfileǁ__init____mutmut_12
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁLightColorProfileǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁLightColorProfileǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁLightColorProfileǁ__init____mutmut_orig)
    xǁLightColorProfileǁ__init____mutmut_orig.__name__ = 'xǁLightColorProfileǁ__init__'


class CustomColorProfile(ColorProfile):
    """Custom color profile with user-defined colors."""
    
    def xǁCustomColorProfileǁ__init____mutmut_orig(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_1(
        self,
        brocaos_prompt: str = "XXXX",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_2(
        self,
        brocaos_prompt: str = "",
        response_text: str = "XXXX",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_3(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "XXXX",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_4(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "XXXX",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_5(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "XXXX",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_6(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = "XXXX"
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_7(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=None,
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_8(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=None,
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_9(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=None,
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_10(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=None,
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_11(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=None,
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_12(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=None
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_13(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_14(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_15(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_16(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_17(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_18(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            )
    
    def xǁCustomColorProfileǁ__init____mutmut_19(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt and "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_20(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "XXXX",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_21(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text and "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_22(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "XXXX",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_23(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt and "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_24(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "XXXX",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_25(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text and "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_26(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "XXXX",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_27(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator and "",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_28(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "XXXX",
            error_indicator=error_indicator or ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_29(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator and ""
        )
    
    def xǁCustomColorProfileǁ__init____mutmut_30(
        self,
        brocaos_prompt: str = "",
        response_text: str = "",
        you_prompt: str = "",
        input_text: str = "",
        success_indicator: str = "",
        error_indicator: str = ""
    ):
        """
        Initialize custom color profile.
        
        Args:
            brocaos_prompt: Custom ANSI color code for BrocaOS prompt
            response_text: Custom ANSI color code for response text
            you_prompt: Custom ANSI color code for you prompt
            input_text: Custom ANSI color code for input text
            success_indicator: Custom ANSI color code for success indicator
            error_indicator: Custom ANSI color code for error indicator
        """
        super().__init__(
            brocaos_prompt=brocaos_prompt or "",
            response_text=response_text or "",
            you_prompt=you_prompt or "",
            input_text=input_text or "",
            success_indicator=success_indicator or "",
            error_indicator=error_indicator or "XXXX"
        )
    
    xǁCustomColorProfileǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁCustomColorProfileǁ__init____mutmut_1': xǁCustomColorProfileǁ__init____mutmut_1, 
        'xǁCustomColorProfileǁ__init____mutmut_2': xǁCustomColorProfileǁ__init____mutmut_2, 
        'xǁCustomColorProfileǁ__init____mutmut_3': xǁCustomColorProfileǁ__init____mutmut_3, 
        'xǁCustomColorProfileǁ__init____mutmut_4': xǁCustomColorProfileǁ__init____mutmut_4, 
        'xǁCustomColorProfileǁ__init____mutmut_5': xǁCustomColorProfileǁ__init____mutmut_5, 
        'xǁCustomColorProfileǁ__init____mutmut_6': xǁCustomColorProfileǁ__init____mutmut_6, 
        'xǁCustomColorProfileǁ__init____mutmut_7': xǁCustomColorProfileǁ__init____mutmut_7, 
        'xǁCustomColorProfileǁ__init____mutmut_8': xǁCustomColorProfileǁ__init____mutmut_8, 
        'xǁCustomColorProfileǁ__init____mutmut_9': xǁCustomColorProfileǁ__init____mutmut_9, 
        'xǁCustomColorProfileǁ__init____mutmut_10': xǁCustomColorProfileǁ__init____mutmut_10, 
        'xǁCustomColorProfileǁ__init____mutmut_11': xǁCustomColorProfileǁ__init____mutmut_11, 
        'xǁCustomColorProfileǁ__init____mutmut_12': xǁCustomColorProfileǁ__init____mutmut_12, 
        'xǁCustomColorProfileǁ__init____mutmut_13': xǁCustomColorProfileǁ__init____mutmut_13, 
        'xǁCustomColorProfileǁ__init____mutmut_14': xǁCustomColorProfileǁ__init____mutmut_14, 
        'xǁCustomColorProfileǁ__init____mutmut_15': xǁCustomColorProfileǁ__init____mutmut_15, 
        'xǁCustomColorProfileǁ__init____mutmut_16': xǁCustomColorProfileǁ__init____mutmut_16, 
        'xǁCustomColorProfileǁ__init____mutmut_17': xǁCustomColorProfileǁ__init____mutmut_17, 
        'xǁCustomColorProfileǁ__init____mutmut_18': xǁCustomColorProfileǁ__init____mutmut_18, 
        'xǁCustomColorProfileǁ__init____mutmut_19': xǁCustomColorProfileǁ__init____mutmut_19, 
        'xǁCustomColorProfileǁ__init____mutmut_20': xǁCustomColorProfileǁ__init____mutmut_20, 
        'xǁCustomColorProfileǁ__init____mutmut_21': xǁCustomColorProfileǁ__init____mutmut_21, 
        'xǁCustomColorProfileǁ__init____mutmut_22': xǁCustomColorProfileǁ__init____mutmut_22, 
        'xǁCustomColorProfileǁ__init____mutmut_23': xǁCustomColorProfileǁ__init____mutmut_23, 
        'xǁCustomColorProfileǁ__init____mutmut_24': xǁCustomColorProfileǁ__init____mutmut_24, 
        'xǁCustomColorProfileǁ__init____mutmut_25': xǁCustomColorProfileǁ__init____mutmut_25, 
        'xǁCustomColorProfileǁ__init____mutmut_26': xǁCustomColorProfileǁ__init____mutmut_26, 
        'xǁCustomColorProfileǁ__init____mutmut_27': xǁCustomColorProfileǁ__init____mutmut_27, 
        'xǁCustomColorProfileǁ__init____mutmut_28': xǁCustomColorProfileǁ__init____mutmut_28, 
        'xǁCustomColorProfileǁ__init____mutmut_29': xǁCustomColorProfileǁ__init____mutmut_29, 
        'xǁCustomColorProfileǁ__init____mutmut_30': xǁCustomColorProfileǁ__init____mutmut_30
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁCustomColorProfileǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁCustomColorProfileǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁCustomColorProfileǁ__init____mutmut_orig)
    xǁCustomColorProfileǁ__init____mutmut_orig.__name__ = 'xǁCustomColorProfileǁ__init__'


class ColorManager:
    """
    Manages color profiles and applies colors to text.
    
    Handles terminal detection, profile switching, and color application.
    """
    
    def xǁColorManagerǁ__init____mutmut_orig(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_1(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = None
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_2(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is not None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_3(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = None
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_4(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(None, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_5(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, None) else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_6(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr('isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_7(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, ) else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_8(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'XXisattyXX') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_9(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'ISATTY') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_10(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else True
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_11(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = None
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_12(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "XXdefaultXX": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_13(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "DEFAULT": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_14(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "XXdarkXX": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_15(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "DARK": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_16(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "XXlightXX": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_17(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "LIGHT": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_18(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = None
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_19(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get(None)
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_20(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("XXdefaultXX")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_21(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("DEFAULT")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_22(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = ""
        self._using_custom: bool = False  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_23(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = None  # Track if we're using custom profile
    
    def xǁColorManagerǁ__init____mutmut_24(self, enabled: Optional[bool] = None):
        """
        Initialize color manager.
        
        Args:
            enabled: Whether colors are enabled (auto-detects TTY if None)
        """
        self._enabled = enabled
        if self._enabled is None:
            self._enabled = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False
        
        # Initialize profiles
        self._profiles: Dict[str, ColorProfile] = {
            "default": DefaultColorProfile(),
            "dark": DarkColorProfile(),
            "light": LightColorProfile(),
        }
        
        self._active_profile: Optional[ColorProfile] = self._profiles.get("default")
        self._custom_profile: Optional[CustomColorProfile] = None
        self._using_custom: bool = True  # Track if we're using custom profile
    
    xǁColorManagerǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorManagerǁ__init____mutmut_1': xǁColorManagerǁ__init____mutmut_1, 
        'xǁColorManagerǁ__init____mutmut_2': xǁColorManagerǁ__init____mutmut_2, 
        'xǁColorManagerǁ__init____mutmut_3': xǁColorManagerǁ__init____mutmut_3, 
        'xǁColorManagerǁ__init____mutmut_4': xǁColorManagerǁ__init____mutmut_4, 
        'xǁColorManagerǁ__init____mutmut_5': xǁColorManagerǁ__init____mutmut_5, 
        'xǁColorManagerǁ__init____mutmut_6': xǁColorManagerǁ__init____mutmut_6, 
        'xǁColorManagerǁ__init____mutmut_7': xǁColorManagerǁ__init____mutmut_7, 
        'xǁColorManagerǁ__init____mutmut_8': xǁColorManagerǁ__init____mutmut_8, 
        'xǁColorManagerǁ__init____mutmut_9': xǁColorManagerǁ__init____mutmut_9, 
        'xǁColorManagerǁ__init____mutmut_10': xǁColorManagerǁ__init____mutmut_10, 
        'xǁColorManagerǁ__init____mutmut_11': xǁColorManagerǁ__init____mutmut_11, 
        'xǁColorManagerǁ__init____mutmut_12': xǁColorManagerǁ__init____mutmut_12, 
        'xǁColorManagerǁ__init____mutmut_13': xǁColorManagerǁ__init____mutmut_13, 
        'xǁColorManagerǁ__init____mutmut_14': xǁColorManagerǁ__init____mutmut_14, 
        'xǁColorManagerǁ__init____mutmut_15': xǁColorManagerǁ__init____mutmut_15, 
        'xǁColorManagerǁ__init____mutmut_16': xǁColorManagerǁ__init____mutmut_16, 
        'xǁColorManagerǁ__init____mutmut_17': xǁColorManagerǁ__init____mutmut_17, 
        'xǁColorManagerǁ__init____mutmut_18': xǁColorManagerǁ__init____mutmut_18, 
        'xǁColorManagerǁ__init____mutmut_19': xǁColorManagerǁ__init____mutmut_19, 
        'xǁColorManagerǁ__init____mutmut_20': xǁColorManagerǁ__init____mutmut_20, 
        'xǁColorManagerǁ__init____mutmut_21': xǁColorManagerǁ__init____mutmut_21, 
        'xǁColorManagerǁ__init____mutmut_22': xǁColorManagerǁ__init____mutmut_22, 
        'xǁColorManagerǁ__init____mutmut_23': xǁColorManagerǁ__init____mutmut_23, 
        'xǁColorManagerǁ__init____mutmut_24': xǁColorManagerǁ__init____mutmut_24
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorManagerǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁColorManagerǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁColorManagerǁ__init____mutmut_orig)
    xǁColorManagerǁ__init____mutmut_orig.__name__ = 'xǁColorManagerǁ__init__'
    
    def xǁColorManagerǁget_profile__mutmut_orig(self, profile_name: str) -> Optional[ColorProfile]:
        """
        Get a color profile by name.
        
        Args:
            profile_name: Name of profile ("default", "dark", "light", "custom")
            
        Returns:
            ColorProfile instance or None if not found
        """
        if profile_name == "custom" and self._custom_profile:
            return self._custom_profile
        return self._profiles.get(profile_name)
    
    def xǁColorManagerǁget_profile__mutmut_1(self, profile_name: str) -> Optional[ColorProfile]:
        """
        Get a color profile by name.
        
        Args:
            profile_name: Name of profile ("default", "dark", "light", "custom")
            
        Returns:
            ColorProfile instance or None if not found
        """
        if profile_name == "custom" or self._custom_profile:
            return self._custom_profile
        return self._profiles.get(profile_name)
    
    def xǁColorManagerǁget_profile__mutmut_2(self, profile_name: str) -> Optional[ColorProfile]:
        """
        Get a color profile by name.
        
        Args:
            profile_name: Name of profile ("default", "dark", "light", "custom")
            
        Returns:
            ColorProfile instance or None if not found
        """
        if profile_name != "custom" and self._custom_profile:
            return self._custom_profile
        return self._profiles.get(profile_name)
    
    def xǁColorManagerǁget_profile__mutmut_3(self, profile_name: str) -> Optional[ColorProfile]:
        """
        Get a color profile by name.
        
        Args:
            profile_name: Name of profile ("default", "dark", "light", "custom")
            
        Returns:
            ColorProfile instance or None if not found
        """
        if profile_name == "XXcustomXX" and self._custom_profile:
            return self._custom_profile
        return self._profiles.get(profile_name)
    
    def xǁColorManagerǁget_profile__mutmut_4(self, profile_name: str) -> Optional[ColorProfile]:
        """
        Get a color profile by name.
        
        Args:
            profile_name: Name of profile ("default", "dark", "light", "custom")
            
        Returns:
            ColorProfile instance or None if not found
        """
        if profile_name == "CUSTOM" and self._custom_profile:
            return self._custom_profile
        return self._profiles.get(profile_name)
    
    def xǁColorManagerǁget_profile__mutmut_5(self, profile_name: str) -> Optional[ColorProfile]:
        """
        Get a color profile by name.
        
        Args:
            profile_name: Name of profile ("default", "dark", "light", "custom")
            
        Returns:
            ColorProfile instance or None if not found
        """
        if profile_name == "custom" and self._custom_profile:
            return self._custom_profile
        return self._profiles.get(None)
    
    xǁColorManagerǁget_profile__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorManagerǁget_profile__mutmut_1': xǁColorManagerǁget_profile__mutmut_1, 
        'xǁColorManagerǁget_profile__mutmut_2': xǁColorManagerǁget_profile__mutmut_2, 
        'xǁColorManagerǁget_profile__mutmut_3': xǁColorManagerǁget_profile__mutmut_3, 
        'xǁColorManagerǁget_profile__mutmut_4': xǁColorManagerǁget_profile__mutmut_4, 
        'xǁColorManagerǁget_profile__mutmut_5': xǁColorManagerǁget_profile__mutmut_5
    }
    
    def get_profile(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorManagerǁget_profile__mutmut_orig"), object.__getattribute__(self, "xǁColorManagerǁget_profile__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_profile.__signature__ = _mutmut_signature(xǁColorManagerǁget_profile__mutmut_orig)
    xǁColorManagerǁget_profile__mutmut_orig.__name__ = 'xǁColorManagerǁget_profile'
    
    def xǁColorManagerǁset_profile__mutmut_orig(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_1(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name != "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_2(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "XXcustomXX":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_3(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "CUSTOM":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_4(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = None
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_5(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = None
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_6(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = False
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_7(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = None
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_8(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get(None)
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_9(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("XXdefaultXX")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_10(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("DEFAULT")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_11(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = None
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_12(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = True
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_13(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = None
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_14(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(None)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_15(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = None
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_16(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = None
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_17(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = True
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_18(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = None
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_19(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get(None)
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_20(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("XXdefaultXX")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_21(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("DEFAULT")
                self._using_custom = False
    
    def xǁColorManagerǁset_profile__mutmut_22(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = None
    
    def xǁColorManagerǁset_profile__mutmut_23(self, profile_name: str) -> None:
        """
        Set active color profile.
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name == "custom":
            if self._custom_profile:
                self._active_profile = self._custom_profile
                self._using_custom = True
            else:
                # Fallback to default if custom not set
                self._active_profile = self._profiles.get("default")
                self._using_custom = False
        else:
            profile = self._profiles.get(profile_name)
            if profile:
                self._active_profile = profile
                self._using_custom = False
            else:
                # Fallback to default if profile not found
                self._active_profile = self._profiles.get("default")
                self._using_custom = True
    
    xǁColorManagerǁset_profile__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorManagerǁset_profile__mutmut_1': xǁColorManagerǁset_profile__mutmut_1, 
        'xǁColorManagerǁset_profile__mutmut_2': xǁColorManagerǁset_profile__mutmut_2, 
        'xǁColorManagerǁset_profile__mutmut_3': xǁColorManagerǁset_profile__mutmut_3, 
        'xǁColorManagerǁset_profile__mutmut_4': xǁColorManagerǁset_profile__mutmut_4, 
        'xǁColorManagerǁset_profile__mutmut_5': xǁColorManagerǁset_profile__mutmut_5, 
        'xǁColorManagerǁset_profile__mutmut_6': xǁColorManagerǁset_profile__mutmut_6, 
        'xǁColorManagerǁset_profile__mutmut_7': xǁColorManagerǁset_profile__mutmut_7, 
        'xǁColorManagerǁset_profile__mutmut_8': xǁColorManagerǁset_profile__mutmut_8, 
        'xǁColorManagerǁset_profile__mutmut_9': xǁColorManagerǁset_profile__mutmut_9, 
        'xǁColorManagerǁset_profile__mutmut_10': xǁColorManagerǁset_profile__mutmut_10, 
        'xǁColorManagerǁset_profile__mutmut_11': xǁColorManagerǁset_profile__mutmut_11, 
        'xǁColorManagerǁset_profile__mutmut_12': xǁColorManagerǁset_profile__mutmut_12, 
        'xǁColorManagerǁset_profile__mutmut_13': xǁColorManagerǁset_profile__mutmut_13, 
        'xǁColorManagerǁset_profile__mutmut_14': xǁColorManagerǁset_profile__mutmut_14, 
        'xǁColorManagerǁset_profile__mutmut_15': xǁColorManagerǁset_profile__mutmut_15, 
        'xǁColorManagerǁset_profile__mutmut_16': xǁColorManagerǁset_profile__mutmut_16, 
        'xǁColorManagerǁset_profile__mutmut_17': xǁColorManagerǁset_profile__mutmut_17, 
        'xǁColorManagerǁset_profile__mutmut_18': xǁColorManagerǁset_profile__mutmut_18, 
        'xǁColorManagerǁset_profile__mutmut_19': xǁColorManagerǁset_profile__mutmut_19, 
        'xǁColorManagerǁset_profile__mutmut_20': xǁColorManagerǁset_profile__mutmut_20, 
        'xǁColorManagerǁset_profile__mutmut_21': xǁColorManagerǁset_profile__mutmut_21, 
        'xǁColorManagerǁset_profile__mutmut_22': xǁColorManagerǁset_profile__mutmut_22, 
        'xǁColorManagerǁset_profile__mutmut_23': xǁColorManagerǁset_profile__mutmut_23
    }
    
    def set_profile(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorManagerǁset_profile__mutmut_orig"), object.__getattribute__(self, "xǁColorManagerǁset_profile__mutmut_mutants"), args, kwargs, self)
        return result 
    
    set_profile.__signature__ = _mutmut_signature(xǁColorManagerǁset_profile__mutmut_orig)
    xǁColorManagerǁset_profile__mutmut_orig.__name__ = 'xǁColorManagerǁset_profile'
    
    def xǁColorManagerǁset_custom_profile__mutmut_orig(self, profile: CustomColorProfile) -> None:
        """
        Set custom color profile.
        
        Args:
            profile: CustomColorProfile instance
        """
        self._custom_profile = profile
        # If currently using custom profile or no active profile, update it
        if self._using_custom or not self._active_profile:
            self._active_profile = profile
    
    def xǁColorManagerǁset_custom_profile__mutmut_1(self, profile: CustomColorProfile) -> None:
        """
        Set custom color profile.
        
        Args:
            profile: CustomColorProfile instance
        """
        self._custom_profile = None
        # If currently using custom profile or no active profile, update it
        if self._using_custom or not self._active_profile:
            self._active_profile = profile
    
    def xǁColorManagerǁset_custom_profile__mutmut_2(self, profile: CustomColorProfile) -> None:
        """
        Set custom color profile.
        
        Args:
            profile: CustomColorProfile instance
        """
        self._custom_profile = profile
        # If currently using custom profile or no active profile, update it
        if self._using_custom and not self._active_profile:
            self._active_profile = profile
    
    def xǁColorManagerǁset_custom_profile__mutmut_3(self, profile: CustomColorProfile) -> None:
        """
        Set custom color profile.
        
        Args:
            profile: CustomColorProfile instance
        """
        self._custom_profile = profile
        # If currently using custom profile or no active profile, update it
        if self._using_custom or self._active_profile:
            self._active_profile = profile
    
    def xǁColorManagerǁset_custom_profile__mutmut_4(self, profile: CustomColorProfile) -> None:
        """
        Set custom color profile.
        
        Args:
            profile: CustomColorProfile instance
        """
        self._custom_profile = profile
        # If currently using custom profile or no active profile, update it
        if self._using_custom or not self._active_profile:
            self._active_profile = None
    
    xǁColorManagerǁset_custom_profile__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorManagerǁset_custom_profile__mutmut_1': xǁColorManagerǁset_custom_profile__mutmut_1, 
        'xǁColorManagerǁset_custom_profile__mutmut_2': xǁColorManagerǁset_custom_profile__mutmut_2, 
        'xǁColorManagerǁset_custom_profile__mutmut_3': xǁColorManagerǁset_custom_profile__mutmut_3, 
        'xǁColorManagerǁset_custom_profile__mutmut_4': xǁColorManagerǁset_custom_profile__mutmut_4
    }
    
    def set_custom_profile(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorManagerǁset_custom_profile__mutmut_orig"), object.__getattribute__(self, "xǁColorManagerǁset_custom_profile__mutmut_mutants"), args, kwargs, self)
        return result 
    
    set_custom_profile.__signature__ = _mutmut_signature(xǁColorManagerǁset_custom_profile__mutmut_orig)
    xǁColorManagerǁset_custom_profile__mutmut_orig.__name__ = 'xǁColorManagerǁset_custom_profile'
    
    def xǁColorManagerǁcolorize__mutmut_orig(self, text: str, color_type: str) -> str:
        """
        Apply color to text using active profile.
        
        Args:
            text: Text to colorize
            color_type: Type of color ("brocaos_prompt", "response_text", "you_prompt", "input_text", "success_indicator", "error_indicator")
            
        Returns:
            Colorized text if enabled, original text otherwise
        """
        if not self._enabled or not self._active_profile:
            return text
        
        try:
            return self._active_profile.apply_color(text, color_type)
        except (AttributeError, KeyError):
            # Graceful degradation - return original text
            return text
    
    def xǁColorManagerǁcolorize__mutmut_1(self, text: str, color_type: str) -> str:
        """
        Apply color to text using active profile.
        
        Args:
            text: Text to colorize
            color_type: Type of color ("brocaos_prompt", "response_text", "you_prompt", "input_text", "success_indicator", "error_indicator")
            
        Returns:
            Colorized text if enabled, original text otherwise
        """
        if not self._enabled and not self._active_profile:
            return text
        
        try:
            return self._active_profile.apply_color(text, color_type)
        except (AttributeError, KeyError):
            # Graceful degradation - return original text
            return text
    
    def xǁColorManagerǁcolorize__mutmut_2(self, text: str, color_type: str) -> str:
        """
        Apply color to text using active profile.
        
        Args:
            text: Text to colorize
            color_type: Type of color ("brocaos_prompt", "response_text", "you_prompt", "input_text", "success_indicator", "error_indicator")
            
        Returns:
            Colorized text if enabled, original text otherwise
        """
        if self._enabled or not self._active_profile:
            return text
        
        try:
            return self._active_profile.apply_color(text, color_type)
        except (AttributeError, KeyError):
            # Graceful degradation - return original text
            return text
    
    def xǁColorManagerǁcolorize__mutmut_3(self, text: str, color_type: str) -> str:
        """
        Apply color to text using active profile.
        
        Args:
            text: Text to colorize
            color_type: Type of color ("brocaos_prompt", "response_text", "you_prompt", "input_text", "success_indicator", "error_indicator")
            
        Returns:
            Colorized text if enabled, original text otherwise
        """
        if not self._enabled or self._active_profile:
            return text
        
        try:
            return self._active_profile.apply_color(text, color_type)
        except (AttributeError, KeyError):
            # Graceful degradation - return original text
            return text
    
    def xǁColorManagerǁcolorize__mutmut_4(self, text: str, color_type: str) -> str:
        """
        Apply color to text using active profile.
        
        Args:
            text: Text to colorize
            color_type: Type of color ("brocaos_prompt", "response_text", "you_prompt", "input_text", "success_indicator", "error_indicator")
            
        Returns:
            Colorized text if enabled, original text otherwise
        """
        if not self._enabled or not self._active_profile:
            return text
        
        try:
            return self._active_profile.apply_color(None, color_type)
        except (AttributeError, KeyError):
            # Graceful degradation - return original text
            return text
    
    def xǁColorManagerǁcolorize__mutmut_5(self, text: str, color_type: str) -> str:
        """
        Apply color to text using active profile.
        
        Args:
            text: Text to colorize
            color_type: Type of color ("brocaos_prompt", "response_text", "you_prompt", "input_text", "success_indicator", "error_indicator")
            
        Returns:
            Colorized text if enabled, original text otherwise
        """
        if not self._enabled or not self._active_profile:
            return text
        
        try:
            return self._active_profile.apply_color(text, None)
        except (AttributeError, KeyError):
            # Graceful degradation - return original text
            return text
    
    def xǁColorManagerǁcolorize__mutmut_6(self, text: str, color_type: str) -> str:
        """
        Apply color to text using active profile.
        
        Args:
            text: Text to colorize
            color_type: Type of color ("brocaos_prompt", "response_text", "you_prompt", "input_text", "success_indicator", "error_indicator")
            
        Returns:
            Colorized text if enabled, original text otherwise
        """
        if not self._enabled or not self._active_profile:
            return text
        
        try:
            return self._active_profile.apply_color(color_type)
        except (AttributeError, KeyError):
            # Graceful degradation - return original text
            return text
    
    def xǁColorManagerǁcolorize__mutmut_7(self, text: str, color_type: str) -> str:
        """
        Apply color to text using active profile.
        
        Args:
            text: Text to colorize
            color_type: Type of color ("brocaos_prompt", "response_text", "you_prompt", "input_text", "success_indicator", "error_indicator")
            
        Returns:
            Colorized text if enabled, original text otherwise
        """
        if not self._enabled or not self._active_profile:
            return text
        
        try:
            return self._active_profile.apply_color(text, )
        except (AttributeError, KeyError):
            # Graceful degradation - return original text
            return text
    
    xǁColorManagerǁcolorize__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorManagerǁcolorize__mutmut_1': xǁColorManagerǁcolorize__mutmut_1, 
        'xǁColorManagerǁcolorize__mutmut_2': xǁColorManagerǁcolorize__mutmut_2, 
        'xǁColorManagerǁcolorize__mutmut_3': xǁColorManagerǁcolorize__mutmut_3, 
        'xǁColorManagerǁcolorize__mutmut_4': xǁColorManagerǁcolorize__mutmut_4, 
        'xǁColorManagerǁcolorize__mutmut_5': xǁColorManagerǁcolorize__mutmut_5, 
        'xǁColorManagerǁcolorize__mutmut_6': xǁColorManagerǁcolorize__mutmut_6, 
        'xǁColorManagerǁcolorize__mutmut_7': xǁColorManagerǁcolorize__mutmut_7
    }
    
    def colorize(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorManagerǁcolorize__mutmut_orig"), object.__getattribute__(self, "xǁColorManagerǁcolorize__mutmut_mutants"), args, kwargs, self)
        return result 
    
    colorize.__signature__ = _mutmut_signature(xǁColorManagerǁcolorize__mutmut_orig)
    xǁColorManagerǁcolorize__mutmut_orig.__name__ = 'xǁColorManagerǁcolorize'
    
    def is_enabled(self) -> bool:
        """Check if colors are enabled."""
        return self._enabled
    
    def xǁColorManagerǁdisable__mutmut_orig(self) -> None:
        """Disable colors."""
        self._enabled = False
    
    def xǁColorManagerǁdisable__mutmut_1(self) -> None:
        """Disable colors."""
        self._enabled = None
    
    def xǁColorManagerǁdisable__mutmut_2(self) -> None:
        """Disable colors."""
        self._enabled = True
    
    xǁColorManagerǁdisable__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorManagerǁdisable__mutmut_1': xǁColorManagerǁdisable__mutmut_1, 
        'xǁColorManagerǁdisable__mutmut_2': xǁColorManagerǁdisable__mutmut_2
    }
    
    def disable(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorManagerǁdisable__mutmut_orig"), object.__getattribute__(self, "xǁColorManagerǁdisable__mutmut_mutants"), args, kwargs, self)
        return result 
    
    disable.__signature__ = _mutmut_signature(xǁColorManagerǁdisable__mutmut_orig)
    xǁColorManagerǁdisable__mutmut_orig.__name__ = 'xǁColorManagerǁdisable'
    
    def xǁColorManagerǁenable__mutmut_orig(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False:
            self._enabled = True
    
    def xǁColorManagerǁenable__mutmut_1(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(None, 'isatty') else False:
            self._enabled = True
    
    def xǁColorManagerǁenable__mutmut_2(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, None) else False:
            self._enabled = True
    
    def xǁColorManagerǁenable__mutmut_3(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr('isatty') else False:
            self._enabled = True
    
    def xǁColorManagerǁenable__mutmut_4(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, ) else False:
            self._enabled = True
    
    def xǁColorManagerǁenable__mutmut_5(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, 'XXisattyXX') else False:
            self._enabled = True
    
    def xǁColorManagerǁenable__mutmut_6(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, 'ISATTY') else False:
            self._enabled = True
    
    def xǁColorManagerǁenable__mutmut_7(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else True:
            self._enabled = True
    
    def xǁColorManagerǁenable__mutmut_8(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False:
            self._enabled = None
    
    def xǁColorManagerǁenable__mutmut_9(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False:
            self._enabled = False
    
    xǁColorManagerǁenable__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁColorManagerǁenable__mutmut_1': xǁColorManagerǁenable__mutmut_1, 
        'xǁColorManagerǁenable__mutmut_2': xǁColorManagerǁenable__mutmut_2, 
        'xǁColorManagerǁenable__mutmut_3': xǁColorManagerǁenable__mutmut_3, 
        'xǁColorManagerǁenable__mutmut_4': xǁColorManagerǁenable__mutmut_4, 
        'xǁColorManagerǁenable__mutmut_5': xǁColorManagerǁenable__mutmut_5, 
        'xǁColorManagerǁenable__mutmut_6': xǁColorManagerǁenable__mutmut_6, 
        'xǁColorManagerǁenable__mutmut_7': xǁColorManagerǁenable__mutmut_7, 
        'xǁColorManagerǁenable__mutmut_8': xǁColorManagerǁenable__mutmut_8, 
        'xǁColorManagerǁenable__mutmut_9': xǁColorManagerǁenable__mutmut_9
    }
    
    def enable(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁColorManagerǁenable__mutmut_orig"), object.__getattribute__(self, "xǁColorManagerǁenable__mutmut_mutants"), args, kwargs, self)
        return result 
    
    enable.__signature__ = _mutmut_signature(xǁColorManagerǁenable__mutmut_orig)
    xǁColorManagerǁenable__mutmut_orig.__name__ = 'xǁColorManagerǁenable'

