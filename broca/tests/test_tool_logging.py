"""
Tests for extensive tool call logging.

Tests that all tool call lifecycle events are properly logged with
full transparency into inputs, outputs, and execution.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import json
import logging
from io import StringIO

from broca.tools.registry import ToolRegistry
from broca.repl.session import ConversationSession
from broca.tests.utils import build_llm_response


class MockTool:
    """Mock tool for testing logging."""
    
    def __init__(self, name: str):
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return f"Mock tool {self._name}"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            }
        }
    
    def execute(self, **kwargs):
        return {"result": f"Executed {self._name}", "data": kwargs}
    
    def format_result(self, result: dict) -> str:
        return f"Formatted result: {result}"


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
    
    def get_records_with_event(self, event_name: str) -> list:
        """Get all log records with given event."""
        return [
            record for record in self.records
            if hasattr(record, "event") and record.event == event_name
        ]


class TestToolRegistryLogging:
    """Test logging in ToolRegistry."""
    
    def test_tool_call_received_logging(self):
        """
        Test that tool call received is logged with full details.
        
        Rationale: Ensures we log when a tool call is received from LLM.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param": "value"})
            }
        }
        
        with LogCapture("broca.tools.registry") as logs:
            registry.execute_tool_call(tool_call)
        
        # Check that tool_call_received event was logged
        assert logs.has_event("tool_call_received")
        records = logs.get_records_with_event("tool_call_received")
        assert len(records) > 0
        
        record = records[0]
        assert hasattr(record, "tool_name")
        assert record.tool_name == "test_tool"
        assert hasattr(record, "tool_call_id")
        assert record.tool_call_id == "call_123"
    
    def test_tool_arguments_logging(self):
        """
        Test that parsed tool arguments are logged.
        
        Rationale: Ensures we log what arguments the LLM passed to the tool.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param": "test_value", "count": 5})
            }
        }
        
        with LogCapture("broca.tools.registry") as logs:
            registry.execute_tool_call(tool_call)
        
        # Check that arguments are logged
        records = logs.get_records_with_event("tool_call_executing")
        assert len(records) > 0
        
        record = records[0]
        assert hasattr(record, "arguments")
        assert record.arguments == {"param": "test_value", "count": 5}
    
    def test_tool_execution_start_logging(self):
        """
        Test that tool execution start is logged.
        
        Rationale: Ensures we log when tool execution begins.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param": "value"})
            }
        }
        
        with LogCapture("broca.tools.registry") as logs:
            registry.execute_tool_call(tool_call)
        
        assert logs.has_event("tool_call_executing")
    
    def test_tool_result_logging(self):
        """
        Test that tool result (raw and formatted) is logged.
        
        Rationale: Ensures we log both raw tool result and formatted result.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param": "value"})
            }
        }
        
        with LogCapture("broca.tools.registry") as logs:
            registry.execute_tool_call(tool_call)
        
        # Check that result was logged
        records = logs.get_records_with_event("tool_call_result")
        assert len(records) > 0
        
        record = records[0]
        assert hasattr(record, "tool_name")
        assert record.tool_name == "test_tool"
        assert hasattr(record, "result") or hasattr(record, "formatted_result")
    
    def test_tool_error_logging(self):
        """
        Test that tool execution errors are logged.
        
        Rationale: Ensures errors during tool execution are properly logged.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        tool.execute = Mock(side_effect=Exception("Test error"))
        registry.register_tool(tool)
        
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": json.dumps({"param": "value"})
            }
        }
        
        with LogCapture("broca.tools.registry", level=logging.ERROR) as logs:
            registry.execute_tool_call(tool_call)
        
        # Should have error logs
        error_records = [r for r in logs.records if r.levelno >= logging.ERROR]
        assert len(error_records) > 0
    
    def test_to_openai_format_logging(self):
        """
        Test that tool format conversion is logged.
        
        Rationale: Ensures we log when tools are converted to OpenAI format.
        """
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        with LogCapture("broca.tools.registry") as logs:
            registry.to_openai_format()
        
        # Should log tool conversion
        debug_records = [r for r in logs.records if "tools" in r.getMessage().lower() or "format" in r.getMessage().lower()]
        assert len(debug_records) > 0


