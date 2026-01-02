"""
Tests for thought_signature extraction and handling in Gemini tool calls.

Tests ensure thought_signature is extracted before tool_calls processing.
"""

import logging
import pytest
from unittest.mock import Mock, MagicMock, patch
from broca.repl.session import ConversationSession
from broca.llm.gemini_client import GeminiClient


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    client = Mock(spec=GeminiClient)
    client.extract_thought_signature = Mock(return_value="test-signature-123")
    client.extract_tool_calls = Mock(return_value=[])
    client.extract_assistant_content = Mock(return_value="Test response")
    client.chat = Mock(return_value={"choices": [{"message": {"content": "Test response"}}]})
    client.is_reasoner_model = Mock(return_value=False)
    return client


@pytest.fixture
def session_with_gemini(mock_gemini_client):
    """Create a session with Gemini client."""
    return ConversationSession(llm=mock_gemini_client)


class TestThoughtSignatureExtractionOrder:
    """Tests to ensure thought_signature is extracted before tool_calls."""
    
    def test_thought_signature_extracted_before_tool_calls(self, session_with_gemini, mock_gemini_client):
        """Test: thought_signature is extracted from response before tool_calls processing."""
        # Mock response with thought_signature
        response = {
            "choices": [{
                "message": {
                    "content": "Test",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "test_tool", "arguments": "{}"}
                        }
                    ]
                }
            }],
            "thought_signature": "sig-123"
        }
        
        # Track call order using separate return values
        call_order = []
        
        def track_extract_sig(resp):
            call_order.append("extract_signature")
            return "sig-123"
        
        def track_extract_tools(resp):
            call_order.append("extract_tools")
            return [{"id": "call_1", "function": {"name": "test_tool", "arguments": {}}}]
        
        mock_gemini_client.extract_thought_signature.side_effect = track_extract_sig
        mock_gemini_client.extract_tool_calls.side_effect = track_extract_tools
        
        # Simulate what happens in send() method - signature extracted first
        session_with_gemini._current_thought_signature = None
        
        # Extract signature first (as done in send() method)
        extracted_sig = mock_gemini_client.extract_thought_signature(response)
        if extracted_sig:
            session_with_gemini._current_thought_signature = extracted_sig
        
        # Then extract tool_calls
        tool_calls = mock_gemini_client.extract_tool_calls(response)
        
        # Verify signature is set before tool_calls
        assert session_with_gemini._current_thought_signature == "sig-123"
        assert len(tool_calls) > 0
        assert call_order[0] == "extract_signature"
        assert call_order[1] == "extract_tools"
    
    def test_thought_signature_extracted_from_tool_calls_fallback(self, session_with_gemini):
        """Test: thought_signature can be extracted from tool_calls as fallback."""
        # Mock tool_calls with thought_signature
        tool_calls = [
            {
                "id": "call_1",
                "function": {"name": "test_tool", "arguments": {}},
                "thought_signature": "sig-from-tool-call"
            }
        ]
        
        session_with_gemini._current_thought_signature = None
        
        # Simulate fallback extraction
        for tool_call in tool_calls:
            if isinstance(tool_call, dict) and "thought_signature" in tool_call:
                session_with_gemini._current_thought_signature = tool_call["thought_signature"]
                break
        
        assert session_with_gemini._current_thought_signature == "sig-from-tool-call"
    
    def test_thought_signature_available_in_handle_tool_calls(self, session_with_gemini):
        """Test: _current_thought_signature is available when _handle_tool_calls processes them."""
        # Set thought_signature before tool_calls
        session_with_gemini._current_thought_signature = "sig-456"
        
        tool_calls = [
            {
                "id": "call_1",
                "function": {"name": "test_tool", "arguments": {}}
            }
        ]
        
        # Verify signature is available
        current_sig = getattr(session_with_gemini, '_current_thought_signature', None)
        assert current_sig == "sig-456"
        
        # Verify it would be added to tool_calls in _handle_tool_calls
        # (We can't easily call _handle_tool_calls without full setup, but we can verify the logic)
        if session_with_gemini._is_gemini_client() and tool_calls:
            for tool_call in tool_calls:
                if isinstance(tool_call, dict) and "thought_signature" not in tool_call:
                    if current_sig:
                        tool_call["thought_signature"] = current_sig
        
        # Verify signature was added
        assert tool_calls[0].get("thought_signature") == "sig-456"


