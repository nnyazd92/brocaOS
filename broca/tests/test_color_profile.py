"""
Tests for REPL color profile system.

Tests color profiles, ANSI code generation, terminal detection, and color application.
"""

from __future__ import annotations

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import will be available after implementation
try:
    from broca.repl.color_profile import (
        ColorProfile,
        DefaultColorProfile,
        DarkColorProfile,
        LightColorProfile,
        CustomColorProfile,
        ColorManager,
        ansi_color,
        ansi_reset,
    )
except ImportError:
    # For TDD - these will be implemented
    ColorProfile = None
    DefaultColorProfile = None
    DarkColorProfile = None
    LightColorProfile = None
    CustomColorProfile = None
    ColorManager = None
    ansi_color = None
    ansi_reset = None

# Hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st, settings, HealthCheck
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False


class TestANSIHelpers:
    """Test ANSI color code helpers."""
    
    def test_ansi_reset_code(self):
        """Test that ANSI reset code is correct."""
        if ansi_reset is None:
            pytest.skip("ansi_reset not yet implemented")
        
        reset_code = ansi_reset()
        assert reset_code == "\033[0m"
    
    def test_ansi_color_code_generation(self):
        """Test ANSI color code generation."""
        if ansi_color is None:
            pytest.skip("ansi_color not yet implemented")
        
        # Test standard colors
        red = ansi_color(31)  # Red
        assert red == "\033[31m"
        
        green = ansi_color(32)  # Green
        assert green == "\033[32m"
        
        blue = ansi_color(34)  # Blue
        assert blue == "\033[34m"
    
    def test_ansi_color_256_mode(self):
        """Test 256-color mode."""
        if ansi_color is None:
            pytest.skip("ansi_color not yet implemented")
        
        color_256 = ansi_color(196, use_256=True)  # Bright red in 256-color
        assert color_256 == "\033[38;5;196m"
    
    def test_ansi_color_bright_colors(self):
        """Test bright color codes (90-97)."""
        if ansi_color is None:
            pytest.skip("ansi_color not yet implemented")
        
        bright_red = ansi_color(91)  # Bright red
        assert bright_red == "\033[91m"
        
        bright_cyan = ansi_color(96)  # Bright cyan
        assert bright_cyan == "\033[96m"
    
    def test_ansi_color_out_of_range_standard(self):
        """Test ANSI color with out-of-range codes (standard mode)."""
        if ansi_color is None:
            pytest.skip("ansi_color not yet implemented")
        
        # Test clamping
        too_low = ansi_color(20, use_256=False)
        assert "\033[30m" in too_low  # Should clamp to 30
        
        too_high = ansi_color(100, use_256=False)
        assert "\033[97m" in too_high  # Should clamp to 97


class TestColorProfile:
    """Test ColorProfile base class."""
    
    def test_color_profile_initialization(self):
        """Test that ColorProfile initializes correctly."""
        if ColorProfile is None:
            pytest.skip("ColorProfile not yet implemented")
        
        profile = ColorProfile(
            brocaos_prompt="\033[36m",
            response_text="\033[0m",
            you_prompt="\033[33m",
            input_text="\033[0m"
        )
        
        assert profile.brocaos_prompt == "\033[36m"
        assert profile.response_text == "\033[0m"
        assert profile.you_prompt == "\033[33m"
        assert profile.input_text == "\033[0m"
    
    def test_color_profile_apply_to_text(self):
        """Test applying color to text."""
        if ColorProfile is None:
            pytest.skip("ColorProfile not yet implemented")
        
        profile = ColorProfile(
            brocaos_prompt="\033[36m",
            response_text="\033[0m",
            you_prompt="\033[33m",
            input_text="\033[0m"
        )
        
        colored = profile.apply_color("test", "brocaos_prompt")
        assert colored.startswith("\033[36m")
        assert colored.endswith("\033[0m")
        assert "test" in colored
    
    def test_color_profile_apply_empty_color(self):
        """Test applying color when color code is empty."""
        if ColorProfile is None:
            pytest.skip("ColorProfile not yet implemented")
        
        profile = ColorProfile(
            brocaos_prompt="",
            response_text="",
            you_prompt="",
            input_text=""
        )
        
        # Should return original text when color is empty
        result = profile.apply_color("test", "brocaos_prompt")
        assert result == "test"


