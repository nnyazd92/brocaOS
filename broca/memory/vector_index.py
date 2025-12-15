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


class VectorIndex:
    """
    FAISS-based vector index for memory similarity search.
    
    Uses cosine similarity (via inner product on normalized vectors)
    for finding similar memories.
    """
    
    def __init__(self, dimension: int, index_path: Optional[str] = None) -> None:
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
    
    def add_vector(self, memory_id: int, embedding: List[float]) -> None:
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
    
    def search_similar(
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
    
    def remove_vector(self, memory_id: int) -> None:
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
    
    def save_index(self, path: Optional[str] = None) -> None:
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
    
    def load_index(self, path: Optional[str] = None) -> None:
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
    
    def sync_with_storage(self, storage: MemoryStorage) -> None:
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
    
    def get_count(self) -> int:
        """Get the number of vectors in the index."""
        return self.index.ntotal
    
    def get_memory_ids(self) -> List[int]:
        """
        Get all memory IDs currently in the index.
        
        Returns:
            List of memory IDs that are indexed
        """
        return list(self.id_map.values())
    
    def clear(self) -> None:
        """Clear all vectors from the index."""
        self.index.reset()
        self.id_map.clear()
        self.faiss_id_counter = 0
        logger.debug("Cleared vector index")

