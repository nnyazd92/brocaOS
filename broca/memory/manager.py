"""
Memory manager orchestrating storage, vector index, and embeddings.

Provides high-level interface for storing and retrieving memories.
"""

from __future__ import annotations

import logging
import json
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from . import MemoryRecord, RelationType
from .storage import MemoryStorage
from .vector_index import VectorIndex
from .embeddings import EmbeddingService
from .relationships import RelationshipManager
from .namespace_index import NamespaceIndexGenerator

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    High-level memory management orchestrating storage, vector index, and embeddings.
    
    Provides unified interface for storing and retrieving memories with
    combined search capabilities (vector similarity + namespace + tags).
    """
    
    def __init__(
        self,
        storage: MemoryStorage,
        vector_index: VectorIndex,
        embedding_service: EmbeddingService
    ) -> None:
        """
        Initialize memory manager.
        
        Args:
            storage: MemoryStorage instance
            vector_index: VectorIndex instance
            embedding_service: EmbeddingService instance
        """
        self.storage = storage
        self.vector_index = vector_index
        self.embedding_service = embedding_service
        self.relationships = RelationshipManager(storage)
        self.namespace_index = NamespaceIndexGenerator(storage)
        
        # Sync vector index with storage on startup
        self._sync_index()
        
        # Create namespace index if it doesn't exist
        self._ensure_namespace_index()
        
        logger.info("Initialized MemoryManager")
    
    def _sync_index(self) -> None:
        """Sync vector index with storage (rebuild if needed)."""
        try:
            # Check if index is empty but storage has memories
            storage_count = len(self.storage.get_all_memories())
            index_count = self.vector_index.get_count()
            
            if storage_count > 0 and index_count == 0:
                logger.info("Vector index is empty, rebuilding from storage...")
                self._rebuild_index_from_storage()
            elif storage_count != index_count:
                logger.warning(
                    f"Index count ({index_count}) doesn't match storage count ({storage_count}), syncing..."
                )
                # Check for orphaned entries (memory IDs in index that don't exist in storage)
                if index_count > storage_count:
                    # Index has more entries - check for orphaned entries
                    indexed_memory_ids = set(self.vector_index.get_memory_ids())
                    storage_memory_ids = {mem.id for mem in self.storage.get_all_memories() if mem.id}
                    orphaned_ids = indexed_memory_ids - storage_memory_ids
                    
                    if orphaned_ids:
                        logger.info(
                            f"Found {len(orphaned_ids)} orphaned entries in index, "
                            f"rebuilding index completely..."
                        )
                        self._rebuild_index_completely()
                    else:
                        # Count mismatch but no orphaned entries - just add missing
                        self._rebuild_index_from_storage()
                else:
                    # Storage has more entries - just add missing
                    self._rebuild_index_from_storage()
            else:
                # Counts match - but still check for orphaned entries or missing memories
                # This handles the case where counts match but contents differ
                indexed_memory_ids = set(self.vector_index.get_memory_ids())
                storage_memory_ids = {mem.id for mem in self.storage.get_all_memories() if mem.id}
                orphaned_ids = indexed_memory_ids - storage_memory_ids
                missing_ids = storage_memory_ids - indexed_memory_ids
                
                if orphaned_ids or missing_ids:
                    if orphaned_ids:
                        logger.info(
                            f"Found {len(orphaned_ids)} orphaned entries and {len(missing_ids)} missing memories, "
                            f"rebuilding index completely..."
                        )
                        self._rebuild_index_completely()
                    else:
                        # Only missing memories, no orphaned - just add missing
                        logger.info(f"Found {len(missing_ids)} missing memories, adding to index...")
                        self._rebuild_index_from_storage()
        except Exception as e:
            logger.error(f"Error syncing index: {e}", exc_info=True)
    
    def _rebuild_index_from_storage(self) -> None:
        """
        Rebuild vector index from storage by regenerating embeddings for missing memories.
        
        This method identifies memories in storage that are not in the index,
        generates embeddings for them, and adds them to the index.
        """
        try:
            # Get all memories from storage
            all_memories = self.storage.get_all_memories()
            
            if not all_memories:
                logger.debug("No memories in storage, nothing to index")
                return
            
            # Get memory IDs already in index
            indexed_memory_ids = set(self.vector_index.get_memory_ids())
            
            # Find memories that need to be indexed
            missing_memories = [
                mem for mem in all_memories
                if mem.id and mem.id not in indexed_memory_ids
            ]
            
            if not missing_memories:
                logger.debug("All memories are already indexed")
                return
            
            logger.info(f"Rebuilding index: adding {len(missing_memories)} missing memories")
            
            # Add missing memories to index
            success_count = 0
            error_count = 0
            
            for memory in missing_memories:
                try:
                    if not memory.id:
                        continue
                    
                    # Load embedding from DB if available, otherwise generate
                    embedding = memory.embedding
                    if embedding is None:
                        # Generate embedding for memories without stored embeddings
                        embedding = self.embedding_service.generate_embedding(memory.text)
                        # Save embedding to DB for future use
                        cursor = self.storage._connection.cursor()
                        cursor.execute(
                            "UPDATE memories SET embedding = ? WHERE id = ?",
                            (json.dumps(embedding), memory.id)
                        )
                        self.storage._connection.commit()
                    else:
                        # Use stored embedding
                        logger.debug(f"Loaded embedding from DB for memory {memory.id}")
                    
                    # Add to index
                    self.vector_index.add_vector(memory.id, embedding)
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to index memory {memory.id}: {e}",
                        exc_info=True
                    )
                    error_count += 1
            
            logger.info(
                f"Index rebuild complete: {success_count} added, {error_count} errors"
            )
            
        except Exception as e:
            logger.error(f"Error rebuilding index from storage: {e}", exc_info=True)
            raise
    
    def _rebuild_index_completely(self) -> None:
        """
        Rebuild vector index completely from storage.
        
        This method clears the entire index and rebuilds it from all memories
        in storage. Used when orphaned entries are detected.
        """
        try:
            # Get all memories from storage
            all_memories = self.storage.get_all_memories()
            
            if not all_memories:
                logger.debug("No memories in storage, clearing index")
                self.vector_index.clear()
                return
            
            logger.info(f"Rebuilding index completely from {len(all_memories)} memories in storage")
            
            # Clear existing index
            self.vector_index.clear()
            
            # Rebuild from all memories
            success_count = 0
            error_count = 0
            
            for memory in all_memories:
                try:
                    if not memory.id:
                        continue
                    
                    # Load embedding from DB if available, otherwise generate
                    embedding = memory.embedding
                    if embedding is None:
                        # Generate embedding for memories without stored embeddings
                        embedding = self.embedding_service.generate_embedding(memory.text)
                        # Save embedding to DB for future use
                        # Need to update the existing record - create a new record with same data
                        updated_record = MemoryRecord(
                            id=memory.id,
                            namespace=memory.namespace,
                            tags=memory.tags,
                            text=memory.text,
                            importance=memory.importance,
                            created_at=memory.created_at,
                            last_used_at=memory.last_used_at,
                            embedding=embedding
                        )
                        # Update embedding in storage
                        cursor = self.storage._connection.cursor()
                        cursor.execute(
                            "UPDATE memories SET embedding = ? WHERE id = ?",
                            (json.dumps(embedding), memory.id)
                        )
                        self.storage._connection.commit()
                    else:
                        # Use stored embedding
                        logger.debug(f"Loaded embedding from DB for memory {memory.id}")
                    
                    # Add to index
                    self.vector_index.add_vector(memory.id, embedding)
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to index memory {memory.id}: {e}",
                        exc_info=True
                    )
                    error_count += 1
            
            logger.info(
                f"Complete index rebuild finished: {success_count} indexed, {error_count} errors"
            )
            
            # Verify counts match
            final_storage_count = len(self.storage.get_all_memories())
            final_index_count = self.vector_index.get_count()
            if final_storage_count != final_index_count:
                logger.warning(
                    f"After rebuild, index count ({final_index_count}) still doesn't match "
                    f"storage count ({final_storage_count})"
                )
            else:
                logger.info("Index sync complete: counts match")
        
        except Exception as e:
            logger.error(f"Error rebuilding index completely: {e}", exc_info=True)
            raise
    
    def store_memory(
        self,
        namespace: str,
        text: str,
        importance: float,
        tags: Optional[List[str]] = None,
        deduplicate: bool = True,
        conflict_check: bool = False,
        auto_resolve: bool = False,
        auto_link: bool = True
    ) -> Tuple[int, bool, List[Any]]:
        """
        Store a new memory with optional deduplication.
        
        Args:
            namespace: Hierarchical namespace
            text: Memory content
            importance: Importance score (0.0-1.0)
            tags: Optional list of tags (defaults to empty list)
            deduplicate: Whether to check for and update duplicates
            conflict_check: Whether to check for conflicts with existing memories
            auto_resolve: Whether to automatically resolve conflicts
            
        Returns:
            Tuple of (memory_id, was_duplicate, conflicts_detected)
            conflicts_detected is a list of Conflict objects (empty if conflict_check=False or no conflicts)
        """
        try:
            # Create memory record
            if tags is None:
                tags = []
            
            # Check for exact duplicate if deduplication is enabled
            if deduplicate:
                duplicate_id = self.storage.check_exact_duplicate(namespace, text)
                if duplicate_id:
                    # Update existing memory
                    logger.info(f"Duplicate found: memory {duplicate_id}, updating instead of creating new")
                    
                    # Merge tags (unique union) and use max importance
                    existing_memory = self.storage.get_memory(duplicate_id)
                    if existing_memory:
                        merged_tags = list(set(existing_memory.tags + tags))
                        # Use max importance (keep the more important one)
                        merged_importance = max(existing_memory.importance, importance)
                    else:
                        merged_tags = tags
                        merged_importance = importance
                    
                    # Update the existing memory
                    success = self.storage.update_memory(duplicate_id, merged_importance, merged_tags)
                    if success:
                        # Update last_used timestamp
                        self.storage.update_last_used(duplicate_id)
                        
                        # Auto-detect SUPERSEDES relationship if enabled
                        # (Note: auto_link parameter is not available in duplicate path,
                        # but we can check if relationships exist to determine if auto-link is desired)
                        # For now, skip auto-detection in duplicate case
                        
                        # Return empty conflicts list for duplicates (exact match, no conflict)
                        return duplicate_id, True, []
                    else:
                        logger.warning(f"Failed to update duplicate memory {duplicate_id}, creating new")
            
            # No duplicate found or deduplication disabled - create new memory
            logger.debug(f"No duplicate found, creating new memory in namespace '{namespace}'")
            
            record = MemoryRecord(
                namespace=namespace,
                tags=tags,
                text=text,
                importance=importance
            )
            
            # Generate embedding
            logger.debug(f"Generating embedding for memory: {text[:50]}...")
            embedding = self.embedding_service.generate_embedding(text)
            
            # Check for conflicts if enabled
            conflicts_detected = []
            if conflict_check:
                try:
                    from .conflict import ConflictDetector, ConflictResolver, ConflictLogger
                    
                    # Get existing memories
                    existing_memories = self.storage.get_all_memories()
                    
                    # Detect conflicts
                    detector = ConflictDetector(
                        memory_manager=self,
                        similarity_threshold=0.85,
                        contradiction_threshold=0.7
                    )
                    conflicts_detected = detector.detect_conflicts(record, existing_memories)
                    
                    # Resolve conflicts if any detected
                    if conflicts_detected and auto_resolve:
                        resolver = ConflictResolver(memory_manager=self)
                        resolution_results = resolver.resolve_conflicts(
                            conflicts_detected,
                            auto_resolve=True
                        )
                        
                        # Apply resolutions
                        conflict_logger = ConflictLogger(self.storage)
                        for result in resolution_results:
                            resolution = result.resolution
                            
                            # Log the conflict and resolution
                            conflict_logger.log_conflict(
                                result.conflict,
                                resolution,
                                user_involved=False
                            )
                            
                            # Apply resolution actions
                            if resolution.action == "keep_new" and resolution.kept_memory:
                                # Keep new memory, archive old
                                if resolution.archived_memory and resolution.archived_memory.id:
                                    # Could mark as archived in future
                                    pass
                            elif resolution.action == "merge" and resolution.merged_memory:
                                # Use merged memory instead
                                record = resolution.merged_memory
                                # Regenerate embedding for merged text
                                embedding = self.embedding_service.generate_embedding(record.text)
                    
                    if conflicts_detected:
                        logger.info(f"Detected {len(conflicts_detected)} conflict(s) for new memory")
                
                except Exception as e:
                    logger.warning(f"Error in conflict detection/resolution: {e}", exc_info=True)
                    # Continue with normal storage if conflict resolution fails
            
            # Store in database
            memory_id = self.storage.store_memory(record, embedding)
            
            # Add to vector index
            self.vector_index.add_vector(memory_id, embedding)
            
            # Save index immediately
            self.save_index()
            
            # Update namespace index if this is a new namespace
            try:
                if self.namespace_index.is_namespace_new(namespace):
                    # Refresh namespace cache and update index
                    self.namespace_index.get_all_namespaces()
                    self.namespace_index.update_index()
                    logger.debug(f"Updated namespace index for new namespace: {namespace}")
            except Exception as e:
                logger.warning(f"Error updating namespace index: {e}", exc_info=True)
                # Don't fail memory storage if index update fails
            
            # Auto-detect relationships if enabled
            if auto_link:
                try:
                    self._auto_detect_relationships(memory_id, record, embedding, conflicts_detected)
                except Exception as e:
                    logger.warning(f"Error in auto-detection: {e}", exc_info=True)
                    # Continue even if auto-detection fails
            
            logger.info(f"Stored new memory {memory_id} in namespace '{namespace}'")
            return memory_id, False, conflicts_detected
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}", exc_info=True)
            raise
    
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
        return self.storage.get_recent_memories(hours=hours, limit=limit)
    
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
        return self.storage.get_memories_from_period(start, end, limit)
    
    def get_oldest_memories(self, limit: int = 10) -> List[MemoryRecord]:
        """
        Get the oldest memories in the database.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of oldest MemoryRecord objects
        """
        return self.storage.get_oldest_memories(limit)
    
    def get_least_recently_used(self, limit: int = 10) -> List[MemoryRecord]:
        """
        Get memories that haven't been used in the longest time.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of least recently used MemoryRecord objects
        """
        return self.storage.get_least_recently_used(limit)
    
    def get_memory_age_stats(self) -> dict:
        """
        Get statistics about memory ages.
        
        Returns:
            Dictionary with age statistics
        """
        return self.storage.get_memory_age_stats()
    
    @staticmethod
    def _normalize_datetime_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """
        Normalize a datetime to UTC timezone-aware.
        
        If datetime is naive (no timezone), assumes UTC and makes it aware.
        If datetime is aware, converts to UTC.
        
        Args:
            dt: Datetime to normalize (can be None, naive, or aware)
            
        Returns:
            UTC timezone-aware datetime, or None if input was None
        """
        if dt is None:
            return None
        
        if dt.tzinfo is None:
            # Naive datetime - assume UTC
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Aware datetime - convert to UTC
            return dt.astimezone(timezone.utc)
    
    def calculate_memory_age(self, memory: MemoryRecord) -> timedelta:
        """
        Calculate how old a memory is.
        
        Args:
            memory: MemoryRecord to calculate age for
            
        Returns:
            timedelta representing the age of the memory
        """
        return datetime.now(timezone.utc) - memory.created_at
    
    def format_memory_age(self, memory: MemoryRecord) -> str:
        """
        Format memory age in human-readable form.
        
        Args:
            memory: MemoryRecord to format age for
            
        Returns:
            Human-readable age string (e.g., "3 days ago", "2 hours ago")
        """
        age = self.calculate_memory_age(memory)
        
        if age.days > 0:
            if age.days == 1:
                return "1 day ago"
            return f"{age.days} days ago"
        elif age.seconds >= 3600:
            hours = age.seconds // 3600
            if hours == 1:
                return "1 hour ago"
            return f"{hours} hours ago"
        elif age.seconds >= 60:
            minutes = age.seconds // 60
            if minutes == 1:
                return "1 minute ago"
            return f"{minutes} minutes ago"
        else:
            return "just now"
    
    def is_memory_recent(self, memory: MemoryRecord, hours: int = 24) -> bool:
        """
        Check if a memory was created recently.
        
        Args:
            memory: MemoryRecord to check
            hours: Threshold for "recent" in hours
            
        Returns:
            True if memory was created within the last N hours
        """
        age = self.calculate_memory_age(memory)
        return age <= timedelta(hours=hours)
    
    # ===== ENHANCED RETRIEVAL WITH TEMPORAL WEIGHTING =====
    
    def retrieve_memories(
        self,
        query: str,
        namespace: Optional[str] = None,
        namespaces: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5,
        recency_weight: float = 0.3,
        namespace_exact: bool = False,
        tag_mode: str = "any",
        query_phrases: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        last_used_after: Optional[datetime] = None,
        last_used_before: Optional[datetime] = None,
        min_importance: Optional[float] = None,
        max_importance: Optional[float] = None
    ) -> List[MemoryRecord]:
        """
        Retrieve memories using combined search with temporal weighting.
        
        Args:
            query: Text query for vector similarity search
            namespace: Optional single namespace filter (fuzzy match) - deprecated in favor of namespaces
            namespaces: Optional list of namespaces to search across (OR logic)
            tags: Optional tags filter
            limit: Maximum number of results
            recency_weight: Weight for recency in scoring (0.0-1.0)
            namespace_exact: If true, use exact namespace matching
            tag_mode: "any" for OR logic, "all" for AND logic
            query_phrases: Optional list of exact phrases to match
            created_after: Optional datetime - filter memories created after this date
            created_before: Optional datetime - filter memories created before this date
            last_used_after: Optional datetime - filter memories last used after this date
            last_used_before: Optional datetime - filter memories last used before this date
            min_importance: Optional float - minimum importance score (0.0-1.0)
            max_importance: Optional float - maximum importance score (0.0-1.0)
            
        Returns:
            List of MemoryRecord objects, ranked by relevance with temporal weighting
        """
        try:
            # Normalize datetime filter parameters to UTC-aware
            created_after = self._normalize_datetime_to_utc(created_after)
            created_before = self._normalize_datetime_to_utc(created_before)
            last_used_after = self._normalize_datetime_to_utc(last_used_after)
            last_used_before = self._normalize_datetime_to_utc(last_used_before)
            
            # Parse query for boolean operators and extract phrases
            parsed_query = self._parse_query(query)
            base_query = parsed_query.get("base_query", query).strip()
            
            # Extract phrases from parsed query if not provided
            if query_phrases is None:
                query_phrases = parsed_query.get("phrases", [])
            
            # Generate query embedding from base query
            if base_query:
                query_embedding = self.embedding_service.generate_embedding(base_query)
            else:
                # If no base query, use first phrase or empty query
                if query_phrases:
                    query_embedding = self.embedding_service.generate_embedding(query_phrases[0])
                else:
                    query_embedding = self.embedding_service.generate_embedding("")
            
            # Get candidates from different sources
            candidates: List[MemoryRecord] = []
            candidate_scores: dict[int, float] = defaultdict(float)
            
            # Resolve namespace(s) - namespaces takes precedence over namespace
            namespaces_to_search = namespaces if namespaces else ([namespace] if namespace else None)
            
            # 1. Vector similarity search
            vector_results = self.vector_index.search_similar(query_embedding, k=limit * 3)
            for memory_id, similarity_score in vector_results:
                memory = self.storage.get_memory(memory_id)
                if memory:
                    # Apply namespace filter(s)
                    if namespaces_to_search:
                        if namespace_exact:
                            if memory.namespace not in namespaces_to_search:
                                continue
                        else:
                            # Fuzzy match - check if any namespace is contained in memory's namespace
                            if not any(ns in memory.namespace for ns in namespaces_to_search):
                                continue
                    
                    # Apply date range filters
                    if created_after and memory.created_at < created_after:
                        continue
                    if created_before and memory.created_at > created_before:
                        continue
                    if last_used_after and memory.last_used_at < last_used_after:
                        continue
                    if last_used_before and memory.last_used_at > last_used_before:
                        continue
                    
                    # Apply importance filters
                    if min_importance is not None and memory.importance < min_importance:
                        continue
                    if max_importance is not None and memory.importance > max_importance:
                        continue
                    
                    candidates.append(memory)
                    # Weight vector similarity heavily
                    candidate_scores[memory_id] += similarity_score * (1.0 - recency_weight)
            
            # 2. Namespace search (if specified)
            if namespaces_to_search:
                if len(namespaces_to_search) == 1:
                    # Single namespace - use existing method
                    namespace_results = self.storage.search_by_namespace(
                        namespaces_to_search[0], limit=limit * 2, exact=namespace_exact
                    )
                else:
                    # Multiple namespaces - use new method
                    namespace_results = self.storage.search_by_namespaces(
                        namespaces_to_search, limit=limit * 2, exact=namespace_exact
                    )
                for memory in namespace_results:
                    # Apply filters
                    if created_after and memory.created_at < created_after:
                        continue
                    if created_before and memory.created_at > created_before:
                        continue
                    if last_used_after and memory.last_used_at < last_used_after:
                        continue
                    if last_used_before and memory.last_used_at > last_used_before:
                        continue
                    if min_importance is not None and memory.importance < min_importance:
                        continue
                    if max_importance is not None and memory.importance > max_importance:
                        continue
                    
                    if memory.id not in candidate_scores:
                        candidates.append(memory)
                    # Weight namespace match
                    candidate_scores[memory.id] += 0.2
            
            # 3. Tag search (if specified)
            if tags:
                all_tags = (tag_mode == "all")
                tag_results = self.storage.search_by_tags(tags, limit=limit * 2, all_tags=all_tags)
                for memory in tag_results:
                    # Apply namespace filter(s)
                    if namespaces_to_search:
                        if namespace_exact:
                            if memory.namespace not in namespaces_to_search:
                                continue
                        else:
                            if not any(ns in memory.namespace for ns in namespaces_to_search):
                                continue
                    
                    # Apply filters
                    if created_after and memory.created_at < created_after:
                        continue
                    if created_before and memory.created_at > created_before:
                        continue
                    if last_used_after and memory.last_used_at < last_used_after:
                        continue
                    if last_used_before and memory.last_used_at > last_used_before:
                        continue
                    if min_importance is not None and memory.importance < min_importance:
                        continue
                    if max_importance is not None and memory.importance > max_importance:
                        continue
                    
                    if memory.id not in candidate_scores:
                        candidates.append(memory)
                    # Weight tag match
                    candidate_scores[memory.id] += 0.1
            
            # 4. Phrase matching (if specified)
            if query_phrases:
                for phrase in query_phrases:
                    phrase_results = self.storage.search_by_text_phrase(phrase, limit=limit * 2)
                    for memory in phrase_results:
                        # Apply namespace filter(s)
                        if namespaces_to_search:
                            if namespace_exact:
                                if memory.namespace not in namespaces_to_search:
                                    continue
                            else:
                                if not any(ns in memory.namespace for ns in namespaces_to_search):
                                    continue
                        
                        # Apply filters
                        if created_after and memory.created_at < created_after:
                            continue
                        if created_before and memory.created_at > created_before:
                            continue
                        if last_used_after and memory.last_used_at < last_used_after:
                            continue
                        if last_used_before and memory.last_used_at > last_used_before:
                            continue
                        if min_importance is not None and memory.importance < min_importance:
                            continue
                        if max_importance is not None and memory.importance > max_importance:
                            continue
                        
                        if memory.id not in candidate_scores:
                            candidates.append(memory)
                        # Weight phrase match
                        candidate_scores[memory.id] += 0.15
            
            # If no filters, use vector search results (but still apply boolean operators)
            if not namespaces_to_search and not tags and not query_phrases:
                # Return top vector results, but apply boolean operators and filters
                results = []
                for memory_id, _ in vector_results[:limit * 2]:
                    memory = self.storage.get_memory(memory_id)
                    if memory:
                        # Apply filters
                        if created_after and memory.created_at < created_after:
                            continue
                        if created_before and memory.created_at > created_before:
                            continue
                        if last_used_after and memory.last_used_at < last_used_after:
                            continue
                        if last_used_before and memory.last_used_at > last_used_before:
                            continue
                        if min_importance is not None and memory.importance < min_importance:
                            continue
                        if max_importance is not None and memory.importance > max_importance:
                            continue
                        
                        # Apply boolean operators
                        if self._apply_boolean_operators(memory, parsed_query):
                            results.append(memory)
                            self.storage.update_last_used(memory_id)
                return results[:limit]
            
            # Combine and rank results
            # Deduplicate by ID and apply filters
            unique_memories: dict[int, MemoryRecord] = {}
            for memory in candidates:
                # Apply namespace filter(s) if specified
                if namespaces_to_search:
                    if namespace_exact:
                        if memory.namespace not in namespaces_to_search:
                            continue
                    else:
                        if not any(ns in memory.namespace for ns in namespaces_to_search):
                            continue
                
                # Apply date range filters
                if created_after and memory.created_at < created_after:
                    continue
                if created_before and memory.created_at > created_before:
                    continue
                if last_used_after and memory.last_used_at < last_used_after:
                    continue
                if last_used_before and memory.last_used_at > last_used_before:
                    continue
                
                # Apply importance filters
                if min_importance is not None and memory.importance < min_importance:
                    continue
                if max_importance is not None and memory.importance > max_importance:
                    continue
                
                # Apply tag filter if specified
                if tags:
                    if tag_mode == "all":
                        # Memory must have ALL tags
                        if not all(tag in memory.tags for tag in tags):
                            continue
                    else:
                        # Memory must have ANY tag (default)
                        if not any(tag in memory.tags for tag in tags):
                            continue
                
                # Apply phrase matching if specified
                if query_phrases:
                    memory_text_lower = memory.text.lower()
                    if not all(phrase.lower() in memory_text_lower for phrase in query_phrases):
                        continue
                
                # Apply boolean operators
                if not self._apply_boolean_operators(memory, parsed_query):
                    continue
                
                if memory.id not in unique_memories:
                    unique_memories[memory.id] = memory
            
            # Calculate recency scores for temporal weighting
            if recency_weight > 0:
                now = datetime.now(timezone.utc)
                max_age_seconds = 0
                recency_scores = {}
                
                # Find maximum age for normalization
                for memory_id, memory in unique_memories.items():
                    age = (now - memory.created_at).total_seconds()
                    max_age_seconds = max(max_age_seconds, age)
                
                # Calculate recency scores (newer = higher score)
                for memory_id, memory in unique_memories.items():
                    if max_age_seconds > 0:
                        age = (now - memory.created_at).total_seconds()
                        # Normalize: 1.0 for newest, 0.0 for oldest
                        recency_score = 1.0 - (age / max_age_seconds)
                    else:
                        recency_score = 1.0  # All memories are same age
                    recency_scores[memory_id] = recency_score
            
            # Sort by combined score, then by importance, then by last_used
            def sort_key(memory: MemoryRecord) -> tuple:
                score = candidate_scores.get(memory.id, 0.0)
                
                # Add recency weighting if enabled
                if recency_weight > 0 and memory.id in recency_scores:
                    score += recency_scores[memory.id] * recency_weight
                
                return (-score, -memory.importance, -memory.last_used_at.timestamp())
            
            results = sorted(unique_memories.values(), key=sort_key)[:limit]
            
            # Update last_used_at for retrieved memories
            for memory in results:
                if memory.id:
                    self.storage.update_last_used(memory.id)
            
            logger.debug(f"Retrieved {len(results)} memories for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}", exc_info=True)
            return []
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse query for boolean operators and extract phrases.
        
        Args:
            query: Query string
            
        Returns:
            Dictionary with parsed query components:
            - base_query: Query without boolean operators for embedding
            - and_terms: List of terms that must be present (AND)
            - or_terms: List of terms that may be present (OR)
            - not_terms: List of terms that must not be present (NOT)
            - phrases: List of quoted phrases
        """
        import re
        
        result = {
            "base_query": query,
            "and_terms": [],
            "or_terms": [],
            "not_terms": [],
            "phrases": []
        }
        
        # Extract quoted phrases
        phrase_pattern = r'"([^"]+)"'
        phrases = re.findall(phrase_pattern, query)
        result["phrases"] = phrases
        
        # Remove quoted phrases from query for term extraction
        query_without_phrases = re.sub(phrase_pattern, "", query)
        
        # Parse boolean operators (case-insensitive)
        # Split by AND, OR, NOT (with word boundaries)
        parts = re.split(r'\s+(AND|OR|NOT)\s+', query_without_phrases, flags=re.IGNORECASE)
        
        if len(parts) == 1:
            # No boolean operators, just a simple query
            result["base_query"] = query_without_phrases.strip()
            return result
        
        # Process parts with operators
        # parts alternates between terms and operators: [term1, "AND", term2, "OR", term3, ...]
        base_terms = []
        current_operator = None
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            
            if part.upper() in ["AND", "OR", "NOT"]:
                current_operator = part.upper()
            else:
                # This is a term
                if current_operator is None:
                    # First term (no operator before it) - part of base query
                    base_terms.append(part)
                elif current_operator == "AND":
                    result["and_terms"].append(part)
                elif current_operator == "OR":
                    result["or_terms"].append(part)
                elif current_operator == "NOT":
                    result["not_terms"].append(part)
                current_operator = None  # Reset after processing
        
        # First term(s) without operator are part of base query
        if base_terms:
            result["base_query"] = " ".join(base_terms)
        elif not result["and_terms"] and not result["or_terms"] and not result["not_terms"]:
            # If no base terms and no boolean terms, use original query
            result["base_query"] = query_without_phrases.strip()
        
        return result
    
    def _apply_boolean_operators(self, memory: MemoryRecord, parsed_query: Dict[str, Any]) -> bool:
        """
        Apply boolean operators to filter memory.
        
        Args:
            memory: Memory record to check
            parsed_query: Parsed query dictionary
            
        Returns:
            True if memory matches boolean criteria, False otherwise
        """
        memory_text_lower = memory.text.lower()
        
        # Check AND terms (all must be present)
        for term in parsed_query.get("and_terms", []):
            if term.lower() not in memory_text_lower:
                return False
        
        # Check NOT terms (none should be present)
        for term in parsed_query.get("not_terms", []):
            if term.lower() in memory_text_lower:
                return False
        
        # Check OR terms (at least one should be present if OR terms exist)
        or_terms = parsed_query.get("or_terms", [])
        base_query = parsed_query.get("base_query", "").strip()
        
        if or_terms:
            has_or_term = any(term.lower() in memory_text_lower for term in or_terms)
            # If there's a base query, OR terms are additional (memory can match base query OR OR terms)
            # If only OR terms exist (no base query), at least one OR term must match
            if not base_query:
                # Only OR terms - must match at least one
                if not has_or_term:
                    return False
            else:
                # Base query + OR terms - can match base query OR any OR term
                # If it doesn't match base query, it must match at least one OR term
                base_matches = any(word.lower() in memory_text_lower for word in base_query.split())
                if not base_matches and not has_or_term:
                    return False
        
        return True
    
    def get_memory(self, memory_id: int) -> Optional[MemoryRecord]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            MemoryRecord if found, None otherwise
        """
        return self.storage.get_memory(memory_id)
    
    def delete_memory(self, memory_id: int) -> bool:
        """
        Delete a memory from storage and index.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deletion successful, False if memory not found
        """
        try:
            # Check if memory exists
            memory = self.storage.get_memory(memory_id)
            if memory is None:
                logger.warning(f"Memory {memory_id} not found for deletion")
                return False
            
            # Delete from storage first
            success = self.storage.delete_memory(memory_id)
            
            if not success:
                return False
            
            # Remove from vector index (clears index, will rebuild)
            self.vector_index.remove_vector(memory_id)
            
            # Rebuild index from remaining memories in storage
            try:
                self._rebuild_index_from_storage()
            except Exception as rebuild_error:
                logger.error(
                    f"Error rebuilding index after deletion of memory {memory_id}: {rebuild_error}",
                    exc_info=True
                )
                # Continue - index will be rebuilt on next sync/startup
            
            # Always save index immediately after deletion (even if rebuild had issues)
            # This ensures the index state is persisted
            try:
                self.save_index()
            except Exception as save_error:
                logger.error(
                    f"Error saving index after deletion of memory {memory_id}: {save_error}",
                    exc_info=True
                )
                # Don't fail the deletion if save fails - it will be saved on close()
            
            logger.info(f"Deleted memory {memory_id} and synchronized index")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}", exc_info=True)
            return False
    
    def update_memory(
        self,
        memory_id: int,
        text: Optional[str] = None,
        namespace: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Update a memory's content and/or metadata.
        
        If text is updated, the embedding will be regenerated and the vector index
        will be updated. Metadata-only updates (namespace, importance, tags) don't
        require embedding regeneration.
        
        Args:
            memory_id: ID of memory to update
            text: Optional new text content (triggers embedding regeneration)
            namespace: Optional new namespace
            importance: Optional new importance score
            tags: Optional new tags list
            
        Returns:
            True if update successful, False if memory not found
        """
        try:
            # Get existing memory
            memory = self.storage.get_memory(memory_id)
            if memory is None:
                logger.warning(f"Memory {memory_id} not found for update")
                return False
            
            # Determine what needs updating
            update_text = text is not None and text != memory.text
            update_embedding = update_text
            
            # Build update parameters
            new_text = text if text is not None else memory.text
            new_namespace = namespace if namespace is not None else memory.namespace
            new_importance = importance if importance is not None else memory.importance
            new_tags = tags if tags is not None else memory.tags
            
            # If text changed, regenerate embedding and update index
            if update_embedding:
                # Generate new embedding first
                new_embedding = self.embedding_service.generate_embedding(new_text)
                
                # Update memory in storage with new text and embedding
                cursor = self.storage._connection.cursor()
                cursor.execute("""
                    UPDATE memories 
                    SET text = ?, namespace = ?, importance = ?, tags = ?, 
                        embedding = ?, last_used_at = ?
                    WHERE id = ?
                """, (
                    new_text,
                    new_namespace,
                    new_importance,
                    json.dumps(new_tags),
                    json.dumps(new_embedding),
                    datetime.now(timezone.utc).isoformat(),
                    memory_id
                ))
                self.storage._connection.commit()
                
                # Remove old vector from index (clears index, will rebuild)
                self.vector_index.remove_vector(memory_id)
                
                # Rebuild index (will include the updated memory)
                try:
                    self._rebuild_index_from_storage()
                except Exception as rebuild_error:
                    logger.error(
                        f"Error rebuilding index after update of memory {memory_id}: {rebuild_error}",
                        exc_info=True
                    )
                    # Continue - index will be rebuilt on next sync/startup
                
                # Always save index immediately after update (even if rebuild had issues)
                # This ensures the index state is persisted
                try:
                    self.save_index()
                except Exception as save_error:
                    logger.error(
                        f"Error saving index after update of memory {memory_id}: {save_error}",
                        exc_info=True
                    )
                    # Don't fail the update if save fails - it will be saved on close()
                
                logger.info(f"Updated memory {memory_id} with new text and embedding, synchronized index")
            else:
                # Metadata-only update (no embedding change needed)
                # Use existing update_memory method for metadata
                if namespace is not None or importance is not None or tags is not None:
                    # Use storage's update_memory for metadata
                    update_importance = importance if importance is not None else memory.importance
                    update_tags = tags if tags is not None else memory.tags
                    
                    # Also update namespace if provided
                    if namespace is not None and namespace != memory.namespace:
                        cursor = self.storage._connection.cursor()
                        cursor.execute("""
                            UPDATE memories 
                            SET namespace = ?, importance = ?, tags = ?, last_used_at = ?
                            WHERE id = ?
                        """, (
                            namespace,
                            update_importance,
                            json.dumps(update_tags),
                            datetime.now(timezone.utc).isoformat(),
                            memory_id
                        ))
                        self.storage._connection.commit()
                    else:
                        self.storage.update_memory(memory_id, update_importance, update_tags)
                    
                    logger.info(f"Updated memory {memory_id} metadata")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}", exc_info=True)
            return False
    
    # ===== RELATIONSHIP METHODS =====
    
    def link_memories(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Link two memories with a relationship.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        return self.relationships.link(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata
        )
    
    def unlink_memories(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Unlink two memories (remove relationship).
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        return self.relationships.unlink(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
    
    def get_related_memories(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, Any]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        return self.relationships.get_related(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction,
            min_strength=min_strength,
            limit=limit
        )
    
    def get_relationship_graph(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        return self.relationships.get_relationship_graph(memory_ids, depth)
    
    def _auto_detect_relationships(
        self,
        memory_id: int,
        record: MemoryRecord,
        embedding: List[float],
        conflicts_detected: List[Any]
    ) -> None:
        """
        Auto-detect and create relationships for a newly stored memory.
        
        Args:
            memory_id: ID of the newly stored memory
            record: MemoryRecord that was stored
            embedding: Embedding vector for the memory
            conflicts_detected: List of conflicts detected (if any)
        """
        try:
            # 1. Auto-detect CONTRADICTS relationships from conflicts
            if conflicts_detected:
                for conflict in conflicts_detected:
                    if hasattr(conflict, 'memory1') and conflict.memory1 and conflict.memory1.id:
                        other_memory_id = conflict.memory1.id
                        if other_memory_id != memory_id:
                            try:
                                self.relationships.link(
                                    source_id=memory_id,
                                    target_id=other_memory_id,
                                    relation_type=RelationType.CONTRADICTS,
                                    strength=conflict.confidence if hasattr(conflict, 'confidence') else 0.8,
                                    metadata={
                                        "detection_method": "conflict_detection",
                                        "auto_detected": True,
                                        "conflict_type": conflict.conflict_type if hasattr(conflict, 'conflict_type') else "unknown"
                                    }
                                )
                            except Exception as e:
                                logger.debug(f"Could not create CONTRADICTS relationship: {e}")
            
            # 2. Auto-detect SIMILAR_TO relationships based on embedding similarity
            try:
                # Find similar memories using vector search
                similar_memories = self.retrieve_memories(
                    query=record.text,
                    limit=5,
                    namespace=record.namespace
                )
                
                for similar_mem in similar_memories:
                    if similar_mem.id and similar_mem.id != memory_id:
                        # Calculate similarity (cosine similarity of embeddings)
                        if similar_mem.embedding:
                            # Get embedding for current memory from index or regenerate
                            similarity = self._cosine_similarity(embedding, similar_mem.embedding)
                            
                            if similarity > 0.85:  # Threshold for SIMILAR_TO
                                try:
                                    self.relationships.link(
                                        source_id=memory_id,
                                        target_id=similar_mem.id,
                                        relation_type=RelationType.SIMILAR_TO,
                                        strength=similarity,
                                        bidirectional=True,
                                        metadata={
                                            "detection_method": "embedding_similarity",
                                            "auto_detected": True,
                                            "similarity_score": similarity
                                        }
                                    )
                                except Exception as e:
                                    logger.debug(f"Could not create SIMILAR_TO relationship: {e}")
            except Exception as e:
                logger.debug(f"Error in similarity-based auto-detection: {e}")
            
            # 3. Auto-detect ELABORATES relationships for namespace hierarchy
            if "." in record.namespace:
                try:
                    parent_ns = record.namespace.rsplit(".", 1)[0]
                    parent_memories = self.storage.search_by_namespace(parent_ns, exact=True, limit=10)
                    
                    for parent_mem in parent_memories:
                        if parent_mem.id and parent_mem.id != memory_id:
                            try:
                                self.relationships.link(
                                    source_id=memory_id,
                                    target_id=parent_mem.id,
                                    relation_type=RelationType.ELABORATES,
                                    strength=0.7,
                                    metadata={
                                        "detection_method": "namespace_hierarchy",
                                        "auto_detected": True
                                    }
                                )
                            except Exception as e:
                                logger.debug(f"Could not create ELABORATES relationship: {e}")
                except Exception as e:
                    logger.debug(f"Error in namespace hierarchy auto-detection: {e}")
            
            # 4. Auto-detect SUPERSEDES when duplicate is updated
            # (This is handled in the duplicate update path)
            
        except Exception as e:
            logger.warning(f"Error in auto-detection: {e}", exc_info=True)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def save_index(self) -> None:
        """Save vector index to disk."""
        if self.vector_index.index_path:
            self.vector_index.save_index()
    
    # ===== EPISTEMIC TRACKING METHODS =====
    
    def retrieve_memories_with_epistemic(
        self,
        query: str,
        limit: int = 10,
        namespace: Optional[str] = None,
        namespaces: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        epistemic_engine: Optional[Any] = None,
        min_confidence: Optional[float] = None,
        rank_by_confidence: bool = True,
        warn_low_confidence: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Retrieve memories with epistemic confidence filtering/ranking.
        
        Args:
            query: Text query for vector similarity search
            limit: Maximum number of results
            namespace: Optional single namespace filter (deprecated, use namespaces)
            namespaces: Optional list of namespaces to search across
            tags: Optional tags filter
            epistemic_engine: Optional MetacognitiveEngine instance for epistemic tracking
            min_confidence: Optional minimum confidence threshold (0.0-1.0) to filter memories
            rank_by_confidence: If True, rank results by epistemic confidence (default: True)
            warn_low_confidence: If True, include warnings for low-confidence memories (default: True)
            **kwargs: Additional arguments passed to retrieve_memories()
            
        Returns:
            Dictionary containing:
                - memories: List[MemoryRecord] - Filtered and ranked memories
                - epistemic_context: Dict - Epistemic metadata about retrieved memories
                - low_confidence_warnings: List[Dict] - Warnings for low-confidence memories
                - confidence_stats: Dict - Statistics about confidence distribution
        """
        # Retrieve memories using existing method
        memories = self.retrieve_memories(
            query=query,
            limit=limit * 2 if min_confidence or rank_by_confidence else limit,  # Get more to filter/rank
            namespace=namespace,
            namespaces=namespaces,
            tags=tags,
            **kwargs
        )
        
        # If no epistemic engine, return basic results
        if not epistemic_engine or not epistemic_engine.epistemic_layer:
            return {
                "memories": memories[:limit],
                "epistemic_context": None,
                "low_confidence_warnings": [],
                "confidence_stats": {},
                "retrieval_confidence": 0.8 if memories else 0.0,
                "completeness_estimate": min(1.0, len(memories) / limit) if limit > 0 else 1.0
            }
        
        # Build epistemic context and get confidence scores
        from broca.self_model.epistemic.models import SourceType, SourceMetadata
        from collections import Counter
        
        memory_confidence_pairs = []
        source_breakdown = Counter()
        confidence_scores = []
        low_confidence_warnings = []
        
        for memory in memories:
            if not memory.id:
                continue
            
            # Get knowledge ID for this memory
            knowledge_id = epistemic_engine.epistemic_layer.get_knowledge_id_for_memory(memory.id)
            
            # Get confidence metrics
            confidence = memory.importance  # Default to importance if no epistemic data
            if knowledge_id:
                metrics = epistemic_engine.epistemic_layer.get_confidence_metrics(knowledge_id)
                if metrics:
                    confidence = metrics.overall_confidence
                    source = epistemic_engine.epistemic_layer.get_knowledge_source(knowledge_id)
                    if source:
                        source_breakdown[source.source_type] += 1
                else:
                    # Has knowledge ID but no metrics - use importance as fallback
                    confidence = memory.importance
            else:
                # No knowledge ID - use importance as fallback
                confidence = memory.importance
            
            confidence_scores.append(confidence)
            
            # Check if below warning threshold
            if warn_low_confidence and confidence < 0.5:
                low_confidence_warnings.append({
                    "memory_id": memory.id,
                    "confidence": confidence,
                    "text_preview": memory.text[:100] if memory.text else "",
                    "namespace": memory.namespace,
                    "knowledge_id": knowledge_id
                })
            
            # Store memory with confidence for filtering/ranking
            memory_confidence_pairs.append((memory, confidence))
        
        # Filter by confidence threshold if provided
        if min_confidence is not None:
            memory_confidence_pairs = [
                (mem, conf) for mem, conf in memory_confidence_pairs
                if conf >= min_confidence
            ]
        
        # Rank by confidence if requested
        if rank_by_confidence:
            memory_confidence_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Extract filtered/ranked memories
        filtered_memories = [mem for mem, _ in memory_confidence_pairs[:limit]]
        
        # Build epistemic context
        epistemic_context = {
            "source_breakdown": dict(source_breakdown),
            "confidence_distribution": {
                "min": min(confidence_scores) if confidence_scores else 0.0,
                "max": max(confidence_scores) if confidence_scores else 1.0,
                "avg": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5,
                "median": sorted(confidence_scores)[len(confidence_scores) // 2] if confidence_scores else 0.5
            },
            "retrieval_count": len(filtered_memories),
            "total_candidates": len(memories),
            "filtered_count": len(memories) - len(filtered_memories) if min_confidence else 0,
            "suggested_verification": [
                w["memory_id"] for w in low_confidence_warnings[:5]  # Top 5 for verification
            ]
        }
        
        # Build confidence stats
        confidence_stats = {
            "total_memories": len(filtered_memories),
            "low_confidence_count": len(low_confidence_warnings),
            "high_confidence_count": sum(1 for _, conf in memory_confidence_pairs[:limit] if conf >= 0.7),
            "average_confidence": epistemic_context["confidence_distribution"]["avg"]
        }
        
        return {
            "memories": filtered_memories,
            "epistemic_context": epistemic_context,
            "low_confidence_warnings": low_confidence_warnings,
            "confidence_stats": confidence_stats,
            "retrieval_confidence": epistemic_context["confidence_distribution"]["avg"],
            "completeness_estimate": min(1.0, len(filtered_memories) / limit) if limit > 0 else 1.0
        }
    
    def retrieve_with_metadata(
        self,
        query: str,
        limit: int = 10,
        namespace: Optional[str] = None,
        tags: Optional[List[str]] = None,
        epistemic_engine: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Retrieve memories with epistemic metadata (deprecated, use retrieve_memories_with_epistemic).
        
        This method is kept for backward compatibility.
        """
        return self.retrieve_memories_with_epistemic(
            query=query,
            limit=limit,
            namespace=namespace,
            tags=tags,
            epistemic_engine=epistemic_engine,
            rank_by_confidence=False,
            warn_low_confidence=False
        )
    
    def store_memory_with_epistemic(
        self,
        namespace: str,
        text: str,
        importance: float,
        tags: Optional[List[str]] = None,
        epistemic_engine: Optional[Any] = None,
        source_metadata: Optional[Any] = None,
        **kwargs
    ) -> Tuple[int, bool, List[Any], Optional[Dict[str, Any]]]:
        """
        Store memory with epistemic tracking.
        
        Args:
            namespace: Hierarchical namespace
            text: Memory content
            importance: Importance score (0.0-1.0)
            tags: Optional list of tags
            epistemic_engine: Optional MetacognitiveEngine instance
            source_metadata: Optional SourceMetadata for tracking
            **kwargs: Additional arguments passed to store_memory
            
        Returns:
            Tuple of (memory_id, was_duplicate, conflicts_detected, epistemic_result)
        """
        # Store memory using existing method
        memory_id, was_duplicate, conflicts = self.store_memory(
            namespace=namespace,
            text=text,
            importance=importance,
            tags=tags,
            **kwargs
        )
        
        # Track epistemic metadata if engine provided
        epistemic_result = None
        if epistemic_engine and memory_id:
            from broca.self_model.epistemic.models import SourceType, SourceMetadata
            from broca.self_model.epistemic.ids import generate_knowledge_id
            
            # Create source metadata if not provided
            if not source_metadata:
                source_metadata = SourceMetadata(
                    source_type=SourceType.MEMORY_RETRIEVAL,
                    memory_id=memory_id,
                    retrieval_confidence=importance,
                    recency_weight=1.0,
                    importance_weight=importance
                )
            
            # Generate knowledge ID for this memory
            knowledge_id = generate_knowledge_id("memory", f"{namespace}:{text}")
            
            # Record knowledge acquisition
            try:
                metrics = epistemic_engine.knowledge_acquisition_workflow(
                    knowledge_id=knowledge_id,
                    source=source_metadata,
                    initial_confidence=importance
                )
                
                # Store memory-knowledge ID mapping in epistemic layer
                if epistemic_engine.epistemic_layer:
                    epistemic_engine.epistemic_layer.add_memory_knowledge_mapping(memory_id, knowledge_id)
                    logger.debug(
                        f"Created memory-knowledge mapping: memory_id={memory_id} -> knowledge_id={knowledge_id}"
                    )
                
                epistemic_result = {
                    "knowledge_id": knowledge_id,
                    "confidence_metrics": metrics,
                    "source": source_metadata
                }
            except Exception as e:
                logger.warning(f"Error tracking epistemic metadata: {e}", exc_info=True)
        
        return memory_id, was_duplicate, conflicts, epistemic_result
    
    def _ensure_namespace_index(self) -> None:
        """
        Ensure namespace index file exists, create if missing.
        
        Called during initialization to create the index file if it doesn't exist.
        """
        try:
            index_path = self.namespace_index.get_index_path()
            if not index_path.exists():
                logger.info("Namespace index file not found, creating initial index...")
                self.namespace_index.update_index()
        except Exception as e:
            logger.warning(f"Error ensuring namespace index exists: {e}", exc_info=True)
            # Don't fail initialization if index creation fails
    
    def retrieve_with_conflict_warnings(
        self,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Retrieve memories and warn about potential conflicts.
        
        Args:
            query: Text query for semantic search
            limit: Maximum number of results
            **kwargs: Additional arguments passed to retrieve_memories
            
        Returns:
            Dictionary containing:
                - memories: List of retrieved memories
                - conflicts: List of detected conflicts
                - warnings: List of conflict warnings
        """
        # Retrieve memories using existing method
        memories = self.retrieve_memories(query=query, limit=limit, **kwargs)
        
        # Detect conflicts in retrieved set
        conflicts = self._detect_conflicts_in_set(memories)
        
        # Generate warnings
        warnings = self._generate_conflict_warnings(conflicts)
        
        return {
            "memories": memories,
            "conflicts": conflicts,
            "warnings": warnings
        }
    
    def _detect_conflicts_in_set(
        self,
        memories: List[MemoryRecord]
    ) -> List[Any]:
        """
        Detect conflicts within a set of memories.
        
        Args:
            memories: List of memories to check for conflicts
            
        Returns:
            List of Conflict objects
        """
        if len(memories) < 2:
            return []
        
        from .conflict import ConflictDetector
        
        conflicts = []
        detector = ConflictDetector(
            memory_manager=self,
            similarity_threshold=0.85,
            contradiction_threshold=0.7
        )
        
        # Check each pair of memories
        for i, memory1 in enumerate(memories):
            for memory2 in memories[i+1:]:
                # Skip if same memory
                if memory1.id and memory2.id and memory1.id == memory2.id:
                    continue
                
                # Detect conflicts between this pair
                pair_conflicts = detector.detect_conflicts(memory1, [memory2])
                conflicts.extend(pair_conflicts)
        
        return conflicts
    
    def _generate_conflict_warnings(
        self,
        conflicts: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate user-friendly warnings from conflicts.
        
        Args:
            conflicts: List of Conflict objects
            
        Returns:
            List of warning dictionaries
        """
        warnings = []
        
        for conflict in conflicts:
            memory1_id = conflict.memory1.id if conflict.memory1.id else "unknown"
            memory2_id = conflict.memory2.id if conflict.memory2.id else "unknown"
            
            warning = {
                "type": conflict.conflict_type,
                "confidence": conflict.confidence,
                "memory1_id": memory1_id,
                "memory2_id": memory2_id,
                "memory1_preview": conflict.memory1.text[:100] if conflict.memory1.text else "",
                "memory2_preview": conflict.memory2.text[:100] if conflict.memory2.text else "",
                "evidence": conflict.evidence,
                "temporal_context": conflict.temporal_context,
                "message": f"Potential {conflict.conflict_type} detected between memories {memory1_id} and {memory2_id}"
            }
            
            if conflict.temporal_context == "different_periods":
                warning["message"] += " (different time periods - may be update rather than contradiction)"
            
            warnings.append(warning)
        
        return warnings
    
    def close(self) -> None:
        """Close storage and save index."""
        self.save_index()
        self.storage.close()