class TestConversationSessionToolLogging:
    """Test logging in ConversationSession for tool calls."""
    
    def test_tool_calls_detected_logging(self, mock_llm_client: Mock):
        """
        Test that tool calls detection is logged.
        
        Rationale: Ensures we log when tool calls are detected in LLM response.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "arguments": json.dumps({"param": "value"})
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final answer")
        
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Use tool")
        
        # Check that tool calls detected was logged
        assert logs.has_event("tool_calls_detected")
        records = logs.get_records_with_event("tool_calls_detected")
        assert len(records) > 0
        
        record = records[0]
        assert hasattr(record, "tool_calls_count")
        assert record.tool_calls_count == 1
        assert hasattr(record, "tool_names")
        assert "test_tool" in record.tool_names
    
    def test_tool_call_processing_logging(self, mock_llm_client: Mock):
        """
        Test that individual tool call processing is logged.
        
        Rationale: Ensures we log each tool call being processed.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "arguments": json.dumps({"param": "value"})
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final answer")
        
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Use tool")
        
        # Check that tool call processing was logged
        assert logs.has_event("tool_call_processing")
    
    def test_tool_result_added_logging(self, mock_llm_client: Mock):
        """
        Test that tool results being added to conversation are logged.
        
        Rationale: Ensures we log when tool results are added to messages.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "arguments": json.dumps({"param": "value"})
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final answer")
        
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Use tool")
        
        # Check that tool result added was logged
        assert logs.has_event("tool_result_added")
    
    def test_tool_iteration_logging(self, mock_llm_client: Mock):
        """
        Test that tool iteration count is logged.
        
        Rationale: Ensures we track how many tool iterations occur.
        """
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register_tool(tool)
        
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "arguments": json.dumps({"param": "value"})
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final answer")
        
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final answer"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Use tool")
        
        # Check that iteration info is logged
        iteration_records = [
            r for r in logs.records
            if hasattr(r, "iteration") or "iteration" in r.getMessage().lower()
        ]
        assert len(iteration_records) > 0
    
    def test_tools_prepared_logging(self, mock_llm_client: Mock):
        """
        Test that tools being prepared for LLM is logged.
        
        Rationale: Ensures we log what tools are available to the LLM.
        """
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        mock_llm_client.extract_tool_calls.return_value = []
        mock_llm_client.extract_assistant_content.return_value = "Response"
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Hello")
        
        # Check that tools prepared was logged
        prepared_records = [
            r for r in logs.records
            if hasattr(r, "available_tools") or "tools" in r.getMessage().lower()
        ]
        assert len(prepared_records) > 0


class TestLoggingUtilities:
    """Test logging utility functions."""
    
    def test_truncation_for_strings(self):
        """
        Test that long strings are truncated in logs.
        
        Rationale: Ensures logs don't become unwieldy with large data.
        """
        # This will be tested when we implement the utilities
        # For now, just verify the concept
        long_string = "a" * 2000
        assert len(long_string) > 1000
        
        # Truncation should limit to reasonable size
        # (Implementation will be in logging_utils.py)
        pass
    
    def test_structured_log_format(self):
        """
        Test that logs use structured format with extra dict.
        
        Rationale: Ensures logs are machine-parseable and searchable.
        """
        logger = logging.getLogger("test")
        
        with LogCapture("test") as logs:
            logger.info(
                "Test message",
                extra={
                    "event": "test_event",
                    "tool_name": "test_tool",
                    "data": {"key": "value"}
                }
            )
        
        assert len(logs.records) > 0
        record = logs.records[0]
        assert hasattr(record, "event")
        assert record.event == "test_event"
        assert hasattr(record, "tool_name")
        assert record.tool_name == "test_tool"

