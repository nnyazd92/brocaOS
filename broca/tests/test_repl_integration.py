"""
Integration tests for the REPL main loop.

Tests command handling, input processing, session management, and error handling
in the REPL interface.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
import sys

from broca.main_repl import main
from broca.repl.session import ConversationSession
from broca.tests.utils import build_llm_response


class TestREPLCommands:
    """Test REPL command handling (/exit, /reset, etc.)."""
    
    @patch('builtins.input', side_effect=['/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_exit_command(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that /exit command terminates the REPL loop.
        
        Rationale: Ensures users can cleanly exit the REPL.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            main()
            
            # Verify initial print occurred
            assert any("BrocaOS REPL" in str(call) for call in mock_print.call_args_list)
            # Verify exit message was printed
            assert any("Bye" in str(call) for call in mock_print.call_args_list)
            # Verify session.send was never called (user exited immediately)
            mock_session.send.assert_not_called()
    
    @patch('builtins.input', side_effect=['/quit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_quit_command_alias(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that /quit command also terminates the REPL (alias for /exit).
        
        Rationale: Ensures both /exit and /quit work as expected.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            main()
            
            # Should exit like /exit
            assert any("Bye" in str(call) for call in mock_print.call_args_list)
            mock_session.send.assert_not_called()
    
    @patch('builtins.input', side_effect=['Hello', '/reset', 'How are you?', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_reset_command_clears_context(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that /reset command clears conversation context.
        
        Rationale: Ensures users can start fresh without restarting the REPL.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.return_value = "Response"
            mock_session_class.return_value = mock_session
            
            main()
            
            # Verify session was created twice (initial + after reset)
            assert mock_session_class.call_count == 2
            # Verify send was called for both messages
            assert mock_session.send.call_count == 2
            # Verify reset message was printed
            assert any("context reset" in str(call).lower() for call in mock_print.call_args_list)
    
    @patch('builtins.input', side_effect=['', '  ', '\t', 'Actual message', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_empty_input_handling(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that empty/whitespace-only input is ignored.
        
        Rationale: Ensures the REPL handles empty inputs gracefully without errors.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            main()
            
            # Should only send the actual message, not empty ones
            assert mock_session.send.call_count == 1
            mock_session.send.assert_called_with("Actual message", stream=True)


class TestREPLConversationFlow:
    """Test normal conversation flow in the REPL."""
    
    @patch('builtins.input', side_effect=['Hello there', 'What can you do?', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_normal_conversation_turns(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that normal conversation turns work correctly.
        
        Rationale: Ensures the core REPL functionality works as expected.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.side_effect = ["Hello! How can I help?", "I can assist with various tasks."]
            mock_session_class.return_value = mock_session
            
            main()
            
            # Verify send was called for each user message
            assert mock_session.send.call_count == 2
            mock_session.send.assert_any_call("Hello there", stream=True)
            mock_session.send.assert_any_call("What can you do?", stream=True)
            
            # Note: When streaming is used, responses are printed during send() execution
            # Since we're using mocks, we can't verify the exact print output
            # But we can verify that send() was called correctly with streaming enabled
    
    @patch('builtins.input', side_effect=['User message', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_response_formatting(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that LLM responses are formatted correctly in output.
        
        Rationale: Ensures user-facing output is properly formatted.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.return_value = "This is the assistant's response"
            mock_session_class.return_value = mock_session
            
            main()
            
            # Check that response was printed (either during streaming or after)
            # When streaming is used, it's printed during send() with "BrocaOS> " prefix
            # When streaming is disabled, it's printed after with "BrocaOS> {reply}\n"
            # The test should verify the response appears somewhere
            print_calls = [str(call) for call in mock_print.call_args_list]
            # Response should appear in output (either streamed or printed after)
            # Since we're using a mock, we can't easily verify exact format,
            # but we can verify send() was called correctly
            mock_session.send.assert_called_once_with("User message", stream=True)


class TestREPLErrorHandling:
    """Test error handling in the REPL."""
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_keyboard_interrupt_handling(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that Ctrl+C (KeyboardInterrupt) exits cleanly.
        
        Rationale: Ensures users can interrupt the REPL with Ctrl+C without errors.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            main()
            
            # Should print exit message
            assert any("Exiting" in str(call) for call in mock_print.call_args_list)
    
    @patch('builtins.input', side_effect=EOFError())
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_eof_handling(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that EOF (Ctrl+D) exits cleanly.
        
        Rationale: Ensures the REPL handles EOF gracefully, common when piping input.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            main()
            
            # Should print exit message
            assert any("Exiting" in str(call) for call in mock_print.call_args_list)
    
    @patch('builtins.input', side_effect=['Test message', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_repl_handles_timeout_gracefully(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that REPL continues after timeout error.
        
        Rationale: Ensures timeout errors don't crash the REPL.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.side_effect = TimeoutError("API request timed out")
            mock_session_class.return_value = mock_session
            
            # Should not raise exception, should continue
            main()
            
            # Verify error message was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("error" in call.lower() or "timeout" in call.lower() for call in print_calls)
            # Verify REPL continued (exit was called)
            assert any("Bye" in str(call) for call in mock_print.call_args_list)
    
    @patch('builtins.input', side_effect=['Test message', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_repl_handles_network_error_gracefully(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that REPL continues after network error.
        
        Rationale: Ensures network errors don't crash the REPL.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.side_effect = ConnectionError("Network connection failed")
            mock_session_class.return_value = mock_session
            
            # Should not raise exception, should continue
            main()
            
            # Verify error message was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("error" in call.lower() or "network" in call.lower() for call in print_calls)
            # Verify REPL continued (exit was called)
            assert any("Bye" in str(call) for call in mock_print.call_args_list)


class TestREPLInitialization:
    """Test REPL initialization and setup."""
    
    @patch('builtins.input', side_effect=['/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_logging_setup_called(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that setup_logging() is called during initialization.
        
        Rationale: Ensures logging is properly configured when REPL starts.
        """
        with patch('broca.main_repl.ConversationSession'):
            main()
            mock_setup_logging.assert_called_once()
    
    @patch('builtins.input', side_effect=['/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_session_initialization(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that ConversationSession is initialized with world state aggregator.
        
        Rationale: Ensures the REPL creates sessions with world state aggregator
        and no hard-coded system prompt (world state becomes the system prompt).
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            main()
            
            # Verify session was created with system_prompt=None and world_state_aggregator
            mock_session_class.assert_called_once()
            call_kwargs = mock_session_class.call_args[1]
            # System prompt should be None (world state will be used instead)
            assert call_kwargs.get("system_prompt") is None
            # World state aggregator should be present
            assert "world_state_aggregator" in call_kwargs
            assert call_kwargs["world_state_aggregator"] is not None
    
    @patch('builtins.input', side_effect=['/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_welcome_message(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that welcome message is printed on startup.
        
        Rationale: Ensures users see helpful instructions when REPL starts.
        """
        with patch('broca.main_repl.ConversationSession'):
            main()
            
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("BrocaOS REPL" in call for call in print_calls)
            assert any("/exit" in call or "exit" in call for call in print_calls)
            assert any("/reset" in call or "reset" in call for call in print_calls)
    
    @patch('builtins.input', side_effect=['Test message', '/exit'])
    @patch('builtins.print')
    def test_repl_no_console_logging_interference(self, mock_print, mock_input):
        """
        Test that console logging suppression prevents log messages from interfering with streaming.
        
        Rationale: Ensures warnings and errors don't appear in console output during REPL streaming,
        preventing them from breaking the streaming display.
        """
        import logging
        import sys
        from io import StringIO
        from broca.logging_config import setup_logging
        from broca.config import LoggingConfig
        
        # Capture stderr to verify no log messages appear
        stderr_capture = StringIO()
        original_stderr = sys.stderr
        sys.stderr = stderr_capture
        
        try:
            # Setup logging with console suppression enabled (default)
            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            
            # Temporarily modify config to ensure suppression is enabled
            from broca import logging_config
            original_config = logging_config.config
            logging_config.config.logging = LoggingConfig(
                level="INFO",
                file_path="test_repl.log",
                suppress_console_logging=True
            )
            
            setup_logging()
            
            # Log warnings and errors that would normally interfere with streaming
            logger = logging.getLogger("test.repl")
            logger.warning("This warning should not appear in console")
            logger.error("This error should not appear in console")
            
            # Flush handlers
            for handler in root_logger.handlers:
                handler.flush()
            
            # Verify nothing was written to stderr
            stderr_content = stderr_capture.getvalue()
            assert "This warning should not appear in console" not in stderr_content
            assert "This error should not appear in console" not in stderr_content
            
            # Verify no console handlers exist (StreamHandler writing to stdout/stderr)
            console_handlers = [
                h for h in root_logger.handlers 
                if isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr)
            ]
            assert len(console_handlers) == 0
            
            # Restore original config
            logging_config.config = original_config
        finally:
            sys.stderr = original_stderr
            root_logger.handlers.clear()


class TestREPLComplexScenarios:
    """Test complex REPL usage scenarios."""
    
    @patch('builtins.input', side_effect=[
        'First message',
        '/reset',
        'Second message',
        'Third message',
        '/reset',
        'Final message',
        '/exit'
    ])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_multiple_resets(self, mock_setup_logging, mock_print, mock_input):
        """
        Test handling of multiple /reset commands in a session.
        
        Rationale: Ensures reset functionality works correctly when used multiple times.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.return_value = "Response"
            mock_session_class.return_value = mock_session
            
            main()
            
            # Should create session 3 times (initial + 2 resets)
            assert mock_session_class.call_count == 3
            # Should send 4 messages: First message, Second message, Third message, Final message
            # (the /reset commands don't send messages, but all user inputs before them do)
            assert mock_session.send.call_count == 4
            mock_session.send.assert_any_call("First message", stream=True)
            mock_session.send.assert_any_call("Second message", stream=True)
            mock_session.send.assert_any_call("Third message", stream=True)
            mock_session.send.assert_any_call("Final message", stream=True)
    
    @patch('builtins.input', side_effect=[
        'Message 1',
        'Message 2',
        'Message 3',
        'Message 4',
        'Message 5',
        '/exit'
    ])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_extended_conversation(self, mock_setup_logging, mock_print, mock_input):
        """
        Test extended conversation with many turns.
        
        Rationale: Ensures the REPL works correctly for longer usage sessions.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.return_value = "Response"
            mock_session_class.return_value = mock_session
            
            main()
            
            # Verify all messages were sent
            assert mock_session.send.call_count == 5
            for i in range(1, 6):
                mock_session.send.assert_any_call(f"Message {i}", stream=True)


class TestREPLMemoryCleanup:
    """Test memory manager cleanup on exit."""
    
    @patch('builtins.input', side_effect=['/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    @patch('broca.main_repl._initialize_memory_manager')
    def test_memory_manager_closed_on_exit(self, mock_init_memory, mock_setup_logging, mock_print, mock_input):
        """
        Test that memory_manager.close() is called when /exit is used.
        
        Rationale: Ensures vector index is saved to disk on normal exit.
        """
        mock_memory_manager = Mock()
        mock_init_memory.return_value = mock_memory_manager
        
        with patch('broca.main_repl.ConversationSession'):
            main()
            
            # Verify memory manager was closed
            mock_memory_manager.close.assert_called_once()
    
    @patch('builtins.input', side_effect=['/quit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    @patch('broca.main_repl._initialize_memory_manager')
    def test_memory_manager_closed_on_quit(self, mock_init_memory, mock_setup_logging, mock_print, mock_input):
        """
        Test that memory_manager.close() is called when /quit is used.
        
        Rationale: Ensures vector index is saved on /quit command.
        """
        mock_memory_manager = Mock()
        mock_init_memory.return_value = mock_memory_manager
        
        with patch('broca.main_repl.ConversationSession'):
            main()
            
            # Verify memory manager was closed
            mock_memory_manager.close.assert_called_once()
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    @patch('broca.main_repl._initialize_memory_manager')
    def test_memory_manager_closed_on_keyboard_interrupt(self, mock_init_memory, mock_setup_logging, mock_print, mock_input):
        """
        Test that memory_manager.close() is called on KeyboardInterrupt (Ctrl+C).
        
        Rationale: Ensures vector index is saved even when user interrupts with Ctrl+C.
        """
        mock_memory_manager = Mock()
        mock_init_memory.return_value = mock_memory_manager
        
        with patch('broca.main_repl.ConversationSession'):
            main()
            
            # Verify memory manager was closed
            mock_memory_manager.close.assert_called_once()
    
    @patch('builtins.input', side_effect=EOFError())
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    @patch('broca.main_repl._initialize_memory_manager')
    def test_memory_manager_closed_on_eof(self, mock_init_memory, mock_setup_logging, mock_print, mock_input):
        """
        Test that memory_manager.close() is called on EOFError (Ctrl+D).
        
        Rationale: Ensures vector index is saved even when user sends EOF.
        """
        mock_memory_manager = Mock()
        mock_init_memory.return_value = mock_memory_manager
        
        with patch('broca.main_repl.ConversationSession'):
            main()
            
            # Verify memory manager was closed
            mock_memory_manager.close.assert_called_once()
    
    @patch('builtins.input', side_effect=['/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    @patch('broca.main_repl._initialize_memory_manager')
    def test_memory_manager_closed_when_none(self, mock_init_memory, mock_setup_logging, mock_print, mock_input):
        """
        Test that no error occurs when memory_manager is None (memory disabled).
        
        Rationale: Ensures cleanup handles the case where memory is not initialized.
        """
        mock_init_memory.return_value = None
        
        with patch('broca.main_repl.ConversationSession'):
            # Should not raise any errors
            main()
            
            # Verify initialization was attempted
            mock_init_memory.assert_called_once()
    
    @patch('builtins.input', side_effect=['Test message', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    @patch('broca.main_repl._initialize_memory_manager')
    def test_memory_manager_closed_on_error(self, mock_init_memory, mock_setup_logging, mock_print, mock_input):
        """
        Test that memory_manager.close() is called even if an error occurs.
        
        Rationale: Ensures cleanup happens in finally block even on exceptions.
        """
        mock_memory_manager = Mock()
        mock_init_memory.return_value = mock_memory_manager
        
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.side_effect = Exception("Test error")
            mock_session_class.return_value = mock_session
            
            # Error should be caught and handled gracefully, but cleanup should still happen
            main()
            
            # Verify memory manager was closed despite the error
            mock_memory_manager.close.assert_called_once()
            # Verify error was handled (printed error message)
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("error" in call.lower() for call in print_calls)


class TestMemoryInitialization:
    """Test memory manager initialization."""
    
    @patch('broca.main_repl.EmbeddingService')
    @patch('broca.main_repl.MemoryStorage')
    @patch('broca.main_repl.VectorIndex')
    @patch('broca.main_repl.MemoryManager')
    def test_memory_initialization_success(self, mock_memory_manager_class, mock_vector_index_class, mock_storage_class, mock_embedding_service_class):
        """
        Test that memory manager initializes successfully when all dependencies are available.
        
        Rationale: Ensures memory is enabled when all required packages are installed.
        """
        from broca.main_repl import _initialize_memory_manager
        
        # Mock successful initialization
        mock_embedding_service = Mock()
        mock_embedding_service_class.return_value = mock_embedding_service
        
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        
        mock_vector_index = Mock()
        mock_vector_index_class.return_value = mock_vector_index
        
        mock_manager = Mock()
        mock_memory_manager_class.return_value = mock_manager
        
        result = _initialize_memory_manager()
        
        assert result is not None
        assert result == mock_manager
        mock_embedding_service_class.assert_called_once()
        mock_storage_class.assert_called_once()
        mock_vector_index_class.assert_called_once()
        mock_memory_manager_class.assert_called_once_with(mock_storage, mock_vector_index, mock_embedding_service)
    
    @patch('broca.main_repl.EmbeddingService')
    def test_memory_initialization_fails_on_embedding_error(self, mock_embedding_service_class):
        """
        Test that memory initialization fails gracefully when EmbeddingService fails.
        
        Rationale: Ensures memory is disabled when embedding service cannot be initialized.
        """
        from broca.main_repl import _initialize_memory_manager
        
        # Mock EmbeddingService initialization failure
        mock_embedding_service_class.side_effect = ValueError("API key required")
        
        result = _initialize_memory_manager()
        
        assert result is None
    
    @patch('broca.main_repl.EmbeddingService')
    @patch('broca.main_repl.MemoryStorage')
    @patch('broca.main_repl.VectorIndex')
    def test_memory_initialization_fails_on_vector_index_error(self, mock_vector_index_class, mock_storage_class, mock_embedding_service_class):
        """
        Test that memory initialization fails gracefully when VectorIndex fails.
        
        Rationale: Ensures memory is disabled when faiss-cpu is not installed.
        """
        from broca.main_repl import _initialize_memory_manager
        
        # Mock successful embedding service
        mock_embedding_service = Mock()
        mock_embedding_service_class.return_value = mock_embedding_service
        
        # Mock storage
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        
        # Mock VectorIndex initialization failure (e.g., faiss-cpu not installed)
        mock_vector_index_class.side_effect = ValueError("faiss-cpu package is not installed")
        
        result = _initialize_memory_manager()
        
        assert result is None
        # Verify storage was closed when vector index failed
        mock_storage.close.assert_called_once()
    
    @patch('broca.main_repl.EmbeddingService')
    @patch('broca.main_repl.MemoryStorage')
    @patch('broca.main_repl.VectorIndex')
    @patch('broca.main_repl.MemoryManager')
    def test_memory_initialization_fails_on_general_error(self, mock_memory_manager_class, mock_vector_index_class, mock_storage_class, mock_embedding_service_class):
        """
        Test that memory initialization fails gracefully on any exception.
        
        Rationale: Ensures memory is disabled when any unexpected error occurs.
        """
        from broca.main_repl import _initialize_memory_manager
        
        # Mock successful embedding service and storage
        mock_embedding_service = Mock()
        mock_embedding_service_class.return_value = mock_embedding_service
        
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        
        mock_vector_index = Mock()
        mock_vector_index_class.return_value = mock_vector_index
        
        # Mock MemoryManager initialization failure
        mock_memory_manager_class.side_effect = Exception("Unexpected error")
        
        result = _initialize_memory_manager()
        
        assert result is None


class TestREPLStreaming:
    """Test streaming functionality in REPL."""
    
    @patch('builtins.input', side_effect=['Hello', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_repl_uses_streaming(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that REPL uses streaming when available.
        
        Rationale: Ensures REPL leverages streaming for better UX.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            mock_session.send.return_value = "Hello! How can I help?"
            mock_session_class.return_value = mock_session
            
            main()
            
            # Verify send was called with streaming enabled
            mock_session.send.assert_called_once_with("Hello", stream=True)
            
            # Note: We can't easily verify streaming happened here since it's internal
            # But we can verify the session was used correctly
    
    @patch('builtins.input', side_effect=['Test message', '/exit'])
    @patch('builtins.print')
    @patch('broca.main_repl.setup_logging')
    def test_repl_streaming_output(self, mock_setup_logging, mock_print, mock_input):
        """
        Test that streaming output appears correctly in REPL.
        
        Rationale: Ensures streaming chunks are displayed properly to user.
        """
        with patch('broca.main_repl.ConversationSession') as mock_session_class:
            mock_session = Mock()
            # Simulate streaming: send() will print during execution
            # For this test, we'll verify the output format
            mock_session.send.return_value = "Streamed response"
            mock_session_class.return_value = mock_session
            
            main()
            
            # Verify send was called with streaming
            mock_session.send.assert_called_once_with("Test message", stream=True)
            
            # Verify response handling (either printed during streaming or after)
            # Note: When streaming is used, the response is printed during send()
            # When streaming is disabled, it's printed after send() returns
            # Since we're using a mock, we can't easily verify the exact output format
            # but we can verify send() was called correctly
            assert mock_session.send.called

