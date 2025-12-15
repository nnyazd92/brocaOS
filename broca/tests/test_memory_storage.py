"""
Tests for MemoryStorage SQLite backend.

Tests database operations, CRUD, and search functionality.
"""

from __future__ import annotations

import tempfile
import os
from pathlib import Path
import pytest
from datetime import datetime, timezone

from broca.memory import MemoryRecord
from broca.memory.storage import MemoryStorage


class TestMemoryStorageInitialization:
    """Test MemoryStorage initialization."""
    
    def test_init_creates_database(self):
        """
        Test that initialization creates database file.
        
        Rationale: Ensures database is created automatically.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            assert Path(db_path).exists()
            storage.close()
    
    def test_init_creates_tables(self):
        """
        Test that initialization creates required tables.
        
        Rationale: Ensures database schema is set up correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Verify table exists by trying to query it
            cursor = storage._connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
            result = cursor.fetchone()
            
            assert result is not None
            storage.close()
    
    def test_init_creates_indexes(self):
        """
        Test that initialization creates indexes.
        
        Rationale: Ensures indexes are created for efficient queries.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            cursor = storage._connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            assert "idx_namespace" in indexes
            assert "idx_importance" in indexes
            assert "idx_last_used" in indexes
            storage.close()


class TestMemoryStorageStoreMemory:
    """Test storing memories."""
    
    def test_store_memory_success(self):
        """
        Test storing a memory successfully.
        
        Rationale: Ensures memories can be stored in the database.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record = MemoryRecord(
                namespace="test.namespace",
                tags=["tag1", "tag2"],
                text="Test memory",
                importance=0.7
            )
            
            memory_id = storage.store_memory(record)
            
            assert memory_id is not None
            assert memory_id > 0
            storage.close()
    
    def test_store_memory_returns_auto_increment_id(self):
        """
        Test that stored memories get auto-increment IDs.
        
        Rationale: Ensures IDs are generated correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record1 = MemoryRecord(namespace="test", text="Memory 1", importance=0.5)
            record2 = MemoryRecord(namespace="test", text="Memory 2", importance=0.5)
            
            id1 = storage.store_memory(record1)
            id2 = storage.store_memory(record2)
            
            assert id2 > id1
            storage.close()
    
    def test_store_memory_persists_data(self):
        """
        Test that stored data persists correctly.
        
        Rationale: Ensures all fields are stored accurately.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record = MemoryRecord(
                namespace="math.sage.api",
                tags=["api-change", "sage"],
                text="SageMath API changed",
                importance=0.8
            )
            
            memory_id = storage.store_memory(record)
            retrieved = storage.get_memory(memory_id)
            
            assert retrieved is not None
            assert retrieved.namespace == "math.sage.api"
            assert retrieved.tags == ["api-change", "sage"]
            assert retrieved.text == "SageMath API changed"
            assert retrieved.importance == 0.8
            storage.close()


class TestMemoryStorageGetMemory:
    """Test retrieving memories."""
    
    def test_get_memory_success(self):
        """
        Test retrieving a memory by ID.
        
        Rationale: Ensures memories can be retrieved by ID.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record = MemoryRecord(namespace="test", text="Test", importance=0.5)
            memory_id = storage.store_memory(record)
            
            retrieved = storage.get_memory(memory_id)
            
            assert retrieved is not None
            assert retrieved.id == memory_id
            assert retrieved.text == "Test"
            storage.close()
    
    def test_get_memory_not_found(self):
        """
        Test retrieving non-existent memory returns None.
        
        Rationale: Ensures graceful handling of missing memories.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            result = storage.get_memory(999)
            
            assert result is None
            storage.close()
    
    def test_get_memory_preserves_timestamps(self):
        """
        Test that timestamps are preserved correctly.
        
        Rationale: Ensures datetime fields are stored and retrieved accurately.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            created = datetime.now(timezone.utc)
            record = MemoryRecord(
                namespace="test",
                text="Test",
                importance=0.5,
                created_at=created,
                last_used_at=created
            )
            
            memory_id = storage.store_memory(record)
            retrieved = storage.get_memory(memory_id)
            
            assert retrieved is not None
            assert retrieved.created_at.isoformat() == created.isoformat()
            storage.close()


class TestMemoryStorageUpdateLastUsed:
    """Test updating last_used_at timestamp."""
    
    def test_update_last_used(self):
        """
        Test updating last_used_at timestamp.
        
        Rationale: Ensures timestamps can be updated for tracking usage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record = MemoryRecord(namespace="test", text="Test", importance=0.5)
            memory_id = storage.store_memory(record)
            
            original = storage.get_memory(memory_id)
            assert original is not None
            original_time = original.last_used_at
            
            import time
            time.sleep(0.01)
            
            storage.update_last_used(memory_id)
            updated = storage.get_memory(memory_id)
            
            assert updated is not None
            assert updated.last_used_at > original_time
            storage.close()


