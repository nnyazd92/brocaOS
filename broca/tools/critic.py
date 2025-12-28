"""
Critic tool for providing devils advocate feedback on content.

Allows the main LLM to get critical, alternative perspectives on any content
by sending it to a critical LLM instance that challenges assumptions, finds
weaknesses, and provides alternative viewpoints.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, Any, Optional

from ..llm import create_llm_client, LLMClient
from ..config import config

logger = logging.getLogger(__name__)


class CriticTool:
    """
    Critic tool for providing devils advocate feedback on content.
    
    Allows the main LLM to get critical analysis and alternative perspectives
    on any content. The critic acts as a devils advocate, challenging assumptions,
    finding weaknesses, and providing constructive criticism.
    """
    
    _DEFAULT_SYSTEM_PROMPT_TEMPLATE = """You are a devils advocate critic. Your role is to provide critical, alternative perspectives on content.

{metadata_section}

{constraints_section}

Your task is to:
- Challenge assumptions and question underlying premises
- Identify potential weaknesses, flaws, or blind spots
- Suggest alternative viewpoints or approaches
- Provide constructive criticism that helps improve the content
- Consider edge cases, potential failures, or unintended consequences

You must respond with a JSON object containing:
- "accepted": boolean indicating if you find the content acceptable (true) or have significant concerns (false)
- "feedback": string providing detailed critical analysis and alternative perspectives
- "violations": array of objects with "constraint" (or "concern") and "description" keys for each issue found

Be thorough, constructive, and thought-provoking in your analysis. Even if content is generally good, identify areas for improvement or alternative perspectives."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        system_prompt_template: Optional[str] = None,
    ) -> None:
        """
        Initialize the critic tool.
        
        Args:
            llm_client: Optional LLMClient instance (defaults to new instance via factory)
            system_prompt_template: Optional custom system prompt template
        """
        self._llm = llm_client or create_llm_client()
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
            "Get devils advocate feedback on any content. Provide a world_state object "
            "containing optional metadata and constraints, along with the content to analyze. "
            "The critic will challenge assumptions, find weaknesses, suggest alternatives, "
            "and provide constructive criticism. Use this tool when you want a critical second "
            "opinion or need to identify potential issues before finalizing your response."
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
                    "description": "Optional. Object containing constraints or concerns to consider. Each key is a constraint/concern name and value is the description.",
                    "additionalProperties": True
                }
            },
            "required": []
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
        if constraints_lines:
            constraints_section = "Considerations to keep in mind:\n" + "\n".join(constraints_lines)
        else:
            constraints_section = "No specific constraints or considerations provided. Provide general critical analysis."
        
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
        Execute critic analysis.
        
        Args:
            world_state: Dictionary containing optional metadata and constraints
            content: The content to analyze
            
        Returns:
            Dictionary containing:
                - "accepted": bool indicating if content is acceptable (true) or has significant concerns (false)
                - "feedback": str providing detailed critical analysis
                - "violations": list of concern objects with "constraint" (or "concern") and "description"
        """
        try:
            # Validate world_state structure
            if not isinstance(world_state, dict):
                raise ValueError("world_state must be a dictionary")
            
            constraints = world_state.get("constraints", {})
            if not isinstance(constraints, dict):
                constraints = {}
            
            # Build system prompt
            system_prompt = self._build_system_prompt(world_state)
            
            # Create messages
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Provide devils advocate feedback on the following content:\n\n{content}"
                }
            ]
            
            logger.debug(f"Calling critic LLM with {len(constraints)} constraints/concerns")
            
            # Call LLM
            response = self._llm.chat(messages)
            response_content = self._llm.extract_assistant_content(response)
            
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
            Formatted string describing the critical analysis
        """
        accepted = result.get("accepted", False)
        feedback = result.get("feedback", "")
        violations = result.get("violations", [])
        
        if accepted:
            status = "ACCEPTABLE"
            message = f"The critic finds the content generally {status.lower()}.\n\nFeedback: {feedback}"
        else:
            status = "CONCERNS IDENTIFIED"
            message = f"The critic has identified concerns: {status.lower()}.\n\nFeedback: {feedback}"
            
            if violations:
                message += "\n\nSpecific concerns:"
                for i, violation in enumerate(violations, 1):
                    constraint = violation.get("constraint", violation.get("concern", "unknown"))
                    description = violation.get("description", "")
                    message += f"\n{i}. {constraint}: {description}"
        
        if "error" in result:
            message += f"\n\nNote: An error occurred during analysis: {result['error']}"
        
        return message

