"""
World state aggregator that collects data from various sources.

Aggregates information from internal sensing, self-model,
and system information into a unified world state object.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import logging
import platform
import os

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..internal_sensing.framework import InternalSensingFramework
    from ..self_model.model import SelfModel
    from ..tools.registry import ToolRegistry
    from ..memory.manager import MemoryManager
    from .directory_structure import DirectoryStructureGenerator
    from ..reasoning.integration_tool import ReasoningTool


class WorldStateAggregator:
    """
    Aggregates world state from multiple sources.
    
    Collects data from:
    - Internal sensing framework (physiology, cognition, affect)
    - Self-model (capabilities, preferences, constraints)
    - System information (date/time, platform)
    - Tool registry (available tools)
    - Memory namespace hierarchy (memory organization structure)
    - Directory structure (Broca house directory structure)
    """
    
    def __init__(
        self,
        internal_sensing: Optional["InternalSensingFramework"] = None,
        self_model: Optional["SelfModel"] = None,
        tool_registry: Optional["ToolRegistry"] = None,
        memory_manager: Optional["MemoryManager"] = None,
        directory_structure_generator: Optional["DirectoryStructureGenerator"] = None,
        self_model_reduction_level: Optional[str] = None,
        reasoning_tool: Optional["ReasoningTool"] = None,
        size_manager: Optional[Any] = None,
        config: Optional[Any] = None,
    ) -> None:
        """
        Initialize world state aggregator.
        
        Args:
            internal_sensing: Optional InternalSensingFramework instance
            self_model: Optional SelfModel instance
            tool_registry: Optional ToolRegistry instance
            memory_manager: Optional MemoryManager instance for namespace hierarchy
            directory_structure_generator: Optional DirectoryStructureGenerator instance for Broca house structure
            self_model_reduction_level: Optional reduction level for self-model data ("none", "mild", "moderate", "heavy").
                                        Defaults to "mild" if not specified.
            reasoning_tool: Optional ReasoningTool instance for reasoning state
        """
        self.internal_sensing = internal_sensing
        self.self_model = self_model
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.directory_structure_generator = directory_structure_generator
        self.self_model_reduction_level = self_model_reduction_level or "mild"
        self.reasoning_tool = reasoning_tool
        self.size_manager = size_manager
        self.config = config
        self._last_tool_registry_hash: Optional[str] = None
        
        logger.info("Initialized WorldStateAggregator")
    
    def aggregate(self) -> Dict[str, Any]:
        """
        Aggregate all available world state data into a clean hierarchical structure.
        
        Returns:
            Dictionary containing all aggregated world state information in a clean,
            hierarchical format. Only includes sections when data is available;
            unavailable sections are omitted entirely.
        """
        world_state: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # System info (always available)
        system_info = self.get_system_info()
        if system_info.get("available"):
            world_state["system"] = {
                "datetime": system_info.get("current_datetime"),
                "date": system_info.get("current_date"),
                "time": system_info.get("current_time"),
                "timezone": system_info.get("timezone"),
                "platform": system_info.get("platform"),
                "platform_release": system_info.get("platform_release"),
                "platform_version": system_info.get("platform_version"),
                "machine": system_info.get("machine"),
                "processor": system_info.get("processor"),
                "python_version": system_info.get("python_version"),
                "working_directory": system_info.get("working_directory"),
            }
        
        # Self-model - use metadata-only mode if size management enabled
        self_model_state = self.get_self_model_state()
        if self_model_state.get("available"):
            # Use metadata-only representation if size management enabled
            if (hasattr(self, 'size_manager') and self.size_manager and 
                hasattr(self, 'config') and self.config and 
                hasattr(self.config, 'self_model') and 
                self.config.self_model.metadata_only_mode):
                try:
                    # Get the actual SelfModel instance from state
                    self_model_instance = self_model_state.get("self_model")
                    if self_model_instance is None and self.self_model:
                        self_model_instance = self.self_model
                    if self_model_instance:
                        metadata_only = self.size_manager.get_metadata_only_representation(
                            self_model_instance
                        )
                        self_model_dict = metadata_only
                    else:
                        # No self model instance, use state dict
                        self_model_dict = {"summary": self_model_state.get("summary")}
                except Exception as e:
                    logger.warning(f"Error getting metadata-only self-model representation: {e}")
                    # Fall back to normal representation
                    self_model_dict = {
                        "summary": self_model_state.get("summary"),
                    }
                    if "capabilities" in self_model_state:
                        self_model_dict["capabilities"] = self_model_state.get("capabilities", [])
                    if "knowledge_boundaries" in self_model_state:
                        self_model_dict["knowledge_boundaries"] = self_model_state.get("knowledge_boundaries", {})
                    if "constraints" in self_model_state:
                        self_model_dict["constraints"] = self_model_state.get("constraints", {})
                    if "metadata" in self_model_state:
                        self_model_dict["metadata"] = self_model_state.get("metadata", {})
            else:
                # Build self_model dict with only fields that are present (respects reduction level)
                self_model_dict = {
                    "summary": self_model_state.get("summary"),
                }
                # Only include these fields if they exist in the state (not present in "heavy" reduction)
                if "capabilities" in self_model_state:
                    self_model_dict["capabilities"] = self_model_state.get("capabilities", [])
                if "knowledge_boundaries" in self_model_state:
                    self_model_dict["knowledge_boundaries"] = self_model_state.get("knowledge_boundaries", {})
                if "constraints" in self_model_state:
                    self_model_dict["constraints"] = self_model_state.get("constraints", {})
                if "metadata" in self_model_state:
                    self_model_dict["metadata"] = self_model_state.get("metadata", {})
            world_state["self_model"] = self_model_dict
        
        # Internal sensing - only include if available
        internal_sensing_state = self.get_internal_sensing_state()
        if internal_sensing_state.get("available"):
            current_state = internal_sensing_state.get("current_state", {})
            world_state["internal_state"] = {
                "tool_statistics": internal_sensing_state.get("tool_statistics", {}),
            }
            # Add physiology, cognition, affect from current_state if available
            if current_state:
                if "computational" in current_state:
                    world_state["internal_state"]["physiology"] = self._aggregate_physiology_health(current_state["computational"])
                if "cognitive" in current_state:
                    # Preserve cognitive state including data_quality indicators
                    cognitive_state = current_state["cognitive"]
                    world_state["internal_state"]["cognition"] = cognitive_state
                    # Ensure data_quality is preserved if present
                    if "data_quality" not in cognitive_state and hasattr(self.internal_sensing.interoception.cognition, 'states'):
                        # Try to extract data_quality from cognitive monitor if not in state
                        cog_states = self.internal_sensing.interoception.cognition.states
                        if "data_quality" in cog_states:
                            cognitive_state["data_quality"] = cog_states["data_quality"]
                if "affective" in current_state:
                    # Preserve affective state including data_quality indicators
                    affective_state = current_state["affective"]
                    world_state["internal_state"]["affect"] = affective_state
                    # Ensure data_quality is preserved if present
                    if "data_quality" not in affective_state and hasattr(self.internal_sensing.interoception.affect, 'affective_states'):
                        # Try to extract data_quality from affective monitor if not in state
                        aff_states = self.internal_sensing.interoception.affect.affective_states
                        if "data_quality" in aff_states:
                            affective_state["data_quality"] = aff_states["data_quality"]
            
            # Add predictive data if available
            if "predictive" in internal_sensing_state:
                world_state["internal_state"]["predictive"] = internal_sensing_state["predictive"]
            
            # Note: behavioral_patterns and reasoning_patterns are excluded from world state
            # to prevent unbounded growth. These accumulate over time and represent historical
            # data rather than current state, violating AGENTS.md guidelines for system prompt size limits.
            
            # Add anomalies if detected
            if "anomalies" in internal_sensing_state:
                anomalies = internal_sensing_state["anomalies"]
                if anomalies:
                    world_state["internal_state"]["anomalies"] = anomalies
            
            # Add quality metrics if available
            if "quality_metrics" in internal_sensing_state:
                quality_metrics = internal_sensing_state["quality_metrics"]
                if quality_metrics:
                    world_state["internal_state"]["quality_metrics"] = quality_metrics
            
            # Add motivational state if available
            if "motivational_state" in internal_sensing_state:
                motivational_state = internal_sensing_state["motivational_state"]
                if motivational_state:
                    world_state["internal_state"]["motivational_state"] = motivational_state
            
            # Add epistemic metrics if available
            if "epistemic" in internal_sensing_state:
                epistemic_data = internal_sensing_state["epistemic"]
                if epistemic_data:
                    # Create compact epistemic summary
                    world_state["internal_state"]["epistemic"] = self._aggregate_epistemic_summary(epistemic_data)
        
        # Tools - only include if available
        tools_info = self.get_tools_info()
        if tools_info.get("available"):
            world_state["tools_registry"] = tools_info.get("tools_registry", {})
            # Conditionally include tools list if hash changed
            if "tools" in tools_info:
                world_state["tools"] = tools_info["tools"]
        
        # Memory index - only include if available
        memory_info = self.get_memory_namespace_hierarchy()
        if memory_info.get("available"):
            world_state["memory"] = {
                "memory_index": memory_info.get("memory_index", {}),
            }
        
        # Repo pointer - only include if available
        broca_house_info = self.get_broca_house_structure()
        if broca_house_info.get("available"):
            world_state["repo"] = broca_house_info.get("repo", {})
            if "note" in broca_house_info:
                world_state["repo_note"] = broca_house_info["note"]
        
        # Reasoning state - only include if available
        reasoning_state = self.get_reasoning_state()
        if reasoning_state.get("available"):
            world_state["reasoning"] = reasoning_state.get("reasoning", {})
        
        return world_state
    
    def get_internal_sensing_state(self) -> Dict[str, Any]:
        """
        Get internal sensing state.
        
        Returns:
            Dictionary with internal sensing information including predictive data,
            behavioral patterns, anomalies, quality metrics, motivational state, and reasoning patterns
        """
        if not self.internal_sensing:
            return {"available": False}
        
        try:
            # Sample current internal state (force fresh sample to get latest moving averages)
            current_state = self.internal_sensing.sample_internal_state(force=True)
            
            # Get interoceptive report
            interoceptive_report = self.internal_sensing.generate_interoceptive_report()
            
            # Get tool statistics
            tool_stats = self.internal_sensing.get_tool_statistics()
            
            # Extract predictive data from current_state
            predictive_data = current_state.get("predictive")
            
            # Extract behavioral patterns
            behavioral_patterns = self.internal_sensing.extract_behavioral_patterns()
            
            # Detect anomalies
            anomalies = self.internal_sensing.interoception.detect_anomalies()
            
            # Get quality metrics (always include since measure_self_awareness_quality() always returns a value)
            self_awareness_quality = self.internal_sensing.interoception.measure_self_awareness_quality()
            interoceptive_accuracy = self.internal_sensing.interoception.track_interoceptive_accuracy()
            
            quality_metrics = {
                "self_awareness_quality": self_awareness_quality,
                "interoceptive_accuracy": interoceptive_accuracy,
            }
            
            # Extract motivational state
            motivational_drives = self.internal_sensing.interoception.affect.get_motivational_drives()
            satisfaction_patterns = self.internal_sensing.interoception.affect.get_satisfaction_patterns()
            
            motivational_state = {}
            if motivational_drives:
                motivational_state["drives"] = motivational_drives
            if satisfaction_patterns:
                # Aggregate satisfaction patterns to prevent unbounded growth
                aggregated = self._aggregate_satisfaction_patterns(satisfaction_patterns)
                if aggregated:  # Only include if aggregation produced data
                    motivational_state["satisfaction_patterns"] = aggregated
            
            # Extract reasoning patterns from cognitive state
            reasoning_patterns = self.internal_sensing.interoception.cognition._get_reasoning_patterns()
            
            # Extract epistemic metrics from epistemic bridge if available
            epistemic_data = None
            if hasattr(self.internal_sensing.interoception, 'epistemic_bridge') and self.internal_sensing.interoception.epistemic_bridge:
                try:
                    epistemic_bridge = self.internal_sensing.interoception.epistemic_bridge
                    
                    # Get aggregated uncertainty
                    epistemic_uncertainty = epistemic_bridge.get_aggregated_uncertainty()
                    
                    # Get aggregated confidence
                    epistemic_confidence = epistemic_bridge.get_aggregated_confidence()
                    
                    # Get source reliability summary
                    source_reliability = epistemic_bridge.get_source_reliability()
                    
                    # Create compact epistemic summary
                    epistemic_data = {
                        "uncertainty": epistemic_uncertainty,
                        "confidence": epistemic_confidence,
                        "source_reliability": self._aggregate_source_reliability(source_reliability),
                    }
                except Exception as e:
                    logger.warning(f"Error extracting epistemic metrics: {e}", exc_info=True)
                    epistemic_data = None
            
            result = {
                "available": True,
                "current_state": current_state,
                "interoceptive_report": interoceptive_report,
                "tool_statistics": tool_stats,
            }
            
            # Add optional fields only if they have data
            if predictive_data:
                result["predictive"] = predictive_data
            if behavioral_patterns:
                result["behavioral_patterns"] = behavioral_patterns
            if anomalies:
                result["anomalies"] = anomalies
            if quality_metrics:
                result["quality_metrics"] = quality_metrics
            if motivational_state:
                result["motivational_state"] = motivational_state
            if reasoning_patterns:
                result["reasoning_patterns"] = reasoning_patterns
            if epistemic_data:
                result["epistemic"] = epistemic_data
            
            return result
        except Exception as e:
            logger.warning(f"Error getting internal sensing state: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def _summarize_with_model(self, text: str, max_length: int = 100) -> str:
        """
        Stub for future sentence-summarization model integration.
        
        This method is a placeholder for when a sentence-summarization model
        (e.g., BART, T5, or LLM-based) is integrated to generate intelligent
        summaries that preserve semantic meaning and key information.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summarized text (currently returns input as stub)
        """
        # TODO: Integrate sentence-summarization model here
        # For now, this is a stub that returns the input
        # Future implementation might use:
        # - BART/T5 models via transformers library
        # - LLM-based summarization via API
        # - Custom fine-tuned model for self-model summarization
        return text[:max_length] if len(text) > max_length else text
    
    def _analyze_capabilities_themes(self, capabilities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Analyze capabilities and group them by theme.
        
        Args:
            capabilities: List of capability dicts or strings
            
        Returns:
            Dictionary mapping themes to lists of capability texts
        """
        texts = [
            cap.get("text", str(cap)) if isinstance(cap, dict) else str(cap)
            for cap in capabilities
        ]
        
        themes = {
            "conversation": [],
            "tools": [],
            "code": [],
            "information": [],
            "mathematics": [],
            "reasoning": [],
            "memory": [],
            "other": []
        }
        
        for text in texts:
            text_lower = text.lower()
            if any(word in text_lower for word in ["conversation", "assistance", "chat", "dialogue", "communication"]):
                themes["conversation"].append(text)
            elif any(word in text_lower for word in ["tool", "terminal", "web search", "memory", "critic", "environment"]):
                themes["tools"].append(text)
            elif any(word in text_lower for word in ["code", "programming", "execution", "software", "development"]):
                themes["code"].append(text)
            elif any(word in text_lower for word in ["information", "retrieval", "synthesis", "research", "search"]):
                themes["information"].append(text)
            elif any(word in text_lower for word in ["math", "mathematical", "calculation", "proof", "equation"]):
                themes["mathematics"].append(text)
            elif any(word in text_lower for word in ["reasoning", "logic", "inference", "analysis", "thinking"]):
                themes["reasoning"].append(text)
            elif any(word in text_lower for word in ["memory", "remember", "recall", "storage"]) and "tool" not in text_lower:
                themes["memory"].append(text)
            else:
                themes["other"].append(text)
        
        return themes
    
    def _summarize_capabilities_moderate(self, capabilities: List[Dict[str, Any]]) -> str:
        """
        Generate moderate summary for capabilities: grouped by theme with key examples.
        
        Args:
            capabilities: List of capability dicts or strings
            
        Returns:
            Sentence summarizing capabilities by theme
        """
        if not capabilities:
            return "No capabilities defined."
        
        themes = self._analyze_capabilities_themes(capabilities)
        total = len(capabilities)
        
        # Build summary with key themes and examples
        parts = []
        if themes["conversation"]:
            parts.append(f"conversation and assistance ({len(themes['conversation'])} capabilities)")
        if themes["tools"]:
            tool_examples = [t.split('(')[0].strip() if '(' in t else t for t in themes['tools'][:3]]
            parts.append(f"tool usage including {', '.join(tool_examples)} ({len(themes['tools'])} total)")
        if themes["code"]:
            parts.append(f"code execution and analysis ({len(themes['code'])} capabilities)")
        if themes["information"]:
            parts.append(f"information retrieval and synthesis ({len(themes['information'])} capabilities)")
        if themes["mathematics"]:
            parts.append(f"mathematical problem solving ({len(themes['mathematics'])} capabilities)")
        if themes["reasoning"]:
            parts.append(f"logical reasoning and analysis ({len(themes['reasoning'])} capabilities)")
        if themes["memory"]:
            parts.append(f"memory operations ({len(themes['memory'])} capabilities)")
        if themes["other"]:
            other_count = len(themes["other"])
            if other_count <= 5:
                parts.append(f"other: {', '.join([t[:50] for t in themes['other']])}")
            else:
                parts.append(f"other capabilities ({other_count} total)")
        
        if not parts:
            return f"Has {total} capabilities across various domains."
        
        return f"Capabilities span {', '.join(parts)}. Total: {total} capabilities."
    
    def _summarize_knowledge_boundaries_moderate(self, knowledge_boundaries: Dict[str, Any]) -> str:
        """
        Generate moderate summary for knowledge boundaries: key boundaries with context.
        
        Args:
            knowledge_boundaries: Dict of knowledge boundary dicts
            
        Returns:
            Sentence summarizing knowledge boundaries
        """
        if not knowledge_boundaries:
            return "No knowledge boundaries defined."
        
        # Extract key boundaries
        boundaries = []
        for key, value_dict in knowledge_boundaries.items():
            value = value_dict.get("value", str(value_dict)) if isinstance(value_dict, dict) else str(value_dict)
            boundaries.append((key, value))
        
        # Group by type if possible
        time_related = [b for b in boundaries if any(word in b[0].lower() for word in ["time", "cutoff", "date", "training"])]
        access_related = [b for b in boundaries if any(word in b[0].lower() for word in ["access", "internet", "real_time", "live"])]
        domain_related = [b for b in boundaries if any(word in b[0].lower() for word in ["domain", "subject", "field", "area"])]
        other = [b for b in boundaries if b not in time_related + access_related + domain_related]
        
        parts = []
        if time_related:
            parts.append(f"temporal: {', '.join([f'{k} ({v})' for k, v in time_related[:2]])}")
        if access_related:
            parts.append(f"access: {', '.join([f'{k} ({v})' for k, v in access_related[:2]])}")
        if domain_related:
            parts.append(f"domain: {', '.join([f'{k} ({v})' for k, v in domain_related[:2]])}")
        if other:
            other_str = ', '.join([f'{k} ({v})' for k, v in other[:2]])
            if len(other) > 2:
                other_str += f" and {len(other) - 2} others"
            parts.append(f"other: {other_str}")
        
        return f"Knowledge boundaries: {'; '.join(parts)}."
    
    def _summarize_constraints_moderate(self, constraints: Dict[str, Any]) -> str:
        """
        Generate moderate summary for constraints: key constraints with context.
        
        Args:
            constraints: Dict of constraint dicts
            
        Returns:
            Sentence summarizing constraints
        """
        if not constraints:
            return "No constraints defined."
        
        # Extract and categorize constraints
        safety = []
        access = []
        operational = []
        other = []
        
        for key, value_dict in constraints.items():
            value = value_dict.get("value", str(value_dict)) if isinstance(value_dict, dict) else str(value_dict)
            key_lower = key.lower()
            value_lower = value.lower()
            
            if any(word in key_lower + value_lower for word in ["safety", "security", "dangerous", "harmful", "unsafe"]):
                safety.append((key, value))
            elif any(word in key_lower + value_lower for word in ["access", "internet", "network", "terminal", "command"]):
                access.append((key, value))
            elif any(word in key_lower + value_lower for word in ["operation", "mode", "read-only", "write", "execute"]):
                operational.append((key, value))
            else:
                other.append((key, value))
        
        parts = []
        if safety:
            parts.append(f"safety: {', '.join([f'{k} ({v[:60]})' for k, v in safety[:2]])}")
        if access:
            parts.append(f"access: {', '.join([f'{k} ({v[:60]})' for k, v in access[:2]])}")
        if operational:
            parts.append(f"operational: {', '.join([f'{k} ({v[:60]})' for k, v in operational[:2]])}")
        if other:
            other_str = ', '.join([f'{k} ({v[:60]})' for k, v in other[:2]])
            if len(other) > 2:
                other_str += f" and {len(other) - 2} others"
            parts.append(f"other: {other_str}")
        
        return f"Constraints: {'; '.join(parts)}."
    
    def _summarize_capabilities_heavy(self, capabilities: List[Dict[str, Any]]) -> str:
        """
        Generate heavy summary for capabilities: high-level essence capturing core identity.
        
        Args:
            capabilities: List of capability dicts or strings
            
        Returns:
            Single sentence capturing core capability identity
        """
        if not capabilities:
            return "No capabilities defined."
        
        themes = self._analyze_capabilities_themes(capabilities)
        total = len(capabilities)
        
        # Identify dominant themes
        theme_counts = {k: len(v) for k, v in themes.items() if v}
        dominant = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Create high-level summary focusing on core identity
        if total <= 10:
            # Small model - be specific
            core_areas = [theme for theme, count in dominant]
            return f"Core capabilities: {', '.join(core_areas)} with {total} total capabilities."
        else:
            # Large model - focus on breadth and key strengths
            primary = dominant[0][0] if dominant else "general"
            secondary_count = sum(count for _, count in dominant[1:])
            return f"Comprehensive cognitive system with {total} capabilities, primarily focused on {primary}" + \
                   (f" and {secondary_count} other key areas" if secondary_count > 0 else "") + "."
    
    def _summarize_knowledge_boundaries_heavy(self, knowledge_boundaries: Dict[str, Any]) -> str:
        """
        Generate heavy summary for knowledge boundaries: essence of limitations.
        
        Args:
            knowledge_boundaries: Dict of knowledge boundary dicts
            
        Returns:
            Single sentence capturing core knowledge limitations
        """
        if not knowledge_boundaries:
            return "No knowledge boundaries defined."
        
        # Extract key themes
        has_temporal = any("time" in k.lower() or "cutoff" in k.lower() or "training" in k.lower() 
                          for k in knowledge_boundaries.keys())
        has_access = any("access" in k.lower() or "internet" in k.lower() or "real_time" in k.lower() 
                        for k in knowledge_boundaries.keys())
        has_domain = any("domain" in k.lower() or "subject" in k.lower() or "field" in k.lower() 
                        for k in knowledge_boundaries.keys())
        
        themes = []
        if has_temporal:
            themes.append("temporal limitations")
        if has_access:
            themes.append("access constraints")
        if has_domain:
            themes.append("domain boundaries")
        
        count = len(knowledge_boundaries)
        if themes:
            return f"Knowledge boundaries include {', '.join(themes)} across {count} defined areas."
        else:
            return f"Has {count} defined knowledge boundaries."
    
    def _summarize_constraints_heavy(self, constraints: Dict[str, Any]) -> str:
        """
        Generate heavy summary for constraints: essence of limitations.
        
        Args:
            constraints: Dict of constraint dicts
            
        Returns:
            Single sentence capturing core operational constraints
        """
        if not constraints:
            return "No constraints defined."
        
        # Identify constraint themes
        has_safety = any("safety" in k.lower() or "security" in k.lower() or "dangerous" in k.lower() 
                        for k in constraints.keys())
        has_access = any("access" in k.lower() or "internet" in k.lower() or "terminal" in k.lower() 
                        for k in constraints.keys())
        has_operational = any("operation" in k.lower() or "mode" in k.lower() or "read-only" in k.lower() 
                             for k in constraints.keys())
        
        themes = []
        if has_safety:
            themes.append("safety restrictions")
        if has_access:
            themes.append("access limitations")
        if has_operational:
            themes.append("operational constraints")
        
        count = len(constraints)
        if themes:
            return f"Subject to {', '.join(themes)} with {count} total constraints."
        else:
            return f"Operates under {count} defined constraints."
    
    def get_self_model_state(self, reduction_level: Optional[str] = None) -> Dict[str, Any]:
        """
        Get self-model state with optional reduction level.
        
        Args:
            reduction_level: Optional reduction level override. If not provided, uses
                           self.self_model_reduction_level (defaults to "mild").
                           Options: "none", "mild", "moderate", "heavy"
        
        Returns:
            Dictionary with self-model information
        """
        if not self.self_model:
            return {"available": False}
        
        try:
            # Determine reduction level
            reduction_level = reduction_level or self.self_model_reduction_level or "mild"
            
            # Always use minimal summary (same for all levels)
            summary = self.self_model.get_minimal_summary()
            
            # Store self_model instance in result for size manager
            result = {
                "available": True,
                "summary": summary,
                "self_model": self.self_model,  # Include instance for size manager
            }
            
            # Apply reduction based on level
            if reduction_level == "none":
                # Full data with all source metadata (backward compatible)
                result.update({
                    "capabilities": self.self_model.capabilities,
                    "knowledge_boundaries": self.self_model.knowledge_boundaries,
                    "constraints": self.self_model.constraints,
                    "metadata": self.self_model.metadata,
                })
                return result
            elif reduction_level == "mild":
                # Remove source metadata, keep all fields
                result.update({
                    "capabilities": [
                        cap.get("text", str(cap)) if isinstance(cap, dict) else str(cap)
                        for cap in self.self_model.capabilities
                    ],
                    "knowledge_boundaries": {
                        key: value_dict.get("value", str(value_dict))
                        if isinstance(value_dict, dict) else str(value_dict)
                        for key, value_dict in self.self_model.knowledge_boundaries.items()
                    },
                    "constraints": {
                        key: value_dict.get("value", str(value_dict))
                        if isinstance(value_dict, dict) else str(value_dict)
                        for key, value_dict in self.self_model.constraints.items()
                    },
                    "metadata": self.self_model.metadata,
                })
                return result
            elif reduction_level == "moderate":
                # Replace each category with a brief sentence
                result.update({
                    "capabilities": self._summarize_capabilities_moderate(self.self_model.capabilities),
                    "knowledge_boundaries": self._summarize_knowledge_boundaries_moderate(self.self_model.knowledge_boundaries),
                    "constraints": self._summarize_constraints_moderate(self.self_model.constraints),
                    "metadata": {
                        "version": self.self_model.metadata.get("version"),
                        "last_updated": self.self_model.metadata.get("last_updated"),
                    },
                })
                return result
            elif reduction_level == "heavy":
                # Single sentence summary per field
                result.update({
                    "capabilities": self._summarize_capabilities_heavy(self.self_model.capabilities),
                    "knowledge_boundaries": self._summarize_knowledge_boundaries_heavy(self.self_model.knowledge_boundaries),
                    "constraints": self._summarize_constraints_heavy(self.self_model.constraints),
                })
                return result
            else:
                # Invalid reduction level, default to mild
                logger.warning(f"Invalid reduction level '{reduction_level}', defaulting to 'mild'")
                return self.get_self_model_state(reduction_level="mild")
        except Exception as e:
            logger.warning(f"Error getting self-model state: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            Dictionary with system information
        """
        try:
            now = datetime.now(timezone.utc)
            return {
                "available": True,
                "current_datetime": now.isoformat(),
                "current_date": now.date().isoformat(),
                "current_time": now.time().isoformat(),
                "timezone": "UTC",
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "working_directory": os.getcwd(),
            }
        except Exception as e:
            logger.warning(f"Error getting system info: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def get_tools_info(self) -> Dict[str, Any]:
        """
        Get information about available tools.
        
        Returns:
            Dictionary with tool registry information. Includes tools list
            only when registry hash changes.
        """
        if not self.tool_registry:
            return {"available": False}
        
        try:
            current_hash = self.tool_registry.get_registry_hash()
            version = self.tool_registry.get_registry_version()
            
            result = {
                "available": True,
                "tools_registry": {
                    "version": version,
                    "hash": current_hash,
                    "refresh_on_change": True
                }
            }
            
            # Include tools if hash changed or first time
            if current_hash != self._last_tool_registry_hash:
                tools = self.tool_registry.list_tools()
                result["tools"] = {
                    "count": len(tools),
                    "names": [tool.name for tool in tools]
                }
                self._last_tool_registry_hash = current_hash
            
            return result
        except Exception as e:
            logger.warning(f"Error getting tools info: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def get_memory_namespace_hierarchy(self) -> Dict[str, Any]:
        """
        Get memory index pointer.
        
        Returns:
            Dictionary with memory index pointer information
        """
        if not self.memory_manager:
            return {"available": False}
        
        try:
            storage = self.memory_manager.storage
            namespace_index = self.memory_manager.namespace_index
            
            # Trigger index update to set last_indexed
            namespace_index.get_namespace_hierarchy()
            
            return {
                "available": True,
                "memory_index": {
                    "root": "broca/",
                    "schema_version": storage.get_schema_version(),
                    "last_indexed": namespace_index.get_last_indexed(),
                    "fetch": "retrieve_memories(query)"
                }
            }
        except Exception as e:
            logger.warning(f"Error getting memory index: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def get_broca_house_structure(self) -> Dict[str, Any]:
        """
        Get repo pointer for directory structure.
        
        Returns:
            Dictionary with repo pointer information
        """
        if not self.directory_structure_generator:
            return {"available": False}
        
        try:
            generator = self.directory_structure_generator
            tree_hash = generator.get_directory_tree_hash()
            
            return {
                "available": True,
                "repo": {
                    "root": str(generator.root_path),
                    "tree_hash": tree_hash,
                    "last_scan": generator.get_last_scan()
                },
                "note": "Use terminal or a file-listing tool to inspect the directory tree; never rely on stale tree."
            }
        except Exception as e:
            logger.warning(f"Error getting repo pointer: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def _aggregate_physiology_health(self, computational_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate computational state to compact health summary.
        
        Extracts only essential metrics: cpu_load, mem_pressure, latency_ms.
        Drops all detailed telemetry (cpu_per_core, disk_io, network_io, etc.)
        
        Args:
            computational_state: Full computational state dict
            
        Returns:
            Compact health summary: {"health": {"cpu_load": X, "mem_pressure": Y, "latency_ms": Z}}
        """
        health = {}
        
        # Extract cpu_load (from computational_load)
        cpu_load = computational_state.get("computational_load")
        if cpu_load is not None:
            health["cpu_load"] = cpu_load
        
        # Extract mem_pressure (from memory_pressure)
        mem_pressure = computational_state.get("memory_pressure")
        if mem_pressure is not None:
            health["mem_pressure"] = mem_pressure
        
        # Extract and convert latency (from processing_latency)
        latency = computational_state.get("processing_latency")
        if latency is not None:
            # Convert to milliseconds if in seconds
            latency_ms = latency * 1000 if latency < 1.0 else latency
            health["latency_ms"] = latency_ms
        
        return {"health": health}
    
    def _aggregate_satisfaction_patterns(
        self, satisfaction_patterns: List[Dict[str, Any]], max_recent: int = 10
    ) -> Dict[str, Any]:
        """
        Aggregate satisfaction patterns into compact summary statistics.
        
        Prevents unbounded growth by replacing the full list with aggregated statistics
        and only the most recent entries for current context.
        
        Args:
            satisfaction_patterns: Full list of satisfaction/frustration pattern dictionaries
            max_recent: Maximum number of recent patterns to include (default: 10)
            
        Returns:
            Aggregated satisfaction patterns dictionary with summary statistics and recent entries
        """
        if not satisfaction_patterns:
            return {}
        
        # Separate satisfaction and frustration entries
        satisfaction_entries = [p for p in satisfaction_patterns if p.get("type") == "satisfaction"]
        frustration_entries = [p for p in satisfaction_patterns if p.get("type") == "frustration"]
        
        # Compute summary statistics
        aggregated = {
            "total_count": len(satisfaction_patterns),
            "satisfaction": {
                "count": len(satisfaction_entries),
            },
            "frustration": {
                "count": len(frustration_entries),
            },
        }
        
        # Compute averages if we have entries
        if satisfaction_entries:
            satisfaction_levels = [p.get("level", 0.0) for p in satisfaction_entries]
            aggregated["satisfaction"]["average_level"] = sum(satisfaction_levels) / len(satisfaction_levels)
        
        if frustration_entries:
            frustration_levels = [p.get("level", 0.0) for p in frustration_entries]
            aggregated["frustration"]["average_level"] = sum(frustration_levels) / len(frustration_levels)
        
        # Include most recent entries for current context (sorted by timestamp, most recent first)
        sorted_patterns = sorted(satisfaction_patterns, key=lambda p: p.get("timestamp", 0.0), reverse=True)
        recent_patterns = sorted_patterns[:max_recent]
        
        if recent_patterns:
            aggregated["recent"] = recent_patterns
        
        return aggregated
    
    def _aggregate_source_reliability(self, source_reliability: Dict[str, float]) -> Dict[str, Any]:
        """
        Aggregate source reliability scores into compact summary.
        
        Args:
            source_reliability: Dictionary mapping source identifiers to reliability scores
            
        Returns:
            Compact summary with tool and memory reliability averages
        """
        if not source_reliability:
            return {}
        
        tool_reliabilities = []
        memory_reliabilities = []
        
        for source_key, reliability in source_reliability.items():
            if source_key.startswith("tool:"):
                tool_reliabilities.append(reliability)
            elif source_key.startswith("memory:"):
                memory_reliabilities.append(reliability)
        
        summary = {}
        
        if tool_reliabilities:
            avg_tool_reliability = sum(tool_reliabilities) / len(tool_reliabilities)
            summary["tool_reliability_avg"] = avg_tool_reliability
            summary["tool_count"] = len(tool_reliabilities)
        
        if memory_reliabilities:
            avg_memory_reliability = sum(memory_reliabilities) / len(memory_reliabilities)
            summary["memory_consistency_avg"] = avg_memory_reliability
            summary["memory_count"] = len(memory_reliabilities)
        
        return summary
    
    def _aggregate_epistemic_summary(self, epistemic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate epistemic data into compact summary for world state.
        
        Similar to _aggregate_physiology_health(), extracts only essential metrics
        to prevent size bloat while preserving key epistemic signals.
        
        Args:
            epistemic_data: Full epistemic data dictionary with uncertainty, confidence, source_reliability
            
        Returns:
            Compact epistemic summary with essential metrics only
        """
        summary = {}
        
        # Extract uncertainty summary
        uncertainty = epistemic_data.get("uncertainty", {})
        if uncertainty:
            # Include only essential uncertainty metrics
            uncertainty_summary = {
                "epistemic": uncertainty.get("epistemic"),
                "aleatoric": uncertainty.get("aleatoric"),
                "total": uncertainty.get("total"),
            }
            # Include data quality if available
            if "data_quality" in uncertainty:
                uncertainty_summary["data_quality"] = uncertainty.get("data_quality")
            if "sample_size" in uncertainty:
                uncertainty_summary["sample_size"] = uncertainty.get("sample_size")
            if "has_data" in uncertainty:
                uncertainty_summary["has_data"] = uncertainty.get("has_data")
            
            summary["uncertainty"] = uncertainty_summary
        
        # Extract confidence summary
        confidence = epistemic_data.get("confidence", {})
        if confidence:
            # Include only essential confidence metrics
            confidence_summary = {
                "overall_confidence": confidence.get("overall_confidence"),
            }
            # Include confidence interval if available
            if "confidence_interval" in confidence:
                confidence_summary["confidence_interval"] = confidence.get("confidence_interval")
            # Include calibration error if available
            if "calibration_error" in confidence and confidence.get("calibration_error") is not None:
                confidence_summary["calibration_error"] = confidence.get("calibration_error")
            # Include data quality if available
            if "data_quality" in confidence:
                confidence_summary["data_quality"] = confidence.get("data_quality")
            if "sample_size" in confidence:
                confidence_summary["sample_size"] = confidence.get("sample_size")
            if "has_data" in confidence:
                confidence_summary["has_data"] = confidence.get("has_data")
            if "uncertainty" in confidence:
                confidence_summary["uncertainty"] = confidence.get("uncertainty")
            
            summary["confidence"] = confidence_summary
        
        # Include source reliability summary (already aggregated)
        source_reliability = epistemic_data.get("source_reliability", {})
        if source_reliability:
            summary["source_reliability"] = source_reliability
        
        return summary
    
    def get_reasoning_state(self) -> Dict[str, Any]:
        """
        Get reasoning system state.
        
        Returns:
            Dictionary with reasoning state information (goals, active rules count, recent inferences)
            Size-limited to prevent unbounded growth (target: ~2KB)
        """
        if not self.reasoning_tool:
            return {"available": False}
        
        try:
            # Get state from reasoning tool
            state_result = self.reasoning_tool.execute("get_state")
            if not state_result.get("success"):
                return {"available": False}
            
            state = state_result.get("state", {})
            goal_manager_dict = state.get("goal_manager", {})
            rule_system_dict = state.get("rule_system", {})
            
            # Extract key information (size-limited)
            reasoning_state = {}
            
            # Active goals (limited count and description length)
            goals = goal_manager_dict.get("goals", {})
            active_goals = [
                {
                    "name": goal.get("name", ""),
                    "description": goal.get("description", "")[:100],  # Limit description
                    "priority": goal.get("priority", 0.0),
                    "progress": goal.get("progress", 0.0)
                }
                for goal in goals.values()
                if goal.get("status") == "active"
            ][:5]  # Limit to top 5 active goals
            
            if active_goals:
                reasoning_state["active_goals"] = active_goals
                reasoning_state["active_goals_count"] = len(active_goals)
            
            # Ready goals count
            ready_goals_count = goal_manager_dict.get("ready_goals_count", 0)
            if ready_goals_count > 0:
                reasoning_state["ready_goals_count"] = ready_goals_count
            
            # Rule system summary
            rules = rule_system_dict.get("rules", [])
            reasoning_state["total_rules"] = len(rules)
            
            # Working memory size
            working_memory_size = state.get("working_memory_size", 0)
            if working_memory_size > 0:
                reasoning_state["working_memory_size"] = working_memory_size
            
            # Daemon status (if available)
            if hasattr(self.reasoning_tool, 'daemon') and self.reasoning_tool.daemon:
                try:
                    daemon_status = self.reasoning_tool.daemon.get_status()
                    reasoning_state["daemon"] = {
                        "status": daemon_status.get("status"),
                        "cycle_count": daemon_status.get("cycle_count", 0),
                        "paused": daemon_status.get("paused", False)
                    }
                except Exception as e:
                    logger.debug(f"Could not get daemon status: {e}")
            
            # Feedback loop metrics (if available)
            if hasattr(self.reasoning_tool, 'daemon') and self.reasoning_tool.daemon:
                if hasattr(self.reasoning_tool.daemon, 'feedback_loop_manager') and self.reasoning_tool.daemon.feedback_loop_manager:
                    try:
                        metrics_summary = self.reasoning_tool.daemon.feedback_loop_manager.get_metrics_summary()
                        if metrics_summary.get("status") != "no_data":
                            reasoning_state["feedback_metrics"] = {
                                "success_rate": round(metrics_summary.get("success_rate", 0.0), 2),
                                "error_rate": round(metrics_summary.get("error_rate", 0.0), 2),
                                "avg_cycle_duration": round(metrics_summary.get("avg_cycle_duration", 0.0), 2)
                            }
                            
                            # Add cognitive dissonance metrics if available
                            if hasattr(self.reasoning_tool.daemon.feedback_loop_manager, 'cognitive_dissonance_monitor'):
                                dissonance_monitor = self.reasoning_tool.daemon.feedback_loop_manager.cognitive_dissonance_monitor
                                if dissonance_monitor:
                                    dissonance_data = dissonance_monitor.get_aggregated_dissonance()
                                    reasoning_state["cognitive_dissonance"] = {
                                        "overall": round(dissonance_data.get("overall_dissonance", 0.0), 3),
                                        "logical": round(dissonance_data.get("logical_dissonance", 0.0), 3),
                                        "factual": round(dissonance_data.get("factual_dissonance", 0.0), 3),
                                        "behavioral": round(dissonance_data.get("behavioral_dissonance", 0.0), 3),
                                        "goal": round(dissonance_data.get("goal_dissonance", 0.0), 3),
                                        "trend": dissonance_data.get("trend", 0.0)  # Positive = increasing
                                    }
                            
                            # Include learning system state if available (check daemon for learning_tool)
                            learning_tool = None
                            if hasattr(self.reasoning_tool, 'daemon') and self.reasoning_tool.daemon:
                                learning_tool = getattr(self.reasoning_tool.daemon, 'learning_tool', None)
                            if not learning_tool and hasattr(self.reasoning_tool, 'learning_tool'):
                                learning_tool = self.reasoning_tool.learning_tool
                            
                            if learning_tool:
                                try:
                                    learning_state = learning_tool.execute("get_learning_state")
                                    if learning_state.get("success"):
                                        reasoning_state["learning"] = {
                                            "procedures_count": learning_state.get("state", {}).get("procedural_learner", {}).get("total_procedures", 0),
                                            "skills_count": learning_state.get("state", {}).get("skill_manager", {}).get("total_skills", 0),
                                            "top_skills": learning_state.get("state", {}).get("skill_manager", {}).get("top_skills", [])[:3]  # Top 3
                                        }
                                except Exception as e:
                                    logger.debug(f"Could not get learning state: {e}")
                    except Exception as e:
                        logger.debug(f"Could not get feedback metrics: {e}")
            
            # Include emotional state if available from affect monitor
            if hasattr(self.reasoning_tool, 'affect_monitor') and self.reasoning_tool.affect_monitor:
                try:
                    emotional_state = self.reasoning_tool.affect_monitor.get_current_state()
                    regulation_needs = self.reasoning_tool.affect_monitor.get_emotional_regulation_needs()
                    
                    reasoning_state["emotion"] = {
                        "valence": round(emotional_state.get("valence", 0.0), 3),
                        "arousal": round(emotional_state.get("arousal", 0.5), 3),
                        "curiosity": round(emotional_state.get("curiosity_drive", 0.5), 3),
                        "needs_regulation": regulation_needs.get("needs_regulation", False),
                        "regulation_priority": round(regulation_needs.get("priority", 0.0), 2) if regulation_needs.get("needs_regulation") else None
                    }
                except Exception as e:
                    logger.debug(f"Could not get emotional state: {e}")
            # Also check daemon for affect monitor
            elif hasattr(self.reasoning_tool, 'daemon') and self.reasoning_tool.daemon and hasattr(self.reasoning_tool.daemon, 'affect_monitor') and self.reasoning_tool.daemon.affect_monitor:
                try:
                    emotional_state = self.reasoning_tool.daemon.affect_monitor.get_current_state()
                    regulation_needs = self.reasoning_tool.daemon.affect_monitor.get_emotional_regulation_needs()
                    
                    reasoning_state["emotion"] = {
                        "valence": round(emotional_state.get("valence", 0.0), 3),
                        "arousal": round(emotional_state.get("arousal", 0.5), 3),
                        "curiosity": round(emotional_state.get("curiosity_drive", 0.5), 3),
                        "needs_regulation": regulation_needs.get("needs_regulation", False),
                        "regulation_priority": round(regulation_needs.get("priority", 0.0), 2) if regulation_needs.get("needs_regulation") else None
                    }
                except Exception as e:
                    logger.debug(f"Could not get emotional state from daemon: {e}")
            
            # Add Z3 validation summary if available
            if hasattr(self.reasoning_tool, 'rule_engine') and self.reasoning_tool.rule_engine:
                if hasattr(self.reasoning_tool.rule_engine, 'z3_validator') and self.reasoning_tool.rule_engine.z3_validator:
                    try:
                        z3_summary = self.reasoning_tool.rule_engine.z3_validator.get_validation_summary(max_size_bytes=200)
                        if z3_summary:
                            reasoning_state["z3_validation"] = z3_summary
                    except Exception as e:
                        logger.debug(f"Could not get Z3 validation summary: {e}")
            
            # Limit total size to ~2KB (rough estimate: ~200 chars per goal, ~50 chars for other fields)
            # This is approximate - actual JSON serialization will vary
            total_size_estimate = len(str(reasoning_state))
            if total_size_estimate > 2000:
                # Truncate goals if too large
                if "active_goals" in reasoning_state:
                    reasoning_state["active_goals"] = reasoning_state["active_goals"][:3]
                    reasoning_state["_truncated"] = True
                # Remove Z3 validation if still too large (it's optional)
                if "z3_validation" in reasoning_state and total_size_estimate > 2000:
                    del reasoning_state["z3_validation"]
            
            return {
                "available": True,
                "reasoning": reasoning_state
            }
            
        except Exception as e:
            logger.warning(f"Error getting reasoning state: {e}", exc_info=True)
            return {"available": False, "error": str(e)}

