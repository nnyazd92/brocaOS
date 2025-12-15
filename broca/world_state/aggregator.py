"""
World state aggregator that collects data from various sources.

Aggregates information from internal sensing, self-model, project world state,
and system information into a unified world state object.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timezone
import logging
import platform
import os

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..internal_sensing.framework import InternalSensingFramework
    from ..self_model.model import SelfModel
    from ..tools.project_world_state import ProjectWorldStateTool
    from ..tools.registry import ToolRegistry


class WorldStateAggregator:
    """
    Aggregates world state from multiple sources.
    
    Collects data from:
    - Internal sensing framework (physiology, cognition, affect)
    - Self-model (capabilities, preferences, constraints)
    - Project world state (file structure, project info)
    - System information (date/time, platform)
    - Tool registry (available tools)
    """
    
    def __init__(
        self,
        internal_sensing: Optional["InternalSensingFramework"] = None,
        self_model: Optional["SelfModel"] = None,
        project_world_state_tool: Optional["ProjectWorldStateTool"] = None,
        tool_registry: Optional["ToolRegistry"] = None,
    ) -> None:
        """
        Initialize world state aggregator.
        
        Args:
            internal_sensing: Optional InternalSensingFramework instance
            self_model: Optional SelfModel instance
            project_world_state_tool: Optional ProjectWorldStateTool instance
            tool_registry: Optional ToolRegistry instance
        """
        self.internal_sensing = internal_sensing
        self.self_model = self_model
        self.project_world_state_tool = project_world_state_tool
        self.tool_registry = tool_registry
        
        logger.info("Initialized WorldStateAggregator")
    
    def aggregate(self) -> Dict[str, Any]:
        """
        Aggregate all available world state data into a clean hierarchical structure.
        
        Returns:
            Dictionary containing all aggregated world state information in a clean,
            hierarchical format. Always includes all sections, with null values when
            data is unavailable to ensure consistent structure.
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
        
        # Self-model - always include, null if unavailable
        self_model_state = self.get_self_model_state()
        if self_model_state.get("available"):
            world_state["self_model"] = {
                "summary": self_model_state.get("summary"),
                "capabilities": self_model_state.get("capabilities", []),
                "knowledge_boundaries": self_model_state.get("knowledge_boundaries", {}),
                "constraints": self_model_state.get("constraints", {}),
                "metadata": self_model_state.get("metadata", {}),
            }
        else:
            world_state["self_model"] = None
        
        # Internal sensing - always include, null if unavailable
        internal_sensing_state = self.get_internal_sensing_state()
        if internal_sensing_state.get("available"):
            current_state = internal_sensing_state.get("current_state", {})
            world_state["internal_state"] = {
                "interoceptive_report": internal_sensing_state.get("interoceptive_report"),
                "tool_statistics": internal_sensing_state.get("tool_statistics", {}),
                "behavioral_patterns": internal_sensing_state.get("behavioral_patterns", []),
            }
            # Add physiology, cognition, affect from current_state if available
            if current_state:
                if "physiology" in current_state:
                    world_state["internal_state"]["physiology"] = current_state["physiology"]
                if "cognition" in current_state:
                    world_state["internal_state"]["cognition"] = current_state["cognition"]
                if "affect" in current_state:
                    world_state["internal_state"]["affect"] = current_state["affect"]
        else:
            world_state["internal_state"] = None
        
        # Project state - always include, null if unavailable
        project_state = self.get_project_state()
        if project_state.get("available"):
            world_state["project"] = {
                "root": project_state.get("project_root"),
                "last_updated": project_state.get("last_updated"),
                "statistics": project_state.get("statistics", {}),
                "file_count": project_state.get("file_count", 0),
                "directory_count": project_state.get("directory_count", 0),
            }
        else:
            world_state["project"] = None
        
        # Tools - always include, null if unavailable
        tools_info = self.get_tools_info()
        if tools_info.get("available"):
            world_state["tools"] = {
                "count": tools_info.get("tool_count", 0),
                "names": tools_info.get("tool_names", []),
            }
        else:
            world_state["tools"] = None
        
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
            
            # Get behavioral patterns
            behavioral_patterns = self.internal_sensing.extract_behavioral_patterns()
            
            return {
                "available": True,
                "current_state": current_state,
                "interoceptive_report": interoceptive_report,
                "tool_statistics": tool_stats,
                "behavioral_patterns": behavioral_patterns,
            }
        except Exception as e:
            logger.warning(f"Error getting internal sensing state: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def get_self_model_state(self) -> Dict[str, Any]:
        """
        Get self-model state.
        
        Returns:
            Dictionary with self-model information
        """
        if not self.self_model:
            return {"available": False}
        
        try:
            # Get summary
            summary = self.self_model.get_summary()
            
            # Get detailed information
            return {
                "available": True,
                "summary": summary,
                "capabilities": self.self_model.capabilities,
                "knowledge_boundaries": self.self_model.knowledge_boundaries,
                "constraints": self.self_model.constraints,
                "metadata": self.self_model.metadata,
            }
        except Exception as e:
            logger.warning(f"Error getting self-model state: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def get_project_state(self) -> Dict[str, Any]:
        """
        Get project world state.
        
        Returns:
            Dictionary with project state information
        """
        if not self.project_world_state_tool:
            return {"available": False}
        
        try:
            # Get world state from tool
            world_state_result = self.project_world_state_tool.get_world_state()
            
            if not world_state_result.get("success"):
                return {
                    "available": False,
                    "error": world_state_result.get("error", "World state not built"),
                }
            
            # Extract key information
            return {
                "available": True,
                "project_root": world_state_result.get("project_root"),
                "last_updated": world_state_result.get("last_updated"),
                "statistics": world_state_result.get("statistics", {}),
                "file_count": len(world_state_result.get("files", [])),
                "directory_count": world_state_result.get("statistics", {}).get("total_directories", 0),
            }
        except Exception as e:
            logger.warning(f"Error getting project state: {e}", exc_info=True)
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
            Dictionary with tool information
        """
        if not self.tool_registry:
            return {"available": False}
        
        try:
            tools = self.tool_registry.list_tools()
            tool_names = [tool.name for tool in tools]
            
            return {
                "available": True,
                "tool_count": len(tools),
                "tool_names": tool_names,
            }
        except Exception as e:
            logger.warning(f"Error getting tools info: {e}", exc_info=True)
            return {"available": False, "error": str(e)}

