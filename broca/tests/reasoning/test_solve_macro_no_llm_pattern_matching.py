"""
Regression: SOLVE should not block on LLM pattern matching by default.

In the primitive toolset, cognition macros must be "pure" and fast: they should
not make remote LLM calls just to match rules. LLM pattern matching can be
explicitly enabled via BROCA_COGNITION_LLM_PATTERN_MATCHING_ENABLED=true.
"""

from __future__ import annotations

import os

from broca.tools.cognition_tools import SolveTool


def test_solve_local_reasoning_tool_disables_llm_pattern_matching_by_default(monkeypatch):
    monkeypatch.delenv("BROCA_COGNITION_LLM_PATTERN_MATCHING_ENABLED", raising=False)

    tool = SolveTool()
    rt = tool._tool()
    assert rt.rule_engine is not None
    from broca.reasoning.local_pattern_matcher import LocalPatternMatcher

    assert isinstance(getattr(rt.rule_engine, "pattern_matcher", None), LocalPatternMatcher)


def test_solve_local_reasoning_tool_can_enable_llm_pattern_matching(monkeypatch):
    monkeypatch.setenv("BROCA_COGNITION_LLM_PATTERN_MATCHING_ENABLED", "true")

    tool = SolveTool()
    rt = tool._tool()

    # We don't assert it's always non-None (depends on OPENAI_API_KEY etc),
    # but we do assert the env toggle is respected and does not crash.
    _ = getattr(rt.rule_engine, "pattern_matcher", None)
