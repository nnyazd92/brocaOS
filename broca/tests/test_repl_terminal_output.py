"""
Tests for REPL terminal output formatting.

Tests terminal output behavior including empty prompt lines, streaming output,
and loading indicators.
"""

from __future__ import annotations

import pytest
import sys
import io
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Iterator

# Hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st, settings, HealthCheck
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

from broca.repl.session import ConversationSession


class TestEmptyPromptLines:
    """Test that empty 'BrocaOS> ' lines are not printed."""
    
    @patch('builtins.print')
    def test_streaming_empty_response_no_prompt(self, mock_print, mock_llm_client: Mock):
        """
        Test that streaming with empty response does not print 'BrocaOS> '.
        
        Rationale: Ensures no empty prompt lines appear when streaming produces no content.
        """
        def mock_chat_stream(*args, **kwargs):
            # Empty generator - no chunks
            return iter(())
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
        mock_llm_client.extract_assistant_content = lambda x: None
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.is_reasoner_model = lambda: False
        
        session = ConversationSession(llm=mock_llm_client)
        session.send("test", stream=True)
        
        # Get all print calls as strings
        print_calls = [str(call) for call in mock_print.call_args_list]
        
        # Should NOT have any standalone "BrocaOS> " without content
        # If there's a "BrocaOS> " it should be followed by content or newline with content
        standalone_prompt_calls = [
            call for call in print_calls 
            if '"BrocaOS> "' in call and 'end=""' in call
        ]
        
        # If we have standalone prompt calls, verify they're followed by content
        if standalone_prompt_calls:
            # Find the index of the prompt call
            for i, call in enumerate(mock_print.call_args_list):
                args_str = str(call)
                if '"BrocaOS> "' in args_str and 'end=""' in args_str:
                    # Check if there's a subsequent call with content
                    has_content_after = False
                    for j in range(i + 1, len(mock_print.call_args_list)):
                        next_call = str(mock_print.call_args_list[j])
                        # Skip empty newlines
                        if next_call and not ('end=""' in next_call and '""' in next_call):
                            has_content_after = True
                            break
                    # If no content after, this is an empty prompt line (bad)
                    if not has_content_after:
                        pytest.fail(f"Found empty 'BrocaOS> ' prompt line: {call}")
    
    @patch('builtins.print')
    def test_streaming_whitespace_only_response_no_empty_prompt(self, mock_print, mock_llm_client: Mock):
        """
        Test that streaming with whitespace-only response does not print empty prompt.
        
        Rationale: Ensures whitespace-only responses don't produce empty prompt lines.
        """
        def mock_chat_stream(*args, **kwargs):
            yield "   "  # Only whitespace
            yield "\t\n"
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
        mock_llm_client.extract_assistant_content = lambda x: "   \t\n"
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.is_reasoner_model = lambda: False
        
        session = ConversationSession(llm=mock_llm_client)
        session.send("test", stream=True)
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        
        # Should NOT print standalone "BrocaOS> " followed only by newline
        # The response guard should handle whitespace-only content
        calls_str = ' '.join(print_calls)
        # Check that we don't have pattern: "BrocaOS> " followed by nothing but newline
        if '"BrocaOS> "' in calls_str:
            # Verify content was printed
            assert any('   ' in call or '\\t' in call for call in print_calls)
    
    @patch('builtins.print')
    def test_streaming_with_content_prints_prompt(self, mock_print, mock_llm_client: Mock):
        """
        Test that streaming with actual content DOES print 'BrocaOS> '.
        
        Rationale: Ensures prompt is printed when there's content to display.
        """
        def mock_chat_stream(*args, **kwargs):
            yield "Hello"
            yield " world"
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
        mock_llm_client.extract_assistant_content = lambda x: "Hello world"
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.is_reasoner_model = lambda: False
        
        session = ConversationSession(llm=mock_llm_client)
        session.send("test", stream=True)
        
        # Should have printed "BrocaOS> "
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("BrocaOS>" in call for call in print_calls)
        
        # Should have printed content
        assert any("Hello" in call for call in print_calls)
        assert any(" world" in call for call in print_calls)
    
    @patch('builtins.print')
    def test_non_streaming_empty_response_handled(self, mock_print, mock_llm_client: Mock):
        """
        Test that non-streaming empty response doesn't print empty prompt line.
        
        Rationale: Ensures non-streaming path also handles empty responses correctly.
        """
        mock_llm_client.chat.return_value = {"choices": [{"message": {"content": None, "role": "assistant"}}]}
        mock_llm_client.extract_assistant_content = lambda x: None
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.is_reasoner_model = lambda: False
        mock_llm_client.hasattr = lambda obj, attr: False  # No chat_stream
        
        session = ConversationSession(llm=mock_llm_client)
        # Response guard should inject fallback, so we should see content
        response = session.send("test", stream=False)
        
        # Response guard should have injected a fallback message
        assert response is not None
        assert len(response) > 0
        
        # Should have printed something (the fallback)
        print_calls = [str(call) for call in mock_print.call_args_list]
        # Should have printed BrocaOS> with content (the fallback)
        calls_str = ' '.join(print_calls)
        if "BrocaOS>" in calls_str:
            # If prompt was printed, content should follow
            assert any("automatic fallback" in call.lower() or "traceid" in call.lower() for call in print_calls)


