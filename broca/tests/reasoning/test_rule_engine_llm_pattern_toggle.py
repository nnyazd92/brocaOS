"""
Unit tests for RuleEngine LLM pattern matching toggle.
"""

from __future__ import annotations

from unittest.mock import Mock

from broca.reasoning.rule_engine import RuleEngine
from broca.config import config


def test_rule_engine_respects_llm_pattern_matching_disabled(monkeypatch):
    # If this is ignored, RuleEngine will instantiate an OpenAI client and make background calls.
    monkeypatch.setattr(config.reasoning, "llm_pattern_matching_enabled", False, raising=False)

    # Guardrail: if someone later refactors and tries to init anyway, we want a hard failure.
    monkeypatch.setattr(
        "broca.llm.create_llm_client",
        Mock(side_effect=AssertionError("create_llm_client should not be called when LLM pattern matching is disabled")),
        raising=False,
    )

    engine = RuleEngine()
    # RuleEngine should still use local pattern matching (LLM-free), but must not instantiate an LLM.
    from broca.reasoning.local_pattern_matcher import LocalPatternMatcher

    assert isinstance(engine.pattern_matcher, LocalPatternMatcher)
