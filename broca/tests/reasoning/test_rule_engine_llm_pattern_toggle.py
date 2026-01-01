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
    assert engine.pattern_matcher is None
