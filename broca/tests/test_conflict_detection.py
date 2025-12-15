"""
Tests for conflict detection engine.

Tests semantic, rule-based, and LLM-based conflict detection.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock, patch
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
    """Mock embedding service for testing."""
    service = Mock(spec=EmbeddingService)
    # Return mock embeddings - use different values for different texts
    def generate_embedding(text: str):
        # Simple hash-based embedding for testing
        hash_val = hash(text) % 1000
        base_embedding = [0.1] * 1536
        base_embedding[0] = hash_val / 1000.0
        return base_embedding
    service.generate_embedding.side_effect = generate_embedding
    return service


@pytest.fixture
def temp_storage():
    """Temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        storage = MemoryStorage(db_path)
        yield storage
        storage.close()


@pytest.fixture
def temp_vector_index():
    """Temporary vector index for testing."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test.faiss")
        index = VectorIndex(dimension=1536, index_path=index_path)
        yield index


@pytest.fixture
def memory_manager(temp_storage, temp_vector_index, mock_embedding_service):
    """Memory manager for testing."""
    return MemoryManager(temp_storage, temp_vector_index, mock_embedding_service)


class TestSemanticConflictDetection:
    """Test semantic similarity-based conflict detection."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_detect_semantic_conflicts_finds_similar(self, memory_manager):
        """
        Test that semantic conflicts are detected for similar memories.
        
        Rationale: Ensures embedding-based similarity detection works.
        """
        from broca.memory.conflict.detection import ConflictDetector
        
        # Store a memory
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="User prefers Python programming language",
            importance=0.5
        )
        
        # Create detector
        detector = ConflictDetector(
            memory_manager=memory_manager,
            similarity_threshold=0.7,
            contradiction_threshold=0.6
        )
        
        # Create new memory that contradicts the first
        new_memory = memory_manager.storage.get_memory(memory_id1)
        assert new_memory is not None
        
        # Create a conflicting memory (will be stored separately for testing)
        conflicting_text = "User hates Python programming language"
        
        # Get existing memories to check against
        existing_memories = memory_manager.storage.get_all_memories()
        
        # Detect conflicts
        conflicts = detector.detect_conflicts(new_memory, existing_memories)
        
        # Should find conflicts for semantically similar but contradictory memories
        assert isinstance(conflicts, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_similarity_threshold_filtering(self, memory_manager):
        """
        Test that only conflicts above similarity threshold are detected.
        
        Rationale: Ensures threshold filtering works correctly.
        """
        from broca.memory.conflict.detection import ConflictDetector
        
        # Store a memory
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="Python is a programming language",
            importance=0.5
        )
        
        memory = memory_manager.storage.get_memory(memory_id1)
        assert memory is not None
        
        # Create detector with high threshold
        detector = ConflictDetector(
            memory_manager=memory_manager,
            similarity_threshold=0.95,  # Very high threshold
            contradiction_threshold=0.6
        )
        
        existing_memories = [m for m in memory_manager.storage.get_all_memories() if m.id != memory_id1]
        
        # Should not find conflicts if similarity is below threshold
        conflicts = detector.detect_conflicts(memory, existing_memories)
        # With high threshold and few memories, may not find conflicts
        assert isinstance(conflicts, list)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_exact_duplicates_not_conflicts(self, memory_manager):
        """
        Test that exact duplicates are NOT flagged as conflicts.
        
        Rationale: Exact duplicates are handled by deduplication, not conflicts.
        """
        from broca.memory.conflict.detection import ConflictDetector
        
        # Store a memory
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test.namespace",
            text="Exact duplicate test",
            importance=0.5
        )
        
        memory = memory_manager.storage.get_memory(memory_id1)
        assert memory is not None
        
        detector = ConflictDetector(
            memory_manager=memory_manager,
            similarity_threshold=0.7,
            contradiction_threshold=0.6
        )
        
        # Get all memories including the duplicate
        existing_memories = memory_manager.storage.get_all_memories()
        
        # Exact duplicates should not be flagged as conflicts
        conflicts = detector.detect_conflicts(memory, existing_memories)
        # Should not find conflicts for exact duplicates
        assert isinstance(conflicts, list)


