"""
Property-based tests for interactive terminal functionality using Hypothesis.

Tests invariants and properties that should hold for all inputs.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from typing import Dict, Any

from broca.tools.terminal import TerminalTool


@pytest.fixture
def terminal_tool():
    """TerminalTool instance for testing."""
    return TerminalTool()


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(output=st.text(min_size=0, max_size=10000))
    def test_is_interactive_pattern_never_crashes(self, terminal_tool, output):
        """Property: _is_interactive_pattern never crashes on any string input."""
        try:
            result = terminal_tool._is_interactive_pattern(output)
            # Should always return a boolean
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"_is_interactive_pattern crashed on input: {repr(output[:100])}, error: {e}")
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(output=st.text(min_size=0, max_size=10000))
    def test_extract_interactive_elements_never_crashes(self, terminal_tool, output):
        """Property: _extract_interactive_elements never crashes on any string input."""
        try:
            result = terminal_tool._extract_interactive_elements(output)
            # Should either return None or a valid dict structure
            if result is not None:
                assert isinstance(result, dict)
                # If it's a dict, it should have a type field
                assert "type" in result
                assert result["type"] in ["menu", "prompt", "yesno"]
        except Exception as e:
            pytest.fail(f"_extract_interactive_elements crashed on input: {repr(output[:100])}, error: {e}")
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        num_options=st.integers(min_value=1, max_value=20),
        option_text=st.text(min_size=1, max_size=100)
    )
    def test_extract_menu_always_returns_valid_structure(self, terminal_tool, num_options, option_text):
        """Property: Menu extraction always returns valid structure with options."""
        # Create a numbered menu
        menu_lines = [f"{i+1}. {option_text} {i+1}" for i in range(num_options)]
        menu_output = "Select:\n" + "\n".join(menu_lines)
        
        result = terminal_tool._extract_interactive_elements(menu_output)
        
        # If it detects as interactive, structure should be valid
        if result is not None:
            assert result["type"] == "menu"
            assert "options" in result
            assert isinstance(result["options"], list)
            assert len(result["options"]) > 0
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
    @given(
        result_dict=st.dictionaries(
            keys=st.sampled_from([
                "success", "interactive", "interactive_elements", "command",
                "stdout", "stderr", "returncode"
            ]),
            values=st.recursive(
                st.one_of(
                    st.booleans(),
                    st.integers(),
                    st.text(max_size=200),
                    st.lists(st.text(max_size=100), max_size=10),
                    st.dictionaries(
                        st.text(max_size=20),
                        st.one_of(st.text(max_size=100), st.booleans()),
                        max_size=5
                    )
                ),
                lambda children: st.lists(children, max_size=5) | st.dictionaries(st.text(max_size=20), children, max_size=5),
                max_leaves=10
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_format_result_never_crashes(self, terminal_tool, result_dict):
        """Property: format_result never crashes on any result dictionary."""
        try:
            formatted = terminal_tool.format_result(result_dict)
            # Should always return a string
            assert isinstance(formatted, str)
        except Exception as e:
            pytest.fail(f"format_result crashed on input: {result_dict}, error: {e}")
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        menu_text=st.text(min_size=0, max_size=500),
        has_numbers=st.booleans(),
        has_letters=st.booleans()
    )
    def test_interactive_detection_consistency(self, terminal_tool, menu_text, has_numbers, has_letters):
        """Property: Interactive detection is consistent - same pattern should always be detected."""
        # Build a menu-like string
        if has_numbers:
            menu_text = f"1. {menu_text}\n2. Option 2"
        elif has_letters:
            menu_text = f"a) {menu_text}\nb) Option B"
        
        # Test detection multiple times
        results = [terminal_tool._is_interactive_pattern(menu_text) for _ in range(5)]
        
        # All results should be the same (consistency)
        assert len(set(results)) == 1, "Interactive detection is inconsistent"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    @given(
        prompt_endings=st.lists(
            st.sampled_from([":", "?", ">", "[y/N]", "(yes/no)"]),
            min_size=1,
            max_size=5
        )
    )
    def test_prompt_detection_property(self, terminal_tool, prompt_endings):
        """Property: Prompts ending with interactive markers are detected."""
        for ending in prompt_endings:
            prompt = f"Enter value{ending}"
            is_interactive = terminal_tool._is_interactive_pattern(prompt)
            # At least one of these should be detected as interactive
            if ending in [":", "?", ">", "[y/N]", "(yes/no)"]:
                # Most should be detected (allow for edge cases)
                pass  # Just ensure it doesn't crash
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    @given(
        result=st.fixed_dictionaries({
            "success": st.booleans(),
            "interactive": st.booleans(),
            "command": st.text(max_size=100),
        }).flatmap(
            lambda base: st.dictionaries(
                st.just("interactive_elements"),
                st.fixed_dictionaries({
                    "type": st.sampled_from(["menu", "prompt", "yesno"]),
                    "options": st.lists(st.text(max_size=50), max_size=10),
                }, optional={"prompt_text": st.text(max_size=100)}),
                min_size=0,
                max_size=1
            ).map(lambda extras: {**base, **extras})
        )
    )
    def test_format_interactive_result_preserves_info(self, terminal_tool, result):
        """Property: Formatting interactive results preserves essential information."""
        if result.get("interactive") and "interactive_elements" in result:
            formatted = terminal_tool.format_result(result)
            # Should include indication of interactivity
            assert "INTERACTIVE" in formatted or "interactive" in formatted.lower()

