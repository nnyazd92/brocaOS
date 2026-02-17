"""
Mutation testing validation tests for EmbeddingService truncation.

These tests are designed to kill mutations in the embedding truncation code.
The actual mutation testing is run with mutmut, but these tests help
validate that our test suite is comprehensive enough to catch bugs.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import pytest

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


class TestEmbeddingTruncationMutationKillers:
    """
    Tests specifically designed to kill mutations in truncation logic.
    
    These tests verify specific behaviors that would be broken by common mutations
    like changing operators, conditions, or return values.
    """
    
    def test_truncate_text_for_embedding_does_not_truncate_when_under_limit(self, mock_openai_class):
        """Kills mutation: truncating when text is under limit."""
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        short_text = "Short text"
        truncated = service._truncate_text_for_embedding(short_text)
        
        # Should not truncate
        assert truncated == short_text
        assert len(truncated) == len(short_text)
    
    def test_truncate_text_for_embedding_truncates_when_over_limit(self, mock_openai_class):
        """Kills mutation: not truncating when text exceeds limit."""
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        long_text = "x" * (DEFAULT_EMBEDDING_MAX_CHARS + 1000)
        truncated = service._truncate_text_for_embedding(long_text)
        
        # Should truncate
        assert len(truncated) <= DEFAULT_EMBEDDING_MAX_CHARS
        assert len(truncated) < len(long_text)
    
    def test_truncate_text_for_embedding_uses_character_limit(self, mock_openai_class):
        """Kills mutation: using wrong truncation method or limit."""
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        # Text exactly at char limit should be at or under limit after truncation check
        text_at_limit = "x" * DEFAULT_EMBEDDING_MAX_CHARS
        truncated = service._truncate_text_for_embedding(text_at_limit)
        
        # Should be at or under the limit (may be slightly under due to token estimation)
        assert len(truncated) <= DEFAULT_EMBEDDING_MAX_CHARS
    
    def test_generate_embedding_calls_truncation(self, mock_openai_class):
        """Kills mutation: not calling truncation before API call."""
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        long_text = "x" * (DEFAULT_EMBEDDING_MAX_CHARS + 1000)
        
        with patch.object(service, '_truncate_text_for_embedding', wraps=service._truncate_text_for_embedding) as mock_truncate:
            service.generate_embedding(long_text)
            
            # Should have called truncation
            mock_truncate.assert_called_once()
            
            # Verify API was called with truncated text
            call_args = service._client.embeddings.create.call_args
            input_text = call_args[1]["input"]
            assert len(input_text) <= DEFAULT_EMBEDDING_MAX_CHARS
    
    def test_generate_embedding_logs_warning_on_truncation(self, mock_openai_class):
        """Kills mutation: not logging warning when truncation occurs."""
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        long_text = "x" * (DEFAULT_EMBEDDING_MAX_CHARS + 1000)
        
        with patch('broca.memory.embeddings.logger') as mock_logger:
            service.generate_embedding(long_text)
            
            # Should have logged warning
            mock_logger.warning.assert_called()
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if call and len(call[0]) > 0]
            assert len(warning_calls) > 0
    
    def test_generate_embeddings_batch_truncates_each_text(self, mock_openai_class):
        """Kills mutation: not truncating individual texts in batch."""
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        texts = [
            "Short text",
            "x" * (DEFAULT_EMBEDDING_MAX_CHARS + 500),  # Should be truncated
            "Another short"
        ]
        
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),
            Mock(embedding=[0.2] * 1536),
            Mock(embedding=[0.3] * 1536)
        ]
        service._client.embeddings.create.return_value = mock_response
        
        service.generate_embeddings_batch(texts)
        
        # Verify long text was truncated
        call_args = service._client.embeddings.create.call_args
        input_texts = call_args[1]["input"]
        assert len(input_texts[0]) == len("Short text")  # Unchanged
        assert len(input_texts[1]) <= DEFAULT_EMBEDDING_MAX_CHARS  # Truncated
        assert len(input_texts[2]) == len("Another short")  # Unchanged
    
    def test_truncate_text_for_embedding_estimates_tokens_correctly(self, mock_openai_class):
        """Kills mutation: using wrong token estimation method."""
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        # Text that should be estimated as over limit
        long_text = "x" * (DEFAULT_EMBEDDING_MAX_CHARS + 100)
        estimated = estimate_tokens(long_text)
        
        # Should estimate over limit
        assert estimated > DEFAULT_EMBEDDING_MAX_TOKENS
        
        # Should truncate
        truncated = service._truncate_text_for_embedding(long_text)
        assert len(truncated) <= DEFAULT_EMBEDDING_MAX_CHARS










