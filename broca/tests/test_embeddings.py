"""
Tests for EmbeddingService.

Tests embedding generation using mocked OpenAI client.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest

from broca.memory.embeddings import EmbeddingService


class TestEmbeddingServiceInitialization:
    """Test EmbeddingService initialization."""
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_init_with_parameters(self, mock_openai_class):
        """
        Test initialization with explicit parameters.
        
        Rationale: Ensures service can be configured with custom parameters.
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(
            api_key="test-key",
            base_url="https://test.api.com/v1",
            model="test-model",
            dimension=512
        )
        
        assert service.api_key == "test-key"
        assert service.base_url == "https://test.api.com/v1"
        assert service.model == "test-model"
        assert service.dimension == 512
        mock_openai_class.assert_called_once_with(
            api_key="test-key",
            base_url="https://test.api.com/v1"
        )
    
    @patch('broca.memory.embeddings.OpenAI')
    @patch('broca.memory.embeddings.config')
    def test_init_with_embedding_config(self, mock_config, mock_openai_class):
        """
        Test initialization with new embedding config structure.
        
        Rationale: Ensures service uses new embedding config when available.
        """
        # Create mock embedding config
        mock_embedding_config = Mock()
        mock_embedding_config.api_key = "embedding-key"
        mock_embedding_config.api_base = "https://api.openai.com/v1"
        mock_embedding_config.model = "text-embedding-3-small"
        mock_embedding_config.dimension = 1536
        
        mock_config.memory.embedding = mock_embedding_config
        mock_config.llm.api_key = "llm-key"  # Should not be used
        mock_config.llm.api_base = "https://llm.api.com/v1"  # Should not be used
        
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService()
        
        assert service.api_key == "embedding-key"
        assert service.base_url == "https://api.openai.com/v1"
        assert service.model == "text-embedding-3-small"
        assert service.dimension == 1536
    
    @patch('broca.memory.embeddings.OpenAI')
    @patch('broca.memory.embeddings.config')
    def test_init_with_backward_compatibility(self, mock_config, mock_openai_class):
        """
        Test initialization with backward compatibility (old config paths).
        
        Rationale: Ensures service falls back to old config paths for compatibility.
        """
        # Simulate old config structure (no embedding config)
        mock_config.memory.embedding = None
        mock_config.llm.api_key = "llm-key"
        mock_config.llm.api_base = "https://llm.api.com/v1"
        mock_config.memory.embedding_model = "old-model"
        mock_config.memory.embedding_dimension = 512
        
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService()
        
        # Should use LLM config with deprecation warning
        assert service.api_key == "llm-key"
        assert service.base_url == "https://llm.api.com/v1"
        assert service.model == "old-model"
        assert service.dimension == 512
    
    def test_init_missing_openai_package(self):
        """
        Test that missing openai package raises error.
        
        Rationale: Ensures clear error when required package is not installed.
        """
        with patch('broca.memory.embeddings.OpenAI', None):
            with pytest.raises(ValueError, match="openai package is not installed"):
                EmbeddingService(api_key="test-key")
    
    @patch('broca.memory.embeddings.OpenAI')
    @patch('broca.memory.embeddings.config')
    def test_init_missing_api_key(self, mock_config, mock_openai_class):
        """
        Test that missing API key raises error.
        
        Rationale: Ensures API key is required for service initialization.
        """
        # Create mock embedding config with empty key
        mock_embedding_config = Mock()
        mock_embedding_config.api_key = ""
        mock_embedding_config.api_base = "https://api.openai.com/v1"
        mock_embedding_config.model = "text-embedding-3-small"
        mock_embedding_config.dimension = 1536
        
        mock_config.memory.embedding = mock_embedding_config
        mock_config.llm.api_key = ""  # Also empty for backward compat
        
        with pytest.raises(ValueError, match="API key is required"):
            EmbeddingService()
    
    @patch('broca.memory.embeddings.OpenAI')
    @patch('broca.memory.embeddings.config')
    def test_init_with_default_openai_config(self, mock_config, mock_openai_class):
        """
        Test initialization with default OpenAI configuration.
        
        Rationale: Ensures default OpenAI config is used when no custom config provided.
        """
        # Create mock embedding config with OpenAI defaults
        mock_embedding_config = Mock()
        mock_embedding_config.api_key = "openai-key"
        mock_embedding_config.api_base = "https://api.openai.com/v1"
        mock_embedding_config.model = "text-embedding-3-small"
        mock_embedding_config.dimension = 1536
        
        mock_config.memory.embedding = mock_embedding_config
        
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService()
        
        assert service.api_key == "openai-key"
        assert service.base_url == "https://api.openai.com/v1"
        assert service.model == "text-embedding-3-small"
        assert service.dimension == 1536


