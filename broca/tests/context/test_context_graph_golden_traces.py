"""
Golden trace replay tests for ContextGraph.

Tests with captured real conversation traces to ensure no regressions.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from broca.context.context_graph import ContextGraph
from broca.summarization.token_estimator import estimate_messages_tokens


@pytest.fixture
def golden_traces_dir():
    """Path to golden traces directory."""
    return Path(__file__).parent.parent / "fixtures" / "golden_traces" / "context"


def load_golden_trace(trace_name: str, golden_traces_dir: Path) -> dict:
    """Load a golden trace from file."""
    trace_path = golden_traces_dir / f"{trace_name}.json"
    if not trace_path.exists():
        pytest.skip(f"Golden trace {trace_name} not found at {trace_path}")
    
    with open(trace_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_typical_conversation_trace():
    """Create a typical conversation golden trace."""
    return {
        "messages": [
            {"role": "user", "content": "Hello, can you help me?", "message_id": "msg1"},
            {"role": "assistant", "content": "Of course! How can I assist you?", "message_id": "msg2"},
            {"role": "user", "content": "I need to write a Python function", "message_id": "msg3"},
            {"role": "assistant", "content": "I'd be happy to help. What should the function do?", "message_id": "msg4"},
            {"role": "user", "content": "It should calculate fibonacci numbers", "message_id": "msg5"},
        ],
        "expected_pruned": ["msg1", "msg2", "msg3", "msg4", "msg5"],
        "expected_tokens": 150,
        "test_scenarios": ["typical", "short"]
    }


def create_tool_heavy_conversation_trace():
    """Create a tool-heavy conversation golden trace."""
    return {
        "messages": [
            {"role": "user", "content": "Search for Python tutorials", "message_id": "msg1"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_1", "function": {"name": "web_search", "arguments": '{"query": "Python tutorials"}'}}],
                "message_id": "msg2"
            },
            {"role": "tool", "content": "Found 10 results...", "tool_call_id": "call_1", "name": "web_search", "message_id": "msg3"},
            {"role": "assistant", "content": "Here are some Python tutorials...", "message_id": "msg4"},
            {"role": "user", "content": "Now search for advanced topics", "message_id": "msg5"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_2", "function": {"name": "web_search", "arguments": '{"query": "advanced Python"}'}}],
                "message_id": "msg6"
            },
            {"role": "tool", "content": "Found 8 results...", "tool_call_id": "call_2", "name": "web_search", "message_id": "msg7"},
            {"role": "assistant", "content": "Here are advanced topics...", "message_id": "msg8"},
        ],
        "expected_pruned": ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8"],
        "expected_tokens": 300,
        "test_scenarios": ["tool_heavy", "multiple_chains"]
    }


def create_branching_conversation_trace():
    """Create a branching conversation golden trace."""
    return {
        "messages": [
            {"role": "user", "content": "Tell me about Python", "message_id": "msg1"},
            {"role": "assistant", "content": "Python is a programming language...", "message_id": "msg2"},
            {"role": "user", "content": "What about JavaScript?", "message_id": "msg3"},  # Topic switch
            {"role": "assistant", "content": "JavaScript is used for web development...", "message_id": "msg4"},
            {"role": "user", "content": "Back to Python - show me syntax", "message_id": "msg5"},  # Back to original topic
            {"role": "assistant", "content": "Here's Python syntax...", "message_id": "msg6"},
        ],
        "expected_pruned": ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6"],
        "expected_tokens": 250,
        "test_scenarios": ["branching", "topic_switch"]
    }


class TestGoldenTraces:
    """Golden trace replay tests."""
    
    def test_golden_trace_typical_conversation(self, golden_traces_dir):
        """Test with typical conversation golden trace."""
        # Use inline trace if file doesn't exist
        try:
            golden_trace = load_golden_trace("typical_conversation", golden_traces_dir)
        except:
            golden_trace = create_typical_conversation_trace()
        
        graph = ContextGraph(min_turns_retained=3)
        
        # Build graph from messages
        for i, msg in enumerate(golden_trace["messages"]):
            parent_id = golden_trace["messages"][i-1]["message_id"] if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Test pruning
        max_tokens = golden_trace.get("expected_tokens", 1000) * 2
        to_keep, tokens = graph.prune_to_fit(max_tokens)
        
        # Should preserve main thread
        main_thread = graph.identify_main_thread()
        for msg_id in main_thread:
            assert msg_id in to_keep
        
        # Should be under token limit
        assert tokens <= max_tokens * 1.1
    
    def test_golden_trace_tool_heavy_conversation(self, golden_traces_dir):
        """Test with tool-heavy conversation golden trace."""
        try:
            golden_trace = load_golden_trace("tool_heavy_conversation", golden_traces_dir)
        except:
            golden_trace = create_tool_heavy_conversation_trace()
        
        graph = ContextGraph(min_turns_retained=3)
        
        # Build graph from messages
        for i, msg in enumerate(golden_trace["messages"]):
            parent_id = golden_trace["messages"][i-1]["message_id"] if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Test that tool call chains are preserved
        max_tokens = golden_trace.get("expected_tokens", 1000) * 2
        messages = graph.get_messages_for_llm(max_tokens)
        
        # Check that tool call chains are intact
        # Assistant with tool_calls should be followed by tool results
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                # Next message should be tool result
                if i + 1 < len(messages):
                    next_msg = messages[i + 1]
                    assert next_msg.get("role") == "tool"
                    assert next_msg.get("tool_call_id") in [
                        tc.get("id") for tc in msg.get("tool_calls", [])
                    ]
    
    def test_golden_trace_branching_conversation(self, golden_traces_dir):
        """Test with branching conversation golden trace."""
        try:
            golden_trace = load_golden_trace("branching_conversation", golden_traces_dir)
        except:
            golden_trace = create_branching_conversation_trace()
        
        graph = ContextGraph(min_turns_retained=2)
        
        # Build graph from messages
        for i, msg in enumerate(golden_trace["messages"]):
            parent_id = golden_trace["messages"][i-1]["message_id"] if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Test main thread identification
        main_thread = graph.identify_main_thread()
        
        # Main thread should include the most recent messages
        assert len(main_thread) >= 2
        
        # Test pruning preserves main thread
        max_tokens = 1000
        to_keep, _ = graph.prune_to_fit(max_tokens)
        
        for msg_id in main_thread:
            assert msg_id in to_keep
    
    def test_golden_trace_large_tool_result(self, golden_traces_dir):
        """Test with very large tool result."""
        large_result = "x" * 50000  # 50K chars
        golden_trace = {
            "messages": [
                {"role": "user", "content": "Get me data", "message_id": "msg1"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{"id": "call_1", "function": {"name": "get_data"}}],
                    "message_id": "msg2"
                },
                {"role": "tool", "content": large_result, "tool_call_id": "call_1", "name": "get_data", "message_id": "msg3"},
                {"role": "assistant", "content": "Here's the data summary", "message_id": "msg4"},
            ],
            "expected_tokens": 15000,
            "test_scenarios": ["large_tool_result"]
        }
        
        graph = ContextGraph(min_turns_retained=2)
        
        for i, msg in enumerate(golden_trace["messages"]):
            parent_id = golden_trace["messages"][i-1]["message_id"] if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Should handle large tool results
        max_tokens = 20000
        to_keep, tokens = graph.prune_to_fit(max_tokens)
        
        # Should stay under limit
        assert tokens <= max_tokens * 1.1
    
    def test_golden_trace_many_small_messages(self, golden_traces_dir):
        """Test with many small messages."""
        golden_trace = {
            "messages": [
                {"role": "user", "content": f"Message {i}", "message_id": f"msg{i}"}
                for i in range(100)
            ],
            "expected_tokens": 500,
            "test_scenarios": ["many_small"]
        }
        
        graph = ContextGraph(min_turns_retained=5)
        
        for i, msg in enumerate(golden_trace["messages"]):
            parent_id = golden_trace["messages"][i-1]["message_id"] if i > 0 else None
            graph.add_message(msg, parent_id=parent_id)
        
        # Should handle many messages
        max_tokens = 1000
        to_keep, tokens = graph.prune_to_fit(max_tokens)
        
        # Should prune appropriately
        assert len(to_keep) <= len(graph.nodes)
        assert tokens <= max_tokens * 1.1

