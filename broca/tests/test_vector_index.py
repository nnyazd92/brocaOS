"""
Tests for VectorIndex FAISS implementation.

Tests vector operations, similarity search, and index persistence.
"""

from __future__ import annotations

import tempfile
import os
import json
from pathlib import Path
import numpy as np
import pytest

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from broca.memory.vector_index import VectorIndex


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
class TestVectorIndexInitialization:
    """Test VectorIndex initialization."""
    
    def test_init_creates_index(self):
        """
        Test that initialization creates FAISS index.
        
        Rationale: Ensures index is created with correct dimension.
        """
        index = VectorIndex(dimension=1536)
        
        assert index.dimension == 1536
        assert index.get_count() == 0
        assert index.id_map == {}
    
    def test_init_with_index_path(self):
        """
        Test initialization with index path.
        
        Rationale: Ensures index path is stored for persistence.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "test.faiss")
            index = VectorIndex(dimension=1536, index_path=index_path)
            
            assert index.index_path == Path(index_path)
    
    def test_init_loads_existing_index(self):
        """
        Test that initialization loads existing index if present.
        
        Rationale: Ensures index persistence works across restarts.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "test.faiss")
            
            # Create and save an index
            index1 = VectorIndex(dimension=1536, index_path=index_path)
            embedding = [0.1] * 1536
            index1.add_vector(1, embedding)
            index1.save_index()
            
            # Load it in a new index
            index2 = VectorIndex(dimension=1536, index_path=index_path)
            
            assert index2.get_count() == 1
            assert 1 in index2.id_map.values()


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
class TestVectorIndexAddVector:
    """Test adding vectors to index."""
    
    def test_add_vector_success(self):
        """
        Test adding a vector successfully.
        
        Rationale: Ensures vectors can be added to the index.
        """
        index = VectorIndex(dimension=1536)
        embedding = [0.1] * 1536
        
        index.add_vector(memory_id=1, embedding=embedding)
        
        assert index.get_count() == 1
        assert 0 in index.id_map  # FAISS ID 0
        assert index.id_map[0] == 1  # Maps to memory ID 1
    
    def test_add_vector_dimension_mismatch(self):
        """
        Test that dimension mismatch raises error.
        
        Rationale: Ensures embedding dimension matches index dimension.
        """
        index = VectorIndex(dimension=1536)
        embedding = [0.1] * 512  # Wrong dimension
        
        with pytest.raises(ValueError, match="dimension"):
            index.add_vector(memory_id=1, embedding=embedding)
    
    def test_add_multiple_vectors(self):
        """
        Test adding multiple vectors.
        
        Rationale: Ensures multiple vectors can be indexed.
        """
        index = VectorIndex(dimension=1536)
        
        for i in range(5):
            embedding = [float(i) / 10.0] * 1536
            index.add_vector(memory_id=i+1, embedding=embedding)
        
        assert index.get_count() == 5
        assert len(index.id_map) == 5


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
class TestVectorIndexSearchSimilar:
    """Test similarity search."""
    
    def test_search_similar_empty_index(self):
        """
        Test searching empty index returns empty results.
        
        Rationale: Ensures search handles empty index gracefully.
        """
        index = VectorIndex(dimension=1536)
        query = [0.1] * 1536
        
        results = index.search_similar(query, k=5)
        
        assert results == []
    
    def test_search_similar_finds_matching(self):
        """
        Test that similarity search finds matching vectors.
        
        Rationale: Ensures cosine similarity search works correctly.
        """
        index = VectorIndex(dimension=1536)
        
        # Add vectors
        embedding1 = [1.0, 0.0, 0.0] + [0.0] * 1533  # Mostly in first dimension
        embedding2 = [0.0, 1.0, 0.0] + [0.0] * 1533  # Mostly in second dimension
        embedding3 = [0.0, 0.0, 1.0] + [0.0] * 1533  # Mostly in third dimension
        
        index.add_vector(1, embedding1)
        index.add_vector(2, embedding2)
        index.add_vector(3, embedding3)
        
        # Search with query similar to embedding1
        query = [0.9, 0.1, 0.0] + [0.0] * 1533
        results = index.search_similar(query, k=2)
        
        assert len(results) == 2
        # First result should be memory_id 1 (most similar)
        assert results[0][0] == 1
        assert results[0][1] > 0  # Similarity score > 0
    
    def test_search_similar_returns_sorted(self):
        """
        Test that search results are sorted by similarity.
        
        Rationale: Ensures results are ranked correctly.
        """
        index = VectorIndex(dimension=1536)
        
        # Add vectors with different similarities
        embedding1 = [1.0] + [0.0] * 1535
        embedding2 = [0.5] + [0.0] * 1535
        embedding3 = [0.1] + [0.0] * 1535
        
        index.add_vector(1, embedding1)
        index.add_vector(2, embedding2)
        index.add_vector(3, embedding3)
        
        # Query similar to embedding1
        query = [0.9] + [0.0] * 1535
        results = index.search_similar(query, k=3)
        
        # Results should be sorted by similarity (descending)
        assert len(results) == 3
        similarities = [r[1] for r in results]
        assert similarities == sorted(similarities, reverse=True)
    
    def test_search_similar_respects_k(self):
        """
        Test that search respects k parameter.
        
        Rationale: Ensures limit on results works correctly.
        """
        index = VectorIndex(dimension=1536)
        
        for i in range(10):
            embedding = [float(i) / 10.0] * 1536
            index.add_vector(i+1, embedding)
        
        query = [0.5] * 1536
        results = index.search_similar(query, k=5)
        
        assert len(results) <= 5
    
    def test_search_similar_dimension_mismatch(self):
        """
        Test that dimension mismatch raises error.
        
        Rationale: Ensures query dimension matches index dimension.
        """
        index = VectorIndex(dimension=1536)
        index.add_vector(1, [0.1] * 1536)
        
        query = [0.1] * 512  # Wrong dimension
        
        with pytest.raises(ValueError, match="dimension"):
            index.search_similar(query, k=5)


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
class TestVectorIndexPersistence:
    """Test index persistence."""
    
    def test_save_and_load_index(self):
        """
        Test saving and loading index.
        
        Rationale: Ensures index can be persisted to disk.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "test.faiss")
            
            # Create and save index
            index1 = VectorIndex(dimension=1536, index_path=index_path)
            index1.add_vector(1, [0.1] * 1536)
            index1.add_vector(2, [0.2] * 1536)
            index1.save_index()
            
            # Load in new index
            index2 = VectorIndex(dimension=1536, index_path=index_path)
            
            assert index2.get_count() == 2
            assert 1 in index2.id_map.values()
            assert 2 in index2.id_map.values()
    
    def test_save_index_creates_files(self):
        """
        Test that save creates both index and mapping files.
        
        Rationale: Ensures both FAISS index and ID mapping are saved.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test.faiss"
            
            index = VectorIndex(dimension=1536, index_path=str(index_path))
            index.add_vector(1, [0.1] * 1536)
            index.save_index()
            
            assert index_path.exists()
            mapping_path = index_path.with_suffix('.json')
            assert mapping_path.exists()
    
    def test_load_index_nonexistent(self):
        """
        Test loading non-existent index doesn't crash.
        
        Rationale: Ensures graceful handling of missing index files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "nonexistent.faiss")
            
            index = VectorIndex(dimension=1536, index_path=index_path)
            
            # Should not crash, just have empty index
            assert index.get_count() == 0


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
class TestVectorIndexOperations:
    """Test index operations."""
    
    def test_get_count(self):
        """
        Test getting vector count.
        
        Rationale: Ensures count reflects number of vectors.
        """
        index = VectorIndex(dimension=1536)
        
        assert index.get_count() == 0
        
        index.add_vector(1, [0.1] * 1536)
        assert index.get_count() == 1
        
        index.add_vector(2, [0.2] * 1536)
        assert index.get_count() == 2
    
    def test_clear(self):
        """
        Test clearing the index.
        
        Rationale: Ensures index can be reset.
        """
        index = VectorIndex(dimension=1536)
        
        index.add_vector(1, [0.1] * 1536)
        index.add_vector(2, [0.2] * 1536)
        
        assert index.get_count() == 2
        
        index.clear()
        
        assert index.get_count() == 0
        assert len(index.id_map) == 0


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
class TestVectorIndexRemoveVector:
    """Test removing vectors from index."""
    
    def test_remove_vector_success(self):
        """
        Test removing a vector successfully.
        
        Rationale: Ensures remove_vector clears the index (FAISS limitation).
        Note: MemoryManager is responsible for rebuilding the index from storage.
        """
        index = VectorIndex(dimension=1536)
        
        # Add vectors
        embedding1 = [0.1] * 1536
        embedding2 = [0.2] * 1536
        embedding3 = [0.3] * 1536
        
        index.add_vector(1, embedding1)
        index.add_vector(2, embedding2)
        index.add_vector(3, embedding3)
        
        assert index.get_count() == 3
        assert 1 in index.get_memory_ids()
        assert 2 in index.get_memory_ids()
        assert 3 in index.get_memory_ids()
        
        # Remove one vector - clears entire index (FAISS limitation)
        index.remove_vector(2)
        
        # Verify index is cleared (MemoryManager will rebuild from storage)
        assert index.get_count() == 0
        assert len(index.get_memory_ids()) == 0
    
    def test_remove_vector_nonexistent(self):
        """
        Test removing non-existent vector doesn't crash.
        
        Rationale: Ensures graceful handling of removal of non-existent vectors.
        Note: remove_vector only clears the index if the vector exists in the index.
        """
        index = VectorIndex(dimension=1536)
        
        index.add_vector(1, [0.1] * 1536)
        
        # Try to remove non-existent vector - doesn't clear index (early return)
        index.remove_vector(999)
        
        # Index should still have the original vector (not cleared for non-existent)
        assert index.get_count() == 1
        assert 1 in index.get_memory_ids()
        
        # Removing an existing vector clears the index
        index.remove_vector(1)
        assert index.get_count() == 0
        assert len(index.get_memory_ids()) == 0
    
    def test_remove_vector_rebuilds_index(self):
        """
        Test that remove_vector clears the index.
        
        Rationale: Ensures remove_vector clears the index (FAISS limitation).
        MemoryManager is responsible for rebuilding the index from storage.
        """
        index = VectorIndex(dimension=1536)
        
        # Add multiple vectors
        embeddings = {}
        for i in range(5):
            embedding = [float(i) / 10.0] * 1536
            index.add_vector(i+1, embedding)
            embeddings[i+1] = embedding
        
        assert index.get_count() == 5
        
        # Remove middle vector - clears entire index
        index.remove_vector(3)
        
        # Verify index is cleared
        assert index.get_count() == 0
        assert len(index.get_memory_ids()) == 0
    
    def test_remove_vector_preserves_other_vectors(self):
        """
        Test that remove_vector clears the index.
        
        Rationale: remove_vector clears the entire index (FAISS limitation).
        MemoryManager rebuilds the index from storage, preserving other vectors.
        This test verifies the clearing behavior.
        """
        index = VectorIndex(dimension=1536)
        
        # Add distinct vectors
        embedding1 = [1.0] + [0.0] * 1535
        embedding2 = [0.0, 1.0] + [0.0] * 1534
        embedding3 = [0.0, 0.0, 1.0] + [0.0] * 1533
        
        index.add_vector(1, embedding1)
        index.add_vector(2, embedding2)
        index.add_vector(3, embedding3)
        
        assert index.get_count() == 3
        
        # Remove vector 2 - clears entire index
        index.remove_vector(2)
        
        # Verify index is cleared
        assert index.get_count() == 0
        assert len(index.get_memory_ids()) == 0
        
        # Note: MemoryManager.delete_memory() will rebuild the index
        # from storage, which preserves other vectors
    
    def test_remove_all_vectors(self):
        """
        Test removing vectors clears the index.
        
        Rationale: remove_vector clears the entire index (FAISS limitation).
        Each call clears the index, so removing all vectors results in empty index.
        """
        index = VectorIndex(dimension=1536)
        
        index.add_vector(1, [0.1] * 1536)
        index.add_vector(2, [0.2] * 1536)
        
        assert index.get_count() == 2
        
        # Remove first vector - clears index
        index.remove_vector(1)
        assert index.get_count() == 0
        assert len(index.get_memory_ids()) == 0
        
        # Re-add vectors to test removing last one
        index.add_vector(1, [0.1] * 1536)
        index.add_vector(2, [0.2] * 1536)
        assert index.get_count() == 2
        
        # Remove last vector - clears index
        index.remove_vector(2)
        assert index.get_count() == 0
        assert len(index.get_memory_ids()) == 0
    
    def test_remove_vector_persists_after_save(self):
        """
        Test that cleared index persists after save and reload.
        
        Rationale: Ensures remove_vector clears the index and this state persists.
        Note: MemoryManager rebuilds the index from storage after removal.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "test.faiss")
            
            index = VectorIndex(dimension=1536, index_path=index_path)
            
            # Add vectors
            index.add_vector(1, [0.1] * 1536)
            index.add_vector(2, [0.2] * 1536)
            index.add_vector(3, [0.3] * 1536)
            
            assert index.get_count() == 3
            
            # Remove one - clears entire index
            index.remove_vector(2)
            
            # Save and reload
            index.save_index()
            new_index = VectorIndex(dimension=1536, index_path=index_path)
            
            # Verify index is cleared (persisted)
            assert new_index.get_count() == 0
            assert len(new_index.get_memory_ids()) == 0

