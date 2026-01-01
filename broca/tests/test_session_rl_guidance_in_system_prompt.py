import json

from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator


def _extract_json_from_system_prompt(prompt: str) -> dict:
    start = prompt.find("{")
    assert start != -1, "System prompt did not contain a JSON object"
    return json.loads(prompt[start:])


def test_rl_guidance_is_visible_in_mutable_system_prompt(mock_llm_client):
    aggregator = WorldStateAggregator()
    session = ConversationSession(llm=mock_llm_client, world_state_aggregator=aggregator)

    aggregator.set_rl_guidance(
        suggested_tool="planning",
        mode="forced",
        confidence=0.42,
        reason="Forced exploration (p=0.10) - collect on-policy data",
        selection_id=123,
        suggested_tools=["planning", "reasoning"],
        ppo_status={"buffer_len": 7, "batch_size": 32},
    )
    session._update_system_prompt()

    assert session.messages[0]["role"] == "system"
    world_state = _extract_json_from_system_prompt(session.messages[0]["content"])
    rl = world_state["rl_guidance"]
    assert rl["reward_system_suggests_tool"] == "planning"
    assert rl["reward_system_suggests_line"] == "REWARD SYSTEM SUGGESTS: planning"
    assert rl["mode"] == "forced"

