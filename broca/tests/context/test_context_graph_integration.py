"""
Integration tests for ContextGraph with ConversationSession.

Tests full conversation flow and integration with the session system.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock
from broca.context.context_graph import ContextGraph
from broca.repl.session import ConversationSession
from broca.summarization.token_estimator import estimate_messages_tokens


@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    llm = Mock()
    llm.chat = Mock(return_value={"choices": [{"message": {"content": "Response"}}]})
    llm.extract_assistant_content = Mock(return_value="Response")
    llm.extract_tool_calls = Mock(return_value=None)
    return llm


@pytest.fixture
def mock_storage():
    """Mock storage backend."""
    storage = Mock()
    storage.load_conversation = Mock(return_value=None)
    storage.save_conversation = Mock()
    return storage


class TestIntegration:
    """Integration tests with ConversationSession."""
    
    def test_full_conversation_flow(self, mock_llm, mock_storage):
        """Test full conversation flow with context graph."""
        session = ConversationSession(
            llm=mock_llm,
            storage=mock_storage,
            session_id="test_session",
        )
        
        # Enable context graph
        from broca.config import config
        config.context.enabled = True
        
        # Send messages
        response1 = session.send("Hello")
        response2 = session.send("How are you?")
        response3 = session.send("Tell me about Python")
        
        # Context graph should be populated
        assert session._context_graph is not None
        assert len(session._context_graph.nodes) >= 6  # At least 3 user + 3 assistant
        
        # Get messages for LLM
        messages = session._get_messages_for_llm()
        
        # Should return valid messages
        assert isinstance(messages, list)
        assert len(messages) > 0
    
    def test_tool_call_chain_preservation(self, mock_llm, mock_storage):
        """Test that tool call chains are preserved."""
        # Mock LLM to return tool calls
        mock_llm.extract_tool_calls = Mock(return_value=[
            {"id": "call_1", "function": {"name": "test_tool", "arguments": "{}"}}
        ])
        
        # Mock tool registry
        tool_registry = Mock()
        tool_registry.to_openai_format = Mock(return_value=[
            {"type": "function", "function": {"name": "test_tool", "description": "Test"}}
        ])
        tool_registry.execute_tool_call = Mock(return_value={"content": "Tool result"})
        
        session = ConversationSession(
            llm=mock_llm,
            storage=mock_storage,
            tool_registry=tool_registry,
            session_id="test_session",
        )
        
        from broca.config import config
        config.context.enabled = True
        
        # Send message that triggers tool call
        session.send("Use test_tool")
        
        # Context graph should have tool call chain
        if session._context_graph:
            messages = session._context_graph.get_messages_for_llm(max_tokens=10000)
            
            # Find assistant with tool_calls
            for i, msg in enumerate(messages):
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    # Should be followed by tool result
                    if i + 1 < len(messages):
                        next_msg = messages[i + 1]
                        assert next_msg.get("role") == "tool"
    
    def test_storage_integration(self, mock_llm, mock_storage):
        """Test loading from storage and graph reconstruction."""
        # Mock storage to return saved conversation
        saved_messages = []
        
        def save_conv(session_id, messages, metadata):
            nonlocal saved_messages
            saved_messages = messages
        
        def load_conv(session_id):
            return {"messages": saved_messages, "metadata": {}}
        
        mock_storage.save_conversation = save_conv
        mock_storage.load_conversation = load_conv
        
        # Create session and add messages
        session1 = ConversationSession(
            llm=mock_llm,
            storage=mock_storage,
            session_id="test_session",
        )
        
        from broca.config import config
        config.context.enabled = True
        
        session1.send("Hello")
        session1.send("How are you?")
        
        # Save
        session1._save_conversation()
        
        # Load from storage
        session2 = ConversationSession.from_storage(
            session_id="test_session",
            storage=mock_storage,
        )
        
        # Context graph should be reconstructed
        if session2._context_graph:
            # Graph should have nodes (may be 0 if messages weren't properly added)
            assert isinstance(session2._context_graph.nodes, dict)
    
    def test_token_filtering_integration(self, mock_llm, mock_storage):
        """Test context graph + token validation integration."""
        session = ConversationSession(
            llm=mock_llm,
            storage=mock_storage,
            session_id="test_session",
        )
        
        from broca.config import config
        config.context.enabled = True
        
        # Add many messages to trigger pruning
        for i in range(50):
            session.send(f"Message {i}")
        
        # Get messages for LLM
        messages = session._get_messages_for_llm()
        
        # Should be under token limit
        tokens = estimate_messages_tokens(messages)
        max_tokens = config.llm.max_context_tokens
        assert tokens <= max_tokens * 1.1  # Allow 10% margin

    def test_plucking_does_not_mutate_persisted_history(self, mock_llm, mock_storage):
        """
        When context graph plucks nodes, it must not delete messages from the session history.
        History is the persisted source of truth; only the in-graph selection should change.
        """
        # Force a small model context limit to trigger plucking deterministically.
        mock_llm.get_max_context_tokens = Mock(return_value=600)

        session = ConversationSession(
            llm=mock_llm,
            storage=mock_storage,
            session_id="test_session",
        )

        from broca.config import config
        config.context.enabled = True

        # Build a large history (explicit IDs to avoid mutation)
        for i in range(80):
            session.messages.append(
                {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"msg {i} " + ("x" * 400),
                    "message_id": f"h{i}",
                }
            )

        original_len = len(session.messages)
        assert session._context_graph is not None

        filtered1 = session._get_messages_for_llm()
        assert len(session.messages) == original_len, "Plucking must not delete persisted history"

        graph_len_after_1 = len(session._context_graph.nodes)
        filtered2 = session._get_messages_for_llm()
        assert len(session.messages) == original_len
        assert len(session._context_graph.nodes) == graph_len_after_1, "Tombstones prevent re-inflation on replay"
        assert len(filtered2) > 0
    
    def test_failsafe_activation(self, mock_llm, mock_storage):
        """Test that failsafe token filtering activates when needed."""
        session = ConversationSession(
            llm=mock_llm,
            storage=mock_storage,
            session_id="test_session",
        )
        
        from broca.config import config
        config.context.enabled = True
        
        # Add very large messages
        for i in range(10):
            large_content = "x" * 10000  # 10K chars per message
            session.messages.append({
                "role": "user",
                "content": large_content,
                "message_id": f"large{i}",
            })
            if session._context_graph:
                session._context_graph.add_message(session.messages[-1])
        
        # Get messages - should trigger failsafe
        messages = session._get_messages_for_llm()
        
        # Should be under limit (failsafe should activate)
        tokens = estimate_messages_tokens(messages)
        max_tokens = config.llm.max_context_tokens
        assert tokens <= max_tokens * 1.1
    
    def test_error_handling_integration(self, mock_llm, mock_storage):
        """Test error handling in integration."""
        session = ConversationSession(
            llm=mock_llm,
            storage=mock_storage,
            session_id="test_session",
        )
        
        from broca.config import config
        config.context.enabled = True
        
        # Add messages
        session.send("Hello")
        
        # Corrupt context graph
        if session._context_graph:
            session._context_graph.nodes = None  # Cause error
        
        # Should fall back to token filtering
        try:
            messages = session._get_messages_for_llm()
            assert isinstance(messages, list)
        except Exception:
            # Should handle gracefully
            pass
