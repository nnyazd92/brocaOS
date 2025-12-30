"""
Simple Critic tool for validating assistant outputs.
Provides a small API evaluate_output which returns a dict with ok(bool) and issues(list).
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import re
import json
import logging
import time

if TYPE_CHECKING:
    from ..llm import LLMClient

logger = logging.getLogger(__name__)

# Import logger utility
try:
    from ..reasoning.llm_pattern_logger import get_logger, initialize_logger
    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False

# Module-level LLM client (can be set for all evaluations)
_llm_client: Optional["LLMClient"] = None
_llm_enabled: bool = True


def set_llm_client(llm_client: Optional["LLMClient"], enabled: bool = True) -> None:
    """Set LLM client for semantic assumption detection."""
    global _llm_client, _llm_enabled
    _llm_client = llm_client
    _llm_enabled = enabled
    if llm_client:
        logger.info(f"Critic tool LLM client set (enabled: {enabled})")


DEFAULT_SYSTEM_PROMPT_TEMPLATE = """You are a critical reviewer (devil's advocate) for assistant outputs.

Your job:
- Validate whether the assistant output satisfies the provided constraints and fits the provided metadata context.
- Be strict but fair.

Metadata (context):
{metadata}

Constraints:
{constraints}

Return JSON only with the following schema:
{{
  "accepted": true/false,
  "feedback": "short explanation",
  "violations": [
    {{"constraint": "constraint_name", "description": "what failed and why"}}
  ]
}}
"""


class CriticTool:
    """LLM-backed tool that critiques/validates a piece of content against constraints."""

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        system_prompt_template: Optional[str] = None,
    ) -> None:
        # Prefer instance-level client; fall back to module-level; else create default.
        if llm_client is not None:
            self._llm = llm_client
        elif _llm_client is not None:
            self._llm = _llm_client
        else:
            from ..llm import create_llm_client

            self._llm = create_llm_client()

        self._system_prompt_template = system_prompt_template or DEFAULT_SYSTEM_PROMPT_TEMPLATE

    @property
    def name(self) -> str:
        return "critic"

    @property
    def description(self) -> str:
        return (
            "Critique/validate a proposed assistant output against the current world_state constraints "
            "(devil's advocate). Returns JSON with accepted/feedback/violations."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "world_state": {
                    "type": "object",
                    "properties": {
                        "constraints": {"type": "object"},
                        "metadata": {"type": "object"},
                    },
                    # constraints are optional
                    "required": [],
                },
                "content": {"type": "string"},
            },
            "required": ["world_state", "content"],
        }

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        world_state = kwargs.get("world_state") or {}
        content = kwargs.get("content") or ""

        if not isinstance(world_state, dict):
            return {"error": "world_state must be an object/dict"}
        if not isinstance(content, str) or not content.strip():
            return {"error": "content must be a non-empty string"}

        metadata_obj = world_state.get("metadata") if isinstance(world_state.get("metadata"), dict) else {}
        constraints_obj = world_state.get("constraints") if isinstance(world_state.get("constraints"), dict) else {}

        # Human-readable blocks
        if metadata_obj:
            metadata = json.dumps(metadata_obj, indent=2, ensure_ascii=False, sort_keys=True)
        else:
            metadata = "(none)"

        if constraints_obj:
            constraints_lines = []
            for k, v in constraints_obj.items():
                constraints_lines.append(f"- {k}: {v}")
            constraints = "\n".join(constraints_lines)
        else:
            constraints = "(none)"

        system_prompt = self._system_prompt_template.format(metadata=metadata, constraints=constraints)
        user_prompt = f"Content to critique:\n\n{content}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            resp = self._llm.chat(messages, temperature=0.0)
            raw = self._llm.extract_assistant_content(resp)
            if not raw:
                return {"error": "Empty critic response"}
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return parsed
                return {"error": "Critic response was not a JSON object", "raw": raw}
            except Exception:
                return {"error": "Critic returned invalid JSON", "raw": raw}
        except Exception as e:
            return {"error": f"Critic LLM call failed: {e}"}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not isinstance(result, dict):
            return str(result)
        if "error" in result:
            return f"Critic error: {result.get('error')}"

        accepted = bool(result.get("accepted", False))
        feedback = str(result.get("feedback", "") or "")
        violations = result.get("violations", [])
        lines = []
        lines.append("Accepted" if accepted else "Rejected")
        if feedback:
            lines.append(f"Feedback: {feedback}")
        if isinstance(violations, list) and violations:
            lines.append("Violations:")
            for v in violations:
                if isinstance(v, dict):
                    lines.append(f"- {v.get('constraint')}: {v.get('description')}")
                else:
                    lines.append(f"- {v}")
        return "\n".join(lines)


def evaluate_output(text: str, task_spec: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Evaluate output for issues using LLM when available, regex fallback otherwise.
    
    Args:
        text: Output text to evaluate
        task_spec: Optional task specification
        
    Returns:
        Dictionary with 'ok' (bool) and 'issues' (list of strings)
    """
    issues: List[str] = []
    ok = True

    if not text or not text.strip():
        ok = False
        issues.append('empty_output')
        return {'ok': ok, 'issues': issues}

    # Clarifying question detection (simple check, keep as-is)
    if text.strip().endswith('?'):
        ok = False
        issues.append('clarifying_question')

    # Assumption detection - use LLM if available
    has_assumption = False
    if _llm_enabled and _llm_client:
        try:
            has_assumption = _detect_assumption_with_llm(text)
        except Exception as e:
            logger.warning(f"LLM assumption detection failed, using regex fallback: {e}")
            # Fall through to regex
            has_assumption = _detect_assumption_with_regex(text)
    else:
        has_assumption = _detect_assumption_with_regex(text)
    
    if has_assumption:
        issues.append('assumption_present')

    return {'ok': ok, 'issues': issues}


def _detect_assumption_with_llm(text: str) -> bool:
    """Detect assumptions using LLM semantic analysis."""
    start_time = time.time()
    error_msg = None
    
    prompt = f"""Analyze this text and determine if it contains assumptions or unverified claims.

Text to analyze:
{text}

An assumption is when the text:
- States something as fact without evidence
- Uses phrases like "I assume", "assuming", "probably", "likely" (when not appropriate)
- Makes claims without justification
- Uses hedging language that indicates uncertainty about facts

Return JSON only:
{{
  "has_assumption": true/false,
  "confidence": 0.0-1.0
}}"""
    
    messages = [
        {
            "role": "system",
            "content": "You are a text critic. Detect assumptions and unverified claims. Return JSON only."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    try:
        response = _llm_client.chat(messages, temperature=0.0)
        content = _llm_client.extract_assistant_content(response)
        
        if not content:
            error_msg = "Empty LLM response"
            return False
        
        # Extract JSON
        content = content.strip()
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        
        json_match = re.search(r'\{[^{}]+\}', content)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(content)
        
        has_assumption = result.get("has_assumption", False)
        confidence = result.get("confidence", 0.5)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log the detection
        if HAS_LOGGER:
            logger_instance = get_logger()
            if logger_instance is None:
                try:
                    from ..config import config
                    logger_instance = initialize_logger(
                        log_path=getattr(config.reasoning, 'llm_pattern_log_path', 'data/llm_pattern_matching_log.csv'),
                        enabled=getattr(config.reasoning, 'llm_pattern_logging_enabled', True)
                    )
                except Exception:
                    logger_instance = None
            
            if logger_instance:
                # Get model name if available
                model = getattr(_llm_client, 'model', 'unknown')
                logger_instance.log(
                    component="CriticTool",
                    operation="assumption_detection",
                    model=model,
                    input_text=text,
                    output_match=has_assumption and confidence >= 0.6,
                    output_confidence=confidence,
                    output_metrics={"has_assumption": has_assumption, "confidence": confidence, "threshold": 0.6},
                    latency_ms=latency_ms,
                    error=error_msg
                )
        
        # Only flag if high confidence
        return has_assumption and confidence >= 0.6
        
    except Exception as e:
        error_msg = str(e)
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Error in LLM assumption detection: {e}", exc_info=True)
        
        # Log error
        if HAS_LOGGER:
            logger_instance = get_logger()
            if logger_instance:
                model = getattr(_llm_client, 'model', 'unknown')
                logger_instance.log(
                    component="CriticTool",
                    operation="assumption_detection",
                    model=model,
                    input_text=text,
                    latency_ms=latency_ms,
                    error=error_msg
                )
        
        raise


def _detect_assumption_with_regex(text: str) -> bool:
    """Fallback regex-based assumption detection."""
    return bool(re.search(r"\b(I assume|ASSUME:|assuming that|for the purpose of this answer)\b", text, flags=re.IGNORECASE))
