"""
Self-model tools for LLM introspection and manual updates.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from . import Tool
from ..self_model.model import SelfModel

if TYPE_CHECKING:
    from ..self_model.storage import SelfModelSQLiteStorage
    from ..damping.action_gate import ActionGate
    from ..signals.manager import SignalManager

logger = logging.getLogger(__name__)


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
        action_gate: Optional["ActionGate"] = None,
        signal_manager: Optional["SignalManager"] = None,
    ) -> None:
        """
        Initialize the update self-model tool.
        
        Args:
            self_model: SelfModel instance
            storage: Storage instance for self-model
            action_gate: Optional ActionGate for gating self-model updates
            signal_manager: Optional SignalManager for getting trigger signals (dissonance)
        """
        self.self_model = self_model
        self.storage = storage
        self._action_gate = action_gate
        self._signal_manager = signal_manager
        logger.info("Initialized UpdateSelfModelTool")
    
    def set_action_gate(self, action_gate: Optional["ActionGate"]) -> None:
        """Set the action gate for self-model updates."""
        self._action_gate = action_gate
    
    def set_signal_manager(self, signal_manager: Optional["SignalManager"]) -> None:
        """Set the signal manager for getting trigger signals."""
        self._signal_manager = signal_manager
    
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
            # Check action gate if available (for manual updates, we still gate based on frequency/dissonance)
            if self._action_gate and self._signal_manager:
                from datetime import datetime, timezone
                # For manual updates, use a fixed trigger value (1.0 = always allow check, gate will handle cooldown)
                # Or use dissonance level as trigger
                dissonance_level = self._signal_manager.get("dissonance.level", default=1.0)
                if not isinstance(dissonance_level, (int, float)):
                    dissonance_level = float(dissonance_level) if dissonance_level is not None else 1.0
                
                should_update, reason = self._action_gate.should_allow_action(
                    trigger_value=dissonance_level,
                    timestamp=datetime.now(timezone.utc)
                )
                if not should_update:
                    logger.debug(f"Manual self-model update gated: {reason}")
                    return {
                        "success": False,
                        "error": f"Update gated: {reason}. Please try again later.",
                        "gated": True,
                    }
            
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
            
            # Record action in gate
            if self._action_gate:
                self._action_gate.record_action(datetime.now(timezone.utc))
            
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
