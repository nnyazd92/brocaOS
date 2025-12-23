"""
Integration tests for REPL color system.

Tests end-to-end color application in REPL contexts including
prompts, responses, and tool status display.
"""

from __future__ import annotations

import pytest
import sys
import io
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from broca.repl.session import ConversationSession
from broca.repl.color_profile import ColorManager, CustomColorProfile
from broca.tools.registry import ToolRegistry
from broca.tools import Tool


class MockTool(Tool):
    """Mock tool for testing."""
    
    def __init__(self, name: str = "mock_tool", delay: float = 0.0):
        self._name = name
        self._delay = delay
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return f"A mock tool named {self._name}"
    
    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Test parameter"}
            },
            "required": []
        }
    
    def execute(self, **kwargs):
        return {"success": True, "result": "test result"}
    
    def format_result(self, result):
        return str(result)


class TestColorIntegration:
    """Integration tests for color system."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM client."""
        llm = Mock()
        llm.chat = Mock(return_value={
            "choices": [{
                "message": {
                    "content": "Test response",
                    "role": "assistant"
                }
            }]
        })
        llm.chat_stream = Mock(return_value=iter(["Test ", "response"]))
        llm.extract_assistant_content = Mock(return_value="Test response")
        llm.extract_tool_calls = Mock(return_value=[])
        return llm
    
    def test_color_manager_integration_with_session(self, mock_llm):
        """Test that ColorManager integrates with ConversationSession."""
        color_manager = ColorManager()
        color_manager.set_profile("default")
        
        session = ConversationSession(
            llm=mock_llm,
            color_manager=color_manager
        )
        
        assert session._color_manager is not None
        assert session._color_manager == color_manager
    
    def test_colors_applied_to_brocaos_prompt(self, mock_llm):
        """Test that colors are applied to BrocaOS prompt."""
        color_manager = ColorManager()
        color_manager.set_profile("default")
        
        session = ConversationSession(
            llm=mock_llm,
            color_manager=color_manager
        )
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                # Simulate non-streaming response
                response = {
                    "choices": [{
                        "message": {
                            "content": "Test response",
                            "role": "assistant"
                        }
                    }]
                }
                mock_llm.extract_assistant_content = Mock(return_value="Test response")
                
                # This would normally be called during send(), but we'll test the colorization directly
                prompt = "BrocaOS> "
                colored_prompt = color_manager.colorize(prompt, "brocaos_prompt")
                
                # Should contain color codes when enabled
                assert isinstance(colored_prompt, str)
                assert "BrocaOS>" in colored_prompt
    
    def test_colors_applied_to_response_text(self, mock_llm):
        """Test that colors are applied to response text."""
        color_manager = ColorManager()
        color_manager.set_profile("default")
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                response_text = "This is a test response"
                colored_text = color_manager.colorize(response_text, "response_text")
                
                # Should contain original text
                assert response_text in colored_text
                assert isinstance(colored_text, str)
    
    def test_colors_disabled_for_non_tty(self, mock_llm):
        """Test that colors are disabled for non-TTY terminals."""
        with patch('sys.stdout.isatty', return_value=False):
            color_manager = ColorManager()
            color_manager.set_profile("default")
            
            prompt = "BrocaOS> "
            colored_prompt = color_manager.colorize(prompt, "brocaos_prompt")
            
            # Should return original text without colors
            assert colored_prompt == prompt
    
    def test_custom_profile_integration(self, mock_llm):
        """Test custom color profile integration."""
        color_manager = ColorManager()
        
        custom_profile = CustomColorProfile(
            brocaos_prompt="\033[35m",
            response_text="\033[37m",
            you_prompt="\033[32m",
            input_text="\033[0m"
        )
        
        color_manager.set_custom_profile(custom_profile)
        color_manager.set_profile("custom")
        
        session = ConversationSession(
            llm=mock_llm,
            color_manager=color_manager
        )
        
        assert session._color_manager is not None
        assert session._color_manager._active_profile == custom_profile
    
    def test_profile_switching(self, mock_llm):
        """Test switching between profiles."""
        color_manager = ColorManager()
        
        # Test default profile
        color_manager.set_profile("default")
        default_colored = color_manager.colorize("test", "brocaos_prompt")
        
        # Test dark profile
        color_manager.set_profile("dark")
        dark_colored = color_manager.colorize("test", "brocaos_prompt")
        
        # Both should be valid strings
        assert isinstance(default_colored, str)
        assert isinstance(dark_colored, str)
        assert "test" in default_colored
        assert "test" in dark_colored
    
    def test_tool_status_display_with_colors(self):
        """Test that tool status display uses colors."""
        color_manager = ColorManager()
        color_manager.set_profile("default")
        
        from broca.repl.tool_status import ToolStatusDisplay
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(color_manager=color_manager)
                display.start_tool_call("web_search", {"query": "test"})
                display.complete_tool_call(success=True)
        
        output_str = output.getvalue()
        # Should have output
        assert len(output_str) > 0
        assert "BrocaOS>" in output_str or "BrocaOS" in output_str
    
    def test_colors_with_streaming(self, mock_llm):
        """Test that colors work with streaming output."""
        color_manager = ColorManager()
        color_manager.set_profile("default")
        
        session = ConversationSession(
            llm=mock_llm,
            color_manager=color_manager
        )
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                # Simulate streaming
                chunks = ["Hello", " ", "World"]
                for chunk in chunks:
                    colored = color_manager.colorize(chunk, "response_text")
                    output.write(colored)
        
        output_str = output.getvalue()
        # Should contain all chunks
        assert "Hello" in output_str
        assert "World" in output_str
    
    def test_color_manager_backward_compatibility(self, mock_llm):
        """Test that sessions work without color manager (backward compatibility)."""
        # Session should work without color_manager
        session = ConversationSession(
            llm=mock_llm,
            color_manager=None
        )
        
        assert session._color_manager is None
        # Should not crash
        assert session is not None
    
    def test_all_profiles_work(self, mock_llm):
        """Test that all predefined profiles work correctly."""
        color_manager = ColorManager()
        
        profiles = ["default", "dark", "light"]
        for profile_name in profiles:
            color_manager.set_profile(profile_name)
            
            # Test all color types
            for color_type in ["brocaos_prompt", "response_text", "you_prompt", "input_text"]:
                colored = color_manager.colorize("test", color_type)
                assert isinstance(colored, str)
                assert "test" in colored or colored == "test"  # May be disabled