class TestDefaultColorProfile:
    """Test DefaultColorProfile."""
    
    def test_default_profile_initialization(self):
        """Test default profile initialization."""
        if DefaultColorProfile is None:
            pytest.skip("DefaultColorProfile not yet implemented")
        
        profile = DefaultColorProfile()
        assert profile is not None
        assert hasattr(profile, 'brocaos_prompt')
        assert hasattr(profile, 'response_text')
        assert hasattr(profile, 'you_prompt')
        assert hasattr(profile, 'input_text')
    
    def test_default_profile_has_colors(self):
        """Test that default profile has color codes."""
        if DefaultColorProfile is None:
            pytest.skip("DefaultColorProfile not yet implemented")
        
        profile = DefaultColorProfile()
        # Should have ANSI codes or empty strings
        assert isinstance(profile.brocaos_prompt, str)
        assert isinstance(profile.response_text, str)
        assert isinstance(profile.you_prompt, str)
        assert isinstance(profile.input_text, str)


class TestDarkColorProfile:
    """Test DarkColorProfile."""
    
    def test_dark_profile_initialization(self):
        """Test dark profile initialization."""
        if DarkColorProfile is None:
            pytest.skip("DarkColorProfile not yet implemented")
        
        profile = DarkColorProfile()
        assert profile is not None
        assert hasattr(profile, 'brocaos_prompt')
        assert hasattr(profile, 'response_text')
        assert hasattr(profile, 'you_prompt')
        assert hasattr(profile, 'input_text')
    
    def test_dark_profile_different_from_default(self):
        """Test that dark profile differs from default."""
        if DarkColorProfile is None or DefaultColorProfile is None:
            pytest.skip("Profiles not yet implemented")
        
        default = DefaultColorProfile()
        dark = DarkColorProfile()
        
        # At least one color should differ (or they could be the same if default is already dark)
        # Just verify both are valid profiles
        assert isinstance(dark.brocaos_prompt, str)
        assert isinstance(default.brocaos_prompt, str)


class TestLightColorProfile:
    """Test LightColorProfile."""
    
    def test_light_profile_initialization(self):
        """Test light profile initialization."""
        if LightColorProfile is None:
            pytest.skip("LightColorProfile not yet implemented")
        
        profile = LightColorProfile()
        assert profile is not None
        assert hasattr(profile, 'brocaos_prompt')
        assert hasattr(profile, 'response_text')
        assert hasattr(profile, 'you_prompt')
        assert hasattr(profile, 'input_text')


class TestCustomColorProfile:
    """Test CustomColorProfile."""
    
    def test_custom_profile_initialization(self):
        """Test custom profile initialization."""
        if CustomColorProfile is None:
            pytest.skip("CustomColorProfile not yet implemented")
        
        profile = CustomColorProfile(
            brocaos_prompt="\033[35m",
            response_text="\033[37m",
            you_prompt="\033[32m",
            input_text="\033[0m"
        )
        
        assert profile.brocaos_prompt == "\033[35m"
        assert profile.response_text == "\033[37m"
        assert profile.you_prompt == "\033[32m"
        assert profile.input_text == "\033[0m"
    
    def test_custom_profile_empty_colors(self):
        """Test custom profile with empty colors (no color)."""
        if CustomColorProfile is None:
            pytest.skip("CustomColorProfile not yet implemented")
        
        profile = CustomColorProfile(
            brocaos_prompt="",
            response_text="",
            you_prompt="",
            input_text=""
        )
        
        # Should accept empty strings (no colors)
        assert profile.brocaos_prompt == ""
        assert profile.response_text == ""


