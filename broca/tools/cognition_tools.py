"""
Cognition macro tools backed by broca/reasoning.

These are explicitly named actions in the primitive toolset:
- SOLVE
- VERIFY
- INTERPRET

They are "cognitive" in the sense that they do not touch external actuators
(filesystem/process) directly, but they *do* interact with the internal
reasoning state machine (working memory / production rules) and persist it so
state survives restarts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..config import config
from ..learning.experience_logger import ExperienceLogger
from ..reasoning.integration_tool import ReasoningTool
from ..reasoning.state_manager import ReasoningStateManager


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_truthy(x: Any) -> bool:
    return bool(x) and str(x).lower() not in {"0", "false", "no", "off"}


class _ReasoningBackedTool:
    def __init__(
        self,
        *,
        reasoning_tool: Optional[ReasoningTool] = None,
        experience_logger: Optional[ExperienceLogger] = None,
        state_file_path: Optional[str] = None,
    ) -> None:
        self._reasoning_tool: Optional[ReasoningTool] = reasoning_tool
        self._experience_logger = experience_logger
        self._state_file_path = state_file_path or getattr(config.reasoning, "state_file_path", "data/reasoning_state.json")
        self._state_manager = ReasoningStateManager(state_file_path=self._state_file_path, backup_enabled=True)
        self._local_tool_initialized = False

    def set_reasoning_tool(self, reasoning_tool: Optional[ReasoningTool]) -> None:
        self._reasoning_tool = reasoning_tool

    def set_experience_logger(self, experience_logger: Optional[ExperienceLogger]) -> None:
        self._experience_logger = experience_logger

    def _tool(self) -> ReasoningTool:
        """
        Get a ReasoningTool instance.

        If no shared reasoning tool is provided, we create a local one and load
        persisted state into it so the cognition macros remain functional and
        restart-safe even when the full reasoning system is disabled.
        """
        if self._reasoning_tool is not None:
            return self._reasoning_tool

        if not self._local_tool_initialized:
            local = ReasoningTool()
            try:
                if getattr(config.reasoning, "state_persistence_enabled", True):
                    self._state_manager.load_state(
                        rule_system=local.rule_system,
                        goal_manager=local.goal_manager,
                        working_memory=local.rule_system.working_memory,
                    )
            except Exception:
                pass
            self._reasoning_tool = local
            self._local_tool_initialized = True

        return self._reasoning_tool

    def _persist(self, tool: ReasoningTool, *, force: bool) -> bool:
        if not getattr(config.reasoning, "state_persistence_enabled", True):
            return False
        ok = self._state_manager.save_state(
            rule_system=tool.rule_system,
            goal_manager=tool.goal_manager,
            working_memory=tool.rule_system.working_memory,
            force=force,
        )
        return bool(ok)

    def _log(self, payload: Dict[str, Any]) -> None:
        if self._experience_logger is None:
            return
        try:
            self._experience_logger.log_experience(payload)
        except Exception:
            pass


class SolveTool(_ReasoningBackedTool):
    @property
    def name(self) -> str:
        return "SOLVE"

    @property
    def description(self) -> str:
        return (
            "Use the internal reasoning engine to work on a problem: add it to working memory, "
            "run one or more reasoning cycles, and return fired rules + queued tool suggestions. "
            "Persists reasoning state so it survives restarts."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "problem": {"type": "string", "description": "Problem statement to solve"},
                "context": {"type": "string", "description": "Optional extra context"},
                "cycles": {"type": "integer", "default": 1, "minimum": 0, "maximum": 10},
                "max_rules": {"type": "integer", "default": 5, "minimum": 1, "maximum": 50},
                "persist": {"type": "boolean", "default": True, "description": "Persist reasoning state to disk"},
                "tag": {"type": "string", "description": "Optional tag for the working memory item"},
            },
            "required": ["problem"],
        }

    def execute(
        self,
        problem: str,
        context: str = "",
        cycles: int = 1,
        max_rules: int = 5,
        persist: bool = True,
        tag: str = "",
        **_: Any,
    ) -> Dict[str, Any]:
        if not isinstance(problem, str) or not problem.strip():
            return {"success": False, "error": "problem_required"}

        tool = self._tool()

        memory_item = {
            "type": "problem",
            "text": problem.strip(),
            "context": context.strip() if isinstance(context, str) else "",
            "tag": tag.strip() if isinstance(tag, str) else "",
            "timestamp": _now_iso(),
        }
        _ = tool.execute(action="add_to_memory", memory_content=memory_item)

        c = max(0, min(10, int(cycles)))
        mr = max(1, min(50, int(max_rules)))

        cycle_results: List[Dict[str, Any]] = []
        queued: List[Dict[str, Any]] = []
        for _i in range(c):
            res = tool.execute(action="execute_cycle", max_rules=mr)
            cycle_results.append(res)
            if isinstance(res, dict):
                q = res.get("queued_tools")
                if isinstance(q, list):
                    queued = q

        state = tool.execute(action="get_state")

        persisted = False
        if _is_truthy(persist):
            persisted = self._persist(tool, force=True)

        self._log(
            {
                "type": "solve",
                "timestamp": _now_iso(),
                "problem_preview": problem[:200],
                "cycles": c,
                "max_rules": mr,
                "persisted": persisted,
                "success": True,
            }
        )

        return {
            "success": True,
            "memory_item": memory_item,
            "cycles_executed": c,
            "cycle_results": cycle_results,
            "queued_tools": queued,
            "state": state.get("state") if isinstance(state, dict) else None,
            "persisted": persisted,
        }

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"SOLVE error: {result.get('error', 'unknown')}"
        n = int(result.get("cycles_executed", 0) or 0)
        q = result.get("queued_tools") or []
        return f"SOLVE: cycles={n} queued_tools={len(q) if isinstance(q, list) else 0} persisted={bool(result.get('persisted'))}"


class InterpretTool(_ReasoningBackedTool):
    @property
    def name(self) -> str:
        return "INTERPRET"

    @property
    def description(self) -> str:
        return (
            "Interpret an observation by adding it to working memory and running reasoning cycles "
            "to derive implications and next-step tool suggestions. Persists reasoning state."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "observation": {"type": "string", "description": "Observation/data to interpret"},
                "context": {"type": "string", "description": "Optional context"},
                "cycles": {"type": "integer", "default": 1, "minimum": 0, "maximum": 10},
                "max_rules": {"type": "integer", "default": 5, "minimum": 1, "maximum": 50},
                "persist": {"type": "boolean", "default": True},
                "tag": {"type": "string"},
            },
            "required": ["observation"],
        }

    def execute(
        self,
        observation: str,
        context: str = "",
        cycles: int = 1,
        max_rules: int = 5,
        persist: bool = True,
        tag: str = "",
        **_: Any,
    ) -> Dict[str, Any]:
        if not isinstance(observation, str) or not observation.strip():
            return {"success": False, "error": "observation_required"}

        tool = self._tool()

        memory_item = {
            "type": "observation",
            "text": observation.strip(),
            "context": context.strip() if isinstance(context, str) else "",
            "tag": tag.strip() if isinstance(tag, str) else "",
            "timestamp": _now_iso(),
        }
        _ = tool.execute(action="add_to_memory", memory_content=memory_item)

        c = max(0, min(10, int(cycles)))
        mr = max(1, min(50, int(max_rules)))

        cycle_results: List[Dict[str, Any]] = []
        queued: List[Dict[str, Any]] = []
        for _i in range(c):
            res = tool.execute(action="execute_cycle", max_rules=mr)
            cycle_results.append(res)
            if isinstance(res, dict):
                q = res.get("queued_tools")
                if isinstance(q, list):
                    queued = q

        persisted = False
        if _is_truthy(persist):
            persisted = self._persist(tool, force=True)

        self._log(
            {
                "type": "interpret",
                "timestamp": _now_iso(),
                "observation_preview": observation[:200],
                "cycles": c,
                "persisted": persisted,
                "success": True,
            }
        )

        return {
            "success": True,
            "memory_item": memory_item,
            "cycles_executed": c,
            "cycle_results": cycle_results,
            "queued_tools": queued,
            "persisted": persisted,
        }

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"INTERPRET error: {result.get('error', 'unknown')}"
        n = int(result.get("cycles_executed", 0) or 0)
        q = result.get("queued_tools") or []
        return f"INTERPRET: cycles={n} queued_tools={len(q) if isinstance(q, list) else 0} persisted={bool(result.get('persisted'))}"


class VerifyTool(_ReasoningBackedTool):
    @property
    def name(self) -> str:
        return "VERIFY"

    @property
    def description(self) -> str:
        return (
            "Verify content using reasoning subsystems. Supports factual claim checking via broca.reasoning.fact_checker "
            "(uses web search when enabled) and logical validation via Z3 (mode=logic, runs z3_validate). "
            "Stores verification results in working memory."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text containing claims to verify"},
                "mode": {
                    "type": "string",
                    "enum": ["facts", "logic"],
                    "default": "facts",
                    "description": "Verification mode: facts (fact checking) or logic (Z3 validation via z3_validate)",
                },
                "z3_code": {
                    "type": "string",
                    "description": "Required when mode=logic: Python code using Z3 to validate logical constraints (same contract as z3_validate)",
                },
                "z3_timeout": {
                    "type": "number",
                    "description": "Optional when mode=logic: execution timeout in seconds (default: 5.0)",
                    "default": 5.0,
                    "minimum": 0.1,
                    "maximum": 30.0,
                },
                "enable_web_search": {
                    "type": "boolean",
                    "default": True,
                    "description": "If true, use web search for fact checking (respects BROCA_ENABLE_WEB_SEARCH by default)",
                },
                "min_claim_confidence": {
                    "type": "number",
                    "default": 0.3,
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Minimum claim confidence threshold for extraction",
                },
                "max_claims": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                "persist": {"type": "boolean", "default": True},
                "store_in_working_memory": {"type": "boolean", "default": True},
            },
            "required": ["text"],
        }

    def execute(
        self,
        text: str,
        mode: str = "facts",
        z3_code: str = "",
        z3_timeout: float = 5.0,
        enable_web_search: Optional[bool] = None,
        min_claim_confidence: float = 0.3,
        max_claims: int = 5,
        persist: bool = True,
        store_in_working_memory: bool = True,
        **_: Any,
    ) -> Dict[str, Any]:
        if not isinstance(text, str) or not text.strip():
            return {"success": False, "error": "text_required"}

        mode_norm = (mode or "facts").strip().lower()
        if mode_norm == "facts":
            from ..reasoning.fact_checker import FactChecker

            if enable_web_search is None:
                enable_web_search = bool(getattr(config.tools, "enable_web_search", True))
            try:
                mcc = max(0.0, min(1.0, float(min_claim_confidence)))
            except Exception:
                mcc = 0.3

            fc = FactChecker(enable_web_search=bool(enable_web_search), min_claim_confidence=mcc)
            claims = fc.extract_factual_claims(text.strip())
            claims = claims[: max(1, min(20, int(max_claims)))]

            results = []
            for c in claims:
                r = fc.fact_check_claim(c)
                results.append(
                    {
                        "claim": c.text,
                        "claim_type": c.claim_type,
                        "claim_confidence": c.confidence,
                        "verified": r.verified,
                        "contradiction_score": r.contradiction_score,
                        "evidence": r.evidence,
                        "confidence": r.confidence,
                    }
                )

            tool = self._tool()
            if _is_truthy(store_in_working_memory):
                try:
                    tool.execute(
                        action="add_to_memory",
                        memory_content={
                            "type": "verification",
                            "mode": "facts",
                            "timestamp": _now_iso(),
                            "source_text_preview": text.strip()[:200],
                            "results": results[:10],
                        },
                    )
                except Exception:
                    pass

            persisted = False
            if _is_truthy(persist):
                persisted = self._persist(tool, force=True)

            self._log(
                {
                    "type": "verify",
                    "timestamp": _now_iso(),
                    "mode": "facts",
                    "n_claims": len(claims),
                    "persisted": persisted,
                    "success": True,
                }
            )

            return {"success": True, "mode": "facts", "count": len(results), "results": results, "persisted": persisted}

        if mode_norm == "logic":
            if not bool(getattr(config.reasoning, "z3_tool_enabled", True)):
                return {"success": False, "error": "z3_tool_disabled"}
            if not isinstance(z3_code, str) or not z3_code.strip():
                return {"success": False, "error": "z3_code_required"}

            try:
                timeout = float(z3_timeout)
            except Exception:
                timeout = 5.0
            timeout = max(0.1, min(30.0, timeout))

            from .z3_validator_tool import Z3ValidatorTool

            z3_tool = Z3ValidatorTool(timeout=timeout)
            try:
                z3_result = z3_tool.execute(z3_code=z3_code, timeout=timeout)
            except Exception as e:
                return {"success": False, "error": f"z3_execute_failed:{e}"}

            if not isinstance(z3_result, dict):
                return {"success": False, "error": "z3_invalid_result"}

            if z3_result.get("result") == "error":
                return {"success": False, "mode": "logic", "z3": z3_result, "error": "z3_error"}

            tool = self._tool()
            if _is_truthy(store_in_working_memory):
                try:
                    from hashlib import sha256

                    code_bytes = z3_code.encode("utf-8", errors="replace")
                    tool.execute(
                        action="add_to_memory",
                        memory_content={
                            "type": "verification",
                            "mode": "logic",
                            "timestamp": _now_iso(),
                            "source_text_preview": text.strip()[:200],
                            "z3_timeout": timeout,
                            "z3_code_sha256": sha256(code_bytes).hexdigest(),
                            "z3_code_preview": z3_code.strip()[:500],
                            "z3_result": {
                                "result": z3_result.get("result"),
                                "model": z3_result.get("model"),
                                "unsat_core": z3_result.get("unsat_core"),
                                "note": z3_result.get("note"),
                            },
                        },
                    )
                except Exception:
                    pass

            persisted = False
            if _is_truthy(persist):
                persisted = self._persist(tool, force=True)

            self._log(
                {
                    "type": "verify",
                    "timestamp": _now_iso(),
                    "mode": "logic",
                    "z3_result": z3_result.get("result"),
                    "persisted": persisted,
                    "success": True,
                }
            )

            return {"success": True, "mode": "logic", "z3": z3_result, "persisted": persisted}

        return {"success": False, "error": f"invalid_mode:{mode}"}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"VERIFY error: {result.get('error', 'unknown')}"
        mode = result.get("mode")
        if mode == "logic":
            z3 = result.get("z3") or {}
            if isinstance(z3, dict):
                zr = z3.get("result", "unknown")
            else:
                zr = "unknown"
            return f"VERIFY: mode=logic z3={zr} persisted={bool(result.get('persisted'))}"
        return f"VERIFY: mode={mode} claims={result.get('count')} persisted={bool(result.get('persisted'))}"
