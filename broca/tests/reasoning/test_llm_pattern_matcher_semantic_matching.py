"""
Tests verifying LLMPatternMatcher performs correct semantic subset matching.

These tests ensure the improved prompt correctly identifies:
1. Pattern subset matches (content has extra fields - OK)
2. Type inference (pattern.type="goal" matches content with goal_type, etc.)
3. Semantic field matching
"""

import pytest


class MockLLM:
    """Mock LLM that returns expected JSON based on the new semantic matching rules."""
    
    def __init__(self, responses: list):
        """
        Args:
            responses: List of JSON response strings, one per batch call.
        """
        self.responses = responses
        self.call_count = 0
        self.last_prompt = None
    
    def chat(self, messages, temperature=0.0):
        self.last_prompt = messages[-1]["content"]  # Store for inspection
        response = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return {"choices": [{"message": {"content": response}}]}
    
    def extract_assistant_content(self, response):
        return response["choices"][0]["message"]["content"]


def test_goal_type_subset_match():
    """Test that pattern {type: goal, goal_type: achieve} matches content with goal_type=achieve."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    
    # LLM should return true because content.goal_type == pattern.goal_type
    mock_llm = MockLLM(['[{"match": true, "confidence": 0.95}]'])
    matcher = LLMPatternMatcher(llm_client=mock_llm, model="gpt-5-nano")
    
    pattern = {"type": "goal", "goal_type": "achieve"}
    content = {
        "name": "implement_cognitive_reasoning",
        "description": "Implement production rule system",
        "goal_type": "achieve",
        "status": "active",
        "priority": 0.9,
    }
    
    result = matcher.match(pattern, content)
    
    # Verify the prompt contains the new semantic matching instructions
    assert "SUBSET matching" in mock_llm.last_prompt
    assert "NOT exact matching" in mock_llm.last_prompt
    assert "Semantic Hint" in mock_llm.last_prompt
    
    assert result is True


def test_goal_type_mismatch():
    """Test that pattern {goal_type: learn} does NOT match content with goal_type=maintain."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    
    # LLM should return false because goal_type doesn't match
    mock_llm = MockLLM(['[{"match": false, "confidence": 0.9}]'])
    matcher = LLMPatternMatcher(llm_client=mock_llm, model="gpt-5-nano")
    
    pattern = {"type": "goal", "goal_type": "learn"}
    content = {
        "name": "minimize_dissonance",
        "goal_type": "maintain",  # Different from pattern
        "priority": 1.0,
    }
    
    result = matcher.match(pattern, content)
    assert result is False


def test_domain_semantic_match():
    """Test semantic matching for domain field."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    
    # LLM should return true if content description relates to code_analysis
    mock_llm = MockLLM(['[{"match": true, "confidence": 0.85}]'])
    matcher = LLMPatternMatcher(llm_client=mock_llm, model="gpt-5-nano")
    
    pattern = {"type": "task", "domain": "code_analysis"}
    content = {
        "name": "analyze_repository",
        "description": "Analyze the codebase structure and dependencies",
        "status": "pending",
    }
    
    result = matcher.match(pattern, content)
    assert result is True


def test_complexity_semantic_match():
    """Test semantic matching for complexity field."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    
    # LLM should infer high complexity from description
    mock_llm = MockLLM(['[{"match": true, "confidence": 0.8}]'])
    matcher = LLMPatternMatcher(llm_client=mock_llm, model="gpt-5-nano")
    
    pattern = {"type": "task", "complexity": "high"}
    content = {
        "name": "implement_ml_pipeline",
        "description": "Build a full machine learning pipeline with data preprocessing, model training, hyperparameter tuning, and deployment",
    }
    
    result = matcher.match(pattern, content)
    assert result is True


def test_empty_content_no_match():
    """Test that empty content doesn't match a pattern with constraints."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    
    mock_llm = MockLLM(['[{"match": false, "confidence": 0.95}]'])
    matcher = LLMPatternMatcher(llm_client=mock_llm, model="gpt-5-nano")
    
    pattern = {"type": "goal", "goal_type": "achieve"}
    content = {}
    
    result = matcher.match(pattern, content)
    assert result is False


def test_contradiction_check_still_works():
    """Test that contradiction_check pattern type still works correctly."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    
    # LLM should detect semantic contradiction
    mock_llm = MockLLM(['[{"match": true, "confidence": 0.9}]'])
    matcher = LLMPatternMatcher(llm_client=mock_llm, model="gpt-5-nano")
    
    pattern = {"type": "contradiction_check", "text": "The sky is blue"}
    content = {"text": "The sky is green"}
    
    result = matcher.match(pattern, content)
    
    # Verify contradiction check instructions are in prompt
    assert "contradiction_check" in mock_llm.last_prompt.lower() or "contradict" in mock_llm.last_prompt.lower()
    assert result is True


def test_batch_matching_with_mixed_results():
    """Test batch matching returns correct mixed results."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    
    # First match (goal with matching goal_type), second no match (different goal_type)
    mock_llm = MockLLM(['[{"match": true, "confidence": 0.95}, {"match": false, "confidence": 0.9}]'])
    matcher = LLMPatternMatcher(llm_client=mock_llm, model="gpt-5-nano")
    
    pairs = [
        (
            {"type": "goal", "goal_type": "achieve"},
            {"name": "task1", "goal_type": "achieve", "priority": 0.9}
        ),
        (
            {"type": "goal", "goal_type": "learn"},
            {"name": "task2", "goal_type": "maintain", "priority": 1.0}
        ),
    ]
    
    results = matcher.match_batch(pairs)
    
    assert len(results) == 2
    assert results[0] == (True, 0.95)
    assert results[1] == (False, 0.9)


def test_prompt_includes_examples():
    """Test that the prompt includes concrete examples for the LLM."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    
    mock_llm = MockLLM(['[{"match": true, "confidence": 0.9}]'])
    matcher = LLMPatternMatcher(llm_client=mock_llm, model="gpt-5-nano")
    
    matcher.match({"type": "goal"}, {"name": "test"})
    
    # Check examples are in prompt
    assert "## Examples" in mock_llm.last_prompt
    assert "match=true" in mock_llm.last_prompt
    assert "match=false" in mock_llm.last_prompt

