"""
Golden trace replay for PatternMatcher JSON parsing + logging hooks.
"""

from broca.reasoning.pattern_matcher import PatternMatcher


class DummyLLM:
    def __init__(self, content: str):
        self._content = content

    def chat(self, messages, temperature=0.0):
        return {"choices": [{"message": {"content": self._content}}]}

    def extract_assistant_content(self, response):
        return response["choices"][0]["message"]["content"]


def test_pattern_match_llm_json_parse_golden_trace():
    # Includes markdown fenced JSON to validate stripping logic.
    content = "```json\n[{\"match\": false, \"confidence\": 0.1}]\n```"
    pm = PatternMatcher(llm_client=DummyLLM(content), model="gpt-5-nano")
    assert pm.match({"type": "contradiction_check", "text": "A"}, {"text": "A"}) is False