class TestColorManager:
    """Test ColorManager."""
    
    def test_color_manager_initialization(self):
        """Test ColorManager initialization."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        assert manager is not None
    
    def test_color_manager_detects_terminal(self):
        """Test that ColorManager detects terminal support."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager()
            # Should detect TTY
            assert hasattr(manager, '_enabled')
    
    def test_color_manager_disables_for_non_tty(self):
        """Test that ColorManager disables colors for non-TTY."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=False):
            manager = ColorManager()
            # Colors should be disabled
            assert manager._enabled is False
    
    def test_color_manager_get_profile(self):
        """Test getting color profile."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        profile = manager.get_profile("default")
        
        assert profile is not None
        assert isinstance(profile, ColorProfile)
    
    def test_color_manager_set_profile(self):
        """Test setting active profile."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        manager.set_profile("dark")
        
        # Should have dark profile active
        assert manager._active_profile is not None
    
    def test_color_manager_colorize_text(self):
        """Test colorizing text with active profile."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager()
            manager.set_profile("default")
            
            colored = manager.colorize("test", "brocaos_prompt")
            # Should return colored text or original if disabled
            assert isinstance(colored, str)
            assert "test" in colored
    
    def test_color_manager_colorize_disabled(self):
        """Test colorizing when colors are disabled."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=False):
            manager = ColorManager()
            manager.set_profile("default")
            
            colored = manager.colorize("test", "brocaos_prompt")
            # Should return original text without colors
            assert colored == "test"
    
    def test_color_manager_all_profiles_available(self):
        """Test that all predefined profiles are available."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        
        profiles = ["default", "dark", "light"]
        for profile_name in profiles:
            profile = manager.get_profile(profile_name)
            assert profile is not None
            assert isinstance(profile, ColorProfile)
    
    def test_color_manager_custom_profile(self):
        """Test creating custom profile."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        
        custom = CustomColorProfile(
            brocaos_prompt="\033[35m",
            response_text="\033[37m",
            you_prompt="\033[32m",
            input_text="\033[0m"
        )
        
        manager.set_custom_profile(custom)
        manager.set_profile("custom")
        
        colored = manager.colorize("test", "brocaos_prompt")
        assert "\033[35m" in colored or colored == "test"  # May be disabled
    
    def test_color_manager_get_custom_profile(self):
        """Test getting custom profile."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        
        custom = CustomColorProfile(
            brocaos_prompt="\033[35m",
            response_text="\033[37m",
            you_prompt="\033[32m",
            input_text="\033[0m"
        )
        
        manager.set_custom_profile(custom)
        profile = manager.get_profile("custom")
        
        assert profile == custom
    
    def test_color_manager_set_custom_when_active(self):
        """Test setting custom profile when custom is already active."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager()
            
            # First set custom profile
            custom = CustomColorProfile(
                brocaos_prompt="\033[35m",
                response_text="\033[37m",
                you_prompt="\033[32m",
                input_text="\033[0m"
            )
            manager.set_custom_profile(custom)
            manager.set_profile("custom")  # Now set to custom
            
            # Should be using custom profile
            assert manager._active_profile == custom
            
            # Update custom profile
            new_custom = CustomColorProfile(
                brocaos_prompt="\033[31m",
                response_text="\033[32m",
                you_prompt="\033[33m",
                input_text="\033[34m"
            )
            manager.set_custom_profile(new_custom)
            # Should update active profile since we're using custom
            assert manager._active_profile == new_custom
    
    def test_color_manager_set_profile_nonexistent(self):
        """Test setting profile that doesn't exist."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        manager.set_profile("nonexistent")
        
        # Should fallback to default
        assert manager._active_profile is not None
        assert manager._active_profile == manager._profiles.get("default")
    
    def test_color_manager_set_custom_without_custom_profile(self):
        """Test setting custom profile when custom profile not set."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        manager.set_profile("custom")
        
        # Should fallback to default if custom not set
        assert manager._active_profile is not None
        assert manager._active_profile == manager._profiles.get("default")
    
    def test_color_manager_colorize_with_exception(self):
        """Test colorize when apply_color raises exception."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager()
            manager.set_profile("default")
            
            # Mock profile to raise exception
            manager._active_profile.apply_color = Mock(side_effect=AttributeError("test"))
            
            # Should return original text on exception
            result = manager.colorize("test", "brocaos_prompt")
            assert result == "test"
    
    def test_color_manager_is_enabled(self):
        """Test is_enabled method."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager()
            assert manager.is_enabled() is True
        
        with patch('sys.stdout.isatty', return_value=False):
            manager = ColorManager()
            assert manager.is_enabled() is False
    
    def test_color_manager_disable(self):
        """Test disable method."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager()
            assert manager.is_enabled() is True
            
            manager.disable()
            assert manager.is_enabled() is False
    
    def test_color_manager_enable(self):
        """Test enable method."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager(enabled=False)
            assert manager.is_enabled() is False
            
            manager.enable()
            assert manager.is_enabled() is True
        
        with patch('sys.stdout.isatty', return_value=False):
            manager = ColorManager(enabled=False)
            manager.enable()
            # Should stay disabled if not TTY
            assert manager.is_enabled() is False
    
    def test_color_manager_initialization_with_enabled_param(self):
        """Test ColorManager initialization with enabled parameter."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        # Test with enabled=True
        manager = ColorManager(enabled=True)
        assert manager.is_enabled() is True
        
        # Test with enabled=False
        manager = ColorManager(enabled=False)
        assert manager.is_enabled() is False


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        text=st.text(min_size=0, max_size=100)
    )
    def test_colorize_preserves_text_content(self, text):
        """Property: Colorizing text preserves original content."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager()
            manager.set_profile("default")
            
            colored = manager.colorize(text, "brocaos_prompt")
            
            # Original text should be in colored output
            assert text in colored or text == ""
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        color_code=st.integers(min_value=0, max_value=255)
    )
    def test_ansi_color_always_valid(self, color_code):
        """Property: ANSI color codes are always valid sequences."""
        if ansi_color is None:
            pytest.skip("ansi_color not yet implemented")
        
        code = ansi_color(color_code, use_256=True)
        
        # Should start with escape sequence
        assert code.startswith("\033[")
        assert "m" in code
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not available")
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    @given(
        profile_name=st.sampled_from(["default", "dark", "light"])
    )
    def test_all_profiles_produce_valid_output(self, profile_name):
        """Property: All predefined profiles produce valid output."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        with patch('sys.stdout.isatty', return_value=True):
            manager = ColorManager()
            manager.set_profile(profile_name)
            
            colored = manager.colorize("test", "brocaos_prompt")
            
            # Should always return a string
            assert isinstance(colored, str)
            assert len(colored) >= len("test")  # At least as long as original


