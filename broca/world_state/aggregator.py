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
        """
        self.internal_sensing = internal_sensing
        self.self_model = self_model
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.directory_structure_generator = directory_structure_generator
        self.self_model_reduction_level = self_model_reduction_level or "mild"
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
        
        # Self-model - only include if available
        self_model_state = self.get_self_model_state()
        if self_model_state.get("available"):
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
                "interoceptive_report": internal_sensing_state.get("interoceptive_report"),
                "tool_statistics": internal_sensing_state.get("tool_statistics", {}),
            }
            # Add physiology, cognition, affect from current_state if available
            if current_state:
                if "computational" in current_state:
                    world_state["internal_state"]["physiology"] = self._aggregate_physiology_health(current_state["computational"])
                if "cognition" in current_state:
                    world_state["internal_state"]["cognition"] = current_state["cognition"]
                if "affective" in current_state:
                    world_state["internal_state"]["affect"] = current_state["affective"]
        
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
        
        return world_state
    
    def get_internal_sensing_state(self) -> Dict[str, Any]:
        """
        Get internal sensing state.
        
        Returns:
            Dictionary with internal sensing information
        """
        if not self.internal_sensing:
            return {"available": False}
        
        try:
            # Sample current internal state
            current_state = self.internal_sensing.sample_internal_state()
            
            # Get interoceptive report
            interoceptive_report = self.internal_sensing.generate_interoceptive_report()
            
            # Get tool statistics
            tool_stats = self.internal_sensing.get_tool_statistics()
            
            return {
                "available": True,
                "current_state": current_state,
                "interoceptive_report": interoceptive_report,
                "tool_statistics": tool_stats,
            }
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
            
            # Apply reduction based on level
            if reduction_level == "none":
                # Full data with all source metadata (backward compatible)
                return {
                    "available": True,
                    "summary": summary,
                    "capabilities": self.self_model.capabilities,
                    "knowledge_boundaries": self.self_model.knowledge_boundaries,
                    "constraints": self.self_model.constraints,
                    "metadata": self.self_model.metadata,
                }
            elif reduction_level == "mild":
                # Remove source metadata, keep all fields
                return {
                    "available": True,
                    "summary": summary,
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
                }
            elif reduction_level == "moderate":
                # Replace each category with a brief sentence
                return {
                    "available": True,
                    "summary": summary,
                    "capabilities": self._summarize_capabilities_moderate(self.self_model.capabilities),
                    "knowledge_boundaries": self._summarize_knowledge_boundaries_moderate(self.self_model.knowledge_boundaries),
                    "constraints": self._summarize_constraints_moderate(self.self_model.constraints),
                    "metadata": {
                        "version": self.self_model.metadata.get("version"),
                        "last_updated": self.self_model.metadata.get("last_updated"),
                    },
                }
            elif reduction_level == "heavy":
                # Single sentence summary per field
                return {
                    "available": True,
                    "summary": summary,
                    "capabilities": self._summarize_capabilities_heavy(self.self_model.capabilities),
                    "knowledge_boundaries": self._summarize_knowledge_boundaries_heavy(self.self_model.knowledge_boundaries),
                    "constraints": self._summarize_constraints_heavy(self.self_model.constraints),
                }
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
                "note": "Use a file-listing tool to inspect the directory tree; never rely on stale tree."
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

