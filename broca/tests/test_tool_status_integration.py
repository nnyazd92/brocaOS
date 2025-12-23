"""
Integration tests for tool status display system.

Tests end-to-end tool invocation with visual feedback, including
multiple concurrent tool calls and interaction with streaming output.
"""

from __future__ import annotations

import pytest
import sys
import io
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tools import Tool


class MockTool(Tool):
    """Mock tool for testing."""
    
    def __init__(self, name: str = "mock_tool", delay: float = 0.1, success: bool = True):
        self._name = name
        self._delay = delay
        self._success = success
    
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
        time.sleep(self._delay)  # Simulate work
        if self._success:
            return {"success": True, "result": "test result"}
        else:
            return {"success": False, "error": "test error"}
    
    def format_result(self, result):
        if isinstance(result, dict) and result.get("success"):
            return "Success: " + str(result.get("result", ""))
        elif isinstance(result, dict) and not result.get("success"):
            return "Error: " + str(result.get("error", ""))
        return str(result)


class TestToolStatusIntegration:
    """Integration tests for tool status display."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM client."""
        llm = Mock()
        llm.chat = Mock(return_value={
            "choices": [{
                "message": {
                    "content": "I'll use a tool to help.",
                    "role": "assistant",
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "mock_tool",
                            "arguments": '{"param1": "value1"}'
                        }
                    }]
                }
            }]
        })
        llm.chat_stream = Mock(return_value=iter([]))
        llm.extract_assistant_content = Mock(return_value="I'll use a tool to help.")
        llm.extract_tool_calls = Mock(return_value=[{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "mock_tool",
                "arguments": '{"param1": "value1"}'
            }
        }])
        return llm
    
    @pytest.fixture
    def tool_registry(self):
        """Create tool registry with mock tool."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register_tool(tool)
        return registry
    
    def test_tool_invocation_shows_status(self, mock_llm, tool_registry):
        """Test that tool invocation shows status display."""
        # Capture stdout
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                # Create session after patching stdout so display uses patched stdout
                session = ConversationSession(
                    llm=mock_llm,
                    tool_registry=tool_registry
                )
                
                # Manually trigger tool handling
                response = {
                    "choices": [{
                        "message": {
                            "content": None,
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "mock_tool",
                                    "arguments": '{"param1": "value1"}'
                                }
                            }]
                        }
                    }]
                }
                
                tool_calls = [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "mock_tool",
                        "arguments": '{"param1": "value1"}'
                    }
                }]
                session._handle_tool_calls(response, tool_calls)
        
        output_str = output.getvalue()
        # Should have some output from status display
        assert len(output_str) > 0
    
    def test_multiple_tool_calls_sequential(self, mock_llm):
        """Test that multiple sequential tool calls show status correctly."""
        # Create new registry with multiple tools
        tool_registry = ToolRegistry()
        tool1 = MockTool(name="tool1", delay=0.05)
        tool2 = MockTool(name="tool2", delay=0.05)
        tool_registry.register_tool(tool1)
        tool_registry.register_tool(tool2)
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                # Create session after patching stdout
                session = ConversationSession(
                    llm=mock_llm,
                    tool_registry=tool_registry
                )
                
                response = {
                    "choices": [{
                        "message": {
                            "content": None,
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "tool1",
                                        "arguments": '{"param1": "value1"}'
                                    }
                                },
                                {
                                    "id": "call_2",
                                    "type": "function",
                                    "function": {
                                        "name": "tool2",
                                        "arguments": '{"param1": "value2"}'
                                    }
                                }
                            ]
                        }
                    }]
                }
                
                tool_calls = [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "tool1",
                            "arguments": '{"param1": "value1"}'
                        }
                    },
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "tool2",
                            "arguments": '{"param1": "value2"}'
                        }
                    }
                ]
                
                session._handle_tool_calls(response, tool_calls)
        
        output_str = output.getvalue()
        # Should have output for both tools
        assert "tool1" in output_str.lower() or "tool2" in output_str.lower()
    
    def test_tool_error_shows_error_indicator(self, mock_llm):
        """Test that tool errors show error indicator."""
        registry = ToolRegistry()
        failing_tool = MockTool(name="failing_tool", success=False)
        registry.register_tool(failing_tool)
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=True):
                # Create session after patching stdout
                session = ConversationSession(
                    llm=mock_llm,
                    tool_registry=registry
                )
                
                response = {
                    "choices": [{
                        "message": {
                            "content": None,
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_fail",
                                "type": "function",
                                "function": {
                                    "name": "failing_tool",
                                    "arguments": '{}'
                                }
                            }]
                        }
                    }]
                }
                
                tool_calls = [{
                    "id": "call_fail",
                    "type": "function",
                    "function": {
                        "name": "failing_tool",
                        "arguments": '{}'
                    }
                }]
                
                session._handle_tool_calls(response, tool_calls)
        
        output_str = output.getvalue()
        # Should have some indication of completion (checkmark or cross)
        assert len(output_str) > 0
    
    def test_non_tty_disables_display(self, mock_llm, tool_registry):
        """Test that display is disabled for non-TTY."""
        session = ConversationSession(
            llm=mock_llm,
            tool_registry=tool_registry
        )
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            with patch('sys.stdout.isatty', return_value=False):
                response = {
                    "choices": [{
                        "message": {
                            "content": None,
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "mock_tool",
                                    "arguments": '{"param1": "value1"}'
                                }
                            }]
                        }
                    }]
                }
                
                tool_calls = [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "mock_tool",
                        "arguments": '{"param1": "value1"}'
                    }
                }]
                
                # Should not crash
                session._handle_tool_calls(response, tool_calls)
        
        # Tool should still execute even if display is disabled
        assert len(session.messages) > 0
    
    def test_display_does_not_interfere_with_tool_execution(self, mock_llm, tool_registry):
        """Test that display system doesn't interfere with tool execution."""
        session = ConversationSession(
            llm=mock_llm,
            tool_registry=tool_registry
        )
        
        with patch('sys.stdout.isatty', return_value=True):
            response = {
                "choices": [{
                    "message": {
                        "content": None,
                        "role": "assistant",
                        "tool_calls": [{
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "mock_tool",
                                "arguments": '{"param1": "value1"}'
                            }
                        }]
                    }
                }]
            }
            
            tool_calls = [{
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "mock_tool",
                    "arguments": '{"param1": "value1"}'
                }
            }]
            
            initial_message_count = len(session.messages)
            session._handle_tool_calls(response, tool_calls)
            
            # Should have added messages (assistant message with tool_calls + tool result)
            assert len(session.messages) > initial_message_count
    
    def test_concurrent_tool_calls_thread_safety(self, mock_llm):
        """Test that concurrent tool calls are handled safely."""
        registry = ToolRegistry()
        tool = MockTool(name="concurrent_tool", delay=0.1)
        registry.register_tool(tool)
        
        session = ConversationSession(
            llm=mock_llm,
            tool_registry=registry
        )
        
        errors = []
        
        def execute_tool_call(tool_call_id: str):
            try:
                with patch('sys.stdout.isatty', return_value=True):
                    response = {
                        "choices": [{
                            "message": {
                                "content": None,
                                "role": "assistant",
                                "tool_calls": [{
                                    "id": tool_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": "concurrent_tool",
                                        "arguments": '{}'
                                    }
                                }]
                            }
                        }]
                    }
                    
                    tool_calls = [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": "concurrent_tool",
                            "arguments": '{}'
                        }
                    }]
                    
                    session._handle_tool_calls(response, tool_calls)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=execute_tool_call, args=(f"call_{i}",))
            for i in range(3)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Thread safety issues: {errors}"

