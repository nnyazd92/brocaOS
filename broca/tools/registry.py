"""
Tool registry for managing and executing LLM tools.

The registry maintains a collection of available tools and provides
methods to convert them to OpenAI function calling format and execute tool calls.

RL-Primary Tool Selection:
- OnlinePolicyRanker provides confidence-gated tool selection
- ≥85% confidence: RL forces tool selection (LLM bypassed)
- 30-85% confidence: RL suggests top-K tools (LLM picks from subset)
- <30% confidence: LLM has full choice (failsafe mode)
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, TYPE_CHECKING
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

if TYPE_CHECKING:
    from ..rl.online_policy import OnlinePolicyRanker, ToolSelection

logger = logging.getLogger(__name__)

# Import tool selection logger from rl module (uses same dedicated log file)
_tool_selection_logger = None

def _get_tool_selection_logger():
    """Get tool selection logger from RL module."""
    global _tool_selection_logger
    if _tool_selection_logger is None:
        try:
            from ..rl.tool_selection_logging import get_tool_selection_logger
            _tool_selection_logger = get_tool_selection_logger()
        except Exception:
            _tool_selection_logger = logger
    return _tool_selection_logger

# Lazy import to avoid circular dependency
ToolSelectionGuidance = None
_OnlinePolicyRanker = None

def _get_online_policy_ranker():
    """Lazy import OnlinePolicyRanker to avoid circular imports."""
    global _OnlinePolicyRanker
    if _OnlinePolicyRanker is None:
        try:
            from ..rl.online_policy import OnlinePolicyRanker
            _OnlinePolicyRanker = OnlinePolicyRanker
        except ImportError as e:
            logger.debug(f"OnlinePolicyRanker not available: {e}")
            _OnlinePolicyRanker = False  # Sentinel to avoid re-import
    return _OnlinePolicyRanker if _OnlinePolicyRanker is not False else None


class ToolRegistry:
    """
    Registry for managing and executing LLM tools.
    
    Maintains a collection of tools and provides methods to:
    - Register and retrieve tools
    - Convert tools to OpenAI function calling format
    - Execute tool calls from the LLM
    """
    
    def __init__(
        self,
        epistemic_engine: Optional[Any] = None,
        internal_sensing_framework: Optional["InternalSensingFramework"] = None,
        tool_selection_guidance: Optional[Any] = None,
        learning_tool: Optional[Any] = None,
        online_policy_ranker: Optional["OnlinePolicyRanker"] = None,
    ) -> None:
        """
        Initialize an empty tool registry.
        
        Args:
            epistemic_engine: Optional MetacognitiveEngine for epistemic tracking
            internal_sensing_framework: Optional InternalSensingFramework for tool usage tracking
            tool_selection_guidance: Optional ToolSelectionGuidance for intelligent tool selection
            learning_tool: Optional LearningTool for automatic learning observation
            online_policy_ranker: Optional OnlinePolicyRanker for RL-primary tool selection
        """
        self._tools: Dict[str, Tool] = {}
        self.epistemic_engine = epistemic_engine
        self.internal_sensing_framework = internal_sensing_framework
        self.tool_selection_guidance = tool_selection_guidance
        self.learning_tool = learning_tool
        self.online_policy_ranker = online_policy_ranker
        
        # Policy mode (read-only)
        # Read from env first (to support tests patching os.environ), fallback to config
        self._policy_mode = os.getenv("BROCA_TOOLS_MODE", getattr(config.tools, "tools_mode", "normal"))
        
        # Cache last RL selection for outcome recording
        self._last_rl_selection: Optional["ToolSelection"] = None
        self._last_rl_context: Optional[Dict[str, Any]] = None

        logger.debug("Initialized ToolRegistry")

    def start_turn(self, turn_no: int) -> None:
        """Reset per-turn counters at start of a new user turn."""
        # No-op: kept for API compatibility, but no counters to reset
        pass
    
    def set_learning_tool(self, learning_tool: Optional[Any]) -> None:
        """
        Set the learning tool for automatic observation.
        
        Args:
            learning_tool: LearningTool instance or None to disable
        """
        self.learning_tool = learning_tool
        if learning_tool:
            logger.debug("Learning tool set on ToolRegistry for automatic observation")
        else:
            logger.debug("Learning tool removed from ToolRegistry")
    
    def set_online_policy_ranker(self, ranker: Optional["OnlinePolicyRanker"]) -> None:
        """
        Set the online policy ranker for RL-primary tool selection.
        
        Args:
            ranker: OnlinePolicyRanker instance or None to disable
        """
        self.online_policy_ranker = ranker
        if ranker:
            logger.info("OnlinePolicyRanker set on ToolRegistry for RL-primary selection")
        else:
            logger.debug("OnlinePolicyRanker removed from ToolRegistry")
    
    def get_rl_selection(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional["ToolSelection"]:
        """
        Get RL-based tool selection with confidence-gated modes.
        
        Args:
            context: Optional context dictionary with rl_signals, active_goals, etc.
            
        Returns:
            ToolSelection with mode indicating how to proceed:
            - "forced": RL forces this tool (LLM should not choose)
            - "suggested": RL suggests top-K (LLM picks from subset)
            - "fallback": RL uncertain (LLM has full choice)
            - None if RL is disabled or not available
        """
        ts_logger = _get_tool_selection_logger()
        
        if not config.rl.enabled:
            ts_logger.debug("REGISTRY_RL | status=disabled | reason=config.rl.enabled=False")
            return None
            
        if self.online_policy_ranker is None:
            ts_logger.debug("REGISTRY_RL | status=unavailable | reason=no_policy_ranker")
            return None
        
        tools = self.list_tools()
        if not tools:
            ts_logger.debug("REGISTRY_RL | status=no_tools | reason=empty_tool_registry")
            return None
        
        ctx = context or {}
        tool_names = [t.name for t in tools]
        
        ts_logger.debug(
            f"REGISTRY_RL_START | n_tools={len(tools)} | tools={tool_names} | "
            f"context_keys={list(ctx.keys())}"
        )
        
        # Get RL selection
        selection = self.online_policy_ranker.select_tool(tools, ctx)
        
        # Cache for outcome recording
        self._last_rl_selection = selection
        self._last_rl_context = ctx
        
        ts_logger.info(
            f"REGISTRY_RL_RESULT | mode={selection.mode} | confidence={selection.confidence:.2%} | "
            f"selected_tool={selection.tool_name} | score={selection.score:.4f} | "
            f"n_alternatives={len(selection.alternatives)}"
        )
        
        return selection
    
    def record_rl_outcome(
        self,
        tool_name: str,
        success: bool,
        execution_time_ms: float = 0.0,
        result_quality: float = 0.5,
    ) -> None:
        """
        Record tool execution outcome for online RL learning.
        
        Args:
            tool_name: Name of executed tool
            success: Whether execution succeeded
            execution_time_ms: Execution time in milliseconds
            result_quality: Quality score of result (0.0-1.0)
        """
        if self.online_policy_ranker is None:
            return
        
        try:
            # Pre-tool context (what the ranker likely saw at selection time)
            pre_ctx = getattr(self, "_last_rl_context", None) or {}

            # Post-tool context (best-effort) to extract RL reward signals
            post_ctx = None
            rl_signals = None
            try:
                if (
                    getattr(self, "tool_selection_guidance", None) is not None
                    and getattr(self.tool_selection_guidance, "guidance_aggregator", None) is not None
                ):
                    post_ctx = self.tool_selection_guidance.guidance_aggregator.gather_context()
                    if isinstance(post_ctx, dict):
                        rl_signals = post_ctx.get("rl_signals") or None
            except Exception:
                post_ctx = None
                rl_signals = None

            self.online_policy_ranker.record_outcome(
                tool_name=tool_name,
                context=pre_ctx,
                next_context=post_ctx,
                success=success,
                execution_time_ms=execution_time_ms,
                result_quality=result_quality,
                # Reward is computed in the ranker from:
                # - intrinsic RL signals (subset) + extrinsic success/failure + latency penalty
                reward=None,
                rl_signals=rl_signals,
            )
        except Exception as e:
            logger.debug(f"Error recording RL outcome: {e}", exc_info=True)
    
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
    
    def to_openai_format(
        self,
        context: Optional[Dict[str, Any]] = None,
        rl_selection: Optional["ToolSelection"] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convert registered tools to OpenAI function calling format.

        Optionally filters and ranks tools based on context if tool selection
        guidance is enabled and available.
        
        RL-Primary Selection:
        - If rl_selection.mode == "forced": Returns only the forced tool
        - If rl_selection.mode == "suggested": Returns top-K suggested tools
        - If rl_selection.mode == "fallback" or None: Returns all tools

        Args:
            context: Optional context dictionary for tool filtering/ranking
            rl_selection: Optional RL selection result for filtering

        Returns:
            List of tool definitions in OpenAI format
        """
        ts_logger = _get_tool_selection_logger()
        
        # Get all tools
        all_tools = list(self._tools.values())
        original_tool_names = [t.name for t in all_tools]
        
        ts_logger.debug(
            f"OPENAI_FORMAT_START | n_tools={len(all_tools)} | "
            f"tools={original_tool_names} | "
            f"rl_selection_provided={rl_selection is not None}"
        )
        
        # RL-primary selection: filter tools based on RL mode
        rl_mode = None
        filtered_out = []
        if rl_selection is not None:
            rl_mode = rl_selection.mode
            
            if rl_mode == "forced":
                # RL forces a single tool - filter to only that tool
                forced_name = rl_selection.tool_name
                filtered_out = [t.name for t in all_tools if t.name != forced_name]
                all_tools = [t for t in all_tools if t.name == forced_name]
                
                ts_logger.info(
                    f"REGISTRY_FILTER | mode=forced | forced_tool={forced_name} | "
                    f"confidence={rl_selection.confidence:.2%} | "
                    f"tools_before={len(original_tool_names)} | tools_after={len(all_tools)} | "
                    f"filtered_out={filtered_out}"
                )
                
                logger.info(
                    f"RL forced tool selection: {forced_name} (confidence: {rl_selection.confidence:.1%})",
                    extra={
                        "event": "rl_forced_selection",
                        "tool_name": forced_name,
                        "confidence": rl_selection.confidence,
                    }
                )
            elif rl_mode == "suggested":
                # RL suggests top-K tools - filter to those tools
                suggested_names = {rl_selection.tool_name}
                for alt_name, _ in rl_selection.alternatives:
                    suggested_names.add(alt_name)
                filtered_out = [t.name for t in all_tools if t.name not in suggested_names]
                all_tools = [t for t in all_tools if t.name in suggested_names]
                
                ts_logger.info(
                    f"REGISTRY_FILTER | mode=suggested | suggested_tools={sorted(suggested_names)} | "
                    f"confidence={rl_selection.confidence:.2%} | "
                    f"tools_before={len(original_tool_names)} | tools_after={len(all_tools)} | "
                    f"filtered_out={filtered_out}"
                )
                
                logger.info(
                    f"RL suggested tools: {sorted(suggested_names)} (confidence: {rl_selection.confidence:.1%})",
                    extra={
                        "event": "rl_suggested_selection",
                        "tool_names": list(suggested_names),
                        "confidence": rl_selection.confidence,
                    }
                )
            else:
                # fallback mode - LLM has full choice
                ts_logger.info(
                    f"REGISTRY_FILTER | mode=fallback | confidence={rl_selection.confidence:.2%} | "
                    f"reason={rl_selection.reason} | "
                    f"tools_count={len(all_tools)} | LLM_has_full_choice=True"
                )
                
                logger.info(
                    f"RL fallback mode: LLM has full choice (confidence: {rl_selection.confidence:.1%})",
                    extra={
                        "event": "rl_fallback_selection",
                        "confidence": rl_selection.confidence,
                        "reason": rl_selection.reason,
                    }
                )
        else:
            ts_logger.debug(
                f"REGISTRY_FILTER | mode=none | reason=no_rl_selection | "
                f"tools_count={len(all_tools)}"
            )
        
        # Apply additional filtering/ranking if enabled and guidance is available
        # (This runs after RL selection, so it further refines the RL-filtered list)
        if (config.tools.pre_filtering_enabled and
            self.tool_selection_guidance is not None and
            rl_mode != "forced"):  # Don't further filter forced selections
            try:
                all_tools = self.tool_selection_guidance.filter_and_rank_tools(
                    all_tools, context=context
                )
                logger.debug(
                    f"Applied tool filtering/ranking: {len(all_tools)} tools",
                    extra={
                        "event": "tool_filtering_applied",
                        "tool_count": len(all_tools),
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Error applying tool filtering/ranking: {e}",
                    exc_info=True,
                    extra={"event": "tool_filtering_error"}
                )
                # Continue with unfiltered tools on error
        
        tools = []
        tool_names = []
        for tool in all_tools:
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
                "tool_names": tool_names,
                "rl_mode": rl_mode,
            }
        )
        
        # Log full tool schemas at DEBUG level or if configured
        # Use module-level config (imported at top of file)
        if config.logging.level == "DEBUG" or config.logging.log_tool_schemas:
            logger.debug(
                "Tool schemas",
                extra={
                    "event": "tool_schemas",
                    "tools": tools
                }
            )
        
        # Reorder tools using RL scores if we have them and not in forced mode
        if rl_selection is not None and rl_selection.all_scores and rl_mode != "forced":
            try:
                tools.sort(
                    key=lambda t: rl_selection.all_scores.get(t['function']['name'], 0.0),
                    reverse=True
                )
            except Exception:
                pass
        # Note: PolicyRanker fallback removed - OnlinePolicyRanker handles all RL-based
        # tool selection with dynamic action mapping from registered tools.

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

            ts_logger = _get_tool_selection_logger()
            ts_logger.info(
                f"TOOL_CALL_START | tool_call_id={tool_call_id} | tool={tool_name or 'unknown'}"
            )
            
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

            # Post-selection validation (if enabled)
            if (config.tools.post_validation_enabled and 
                self.tool_selection_guidance is not None):
                try:
                    # Gather context for validation
                    context = self.tool_selection_guidance.guidance_aggregator.gather_context()
                    
                    validation_result = self.tool_selection_guidance.validate_tool_selection(
                        tool_name, arguments, context=context
                    )
                    
                    # Check if tool should be blocked
                    if validation_result.blocked:
                        logger.warning(
                            f"Tool '{tool_name}' blocked by validation: {validation_result.severity}",
                            extra={
                                "event": "tool_validation_blocked",
                                "tool_name": tool_name,
                                "warnings": validation_result.warnings,
                                "alternatives": validation_result.alternatives,
                                "confidence": validation_result.confidence,
                                "severity": validation_result.severity,
                            }
                        )
                        
                        # Return blocking message with alternatives
                        alternatives_text = ""
                        if validation_result.alternatives:
                            alternatives_text = f"\n\nSuggested alternatives: {', '.join(validation_result.alternatives)}"
                        
                        warnings_text = "\n".join(f"- {w}" for w in validation_result.warnings)
                        
                        return {
                            "tool_call_id": tool_call_id,
                            "role": "tool",
                            "name": tool_name,
                            "content": (
                                f"Tool execution blocked by validation ({validation_result.severity}):\n"
                                f"{warnings_text}"
                                f"{alternatives_text}"
                            )
                        }
                    
                    # Log warnings if validation found issues but didn't block
                    if validation_result.warnings:
                        logger.warning(
                            f"Tool selection validation issues for '{tool_name}': "
                            f"{', '.join(validation_result.warnings)}",
                            extra={
                                "event": "tool_validation_warning",
                                "tool_name": tool_name,
                                "warnings": validation_result.warnings,
                                "suggestions": validation_result.suggestions,
                                "confidence": validation_result.confidence,
                                "severity": validation_result.severity,
                            }
                        )
                        
                        # Log suggestions if available
                        if validation_result.suggestions:
                            logger.info(
                                f"Tool selection suggestions for '{tool_name}': "
                                f"{', '.join(validation_result.suggestions)}"
                            )
                except Exception as e:
                    logger.debug(
                        f"Error in tool selection validation: {e}",
                        exc_info=True,
                        extra={"event": "tool_validation_error"}
                    )
                    # Continue with execution on validation error

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

                    # --- Instrumentation: append structured experience for RL ---
                    try:
                        from broca.rl.experiences import append_experience
                        import json
                        from pathlib import Path as _Path
                        from datetime import datetime as _dt

                        uid = hashlib.sha1(f"{tool_name}:{time.time()}".encode()).hexdigest()
                        # Best-effort snapshots for offline RL dataset building:
                        # - pre_context: what the ranker saw when selecting tools (if RL selection ran)
                        # - post_context: what the guidance system sees after the tool completes
                        pre_context = getattr(self, "_last_rl_context", None)
                        post_context = None
                        try:
                            if (
                                getattr(self, "tool_selection_guidance", None) is not None
                                and getattr(self.tool_selection_guidance, "guidance_aggregator", None) is not None
                            ):
                                post_context = self.tool_selection_guidance.guidance_aggregator.gather_context()
                        except Exception:
                            post_context = None

                        experience = {
                            "uid": uid,
                            "timestamp": _dt.utcnow().isoformat() + "Z",
                            "tool_call_id": tool_call_id,
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "result_summary": str(result)[:1000],
                            "success": (result.get("success", True) if isinstance(result, dict) else True),
                            "execution_time_ms": execution_time_ms,
                            "epistemic": None,
                            "provenance": None,
                            "pre_context": pre_context,
                            "post_context": post_context,
                        }

                        if epistemic_impact is not None and isinstance(epistemic_impact, dict):
                            experience["epistemic"] = {
                                "tool_reliability": epistemic_impact.get("confidence_metrics", {}).get("tool_reliability_score"),
                                "evidence_strength": epistemic_impact.get("confidence_metrics", {}).get("evidence_strength"),
                            }

                        try:
                            token_path = _Path("/home/wizard/Documents/Code/BrocaOS/.temporary_token.txt")
                            if token_path.exists():
                                token_json = json.loads(token_path.read_text(encoding="utf-8"))
                                experience["provenance"] = {"token_jti": token_json.get("payload", {}).get("jti"), "scopes": token_json.get("payload", {}).get("scopes")}
                        except Exception:
                            pass

                        append_experience(experience)
                    except Exception as e:
                        logger.debug(f"Failed to append experience for RL: {e}", exc_info=True)

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
            
            # Record tool outcome for feedback loop
            if self.tool_selection_guidance is not None:
                try:
                    # Determine success from result
                    success = result.get("success", True) if isinstance(result, dict) else True
                    self.tool_selection_guidance.record_tool_outcome(tool_name, success)
                except Exception as e:
                    logger.debug(f"Error recording tool outcome: {e}", exc_info=True)
            
            # Record outcome for RL online learning
            if self.online_policy_ranker is not None:
                try:
                    success = result.get("success", True) if isinstance(result, dict) else True
                    # Estimate result quality from epistemic impact if available
                    result_quality = 0.5
                    if epistemic_impact and "confidence_metrics" in epistemic_impact:
                        result_quality = epistemic_impact["confidence_metrics"].get("evidence_strength", 0.5)
                    
                    self.record_rl_outcome(
                        tool_name=tool_name,
                        success=success,
                        execution_time_ms=execution_time_ms,
                        result_quality=result_quality,
                    )
                except Exception as e:
                    logger.debug(f"Error recording RL outcome: {e}", exc_info=True)

            # Always log a per-call outcome line to the dedicated tool selection log.
            # This provides per-tool-call observability comparable to rl_rewards.csv.
            try:
                success = result.get("success", True) if isinstance(result, dict) else True
                result_quality = 0.5
                if epistemic_impact and "confidence_metrics" in epistemic_impact:
                    result_quality = epistemic_impact["confidence_metrics"].get("evidence_strength", 0.5)

                selection = getattr(self, "_last_rl_selection", None)
                selected_tool = getattr(selection, "tool_name", None) if selection is not None else None
                selected_mode = getattr(selection, "mode", None) if selection is not None else None
                selected_conf = getattr(selection, "confidence", None) if selection is not None else None
                matches_selected = (selected_tool == tool_name) if selected_tool else False
                selected_conf_str = (
                    f"{float(selected_conf):.4f}"
                    if isinstance(selected_conf, (int, float))
                    else "None"
                )

                rl_signals = None
                try:
                    if (
                        getattr(self, "tool_selection_guidance", None) is not None
                        and getattr(self.tool_selection_guidance, "guidance_aggregator", None) is not None
                    ):
                        post_ctx = self.tool_selection_guidance.guidance_aggregator.gather_context()
                        if isinstance(post_ctx, dict):
                            rl_signals = post_ctx.get("rl_signals") or None
                except Exception:
                    rl_signals = None

                ts_logger.info(
                    "TOOL_CALL_DONE | "
                    f"tool_call_id={tool_call_id} | tool={tool_name} | "
                    f"success={bool(success)} | execution_time_ms={execution_time_ms:.2f} | "
                    f"result_quality={float(result_quality):.3f} | "
                    f"rl_selected_tool={selected_tool} | rl_mode={selected_mode} | "
                    f"rl_confidence={selected_conf_str} | matches_selected={bool(matches_selected)} | "
                    f"rl_signals={rl_signals}"
                )
            except Exception:
                pass
            
            # Automatically observe tool call for learning if learning_tool is available
            # and runtime config allows auto-observation (to avoid unapproved persistent writes)
            try:
                auto_obs = getattr(config.tools, 'auto_observe_tool_calls', False)
            except Exception:
                auto_obs = False

            if self.learning_tool and auto_obs:
                try:
                    # Debounce: avoid observing too frequently for identical tool calls within same process tick
                    tool_call_data = {
                        "name": tool_name,
                        "parameters": arguments
                    }

                    success = result.get("success", True) if isinstance(result, dict) else True
                    result_data = {
                        "success": success,
                        "result": result,
                        "execution_time_ms": execution_time_ms
                    }

                    # Execute observation
                    self.learning_tool.execute("observe_tool_call", tool_call=tool_call_data, result=result_data)
                    logger.debug(f"Automatically observed tool call '{tool_name}' for learning (auto_obs enabled)")
                except Exception as e:
                    # Don't fail tool execution if learning observation fails
                    logger.debug(f"Failed to observe tool call for learning: {e}", exc_info=True)
            
            return result_dict
            
        except Exception as e:
            tool_name = tool_call.get("function", {}).get("name", "unknown")
            tool_call_id = tool_call.get("id", "")
            try:
                ts_logger = _get_tool_selection_logger()
                ts_logger.warning(
                    f"TOOL_CALL_ERROR | tool_call_id={tool_call_id} | tool={tool_name} | error={str(e)}"
                )
            except Exception:
                pass
            
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
