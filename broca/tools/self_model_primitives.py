"""
Primitive self-model tools.

These wrap the existing `SelfModelCRUDTool` into explicit operations aligned with
the RL/agent action vocabulary:
- SELF_MODEL_GET
- SELF_MODEL_UPDATE
- SELF_MODEL_ARCHIVE
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from .self_model_crud_tool import SelfModelCRUDTool


class SelfModelGetTool:
    def __init__(self, self_model: Any, storage: Any, epistemic_engine: Optional[Any] = None) -> None:
        self._crud = SelfModelCRUDTool(self_model=self_model, storage=storage, epistemic_engine=epistemic_engine)

    @property
    def name(self) -> str:
        return "SELF_MODEL_GET"

    @property
    def description(self) -> str:
        return "Read/query the current self-model (capabilities, constraints, knowledge boundaries)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "aspect": {
                    "type": "string",
                    "enum": ["all", "capabilities", "knowledge_boundaries", "constraints", "metadata"],
                    "default": "all",
                },
                "filters": {"type": "object", "additionalProperties": True},
                "include_epistemic": {"type": "boolean", "default": True},
            },
            "required": [],
        }

    def execute(self, aspect: str = "all", filters: Optional[Dict[str, Any]] = None, include_epistemic: bool = True, **_: Any) -> Dict[str, Any]:
        return self._crud.execute(action="query", aspect=aspect, filters=filters, include_epistemic=include_epistemic)

    def format_result(self, result: Dict[str, Any]) -> str:
        return self._crud.format_result(result)


class SelfModelUpdateTool:
    def __init__(self, self_model: Any, storage: Any, epistemic_engine: Optional[Any] = None) -> None:
        self._crud = SelfModelCRUDTool(self_model=self_model, storage=storage, epistemic_engine=epistemic_engine)

    @property
    def name(self) -> str:
        return "SELF_MODEL_UPDATE"

    @property
    def description(self) -> str:
        return (
            "Update the current self-model. This tool mutates the self-model and persists it via storage. "
            "Use rationale to explain why the update is justified."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["create", "update", "delete"], "default": "update"},
                "aspect": {
                    "type": "string",
                    "enum": ["capabilities", "knowledge_boundaries", "constraints"],
                    "description": "Aspect to modify",
                },
                "entries": {
                    "type": "array",
                    "items": {"type": ["string", "object"]},
                    "description": "Entries to create/update (strings for capabilities, dicts for key/value aspects)",
                },
                "match_criteria": {
                    "type": "object",
                    "description": "Criteria for matching existing entries (for update/delete)",
                    "additionalProperties": True,
                },
                "rationale": {"type": "string", "description": "Rationale for the operation"},
                "include_epistemic": {"type": "boolean", "default": True},
            },
            "required": ["aspect"],
        }

    def execute(
        self,
        aspect: str,
        mode: str = "update",
        entries: Optional[List[Union[str, Dict[str, Any]]]] = None,
        match_criteria: Optional[Dict[str, Any]] = None,
        rationale: Optional[str] = None,
        include_epistemic: bool = True,
        **_: Any,
    ) -> Dict[str, Any]:
        action = mode if mode in ("create", "update", "delete") else "update"
        return self._crud.execute(
            action=action,
            aspect=aspect,
            entries=entries,
            match_criteria=match_criteria,
            include_epistemic=include_epistemic,
            rationale=rationale,
        )

    def format_result(self, result: Dict[str, Any]) -> str:
        return self._crud.format_result(result)


class SelfModelArchiveTool:
    def __init__(self, self_model: Any, storage: Any) -> None:
        self._self_model = self_model
        self._storage = storage

    @property
    def name(self) -> str:
        return "SELF_MODEL_ARCHIVE"

    @property
    def description(self) -> str:
        return (
            "Archive the current self-model by incrementing its version and persisting it. "
            "Use this to create an explicit checkpoint before/after major changes."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why this archive/checkpoint is being created"},
            },
            "required": [],
        }

    def execute(self, reason: Optional[str] = None, **_: Any) -> Dict[str, Any]:
        meta = getattr(self._self_model, "metadata", None)
        if not isinstance(meta, dict):
            return {"success": False, "error": "self_model_missing_metadata"}

        current_version = meta.get("version", 1)
        try:
            next_version = int(current_version) + 1
        except Exception:
            next_version = 2

        meta["version"] = next_version
        meta["archived_at"] = datetime.now(timezone.utc).isoformat()
        if isinstance(reason, str) and reason.strip():
            meta["archived_reason"] = reason.strip()

        self._storage.save(self._self_model)
        return {"success": True, "version": next_version, "message": f"Archived self-model as version {next_version}"}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"SELF_MODEL_ARCHIVE error: {result.get('error', 'unknown')}"
        return str(result.get("message", "Archived self-model"))