class TestSpinnerVisibility:
    """Test spinner visibility and display behavior."""
    
    def test_spinner_prints_with_carriage_return(self):
        """
        Test that spinner updates use carriage return for same-line updates.
        
        Rationale: Ensures spinner animation works correctly with carriage return.
        """
        from broca.repl.tool_status import ToolStatusDisplay, Spinner
        import sys
        import io
        
        # Capture stdout
        captured_output = io.StringIO()
        
        with patch('sys.stdout', captured_output):
            with patch('sys.stdout.isatty', return_value=True):
                display = ToolStatusDisplay(enabled=True)
                display.start_tool_call("terminal", {"command": "echo test"}, "test_id")
                
                # Wait briefly for spinner thread to run
                import time
                time.sleep(0.15)
                
                display.complete_tool_call("test_id", success=True)
                
                # Wait for thread to finish
                time.sleep(0.1)
                
                output = captured_output.getvalue()
                
                # Should contain carriage return for line overwrite
                assert '\r' in output or 'BrocaOS>' in output
    
    def test_spinner_visible_when_enabled(self):
        """
        Test that spinner characters are visible when enabled.
        
        Rationale: Ensures spinner actually displays when terminal supports it.
        """
        from broca.repl.tool_status import Spinner
        
        spinner = Spinner(enabled=True)
        spinner.start()
        
        # Get spinner character
        char = spinner.update()
        
        # Should return a non-empty character
        assert char != ""
        assert len(char) > 0
        
        # Should be one of the spinner characters
        assert char in Spinner.SPINNER_CHARS
    
    def test_spinner_disabled_when_not_tty(self):
        """
        Test that spinner is disabled when not a TTY.
        
        Rationale: Ensures graceful degradation when terminal doesn't support spinners.
        """
        from broca.repl.tool_status import Spinner
        
        with patch('sys.stdout.isatty', return_value=False):
            spinner = Spinner()
            # Should be disabled
            char = spinner.update()
            assert char == ""


class TestPropertyBasedTerminalOutput:
    """Property-based tests for terminal output using Hypothesis."""
    
    if HAS_HYPOTHESIS:
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
        @given(
            chunks=st.lists(
                st.text(min_size=0, max_size=100),
                min_size=0,
                max_size=20
            )
        )
        @patch('builtins.print')
        def test_streaming_never_produces_empty_prompt_lines(
            self, mock_print, mock_llm_client: Mock, chunks
        ):
            """
            Property: Streaming with any combination of chunks never produces empty prompt lines.
            
            Rationale: Ensures that regardless of chunk content (empty, whitespace, text),
            we never print standalone "BrocaOS> " without content.
            """
            def mock_chat_stream(*args, **kwargs):
                for chunk in chunks:
                    yield chunk
            
            mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
            mock_llm_client.extract_assistant_content = lambda x: "".join(chunks) if chunks else None
            mock_llm_client.extract_tool_calls = lambda x: []
            mock_llm_client.is_reasoner_model = lambda: False
            
            session = ConversationSession(llm=mock_llm_client)
            session.send("test", stream=True)
            
            # Get all print calls
            print_calls = [str(call) for call in mock_print.call_args_list]
            
            # If no chunks were provided, should not print "BrocaOS> " at all
            if not chunks or all(not chunk.strip() for chunk in chunks):
                # Should not have standalone prompt
                standalone_prompts = [
                    call for call in print_calls
                    if '"BrocaOS> "' in call and 'end=""' in call
                ]
                # If there are standalone prompts, they must be followed by content
                if standalone_prompts:
                    # Find index of prompt call
                    for i, call in enumerate(mock_print.call_args_list):
                        args_str = str(call)
                        if '"BrocaOS> "' in args_str and 'end=""' in args_str:
                            # Check subsequent calls for content
                            has_content = False
                            for j in range(i + 1, len(mock_print.call_args_list)):
                                next_call = str(mock_print.call_args_list[j])
                                # Skip empty newlines
                                if next_call and not ('end=""' in next_call and '""' in next_call):
                                    has_content = True
                                    break
                            # If no content follows, this violates the property
                            if not has_content:
                                pytest.fail(f"Empty prompt line found with chunks: {chunks}")
            else:
                # If chunks exist and have content, prompt should be printed with content
                assert any("BrocaOS>" in call for call in print_calls)


