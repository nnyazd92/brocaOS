"""
Tests for memory relationship storage.

Tests database operations for relationships (CRUD).
"""

from __future__ import annotations

import tempfile
import os
import pytest
from datetime import datetime, timezone

from broca.memory import MemoryRecord, RelationType, RelationshipRecord
from broca.memory.storage import MemoryStorage


class TestRelationshipStorageTableCreation:
    """Test relationship table creation."""
    
    def test_relationship_tables_created(self):
        """
        Test that relationship tables are created on initialization.
        
        Rationale: Ensures database schema includes relationship tables.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
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


class TestRelationshipStorageCRUD:
    """Test relationship CRUD operations."""
    
    def test_store_relationship_success(self):
        """
        Test storing a relationship successfully.
        
        Rationale: Ensures relationships can be stored in database.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Create two memories first
            record1 = MemoryRecord(
                namespace="test.ns1",
                text="Memory 1",
                importance=0.7
            )
            record2 = MemoryRecord(
                namespace="test.ns2",
                text="Memory 2",
                importance=0.8
            )
            
            mem_id1 = storage.store_memory(record1)
            mem_id2 = storage.store_memory(record2)
            
            # Store relationship
            rel_record = RelationshipRecord(
                source_id=mem_id1,
                target_id=mem_id2,
                relation_type=RelationType.SUPPORTS,
                strength=0.9
            )
            
            rel_id = storage.store_relationship(rel_record)
            
            assert rel_id > 0
            storage.close()
    
    def test_get_relationships_by_source(self):
        """
        Test retrieving relationships by source memory ID.
        
        Rationale: Ensures outgoing relationships can be queried.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Create memories
            mem_id1 = storage.store_memory(MemoryRecord(
                namespace="test.ns1", text="Memory 1", importance=0.7
            ))
            mem_id2 = storage.store_memory(MemoryRecord(
                namespace="test.ns2", text="Memory 2", importance=0.8
            ))
            mem_id3 = storage.store_memory(MemoryRecord(
                namespace="test.ns3", text="Memory 3", importance=0.6
            ))
            
            # Create relationships
            rel1 = RelationshipRecord(
                source_id=mem_id1,
                target_id=mem_id2,
                relation_type=RelationType.SUPPORTS
            )
            rel2 = RelationshipRecord(
                source_id=mem_id1,
                target_id=mem_id3,
                relation_type=RelationType.CONTRADICTS
            )
            
            storage.store_relationship(rel1)
            storage.store_relationship(rel2)
            
            # Get relationships from mem_id1
            relationships = storage.get_relationships(source_id=mem_id1)
            
            assert len(relationships) == 2
            rel_types = {r.relation_type for r in relationships}
            assert RelationType.SUPPORTS in rel_types
            assert RelationType.CONTRADICTS in rel_types
            
            storage.close()
    
    def test_get_relationships_by_target(self):
        """
        Test retrieving relationships by target memory ID.
        
        Rationale: Ensures incoming relationships can be queried.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Create memories
            mem_id1 = storage.store_memory(MemoryRecord(
                namespace="test.ns1", text="Memory 1", importance=0.7
            ))
            mem_id2 = storage.store_memory(MemoryRecord(
                namespace="test.ns2", text="Memory 2", importance=0.8
            ))
            mem_id3 = storage.store_memory(MemoryRecord(
                namespace="test.ns3", text="Memory 3", importance=0.6
            ))
            
            # Create relationships pointing to mem_id2
            rel1 = RelationshipRecord(
                source_id=mem_id1,
                target_id=mem_id2,
                relation_type=RelationType.ELABORATES
            )
            rel2 = RelationshipRecord(
                source_id=mem_id3,
                target_id=mem_id2,
                relation_type=RelationType.REFERENCES
            )
            
            storage.store_relationship(rel1)
            storage.store_relationship(rel2)
            
            # Get relationships to mem_id2
            relationships = storage.get_relationships(target_id=mem_id2)
            
            assert len(relationships) == 2
            rel_types = {r.relation_type for r in relationships}
            assert RelationType.ELABORATES in rel_types
            assert RelationType.REFERENCES in rel_types
            
            storage.close()
    
    def test_get_relationships_by_type(self):
        """
        Test retrieving relationships by type.
        
        Rationale: Ensures relationships can be filtered by type.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Create memories
            mem_id1 = storage.store_memory(MemoryRecord(
                namespace="test.ns1", text="Memory 1", importance=0.7
            ))
            mem_id2 = storage.store_memory(MemoryRecord(
                namespace="test.ns2", text="Memory 2", importance=0.8
            ))
            mem_id3 = storage.store_memory(MemoryRecord(
                namespace="test.ns3", text="Memory 3", importance=0.6
            ))
            
            # Create relationships of different types
            storage.store_relationship(RelationshipRecord(
                source_id=mem_id1, target_id=mem_id2,
                relation_type=RelationType.CONTRADICTS
            ))
            storage.store_relationship(RelationshipRecord(
                source_id=mem_id1, target_id=mem_id3,
                relation_type=RelationType.SUPPORTS
            ))
            storage.store_relationship(RelationshipRecord(
                source_id=mem_id2, target_id=mem_id3,
                relation_type=RelationType.CONTRADICTS
            ))
            
            # Get only CONTRADICTS relationships
            relationships = storage.get_relationships(relation_type=RelationType.CONTRADICTS)
            
            assert len(relationships) == 2
            assert all(r.relation_type == RelationType.CONTRADICTS for r in relationships)
            
            storage.close()
    
    def test_delete_relationship(self):
        """
        Test deleting a relationship.
        
        Rationale: Ensures relationships can be removed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Create memories and relationship
            mem_id1 = storage.store_memory(MemoryRecord(
                namespace="test.ns1", text="Memory 1", importance=0.7
            ))
            mem_id2 = storage.store_memory(MemoryRecord(
                namespace="test.ns2", text="Memory 2", importance=0.8
            ))
            
            rel_id = storage.store_relationship(RelationshipRecord(
                source_id=mem_id1,
                target_id=mem_id2,
                relation_type=RelationType.SUPPORTS
            ))
            
            # Verify it exists
            relationships = storage.get_relationships(source_id=mem_id1)
            assert len(relationships) == 1
            
            # Delete it
            success = storage.delete_relationship(rel_id)
            assert success is True
            
            # Verify it's gone
            relationships = storage.get_relationships(source_id=mem_id1)
            assert len(relationships) == 0
            
            storage.close()
    
    def test_delete_relationship_nonexistent(self):
        """
        Test deleting non-existent relationship returns False.
        
        Rationale: Ensures graceful handling of deletion of non-existent relationships.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            success = storage.delete_relationship(99999)
            assert success is False
            
            storage.close()
    
    def test_relationship_unique_constraint(self):
        """
        Test that UNIQUE constraint prevents duplicate relationships.
        
        Rationale: Ensures same relationship can't be stored twice.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Create memories
            mem_id1 = storage.store_memory(MemoryRecord(
                namespace="test.ns1", text="Memory 1", importance=0.7
            ))
            mem_id2 = storage.store_memory(MemoryRecord(
                namespace="test.ns2", text="Memory 2", importance=0.8
            ))
            
            # Store relationship
            rel_record = RelationshipRecord(
                source_id=mem_id1,
                target_id=mem_id2,
                relation_type=RelationType.SUPPORTS
            )
            rel_id = storage.store_relationship(rel_record)
            
            # Try to store same relationship again
            # Our implementation handles UNIQUE constraint gracefully by returning existing ID
            rel_id2 = storage.store_relationship(rel_record)
            assert rel_id2 == rel_id  # Should return same ID
            
            storage.close()
    
    def test_cascade_delete_when_memory_deleted(self):
        """
        Test that relationships are deleted when memory is deleted (CASCADE).
        
        Rationale: Ensures referential integrity with CASCADE delete.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Create memories
            mem_id1 = storage.store_memory(MemoryRecord(
                namespace="test.ns1", text="Memory 1", importance=0.7
            ))
            mem_id2 = storage.store_memory(MemoryRecord(
                namespace="test.ns2", text="Memory 2", importance=0.8
            ))
            mem_id3 = storage.store_memory(MemoryRecord(
                namespace="test.ns3", text="Memory 3", importance=0.6
            ))
            
            # Create relationships
            storage.store_relationship(RelationshipRecord(
                source_id=mem_id1, target_id=mem_id2,
                relation_type=RelationType.SUPPORTS
            ))
            storage.store_relationship(RelationshipRecord(
                source_id=mem_id1, target_id=mem_id3,
                relation_type=RelationType.CONTRADICTS
            ))
            storage.store_relationship(RelationshipRecord(
                source_id=mem_id2, target_id=mem_id3,
                relation_type=RelationType.ELABORATES
            ))
            
            # Verify relationships exist
            assert len(storage.get_relationships(source_id=mem_id1)) == 2
            assert len(storage.get_relationships(target_id=mem_id2)) == 1
            
            # Delete mem_id1
            storage.delete_memory(mem_id1)
            
            # Relationships from/to mem_id1 should be deleted (CASCADE)
            assert len(storage.get_relationships(source_id=mem_id1)) == 0
            assert len(storage.get_relationships(target_id=mem_id1)) == 0
            
            # Relationship from mem_id2 to mem_id3 should still exist
            assert len(storage.get_relationships(source_id=mem_id2)) == 1
            
            storage.close()
    
    def test_get_related_memories(self):
        """
        Test getting related memories for a given memory.
        
        Rationale: Ensures related memories can be retrieved efficiently.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = MemoryStorage(os.path.join(tmpdir, "test.db"))
            
            # Create memories
            mem_id1 = storage.store_memory(MemoryRecord(
                namespace="test.ns1", text="Memory 1", importance=0.7
            ))
            mem_id2 = storage.store_memory(MemoryRecord(
                namespace="test.ns2", text="Memory 2", importance=0.8
            ))
            mem_id3 = storage.store_memory(MemoryRecord(
                namespace="test.ns3", text="Memory 3", importance=0.6
            ))
            
            # Create relationships
            storage.store_relationship(RelationshipRecord(
                source_id=mem_id1, target_id=mem_id2,
                relation_type=RelationType.SUPPORTS, strength=0.9
            ))
            storage.store_relationship(RelationshipRecord(
                source_id=mem_id1, target_id=mem_id3,
                relation_type=RelationType.CONTRADICTS, strength=0.8
            ))
            
            # Get related memories for mem_id1
            related = storage.get_related_memories(mem_id1)
            
            assert len(related) == 2
            related_ids = {mem.id for mem, rel in related}
            assert mem_id2 in related_ids
            assert mem_id3 in related_ids
            
            # Verify relationship info is included
            for mem, rel in related:
                assert isinstance(rel, RelationshipRecord)
                assert rel.source_id == mem_id1
            
            storage.close()

