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
import itertools
import shlex

from . import Tool
from ..config import config
import os
from .logging_utils import (
    log_tool_call_received,
    log_tool_execution_start,
    log_tool_result
)
from .json_repair import attempt_json_repair
from ..veto import get_veto_guard
from ..veto.veto_logger import get_veto_csv_logger

if TYPE_CHECKING:
    from ..rl.online_policy import OnlinePolicyRanker, ToolSelection

logger = logging.getLogger(__name__)

# Hard limit for how many times the model can attempt a non-whitelisted EXECUTE
# in a single user turn before we stop accepting further noncompliant EXECUTE calls.
_EXECUTE_WHITELIST_RETRY_LIMIT = 3


def _extract_base_command(cmd: Any) -> str:
    """
    Best-effort extraction of the "base command" from a shell command string.

    Matches `ExecuteTool` behavior: skips leading env var assignments like FOO=bar.
    """
    if not isinstance(cmd, str):
        return ""
    cmd_s = cmd.strip()
    if not cmd_s:
        return ""
    try:
        parts = shlex.split(cmd_s)
        for part in parts:
            if (
                "=" in part
                and not part.startswith(("./", "/"))
                and part.split("=", 1)[0].isidentifier()
            ):
                continue
            return part
    except Exception:
        pass
    parts2 = cmd_s.split()
    return parts2[0] if parts2 else ""

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

        # Governance policy (capability gating / scopes / budgets / audit)
        self._governance_engine = None
        try:
            from ..governance.policy import GovernanceEngine

            self._governance_engine = GovernanceEngine()
        except Exception:
            self._governance_engine = None
        
        # Cache last RL selection for outcome recording
        self._last_rl_selection: Optional["ToolSelection"] = None
        self._last_rl_context: Optional[Dict[str, Any]] = None

        # Correlate the last selection used to build the OpenAI tool list with subsequent tool calls.
        # This is critical for observability in the web API where multiple tool calls can occur.
        self._selection_seq = itertools.count(1)
        self._last_format_selection_id: Optional[int] = None
        self._last_format_selection_ts: Optional[float] = None
        self._last_format_selection: Optional["ToolSelection"] = None
        self._last_format_suggested_tools: List[str] = []
        self._last_format_allowed_tools: List[str] = []

        # Sticky forced-exploration:
        # When PPO triggers a forced exploration selection, we must keep returning the same forced tool
        # until it is actually executed, otherwise a noncompliant tool call can cause the next iteration
        # to recompute selection and fall back -> PPO_SKIP.
        self._sticky_forced_selection: Optional["ToolSelection"] = None
        self._sticky_forced_context: Optional[Dict[str, Any]] = None
        self._sticky_forced_tool: Optional[str] = None
        self._sticky_forced_blocks: int = 0

        # DONE macro: once called, tools are disabled for the remainder of the current user turn
        # so the next LLM iteration is forced to produce a natural-language answer.
        self._force_final_response: bool = False

        # Per-user-turn safety counters (reset by start_turn()).
        self._turn_no: Optional[int] = None
        self._execute_whitelist_block_count: int = 0
        self._execute_whitelist_block_by_base: Dict[str, int] = {}
        self._consecutive_veto_count: int = 0

        logger.debug("Initialized ToolRegistry")

    def start_turn(self, turn_no: int) -> None:
        """Reset per-turn counters at start of a new user turn."""
        self._turn_no = int(turn_no) if isinstance(turn_no, int) else None
        self._execute_whitelist_block_count = 0
        self._execute_whitelist_block_by_base = {}
        self._consecutive_veto_count = 0
        # Reset per-turn sticky forced exploration to avoid cross-turn action-space collapse.
        self._sticky_forced_selection = None
        self._sticky_forced_context = None
        self._sticky_forced_tool = None
        self._sticky_forced_blocks = 0
        # Reset DONE latch for new user turn.
        self._force_final_response = False

    @property
    def force_final_response(self) -> bool:
        return bool(self._force_final_response)
    
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

        # If DONE was called, we intentionally disable tools and let the model answer.
        if self._force_final_response:
            ts_logger.info("REGISTRY_RL | status=disabled | reason=force_final_response")
            return None
        
        if not config.rl.enabled:
            ts_logger.debug("REGISTRY_RL | status=disabled | reason=config.rl.enabled=False")
            return None
            
        if self.online_policy_ranker is None:
            ts_logger.debug("REGISTRY_RL | status=unavailable | reason=no_policy_ranker")
            return None
        
        tools = self._visible_tools()
        if not tools:
            ts_logger.debug("REGISTRY_RL | status=no_tools | reason=empty_tool_registry")
            return None
        
        ctx = context or {}
        tool_names = [t.name for t in tools]

        # Sticky forced exploration: if active, keep returning it until the forced tool is executed.
        if (
            self._sticky_forced_selection is not None
            and isinstance(self._sticky_forced_tool, str)
            and self._sticky_forced_tool
        ):
            ts_logger.info(
                f"REGISTRY_RL_STICKY | mode=forced | forced_tool={self._sticky_forced_tool} | "
                f"blocks={int(self._sticky_forced_blocks)} | reason=sticky_forced_exploration"
            )
            self._last_rl_selection = self._sticky_forced_selection
            self._last_rl_context = (self._sticky_forced_context or ctx) if isinstance(self._sticky_forced_context, dict) else ctx
            return self._sticky_forced_selection

        ts_logger.debug(
            f"REGISTRY_RL_START | n_tools={len(tools)} | tools={tool_names} | "
            f"context_keys={list(ctx.keys())}"
        )
        
        # Get RL selection
        selection = self.online_policy_ranker.select_tool(tools, ctx)
        
        # Cache for outcome recording
        self._last_rl_selection = selection
        self._last_rl_context = ctx

        # Activate sticky forced exploration if applicable.
        try:
            if (
                getattr(selection, "mode", None) == "forced"
                and isinstance(getattr(selection, "tool_name", None), str)
                and "Forced exploration" in str(getattr(selection, "reason", "") or "")
            ):
                self._sticky_forced_selection = selection
                self._sticky_forced_context = ctx
                self._sticky_forced_tool = selection.tool_name
                self._sticky_forced_blocks = 0
                ts_logger.info(
                    f"REGISTRY_RL_STICKY_ARM | forced_tool={self._sticky_forced_tool} | reason=forced_exploration"
                )
        except Exception:
            pass
        
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
        tool_arguments: Optional[Dict[str, Any]] = None,
        tool_result_text: Optional[str] = None,
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

            # Attach post-action text features so next_state can condition on tool args/results.
            if isinstance(post_ctx, dict):
                tf = post_ctx.get("text_features")
                if not isinstance(tf, dict):
                    tf = {}
                try:
                    tf["tool_args"] = json.dumps(tool_arguments, ensure_ascii=False) if isinstance(tool_arguments, dict) else ""
                except Exception:
                    tf["tool_args"] = ""
                try:
                    # Keep short to avoid accidental prompt bloat.
                    tf["tool_result"] = (tool_result_text or "")[:2000]
                except Exception:
                    tf["tool_result"] = ""
                post_ctx["text_features"] = tf

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

            # Clear sticky forced-exploration once the forced tool is actually executed.
            try:
                forced_tool = self._sticky_forced_tool
                if (
                    self._sticky_forced_selection is not None
                    and isinstance(forced_tool, str)
                    and forced_tool
                    and tool_name == forced_tool
                ):
                    ts_logger = _get_tool_selection_logger()
                    ts_logger.info(
                        f"REGISTRY_RL_STICKY_CLEAR | forced_tool={forced_tool} | "
                        f"blocks={int(self._sticky_forced_blocks)} | reason=forced_tool_executed"
                    )
                    self._sticky_forced_selection = None
                    self._sticky_forced_context = None
                    self._sticky_forced_tool = None
                    self._sticky_forced_blocks = 0
            except Exception:
                pass
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
        elif tool_name == "EXECUTE":
            lines.extend([
                "The 'cmd' parameter is REQUIRED and must be a non-empty string.",
                "",
                "Correct usage examples:",
                '  {"cmd": "pytest -q"}',
                '  {"cmd": "python -m pip --version"}',
                '  {"cmd": "python -c \\"print(123)\\""}',
                '  {"cmd": "rg \\"ToolRegistry\\" -n broca", "cwd": "."}',
                '  {"cmd": "python -m pytest -q", "timeout": 120, "env_allowlist": ["PATH", "HOME"]}',
                "",
                "To fix this error:",
                "1. Always include the 'cmd' parameter in your tool call",
                "2. The 'cmd' must be a non-empty string containing the command to execute",
                "3. If you need a working directory, supply 'cwd'",
                "",
                "Do NOT call EXECUTE with empty arguments {} or without the 'cmd' parameter."
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
        schema = self._tool_parameters(tool)
        required = schema.get("required", [])
        
        return [
            param for param in required
            if param not in arguments or arguments[param] is None
        ]

    @staticmethod
    def _tool_attr_value(tool: Tool, attr: str) -> Any:
        """
        Robustly fetch tool attributes that may be defined as @property or as a method.
        """
        try:
            v = getattr(tool, attr)
        except Exception:
            return None
        try:
            if callable(v):
                return v()
        except Exception:
            return None
        return v

    def _tool_name(self, tool: Tool) -> str:
        v = self._tool_attr_value(tool, "name")
        if isinstance(v, str) and v.strip():
            return v.strip()
        # Avoid inserting method objects as keys; always coerce.
        return str(v) if v is not None else ""

    def _tool_description(self, tool: Tool) -> str:
        v = self._tool_attr_value(tool, "description")
        if isinstance(v, str):
            return v
        return str(v) if v is not None else ""

    def _tool_parameters(self, tool: Tool) -> Dict[str, Any]:
        v = self._tool_attr_value(tool, "parameters")
        if isinstance(v, dict):
            return v
        # Defensive fallback: always return a valid (empty) schema dict.
        return {"type": "object", "properties": {}, "required": []}
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ValueError: If a tool with the same name is already registered
        """
        name = self._tool_name(tool)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Tool has invalid name (must be non-empty string)")
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        self._tools[name] = tool
        logger.info(f"Registered tool: {name}")
    
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

    def _primitive_allowed_tool_names(self) -> set[str]:
        """
        Allowed tool names for the primitive (macro) toolset.

        This is the intended RL/agent action space: explicit, typed macros only.
        """
        return {
            # Core I/O
            "READ_FILE",
            "WRITE_FILE",
            "APPEND_FILE",
            "PATCH_FILE",
            "LIST_DIR",
            "STAT_PATH",
            "EXECUTE",
            # Web
            "WEB_SEARCH",
            "WEB_FETCH",
            # Cognition (pure)
            "PLAN",
            "CRITIC",
            "SOLVE",
            "VERIFY",
            "INTERPRET",
            "DONE",
            "RESPOND_AND_CONTINUE",
            # Memory / self-model (versioned)
            "MEMORY_PUT",
            "MEMORY_GET",
            "MEMORY_LINK",
            "MEMORY_DELETE",
            "MEMORY_UPDATE",
            "MEMORY_RELATED",
            "SELF_MODEL_GET",
            "SELF_MODEL_UPDATE",
            "SELF_MODEL_ARCHIVE",
            # Learning / Goals (mutating only via explicit steps)
            "SET_GOALS",
            "DESIGN_REWARD",
            # Governance policy tools (declarative gating + audit)
            "GET_POLICY",
            "SET_POLICY",
            "REQUEST_POLICY_CHANGE",
            "COMMIT_APPROVAL",
            "EVALUATE_ACTION",
            "GET_AUDIT_LOG",
            # Operator-only RL debug tools (registered conditionally)
            "UPDATE_POLICY",
            "EVALUATE_POLICY",
            "PROMOTE_POLICY",
            "ROLLBACK_POLICY",
        }

    def _is_tool_visible(self, tool_name: str) -> bool:
        # Read from env first (supports runtime overrides + tests patching os.environ), fallback to config.
        toolset = str(os.getenv("BROCA_TOOLSET", getattr(config.tools, "toolset", "primitive")) or "primitive").lower()
        if toolset != "primitive":
            return True
        return tool_name in self._primitive_allowed_tool_names()

    def _visible_tools(self) -> List[Tool]:
        # Use normalized registry keys for visibility filtering (avoid calling t.name which may be misdefined).
        out: List[Tool] = []
        for name, t in self._tools.items():
            try:
                if self._is_tool_visible(str(name)):
                    out.append(t)
            except Exception:
                continue
        return out
    
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

        # DONE macro: once called, disable all tools for the remainder of this user turn so the
        # next LLM iteration produces a natural-language answer.
        if self._force_final_response:
            try:
                self._last_format_selection_id = int(next(self._selection_seq))
                self._last_format_selection_ts = time.time()
            except Exception:
                self._last_format_selection_id = None
                self._last_format_selection_ts = None
            self._last_format_selection = None
            self._last_format_suggested_tools = []
            self._last_format_allowed_tools = []
            try:
                ts_logger.info(
                    f"AVAILABLE_TOOL_BUFFER | selection_id={self._last_format_selection_id} | "
                    f"mode=none | n_allowed=0 | allowed_tools=[] | reason=force_final_response"
                )
            except Exception:
                pass
            return []
        
        # Get visible tools (toolset policy)
        all_tools = self._visible_tools()
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
            try:
                self._last_format_selection_id = int(next(self._selection_seq))
                self._last_format_selection_ts = time.time()
                self._last_format_selection = rl_selection
                sug = [getattr(rl_selection, "tool_name", None)]
                for alt_name, _ in (getattr(rl_selection, "alternatives", None) or []):
                    sug.append(alt_name)
                self._last_format_suggested_tools = [s for s in sug if isinstance(s, str) and s]
            except Exception:
                self._last_format_selection_id = None
                self._last_format_selection_ts = None
                self._last_format_selection = rl_selection
                self._last_format_suggested_tools = []

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
                    f"filtered_out={filtered_out} | selection_id={self._last_format_selection_id}"
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
                    f"filtered_out={filtered_out} | selection_id={self._last_format_selection_id}"
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
                    f"tools_count={len(all_tools)} | LLM_has_full_choice=True | selection_id={self._last_format_selection_id}"
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

        # Persist the *allowed* tool names for this formatting pass so we can enforce
        # forced-mode even if the LLM/provider emits an out-of-schema tool call.
        try:
            self._last_format_allowed_tools = [self._tool_name(t) for t in all_tools]
        except Exception:
            self._last_format_allowed_tools = []

        # Explicit "available tool buffer" visibility.
        try:
            ts_logger.info(
                f"AVAILABLE_TOOL_BUFFER | selection_id={self._last_format_selection_id} | "
                f"mode={rl_mode or 'none'} | n_allowed={len(self._last_format_allowed_tools)} | "
                f"allowed_tools={list(self._last_format_allowed_tools)}"
            )
        except Exception:
            pass

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
            tname = self._tool_name(tool)
            tdesc = self._tool_description(tool)
            tparams = self._tool_parameters(tool)
            tools.append({
                "type": "function",
                "function": {
                    "name": tname,
                    "description": tdesc,
                    "parameters": tparams
                }
            })
            tool_names.append(tname)
        
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
            selection_id = self._last_format_selection_id
            selection = self._last_format_selection
            selection_mode = getattr(selection, "mode", None) if selection is not None else None
            selection_tool = getattr(selection, "tool_name", None) if selection is not None else None
            selection_conf = getattr(selection, "confidence", None) if selection is not None else None
            sel_age_ms = None
            try:
                if self._last_format_selection_ts is not None:
                    sel_age_ms = (time.time() - float(self._last_format_selection_ts)) * 1000.0
            except Exception:
                sel_age_ms = None

            ts_logger.info(
                f"TOOL_CALL_START | tool_call_id={tool_call_id} | tool={tool_name or 'unknown'} | "
                f"selection_id={selection_id} | selection_mode={selection_mode} | "
                f"selection_tool={selection_tool} | selection_confidence={selection_conf} | "
                f"selection_age_ms={None if sel_age_ms is None else f'{sel_age_ms:.1f}'}"
            )
            
            if not tool_name:
                raise ValueError("Tool call missing 'function.name'")

            # DONE/RESPOND_AND_CONTINUE latch: once tools are disabled for the remainder of the
            # current user turn, enforce that at execution time too. Some model clients may emit
            # tool_calls even when no tools were advertised.
            if self._force_final_response:
                try:
                    ts_logger.warning(
                        f"TOOL_CALL_BLOCKED | tool_call_id={tool_call_id} | tool={tool_name} | "
                        f"reason=force_final_response | selection_id={selection_id}"
                    )
                except Exception:
                    pass
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": (
                        "Tool call blocked: tools are disabled because DONE/RESPOND_AND_CONTINUE was invoked.\n"
                        "You MUST provide the final user-visible response now (no more tool calls).\n"
                        f"Requested tool: {tool_name}\n"
                        f"selection_id: {selection_id}"
                    ),
                    "_success": False,
                    "_error": "force_final_response",
                }

            # Toolset visibility enforcement (macro toolset must not execute legacy tools).
            if isinstance(tool_name, str) and not self._is_tool_visible(tool_name):
                allowed = sorted(list(self._primitive_allowed_tool_names()))
                try:
                    ts_logger.warning(
                        f"TOOL_CALL_BLOCKED | tool_call_id={tool_call_id} | tool={tool_name} | "
                        f"reason=toolset_disallowed | toolset={getattr(config.tools, 'toolset', 'legacy')} | "
                        f"allowed_tools={allowed} | selection_id={selection_id}"
                    )
                except Exception:
                    pass
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": (
                        "Tool call blocked by toolset policy (primitive macro toolset).\n"
                        f"Requested tool: {tool_name}\n"
                        f"Allowed tools: {allowed}\n"
                        f"selection_id: {selection_id}"
                    ),
                    "_success": False,
                }

            # Enforce RL forced-mode at execution time.
            # Some providers/clients do not strictly enforce the advertised tool schema,
            # so the model may emit a tool call to a disallowed tool anyway.
            allowed_tools = list(self._last_format_allowed_tools or [])

            # General "available tool buffer" enforcement:
            # if the model calls any tool that isn't in the *currently advertised* tool list,
            # return a tool error message and let the model retry.
            if isinstance(tool_name, str) and allowed_tools and tool_name not in allowed_tools:
                try:
                    ts_logger.warning(
                        f"TOOL_CALL_BLOCKED | tool_call_id={tool_call_id} | tool={tool_name} | "
                        f"reason=not_in_allowed_tools | allowed_tools={allowed_tools} | selection_id={selection_id}"
                    )
                except Exception:
                    pass

                # If we are in sticky forced-exploration, count blocks so we can log/debug.
                try:
                    if (
                        self._sticky_forced_selection is not None
                        and isinstance(self._sticky_forced_tool, str)
                        and self._sticky_forced_tool
                    ):
                        self._sticky_forced_blocks += 1
                        ts_logger.info(
                            f"REGISTRY_RL_STICKY_BLOCK | forced_tool={self._sticky_forced_tool} | "
                            f"requested_tool={tool_name} | blocks={int(self._sticky_forced_blocks)} | selection_id={selection_id}"
                        )
                except Exception:
                    pass

                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": (
                        "Tool call blocked by policy: tool not in the available tool buffer.\n"
                        f"Requested tool: {tool_name}\n"
                        f"Allowed tools: {allowed_tools}\n"
                        f"selection_id: {selection_id}"
                    ),
                    "_success": False,
                }

            # Back-compat: forced-mode mismatch stays explicit in logs.
            if (
                selection_id is not None
                and selection_mode == "forced"
                and isinstance(selection_tool, str)
                and selection_tool
                and tool_name != selection_tool
            ):
                try:
                    ts_logger.warning(
                        f"TOOL_CALL_BLOCKED | tool_call_id={tool_call_id} | tool={tool_name} | "
                        f"reason=forced_mode_disallowed | forced_tool={selection_tool} | selection_id={selection_id}"
                    )
                except Exception:
                    pass
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": (
                        f"Tool call blocked by RL forced-mode policy.\n"
                        f"Forced tool: {selection_tool}\n"
                        f"Requested tool: {tool_name}\n"
                        f"selection_id: {selection_id}"
                    ),
                    "_success": False,
                }
            
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
                readonly_blocked = {
                    # Legacy memory writes
                    "store_memory",
                    "update_memory",
                    "delete_memory",
                    "link_memories",
                    # Primitive memory writes
                    "MEMORY_PUT",
                    "MEMORY_LINK",
                    "MEMORY_DELETE",
                    "MEMORY_UPDATE",
                    # Primitive file/exec writes
                    "WRITE_FILE",
                    "APPEND_FILE",
                    "PATCH_FILE",
                    "EXECUTE",
                    # Self-model mutation
                    "self_model_crud",
                    "SELF_MODEL_UPDATE",
                    "SELF_MODEL_ARCHIVE",
                    # Policy lifecycle mutation
                    "UPDATE_POLICY",
                    "PROMOTE_POLICY",
                    "ROLLBACK_POLICY",
                }
                if tool_name in readonly_blocked:
                    return {
                        "tool_call_id": tool_call_id,
                        "role": "tool",
                        "name": tool_name,
                        "content": "Blocked by read-only policy: write/mutation tools are disabled."
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

            # System-level strict EXECUTE allowlist + 3-try reprompt budget.
            if tool_name == "EXECUTE":
                allowlist = getattr(config.tools, "execute_command_whitelist", None)
                if isinstance(allowlist, list) and allowlist:
                    cmd = arguments.get("cmd")
                    base = _extract_base_command(cmd)
                    if base not in allowlist:
                        self._execute_whitelist_block_count += 1
                        self._execute_whitelist_block_by_base[base] = (
                            self._execute_whitelist_block_by_base.get(base, 0) + 1
                        )

                        shown_attempt = min(
                            int(self._execute_whitelist_block_count),
                            _EXECUTE_WHITELIST_RETRY_LIMIT,
                        )
                        remaining = max(0, _EXECUTE_WHITELIST_RETRY_LIMIT - shown_attempt)
                        exhausted = self._execute_whitelist_block_count >= _EXECUTE_WHITELIST_RETRY_LIMIT

                        try:
                            ts_logger.warning(
                                "TOOL_CALL_BLOCKED | "
                                f"tool_call_id={tool_call_id} | tool=EXECUTE | reason=command_not_allowed | "
                                f"base_command={base} | allowed_commands={allowlist} | "
                                f"attempt={shown_attempt}/{_EXECUTE_WHITELIST_RETRY_LIMIT} | "
                                f"turn_no={self._turn_no}"
                            )
                        except Exception:
                            pass

                        guidance = (
                            "Pick a `cmd` whose first executable token is an allowed base command; args may vary.\n"
                            "If you need to expand the whitelist, update `BROCA_EXECUTE_WHITELIST` in `.env` and restart."
                        )
                        if exhausted:
                            guidance = (
                                "Retry budget exhausted for non-whitelisted EXECUTE in this turn.\n"
                                + guidance
                            )

                        return {
                            "tool_call_id": tool_call_id,
                            "role": "tool",
                            "name": tool_name,
                            "content": (
                                "EXECUTE blocked: base command not allowed by whitelist.\n"
                                f"attempt: {shown_attempt}/{_EXECUTE_WHITELIST_RETRY_LIMIT} "
                                f"(remaining: {remaining})\n"
                                f"base_command: {base}\n"
                                f"allowed_base_commands: {allowlist}\n"
                                f"cmd: {cmd}\n\n"
                                f"{guidance}"
                            ),
                            "_success": False,
                            "_error": "command_not_allowed",
                            "_base_command": base,
                            "_allowed_base_commands": allowlist,
                            "_attempt": shown_attempt,
                            "_remaining_attempts": remaining,
                        }

            # Governance policy preflight (capability gating / scopes / budgets).
            if self._governance_engine is not None:
                try:
                    decision = self._governance_engine.evaluate_action(
                        tool_name=str(tool_name),
                        arguments=arguments if isinstance(arguments, dict) else {},
                    )
                    # Audit the attempt regardless of allow/deny.
                    try:
                        self._governance_engine.audit().append(
                            {
                                "ts": time.time(),
                                "event_type": "action_attempt",
                                "tool": tool_name,
                                "allowed": bool(decision.allowed),
                                "reason": decision.reason,
                                "matched_rule": decision.matched_rule,
                            }
                        )
                    except Exception:
                        pass

                    if not decision.allowed:
                        return {
                            "tool_call_id": tool_call_id,
                            "role": "tool",
                            "name": tool_name,
                            "content": (
                                "Blocked by governance policy.\n"
                                f"reason: {decision.reason}\n"
                                f"matched_rule: {decision.matched_rule}\n"
                                f"normalized: {decision.normalized}\n"
                                "To change policy: use SET_POLICY (tighten-only) or REQUEST_POLICY_CHANGE + COMMIT_APPROVAL."
                            ),
                            "_success": False,
                        }
                except Exception:
                    # Fail open if policy evaluation errors; keep system usable.
                    pass

            # Learned Veto (GRU/LSTM over time slices): suppress action when κ_integrated remains
            # below a dynamic threshold for a persistent window (hysteresis).
            try:
                from datetime import datetime, timezone

                k_last = 1.0
                k_int = 0.0
                try:
                    pred = (
                        self.internal_sensing_framework.interoception.prediction
                        if getattr(self, "internal_sensing_framework", None) is not None
                        and getattr(self.internal_sensing_framework, "interoception", None) is not None
                        and getattr(self.internal_sensing_framework.interoception, "prediction", None) is not None
                        else None
                    )
                    if pred is not None:
                        k_last = float(pred.get_kappa_last())
                        k_int = float(pred.get_kappa_integrated())
                except Exception:
                    k_last = 1.0
                    k_int = 0.0

                veto_ctx = None
                try:
                    if (
                        getattr(self, "tool_selection_guidance", None) is not None
                        and getattr(self.tool_selection_guidance, "guidance_aggregator", None) is not None
                    ):
                        veto_ctx = self.tool_selection_guidance.guidance_aggregator.gather_context()
                except Exception:
                    veto_ctx = None
                rl_signals = veto_ctx.get("rl_signals") if isinstance(veto_ctx, dict) else None

                x_t = get_veto_guard().build_time_slice(
                    kappa_last=float(k_last),
                    kappa_integrated=float(k_int),
                    rl_signals=rl_signals if isinstance(rl_signals, dict) else None,
                    tool_name=str(tool_name),
                    tool_success_last=None,
                    tool_count_this_turn=int(self._turn_no) if isinstance(self._turn_no, int) else None,
                )
                decision_v = get_veto_guard().check(
                    x_t=x_t,
                    reason="pre_tool_call",
                    kappa_last=float(k_last),
                    kappa_integrated=float(k_int),
                )

                # Failsafe: cap consecutive vetoes per user turn to prevent permanent incapacitation.
                # If the cap is hit, fail-open and execute the tool anyway (but log loudly).
                try:
                    max_vetos = int(getattr(getattr(config, "veto", None), "max_consecutive_vetos", 0) or 0)
                except Exception:
                    max_vetos = 0

                # CSV telemetry: log only when training ran OR veto state changed (default cadence request).
                try:
                    dbg = decision_v.debug if isinstance(decision_v.debug, dict) else {}
                    train = dbg.get("train") if isinstance(dbg.get("train"), dict) else {}
                    trained = bool(train.get("trained", False))
                    changed = bool(dbg.get("state_changed", False))
                    if trained or changed:
                        get_veto_csv_logger().log_decision(
                            decision_v,
                            event="decision",
                            tool_name=str(tool_name),
                            tool_call_id=str(tool_call_id),
                            turn_no=int(self._turn_no) if isinstance(self._turn_no, int) else None,
                            iteration=None,
                        )
                except Exception:
                    pass

                if bool(decision_v.veto):
                    # Track consecutive vetoes and apply failsafe if configured.
                    try:
                        self._consecutive_veto_count = int(getattr(self, "_consecutive_veto_count", 0) or 0) + 1
                    except Exception:
                        self._consecutive_veto_count = 1

                    should_failsafe = bool(max_vetos > 0 and int(self._consecutive_veto_count) > int(max_vetos))
                    if should_failsafe:
                        try:
                            ts_logger.warning(
                                "TOOL_CALL_VETO_FAILSAFE | "
                                f"tool_call_id={tool_call_id} | tool={tool_name} | "
                                f"max_consecutive_vetos={int(max_vetos)} | "
                                f"consecutive_vetos={int(self._consecutive_veto_count)}"
                            )
                        except Exception:
                            pass
                        # Fail-open: allow tool execution to proceed.
                        # Reset counter so the system can make forward progress.
                        self._consecutive_veto_count = 0
                    else:
                        # Normal veto behavior.
                        ts_logger = _get_tool_selection_logger()
                        try:
                            ts_logger.warning(
                                "TOOL_CALL_VETO | "
                                f"tool_call_id={tool_call_id} | tool={tool_name} | "
                                f"threshold={decision_v.threshold:.6f} | kappa_integrated={decision_v.kappa_integrated:.6f} | "
                                f"persist_m={decision_v.debug.get('persist_m')} | persist_n={decision_v.debug.get('persist_n')}"
                            )
                        except Exception:
                            pass

                        veto_payload = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "tool_name": str(tool_name),
                            "tool_call_id": str(tool_call_id),
                            "source_of_conflict": "LearnedVetoGuard: κ_integrated sustained below learned threshold (coherence non-stationarity).",
                            "kappa": float(decision_v.kappa_last),
                            "kappa_integrated": float(decision_v.kappa_integrated),
                            "threshold": float(decision_v.threshold),
                            "debug": dict(decision_v.debug or {}),
                        }

                        # Synthetic penalty: learn from near-miss (treat as failure).
                        try:
                            self.record_rl_outcome(
                                tool_name=str(tool_name),
                                success=False,
                                execution_time_ms=0.0,
                                result_quality=0.0,
                                tool_arguments=arguments if isinstance(arguments, dict) else None,
                                tool_result_text=f"VETOED: {veto_payload}",
                            )
                        except Exception:
                            pass

                        return {
                            "tool_call_id": tool_call_id,
                            "role": "tool",
                            "name": tool_name,
                            "_success": False,
                            "_veto": True,
                            "_veto_payload": veto_payload,
                            "content": (
                                "VETO: action suppressed (Immediate Inhibition).\n\n"
                                "Dissonance Report (L3 Injection):\n"
                                f"- source_of_conflict: {veto_payload['source_of_conflict']}\n"
                                f"- kappa: {veto_payload['kappa']}\n"
                                f"- kappa_integrated (I): {veto_payload['kappa_integrated']}\n"
                                f"- learned_threshold: {veto_payload['threshold']}\n\n"
                                "Second Look required: re-sample context (re-read prompt/files, gather missing info) and choose a safer alternative.\n"
                                "Do NOT retry the same tool call unchanged."
                            ),
                        }
                else:
                    # Clear consecutive veto streak on non-veto decisions.
                    try:
                        self._consecutive_veto_count = 0
                    except Exception:
                        pass
            except Exception:
                # Fail open: veto is best-effort and must not break tool execution.
                pass
            
            # Log execution start
            log_tool_execution_start(tool_name, arguments, tool_call_id, logger)
            
            # Execute tool with timing
            start_time = time.time()
            result = tool.execute(**arguments)
            execution_time_ms = (time.time() - start_time) * 1000

            # DONE/RESPOND_AND_CONTINUE macros: latch "force final response" after successful execution.
            if tool_name in {"DONE", "RESPOND_AND_CONTINUE"}:
                try:
                    is_ok = result.get("success", True) if isinstance(result, dict) else True
                    if is_ok:
                        self._force_final_response = True
                        # Clear forced-exploration sticky state so we don't keep advertising a forced tool.
                        self._sticky_forced_selection = None
                        self._sticky_forced_context = None
                        self._sticky_forced_tool = None
                        self._sticky_forced_blocks = 0
                except Exception:
                    self._force_final_response = True

            # Governance audit: record action result and basic cost signals (best-effort).
            if self._governance_engine is not None:
                try:
                    cost: Dict[str, Any] = {"execution_time_ms": float(execution_time_ms)}
                    if isinstance(result, dict):
                        for k in ("bytes_written", "bytes_appended", "bytes", "exit_code", "status_code"):
                            if k in result:
                                cost[k] = result.get(k)
                    self._governance_engine.audit().append(
                        {
                            "ts": time.time(),
                            "event_type": "action_result",
                            "tool": tool_name,
                            "success": bool(result.get("success", True)) if isinstance(result, dict) else True,
                            "cost": cost,
                        }
                    )
                except Exception:
                    pass
            
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
            

            # --- Instrumentation: κ / κ_integrated telemetry (always-on; best-effort) ---
            # We want the CSVs to exist even when internal sensing / PredictiveInteroception is disabled.
            kappa_val = 0.0
            try:
                # Prefer post-tool guidance context when available; fall back to pre-RL context.
                pre_context = getattr(self, "_last_rl_context", None) if isinstance(getattr(self, "_last_rl_context", None), dict) else {}
                post_context = None
                try:
                    if (
                        getattr(self, "tool_selection_guidance", None) is not None
                        and getattr(self.tool_selection_guidance, "guidance_aggregator", None) is not None
                    ):
                        pc = self.tool_selection_guidance.guidance_aggregator.gather_context()
                        if isinstance(pc, dict):
                            post_context = pc
                except Exception:
                    post_context = None

                kappa_ctx = post_context if isinstance(post_context, dict) else pre_context
                pred = None
                if (
                    getattr(self, "internal_sensing_framework", None) is not None
                    and getattr(self.internal_sensing_framework, "interoception", None) is not None
                ):
                    pred = getattr(self.internal_sensing_framework.interoception, "prediction", None)

                k_int_override = None
                try:
                    if pred is not None and hasattr(pred, "get_kappa_integrated"):
                        k_int_override = float(pred.get_kappa_integrated())
                except Exception:
                    k_int_override = None

                from broca.rl.coherence_telemetry import log_from_context

                sample = log_from_context(
                    kappa_ctx if isinstance(kappa_ctx, dict) else {},
                    tool_name=str(tool_name),
                    success=bool(result.get("success", True) if isinstance(result, dict) else True),
                    now=time.time(),
                    kappa_integrated_override=k_int_override,
                )
                kappa_val = float(sample.kappa)
            except Exception:
                # Telemetry must never break tool execution.
                kappa_val = 0.0

            # Record usage in internal sensing framework
            if self.internal_sensing_framework:
                try:
                    self.internal_sensing_framework.record_tool_usage(tool_name, arguments, result)
                    # Estimate impact based on tool type
                    impact = 2 if tool_name in ('terminal', 'web_search') else 1
                    self.internal_sensing_framework.record_cognitive_impact(tool_name, impact)

                    # Feed κ sample into PredictiveInteroception (event-driven) when available.
                    try:
                        pred = getattr(self.internal_sensing_framework.interoception, "prediction", None) if self.internal_sensing_framework else None
                        if pred is not None and hasattr(pred, "record_kappa_sample"):
                            pred.record_kappa_sample(float(kappa_val), now=time.time())
                    except Exception:
                        pass

                    # Feed a post-action observation into the learned veto model (best-effort).
                    try:
                        pred = getattr(self.internal_sensing_framework.interoception, "prediction", None) if self.internal_sensing_framework else None
                        k_last2 = float(pred.get_kappa_last()) if pred is not None and hasattr(pred, "get_kappa_last") else float(kappa_val)
                        k_int2 = float(pred.get_kappa_integrated()) if pred is not None and hasattr(pred, "get_kappa_integrated") else 0.0

                        # Reuse the same post/pre context choice used for telemetry.
                        post_ctx2 = post_context if isinstance(post_context, dict) else pre_context if isinstance(pre_context, dict) else {}
                        rl_s2 = post_ctx2.get("rl_signals") if isinstance(post_ctx2, dict) else None
                        x_post = get_veto_guard().build_time_slice(
                            kappa_last=float(k_last2),
                            kappa_integrated=float(k_int2),
                            rl_signals=rl_s2 if isinstance(rl_s2, dict) else None,
                            tool_name=str(tool_name),
                            tool_success_last=bool(result.get("success", True) if isinstance(result, dict) else True),
                            tool_count_this_turn=int(self._turn_no) if isinstance(self._turn_no, int) else None,
                        )
                        decision_post = get_veto_guard().check(
                            x_t=x_post,
                            reason="post_tool_call",
                            kappa_last=float(k_last2),
                            kappa_integrated=float(k_int2),
                        )
                        # Log post-tool observation if training ran or veto state changed.
                        try:
                            dbg2 = decision_post.debug if isinstance(decision_post.debug, dict) else {}
                            train2 = dbg2.get("train") if isinstance(dbg2.get("train"), dict) else {}
                            trained2 = bool(train2.get("trained", False))
                            changed2 = bool(dbg2.get("state_changed", False))
                            if trained2 or changed2:
                                get_veto_csv_logger().log_decision(
                                    decision_post,
                                    event="observation",
                                    tool_name=str(tool_name),
                                    tool_call_id=str(tool_call_id),
                                    turn_no=int(self._turn_no) if isinstance(self._turn_no, int) else None,
                                )
                        except Exception:
                            pass
                    except Exception:
                        pass

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
                "content": formatted_result,
            }

            # Include success field from raw result for proper success detection
            # Always set _success as a boolean to ensure consistent success detection
            if isinstance(result, dict) and "success" in result:
                result_dict["_success"] = bool(result.get("success", True))

            # RESPOND_AND_CONTINUE: surface the internal continue prompt to the caller so the
            # surface (web_api/main_repl) can enqueue a hidden user turn asynchronously.
            if tool_name == "RESPOND_AND_CONTINUE" and isinstance(result, dict):
                cp = result.get("continue_prompt")
                if isinstance(cp, str) and cp.strip():
                    result_dict["_auto_continue_prompt"] = cp.strip()
            
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
                        tool_arguments=arguments if isinstance(arguments, dict) else None,
                        tool_result_text=formatted_result,
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
                suggested_tools = list(self._last_format_suggested_tools or [])
                in_suggested_set = bool(tool_name in suggested_tools) if isinstance(tool_name, str) else False

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
                    f"selection_id={selection_id} | selection_mode={selection_mode} | "
                    f"in_suggested_set={in_suggested_set} | suggested_tools={suggested_tools[:5]} | "
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
