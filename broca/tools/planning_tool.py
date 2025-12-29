"""
Planning tool for LLM-driven plan generation.

Allows the LLM to self-prompt to generate structured plans of action.
Integrates with z3_validator_tool for logical validation (LLM-driven, not automated).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PlanningTool:
    """
    Tool for generating structured plans of action.
    
    Allows LLM to:
    - Generate structured plans with goal, steps, assumptions, expected outcomes
    - Self-prompt to organize complex tasks
    - Optionally validate plans using z3_validate tool (LLM must call it explicitly)
    """
    
    def __init__(self):
        """Initialize planning tool."""
        logger.info("Initialized PlanningTool")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "planning"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Generate a structured plan of action for achieving a goal. "
            "This tool helps you organize your approach to complex tasks by creating a structured plan.\n\n"
            "**Plan Structure:**\n"
            "- **Goal**: Clear statement of what you want to achieve\n"
            "- **Steps**: Step-by-step actions to accomplish the goal\n"
            "- **Assumptions**: Assumptions you're making (optional)\n"
            "- **Expected Outcomes**: What you expect to achieve (optional)\n"
            "- **Context**: Additional context or constraints (optional)\n\n"
            "**Logical Validation (Optional):**\n"
            "After creating a plan, you can optionally validate its logical soundness using the `z3_validate` tool. "
            "Write Z3 Python code that encodes your plan's logic:\n"
            "- Encode plan steps as logical propositions\n"
            "- Encode assumptions as premises\n"
            "- Encode goal as conclusion\n"
            "- Check if (steps AND assumptions) => goal is satisfiable\n\n"
            "**Example Workflow:**\n"
            "1. Use this planning tool to create a structured plan\n"
            "2. Optionally use `z3_validate` tool to verify logical consistency\n"
            "3. Execute the plan using appropriate tools\n\n"
            "**Note**: The planning tool does NOT automatically validate plans. "
            "You must explicitly call `z3_validate` if you want to check logical soundness."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "Clear statement of what you want to achieve"
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Step-by-step actions to accomplish the goal"
                },
                "context": {
                    "type": "string",
                    "description": "Optional context, constraints, or background information"
                },
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional assumptions you're making about the situation"
                },
                "expected_outcomes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional expected results or outcomes for each step or the overall goal"
                }
            },
            "required": ["goal", "steps"]
        }
    
    def execute(
        self,
        goal: str,
        steps: List[str],
        context: Optional[str] = None,
        assumptions: Optional[List[str]] = None,
        expected_outcomes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute the planning tool to generate a structured plan.
        
        Args:
            goal: Clear statement of what to achieve
            steps: Step-by-step actions
            context: Optional context or constraints
            assumptions: Optional assumptions made
            expected_outcomes: Optional expected results
            
        Returns:
            Dictionary containing structured plan:
            {
                "plan_id": str,
                "goal": str,
                "steps": List[str],
                "context": Optional[str],
                "assumptions": Optional[List[str]],
                "expected_outcomes": Optional[List[str]],
                "created_at": str (ISO format)
            }
        """
        # Generate unique plan ID
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        
        # Create structured plan
        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "steps": steps,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add optional fields if provided
        if context is not None:
            plan["context"] = context
        if assumptions is not None:
            plan["assumptions"] = assumptions
        if expected_outcomes is not None:
            plan["expected_outcomes"] = expected_outcomes
        
        logger.info(
            f"Generated plan {plan_id} with {len(steps)} steps",
            extra={
                "event": "planning_tool_executed",
                "plan_id": plan_id,
                "goal": goal[:100] if goal else "",
                "steps_count": len(steps)
            }
        )
        
        return plan
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format plan result for LLM consumption.
        
        Args:
            result: Plan dictionary from execute()
            
        Returns:
            Formatted string representation of the plan
        """
        lines = []
        lines.append("## Plan Generated")
        lines.append(f"**Plan ID**: {result.get('plan_id', 'unknown')}")
        lines.append("")
        lines.append(f"**Goal**: {result.get('goal', 'N/A')}")
        lines.append("")
        
        steps = result.get('steps', [])
        if steps:
            lines.append("**Steps**:")
            for i, step in enumerate(steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        
        if result.get('context'):
            lines.append(f"**Context**: {result['context']}")
            lines.append("")
        
        assumptions = result.get('assumptions')
        if assumptions:
            lines.append("**Assumptions**:")
            for assumption in assumptions:
                lines.append(f"- {assumption}")
            lines.append("")
        
        expected_outcomes = result.get('expected_outcomes')
        if expected_outcomes:
            lines.append("**Expected Outcomes**:")
            for outcome in expected_outcomes:
                lines.append(f"- {outcome}")
            lines.append("")
        
        lines.append(f"**Created**: {result.get('created_at', 'N/A')}")
        lines.append("")
        lines.append("**Next Steps**:")
        lines.append("- Review the plan")
        lines.append("- Optionally use `z3_validate` tool to verify logical consistency")
        lines.append("- Execute the plan using appropriate tools")
        
        return "\n".join(lines)

