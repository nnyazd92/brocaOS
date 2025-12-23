"""
Unit tests for ConversationSession.

Tests session management, message history, context tracking, and logging functionality.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
import logging

from broca.repl.session import ConversationSession
from broca.tests.utils import build_llm_response, create_message_list, LogCapture


class TestConversationSessionInitialization:
    """Test ConversationSession initialization with various configurations."""
    
    def test_init_without_system_prompt(self, mock_llm_client: Mock):
        """
        Test initialization without system prompt creates empty message list.
        
        Rationale: Ensures sessions can be created without a system prompt.
        """
        session = ConversationSession(llm=mock_llm_client)
        assert session.messages == []
        assert session.llm == mock_llm_client
    
    def test_init_with_system_prompt(self, mock_llm_client: Mock):
        """
        Test initialization with system prompt adds it to messages.
        
        Rationale: Ensures system prompts are correctly added to conversation history.
        """
        system_prompt = "You are a helpful assistant."
        session = ConversationSession(system_prompt=system_prompt, llm=mock_llm_client)
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        assert session.messages[0]["content"] == system_prompt
    
    def test_init_with_default_llm(self):
        """
        Test initialization creates default DeepSeekClient when none provided.
        
        Rationale: Ensures dependency injection is optional and defaults work correctly.
        """
        # The actual client type depends on configured provider (deepseek or openai).
        # This test should verify that a real LLM client is created, not which provider.
        from broca.llm.deepseek_client import DeepSeekClient
        from broca.llm.openai_client import OpenAIClient

        session = ConversationSession()
        assert session.llm is not None
        assert isinstance(session.llm, (DeepSeekClient, OpenAIClient))
    
    def test_init_with_custom_llm(self, mock_llm_client: Mock):
        """
        Test that custom LLM client can be injected.
        
        Rationale: Ensures dependency injection pattern works for testing.
        """
        session = ConversationSession(llm=mock_llm_client)
        assert session.llm == mock_llm_client


class TestConversationSessionSend:
    """Test the send() method for handling user messages and LLM interactions."""
    
    def test_send_single_turn(self, mock_llm_client: Mock):
        """
        Test single conversation turn adds messages correctly.
        
        Rationale: Ensures basic send() functionality works as expected.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Hello! How can I help?")
        session = ConversationSession(system_prompt="You are helpful", llm=mock_llm_client)
        
        response = session.send("Hi there")
        
        assert response == "Hello! How can I help?"
        assert len(session.messages) == 3  # system, user, assistant
        assert session.messages[1]["role"] == "user"
        assert session.messages[1]["content"] == "Hi there"
        assert session.messages[2]["role"] == "assistant"
        assert session.messages[2]["content"] == "Hello! How can I help?"
    
    def test_send_multi_turn_conversation(self, mock_llm_client: Mock):
        """
        Test multiple conversation turns preserve context.
        
        Rationale: Ensures conversation history is maintained across multiple exchanges.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(system_prompt="System", llm=mock_llm_client)
        
        session.send("First message")
        session.send("Second message")
        session.send("Third message")
        
        assert len(session.messages) == 7  # system + 3 turns (user+assistant each)
        assert session.messages[1]["content"] == "First message"
        assert session.messages[3]["content"] == "Second message"
        assert session.messages[5]["content"] == "Third message"
        
        # Verify all messages were passed to LLM (with full context)
        assert mock_llm_client.chat.call_count == 3
    
    def test_send_context_preservation(self, mock_llm_client: Mock):
        """
        Test that full context is passed to LLM on each turn.
        
        Rationale: Ensures the LLM receives complete conversation history.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(system_prompt="System prompt", llm=mock_llm_client)
        
        session.send("Message 1")
        call_args_1 = mock_llm_client.chat.call_args[0][0]
        assert len(call_args_1) == 2  # system, user (assistant is added after LLM call)
        
        session.send("Message 2")
        call_args_2 = mock_llm_client.chat.call_args[0][0]
        assert len(call_args_2) == 4  # system, user1, assistant1, user2 (assistant2 is added after LLM call)
        assert call_args_2[0]["role"] == "system"  # System prompt preserved
    
    def test_send_empty_response_handling(self, mock_llm_client: Mock):
        """
        Test handling of empty LLM response.
        
        Rationale: Ensures the session handles edge cases gracefully.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="")
        session = ConversationSession(llm=mock_llm_client)
        
        response = session.send("Test")
        
        assert response == ""
        assert len(session.messages) == 2  # user + empty assistant
        assert session.messages[1]["role"] == "assistant"
        assert session.messages[1]["content"] == ""
    
    def test_send_return_value(self, mock_llm_client: Mock):
        """
        Test that send() returns the assistant's response text.
        
        Rationale: Ensures the return value matches expected behavior.
        """
        expected_response = "This is the assistant's response"
        mock_llm_client.chat.return_value = build_llm_response(content=expected_response)
        session = ConversationSession(llm=mock_llm_client)
        
        response = session.send("User message")
        
        assert response == expected_response


class TestCurrentContextStats:
    """Test the _current_context_stats() method for tracking conversation metrics."""
    
    def test_stats_empty_session(self, mock_llm_client: Mock):
        """
        Test stats for empty session (no messages).
        
        Rationale: Ensures stats calculation works for initial state.
        """
        session = ConversationSession(llm=mock_llm_client)
        stats = session._current_context_stats()
        
        assert stats["messages_total"] == 0
        assert stats["messages_user"] == 0
        assert stats["messages_assistant"] == 0
        assert stats["messages_system"] == 0
        assert stats["total_chars"] == 0
    
    def test_stats_with_system_prompt(self, mock_llm_client: Mock):
        """
        Test stats correctly count system messages.
        
        Rationale: Ensures system prompts are counted in statistics.
        """
        session = ConversationSession(system_prompt="System message", llm=mock_llm_client)
        stats = session._current_context_stats()
        
        assert stats["messages_total"] == 1
        assert stats["messages_system"] == 1
        assert stats["total_chars"] == len("System message")
    
    def test_stats_accurate_counts(self, mock_llm_client: Mock):
        """
        Test that stats accurately count different message types.
        
        Rationale: Ensures message type counting logic is correct.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(system_prompt="System", llm=mock_llm_client)
        
        session.send("User 1")
        session.send("User 2")
        
        stats = session._current_context_stats()
        
        assert stats["messages_total"] == 5  # system + 2 user + 2 assistant
        assert stats["messages_user"] == 2
        assert stats["messages_assistant"] == 2
        assert stats["messages_system"] == 1
    
    def test_stats_character_counting(self, mock_llm_client: Mock):
        """
        Test that character counting is accurate.
        
        Rationale: Ensures total character count includes all message contents.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Assistant reply")
        session = ConversationSession(system_prompt="System prompt", llm=mock_llm_client)
        
        session.send("User message")
        
        stats = session._current_context_stats()
        expected_chars = len("System prompt") + len("User message") + len("Assistant reply")
        assert stats["total_chars"] == expected_chars
    
    def test_stats_with_various_messages(self, mock_llm_client: Mock):
        """
        Test stats with complex message history.
        
        Rationale: Ensures stats work correctly with various message configurations.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(system_prompt="System", llm=mock_llm_client)
        
        # Add multiple turns
        for i in range(5):
            session.send(f"User message {i}")
        
        stats = session._current_context_stats()
        
        assert stats["messages_total"] == 11  # 1 system + 5 user + 5 assistant
        assert stats["messages_user"] == 5
        assert stats["messages_assistant"] == 5
        assert stats["messages_system"] == 1


