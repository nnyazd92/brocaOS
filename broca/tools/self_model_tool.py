"""
Self-model tools for LLM introspection and manual updates.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from . import Tool
from ..self_model.model import SelfModel
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..self_model.storage import SelfModelSQLiteStorage

logger = logging.getLogger(__name__)


class QuerySelfModelTool:
    """
    Tool for querying the current self-model.
    
    Allows the LLM to introspect its self-model to understand its capabilities,
    preferences, knowledge boundaries, constraints, and behavioral patterns.
    """
    
    def __init__(
        self,
        self_model: SelfModel,
        storage: Any,
    ) -> None:
        """
        Initialize the query self-model tool.
        
        Args:
            self_model: SelfModel instance
            storage: Storage instance for self-model
        """
        self.self_model = self_model
        self.storage = storage
        logger.info("Initialized QuerySelfModelTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "query_self_model"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Query your self-model to understand your capabilities, preferences, "
            "knowledge boundaries, constraints, and behavioral patterns. "
            "Use this tool when you need to introspect about what you know about yourself, "
            "or when you need to check your self-model before making claims or taking actions."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "aspect": {
                    "type": "string",
                    "enum": ["all", "capabilities", "preferences", "knowledge_boundaries", "constraints", "behavioral_patterns", "metadata", "epistemic"],
                    "description": "Which aspect of the self-model to query (default: 'all'). Use 'epistemic' to get only epistemic metadata.",
                    "default": "all"
                }
            },
            "required": []
        }
    
    def execute(
        self,
        aspect: str = "all",
    ) -> Dict[str, Any]:
        """
        Execute self-model query.
        
        Args:
            aspect: Which aspect to query
            
        Returns:
            Dictionary with self-model information
        """
        try:
            if aspect == "all":
                result = {
                    "success": True,
                    "self_model": self.self_model.to_dict(),
                    "summary": self.self_model.get_summary(),
                }
                
                # Add epistemic context if available
                if self.self_model.epistemic_layer:
                    try:
                        from broca.self_model.epistemic.ids import generate_capability_id
                        from broca.self_model.epistemic.engine import MetacognitiveEngine
                        
                        # Create epistemic engine if not available
                        epistemic_engine = MetacognitiveEngine(epistemic_layer=self.self_model.epistemic_layer)
                        
                        # Get epistemic context for capabilities
                        epistemic_context = {}
                        for capability in self.self_model.capabilities:
                            # Extract text from capability dict (capabilities are stored as dicts with "text" and "source")
                            capability_text = capability.get("text", str(capability)) if isinstance(capability, dict) else str(capability)
                            kid = generate_capability_id(capability_text)
                            context = epistemic_engine.get_epistemic_context(kid)
                            if context:
                                epistemic_context[kid] = context
                        
                        result["epistemic_context"] = {
                            "capabilities": epistemic_context,
                            "has_epistemic_layer": True
                        }
                    except Exception as e:
                        logger.warning(f"Error getting epistemic context: {e}", exc_info=True)
                        result["epistemic_context"] = {"has_epistemic_layer": True, "error": str(e)}
                else:
                    result["epistemic_context"] = {"has_epistemic_layer": False}
                
                return result
            elif aspect == "capabilities":
                return {
                    "success": True,
                    "aspect": "capabilities",
                    "capabilities": self.self_model.capabilities,
                }
            elif aspect == "preferences":
                # Note: preferences attribute was removed from SelfModel - return empty dict for backward compatibility
                return {
                    "success": True,
                    "aspect": "preferences",
                    "preferences": {},
                }
            elif aspect == "knowledge_boundaries":
                return {
                    "success": True,
                    "aspect": "knowledge_boundaries",
                    "knowledge_boundaries": self.self_model.knowledge_boundaries,
                }
            elif aspect == "constraints":
                return {
                    "success": True,
                    "aspect": "constraints",
                    "constraints": self.self_model.constraints,
                }
            elif aspect == "behavioral_patterns":
                # Note: behavioral_patterns attribute was removed from SelfModel - return empty list for backward compatibility
                return {
                    "success": True,
                    "aspect": "behavioral_patterns",
                    "behavioral_patterns": [],
                }
            elif aspect == "metadata":
                return {
                    "success": True,
                    "aspect": "metadata",
                    "metadata": self.self_model.metadata,
                }
            elif aspect == "epistemic":
                # Return only epistemic metadata
                if not self.self_model.epistemic_layer:
                    # Attempt to lazy-load epistemic layer from storage if available
                    try:
                        if hasattr(self.storage, 'load'):
                            loaded = self.storage.load()
                            if getattr(loaded, 'epistemic_layer', None):
                                self.self_model.epistemic_layer = loaded.epistemic_layer
                    except Exception:
                        pass

                    return {
                        "success": True,
                        "aspect": "epistemic",
                        "epistemic_layer": None,
                        "message": "No epistemic layer available"
                    }
                
                try:
                    from broca.self_model.epistemic.engine import MetacognitiveEngine
                    epistemic_engine = MetacognitiveEngine(epistemic_layer=self.self_model.epistemic_layer)
                    
                    # Get epistemic context for all knowledge items
                    all_contexts = {}
                    for kid in self.self_model.epistemic_layer.knowledge_sources.keys():
                        context = epistemic_engine.get_epistemic_context(kid)
                        if context:
                            all_contexts[kid] = context
                    
                    return {
                        "success": True,
                        "aspect": "epistemic",
                        "epistemic_layer": self.self_model.epistemic_layer.to_dict(),
                        "knowledge_contexts": all_contexts,
                        "total_knowledge_items": len(all_contexts)
                    }
                except Exception as e:
                    logger.error(f"Error getting epistemic metadata: {e}", exc_info=True)
                    return {
                        "success": False,
                        "error": str(e),
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unknown aspect: {aspect}",
                }
                
        except Exception as e:
            logger.error(f"Error querying self-model: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format query result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            return f"Error querying self-model: {result.get('error', 'Unknown error')}"
        
        if "summary" in result:
            return result["summary"]
        
        aspect = result.get("aspect", "unknown")
        if aspect == "capabilities":
            lines = ["Capabilities:"]
            for cap in result.get("capabilities", []):
                # Extract text from capability dict (capabilities are stored as dicts with "text" and "source")
                cap_text = cap.get("text", str(cap)) if isinstance(cap, dict) else str(cap)
                lines.append(f"  - {cap_text}")
            return "\n".join(lines)
        elif aspect == "preferences":
            lines = ["Preferences:"]
            for key, value in result.get("preferences", {}).items():
                lines.append(f"  - {key}: {value}")
            return "\n".join(lines)
        elif aspect == "knowledge_boundaries":
            lines = ["Knowledge Boundaries:"]
            for key, value in result.get("knowledge_boundaries", {}).items():
                lines.append(f"  - {key}: {value}")
            return "\n".join(lines)
        elif aspect == "constraints":
            lines = ["Constraints:"]
            for key, value in result.get("constraints", {}).items():
                lines.append(f"  - {key}: {value}")
            return "\n".join(lines)
        elif aspect == "behavioral_patterns":
            lines = ["Behavioral Patterns:"]
            for i, pattern in enumerate(result.get("behavioral_patterns", []), 1):
                if isinstance(pattern, dict):
                    lines.append(f"  {i}. {pattern}")
                else:
                    lines.append(f"  {i}. {pattern}")
            return "\n".join(lines)
        elif aspect == "metadata":
            lines = ["Metadata:"]
            for key, value in result.get("metadata", {}).items():
                lines.append(f"  - {key}: {value}")
            return "\n".join(lines)
        else:
            return "Self-model information retrieved successfully."


class UpdateSelfModelTool:
    """
    Tool for manually updating the self-model.
    
    Allows the LLM to update specific aspects of its self-model based on
    new information or insights.
    """
    
    def __init__(
        self,
        self_model: SelfModel,
        storage: Any,
    ) -> None:
        """
        Initialize the update self-model tool.
        
        Args:
            self_model: SelfModel instance
            storage: Storage instance for self-model
        """
        self.self_model = self_model
        self.storage = storage
        logger.info("Initialized UpdateSelfModelTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "update_self_model"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Update your self-model to reflect new information, insights, or changes. "
            "Use this tool when you learn something new about yourself, discover a new "
            "capability, or need to update your preferences, knowledge boundaries, or constraints. "
            "Only update aspects that genuinely need to change based on new information."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "updates": {
                    "type": "object",
                    "description": "Dictionary of updates to apply",
                    "properties": {
                        "capabilities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "New or updated capabilities to add"
                        },
                        "preferences": {
                            "type": "object",
                            "description": "New or updated preferences",
                            "additionalProperties": True
                        },
                        "knowledge_boundaries": {
                            "type": "object",
                            "description": "New or updated knowledge boundaries",
                            "additionalProperties": True
                        },
                        "constraints": {
                            "type": "object",
                            "description": "New or updated constraints",
                            "additionalProperties": True
                        },
                        "behavioral_patterns": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "New behavioral patterns to add"
                        }
                    }
                },
                "rationale": {
                    "type": "string",
                    "description": "Explanation of why these updates are needed"
                }
            },
            "required": ["updates"]
        }
    
    def execute(
        self,
        updates: Dict[str, Any],
        rationale: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute self-model update.
        
        Args:
            updates: Dictionary of updates to apply
            rationale: Optional explanation for the updates
            
        Returns:
            Dictionary with update result
        """
        try:
            # Create updated model using updater
            from ..self_model.updater import SelfModelUpdater
            updater = SelfModelUpdater()
            updated_model = updater.apply_updates(self.self_model, updates)
            
            # Update metadata
            from datetime import datetime, timezone
            updated_model.metadata["version"] = self.self_model.metadata.get("version", 1) + 1
            updated_model.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
            updated_model.metadata["update_reason"] = "manual_update"
            if rationale:
                updated_model.metadata["update_rationale"] = rationale
            
            # Save updated model
            self.storage.save(updated_model)
            # Update local reference
            self.self_model = updated_model
            
            return {
                "success": True,
                "version": updated_model.metadata.get("version"),
                "updated_aspects": list(updates.keys()),
                "rationale": rationale,
            }
            
        except Exception as e:
            logger.error(f"Error updating self-model: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format update result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            return f"Error updating self-model: {result.get('error', 'Unknown error')}"
        
        lines = [f"Self-model updated successfully to version {result.get('version', 'unknown')}."]
        lines.append(f"Updated aspects: {', '.join(result.get('updated_aspects', []))}")
        if result.get("rationale"):
            lines.append(f"Rationale: {result['rationale']}")
        
        return "\n".join(lines)

