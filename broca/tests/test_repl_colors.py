"""
Tests for REPL color differentiation.

Tests that colors are properly differentiated between BrocaOS prompt,
user input text, and default terminal color.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from broca.repl.color_profile import (
    ColorManager,
    DefaultColorProfile,
    DarkColorProfile,
    LightColorProfile,
    CustomColorProfile,
    ANSI_RESET,
    ANSI_CYAN,
    ANSI_BRIGHT_GREEN,
    ANSI_MAGENTA,
)


class TestColorDifferentiation:
    """Test that colors are distinct and properly differentiated."""
    
    def test_default_profile_colors_are_distinct(self):
        """
        Test that DefaultColorProfile has distinct colors for all elements.
        
        Rationale: Ensures BrocaOS prompt and input text have different colors.
        """
        profile = DefaultColorProfile()
        
        # BrocaOS prompt should have a color (not empty/reset)
        assert profile.brocaos_prompt != ""
        assert profile.brocaos_prompt != ANSI_RESET
        
        # Input text should have a distinct color (not empty/reset, not same as prompt)
        assert profile.input_text != ""
        assert profile.input_text != ANSI_RESET
        assert profile.input_text != profile.brocaos_prompt
        
        # Response text can be reset (default), but prompt and input should differ
        # Verify all required colors are set
        assert hasattr(profile, 'brocaos_prompt')
        assert hasattr(profile, 'response_text')
        assert hasattr(profile, 'you_prompt')
        assert hasattr(profile, 'input_text')
    
    def test_default_profile_input_text_is_colored(self):
        """
        Test that input_text in DefaultColorProfile is not ANSI_RESET.
        
        Rationale: Input text should be visually distinct from default terminal color.
        """
        profile = DefaultColorProfile()
        
        # Input text should have a color code, not be reset
        assert profile.input_text != ANSI_RESET
        assert profile.input_text != ""
        
        # Should be a valid ANSI color code
        assert profile.input_text.startswith('\033[')
    
    def test_brocaos_prompt_is_colored(self):
        """
        Test that BrocaOS prompt has a color in default profile.
        
        Rationale: BrocaOS prompt should be visually distinct.
        """
        profile = DefaultColorProfile()
        
        assert profile.brocaos_prompt != ""
        assert profile.brocaos_prompt != ANSI_RESET
        assert profile.brocaos_prompt.startswith('\033[')
    
    def test_colors_apply_correctly(self):
        """
        Test that colors are applied correctly by ColorManager.
        
        Rationale: Ensures colorization works as expected.
        """
        manager = ColorManager(enabled=True)
        manager.set_profile("default")
        
        # Colorize should return colored text
        colored_prompt = manager.colorize("BrocaOS> ", "brocaos_prompt")
        colored_input = manager.colorize("user input", "input_text")
        
        # Should contain ANSI codes
        assert '\033[' in colored_prompt
        assert '\033[' in colored_input
        
        # Should be different (different colors applied)
        assert colored_prompt != colored_input
    
    def test_all_profiles_have_distinct_input_text(self):
        """
        Test that all color profiles have distinct input_text colors.
        
        Rationale: Ensures consistency across all profiles.
        """
        profiles = [
            DefaultColorProfile(),
            DarkColorProfile(),
            LightColorProfile(),
        ]
        
        for profile in profiles:
            assert profile.input_text != ""
            assert profile.input_text != ANSI_RESET
            assert hasattr(profile, 'input_text')
    
    def test_custom_profile_preserves_colors(self):
        """
        Test that custom profile preserves distinct colors when set.
        
        Rationale: Ensures custom profiles work correctly.
        """
        custom = CustomColorProfile(
            brocaos_prompt=ANSI_CYAN,
            input_text=ANSI_BRIGHT_GREEN,
        )
        
        assert custom.brocaos_prompt == ANSI_CYAN
        assert custom.input_text == ANSI_BRIGHT_GREEN
        assert custom.brocaos_prompt != custom.input_text
        
        manager = ColorManager(enabled=True)
        manager.set_custom_profile(custom)
        manager.set_profile("custom")
        
        colored_prompt = manager.colorize("BrocaOS> ", "brocaos_prompt")
        colored_input = manager.colorize("input", "input_text")
        
        assert ANSI_CYAN in colored_prompt
        assert ANSI_BRIGHT_GREEN in colored_input


# Property-based tests for colors
try:
    from hypothesis import given, strategies as st, settings, HealthCheck
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False


if HAS_HYPOTHESIS:
    class TestPropertyBasedColors:
        """Property-based tests for color differentiation."""
        
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
        @given(
            text=st.text(max_size=200)
        )
        def test_color_application_always_produces_valid_string(self, text):
            """
            Property: Color application always produces a valid string.
            
            Rationale: Ensures colorization never fails or produces invalid output.
            """
            manager = ColorManager(enabled=True)
            manager.set_profile("default")
            
            colored = manager.colorize(text, "input_text")
            
            assert isinstance(colored, str)
            assert len(colored) >= len(text)  # Should contain original text plus possibly ANSI codes

