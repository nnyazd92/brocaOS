"""
Embedding service for generating text embeddings using a separate embedding API.

Uses the OpenAI-compatible API via the openai package to generate embeddings.
By default, uses OpenAI's embeddings API (separate from the chat LLM API).
"""

from __future__ import annotations

import os
import logging
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

from ..config import config
from ..summarization.token_estimator import estimate_tokens

logger = logging.getLogger(__name__)

# Maximum tokens for embedding models (OpenAI embeddings typically support 8192 tokens)
# Using ~4 chars per token, that's approximately 32768 characters
DEFAULT_EMBEDDING_MAX_TOKENS = 8192
DEFAULT_EMBEDDING_MAX_CHARS = DEFAULT_EMBEDDING_MAX_TOKENS * 4  # ~32768 chars


class EmbeddingService:
    """
    Service for generating text embeddings using a separate embedding API.
    
    Uses the OpenAI-compatible API endpoint at /v1/embeddings.
    By default, uses OpenAI's embeddings API (separate from the chat LLM API).
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[int] = None
    ) -> None:
        """
        Initialize the embedding service.
        
        Args:
            api_key: Embedding API key (defaults to config.memory.embedding.api_key)
            base_url: API base URL (defaults to config.memory.embedding.api_base)
            model: Embedding model name (defaults to config.memory.embedding.model)
            dimension: Embedding dimension (defaults to config.memory.embedding.dimension)
        """
        if OpenAI is None:
            raise ValueError(
                "openai package is not installed. "
                "Install it with: pip install openai"
            )
        
        # Use new embedding config if available, with backward compatibility
        embedding_config = getattr(config.memory, 'embedding', None)
        
        # Determine API key with backward compatibility
        if api_key:
            self.api_key = api_key
        elif embedding_config and embedding_config.api_key:
            self.api_key = embedding_config.api_key
        elif config.llm.api_key:
            # Backward compatibility: fall back to LLM API key
            logger.warning(
                "Using LLM API key for embeddings (deprecated). "
                "Please set OPENAI_API_KEY or EMBEDDING_API_KEY for embedding service."
            )
            self.api_key = config.llm.api_key
        else:
            self.api_key = ""
        
        # Determine API base URL with backward compatibility
        if base_url:
            self.base_url = base_url
        elif embedding_config and embedding_config.api_base:
            self.base_url = embedding_config.api_base
            # Log if using default OpenAI endpoint
            if embedding_config.api_base == "https://api.openai.com/v1" and not api_key:
                logger.info("Using default OpenAI embeddings API (https://api.openai.com/v1)")
        elif config.llm.api_base:
            # Backward compatibility: fall back to LLM API base
            logger.warning(
                f"Using LLM API base ({config.llm.api_base}) for embeddings (deprecated). "
                "Please configure BROCA_EMBEDDING_API_BASE or set embedding config."
            )
            self.base_url = config.llm.api_base
        else:
            # Final fallback to OpenAI default
            self.base_url = "https://api.openai.com/v1"
            logger.info("Using default OpenAI embeddings API (https://api.openai.com/v1)")
        
        # Determine model with backward compatibility
        if model:
            self.model = model
        elif embedding_config and embedding_config.model:
            self.model = embedding_config.model
        else:
            # Fall back to old config path
            self.model = getattr(config.memory, 'embedding_model', 'text-embedding-3-small')
        
        # Determine dimension with backward compatibility
        if dimension:
            self.dimension = dimension
        elif embedding_config and embedding_config.dimension:
            self.dimension = embedding_config.dimension
        else:
            # Fall back to old config path
            self.dimension = getattr(config.memory, 'embedding_dimension', 1536)
        
        if not self.api_key:
            raise ValueError(
                "API key is required for embedding service. "
                "Please set OPENAI_API_KEY or EMBEDDING_API_KEY environment variable, "
                f"or configure embedding API key. Using API: {self.base_url}"
            )
        
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Maximum context length for embedding models
        # Most embedding models support 8192 tokens (~32768 chars)
        self.max_tokens = DEFAULT_EMBEDDING_MAX_TOKENS
        self.max_chars = DEFAULT_EMBEDDING_MAX_CHARS
        
        logger.info(
            f"Initialized EmbeddingService with model: {self.model}, "
            f"API: {self.base_url}, dimension: {self.dimension}, "
            f"max_tokens: {self.max_tokens}"
        )
    
    def _truncate_text_for_embedding(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        if estimated_tokens <= self.max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        # Use character-based truncation for simplicity and performance
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {self.max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters.",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "estimated_tokens": estimated_tokens,
                "max_tokens": self.max_tokens,
            }
        )
        
        return truncated_text
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If text is empty
            RuntimeError: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Truncate text if it exceeds token limits
        text_to_embed = self._truncate_text_for_embedding(text.strip())
        
        try:
            logger.debug(f"Generating embedding for text (length: {len(text_to_embed)})")
            
            response = self._client.embeddings.create(
                model=self.model,
                input=text_to_embed
            )
            
            # Extract embedding vector
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
            
        Raises:
            ValueError: If texts list is empty
            RuntimeError: If API call fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # Filter out empty texts and truncate each if needed
        valid_texts = [self._truncate_text_for_embedding(t.strip()) for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("No valid texts provided")
        
        try:
            logger.debug(f"Generating embeddings for {len(valid_texts)} texts")
            
            response = self._client.embeddings.create(
                model=self.model,
                input=valid_texts
            )
            
            # Extract all embeddings
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e

