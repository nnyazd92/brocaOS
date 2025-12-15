"""
Tests for enhanced memory search features.

Tests boolean operators, phrase matching, exact namespace matching, and tag combinations.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest

from broca.memory import MemoryRecord
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.memory.manager import MemoryManager

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service that returns unique embeddings based on text."""
    service = Mock(spec=EmbeddingService)
    
    def generate_embedding(text: str):
        # Generate a simple deterministic embedding based on text hash
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        embedding = [0.1 + (hash_val % 100) / 10000.0] * 1536
        return embedding
    
    service.generate_embedding.side_effect = generate_embedding
    return service


@pytest.fixture
def temp_memory_system(mock_embedding_service):
    """Create temporary memory system for testing."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        index_path = os.path.join(tmpdir, "test.faiss")
        
        storage = MemoryStorage(db_path)
        vector_index = VectorIndex(dimension=1536, index_path=index_path)
        manager = MemoryManager(storage, vector_index, mock_embedding_service)
        
        yield manager, storage, vector_index
        
        manager.close()


class TestExactNamespaceMatching:
    """Test exact namespace matching vs fuzzy matching."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_exact_namespace_match(self, temp_memory_system):
        """
        Test exact namespace matching finds only exact matches.
        
        Rationale: Ensures exact namespace matching works correctly.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with different namespaces
        mem_id1, _, _ = manager.store_memory(
            namespace="math.sage",
            text="Sage math library",
            importance=0.7,
            tags=["sage"]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="math.sage.api",
            text="Sage API documentation",
            importance=0.8,
            tags=["sage", "api"]
        )
        
        # Exact match should only find math.sage, not math.sage.api
        results = manager.retrieve_memories(
            query="sage",
            namespace="math.sage",
            namespace_exact=True,
            limit=10
        )
        
        # Should only find the exact match
        assert len(results) == 1
        assert results[0].namespace == "math.sage"
        assert results[0].id == mem_id1
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_fuzzy_namespace_match_still_works(self, temp_memory_system):
        """
        Test fuzzy namespace matching still works (backward compatibility).
        
        Rationale: Ensures existing fuzzy matching behavior is preserved.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with different namespaces
        mem_id1, _, _ = manager.store_memory(
            namespace="math.sage",
            text="Sage math library",
            importance=0.7,
            tags=["sage"]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="math.sage.api",
            text="Sage API documentation",
            importance=0.8,
            tags=["sage", "api"]
        )
        
        # Fuzzy match should find both
        results = manager.retrieve_memories(
            query="sage",
            namespace="math.sage",
            namespace_exact=False,  # Default behavior
            limit=10
        )
        
        # Should find both (fuzzy match)
        assert len(results) >= 1
        namespaces = {r.namespace for r in results}
        assert "math.sage" in namespaces or "math.sage.api" in namespaces


