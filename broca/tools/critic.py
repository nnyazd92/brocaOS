"""
Critic tool for validating LLM responses against constraints.

Allows the main LLM to send prompts to a critical LLM instance that validates
responses against provided constraints and returns structured feedback.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, Any, Optional

from ..llm.deepseek_client import DeepSeekClient
from ..config import config

logger = logging.getLogger(__name__)


class CriticTool:
    """
    Critic tool for validating LLM responses against constraints.
    
    Allows the main LLM to validate its responses by sending them to a critical
    LLM instance with a highly critical system prompt. The critic evaluates the
    response against provided constraints and returns structured feedback.
    """
    
    _DEFAULT_SYSTEM_PROMPT_TEMPLATE = """You are a highly critical validator. Your role is to strictly evaluate responses against the provided constraints.

{metadata_section}

Constraints to enforce:
{constraints_section}

You must respond with a JSON object containing:
- "accepted": boolean indicating if the response passes validation
- "feedback": string explaining your decision
- "violations": array of objects with "constraint" and "description" keys for each violation found

Be strict and thorough in your evaluation. Reject any response that violates even a single constraint."""

    def __init__(
        self,
        llm_client: Optional[DeepSeekClient] = None,
        system_prompt_template: Optional[str] = None,
    ) -> None:
        """
        Initialize the critic tool.
        
        Args:
            llm_client: Optional DeepSeekClient instance (defaults to new instance)
            system_prompt_template: Optional custom system prompt template
        """
        self._llm = llm_client or DeepSeekClient()
        self._system_prompt_template = (
            system_prompt_template or self._DEFAULT_SYSTEM_PROMPT_TEMPLATE
        )
        logger.info("Initialized CriticTool")

    @property
    def name(self) -> str:
        """Tool identifier."""
        return "critic"

    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Validate a response against constraints using a critical validator. "
            "Provide a world_state object containing metadata and constraints, "
            "along with the content to validate. The critic will evaluate whether "
            "the response violates any constraints and provide detailed feedback. "
            "Use this tool when you need to ensure your response meets specific "
            "requirements or constraints."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "world_state": {
                    "type": "object",
                    "description": "World state containing metadata and constraints",
                    "properties": {
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata about the context (e.g., domain, context type)",
                            "additionalProperties": True
                        },
                        "constraints": {
                            "type": "object",
                            "description": "Required. Object containing constraint rules to enforce. Each key is a constraint name and value is the constraint description.",
                            "additionalProperties": True
                        }
                    },
                    "required": ["constraints"]
                },
                "content": {
                    "type": "string",
                    "description": "The response content to validate against the constraints"
                }
            },
            "required": ["world_state", "content"]
        }

    def _build_system_prompt(self, world_state: Dict[str, Any]) -> str:
        """
        Build system prompt from template using world_state.
        
        Args:
            world_state: World state containing metadata and constraints
            
        Returns:
            Formatted system prompt string
        """
        metadata = world_state.get("metadata", {})
        constraints = world_state.get("constraints", {})
        
        # Format metadata section
        if metadata:
            metadata_lines = ["Context:"]
            for key, value in metadata.items():
                metadata_lines.append(f"- {key}: {value}")
            metadata_section = "\n".join(metadata_lines)
        else:
            metadata_section = ""
        
        # Format constraints section
        constraints_lines = []
        for constraint_name, constraint_desc in constraints.items():
            constraints_lines.append(f"- {constraint_name}: {constraint_desc}")
        constraints_section = "\n".join(constraints_lines) if constraints_lines else "No specific constraints provided."
        
        # Build prompt
        prompt = self._system_prompt_template.format(
            metadata_section=metadata_section,
            constraints_section=constraints_section
        )
        
        return prompt

    def execute(
        self,
        world_state: Dict[str, Any],
        content: str,
    ) -> Dict[str, Any]:
        """
        Execute critic validation.
        
        Args:
            world_state: Dictionary containing metadata and constraints
            content: The response content to validate
            
        Returns:
            Dictionary containing:
                - "accepted": bool indicating if response passes validation
                - "feedback": str explaining the decision
                - "violations": list of violation objects with "constraint" and "description"
        """
        try:
            # Validate world_state structure
            if not isinstance(world_state, dict):
                raise ValueError("world_state must be a dictionary")
            
            constraints = world_state.get("constraints")
            if not constraints or not isinstance(constraints, dict):
                raise ValueError("world_state must contain a 'constraints' dictionary")
            
            # Build system prompt
            system_prompt = self._build_system_prompt(world_state)
            
            # Create messages
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Evaluate the following response against the constraints:\n\n{content}"
                }
            ]
            
            logger.debug(f"Calling critic LLM with {len(constraints)} constraints")
            
            # Call LLM
            response = self._llm.chat(messages)
            response_content = DeepSeekClient.extract_assistant_content(response)
            
            # Parse JSON response
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
                
                result = json.loads(response_content)
                
                # Validate result structure
                if not isinstance(result, dict):
                    raise ValueError("Response is not a JSON object")
                
                # Ensure required fields exist with defaults
                accepted = result.get("accepted", False)
                feedback = result.get("feedback", "No feedback provided.")
                violations = result.get("violations", [])
                
                # Validate violations structure
                if not isinstance(violations, list):
                    violations = []
                else:
                    # Ensure each violation has required fields
                    validated_violations = []
                    for violation in violations:
                        if isinstance(violation, dict) and "constraint" in violation:
                            validated_violations.append({
                                "constraint": violation.get("constraint", ""),
                                "description": violation.get("description", "")
                            })
                    violations = validated_violations
                
                return {
                    "accepted": bool(accepted),
                    "feedback": str(feedback),
                    "violations": violations
                }
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response from critic: {e}")
                logger.debug(f"Response content: {response_content}")
                # Return error result
                return {
                    "accepted": False,
                    "feedback": f"Critic returned invalid JSON response. Original response: {response_content[:200]}",
                    "violations": [
                        {
                            "constraint": "response_format",
                            "description": "Critic failed to return valid JSON"
                        }
                    ],
                    "error": "json_parse_error"
                }
            
        except ValueError as e:
            logger.error(f"Invalid input to critic tool: {e}", exc_info=True)
            return {
                "accepted": False,
                "feedback": f"Invalid input: {str(e)}",
                "violations": [
                    {
                        "constraint": "input_validation",
                        "description": str(e)
                    }
                ],
                "error": "validation_error"
            }
        except Exception as e:
            logger.error(f"Error executing critic tool: {e}", exc_info=True)
            return {
                "accepted": False,
                "feedback": f"Error during validation: {str(e)}",
                "violations": [
                    {
                        "constraint": "system_error",
                        "description": str(e)
                    }
                ],
                "error": "execution_error"
            }

    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format execution result for LLM consumption.
        
        Args:
            result: Result dictionary from execute()
            
        Returns:
            Formatted string describing the validation result
        """
        accepted = result.get("accepted", False)
        feedback = result.get("feedback", "")
        violations = result.get("violations", [])
        
        if accepted:
            status = "ACCEPTED"
            message = f"The response was {status.lower()} by the critic.\n\nFeedback: {feedback}"
        else:
            status = "REJECTED"
            message = f"The response was {status.lower()} by the critic.\n\nFeedback: {feedback}"
            
            if violations:
                message += "\n\nViolations found:"
                for i, violation in enumerate(violations, 1):
                    constraint = violation.get("constraint", "unknown")
                    description = violation.get("description", "")
                    message += f"\n{i}. Constraint '{constraint}': {description}"
        
        if "error" in result:
            message += f"\n\nNote: An error occurred during validation: {result['error']}"
        
        return message

