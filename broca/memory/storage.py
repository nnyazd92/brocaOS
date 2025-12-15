"""
SQLite storage backend for memory records.

Handles persistent storage of memories in SQLite database.
"""

from __future__ import annotations

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta

from . import MemoryRecord, RelationshipRecord, RelationType

logger = logging.getLogger(__name__)


class MemoryStorage:
    """
    SQLite-based storage for memory records.
    
    Provides CRUD operations and search capabilities for memories.
    """
    
    def __init__(self, db_path: str) -> None:
        """
        Initialize memory storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_connection()
        self.create_tables()
        logger.info(f"Initialized MemoryStorage at {self.db_path}")
    
    def _ensure_connection(self) -> None:
        """Ensure database connection is established."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            # Enable foreign key constraints for CASCADE deletes
            self._connection.execute("PRAGMA foreign_keys = ON")
    
    def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT NOT NULL,
                tags TEXT NOT NULL,  -- JSON array of strings
                text TEXT NOT NULL,
                importance REAL NOT NULL CHECK (importance >= 0.0 AND importance <= 1.0),
                created_at TEXT NOT NULL,  -- ISO format datetime
                last_used_at TEXT NOT NULL,  -- ISO format datetime
                embedding TEXT,  -- JSON array of floats (embedding vector)
                valid_from TEXT,  -- ISO format datetime (temporal metadata)
                valid_until TEXT,  -- ISO format datetime (temporal metadata)
                temporal_scope TEXT,  -- Temporal classification
                UNIQUE(id)
            )
        """)
        
        # Add columns if they don't exist (for existing databases)
        cursor.execute("PRAGMA table_info(memories)")
        columns = [row[1] for row in cursor.fetchall()]
        if "embedding" not in columns:
            cursor.execute("ALTER TABLE memories ADD COLUMN embedding TEXT")
            logger.info("Added embedding column to memories table")
        if "valid_from" not in columns:
            cursor.execute("ALTER TABLE memories ADD COLUMN valid_from TEXT")
            logger.info("Added valid_from column to memories table")
        if "valid_until" not in columns:
            cursor.execute("ALTER TABLE memories ADD COLUMN valid_until TEXT")
            logger.info("Added valid_until column to memories table")
        if "temporal_scope" not in columns:
            cursor.execute("ALTER TABLE memories ADD COLUMN temporal_scope TEXT")
            logger.info("Added temporal_scope column to memories table")
        
        # Create indexes for faster searches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_namespace ON memories(namespace)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_used ON memories(last_used_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temporal_valid_from ON memories(valid_from)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temporal_valid_until ON memories(valid_until)")
        
        # Create relationship tables
        self.create_relationship_tables()
        
        self._connection.commit()
        logger.debug("Created memory tables and indexes")
    
    def check_exact_duplicate(self, namespace: str, text: str) -> Optional[int]:
        """
        Check for exact duplicate memory (same namespace and text).
        
        Args:
            namespace: Memory namespace
            text: Memory text content
            
        Returns:
            Memory ID if duplicate found, None otherwise
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT id FROM memories 
            WHERE namespace = ? AND text = ?
            LIMIT 1
        """, (namespace, text))
        
        row = cursor.fetchone()
        return row[0] if row else None
    
    def update_memory(self, memory_id: int, importance: float, tags: List[str]) -> bool:
        """
        Update existing memory's importance and tags.
        
        Args:
            memory_id: ID of memory to update
            importance: New importance score
            tags: New tags list
            
        Returns:
            True if update successful, False otherwise
        """
        self._ensure_connection()
        
        try:
            cursor = self._connection.cursor()
            
            # Convert tags to JSON
            tags_json = json.dumps(tags)
            
            # Update memory
            cursor.execute("""
                UPDATE memories 
                SET importance = ?, tags = ?, last_used_at = ?
                WHERE id = ?
            """, (
                importance,
                tags_json,
                datetime.now(timezone.utc).isoformat(),
                memory_id
            ))
            
            self._connection.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"Updated memory {memory_id} with importance {importance}")
                return True
            else:
                logger.warning(f"Memory {memory_id} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}", exc_info=True)
            return False
    
    def delete_memory(self, memory_id: int) -> bool:
        """
        Delete a memory from the database.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deletion successful, False if memory not found
        """
        self._ensure_connection()
        
        try:
            cursor = self._connection.cursor()
            
            # Delete memory
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            
            self._connection.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"Deleted memory {memory_id}")
                return True
            else:
                logger.warning(f"Memory {memory_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}", exc_info=True)
            return False
    
    def store_memory(self, record: MemoryRecord, embedding: Optional[List[float]] = None) -> int:
        """
        Store a memory record in the database.
        
        Args:
            record: MemoryRecord to store
            embedding: Optional embedding vector (not stored in DB, handled by vector index)
            
        Returns:
            ID of the stored memory
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        
        # Convert tags to JSON
        tags_json = json.dumps(record.tags)
        
        # Convert datetimes to ISO format strings
        created_at_str = record.created_at.isoformat()
        last_used_at_str = record.last_used_at.isoformat()
        valid_from_str = record.valid_from.isoformat() if record.valid_from else None
        valid_until_str = record.valid_until.isoformat() if record.valid_until else None
        
        # Convert embedding to JSON if provided
        embedding_json = json.dumps(embedding) if embedding else None
        
        cursor.execute("""
            INSERT INTO memories (namespace, tags, text, importance, created_at, last_used_at, embedding, valid_from, valid_until, temporal_scope)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.namespace,
            tags_json,
            record.text,
            record.importance,
            created_at_str,
            last_used_at_str,
            embedding_json,
            valid_from_str,
            valid_until_str,
            record.temporal_scope
        ))
        
        memory_id = cursor.lastrowid
        self._connection.commit()
        
        logger.debug(f"Stored memory with ID: {memory_id}")
        return memory_id
    
    def get_memory(self, id: int) -> Optional[MemoryRecord]:
        """
        Retrieve a memory by ID.
        
        Args:
            id: Memory ID
            
        Returns:
            MemoryRecord if found, None otherwise
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_record(row)
    
    def update_last_used(self, id: int) -> None:
        """
        Update the last_used_at timestamp for a memory.
        
        Args:
            id: Memory ID
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("UPDATE memories SET last_used_at = ? WHERE id = ?", (now, id))
        self._connection.commit()
        
        logger.debug(f"Updated last_used_at for memory {id}")
    
    # ===== TEMPORAL QUERY METHODS =====
    
    def get_recent_memories(self, hours: int = 24, limit: int = 10) -> List[MemoryRecord]:
        """
        Get memories created within the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of results
            
        Returns:
            List of MemoryRecord objects created recently
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        cursor.execute("""
            SELECT * FROM memories
            WHERE created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (cutoff_str, limit))
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_memories_from_period(self, start: datetime, end: datetime, limit: int = 10) -> List[MemoryRecord]:
        """
        Get memories created within a specific time period.
        
        Args:
            start: Start datetime (inclusive)
            end: End datetime (inclusive)
            limit: Maximum number of results
            
        Returns:
            List of MemoryRecord objects from the period
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        start_str = start.isoformat()
        end_str = end.isoformat()
        
        cursor.execute("""
            SELECT * FROM memories
            WHERE created_at >= ? AND created_at <= ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (start_str, end_str, limit))
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_oldest_memories(self, limit: int = 10) -> List[MemoryRecord]:
        """
        Get the oldest memories in the database.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of oldest MemoryRecord objects
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT * FROM memories
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_least_recently_used(self, limit: int = 10) -> List[MemoryRecord]:
        """
        Get memories that haven't been used in the longest time.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of least recently used MemoryRecord objects
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT * FROM memories
            ORDER BY last_used_at ASC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_memory_age_stats(self) -> dict:
        """
        Get statistics about memory ages.
        
        Returns:
            Dictionary with age statistics
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        
        # Get current time for calculations
        now = datetime.now(timezone.utc)
        
        # Get all memories with their creation times
        cursor.execute("SELECT created_at FROM memories")
        rows = cursor.fetchall()
        
        if not rows:
            return {
                "total_memories": 0,
                "average_age_days": 0,
                "oldest_age_days": 0,
                "newest_age_days": 0
            }
        
        # Calculate ages
        ages = []
        for row in rows:
            created_at = datetime.fromisoformat(row["created_at"])
            age = now - created_at
            ages.append(age.days + age.seconds / 86400)  # Age in days
        
        return {
            "total_memories": len(ages),
            "average_age_days": sum(ages) / len(ages) if ages else 0,
            "oldest_age_days": max(ages) if ages else 0,
            "newest_age_days": min(ages) if ages else 0
        }
    
    # ===== EXISTING SEARCH METHODS =====
    
    def search_by_namespace(self, namespace: str, limit: int = 10, exact: bool = False) -> List[MemoryRecord]:
        """
        Search memories by namespace (fuzzy or exact match).
        
        Uses LIKE pattern matching for fuzzy namespace search, or exact match.
        
        Args:
            namespace: Namespace pattern to search for
            limit: Maximum number of results
            exact: If True, use exact match; if False, use fuzzy LIKE match
            
        Returns:
            List of MemoryRecord objects matching the namespace
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        if exact:
            # Exact match
            cursor.execute("""
                SELECT * FROM memories
                WHERE namespace = ?
                ORDER BY importance DESC, last_used_at DESC
                LIMIT ?
            """, (namespace, limit))
        else:
            # Use LIKE for fuzzy matching (supports partial matches)
            pattern = f"%{namespace}%"
            cursor.execute("""
                SELECT * FROM memories
                WHERE namespace LIKE ?
                ORDER BY importance DESC, last_used_at DESC
                LIMIT ?
            """, (pattern, limit))
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def search_by_namespace_exact(self, namespace: str, limit: int = 10) -> List[MemoryRecord]:
        """
        Search memories by exact namespace match.
        
        Args:
            namespace: Exact namespace to match
            limit: Maximum number of results
            
        Returns:
            List of MemoryRecord objects with exact namespace match
        """
        return self.search_by_namespace(namespace, limit=limit, exact=True)
    
    def search_by_namespaces(self, namespaces: List[str], limit: int = 10, exact: bool = False) -> List[MemoryRecord]:
        """
        Search memories by multiple namespaces (OR logic - matches any namespace).
        
        Args:
            namespaces: List of namespace patterns to search for
            limit: Maximum number of results
            exact: If True, use exact match; if False, use fuzzy LIKE match
            
        Returns:
            List of MemoryRecord objects matching any of the namespaces
        """
        self._ensure_connection()
        
        if not namespaces:
            return []
        
        cursor = self._connection.cursor()
        
        if exact:
            # Exact match - use IN clause
            placeholders = ",".join("?" * len(namespaces))
            params = list(namespaces) + [limit]
            cursor.execute(f"""
                SELECT * FROM memories
                WHERE namespace IN ({placeholders})
                ORDER BY importance DESC, last_used_at DESC
                LIMIT ?
            """, params)
        else:
            # Fuzzy match - use LIKE with OR
            conditions = []
            params = []
            for namespace in namespaces:
                conditions.append("namespace LIKE ?")
                params.append(f"%{namespace}%")
            
            where_clause = " OR ".join(conditions)
            params.append(limit)
            
            cursor.execute(f"""
                SELECT * FROM memories
                WHERE {where_clause}
                ORDER BY importance DESC, last_used_at DESC
                LIMIT ?
            """, params)
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def search_by_tags(self, tags: List[str], limit: int = 10, all_tags: bool = False) -> List[MemoryRecord]:
        """
        Search memories by tags.
        
        Finds memories that have any of the specified tags (OR) or all tags (AND).
        
        Args:
            tags: List of tags to search for
            limit: Maximum number of results
            all_tags: If True, memory must have ALL tags (AND); if False, ANY tag (OR)
            
        Returns:
            List of MemoryRecord objects matching the tags
        """
        self._ensure_connection()
        
        if not tags:
            return []
        
        cursor = self._connection.cursor()
        
        if all_tags:
            # Find memories with ALL tags (AND logic)
            # Build query where each tag must be present
            conditions = []
            params = []
            for tag in tags:
                conditions.append("tags LIKE ?")
                params.append(f'%"{tag}"%')  # Match tag in JSON array
            
            where_clause = " AND ".join(conditions)
            params.append(limit)
            
            cursor.execute(f"""
                SELECT * FROM memories
                WHERE {where_clause}
                ORDER BY importance DESC, last_used_at DESC
                LIMIT ?
            """, params)
        else:
            # Find memories with ANY tag (OR logic) - original behavior
            conditions = []
            params = []
            for tag in tags:
                conditions.append("tags LIKE ?")
                params.append(f'%"{tag}"%')  # Match tag in JSON array
            
            where_clause = " OR ".join(conditions)
            params.append(limit)
            
            cursor.execute(f"""
                SELECT * FROM memories
                WHERE {where_clause}
                ORDER BY importance DESC, last_used_at DESC
                LIMIT ?
            """, params)
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def search_by_tags_all(self, tags: List[str], limit: int = 10) -> List[MemoryRecord]:
        """
        Search memories that have ALL specified tags.
        
        Args:
            tags: List of tags (all must be present)
            limit: Maximum number of results
            
        Returns:
            List of MemoryRecord objects with all tags
        """
        return self.search_by_tags(tags, limit=limit, all_tags=True)
    
    def search_by_text_phrase(self, phrase: str, limit: int = 10) -> List[MemoryRecord]:
        """
        Search memories containing exact phrase in text.
        
        Args:
            phrase: Exact phrase to search for (case-insensitive)
            limit: Maximum number of results
            
        Returns:
            List of MemoryRecord objects containing the phrase
        """
        self._ensure_connection()
        
        if not phrase:
            return []
        
        cursor = self._connection.cursor()
        # Use LIKE for case-insensitive phrase matching
        pattern = f"%{phrase}%"
        cursor.execute("""
            SELECT * FROM memories
            WHERE LOWER(text) LIKE LOWER(?)
            ORDER BY importance DESC, last_used_at DESC
            LIMIT ?
        """, (pattern, limit))
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_all_memories(self, limit: Optional[int] = None) -> List[MemoryRecord]:
        """
        Get all memories (for vector index synchronization).
        
        Args:
            limit: Optional limit on number of records
            
        Returns:
            List of all MemoryRecord objects
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        if limit:
            cursor.execute("SELECT * FROM memories ORDER BY id LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT * FROM memories ORDER BY id")
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_all_namespaces(self) -> List[str]:
        """
        Get all unique namespaces from the database.
        
        Returns:
            List of unique namespace strings
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cursor.execute("SELECT DISTINCT namespace FROM memories ORDER BY namespace")
        
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    
    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        """Convert database row to MemoryRecord."""
        tags = json.loads(row["tags"])
        created_at = datetime.fromisoformat(row["created_at"])
        last_used_at = datetime.fromisoformat(row["last_used_at"])
        
        # Normalize datetimes to UTC-aware (handle both naive and aware datetimes from storage)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = created_at.astimezone(timezone.utc)
        
        if last_used_at.tzinfo is None:
            last_used_at = last_used_at.replace(tzinfo=timezone.utc)
        else:
            last_used_at = last_used_at.astimezone(timezone.utc)
        
        # Load temporal metadata if present
        valid_from = None
        try:
            if row["valid_from"] is not None:
                valid_from = datetime.fromisoformat(row["valid_from"])
                if valid_from.tzinfo is None:
                    valid_from = valid_from.replace(tzinfo=timezone.utc)
                else:
                    valid_from = valid_from.astimezone(timezone.utc)
        except (KeyError, IndexError):
            pass  # Column doesn't exist or is None
        
        valid_until = None
        try:
            if row["valid_until"] is not None:
                valid_until = datetime.fromisoformat(row["valid_until"])
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                else:
                    valid_until = valid_until.astimezone(timezone.utc)
        except (KeyError, IndexError):
            pass  # Column doesn't exist or is None
        
        temporal_scope = None
        try:
            temporal_scope = row["temporal_scope"]
        except (KeyError, IndexError):
            pass  # Column doesn't exist
        
        # Load embedding if present
        embedding = None
        if row["embedding"] is not None:
            embedding = json.loads(row["embedding"])
        
        return MemoryRecord(
            id=row["id"],
            namespace=row["namespace"],
            tags=tags,
            text=row["text"],
            importance=row["importance"],
            created_at=created_at,
            last_used_at=last_used_at,
            embedding=embedding,
            valid_from=valid_from,
            valid_until=valid_until,
            temporal_scope=temporal_scope
        )
    
    def get_embedding(self, memory_id: int) -> Optional[List[float]]:
        """
        Retrieve embedding for a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Embedding vector if found, None otherwise
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cursor.execute("SELECT embedding FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        if row is None or row[0] is None:
            return None
        
        return json.loads(row[0])
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("Closed memory storage connection")
    
    def create_relationship_tables(self) -> None:
        """Create relationship tables if they don't exist."""
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0 CHECK (strength >= 0.0 AND strength <= 1.0),
                bidirectional BOOLEAN DEFAULT 0,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES memories(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES memories(id) ON DELETE CASCADE,
                UNIQUE(source_id, target_id, relation_type)
            )
        """)
        
        # Create indexes for fast traversal
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_source ON memory_relationships(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_target ON memory_relationships(target_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_type ON memory_relationships(relation_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_strength ON memory_relationships(strength DESC)")
        
        self._connection.commit()
        logger.debug("Created relationship tables and indexes")
    
    def store_relationship(self, relationship: RelationshipRecord) -> int:
        """
        Store a relationship in the database.
        
        Args:
            relationship: RelationshipRecord to store
            
        Returns:
            ID of the stored relationship
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        
        # Convert metadata to JSON if provided
        metadata_json = json.dumps(relationship.metadata) if relationship.metadata else None
        
        # Use provided created_at or current time
        created_at = relationship.created_at or datetime.now(timezone.utc)
        created_at_str = created_at.isoformat()
        
        try:
            cursor.execute("""
                INSERT INTO memory_relationships 
                (source_id, target_id, relation_type, strength, bidirectional, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                relationship.source_id,
                relationship.target_id,
                relationship.relation_type.value,
                relationship.strength,
                1 if relationship.bidirectional else 0,
                metadata_json,
                created_at_str
            ))
            
            relationship_id = cursor.lastrowid
            
            # If bidirectional, create reverse relationship
            if relationship.bidirectional:
                cursor.execute("""
                    INSERT INTO memory_relationships 
                    (source_id, target_id, relation_type, strength, bidirectional, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    relationship.target_id,
                    relationship.source_id,
                    relationship.relation_type.value,
                    relationship.strength,
                    1,
                    metadata_json,
                    created_at_str
                ))
            
            self._connection.commit()
            logger.debug(f"Stored relationship {relationship_id} from {relationship.source_id} to {relationship.target_id}")
            return relationship_id
            
        except sqlite3.IntegrityError as e:
            self._connection.rollback()
            if "UNIQUE constraint" in str(e):
                logger.warning(
                    f"Relationship already exists: {relationship.source_id} -> "
                    f"{relationship.target_id} ({relationship.relation_type.value})"
                )
                # Try to get existing relationship ID
                cursor.execute("""
                    SELECT id FROM memory_relationships
                    WHERE source_id = ? AND target_id = ? AND relation_type = ?
                """, (relationship.source_id, relationship.target_id, relationship.relation_type.value))
                row = cursor.fetchone()
                if row:
                    return row[0]
            raise
    
    def get_relationships(
        self,
        source_id: Optional[int] = None,
        target_id: Optional[int] = None,
        relation_type: Optional[RelationType] = None
    ) -> List[RelationshipRecord]:
        """
        Get relationships matching the criteria.
        
        Args:
            source_id: Filter by source memory ID (optional)
            target_id: Filter by target memory ID (optional)
            relation_type: Filter by relationship type (optional)
            
        Returns:
            List of RelationshipRecord objects
        """
        self._ensure_connection()
        
        cursor = self._connection.cursor()
        
        # Build query dynamically based on filters
        conditions = []
        params = []
        
        if source_id is not None:
            conditions.append("source_id = ?")
            params.append(source_id)
        
        if target_id is not None:
            conditions.append("target_id = ?")
            params.append(target_id)
        
        if relation_type is not None:
            conditions.append("relation_type = ?")
            params.append(relation_type.value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor.execute(f"""
            SELECT * FROM memory_relationships
            WHERE {where_clause}
            ORDER BY strength DESC, created_at DESC
        """, params)
        
        rows = cursor.fetchall()
        return [self._row_to_relationship(row) for row in rows]
    
    def delete_relationship(self, relationship_id: int) -> bool:
        """
        Delete a relationship by ID.
        
        Args:
            relationship_id: ID of relationship to delete
            
        Returns:
            True if deletion successful, False if relationship not found
        """
        self._ensure_connection()
        
        try:
            cursor = self._connection.cursor()
            
            # Get relationship to check if bidirectional
            cursor.execute("SELECT * FROM memory_relationships WHERE id = ?", (relationship_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            relationship = self._row_to_relationship(row)
            
            # Delete the relationship
            cursor.execute("DELETE FROM memory_relationships WHERE id = ?", (relationship_id,))
            
            # If bidirectional, also delete reverse relationship
            if relationship.bidirectional:
                cursor.execute("""
                    DELETE FROM memory_relationships
                    WHERE source_id = ? AND target_id = ? AND relation_type = ?
                """, (
                    relationship.target_id,
                    relationship.source_id,
                    relationship.relation_type.value
                ))
            
            self._connection.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"Deleted relationship {relationship_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting relationship {relationship_id}: {e}", exc_info=True)
            return False
    
    def get_related_memories(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both"
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord)
        """
        self._ensure_connection()
        
        related: List[Tuple[MemoryRecord, RelationshipRecord]] = []
        
        # Get outgoing relationships
        if direction in ("outgoing", "both"):
            if relation_types:
                for rel_type in relation_types:
                    relationships = self.get_relationships(
                        source_id=memory_id,
                        relation_type=rel_type
                    )
                    for rel in relationships:
                        target_memory = self.get_memory(rel.target_id)
                        if target_memory:
                            related.append((target_memory, rel))
            else:
                relationships = self.get_relationships(source_id=memory_id)
                for rel in relationships:
                    target_memory = self.get_memory(rel.target_id)
                    if target_memory:
                        related.append((target_memory, rel))
        
        # Get incoming relationships
        if direction in ("incoming", "both"):
            if relation_types:
                for rel_type in relation_types:
                    relationships = self.get_relationships(
                        target_id=memory_id,
                        relation_type=rel_type
                    )
                    for rel in relationships:
                        source_memory = self.get_memory(rel.source_id)
                        if source_memory:
                            related.append((source_memory, rel))
            else:
                relationships = self.get_relationships(target_id=memory_id)
                for rel in relationships:
                    source_memory = self.get_memory(rel.source_id)
                    if source_memory:
                        related.append((source_memory, rel))
        
        # Remove duplicates (can happen with bidirectional relationships)
        seen = set()
        unique_related = []
        for mem, rel in related:
            key = (mem.id, rel.id)
            if key not in seen:
                seen.add(key)
                unique_related.append((mem, rel))
        
        return unique_related
    
    def _row_to_relationship(self, row: sqlite3.Row) -> RelationshipRecord:
        """Convert database row to RelationshipRecord."""
        metadata = None
        if row["metadata"]:
            metadata = json.loads(row["metadata"])
        
        created_at = None
        if row["created_at"]:
            created_at = datetime.fromisoformat(row["created_at"])
        
        return RelationshipRecord(
            id=row["id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation_type=RelationType(row["relation_type"]),
            strength=row["strength"],
            bidirectional=bool(row["bidirectional"]),
            metadata=metadata,
            created_at=created_at
        )
    
    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.close()