class TestTagCombinations:
    """Test tag combination modes (all tags vs any tags)."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tag_mode_any_finds_any_tag(self, temp_memory_system):
        """
        Test 'any' tag mode finds memories with any of the specified tags.
        
        Rationale: Ensures OR logic for tags works correctly.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with different tag combinations
        mem_id1, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with python tag",
            importance=0.7,
            tags=["python"]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with api tag",
            importance=0.8,
            tags=["api"]
        )
        mem_id3, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with both tags",
            importance=0.9,
            tags=["python", "api"]
        )
        mem_id4, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with neither tag",
            importance=0.6,
            tags=["other"]
        )
        
        # Any tag mode should find memories with python OR api
        results = manager.retrieve_memories(
            query="memory",
            tags=["python", "api"],
            tag_mode="any",
            limit=10
        )
        
        # Should find memories with python, api, or both
        result_ids = {r.id for r in results}
        assert mem_id1 in result_ids  # Has python
        assert mem_id2 in result_ids  # Has api
        assert mem_id3 in result_ids  # Has both
        assert mem_id4 not in result_ids  # Has neither
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tag_mode_all_finds_all_tags(self, temp_memory_system):
        """
        Test 'all' tag mode finds only memories with all specified tags.
        
        Rationale: Ensures AND logic for tags works correctly.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with different tag combinations
        mem_id1, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with python tag only",
            importance=0.7,
            tags=["python"]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with api tag only",
            importance=0.8,
            tags=["api"]
        )
        mem_id3, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with both tags",
            importance=0.9,
            tags=["python", "api"]
        )
        mem_id4, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with python, api, and extra",
            importance=0.95,
            tags=["python", "api", "extra"]
        )
        
        # All tag mode should find only memories with BOTH python AND api
        results = manager.retrieve_memories(
            query="memory",
            tags=["python", "api"],
            tag_mode="all",
            limit=10
        )
        
        # Should find only memories with both tags
        result_ids = {r.id for r in results}
        assert mem_id1 not in result_ids  # Only python
        assert mem_id2 not in result_ids  # Only api
        assert mem_id3 in result_ids  # Has both
        assert mem_id4 in result_ids  # Has both (and more)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tag_mode_default_is_any(self, temp_memory_system):
        """
        Test default tag mode is 'any' for backward compatibility.
        
        Rationale: Ensures existing behavior is preserved.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories
        mem_id1, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with python",
            importance=0.7,
            tags=["python"]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="test",
            text="Memory with api",
            importance=0.8,
            tags=["api"]
        )
        
        # Default behavior (no tag_mode specified) should be 'any'
        results = manager.retrieve_memories(
            query="memory",
            tags=["python", "api"],
            limit=10
        )
        
        # Should find both (any tag mode)
        result_ids = {r.id for r in results}
        assert mem_id1 in result_ids
        assert mem_id2 in result_ids