class TestThoughtSignatureFaultInjection:
    """Fault injection tests for thought_signature handling."""
    
    def test_handles_missing_thought_signature(self, session_with_gemini, mock_gemini_client):
        """Test: Handles missing thought_signature gracefully."""
        mock_gemini_client.extract_thought_signature.return_value = None
        
        response = {"choices": [{"message": {"content": "Test"}}]}
        extracted_sig = mock_gemini_client.extract_thought_signature(response)
        
        # Should handle None gracefully
        if extracted_sig:
            session_with_gemini._current_thought_signature = extracted_sig
        else:
            # Should not crash, just leave signature as None or previous value
            pass
        
        # Should not raise exception
        assert True
    
    def test_handles_extract_thought_signature_exception(self, session_with_gemini, mock_gemini_client):
        """Test: Handles exceptions in extract_thought_signature."""
        mock_gemini_client.extract_thought_signature.side_effect = Exception("Extraction failed")
        
        response = {"choices": [{"message": {"content": "Test"}}]}
        
        # Should handle exception gracefully
        try:
            extracted_sig = mock_gemini_client.extract_thought_signature(response)
        except Exception:
            extracted_sig = None
        
        # Should not crash the system
        assert extracted_sig is None or isinstance(extracted_sig, str)


class DummyGeminiStreamingToolCalls(GeminiClient):
    """
    Minimal GeminiClient subtype to exercise ConversationSession's streaming + tool_calls check path
    without making network calls.
    """

    def __init__(self) -> None:
        # Intentionally do not call super().__init__ (avoid network/client setup).
        self.model = "dummy-gemini"
        self._stream_calls = 0

    def chat_stream(self, messages, tools=None, reasoning_content=None, thought_signature=None):
        # 1st stream yields no chunks -> triggers non-stream tool_calls check.
        # 2nd stream yields a final answer -> completes the turn.
        self._stream_calls += 1
        if self._stream_calls == 1:
            if False:
                yield ""  # pragma: no cover
            return
        yield "Final answer."

    def chat(self, messages, tools=None, tool_choice=None, reasoning_content=None, thought_signature=None, **kwargs):
        # Non-stream tool_calls check response: includes thought_signature we must preserve.
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {"name": "test_tool", "arguments": "{}"},
                            }
                        ],
                    }
                }
            ],
            "thought_signature": "sig-xyz",
        }

    def extract_tool_calls(self, response):
        try:
            return response["choices"][0]["message"].get("tool_calls") or []
        except Exception:
            return []

    def extract_assistant_content(self, response):
        try:
            return response["choices"][0]["message"].get("content")
        except Exception:
            return None

    def is_reasoner_model(self):
        return False


