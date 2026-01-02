from __future__ import annotations

from broca.world_state.aggregator import WorldStateAggregator


def test_world_state_clamps_large_strings_and_lists_for_prompt():
    ws = {
        "timestamp": "t",
        "internal_state": {
            "huge_text": "x" * 50000,
            "huge_list": list(range(1000)),
            "nested": {
                "k": {
                    "deep": {
                        "more": {
                            "even_more": {
                                "too_deep": {"v": "y" * 50000},
                            }
                        }
                    }
                }
            },
        },
    }
    clamped = WorldStateAggregator._clamp_for_prompt(ws, max_string_len=1000, max_list_len=10, max_dict_items=10)
    assert isinstance(clamped, dict)
    assert len(clamped["internal_state"]["huge_text"]) <= 1014  # 1000 + "...[truncated]"
    assert len(clamped["internal_state"]["huge_list"]) == 10

