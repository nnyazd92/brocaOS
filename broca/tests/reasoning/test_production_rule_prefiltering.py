from __future__ import annotations

from broca.reasoning.local_pattern_matcher import LocalPatternMatcher
from broca.reasoning.production_rules import ProductionRule, ProductionRuleSystem, RuleType
from broca.reasoning.working_memory import WorkingMemory


class CountingMatcher:
    def __init__(self) -> None:
        self.calls = 0
        self._delegate = LocalPatternMatcher()

    def match(self, pattern, content) -> bool:
        self.calls += 1
        return self._delegate.match(pattern, content)

    def rank_text_candidates(self, query, candidates, *, top_k=None):
        return self._delegate.rank_text_candidates(query, candidates, top_k=top_k)


def test_production_rule_matching_prefilters_by_hard_constraints_to_avoid_cartesian_scans():
    wm = WorkingMemory()
    wm.add({"type": "b", "status": "x"})

    matcher = CountingMatcher()
    prs = ProductionRuleSystem(working_memory=wm, pattern_matcher=matcher)

    # Remove defaults for deterministic test.
    prs.rules = []
    prs._compiled_conditions_key = None

    for i in range(200):
        prs.add_rule(
            ProductionRule(
                name=f"r{i}",
                conditions=[{"type": "a", "status": i}],
                actions=[],
                rule_type=RuleType.INFERENCE,
            )
        )

    matched = prs.match_rules(working_memory=wm)
    assert matched == []
    # Because WM items have type="b", the compiled prefilter should exclude all conditions
    # without calling the matcher at all.
    assert matcher.calls == 0

