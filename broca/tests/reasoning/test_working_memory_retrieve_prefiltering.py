from __future__ import annotations

from broca.reasoning.local_pattern_matcher import LocalPatternMatcher
from broca.reasoning.working_memory import WorkingMemory


class CountingMatcher:
    def __init__(self) -> None:
        self.calls = 0
        self._delegate = LocalPatternMatcher()

    def match(self, pattern, content) -> bool:
        self.calls += 1
        return self._delegate.match(pattern, content)


def test_working_memory_retrieve_prefilters_hard_constraints_before_matching():
    wm = WorkingMemory(pattern_matcher=CountingMatcher())
    wm.add({"type": "b", "status": "x"})
    wm.add({"type": "b", "status": "y"})

    matcher = wm.pattern_matcher
    assert matcher is not None

    _ = wm.retrieve(pattern={"type": "a"})
    assert matcher.calls == 0