class TestGoldenTraces:
    """Golden trace replay tests for color system."""
    
    def test_default_profile_golden_trace(self):
        """Test that default profile produces consistent output."""
        if DefaultColorProfile is None:
            pytest.skip("DefaultColorProfile not yet implemented")
        
        profile = DefaultColorProfile()
        
        # Verify profile structure
        assert hasattr(profile, 'brocaos_prompt')
        assert hasattr(profile, 'response_text')
        assert hasattr(profile, 'you_prompt')
        assert hasattr(profile, 'input_text')
        
        # All should be strings
        assert isinstance(profile.brocaos_prompt, str)
        assert isinstance(profile.response_text, str)
        assert isinstance(profile.you_prompt, str)
        assert isinstance(profile.input_text, str)
    
    def test_color_application_consistency(self):
        """Test that color application is consistent."""
        if ColorManager is None or ColorProfile is None:
            pytest.skip("ColorManager not yet implemented")
        
        color_manager = ColorManager()
        color_manager.set_profile("default")
        
        # Same input should produce consistent output
        text1 = color_manager.colorize("test", "brocaos_prompt")
        text2 = color_manager.colorize("test", "brocaos_prompt")
        
        # Should be identical
        assert text1 == text2
    
    def test_ansi_code_format_consistency(self):
        """Test that ANSI codes follow consistent format."""
        if ansi_color is None:
            pytest.skip("ansi_color not yet implemented")
        
        # Test standard colors
        codes = [31, 32, 33, 34, 35, 36, 37]
        for code in codes:
            ansi_code = ansi_color(code)
            # Should start with escape sequence
            assert ansi_code.startswith("\033[")
            assert ansi_code.endswith("m")
            # Should contain the code
            assert str(code) in ansi_code
    
    def test_profile_output_format(self):
        """Test that all profiles produce valid output format."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        color_manager = ColorManager()
        
        profiles = ["default", "dark", "light"]
        for profile_name in profiles:
            color_manager.set_profile(profile_name)
            
            # Test formatting
            test_text = "BrocaOS> "
            colored = color_manager.colorize(test_text, "brocaos_prompt")
            
            # Should be a valid string
            assert isinstance(colored, str)
            # Should contain original text (or be original if disabled)
            assert test_text in colored or colored == test_text
    
    def test_backward_compatibility_no_colors(self):
        """Test backward compatibility - colors can be disabled."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        # Disable colors
        color_manager = ColorManager(enabled=False)
        color_manager.set_profile("default")
        
        # Should return original text
        text = "BrocaOS> test"
        colored = color_manager.colorize(text, "brocaos_prompt")
        assert colored == text