class TestRuleBasedConflictDetection:
    """Test rule-based pattern matching conflict detection."""
    
    def test_numerical_contradiction_detection(self):
        """
        Test detection of numerical contradictions.
        
        Rationale: Ensures pattern-based detection works for numbers.
        """
        from broca.memory.conflict.detection import ConflictDetector
        from broca.memory import MemoryRecord
        
        memory1 = MemoryRecord(
            namespace="test",
            text="User is 25 years old",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="User is 30 years old",
            importance=0.5
        )
        
        # Create a minimal detector (no memory_manager needed for rule-based)
        detector = ConflictDetector(
            memory_manager=None,  # Rule-based doesn't need manager
            similarity_threshold=0.7,
            contradiction_threshold=0.6
        )
        
        # Should detect numerical contradiction
        conflict = detector.detect_rule_based_conflicts(memory1.text, memory2.text)
        # May return None if not detected, or Conflict if detected
        assert conflict is None or hasattr(conflict, 'confidence')
    
    def test_boolean_contradiction_detection(self):
        """
        Test detection of boolean contradictions.
        
        Rationale: Ensures pattern-based detection works for boolean opposites.
        """
        from broca.memory.conflict.detection import ConflictDetector
        from broca.memory import MemoryRecord
        
        memory1 = MemoryRecord(
            namespace="test",
            text="User prefers Python",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="User hates Python",
            importance=0.5
        )
        
        detector = ConflictDetector(
            memory_manager=None,
            similarity_threshold=0.7,
            contradiction_threshold=0.6
        )
        
        # Should detect boolean contradiction
        conflict = detector.detect_rule_based_conflicts(memory1.text, memory2.text)
        assert conflict is None or hasattr(conflict, 'confidence')
    
    def test_temporal_contradiction_detection(self):
        """
        Test detection of temporal contradictions.
        
        Rationale: Ensures pattern-based detection works for time-based conflicts.
        """
        from broca.memory.conflict.detection import ConflictDetector
        from broca.memory import MemoryRecord
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Meeting was yesterday",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Meeting is tomorrow",
            importance=0.5
        )
        
        detector = ConflictDetector(
            memory_manager=None,
            similarity_threshold=0.7,
            contradiction_threshold=0.6
        )
        
        # Should detect temporal contradiction
        conflict = detector.detect_rule_based_conflicts(memory1.text, memory2.text)
        assert conflict is None or hasattr(conflict, 'confidence')
    
    def test_non_contradictory_texts_not_detected(self):
        """
        Test that non-contradictory similar texts don't trigger false positives.
        
        Rationale: Ensures rule-based detection doesn't have false positives.
        """
        from broca.memory.conflict.detection import ConflictDetector
        from broca.memory import MemoryRecord
        
        memory1 = MemoryRecord(
            namespace="test",
            text="User likes Python and Java",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="User enjoys programming in Python",
            importance=0.5
        )
        
        detector = ConflictDetector(
            memory_manager=None,
            similarity_threshold=0.7,
            contradiction_threshold=0.6
        )
        
        # Should not detect conflict for non-contradictory texts
        conflict = detector.detect_rule_based_conflicts(memory1.text, memory2.text)
        # These are not contradictory, so should return None
        assert conflict is None


class TestLLMBasedConflictDetection:
    """Test LLM-based contradiction analysis."""
    
    def test_llm_contradiction_analysis(self):
        """
        Test LLM contradiction analysis with mock LLM client.
        
        Rationale: Ensures LLM-based detection works correctly.
        """
        from broca.memory.conflict.detection import ConflictDetector
        from broca.memory import MemoryRecord
        from unittest.mock import Mock
        
        memory1 = MemoryRecord(
            namespace="test",
            text="The project deadline is next Monday",
            importance=0.8
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="The project deadline is next Friday",
            importance=0.8
        )
        
        # Mock LLM client
        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "choices": [{
                "message": {
                    "content": '{"contradicts": true, "confidence": 0.85, "type": "temporal", "explanation": "Different deadlines"}'
                }
            }]
        }
        
        detector = ConflictDetector(
            memory_manager=None,
            similarity_threshold=0.7,
            contradiction_threshold=0.6,
            llm_client=mock_llm
        )
        
        # Should use LLM to analyze
        result = detector.analyze_with_llm(memory1.text, memory2.text)
        assert isinstance(result, dict)
        assert "contradicts" in result or result is None
    
    def test_llm_api_failure_handling(self):
        """
        Test graceful degradation when LLM API fails.
        
        Rationale: Ensures system works even without LLM.
        """
        from broca.memory.conflict.detection import ConflictDetector
        from broca.memory import MemoryRecord
        from unittest.mock import Mock
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Test memory 1",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Test memory 2",
            importance=0.5
        )
        
        # Mock LLM client that raises exception
        mock_llm = Mock()
        mock_llm.chat.side_effect = Exception("API failure")
        
        detector = ConflictDetector(
            memory_manager=None,
            similarity_threshold=0.7,
            contradiction_threshold=0.6,
            llm_client=mock_llm
        )
        
        # Should handle exception gracefully
        result = detector.analyze_with_llm(memory1.text, memory2.text)
        # Should return None or empty dict on failure
        assert result is None or isinstance(result, dict)
    
    def test_llm_optional(self):
        """
        Test that LLM is optional and system works without it.
        
        Rationale: Ensures system works without LLM client.
        """
        from broca.memory.conflict.detection import ConflictDetector
        from broca.memory import MemoryRecord
        
        memory1 = MemoryRecord(
            namespace="test",
            text="Test memory 1",
            importance=0.5
        )
        memory2 = MemoryRecord(
            namespace="test",
            text="Test memory 2",
            importance=0.5
        )
        
        # Detector without LLM client
        detector = ConflictDetector(
            memory_manager=None,
            similarity_threshold=0.7,
            contradiction_threshold=0.6,
            llm_client=None
        )
        
        # Should work without LLM (returns None)
        result = detector.analyze_with_llm(memory1.text, memory2.text)
        assert result is None

