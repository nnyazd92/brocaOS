"""
Property-based tests for EmbeddingService truncation.

Uses hypothesis to test properties that should hold for all inputs.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck

from broca.memory.embeddings import EmbeddingService, DEFAULT_EMBEDDING_MAX_TOKENS, DEFAULT_EMBEDDING_MAX_CHARS
from broca.summarization.token_estimator import estimate_tokens


@pytest.fixture
def mock_openai_class():
    """Mock OpenAI client class."""
    with patch('broca.memory.embeddings.OpenAI') as mock_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response
        mock_class.return_value = mock_client
        yield mock_class


@pytest.fixture
def embedding_service(mock_openai_class):
    """EmbeddingService instance with mocked client."""
    return EmbeddingService(api_key="test-key", dimension=1536)


class TestEmbeddingTruncationProperties:
    """Property-based tests for embedding truncation."""
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(text=st.text(min_size=1, max_size=DEFAULT_EMBEDDING_MAX_CHARS * 2))
    def test_truncated_text_always_under_limit(self, embedding_service, text):
        """
        Property: Truncated text is always under the character limit.
        
        Rationale: For any text input, truncation should ensure the result
        fits within the embedding model's context limits.
        """
        truncated = embedding_service._truncate_text_for_embedding(text)
        
        # Property: truncated text should never exceed max_chars
        assert len(truncated) <= DEFAULT_EMBEDDING_MAX_CHARS
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(text=st.text(min_size=1, max_size=DEFAULT_EMBEDDING_MAX_CHARS // 2))
    def test_short_text_never_truncated(self, embedding_service, text):
        """
        Property: Short texts are never truncated.
        
        Rationale: Texts well under the limit should remain unchanged.
        """
        truncated = embedding_service._truncate_text_for_embedding(text)
        
        # Property: short text should remain unchanged
        assert truncated == text
        assert len(truncated) == len(text)
    
    @settings(
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.large_base_example,
            HealthCheck.data_too_large
        ],
        max_examples=10
    )
    @given(
        # Use a reasonable size that's still meaningful for testing truncation
        # Hypothesis has limits, so we use 2000-4000 chars which is still a good test
        text=st.text(min_size=2000, max_size=4000)
    )
    def test_long_text_always_truncated(self, embedding_service, text):
        """
        Property: Long texts are always truncated to fit limit.
        
        Rationale: Texts exceeding the limit should be truncated.
        Note: Using smaller text size (2000-4000 chars) due to Hypothesis limitations,
        but still tests that truncation logic works correctly.
        """
        truncated = embedding_service._truncate_text_for_embedding(text)
        
        # Property: truncated text should always be under limit
        assert len(truncated) <= DEFAULT_EMBEDDING_MAX_CHARS
        # If original text was over limit, it should be truncated
        if len(text) > DEFAULT_EMBEDDING_MAX_CHARS:
            assert len(truncated) < len(text)
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(text=st.text(min_size=1))
    def test_truncation_is_idempotent(self, embedding_service, text):
        """
        Property: Truncating already-truncated text doesn't change it further.
        
        Rationale: Truncation should be idempotent - applying it twice
        should produce the same result as applying it once.
        """
        truncated_once = embedding_service._truncate_text_for_embedding(text)
        truncated_twice = embedding_service._truncate_text_for_embedding(truncated_once)
        
        # Property: second truncation should produce same result
        assert truncated_once == truncated_twice
        assert len(truncated_once) == len(truncated_twice)
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        text1=st.text(min_size=1),
        text2=st.text(min_size=1)
    )
    def test_truncation_preserves_ordering_for_short_texts(self, embedding_service, text1, text2):
        """
        Property: Truncation preserves relative ordering for short texts.
        
        Rationale: For texts under the limit, truncation should preserve
        the original text (no change in ordering/length relationships).
        """
        # Only test when both are short
        assume(estimate_tokens(text1) <= DEFAULT_EMBEDDING_MAX_TOKENS)
        assume(estimate_tokens(text2) <= DEFAULT_EMBEDDING_MAX_TOKENS)
        
        truncated1 = embedding_service._truncate_text_for_embedding(text1)
        truncated2 = embedding_service._truncate_text_for_embedding(text2)
        
        # Property: original length relationships should be preserved
        if len(text1) < len(text2):
            assert len(truncated1) <= len(truncated2)
        elif len(text1) > len(text2):
            assert len(truncated1) >= len(truncated2)
        else:
            assert len(truncated1) == len(truncated2)
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(texts=st.lists(st.text(min_size=1, alphabet=st.characters(min_codepoint=33, max_codepoint=126)), min_size=1, max_size=10))
    def test_batch_truncation_all_under_limit(self, embedding_service, texts):
        """
        Property: All texts in batch are truncated to fit limits.
        
        Rationale: Batch truncation should ensure all texts fit within limits.
        Note: Using printable ASCII to avoid whitespace-only texts that get filtered.
        """
        # All texts should be non-empty and non-whitespace due to strategy
        assert len(texts) > 0
        assert all(t.strip() for t in texts)
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536) for _ in texts]
        embedding_service._client.embeddings.create.return_value = mock_response
        
        embedding_service.generate_embeddings_batch(texts)
        
        # Verify all texts sent to API are under limit
        call_args = embedding_service._client.embeddings.create.call_args
        input_texts = call_args[1]["input"]
        
        for text in input_texts:
            # Property: all texts should be under limit
            assert len(text) <= DEFAULT_EMBEDDING_MAX_CHARS
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(text=st.text(min_size=1))
    def test_truncation_preserves_text_prefix(self, embedding_service, text):
        """
        Property: Truncation preserves the beginning of the text.
        
        Rationale: Truncation should keep the start of the text (prefix),
        which typically contains the most important information.
        """
        truncated = embedding_service._truncate_text_for_embedding(text)
        
        # Property: if text was truncated, the prefix should be preserved
        if len(truncated) < len(text):
            prefix_length = min(len(truncated), len(text))
            assert text[:prefix_length] == truncated[:prefix_length]
        else:
            # If not truncated, should be identical
            assert text == truncated

