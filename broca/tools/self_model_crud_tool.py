"""
Enhanced Self-Model CRUD Tool.

Provides comprehensive Create, Read, Update, Delete operations for the self-model
with epistemic context integration and batch operation support.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from . import Tool
from ..self_model.model import SelfModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..self_model.storage import SelfModelSQLiteStorage

logger = logging.getLogger(__name__)


class SelfModelCRUDTool:
    """
    Comprehensive CRUD tool for self-model operations.
    
    Provides unified interface for all self-model operations:
    - Create: Add new entries
    - Read: Query self-model
    - Update: Modify existing entries
    - Delete: Remove entries
    - List: List entries with filtering
    """
    
    def __init__(
        self,
        self_model: SelfModel,
        storage: Any,
        epistemic_engine: Optional[Any] = None,
    ) -> None:
        """
        Initialize the CRUD tool.
        
        Args:
            self_model: SelfModel instance
            storage: Storage instance for self-model
            epistemic_engine: Optional MetacognitiveEngine for epistemic context
        """
        self.self_model = self_model
        self.storage = storage
        self.epistemic_engine = epistemic_engine
        
        # Log the database path being used for persistence
        if hasattr(storage, 'db_path'):
            db_path = storage.db_path
            if hasattr(db_path, 'absolute'):
                abs_path = db_path.absolute()
                logger.info(f"Initialized SelfModelCRUDTool with database at: {abs_path}")
            else:
                logger.info(f"Initialized SelfModelCRUDTool with database at: {db_path}")
        else:
            logger.info("Initialized SelfModelCRUDTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "self_model_crud"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Comprehensive tool for managing your self-model. Use this tool to: "
            "query your capabilities, knowledge boundaries, and constraints; "
            "create new entries; update existing ones; delete outdated entries; "
            "and get epistemic context about entries. "
            "This tool helps you maintain an accurate and up-to-date model of yourself."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["query", "create", "update", "delete", "list", "get_epistemic"],
                    "description": "Action to perform: query (read), create, update, delete, list, or get_epistemic"
                },
                "aspect": {
                    "type": "string",
                    "enum": ["all", "capabilities", "knowledge_boundaries", "constraints", "behaviors", "metadata"],
                    "description": "Which aspect of self-model to operate on. 'behaviors' queries behavioral patterns from metadata.",
                    "default": "all"
                },
                "entries": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Entries for create/update operations (list of dicts or strings)"
                },
                "match_criteria": {
                    "type": "object",
                    "description": "Criteria for matching entries to update/delete (text, source, etc.)",
                    "additionalProperties": True
                },
                "filters": {
                    "type": "object",
                    "description": "Filters for query/list operations",
                    "additionalProperties": True
                },
                "entry_id": {
                    "type": "string",
                    "description": "Entry identifier for get_epistemic action"
                },
                "include_epistemic": {
                    "type": "boolean",
                    "description": "Whether to include epistemic context in responses",
                    "default": True
                },
                "rationale": {
                    "type": "string",
                    "description": "Rationale for create/update/delete operations"
                }
            },
            "required": ["action"]
        }
    
    def execute(
        self,
        action: str,
        aspect: str = "all",
        entries: Optional[List[Union[str, Dict[str, Any]]]] = None,
        match_criteria: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        entry_id: Optional[str] = None,
        include_epistemic: bool = True,
        rationale: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute CRUD operation.
        
        Args:
            action: Action to perform (query, create, update, delete, list, get_epistemic)
            aspect: Which aspect to operate on
            entries: Entries for create/update operations
            match_criteria: Criteria for matching entries
            filters: Filters for query/list operations
            entry_id: Entry identifier for get_epistemic
            include_epistemic: Whether to include epistemic context
            rationale: Rationale for the operation
            
        Returns:
            Dictionary with operation result
        """
        try:
            if action == "query":
                return self._query(aspect, filters, include_epistemic)
            elif action == "create":
                return self._create(aspect, entries or [], rationale)
            elif action == "update":
                return self._update(aspect, entries or [], match_criteria, rationale)
            elif action == "delete":
                return self._delete(aspect, match_criteria, rationale)
            elif action == "list":
                return self._list(aspect, filters, include_epistemic)
            elif action == "get_epistemic":
                return self._get_epistemic_context(entry_id, aspect)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            logger.error(f"Error in self-model CRUD operation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _query(
        self,
        aspect: str,
        filters: Optional[Dict[str, Any]],
        include_epistemic: bool
    ) -> Dict[str, Any]:
        """Query self-model aspects."""
        result = {"success": True, "action": "query", "aspect": aspect}
        
        if aspect == "all":
            result["self_model"] = self.self_model.to_dict()
            result["summary"] = self.self_model.get_summary()
        elif aspect == "capabilities":
            result["capabilities"] = self.self_model.capabilities
        elif aspect == "knowledge_boundaries":
            result["knowledge_boundaries"] = self.self_model.knowledge_boundaries
        elif aspect == "constraints":
            result["constraints"] = self.self_model.constraints
        else:
            return {"success": False, "error": f"Unknown aspect: {aspect}"}
        
        # Apply filters if provided
        if filters:
            result = self._apply_filters(result, filters)
        
        # Add epistemic context if requested
        if include_epistemic and self.epistemic_engine:
            epistemic_context = self._get_epistemic_context_for_aspect(aspect)
            result["epistemic_context"] = epistemic_context
        
        return result
    
    def _create(
        self,
        aspect: str,
        entries: List[Union[str, Dict[str, Any]]],
        rationale: Optional[str]
    ) -> Dict[str, Any]:
        """Create new entries in specified aspect."""
        if not entries:
            return {"success": False, "error": "No entries provided"}
        
        # Prepare updates dict
        updates: Dict[str, Any] = {}
        
        if aspect == "capabilities":
            current_caps = [cap.get("text", str(cap)) for cap in self.self_model.capabilities]
            new_caps = []
            for entry in entries:
                if isinstance(entry, str):
                    if entry not in current_caps:
                        new_caps.append(entry)
                elif isinstance(entry, dict):
                    text = entry.get("text", str(entry))
                    if text not in current_caps:
                        new_caps.append(entry.get("text", text))
            if new_caps:
                updates["capabilities"] = new_caps
        elif aspect == "knowledge_boundaries":
            updates["knowledge_boundaries"] = {}
            for entry in entries:
                if isinstance(entry, dict):
                    for key, value in entry.items():
                        if key not in self.self_model.knowledge_boundaries:
                            updates["knowledge_boundaries"][key] = value
        elif aspect == "constraints":
            updates["constraints"] = {}
            for entry in entries:
                if isinstance(entry, dict):
                    for key, value in entry.items():
                        if key not in self.self_model.constraints:
                            updates["constraints"][key] = value
        else:
            return {"success": False, "error": f"Cannot create entries for aspect: {aspect}"}
        
        if not updates:
            return {"success": True, "message": "No new entries to create (all already exist)"}
        
        # Apply updates using updater
        from ..self_model.updater import SelfModelUpdater
        updater = SelfModelUpdater()
        updated_model = updater.apply_updates(self.self_model, updates)
        
        # Update metadata
        updated_model.metadata["version"] = self.self_model.metadata.get("version", 1) + 1
        updated_model.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
        updated_model.metadata["update_reason"] = "manual_create"
        if rationale:
            updated_model.metadata["update_rationale"] = rationale
        
        # Save and update local reference with error handling
        try:
            logger.info(f"Persisting create operation for {aspect} to self-model database")
            self.storage.save(updated_model)
            self.self_model = updated_model
            logger.debug(
                f"Successfully persisted create operation: version {updated_model.metadata.get('version')}"
            )
        except Exception as e:
            logger.error(
                f"Failed to persist create operation for {aspect}: {e}",
                exc_info=True
            )
            raise
        
        return {
            "success": True,
            "action": "create",
            "aspect": aspect,
            "entries_created": len(updates.get(aspect, updates.get(list(updates.keys())[0], []))),
            "version": updated_model.metadata.get("version"),
            "rationale": rationale
        }
    
    def _update(
        self,
        aspect: str,
        entries: List[Union[str, Dict[str, Any]]],
        match_criteria: Optional[Dict[str, Any]],
        rationale: Optional[str]
    ) -> Dict[str, Any]:
        """Update existing entries."""
        if not entries:
            return {"success": False, "error": "No entries provided for update"}
        
        updates: Dict[str, Any] = {}
        
        if aspect == "capabilities":
            # Update capabilities by matching text
            current_caps = {cap.get("text", str(cap)): cap for cap in self.self_model.capabilities}
            updated_caps = []
            for entry in entries:
                if isinstance(entry, str):
                    if entry in current_caps:
                        updated_caps.append(entry)
                elif isinstance(entry, dict):
                    text = entry.get("text", str(entry))
                    if text in current_caps:
                        updated_caps.append(entry.get("text", text))
            if updated_caps:
                updates["capabilities"] = updated_caps
        elif aspect == "knowledge_boundaries":
            updates["knowledge_boundaries"] = {}
            for entry in entries:
                if isinstance(entry, dict):
                    for key, value in entry.items():
                        if key in self.self_model.knowledge_boundaries:
                            updates["knowledge_boundaries"][key] = value
        elif aspect == "constraints":
            updates["constraints"] = {}
            for entry in entries:
                if isinstance(entry, dict):
                    for key, value in entry.items():
                        if key in self.self_model.constraints:
                            updates["constraints"][key] = value
        else:
            return {"success": False, "error": f"Cannot update entries for aspect: {aspect}"}
        
        if not updates:
            return {"success": False, "error": "No matching entries found to update"}
        
        # Apply updates
        from ..self_model.updater import SelfModelUpdater
        updater = SelfModelUpdater()
        updated_model = updater.apply_updates(self.self_model, updates)
        
        # Update metadata
        updated_model.metadata["version"] = self.self_model.metadata.get("version", 1) + 1
        updated_model.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
        updated_model.metadata["update_reason"] = "manual_update"
        if rationale:
            updated_model.metadata["update_rationale"] = rationale
        
        # Save and update local reference with error handling
        try:
            logger.info(f"Persisting update operation for {aspect} to self-model database")
            self.storage.save(updated_model)
            self.self_model = updated_model
            logger.debug(
                f"Successfully persisted update operation: version {updated_model.metadata.get('version')}"
            )
        except Exception as e:
            logger.error(
                f"Failed to persist update operation for {aspect}: {e}",
                exc_info=True
            )
            raise
        
        return {
            "success": True,
            "action": "update",
            "aspect": aspect,
            "entries_updated": len(updates.get(aspect, updates.get(list(updates.keys())[0], []))),
            "version": updated_model.metadata.get("version"),
            "rationale": rationale
        }
    
    def _delete(
        self,
        aspect: str,
        match_criteria: Optional[Dict[str, Any]],
        rationale: Optional[str]
    ) -> Dict[str, Any]:
        """Delete entries matching criteria."""
        if not match_criteria:
            return {"success": False, "error": "Match criteria required for delete operation"}
        
        updates: Dict[str, Any] = {}
        deleted_count = 0
        
        if aspect == "capabilities":
            text_match = match_criteria.get("text")
            if text_match:
                current_caps = [cap for cap in self.self_model.capabilities 
                               if cap.get("text", str(cap)) != text_match]
                deleted_count = len(self.self_model.capabilities) - len(current_caps)
                if deleted_count > 0:
                    updates["capabilities"] = [cap.get("text", str(cap)) for cap in current_caps]
        elif aspect == "knowledge_boundaries":
            key_match = match_criteria.get("key")
            if key_match:
                if key_match in self.self_model.knowledge_boundaries:
                    # Remove by not including it in updates (merge would exclude it)
                    updated_kb = {k: v for k, v in self.self_model.knowledge_boundaries.items() 
                                 if k != key_match}
                    updates["knowledge_boundaries"] = updated_kb
                    deleted_count = 1
        elif aspect == "constraints":
            key_match = match_criteria.get("key")
            if key_match:
                if key_match in self.self_model.constraints:
                    updated_constraints = {k: v for k, v in self.self_model.constraints.items() 
                                          if k != key_match}
                    updates["constraints"] = updated_constraints
                    deleted_count = 1
        else:
            return {"success": False, "error": f"Cannot delete entries for aspect: {aspect}"}
        
        if deleted_count == 0:
            return {"success": False, "error": "No matching entries found to delete"}
        
        # Create updated model by reconstructing with remaining entries
        from ..self_model.model import SelfModel
        if aspect == "capabilities":
            updated_model = SelfModel(
                capabilities=updates.get("capabilities", []),
                knowledge_boundaries=self.self_model.knowledge_boundaries,
                constraints=self.self_model.constraints,
                metadata=self.self_model.metadata.copy(),
                epistemic_layer=self.self_model.epistemic_layer
            )
        elif aspect == "knowledge_boundaries":
            updated_model = SelfModel(
                capabilities=self.self_model.capabilities,
                knowledge_boundaries=updates.get("knowledge_boundaries", {}),
                constraints=self.self_model.constraints,
                metadata=self.self_model.metadata.copy(),
                epistemic_layer=self.self_model.epistemic_layer
            )
        else:  # constraints
            updated_model = SelfModel(
                capabilities=self.self_model.capabilities,
                knowledge_boundaries=self.self_model.knowledge_boundaries,
                constraints=updates.get("constraints", {}),
                metadata=self.self_model.metadata.copy(),
                epistemic_layer=self.self_model.epistemic_layer
            )
        
        # Update metadata
        updated_model.metadata["version"] = self.self_model.metadata.get("version", 1) + 1
        updated_model.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
        updated_model.metadata["update_reason"] = "manual_delete"
        if rationale:
            updated_model.metadata["update_rationale"] = rationale
        
        # Save and update local reference with error handling
        try:
            logger.info(f"Persisting delete operation for {aspect} to self-model database")
            self.storage.save(updated_model)
            self.self_model = updated_model
            logger.debug(
                f"Successfully persisted delete operation: version {updated_model.metadata.get('version')}"
            )
        except Exception as e:
            logger.error(
                f"Failed to persist delete operation for {aspect}: {e}",
                exc_info=True
            )
            raise
        
        return {
            "success": True,
            "action": "delete",
            "aspect": aspect,
            "entries_deleted": deleted_count,
            "version": updated_model.metadata.get("version"),
            "rationale": rationale
        }
    
    def _list(
        self,
        aspect: str,
        filters: Optional[Dict[str, Any]],
        include_epistemic: bool
    ) -> Dict[str, Any]:
        """List entries with optional filtering."""
        result = {"success": True, "action": "list", "aspect": aspect}
        
        if aspect == "capabilities":
            entries = self.self_model.capabilities
        elif aspect == "knowledge_boundaries":
            entries = list(self.self_model.knowledge_boundaries.items())
        elif aspect == "constraints":
            entries = list(self.self_model.constraints.items())
        elif aspect == "behaviors":
            # Behaviors are stored in metadata
            entries = self.self_model.metadata.get("behaviors", [])
        elif aspect == "metadata":
            entries = list(self.self_model.metadata.items())
        else:
            return {"success": False, "error": f"Unknown aspect: {aspect}"}
        
        # Apply filters
        if filters:
            entries = self._filter_entries(entries, aspect, filters)
        
        result["entries"] = entries
        result["count"] = len(entries)
        
        # Add epistemic context if requested
        if include_epistemic and self.epistemic_engine:
            epistemic_context = self._get_epistemic_context_for_aspect(aspect)
            result["epistemic_context"] = epistemic_context
        
        return result
    
    def _get_epistemic_context(
        self,
        entry_id: Optional[str],
        aspect: str
    ) -> Dict[str, Any]:
        """Get epistemic context for a specific entry."""
        if not self.epistemic_engine or not self.self_model.epistemic_layer:
            return {
                "success": False,
                "error": "Epistemic engine or layer not available"
            }
        
        if not entry_id:
            return {"success": False, "error": "entry_id required"}
        
        try:
            from ..self_model.epistemic.ids import (
                generate_capability_id,
                generate_constraint_id,
                generate_knowledge_boundary_id
            )
            
            # Generate knowledge ID based on aspect and entry_id
            if aspect == "capabilities":
                kid = generate_capability_id(entry_id)
            elif aspect == "knowledge_boundaries":
                # For knowledge boundaries, entry_id is the key
                # Need to get value from self-model to generate proper ID
                if entry_id in self.self_model.knowledge_boundaries:
                    value = self.self_model.knowledge_boundaries[entry_id].get("value", str(self.self_model.knowledge_boundaries[entry_id]))
                    kid = generate_knowledge_boundary_id(entry_id, value)
                else:
                    return {"success": False, "error": f"Entry '{entry_id}' not found in knowledge_boundaries"}
            elif aspect == "constraints":
                # For constraints, entry_id is the key
                if entry_id in self.self_model.constraints:
                    value = self.self_model.constraints[entry_id].get("value", str(self.self_model.constraints[entry_id]))
                    kid = generate_constraint_id(entry_id, value)
                else:
                    return {"success": False, "error": f"Entry '{entry_id}' not found in constraints"}
            else:
                return {"success": False, "error": f"Unknown aspect: {aspect}"}
            
            context = self.epistemic_engine.get_epistemic_context(kid)
            return {
                "success": True,
                "entry_id": entry_id,
                "aspect": aspect,
                "epistemic_context": context
            }
        except Exception as e:
            logger.error(f"Error getting epistemic context: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_epistemic_context_for_aspect(
        self,
        aspect: str
    ) -> Dict[str, Any]:
        """Get epistemic context for all entries in an aspect."""
        if not self.epistemic_engine or not self.self_model.epistemic_layer:
            return {}
        
        contexts = {}
        try:
            from ..self_model.epistemic.ids import (
                generate_capability_id,
                generate_constraint_id,
                generate_knowledge_boundary_id
            )
            
            if aspect == "capabilities":
                for cap in self.self_model.capabilities:
                    text = cap.get("text", str(cap))
                    kid = generate_capability_id(text)
                    context = self.epistemic_engine.get_epistemic_context(kid)
                    if context:
                        contexts[text] = context
            elif aspect == "knowledge_boundaries":
                for key, value_dict in self.self_model.knowledge_boundaries.items():
                    value = value_dict.get("value", str(value_dict))
                    kid = generate_knowledge_boundary_id(key, value)
                    context = self.epistemic_engine.get_epistemic_context(kid)
                    if context:
                        contexts[key] = context
            elif aspect == "constraints":
                for key, value_dict in self.self_model.constraints.items():
                    value = value_dict.get("value", str(value_dict))
                    kid = generate_constraint_id(key, value)
                    context = self.epistemic_engine.get_epistemic_context(kid)
                    if context:
                        contexts[key] = context
        except Exception as e:
            logger.error(f"Error getting epistemic context for aspect: {e}", exc_info=True)
        
        return contexts
    
    def _apply_filters(
        self,
        result: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply filters to query result."""
        # Simple filtering - can be enhanced
        filtered_result = result.copy()
        
        # Filter by source if provided
        if "source" in filters:
            source_filter = filters["source"]
            if "capabilities" in result:
                filtered_result["capabilities"] = [
                    cap for cap in result["capabilities"]
                    if cap.get("source", {}).get("type") == source_filter
                ]
        
        return filtered_result
    
    def _filter_entries(
        self,
        entries: List[Any],
        aspect: str,
        filters: Dict[str, Any]
    ) -> List[Any]:
        """Filter entries based on criteria."""
        filtered = entries
        
        if aspect == "capabilities":
            if "source" in filters:
                source_filter = filters["source"]
                filtered = [
                    cap for cap in filtered
                    if isinstance(cap, dict) and cap.get("source", {}).get("type") == source_filter
                ]
        elif aspect in ["knowledge_boundaries", "constraints"]:
            # Filters for dict-based aspects
            if "key_pattern" in filters:
                pattern = filters["key_pattern"]
                filtered = [(k, v) for k, v in filtered if pattern.lower() in k.lower()]
        
        return filtered
    
    def get_database_path(self) -> Optional[str]:
        """
        Get the absolute path to the database file for verification.
        
        Returns:
            Absolute path to database file, or None if not available
        """
        if hasattr(self.storage, 'db_path'):
            db_path = self.storage.db_path
            if hasattr(db_path, 'absolute'):
                return str(db_path.absolute())
            return str(db_path)
        return None
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            return f"Error: {result.get('error', 'Unknown error')}"
        
        action = result.get("action", "unknown")
        
        if action == "query":
            if "summary" in result:
                return result["summary"]
            elif "self_model" in result:
                return "Self-model information retrieved successfully."
            else:
                aspect = result.get("aspect", "unknown")
                count = len(result.get(aspect, []))
                return f"Retrieved {count} {aspect} entries."
        
        elif action == "create":
            count = result.get("entries_created", 0)
            aspect = result.get("aspect", "entries")
            version = result.get("version", "unknown")
            return f"Successfully created {count} {aspect} entries. Self-model version: {version}"
        
        elif action == "update":
            count = result.get("entries_updated", 0)
            aspect = result.get("aspect", "entries")
            version = result.get("version", "unknown")
            return f"Successfully updated {count} {aspect} entries. Self-model version: {version}"
        
        elif action == "delete":
            count = result.get("entries_deleted", 0)
            aspect = result.get("aspect", "entries")
            version = result.get("version", "unknown")
            return f"Successfully deleted {count} {aspect} entries. Self-model version: {version}"
        
        elif action == "list":
            count = result.get("count", 0)
            aspect = result.get("aspect", "entries")
            return f"Listed {count} {aspect} entries."
        
        elif action == "get_epistemic":
            context = result.get("epistemic_context", {})
            return f"Epistemic context: {context}"
        
        else:
            return "Operation completed successfully."

