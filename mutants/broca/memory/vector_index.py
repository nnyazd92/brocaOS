"""
Vector index for memory similarity search using FAISS.

Handles efficient vector similarity search for memory retrieval.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore

from .storage import MemoryStorage

logger = logging.getLogger(__name__)
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


class VectorIndex:
    """
    FAISS-based vector index for memory similarity search.
    
    Uses cosine similarity (via inner product on normalized vectors)
    for finding similar memories.
    """
    
    def xǁVectorIndexǁ__init____mutmut_orig(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_1(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is not None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_2(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                None
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_3(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "XXfaiss-cpu package is not installed. XX"
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_4(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "FAISS-CPU PACKAGE IS NOT INSTALLED. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_5(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "XXInstall it with: pip install faiss-cpuXX"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_6(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_7(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "INSTALL IT WITH: PIP INSTALL FAISS-CPU"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_8(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = None
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_9(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_10(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(None) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_11(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = None
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_12(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(None)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_13(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = None
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_14(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = None
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_15(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 1
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_16(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path or self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_17(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(None)
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_18(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(None))
        
        logger.info(f"Initialized VectorIndex with dimension {dimension}")
    
    def xǁVectorIndexǁ__init____mutmut_19(self, dimension: int, index_path: Optional[str] = None) -> None:
        """
        Initialize vector index.
        
        Args:
            dimension: Dimension of embedding vectors
            index_path: Optional path to save/load index from disk
        """
        if faiss is None:
            raise ValueError(
                "faiss-cpu package is not installed. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        # Vectors will be normalized before adding/searching
        self.index = faiss.IndexFlatIP(dimension)
        
        # Map FAISS IDs to memory IDs
        self.id_map: Dict[int, int] = {}
        self.faiss_id_counter = 0
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load_index(str(self.index_path))
        
        logger.info(None)
    
    xǁVectorIndexǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁ__init____mutmut_1': xǁVectorIndexǁ__init____mutmut_1, 
        'xǁVectorIndexǁ__init____mutmut_2': xǁVectorIndexǁ__init____mutmut_2, 
        'xǁVectorIndexǁ__init____mutmut_3': xǁVectorIndexǁ__init____mutmut_3, 
        'xǁVectorIndexǁ__init____mutmut_4': xǁVectorIndexǁ__init____mutmut_4, 
        'xǁVectorIndexǁ__init____mutmut_5': xǁVectorIndexǁ__init____mutmut_5, 
        'xǁVectorIndexǁ__init____mutmut_6': xǁVectorIndexǁ__init____mutmut_6, 
        'xǁVectorIndexǁ__init____mutmut_7': xǁVectorIndexǁ__init____mutmut_7, 
        'xǁVectorIndexǁ__init____mutmut_8': xǁVectorIndexǁ__init____mutmut_8, 
        'xǁVectorIndexǁ__init____mutmut_9': xǁVectorIndexǁ__init____mutmut_9, 
        'xǁVectorIndexǁ__init____mutmut_10': xǁVectorIndexǁ__init____mutmut_10, 
        'xǁVectorIndexǁ__init____mutmut_11': xǁVectorIndexǁ__init____mutmut_11, 
        'xǁVectorIndexǁ__init____mutmut_12': xǁVectorIndexǁ__init____mutmut_12, 
        'xǁVectorIndexǁ__init____mutmut_13': xǁVectorIndexǁ__init____mutmut_13, 
        'xǁVectorIndexǁ__init____mutmut_14': xǁVectorIndexǁ__init____mutmut_14, 
        'xǁVectorIndexǁ__init____mutmut_15': xǁVectorIndexǁ__init____mutmut_15, 
        'xǁVectorIndexǁ__init____mutmut_16': xǁVectorIndexǁ__init____mutmut_16, 
        'xǁVectorIndexǁ__init____mutmut_17': xǁVectorIndexǁ__init____mutmut_17, 
        'xǁVectorIndexǁ__init____mutmut_18': xǁVectorIndexǁ__init____mutmut_18, 
        'xǁVectorIndexǁ__init____mutmut_19': xǁVectorIndexǁ__init____mutmut_19
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁVectorIndexǁ__init____mutmut_orig)
    xǁVectorIndexǁ__init____mutmut_orig.__name__ = 'xǁVectorIndexǁ__init__'
    
    def xǁVectorIndexǁadd_vector__mutmut_orig(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_1(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) == self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_2(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                None
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_3(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = None
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_4(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array(None, dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_5(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=None)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_6(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array(dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_7(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], )
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_8(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(None)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_9(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = None
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_10(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(None)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_11(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = None
        self.faiss_id_counter += 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_12(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter = 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_13(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter -= 1
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_14(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 2
        
        logger.debug(f"Added vector for memory {memory_id} to index")
    
    def xǁVectorIndexǁadd_vector__mutmut_15(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a vector to the index.
        
        Args:
            memory_id: Memory record ID
            embedding: Embedding vector
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize vector for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        faiss_id = self.faiss_id_counter
        self.index.add(embedding_array)
        self.id_map[faiss_id] = memory_id
        self.faiss_id_counter += 1
        
        logger.debug(None)
    
    xǁVectorIndexǁadd_vector__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁadd_vector__mutmut_1': xǁVectorIndexǁadd_vector__mutmut_1, 
        'xǁVectorIndexǁadd_vector__mutmut_2': xǁVectorIndexǁadd_vector__mutmut_2, 
        'xǁVectorIndexǁadd_vector__mutmut_3': xǁVectorIndexǁadd_vector__mutmut_3, 
        'xǁVectorIndexǁadd_vector__mutmut_4': xǁVectorIndexǁadd_vector__mutmut_4, 
        'xǁVectorIndexǁadd_vector__mutmut_5': xǁVectorIndexǁadd_vector__mutmut_5, 
        'xǁVectorIndexǁadd_vector__mutmut_6': xǁVectorIndexǁadd_vector__mutmut_6, 
        'xǁVectorIndexǁadd_vector__mutmut_7': xǁVectorIndexǁadd_vector__mutmut_7, 
        'xǁVectorIndexǁadd_vector__mutmut_8': xǁVectorIndexǁadd_vector__mutmut_8, 
        'xǁVectorIndexǁadd_vector__mutmut_9': xǁVectorIndexǁadd_vector__mutmut_9, 
        'xǁVectorIndexǁadd_vector__mutmut_10': xǁVectorIndexǁadd_vector__mutmut_10, 
        'xǁVectorIndexǁadd_vector__mutmut_11': xǁVectorIndexǁadd_vector__mutmut_11, 
        'xǁVectorIndexǁadd_vector__mutmut_12': xǁVectorIndexǁadd_vector__mutmut_12, 
        'xǁVectorIndexǁadd_vector__mutmut_13': xǁVectorIndexǁadd_vector__mutmut_13, 
        'xǁVectorIndexǁadd_vector__mutmut_14': xǁVectorIndexǁadd_vector__mutmut_14, 
        'xǁVectorIndexǁadd_vector__mutmut_15': xǁVectorIndexǁadd_vector__mutmut_15
    }
    
    def add_vector(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁadd_vector__mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁadd_vector__mutmut_mutants"), args, kwargs, self)
        return result 
    
    add_vector.__signature__ = _mutmut_signature(xǁVectorIndexǁadd_vector__mutmut_orig)
    xǁVectorIndexǁadd_vector__mutmut_orig.__name__ = 'xǁVectorIndexǁadd_vector'
    
    def xǁVectorIndexǁsearch_similar__mutmut_orig(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_1(
        self,
        query_embedding: List[float],
        k: int = 6
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_2(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal != 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_3(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 1:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_4(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) == self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_5(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                None
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_6(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = None
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_7(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array(None, dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_8(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=None)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_9(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array(dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_10(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], )
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_11(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(None)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_12(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = None
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_13(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(None, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_14(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, None)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_15(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_16(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, )
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_17(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = None
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_18(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(None, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_19(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, None)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_20(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_21(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, )
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_22(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = None
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_23(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(None, distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_24(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], None):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_25(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_26(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], ):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_27(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[1], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_28(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[1]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_29(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id not in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_30(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = None
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_31(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = None
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_32(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(None)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_33(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append(None)
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_34(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=None, reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_35(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=None)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_36(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_37(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], )
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_38(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: None, reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_39(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[2], reverse=True)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_40(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=False)
        
        logger.debug(f"Found {len(results)} similar vectors")
        return results
    
    def xǁVectorIndexǁsearch_similar__mutmut_41(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert FAISS IDs to memory IDs and return with similarity scores
        results = []
        for faiss_id, distance in zip(indices[0], distances[0]):
            if faiss_id in self.id_map:
                memory_id = self.id_map[faiss_id]
                # Distance is inner product (cosine similarity for normalized vectors)
                similarity = float(distance)
                results.append((memory_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(None)
        return results
    
    xǁVectorIndexǁsearch_similar__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁsearch_similar__mutmut_1': xǁVectorIndexǁsearch_similar__mutmut_1, 
        'xǁVectorIndexǁsearch_similar__mutmut_2': xǁVectorIndexǁsearch_similar__mutmut_2, 
        'xǁVectorIndexǁsearch_similar__mutmut_3': xǁVectorIndexǁsearch_similar__mutmut_3, 
        'xǁVectorIndexǁsearch_similar__mutmut_4': xǁVectorIndexǁsearch_similar__mutmut_4, 
        'xǁVectorIndexǁsearch_similar__mutmut_5': xǁVectorIndexǁsearch_similar__mutmut_5, 
        'xǁVectorIndexǁsearch_similar__mutmut_6': xǁVectorIndexǁsearch_similar__mutmut_6, 
        'xǁVectorIndexǁsearch_similar__mutmut_7': xǁVectorIndexǁsearch_similar__mutmut_7, 
        'xǁVectorIndexǁsearch_similar__mutmut_8': xǁVectorIndexǁsearch_similar__mutmut_8, 
        'xǁVectorIndexǁsearch_similar__mutmut_9': xǁVectorIndexǁsearch_similar__mutmut_9, 
        'xǁVectorIndexǁsearch_similar__mutmut_10': xǁVectorIndexǁsearch_similar__mutmut_10, 
        'xǁVectorIndexǁsearch_similar__mutmut_11': xǁVectorIndexǁsearch_similar__mutmut_11, 
        'xǁVectorIndexǁsearch_similar__mutmut_12': xǁVectorIndexǁsearch_similar__mutmut_12, 
        'xǁVectorIndexǁsearch_similar__mutmut_13': xǁVectorIndexǁsearch_similar__mutmut_13, 
        'xǁVectorIndexǁsearch_similar__mutmut_14': xǁVectorIndexǁsearch_similar__mutmut_14, 
        'xǁVectorIndexǁsearch_similar__mutmut_15': xǁVectorIndexǁsearch_similar__mutmut_15, 
        'xǁVectorIndexǁsearch_similar__mutmut_16': xǁVectorIndexǁsearch_similar__mutmut_16, 
        'xǁVectorIndexǁsearch_similar__mutmut_17': xǁVectorIndexǁsearch_similar__mutmut_17, 
        'xǁVectorIndexǁsearch_similar__mutmut_18': xǁVectorIndexǁsearch_similar__mutmut_18, 
        'xǁVectorIndexǁsearch_similar__mutmut_19': xǁVectorIndexǁsearch_similar__mutmut_19, 
        'xǁVectorIndexǁsearch_similar__mutmut_20': xǁVectorIndexǁsearch_similar__mutmut_20, 
        'xǁVectorIndexǁsearch_similar__mutmut_21': xǁVectorIndexǁsearch_similar__mutmut_21, 
        'xǁVectorIndexǁsearch_similar__mutmut_22': xǁVectorIndexǁsearch_similar__mutmut_22, 
        'xǁVectorIndexǁsearch_similar__mutmut_23': xǁVectorIndexǁsearch_similar__mutmut_23, 
        'xǁVectorIndexǁsearch_similar__mutmut_24': xǁVectorIndexǁsearch_similar__mutmut_24, 
        'xǁVectorIndexǁsearch_similar__mutmut_25': xǁVectorIndexǁsearch_similar__mutmut_25, 
        'xǁVectorIndexǁsearch_similar__mutmut_26': xǁVectorIndexǁsearch_similar__mutmut_26, 
        'xǁVectorIndexǁsearch_similar__mutmut_27': xǁVectorIndexǁsearch_similar__mutmut_27, 
        'xǁVectorIndexǁsearch_similar__mutmut_28': xǁVectorIndexǁsearch_similar__mutmut_28, 
        'xǁVectorIndexǁsearch_similar__mutmut_29': xǁVectorIndexǁsearch_similar__mutmut_29, 
        'xǁVectorIndexǁsearch_similar__mutmut_30': xǁVectorIndexǁsearch_similar__mutmut_30, 
        'xǁVectorIndexǁsearch_similar__mutmut_31': xǁVectorIndexǁsearch_similar__mutmut_31, 
        'xǁVectorIndexǁsearch_similar__mutmut_32': xǁVectorIndexǁsearch_similar__mutmut_32, 
        'xǁVectorIndexǁsearch_similar__mutmut_33': xǁVectorIndexǁsearch_similar__mutmut_33, 
        'xǁVectorIndexǁsearch_similar__mutmut_34': xǁVectorIndexǁsearch_similar__mutmut_34, 
        'xǁVectorIndexǁsearch_similar__mutmut_35': xǁVectorIndexǁsearch_similar__mutmut_35, 
        'xǁVectorIndexǁsearch_similar__mutmut_36': xǁVectorIndexǁsearch_similar__mutmut_36, 
        'xǁVectorIndexǁsearch_similar__mutmut_37': xǁVectorIndexǁsearch_similar__mutmut_37, 
        'xǁVectorIndexǁsearch_similar__mutmut_38': xǁVectorIndexǁsearch_similar__mutmut_38, 
        'xǁVectorIndexǁsearch_similar__mutmut_39': xǁVectorIndexǁsearch_similar__mutmut_39, 
        'xǁVectorIndexǁsearch_similar__mutmut_40': xǁVectorIndexǁsearch_similar__mutmut_40, 
        'xǁVectorIndexǁsearch_similar__mutmut_41': xǁVectorIndexǁsearch_similar__mutmut_41
    }
    
    def search_similar(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁsearch_similar__mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁsearch_similar__mutmut_mutants"), args, kwargs, self)
        return result 
    
    search_similar.__signature__ = _mutmut_signature(xǁVectorIndexǁsearch_similar__mutmut_orig)
    xǁVectorIndexǁsearch_similar__mutmut_orig.__name__ = 'xǁVectorIndexǁsearch_similar'
    
    def xǁVectorIndexǁremove_vector__mutmut_orig(self, memory_id: int) -> None:
        """
        Remove a vector from the index.
        
        Note: FAISS doesn't support efficient removal, so we clear the index
        completely. The caller (MemoryManager) must rebuild the index from storage
        after calling this method using _rebuild_index_from_storage().
        
        Args:
            memory_id: Memory record ID to remove
        """
        # Check if memory is in index
        if memory_id not in self.id_map.values():
            logger.warning(f"Memory {memory_id} not found in index")
            return
        
        # Clear the entire index - it will be rebuilt by MemoryManager
        # This is inefficient but FAISS doesn't support removal
        logger.info(f"Clearing index to remove memory {memory_id}. Index will be rebuilt from storage.")
        self.clear()
        
        # Note: MemoryManager.delete_memory() will call _rebuild_index_from_storage()
        # to rebuild the index with all remaining memories after deletion.
    
    def xǁVectorIndexǁremove_vector__mutmut_1(self, memory_id: int) -> None:
        """
        Remove a vector from the index.
        
        Note: FAISS doesn't support efficient removal, so we clear the index
        completely. The caller (MemoryManager) must rebuild the index from storage
        after calling this method using _rebuild_index_from_storage().
        
        Args:
            memory_id: Memory record ID to remove
        """
        # Check if memory is in index
        if memory_id in self.id_map.values():
            logger.warning(f"Memory {memory_id} not found in index")
            return
        
        # Clear the entire index - it will be rebuilt by MemoryManager
        # This is inefficient but FAISS doesn't support removal
        logger.info(f"Clearing index to remove memory {memory_id}. Index will be rebuilt from storage.")
        self.clear()
        
        # Note: MemoryManager.delete_memory() will call _rebuild_index_from_storage()
        # to rebuild the index with all remaining memories after deletion.
    
    def xǁVectorIndexǁremove_vector__mutmut_2(self, memory_id: int) -> None:
        """
        Remove a vector from the index.
        
        Note: FAISS doesn't support efficient removal, so we clear the index
        completely. The caller (MemoryManager) must rebuild the index from storage
        after calling this method using _rebuild_index_from_storage().
        
        Args:
            memory_id: Memory record ID to remove
        """
        # Check if memory is in index
        if memory_id not in self.id_map.values():
            logger.warning(None)
            return
        
        # Clear the entire index - it will be rebuilt by MemoryManager
        # This is inefficient but FAISS doesn't support removal
        logger.info(f"Clearing index to remove memory {memory_id}. Index will be rebuilt from storage.")
        self.clear()
        
        # Note: MemoryManager.delete_memory() will call _rebuild_index_from_storage()
        # to rebuild the index with all remaining memories after deletion.
    
    def xǁVectorIndexǁremove_vector__mutmut_3(self, memory_id: int) -> None:
        """
        Remove a vector from the index.
        
        Note: FAISS doesn't support efficient removal, so we clear the index
        completely. The caller (MemoryManager) must rebuild the index from storage
        after calling this method using _rebuild_index_from_storage().
        
        Args:
            memory_id: Memory record ID to remove
        """
        # Check if memory is in index
        if memory_id not in self.id_map.values():
            logger.warning(f"Memory {memory_id} not found in index")
            return
        
        # Clear the entire index - it will be rebuilt by MemoryManager
        # This is inefficient but FAISS doesn't support removal
        logger.info(None)
        self.clear()
        
        # Note: MemoryManager.delete_memory() will call _rebuild_index_from_storage()
        # to rebuild the index with all remaining memories after deletion.
    
    xǁVectorIndexǁremove_vector__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁremove_vector__mutmut_1': xǁVectorIndexǁremove_vector__mutmut_1, 
        'xǁVectorIndexǁremove_vector__mutmut_2': xǁVectorIndexǁremove_vector__mutmut_2, 
        'xǁVectorIndexǁremove_vector__mutmut_3': xǁVectorIndexǁremove_vector__mutmut_3
    }
    
    def remove_vector(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁremove_vector__mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁremove_vector__mutmut_mutants"), args, kwargs, self)
        return result 
    
    remove_vector.__signature__ = _mutmut_signature(xǁVectorIndexǁremove_vector__mutmut_orig)
    xǁVectorIndexǁremove_vector__mutmut_orig.__name__ = 'xǁVectorIndexǁremove_vector'
    
    def xǁVectorIndexǁsave_index__mutmut_orig(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_1(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = None
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_2(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(None) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_3(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is not None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_4(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError(None)
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_5(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("XXNo path provided for saving indexXX")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_6(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("no path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_7(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("NO PATH PROVIDED FOR SAVING INDEX")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_8(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=None, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_9(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=None)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_10(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_11(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, )
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_12(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=False, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_13(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=False)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_14(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(None, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_15(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, None)
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_16(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_17(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, )
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_18(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(None))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_19(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = None
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_20(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix(None)
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_21(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('XX.jsonXX')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_22(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.JSON')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_23(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(None, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_24(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, None) as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_25(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open('w') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_26(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, ) as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_27(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'XXwXX') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_28(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'W') as f:
            json.dump(self.id_map, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_29(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(None, f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_30(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, None)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_31(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(f)
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_32(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, )
        
        logger.info(f"Saved vector index to {save_path}")
    
    def xǁVectorIndexǁsave_index__mutmut_33(self, path: Optional[str] = None) -> None:
        """
        Save index to disk.
        
        Args:
            path: Optional path to save to (uses instance path if not provided)
        """
        save_path = Path(path) if path else self.index_path
        if save_path is None:
            raise ValueError("No path provided for saving index")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save ID mapping separately (as JSON)
        import json
        mapping_path = save_path.with_suffix('.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.id_map, f)
        
        logger.info(None)
    
    xǁVectorIndexǁsave_index__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁsave_index__mutmut_1': xǁVectorIndexǁsave_index__mutmut_1, 
        'xǁVectorIndexǁsave_index__mutmut_2': xǁVectorIndexǁsave_index__mutmut_2, 
        'xǁVectorIndexǁsave_index__mutmut_3': xǁVectorIndexǁsave_index__mutmut_3, 
        'xǁVectorIndexǁsave_index__mutmut_4': xǁVectorIndexǁsave_index__mutmut_4, 
        'xǁVectorIndexǁsave_index__mutmut_5': xǁVectorIndexǁsave_index__mutmut_5, 
        'xǁVectorIndexǁsave_index__mutmut_6': xǁVectorIndexǁsave_index__mutmut_6, 
        'xǁVectorIndexǁsave_index__mutmut_7': xǁVectorIndexǁsave_index__mutmut_7, 
        'xǁVectorIndexǁsave_index__mutmut_8': xǁVectorIndexǁsave_index__mutmut_8, 
        'xǁVectorIndexǁsave_index__mutmut_9': xǁVectorIndexǁsave_index__mutmut_9, 
        'xǁVectorIndexǁsave_index__mutmut_10': xǁVectorIndexǁsave_index__mutmut_10, 
        'xǁVectorIndexǁsave_index__mutmut_11': xǁVectorIndexǁsave_index__mutmut_11, 
        'xǁVectorIndexǁsave_index__mutmut_12': xǁVectorIndexǁsave_index__mutmut_12, 
        'xǁVectorIndexǁsave_index__mutmut_13': xǁVectorIndexǁsave_index__mutmut_13, 
        'xǁVectorIndexǁsave_index__mutmut_14': xǁVectorIndexǁsave_index__mutmut_14, 
        'xǁVectorIndexǁsave_index__mutmut_15': xǁVectorIndexǁsave_index__mutmut_15, 
        'xǁVectorIndexǁsave_index__mutmut_16': xǁVectorIndexǁsave_index__mutmut_16, 
        'xǁVectorIndexǁsave_index__mutmut_17': xǁVectorIndexǁsave_index__mutmut_17, 
        'xǁVectorIndexǁsave_index__mutmut_18': xǁVectorIndexǁsave_index__mutmut_18, 
        'xǁVectorIndexǁsave_index__mutmut_19': xǁVectorIndexǁsave_index__mutmut_19, 
        'xǁVectorIndexǁsave_index__mutmut_20': xǁVectorIndexǁsave_index__mutmut_20, 
        'xǁVectorIndexǁsave_index__mutmut_21': xǁVectorIndexǁsave_index__mutmut_21, 
        'xǁVectorIndexǁsave_index__mutmut_22': xǁVectorIndexǁsave_index__mutmut_22, 
        'xǁVectorIndexǁsave_index__mutmut_23': xǁVectorIndexǁsave_index__mutmut_23, 
        'xǁVectorIndexǁsave_index__mutmut_24': xǁVectorIndexǁsave_index__mutmut_24, 
        'xǁVectorIndexǁsave_index__mutmut_25': xǁVectorIndexǁsave_index__mutmut_25, 
        'xǁVectorIndexǁsave_index__mutmut_26': xǁVectorIndexǁsave_index__mutmut_26, 
        'xǁVectorIndexǁsave_index__mutmut_27': xǁVectorIndexǁsave_index__mutmut_27, 
        'xǁVectorIndexǁsave_index__mutmut_28': xǁVectorIndexǁsave_index__mutmut_28, 
        'xǁVectorIndexǁsave_index__mutmut_29': xǁVectorIndexǁsave_index__mutmut_29, 
        'xǁVectorIndexǁsave_index__mutmut_30': xǁVectorIndexǁsave_index__mutmut_30, 
        'xǁVectorIndexǁsave_index__mutmut_31': xǁVectorIndexǁsave_index__mutmut_31, 
        'xǁVectorIndexǁsave_index__mutmut_32': xǁVectorIndexǁsave_index__mutmut_32, 
        'xǁVectorIndexǁsave_index__mutmut_33': xǁVectorIndexǁsave_index__mutmut_33
    }
    
    def save_index(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁsave_index__mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁsave_index__mutmut_mutants"), args, kwargs, self)
        return result 
    
    save_index.__signature__ = _mutmut_signature(xǁVectorIndexǁsave_index__mutmut_orig)
    xǁVectorIndexǁsave_index__mutmut_orig.__name__ = 'xǁVectorIndexǁsave_index'
    
    def xǁVectorIndexǁload_index__mutmut_orig(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_1(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = None
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_2(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(None) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_3(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None and not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_4(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is not None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_5(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_6(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(None)
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_7(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = None
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_8(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(None)
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_9(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(None))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_10(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = None
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_11(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix(None)
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_12(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('XX.jsonXX')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_13(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.JSON')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_14(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(None, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_15(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, None) as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_16(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open('r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_17(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, ) as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_18(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'XXrXX') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_19(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'R') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_20(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = None
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_21(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(None): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_22(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(None) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_23(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(None).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_24(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = None
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_25(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) - 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_26(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(None) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_27(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 2
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_28(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(None)
            self.id_map = {}
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_29(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = None
        
        logger.info(f"Loaded vector index from {load_path} with {self.index.ntotal} vectors")
    
    def xǁVectorIndexǁload_index__mutmut_30(self, path: Optional[str] = None) -> None:
        """
        Load index from disk.
        
        Args:
            path: Optional path to load from (uses instance path if not provided)
        """
        load_path = Path(path) if path else self.index_path
        if load_path is None or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load ID mapping
        import json
        mapping_path = load_path.with_suffix('.json')
        if mapping_path.exists():
            with open(mapping_path, 'r') as f:
                self.id_map = {int(k): int(v) for k, v in json.load(f).items()}
            
            # Update counter to be higher than max FAISS ID
            if self.id_map:
                self.faiss_id_counter = max(self.id_map.keys()) + 1
        else:
            logger.warning(f"ID mapping file not found at {mapping_path}")
            self.id_map = {}
        
        logger.info(None)
    
    xǁVectorIndexǁload_index__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁload_index__mutmut_1': xǁVectorIndexǁload_index__mutmut_1, 
        'xǁVectorIndexǁload_index__mutmut_2': xǁVectorIndexǁload_index__mutmut_2, 
        'xǁVectorIndexǁload_index__mutmut_3': xǁVectorIndexǁload_index__mutmut_3, 
        'xǁVectorIndexǁload_index__mutmut_4': xǁVectorIndexǁload_index__mutmut_4, 
        'xǁVectorIndexǁload_index__mutmut_5': xǁVectorIndexǁload_index__mutmut_5, 
        'xǁVectorIndexǁload_index__mutmut_6': xǁVectorIndexǁload_index__mutmut_6, 
        'xǁVectorIndexǁload_index__mutmut_7': xǁVectorIndexǁload_index__mutmut_7, 
        'xǁVectorIndexǁload_index__mutmut_8': xǁVectorIndexǁload_index__mutmut_8, 
        'xǁVectorIndexǁload_index__mutmut_9': xǁVectorIndexǁload_index__mutmut_9, 
        'xǁVectorIndexǁload_index__mutmut_10': xǁVectorIndexǁload_index__mutmut_10, 
        'xǁVectorIndexǁload_index__mutmut_11': xǁVectorIndexǁload_index__mutmut_11, 
        'xǁVectorIndexǁload_index__mutmut_12': xǁVectorIndexǁload_index__mutmut_12, 
        'xǁVectorIndexǁload_index__mutmut_13': xǁVectorIndexǁload_index__mutmut_13, 
        'xǁVectorIndexǁload_index__mutmut_14': xǁVectorIndexǁload_index__mutmut_14, 
        'xǁVectorIndexǁload_index__mutmut_15': xǁVectorIndexǁload_index__mutmut_15, 
        'xǁVectorIndexǁload_index__mutmut_16': xǁVectorIndexǁload_index__mutmut_16, 
        'xǁVectorIndexǁload_index__mutmut_17': xǁVectorIndexǁload_index__mutmut_17, 
        'xǁVectorIndexǁload_index__mutmut_18': xǁVectorIndexǁload_index__mutmut_18, 
        'xǁVectorIndexǁload_index__mutmut_19': xǁVectorIndexǁload_index__mutmut_19, 
        'xǁVectorIndexǁload_index__mutmut_20': xǁVectorIndexǁload_index__mutmut_20, 
        'xǁVectorIndexǁload_index__mutmut_21': xǁVectorIndexǁload_index__mutmut_21, 
        'xǁVectorIndexǁload_index__mutmut_22': xǁVectorIndexǁload_index__mutmut_22, 
        'xǁVectorIndexǁload_index__mutmut_23': xǁVectorIndexǁload_index__mutmut_23, 
        'xǁVectorIndexǁload_index__mutmut_24': xǁVectorIndexǁload_index__mutmut_24, 
        'xǁVectorIndexǁload_index__mutmut_25': xǁVectorIndexǁload_index__mutmut_25, 
        'xǁVectorIndexǁload_index__mutmut_26': xǁVectorIndexǁload_index__mutmut_26, 
        'xǁVectorIndexǁload_index__mutmut_27': xǁVectorIndexǁload_index__mutmut_27, 
        'xǁVectorIndexǁload_index__mutmut_28': xǁVectorIndexǁload_index__mutmut_28, 
        'xǁVectorIndexǁload_index__mutmut_29': xǁVectorIndexǁload_index__mutmut_29, 
        'xǁVectorIndexǁload_index__mutmut_30': xǁVectorIndexǁload_index__mutmut_30
    }
    
    def load_index(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁload_index__mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁload_index__mutmut_mutants"), args, kwargs, self)
        return result 
    
    load_index.__signature__ = _mutmut_signature(xǁVectorIndexǁload_index__mutmut_orig)
    xǁVectorIndexǁload_index__mutmut_orig.__name__ = 'xǁVectorIndexǁload_index'
    
    def xǁVectorIndexǁsync_with_storage__mutmut_orig(self, storage: MemoryStorage) -> None:
        """
        Rebuild index from storage (for synchronization).
        
        This should be called when the index needs to be rebuilt from storage.
        Note: This requires embeddings to be regenerated, so it's typically
        called during initialization or when index is corrupted.
        
        Args:
            storage: MemoryStorage instance to sync from
        """
        logger.warning("sync_with_storage requires embeddings - should be handled by MemoryManager")
        # This method is a placeholder - actual sync should be done by MemoryManager
        # which has access to the embedding service
    
    def xǁVectorIndexǁsync_with_storage__mutmut_1(self, storage: MemoryStorage) -> None:
        """
        Rebuild index from storage (for synchronization).
        
        This should be called when the index needs to be rebuilt from storage.
        Note: This requires embeddings to be regenerated, so it's typically
        called during initialization or when index is corrupted.
        
        Args:
            storage: MemoryStorage instance to sync from
        """
        logger.warning(None)
        # This method is a placeholder - actual sync should be done by MemoryManager
        # which has access to the embedding service
    
    def xǁVectorIndexǁsync_with_storage__mutmut_2(self, storage: MemoryStorage) -> None:
        """
        Rebuild index from storage (for synchronization).
        
        This should be called when the index needs to be rebuilt from storage.
        Note: This requires embeddings to be regenerated, so it's typically
        called during initialization or when index is corrupted.
        
        Args:
            storage: MemoryStorage instance to sync from
        """
        logger.warning("XXsync_with_storage requires embeddings - should be handled by MemoryManagerXX")
        # This method is a placeholder - actual sync should be done by MemoryManager
        # which has access to the embedding service
    
    def xǁVectorIndexǁsync_with_storage__mutmut_3(self, storage: MemoryStorage) -> None:
        """
        Rebuild index from storage (for synchronization).
        
        This should be called when the index needs to be rebuilt from storage.
        Note: This requires embeddings to be regenerated, so it's typically
        called during initialization or when index is corrupted.
        
        Args:
            storage: MemoryStorage instance to sync from
        """
        logger.warning("sync_with_storage requires embeddings - should be handled by memorymanager")
        # This method is a placeholder - actual sync should be done by MemoryManager
        # which has access to the embedding service
    
    def xǁVectorIndexǁsync_with_storage__mutmut_4(self, storage: MemoryStorage) -> None:
        """
        Rebuild index from storage (for synchronization).
        
        This should be called when the index needs to be rebuilt from storage.
        Note: This requires embeddings to be regenerated, so it's typically
        called during initialization or when index is corrupted.
        
        Args:
            storage: MemoryStorage instance to sync from
        """
        logger.warning("SYNC_WITH_STORAGE REQUIRES EMBEDDINGS - SHOULD BE HANDLED BY MEMORYMANAGER")
        # This method is a placeholder - actual sync should be done by MemoryManager
        # which has access to the embedding service
    
    xǁVectorIndexǁsync_with_storage__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁsync_with_storage__mutmut_1': xǁVectorIndexǁsync_with_storage__mutmut_1, 
        'xǁVectorIndexǁsync_with_storage__mutmut_2': xǁVectorIndexǁsync_with_storage__mutmut_2, 
        'xǁVectorIndexǁsync_with_storage__mutmut_3': xǁVectorIndexǁsync_with_storage__mutmut_3, 
        'xǁVectorIndexǁsync_with_storage__mutmut_4': xǁVectorIndexǁsync_with_storage__mutmut_4
    }
    
    def sync_with_storage(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁsync_with_storage__mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁsync_with_storage__mutmut_mutants"), args, kwargs, self)
        return result 
    
    sync_with_storage.__signature__ = _mutmut_signature(xǁVectorIndexǁsync_with_storage__mutmut_orig)
    xǁVectorIndexǁsync_with_storage__mutmut_orig.__name__ = 'xǁVectorIndexǁsync_with_storage'
    
    def get_count(self) -> int:
        """Get the number of vectors in the index."""
        return self.index.ntotal
    
    def xǁVectorIndexǁget_memory_ids__mutmut_orig(self) -> List[int]:
        """
        Get all memory IDs currently in the index.
        
        Returns:
            List of memory IDs that are indexed
        """
        return list(self.id_map.values())
    
    def xǁVectorIndexǁget_memory_ids__mutmut_1(self) -> List[int]:
        """
        Get all memory IDs currently in the index.
        
        Returns:
            List of memory IDs that are indexed
        """
        return list(None)
    
    xǁVectorIndexǁget_memory_ids__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁget_memory_ids__mutmut_1': xǁVectorIndexǁget_memory_ids__mutmut_1
    }
    
    def get_memory_ids(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁget_memory_ids__mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁget_memory_ids__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_memory_ids.__signature__ = _mutmut_signature(xǁVectorIndexǁget_memory_ids__mutmut_orig)
    xǁVectorIndexǁget_memory_ids__mutmut_orig.__name__ = 'xǁVectorIndexǁget_memory_ids'
    
    def xǁVectorIndexǁclear__mutmut_orig(self) -> None:
        """Clear all vectors from the index."""
        self.index.reset()
        self.id_map.clear()
        self.faiss_id_counter = 0
        logger.debug("Cleared vector index")
    
    def xǁVectorIndexǁclear__mutmut_1(self) -> None:
        """Clear all vectors from the index."""
        self.index.reset()
        self.id_map.clear()
        self.faiss_id_counter = None
        logger.debug("Cleared vector index")
    
    def xǁVectorIndexǁclear__mutmut_2(self) -> None:
        """Clear all vectors from the index."""
        self.index.reset()
        self.id_map.clear()
        self.faiss_id_counter = 1
        logger.debug("Cleared vector index")
    
    def xǁVectorIndexǁclear__mutmut_3(self) -> None:
        """Clear all vectors from the index."""
        self.index.reset()
        self.id_map.clear()
        self.faiss_id_counter = 0
        logger.debug(None)
    
    def xǁVectorIndexǁclear__mutmut_4(self) -> None:
        """Clear all vectors from the index."""
        self.index.reset()
        self.id_map.clear()
        self.faiss_id_counter = 0
        logger.debug("XXCleared vector indexXX")
    
    def xǁVectorIndexǁclear__mutmut_5(self) -> None:
        """Clear all vectors from the index."""
        self.index.reset()
        self.id_map.clear()
        self.faiss_id_counter = 0
        logger.debug("cleared vector index")
    
    def xǁVectorIndexǁclear__mutmut_6(self) -> None:
        """Clear all vectors from the index."""
        self.index.reset()
        self.id_map.clear()
        self.faiss_id_counter = 0
        logger.debug("CLEARED VECTOR INDEX")
    
    xǁVectorIndexǁclear__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁVectorIndexǁclear__mutmut_1': xǁVectorIndexǁclear__mutmut_1, 
        'xǁVectorIndexǁclear__mutmut_2': xǁVectorIndexǁclear__mutmut_2, 
        'xǁVectorIndexǁclear__mutmut_3': xǁVectorIndexǁclear__mutmut_3, 
        'xǁVectorIndexǁclear__mutmut_4': xǁVectorIndexǁclear__mutmut_4, 
        'xǁVectorIndexǁclear__mutmut_5': xǁVectorIndexǁclear__mutmut_5, 
        'xǁVectorIndexǁclear__mutmut_6': xǁVectorIndexǁclear__mutmut_6
    }
    
    def clear(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁVectorIndexǁclear__mutmut_orig"), object.__getattribute__(self, "xǁVectorIndexǁclear__mutmut_mutants"), args, kwargs, self)
        return result 
    
    clear.__signature__ = _mutmut_signature(xǁVectorIndexǁclear__mutmut_orig)
    xǁVectorIndexǁclear__mutmut_orig.__name__ = 'xǁVectorIndexǁclear'

