"""
Tests for EpistemicStorage.

Tests storage of detailed epistemic history (hybrid approach).
"""

from __future__ import annotations

import tempfile
import os
from pathlib import Path
import pytest
from datetime import datetime, timezone

from broca.self_model.epistemic.storage import EpistemicStorage
from broca.self_model.epistemic.models import (
    SourceType,
    SourceMetadata,
    ConfidenceMetrics,
    VerificationRecord,
    KnowledgeEvolution,
)
from broca.self_model.epistemic.ids import KnowledgeID


class TestEpistemicStorageInitialization:
    """Test EpistemicStorage initialization."""
    
    def test_init_creates_storage_file(self):
        """Test that initialization creates storage file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "epistemic_history.json")
            storage = EpistemicStorage(storage_path)
            
            assert Path(storage_path).exists()
    
    def test_init_loads_existing_data(self):
        """Test that initialization loads existing data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "epistemic_history.json")
            
            # Create initial storage
            storage1 = EpistemicStorage(storage_path)
            knowledge_id = "test_knowledge_1"
            
            record = VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="tool_test",
                result="confirmed"
            )
            storage1.add_verification_record(knowledge_id, record)
            storage1.save()
            
            # Load in new instance
            storage2 = EpistemicStorage(storage_path)
            history = storage2.get_verification_history(knowledge_id)
            
            assert len(history) == 1
            assert history[0].result == "confirmed"


class TestEpistemicStorageVerificationHistory:
    """Test verification history storage."""
    
    def test_add_verification_record(self):
        """Test adding verification records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EpistemicStorage(os.path.join(tmpdir, "test.json"))
            knowledge_id = "test_knowledge_1"
            
            record = VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="tool_test",
                result="confirmed",
                confidence_delta=0.1
            )
            
            storage.add_verification_record(knowledge_id, record)
            storage.save()
            
            history = storage.get_verification_history(knowledge_id)
            assert len(history) == 1
            assert history[0].result == "confirmed"
            assert history[0].confidence_delta == 0.1
    
    def test_multiple_verification_records(self):
        """Test storing multiple verification records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EpistemicStorage(os.path.join(tmpdir, "test.json"))
            knowledge_id = "test_knowledge_1"
            
            record1 = VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="tool_test",
                result="confirmed"
            )
            record2 = VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="memory_retrieval",
                result="confirmed"
            )
            
            storage.add_verification_record(knowledge_id, record1)
            storage.add_verification_record(knowledge_id, record2)
            storage.save()
            
            history = storage.get_verification_history(knowledge_id)
            assert len(history) == 2
    
    def test_get_verification_history_nonexistent(self):
        """Test getting verification history for nonexistent knowledge."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EpistemicStorage(os.path.join(tmpdir, "test.json"))
            
            history = storage.get_verification_history("nonexistent")
            assert history == []


class TestEpistemicStorageKnowledgeEvolution:
    """Test knowledge evolution storage."""
    
    def test_add_knowledge_evolution(self):
        """Test adding knowledge evolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EpistemicStorage(os.path.join(tmpdir, "test.json"))
            knowledge_id = "test_knowledge_1"
            
            evolution = KnowledgeEvolution(
                creation_event={
                    "timestamp": datetime.now(timezone.utc),
                    "initial_confidence": 0.7,
                    "initial_source": SourceMetadata(source_type=SourceType.USER_PROVIDED)
                }
            )
            
            storage.add_knowledge_evolution(knowledge_id, evolution)
            storage.save()
            
            retrieved = storage.get_knowledge_evolution(knowledge_id)
            assert retrieved is not None
            assert retrieved.creation_event["initial_confidence"] == 0.7
    
    def test_update_knowledge_evolution(self):
        """Test updating knowledge evolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EpistemicStorage(os.path.join(tmpdir, "test.json"))
            knowledge_id = "test_knowledge_1"
            
            evolution1 = KnowledgeEvolution(
                creation_event={
                    "timestamp": datetime.now(timezone.utc),
                    "initial_confidence": 0.7,
                    "initial_source": SourceMetadata(source_type=SourceType.USER_PROVIDED)
                }
            )
            
            storage.add_knowledge_evolution(knowledge_id, evolution1)
            storage.save()
            
            # Add verification to evolution
            record = VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="tool_test",
                result="confirmed"
            )
            evolution1.verification_history.append(record)
            
            storage.add_knowledge_evolution(knowledge_id, evolution1)
            storage.save()
            
            retrieved = storage.get_knowledge_evolution(knowledge_id)
            assert len(retrieved.verification_history) == 1


class TestEpistemicStoragePersistence:
    """Test storage persistence."""
    
    def test_save_and_load(self):
        """Test that data persists across save/load cycles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "test.json")
            
            # Create and save data
            storage1 = EpistemicStorage(storage_path)
            knowledge_id = "test_knowledge_1"
            
            record = VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="tool_test",
                result="confirmed"
            )
            storage1.add_verification_record(knowledge_id, record)
            storage1.save()
            
            # Load in new instance
            storage2 = EpistemicStorage(storage_path)
            history = storage2.get_verification_history(knowledge_id)
            
            assert len(history) == 1
            assert history[0].result == "confirmed"
    
    def test_auto_save(self):
        """Test automatic saving on changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "test.json")
            storage = EpistemicStorage(storage_path, auto_save=True)
            
            knowledge_id = "test_knowledge_1"
            record = VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="tool_test",
                result="confirmed"
            )
            
            storage.add_verification_record(knowledge_id, record)
            # Should auto-save
            
            # Load in new instance to verify
            storage2 = EpistemicStorage(storage_path)
            history = storage2.get_verification_history(knowledge_id)
            
            assert len(history) == 1


class TestEpistemicStorageQueries:
    """Test query methods."""
    
    def test_get_all_knowledge_ids(self):
        """Test getting all knowledge IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EpistemicStorage(os.path.join(tmpdir, "test.json"))
            
            storage.add_verification_record("k1", VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="tool_test",
                result="confirmed"
            ))
            storage.add_verification_record("k2", VerificationRecord(
                timestamp=datetime.now(timezone.utc),
                verification_type="tool_test",
                result="confirmed"
            ))
            storage.add_knowledge_evolution("k3", KnowledgeEvolution(
                creation_event={
                    "timestamp": datetime.now(timezone.utc),
                    "initial_confidence": 0.7,
                    "initial_source": SourceMetadata(source_type=SourceType.USER_PROVIDED)
                }
            ))
            storage.save()
            
            all_ids = storage.get_all_knowledge_ids()
            assert "k1" in all_ids
            assert "k2" in all_ids
            assert "k3" in all_ids
    
    def test_get_verification_count(self):
        """Test getting verification count for knowledge."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EpistemicStorage(os.path.join(tmpdir, "test.json"))
            knowledge_id = "test_knowledge_1"
            
            for i in range(5):
                record = VerificationRecord(
                    timestamp=datetime.now(timezone.utc),
                    verification_type="tool_test",
                    result="confirmed"
                )
                storage.add_verification_record(knowledge_id, record)
            
            storage.save()
            
            count = storage.get_verification_count(knowledge_id)
            assert count == 5

