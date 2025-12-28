"""
Memory tools for storing and retrieving memories.

Provides tools for the LLM to store and retrieve memories from the memory system.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from . import Tool
from ..memory.manager import MemoryManager
from ..memory import RelationType, SourceType, SourceMetadata, MemoryRecord
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..self_model.model import SelfModel
    from ..self_model.storage import SelfModelSQLiteStorage

logger = logging.getLogger(__name__)


class StoreMemoryTool:
    """
    Tool for storing memories.
    
    Allows the LLM to store facts, insights, and information for later retrieval.
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        epistemic_engine: Optional[Any] = None,
        self_model: Optional["SelfModel"] = None,
        storage: Optional[Any] = None
    ) -> None:
        """
        Initialize the store memory tool.
        
        Args:
            memory_manager: MemoryManager instance
            epistemic_engine: Optional MetacognitiveEngine for epistemic tracking
            self_model: Optional SelfModel instance for saving after memory storage
            storage: Optional storage instance for saving self-model
        """
        self.memory_manager = memory_manager
        self.epistemic_engine = epistemic_engine
        self.self_model = self_model
        self.storage = storage
        logger.info("Initialized StoreMemoryTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "store_memory"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Store a memory (fact, insight, or information) for later retrieval. "
            "Use this tool when you learn something important that should be remembered "
            "for future conversations. Memories are organized by namespace and tags, "
            "and can be retrieved using semantic search. "
            "By default, the system checks for exact duplicates and updates existing "
            "memories instead of creating new ones."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string",
                    "description": "Hierarchical namespace for organizing the memory (e.g., 'math.sage.api', 'user.preferences')"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags for categorizing the memory (e.g., ['api-change', 'sage', 'integral'])"
                },
                "text": {
                    "type": "string",
                    "description": "The memory content - the fact, insight, or information to store"
                },
                "importance": {
                    "type": "number",
                    "description": "Importance score from 0.0 to 1.0 (higher = more important)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.5
                },
                "deduplicate": {
                    "type": "boolean",
                    "description": "Whether to check for and update exact duplicates (default: true)",
                    "default": True
                },
                "conflict_check": {
                    "type": "boolean",
                    "description": "Whether to check for conflicts with existing memories (default: false)",
                    "default": False
                },
                "auto_resolve": {
                    "type": "boolean",
                    "description": "Whether to automatically resolve conflicts (if confidence high, default: false)",
                    "default": False
                },
                "ask_user_threshold": {
                    "type": "number",
                    "description": "Confidence threshold below which to ask user (0.0-1.0, default: 0.7)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7
                }
            },
            "required": ["namespace", "text"]
        }
    
    def execute(
        self,
        namespace: str,
        text: str,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        deduplicate: bool = True,
        conflict_check: bool = False,
        auto_resolve: bool = False,
        ask_user_threshold: float = 0.7,
        source_type: Optional[str] = None,
        source_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute memory storage with optional conflict resolution.
        
        Args:
            namespace: Hierarchical namespace
            text: Memory content
            tags: Optional list of tags
            importance: Importance score (0.0-1.0)
            deduplicate: Whether to check for exact duplicates
            conflict_check: Whether to check for conflicts
            auto_resolve: Whether to automatically resolve conflicts
            ask_user_threshold: Confidence threshold for asking user
            source_type: Optional source type (defaults to 'user' for user-initiated storage)
            source_metadata: Optional additional source metadata
            
        Returns:
            Dictionary with memory ID, was_duplicate flag, conflict info, and confirmation
        """
        try:
            # Validate and clean inputs
            if not namespace or not namespace.strip():
                raise ValueError("Namespace cannot be empty")
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            if not 0.0 <= importance <= 1.0:
                raise ValueError(f"Importance must be between 0.0 and 1.0, got {importance}")
            
            tags = tags or []
            
            # Create source metadata (default to USER for user-initiated storage)
            if source_type is None:
                source_type = "user"
            try:
                source_type_enum = SourceType(source_type)
            except ValueError:
                raise ValueError(f"Invalid source_type: {source_type}. Must be one of: {[st.value for st in SourceType]}")
            
            source = SourceMetadata(
                source_type=source_type_enum,
                metadata=source_metadata
            )
            
            # Store memory with epistemic tracking if engine available
            if self.epistemic_engine:
                try:
                    from broca.self_model.epistemic.models import SourceType as EpistemicSourceType, SourceMetadata as EpistemicSourceMetadata
                    from datetime import datetime, timezone
                    
                    epistemic_source_metadata = EpistemicSourceMetadata(
                        source_type=EpistemicSourceType.MEMORY_RETRIEVAL,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    memory_id, was_duplicate, conflicts_detected, epistemic_result = (
                        self.memory_manager.store_memory_with_epistemic(
                            namespace=namespace.strip(),
                            text=text.strip(),
                            importance=importance,
                            tags=tags,
                            epistemic_engine=self.epistemic_engine,
                            source_metadata=epistemic_source_metadata,
                            source=source,
                            deduplicate=deduplicate,
                            conflict_check=conflict_check,
                            auto_resolve=auto_resolve,
                            auto_link=True
                        )
                    )
                    
                    # Save self-model if self_model and storage are available and mapping was created
                    if self.self_model and self.storage and epistemic_result and self.epistemic_engine:
                        try:
                            # Verify mapping was created
                            if self.epistemic_engine.epistemic_layer.get_knowledge_id_for_memory(memory_id):
                                # Save self-model to persist the mapping
                                self.storage.save(self.self_model)
                                logger.debug(f"Saved self-model after memory storage to persist memory-knowledge mapping for memory {memory_id}")
                        except Exception as e:
                            logger.warning(f"Failed to save self-model after memory storage: {e}", exc_info=True)
                except Exception as e:
                    logger.warning(f"Error using epistemic-aware memory storage: {e}, falling back to regular storage", exc_info=True)
                    # Fall back to regular storage
                    memory_id, was_duplicate, conflicts_detected = self.memory_manager.store_memory(
                        namespace=namespace.strip(),
                        text=text.strip(),
                        importance=importance,
                        tags=tags,
                        source=source,
                        deduplicate=deduplicate,
                        conflict_check=conflict_check,
                        auto_resolve=auto_resolve,
                        auto_link=True
                    )
            else:
                # Store memory (returns tuple: memory_id, was_duplicate, conflicts_detected)
                memory_id, was_duplicate, conflicts_detected = self.memory_manager.store_memory(
                    namespace=namespace.strip(),
                    text=text.strip(),
                    importance=importance,
                    tags=tags,
                    source=source,
                    deduplicate=deduplicate,
                    conflict_check=conflict_check,
                    auto_resolve=auto_resolve,
                    auto_link=True  # Default to auto-linking relationships
                )
            
            result = {
                "success": True,
                "memory_id": memory_id,
                "was_duplicate": was_duplicate,
                "namespace": namespace,
                "message": f"Memory {'updated' if was_duplicate else 'stored'} successfully with ID {memory_id}"
            }
            
            # Add conflict information if conflict checking was enabled
            if conflict_check:
                # Serialize conflicts to dictionaries
                conflicts_serialized = []
                for conflict in conflicts_detected:
                    conflict_dict = {
                        "conflict_type": conflict.conflict_type,
                        "confidence": conflict.confidence,
                        "evidence": conflict.evidence,
                        "resolution_strategy": conflict.resolution_strategy,
                    }
                    # Include memory IDs instead of full objects
                    if conflict.memory1 and conflict.memory1.id:
                        conflict_dict["memory1_id"] = conflict.memory1.id
                    if conflict.memory2 and conflict.memory2.id:
                        conflict_dict["memory2_id"] = conflict.memory2.id
                    conflicts_serialized.append(conflict_dict)
                
                result["conflicts"] = conflicts_serialized
                result["conflict_count"] = len(conflicts_serialized)
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to store memory: {e}"
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format storage result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if result.get("success"):
            memory_id = result.get("memory_id")
            was_duplicate = result.get("was_duplicate", False)
            namespace = result.get("namespace", "unknown")
            
            if was_duplicate:
                return f"Memory updated (ID: {memory_id}) in namespace '{namespace}' (was duplicate)"
            else:
                return f"Memory stored successfully (ID: {memory_id}) in namespace '{namespace}'"
        else:
            return f"Error storing memory: {result.get('error', 'Unknown error')}"


class RetrieveMemoriesTool:
    """
    Tool for retrieving memories.
    
    Allows the LLM to search and retrieve stored memories using semantic search,
    namespace filtering, and tag filtering with temporal weighting.
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        epistemic_engine: Optional[Any] = None
    ) -> None:
        """
        Initialize the retrieve memories tool.
        
        Args:
            memory_manager: MemoryManager instance
            epistemic_engine: Optional MetacognitiveEngine for epistemic tracking
        """
        self.memory_manager = memory_manager
        self.epistemic_engine = epistemic_engine
        logger.info("Initialized RetrieveMemoriesTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "retrieve_memories"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Retrieve memories (facts, insights, or information) by query or by ID. "
            "Searches using semantic similarity, namespace filtering (single or multiple namespaces), "
            "and tag filtering. Supports boolean operators (AND, OR, NOT) in queries, exact phrase "
            "matching, exact namespace matching, and tag combination modes (any/all). "
            "Advanced search features: cross-namespace search (search across multiple namespaces), "
            "date range filtering (created_after/before, last_used_after/before), and importance "
            "filtering (min_importance, max_importance). Results are ranked by relevance with temporal "
            "weighting (newer memories rank higher). Each retrieved memory includes a 'Linked to' "
            "section showing related memories with relationship types, enabling graph traversal. "
            "For graph traversal: use memory_ids parameter to retrieve specific memories by ID (e.g., "
            "when following links from the 'Linked to' section). Use this tool when you need to recall "
            "previously stored information. Results are ranked by relevance and importance."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text query for semantic search - what information are you looking for? Required if memory_ids is not provided."
                },
                "memory_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Optional list of memory IDs to retrieve directly (for graph traversal). If provided, query is ignored and these specific memories are retrieved by ID. Use this when you see memory IDs in the 'Linked to' section and want to retrieve those specific memories."
                },
                "namespace": {
                    "type": "string",
                    "description": "Optional single namespace filter (fuzzy match by default). Deprecated in favor of 'namespaces' for multiple namespaces."
                },
                "namespaces": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of namespaces to search across (OR logic). If provided, 'namespace' is ignored."
                },
                "namespace_exact": {
                    "type": "boolean",
                    "description": "If true, use exact namespace matching; if false, use fuzzy matching (default: false)",
                    "default": False
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of tags to filter by"
                },
                "tag_mode": {
                    "type": "string",
                    "description": "Tag combination mode: 'any' (OR logic, default) or 'all' (AND logic)",
                    "enum": ["any", "all"],
                    "default": "any"
                },
                "query_phrases": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of exact phrases to match in memory text (case-insensitive)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of memories to retrieve (default: 5)",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5
                },
                "recency_weight": {
                    "type": "number",
                    "description": "Weight for recency in scoring (0.0 = ignore recency, 1.0 = only recency matters, default: 0.3)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3
                },
                "created_after": {
                    "type": "string",
                    "description": "Optional ISO format datetime string - filter memories created after this date"
                },
                "created_before": {
                    "type": "string",
                    "description": "Optional ISO format datetime string - filter memories created before this date"
                },
                "last_used_after": {
                    "type": "string",
                    "description": "Optional ISO format datetime string - filter memories last used after this date"
                },
                "last_used_before": {
                    "type": "string",
                    "description": "Optional ISO format datetime string - filter memories last used before this date"
                },
                "min_importance": {
                    "type": "number",
                    "description": "Optional minimum importance score (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "max_importance": {
                    "type": "number",
                    "description": "Optional maximum importance score (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "min_confidence": {
                    "type": "number",
                    "description": "Optional minimum epistemic confidence threshold (0.0-1.0). Filters out memories below this confidence level. Only used when epistemic engine is available.",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "rank_by_confidence": {
                    "type": "boolean",
                    "description": "If true, rank results by epistemic confidence instead of relevance (default: true when epistemic engine available). Only used when epistemic engine is available.",
                    "default": True
                },
                "warn_low_confidence": {
                    "type": "boolean",
                    "description": "If true, include warnings for low-confidence memories (default: true). Only used when epistemic engine is available.",
                    "default": True
                },
                "source_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["web_search", "user", "system_file", "terminal_output", "memory_retrieval", "unknown"]
                    },
                    "description": "Optional list of source types to filter by (e.g., ['web_search', 'user'])"
                },
                "include_linked": {
                    "type": "boolean",
                    "description": "If true, include linked memories (related memories) for each retrieved memory (default: true). Enables graph traversal.",
                    "default": True
                },
                "linked_limit": {
                    "type": "integer",
                    "description": "Maximum number of linked memories to include per memory (default: 5, max: 10)",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5
                }
            },
            "required": []
        }
    
    def execute(
        self,
        query: Optional[str] = None,
        memory_ids: Optional[List[int]] = None,
        namespace: Optional[str] = None,
        namespaces: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5,
        recency_weight: float = 0.3,
        namespace_exact: bool = False,
        tag_mode: str = "any",
        query_phrases: Optional[List[str]] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        last_used_after: Optional[str] = None,
        last_used_before: Optional[str] = None,
        min_importance: Optional[float] = None,
        max_importance: Optional[float] = None,
        min_confidence: Optional[float] = None,
        rank_by_confidence: bool = True,
        warn_low_confidence: bool = True,
        source_types: Optional[List[str]] = None,
        include_linked: bool = True,
        linked_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Execute memory retrieval with temporal weighting and enhanced search features.
        
        Args:
            query: Text query for semantic search (supports boolean operators: AND, OR, NOT). Required if memory_ids is not provided.
            memory_ids: Optional list of memory IDs to retrieve directly (for graph traversal). If provided, query is ignored.
            namespace: Optional single namespace filter (deprecated - use namespaces for multiple)
            namespaces: Optional list of namespaces to search across (OR logic)
            tags: Optional tag filters
            limit: Maximum number of results
            recency_weight: Weight for recency in scoring (0.0-1.0, default: 0.3)
            namespace_exact: If true, use exact namespace matching; if false, use fuzzy matching
            tag_mode: "any" for OR logic, "all" for AND logic
            query_phrases: Optional list of exact phrases to match in memory text
            created_after: Optional ISO format datetime string - filter by created_at
            created_before: Optional ISO format datetime string - filter by created_at
            last_used_after: Optional ISO format datetime string - filter by last_used_at
            last_used_before: Optional ISO format datetime string - filter by last_used_at
            min_importance: Optional minimum importance score (0.0-1.0)
            max_importance: Optional maximum importance score (0.0-1.0)
            min_confidence: Optional minimum epistemic confidence threshold (0.0-1.0)
            rank_by_confidence: If true, rank by epistemic confidence (default: True)
            warn_low_confidence: If true, include low-confidence warnings (default: True)
            source_types: Optional list of source types to filter by
            include_linked: If true, include linked memories for graph traversal (default: True)
            linked_limit: Maximum number of linked memories per memory (default: 5, max: 10)
            
        Returns:
            Dictionary with retrieved memories including temporal information, epistemic context, and linked memories
        """
        try:
            # Validate inputs - either query or memory_ids must be provided
            if memory_ids:
                # ID-based retrieval mode
                if not isinstance(memory_ids, list) or not all(isinstance(id, int) and id > 0 for id in memory_ids):
                    return {
                        "success": False,
                        "error": "memory_ids must be a list of positive integers"
                    }
                if len(memory_ids) > limit:
                    memory_ids = memory_ids[:limit]  # Limit to requested limit
            elif not query or not query.strip():
                raise ValueError("Either 'query' or 'memory_ids' must be provided")
            
            limit = max(1, min(20, limit))  # Clamp to valid range
            recency_weight = max(0.0, min(1.0, recency_weight))  # Clamp to 0.0-1.0
            
            # Validate tag_mode
            if tag_mode not in ["any", "all"]:
                tag_mode = "any"  # Default to "any" if invalid
            
            # Parse date strings to datetime objects
            parsed_created_after = None
            parsed_created_before = None
            parsed_last_used_after = None
            parsed_last_used_before = None
            
            if created_after:
                try:
                    parsed_created_after = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return {
                        "success": False,
                        "error": f"Invalid created_after date format: {created_after}. Use ISO format."
                    }
            
            if created_before:
                try:
                    parsed_created_before = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return {
                        "success": False,
                        "error": f"Invalid created_before date format: {created_before}. Use ISO format."
                    }
            
            if last_used_after:
                try:
                    parsed_last_used_after = datetime.fromisoformat(last_used_after.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return {
                        "success": False,
                        "error": f"Invalid last_used_after date format: {last_used_after}. Use ISO format."
                    }
            
            if last_used_before:
                try:
                    parsed_last_used_before = datetime.fromisoformat(last_used_before.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return {
                        "success": False,
                        "error": f"Invalid last_used_before date format: {last_used_before}. Use ISO format."
                    }
            
            # Validate importance ranges
            if min_importance is not None and (min_importance < 0.0 or min_importance > 1.0):
                return {
                    "success": False,
                    "error": f"min_importance must be between 0.0 and 1.0, got {min_importance}"
                }
            
            if max_importance is not None and (max_importance < 0.0 or max_importance > 1.0):
                return {
                    "success": False,
                    "error": f"max_importance must be between 0.0 and 1.0, got {max_importance}"
                }
            
            if min_importance is not None and max_importance is not None and min_importance > max_importance:
                return {
                    "success": False,
                    "error": f"min_importance ({min_importance}) cannot be greater than max_importance ({max_importance})"
                }
            
            # Validate confidence threshold
            if min_confidence is not None and (min_confidence < 0.0 or min_confidence > 1.0):
                return {
                    "success": False,
                    "error": f"min_confidence must be between 0.0 and 1.0, got {min_confidence}"
                }
            
            # Validate linked_limit
            linked_limit = max(1, min(10, linked_limit))  # Clamp to valid range
            
            # Convert source_types strings to SourceType enums if provided
            source_type_enums = None
            if source_types:
                try:
                    source_type_enums = [SourceType(st) for st in source_types]
                except ValueError as e:
                    return {
                        "success": False,
                        "error": f"Invalid source_type in list: {e}. Must be one of: {[st.value for st in SourceType]}"
                    }
            
            # Handle ID-based retrieval (for graph traversal)
            memories: List[MemoryRecord] = []
            epistemic_result_dict = None
            
            if memory_ids:
                # Direct ID-based retrieval - fetch memories by ID
                for memory_id in memory_ids:
                    memory = self.memory_manager.get_memory(memory_id)
                    if memory:
                        memories.append(memory)
                    else:
                        logger.warning(f"Memory {memory_id} not found during ID-based retrieval")
            else:
                # Query-based retrieval with enhanced search features
                # Use epistemic-aware retrieval if engine available
                if self.epistemic_engine:
                    try:
                        epistemic_result_dict = self.memory_manager.retrieve_memories_with_epistemic(
                            query=query.strip(),
                            limit=limit,
                            namespace=namespace.strip() if namespace else None,
                            namespaces=namespaces,
                            tags=tags,
                            epistemic_engine=self.epistemic_engine,
                            min_confidence=min_confidence,
                            rank_by_confidence=rank_by_confidence,
                            warn_low_confidence=warn_low_confidence,
                            recency_weight=recency_weight,
                            namespace_exact=namespace_exact,
                            tag_mode=tag_mode,
                            query_phrases=query_phrases,
                            created_after=parsed_created_after,
                            created_before=parsed_created_before,
                            last_used_after=parsed_last_used_after,
                            last_used_before=parsed_last_used_before,
                            min_importance=min_importance,
                            max_importance=max_importance,
                            source_types=source_type_enums
                        )
                        memories = epistemic_result_dict.get("memories", [])
                    except Exception as e:
                        logger.warning(f"Error using epistemic-aware memory retrieval: {e}, falling back to regular retrieval", exc_info=True)
                        memories = self.memory_manager.retrieve_memories(
                            query=query.strip(),
                            namespace=namespace.strip() if namespace else None,
                            namespaces=namespaces,
                            tags=tags,
                            limit=limit,
                            recency_weight=recency_weight,
                            namespace_exact=namespace_exact,
                            tag_mode=tag_mode,
                            query_phrases=query_phrases,
                            created_after=parsed_created_after,
                            created_before=parsed_created_before,
                            last_used_after=parsed_last_used_after,
                            last_used_before=parsed_last_used_before,
                            min_importance=min_importance,
                            max_importance=max_importance,
                            source_types=source_type_enums
                        )
                else:
                    memories = self.memory_manager.retrieve_memories(
                        query=query.strip(),
                        namespace=namespace.strip() if namespace else None,
                        namespaces=namespaces,
                        tags=tags,
                        limit=limit,
                        recency_weight=recency_weight,
                        namespace_exact=namespace_exact,
                        tag_mode=tag_mode,
                        query_phrases=query_phrases,
                        created_after=parsed_created_after,
                        created_before=parsed_created_before,
                        last_used_after=parsed_last_used_after,
                        last_used_before=parsed_last_used_before,
                        min_importance=min_importance,
                        max_importance=max_importance,
                        source_types=source_type_enums
                    )
            
            # Format results with temporal information
            results = []
            for memory in memories:
                # Calculate age information
                age = self.memory_manager.calculate_memory_age(memory)
                age_human = self.memory_manager.format_memory_age(memory)
                is_recent = self.memory_manager.is_memory_recent(memory, hours=24)
                
                result_item = {
                    "id": memory.id,
                    "namespace": memory.namespace,
                    "tags": memory.tags,
                    "text": memory.text,
                    "importance": memory.importance,
                    "created_at": memory.created_at.isoformat(),
                    "last_used_at": memory.last_used_at.isoformat(),
                    "age_days": age.days + age.seconds / 86400,
                    "age_human": age_human,
                    "is_recent": is_recent
                }
                
                # Fetch linked memories if requested
                if include_linked and memory.id:
                    try:
                        related_memories = self.memory_manager.get_related_memories(
                            memory_id=memory.id,
                            relation_types=None,  # Get all relationship types
                            direction="both",  # Get both outgoing and incoming
                            min_strength=0.0,
                            limit=linked_limit
                        )
                        
                        linked_memories_list = []
                        for related_memory, relationship in related_memories:
                            # Determine direction
                            if relationship.source_id == memory.id:
                                direction = "outgoing"
                            elif relationship.target_id == memory.id:
                                direction = "incoming"
                            else:
                                direction = "unknown"
                            
                            linked_memories_list.append({
                                "memory_id": related_memory.id,
                                "relationship_type": relationship.relation_type.value,
                                "relationship_strength": relationship.strength,
                                "direction": direction,
                                "text_preview": related_memory.text[:50] + "..." if len(related_memory.text) > 50 else related_memory.text
                            })
                        
                        result_item["linked_memories"] = linked_memories_list
                    except Exception as e:
                        logger.warning(f"Error fetching linked memories for memory {memory.id}: {e}", exc_info=True)
                        result_item["linked_memories"] = []
                else:
                    result_item["linked_memories"] = []
                
                # Add epistemic confidence if available
                if epistemic_result_dict and memory.id:
                    # Try to get confidence from epistemic context
                    epistemic_context = epistemic_result_dict.get("epistemic_context", {})
                    # Confidence would be in the memory-knowledge mapping
                    # For now, we'll add it in format_result if needed
                
                results.append(result_item)
            
            return_dict = {
                "success": True,
                "count": len(results),
                "memories": results,
                "recency_weight_used": recency_weight
            }
            
            # Include query or memory_ids in return dict for context
            if memory_ids:
                return_dict["memory_ids"] = memory_ids
                return_dict["retrieval_mode"] = "id_based"
            else:
                return_dict["query"] = query
                return_dict["retrieval_mode"] = "query_based"
            
            # Add epistemic context and warnings if available
            if epistemic_result_dict:
                return_dict["epistemic_context"] = epistemic_result_dict.get("epistemic_context")
                return_dict["low_confidence_warnings"] = epistemic_result_dict.get("low_confidence_warnings", [])
                return_dict["confidence_stats"] = epistemic_result_dict.get("confidence_stats", {})
            
            return return_dict
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "count": 0,
                "memories": []
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format retrieval results for LLM consumption with temporal information and epistemic context.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation of memories with temporal context and epistemic warnings
        """
        if not result.get("success"):
            return f"Error retrieving memories: {result.get('error', 'Unknown error')}"
        
        memories = result.get("memories", [])
        retrieval_mode = result.get("retrieval_mode", "query_based")
        recency_weight = result.get("recency_weight_used", 0.3)
        
        # Include epistemic warnings if available
        warnings = result.get("low_confidence_warnings", [])
        confidence_stats = result.get("confidence_stats", {})
        
        if not memories:
            if retrieval_mode == "id_based":
                memory_ids = result.get("memory_ids", [])
                return f"No memories found for IDs: {memory_ids}"
            else:
                query = result.get("query", "unknown")
                return f"No memories found for query: '{query}'"
        
        # Build header based on retrieval mode
        if retrieval_mode == "id_based":
            memory_ids = result.get("memory_ids", [])
            lines = [f"Found {len(memories)} memory(ies) by ID {memory_ids}:\n"]
        else:
            query = result.get("query", "unknown")
            lines = [f"Found {len(memories)} memory(ies) for query '{query}' (recency weight: {recency_weight}):\n"]
        
        # Add confidence stats if available
        if confidence_stats:
            avg_conf = confidence_stats.get("average_confidence", 0.0)
            lines.append(f"Epistemic confidence: average {avg_conf:.2f}, "
                        f"{confidence_stats.get('high_confidence_count', 0)} high-confidence, "
                        f"{confidence_stats.get('low_confidence_count', 0)} low-confidence memories\n")
        
        for i, memory in enumerate(memories, 1):
            lines.append(f"{i}. [ID: {memory['id']}] {memory['text']}")
            lines.append(f"   Namespace: {memory['namespace']}")
            if memory.get('tags'):
                lines.append(f"   Tags: {', '.join(memory['tags'])}")
            lines.append(f"   Importance: {memory['importance']:.2f}")
            lines.append(f"   Age: {memory.get('age_human', 'unknown')} (created: {memory['created_at'][:10]})")
            if memory.get('is_recent'):
                lines.append(f"   ✓ Recent (within 24 hours)")
            
            # Display linked memories if available
            linked_memories = memory.get('linked_memories', [])
            if linked_memories:
                lines.append(f"   Linked to:")
                # Limit display to top 5 linked memories
                for linked in linked_memories[:5]:
                    rel_type = linked.get('relationship_type', 'unknown')
                    strength = linked.get('relationship_strength', 1.0)
                    direction = linked.get('direction', 'unknown')
                    linked_id = linked.get('memory_id', 'unknown')
                    text_preview = linked.get('text_preview', '')
                    lines.append(f"     - Memory {linked_id} ({rel_type}, strength={strength:.2f}, {direction}): \"{text_preview}\"")
                if len(linked_memories) > 5:
                    lines.append(f"     ... and {len(linked_memories) - 5} more linked memories")
            
            lines.append("")  # Empty line between memories
        
        # Add warnings if available
        if warnings:
            lines.append("\n⚠️  Low-confidence warnings:")
            for warning in warnings[:5]:  # Show top 5 warnings
                lines.append(f"   - Memory ID {warning.get('memory_id')}: "
                           f"confidence {warning.get('confidence', 0.0):.2f} "
                           f"({warning.get('text_preview', '')[:50]}...)")
            if len(warnings) > 5:
                lines.append(f"   ... and {len(warnings) - 5} more low-confidence memories")
        
        return "\n".join(lines)


class DeleteMemoryTool:
    """
    Tool for deleting memories.
    
    Allows the LLM to delete memories that are no longer needed or incorrect.
    """
    
    def __init__(self, memory_manager: MemoryManager) -> None:
        """
        Initialize the delete memory tool.
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager
        logger.info("Initialized DeleteMemoryTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "delete_memory"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Delete a memory by its ID. Use this tool when a memory is incorrect, "
            "outdated, or no longer needed. The memory will be permanently removed "
            "from both storage and the search index."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer",
                    "description": "The ID of the memory to delete"
                }
            },
            "required": ["memory_id"]
        }
    
    def execute(self, memory_id: int) -> Dict[str, Any]:
        """
        Execute memory deletion.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            Dictionary with success status and message
        """
        try:
            # Validate input
            if not isinstance(memory_id, int) or memory_id <= 0:
                raise ValueError(f"Invalid memory_id: {memory_id}")
            
            # Delete memory
            success = self.memory_manager.delete_memory(memory_id)
            
            if success:
                return {
                    "success": True,
                    "memory_id": memory_id,
                    "message": f"Memory {memory_id} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "memory_id": memory_id,
                    "error": "Memory not found",
                    "message": f"Memory {memory_id} not found"
                }
                
        except Exception as e:
            logger.error(f"Error deleting memory: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete memory: {e}"
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format deletion result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if result.get("success"):
            memory_id = result.get("memory_id")
            return f"Memory {memory_id} deleted successfully"
        else:
            error = result.get("error", "Unknown error")
            return f"Error deleting memory: {error}"


class UpdateMemoryTool:
    """
    Tool for updating memories.
    
    Allows the LLM to update memory content (text), metadata (importance, tags),
    or namespace. Text updates will regenerate embeddings for accurate search.
    """
    
    def __init__(self, memory_manager: MemoryManager) -> None:
        """
        Initialize the update memory tool.
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager
        logger.info("Initialized UpdateMemoryTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "update_memory"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Update an existing memory's content or metadata. You can update the text "
            "(which will regenerate the embedding for accurate search), namespace, "
            "importance score, or tags. All parameters except memory_id are optional - "
            "only provide the fields you want to update."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer",
                    "description": "The ID of the memory to update"
                },
                "text": {
                    "type": "string",
                    "description": "New text content (optional, will regenerate embedding if provided)"
                },
                "namespace": {
                    "type": "string",
                    "description": "New namespace (optional)"
                },
                "importance": {
                    "type": "number",
                    "description": "New importance score from 0.0 to 1.0 (optional)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New tags list (optional)"
                }
            },
            "required": ["memory_id"]
        }
    
    def execute(
        self,
        memory_id: int,
        text: Optional[str] = None,
        namespace: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute memory update.
        
        Args:
            memory_id: ID of memory to update
            text: Optional new text content
            namespace: Optional new namespace
            importance: Optional new importance score
            tags: Optional new tags list
            
        Returns:
            Dictionary with success status and updated memory details
        """
        try:
            # Validate inputs
            if not isinstance(memory_id, int) or memory_id <= 0:
                raise ValueError(f"Invalid memory_id: {memory_id}")
            
            if text is not None and (not text or not text.strip()):
                raise ValueError("Text cannot be empty")
            
            if importance is not None and not (0.0 <= importance <= 1.0):
                raise ValueError(f"Importance must be between 0.0 and 1.0, got {importance}")
            
            # Update memory
            success = self.memory_manager.update_memory(
                memory_id=memory_id,
                text=text.strip() if text else None,
                namespace=namespace.strip() if namespace else None,
                importance=importance,
                tags=tags
            )
            
            if success:
                # Get updated memory
                updated_memory = self.memory_manager.get_memory(memory_id)
                
                result = {
                    "success": True,
                    "memory_id": memory_id,
                    "message": f"Memory {memory_id} updated successfully"
                }
                
                if updated_memory:
                    result["memory"] = {
                        "id": updated_memory.id,
                        "namespace": updated_memory.namespace,
                        "tags": updated_memory.tags,
                        "text": updated_memory.text,
                        "importance": updated_memory.importance
                    }
                
                return result
            else:
                return {
                    "success": False,
                    "memory_id": memory_id,
                    "error": "Memory not found",
                    "message": f"Memory {memory_id} not found"
                }
                
        except Exception as e:
            logger.error(f"Error updating memory: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update memory: {e}"
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format update result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if result.get("success"):
            memory_id = result.get("memory_id")
            memory = result.get("memory")
            if memory:
                return (
                    f"Memory {memory_id} updated successfully. "
                    f"Namespace: {memory['namespace']}, "
                    f"Importance: {memory['importance']:.2f}, "
                    f"Tags: {', '.join(memory['tags']) if memory['tags'] else 'none'}"
                )
            else:
                return f"Memory {memory_id} updated successfully"
        else:
            error = result.get("error", "Unknown error")
            return f"Error updating memory: {error}"


class LinkMemoriesTool:
    """
    Tool for creating relationships between memories.
    
    Allows the LLM to explicitly link memories with typed relationships.
    """
    
    def __init__(self, memory_manager: MemoryManager) -> None:
        """
        Initialize the link memories tool.
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager
        logger.info("Initialized LinkMemoriesTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "link_memories"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Create a relationship between two memories. "
            "Relationships can be typed (supports, contradicts, elaborates, etc.) "
            "and have a strength score. Some relationships can be bidirectional."
        )
    
    @property
    def parameters(self) -> dict:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "source_id": {
                    "type": "integer",
                    "description": "ID of the source memory"
                },
                "target_id": {
                    "type": "integer",
                    "description": "ID of the target memory"
                },
                "relation_type": {
                    "type": "string",
                    "enum": [
                        "supports", "contradicts", "supersedes", "elaborates",
                        "summarizes", "references", "causes", "caused_by",
                        "precedes", "follows", "similar_to", "related_to"
                    ],
                    "description": "Type of relationship"
                },
                "strength": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 1.0,
                    "description": "Relationship strength (0.0-1.0)"
                },
                "bidirectional": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether relationship goes both ways"
                }
            },
            "required": ["source_id", "target_id", "relation_type"]
        }
    
    def execute(
        self,
        source_id: int,
        target_id: int,
        relation_type: str,
        strength: float = 1.0,
        bidirectional: bool = False
    ) -> Dict[str, Any]:
        """
        Execute the link memories tool.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0)
            bidirectional: Whether relationship goes both ways
            
        Returns:
            Result dictionary
        """
        try:
            # Validate relation_type
            try:
                rel_type = RelationType(relation_type)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid relation_type: {relation_type}",
                    "message": f"Relation type must be one of: {[rt.value for rt in RelationType]}"
                }
            
            # Validate strength
            if not 0.0 <= strength <= 1.0:
                return {
                    "success": False,
                    "error": f"Invalid strength: {strength}",
                    "message": "Strength must be between 0.0 and 1.0"
                }
            
            # Link memories
            relationship_id = self.memory_manager.link_memories(
                source_id=source_id,
                target_id=target_id,
                relation_type=rel_type,
                strength=strength,
                bidirectional=bidirectional
            )
            
            return {
                "success": True,
                "relationship_id": relationship_id,
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": relation_type,
                "strength": strength,
                "bidirectional": bidirectional,
                "message": f"Linked memory {source_id} -> {target_id} ({relation_type})"
            }
            
        except ValueError as e:
            logger.error(f"Error linking memories: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to link memories: {e}"
            }
        except Exception as e:
            logger.error(f"Error linking memories: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to link memories: {e}"
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format link result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if result.get("success"):
            source_id = result.get("source_id")
            target_id = result.get("target_id")
            relation_type = result.get("relation_type", "unknown")
            strength = result.get("strength", 1.0)
            bidirectional = result.get("bidirectional", False)
            
            direction = " <-> " if bidirectional else " -> "
            strength_str = f", strength={strength:.2f}" if strength != 1.0 else ""
            
            return f"Linked memory {source_id}{direction}{target_id} ({relation_type}{strength_str})"
        else:
            error = result.get("error", "Unknown error")
            return f"Error linking memories: {error}"


class GetRelatedMemoriesTool:
    """
    Tool for retrieving related memories.
    
    Allows the LLM to find memories related to a given memory through relationships.
    """
    
    def __init__(self, memory_manager: MemoryManager) -> None:
        """
        Initialize the get related memories tool.
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager
        logger.info("Initialized GetRelatedMemoriesTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "get_related_memories"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Get memories related to a given memory through relationships. "
            "Can filter by relationship types and include implicit relationships "
            "based on similarity."
        )
    
    @property
    def parameters(self) -> dict:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer",
                    "description": "ID of the memory to find relations for"
                },
                "relation_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by relationship types (optional)"
                },
                "include_implicit": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include auto-detected similar memories"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Maximum number of results"
                }
            },
            "required": ["memory_id"]
        }
    
    def execute(
        self,
        memory_id: int,
        relation_types: Optional[List[str]] = None,
        include_implicit: bool = True,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Execute the get related memories tool.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            include_implicit: Include auto-detected similar memories (not used yet)
            limit: Maximum number of results
            
        Returns:
            Result dictionary
        """
        try:
            # Verify memory exists
            memory = self.memory_manager.get_memory(memory_id)
            if not memory:
                return {
                    "success": False,
                    "error": f"Memory {memory_id} not found",
                    "message": f"Memory {memory_id} does not exist"
                }
            
            # Convert relation_types strings to RelationType enums
            rel_types = None
            if relation_types:
                try:
                    rel_types = [RelationType(rt) for rt in relation_types]
                except ValueError as e:
                    return {
                        "success": False,
                        "error": f"Invalid relation_type in list: {e}",
                        "message": f"Invalid relation types: {relation_types}"
                    }
            
            # Get related memories
            related = self.memory_manager.get_related_memories(
                memory_id=memory_id,
                relation_types=rel_types,
                limit=limit
            )
            
            # Format results
            related_memories = []
            for mem, rel in related:
                related_memories.append({
                    "memory_id": mem.id,
                    "namespace": mem.namespace,
                    "text": mem.text,
                    "importance": mem.importance,
                    "relationship_type": rel.relation_type.value,
                    "relationship_strength": rel.strength,
                    "bidirectional": rel.bidirectional
                })
            
            return {
                "success": True,
                "memory_id": memory_id,
                "related_memories": related_memories,
                "count": len(related_memories),
                "message": f"Found {len(related_memories)} related memories"
            }
            
        except Exception as e:
            logger.error(f"Error getting related memories: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get related memories: {e}"
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format get related memories result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return f"Error getting related memories: {error}"
        
        memory_id = result.get("memory_id")
        related_memories = result.get("related_memories", [])
        count = result.get("count", len(related_memories))
        
        if count == 0:
            return f"No related memories found for memory {memory_id}"
        
        lines = [f"Found {count} related memory{'ies' if count != 1 else ''} for memory {memory_id}:\n"]
        
        for i, mem in enumerate(related_memories, 1):
            mem_id = mem.get("memory_id")
            text = mem.get("text", "")
            rel_type = mem.get("relationship_type", "unknown")
            strength = mem.get("relationship_strength", 1.0)
            
            # Truncate text if too long
            text_preview = text[:50] + "..." if len(text) > 50 else text
            
            lines.append(
                f"{i}. Memory {mem_id} ({rel_type}, strength={strength:.2f}): {text_preview}"
            )
        
        return "\n".join(lines)