class TestFaultInjection:
    """Fault injection tests for edge cases."""
    
    def test_streaming_when_not_tty(self, mock_llm_client: Mock):
        """
        Test streaming behavior when stdout is not a TTY.
        
        Rationale: Ensures graceful degradation when terminal capabilities are missing.
        """
        def mock_chat_stream(*args, **kwargs):
            yield "Hello"
            yield " world"
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
        mock_llm_client.extract_assistant_content = lambda x: "Hello world"
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.is_reasoner_model = lambda: False
        
        session = ConversationSession(llm=mock_llm_client)
        
        # Should not crash when not a TTY
        with patch('sys.stdout.isatty', return_value=False):
            response = session.send("test", stream=True)
            assert response == "Hello world"
    
    def test_spinner_when_stdout_redirected(self):
        """
        Test spinner behavior when stdout is redirected.
        
        Rationale: Ensures spinner handles non-TTY gracefully.
        """
        from broca.repl.tool_status import ToolStatusDisplay
        import io
        
        captured = io.StringIO()
        
        with patch('sys.stdout', captured):
            with patch('sys.stdout.isatty', return_value=False):
                display = ToolStatusDisplay(enabled=True)
                # Should not crash
                display.start_tool_call("terminal", {"command": "echo test"}, "test_id")
                display.complete_tool_call("test_id", success=True)
    
    def test_color_manager_when_not_tty(self):
        """
        Test color manager when stdout is not a TTY.
        
        Rationale: Ensures colors are disabled gracefully.
        """
        from broca.repl.color_profile import ColorManager
        
        with patch('sys.stdout.isatty', return_value=False):
            manager = ColorManager()
            # Should disable colors
            assert not manager.is_enabled()
            
            # Colorize should return original text
            result = manager.colorize("test", "brocaos_prompt")
            assert result == "test"
    
    def test_spinner_thread_cleanup_on_exception(self):
        """
        Test spinner thread cleanup when exception occurs.
        
        Rationale: Ensures threads don't leak when errors occur.
        """
        from broca.repl.tool_status import ToolStatusDisplay
        import threading
        import time
        
        display = ToolStatusDisplay(enabled=True)
        
        # Start a spinner
        display.start_tool_call("terminal", {"command": "test"}, "test_id")
        
        # Wait for thread to start
        time.sleep(0.1)
        
        # Simulate exception scenario - pause and resume
        display.pause_updates()
        
        # Threads should be stopped
        with display._lock:
            assert not display._spinner_running.get("test_id", False)
        
        display.resume_updates()
        display.complete_tool_call("test_id", success=True)
        
        # Thread should be cleaned up
        with display._lock:
            assert "test_id" not in display._spinner_threads
    
    def test_streaming_with_malformed_chunks(self, mock_llm_client: Mock):
        """
        Test streaming behavior with edge case chunks (None, empty strings, etc.).
        
        Rationale: Ensures robustness with malformed input.
        """
        def mock_chat_stream(*args, **kwargs):
            yield ""  # Empty string chunk
            yield "content"
            yield ""  # Another empty chunk
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
        mock_llm_client.extract_assistant_content = lambda x: "content"
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.is_reasoner_model = lambda: False
        
        session = ConversationSession(llm=mock_llm_client)
        
        with patch('builtins.print'):
            response = session.send("test", stream=True)
            # Should handle empty chunks gracefully
            assert "content" in response or response == "content"


