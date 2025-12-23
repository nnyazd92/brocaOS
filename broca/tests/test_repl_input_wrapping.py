"""
Tests for REPL input wrapping functionality.

Tests that multi-line input handles colored prompts correctly and supports
proper terminal wrapping.
"""

from __future__ import annotations

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
import io

from broca.main_repl import _get_user_input_with_colored_prompt


class TestInputWrapping:
    """Test input wrapping with colored prompts."""
    
    def test_colored_prompt_prints_separately(self):
        """
        Test that colored prompt is printed separately from input.
        
        Rationale: Ensures prompt and input are separated for proper wrapping.
        """
        colored_prompt = "\033[33myou> \033[0m"  # Yellow color
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with patch('builtins.input', return_value='test input'):
                result = _get_user_input_with_colored_prompt(colored_prompt)
                
                # Should have printed the prompt
                output = mock_stdout.getvalue()
                assert colored_prompt in output
                
                # Should return the input
                assert result == 'test input'
    
    def test_empty_prompt_for_input_call(self):
        """
        Test that input() is called with empty prompt.
        
        Rationale: Ensures readline sees empty prompt for proper wrapping calculation.
        """
        colored_prompt = "\033[33myou> \033[0m"
        
        with patch('sys.stdout', new_callable=io.StringIO):
            with patch('builtins.input') as mock_input:
                mock_input.return_value = 'test'
                _get_user_input_with_colored_prompt(colored_prompt)
                
                # Should be called with empty string
                mock_input.assert_called_once_with('')
    
    def test_fallback_on_exception(self):
        """
        Test that function falls back to simple input on exception.
        
        Rationale: Ensures graceful degradation if stdout.write fails.
        """
        colored_prompt = "\033[33myou> \033[0m"
        
        with patch('sys.stdout.write', side_effect=Exception("Write failed")):
            with patch('builtins.input', return_value='fallback input') as mock_input:
                result = _get_user_input_with_colored_prompt(colored_prompt)
                
                # Should fall back to input with prompt
                mock_input.assert_called_once_with(colored_prompt)
                assert result == 'fallback input'
    
    def test_eof_error_propagates(self):
        """
        Test that EOFError is re-raised.
        
        Rationale: Ensures caller can handle EOF correctly.
        """
        colored_prompt = "you> "
        
        with patch('sys.stdout', new_callable=io.StringIO):
            with patch('builtins.input', side_effect=EOFError):
                with pytest.raises(EOFError):
                    _get_user_input_with_colored_prompt(colored_prompt)
    
    def test_keyboard_interrupt_propagates(self):
        """
        Test that KeyboardInterrupt is re-raised.
        
        Rationale: Ensures caller can handle Ctrl+C correctly.
        """
        colored_prompt = "you> "
        
        with patch('sys.stdout', new_callable=io.StringIO):
            with patch('builtins.input', side_effect=KeyboardInterrupt):
                with pytest.raises(KeyboardInterrupt):
                    _get_user_input_with_colored_prompt(colored_prompt)
    
    def test_plain_prompt_works(self):
        """
        Test that plain (non-colored) prompts also work.
        
        Rationale: Ensures function works even without ANSI codes.
        """
        plain_prompt = "you> "
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with patch('builtins.input', return_value='test'):
                result = _get_user_input_with_colored_prompt(plain_prompt)
                
                # Should have printed the prompt
                output = mock_stdout.getvalue()
                assert plain_prompt in output
                assert result == 'test'

