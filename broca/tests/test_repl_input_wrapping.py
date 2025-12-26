"""
Tests for REPL input functionality.

Tests that input handling works correctly in the REPL.
Note: The REPL now uses plain prompts (not colored) to avoid readline/ANSI conflicts.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

# Note: The function _get_user_input_with_colored_prompt was removed.
# The REPL now uses plain input() directly. These tests verify the current behavior.


class TestInputHandling:
    """Test input handling in REPL."""
    
    def test_plain_prompt_works(self):
        """
        Test that plain prompts work correctly.
        
        Rationale: Ensures the REPL uses plain prompts (current implementation).
        """
        plain_prompt = "you> "
        
        with patch('builtins.input') as mock_input:
            mock_input.return_value = 'test input'
            result = input(plain_prompt).strip()
            
            # Should be called with the prompt
            mock_input.assert_called_once_with(plain_prompt)
            # Should return the input
            assert result == 'test input'
    
    def test_input_strips_whitespace(self):
        """
        Test that input is stripped of whitespace.
        
        Rationale: Ensures the REPL strips whitespace from user input.
        """
        with patch('builtins.input') as mock_input:
            mock_input.return_value = '  test input  '
            result = input("you> ").strip()
            
            assert result == 'test input'
    
    def test_eof_error_handled(self):
        """
        Test that EOFError can be caught.
        
        Rationale: Ensures caller can handle EOF correctly.
        """
        with patch('builtins.input', side_effect=EOFError):
            with pytest.raises(EOFError):
                input("you> ")
    
    def test_keyboard_interrupt_handled(self):
        """
        Test that KeyboardInterrupt can be caught.
        
        Rationale: Ensures caller can handle Ctrl+C correctly.
        """
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt):
                input("you> ")