class TestMemoryStorageSearchByNamespace:
    """Test namespace search."""
    
    def test_search_by_namespace_exact_match(self):
        """
        Test searching by exact namespace match.
        
        Rationale: Ensures exact namespace matches are found.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            storage.store_memory(MemoryRecord(namespace="math.sage", text="Memory 1", importance=0.5))
            storage.store_memory(MemoryRecord(namespace="math.sage.api", text="Memory 2", importance=0.5))
            storage.store_memory(MemoryRecord(namespace="other", text="Memory 3", importance=0.5))
            
            results = storage.search_by_namespace("math.sage")
            
            assert len(results) >= 2
            namespaces = [r.namespace for r in results]
            assert "math.sage" in namespaces or "math.sage.api" in namespaces
            storage.close()
    
    def test_search_by_namespace_fuzzy_match(self):
        """
        Test searching by partial namespace (fuzzy match).
        
        Rationale: Ensures LIKE pattern matching works for fuzzy searches.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            storage.store_memory(MemoryRecord(namespace="math.sage.api", text="Memory 1", importance=0.5))
            storage.store_memory(MemoryRecord(namespace="math.sage.core", text="Memory 2", importance=0.5))
            storage.store_memory(MemoryRecord(namespace="other", text="Memory 3", importance=0.5))
            
            results = storage.search_by_namespace("sage", limit=10)
            
            assert len(results) >= 2
            namespaces = [r.namespace for r in results]
            assert all("sage" in ns for ns in namespaces)
            storage.close()
    
    def test_search_by_namespace_respects_limit(self):
        """
        Test that namespace search respects limit.
        
        Rationale: Ensures limit parameter works correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            for i in range(10):
                storage.store_memory(
                    MemoryRecord(namespace="test", text=f"Memory {i}", importance=0.5)
                )
            
            results = storage.search_by_namespace("test", limit=5)
            
            assert len(results) <= 5
            storage.close()


class TestMemoryStorageSearchByTags:
    """Test tag-based search."""
    
    def test_search_by_tags_single_tag(self):
        """
        Test searching by a single tag.
        
        Rationale: Ensures tag-based search finds matching memories.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            storage.store_memory(
                MemoryRecord(namespace="test", text="Memory 1", importance=0.5, tags=["tag1", "tag2"])
            )
            storage.store_memory(
                MemoryRecord(namespace="test", text="Memory 2", importance=0.5, tags=["tag2", "tag3"])
            )
            storage.store_memory(
                MemoryRecord(namespace="test", text="Memory 3", importance=0.5, tags=["tag4"])
            )
            
            results = storage.search_by_tags(["tag2"], limit=10)
            
            assert len(results) >= 2
            assert all("tag2" in r.tags for r in results)
            storage.close()
    
    def test_search_by_tags_multiple_tags(self):
        """
        Test searching by multiple tags (OR logic).
        
        Rationale: Ensures memories with any of the tags are found.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            storage.store_memory(
                MemoryRecord(namespace="test", text="Memory 1", importance=0.5, tags=["tag1"])
            )
            storage.store_memory(
                MemoryRecord(namespace="test", text="Memory 2", importance=0.5, tags=["tag2"])
            )
            storage.store_memory(
                MemoryRecord(namespace="test", text="Memory 3", importance=0.5, tags=["tag3"])
            )
            
            results = storage.search_by_tags(["tag1", "tag2"], limit=10)
            
            assert len(results) >= 2
            tags_found = set()
            for r in results:
                tags_found.update(r.tags)
            assert "tag1" in tags_found or "tag2" in tags_found
            storage.close()
    
    def test_search_by_tags_empty_list(self):
        """
        Test searching with empty tags list returns empty results.
        
        Rationale: Ensures empty tag list is handled gracefully.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            results = storage.search_by_tags([])
            
            assert results == []
            storage.close()


