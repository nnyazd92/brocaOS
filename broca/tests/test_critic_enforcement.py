"""
Tests for critic iteration enforcement.

Tests that the system enforces iteration with the critic tool until acceptance,
preventing the LLM from providing final responses when the critic has rejected.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
import json
import logging

from broca.repl.session import ConversationSession
from broca.tools.registry import ToolRegistry
from broca.tests.utils import build_llm_response


class MockCriticTool:
    """Mock critic tool for testing enforcement."""
    
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
        # Return result based on test scenario
        # Tests will override this
        return {"accepted": True, "feedback": "Accepted", "violations": []}
    
    def format_result(self, result: dict) -> str:
        if result.get("accepted", False):
            return f"ACCEPTED: {result.get('feedback', '')}"
        else:
            return f"REJECTED: {result.get('feedback', '')}"


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


class TestCriticEnforcement:
    """Test critic iteration enforcement."""
    
    def test_pending_critic_rejection_detected(self, mock_llm_client: Mock):
        """
        Test that pending critic rejections are detected.
        
        Rationale: Ensures the system can identify when critic has rejected.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Rejected",
            "violations": [{"constraint": "test", "description": "test violation"}]
        })
        registry.register_tool(critic_tool)
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        # Simulate a critic rejection in messages
        session.messages.append({
            "role": "tool",
            "name": "critic",
            "content": "REJECTED: Rejected",
            "_raw_result": {"accepted": False, "feedback": "Rejected", "violations": []}
        })
        
        # Check that rejection is detected
        assert session._has_pending_critic_rejection() is True
    
    def test_pending_critic_acceptance_detected(self, mock_llm_client: Mock):
        """
        Test that critic acceptance is detected (no pending rejection).
        
        Rationale: Ensures the system recognizes when critic has accepted.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        registry.register_tool(critic_tool)
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        # Simulate a critic acceptance in messages
        session.messages.append({
            "role": "tool",
            "name": "critic",
            "content": "ACCEPTED: Accepted",
            "_raw_result": {"accepted": True, "feedback": "Accepted", "violations": []}
        })
        
        # Check that no rejection is pending
        assert session._has_pending_critic_rejection() is False
    
    def test_final_response_blocked_on_rejection(self, mock_llm_client: Mock):
        """
        Test that final responses are blocked when critic has rejected.
        
        Rationale: Ensures LLM cannot provide final response after rejection.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Rejected",
            "violations": []
        })
        registry.register_tool(critic_tool)
        
        # First response: critic call
        tool_call_response = {
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
        
        # Second response: LLM tries to give final response (should be blocked)
        final_response_attempt = build_llm_response(content="Final response")
        
        # Third response: LLM calls critic again (after being forced)
        tool_call_response_2 = {
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
                                "content": "revised test"
                            })
                        }
                    }]
                }
            }]
        }
        
        # Fourth response: Critic accepts, final response allowed
        final_response_allowed = build_llm_response(content="Final response after acceptance")
        
        # Flow:
        # 1. First critic call (rejection)
        # 2. System message injected, LLM tries final response (blocked)
        # 3. System message injected, LLM calls critic again (accepts this time)
        # 4. Final response allowed
        
        # Make critic accept on second call
        critic_tool.execute = Mock(side_effect=[
            {"accepted": False, "feedback": "Rejected", "violations": []},  # First call
            {"accepted": True, "feedback": "Accepted", "violations": []}   # Second call
        ])
        
        mock_llm_client.chat.side_effect = [
            tool_call_response,           # 1. First critic call
            final_response_attempt,       # 2. Tries final (blocked, system msg injected)
            tool_call_response_2,         # 3. Calls critic again (system msg, accepts)
            final_response_allowed        # 4. Final response allowed
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],  # 1
            [],  # 2. No tool calls (trying to give final response)
            tool_call_response_2["choices"][0]["message"]["tool_calls"],  # 3
            []  # 4. No tool calls (final response after acceptance)
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            None,  # 1
            "Final response",  # 2. This should be blocked
            None,  # 3
            "Final response after acceptance"  # 4. This should be allowed
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            response = session.send("Test message")
        
        # Should have blocked the first final response attempt
        assert logs.has_event("critic_rejection_blocked_final_response")
        
        # Final response should be the one after acceptance
        assert "after acceptance" in response or response == "Final response after acceptance"
        
        # Should have multiple LLM calls (enforcement forced iteration)
        assert mock_llm_client.chat.call_count >= 3
    
    def test_iteration_forced_on_rejection(self, mock_llm_client: Mock):
        """
        Test that iteration is forced when LLM tries final response after critic rejects.
        
        Rationale: Ensures system injects message to force iteration when final response attempted.
        Note: With relaxed enforcement, iteration is only forced when final response is attempted,
        not immediately after critic rejection (allowing tool usage first).
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(side_effect=[
            {"accepted": False, "feedback": "Rejected", "violations": []},  # First call
            {"accepted": True, "feedback": "Accepted", "violations": []}   # Second call
        ])
        registry.register_tool(critic_tool)
        
        tool_call_response = {
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
        
        # After blocking, LLM calls critic again
        tool_call_response_2 = {
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
        
        final_response_allowed = build_llm_response(content="Final after acceptance")
        
        mock_llm_client.chat.side_effect = [
            tool_call_response,
            final_response_attempt,  # Should be blocked
            tool_call_response_2,
            final_response_allowed
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            [],  # No tool calls (trying final response)
            tool_call_response_2["choices"][0]["message"]["tool_calls"],
            []
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            None, "Final response", None, "Final after acceptance"
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Test message")
        
        # Should have blocked final response (not forced immediately after tool calls)
        assert logs.has_event("critic_rejection_blocked_final_response")
        
        # Check that system message was injected (when final response attempted)
        system_messages = [m for m in session.messages if m.get("role") == "system"]
        assert any("critic" in msg.get("content", "").lower() and "reject" in msg.get("content", "").lower() 
                   for msg in system_messages)
    
    def test_final_response_allowed_on_acceptance(self, mock_llm_client: Mock):
        """
        Test that final responses are allowed when critic accepts.
        
        Rationale: Ensures normal flow works when critic accepts.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": True,
            "feedback": "Accepted",
            "violations": []
        })
        registry.register_tool(critic_tool)
        
        tool_call_response = {
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
        
        final_response = build_llm_response(content="Final response")
        
        mock_llm_client.chat.side_effect = [tool_call_response, final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        mock_llm_client.extract_assistant_content.side_effect = [None, "Final response"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        response = session.send("Test message")
        
        # Final response should be allowed
        assert response == "Final response"
        
        # Should not have blocked final response
        # (We can't easily check this without log capture, but response being returned is the test)
    
    def test_multiple_critic_iterations(self, mock_llm_client: Mock):
        """
        Test that multiple critic iterations work correctly.
        
        Rationale: Ensures enforcement works across multiple rejections.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        
        # First two calls reject, third accepts
        critic_tool.execute = Mock(side_effect=[
            {"accepted": False, "feedback": "Rejected 1", "violations": []},
            {"accepted": False, "feedback": "Rejected 2", "violations": []},
            {"accepted": True, "feedback": "Accepted", "violations": []}
        ])
        registry.register_tool(critic_tool)
        
        tool_call_responses = [
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": f"call_{i}",
                            "type": "function",
                            "function": {
                                "name": "critic",
                                "arguments": json.dumps({
                                    "world_state": {"constraints": {}},
                                    "content": f"test {i}"
                                })
                            }
                        }]
                    }
                }]
            }
            for i in range(3)
        ]
        
        final_response = build_llm_response(content="Final response")
        
        mock_llm_client.chat.side_effect = tool_call_responses + [final_response]
        mock_llm_client.extract_tool_calls.side_effect = [
            resp["choices"][0]["message"]["tool_calls"] for resp in tool_call_responses
        ] + [[]]
        mock_llm_client.extract_assistant_content.side_effect = [None] * 3 + ["Final response"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        response = session.send("Test message")
        
        # Should have called critic multiple times
        assert critic_tool.execute.call_count == 3
        
        # Final response should be returned after acceptance
        assert response == "Final response"
    
    def test_critic_enforcement_logging(self, mock_llm_client: Mock):
        """
        Test that enforcement actions are properly logged.
        
        Rationale: Ensures all enforcement actions are logged for debugging.
        Note: With relaxed enforcement, logging happens when final response is blocked,
        not immediately after critic rejection.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(side_effect=[
            {"accepted": False, "feedback": "Rejected", "violations": []},  # First call
            {"accepted": True, "feedback": "Accepted", "violations": []}   # Second call
        ])
        registry.register_tool(critic_tool)
        
        tool_call_response = {
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
        
        tool_call_response_2 = {
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
        
        final_response_allowed = build_llm_response(content="Final after acceptance")
        
        mock_llm_client.chat.side_effect = [
            tool_call_response,
            final_response_attempt,  # Should be blocked
            tool_call_response_2,
            final_response_allowed
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            tool_call_response["choices"][0]["message"]["tool_calls"],
            [],  # No tool calls (trying final response)
            tool_call_response_2["choices"][0]["message"]["tool_calls"],
            []
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            None, "Final response", None, "Final after acceptance"
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        with LogCapture("broca.repl.session") as logs:
            session.send("Test message")
        
        # Should have logged when final response was blocked
        assert logs.has_event("critic_rejection_blocked_final_response")
    
    def test_no_critic_tool_no_enforcement(self, mock_llm_client: Mock):
        """
        Test that enforcement doesn't apply when critic tool is not available.
        
        Rationale: Ensures backward compatibility when critic is not registered.
        """
        # No critic tool registered
        session = ConversationSession(llm=mock_llm_client, tool_registry=None)
        
        mock_llm_client.chat.return_value = build_llm_response(content="Response")
        mock_llm_client.extract_tool_calls.return_value = []
        mock_llm_client.extract_assistant_content.return_value = "Response"
        
        response = session.send("Test message")
        
        # Should work normally without enforcement
        assert response == "Response"
        
        # Should not have pending rejection (no critic tool)
        assert session._has_pending_critic_rejection() is False

