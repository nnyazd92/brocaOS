"""
Golden trace replay for RL signal LLM estimator parsing.
"""

from broca.reasoning.rl_signal_estimators import LLMRLSignalEstimator


class DummyLLM:
    def __init__(self, content: str):
        self._content = content

    def chat(self, messages, temperature=0.0, tools=None, reasoning_content=None, thought_signature=None):
        return {"choices": [{"message": {"content": self._content}}]}

    def extract_assistant_content(self, response):
        return response["choices"][0]["message"]["content"]


def test_rl_signal_estimator_json_parse_golden_trace():
    content = '{"estimates": {"information_gain": {"value": 0.6, "uncertainty": 0.2}}}'
    est = LLMRLSignalEstimator(llm_client=DummyLLM(content), model="gpt-5-nano", cache_size=0)
    v, u = est.estimate_information_gain(context={"epistemic_info": {"has_data": False}})
    assert 0.59 <= v <= 0.61
    assert 0.19 <= u <= 0.21


def test_rl_signal_estimator_fault_injection_malformed_json_returns_empty():
    # malformed JSON should not crash; estimator should return fallback values.
    content = "not json"
    est = LLMRLSignalEstimator(llm_client=DummyLLM(content), model="gpt-5-nano", cache_size=0)
    v, u = est.estimate_surprise(context={"affective_state": {"data_quality": {"surprise": "missing"}}})
    assert 0.0 <= v <= 1.0
    assert 0.0 <= u <= 1.0


