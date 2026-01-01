from __future__ import annotations

from broca.prompting.recursive_thought import AppendOnlyThoughtLogger, RecursiveThoughtLoop


class StubBackend:
    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)
        self.prompts: list[str] = []
        self.conversation_id = "conv_test"

    def send(self, prompt: str, *, web_search: bool = True, include_rl_signals: bool = False):
        self.prompts.append(prompt)
        if not self._replies:
            raise AssertionError("StubBackend ran out of replies")
        return self._replies.pop(0), {"conversation_id": self.conversation_id}


def test_recursive_thought_auto_pivots_instead_of_exiting(tmp_path):
    backend = StubBackend(
        replies=[
            "plan ok",          # initial_plan
            "cycle one",        # cycle
            "next topic",       # pivot
            "cycle two",        # cycle after pivot
        ]
    )
    thought_logger = AppendOnlyThoughtLogger(
        text_path=tmp_path / "stream.log",
        jsonl_path=tmp_path / "stream.jsonl",
    )

    loop = RecursiveThoughtLoop("seed", backend=backend, thought_logger=thought_logger)
    loop.run(
        max_iterations=1,          # pivot after every cycle
        auto_pivot=True,
        max_total_cycles=2,        # stop after two cycles total (test determinism)
        sleep_between_cycles_seconds=0.0,
    )

    assert any("PLAN:" in p for p in backend.prompts)
    assert any("You are running an autonomous recursive thought loop" in p for p in backend.prompts)