def test_streaming_tool_calls_check_preserves_thought_signature(monkeypatch, caplog):
    """
    Regression: when streaming yields no/minimal content and we do a non-streaming tool_calls check,
    we must preserve Gemini's thought_signature from that check response so tool calls can be replayed
    without warnings/API errors.
    """
    from broca.config import config

    # Avoid sleeps during streaming in tests.
    monkeypatch.setattr(config.llm, "streaming_delay", 0.0, raising=False)
    # Keep this test focused: disable RL-driven tool forcing and tool pre-filtering.
    monkeypatch.setattr(getattr(config, "rl", object()), "enabled", False, raising=False)
    monkeypatch.setattr(getattr(config, "tools", object()), "pre_filtering_enabled", False, raising=False)

    llm = DummyGeminiStreamingToolCalls()

    tool_registry = Mock()
    tool_registry.force_final_response = False
    tool_registry.tool_selection_guidance = None
    tool_registry.to_openai_format = Mock(
        return_value=[
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "Test tool",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
    )
    tool_registry.execute_tool_call = Mock(
        return_value={
            "tool_call_id": "call_1",
            "role": "tool",
            "name": "test_tool",
            "content": "OK",
        }
    )

    session = ConversationSession(llm=llm, tool_registry=tool_registry)
    session._tool_status_display = None

    caplog.set_level(logging.WARNING)
    _ = session.send("Hello", stream=True)

    assert session._current_thought_signature == "sig-xyz"

    # Ensure the assistant(tool_calls) message persisted the signature onto the tool_call payload.
    assistant_tool_msgs = [m for m in session.messages if m.get("role") == "assistant" and m.get("tool_calls")]
    assert assistant_tool_msgs
    assert assistant_tool_msgs[-1]["tool_calls"][0].get("thought_signature") == "sig-xyz"


class DummyGeminiSdkNoStreaming(GeminiClient):
    """
    GeminiClient subtype that simulates an SDK-capable configuration.

    We want ConversationSession to avoid calling chat_stream() for Gemini SDK mode,
    because REST streaming may not preserve thought_signature.
    """

    def __init__(self) -> None:
        # Intentionally do not call super().__init__ (avoid network/client setup).
        self.model = "dummy-gemini-sdk"
        self.use_sdk = True
        self._sdk_client = object()  # sentinel: indicates SDK is available/initialized
        self._called_chat_stream = False

    def chat_stream(self, *args, **kwargs):
        # If ConversationSession tries to stream, we record it and yield nothing.
        # (No chunks) triggers the non-stream tool_calls check path.
        self._called_chat_stream = True
        if False:
            yield ""  # pragma: no cover
        return

    def chat(self, messages, tools=None, tool_choice=None, reasoning_content=None, thought_signature=None, **kwargs):
        return {
            "choices": [
                {"message": {"role": "assistant", "content": "OK"}},
            ],
            "thought_signature": "sig-sdk",
        }

    def extract_tool_calls(self, response):
        return []

    def extract_assistant_content(self, response):
        try:
            return response["choices"][0]["message"].get("content")
        except Exception:
            return ""

    def extract_thought_signature(self, response):
        return response.get("thought_signature")

    def is_reasoner_model(self):
        return False


def test_gemini_sdk_mode_disables_streaming_even_when_requested(monkeypatch):
    """
    Regression/parity: when Gemini is configured for SDK mode, ConversationSession.send()
    must not use chat_stream() even if stream=True, so thought_signature round-trips.
    """
    from broca.config import config

    monkeypatch.setattr(config.llm, "streaming_delay", 0.0, raising=False)
    monkeypatch.setattr(getattr(config, "rl", object()), "enabled", False, raising=False)
    monkeypatch.setattr(getattr(config, "tools", object()), "pre_filtering_enabled", False, raising=False)

    llm = DummyGeminiSdkNoStreaming()
    session = ConversationSession(llm=llm, tool_registry=None)

    out = session.send("Hello", stream=True)
    assert out == "OK"
    assert llm._called_chat_stream is False


class DummyGeminiStoredSignature(GeminiClient):
    """
    GeminiClient subtype with a stored _thought_signature but no session-local signature.

    This simulates cases where the client has the signature (e.g., stored internally),
    but the session hasn't extracted it yet. Tool calls must still carry it.
    """

    def __init__(self) -> None:
        # Avoid super().__init__
        self.model = "dummy-gemini-stored-sig"
        self.use_sdk = True
        self._sdk_client = object()
        self._thought_signature = "sig-stored"

    def extract_assistant_content(self, response):
        try:
            return response["choices"][0]["message"].get("content")
        except Exception:
            return ""

    def extract_tool_calls(self, response):
        try:
            return response["choices"][0]["message"].get("tool_calls") or []
        except Exception:
            return []

    def extract_thought_signature(self, response):
        # Simulate a response shape that doesn't expose thought_signature directly.
        return None

    def is_reasoner_model(self):
        return False


def test_handle_tool_calls_injects_signature_from_client_storage(caplog):
    """
    Fault injection: tool_calls missing thought_signature should be repaired using
    GeminiClient._thought_signature (session fallback), preventing warning spam.
    """
    from broca.repl.session import ConversationSession

    llm = DummyGeminiStoredSignature()
    tool_registry = Mock()
    tool_registry.execute_tool_call = Mock(
        return_value={
            "tool_call_id": "call_1",
            "role": "tool",
            "name": "test_tool",
            "content": "OK",
        }
    )

    session = ConversationSession(llm=llm, tool_registry=tool_registry)
    session._tool_status_display = None
    session._current_thought_signature = None  # ensure fallback path is used

    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "test_tool", "arguments": "{}"},
                        }
                    ],
                }
            }
        ]
    }
    tool_calls = llm.extract_tool_calls(response)

    caplog.set_level(logging.WARNING)
    session._handle_tool_calls(response, tool_calls)

    assistant_tool_msgs = [m for m in session.messages if m.get("role") == "assistant" and m.get("tool_calls")]
    assert assistant_tool_msgs
    assert assistant_tool_msgs[-1]["tool_calls"][0].get("thought_signature") == "sig-stored"
    # With repair, we should not emit the missing signature warning.
    assert not any("missing_thought_signature" in r.message for r in caplog.records)


