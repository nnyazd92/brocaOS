"""
Primitive toolset registration.

This module provides a "v2" toolset intended for RL/agent operation, where
high-level universal tools (e.g., terminal) are replaced by explicit, small
action tools.
"""

from __future__ import annotations

from typing import Any, Optional

from ..config import config
from ..memory.manager import MemoryManager
from ..tools.registry import ToolRegistry

from .primitive_io import (
    AppendFileTool,
    ExecuteTool,
    ListDirTool,
    PatchFileTool,
    ReadFileTool,
    StatPathTool,
    WriteFileTool,
)


class _RenamedTool:
    def __init__(self, inner: Any, name: str, description: Optional[str] = None) -> None:
        self._inner = inner
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description if isinstance(self._description, str) else getattr(self._inner, "description", "")

    @property
    def parameters(self):
        return getattr(self._inner, "parameters")

    def execute(self, **kwargs):
        return self._inner.execute(**kwargs)

    def format_result(self, result):
        return self._inner.format_result(result)


class CognitionMarkerTool:
    """
    A pure "cognition" tool that records an action without touching the environment.

    These are intentionally non-actuating; they provide a stable, explicit action
    vocabulary for RL without collapsing into universal environment manipulation.
    """

    def __init__(self, tool_name: str) -> None:
        self._tool_name = tool_name

    @property
    def name(self) -> str:
        return self._tool_name

    @property
    def description(self) -> str:
        return (
            "Pure cognition marker. Use this to indicate an internal cognitive step "
            "without performing environment I/O."
        )

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Optional input/context for this cognitive step"},
                "notes": {"type": "string", "description": "Optional notes"},
            },
            "required": [],
        }

    def execute(self, input: str = "", notes: str = "", **kwargs):
        return {"success": True, "tool": self._tool_name, "input": input, "notes": notes}

    def format_result(self, result):
        if not result.get("success"):
            return f"{self._tool_name} error: {result.get('error', 'unknown')}"
        return f"{self._tool_name}: recorded"


class DoneTool:
    """
    Signal that the agent is done gathering information and should respond.

    This is a pure (non-actuating) macro intended to let RL learn when to stop
    calling tools and provide a final natural-language answer.
    """

    @property
    def name(self) -> str:
        return "DONE"

    @property
    def description(self) -> str:
        return (
            "Signal that you're done using tools for this turn. After calling DONE, "
            "the system will disable tools and you MUST provide your final response."
        )

    @property
    def parameters(self):
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs):
        return {"success": True, "done": True}

    def format_result(self, result):
        if not result.get("success", True):
            return f"DONE error: {result.get('error', 'unknown')}"
        return "DONE: ok"


class RespondAndContinueTool:
    """
    Respond to the user, then continue working in the background.

    Semantics:
    - Like DONE, this forces the next LLM iteration to produce a natural-language response
      by disabling tools.
    - Additionally, the runtime will enqueue a hidden internal user message after the response
      so the agent continues working with tools enabled.
    """

    @property
    def name(self) -> str:
        return "RESPOND_AND_CONTINUE"

    @property
    def description(self) -> str:
        return (
            "Respond now, then continue working in the background. After calling this, the system will "
            "disable tools for the next iteration so you MUST produce the user-visible answer. Then a "
            "hidden internal user prompt will be queued to continue the task with tools enabled."
        )

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "continue_prompt": {
                    "type": "string",
                    "description": "Optional internal prompt used to continue work after responding.",
                }
            },
            "required": [],
        }

    def execute(self, continue_prompt: str = "", **kwargs):
        prompt = (continue_prompt or "").strip()
        if not prompt:
            prompt = (
                "Continue working in the background on the same task. "
                "Do not repeat the user-facing response. "
                "Use tools as needed; if there is nothing more to do, stop."
            )
        return {"success": True, "continue_prompt": prompt}

    def format_result(self, result):
        if not result.get("success", True):
            return f"RESPOND_AND_CONTINUE error: {result.get('error', 'unknown')}"
        return "RESPOND_AND_CONTINUE: queued"


