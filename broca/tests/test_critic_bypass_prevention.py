"""
Tests to prevent LLM from bypassing critic approval.

Tests that ensure the LLM cannot provide a final response without critic approval,
even in edge cases.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest
import json

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


class TestCriticBypassPrevention:
    """Test that LLM cannot bypass critic approval."""
    
    def test_final_response_blocked_without_critic_call(self, mock_llm_client: Mock):
        """
        Test that final response is blocked if critic was never called.
        
        Rationale: If critic tool is available, LLM must call it before final response.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        registry.register_tool(critic_tool)
        
        # LLM tries to give final response without calling critic
        final_response = build_llm_response(content="Final response without critic")
        
        mock_llm_client.chat.side_effect = [final_response]
        mock_llm_client.extract_tool_calls.side_effect = [[]]
        mock_llm_client.extract_assistant_content.side_effect = ["Final response without critic"]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        # This should be blocked - critic must be called first
        # Since critic was never called, we need to check if enforcement happens
        # Actually, wait - if critic was never called, there's no rejection pending
        # So the current logic might allow it...
        
        # Let me think: if critic tool exists but was never called, should we block?
        # The user's requirement is: "cannot make final response without critic approval"
        # This implies critic MUST be called and MUST accept
        
        # So we need to track: has critic been called in this turn? Has it accepted?
        # The response should be blocked - system should force critic call
        # After blocking, provide a mock response where critic is called
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
        
        # Make critic accept
        critic_tool.execute = Mock(return_value={
            "accepted": True,
            "feedback": "Accepted",
            "violations": []
        })
        
        final_response_after_critic = build_llm_response(content="Final after critic")
        
        mock_llm_client.chat.side_effect = [
            final_response,  # First attempt (should be blocked)
            critic_response,  # After blocking, LLM calls critic
            final_response_after_critic  # Then final response
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            [],  # No tool calls (trying final response)
            critic_response["choices"][0]["message"]["tool_calls"],
            []
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            "Final response without critic",
            None,
            "Final after critic"
        ]
        
        response = session.send("Test message")
        
        # Critic should have been called
        assert critic_tool.execute.called
        
        # Final response should only be returned after critic accepts
        assert "after critic" in response or response == "Final after critic"
    
    def test_final_response_blocked_after_rejection_without_retry(self, mock_llm_client: Mock):
        """
        Test that final response is blocked after critic rejection if critic isn't called again.
        
        Rationale: After rejection, LLM must call critic again and get acceptance.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Rejected",
            "violations": []
        })
        registry.register_tool(critic_tool)
        
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
        
        # Second: LLM tries final response without calling critic again (should be blocked)
        final_response_attempt = build_llm_response(content="Final response attempt")
        
        # After blocking, LLM should call critic again
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
        
        # Critic accepts on second call
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
            None, "Final response attempt", None, "Final after acceptance"
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        
        response = session.send("Test message")
        
        # Should have called critic twice (reject then accept)
        assert critic_tool.execute.call_count == 2
        
        # Final response should only be returned after acceptance
        assert "after acceptance" in response or response == "Final after acceptance"
    
    def test_final_response_blocked_if_critic_never_accepts(self, mock_llm_client: Mock):
        """
        Test that final response is blocked if critic never accepts.
        
        Rationale: LLM cannot provide final response if critic keeps rejecting.
        """
        registry = ToolRegistry()
        critic_tool = MockCriticTool()
        critic_tool.execute = Mock(return_value={
            "accepted": False,
            "feedback": "Rejected",
            "violations": []
        })
        registry.register_tool(critic_tool)
        
        # Critic always rejects
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
        
        # After blocking, LLM calls critic again (still rejects)
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
        
        # Final response attempt again (should still be blocked)
        final_response_attempt_2 = build_llm_response(content="Final response 2")
        
        mock_llm_client.chat.side_effect = [
            critic_response,
            final_response_attempt,  # Blocked
            critic_response_2,
            final_response_attempt_2  # Still blocked
        ]
        
        mock_llm_client.extract_tool_calls.side_effect = [
            critic_response["choices"][0]["message"]["tool_calls"],
            [],
            critic_response_2["choices"][0]["message"]["tool_calls"],
            []
        ]
        
        mock_llm_client.extract_assistant_content.side_effect = [
            None, "Final response", None, "Final response 2"
        ]
        
        session = ConversationSession(llm=mock_llm_client, tool_registry=registry)
        session._max_tool_iterations = 10  # Set max iterations for this test
        
        # Should hit max iterations (critic never accepts, so enforcement keeps blocking)
        # After max iterations, it will return an error message
        response = session.send("Test message")
        
        # Critic should have been called multiple times
        assert critic_tool.execute.call_count >= 2
        
        # Final response should NOT be returned (critic never accepted)
        # The response should be an error about max iterations or similar
        # OR it should still be blocked
        # Actually, if we hit max iterations, the session will return a warning message
        # But the key is: critic never accepted, so enforcement should prevent final response
        # Let's check that the response is not the final response content
        assert "Final response" not in response or "max" in response.lower() or "iteration" in response.lower()

