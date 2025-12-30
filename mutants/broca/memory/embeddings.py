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
# Using ~3 chars per token (safer ratio) for approximately 24576 characters
# This accounts for variation in char-to-token ratios (typically 3-5 chars per token)
DEFAULT_EMBEDDING_MAX_TOKENS = 8192
DEFAULT_EMBEDDING_MAX_CHARS = DEFAULT_EMBEDDING_MAX_TOKENS * 3  # ~24576 chars (safer ratio)
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


class EmbeddingService:
    """
    Service for generating text embeddings using a separate embedding API.
    
    Uses the OpenAI-compatible API endpoint at /v1/embeddings.
    By default, uses OpenAI's embeddings API (separate from the chat LLM API).
    """
    
    def xǁEmbeddingServiceǁ__init____mutmut_orig(
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_1(
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
        if OpenAI is not None:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_2(
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
                None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_3(
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
                "XXopenai package is not installed. XX"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_4(
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
                "OPENAI PACKAGE IS NOT INSTALLED. "
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_5(
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
                "XXInstall it with: pip install openaiXX"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_6(
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
                "install it with: pip install openai"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_7(
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
                "INSTALL IT WITH: PIP INSTALL OPENAI"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_8(
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
        embedding_config = None
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_9(
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
        embedding_config = getattr(None, 'embedding', None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_10(
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
        embedding_config = getattr(config.memory, None, None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_11(
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
        embedding_config = getattr('embedding', None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_12(
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
        embedding_config = getattr(config.memory, None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_13(
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
        embedding_config = getattr(config.memory, 'embedding', )
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_14(
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
        embedding_config = getattr(config.memory, 'XXembeddingXX', None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_15(
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
        embedding_config = getattr(config.memory, 'EMBEDDING', None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_16(
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
            self.api_key = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_17(
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
        elif embedding_config or embedding_config.api_key:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_18(
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
            self.api_key = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_19(
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
                None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_20(
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
                "XXUsing LLM API key for embeddings (deprecated). XX"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_21(
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
                "using llm api key for embeddings (deprecated). "
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_22(
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
                "USING LLM API KEY FOR EMBEDDINGS (DEPRECATED). "
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_23(
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
                "XXPlease set OPENAI_API_KEY or EMBEDDING_API_KEY for embedding service.XX"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_24(
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
                "please set openai_api_key or embedding_api_key for embedding service."
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_25(
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
                "PLEASE SET OPENAI_API_KEY OR EMBEDDING_API_KEY FOR EMBEDDING SERVICE."
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_26(
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
            self.api_key = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_27(
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
            self.api_key = None
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_28(
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
            self.api_key = "XXXX"
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_29(
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
            self.base_url = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_30(
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
        elif embedding_config or embedding_config.api_base:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_31(
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
            self.base_url = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_32(
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
            if embedding_config.api_base == "https://api.openai.com/v1" or not api_key:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_33(
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
            if embedding_config.api_base != "https://api.openai.com/v1" and not api_key:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_34(
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
            if embedding_config.api_base == "XXhttps://api.openai.com/v1XX" and not api_key:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_35(
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
            if embedding_config.api_base == "HTTPS://API.OPENAI.COM/V1" and not api_key:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_36(
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
            if embedding_config.api_base == "https://api.openai.com/v1" and api_key:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_37(
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
                logger.info(None)
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_38(
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
                logger.info("XXUsing default OpenAI embeddings API (https://api.openai.com/v1)XX")
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_39(
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
                logger.info("using default openai embeddings api (https://api.openai.com/v1)")
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_40(
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
                logger.info("USING DEFAULT OPENAI EMBEDDINGS API (HTTPS://API.OPENAI.COM/V1)")
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_41(
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
                None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_42(
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
                "XXPlease configure BROCA_EMBEDDING_API_BASE or set embedding config.XX"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_43(
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
                "please configure broca_embedding_api_base or set embedding config."
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_44(
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
                "PLEASE CONFIGURE BROCA_EMBEDDING_API_BASE OR SET EMBEDDING CONFIG."
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_45(
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
            self.base_url = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_46(
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
            self.base_url = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_47(
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
            self.base_url = "XXhttps://api.openai.com/v1XX"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_48(
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
            self.base_url = "HTTPS://API.OPENAI.COM/V1"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_49(
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
            logger.info(None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_50(
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
            logger.info("XXUsing default OpenAI embeddings API (https://api.openai.com/v1)XX")
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_51(
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
            logger.info("using default openai embeddings api (https://api.openai.com/v1)")
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_52(
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
            logger.info("USING DEFAULT OPENAI EMBEDDINGS API (HTTPS://API.OPENAI.COM/V1)")
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_53(
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
            self.model = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_54(
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
        elif embedding_config or embedding_config.model:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_55(
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
            self.model = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_56(
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
            self.model = None
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_57(
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
            self.model = getattr(None, 'embedding_model', 'text-embedding-3-small')
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_58(
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
            self.model = getattr(config.memory, None, 'text-embedding-3-small')
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_59(
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
            self.model = getattr(config.memory, 'embedding_model', None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_60(
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
            self.model = getattr('embedding_model', 'text-embedding-3-small')
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_61(
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
            self.model = getattr(config.memory, 'text-embedding-3-small')
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_62(
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
            self.model = getattr(config.memory, 'embedding_model', )
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_63(
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
            self.model = getattr(config.memory, 'XXembedding_modelXX', 'text-embedding-3-small')
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_64(
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
            self.model = getattr(config.memory, 'EMBEDDING_MODEL', 'text-embedding-3-small')
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_65(
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
            self.model = getattr(config.memory, 'embedding_model', 'XXtext-embedding-3-smallXX')
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_66(
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
            self.model = getattr(config.memory, 'embedding_model', 'TEXT-EMBEDDING-3-SMALL')
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_67(
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
            self.dimension = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_68(
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
        elif embedding_config or embedding_config.dimension:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_69(
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
            self.dimension = None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_70(
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
            self.dimension = None
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_71(
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
            self.dimension = getattr(None, 'embedding_dimension', 1536)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_72(
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
            self.dimension = getattr(config.memory, None, 1536)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_73(
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
            self.dimension = getattr(config.memory, 'embedding_dimension', None)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_74(
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
            self.dimension = getattr('embedding_dimension', 1536)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_75(
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
            self.dimension = getattr(config.memory, 1536)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_76(
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
            self.dimension = getattr(config.memory, 'embedding_dimension', )
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_77(
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
            self.dimension = getattr(config.memory, 'XXembedding_dimensionXX', 1536)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_78(
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
            self.dimension = getattr(config.memory, 'EMBEDDING_DIMENSION', 1536)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_79(
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
            self.dimension = getattr(config.memory, 'embedding_dimension', 1537)
        
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_80(
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
        
        if self.api_key:
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_81(
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
                None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_82(
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
                "XXAPI key is required for embedding service. XX"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_83(
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
                "api key is required for embedding service. "
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_84(
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
                "API KEY IS REQUIRED FOR EMBEDDING SERVICE. "
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_85(
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
                "XXPlease set OPENAI_API_KEY or EMBEDDING_API_KEY environment variable, XX"
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_86(
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
                "please set openai_api_key or embedding_api_key environment variable, "
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_87(
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
                "PLEASE SET OPENAI_API_KEY OR EMBEDDING_API_KEY ENVIRONMENT VARIABLE, "
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_88(
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
        
        self._client = None
        
        # Maximum context length for embedding models
        # Most embedding models support 8192 tokens (~32768 chars)
        self.max_tokens = DEFAULT_EMBEDDING_MAX_TOKENS
        self.max_chars = DEFAULT_EMBEDDING_MAX_CHARS
        
        logger.info(
            f"Initialized EmbeddingService with model: {self.model}, "
            f"API: {self.base_url}, dimension: {self.dimension}, "
            f"max_tokens: {self.max_tokens}"
        )
    
    def xǁEmbeddingServiceǁ__init____mutmut_89(
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
            api_key=None,
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_90(
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
            base_url=None
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_91(
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_92(
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
    
    def xǁEmbeddingServiceǁ__init____mutmut_93(
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
        self.max_tokens = None
        self.max_chars = DEFAULT_EMBEDDING_MAX_CHARS
        
        logger.info(
            f"Initialized EmbeddingService with model: {self.model}, "
            f"API: {self.base_url}, dimension: {self.dimension}, "
            f"max_tokens: {self.max_tokens}"
        )
    
    def xǁEmbeddingServiceǁ__init____mutmut_94(
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
        self.max_chars = None
        
        logger.info(
            f"Initialized EmbeddingService with model: {self.model}, "
            f"API: {self.base_url}, dimension: {self.dimension}, "
            f"max_tokens: {self.max_tokens}"
        )
    
    def xǁEmbeddingServiceǁ__init____mutmut_95(
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
            None
        )
    
    xǁEmbeddingServiceǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁEmbeddingServiceǁ__init____mutmut_1': xǁEmbeddingServiceǁ__init____mutmut_1, 
        'xǁEmbeddingServiceǁ__init____mutmut_2': xǁEmbeddingServiceǁ__init____mutmut_2, 
        'xǁEmbeddingServiceǁ__init____mutmut_3': xǁEmbeddingServiceǁ__init____mutmut_3, 
        'xǁEmbeddingServiceǁ__init____mutmut_4': xǁEmbeddingServiceǁ__init____mutmut_4, 
        'xǁEmbeddingServiceǁ__init____mutmut_5': xǁEmbeddingServiceǁ__init____mutmut_5, 
        'xǁEmbeddingServiceǁ__init____mutmut_6': xǁEmbeddingServiceǁ__init____mutmut_6, 
        'xǁEmbeddingServiceǁ__init____mutmut_7': xǁEmbeddingServiceǁ__init____mutmut_7, 
        'xǁEmbeddingServiceǁ__init____mutmut_8': xǁEmbeddingServiceǁ__init____mutmut_8, 
        'xǁEmbeddingServiceǁ__init____mutmut_9': xǁEmbeddingServiceǁ__init____mutmut_9, 
        'xǁEmbeddingServiceǁ__init____mutmut_10': xǁEmbeddingServiceǁ__init____mutmut_10, 
        'xǁEmbeddingServiceǁ__init____mutmut_11': xǁEmbeddingServiceǁ__init____mutmut_11, 
        'xǁEmbeddingServiceǁ__init____mutmut_12': xǁEmbeddingServiceǁ__init____mutmut_12, 
        'xǁEmbeddingServiceǁ__init____mutmut_13': xǁEmbeddingServiceǁ__init____mutmut_13, 
        'xǁEmbeddingServiceǁ__init____mutmut_14': xǁEmbeddingServiceǁ__init____mutmut_14, 
        'xǁEmbeddingServiceǁ__init____mutmut_15': xǁEmbeddingServiceǁ__init____mutmut_15, 
        'xǁEmbeddingServiceǁ__init____mutmut_16': xǁEmbeddingServiceǁ__init____mutmut_16, 
        'xǁEmbeddingServiceǁ__init____mutmut_17': xǁEmbeddingServiceǁ__init____mutmut_17, 
        'xǁEmbeddingServiceǁ__init____mutmut_18': xǁEmbeddingServiceǁ__init____mutmut_18, 
        'xǁEmbeddingServiceǁ__init____mutmut_19': xǁEmbeddingServiceǁ__init____mutmut_19, 
        'xǁEmbeddingServiceǁ__init____mutmut_20': xǁEmbeddingServiceǁ__init____mutmut_20, 
        'xǁEmbeddingServiceǁ__init____mutmut_21': xǁEmbeddingServiceǁ__init____mutmut_21, 
        'xǁEmbeddingServiceǁ__init____mutmut_22': xǁEmbeddingServiceǁ__init____mutmut_22, 
        'xǁEmbeddingServiceǁ__init____mutmut_23': xǁEmbeddingServiceǁ__init____mutmut_23, 
        'xǁEmbeddingServiceǁ__init____mutmut_24': xǁEmbeddingServiceǁ__init____mutmut_24, 
        'xǁEmbeddingServiceǁ__init____mutmut_25': xǁEmbeddingServiceǁ__init____mutmut_25, 
        'xǁEmbeddingServiceǁ__init____mutmut_26': xǁEmbeddingServiceǁ__init____mutmut_26, 
        'xǁEmbeddingServiceǁ__init____mutmut_27': xǁEmbeddingServiceǁ__init____mutmut_27, 
        'xǁEmbeddingServiceǁ__init____mutmut_28': xǁEmbeddingServiceǁ__init____mutmut_28, 
        'xǁEmbeddingServiceǁ__init____mutmut_29': xǁEmbeddingServiceǁ__init____mutmut_29, 
        'xǁEmbeddingServiceǁ__init____mutmut_30': xǁEmbeddingServiceǁ__init____mutmut_30, 
        'xǁEmbeddingServiceǁ__init____mutmut_31': xǁEmbeddingServiceǁ__init____mutmut_31, 
        'xǁEmbeddingServiceǁ__init____mutmut_32': xǁEmbeddingServiceǁ__init____mutmut_32, 
        'xǁEmbeddingServiceǁ__init____mutmut_33': xǁEmbeddingServiceǁ__init____mutmut_33, 
        'xǁEmbeddingServiceǁ__init____mutmut_34': xǁEmbeddingServiceǁ__init____mutmut_34, 
        'xǁEmbeddingServiceǁ__init____mutmut_35': xǁEmbeddingServiceǁ__init____mutmut_35, 
        'xǁEmbeddingServiceǁ__init____mutmut_36': xǁEmbeddingServiceǁ__init____mutmut_36, 
        'xǁEmbeddingServiceǁ__init____mutmut_37': xǁEmbeddingServiceǁ__init____mutmut_37, 
        'xǁEmbeddingServiceǁ__init____mutmut_38': xǁEmbeddingServiceǁ__init____mutmut_38, 
        'xǁEmbeddingServiceǁ__init____mutmut_39': xǁEmbeddingServiceǁ__init____mutmut_39, 
        'xǁEmbeddingServiceǁ__init____mutmut_40': xǁEmbeddingServiceǁ__init____mutmut_40, 
        'xǁEmbeddingServiceǁ__init____mutmut_41': xǁEmbeddingServiceǁ__init____mutmut_41, 
        'xǁEmbeddingServiceǁ__init____mutmut_42': xǁEmbeddingServiceǁ__init____mutmut_42, 
        'xǁEmbeddingServiceǁ__init____mutmut_43': xǁEmbeddingServiceǁ__init____mutmut_43, 
        'xǁEmbeddingServiceǁ__init____mutmut_44': xǁEmbeddingServiceǁ__init____mutmut_44, 
        'xǁEmbeddingServiceǁ__init____mutmut_45': xǁEmbeddingServiceǁ__init____mutmut_45, 
        'xǁEmbeddingServiceǁ__init____mutmut_46': xǁEmbeddingServiceǁ__init____mutmut_46, 
        'xǁEmbeddingServiceǁ__init____mutmut_47': xǁEmbeddingServiceǁ__init____mutmut_47, 
        'xǁEmbeddingServiceǁ__init____mutmut_48': xǁEmbeddingServiceǁ__init____mutmut_48, 
        'xǁEmbeddingServiceǁ__init____mutmut_49': xǁEmbeddingServiceǁ__init____mutmut_49, 
        'xǁEmbeddingServiceǁ__init____mutmut_50': xǁEmbeddingServiceǁ__init____mutmut_50, 
        'xǁEmbeddingServiceǁ__init____mutmut_51': xǁEmbeddingServiceǁ__init____mutmut_51, 
        'xǁEmbeddingServiceǁ__init____mutmut_52': xǁEmbeddingServiceǁ__init____mutmut_52, 
        'xǁEmbeddingServiceǁ__init____mutmut_53': xǁEmbeddingServiceǁ__init____mutmut_53, 
        'xǁEmbeddingServiceǁ__init____mutmut_54': xǁEmbeddingServiceǁ__init____mutmut_54, 
        'xǁEmbeddingServiceǁ__init____mutmut_55': xǁEmbeddingServiceǁ__init____mutmut_55, 
        'xǁEmbeddingServiceǁ__init____mutmut_56': xǁEmbeddingServiceǁ__init____mutmut_56, 
        'xǁEmbeddingServiceǁ__init____mutmut_57': xǁEmbeddingServiceǁ__init____mutmut_57, 
        'xǁEmbeddingServiceǁ__init____mutmut_58': xǁEmbeddingServiceǁ__init____mutmut_58, 
        'xǁEmbeddingServiceǁ__init____mutmut_59': xǁEmbeddingServiceǁ__init____mutmut_59, 
        'xǁEmbeddingServiceǁ__init____mutmut_60': xǁEmbeddingServiceǁ__init____mutmut_60, 
        'xǁEmbeddingServiceǁ__init____mutmut_61': xǁEmbeddingServiceǁ__init____mutmut_61, 
        'xǁEmbeddingServiceǁ__init____mutmut_62': xǁEmbeddingServiceǁ__init____mutmut_62, 
        'xǁEmbeddingServiceǁ__init____mutmut_63': xǁEmbeddingServiceǁ__init____mutmut_63, 
        'xǁEmbeddingServiceǁ__init____mutmut_64': xǁEmbeddingServiceǁ__init____mutmut_64, 
        'xǁEmbeddingServiceǁ__init____mutmut_65': xǁEmbeddingServiceǁ__init____mutmut_65, 
        'xǁEmbeddingServiceǁ__init____mutmut_66': xǁEmbeddingServiceǁ__init____mutmut_66, 
        'xǁEmbeddingServiceǁ__init____mutmut_67': xǁEmbeddingServiceǁ__init____mutmut_67, 
        'xǁEmbeddingServiceǁ__init____mutmut_68': xǁEmbeddingServiceǁ__init____mutmut_68, 
        'xǁEmbeddingServiceǁ__init____mutmut_69': xǁEmbeddingServiceǁ__init____mutmut_69, 
        'xǁEmbeddingServiceǁ__init____mutmut_70': xǁEmbeddingServiceǁ__init____mutmut_70, 
        'xǁEmbeddingServiceǁ__init____mutmut_71': xǁEmbeddingServiceǁ__init____mutmut_71, 
        'xǁEmbeddingServiceǁ__init____mutmut_72': xǁEmbeddingServiceǁ__init____mutmut_72, 
        'xǁEmbeddingServiceǁ__init____mutmut_73': xǁEmbeddingServiceǁ__init____mutmut_73, 
        'xǁEmbeddingServiceǁ__init____mutmut_74': xǁEmbeddingServiceǁ__init____mutmut_74, 
        'xǁEmbeddingServiceǁ__init____mutmut_75': xǁEmbeddingServiceǁ__init____mutmut_75, 
        'xǁEmbeddingServiceǁ__init____mutmut_76': xǁEmbeddingServiceǁ__init____mutmut_76, 
        'xǁEmbeddingServiceǁ__init____mutmut_77': xǁEmbeddingServiceǁ__init____mutmut_77, 
        'xǁEmbeddingServiceǁ__init____mutmut_78': xǁEmbeddingServiceǁ__init____mutmut_78, 
        'xǁEmbeddingServiceǁ__init____mutmut_79': xǁEmbeddingServiceǁ__init____mutmut_79, 
        'xǁEmbeddingServiceǁ__init____mutmut_80': xǁEmbeddingServiceǁ__init____mutmut_80, 
        'xǁEmbeddingServiceǁ__init____mutmut_81': xǁEmbeddingServiceǁ__init____mutmut_81, 
        'xǁEmbeddingServiceǁ__init____mutmut_82': xǁEmbeddingServiceǁ__init____mutmut_82, 
        'xǁEmbeddingServiceǁ__init____mutmut_83': xǁEmbeddingServiceǁ__init____mutmut_83, 
        'xǁEmbeddingServiceǁ__init____mutmut_84': xǁEmbeddingServiceǁ__init____mutmut_84, 
        'xǁEmbeddingServiceǁ__init____mutmut_85': xǁEmbeddingServiceǁ__init____mutmut_85, 
        'xǁEmbeddingServiceǁ__init____mutmut_86': xǁEmbeddingServiceǁ__init____mutmut_86, 
        'xǁEmbeddingServiceǁ__init____mutmut_87': xǁEmbeddingServiceǁ__init____mutmut_87, 
        'xǁEmbeddingServiceǁ__init____mutmut_88': xǁEmbeddingServiceǁ__init____mutmut_88, 
        'xǁEmbeddingServiceǁ__init____mutmut_89': xǁEmbeddingServiceǁ__init____mutmut_89, 
        'xǁEmbeddingServiceǁ__init____mutmut_90': xǁEmbeddingServiceǁ__init____mutmut_90, 
        'xǁEmbeddingServiceǁ__init____mutmut_91': xǁEmbeddingServiceǁ__init____mutmut_91, 
        'xǁEmbeddingServiceǁ__init____mutmut_92': xǁEmbeddingServiceǁ__init____mutmut_92, 
        'xǁEmbeddingServiceǁ__init____mutmut_93': xǁEmbeddingServiceǁ__init____mutmut_93, 
        'xǁEmbeddingServiceǁ__init____mutmut_94': xǁEmbeddingServiceǁ__init____mutmut_94, 
        'xǁEmbeddingServiceǁ__init____mutmut_95': xǁEmbeddingServiceǁ__init____mutmut_95
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁEmbeddingServiceǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁEmbeddingServiceǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁEmbeddingServiceǁ__init____mutmut_orig)
    xǁEmbeddingServiceǁ__init____mutmut_orig.__name__ = 'xǁEmbeddingServiceǁ__init__'
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_orig(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_1(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = None
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_2(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(None)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_3(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = None  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_4(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 101  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_5(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = None
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_6(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens + safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_7(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens < target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_8(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = None
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_9(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = None
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_10(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = None
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_11(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 6
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_12(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(None):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_13(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = None
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_14(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(None)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_15(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after < target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_16(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                return
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_17(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = None
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_18(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(None)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_19(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) / 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_20(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 1.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_21(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars < 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_22(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 1:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_23(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = None
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_24(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 2
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_25(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = None
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_26(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = None
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_27(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(None)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_28(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            None,
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_29(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra=None
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_30(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_31(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_32(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "XXeventXX": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_33(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "EVENT": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_34(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "XXembedding_text_truncatedXX",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_35(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "EMBEDDING_TEXT_TRUNCATED",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_36(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "XXoriginal_lengthXX": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_37(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "ORIGINAL_LENGTH": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_38(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "XXtruncated_lengthXX": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_39(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "TRUNCATED_LENGTH": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_40(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "XXoriginal_estimated_tokensXX": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_41(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "ORIGINAL_ESTIMATED_TOKENS": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_42(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "XXfinal_estimated_tokensXX": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_43(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "FINAL_ESTIMATED_TOKENS": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_44(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "XXmax_tokensXX": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_45(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "MAX_TOKENS": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_46(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "XXtarget_max_tokensXX": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_47(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "TARGET_MAX_TOKENS": target_max_tokens,
                "iterations": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_48(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "XXiterationsXX": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_49(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "ITERATIONS": iteration + 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_50(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration - 1,
            }
        )
        
        return truncated_text
    
    def xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_51(self, text: str) -> str:
        """
        Truncate text to fit within embedding model token limits.
        
        Uses character-based approximation to estimate tokens and truncates
        if text exceeds the maximum allowed tokens. Re-validates tokens after
        truncation to ensure we stay under the limit with a safety margin.
        
        Args:
            text: Text to potentially truncate
            
        Returns:
            Truncated text if needed, otherwise original text
        """
        # Estimate tokens using character-based approximation
        estimated_tokens = estimate_tokens(text)
        
        # Safety margin to account for estimation errors
        safety_margin = 100  # tokens
        target_max_tokens = self.max_tokens - safety_margin
        
        if estimated_tokens <= target_max_tokens:
            return text
        
        # Text exceeds limit - truncate to max_chars
        original_length = len(text)
        truncated_text = text[:self.max_chars]
        
        # Re-validate tokens after truncation and truncate further if needed
        MAX_TRUNCATION_ITERATIONS = 5
        for iteration in range(MAX_TRUNCATION_ITERATIONS):
            estimated_tokens_after = estimate_tokens(truncated_text)
            if estimated_tokens_after <= target_max_tokens:
                break
            
            # Truncate further (reduce by 10% each iteration)
            target_chars = int(len(truncated_text) * 0.9)
            if target_chars <= 0:
                # Safety check to avoid empty text
                target_chars = 1
            truncated_text = text[:target_chars]
        
        # Final token check
        final_estimated_tokens = estimate_tokens(truncated_text)
        
        logger.warning(
            f"Text exceeds embedding token limit ({estimated_tokens} > {target_max_tokens} tokens). "
            f"Truncating from {original_length} to {len(truncated_text)} characters "
            f"(final estimated tokens: {final_estimated_tokens}).",
            extra={
                "event": "embedding_text_truncated",
                "original_length": original_length,
                "truncated_length": len(truncated_text),
                "original_estimated_tokens": estimated_tokens,
                "final_estimated_tokens": final_estimated_tokens,
                "max_tokens": self.max_tokens,
                "target_max_tokens": target_max_tokens,
                "iterations": iteration + 2,
            }
        )
        
        return truncated_text
    
    xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_1': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_1, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_2': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_2, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_3': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_3, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_4': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_4, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_5': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_5, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_6': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_6, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_7': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_7, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_8': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_8, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_9': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_9, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_10': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_10, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_11': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_11, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_12': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_12, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_13': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_13, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_14': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_14, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_15': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_15, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_16': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_16, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_17': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_17, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_18': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_18, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_19': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_19, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_20': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_20, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_21': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_21, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_22': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_22, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_23': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_23, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_24': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_24, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_25': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_25, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_26': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_26, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_27': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_27, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_28': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_28, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_29': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_29, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_30': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_30, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_31': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_31, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_32': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_32, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_33': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_33, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_34': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_34, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_35': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_35, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_36': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_36, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_37': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_37, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_38': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_38, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_39': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_39, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_40': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_40, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_41': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_41, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_42': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_42, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_43': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_43, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_44': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_44, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_45': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_45, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_46': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_46, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_47': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_47, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_48': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_48, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_49': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_49, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_50': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_50, 
        'xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_51': xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_51
    }
    
    def _truncate_text_for_embedding(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_orig"), object.__getattribute__(self, "xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _truncate_text_for_embedding.__signature__ = _mutmut_signature(xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_orig)
    xǁEmbeddingServiceǁ_truncate_text_for_embedding__mutmut_orig.__name__ = 'xǁEmbeddingServiceǁ_truncate_text_for_embedding'
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_orig(self, text: str) -> List[float]:
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_1(self, text: str) -> List[float]:
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
        if not text and not text.strip():
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_2(self, text: str) -> List[float]:
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
        if text or not text.strip():
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_3(self, text: str) -> List[float]:
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
        if not text or text.strip():
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_4(self, text: str) -> List[float]:
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
            raise ValueError(None)
        
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_5(self, text: str) -> List[float]:
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
            raise ValueError("XXText cannot be emptyXX")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_6(self, text: str) -> List[float]:
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
            raise ValueError("text cannot be empty")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_7(self, text: str) -> List[float]:
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
            raise ValueError("TEXT CANNOT BE EMPTY")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_8(self, text: str) -> List[float]:
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
        text_to_embed = None
        
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_9(self, text: str) -> List[float]:
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
        text_to_embed = self._truncate_text_for_embedding(None)
        
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_10(self, text: str) -> List[float]:
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
            logger.debug(None)
            
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
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_11(self, text: str) -> List[float]:
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
            
            response = None
            
            # Extract embedding vector
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_12(self, text: str) -> List[float]:
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
                model=None,
                input=text_to_embed
            )
            
            # Extract embedding vector
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_13(self, text: str) -> List[float]:
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
                input=None
            )
            
            # Extract embedding vector
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_14(self, text: str) -> List[float]:
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
                input=text_to_embed
            )
            
            # Extract embedding vector
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_15(self, text: str) -> List[float]:
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
                )
            
            # Extract embedding vector
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_16(self, text: str) -> List[float]:
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
            embedding = None
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_17(self, text: str) -> List[float]:
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
            embedding = response.data[1].embedding
            
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_18(self, text: str) -> List[float]:
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
            
            logger.debug(None)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_19(self, text: str) -> List[float]:
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
            logger.error(None, exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_20(self, text: str) -> List[float]:
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
            logger.error(f"Error generating embedding: {e}", exc_info=None)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_21(self, text: str) -> List[float]:
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
            logger.error(exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_22(self, text: str) -> List[float]:
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
            logger.error(f"Error generating embedding: {e}", )
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_23(self, text: str) -> List[float]:
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
            logger.error(f"Error generating embedding: {e}", exc_info=False)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embedding__mutmut_24(self, text: str) -> List[float]:
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
            raise RuntimeError(None) from e
    
    xǁEmbeddingServiceǁgenerate_embedding__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁEmbeddingServiceǁgenerate_embedding__mutmut_1': xǁEmbeddingServiceǁgenerate_embedding__mutmut_1, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_2': xǁEmbeddingServiceǁgenerate_embedding__mutmut_2, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_3': xǁEmbeddingServiceǁgenerate_embedding__mutmut_3, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_4': xǁEmbeddingServiceǁgenerate_embedding__mutmut_4, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_5': xǁEmbeddingServiceǁgenerate_embedding__mutmut_5, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_6': xǁEmbeddingServiceǁgenerate_embedding__mutmut_6, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_7': xǁEmbeddingServiceǁgenerate_embedding__mutmut_7, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_8': xǁEmbeddingServiceǁgenerate_embedding__mutmut_8, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_9': xǁEmbeddingServiceǁgenerate_embedding__mutmut_9, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_10': xǁEmbeddingServiceǁgenerate_embedding__mutmut_10, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_11': xǁEmbeddingServiceǁgenerate_embedding__mutmut_11, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_12': xǁEmbeddingServiceǁgenerate_embedding__mutmut_12, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_13': xǁEmbeddingServiceǁgenerate_embedding__mutmut_13, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_14': xǁEmbeddingServiceǁgenerate_embedding__mutmut_14, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_15': xǁEmbeddingServiceǁgenerate_embedding__mutmut_15, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_16': xǁEmbeddingServiceǁgenerate_embedding__mutmut_16, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_17': xǁEmbeddingServiceǁgenerate_embedding__mutmut_17, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_18': xǁEmbeddingServiceǁgenerate_embedding__mutmut_18, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_19': xǁEmbeddingServiceǁgenerate_embedding__mutmut_19, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_20': xǁEmbeddingServiceǁgenerate_embedding__mutmut_20, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_21': xǁEmbeddingServiceǁgenerate_embedding__mutmut_21, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_22': xǁEmbeddingServiceǁgenerate_embedding__mutmut_22, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_23': xǁEmbeddingServiceǁgenerate_embedding__mutmut_23, 
        'xǁEmbeddingServiceǁgenerate_embedding__mutmut_24': xǁEmbeddingServiceǁgenerate_embedding__mutmut_24
    }
    
    def generate_embedding(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁEmbeddingServiceǁgenerate_embedding__mutmut_orig"), object.__getattribute__(self, "xǁEmbeddingServiceǁgenerate_embedding__mutmut_mutants"), args, kwargs, self)
        return result 
    
    generate_embedding.__signature__ = _mutmut_signature(xǁEmbeddingServiceǁgenerate_embedding__mutmut_orig)
    xǁEmbeddingServiceǁgenerate_embedding__mutmut_orig.__name__ = 'xǁEmbeddingServiceǁgenerate_embedding'
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_orig(self, texts: List[str]) -> List[List[float]]:
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_1(self, texts: List[str]) -> List[List[float]]:
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
        if texts:
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_2(self, texts: List[str]) -> List[List[float]]:
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
            raise ValueError(None)
        
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_3(self, texts: List[str]) -> List[List[float]]:
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
            raise ValueError("XXTexts list cannot be emptyXX")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_4(self, texts: List[str]) -> List[List[float]]:
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
            raise ValueError("texts list cannot be empty")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_5(self, texts: List[str]) -> List[List[float]]:
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
            raise ValueError("TEXTS LIST CANNOT BE EMPTY")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_6(self, texts: List[str]) -> List[List[float]]:
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
        valid_texts = None
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_7(self, texts: List[str]) -> List[List[float]]:
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
        valid_texts = [self._truncate_text_for_embedding(None) for t in texts if t and t.strip()]
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_8(self, texts: List[str]) -> List[List[float]]:
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
        valid_texts = [self._truncate_text_for_embedding(t.strip()) for t in texts if t or t.strip()]
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_9(self, texts: List[str]) -> List[List[float]]:
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
        if valid_texts:
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_10(self, texts: List[str]) -> List[List[float]]:
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
            raise ValueError(None)
        
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_11(self, texts: List[str]) -> List[List[float]]:
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
            raise ValueError("XXNo valid texts providedXX")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_12(self, texts: List[str]) -> List[List[float]]:
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
            raise ValueError("no valid texts provided")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_13(self, texts: List[str]) -> List[List[float]]:
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
            raise ValueError("NO VALID TEXTS PROVIDED")
        
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_14(self, texts: List[str]) -> List[List[float]]:
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
            logger.debug(None)
            
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
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_15(self, texts: List[str]) -> List[List[float]]:
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
            
            response = None
            
            # Extract all embeddings
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_16(self, texts: List[str]) -> List[List[float]]:
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
                model=None,
                input=valid_texts
            )
            
            # Extract all embeddings
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_17(self, texts: List[str]) -> List[List[float]]:
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
                input=None
            )
            
            # Extract all embeddings
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_18(self, texts: List[str]) -> List[List[float]]:
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
                input=valid_texts
            )
            
            # Extract all embeddings
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_19(self, texts: List[str]) -> List[List[float]]:
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
                )
            
            # Extract all embeddings
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_20(self, texts: List[str]) -> List[List[float]]:
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
            embeddings = None
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_21(self, texts: List[str]) -> List[List[float]]:
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
            
            logger.debug(None)
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_22(self, texts: List[str]) -> List[List[float]]:
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
            logger.error(None, exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_23(self, texts: List[str]) -> List[List[float]]:
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
            logger.error(f"Error generating batch embeddings: {e}", exc_info=None)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_24(self, texts: List[str]) -> List[List[float]]:
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
            logger.error(exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_25(self, texts: List[str]) -> List[List[float]]:
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
            logger.error(f"Error generating batch embeddings: {e}", )
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_26(self, texts: List[str]) -> List[List[float]]:
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
            logger.error(f"Error generating batch embeddings: {e}", exc_info=False)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
    
    def xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_27(self, texts: List[str]) -> List[List[float]]:
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
            raise RuntimeError(None) from e
    
    xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_1': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_1, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_2': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_2, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_3': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_3, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_4': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_4, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_5': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_5, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_6': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_6, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_7': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_7, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_8': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_8, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_9': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_9, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_10': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_10, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_11': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_11, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_12': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_12, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_13': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_13, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_14': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_14, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_15': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_15, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_16': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_16, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_17': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_17, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_18': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_18, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_19': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_19, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_20': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_20, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_21': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_21, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_22': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_22, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_23': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_23, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_24': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_24, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_25': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_25, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_26': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_26, 
        'xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_27': xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_27
    }
    
    def generate_embeddings_batch(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_orig"), object.__getattribute__(self, "xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_mutants"), args, kwargs, self)
        return result 
    
    generate_embeddings_batch.__signature__ = _mutmut_signature(xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_orig)
    xǁEmbeddingServiceǁgenerate_embeddings_batch__mutmut_orig.__name__ = 'xǁEmbeddingServiceǁgenerate_embeddings_batch'