class TestMemoryStorageGetAllMemories:
    """Test retrieving all memories."""
    
    def test_get_all_memories(self):
        """
        Test retrieving all memories.
        
        Rationale: Ensures all memories can be retrieved for index sync.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            for i in range(5):
                storage.store_memory(
                    MemoryRecord(namespace="test", text=f"Memory {i}", importance=0.5)
                )
            
            all_memories = storage.get_all_memories()
            
            assert len(all_memories) == 5
            storage.close()
    
    def test_get_all_memories_with_limit(self):
        """
        Test retrieving all memories with limit.
        
        Rationale: Ensures limit parameter works for bulk retrieval.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            for i in range(10):
                storage.store_memory(
                    MemoryRecord(namespace="test", text=f"Memory {i}", importance=0.5)
                )
            
            all_memories = storage.get_all_memories(limit=5)
            
            assert len(all_memories) == 5
            storage.close()


class TestMemoryStorageEmbeddings:
    """Test embedding storage and retrieval."""
    
    def test_store_memory_with_embedding(self):
        """
        Test storing a memory with an embedding.
        
        Rationale: Ensures embeddings can be stored in the database.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record = MemoryRecord(
                namespace="test.namespace",
                tags=["tag1"],
                text="Test memory",
                importance=0.7
            )
            embedding = [0.1, 0.2, 0.3] * 512  # 1536-dim embedding
            
            memory_id = storage.store_memory(record, embedding=embedding)
            
            assert memory_id is not None
            # Verify embedding was stored
            retrieved = storage.get_memory(memory_id)
            assert retrieved is not None
            assert retrieved.embedding == embedding
            
            storage.close()
    
    def test_store_memory_without_embedding(self):
        """
        Test storing a memory without an embedding (backward compatibility).
        
        Rationale: Ensures backward compatibility with existing code.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record = MemoryRecord(
                namespace="test.namespace",
                tags=["tag1"],
                text="Test memory",
                importance=0.7
            )
            
            memory_id = storage.store_memory(record)
            
            assert memory_id is not None
            retrieved = storage.get_memory(memory_id)
            assert retrieved is not None
            assert retrieved.embedding is None
            
            storage.close()
    
    def test_get_embedding_retrieves_stored_embedding(self):
        """
        Test that get_embedding retrieves the stored embedding.
        
        Rationale: Ensures embeddings can be retrieved independently.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record = MemoryRecord(
                namespace="test.namespace",
                tags=["tag1"],
                text="Test memory",
                importance=0.7
            )
            embedding = [0.1, 0.2, 0.3] * 512  # 1536-dim embedding
            
            memory_id = storage.store_memory(record, embedding=embedding)
            
            retrieved_embedding = storage.get_embedding(memory_id)
            assert retrieved_embedding == embedding
            
            storage.close()
    
    def test_get_embedding_returns_none_if_not_stored(self):
        """
        Test that get_embedding returns None if no embedding was stored.
        
        Rationale: Ensures graceful handling of missing embeddings.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            record = MemoryRecord(
                namespace="test.namespace",
                tags=["tag1"],
                text="Test memory",
                importance=0.7
            )
            
            memory_id = storage.store_memory(record)
            
            retrieved_embedding = storage.get_embedding(memory_id)
            assert retrieved_embedding is None
            
            storage.close()
    
    def test_embedding_persists_across_restarts(self):
        """
        Test that embeddings persist when storage is closed and reopened.
        
        Rationale: Ensures embeddings are actually persisted to disk.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            record = MemoryRecord(
                namespace="test.namespace",
                tags=["tag1"],
                text="Test memory",
                importance=0.7
            )
            embedding = [0.1, 0.2, 0.3] * 512  # 1536-dim embedding
            
            memory_id = storage.store_memory(record, embedding=embedding)
            storage.close()
            
            # Reopen storage (within same temp directory context)
            storage2 = MemoryStorage(db_path)
            retrieved = storage2.get_memory(memory_id)
            assert retrieved is not None
            assert retrieved.embedding == embedding
            
            storage2.close()
    
    def test_all_memories_include_embeddings(self):
        """
        Test that get_all_memories includes embeddings.
        
        Rationale: Ensures embeddings are loaded when retrieving all memories.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Store memories with and without embeddings
            record1 = MemoryRecord(
                namespace="test.ns1",
                tags=[],
                text="Memory 1",
                importance=0.7
            )
            embedding1 = [0.1] * 1536
            memory_id1 = storage.store_memory(record1, embedding=embedding1)
            
            record2 = MemoryRecord(
                namespace="test.ns2",
                tags=[],
                text="Memory 2",
                importance=0.8
            )
            memory_id2 = storage.store_memory(record2)
            
            all_memories = storage.get_all_memories()
            assert len(all_memories) == 2
            
            mem1 = next(m for m in all_memories if m.id == memory_id1)
            mem2 = next(m for m in all_memories if m.id == memory_id2)
            
            assert mem1.embedding == embedding1
            assert mem2.embedding is None
            
            storage.close()


