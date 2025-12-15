"""
Tests for relaxed critic enforcement.

Tests that the LLM can use other tools (terminal, web_search, etc.) after
critic rejection, and that enforcement only happens when attempting final response.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json
import logging

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tests.utils import build_llm_response


class MockCriticTool:
    """Mock critic tool for testing."""
    
    def __init__(self, name: str = "critic"):
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return "Mock critic tool"
    
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
        if result.get("accepted", False):
            return f"ACCEPTED: {result.get('feedback', '')}"
        else:
            return f"REJECTED: {result.get('feedback', '')}"


class MockTerminalTool:
    """Mock terminal tool for testing."""
    
    def __init__(self):
        self._execute_called = False
        self._execute_call_count = 0
    
    @property
    def name(self) -> str:
        return "terminal"
    
    @property
    def description(self) -> str:
        return "Mock terminal tool"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string"}
            },
            "required": ["command"]
        }
    
    def execute(self, **kwargs):
        self._execute_called = True
        self._execute_call_count += 1
        return {"success": True, "stdout": "Command output", "returncode": 0}
    
    def format_result(self, result: dict) -> str:
        return f"Output: {result.get('stdout', '')}"
    
    @property
    def execute_called(self):
        return self._execute_called
    
    @property
    def execute_call_count(self):
        return self._execute_call_count


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


class TestRelaxedCriticEnforcement:
    """Test relaxed critic enforcement allowing tool usage."""
    
    def test_tools_allowed_after_critic_rejection(self, mock_llm_client: Mock):
        """
        Test that other tools can be called after critic rejection.
        
        Rationale: Ensures LLM can use tools to gather information after rejection.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Rejected",
            "violations": []
        })
        terminal_tool = MockTerminalTool()
        registry.register_tool(critic_tool)
        registry.register_tool(terminal_tool)
        
        # First: critic call (rejects)
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
        
        # Second: LLM uses terminal tool (should be allowed)
        terminal_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "terminal",
                            "arguments": json.dumps({"command": "python test.py"})
                        }
                    }]
                }
            }]
        }
        
        # Third: LLM calls critic again (after using terminal)
        critic_response_2 = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_3",
                        "type": "function",
                        "function": {
                            "name": "critic",
                            "arguments": json.dumps({
                                "world_state": {"constraints": {}},
                                "content": "revised test"
                            })
                        }
                    }]
                }
            }]
        }
        
        # Make critic accept on second call
        critic_tool.execute = Mock(side_effect=[
            {"accepted": False, "feedback": "Rejected", "violations": []},  # First call
            {"accepted": True, "feedback": "Accepted", "violations": []}   # Second call
        ])
        
        # Fourth: Critic accepts, final response
        final_response = build_llm_response(content="Final response")
        
        # Flow: critic rejects -> terminal -> critic accepts -> final response
        # But when final response is attempted before critic accepts, it gets blocked
        # So we need: critic -> terminal -> critic -> (tries final, blocked) -> critic -> final
        # Actually, let me trace through:
        # 1. critic rejects
        # 2. terminal (allowed now)
        # 3. critic accepts
        # 4. final response (should be allowed)
        
        mock_llm_client.chat.side_effect = [
            critic_response,      # 1. Critic rejects
            terminal_response,    # 2. Terminal (allowed)
            critic_response_2,    # 3. Critic accepts
            final_response        # 4. Final response
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            critic_response["choices"][0]["message"]["tool_calls"],  # 1
            terminal_response["choices"][0]["message"]["tool_calls"],  # 2
            critic_response_2["choices"][0]["message"]["tool_calls"],  # 3
            []  # 4. Final response
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            None, None, None, "Final response"
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        response = session.send("Test message")
        
        # Terminal tool should have been called (after critic rejection)
        assert terminal_tool.execute_called
        
        # Final response should be returned after critic accepts
        assert response == "Final response"
    
    def test_terminal_tool_allowed_after_rejection(self, mock_llm_client: Mock):
        """
        Test that terminal tool works after critic rejection.
        
        Rationale: Ensures terminal tool can be used to gather code output/errors.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Rejected",
            "violations": []
        })
        terminal_tool = MockTerminalTool()
        registry.register_tool(critic_tool)
        registry.register_tool(terminal_tool)
        
        # Critic rejects
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
        
        # Terminal tool call (should be allowed)
        terminal_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "terminal",
                            "arguments": json.dumps({"command": "python test.py"})
                        }
                    }]
                }
            }]
        }
        
        mock_llm_client.chat.side_effect = [critic_response, terminal_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            critic_response["choices"][0]["message"]["tool_calls"],
            terminal_response["choices"][0]["message"]["tool_calls"]
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, None]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        # Should not raise exception, should allow terminal tool
        session.send("Test message")
        
        # Terminal should have been executed
        assert terminal_tool.execute_called
    
    def test_final_response_still_blocked(self, mock_llm_client: Mock):
        """
        Test that final response is still blocked without critic acceptance.
        
        Rationale: Ensures core enforcement (blocking final response) still works.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Rejected",
            "violations": []
        })
        registry.register_tool(critic_tool)
        
        # Critic rejects
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
        
        # LLM tries final response (should be blocked)
        final_response_attempt = build_llm_response(content="Final response")
        
        # After blocking, LLM calls critic again
        critic_response_2 = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "critic",
                            "arguments": json.dumps({
                                "world_state": {"constraints": {}},
                                "content": "revised"
                            })
                        }
                    }]
                }
            }]
        }
        
        # Critic accepts
        critic_tool.execute = Mock(side_effect=[
            {"accepted": False, "feedback": "Rejected", "violations": []},
            {"accepted": True, "feedback": "Accepted", "violations": []}
        ])
        
        final_response_allowed = build_llm_response(content="Final after acceptance")
        
        mock_llm_client.chat.side_effect = [
            critic_response,
            final_response_attempt,  # Should be blocked
            critic_response_2,
            final_response_allowed
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            critic_response["choices"][0]["message"]["tool_calls"],
            [],  # No tool calls (trying final response)
            critic_response_2["choices"][0]["message"]["tool_calls"],
            []
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            None, "Final response", None, "Final after acceptance"
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            response = session.send("Test message")
        
        # Should have blocked final response
        assert logs.has_event("critic_rejection_blocked_final_response")
        
        # Final response should be after acceptance
        assert "after acceptance" in response or response == "Final after acceptance"
    
    def test_critic_can_be_called_after_other_tools(self, mock_llm_client: Mock):
        """
        Test that critic can be called after using other tools.
        
        Rationale: Ensures LLM can gather info with tools, then call critic.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(side_effect=[
            {"accepted": False, "feedback": "Rejected", "violations": []},
            {"accepted": True, "feedback": "Accepted", "violations": []}
        ])
        terminal_tool = MockTerminalTool()
        registry.register_tool(critic_tool)
        registry.register_tool(terminal_tool)
        
        # Flow: critic rejects -> terminal -> critic accepts
        critic_response_1 = {
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
        
        terminal_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "terminal",
                            "arguments": json.dumps({"command": "python test.py"})
                        }
                    }]
                }
            }]
        }
        
        critic_response_2 = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_3",
                        "type": "function",
                        "function": {
                            "name": "critic",
                            "arguments": json.dumps({
                                "world_state": {"constraints": {}},
                                "content": "revised with terminal output"
                            })
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final response")
        
        mock_llm_client.chat.side_effect = [
            critic_response_1,
            terminal_response,
            critic_response_2,
            final_response
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            critic_response_1["choices"][0]["message"]["tool_calls"],
            terminal_response["choices"][0]["message"]["tool_calls"],
            critic_response_2["choices"][0]["message"]["tool_calls"],
            []
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            None, None, None, "Final response"
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        response = session.send("Test message")
        
        # Should have called critic twice and terminal once
        assert critic_tool.execute.call_count == 2
        assert terminal_tool.execute_called
        
        # Final response should be returned
        assert response == "Final response"
    
    def test_multiple_tool_usage_before_critic(self, mock_llm_client: Mock):
        """
        Test that multiple tools can be used before calling critic again.
        
        Rationale: Ensures LLM can use multiple tools to gather comprehensive information.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(side_effect=[
            {"accepted": False, "feedback": "Rejected", "violations": []},
            {"accepted": True, "feedback": "Accepted", "violations": []}
        ])
        terminal_tool = MockTerminalTool()
        registry.register_tool(critic_tool)
        registry.register_tool(terminal_tool)
        
        # Flow: critic rejects -> terminal -> terminal again -> critic accepts
        critic_response_1 = {
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
        
        terminal_response_1 = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "terminal",
                            "arguments": json.dumps({"command": "python test1.py"})
                        }
                    }]
                }
            }]
        }
        
        terminal_response_2 = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_3",
                        "type": "function",
                        "function": {
                            "name": "terminal",
                            "arguments": json.dumps({"command": "python test2.py"})
                        }
                    }]
                }
            }]
        }
        
        critic_response_2 = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_4",
                        "type": "function",
                        "function": {
                            "name": "critic",
                            "arguments": json.dumps({
                                "world_state": {"constraints": {}},
                                "content": "revised"
                            })
                        }
                    }]
                }
            }]
        }
        
        final_response = build_llm_response(content="Final response")
        
        mock_llm_client.chat.side_effect = [
            critic_response_1,
            terminal_response_1,
            terminal_response_2,
            critic_response_2,
            final_response
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            critic_response_1["choices"][0]["message"]["tool_calls"],
            terminal_response_1["choices"][0]["message"]["tool_calls"],
            terminal_response_2["choices"][0]["message"]["tool_calls"],
            critic_response_2["choices"][0]["message"]["tool_calls"],
            []
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            None, None, None, None, "Final response"
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        response = session.send("Test message")
        
        # Should have called terminal multiple times
        assert terminal_tool.execute_call_count == 2
        # Should have called critic twice
        assert critic_tool.execute.call_count == 2
        # Final response should be returned
        assert response == "Final response"
    
    def test_enforcement_message_less_prescriptive(self, mock_llm_client: Mock):
        """
        Test that system message allows tool usage.
        
        Rationale: Ensures system message doesn't prevent tool usage.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Rejected",
            "violations": []
        })
        registry.register_tool(critic_tool)
        
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
        
        final_response_attempt = build_llm_response(content="Final response")
        
        mock_llm_client.chat.side_effect = [critic_response, final_response_attempt]
        mock_llm_client.extract_tool_calls.side_effect = [
            critic_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final response"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        session.send("Test message")
        
        # Check that system message allows tool usage
        system_messages = [m for m in session.messages if m.get("role") == "system"]
        enforcement_message = next(
            (m for m in system_messages if "critic" in m.get("content", "").lower() and "reject" in m.get("content", "").lower()),
            None
        )
        
        assert enforcement_message is not None
        # Message should mention that tools can be used
        content = enforcement_message.get("content", "")
        assert "tools" in content.lower() or "terminal" in content.lower() or "may use" in content.lower()

