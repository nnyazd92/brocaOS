"""
Tests for relationship table migration and backward compatibility.

Tests that existing databases get relationship tables and existing functionality is unchanged.
"""

from __future__ import annotations

import tempfile
import os
import pytest
import sqlite3

from broca.memory import MemoryRecord, RelationshipRecord
from broca.memory.storage import MemoryStorage


class TestRelationshipTableMigration:
    """Test relationship table migration."""
    
    def test_existing_database_gets_relationship_tables(self):
        """
        Test that existing databases get relationship tables on initialization.
        
        Rationale: Ensures backward compatibility - existing databases are upgraded.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            
            # Create database with only memories table (simulating old database)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    namespace TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    text TEXT NOT NULL,
                    importance REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
            
            # Initialize MemoryStorage (should create relationship tables)
            storage = MemoryStorage(db_path)
            
            # Verify relationship table exists
            cursor = storage._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='memory_relationships'
            """)
            result = cursor.fetchone()
            
            assert result is not None
            storage.close()
    
    def test_existing_functionality_unchanged(self):
        """
        Test that existing memory functionality is unchanged.
        
        Rationale: Ensures relationship tables don't break existing operations.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Test storing memory (existing functionality)
            record = MemoryRecord(
                namespace="test.ns1",
                text="Test memory",
                importance=0.7
            )
            memory_id = storage.store_memory(record)
            
            assert memory_id > 0
            
            # Test retrieving memory (existing functionality)
            retrieved = storage.get_memory(memory_id)
            assert retrieved is not None
            assert retrieved.text == "Test memory"
            
            # Test updating memory (existing functionality)
            success = storage.update_memory(memory_id, 0.8, ["tag1"])
            assert success is True
            
            # Test deleting memory (existing functionality)
            success = storage.delete_memory(memory_id)
            assert success is True
            
            # Verify deleted
            retrieved = storage.get_memory(memory_id)
            assert retrieved is None
            
            storage.close()
    
    def test_cascade_delete_behavior(self):
        """
        Test that CASCADE delete works correctly.
        
        Rationale: Ensures relationships are deleted when memories are deleted.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            # Create memories
            mem_id1 = storage.store_memory(MemoryRecord(
                namespace="test.ns1", text="Memory 1", importance=0.7
            ))
            mem_id2 = storage.store_memory(MemoryRecord(
                namespace="test.ns2", text="Memory 2", importance=0.8
            ))
            
            # Create relationship
            from broca.memory import RelationshipRecord, RelationType
            rel_record = RelationshipRecord(
                source_id=mem_id1,
                target_id=mem_id2,
                relation_type=RelationType.SUPPORTS
            )
            rel_id = storage.store_relationship(rel_record)
            assert rel_id > 0
            
            # Verify relationship exists
            relationships = storage.get_relationships(source_id=mem_id1)
            assert len(relationships) == 1
            
            # Delete source memory
            storage.delete_memory(mem_id1)
            
            # Verify relationship was deleted (CASCADE)
            relationships = storage.get_relationships(source_id=mem_id1)
            assert len(relationships) == 0
            
            # Verify target memory still exists
            mem2 = storage.get_memory(mem_id2)
            assert mem2 is not None
            
            storage.close()
    
    def test_relationship_tables_created_on_first_init(self):
        """
        Test that relationship tables are created on first initialization.
        
        Rationale: Ensures new databases get relationship tables.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "new.db")
            
            # Initialize new database
            storage = MemoryStorage(db_path)
            
            # Verify both tables exist
            cursor = storage._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('memories', 'memory_relationships')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            assert "memories" in tables
            assert "memory_relationships" in tables
            
            storage.close()
    
    def test_relationship_indexes_created(self):
        """
        Test that relationship indexes are created.
        
        Rationale: Ensures indexes exist for fast queries.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = MemoryStorage(db_path)
            
            cursor = storage._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_rel%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            assert "idx_rel_source" in indexes
            assert "idx_rel_target" in indexes
            assert "idx_rel_type" in indexes
            assert "idx_rel_strength" in indexes
            
            storage.close()