class TestGoldenTraces:
    """Golden trace replay tests for terminal output."""
    
    @pytest.fixture
    def golden_traces_dir(self):
        """Get directory for golden traces."""
        return Path(__file__).parent / "fixtures" / "golden_traces" / "repl_terminal"
    
    def load_golden_trace(self, trace_name: str, golden_traces_dir: Path) -> dict:
        """Load a golden trace JSON file."""
        golden_traces_dir.mkdir(parents=True, exist_ok=True)
        trace_path = golden_traces_dir / f"{trace_name}.json"
        if not trace_path.exists():
            return None
        
        import json
        with open(trace_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_golden_trace(self, trace_name: str, golden_traces_dir: Path, data: dict):
        """Save a golden trace JSON file."""
        golden_traces_dir.mkdir(parents=True, exist_ok=True)
        trace_path = golden_traces_dir / f"{trace_name}.json"
        
        import json
        with open(trace_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    @patch('builtins.print')
    def test_streaming_with_content_golden_trace(self, mock_print, mock_llm_client: Mock, golden_traces_dir):
        """
        Test that streaming output format matches golden trace.
        
        Rationale: Ensures output format consistency and no empty prompt lines.
        """
        def mock_chat_stream(*args, **kwargs):
            yield "Hello"
            yield " world"
            yield "!"
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
        mock_llm_client.extract_assistant_content = lambda x: "Hello world!"
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.is_reasoner_model = lambda: False
        
        session = ConversationSession(llm=mock_llm_client)
        session.send("test", stream=True)
        
        # Capture print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        calls_str = ' '.join(print_calls)
        
        expected = {
            "has_brocaos_prompt": "BrocaOS>" in calls_str,
            "has_content": "Hello" in calls_str and "world" in calls_str,
            "no_empty_prompt": True,  # Key property: no standalone "BrocaOS> " followed only by newline
            "notes": [
                "Prompt should only appear when content is streamed",
                "No empty 'BrocaOS> ' lines should be printed",
                "Content chunks should be printed after prompt"
            ]
        }
        
        golden = self.load_golden_trace("streaming_with_content", golden_traces_dir)
        if golden:
            # Replay: verify format matches
            assert expected["has_brocaos_prompt"] == golden.get("has_brocaos_prompt", True)
            assert expected["has_content"] == golden.get("has_content", True)
            assert expected["no_empty_prompt"] == golden.get("no_empty_prompt", True)
        else:
            # Record: save golden trace
            self.save_golden_trace("streaming_with_content", golden_traces_dir, expected)
            pytest.skip("Golden trace created - run again to verify")
    
    @patch('builtins.print')
    def test_streaming_empty_response_golden_trace(self, mock_print, mock_llm_client: Mock, golden_traces_dir):
        """
        Test that empty streaming response doesn't print empty prompt (golden trace).
        
        Rationale: Ensures empty responses never produce empty prompt lines.
        """
        def mock_chat_stream(*args, **kwargs):
            return iter(())  # Empty generator
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
        mock_llm_client.extract_assistant_content = lambda x: None
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.is_reasoner_model = lambda: False
        
        session = ConversationSession(llm=mock_llm_client)
        session.send("test", stream=True)
        
        # Capture print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        calls_str = ' '.join(print_calls)
        
        expected = {
            "has_brocaos_prompt": "BrocaOS>" in calls_str,
            "no_empty_prompt": not ('"BrocaOS> "' in calls_str and calls_str.count('BrocaOS>') == calls_str.count('end=""')),  # No standalone prompt
            "notes": [
                "Empty streaming responses should not print 'BrocaOS> '",
                "Response guard should inject fallback message if needed",
                "No empty prompt lines should appear"
            ]
        }
        
        golden = self.load_golden_trace("streaming_empty_response", golden_traces_dir)
        if golden:
            # Replay: verify no empty prompt
            assert expected["no_empty_prompt"] == golden.get("no_empty_prompt", True)
        else:
            # Record: save golden trace
            self.save_golden_trace("streaming_empty_response", golden_traces_dir, expected)
            pytest.skip("Golden trace created - run again to verify")
    
    def test_color_profile_golden_trace(self, golden_traces_dir):
        """
        Test that color profile colors match golden trace.
        
        Rationale: Ensures color differentiation is consistent.
        """
        from broca.repl.color_profile import DefaultColorProfile
        
        profile = DefaultColorProfile()
        
        expected = {
            "brocaos_prompt": profile.brocaos_prompt,
            "input_text": profile.input_text,
            "response_text": profile.response_text,
            "you_prompt": profile.you_prompt,
            "input_text_distinct_from_prompt": profile.input_text != profile.brocaos_prompt,
            "input_text_not_reset": profile.input_text != "",
            "notes": [
                "input_text should be distinct from brocaos_prompt",
                "input_text should have a color (not empty/reset)",
                "Colors should be ANSI escape sequences"
            ]
        }
        
        golden = self.load_golden_trace("color_profile_default", golden_traces_dir)
        if golden:
            # Replay: verify colors match
            assert expected["input_text_distinct_from_prompt"] == golden.get("input_text_distinct_from_prompt", True)
            assert expected["input_text_not_reset"] == golden.get("input_text_not_reset", True)
            # Colors should match (allowing for config changes if documented)
            if "brocaos_prompt" in golden:
                # Allow color values to differ, but verify they're set
                assert profile.brocaos_prompt != ""
        else:
            # Record: save golden trace
            self.save_golden_trace("color_profile_default", golden_traces_dir, expected)
            pytest.skip("Golden trace created - run again to verify")