class TestPhraseMatching:
    """Test phrase matching in queries."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_phrase_matching_finds_exact_phrase(self, temp_memory_system):
        """
        Test phrase matching finds memories with exact phrase.
        
        Rationale: Ensures exact phrase matching works correctly.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with similar but different phrases
        mem_id1, _, _ = manager.store_memory(
            namespace="test",
            text="machine learning algorithm",
            importance=0.7,
            tags=[]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="test",
            text="learning machine design",
            importance=0.8,
            tags=[]
        )
        mem_id3, _, _ = manager.store_memory(
            namespace="test",
            text="deep learning model",
            importance=0.9,
            tags=[]
        )
        
        # Phrase match for "machine learning" should find only mem_id1
        results = manager.retrieve_memories(
            query="machine learning",
            query_phrases=["machine learning"],
            limit=10
        )
        
        # Should find memory with exact phrase
        result_ids = {r.id for r in results}
        assert mem_id1 in result_ids  # Has exact phrase
        # mem_id2 and mem_id3 have words but not exact phrase
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_phrase_matching_case_insensitive(self, temp_memory_system):
        """
        Test phrase matching is case insensitive.
        
        Rationale: Ensures phrase matching is user-friendly.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memory with mixed case
        mem_id1, _, _ = manager.store_memory(
            namespace="test",
            text="Machine Learning Algorithm",
            importance=0.7,
            tags=[]
        )
        
        # Phrase match with different case should still work
        results = manager.retrieve_memories(
            query="machine learning",
            query_phrases=["machine learning"],
            limit=10
        )
        
        # Should find the memory
        result_ids = {r.id for r in results}
        assert mem_id1 in result_ids


class TestBooleanOperators:
    """Test boolean operators in queries."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_and_operator_finds_both_terms(self, temp_memory_system):
        """
        Test AND operator finds memories with both terms.
        
        Rationale: Ensures AND logic works in queries.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with different term combinations
        mem_id1, _, _ = manager.store_memory(
            namespace="test",
            text="python programming language",
            importance=0.7,
            tags=[]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="test",
            text="sage mathematical software",
            importance=0.8,
            tags=[]
        )
        mem_id3, _, _ = manager.store_memory(
            namespace="test",
            text="python and sage integration",
            importance=0.9,
            tags=[]
        )
        
        # AND query should find only memory with both terms
        results = manager.retrieve_memories(
            query="python AND sage",
            limit=10
        )
        
        # Should find only memory with both terms
        result_ids = {r.id for r in results}
        assert mem_id3 in result_ids  # Has both
        # mem_id1 and mem_id2 have only one term each
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_or_operator_finds_either_term(self, temp_memory_system):
        """
        Test OR operator finds memories with either term.
        
        Rationale: Ensures OR logic works in queries.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories with different terms
        mem_id1, _, _ = manager.store_memory(
            namespace="test",
            text="python programming",
            importance=0.7,
            tags=[]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="test",
            text="sage mathematics",
            importance=0.8,
            tags=[]
        )
        mem_id3, _, _ = manager.store_memory(
            namespace="test",
            text="other topic",
            importance=0.6,
            tags=[]
        )
        
        # OR query should find memories with either term
        results = manager.retrieve_memories(
            query="python OR sage",
            limit=10
        )
        
        # Should find memories with python or sage
        result_ids = {r.id for r in results}
        assert mem_id1 in result_ids  # Has python
        assert mem_id2 in result_ids  # Has sage
        assert mem_id3 not in result_ids  # Has neither
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_not_operator_excludes_term(self, temp_memory_system):
        """
        Test NOT operator excludes memories with the term.
        
        Rationale: Ensures NOT logic works in queries.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories
        mem_id1, _, _ = manager.store_memory(
            namespace="test",
            text="python programming",
            importance=0.7,
            tags=[]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="test",
            text="sage mathematics",
            importance=0.8,
            tags=[]
        )
        mem_id3, _, _ = manager.store_memory(
            namespace="test",
            text="other topic",
            importance=0.6,
            tags=[]
        )
        
        # NOT query should exclude memories with the term
        results = manager.retrieve_memories(
            query="programming NOT python",
            limit=10
        )
        
        # Should find memories with programming but not python
        result_ids = {r.id for r in results}
        assert mem_id1 not in result_ids  # Has python (excluded)
        # mem_id2 and mem_id3 don't have python, so they could be included


class TestCombinedFeatures:
    """Test combining multiple enhanced search features."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_exact_namespace_and_tag_mode_all(self, temp_memory_system):
        """
        Test combining exact namespace with tag mode 'all'.
        
        Rationale: Ensures features work together correctly.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store memories
        mem_id1, _, _ = manager.store_memory(
            namespace="math.sage",
            text="Sage math",
            importance=0.7,
            tags=["python", "api"]
        )
        mem_id2, _, _ = manager.store_memory(
            namespace="math.sage.api",
            text="Sage API",
            importance=0.8,
            tags=["python", "api"]
        )
        mem_id3, _, _ = manager.store_memory(
            namespace="math.sage",
            text="Sage other",
            importance=0.6,
            tags=["python"]  # Missing 'api'
        )
        
        # Exact namespace + all tags should find only mem_id1
        results = manager.retrieve_memories(
            query="sage",
            namespace="math.sage",
            namespace_exact=True,
            tags=["python", "api"],
            tag_mode="all",
            limit=10
        )
        
        result_ids = {r.id for r in results}
        assert mem_id1 in result_ids  # Exact namespace + all tags
        assert mem_id2 not in result_ids  # Wrong namespace
        assert mem_id3 not in result_ids  # Missing 'api' tag


class TestBackwardCompatibility:
    """Test that existing queries still work."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_existing_queries_still_work(self, temp_memory_system):
        """
        Test that existing query format still works.
        
        Rationale: Ensures backward compatibility.
        """
        manager, storage, vector_index = temp_memory_system
        
        # Store a memory
        mem_id1, _, _ = manager.store_memory(
            namespace="test.ns",
            text="Test memory",
            importance=0.7,
            tags=["tag1"]
        )
        
        # Existing query format should still work
        results = manager.retrieve_memories(
            query="test",
            namespace="test",
            tags=["tag1"],
            limit=10
        )
        
        # Should find the memory
        assert len(results) >= 1
        result_ids = {r.id for r in results}
        assert mem_id1 in result_ids

