from unittest.mock import Mock, patch
import json


def _tool_call(tool_name: str, call_id: str) -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": tool_name, "arguments": json.dumps({"param": "x"})},
    }


def test_web_api_calls_rl_selection_each_tool_iteration():
    """
    Regression/behavior: web_api should recompute RL selection between tool calls so RL can
    influence tool selection per tool-call step (not only once per user message).
    """
    runtime = Mock()

    tool_registry = Mock()
    tool_registry.to_openai_format = Mock(return_value=[])
    tool_registry.execute_tool_call = Mock(
        return_value={"tool_call_id": "call_x", "role": "tool", "name": "terminal", "content": "ok", "_success": True}
    )
    tool_registry.get_rl_selection = Mock(return_value=None)
    tool_registry.tool_selection_guidance = Mock()
    tool_registry.tool_selection_guidance.guidance_aggregator = Mock()
    tool_registry.tool_selection_guidance.guidance_aggregator.gather_context = Mock(return_value={})
    runtime.tool_registry = tool_registry
    runtime.world_state_aggregator = None

    session = Mock()
    session.messages = []
    session.internal_sensing_framework = None
    session._update_system_prompt = Mock()
    session._get_messages_for_llm = Mock(return_value=[])

    llm = Mock()
    llm.extract_assistant_content = Mock(return_value="")

    # Iteration 1: tool call
    # Iteration 2: tool call
    # Iteration 3: final response
    tool_call_lists = [
        [_tool_call("terminal", "call_1")],
        [_tool_call("terminal", "call_2")],
        [],
    ]
    llm.chat = Mock(side_effect=[{"choices": [{"message": {"content": ""}}]}] * 3)
    llm.extract_tool_calls = Mock(side_effect=tool_call_lists)
    session.llm = llm
    runtime.session = session

    with patch("broca.web_api.get_runtime", return_value=runtime):
        with patch("broca.web_api.get_storage", return_value=None):
            with patch("broca.web_api.create_session", return_value=session):
                from broca.web_api import stream_response

                list(stream_response("cid", "do stuff", web_search_enabled=True))

    # One RL selection per iteration where we call the LLM (here: 3).
    # If RL is disabled, this can still be called with None.
    assert tool_registry.get_rl_selection.call_count >= 2
