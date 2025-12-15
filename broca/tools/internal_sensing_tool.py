"""
Internal sensing tools for LLM introspection.

Provides tools for the LLM to query its internal state and get interoceptive reports.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from . import Tool
from ..internal_sensing.framework import InternalSensingFramework

logger = logging.getLogger(__name__)


class QueryInternalStateTool:
    """
    Tool for querying current internal state.
    
    Allows the LLM to introspect its internal sensing data.
    """
    
    def __init__(self, framework: InternalSensingFramework) -> None:
        """
        Initialize the query internal state tool.
        
        Args:
            framework: InternalSensingFramework instance
        """
        self.framework = framework
        logger.info("Initialized QueryInternalStateTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "query_internal_state"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Query your current internal state including computational, cognitive, "
            "and affective states. Use this tool when you need to understand your "
            "current internal condition or check your internal sensing data."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "aspect": {
                    "type": "string",
                    "enum": ["all", "computational", "cognitive", "affective", "predictive"],
                    "description": "Which aspect of internal state to query (default: 'all')",
                    "default": "all"
                }
            },
            "required": []
        }
    
    def execute(self, aspect: str = "all") -> Dict[str, Any]:
        """
        Execute internal state query.
        
        Args:
            aspect: Which aspect to query
            
        Returns:
            Dictionary with internal state information
        """
        try:
            state = self.framework.sample_internal_state()
            
            if aspect == "all":
                return {
                    "success": True,
                    "state": state,
                }
            elif aspect in ["computational", "cognitive", "affective", "predictive"]:
                return {
                    "success": True,
                    "aspect": aspect,
                    "state": state.get(aspect, {}),
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown aspect: {aspect}",
                }
                
        except Exception as e:
            logger.error(f"Error querying internal state: {e}", exc_info=True)
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
            return f"Error querying internal state: {result.get('error', 'Unknown error')}"
        
        state = result.get("state", {})
        if not state:
            return "No internal state data available."
        
        if "aspect" in result:
            aspect = result["aspect"]
            aspect_data = state
            return f"Internal state ({aspect}): {aspect_data}"
        else:
            return f"Internal state: {state}"


class GetInteroceptiveReportTool:
    """
    Tool for getting interoceptive reports.
    
    Allows the LLM to get natural language descriptions of its internal state.
    """
    
    def __init__(self, framework: InternalSensingFramework) -> None:
        """
        Initialize the get interoceptive report tool.
        
        Args:
            framework: InternalSensingFramework instance
        """
        self.framework = framework
        logger.info("Initialized GetInteroceptiveReportTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "get_interoceptive_report"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Get a natural language report describing your current internal state. "
            "This includes computational resources, cognitive states, affective states, "
            "and predictions. Use this tool when you need to understand or communicate "
            "your internal condition."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute interoceptive report generation.
        
        Returns:
            Dictionary with report
        """
        try:
            report = self.framework.generate_interoceptive_report()
            
            return {
                "success": True,
                "report": report,
            }
            
        except Exception as e:
            logger.error(f"Error generating interoceptive report: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format report result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            return f"Error generating report: {result.get('error', 'Unknown error')}"
        
        return result.get("report", "No report available.")

