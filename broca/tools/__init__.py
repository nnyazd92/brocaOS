"""
Tool abstraction for LLM tool usage.

This module defines the Tool protocol that all tools must implement.
This allows the LLM to use various tools like web search, calculators, etc.
"""

from __future__ import annotations

from typing import Protocol, Dict, Any


class Tool(Protocol):
    """
    Protocol defining the interface for LLM tools.
    
    All tool implementations must conform to this interface to ensure
    compatibility with the tool registry and LLM integration.
    """
    
    @property
    def name(self) -> str:
        """
        Unique identifier for the tool.
        
        Returns:
            Tool name (e.g., "web_search", "calculator")
        """
        ...
    
    @property
    def description(self) -> str:
        """
        Human-readable description of what the tool does.
        
        This description is provided to the LLM to help it decide when to use the tool.
        
        Returns:
            Tool description
        """
        ...
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """
        JSON schema defining the tool's parameters.
        
        Must conform to JSON Schema format for OpenAI function calling.
        
        Returns:
            Dictionary containing parameter schema (type, properties, required, etc.)
        """
        ...
    
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Tool parameters as specified in the parameters schema
            
        Returns:
            Dictionary containing tool execution results
        """
        ...
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for LLM consumption.
        
        Converts the structured result dictionary into a readable text format
        that the LLM can understand and use in its response.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation of the result
        """
        ...

