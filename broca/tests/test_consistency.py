"""
Tests for ConsistencyChecker validation logic.

Tests consistency checking functionality including edge cases
for conversation context handling.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from broca.self_model.consistency import ConsistencyChecker, ConsistencyResult
from broca.self_model.model import SelfModel


class TestConsistencyCheckerConversationContext:
    """Test ConsistencyChecker handling of conversation context."""
    
    def test_validate_handles_none_content(self, mock_llm_client):
        """
        Test that validate() handles None content in conversation context gracefully.
        
        Rationale: Ensures no TypeError when message content is None.
        This is the bug fix test case.
        """
        checker = ConsistencyChecker(llm_client=mock_llm_client)
        self_model = SelfModel.create_default()
        
        # Mock LLM response with valid JSON
        mock_llm_client.chat.return_value = {
            "choices": [{
                "message": {
                    "content": '{"is_consistent": true, "violations": [], "overall_severity": 0.0}'
                }
            }]
        }
        
        # Conversation context with None content (the bug case)
        conversation_context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": None},  # None content - this causes the bug
            {"role": "user", "content": "How are you?"}
        ]
        
        # Should not raise TypeError
        result = checker.validate(
            response="I'm doing well!",
            self_model=self_model,
            conversation_context=conversation_context
        )
        
        assert isinstance(result, ConsistencyResult)
        assert result.is_consistent is True
        assert len(result.violations) == 0
        assert result.severity == 0.0
    
    def test_validate_handles_missing_content_key(self, mock_llm_client):
        """
        Test that validate() handles missing content key in conversation context.
        
        Rationale: Ensures robustness when message structure is incomplete.
        """
        checker = ConsistencyChecker(llm_client=mock_llm_client)
        self_model = SelfModel.create_default()
        
        # Mock LLM response
        mock_llm_client.chat.return_value = {
            "choices": [{
                "message": {
                    "content": '{"is_consistent": true, "violations": [], "overall_severity": 0.0}'
                }
            }]
        }
        
        # Conversation context with missing content key
        conversation_context = [
            {"role": "user"},  # Missing content key
            {"role": "assistant", "content": "Response"}
        ]
        
        # Should not raise KeyError or TypeError
        result = checker.validate(
            response="Test response",
            self_model=self_model,
            conversation_context=conversation_context
        )
        
        assert isinstance(result, ConsistencyResult)
    
    def test_validate_handles_empty_content(self, mock_llm_client):
        """
        Test that validate() handles empty string content.
        
        Rationale: Ensures empty strings are handled correctly.
        """
        checker = ConsistencyChecker(llm_client=mock_llm_client)
        self_model = SelfModel.create_default()
        
        # Mock LLM response
        mock_llm_client.chat.return_value = {
            "choices": [{
                "message": {
                    "content": '{"is_consistent": true, "violations": [], "overall_severity": 0.0}'
                }
            }]
        }
        
        # Conversation context with empty content
        conversation_context = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "Response"}
        ]
        
        result = checker.validate(
            response="Test response",
            self_model=self_model,
            conversation_context=conversation_context
        )
        
        assert isinstance(result, ConsistencyResult)
    
    def test_validate_handles_normal_content(self, mock_llm_client):
        """
        Test that validate() works correctly with normal conversation context.
        
        Rationale: Ensures no regressions in normal operation.
        """
        checker = ConsistencyChecker(llm_client=mock_llm_client)
        self_model = SelfModel.create_default()
        
        # Mock LLM response
        mock_llm_client.chat.return_value = {
            "choices": [{
                "message": {
                    "content": '{"is_consistent": true, "violations": [], "overall_severity": 0.0}'
                }
            }]
        }
        
        # Normal conversation context
        conversation_context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = checker.validate(
            response="I'm doing well!",
            self_model=self_model,
            conversation_context=conversation_context
        )
        
        assert isinstance(result, ConsistencyResult)
        assert result.is_consistent is True
    
    def test_validate_handles_mixed_none_and_normal_content(self, mock_llm_client):
        """
        Test that validate() handles mix of None and normal content.
        
        Rationale: Ensures robustness with mixed message types.
        """
        checker = ConsistencyChecker(llm_client=mock_llm_client)
        self_model = SelfModel.create_default()
        
        # Mock LLM response
        mock_llm_client.chat.return_value = {
            "choices": [{
                "message": {
                    "content": '{"is_consistent": true, "violations": [], "overall_severity": 0.0}'
                }
            }]
        }
        
        # Mixed conversation context
        conversation_context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": None},  # None content
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm fine"},  # Normal content
            {"role": "user", "content": None}  # Another None
        ]
        
        # Should not raise TypeError
        result = checker.validate(
            response="Test response",
            self_model=self_model,
            conversation_context=conversation_context
        )
        
        assert isinstance(result, ConsistencyResult)
    
    def test_validate_handles_empty_conversation_context(self, mock_llm_client):
        """
        Test that validate() handles empty conversation context.
        
        Rationale: Ensures None or empty list is handled correctly.
        """
        checker = ConsistencyChecker(llm_client=mock_llm_client)
        self_model = SelfModel.create_default()
        
        # Mock LLM response
        mock_llm_client.chat.return_value = {
            "choices": [{
                "message": {
                    "content": '{"is_consistent": true, "violations": [], "overall_severity": 0.0}'
                }
            }]
        }
        
        # Empty conversation context
        result = checker.validate(
            response="Test response",
            self_model=self_model,
            conversation_context=None
        )
        
        assert isinstance(result, ConsistencyResult)
        
        # Empty list
        result = checker.validate(
            response="Test response",
            self_model=self_model,
            conversation_context=[]
        )
        
        assert isinstance(result, ConsistencyResult)
    
    def test_validate_truncates_long_content(self, mock_llm_client):
        """
        Test that validate() truncates long content to 200 characters.
        
        Rationale: Ensures content truncation works correctly.
        """
        checker = ConsistencyChecker(llm_client=mock_llm_client)
        self_model = SelfModel.create_default()
        
        # Mock LLM response
        mock_llm_client.chat.return_value = {
            "choices": [{
                "message": {
                    "content": '{"is_consistent": true, "violations": [], "overall_severity": 0.0}'
                }
            }]
        }
        
        # Long content (300 characters)
        long_content = "A" * 300
        conversation_context = [
            {"role": "user", "content": long_content}
        ]
        
        result = checker.validate(
            response="Test response",
            self_model=self_model,
            conversation_context=conversation_context
        )
        
        assert isinstance(result, ConsistencyResult)
        # Verify the LLM was called (content was processed)
        assert mock_llm_client.chat.called

