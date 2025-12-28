"""
Tool registry for managing and executing LLM tools.

The registry maintains a collection of available tools and provides
methods to convert them to OpenAI function calling format and execute tool calls.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import logging
import time
import hashlib

from . import Tool
from ..config import config
import os
from .logging_utils import (
    log_tool_call_received,
    log_tool_execution_start,
    log_tool_result
)
from .json_repair import attempt_json_repair

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing and executing LLM tools.
    
    Maintains a collection of tools and provides methods to:
    - Register and retrieve tools
    - Convert tools to OpenAI function calling format
    - Execute tool calls from the LLM
    """
    
    def __init__(self, epistemic_engine: Optional[Any] = None, internal_sensing_framework: Optional["InternalSensingFramework"] = None) -> None:
        """
        Initialize an empty tool registry.
        
        Args:
            epistemic_engine: Optional MetacognitiveEngine for epistemic tracking
        """
        self._tools: Dict[str, Tool] = {}
        self.epistemic_engine = epistemic_engine
        self.internal_sensing_framework = internal_sensing_framework
        # Policy mode (read-only)
        # Read from env first (to support tests patching os.environ), fallback to config
        self._policy_mode = os.getenv("BROCA_TOOLS_MODE", getattr(config.tools, "tools_mode", "normal"))

        logger.debug("Initialized ToolRegistry")

    def start_turn(self, turn_no: int) -> None:
        """Reset per-turn counters at start of a new user turn."""
        # No-op: kept for API compatibility, but no counters to reset
        pass
    
    def _validate_tool_arguments(self, tool: Tool, arguments: Dict[str, Any]) -> Optional[str]:
        """
        Validate that all required tool parameters are present.
        
        Args:
            tool: Tool instance to validate arguments for
            arguments: Parsed arguments dictionary
            
        Returns:
            None if valid, error message string if invalid
        """
        schema = tool.parameters
        required = schema.get("required", [])
        
        if not required:
            return None  # No required parameters, validation passes
        
        # Check for missing parameters (not present or None)
        missing = [
            param for param in required
            if param not in arguments or arguments[param] is None
        ]
        
        if missing:
            missing_str = ", ".join(missing)
            required_str = ", ".join(required)
            
            # Generate tool-specific error message with examples
            error_msg = self._generate_validation_error_message(
                tool.name, missing, required, arguments
            )
            
            return error_msg
        
        return None
    
    def _generate_validation_error_message(
        self,
        tool_name: str,
        missing: List[str],
        required: List[str],
        provided_arguments: Dict[str, Any]
    ) -> str:
        """
        Generate a helpful validation error message with examples.
        
        Args:
            tool_name: Name of the tool
            missing: List of missing required parameters
            required: List of all required parameters
            provided_arguments: Arguments that were provided
            
        Returns:
            Error message string with examples
        """
        missing_str = ", ".join(missing)
        required_str = ", ".join(required)
        
        # Base error message
        lines = [
            f"Missing required parameter(s): {missing_str}.",
            f"The tool '{tool_name}' requires the following parameters: {required_str}.",
            ""
        ]
        
        # Add tool-specific examples
        if tool_name == "terminal":
            lines.extend([
                "The 'command' parameter is REQUIRED and must be a non-empty string.",
                "",
                "Correct usage examples:",
                '  {"command": "python script.py"}',
                '  {"command": "python3 my_script.py"}',
                '  {"command": "ls -la"}',
                '  {"command": "echo hello", "working_dir": "/path/to/dir"}',
                '  {"command": "python script.py", "timeout": 60}',
                "",
                "To fix this error:",
                "1. Always include the 'command' parameter in your tool call",
                "2. The 'command' must be a non-empty string containing the command to execute",
                "3. For Python scripts, use: {\"command\": \"python script.py\"}",
                "",
                "Do NOT call the terminal tool with empty arguments {} or without the 'command' parameter."
            ])
        else:
            # Generic example for other tools
            example_dict = {param: f"<{param}_value>" for param in required}
            import json
            lines.extend([
                "Example format:",
                f"  {json.dumps(example_dict, indent=2)}",
                "",
                f"Please provide all required parameters: {required_str}"
            ])
        
        return "\n".join(lines)
    
    def _get_missing_parameters(self, tool: Tool, arguments: Dict[str, Any]) -> List[str]:
        """
        Get list of missing required parameters.
        
        Args:
            tool: Tool instance
            arguments: Parsed arguments dictionary
            
        Returns:
            List of missing parameter names
        """
        schema = tool.parameters
        required = schema.get("required", [])
        
        return [
            param for param in required
            if param not in arguments or arguments[param] is None
        ]
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Retrieve a tool by name.
        
        Args:
            name: Tool name to retrieve
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[Tool]:
        """
        List all registered tools.
        
        Returns:
            List of all registered tool instances
        """
        return list(self._tools.values())
    
    def get_registry_hash(self) -> str:
        """
        Compute hash of tool registry based on tool names.
        
        Returns:
            SHA256 hex digest of sorted tool names
        """
        tool_names = sorted(self._tools.keys())
        hash_obj = hashlib.sha256("|".join(tool_names).encode())
        return hash_obj.hexdigest()
    
    def get_registry_version(self) -> str:
        """
        Get version string from registry hash.
        
        Returns:
            Version string in format "v{first_8_chars_of_hash}"
        """
        hash_str = self.get_registry_hash()
        return f"v{hash_str[:8]}"
    
    def to_openai_format(self) -> List[Dict[str, Any]]:
        """
        Convert registered tools to OpenAI function calling format.
        
        Returns a list of tool definitions in the format expected by
        OpenAI-compatible APIs (DeepSeek, etc.).
        
        Returns:
            List of tool definitions in OpenAI format
        """
        tools = []
        tool_names = []
        for tool in self._tools.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
            tool_names.append(tool.name)
        
        logger.info(
            f"Converted {len(tools)} tools to OpenAI format",
            extra={
                "event": "tools_converted_to_openai_format",
                "tool_count": len(tools),
                "tool_names": tool_names
            }
        )
        
        # Log full tool schemas at DEBUG level or if configured
        from ..config import config
        if config.logging.level == "DEBUG" or config.logging.log_tool_schemas:
            logger.debug(
                "Tool schemas",
                extra={
                    "event": "tool_schemas",
                    "tools": tools
                }
            )
        
        return tools
    
    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call from the LLM.
        
        Args:
            tool_call: Tool call dictionary from LLM response, containing:
                - "id": tool call ID
                - "type": "function"
                - "function": {
                    - "name": tool name
                    - "arguments": JSON string of arguments
                }
        
        Returns:
            Dictionary containing:
                - "tool_call_id": ID of the tool call
                - "role": "tool"
                - "name": tool name
                - "content": formatted result string
            Or error information if execution fails
        """
        import json
        
        # Log tool call received
        log_tool_call_received(tool_call, logger)
        
        try:
            function_info = tool_call.get("function", {})
            tool_name = function_info.get("name")
            arguments_str = function_info.get("arguments", "{}")
            tool_call_id = tool_call.get("id", "")
            
            if not tool_name:
                raise ValueError("Tool call missing 'function.name'")
            
            tool = self.get_tool(tool_name)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found in registry")
            
            # Parse arguments JSON string with repair attempts
            arguments, parse_error = attempt_json_repair(arguments_str) if arguments_str else ({}, None)
            
            if parse_error is not None:
                # Return detailed error to LLM instead of raising exception
                logger.warning(
                    f"Failed to parse tool arguments JSON: {parse_error[:200]}",
                    extra={
                        "event": "tool_argument_json_parse_failed",
                        "tool_name": tool_name,
                        "tool_call_id": tool_call_id,
                        "arguments_preview": arguments_str[:200] if arguments_str else ""
                    }
                )
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": f"JSON Parsing Error: {parse_error}\n\nPlease fix the JSON format and try again."
                }
            
            if arguments is None:
                arguments = {}

            # Enforce read-only policy and web search limits
            if self._policy_mode == "read_only":
                readonly_blocked = {"store_memory", "update_memory", "delete_memory", "link_memories"}
                if tool_name in readonly_blocked:
                    return {
                        "tool_call_id": tool_call_id,
                        "role": "tool",
                        "name": tool_name,
                        "content": "Blocked by read-only policy: memory write tools are disabled."
                    }
                if tool_name == "terminal":
                    return {
                        "tool_call_id": tool_call_id,
                        "role": "tool",
                        "name": tool_name,
                        "content": "Blocked by read-only policy: terminal is disabled."
                    }
            
            # Validate required parameters
            validation_error = self._validate_tool_arguments(tool, arguments)
            if validation_error:
                missing_params = self._get_missing_parameters(tool, arguments)
                provided_params = list(arguments.keys())
                
                # Enhanced diagnostic logging
                logger.warning(
                    f"Tool argument validation failed: {validation_error}",
                    extra={
                        "event": "tool_argument_validation_failed",
                        "tool_name": tool_name,
                        "tool_call_id": tool_call_id,
                        "missing_parameters": missing_params,
                        "provided_arguments": provided_params,
                        "arguments_preview": str(arguments)[:200] if arguments else "{}",
                        "arguments_count": len(arguments),
                        "required_parameters": tool.parameters.get("required", []),
                    }
                )
                
                # Return error message to LLM instead of raising exception
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": f"Error: {validation_error}\n\nPlease provide all required parameters and try again."
                }
            
            # Log execution start
            log_tool_execution_start(tool_name, arguments, tool_call_id, logger)
            
            # Execute tool with timing
            start_time = time.time()
            result = tool.execute(**arguments)
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Track epistemic metadata if engine available
            epistemic_impact = None
            if self.epistemic_engine:
                try:
                    from broca.self_model.epistemic.models import SourceType, SourceMetadata
                    from broca.self_model.epistemic.ids import generate_knowledge_id
                    from datetime import datetime, timezone
                    
                    # Determine if execution was successful
                    success = result.get("success", True) if isinstance(result, dict) else True
                    
                    # Create source metadata for tool execution
                    source_metadata = SourceMetadata(
                        source_type=SourceType.TOOL_MEDIATED_VERIFICATION,
                        tool_type=tool_name,
                        verification_method="direct_execution",
                        timestamp=datetime.now(timezone.utc),
                        success_metrics={
                            "success": success,
                            "execution_time_ms": execution_time_ms
                        }
                    )
                    
                    # Calculate confidence based on tool reliability (assess BEFORE recording current execution)
                    # This uses historical reliability to assess confidence in the current execution
                    tool_reliability = None
                    if hasattr(self.epistemic_engine, 'validator'):
                        tool_reliability = self.epistemic_engine.validator.assess_tool_reliability(tool_name)
                        if success:
                            # For successful executions, use tool reliability directly
                            evidence_strength = tool_reliability
                        else:
                            # For failed executions, scale down reliability
                            evidence_strength = tool_reliability * 0.3
                    else:
                        # Fallback if validator doesn't exist
                        tool_reliability = 0.5  # Default when no validator
                        evidence_strength = 0.9 if success else 0.3
                    
                    # Record tool execution in validator (after assessing, so current execution affects next time)
                    if hasattr(self.epistemic_engine, 'validator'):
                        self.epistemic_engine.validator.record_tool_execution(tool_name, success)
                    
                    # Track tool result as knowledge if it provides information
                    # Only track for tools that provide new information (not errors)
                    if success and isinstance(result, dict) and result.get("success", True):
                        try:
                            # Generate knowledge ID for tool result
                            # Use tool name and a hash of the result content
                            result_summary = str(result)[:200]  # Truncate for ID generation
                            knowledge_id = generate_knowledge_id(
                                "tool_result",
                                f"{tool_name}:{result_summary}"
                            )
                            
                            # Track as knowledge acquisition
                            self.epistemic_engine.knowledge_acquisition_workflow(
                                knowledge_id=knowledge_id,
                                source=source_metadata,
                                initial_confidence=evidence_strength
                            )
                        except Exception as e:
                            logger.debug(f"Error tracking tool result as knowledge: {e}", exc_info=True)
                    
                    epistemic_impact = {
                        "source_metadata": source_metadata,
                        "confidence_metrics": {
                            "tool_reliability_score": tool_reliability if tool_reliability is not None else (self.epistemic_engine.validator.assess_tool_reliability(tool_name) if hasattr(self.epistemic_engine, 'validator') else 0.5),
                            "execution_success": success,
                            "evidence_strength": evidence_strength
                        },
                        "suggested_verification": []  # Could suggest cross-tool verification
                    }
                except Exception as e:
                    logger.warning(f"Error tracking epistemic metadata for tool execution: {e}", exc_info=True)
            
            # Check if result indicates failure and include stderr if available
            if isinstance(result, dict) and not result.get("success", True) and result.get("stderr"):
                # Tool failed and has stderr - ensure it's visible in formatted result
                formatted_result = tool.format_result(result)
                # If stderr not already in formatted result, append it
                if "stderr" in result and result["stderr"] and result["stderr"] not in formatted_result:
                    formatted_result += f"\n\nStderr output:\n{result['stderr']}"
            else:
                # Format result for LLM
                formatted_result = tool.format_result(result)
            

            # Record usage in internal sensing framework
            if self.internal_sensing_framework:
                try:
                    self.internal_sensing_framework.record_tool_usage(tool_name, arguments, result)
                    # Estimate impact based on tool type
                    impact = 2 if tool_name in ('terminal', 'web_search') else 1
                    self.internal_sensing_framework.record_cognitive_impact(tool_name, impact)

                    # Record informational surprise (expectation vs reality)
                    # Expectation is the tool name + arguments, reality is the result
                    expectation = f'{tool_name} {str(arguments)}'
                    reality = str(result)
                    self.internal_sensing_framework.record_informational_surprise(expectation, reality)

                except Exception as e:
                    logger.debug(f'Error recording tool usage in sensing framework: {e}')

            # Log result
            log_tool_result(
                tool_name,
                result,
                formatted_result,
                tool_call_id,
                execution_time_ms,
                logger
            )
            
            result_dict = {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": tool_name,
                "content": formatted_result
            }
            
            # Include success field from raw result for proper success detection
            # Always set _success as a boolean to ensure consistent success detection
            if isinstance(result, dict) and "success" in result:
                result_dict["_success"] = bool(result.get("success", True))
            
            # Include epistemic impact if available
            if epistemic_impact:
                result_dict["_epistemic_impact"] = {
                    "confidence_metrics": epistemic_impact["confidence_metrics"],
                    "suggested_verification": epistemic_impact["suggested_verification"]
                }
            
            return result_dict
            
        except Exception as e:
            tool_name = tool_call.get("function", {}).get("name", "unknown")
            tool_call_id = tool_call.get("id", "")
            
            # Try to extract stderr from the exception if it's a tool execution error
            error_msg_parts = [f"Error executing tool '{tool_name}': {str(e)}"]
            
            # Check if exception has stderr attribute (from tool execution)
            if hasattr(e, 'stderr') and e.stderr:
                error_msg_parts.append(f"\n\nStderr output:\n{e.stderr}")
            
            # Check if exception has result with stderr (from tool that returned error dict)
            if hasattr(e, 'result') and isinstance(e.result, dict):
                if 'stderr' in e.result and e.result['stderr']:
                    error_msg_parts.append(f"\n\nStderr output:\n{e.result['stderr']}")
            
            error_content = "\n".join(error_msg_parts)
            
            logger.error(
                f"Error executing tool call: {e}",
                exc_info=True,
                extra={
                    "event": "tool_call_error",
                    "tool_name": tool_name,
                    "tool_call_id": tool_call_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            # Return error information in a format the LLM can understand
            return {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": tool_name,
                "content": error_content
            }

