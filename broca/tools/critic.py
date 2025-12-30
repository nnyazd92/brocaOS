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
