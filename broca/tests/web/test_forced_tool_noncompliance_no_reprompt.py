import logging
from unittest.mock import Mock, patch


class _Sel:
    def __init__(self, tool_name: str):
        self.mode = "forced"
        self.confidence = 0.5
        self.tool_name = tool_name
        self.score = 0.5
        self.alternatives = []
        self.reason = "forced for test"
        self.all_scores = {}


def _tool_call(tool_name: str, call_id: str) -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": tool_name, "arguments": "{}"},
    }


def test_forced_tool_noncompliance_is_not_reprompted(caplog):
    """
    Web API should not enter a forced-mode reprompt loop (can cause multi-minute silent waits).
    It should surface execution-time enforcement immediately (ToolRegistry blocks disallowed tools).
    """
    caplog.set_level(logging.WARNING)

    runtime = Mock()
    tool_registry = Mock()
    tool_registry.tool_selection_guidance = Mock()
    tool_registry.tool_selection_guidance.guidance_aggregator = Mock()
    tool_registry.tool_selection_guidance.guidance_aggregator.gather_context = Mock(return_value={})

    # web_api calls get_rl_selection once pre-loop and then per iteration.
    tool_registry.get_rl_selection = Mock(
        side_effect=[
            _Sel("retrieve_memories"),  # pre-loop
            _Sel("retrieve_memories"),  # iteration 1 (forced)
            None,  # iteration 2 (stop forcing)
        ]
    )
    tool_registry.to_openai_format = Mock(return_value=[])
    tool_registry.execute_tool_call = Mock(
        return_value={
            "role": "tool",
            "tool_call_id": "call_1",
            "name": "store_memory",
            "content": "Blocked: forced tool selection mismatch",
            "_success": False,
        }
    )
    runtime.tool_registry = tool_registry
    runtime.world_state_aggregator = None

    session = Mock()
    session.messages = []
    session.internal_sensing_framework = None
    session._update_system_prompt = Mock()
    session._get_messages_for_llm = Mock(return_value=[])

    llm = Mock()
    llm.extract_assistant_content = Mock(return_value="")
    llm.chat = Mock(
        side_effect=[
            {"choices": [{"message": {"content": ""}}]},
            {"choices": [{"message": {"content": "done"}}]},
        ]
    )
    llm.extract_tool_calls = Mock(
        side_effect=[
            [_tool_call("store_memory", "call_1")],  # wrong for forced retrieve_memories
            [],
        ]
    )
    session.llm = llm

    # Capture tool selection logger output (web_api uses propagate=False loggers normally).
    test_logger = logging.getLogger("test.forced.noncompliance")
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = True

    storage = Mock()
    storage.load_conversation = Mock(return_value={"conversation_id": "cid", "messages": []})

    with patch("broca.web_api.get_runtime", return_value=runtime):
        with patch("broca.web_api.get_storage", return_value=storage):
            with patch("broca.web_api.create_session", return_value=session):
                with patch("broca.web_api._get_tool_selection_logger", return_value=test_logger):
                    from broca.web_api import stream_response

                    out = list(stream_response("cid", "hello", web_search_enabled=True))

    # No extra LLM call should be used for reprompting; only the tool-result continuation triggers 2nd call.
    assert llm.chat.call_count == 2

    # Ensure we did not inject the old "[SYSTEM DIRECTIVE] RL forced-mode is active..." message.
    directive_msgs = [
        m
        for m in session.messages
        if isinstance(m, dict)
        and isinstance(m.get("content"), str)
        and "RL forced-mode is active" in m.get("content")
    ]
    assert directive_msgs == []

    msgs = "\n".join(r.message for r in caplog.records)
    assert "API_FORCED_TOOL_NONCOMPLIANCE" in msgs
    assert "remaining_reprompts" not in msgs

    # Ensure client sees a tool_result event (immediate enforcement feedback).
    assert any('"type": "tool_result"' in line for line in out)

