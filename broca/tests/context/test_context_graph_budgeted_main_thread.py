"""
Regression tests for ContextGraph main-thread budgeting.

The failure mode seen in broca_repl.log is that must_keep_tokens grows unbounded
because main_thread_ids is the full root->latest path in a linear chat.
That forces emergency truncation and increases agent weirdness.
"""

from __future__ import annotations

import logging

from broca.context.context_graph import ContextGraph


def test_linear_chat_does_not_force_must_keep_overflow(caplog):
    """
    In a long linear chat, pruning should not treat the entire history as must-keep.

    We assert we do NOT emit the warning:
      \"Must-keep messages exceed token limit ...\"
    for a scenario where the full history would exceed max_tokens, but a budgeted
    main-thread would fit.
    """
    graph = ContextGraph(min_turns_retained=2)

    # Create a long linear chat with medium-sized messages.
    # Total history will exceed 1000 tokens, but a recent slice should fit.
    parent = None
    for i in range(200):
        role = "user" if i % 2 == 0 else "assistant"
        msg = {
            "role": role,
            "content": f"{role} message {i}: " + ("x" * 200),
            "message_id": f"m{i}",
        }
        graph.add_message(msg, parent_id=parent)
        parent = msg["message_id"]

    caplog.set_level(logging.WARNING)
    to_keep, tokens = graph.prune_to_fit(max_tokens=1000, safety_margin=0.95)

    assert tokens <= int(1000 * 0.95) * 1.05  # small estimation slack
    assert len(to_keep) > 0
    # Key: with budgeting, we should not hit the emergency \"must keep overflow\" path.
    assert not any("Must-keep messages exceed token limit" in r.message for r in caplog.records)