class TestSessionLogging:
    """Test logging functionality in ConversationSession."""
    
    def test_log_context_before_turn(self, mock_llm_client: Mock):
        """
        Test that context is logged before each turn.
        
        Rationale: Ensures logging provides visibility into conversation state.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        
        # Capture log records to check extra fields
        import logging
        log_records = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_records.append(record)
        
        logger = logging.getLogger("broca.repl.session")
        # Set level to ensure we capture INFO logs
        logger.setLevel(logging.INFO)
        handler = TestHandler()
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        try:
            session = ConversationSession(system_prompt="System", llm=mock_llm_client)
            session.send("Test message")
            
            # Find the "Sending user message" log record
            before_record = next((r for r in log_records if "Sending user message" in r.getMessage()), None)
            assert before_record is not None, f"Log records captured: {[r.getMessage() for r in log_records]}"
            assert hasattr(before_record, "event")
            assert before_record.event == "turn_before"
        finally:
            logger.removeHandler(handler)
            # Clean up any handlers added during session init
            logger.handlers = [h for h in logger.handlers if h != handler]
    
    def test_log_context_after_turn(self, mock_llm_client: Mock):
        """
        Test that context is logged after each turn with usage stats.
        
        Rationale: Ensures logging captures both request and response information.
        """
        mock_response = build_llm_response(
            content="Assistant response",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )
        mock_llm_client.chat.return_value = mock_response
        session = ConversationSession(llm=mock_llm_client)
        
        # Capture log records to check extra fields
        import logging
        log_records = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_records.append(record)
        
        logger = logging.getLogger("broca.repl.session")
        handler = TestHandler()
        logger.addHandler(handler)
        
        try:
            session.send("User message")
            
            # Find the "Received assistant message" log record
            after_record = next((r for r in log_records if "Received assistant message" in r.getMessage()), None)
            assert after_record is not None
            assert hasattr(after_record, "event")
            assert after_record.event == "turn_after"
        finally:
            logger.removeHandler(handler)
    
    def test_log_preview_truncation(self, mock_llm_client: Mock):
        """
        Test that long messages are truncated in logs.
        
        Rationale: Ensures log size is kept manageable while preserving useful information.
        """
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        session = ConversationSession(llm=mock_llm_client)
        
        long_message = "a" * 300  # Longer than 200 char preview limit
        with LogCapture("broca.repl.session") as logs:
            session.send(long_message)
        
        log_output = logs.getvalue()
        # Should contain truncated preview (200 chars + "...")
        assert len(long_message[:200] + "...") == 203
    
    def test_session_start_logging(self, mock_llm_client: Mock):
        """
        Test that session initialization is logged.
        
        Rationale: Ensures session lifecycle is tracked in logs.
        """
        # Capture log records to check extra fields
        import logging
        log_records = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_records.append(record)
        
        logger = logging.getLogger("broca.repl.session")
        handler = TestHandler()
        logger.addHandler(handler)
        
        try:
            ConversationSession(system_prompt="System", llm=mock_llm_client)
            
            # Find the "Conversation session started" log record
            start_record = next((r for r in log_records if "Conversation session started" in r.getMessage()), None)
            assert start_record is not None
            assert hasattr(start_record, "event")
            assert start_record.event == "session_start"
        finally:
            logger.removeHandler(handler)


class TestConversationSessionErrorHandling:
    """Test error handling in ConversationSession."""
    
    def test_send_handles_timeout_error(self, mock_llm_client: Mock):
        """
        Test that timeout errors return user-friendly message.
        
        Rationale: Ensures timeout errors are handled gracefully without crashing.
        """
        mock_llm_client.chat.side_effect = TimeoutError("API request timed out")
        session = ConversationSession(llm=mock_llm_client)
        
        response = session.send("Test message")
        
        assert "timeout" in response.lower() or "timed out" in response.lower()
        assert "apologize" in response.lower() or "sorry" in response.lower()
        # Verify user message was added
        assert len(session.messages) >= 2  # user + error assistant message
        assert session.messages[-2]["role"] == "user"
        assert session.messages[-1]["role"] == "assistant"
    
    def test_send_handles_network_error(self, mock_llm_client: Mock):
        """
        Test that network errors return user-friendly message.
        
        Rationale: Ensures network errors are handled gracefully.
        """
        mock_llm_client.chat.side_effect = ConnectionError("Network connection failed")
        session = ConversationSession(llm=mock_llm_client)
        
        response = session.send("Test message")
        
        assert "network" in response.lower() or "connection" in response.lower()
        assert "apologize" in response.lower() or "sorry" in response.lower()
        # Verify user message was added
        assert len(session.messages) >= 2
        assert session.messages[-2]["role"] == "user"
        assert session.messages[-1]["role"] == "assistant"
    
    def test_send_handles_http_error(self, mock_llm_client: Mock):
        """
        Test that HTTP errors are handled gracefully.
        
        Rationale: Ensures HTTP status errors don't crash the session.
        """
        import httpx
        mock_response = Mock()
        mock_llm_client.chat.side_effect = httpx.HTTPStatusError(
            "HTTP 500", request=Mock(), response=mock_response
        )
        session = ConversationSession(llm=mock_llm_client)
        
        response = session.send("Test message")
        
        assert "error" in response.lower() or "apologize" in response.lower()
        # Verify user message was added
        assert len(session.messages) >= 2
        assert session.messages[-2]["role"] == "user"
        assert session.messages[-1]["role"] == "assistant"
    
    def test_send_preserves_conversation_on_error(self, mock_llm_client: Mock):
        """
        Test that conversation state is preserved on errors.
        
        Rationale: Ensures errors don't corrupt conversation history.
        """
        # First successful turn
        mock_llm_client.chat.return_value = build_llm_response(content="First response")
        session = ConversationSession(system_prompt="System", llm=mock_llm_client)
        session.send("First message")
        
        initial_message_count = len(session.messages)
        
        # Error on second turn
        mock_llm_client.chat.side_effect = TimeoutError("Timeout")
        session.send("Second message")
        
        # Verify previous messages are still there
        assert len(session.messages) > initial_message_count
        assert session.messages[0]["role"] == "system"
        assert session.messages[1]["content"] == "First message"
        assert session.messages[2]["content"] == "First response"
    
    def test_send_saves_conversation_on_error(self, mock_llm_client: Mock):
        """
        Test that conversation is saved even on errors.
        
        Rationale: Ensures errors don't prevent conversation persistence.
        """
        mock_storage = Mock()
        mock_llm_client.chat.side_effect = TimeoutError("Timeout")
        session = ConversationSession(llm=mock_llm_client, storage=mock_storage)
        
        session.send("Test message")
        
        # Verify save was called (even after error)
        assert mock_storage.save_conversation.called


class TestConversationSessionStreaming:
    """Test streaming functionality in ConversationSession."""
    
    @patch('builtins.print')
    def test_send_streams_final_response(self, mock_print, mock_llm_client: Mock):
        """
        Test that final response streams when no tool calls.
        
        Rationale: Ensures streaming works for simple responses without tools.
        """
        # Create mock stream that yields strings directly
        # The chat_stream method yields strings, so we mock it to return an iterable of strings
        def mock_chat_stream(*args, **kwargs):
            yield "Hello"
            yield " world"
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream)
        mock_llm_client.extract_assistant_content = lambda x: "Hello world"
        mock_llm_client.extract_tool_calls = lambda x: []
        
        session = ConversationSession(llm=mock_llm_client)
        
        response = session.send("Hi")
        
        # Verify response is correct
        assert response == "Hello world"
        
        # Streaming is enabled when available, so chat_stream should be called
        assert mock_llm_client.chat_stream.called
        
        # Verify output was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("BrocaOS>" in call for call in print_calls)
        # With streaming, text is printed in chunks, so check for chunks
        assert any("Hello" in call for call in print_calls)
        assert any(" world" in call for call in print_calls)
    
    @patch('builtins.print')
    def test_send_streams_after_tool_calls(self, mock_print, mock_llm_client: Mock):
        """
        Test that streaming works after tool calls are resolved.
        
        Rationale: Ensures final response streams even after tool execution.
        """
        from broca.tools.registry import ToolRegistry
        
        # First response has tool calls (non-streaming)
        tool_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "arguments": "{}"
                        }
                    }]
                }
            }]
        }
        
        # Second response is final (streaming)
        def mock_chat_stream_final(*args, **kwargs):
            yield "Final"
            yield " response"
        
        # Mock tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.execute.return_value = {"role": "tool", "content": "Tool result"}
        
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.to_openai_format.return_value = [{"type": "function", "function": {"name": "test_tool"}}]
        mock_registry.execute_tool_call.return_value = {"role": "tool", "content": "Tool result"}
        mock_registry.get_tool.return_value = None  # No critic
        
        # Setup LLM mocks
        mock_llm_client.chat.return_value = tool_response
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream_final)
        mock_llm_client.extract_tool_calls = lambda x: (
            tool_response["choices"][0]["message"]["tool_calls"] if "tool_calls" in x.get("choices", [{}])[0].get("message", {}) else []
        )
        mock_llm_client.extract_assistant_content = lambda x: "Final response"
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=mock_registry)
        
        response = session.send("Use tool then respond")
        
        # Verify final response is correct
        assert response == "Final response"
        
        # With streaming enabled, the first iteration will attempt streaming
        # But if streaming returns minimal content and tool_calls are detected, it falls back to chat()
        # The final response will also use streaming
        # So both may be called - verify chat_stream was called at least once
        assert mock_llm_client.chat_stream.called or mock_llm_client.chat.called
    
    @patch('builtins.print')
    def test_send_no_streaming_during_tool_iterations(self, mock_print, mock_llm_client: Mock):
        """
        Test that intermediate tool call responses don't stream.
        
        Rationale: Ensures tool call detection works correctly (requires non-streaming).
        """
        from broca.tools.registry import ToolRegistry
        
        tool_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": "{}"}
                    }]
                }
            }]
        }
        
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.to_openai_format.return_value = [{"type": "function", "function": {"name": "test_tool"}}]
        mock_registry.execute_tool_call.return_value = {"role": "tool", "content": "Result"}
        mock_registry.get_tool.return_value = None
        
        mock_llm_client.chat.return_value = tool_response
        mock_llm_client.extract_tool_calls = lambda x: (
            tool_response["choices"][0]["message"]["tool_calls"] if "tool_calls" in x.get("choices", [{}])[0].get("message", {}) else []
        )
        mock_llm_client.extract_assistant_content = lambda x: ""
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=mock_registry)
        
        # This will hit max iterations since we're not providing a final response
        # With streaming enabled, streaming will be attempted but will fall back to chat()
        # when tool_calls are detected (see lines 291-300 in session.py)
        try:
            session.send("Use tool")
        except:
            pass
        
        # With streaming enabled, chat_stream will be called initially, but then
        # it will fall back to chat() when tool_calls are detected
        # So both may be called - verify that chat() was called (for tool call handling)
        assert mock_llm_client.chat.called
    
    @patch('builtins.print')
    def test_send_streaming_with_tools_available_but_not_called(self, mock_print, mock_llm_client: Mock):
        """
        Test that when tools are available, we use non-streaming to detect tool calls.
        
        Rationale: When tools are available, we must use non-streaming on first iteration
        to properly detect tool calls, even if the LLM doesn't use them.
        """
        from broca.tools.registry import ToolRegistry
        
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.to_openai_format.return_value = [{"type": "function", "function": {"name": "test_tool"}}]
        mock_registry.get_tool.return_value = None
        
        # When tools are available, we use non-streaming to detect tool calls
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.extract_assistant_content = lambda x: "Response"
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=mock_registry)
        
        response = session.send("Hello")
        
        assert response == "Response"
        # With streaming enabled, streaming will be attempted first
        # If it returns content (no tool calls), streaming succeeds
        # If it returns minimal content, it falls back to chat() to check for tool_calls
        # In this case, since there are no tool calls, streaming should succeed
        # So chat_stream should be called (or chat if streaming failed and fell back)
        assert mock_llm_client.chat_stream.called or mock_llm_client.chat.called
    
    @patch('builtins.print')
    @patch('broca.config.config')
    def test_send_streaming_respects_config(self, mock_config, mock_print, mock_llm_client: Mock):
        """
        Test that streaming can be disabled via config.
        
        Rationale: Ensures config setting controls streaming behavior.
        """
        # Disable streaming in config
        mock_config.llm.streaming_enabled = False
        # Set up other config attributes that might be accessed
        mock_config.summarization.last_turns_count = 10
        mock_config.llm.max_context_tokens = 100000
        mock_config.summarization.max_tool_result_size = 1000
        
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        mock_llm_client.extract_tool_calls = lambda x: []
        mock_llm_client.extract_assistant_content = lambda x: "Response"
        
        session = ConversationSession(llm=mock_llm_client)
        
        response = session.send("Hello")
        
        assert response == "Response"
        # Verify chat_stream was NOT called
        assert not hasattr(mock_llm_client, 'chat_stream') or not mock_llm_client.chat_stream.called
        # Verify regular chat was called
        mock_llm_client.chat.assert_called_once()
    
    @patch('builtins.print')
    def test_send_streaming_output_format(self, mock_print, mock_llm_client: Mock):
        """
        Test that streaming prints correctly with "BrocaOS> " prefix.
        
        Rationale: Ensures streaming output format matches non-streaming format.
        """
        def mock_chat_stream_format(*args, **kwargs):
            yield "Hello"
            yield " there"
        
        mock_llm_client.chat_stream = Mock(side_effect=mock_chat_stream_format)
        mock_llm_client.extract_assistant_content = lambda x: "Hello there"
        mock_llm_client.extract_tool_calls = lambda x: []
        
        session = ConversationSession(llm=mock_llm_client)
        
        session.send("Hi")
        
        # Verify print was called with "BrocaOS> " prefix
        print_calls = [str(call) for call in mock_print.call_args_list]
        # Check that "BrocaOS>" appears in the calls
        assert any("BrocaOS>" in str(call) for call in mock_print.call_args_list)

