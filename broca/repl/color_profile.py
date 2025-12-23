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


def ansi_color(code: int, use_256: bool = False) -> str:
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
    
    def __init__(
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
    
    def apply_color(self, text: str, color_type: str) -> str:
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


class DefaultColorProfile(ColorProfile):
    """Default color profile - subtle colors."""
    
    def __init__(self):
        """Initialize default color profile."""
        super().__init__(
            brocaos_prompt=ANSI_CYAN,
            response_text=ANSI_RESET,  # Default text color
            you_prompt=ANSI_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,  # Distinct color for user input (different from default and prompt)
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )


class DarkColorProfile(ColorProfile):
    """Dark theme color profile - bright colors on dark background."""
    
    def __init__(self):
        """Initialize dark color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BRIGHT_CYAN,
            response_text=ANSI_BRIGHT_WHITE,
            you_prompt=ANSI_BRIGHT_YELLOW,
            input_text=ANSI_BRIGHT_GREEN,
            success_indicator=ANSI_BRIGHT_GREEN,
            error_indicator=ANSI_BRIGHT_RED
        )


class LightColorProfile(ColorProfile):
    """Light theme color profile - darker colors on light background."""
    
    def __init__(self):
        """Initialize light color profile."""
        super().__init__(
            brocaos_prompt=ANSI_BLUE,
            response_text=ANSI_BLACK,
            you_prompt=ANSI_MAGENTA,
            input_text=ANSI_BLACK,
            success_indicator=ANSI_GREEN,
            error_indicator=ANSI_RED
        )


class CustomColorProfile(ColorProfile):
    """Custom color profile with user-defined colors."""
    
    def __init__(
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


class ColorManager:
    """
    Manages color profiles and applies colors to text.
    
    Handles terminal detection, profile switching, and color application.
    """
    
    def __init__(self, enabled: Optional[bool] = None):
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
    
    def get_profile(self, profile_name: str) -> Optional[ColorProfile]:
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
    
    def set_profile(self, profile_name: str) -> None:
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
    
    def set_custom_profile(self, profile: CustomColorProfile) -> None:
        """
        Set custom color profile.
        
        Args:
            profile: CustomColorProfile instance
        """
        self._custom_profile = profile
        # If currently using custom profile or no active profile, update it
        if self._using_custom or not self._active_profile:
            self._active_profile = profile
    
    def colorize(self, text: str, color_type: str) -> str:
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
    
    def is_enabled(self) -> bool:
        """Check if colors are enabled."""
        return self._enabled
    
    def disable(self) -> None:
        """Disable colors."""
        self._enabled = False
    
    def enable(self) -> None:
        """Enable colors (if terminal supports it)."""
        if sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False:
            self._enabled = True

