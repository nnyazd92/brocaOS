"""
Tests for conflict evolution tracking.

Tests tracking how conflicts between memories evolve over time.
"""

from __future__ import annotations

import tempfile
import os
from unittest.mock import Mock
import pytest
from datetime import datetime, timezone, timedelta

from broca.memory import MemoryRecord
from broca.memory.storage import MemoryStorage
from broca.memory.vector_index import VectorIndex
from broca.memory.embeddings import EmbeddingService
from broca.memory.manager import MemoryManager
from broca.memory.conflict.models import Conflict, Resolution
from broca.memory.conflict.logger import ConflictLogger

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    service = Mock(spec=EmbeddingService)
    def generate_embedding(text: str):
        hash_val = hash(text.lower()) % 1000
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


@pytest.fixture
def conflict_logger(temp_storage):
    """Conflict logger for testing."""
    return ConflictLogger(temp_storage)


class TestConflictEvolutionTracking:
    """Test conflict evolution tracking."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_tracks_conflict_history_between_memories(self, memory_manager, conflict_logger):
        """
        Test tracking conflict history between two specific memories.
        
        Rationale: Ensures we can retrieve all conflicts between two memories over time.
        """
        from broca.memory.conflict.evolution import ConflictEvolutionTracker
        
        # Create memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User prefers Python",
            importance=0.6
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="User prefers Java",
            importance=0.6
        )
        
        # Create multiple conflicts over time
        memory1 = memory_manager.get_memory(memory_id1)
        memory2 = memory_manager.get_memory(memory_id2)
        
        conflict1 = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.7,
            evidence="Initial conflict",
            resolution_strategy="recency"
        )
        
        resolution1 = Resolution(
            action="keep_new",
            kept_memory=memory2,
            archived_memory=memory1,
            rationale="Keep newer"
        )
        
        conflict_logger.log_conflict(conflict1, resolution1)
        
        # Create another conflict later
        import time
        time.sleep(0.1)
        
        conflict2 = Conflict(
            memory1=memory1,
            memory2=memory2,
            conflict_type="contradiction",
            confidence=0.8,
            evidence="Updated conflict",
            resolution_strategy="importance"
        )
        
        resolution2 = Resolution(
            action="keep_important",
            kept_memory=memory1,
            archived_memory=memory2,
            rationale="Keep more important"
        )
        
        conflict_logger.log_conflict(conflict2, resolution2)
        
        # Track history
        tracker = ConflictEvolutionTracker(conflict_logger.storage)
        history = tracker.track_conflict_history(memory_id1, memory_id2)
        
        # Should have 2 conflicts
        assert len(history) == 2
        assert history[0]["memory1_id"] == memory_id1
        assert history[0]["memory2_id"] == memory_id2
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_conflict_history_ordered_chronologically(self, memory_manager, conflict_logger):
        """
        Test that conflict history is ordered chronologically.
        
        Rationale: Ensures evolution can be tracked in time order.
        """
        from broca.memory.conflict.evolution import ConflictEvolutionTracker
        
        import time
        
        # Create memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Memory A",
            importance=0.6
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Memory B",
            importance=0.6
        )
        
        memory1 = memory_manager.get_memory(memory_id1)
        memory2 = memory_manager.get_memory(memory_id2)
        
        # Create conflicts at different times
        for i in range(3):
            conflict = Conflict(
                memory1=memory1,
                memory2=memory2,
                conflict_type="contradiction",
                confidence=0.7 + i * 0.05,
                evidence=f"Conflict {i+1}",
                resolution_strategy="recency"
            )
            
            resolution = Resolution(
                action="keep_new",
                kept_memory=memory2,
                archived_memory=memory1,
                rationale=f"Resolution {i+1}"
            )
            
            conflict_logger.log_conflict(conflict, resolution)
            time.sleep(0.1)
        
        # Track history
        tracker = ConflictEvolutionTracker(conflict_logger.storage)
        history = tracker.track_conflict_history(memory_id1, memory_id2)
        
        # Should be ordered chronologically (oldest first)
        assert len(history) == 3
        timestamps = [h["timestamp"] for h in history]
        assert timestamps == sorted(timestamps)
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_evolution_stats_show_confidence_changes(self, memory_manager, conflict_logger):
        """
        Test that evolution stats show changes in confidence over time.
        
        Rationale: Ensures we can track how conflict confidence evolves.
        """
        from broca.memory.conflict.evolution import ConflictEvolutionTracker
        
        import time
        
        # Create memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Memory A",
            importance=0.6
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Memory B",
            importance=0.6
        )
        
        memory1 = memory_manager.get_memory(memory_id1)
        memory2 = memory_manager.get_memory(memory_id2)
        
        # Create conflicts with varying confidence
        confidences = [0.6, 0.7, 0.8, 0.75]
        for conf in confidences:
            conflict = Conflict(
                memory1=memory1,
                memory2=memory2,
                conflict_type="contradiction",
                confidence=conf,
                evidence="Test conflict",
                resolution_strategy="recency"
            )
            
            resolution = Resolution(
                action="keep_new",
                kept_memory=memory2,
                archived_memory=memory1,
                rationale="Test"
            )
            
            conflict_logger.log_conflict(conflict, resolution)
            time.sleep(0.05)
        
        # Get evolution stats
        tracker = ConflictEvolutionTracker(conflict_logger.storage)
        stats = tracker.get_conflict_evolution_stats(memory_id1)
        
        # Should show confidence changes
        assert "confidence_changes" in stats or "confidence_history" in stats or "total_conflicts" in stats
        assert stats.get("total_conflicts", 0) >= 4
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_resolution_trends_analysis(self, memory_manager, conflict_logger):
        """
        Test resolution trends analysis.
        
        Rationale: Ensures we can analyze trends in conflict resolution over time.
        """
        from broca.memory.conflict.evolution import ConflictEvolutionTracker
        
        import time
        
        # Create multiple conflicts with different resolutions
        memory_ids = []
        for i in range(5):
            mem_id, _, _ = memory_manager.store_memory(
                namespace="test",
                text=f"Memory {i}",
                importance=0.6
            )
            memory_ids.append(mem_id)
        
        # Create conflicts with different resolution strategies
        strategies = ["recency", "importance", "recency", "merge", "recency"]
        
        for i in range(len(memory_ids) - 1):
            mem1 = memory_manager.get_memory(memory_ids[i])
            mem2 = memory_manager.get_memory(memory_ids[i+1])
            
            conflict = Conflict(
                memory1=mem1,
                memory2=mem2,
                conflict_type="contradiction",
                confidence=0.7,
                evidence="Test",
                resolution_strategy=strategies[i]
            )
            
            resolution = Resolution(
                action="keep_new" if strategies[i] == "recency" else "merge",
                kept_memory=mem2,
                archived_memory=mem1,
                rationale="Test"
            )
            
            conflict_logger.log_conflict(conflict, resolution)
            time.sleep(0.05)
        
        # Get resolution trends
        tracker = ConflictEvolutionTracker(conflict_logger.storage)
        trends = tracker.get_resolution_trends()
        
        # Should show trends
        assert isinstance(trends, dict)
        assert "by_strategy" in trends or "by_action" in trends or "total_resolutions" in trends
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_handles_memories_with_no_conflict_history(self, memory_manager, conflict_logger):
        """
        Test handling of memories with no conflict history.
        
        Rationale: Ensures graceful handling when no conflicts exist.
        """
        from broca.memory.conflict.evolution import ConflictEvolutionTracker
        
        # Create memories
        memory_id1, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Memory A",
            importance=0.6
        )
        
        memory_id2, _, _ = memory_manager.store_memory(
            namespace="test",
            text="Memory B",
            importance=0.6
        )
        
        # Track history (no conflicts logged)
        tracker = ConflictEvolutionTracker(conflict_logger.storage)
        history = tracker.track_conflict_history(memory_id1, memory_id2)
        
        # Should return empty list
        assert len(history) == 0
        
        # Stats should handle no conflicts
        stats = tracker.get_conflict_evolution_stats(memory_id1)
        assert isinstance(stats, dict)

