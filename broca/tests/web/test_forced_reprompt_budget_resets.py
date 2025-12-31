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


def test_forced_reprompt_budget_resets_when_forced_tool_changes(caplog):
    """
    Regression: forced reprompt budget should not be global "3 strikes you're out".
    It should reset when a new forced tool selection episode begins (forced tool changes).
    """
    # Capture tool selection logger output (web_api uses propagate=False loggers normally).
    caplog.set_level(logging.WARNING)

    runtime = Mock()
    tool_registry = Mock()
    tool_registry.tool_selection_guidance = Mock()
    tool_registry.tool_selection_guidance.guidance_aggregator = Mock()
    tool_registry.tool_selection_guidance.guidance_aggregator.gather_context = Mock(return_value={})

    # Force tool A, then force tool B, then stop forcing.
    # Note: web_api calls get_rl_selection once pre-loop and then per-iteration.
    tool_registry.get_rl_selection = Mock(
        side_effect=[
            _Sel("retrieve_memories"),  # pre-loop
            _Sel("retrieve_memories"),  # iteration 1
            _Sel("store_memory"),  # iteration 2 (new forced tool -> budget should reset)
            None,  # iteration 3
        ]
    )
    tool_registry.to_openai_format = Mock(return_value=[])
    tool_registry.execute_tool_call = Mock(return_value={"role": "tool", "tool_call_id": "x", "name": "noop", "content": "", "_success": True})
    runtime.tool_registry = tool_registry
    runtime.world_state_aggregator = None

    session = Mock()
    session.messages = []
    session.internal_sensing_framework = None
    session._update_system_prompt = Mock()
    session._get_messages_for_llm = Mock(return_value=[])

    llm = Mock()
    llm.extract_assistant_content = Mock(return_value="")
    llm.chat = Mock(side_effect=[{"choices": [{"message": {"content": ""}}]}] * 3)
    # Each iteration tries the wrong tool name, so we trigger the reprompt path twice.
    llm.extract_tool_calls = Mock(
        side_effect=[
            [_tool_call("store_memory", "call_1")],  # wrong for forced retrieve_memories
            [_tool_call("retrieve_memories", "call_2")],  # wrong for forced store_memory
            [],  # end
        ]
    )
    session.llm = llm

    test_logger = logging.getLogger("test.forced.reprompt")
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = True

    storage = Mock()
    storage.load_conversation = Mock(return_value={"conversation_id": "cid", "messages": []})

    with patch("broca.web_api.get_runtime", return_value=runtime):
        with patch("broca.web_api.get_storage", return_value=storage):
            with patch("broca.web_api.create_session", return_value=session):
                with patch("broca.web_api._get_tool_selection_logger", return_value=test_logger):
                    from broca.web_api import stream_response

                    list(stream_response("cid", "hello", web_search_enabled=True))

    msgs = "\n".join(r.message for r in caplog.records)
    # Budget starts at 3; after first noncompliance it should log remaining_reprompts=2.
    # When forced tool changes, it should reset to 3 again, so the second noncompliance also logs 2.
    assert msgs.count("remaining_reprompts=2") >= 2