def register_primitive_toolset(
    registry: ToolRegistry,
    *,
    memory_manager: Optional[MemoryManager] = None,
    epistemic_engine: Optional[Any] = None,
    self_model: Optional[Any] = None,
    storage: Optional[Any] = None,
    goal_manager: Optional[Any] = None,
    learning_tool: Optional[Any] = None,
) -> None:
    """
    Register the primitive toolset on an existing ToolRegistry.

    Notes:
    - Intentionally does NOT register `terminal`.
    - Uses existing implementations where possible but exposes requested names.
    """
    # Core I/O
    registry.register_tool(ReadFileTool())
    registry.register_tool(WriteFileTool())
    registry.register_tool(AppendFileTool())
    registry.register_tool(PatchFileTool())
    registry.register_tool(ListDirTool())
    registry.register_tool(StatPathTool())
    registry.register_tool(ExecuteTool())

    # Web
    if getattr(config.tools, "enable_web_search", False):
        try:
            from .web_search import WebSearchTool

            web_search = WebSearchTool(api_key=getattr(config.tools, "tavily_api_key", "") or None)
            registry.register_tool(_RenamedTool(web_search, "WEB_SEARCH"))
        except Exception:
            # If web search fails to initialize, keep toolset usable.
            pass

    try:
        from .web_fetch import WebFetchTool

        registry.register_tool(WebFetchTool())
    except Exception:
        # Optional; WEB_FETCH depends on extra libs.
        pass

    # Cognition (pure)
    try:
        from .planning_tool import PlanningTool

        registry.register_tool(_RenamedTool(PlanningTool(), "PLAN"))
    except Exception:
        pass

    if getattr(config.tools, "enable_critic", False):
        try:
            from .critic import CriticTool

            registry.register_tool(
                _RenamedTool(
                    CriticTool(system_prompt_template=getattr(config.tools, "critic_system_prompt_template", None)),
                    "CRITIC",
                )
            )
        except Exception:
            pass

    try:
        from .cognition_tools import InterpretTool, SolveTool, VerifyTool

        experience_logger = getattr(learning_tool, "experience_logger", None) if learning_tool else None
        # These tools are reasoning-backed and persist reasoning state; they remain functional even if
        # the full reasoning system is disabled by using a local ReasoningTool with persisted state.
        registry.register_tool(SolveTool(experience_logger=experience_logger))
        registry.register_tool(VerifyTool(experience_logger=experience_logger))
        registry.register_tool(InterpretTool(experience_logger=experience_logger))
    except Exception:
        # Fallback to non-actuating markers if reasoning-backed tools fail to load.
        registry.register_tool(CognitionMarkerTool("SOLVE"))
        registry.register_tool(CognitionMarkerTool("VERIFY"))
        registry.register_tool(CognitionMarkerTool("INTERPRET"))

    # RL-stop macro (pure)
    registry.register_tool(DoneTool())
    registry.register_tool(RespondAndContinueTool())

    # Memory / self-model (versioned)
    if memory_manager:
        try:
            from .memory_tool import (
                DeleteMemoryTool,
                GetRelatedMemoriesTool,
                LinkMemoriesTool,
                RetrieveMemoriesTool,
                StoreMemoryTool,
                UpdateMemoryTool,
            )

            registry.register_tool(_RenamedTool(StoreMemoryTool(memory_manager, epistemic_engine=epistemic_engine, self_model=self_model, storage=storage), "MEMORY_PUT"))
            registry.register_tool(_RenamedTool(RetrieveMemoriesTool(memory_manager, epistemic_engine=epistemic_engine), "MEMORY_GET"))
            registry.register_tool(_RenamedTool(LinkMemoriesTool(memory_manager), "MEMORY_LINK"))
            registry.register_tool(_RenamedTool(DeleteMemoryTool(memory_manager), "MEMORY_DELETE"))

            # Optional graph helpers (useful for traversal and maintenance).
            registry.register_tool(_RenamedTool(UpdateMemoryTool(memory_manager), "MEMORY_UPDATE"))
            registry.register_tool(_RenamedTool(GetRelatedMemoriesTool(memory_manager), "MEMORY_RELATED"))
        except Exception:
            pass

    if self_model and storage:
        try:
            from .self_model_primitives import (
                SelfModelArchiveTool,
                SelfModelGetTool,
                SelfModelUpdateTool,
            )

            registry.register_tool(SelfModelGetTool(self_model=self_model, storage=storage, epistemic_engine=epistemic_engine))
            registry.register_tool(SelfModelUpdateTool(self_model=self_model, storage=storage, epistemic_engine=epistemic_engine))
            registry.register_tool(SelfModelArchiveTool(self_model=self_model, storage=storage))
        except Exception:
            pass

    # Learning / Goals (macro)
    if goal_manager:
        try:
            from .goal_reward_tools import DesignRewardTool, SetGoalsTool

            experience_logger = getattr(learning_tool, "experience_logger", None) if learning_tool else None
            registry.register_tool(SetGoalsTool(goal_manager=goal_manager, experience_logger=experience_logger))
            registry.register_tool(DesignRewardTool(experience_logger=experience_logger))
        except Exception:
            pass

    # Learning / Policy (macro)
    try:
        from .policy_tools import (
            CommitApprovalTool,
            EvaluateActionTool,
            GetAuditLogTool,
            GetPolicyTool,
            RequestPolicyChangeTool,
            SetPolicyTool,
        )

        registry.register_tool(GetPolicyTool())
        registry.register_tool(SetPolicyTool())
        registry.register_tool(RequestPolicyChangeTool())
        registry.register_tool(CommitApprovalTool())
        registry.register_tool(EvaluateActionTool())
        registry.register_tool(GetAuditLogTool())
    except Exception:
        pass

    # RL ranker lifecycle tools intentionally NOT exposed to the agent by default.
    # The rankers train/update automatically based on buffer thresholds and update_frequency.
    #
    # Operator debugging can be enabled explicitly when needed.
    if bool(getattr(config.tools, "enable_rl_policy_debug_tools", False)):
        try:
            from .rl_policy_tools import (
                EvaluatePolicyTool,
                PolicyDiffTool,
                PolicyGuardTool,
                PolicyListTool,
                PromotePolicyTool,
                RollbackPolicyTool,
                UpdatePolicyTool,
            )

            experience_logger = getattr(learning_tool, "experience_logger", None) if learning_tool else None
            registry.register_tool(UpdatePolicyTool(tool_registry=registry, experience_logger=experience_logger))
            registry.register_tool(EvaluatePolicyTool(tool_registry=registry, experience_logger=experience_logger))
            registry.register_tool(PromotePolicyTool(tool_registry=registry, experience_logger=experience_logger))
            registry.register_tool(RollbackPolicyTool(tool_registry=registry, experience_logger=experience_logger))
            registry.register_tool(PolicyListTool())
            registry.register_tool(PolicyDiffTool())
            registry.register_tool(PolicyGuardTool())
        except Exception:
            pass
