"""
Self-model updater that generates and applies updates when inconsistencies are detected.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List, TYPE_CHECKING
import logging
from datetime import datetime, timezone

from .model import SelfModel
from .consistency import ConsistencyResult
from .source import Source
from ..llm import create_llm_client, LLMClient

logger = logging.getLogger(__name__)

# Type checking for internal sensing
if TYPE_CHECKING:
    from ..internal_sensing.framework import InternalSensingFramework


class SelfModelUpdater:
    """
    Updates the self-model when inconsistencies are detected.
    
    Uses LLM to generate self-model updates based on consistency violations,
    then applies them recursively (may trigger re-checking).
    """
    
    _DEFAULT_UPDATE_PROMPT = """You are a self-model updater. Your role is to update the LLM's self-model to resolve consistency violations.

Current Self-Model:
{self_model_summary}

Consistency Violations:
{violations_summary}

Original Response that caused violations:
{response}

Your task is to propose updates to the self-model that would resolve these violations. The updates should:
1. Address the specific violations identified
2. Maintain consistency with the rest of the self-model
3. Be specific and actionable

Respond with a JSON object containing the proposed updates:
{{
  "capabilities": ["list of new or updated capabilities as strings"] or null to keep unchanged,
  "knowledge_boundaries": {{"key": "value as string"}} or null to keep unchanged,
  "constraints": {{"key": "value as string"}} or null to keep unchanged,
  "rationale": "explanation of why these updates resolve the violations"
}}