class TestEmbeddingServiceGenerateEmbedding:
    """Test embedding generation."""
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_success(self, mock_openai_class):
        """
        Test successful embedding generation.
        
        Rationale: Ensures embeddings are generated correctly from API.
        """
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]  # 1536-dim
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key", dimension=1536)
        embedding = service.generate_embedding("Test text")
        
        assert len(embedding) == 1536
        assert embedding[0] == 0.1
        mock_client.embeddings.create.assert_called_once_with(
            model=service.model,
            input="Test text"
        )
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_empty_text(self, mock_openai_class):
        """
        Test that empty text raises error.
        
        Rationale: Ensures text validation works.
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.generate_embedding("")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.generate_embedding("   ")
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_strips_whitespace(self, mock_openai_class):
        """
        Test that text is stripped before sending to API.
        
        Rationale: Ensures whitespace is handled correctly.
        """
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key")
        service.generate_embedding("  Test text  ")
        
        mock_client.embeddings.create.assert_called_once_with(
            model=service.model,
            input="Test text"
        )
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_api_error(self, mock_openai_class):
        """
        Test that API errors are handled gracefully.
        
        Rationale: Ensures errors are properly raised and logged.
        """
        mock_client = Mock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key")
        
        with pytest.raises(RuntimeError, match="Failed to generate embedding"):
            service.generate_embedding("Test text")


class TestEmbeddingServiceBatchGeneration:
    """Test batch embedding generation."""
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embeddings_batch_success(self, mock_openai_class):
        """
        Test successful batch embedding generation.
        
        Rationale: Ensures multiple embeddings can be generated efficiently.
        """
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),
            Mock(embedding=[0.2] * 1536),
            Mock(embedding=[0.3] * 1536)
        ]
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key", dimension=1536)
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = service.generate_embeddings_batch(texts)
        
        assert len(embeddings) == 3
        assert len(embeddings[0]) == 1536
        mock_client.embeddings.create.assert_called_once_with(
            model=service.model,
            input=texts
        )
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embeddings_batch_empty_list(self, mock_openai_class):
        """
        Test that empty list raises error.
        
        Rationale: Ensures batch operation validates input.
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key")
        
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            service.generate_embeddings_batch([])
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embeddings_batch_filters_empty(self, mock_openai_class):
        """
        Test that empty texts are filtered from batch.
        
        Rationale: Ensures batch operation handles empty strings gracefully.
        """
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key", dimension=1536)
        texts = ["Valid text", "", "   ", "Another valid"]
        embeddings = service.generate_embeddings_batch(texts)
        
        # Should only process valid texts
        assert len(embeddings) == 1
        call_args = mock_client.embeddings.create.call_args
        assert len(call_args[1]["input"]) == 2  # Only valid texts
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embeddings_batch_all_empty(self, mock_openai_class):
        """
        Test that all empty texts raises error.
        
        Rationale: Ensures batch operation fails when no valid texts.
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key")
        
        with pytest.raises(ValueError, match="No valid texts provided"):
            service.generate_embeddings_batch(["", "   ", "\t"])


class TestEmbeddingServiceTruncation:
    """Test embedding text truncation for context length limits."""
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_truncates_long_text(self, mock_openai_class):
        """
        Test that text exceeding token limit is truncated before API call.
        
        Rationale: Ensures embeddings can be generated for long texts by truncating
        to fit within model's context length (8192 tokens ~32768 chars).
        """
        from broca.summarization.token_estimator import estimate_tokens
        from broca.memory.embeddings import DEFAULT_EMBEDDING_MAX_CHARS
        
        # Create text that exceeds the limit (35000 chars > 32768 max)
        long_text = "x" * 35000
        estimated_tokens = estimate_tokens(long_text)
        assert estimated_tokens > 8192  # Should exceed limit
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        # Should not raise, but truncate and log warning
        with patch('broca.memory.embeddings.logger') as mock_logger:
            embedding = service.generate_embedding(long_text)
            
            # Verify truncation occurred - API should be called with truncated text
            call_args = mock_client.embeddings.create.call_args
            input_text = call_args[1]["input"]
            assert len(input_text) <= DEFAULT_EMBEDDING_MAX_CHARS
            assert len(input_text) < len(long_text)
            
            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args
            warning_msg = str(warning_call)
            assert "exceeds embedding token limit" in warning_msg or "Truncating" in warning_msg
            
            # Embedding should still be generated successfully
            assert len(embedding) == 1536
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_does_not_truncate_short_text(self, mock_openai_class):
        """
        Test that text within token limit is not truncated.
        
        Rationale: Ensures normal-sized texts are processed without truncation.
        """
        # Create text well under the limit
        short_text = "This is a short text for embedding."
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        with patch('broca.memory.embeddings.logger') as mock_logger:
            embedding = service.generate_embedding(short_text)
            
            # Verify original text was sent to API
            call_args = mock_client.embeddings.create.call_args
            input_text = call_args[1]["input"]
            assert input_text == short_text
            
            # Verify no warning was logged
            mock_logger.warning.assert_not_called()
            
            assert len(embedding) == 1536
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_exact_limit_boundary(self, mock_openai_class):
        """
        Test text at exactly the token limit boundary.
        
        Rationale: Ensures boundary conditions are handled correctly.
        """
        from broca.memory.embeddings import DEFAULT_EMBEDDING_MAX_CHARS
        
        # Create text exactly at the character limit
        text_at_limit = "x" * DEFAULT_EMBEDDING_MAX_CHARS
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        with patch('broca.memory.embeddings.logger') as mock_logger:
            embedding = service.generate_embedding(text_at_limit)
            
            # Text at limit should be sent as-is (estimate_tokens may be slightly under)
            call_args = mock_client.embeddings.create.call_args
            input_text = call_args[1]["input"]
            # Should be at or under the limit
            assert len(input_text) <= DEFAULT_EMBEDDING_MAX_CHARS
            
            assert len(embedding) == 1536
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_just_over_limit(self, mock_openai_class):
        """
        Test text just over the token limit.
        
        Rationale: Ensures text slightly exceeding limit is properly truncated.
        """
        from broca.memory.embeddings import DEFAULT_EMBEDDING_MAX_CHARS
        
        # Create text just over the limit (100 chars over)
        text_just_over = "x" * (DEFAULT_EMBEDDING_MAX_CHARS + 100)
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        with patch('broca.memory.embeddings.logger') as mock_logger:
            embedding = service.generate_embedding(text_just_over)
            
            # Should be truncated to max_chars
            call_args = mock_client.embeddings.create.call_args
            input_text = call_args[1]["input"]
            assert len(input_text) == DEFAULT_EMBEDDING_MAX_CHARS
            assert len(input_text) < len(text_just_over)
            
            # Warning should be logged
            mock_logger.warning.assert_called_once()
            
            assert len(embedding) == 1536
    
    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embeddings_batch_truncates_long_texts(self, mock_openai_class):
        """
        Test that batch embedding truncates individual texts if needed.
        
        Rationale: Ensures batch operation also handles truncation correctly.
        """
        from broca.memory.embeddings import DEFAULT_EMBEDDING_MAX_CHARS
        
        # Mix of short and long texts
        texts = [
            "Short text",
            "x" * 35000,  # Exceeds limit
            "Another short text",
            "y" * (DEFAULT_EMBEDDING_MAX_CHARS + 50)  # Just over limit
        ]
        
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),
            Mock(embedding=[0.2] * 1536),
            Mock(embedding=[0.3] * 1536),
            Mock(embedding=[0.4] * 1536)
        ]
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = EmbeddingService(api_key="test-key", dimension=1536)
        
        with patch('broca.memory.embeddings.logger') as mock_logger:
            embeddings = service.generate_embeddings_batch(texts)
            
            # Verify all texts were processed (2 should be truncated)
            call_args = mock_client.embeddings.create.call_args
            input_texts = call_args[1]["input"]
            assert len(input_texts) == 4
            
            # Verify long texts were truncated
            assert len(input_texts[0]) == len("Short text")  # Short text unchanged
            assert len(input_texts[1]) <= DEFAULT_EMBEDDING_MAX_CHARS  # Long text truncated
            assert len(input_texts[2]) == len("Another short text")  # Short text unchanged
            assert len(input_texts[3]) == DEFAULT_EMBEDDING_MAX_CHARS  # Just over limit truncated
            
            # Should have logged warnings for truncated texts
            assert mock_logger.warning.call_count >= 2  # At least 2 warnings for 2 long texts
            
            assert len(embeddings) == 4

    @patch('broca.memory.embeddings.OpenAI')
    def test_generate_embedding_retries_on_overlength_error(self, mock_openai_class):
        """
        Regression: if the embedding API returns a maximum-context-length error, we retry once
        with more aggressive truncation instead of failing immediately.
        """
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]

        mock_client = Mock()

        overlength_exc = Exception(
            "Error code: 400 - {'error': {'message': \"This model's maximum context length is 8192 tokens, "
            "however you requested 9526 tokens (9526 in your prompt; 0 for the completion).\"}}"
        )
        mock_client.embeddings.create.side_effect = [overlength_exc, mock_response]
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(api_key="test-key", dimension=1536)
        # Use a long text to ensure we trigger truncation paths
        text = "x" * 30000

        embedding = service.generate_embedding(text)
        assert len(embedding) == 1536
        assert mock_client.embeddings.create.call_count == 2