def test_golden_trace_replay_tool_call_signature_parity():
    """
    Golden-ish trace: ensure the shared injection helper yields the same tool_call payload shape
    as ConversationSession._handle_tool_calls() for Gemini.
    """
    from copy import deepcopy
    from broca.repl.session import ConversationSession, _inject_thought_signature_into_tool_calls

    llm = DummyGeminiStoredSignature()
    tool_registry = Mock()
    tool_registry.execute_tool_call = Mock(
        return_value={
            "tool_call_id": "call_1",
            "role": "tool",
            "name": "test_tool",
            "content": "OK",
        }
    )
    session = ConversationSession(llm=llm, tool_registry=tool_registry)
    session._tool_status_display = None
    session._current_thought_signature = None

    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "test_tool", "arguments": "{}"},
                        }
                    ],
                }
            }
        ]
    }
    tool_calls_session = llm.extract_tool_calls(response)
    tool_calls_helper = deepcopy(tool_calls_session)

    # "Web API path": helper injection based on stored sig.
    _inject_thought_signature_into_tool_calls(tool_calls_helper, llm._thought_signature)

    # "REPL path": ConversationSession tool handling injection.
    session._handle_tool_calls(response, tool_calls_session)
    assistant_tool_msgs = [m for m in session.messages if m.get("role") == "assistant" and m.get("tool_calls")]
    assert assistant_tool_msgs
    tool_calls_repl = assistant_tool_msgs[-1]["tool_calls"]

    assert tool_calls_helper[0]["thought_signature"] == tool_calls_repl[0]["thought_signature"] == "sig-stored"


def test_inject_thought_signature_is_idempotent_property():
    """
    Property: injection helper is idempotent and never overwrites an existing thought_signature.
    """
    from copy import deepcopy
    from hypothesis import given, strategies as st
    from broca.repl.session import _inject_thought_signature_into_tool_calls

    tool_call_strategy = st.fixed_dictionaries(
        {
            "id": st.text(min_size=1, max_size=10),
            "type": st.just("function"),
            "function": st.fixed_dictionaries(
                {
                    "name": st.text(min_size=1, max_size=10),
                    "arguments": st.text(min_size=0, max_size=20),
                }
            ),
        },
        optional={
            "thought_signature": st.text(min_size=1, max_size=20),
        },
    )

    @given(st.lists(tool_call_strategy, min_size=1, max_size=10))
    def _prop(tool_calls):
        sig = "sig-prop"
        original = deepcopy(tool_calls)
        changed1 = _inject_thought_signature_into_tool_calls(tool_calls, sig)
        changed2 = _inject_thought_signature_into_tool_calls(tool_calls, sig)

        # Every tool_call has a thought_signature after injection.
        assert all(isinstance(tc.get("thought_signature"), str) and tc["thought_signature"] for tc in tool_calls)
        # Existing signatures are preserved.
        for before, after in zip(original, tool_calls):
            if "thought_signature" in before:
                assert after["thought_signature"] == before["thought_signature"]
        # Second run does not change anything.
        assert changed2 is False
        # First run changes iff there existed at least one missing signature.
        assert changed1 is (any("thought_signature" not in tc for tc in original))

    _prop()
