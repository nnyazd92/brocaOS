"""
Tests for conversation logging (turn_before and turn_after events).

Tests that conversation logs are generated for each turn.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json
import logging

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tests.utils import build_llm_response


class LogCapture:
    """Capture log records for testing."""
    
    def __init__(self, logger_name: str, level: int = logging.INFO):
        self.logger_name = logger_name
        self.level = level
        self.records = []
        self.handler = None
    
    def __enter__(self):
        logger = logging.getLogger(self.logger_name)
        self.handler = logging.Handler()
        self.handler.setLevel(self.level)
        self.handler.emit = self.records.append
        logger.addHandler(self.handler)
        logger.setLevel(self.level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = logging.getLogger(self.logger_name)
        logger.removeHandler(self.handler)
    
    def has_event(self, event_name: str) -> bool:
        """Check if a log record with given event exists."""
        return any(
            hasattr(record, "event") and record.event == event_name
            for record in self.records
        )
    
    def get_events(self) -> list:
        """Get all event names from log records."""
        events = []
        for record in self.records:
            if hasattr(record, "event"):
                events.append(record.event)
        return events


class TestConversationLogging:
    """Test that conversation logs are generated."""
    
    def test_turn_before_logged(self, mock_llm_client: Mock):
        """
        Test that turn_before event is logged when user sends message.
        
        Rationale: Ensures conversation logging starts correctly.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        final_response = build_llm_response(content="Test response")
        mock_llm_client.chat.return_value = final_response
        mock_llm_client.extract_tool_calls.return_value = []
        mock_llm_client.extract_assistant_content.return_value = "Test response"
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Test message")
        
        # Should have logged turn_before event
        assert logs.has_event("turn_before")
    
    def test_turn_after_logged(self, mock_llm_client: Mock):
        """
        Test that turn_after event is logged when assistant responds.
        
        Rationale: Ensures conversation logging completes correctly.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        final_response = build_llm_response(content="Test response")
        mock_llm_client.chat.return_value = final_response
        mock_llm_client.extract_tool_calls.return_value = []
        mock_llm_client.extract_assistant_content.return_value = "Test response"
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Test message")
        
        # Should have logged turn_after event
        assert logs.has_event("turn_after")
    
    def test_both_turn_events_logged(self, mock_llm_client: Mock):
        """
        Test that both turn_before and turn_after are logged in sequence.
        
        Rationale: Ensures complete conversation logging for each turn.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        final_response = build_llm_response(content="Test response")
        mock_llm_client.chat.return_value = final_response
        mock_llm_client.extract_tool_calls.return_value = []
        mock_llm_client.extract_assistant_content.return_value = "Test response"
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Test message")
        
        events = logs.get_events()
        
        # Should have both events
        assert "turn_before" in events
        assert "turn_after" in events
        
        # turn_before should come before turn_after
        turn_before_idx = events.index("turn_before")
        turn_after_idx = events.index("turn_after")
        assert turn_before_idx < turn_after_idx
    
    def test_turn_after_logged_with_tool_calls(self, mock_llm_client: Mock):
        """
        Test that turn_after is logged even when tool calls are involved.
        
        Rationale: Ensures logging works correctly with tool iterations.
        """
        registry = ToolRegistry()
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        # First response has tool calls
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "arguments": json.dumps({"query": "test"})
                        }
                    }]
                }
            }]
        }
        
        # Second response is final
        final_response = build_llm_response(content="Final response")
        
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final response"]
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Test message")
        
        # Should have logged turn_after event
        assert logs.has_event("turn_after")
    
    def test_turn_after_logged_with_critic_tool(self, mock_llm_client: Mock):
        """
        Test that turn_after is logged when critic tool is used.
        
        Rationale: Ensures logging works correctly with critic tool.
        """
        registry = ToolRegistry()
        
        class MockCriticTool:
            @property
            def name(self) -> str:
                return "critic"
            
            @property
            def description(self) -> str:
                return "Mock critic"
            
            @property
            def parameters(self) -> dict:
                return {
                    "type": "object",
                    "properties": {
                        "world_state": {"type": "object"},
                        "content": {"type": "string"}
                    },
                    "required": ["world_state", "content"]
                }
            
            def execute(self, **kwargs):
                return {"accepted": True, "feedback": "Accepted", "violations": []}
            
            def format_result(self, result: dict) -> str:
                return "ACCEPTED"
        
        critic_tool = MockCriticTool()
        registry.register_tool(critic_tool)
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        # Critic call
        critic_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "critic",
                            "arguments": json.dumps({
                                "world_state": {"constraints": {}},
                                "content": "test"
                            })
                        }
                    }]
                }
            }]
        }
        
        # Final response
        final_response = build_llm_response(content="Final response")
        
        mock_llm_client.chat.side_effect = [critic_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            critic_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final response"]
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Test message")
        
        # Should have logged turn_after event
        assert logs.has_event("turn_after")

    
    def test_turn_after_logged_on_max_iterations(self, mock_llm_client: Mock):
        """
        Test that turn_after is logged even when max iterations is reached.
        
        Rationale: Ensures logging works correctly in all code paths.
        """
        registry = ToolRegistry()
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        session._max_tool_iterations = 2  # Set low to trigger max iterations
        
        # Tool call response (will loop)
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "arguments": json.dumps({"query": "test"})
                        }
                    }]
                }
            }]
        }
        
        # Mock will keep returning tool calls until max iterations
        mock_llm_client.chat.return_value = tool_call_response
        mock_llm_client.extract_tool_calls.return_value = tool_call_response["choices"][0]["message"]["tool_calls"]
        mock_llm_client.extract_assistant_content.return_value = "Max iterations response"
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Test message")
        
        # Should have logged turn_after event even on max iterations
        assert logs.has_event("turn_after")
    
    def test_turn_after_logged_on_timeout_error(self, mock_llm_client: Mock):
        """
        Test that turn_after is logged even when TimeoutError occurs.
        
        Rationale: Ensures logging works correctly in error paths.
        """
        session = ConversationSession(llm=mock_llm_client)
        
        # Simulate TimeoutError
        mock_llm_client.chat.side_effect = TimeoutError("Request timed out")
        
        with LogCapture("broca.repl.session") as logs:
            response = session.send("Test message")
        
        # Should have logged turn_after event even on error
        assert logs.has_event("turn_after")