Only include fields that need to be updated. Use null for fields that should remain unchanged.
Note: Sources will be automatically assigned (llm_inference for updates from this process)."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        update_prompt_template: Optional[str] = None,
    ) -> None:
        """
        Initialize self-model updater.
        
        Args:
            llm_client: Optional LLMClient instance (defaults to new instance via factory)
            update_prompt_template: Optional custom prompt template for updates
        """
        self._llm = llm_client or create_llm_client()
        self._update_prompt_template = update_prompt_template or self._DEFAULT_UPDATE_PROMPT
        logger.info("Initialized SelfModelUpdater")
    
    def update_from_violations(
        self,
        consistency_result: ConsistencyResult,
        current_model: SelfModel,
        original_response: str,
    ) -> SelfModel:
        """
        Update self-model based on consistency violations.
        
        Args:
            consistency_result: ConsistencyResult with violations
            current_model: Current self-model
            original_response: The response that caused violations
            
        Returns:
            Updated SelfModel instance
        """
        try:
            # If no violations or suggested updates, return current model
            if consistency_result.is_consistent or not consistency_result.violations:
                logger.debug("No violations to update from")
                return current_model
            
            # Use suggested updates if available, otherwise generate them
            if consistency_result.suggested_updates:
                updates = consistency_result.suggested_updates
                logger.info("Using suggested updates from consistency checker")
            else:
                # Generate updates using LLM
                updates = self._generate_updates(
                    consistency_result,
                    current_model,
                    original_response,
                )
            
            if not updates:
                logger.warning("No updates generated")
                return current_model
            
            # Apply updates to create new model (source will be llm_inference by default)
            updated_model = self.apply_updates(current_model, updates)
            
            # Update metadata
            updated_model.metadata["version"] = current_model.metadata.get("version", 1) + 1
            updated_model.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
            updated_model.metadata["update_reason"] = "consistency_violations"
            
            logger.info(f"Updated self-model to version {updated_model.metadata['version']}")
            return updated_model
            
        except Exception as e:
            logger.error(f"Error updating self-model: {e}", exc_info=True)
            # Return current model on error
            return current_model
    
    def _generate_updates(
        self,
        consistency_result: ConsistencyResult,
        current_model: SelfModel,
        original_response: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate self-model updates using LLM.
        
        Args:
            consistency_result: ConsistencyResult with violations
            current_model: Current self-model
            original_response: The response that caused violations
            
        Returns:
            Dictionary of proposed updates or None
        """
        try:
            # Format violations summary
            violations_lines = []
            for i, violation in enumerate(consistency_result.violations, 1):
                violations_lines.append(
                    f"{i}. Type: {violation.get('type', 'unknown')}, "
                    f"Severity: {violation.get('severity', 0.0):.2f}\n"
                    f"   Description: {violation.get('description', '')}\n"
                    f"   Evidence: {violation.get('evidence', '')}"
                )
            violations_summary = "\n".join(violations_lines) if violations_lines else "No violations"
            
            # Build prompt
            prompt = self._update_prompt_template.format(
                self_model_summary=current_model.get_summary(),
                violations_summary=violations_summary,
                response=original_response[:500],  # Truncate for brevity
            )
            
            # Call LLM
            messages = [
                {"role": "system", "content": "You are a self-model updater. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            logger.debug("Calling LLM to generate self-model updates")
            llm_response = self._llm.chat(messages)
            response_content = self._llm.extract_assistant_content(llm_response)
            
            # Parse JSON response
            updates = self._parse_updates(response_content)
            
            return updates
            
        except Exception as e:
            logger.error(f"Error generating updates: {e}", exc_info=True)
            return None
    
    def _parse_updates(self, response_content: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response into update dictionary.
        
        Args:
            response_content: Raw LLM response content
            
        Returns:
            Dictionary of updates or None
        """
        import json
        
        try:
            # Try to extract JSON from response (may be wrapped in markdown code blocks)
            response_content = response_content.strip()
            if response_content.startswith("```"):
                # Extract JSON from code block
                lines = response_content.split("\n")
                json_start = None
                json_end = None
                for i, line in enumerate(lines):
                    if line.strip().startswith("```json") or line.strip().startswith("```"):
                        json_start = i + 1
                        break
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip().startswith("```"):
                        json_end = i
                        break
                if json_start is not None and json_end is not None:
                    response_content = "\n".join(lines[json_start:json_end])
            
            data = json.loads(response_content)
            
            # Filter out null values and empty updates
            updates = {k: v for k, v in data.items() if v is not None and k != "rationale"}
            
            if not updates:
                logger.debug("No valid updates in LLM response")
                return None
            
            logger.debug(f"Parsed updates: {list(updates.keys())}")
            return updates
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse update response as JSON: {e}")
            logger.debug(f"Response content: {response_content[:500]}")
            return None
    
    def _normalize_capabilities(self, capabilities: Any, source: Optional[Source] = None) -> List[Dict[str, Any]]:
        """
        Normalize capabilities to a list of dicts with text and source.
        
        Handles cases where capabilities come as:
        - List of strings (expected from LLM)
        - List of dicts (already in correct format)
        - Mixed types
        
        Args:
            capabilities: Capabilities in various formats
            source: Source to assign to new capabilities (defaults to llm_inference)
            
        Returns:
            List of normalized capability dicts with "text" and "source"
        """
        import json
        
        if not isinstance(capabilities, list):
            logger.warning(f"Capabilities must be a list, got {type(capabilities)}")
            return []
        
        if source is None:
            source = Source.llm_inference()
        
        normalized = []
        for cap in capabilities:
            if isinstance(cap, str):
                # String - convert to dict with source
                normalized.append({
                    "text": cap,
                    "source": source.to_dict()
                })
            elif isinstance(cap, dict):
                # Already a dict - ensure it has text and source
                if "text" not in cap:
                    # Try to extract text from common fields
                    text = cap.get("name") or cap.get("description") or str(cap)
                    cap = {"text": text, **cap}
                if "source" not in cap:
                    cap["source"] = source.to_dict()
                elif isinstance(cap["source"], dict):
                    # Source already a dict, keep it
                    pass
                else:
                    # Source is an object, convert to dict
                    cap["source"] = cap["source"].to_dict() if hasattr(cap["source"], "to_dict") else source.to_dict()
                normalized.append(cap)
            else:
                # Try to convert to string
                try:
                    normalized.append({
                        "text": str(cap),
                        "source": source.to_dict()
                    })
                except Exception as e:
                    logger.warning(f"Could not convert capability to string: {e}")
                    continue
        
        return normalized
    
    def _normalize_to_dict(self, value: Any) -> Dict[str, Any]:
        """
        Normalize a value to a dictionary.
        
        Handles cases where dict fields come as:
        - Dict (expected) - use as-is
        - List of key-value pair dicts: [{"key": "k1", "value": "v1"}]
        - List of tuples: [("k1", "v1"), ("k2", "v2")]
        - List of name-value dicts: [{"name": "k1", "value": "v1"}]
        - List of strings with "key: value" format: ["key1: value1"]
        - List of single-item dicts: [{"k1": "v1"}, {"k2": "v2"}]
        
        Args:
            value: Value in various formats that should be a dict
            
        Returns:
            Normalized dictionary, or empty dict if normalization fails
        """
        # If already a dict, return as-is
        if isinstance(value, dict):
            return value
        
        # If not a list, can't normalize
        if not isinstance(value, list):
            logger.warning(f"Cannot normalize to dict: expected dict or list, got {type(value)}")
            return {}
        
        # Empty list returns empty dict
        if len(value) == 0:
            return {}
        
        result = {}
        
        # Try different list formats
        for item in value:
            if isinstance(item, dict):
                # Try format: {"key": "k", "value": "v"}
                if "key" in item and "value" in item:
                    result[item["key"]] = item["value"]
                    continue
                
                # Try format: {"name": "k", "value": "v"}
                if "name" in item and "value" in item:
                    result[item["name"]] = item["value"]
                    continue
                
                # Try format: single-item dict {"k": "v"}
                if len(item) == 1:
                    key, val = next(iter(item.items()))
                    result[key] = val
                    continue
                
                # If dict has multiple items, try to extract key/value
                # Look for common key names
                for possible_key in ["key", "name", "id", "field"]:
                    if possible_key in item:
                        key = item[possible_key]
                        # Look for value
                        for possible_val in ["value", "val", "data", "content"]:
                            if possible_val in item:
                                result[str(key)] = item[possible_val]
                                break
                        else:
                            # No value field found, use the key as both key and value
                            result[str(key)] = item
                        break
                else:
                    # Couldn't extract key-value, skip this item
                    logger.debug(f"Could not extract key-value from dict item: {item}")
                    continue
            
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                # Try format: tuple/list ("k", "v") or ["k", "v"]
                key, val = item[0], item[1]
                result[str(key)] = val
                continue
            
            elif isinstance(item, str):
                # Try format: "key: value" string
                if ":" in item:
                    parts = item.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip()
                        if key:
                            result[key] = val
                            continue
                
                # If no colon, treat entire string as key with empty value
                result[item] = ""
                continue
            
            else:
                # Unknown format, try to convert to string key
                try:
                    result[str(item)] = item
                except Exception:
                    logger.debug(f"Could not normalize item to dict entry: {item}")
                    continue
        
        return result
    
    def _validate_updates(self, updates: Dict[str, Any], source: Optional[Source] = None) -> Dict[str, Any]:
        """
        Validate and normalize update dictionary.
        
        Ensures all update fields have correct types:
        - capabilities: List[Dict[str, Any]] with "text" and "source" (normalized from various formats)
        - knowledge_boundaries: Dict[str, Dict[str, Any]] with "value" and "source"
        - constraints: Dict[str, Dict[str, Any]] with "value" and "source"
        
        Args:
            updates: Raw update dictionary
            source: Source to assign to new items (defaults to llm_inference)
            
        Returns:
            Validated and normalized update dictionary
        """
        if source is None:
            source = Source.llm_inference()
        
        validated = {}
        
        # Validate and normalize capabilities
        if "capabilities" in updates:
            if updates["capabilities"] is None:
                # Skip None values
                pass
            elif isinstance(updates["capabilities"], list):
                normalized = self._normalize_capabilities(updates["capabilities"], source=source)
                if normalized:
                    validated["capabilities"] = normalized
            else:
                logger.warning(
                    f"Invalid capabilities update type: {type(updates['capabilities'])}. "
                    f"Expected list, got {type(updates['capabilities'])}"
                )
        
        # Validate and normalize knowledge_boundaries
        if "knowledge_boundaries" in updates:
            if updates["knowledge_boundaries"] is None:
                pass
            else:
                normalized = self._normalize_dict_with_sources(updates["knowledge_boundaries"], source=source)
                if normalized:
                    validated["knowledge_boundaries"] = normalized
                elif not isinstance(updates["knowledge_boundaries"], (dict, list)):
                    logger.warning(
                        f"Invalid knowledge_boundaries update type: {type(updates['knowledge_boundaries'])}. "
                        f"Expected dict or list, got {type(updates['knowledge_boundaries'])}"
                    )
        
        # Validate and normalize constraints
        if "constraints" in updates:
            if updates["constraints"] is None:
                pass
            else:
                normalized = self._normalize_dict_with_sources(updates["constraints"], source=source)
                if normalized:
                    validated["constraints"] = normalized
                elif not isinstance(updates["constraints"], (dict, list)):
                    logger.warning(
                        f"Invalid constraints update type: {type(updates['constraints'])}. "
                        f"Expected dict or list, got {type(updates['constraints'])}"
                    )
        
        return validated
    
    def _normalize_dict_with_sources(self, data: Any, source: Optional[Source] = None) -> Dict[str, Dict[str, Any]]:
        """
        Normalize dict values to dict format with sources.
        
        Args:
            data: Dictionary or list that should become a dict
            source: Source to assign to new items (defaults to llm_inference)
            
        Returns:
            Dictionary with dict values containing "value" and "source" keys
        """
        if source is None:
            source = Source.llm_inference()
        
        # First normalize to simple dict (string values)
        simple_dict = self._normalize_to_dict(data)
        
        # Then convert to dict with sources
        result = {}
        for key, value in simple_dict.items():
            if isinstance(value, dict):
                # Already a dict - ensure it has value and source
                if "value" not in value:
                    # Use the dict itself as value, but ensure source exists
                    result[key] = {
                        "value": value,
                        "source": value.get("source", source.to_dict())
                    }
                else:
                    # Has value, ensure source exists
                    if "source" not in value:
                        value["source"] = source.to_dict()
                    elif not isinstance(value["source"], dict):
                        # Convert Source object to dict
                        value["source"] = value["source"].to_dict() if hasattr(value["source"], "to_dict") else source.to_dict()
                    result[key] = value
            else:
                # String or other type - convert to dict with source
                result[key] = {
                    "value": str(value),
                    "source": source.to_dict()
                }
        
        return result
    
    def apply_updates(
        self, 
        current_model: SelfModel, 
        updates: Dict[str, Any],
        source: Optional[Source] = None
    ) -> SelfModel:
        """
        Apply updates to current model to create updated model.
        
        Args:
            current_model: Current self-model
            updates: Dictionary of updates to apply
            source: Source to assign to new items (defaults to llm_inference)
            
        Returns:
            New SelfModel instance with updates applied
        """
        if source is None:
            source = Source.llm_inference()
        
        # Validate and normalize updates first
        validated_updates = self._validate_updates(updates, source=source)
        
        if not validated_updates:
            logger.debug("No valid updates to apply after validation")
            return current_model
        
        # Create new model starting from current (SelfModel will normalize the structure)
        updated_model = SelfModel(
            capabilities=current_model.capabilities.copy(),
            knowledge_boundaries=current_model.knowledge_boundaries.copy(),
            constraints=current_model.constraints.copy(),
            metadata=current_model.metadata.copy(),
            epistemic_layer=current_model.epistemic_layer,  # Preserve epistemic layer
        )
        
        # Track new/updated knowledge in epistemic layer if available
        if updated_model.epistemic_layer:
            try:
                from .epistemic.ids import (
                    generate_capability_id,
                    generate_preference_id,
                    generate_constraint_id,
                    generate_knowledge_boundary_id,
                    generate_behavioral_pattern_id,
                )
                from .epistemic.models import SourceType, SourceMetadata
                from .epistemic.engine import MetacognitiveEngine
                from datetime import datetime, timezone
                
                engine = MetacognitiveEngine(epistemic_layer=updated_model.epistemic_layer)
                source = SourceMetadata(
                    source_type=SourceType.SYSTEM_DEFAULT,
                    timestamp=datetime.now(timezone.utc)
                )
            except Exception as e:
                logger.debug(f"Error setting up epistemic tracking for updates: {e}", exc_info=True)
                engine = None
        else:
            engine = None
        
        # Apply updates (all updates are now validated and normalized)
        if "capabilities" in validated_updates:
            # Capabilities are already normalized to List[Dict] with sources by _validate_updates
            # Merge with existing, avoiding duplicates by text
            existing_texts = {cap.get("text", str(cap)) for cap in updated_model.capabilities}
            new_caps = [
                cap for cap in validated_updates["capabilities"]
                if cap.get("text", str(cap)) not in existing_texts
            ]
            updated_model.capabilities.extend(new_caps)
            
            # Track new capabilities in epistemic layer
            if engine:
                from .epistemic.inference import InferenceTracker
                tracker = InferenceTracker()
                
                for cap_dict in new_caps:
                    try:
                        cap_text = cap_dict.get("text", str(cap_dict))
                        knowledge_id = generate_capability_id(cap_text)
                        # Use assessed source reliability instead of hardcoded value
                        source_reliability = engine.validator.assess_source_reliability(source)
                        metrics = engine.knowledge_acquisition_workflow(
                            knowledge_id=knowledge_id,
                            source=source,
                            initial_confidence=source_reliability
                        )
                        
                        # Create inference node if this is derived from self-model update
                        if source.source_type == SourceType.SYSTEM_DEFAULT:
                            from .epistemic.models import InferenceNode
                            inference_node = InferenceNode(
                                knowledge_id=knowledge_id,
                                node_type="conclusion",
                                inference_type="self_model_update",
                                confidence=metrics.overall_confidence,
                                source=source
                            )
                            tracker.track_inference(inference_node, engine.epistemic_layer)
                    except Exception as e:
                        logger.debug(f"Error tracking capability update: {e}", exc_info=True)
        
        if "knowledge_boundaries" in validated_updates:
            # Knowledge boundaries are already validated as Dict[str, Dict] with sources
            # Track new/updated knowledge boundaries
            if engine:
                for key, value_dict in validated_updates["knowledge_boundaries"].items():
                    try:
                        value = value_dict.get("value", str(value_dict))
                        knowledge_id = generate_knowledge_boundary_id(key, value)
                        # Use assessed source reliability instead of hardcoded value
                        source_reliability = engine.validator.assess_source_reliability(source)
                        engine.knowledge_acquisition_workflow(
                            knowledge_id=knowledge_id,
                            source=source,
                            initial_confidence=source_reliability
                        )
                    except Exception as e:
                        logger.debug(f"Error tracking knowledge boundary update: {e}", exc_info=True)
            # Update knowledge boundaries (other takes precedence)
            updated_model.knowledge_boundaries.update(validated_updates["knowledge_boundaries"])
        
        if "constraints" in validated_updates:
            # Constraints are already validated as Dict[str, Dict] with sources
            # Track new/updated constraints
            if engine:
                for key, value_dict in validated_updates["constraints"].items():
                    try:
                        value = value_dict.get("value", str(value_dict))
                        knowledge_id = generate_constraint_id(key, value)
                        # Use assessed source reliability instead of hardcoded value
                        source_reliability = engine.validator.assess_source_reliability(source)
                        engine.knowledge_acquisition_workflow(
                            knowledge_id=knowledge_id,
                            source=source,
                            initial_confidence=source_reliability
                        )
                    except Exception as e:
                        logger.debug(f"Error tracking constraint update: {e}", exc_info=True)
            # Update constraints (other takes precedence)
            updated_model.constraints.update(validated_updates["constraints"])
        
        return updated_model
    
    def merge_updates(
        self,
        base_model: SelfModel,
        updates: List[Dict[str, Any]],
    ) -> SelfModel:
        """
        Merge multiple updates into a base model.
        
        Args:
            base_model: Base self-model
            updates: List of update dictionaries
            
        Returns:
            Merged SelfModel instance
        """
        result = base_model
        for update in updates:
            result = self.apply_updates(result, update)
        return result
    
    def update_from_internal_sensing(
        self,
        current_model: SelfModel,
        sensing_framework: "InternalSensingFramework",
    ) -> SelfModel:
        """
        Update self-model from internal sensing data.
        
        Args:
            current_model: Current self-model
            sensing_framework: InternalSensingFramework instance
            
        Returns:
            Updated SelfModel instance
        """
        try:
            # Extract tool usage statistics
            tool_stats = sensing_framework.get_tool_statistics()
            
            # Build updates from sensing data
            updates: Dict[str, Any] = {}
            
            # Infer capabilities from tool usage
            if tool_stats:
                existing_texts = {cap.get("text", str(cap)) for cap in current_model.capabilities}
                new_capabilities = []
                for tool_name, count in tool_stats.items():
                    if count > 5:  # Frequently used
                        capability_text = f"Uses {tool_name} tool effectively"
                        if capability_text not in existing_texts:
                            new_capabilities.append(capability_text)
                if new_capabilities:
                    updates["capabilities"] = new_capabilities
            
            # Apply updates if any
            if updates:
                # Use internal_sensing as source
                source = Source(type="internal_sensing")
                updated_model = self.apply_updates(current_model, updates, source=source)
                updated_model.metadata["version"] = current_model.metadata.get("version", 1) + 1
                updated_model.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
                updated_model.metadata["update_reason"] = "internal_sensing"
                logger.info(f"Updated self-model from internal sensing to version {updated_model.metadata['version']}")
                return updated_model
            
            return current_model
            
        except Exception as e:
            logger.error(f"Error updating self-model from internal sensing: {e}", exc_info=True)
            return current_model