class TestMemoryStorageDeleteMemory:
    """Test deleting memories."""
    
    def test_delete_memory_success(self):
        """
        Test deleting a memory successfully.
        
        Rationale: Ensures memories can be deleted from the database.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Store a memory
            record = MemoryRecord(
                namespace="test.namespace",
                tags=["tag1"],
                text="Test memory",
                importance=0.7
            )
            memory_id = storage.store_memory(record)
            
            # Verify it exists
            assert storage.get_memory(memory_id) is not None
            
            # Delete it
            success = storage.delete_memory(memory_id)
            
            assert success is True
            assert storage.get_memory(memory_id) is None
            
            storage.close()
    
    def test_delete_memory_nonexistent(self):
        """
        Test deleting non-existent memory returns False.
        
        Rationale: Ensures graceful handling of deletion of non-existent memories.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Try to delete non-existent memory
            success = storage.delete_memory(99999)
            
            assert success is False
            storage.close()
    
    def test_delete_memory_removes_from_get_all(self):
        """
        Test that deleted memory is removed from get_all_memories().
        
        Rationale: Ensures deletion is reflected in queries.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Store multiple memories
            memory_ids = []
            for i in range(3):
                record = MemoryRecord(
                    namespace=f"test.ns{i}",
                    tags=[],
                    text=f"Memory {i}",
                    importance=0.5
                )
                mem_id = storage.store_memory(record)
                memory_ids.append(mem_id)
            
            # Verify all are present
            all_memories = storage.get_all_memories()
            assert len(all_memories) == 3
            
            # Delete one
            storage.delete_memory(memory_ids[1])
            
            # Verify it's removed
            all_memories = storage.get_all_memories()
            assert len(all_memories) == 2
            remaining_ids = {m.id for m in all_memories}
            assert memory_ids[0] in remaining_ids
            assert memory_ids[1] not in remaining_ids
            assert memory_ids[2] in remaining_ids
            
            storage.close()
    
    def test_delete_memory_removes_from_search(self):
        """
        Test that deleted memory is removed from search results.
        
        Rationale: Ensures deletion is reflected in search queries.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Store memories
            record1 = MemoryRecord(
                namespace="test.ns1",
                tags=["tag1"],
                text="Memory to keep",
                importance=0.7
            )
            record2 = MemoryRecord(
                namespace="test.ns1",
                tags=["tag1"],
                text="Memory to delete",
                importance=0.8
            )
            
            mem_id1 = storage.store_memory(record1)
            mem_id2 = storage.store_memory(record2)
            
            # Search should find both
            results = storage.search_by_namespace("test.ns1", limit=10)
            assert len(results) == 2
            
            # Delete one
            storage.delete_memory(mem_id2)
            
            # Search should only find remaining one
            results = storage.search_by_namespace("test.ns1", limit=10)
            assert len(results) == 1
            assert results[0].id == mem_id1
            
            storage.close()
    
    def test_delete_memory_preserves_other_memories(self):
        """
        Test that deleting one memory doesn't affect others.
        
        Rationale: Ensures deletion is isolated to the specified memory.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Store multiple memories with different properties
            records = []
            for i in range(5):
                record = MemoryRecord(
                    namespace=f"test.ns{i}",
                    tags=[f"tag{i}"],
                    text=f"Memory {i}",
                    importance=0.5 + i * 0.1
                )
                mem_id = storage.store_memory(record)
                records.append((mem_id, record))
            
            # Delete middle one
            delete_id, delete_record = records[2]
            storage.delete_memory(delete_id)
            
            # Verify others are still present
            all_memories = storage.get_all_memories()
            assert len(all_memories) == 4
            
            remaining_ids = {m.id for m in all_memories}
            for mem_id, _ in records:
                if mem_id != delete_id:
                    assert mem_id in remaining_ids
                else:
                    assert mem_id not in remaining_ids
            
            storage.close()

