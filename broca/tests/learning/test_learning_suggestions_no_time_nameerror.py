"""
Regression test for broca_repl.log:
  Error executing learning action 'get_learning_suggestions': name 'time' is not defined

Root cause was missing `import time` in broca/reasoning/llm_pattern_matcher.py.
This test ensures the LearningTool suggestion path cannot crash with NameError.
"""

from __future__ import annotations

from broca.learning.integration_tool import LearningTool


class DummyLLM:
    def chat(self, messages, temperature=0.0, tools=None, reasoning_content=None, thought_signature=None):
        # LLMPatternMatcher.match_batch expects a JSON list of {match, confidence} objects.
        return {"choices": [{"message": {"content": '[{\"match\": true, \"confidence\": 0.5}]'}}]}

    def extract_assistant_content(self, response):
        return response["choices"][0]["message"]["content"]


def test_learning_get_learning_suggestions_does_not_raise_time_nameerror(monkeypatch):
    # Create tool with a SkillManager that will initialize LLMPatternMatcher.
    tool = LearningTool()

    # Monkeypatch the LLM client used by SkillManager's pattern matcher (if present).
    if getattr(tool.skill_manager, "pattern_matcher", None) is not None:
        tool.skill_manager.pattern_matcher.llm = DummyLLM()

    result = tool.execute(action="get_learning_suggestions", context={"dissonance": 0.2})
    assert isinstance(result, dict)
    assert result.get("success") is True


