import logging
from unittest.mock import Mock, patch


def test_stream_response_logs_llm_chat_stage(caplog):
    caplog.set_level(logging.INFO)

    runtime = Mock()
    tool_registry = Mock()
    tool_registry.to_openai_format = Mock(return_value=[])
    tool_registry.execute_tool_call = Mock(
        return_value={"tool_call_id": "call_x", "role": "tool", "name": "noop", "content": "ok", "_success": True}
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
    llm.extract_assistant_content = Mock(return_value="done")
    llm.extract_tool_calls = Mock(return_value=[])
    llm.chat = Mock(return_value={"choices": [{"message": {"content": "done"}}]})
    session.llm = llm

    test_logger = logging.getLogger("test.web.timing")
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = True

    with patch("broca.web_api.get_runtime", return_value=runtime):
        with patch("broca.web_api.get_storage", return_value=None):
            with patch("broca.web_api.create_session", return_value=session):
                with patch("broca.web_api._get_tool_selection_logger", return_value=test_logger):
                    from broca.web_api import stream_response

                    list(stream_response("cid", "hello", web_search_enabled=True))

    msgs = "\n".join(r.message for r in caplog.records)
    assert "API_STAGE_START" in msgs and "stage=llm_chat" in msgs
    assert "API_STAGE_END" in msgs and "stage=llm_chat" in msgs

