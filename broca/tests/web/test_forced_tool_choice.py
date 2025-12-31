from unittest.mock import Mock, patch


def test_web_api_sets_tool_choice_in_forced_mode():
    runtime = Mock()

    selection = Mock()
    selection.mode = "forced"
    selection.confidence = 1.0
    selection.tool_name = "delete_memory"
    selection.score = 1.0
    selection.alternatives = []
    selection.reason = "forced for test"

    tool_registry = Mock()
    tool_registry.get_rl_selection = Mock(return_value=selection)
    tool_registry.to_openai_format = Mock(
        return_value=[
            {
                "type": "function",
                "function": {
                    "name": "delete_memory",
                    "description": "x",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
    )
    runtime.tool_registry = tool_registry
    runtime.world_state_aggregator = None

    session = Mock()
    session.messages = []
    session.internal_sensing_framework = None
    session._update_system_prompt = Mock()
    session._get_messages_for_llm = Mock(return_value=[])

    llm = Mock()
    llm.extract_assistant_content = Mock(return_value="done")
    llm.extract_tool_calls = Mock(return_value=[])
    llm.chat = Mock(return_value={"choices": [{"message": {"content": "done"}}]})
    session.llm = llm

    with patch("broca.web_api.get_runtime", return_value=runtime):
        with patch("broca.web_api.get_storage", return_value=None):
            with patch("broca.web_api.create_session", return_value=session):
                from broca.web_api import stream_response

                list(stream_response("cid", "hello", web_search_enabled=True))

    assert llm.chat.call_count >= 1
    _, kwargs = llm.chat.call_args
    assert kwargs["tool_choice"] == {"type": "function", "function": {"name": "delete_memory"}}

