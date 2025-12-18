"""
Core SelfModel data structure representing the LLM's model of itself.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime, timezone
import logging

from .source import Source

if TYPE_CHECKING:
    from .epistemic.layer import EpistemicLayer

logger = logging.getLogger(__name__)


class SelfModel:
    """
    Core data structure representing the LLM's self-model.
    
    Contains information about:
    - Capabilities: What the LLM can do (with source tracking)
    - Knowledge boundaries: What the LLM knows/doesn't know (with source tracking)
    - Constraints: Rules and limitations (with source tracking)
    - Metadata: Version, timestamps, confidence scores
    
    Each item (capability, constraint, knowledge_boundary) has a source
    that tracks where it came from (memory, system_default, user_input, etc.).
    """
    
    def __init__(
        self,
        capabilities: Optional[List[Union[str, Dict[str, Any]]]] = None,
        knowledge_boundaries: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
        constraints: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        epistemic_layer: Optional["EpistemicLayer"] = None,
    ) -> None:
        """
        Initialize a SelfModel instance.
        
        Args:
            capabilities: List of capability descriptions (strings or dicts with "text" and "source")
            knowledge_boundaries: Dictionary describing knowledge boundaries (values can be strings or dicts with "value" and "source")
            constraints: Dictionary of rules and limitations (values can be strings or dicts with "value" and "source")
            metadata: Additional metadata (version, timestamps, etc.)
            epistemic_layer: Optional epistemic layer for second-order self-modeling
        """
        # Normalize capabilities to dict format with sources
        self.capabilities = self._normalize_capabilities(capabilities or [])
        # Normalize knowledge_boundaries to dict format with sources
        self.knowledge_boundaries = self._normalize_dict_with_sources(knowledge_boundaries or {})
        # Normalize constraints to dict format with sources
        self.constraints = self._normalize_dict_with_sources(constraints or {})
        self.epistemic_layer = epistemic_layer  # Optional epistemic layer
        
        # Initialize metadata with defaults
        now = datetime.now(timezone.utc).isoformat()
        self.metadata = metadata or {}
        if "version" not in self.metadata:
            self.metadata["version"] = 1
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = now
        if "last_updated" not in self.metadata:
            self.metadata["last_updated"] = now
        if "confidence" not in self.metadata:
            self.metadata["confidence"] = 0.5  # Default confidence score
    
    @staticmethod
    def _normalize_capabilities(capabilities: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Normalize capabilities to dict format with sources.
        
        Args:
            capabilities: List of strings or dicts
            
        Returns:
            List of dicts with "text" and "source" keys
        """
        normalized = []
        for cap in capabilities:
            if isinstance(cap, str):
                # Convert string to dict with system_default source
                normalized.append({
                    "text": cap,
                    "source": Source.system_default().to_dict()
                })
            elif isinstance(cap, dict):
                # Ensure it has text and source
                if "text" not in cap:
                    # Try to extract from common fields
                    text = cap.get("name") or cap.get("description") or str(cap)
                    cap = {"text": text, **cap}
                if "source" not in cap:
                    cap["source"] = Source.system_default().to_dict()
                elif isinstance(cap["source"], dict):
                    # Ensure source is properly formatted
                    pass
                else:
                    # Convert Source object to dict
                    cap["source"] = cap["source"].to_dict() if hasattr(cap["source"], "to_dict") else Source.system_default().to_dict()
                normalized.append(cap)
            else:
                # Convert other types to string
                normalized.append({
                    "text": str(cap),
                    "source": Source.system_default().to_dict()
                })
        return normalized
    
    @staticmethod
    def _normalize_dict_with_sources(data: Dict[str, Union[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """
        Normalize dict values to dict format with sources.
        
        Args:
            data: Dictionary with string or dict values
            
        Returns:
            Dictionary with dict values containing "value" and "source" keys
        """
        normalized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Convert string to dict with system_default source
                normalized[key] = {
                    "value": value,
                    "source": Source.system_default().to_dict()
                }
            elif isinstance(value, dict):
                # Ensure it has value and source
                if "value" not in value:
                    # Use the dict itself as value, but ensure source exists
                    normalized[key] = {
                        "value": value,
                        "source": value.get("source", Source.system_default().to_dict())
                    }
                else:
                    # Has value, ensure source exists
                    if "source" not in value:
                        value["source"] = Source.system_default().to_dict()
                    elif not isinstance(value["source"], dict):
                        # Convert Source object to dict
                        value["source"] = value["source"].to_dict() if hasattr(value["source"], "to_dict") else Source.system_default().to_dict()
                    normalized[key] = value
            else:
                # Convert other types to string
                normalized[key] = {
                    "value": str(value),
                    "source": Source.system_default().to_dict()
                }
        return normalized
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert SelfModel to dictionary representation.
        
        Returns:
            Dictionary containing all self-model data
        """
        result = {
            "capabilities": self.capabilities,
            "knowledge_boundaries": self.knowledge_boundaries,
            "constraints": self.constraints,
            "metadata": self.metadata,
        }
        
        # Include epistemic layer if present
        if self.epistemic_layer is not None:
            result["epistemic_layer"] = self.epistemic_layer.to_dict()
        else:
            result["epistemic_layer"] = None
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SelfModel:
        """
        Create SelfModel from dictionary representation.
        
        Supports backward compatibility with old format (strings for capabilities,
        simple dicts for constraints/knowledge_boundaries).
        
        Note: This method gracefully ignores unknown fields like "preferences" and
        "behavioral_patterns" that were removed from the model in later versions.
        
        Args:
            data: Dictionary containing self-model data
            
        Returns:
            SelfModel instance
        """
        # Handle epistemic layer (backward compatible - may not exist)
        epistemic_layer = None
        if "epistemic_layer" in data and data["epistemic_layer"] is not None:
            from .epistemic.layer import EpistemicLayer
            # If it's already an EpistemicLayer object, use it directly
            if isinstance(data["epistemic_layer"], EpistemicLayer):
                epistemic_layer = data["epistemic_layer"]
            else:
                # Otherwise, convert from dict
                epistemic_layer = EpistemicLayer.from_dict(data["epistemic_layer"])
        
        # Extract only known fields - unknown fields (like old "preferences" and
        # "behavioral_patterns") are automatically ignored via data.get()
        return cls(
            capabilities=data.get("capabilities", []),
            knowledge_boundaries=data.get("knowledge_boundaries", {}),
            constraints=data.get("constraints", {}),
            metadata=data.get("metadata", {}),
            epistemic_layer=epistemic_layer,
        )
    
    def merge(self, other: SelfModel, strategy: str = "update") -> SelfModel:
        """
        Merge another SelfModel into this one.
        
        Args:
            other: SelfModel to merge
            strategy: Merge strategy - "update" (replace), "append" (add to lists), "merge" (deep merge dicts)
            
        Returns:
            New merged SelfModel instance
        """
        merged = SelfModel()
        
        if strategy == "update":
            # Simple replacement
            merged.capabilities = other.capabilities or self.capabilities
            merged.knowledge_boundaries = other.knowledge_boundaries or self.knowledge_boundaries
            merged.constraints = other.constraints or self.constraints
        elif strategy == "append":
            # Append to lists, merge dicts
            # For capabilities, merge by text (avoid duplicates)
            merged_caps = {cap.get("text", str(cap)): cap for cap in self.capabilities}
            for cap in (other.capabilities or []):
                text = cap.get("text", str(cap))
                merged_caps[text] = cap  # Other takes precedence
            merged.capabilities = list(merged_caps.values())
            
            # Merge knowledge_boundaries and constraints (other takes precedence)
            merged.knowledge_boundaries = {**self.knowledge_boundaries, **(other.knowledge_boundaries or {})}
            merged.constraints = {**self.constraints, **(other.constraints or {})}
        elif strategy == "merge":
            # Deep merge for dicts, append for lists
            # For capabilities, merge by text (avoid duplicates)
            merged_caps = {cap.get("text", str(cap)): cap for cap in self.capabilities}
            for cap in (other.capabilities or []):
                text = cap.get("text", str(cap))
                merged_caps[text] = cap  # Other takes precedence
            merged.capabilities = list(merged_caps.values())
            
            # Deep merge for knowledge_boundaries and constraints
            merged.knowledge_boundaries = self._deep_merge_dicts(self.knowledge_boundaries, other.knowledge_boundaries or {})
            merged.constraints = self._deep_merge_dicts(self.constraints, other.constraints or {})
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")
        
        # Update metadata
        merged.metadata = {
            **self.metadata,
            **(other.metadata or {}),
            "version": max(self.metadata.get("version", 1), other.metadata.get("version", 1)) + 1,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        
        # Merge epistemic layers if both exist
        if self.epistemic_layer is not None or other.epistemic_layer is not None:
            from .epistemic.layer import EpistemicLayer
            if self.epistemic_layer is None:
                merged.epistemic_layer = other.epistemic_layer
            elif other.epistemic_layer is None:
                merged.epistemic_layer = self.epistemic_layer
            else:
                # Both exist - merge them (prefer other's data for conflicts)
                merged.epistemic_layer = EpistemicLayer()
                # Copy self's data
                merged.epistemic_layer.knowledge_sources = self.epistemic_layer.knowledge_sources.copy()
                merged.epistemic_layer.confidence_calibration = self.epistemic_layer.confidence_calibration.copy()
                merged.epistemic_layer.verification_history = {
                    k: v.copy() for k, v in self.epistemic_layer.verification_history.items()
                }
                merged.epistemic_layer.inference_chains = self.epistemic_layer.inference_chains.copy()
                merged.epistemic_layer.temporal_dynamics = self.epistemic_layer.temporal_dynamics.copy()
                # Update with other's data (other takes precedence)
                merged.epistemic_layer.knowledge_sources.update(other.epistemic_layer.knowledge_sources)
                merged.epistemic_layer.confidence_calibration.update(other.epistemic_layer.confidence_calibration)
                for k, v in other.epistemic_layer.verification_history.items():
                    if k in merged.epistemic_layer.verification_history:
                        merged.epistemic_layer.verification_history[k].extend(v)
                    else:
                        merged.epistemic_layer.verification_history[k] = v.copy()
                merged.epistemic_layer.inference_chains.update(other.epistemic_layer.inference_chains)
                merged.epistemic_layer.temporal_dynamics.update(other.epistemic_layer.temporal_dynamics)
        
        return merged
    
    @staticmethod
    def _deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = SelfModel._deep_merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate the self-model structure.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check that capabilities is a list of dicts with text and source
        if not isinstance(self.capabilities, list):
            errors.append("capabilities must be a list")
        else:
            for i, cap in enumerate(self.capabilities):
                if not isinstance(cap, dict):
                    errors.append(f"capabilities[{i}] must be a dictionary")
                else:
                    if "text" not in cap:
                        errors.append(f"capabilities[{i}] must have 'text' field")
                    if "source" not in cap:
                        errors.append(f"capabilities[{i}] must have 'source' field")
        
        # Check that knowledge_boundaries is a dict with dict values
        if not isinstance(self.knowledge_boundaries, dict):
            errors.append("knowledge_boundaries must be a dictionary")
        else:
            for key, value in self.knowledge_boundaries.items():
                if not isinstance(value, dict):
                    errors.append(f"knowledge_boundaries['{key}'] must be a dictionary")
                else:
                    if "value" not in value:
                        errors.append(f"knowledge_boundaries['{key}'] must have 'value' field")
                    if "source" not in value:
                        errors.append(f"knowledge_boundaries['{key}'] must have 'source' field")
        
        # Check that constraints is a dict with dict values
        if not isinstance(self.constraints, dict):
            errors.append("constraints must be a dictionary")
        else:
            for key, value in self.constraints.items():
                if not isinstance(value, dict):
                    errors.append(f"constraints['{key}'] must be a dictionary")
                else:
                    if "value" not in value:
                        errors.append(f"constraints['{key}'] must have 'value' field")
                    if "source" not in value:
                        errors.append(f"constraints['{key}'] must have 'source' field")
        
        # Check metadata structure
        if not isinstance(self.metadata, dict):
            errors.append("metadata must be a dictionary")
        else:
            if "version" not in self.metadata:
                errors.append("metadata must contain 'version'")
            if "last_updated" not in self.metadata:
                errors.append("metadata must contain 'last_updated'")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> str:
        """
        Get a text summary of the self-model for display/LLM consumption.
        
        Returns:
            Formatted string summary
        """
        lines = ["Self-Model Summary:"]
        lines.append(f"Version: {self.metadata.get('version', 'unknown')}")
        lines.append(f"Last Updated: {self.metadata.get('last_updated', 'unknown')}")
        lines.append("")
        
        if self.capabilities:
            lines.append("Capabilities:")
            for cap in self.capabilities:
                text = cap.get("text", str(cap))
                source_info = cap.get("source", {})
                source_type = source_info.get("type", "unknown")
                if source_type == "memory" and "memory_id" in source_info:
                    lines.append(f"  - {text} [from memory {source_info['memory_id']}]")
                else:
                    lines.append(f"  - {text} [from {source_type}]")
            lines.append("")
        
        if self.knowledge_boundaries:
            lines.append("Knowledge Boundaries:")
            for key, value_dict in self.knowledge_boundaries.items():
                value = value_dict.get("value", str(value_dict))
                source_info = value_dict.get("source", {})
                source_type = source_info.get("type", "unknown")
                if source_type == "memory" and "memory_id" in source_info:
                    lines.append(f"  - {key}: {value} [from memory {source_info['memory_id']}]")
                else:
                    lines.append(f"  - {key}: {value} [from {source_type}]")
            lines.append("")
        
        if self.constraints:
            lines.append("Constraints:")
            for key, value_dict in self.constraints.items():
                value = value_dict.get("value", str(value_dict))
                source_info = value_dict.get("source", {})
                source_type = source_info.get("type", "unknown")
                if source_type == "memory" and "memory_id" in source_info:
                    lines.append(f"  - {key}: {value} [from memory {source_info['memory_id']}]")
                else:
                    lines.append(f"  - {key}: {value} [from {source_type}]")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_minimal_summary(self) -> str:
        """
        Get minimal summary: version, last updated, counts only.
        
        Returns:
            Minimal string summary with just version, last updated, and counts
        """
        cap_count = len(self.capabilities)
        kb_count = len(self.knowledge_boundaries)
        const_count = len(self.constraints)
        version = self.metadata.get('version', 'unknown')
        last_updated = self.metadata.get('last_updated', 'unknown')
        return f"Self-Model Summary: Version {version}, last updated {last_updated}. Contains {cap_count} capabilities, {kb_count} knowledge boundaries, {const_count} constraints."
    
    @classmethod
    def create_default(cls) -> SelfModel:
        """
        Create a default minimal self-model.
        
        Returns:
            Default SelfModel instance with epistemic layer initialized by default
        """
        from .epistemic.layer import EpistemicLayer
        from .epistemic.ids import (
            generate_capability_id,
            generate_constraint_id,
            generate_knowledge_boundary_id,
        )
        from .epistemic.models import SourceType, SourceMetadata
        from .epistemic.engine import MetacognitiveEngine
        from datetime import datetime, timezone
        
        # Initialize epistemic layer
        epistemic_layer = EpistemicLayer()
        engine = MetacognitiveEngine(epistemic_layer=epistemic_layer)
        
        # Create default capabilities with sources
        default_source = Source.system_default()
        capabilities = [
            {
                "text": "General conversation and assistance",
                "source": default_source.to_dict()
            },
            {
                "text": "Tool usage (memory, web search, terminal, critic)",
                "source": default_source.to_dict()
            },
            {
                "text": "Code execution and analysis",
                "source": default_source.to_dict()
            },
            {
                "text": "Information retrieval and synthesis",
                "source": default_source.to_dict()
            },
        ]
        
        # Create default knowledge boundaries with sources
        knowledge_boundaries = {
            "training_cutoff": {
                "value": "unknown",
                "source": default_source.to_dict()
            },
            "real_time_info": {
                "value": "requires web search or tools",
                "source": default_source.to_dict()
            },
        }
        
        # Create default constraints with sources
        constraints = {
            "cannot_execute_arbitrary_code": {
                "value": "limited to whitelisted terminal commands",
                "source": default_source.to_dict()
            },
            "cannot_access_internet_directly": {
                "value": "requires web search tool",
                "source": default_source.to_dict()
            },
        }
        
        # Track capabilities in epistemic layer
        for cap_dict in capabilities:
            capability = cap_dict["text"]
            knowledge_id = generate_capability_id(capability)
            source = SourceMetadata(
                source_type=SourceType.SYSTEM_DEFAULT,
                timestamp=datetime.now(timezone.utc)
            )
            # Use assessed source reliability instead of hardcoded value
            source_reliability = engine.validator.assess_source_reliability(source)
            engine.knowledge_acquisition_workflow(
                knowledge_id=knowledge_id,
                source=source,
                initial_confidence=source_reliability
            )
        
        # Track knowledge boundaries in epistemic layer
        for key, value_dict in knowledge_boundaries.items():
            value = value_dict["value"]
            knowledge_id = generate_knowledge_boundary_id(key, value)
            source = SourceMetadata(
                source_type=SourceType.SYSTEM_DEFAULT,
                timestamp=datetime.now(timezone.utc)
            )
            # Use assessed source reliability instead of hardcoded value
            source_reliability = engine.validator.assess_source_reliability(source)
            engine.knowledge_acquisition_workflow(
                knowledge_id=knowledge_id,
                source=source,
                initial_confidence=source_reliability
            )
        
        # Track constraints in epistemic layer
        for key, value_dict in constraints.items():
            value = value_dict["value"]
            knowledge_id = generate_constraint_id(key, value)
            source = SourceMetadata(
                source_type=SourceType.SYSTEM_DEFAULT,
                timestamp=datetime.now(timezone.utc)
            )
            # Use assessed source reliability instead of hardcoded value
            source_reliability = engine.validator.assess_source_reliability(source)
            engine.knowledge_acquisition_workflow(
                knowledge_id=knowledge_id,
                source=source,
                initial_confidence=source_reliability
            )
        
        return cls(
            capabilities=capabilities,
            knowledge_boundaries=knowledge_boundaries,
            constraints=constraints,
            epistemic_layer=epistemic_layer,
        )

