"""
Tests for REPL input wrapping functionality.

Tests that input handles colored prompts correctly.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

from broca.main_repl import _get_user_input_with_colored_prompt


class TestInputWrapping:
    """Test input with colored prompts."""
    
    def test_colored_prompt_passed_to_input(self):
        """
        Test that colored prompt is passed directly to input().
        
        Rationale: Ensures the function simply uses input() with the prompt.
        """
        colored_prompt = "\033[33myou> \033[0m"  # Yellow color
        
        with patch('builtins.input') as mock_input:
            mock_input.return_value = 'test input'
            result = _get_user_input_with_colored_prompt(colored_prompt)
            
            # Should be called with the prompt
            mock_input.assert_called_once_with(colored_prompt)
            # Should return the input
            assert result == 'test input'
    
    def test_plain_prompt_works(self):
        """
        Test that plain (non-colored) prompts also work.
        
        Rationale: Ensures function works even without ANSI codes.
        """
        plain_prompt = "you> "
        
        with patch('builtins.input') as mock_input:
            mock_input.return_value = 'test'
            result = _get_user_input_with_colored_prompt(plain_prompt)
            
            # Should be called with the prompt
            mock_input.assert_called_once_with(plain_prompt)
            assert result == 'test'
    
    def test_eof_error_propagates(self):
        """
        Test that EOFError is re-raised.
        
        Rationale: Ensures caller can handle EOF correctly.
        """
        colored_prompt = "you> "
        
        with patch('builtins.input', side_effect=EOFError):
            with pytest.raises(EOFError):
                _get_user_input_with_colored_prompt(colored_prompt)
    
    def test_keyboard_interrupt_propagates(self):
        """
        Test that KeyboardInterrupt is re-raised.
        
        Rationale: Ensures caller can handle Ctrl+C correctly.
        """
        colored_prompt = "you> "
        
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt):
                _get_user_input_with_colored_prompt(colored_prompt)