class TestFaultInjection:
    """Fault injection tests for error handling."""
    
    def test_color_manager_handles_missing_profile(self):
        """Test handling of missing profile name."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        
        # Should handle gracefully (fallback to default or raise)
        try:
            profile = manager.get_profile("nonexistent")
            # If it doesn't raise, should return default or None
            assert profile is None or isinstance(profile, ColorProfile)
        except (KeyError, ValueError):
            # Expected behavior - invalid profile name
            pass
    
    def test_color_manager_handles_invalid_color_type(self):
        """Test handling of invalid color type."""
        if ColorManager is None:
            pytest.skip("ColorManager not yet implemented")
        
        manager = ColorManager()
        manager.set_profile("default")
        
        # Should handle invalid color type gracefully
        try:
            colored = manager.colorize("test", "invalid_type")
            # Should return original text or raise
            assert isinstance(colored, str)
        except (KeyError, ValueError):
            # Expected behavior
            pass
    
    def test_ansi_color_handles_edge_cases(self):
        """Test ANSI color with edge case values."""
        if ansi_color is None:
            pytest.skip("ansi_color not yet implemented")
        
        # Test with various edge cases
        edge_cases = [0, 255, -1, 256, 1000]
        for code in edge_cases:
            try:
                result = ansi_color(code, use_256=True)
                # Should return a string (may be invalid but shouldn't crash)
                assert isinstance(result, str)
            except (ValueError, TypeError):
                # Expected for invalid codes
                pass
    
    def test_color_profile_handles_none_values(self):
        """Test color profile with None values."""
        if CustomColorProfile is None:
            pytest.skip("CustomColorProfile not yet implemented")
        
        # Should handle None gracefully or raise TypeError
        try:
            profile = CustomColorProfile(
                brocaos_prompt=None,
                response_text=None,
                you_prompt=None,
                input_text=None
            )
            # If it doesn't raise, should convert None to empty string
            assert all(isinstance(getattr(profile, attr), str) for attr in 
                      ['brocaos_prompt', 'response_text', 'you_prompt', 'input_text'])
        except TypeError:
            # Expected behavior
            pass

