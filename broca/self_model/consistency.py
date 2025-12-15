"""
Consistency checker that validates LLM responses against the self-model.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

from .model import SelfModel
from ..llm.deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyResult:
    """
    Result of consistency checking.
    
    Attributes:
        is_consistent: Whether the response is consistent with self-model
        violations: List of violation objects
        severity: Overall severity score (0.0-1.0)
        suggested_updates: Proposed self-model changes
    """
    is_consistent: bool
    violations: List[Dict[str, Any]]
    severity: float
    suggested_updates: Optional[Dict[str, Any]] = None


class ConsistencyChecker:
    """
    Validates LLM responses against the self-model for consistency.
    
    Checks for:
    - Logical inconsistencies: Contradictions with stated knowledge/capabilities
    - Factual inconsistencies: Claims that contradict the self-model
    - Behavioral inconsistencies: Responses that don't match stated preferences/patterns
    """
    
    _DEFAULT_CHECK_PROMPT = """You are a consistency validator. Your role is to check if a response is consistent with the LLM's self-model.

Self-Model:
{self_model_summary}

Response to check:
{response}

Conversation context (last 3 messages):
{context}

Check for:
1. Logical inconsistencies: Does the response contradict stated capabilities, knowledge boundaries, or constraints?
2. Factual inconsistencies: Does the response make claims that contradict the self-model?
3. Behavioral inconsistencies: Does the response style or approach contradict stated preferences or behavioral patterns?

Respond with a JSON object containing:
- "is_consistent": boolean indicating if the response is consistent
- "violations": array of objects, each with:
  - "type": one of "logical", "factual", "behavioral"
  - "severity": number from 0.0 to 1.0
  - "description": string describing the violation
  - "evidence": string with specific evidence from the response
- "overall_severity": number from 0.0 to 1.0 (0.0 = consistent, 1.0 = highly inconsistent)
- "suggested_updates": optional object with suggested self-model updates to resolve inconsistencies, with keys like "capabilities", "preferences", "knowledge_boundaries", "constraints", "behavioral_patterns"

Be thorough but fair. Only flag genuine inconsistencies."""
    
    def __init__(
        self,
        llm_client: Optional[DeepSeekClient] = None,
        check_prompt_template: Optional[str] = None,
    ) -> None:
        """
        Initialize consistency checker.
        
        Args:
            llm_client: Optional DeepSeekClient instance
            check_prompt_template: Optional custom prompt template for consistency checking
        """
        self._llm = llm_client or DeepSeekClient()
        self._check_prompt_template = check_prompt_template or self._DEFAULT_CHECK_PROMPT
        logger.info("Initialized ConsistencyChecker")
    
    def validate(
        self,
        response: str,
        self_model: SelfModel,
        conversation_context: Optional[List[Dict[str, str]]] = None,
    ) -> ConsistencyResult:
        """
        Validate a response against the self-model.
        
        Args:
            response: The LLM response to validate
            self_model: Current self-model
            conversation_context: Optional conversation context (last few messages)
            
        Returns:
            ConsistencyResult with validation results
        """
        try:
            # Build prompt
            self_model_summary = self_model.get_summary()
            
            # Format conversation context
            context_str = "No context provided"
            if conversation_context:
                context_lines = []
                for msg in conversation_context[-3:]:  # Last 3 messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")[:200]  # Truncate for brevity
                    context_lines.append(f"{role}: {content}")
                context_str = "\n".join(context_lines)
            
            prompt = self._check_prompt_template.format(
                self_model_summary=self_model_summary,
                response=response,
                context=context_str,
            )
            
            # Call LLM for consistency check
            messages = [
                {"role": "system", "content": "You are a consistency validator. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            logger.debug("Calling LLM for consistency check")
            llm_response = self._llm.chat(messages)
            response_content = DeepSeekClient.extract_assistant_content(llm_response)
            
            # Parse JSON response
            result = self._parse_response(response_content)
            
            logger.info(
                f"Consistency check completed: consistent={result.is_consistent}, "
                f"violations={len(result.violations)}, severity={result.severity:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during consistency check: {e}", exc_info=True)
            # Return a result indicating an error occurred
            return ConsistencyResult(
                is_consistent=True,  # Default to consistent on error to avoid blocking
                violations=[],
                severity=0.0,
                suggested_updates=None,
            )
    
    def _parse_response(self, response_content: str) -> ConsistencyResult:
        """
        Parse LLM response into ConsistencyResult.
        
        Args:
            response_content: Raw LLM response content
            
        Returns:
            ConsistencyResult instance
        """
        import json
        
        try:
            # Try to extract JSON from response (may be wrapped in markdown code blocks)
            response_content = response_content.strip()
            if response_content.startswith("```"):
                # Extract JSON from code block
                lines = response_content.split("\n")
                json_start = None
                json_end = None
                for i, line in enumerate(lines):
                    if line.strip().startswith("```json") or line.strip().startswith("```"):
                        json_start = i + 1
                        break
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip().startswith("```"):
                        json_end = i
                        break
                if json_start is not None and json_end is not None:
                    response_content = "\n".join(lines[json_start:json_end])
            
            data = json.loads(response_content)
            
            # Extract fields with defaults
            is_consistent = data.get("is_consistent", True)
            violations = data.get("violations", [])
            severity = float(data.get("overall_severity", 0.0))
            suggested_updates = data.get("suggested_updates")
            
            # Validate violations structure
            validated_violations = []
            for violation in violations:
                if isinstance(violation, dict):
                    validated_violations.append({
                        "type": violation.get("type", "unknown"),
                        "severity": float(violation.get("severity", 0.5)),
                        "description": violation.get("description", ""),
                        "evidence": violation.get("evidence", ""),
                    })
            
            # Determine consistency based on severity
            if severity > 0.5 or len(validated_violations) > 0:
                is_consistent = False
            
            return ConsistencyResult(
                is_consistent=is_consistent,
                violations=validated_violations,
                severity=severity,
                suggested_updates=suggested_updates,
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse consistency check response as JSON: {e}")
            logger.debug(f"Response content: {response_content[:500]}")
            # Return default result on parse error
            return ConsistencyResult(
                is_consistent=True,  # Default to consistent on parse error
                violations=[],
                severity=0.0,
                suggested_updates=None,
            )

