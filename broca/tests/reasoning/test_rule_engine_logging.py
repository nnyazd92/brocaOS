"""
Regression tests for RuleEngine logging behavior.
"""

from __future__ import annotations

import logging

from broca.reasoning.rule_engine import RuleEngine
from broca.reasoning.production_rules import ProductionRule, RuleType
from broca.reasoning.working_memory import WorkingMemory


def test_rule_engine_does_not_info_spam_when_no_matches(caplog):
    engine = RuleEngine(pattern_matcher=None)
    engine.rule_system.rules = [
        ProductionRule(
            name="never_matches",
            conditions=[{"type": "fact", "content": "something"}],
            actions=[],
            rule_type=RuleType.INFERENCE,
        )
    ]

    caplog.set_level(logging.DEBUG)
    wm = WorkingMemory()
    _ = engine.match_rules(wm)

    # When no rules match, we should log at DEBUG (not INFO).
    assert any(
        rec.name == "broca.reasoning.rule_engine"
        and rec.levelno == logging.DEBUG
        and "matched=0" in rec.message
        for rec in caplog.records
    )
    assert not any(
        rec.name == "broca.reasoning.rule_engine"
        and rec.levelno == logging.INFO
        and "matched=0" in rec.message
        for rec in caplog.records
    )

